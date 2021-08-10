import re

import pytest
from pytest_mock import MockFixture
import requests_mock
from callee import Regex

from lemoncheesecake_requests import Session, Logger, is_2xx, is_3xx, is_4xx, is_5xx


def test_is_2xx():
    assert is_2xx().matches(204)
    assert not is_2xx().matches(199)
    assert not is_2xx().matches(300)


def test_is_3xx():
    assert is_3xx().matches(301)
    assert not is_3xx().matches(299)
    assert not is_3xx().matches(400)


def test_is_4xx():
    assert is_4xx().matches(404)
    assert not is_4xx().matches(399)
    assert not is_4xx().matches(500)


def test_is_5xx():
    assert is_5xx().matches(503)
    assert not is_5xx().matches(499)
    assert not is_5xx().matches(600)


@pytest.fixture
def lcc_mock(mocker):
    return mocker.patch("lemoncheesecake_requests.lcc")


def mock_session(session, **kwargs):
    adapter = requests_mock.Adapter()
    adapter.register_uri(requests_mock.ANY, requests_mock.ANY, **kwargs)
    session.mount('mock://', adapter)
    return session


def assert_logs(mock, *expected):
    for val in expected:
        if type(val) is str:
            val = Regex(val, re.DOTALL | re.IGNORECASE)
        if not isinstance(val, Regex):
            val = Regex(val)
        mock.log_info.assert_any_call(val)


def test_session_get(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    session.get("mock://www.example.net")
    assert_logs(
        lcc_mock,
        "HTTP request.+GET mock://www.example.net",
        "HTTP request headers",
        r".+status.+201",
        "HTTP response headers.+foo.+bar",
        "HTTP response body.+foobar"
    )
