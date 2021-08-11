import re
import io

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


def mock_session(session=None, **kwargs):
    if not session:
        session = Session(logger=Logger.off())
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
    session = mock_session()
    session.logger.request_line_logging = True
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r"HTTP request.+GET http://www\.example\.net",
    )


def test_session_log_only_request_line_with_params(lcc_mock):
    session = mock_session()
    session.logger.request_line_logging = True
    session.get("http://www.example.net", params={"foo": "bar"})
    assert_logs(
        lcc_mock,
        r"HTTP request.+GET http://www\.example\.net\?foo=bar",
    )


def test_session_log_only_request_header(lcc_mock):
    session = mock_session()
    session.logger.request_headers_logging = True
    session.get("http://www.example.net", headers={"foo": "bar"})
    assert_logs(
        lcc_mock,
        "HTTP request headers.+foo.+bar"
    )


def test_session_log_only_request_body_json(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", json={"foo": "bar"})
    assert_logs(
        lcc_mock,
        "HTTP request body.+JSON.+foo.+bar"
    )


def test_session_log_only_request_body_data_as_dict(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", data={"foo": "bar"})
    assert_logs(
        lcc_mock,
        "HTTP request body.+foo.+bar"
    )


def test_session_log_only_request_body_data_as_text(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", data="foobar")
    assert_logs(
        lcc_mock,
        "HTTP request body.+foobar"
    )


def test_session_log_only_request_body_data_as_binary(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", data=b"foobar")
    assert_logs(
        lcc_mock,
        "HTTP request body.+Zm9vYmFy"  # NB: Zm9vYmFy is base64-ified "foobar"
    )


def test_session_log_only_request_body_data_as_stream(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", data=io.StringIO("foobar"))
    assert_logs(
        lcc_mock,
        "HTTP request body.+IO stream"
    )


def test_session_log_only_request_body_data_as_generator(lcc_mock):
    def mygen():
        yield "foo"
        yield "bar"

    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", data=mygen())
    assert_logs(
        lcc_mock,
        "HTTP request body.+generator"
    )


def test_session_log_only_request_body_files_as_list(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", files=[("file", ("plain.txt", "sometextdata", "text/plain"))])
    assert_logs(
        lcc_mock,
        r"HTTP request body.+plain\.txt.+text/plain"
    )


def test_session_log_only_request_body_files_as_dict(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", files={"file": ("plain.txt", "sometextdata", "text/plain")})
    assert_logs(
        lcc_mock,
        r"HTTP request body.+plain\.txt.+text/plain"
    )


def test_session_log_only_request_body_files_as_2_tuple(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.get("http://www.example.net", files=[("file", ("plain.txt", "sometextdata"))])
    assert_logs(
        lcc_mock,
        r"HTTP request body.+plain\.txt"
    )


def test_session_log_hints(lcc_mock):
    session = mock_session(Session(logger=Logger.off(), hint="this is hint"))
    session.logger.request_line_logging = True
    session.logger.response_code_logging = True
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r"HTTP request \(this is hint\)",
        r"HTTP response \(this is hint\)"
    )
