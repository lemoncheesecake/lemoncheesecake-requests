import json
from urllib.parse import urlencode

import lemoncheesecake.api as lcc
import requests


__all__ = ("Session", "Logger")


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

    @staticmethod
    def _serialize_dict(headers):
        return "\n".join(f"- {name}: {value}" for name, value in headers.items())

    @staticmethod
    def _serialize_headers(headers, type):
        return "HTTP %s headers:\n%s" % (type, Logger._serialize_dict(headers))

    @staticmethod
    def _serialize_request_data(data):
        return "HTTP request body (multipart form parameters)\n" + Logger._serialize_dict(data)

    @staticmethod
    def _serialize_request_files(files):
        return "HTTP request body (multipart files)\n%s" % (
            "\n".join("%s (%s)" % (f[0], f[2]) for f in files.values())
        )

    @staticmethod
    def _serialize_request_json(data):
        return "HTTP request body (JSON):\n" + _jsonify(data)

    @staticmethod
    def _serialize_request_line(method: str, url: str, params: dict, session_nickname: str):
        serialized = f"HTTP request: {method} {url}"
        if params:
            serialized += "?" + urlencode(params)
        if session_nickname:
            serialized += f" [{session_nickname}]"
        return serialized

    @staticmethod
    def _serialize_response_line(resp):
        return "HTTP response code: %s (in %.03fs)" % (resp.status_code, resp.elapsed.total_seconds())

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

    def log_request(self, request: requests.Request, prepared_request: requests.PreparedRequest, session_nickname: str):
        if self.request_line_logging:
            lcc.log_info(self._serialize_request_line(request.method, request.url, request.params, session_nickname))

        if self.request_headers_logging:
            lcc.log_info(self._serialize_headers(prepared_request.headers, "request"))

        if self.request_body_logging:
            if request.json is not None:
                lcc.log_info(_jsonify(request.json))
            if request.data:
                lcc.log_info(self._serialize_request_data(request.data))
            if request.files:
                lcc.log_info(self._serialize_request_files(request.files))

    def log_response(self, resp: requests.Response):
        if self.response_code_logging:
            lcc.log_info(self._serialize_response_line(resp))

        if self.response_headers_logging:
            lcc.log_info(self._serialize_headers(resp.headers, "response"))

        if self.response_body_logging:
            lcc.log_info(self._serialize_response_body(resp))


class Session(requests.Session):
    def __init__(self, base_url="", logger=None, nickname=None):
        super().__init__()
        self.base_url = base_url
        self.logger = logger or Logger()
        self.nickname = nickname

    def prepare_request(self, request):
        prepared_request = super().prepare_request(request)
        self.logger.log_request(request, prepared_request, self.nickname)
        return prepared_request

    def request(self, method, url, *args, **kwargs):
        resp = super().request(method, self.base_url + url, *args, **kwargs)
        self.logger.log_response(resp)
        return resp
