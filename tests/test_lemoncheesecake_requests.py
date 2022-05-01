import re
import io
import base64

import callee
import pytest
import requests_mock
from callee import Regex

from lemoncheesecake_requests import Session, Logger, Response, StatusCodeMismatch, \
    is_2xx, is_3xx, is_4xx, is_5xx
from lemoncheesecake_requests.__version__ import __version__
from lemoncheesecake.exceptions import AbortTest


REGEXP_CLASS = re.compile("dummy").__class__


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


@pytest.mark.parametrize("debug,expected", ((None, False), (False, False), (True, True)))
def test_logger_on(debug, expected):
    logger = Logger.on() if debug is None else Logger.on(debug)
    assert logger.request_line_logging is True
    assert logger.request_headers_logging is True
    assert logger.request_body_logging is True
    assert logger.response_code_logging is True
    assert logger.response_headers_logging is True
    assert logger.response_body_logging is True
    assert logger.debug is expected


def test_logger_off():
    logger = Logger.off()
    assert logger.request_line_logging is False
    assert logger.request_headers_logging is False
    assert logger.request_body_logging is False
    assert logger.response_code_logging is False
    assert logger.response_headers_logging is False
    assert logger.response_body_logging is False
    assert logger.debug is False


@pytest.mark.parametrize("debug,expected", ((None, False), (False, False), (True, True)))
def test_logger_no_headers(debug, expected):
    logger = Logger.no_headers() if debug is None else Logger.no_headers(debug)
    assert logger.request_line_logging is True
    assert logger.request_headers_logging is False
    assert logger.request_body_logging is True
    assert logger.response_code_logging is True
    assert logger.response_headers_logging is False
    assert logger.response_body_logging is True
    assert logger.debug is expected


@pytest.mark.parametrize("debug,expected", ((None, False), (False, False), (True, True)))
def test_logger_no_response_body(debug, expected):
    logger = Logger.no_response_body() if debug is None else Logger.no_response_body(debug)
    assert logger.request_line_logging is True
    assert logger.request_headers_logging is True
    assert logger.request_body_logging is True
    assert logger.response_code_logging is True
    assert logger.response_headers_logging is True
    assert logger.response_body_logging is False
    assert logger.debug is expected


@pytest.fixture
def lcc_mock(mocker):
    return mocker.patch("lemoncheesecake_requests.lcc")


@pytest.fixture
def log_check_mock(mocker):
    return mocker.patch("lemoncheesecake.matching.operations.log_check")


def mock_session(session=None, **kwargs):
    if not session:
        session = Session(logger=Logger.off())
    adapter = requests_mock.Adapter()
    adapter.register_uri(requests_mock.ANY, requests_mock.ANY, **kwargs)
    session.mount('http://', adapter)
    return session


def assert_logs(mock, *expected, as_debug=False):
    log_mock = mock.log_debug if as_debug else mock.log_info

    for val in expected:
        if type(val) is str:
            val = Regex(val, re.DOTALL | re.IGNORECASE)
        if isinstance(val, REGEXP_CLASS):
            val = Regex(val)
        log_mock.assert_any_call(val)
    assert len(log_mock.mock_calls) == len(expected)


@pytest.mark.parametrize("as_debug", ([False], [True]))
def test_session_default(lcc_mock, as_debug):
    session = mock_session(Session(), status_code=201, headers={"Foo": "bar"}, text="foobar")
    if as_debug:
        session.logger.debug = True
    session.post("http://www.example.net", data="foobar")
    assert_logs(
        lcc_mock,
        r"HTTP request.+POST http://www\.example\.net",
        "HTTP request headers",
        "HTTP request body",
        r".+status.+201",
        "HTTP response headers.+foo.+bar",
        "HTTP response body.+foobar",
        as_debug=as_debug
    )


def test_session_no_logging_at_all(lcc_mock):
    session = mock_session()
    session.get("http://www.example.net")
    assert_logs(lcc_mock)


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
    session.post("http://www.example.net", json={"foo": "bar"})
    assert_logs(
        lcc_mock,
        "HTTP request body.+JSON.+foo.+bar"
    )


def test_session_log_only_request_body_data_as_dict(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.post("http://www.example.net", data={"foo": "bar"})
    assert_logs(
        lcc_mock,
        "HTTP request body.+foo.+bar"
    )


def test_session_log_only_request_body_data_as_text(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.post("http://www.example.net", data="foobar")
    assert_logs(
        lcc_mock,
        "HTTP request body.+foobar"
    )


def test_session_log_only_request_body_data_as_binary(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.post("http://www.example.net", data=b"foobar")
    assert_logs(
        lcc_mock,
        "HTTP request body.+Zm9vYmFy"  # NB: Zm9vYmFy is base64-ified "foobar"
    )


def test_session_log_only_request_body_data_as_stream(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.post("http://www.example.net", data=io.StringIO("foobar"))
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
    session.post("http://www.example.net", data=mygen())
    assert_logs(
        lcc_mock,
        "HTTP request body.+generator"
    )


def test_session_log_only_request_body_files_as_list(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.post("http://www.example.net", files=[("file", ("plain.txt", "sometextdata", "text/plain"))])
    assert_logs(
        lcc_mock,
        r"HTTP request body.+plain\.txt.+text/plain"
    )


def test_session_log_only_request_body_files_as_dict(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.post("http://www.example.net", files={"file": ("plain.txt", "sometextdata", "text/plain")})
    assert_logs(
        lcc_mock,
        r"HTTP request body.+plain\.txt.+text/plain"
    )


def test_session_log_only_request_body_files_as_2_tuple(lcc_mock):
    session = mock_session()
    session.logger.request_body_logging = True
    session.post("http://www.example.net", files=[("file", ("plain.txt", "sometextdata"))])
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


def test_session_log_only_response_line(lcc_mock):
    session = mock_session(status_code=204)
    session.logger.response_code_logging = True
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r"HTTP response.+204"
    )


def test_session_log_only_response_header(lcc_mock):
    session = mock_session(headers={"Foo": "bar"})
    session.logger.response_headers_logging = True
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r"HTTP response headers.+Foo.+bar"
    )


def test_session_log_only_response_body_text(lcc_mock):
    session = mock_session(text="foobar")
    session.logger.response_body_logging = True
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r"HTTP response body.+foobar"
    )


def test_session_log_only_response_body_json(lcc_mock):
    session = mock_session(json={"foo": "bar"})
    session.logger.response_body_logging = True
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r'HTTP response body.+"foo": "bar"'
    )


def test_session_log_only_response_body_binary(lcc_mock):
    # This is https://docs.python.org/3/_static/py.png:
    data = b"""\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\
\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x06bKGD\x00\xff\x00\xff\x00\xff\xa0\xbd\xa7\x93\x00\x00\x00\tpHYs\x00\
\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xd8\x04\x1b\x118!\x063\'^\x00\x00\x027IDAT8\
\xcbe\x93OHUA\x14\x87\xbf{\xdf\xb3w{"\x94\x10\xa5\xd1&hS\x8b6\xadZ\xb4\x10\x1emB*xP\xdb\xc0MQ\xae\xdd\x04A\x8b "\xda)\
mZH\x1b\x17\x91 F\x11EF\x98\x96\xb6\xb5\x88\xcc2\x15\xd4\xfc\xf3\xee\x9dy3g\xe6\xb6\xf0\xde\xbc\xea\x81\xc3\xc0\xcc\xf7\
;\xe77\xcc\x9c\x80]\xd1\xfd\xe0\xed3i\x9as\xde\x99v\xb1M\xc4\x18\xa4\xa9\xb4U\xfa\xf1\xc7\xfe\xeb}\x80\x06\\\xce\x87\xbb\
\x0bx\'\x17G\xfaj\xedN,\xceZ\xbcX\xbcwQ\x1a\xf8\x9b\xc01 *\xf2{\n8k9\x7fg\x18\'v;\xad\xcd\x8f;\x80j\x91/\x03t?|\x7f\xdb\
[{\\\xac\n\x8cN\x06\x8dj\x94E\xc7%g\x0c\xe1\xbeJ=M}\xceW\x80\xd2\x8e\x02\x97\x1f}x\xed\xc4v\xa5^\xc0{\x02\xa0Tn\x81J\x15\
\x82\x12N\xec\x0e\x87\xe9\\}\xc1\xdbX\x8bn\xdc\xaf\x9czw/\xf4\xdeumY5;mg\x99\x87\xa8\xcdQ\xc0"\t\xa1SQ\x19}\x03\xe8,\
\xe7\xa0/\x88|\xe1\xdei\xea\xb5\xd3\xf1\x9b\xa9\'}\x03\xcbS\xb5\x1a\xa2@\x12B\xaf\xda\x81\x8e\xf2\x0e\xb1\xb5\xe8\xc6\
\xda\xe8\xfc\xf8\xf0\xd3\xf9\xe9Wk\x80\x00)`\xe6\xc6j\'\x0f\xb6J/N\x81K@\x12\x80\xfde1M\xed\xc5FN,j}yhb\xa0wp\xe3\xe7\
\xad+\xad\xd1\x89K\xa1S\xd1\x7fXb\xf2\xee\x88\xc2\x8b\xd6@\x10:\x91\xd9\xdc\xfa\x9f\xc9\x97\xcf\xe3_\xbd=mU\x7f5\xf4EqR\
\x10\'\xe04I\x92N\x02&t:\xee\x17c\xb4\x13\xcb\xef\xa9\x91\xb5j\xe4.l\x0b\n\xa2\x82\x18`zF\xbf\x006\x83\xecgu\x00G\x81f\
\xbapm"\x87\x97\x16\xff\x0e\x95\xbcJ\xb7\x9c(p\n\x80o\xb3\xe6\xcb\xd9\x9e\xd5q\xe0G\x190\xc0"\xb0\x01\xa4\xc5n\x87\x0f\
\xb8:"\xe0,\x88%8\xb3\xd8\x054\x00\x95\xf1+!\xe0\xb3\x8d\x15`\xd5\xdbDoY-\xe4\xe9\xaf\xf84\xd5\xd9\x8b,\x00\xdf\xb35\xd93\
\x0b\x8d\x8d\xf5\xba\xd5\xf1gob\x9d;\xb1\xe3\x9d3c\x9f\xd4]\xc0\x02I\xd6\xd0\x02i\xc0\xde\x88\x80C\xc0\x11\xa0\rh\xc9\
\\nf]\x97\xb2\x91\x06\xe0\x1f\x01\xbf\xaf\xff\xfc\x8c\x00\x9a\x00\x00\x00\x00IEND\xaeB`\x82"""
    data_b64 = base64.encodebytes(data).decode()

    session = mock_session(headers={"Content-Type": "image/png"}, content=data)
    session.logger.response_body_logging = True
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        r'HTTP response body.+' + re.escape(data_b64)
    )


def test_session_logger_switching(lcc_mock):
    session = mock_session(Session(logger=Logger.on()))

    # First call, using the session.logger
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        callee.Any(), callee.Any(), callee.Any(), callee.Any(), callee.Any()
    )
    lcc_mock.reset_mock()

    # Second call, using the logger passed as argument
    session.get("http://www.example.net", logger=Logger.off())
    assert_logs(lcc_mock)
    lcc_mock.reset_mock()

    # Third call, back to the session.logger
    session.get("http://www.example.net")
    assert_logs(
        lcc_mock,
        callee.Any(), callee.Any(), callee.Any(), callee.Any(), callee.Any()
    )


def test_bodies_saved_as_attachments(lcc_mock):
    request_body = "A" * 20
    response_body = "B" * 20
    session = mock_session(text=response_body)
    session.logger = Logger.on()
    session.logger.max_inlined_body_size = 10
    session.post("http://www.example.net", data=request_body)
    assert_logs(lcc_mock, callee.Any(), callee.Any(), callee.Any(), callee.Any())
    lcc_mock.save_attachment_content.assert_any_call(
        callee.Regex(f".*{request_body}.*", re.DOTALL), callee.Any(), "HTTP request body"
    )
    lcc_mock.save_attachment_content.assert_any_call(
        callee.Regex(f".*{response_body}.*", re.DOTALL), callee.Any(), "HTTP response body"
    )


def test_max_inlined_body_size_and_debug(lcc_mock):
    request_body = "A" * 20
    response_body = "B" * 20
    session = mock_session(text=response_body)
    session.logger = Logger.on()
    session.logger.max_inlined_body_size = 10
    session.logger.debug = True
    session.post("http://www.example.net", data=request_body)
    assert_logs(
        lcc_mock,
        callee.Any(), callee.Any(), callee.Any(), callee.Any(), callee.Any(), callee.Any(),
        as_debug=True
    )


@pytest.mark.parametrize("method", ("get", "options", "head", "post", "put", "patch", "delete"))
def test_method(lcc_mock, method):
    session = mock_session()
    session.logger.request_line_logging = True
    getattr(session, method)("http://www.example.net")
    assert_logs(lcc_mock, rf".+{method.upper()} http://www\.example\.net")


def test_request(lcc_mock):
    session = mock_session()
    session.logger.request_line_logging = True
    session.request("GET", "http://www.example.net")
    assert_logs(lcc_mock, rf".+GET http://www\.example\.net")


def test_response_constructor():
    # see comment in Response.__init__
    # this test is here to make test coverage happy
    Response()


def test_response_check_status_code_success(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.check_status_code(200) is resp
    log_check_mock.assert_called_with(callee.Regex(".*200.*"), True, callee.Any())


def test_response_check_status_code_failure(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.check_status_code(201) is resp
    log_check_mock.assert_called_with(callee.Regex(".*201.*"), False, callee.Regex(".*200.*"))


def test_response_check_ok(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.check_ok() is resp
    log_check_mock.assert_called_with(callee.Regex(".*2xx.*"), True, callee.Any())


def test_response_require_status_code_success(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.require_status_code(200) is resp
    log_check_mock.assert_called_with(callee.Regex(".*200.*"), True, callee.Any())


def test_response_require_status_code_failure(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    with pytest.raises(AbortTest):
        resp.require_status_code(201)
    log_check_mock.assert_called_with(callee.Regex(".*201.*"), False, callee.Regex(".*200.*"))


def test_response_require_ok(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.require_ok() is resp
    log_check_mock.assert_called_with(callee.Regex(".*2xx.*"), True, callee.Any())


def test_response_assert_status_code_success(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.assert_status_code(200) is resp
    log_check_mock.assert_not_called()


def test_response_assert_status_code_failure(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    with pytest.raises(AbortTest):
        resp.assert_status_code(201)
    log_check_mock.assert_called_with(callee.Regex(".*201.*"), False, callee.Regex(".*200.*"))


def test_response_assert_ok(lcc_mock, log_check_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.assert_ok() is resp
    log_check_mock.assert_not_called()


def test_raise_unless_status_code_success(lcc_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.raise_unless_status_code(200) is resp


def test_raise_unless_status_code_failure(lcc_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    with pytest.raises(StatusCodeMismatch) as excinfo:
        resp.raise_unless_status_code(201)
    assert re.search(r"expected .+ 201, .+ 200", str(excinfo.value))


def test_raise_unless_ok(lcc_mock):
    session = mock_session(status_code=200)
    resp = session.get("http://www.example.net")
    assert resp.raise_unless_ok() is resp


def test_version():
    assert re.match(r"^\d+\.\d+\.\d+$", __version__)
