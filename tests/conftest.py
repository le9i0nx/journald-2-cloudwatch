import datetime as dt


import botocore.vendored.requests
import pytest
import requests_mock
import requests_mock.mocker


@pytest.fixture
def client(request, tmpdir_factory):
    from jd2cw import CloudWatchClient

    cursor = tmpdir_factory.mktemp('tmp').join('cursor')
    with requests_mock.mock() as m:
        m.post('https://logs.eu-west-1.amazonaws.com/')
        m.get('http://169.254.169.254/latest/meta-data/iam/'
              'security-credentials/')
        client = CloudWatchClient(request.fixturename, cursor.strpath, 1)
    return client


@pytest.fixture
def now():
    return dt.datetime.now()


@pytest.fixture(autouse=True, scope='session')
def mock_vendored_requests():
    requests_mock.mocker.requests = botocore.vendored.requests
