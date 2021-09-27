import base64
import inspect
import collections.abc
import io
import json
from urllib.parse import urlencode
from typing import Union, Optional

import requests

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from lemoncheesecake.matching.matcher import Matcher, MatchResult, MatcherDescriptionTransformer

__all__ = (
    "Session", "Response", "Logger",
    "is_2xx", "is_3xx", "is_4xx", "is_5xx",
    "LemoncheesecakeRequestsException", "StatusCodeMismatch"
)


class LemoncheesecakeRequestsException(Exception):
    """
    Base exception class for lemoncheesecake-requests.
    """
    pass


class StatusCodeMismatch(LemoncheesecakeRequestsException):
    """
    This exception is raised by ``raise_unless_*`` methods.
    """

    def __init__(self, response: "Response", matcher: Matcher, match_result: MatchResult):
        self.response = response
        self.matcher = matcher
        self.match_result = match_result

    def __str__(self):
        return (
            f"expected status code {self.matcher.build_description(MatcherDescriptionTransformer())}," +
            f" {self.match_result.description}\n\n" +
            "\n\n".join(
                # some serializing methods can return empty data, that's why we filter them out
                filter(bool, (
                    Logger.format_request_line(
                        self.response.request.method, self.response.request.url
                    ),
                    Logger.format_request_headers(self.response.request.headers),
                    Logger.format_request_body(self.response.orig_request),
                    Logger.format_response_line(self.response),
                    Logger.format_response_headers(self.response.headers),
                    Logger.format_response_body(self.response)
                ))
            )
        )


class Logger:
    """
    The Logger class.

    It provides lemoncheesecake logging facilities for a :py:class:`lemoncheesecake_requests.Session` object.
    """
    def __init__(self,
                 request_line_logging=True, request_headers_logging=True, request_body_logging=True,
                 response_code_logging=True, response_headers_logging=True, response_body_logging=True,
                 max_inlined_body_size=2048):
        #: Whether or not the request line must be logged.
        self.request_line_logging: bool = request_line_logging
        #: Whether or not the request headers must be logged.
        self.request_headers_logging: bool = request_headers_logging
        #: Whether or not the request body must be logged.
        self.request_body_logging: bool = request_body_logging
        #: Whether or not the response body must be logged.
        self.response_code_logging: bool = response_code_logging
        #: Whether or not the response headers must be logged.
        self.response_headers_logging: bool = response_headers_logging
        #: Whether or not the response body must be logged.
        self.response_body_logging: bool = response_body_logging
        #: If a serialized request/response body size is greater than ``max_inlined_body_size`` then it will
        #: be logged as an attachment. If it is set to ``None``, the body will be logged directly
        #: whatever his size.
        self.max_inlined_body_size: Optional[int] = max_inlined_body_size

    @classmethod
    def on(cls) -> "Logger":
        """
        Create a logger with every request/response details enabled.
        """
        return cls()

    @classmethod
    def off(cls) -> "Logger":
        """
        Create a logger with every request/response details disabled.
        """
        return cls(
            request_line_logging=False, request_headers_logging=False, request_body_logging=False,
            response_code_logging=False, response_headers_logging=False, response_body_logging=False
        )

    @classmethod
    def no_headers(cls) -> "Logger":
        """
        Create a logger with every request/response details enabled except headers.
        """
        return cls(request_headers_logging=False, response_headers_logging=False)

    @classmethod
    def no_response_body(cls) -> "Logger":
        """
        Create a logger with every request/response details enabled except the response body.
        """
        return cls(response_body_logging=False)

    @staticmethod
    def format_request_line(method: str, url: str, params: dict = None, hint: str = None) -> str:
        formatted = "HTTP request"
        if hint:
            formatted += f" ({hint})"
        formatted += f":\n  > {method} {url}"
        if params:
            formatted += ("&" if "?" in url else "?") + urlencode(params)
        return formatted

    @staticmethod
    def _format_json(data):
        return json.dumps(data, indent=4, ensure_ascii=False)

    @staticmethod
    def _format_dict(data) -> str:
        return "\n".join(f"- {name}: {value}" for name, value in data.items())

    @staticmethod
    def _format_binary(data: bytes) -> str:
        return base64.encodebytes(data).decode()

    @staticmethod
    def format_request_headers(headers) -> str:
        return "HTTP request headers:\n%s" % Logger._format_dict(headers)

    @classmethod
    def _format_request_json(cls, data) -> str:
        return "HTTP request body (JSON):\n" + cls._format_json(data)

    @classmethod
    def _format_request_data(cls, data) -> str:
        if isinstance(data, collections.abc.Mapping):
            return "HTTP request body (multi-part form parameters):\n" + Logger._format_dict(data)
        elif inspect.isgenerator(data):
            return "HTTP request body:\n  > <generator>"
        elif isinstance(data, io.IOBase):
            return "HTTP request body:\n  > <IO stream>"
        elif isinstance(data, bytes):
            return "HTTP request body (binary, base64-ified):\n" + cls._format_binary(data)
        else:
            return "HTTP request body:\n" + data

    @staticmethod
    def _format_request_files(files) -> str:
        if isinstance(files, collections.abc.Mapping):
            infos = files.values()
        else:
            infos = [f[1] for f in files]

        return "HTTP request body (multipart files):\n%s" % (
            "\n".join(
                "- %s (%s)" % (info[0], info[2]) if len(info) >= 3 else "- %s" % info[0]
                for info in infos
            )
        )

    @classmethod
    def format_request_body(cls, request: requests.Request) -> str:
        chunks = []

        if request.json is not None:
            chunks.append(cls._format_request_json(request.json))
        if request.data:
            chunks.append(cls._format_request_data(request.data))
        if request.files:
            chunks.append(cls._format_request_files(request.files))

        return "\n".join(chunks)

    @staticmethod
    def format_response_line(resp, hint: str = None) -> str:
        content = "HTTP response"
        if hint:
            content += f" ({hint})"
        content += ":\n"
        content += "  > Status: %d\n" % resp.status_code
        content += "  > Duration: %.03fs" % resp.elapsed.total_seconds()
        return content

    @classmethod
    def format_response_headers(cls, headers) -> str:
        return "HTTP response headers:\n%s" % Logger._format_dict(headers)

    @classmethod
    def format_response_body(cls, resp: "Response") -> str:
        if not resp.content:
            return "HTTP response body:\n  > n/a"
        try:
            js = resp.json()
        except ValueError:
            if resp.apparent_encoding is not None:  # None means that it does not look like text
                return "HTTP response body:\n" + resp.text
            else:
                return "HTTP response body (binary, base64-ified):\n" + cls._format_binary(resp.content)
        else:
            return "HTTP response body (JSON):\n" + (cls._format_json(js))

    def _log_body(self, formatted_body, description):
        if self.max_inlined_body_size is not None and len(formatted_body) > self.max_inlined_body_size:
            lcc.save_attachment_content(formatted_body, "body", description)
        else:
            lcc.log_info(formatted_body)

    def log_request(self, request: requests.Request, prepared_request: requests.PreparedRequest, hint: str):
        if self.request_line_logging:
            lcc.log_info(self.format_request_line(request.method, request.url, request.params, hint))

        if self.request_headers_logging:
            lcc.log_info(self.format_request_headers(prepared_request.headers))

        if self.request_body_logging:
            formatted_body = self.format_request_body(request)
            if formatted_body:
                self._log_body(formatted_body, "HTTP request body")

    def log_response(self, resp: requests.Response, hint: str):
        if self.response_code_logging:
            lcc.log_info(self.format_response_line(resp, hint))

        if self.response_headers_logging:
            lcc.log_info(self.format_response_headers(resp.headers))

        if self.response_body_logging:
            self._log_body(self.format_response_body(resp), "HTTP response body")


class Response(requests.Response):
    """
    The Response class.

    It inherits :py:class:`requests.Response` and provides extra methods that
    deal with status code verification.
    """

    def __init__(self):
        # This constructor is not called but is necessary to make the IDE happy when accessing
        # `orig_request`
        super().__init__()
        self.orig_request = requests.Request()

    @classmethod
    def cast(cls, resp: requests.Response, orig_request: requests.Request) -> "Response":
        resp.__class__ = cls
        resp.orig_request = orig_request
        return resp

    def check_status_code(self, expected: Union[Matcher, int]) -> "Response":
        """
        Check the status code using the :py:func:`lemoncheesecake.matching.check_that` function.
        """
        check_that("HTTP status code", self.status_code, is_(expected))
        return self

    def check_ok(self) -> "Response":
        """
        Check that the status code is 2xx using the :py:func:`lemoncheesecake.matching.check_that` function.
        """
        return self.check_status_code(is_2xx())

    def require_status_code(self, expected: Union[Matcher, int]) -> "Response":
        """
        Check the status code using the :py:func:`lemoncheesecake.matching.require_that` function.
        """
        require_that("HTTP status code", self.status_code, is_(expected))
        return self

    def require_ok(self) -> "Response":
        """
        Check that the status code is 2xx using the :py:func:`lemoncheesecake.matching.require_that` function.
        """
        return self.require_status_code(is_2xx())

    def assert_status_code(self, expected: Union[Matcher, int]) -> "Response":
        """
        Check the status code using the :py:func:`lemoncheesecake.matching.assert_that` function.
        """
        assert_that("HTTP status code", self.status_code, is_(expected))
        return self

    def assert_ok(self) -> "Response":
        """
        Check that the status code is 2xx using the :py:func:`lemoncheesecake.matching.assert_that` function.
        """
        return self.assert_status_code(is_2xx())

    def raise_unless_status_code(self, expected: Union[Matcher, int]) -> "Response":
        """
        Raise a :py:class:`StatusCodeMismatch` exception unless the status code expected condition is met.

        :raises: :py:class:`StatusCodeMismatch`
        """
        matcher = is_(expected)
        match_result = matcher.matches(self.status_code)
        if not match_result:
            raise StatusCodeMismatch(self, matcher, match_result)
        return self

    def raise_unless_ok(self) -> "Response":
        """
        Raise a :py:class:`StatusCodeMismatch` exception unless the status code is 2xx.

        :raises: :py:class:`StatusCodeMismatch`
        """
        return self.raise_unless_status_code(is_2xx())


class Session(requests.Session):
    """
    The Session class.

    It inherits the :py:class:`requests.Session` class to provide logging facilities for lemoncheesecake.
    The actual logging is performed through the :py:class:`Logger` instance which is associated to the session.

    The following ``requests`` methods, performing an actual HTTP request:

    - ``request()``
    - ``get()``
    - ``options()``
    - ``head()``
    - ``post()``
    - ``put()``
    - ``patch()``
    - ``delete()``

    are overridden, they all:

    - take an optional extra ``logger`` argument that is used over the session-wide ``logger`` for that call::

        session.get("/foo", logger=Logger.off())

    - return an instance of :py:class:`lemoncheesecake_requests.Response`
    """
    def __init__(self, base_url="", logger=None, hint=None):
        super().__init__()
        #: The base_url will be concatenated to the URL passed to methods such as ``get()``, ``post()`` etc..
        #: to form the complete URL (let the string empty if there is no base_url).
        self.base_url: str = base_url
        #: The logger to be used by default for the session logging,
        #: if not provided, :py:func:`Logger.on` is used.
        self.logger: Logger = logger or Logger.on()
        #: An optional string value to be logged to provide more context to the report reader.
        self.hint: Optional[str] = hint
        self._last_request = requests.Request()

    def prepare_request(self, request):
        prepared_request = super().prepare_request(request)
        self.logger.log_request(request, prepared_request, self.hint)
        self._last_request = request
        return prepared_request

    def request(self, method, url, *args, **kwargs) -> Response:
        logger = kwargs.pop("logger", self.logger)

        # set actual logger for prepare_request since it cannot be passed another way
        orig_logger = self.logger
        self.logger = logger
        try:
            resp = super().request(method, self.base_url + url, *args, **kwargs)
        finally:
            self.logger = orig_logger

        logger.log_response(resp, self.hint)

        return Response.cast(resp, self._last_request)

    def get(self, url, **kwargs) -> Response:
        return super().get(url, **kwargs)

    def options(self, url, **kwargs) -> Response:
        return super().options(url, **kwargs)

    def head(self, url, **kwargs) -> Response:
        return super().head(url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs) -> Response:
        return super().post(url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs) -> Response:
        return super().put(url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs) -> Response:
        return super().patch(url, data=data, **kwargs)

    def delete(self, url, **kwargs) -> Response:
        return super().delete(url, **kwargs)


def is_2xx() -> Matcher:
    """
    Test if the value is between 200 and 299.
    """
    return is_between(200, 299)


def is_3xx() -> Matcher:
    """
    Test if the value is between 300 and 399.
    """
    return is_between(300, 399)


def is_4xx() -> Matcher:
    """
    Test if the value is between 400 and 499.
    """

    return is_between(400, 499)


def is_5xx() -> Matcher:
    """
    Test if the value is between 500 and 599.
    """
    return is_between(500, 599)
