import itertools
import urllib.request

import systemd.journal

from .client import CloudWatchClient


def get_instance_id():
    URL = 'http://169.254.169.254/latest/meta-data/instance-id'
    with urllib.request.urlopen(URL) as src:
        return src.read().decode()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--cursor', required=True,
                        help='Store/read the journald cursor in this file')
    parser.add_argument('--logs', default='/var/log/journal',
                        help='Directory to journald logs'
                        ' (default: %(default)s)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--prefix', default='',
                       help='Log group prefix (default is blank).'
                       ' Log group will be {prefix}_{instance_id}')
    group.add_argument('--log-group',
                       help='Name of the log group to use')
    parser.add_argument('--retention', type=int, default=0,
                        help='Set retention duration of log_group in days.'
                        ' Only when log group is created.'
                        ' %(default)s means infinite')
    args = parser.parse_args()

    if args.log_group:
        log_group = args.log_group
    else:
        log_group = get_instance_id()
        if args.prefix:
            log_group = '{}_{}'.format(args.prefix, log_group)

    client = CloudWatchClient(log_group, args.cursor, args.retention)

    while True:
        cursor = client.load_cursor()
        with systemd.journal.Reader(path=args.logs) as reader:
            if cursor:
                reader.seek_cursor(cursor)
            else:
                # no cursor, start from start of this boot
                reader.this_boot()
                reader.seek_head()

            reader = filter(CloudWatchClient.retain_message, reader)
            for log_stream, messages in itertools.groupby(
                    reader, key=client.log_stream_for):
                client.log_messages(log_stream, list(messages))
