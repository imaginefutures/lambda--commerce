from common.errors import NaverApiError
from common.http_client import request_json
from common.response import extract_trace_id


class NaverApiClient:
    def __init__(self, settings):
        self.settings = settings

    def request(self, method, url, access_token, params=None, json_payload=None):
        status_code, response_text, data = request_json(
            method,
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            params=params,
            json_payload=json_payload,
            timeout=self.settings.request_timeout_seconds,
        )

        if status_code >= 400:
            raise NaverApiError(
                "네이버 API 요청이 실패했습니다.",
                errors=[
                    {
                        "source": "naver",
                        "status": status_code,
                        "message": _message_from_response(data, response_text),
                        "detail": data or response_text,
                    }
                ],
                status_code=status_code if status_code < 500 else 502,
                retryable=status_code >= 500,
                naver_status_code=status_code,
                naver_trace_id=extract_trace_id(data),
            )

        return data, status_code


def _message_from_response(data, response_text):
    if isinstance(data, dict):
        return (
            data.get("message")
            or data.get("error")
            or data.get("code")
            or response_text
        )
    return response_text
