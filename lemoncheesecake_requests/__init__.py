import json
from urllib.parse import urlencode

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
import requests


__all__ = (
    "Session", "Response", "Logger", "is_2xx", "is_3xx", "is_4xx", "is_5xx"
)


def _jsonify(data):
    return json.dumps(data, indent=4, ensure_ascii=False)


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
    def _serialize_request_line(method: str, url: str, params: dict, hint: str = None):
        serialized = f"HTTP request: {method} {url}"
        if params:
            serialized += "?" + urlencode(params)
        if hint:
            serialized += f" [{hint}]"
        return serialized

    @staticmethod
    def _serialize_dict(headers):
        return "\n".join(f"- {name}: {value}" for name, value in headers.items())

    @staticmethod
    def _serialize_request_headers(headers):
        return "HTTP request headers:\n%s" % Logger._serialize_dict(headers)

    @classmethod
    def _serialize_request_json(cls, data):
        return "HTTP request body (JSON)\n" + _jsonify(data)

    @staticmethod
    def _serialize_request_data(data):
        return "HTTP request body (multipart form parameters)\n" + Logger._serialize_dict(data)

    @staticmethod
    def _serialize_request_files(files):
        return "HTTP request body (multipart files)\n%s" % (
            "\n".join("%s (%s)" % (f[0], f[2]) for f in files.values())
        )

    @staticmethod
    def _serialize_response_line(resp):
        return "HTTP response code: %s (in %.03fs)" % (resp.status_code, resp.elapsed.total_seconds())

    @classmethod
    def _serialize_response_headers(cls, headers):
        return "HTTP response headers:\n%s" % Logger._serialize_dict(headers)

    @staticmethod
    def _serialize_response_body(resp):
        try:
            js = resp.json()
        except ValueError:
            if resp.text:
                return "HTTP response body:\n" + resp.text
            else:
                return "HTTP response body: n/a"
        else:
            return "HTTP response body (JSON):\n" + (_jsonify(js))

    @classmethod
    def _serialize_request_error(cls,
                                 request: requests.Request, prepared_request: requests.PreparedRequest,
                                 resp: requests.Response):
        chunks = [
            "HTTP request failure:",
            cls._serialize_request_line(request.method, request.url, request.params),
            cls._serialize_request_headers(prepared_request.headers)
        ]

        if request.json is not None:
            chunks.append(cls._serialize_request_line(request.json))
        if request.data:
            chunks.append(cls._serialize_request_data(request.data))
        if request.files:
            chunks.append(cls._serialize_request_files(request.files))

        chunks.append(cls._serialize_response_line(resp))
        chunks.append(cls._serialize_response_headers(resp.headers))
        chunks.append(cls._serialize_response_body(resp))

        return "\n".join(chunks)

    def log_request(self, request: requests.Request, prepared_request: requests.PreparedRequest, hint: str):
        if self.request_line_logging:
            lcc.log_info(self._serialize_request_line(request.method, request.url, request.params, hint))

        if self.request_headers_logging:
            lcc.log_info(self._serialize_request_headers(prepared_request.headers))

        if self.request_body_logging:
            if request.json is not None:
                lcc.log_info(self._serialize_request_line(request.json))
            if request.data:
                lcc.log_info(self._serialize_request_data(request.data))
            if request.files:
                lcc.log_info(self._serialize_request_files(request.files))

    def log_response(self, resp: requests.Response):
        if self.response_code_logging:
            lcc.log_info(self._serialize_response_line(resp))

        if self.response_headers_logging:
            lcc.log_info(self._serialize_response_headers(resp.headers))

        if self.response_body_logging:
            lcc.log_info(self._serialize_response_body(resp))


class Response(requests.Response):
    def __init__(self):
        super().__init__()
        self._request = requests.Request()
        self._prepared_request = requests.PreparedRequest()

    @classmethod
    def wrap(cls, resp, request, prepared_request):
        resp.__class__ = cls
        resp._request = request
        resp._prepared_request = prepared_request
        return resp

    def check_status_code(self, expected):
        check_that("HTTP status code", self.status_code, is_(expected))
        return self

    def require_status_code(self, expected):
        require_that("HTTP status code", self.status_code, is_(expected))
        return self

    def assert_status_code(self, expected):
        assert_that("HTTP status code", self.status_code, is_(expected))
        return self

    def raise_unless_status_code(self, expected):
        matcher = is_(expected)
        if not matcher.matches(self.status_code):
            raise Exception(
                Logger._serialize_request_error(self._request, self._prepared_request, self)
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

        logger.log_response(resp)

        return Response.wrap(resp, self._last_request, self._last_prepared_request)

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
