import datetime
import itertools
import json
import re
import time
import uuid

import boto3
import botocore


class JournalMsgEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.timestamp()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return super().default(obj)


seq_token_finder = re.compile(r'\d{16,}').search


class CloudWatchClient:
    ALREADY_EXISTS = 'ResourceAlreadyExistsException'
    THROTTLED = 'ThrottlingException'
    CONFLICT = 'ResourceConflictException'

    def __init__(self, log_group, cursor_path, retention,
                 subscription_filter_config):
        self.log_group = log_group
        self.retention = retention
        self.client = boto3.client('logs')
        self.cursor_path = cursor_path
        self.subscription_filter_config = subscription_filter_config
        self.seq_tokens = {}
        self.configured = False

    def configure(self):
        self.create_log_group()
        self.configured = True

    def create_log_group(self):
        '''create a log group, ignoring if it exists.
        If a subscription filter is required create it also,
        only during creation_time of log_group.
        '''
        try:
            self.client.create_log_group(logGroupName=self.log_group)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != self.ALREADY_EXISTS:
                raise
        else:
            if self.retention > 0:
                self.client.put_retention_policy(
                    logGroupName=self.log_group,
                    retentionInDays=self.retention)
            if self.subscription_filter_config:
                destination_arn = self.subscription_filter_config[
                    'destinationArn']
                if destination_arn.split(':', 3)[2] == 'lambda':
                    # if subscription is a lambda we need to set proper,
                    # permission to cloudwatch.
                    lambda_client = boto3.client('lambda')
                    try:
                        lambda_client.add_permission(
                            FunctionName=destination_arn,
                            StatementId='permission_{}'.format(self.log_group),
                            Action='lambda:Invoke',
                            Principal='logs.{}.amazonaws.com'.format(
                                self.client.meta.config.region_name),
                        )
                    except botocore.exceptions.ClientError as e:
                        if e.response['Error']['Code'] != self.CONFLICT:
                            raise e
                self.client.put_subscription_filter(
                    **self.subscription_filter_config)

    def create_log_stream(self, log_stream):
        ''' create a log stream, ignoring if it exists '''
        try:
            self.client.create_log_stream(logGroupName=self.log_group,
                                          logStreamName=log_stream)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != self.ALREADY_EXISTS:
                raise

    def log_stream_for(self, msg):
        # docker container
        if ('CONTAINER_NAME' in msg and
                msg.get('_SYSTEMD_UNIT') == 'docker.service'):
            return '{}.container'.format(msg['CONTAINER_NAME'])

        # systemd unit
        if '_SYSTEMD_UNIT' in msg:
            unit = msg['_SYSTEMD_UNIT']
            if '@' in unit:
                # remove templating in unit names
                # e.g. sshd@127.0.0.1:12345.service -> sshd.service
                unit = '.'.join((unit.partition('@')[0],
                                 unit.rpartition('.')[2]))
            return unit

        # syslog
        if 'SYSLOG_IDENTIFIER' in msg:
            return msg['SYSLOG_IDENTIFIER']

        # otherwise, log by executable
        return msg.get('_EXE', '[other]')

    def make_message(self, message):
        ''' prepare a message to send to cloudwatch '''
        timestamp = int(message['__REALTIME_TIMESTAMP'].timestamp() * 1000)
        # remove unserialisable values
        message = {k: v for k, v in message.items() if
                   isinstance(v, (str, int, float, bytes,
                                  uuid.UUID, datetime.datetime))}
        # encode entire message in json
        message = json.dumps(message, cls=JournalMsgEncoder)
        return dict(timestamp=timestamp, message=message)

    def put_log_messages(self, log_stream, messages):
        ''' log the message to cloudwatch '''
        try:
            seq_token = self.seq_tokens[log_stream]
        except KeyError:
            seq_token = self.get_seq_token(log_stream)

        kwargs = (dict(sequenceToken=seq_token) if seq_token else {})
        log_events = sorted(map(self.make_message, messages),
                            key=lambda x: x['timestamp'])

        MAX_RETRY = 5
        counter = 0
        while True:
            try:
                response = self.client.put_log_events(
                    logGroupName=self.log_group,
                    logStreamName=log_stream,
                    logEvents=log_events,
                    **kwargs
                )
            except botocore.exceptions.ClientError as err:
                if (err.response['Error']['Code'] ==
                        'InvalidSequenceTokenException'):
                    # the error message is giving us the expected token
                    seq_token = seq_token_finder(
                        err.response['Error']['Message']).group(0)
                    kwargs['sequenceToken'] = seq_token
                    counter += 1
                    if counter > MAX_RETRY:
                        time.sleep(.1)
                        seq_token = self.get_seq_token(log_stream)
                        counter = 0
                else:
                    raise err
            else:
                break
        self.seq_tokens[log_stream] = response['nextSequenceToken']

    def group_messages(self, messages, maxlen=10,
                       timespan=datetime.timedelta(hours=23)):
        '''
        group messages:
            - in 23 hour segments (cloudwatch rejects logs spanning > 24 hours)
            - in groups of 10 to avoid upload limits
        '''
        while messages:
            group = messages
            start_date = group[0]['__REALTIME_TIMESTAMP']
            group = itertools.takewhile(
                lambda m: m['__REALTIME_TIMESTAMP'] - start_date < timespan,
                group)
            group = itertools.islice(group, maxlen)
            group = list(group)
            yield group
            messages = messages[len(group):]

    def log_messages(self, log_stream, messages):
        if not self.configured:
            raise RuntimeError

        for chunk in self.group_messages(messages):
            self._log_messages(log_stream, chunk)

    def _log_messages(self, log_stream, messages):
        ''' log the messages, then save the cursor '''
        if not messages:
            return

        while True:
            try:
                self.put_log_messages(log_stream, messages)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != self.THROTTLED:
                    raise
            else:
                break
            time.sleep(1)
        # save last cursor
        self.save_cursor(messages[-1]['__CURSOR'])

    def get_seq_token(self, log_stream):
        ''' get the sequence token for the stream '''

        streams = self.client.describe_log_streams(
            logGroupName=self.log_group,
            logStreamNamePrefix=log_stream,
            limit=1)
        if streams['logStreams']:
            stream = streams['logStreams'][0]
            if stream['logStreamName'] == log_stream:
                # found the stream
                return stream.get('uploadSequenceToken')
        # no stream, create it
        self.create_log_stream(log_stream)

    @staticmethod
    def retain_message(message, retention=datetime.timedelta(days=14)):
        ''' cloudwatch ignores messages older than 14 days '''
        return ((datetime.datetime.now() - message['__REALTIME_TIMESTAMP']) <
                retention)

    def save_cursor(self, cursor):
        ''' saves the journal cursor to file '''
        with open(self.cursor_path, 'w') as f:
            f.write(cursor)

    def load_cursor(self):
        '''loads the journal cursor from file, returns None if file not found
        '''
        try:
            with open(self.cursor_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return
