import json
from urllib.parse import urlencode

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from lemoncheesecake.matching.matcher import MatcherDescriptionTransformer
import requests


__all__ = (
    "Session", "Response", "Logger", "LemoncheesecakeRequestsException",
    "is_2xx", "is_3xx", "is_4xx", "is_5xx"
)


class LemoncheesecakeRequestsException(Exception):
    pass


class Logger:
    def __init__(self,
                 request_line_logging=True, request_headers_logging=True, request_body_logging=True,
                 response_code_logging=True, response_headers_logging=True, response_body_logging=True
                 ):
        self.request_line_logging = request_line_logging
        self.request_headers_logging = request_headers_logging
        self.request_body_logging = request_body_logging
        self.response_code_logging = response_code_logging
        self.response_headers_logging = response_headers_logging
        self.response_body_logging = response_body_logging

    @classmethod
    def on(cls):
        return cls()

    @classmethod
    def off(cls):
        return cls(
            request_line_logging=False, request_headers_logging=False, request_body_logging=False,
            response_code_logging=False, response_headers_logging=False, response_body_logging=False
        )

    @classmethod
    def no_headers(cls):
        return cls(request_headers_logging=False, response_headers_logging=False)

    @classmethod
    def no_response_body(cls):
        return cls(response_body_logging=False)

    @staticmethod
    def format_request_line(method: str, url: str, params: dict, hint: str = None) -> str:
        formatted = "HTTP request"
        if hint:
            formatted += f" ({hint})"
        formatted += f":\n  > {method} {url}"
        if params:
            formatted += "?" + urlencode(params)
        return formatted

    @staticmethod
    def _format_json(data):
        return json.dumps(data, indent=4, ensure_ascii=False)

    @staticmethod
    def _format_dict(headers) -> str:
        return "\n".join(f"- {name}: {value}" for name, value in headers.items())

    @staticmethod
    def format_request_headers(headers) -> str:
        return "HTTP request headers:\n%s" % Logger._format_dict(headers)

    @classmethod
    def _format_request_json(cls, data) -> str:
        return "HTTP request body (JSON)\n" + cls._format_json(data)

    @staticmethod
    def _format_request_data(data) -> str:
        return "HTTP request body (multipart form parameters)\n" + Logger._format_dict(data)

    @staticmethod
    def _format_request_files(files) -> str:
        return "HTTP request body (multipart files)\n%s" % (
            "\n".join("- %s (%s)" % (f[0], f[2]) for f in files.values())
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
    def format_response_body(cls, resp) -> str:
        try:
            js = resp.json()
        except ValueError:
            if resp.text:
                return "HTTP response body:\n" + resp.text
            else:
                return "HTTP response body: n/a"
        else:
            return "HTTP response body (JSON):\n" + (cls._format_json(js))

    def log_request(self, request: requests.Request, prepared_request: requests.PreparedRequest, hint: str):
        if self.request_line_logging:
            lcc.log_info(self.format_request_line(request.method, request.url, request.params, hint))

        if self.request_headers_logging:
            lcc.log_info(self.format_request_headers(prepared_request.headers))

        if self.request_body_logging:
            formatted_body = self.format_request_body(request)
            if formatted_body:
                lcc.log_info(formatted_body)

    def log_response(self, resp: requests.Response, hint: str):
        if self.response_code_logging:
            lcc.log_info(self.format_response_line(resp, hint))

        if self.response_headers_logging:
            lcc.log_info(self.format_response_headers(resp.headers))

        if self.response_body_logging:
            lcc.log_info(self.format_response_body(resp))


class Response(requests.Response):
    def __init__(self):
        super().__init__()
        self._request = requests.Request()
        self._prepared_request = requests.PreparedRequest()

    @classmethod
    def cast(cls, resp, request, prepared_request):
        resp.__class__ = cls
        resp._request = request
        resp._prepared_request = prepared_request
        return resp

    def check_status_code(self, expected):
        check_that("HTTP status code", self.status_code, is_(expected))
        return self

    def check_ok(self):
        return self.check_status_code(is_2xx())

    def require_status_code(self, expected):
        require_that("HTTP status code", self.status_code, is_(expected))
        return self

    def require_ok(self):
        return self.require_status_code(is_2xx())

    def assert_status_code(self, expected):
        assert_that("HTTP status code", self.status_code, is_(expected))
        return self

    def assert_ok(self):
        return self.assert_status_code(is_2xx())

    def raise_unless_status_code(self, expected):
        matcher = is_(expected)
        outcome = matcher.matches(self.status_code)
        if not outcome:
            raise LemoncheesecakeRequestsException(
                f"expected status code {matcher.build_description(MatcherDescriptionTransformer())}," +
                f" {outcome.description}\n\n" +
                "\n\n".join(
                    # some serializing methods can return empty data, that's why we filter them out
                    filter(bool, (
                        Logger.format_request_line(self._request.method, self._request.url, self._request.params),
                        Logger.format_request_headers(self._prepared_request.headers),
                        Logger.format_request_body(self._request),
                        Logger.format_response_line(self),
                        Logger.format_response_headers(self.headers),
                        Logger.format_response_body(self)
                    )
                ))
            )
        return self

    def raise_unless_ok(self):
        return self.raise_unless_status_code(is_2xx())


class Session(requests.Session):
    def __init__(self, base_url="", logger=None, hint=None):
        super().__init__()
        self.base_url = base_url
        self.logger = logger or Logger()
        self.hint = hint
        self._last_request = requests.Request()
        self._last_prepared_request = requests.Request()

    def prepare_request(self, request):
        prepared_request = super().prepare_request(request)
        self.logger.log_request(request, prepared_request, self.hint)
        self._last_request = request
        self._last_prepared_request = prepared_request
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

        return Response.cast(resp, self._last_request, self._last_prepared_request)

    def get(self, url, **kwargs) -> Response:
        return super().get(url, **kwargs)

    def options(self, url, **kwargs) -> Response:
        return super().options(url, **kwargs)

    def head(self, url, **kwargs):
        return super().head(url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return super().post(url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return super().put(url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return super().patch(url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return super().delete(url, **kwargs)


def is_2xx():
    return is_between(200, 299)


def is_3xx():
    return is_between(300, 399)


def is_4xx():
    return is_between(400, 499)


def is_5xx():
    return is_between(500, 599)
