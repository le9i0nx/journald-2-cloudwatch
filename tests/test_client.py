import json
import uuid


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
