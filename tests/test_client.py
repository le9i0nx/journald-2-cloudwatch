import json
import uuid

import requests_mock


def test_client_make_message(client, now):
    uuid_ = uuid.uuid4()
    encoded = client.make_message({
        '__REALTIME_TIMESTAMP': now,
        'float': .1,
        'str': '',
        'bytes': b'',
        'int': 1,
        'uuid': uuid_,
        'datetime': now})

    assert json.loads(encoded['message']) == {
        '__REALTIME_TIMESTAMP': now.timestamp(),
        'float': .1,
        'str': '',
        'bytes': '',
        'int': 1,
        'uuid': str(uuid_),
        'datetime': now.timestamp(),
    }


def test_client_create_log_group(client):
    with requests_mock.mock() as m:
        m.post('https://logs.eu-west-1.amazonaws.com/')
        client.create_log_group()
    assert m.call_count == 2


def test_client_log_stream(client):
    with requests_mock.mock() as m:
        m.post('https://logs.eu-west-1.amazonaws.com/')
        client.create_log_stream('stream')
    assert m.called
