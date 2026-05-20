import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from common.errors import NaverTimeoutError


def request_json(method, url, headers=None, params=None, json_payload=None, timeout=20):
    request_url = _with_query(url, params)
    request_headers = headers or {}
    body = None

    if json_payload is not None:
        body = json.dumps(json_payload).encode("utf-8")
        request_headers = {
            "Content-Type": "application/json",
            **request_headers,
        }

    request = Request(
        request_url,
        data=body,
        headers=request_headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            return response.status, response_body, _decode_json(response_body)
    except HTTPError as error:
        response_body = error.read().decode("utf-8")
        return error.code, response_body, _decode_json(response_body)
    except (TimeoutError, socket.timeout, URLError) as error:
        raise NaverTimeoutError(
            "네이버 API 또는 인증 Lambda 응답 시간이 초과되었습니다.",
            errors=[
                {
                    "source": "network",
                    "message": str(error),
                }
            ],
        ) from error


def _with_query(url, params):
    clean_params = _clean_params(params)
    if not clean_params:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode(clean_params, doseq=True)}"


def _clean_params(params):
    if not params:
        return {}
    return {
        key: value
        for key, value in params.items()
        if value is not None and value != ""
    }


def _decode_json(response_body):
    if not response_body:
        return {}
    try:
        return json.loads(response_body)
    except json.JSONDecodeError:
        return {}
