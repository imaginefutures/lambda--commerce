from common.errors import AuthError
from common.http_client import request_json


class NaverAuthClient:
    def __init__(self, settings):
        self.settings = settings

    def get_access_token(self):
        payload = {
            "client_id": self.settings.naver_client_id,
            "client_secret": self.settings.naver_client_secret,
            "type": self.settings.naver_account_type,
        }
        if self.settings.naver_account_type == "SELLER":
            payload["account_id"] = self.settings.naver_account_id

        status_code, response_text, data = request_json(
            "POST",
            self.settings.naver_auth_api_url,
            headers={"Content-Type": "application/json"},
            json_payload=payload,
            timeout=self.settings.request_timeout_seconds,
        )

        if status_code != 200:
            raise AuthError(
                "네이버 인증 토큰 발급에 실패했습니다.",
                errors=[
                    {
                        "source": "auth_lambda",
                        "status": status_code,
                        "message": _message_from_response(data, response_text),
                    }
                ],
                naver_status_code=status_code,
                retryable=status_code >= 500,
            )

        access_token = data.get("access_token")
        if not access_token:
            raise AuthError(
                "네이버 인증 Lambda 응답에 access_token이 없습니다.",
                errors=[
                    {
                        "source": "auth_lambda",
                        "status": status_code,
                        "message": "access_token is missing.",
                    }
                ],
                naver_status_code=status_code,
            )
        return access_token


def _message_from_response(data, response_text):
    if isinstance(data, dict):
        return data.get("message") or data.get("result") or response_text
    return response_text
