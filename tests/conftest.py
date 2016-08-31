import datetime as dt


import pytest


@pytest.fixture
def client(request, tmpdir_factory):
    from jd2cw import CloudWatchClient

    cursor = tmpdir_factory.mktemp('tmp').join('cursor')
    client = CloudWatchClient(request.fixturename, cursor.strpath, 0)
    return client


@pytest.fixture
def now():
    return dt.datetime.now()
