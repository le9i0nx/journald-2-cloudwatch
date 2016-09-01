import datetime as dt


import pytest


@pytest.fixture
def client(request, tmpdir_factory):
    from jd2cw import CloudWatchClient

    cursor = tmpdir_factory.mktemp('tmp').join('cursor')
    client = CloudWatchClient(request.fixturename, cursor.strpath, 1)
    return client


@pytest.fixture
def now():
    return dt.datetime.now()


@pytest.fixture(autouse=True, scope='session')
def mock_vendored_requests():
    import botocore.vendored.requests
    import requests_mock.mocker
    requests_mock.mocker.requests = botocore.vendored.requests
