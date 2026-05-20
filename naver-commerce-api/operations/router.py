from common.errors import UnsupportedOperationError
from common.logging import log_event, payload_summary
from common.response import extract_trace_id
from common.validation import validate_payload
from operations.catalog import get_operation
from operations.transforms import build_request


class OperationRouter:
    def __init__(self, settings, auth_client, api_client):
        self.settings = settings
        self.auth_client = auth_client
        self.api_client = api_client

    def execute(self, operation, payload, request_id):
        definition = get_operation(operation)
        if not definition:
            raise UnsupportedOperationError(
                "지원하지 않는 operation입니다.",
                errors=[
                    {
                        "source": "adapter",
                        "field": "operation",
                        "message": f"{operation} is not supported.",
                    }
                ],
            )

        validate_payload(
            payload,
            definition.get("required", []),
            definition.get("conditional_required", []),
        )
        log_event(
            "INFO",
            "Validated adapter request.",
            requestId=request_id,
            operation=operation,
            step="validate_request",
            payloadSummary=payload_summary(payload),
        )

        access_token = self.auth_client.get_access_token()
        log_event(
            "INFO",
            "Access token issued.",
            requestId=request_id,
            operation=operation,
            step="get_access_token",
        )

        request = build_request(self.settings.naver_api_base_url, definition, payload)
        data, status_code = self.api_client.request(access_token=access_token, **request)
        log_event(
            "INFO",
            "Naver API request completed.",
            requestId=request_id,
            operation=operation,
            step="call_naver_api",
            naverStatusCode=status_code,
            naverTraceId=extract_trace_id(data),
        )
        return data, status_code
