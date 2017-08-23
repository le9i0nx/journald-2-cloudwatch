# journald-2-cloudwatch

Send journald logs to AWS CloudWatch

[![Build Status](https://travis-ci.org/lock8/journald-2-cloudwatch.svg?branch=master)](https://travis-ci.org/lock8/journald-2-cloudwatch)
[![Docker Repository on Quay](https://quay.io/repository/lock8/journald-2-cloudwatch/status "Docker Repository on Quay")](https://quay.io/repository/lock8/journald-2-cloudwatch)
[![codecov](https://codecov.io/gh/lock8/journald-2-cloudwatch/branch/master/graph/badge.svg)](https://codecov.io/gh/lock8/journald-2-cloudwatch)

This is heavily based on <https://github.com/arkenio/journald-wrapper>.

## Running in Docker

```bash
docker run -e AWS_DEFAULT_REGION=ap-southeast-2 -v /var/log/journal/:/var/log/journal/:ro -v /data/journald:/data/journald/:rw quay.io/lock8/journald-2-cloudwatch --cursor=/data/journald/cursor
```

If journald is configured with `"volatile"` `Storage` then the command will be:

```bash
docker run -e AWS_DEFAULT_REGION=ap-southeast-2 -v /run/log/journal/:/var/log/journal/:ro -v /data/journald:/data/journald/:rw quay.io/lock8/journald-2-cloudwatch --cursor=/data/journald/cursor
```

Note the host mount point `/run/log/journal/`.

## CloudWatch log format

### Log group

By default, the log group is the EC2 instance ID (fetched from the AWS metadata URL).
If the `--prefix=abcdef` flag is given, the log group is prefixed and becomes (for example) `abcdef_{instance_id}`
If the `--log-group=abcdef` flag is given, the argument is used as the log group instead.

### Log stream

The log stream is taken from the fields in the journal messages, in decreasing priority:

* the docker container name
* the systemd unit name (with the templated parts removed)
* the syslog identifier
* the `_EXE` field of the message
* `[other]` for anything else

## Journal cursor

The journal cursor is stored in the file specified in the `--cursor` flag.
This file should be persisted to disk/placed in a mounted volume; consider using named volumes.
