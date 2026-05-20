import json
import uuid

from clients.naver_api_client import NaverApiClient
from clients.naver_auth_client import NaverAuthClient
from common.config import load_settings, validate_settings
from common.errors import AdapterError, InvalidRequestError
from common.logging import configure_logging, log_event
from common.response import api_response, error_payload, success_payload
from operations.router import OperationRouter


def lambda_handler(event, context):
    settings = load_settings()
    configure_logging(settings.log_level)
    operation = None
    request_id = _request_id_from_context(context)

    try:
        settings_errors = validate_settings(settings)
        if settings_errors:
            raise InvalidRequestError(
                "Lambda 환경변수 설정이 누락되었습니다.",
                errors=[
                    {
                        "source": "adapter",
                        "field": field,
                        "message": f"{field} is required.",
                    }
                    for field in settings_errors
                ],
                action_hint="Lambda 환경변수를 확인하세요.",
            )

        body = _parse_body(event)
        operation = body.get("operation")
        request_id = body.get("requestId") or request_id
        payload = body.get("payload")

        if not operation or not isinstance(operation, str):
            raise InvalidRequestError(
                "operation은 필수 문자열입니다.",
                errors=[
                    {
                        "source": "adapter",
                        "field": "operation",
                        "message": "operation is required.",
                    }
                ],
            )
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise InvalidRequestError(
                "payload는 object 형식이어야 합니다.",
                errors=[
                    {
                        "source": "adapter",
                        "field": "payload",
                        "message": "payload must be an object.",
                    }
                ],
            )

        log_event(
            "INFO",
            "Adapter request received.",
            requestId=request_id,
            operation=operation,
            step="parse_request",
        )

        router = OperationRouter(
            settings,
            NaverAuthClient(settings),
            NaverApiClient(settings),
        )
        data, naver_status_code = router.execute(operation, payload, request_id)
        response = success_payload(
            operation,
            request_id,
            data,
            naver_status_code=naver_status_code,
        )
        return api_response(200, response)

    except AdapterError as error:
        log_event(
            "ERROR",
            str(error),
            requestId=request_id,
            operation=operation,
            step="build_response",
            errorCode=error.error_code,
            naverStatusCode=error.naver_status_code,
            naverTraceId=error.naver_trace_id,
        )
        return api_response(error.status_code, error_payload(operation, request_id, error))
    except Exception as error:
        log_event(
            "ERROR",
            str(error),
            requestId=request_id,
            operation=operation,
            step="build_response",
            errorCode="LAMBDA_INTERNAL_ERROR",
        )
        internal_error = AdapterError("Lambda 내부 오류가 발생했습니다.")
        return api_response(500, error_payload(operation, request_id, internal_error))


def _parse_body(event):
    if not isinstance(event, dict):
        raise InvalidRequestError("event는 object 형식이어야 합니다.")

    raw_body = event.get("body")
    if isinstance(raw_body, str):
        try:
            return json.loads(raw_body or "{}")
        except json.JSONDecodeError as error:
            raise InvalidRequestError(
                "body를 JSON으로 파싱할 수 없습니다.",
                errors=[
                    {
                        "source": "adapter",
                        "field": "body",
                        "message": str(error),
                    }
                ],
            ) from error
    if isinstance(raw_body, dict):
        return raw_body
    return event


def _request_id_from_context(context):
    aws_request_id = getattr(context, "aws_request_id", None)
    return aws_request_id or f"adapter-{uuid.uuid4()}"
