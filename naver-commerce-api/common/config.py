import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    naver_auth_api_url: str
    naver_client_id: str
    naver_client_secret: str
    naver_account_type: str
    naver_account_id: str
    naver_api_base_url: str
    request_timeout_seconds: int
    log_level: str


def load_settings():
    return Settings(
        naver_auth_api_url=os.environ.get("NAVER_AUTH_API_URL", ""),
        naver_client_id=os.environ.get("NAVER_CLIENT_ID", ""),
        naver_client_secret=os.environ.get("NAVER_CLIENT_SECRET", ""),
        naver_account_type=os.environ.get("NAVER_ACCOUNT_TYPE", "SELF"),
        naver_account_id=os.environ.get("NAVER_ACCOUNT_ID", ""),
        naver_api_base_url=os.environ.get(
            "NAVER_API_BASE_URL",
            "https://api.commerce.naver.com/external",
        ).rstrip("/"),
        request_timeout_seconds=int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "20")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )


def validate_settings(settings):
    missing = []
    for field_name in (
        "naver_auth_api_url",
        "naver_client_id",
        "naver_client_secret",
        "naver_account_type",
    ):
        if not getattr(settings, field_name):
            missing.append(field_name.upper())

    if settings.naver_account_type == "SELLER" and not settings.naver_account_id:
        missing.append("NAVER_ACCOUNT_ID")

    return missing
