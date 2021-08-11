import re

import pytest
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
    session.mount('http://', adapter)
    return session


def assert_logs(mock, *expected):
    for val in expected:
        if type(val) is str:
            val = Regex(val, re.DOTALL | re.IGNORECASE)
        if not isinstance(val, Regex):
            val = Regex(val)
        mock.log_info.assert_any_call(val)
    assert len(mock.log_info.mock_calls) == len(expected)


def test_session_default(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r"HTTP request.+GET http://www\.example\.net",
        "HTTP request headers",
        r".+status.+201",
        "HTTP response headers.+foo.+bar",
        "HTTP response body.+foobar"
    )


def test_session_log_only_request_line(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    logger = Logger.off()
    logger.request_line_logging = True
    session.get("http://www.example.net", logger=logger)
    assert_logs(
        lcc_mock,
        r"HTTP request.+GET http://www\.example\.net",
    )


def test_session_log_only_request_header(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    logger = Logger.off()
    logger.request_headers_logging = True
    session.get("http://www.example.net", logger=logger)
    assert_logs(
        lcc_mock,
        "HTTP request headers"
    )


def test_session_log_only_request_body_json(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    logger = Logger.off()
    logger.request_body_logging = True
    session.get("http://www.example.net", json={"foo": "bar"}, logger=logger)
    assert_logs(
        lcc_mock,
        "HTTP request body.+JSON.+foo.+bar"
    )


def test_session_log_only_request_body_data_dict(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    logger = Logger.off()
    logger.request_body_logging = True
    session.get("http://www.example.net", data={"foo": "bar"}, logger=logger)
    assert_logs(
        lcc_mock,
        "HTTP request body.+foo.+bar"
    )


def test_session_log_only_request_body_data_raw(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    logger = Logger.off()
    logger.request_body_logging = True
    session.get("http://www.example.net", data="foobar", logger=logger)
    assert_logs(
        lcc_mock,
        "HTTP request body.+foobar"
    )


def test_session_log_only_request_body_files_as_list(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    logger = Logger.off()
    logger.request_body_logging = True
    session.get("http://www.example.net", files=[("file", ("plain.txt", "sometextdata", "text/plain"))], logger=logger)
    assert_logs(
        lcc_mock,
        r"HTTP request body.+plain\.txt.+text/plain"
    )


def test_session_log_only_request_body_files_as_dict(lcc_mock):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    logger = Logger.off()
    logger.request_body_logging = True
    session.get("http://www.example.net", files={"file": ("plain.txt", "sometextdata", "text/plain")}, logger=logger)
    assert_logs(
        lcc_mock,
        r"HTTP request body.+plain\.txt.+text/plain"
    )
