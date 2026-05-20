class AdapterError(Exception):
    error_code = "LAMBDA_INTERNAL_ERROR"
    status_code = 500
    retryable = False
    action_hint = "Lambda 로그의 requestId를 확인하세요."

    def __init__(
        self,
        message,
        *,
        errors=None,
        status_code=None,
        retryable=None,
        action_hint=None,
        naver_status_code=None,
        naver_trace_id=None,
        detail=None,
    ):
        super().__init__(message)
        self.message = message
        self.errors = errors or []
        self.status_code = status_code or self.status_code
        self.retryable = self.retryable if retryable is None else retryable
        self.action_hint = action_hint or self.action_hint
        self.naver_status_code = naver_status_code
        self.naver_trace_id = naver_trace_id
        self.detail = detail


class InvalidRequestError(AdapterError):
    error_code = "INVALID_REQUEST"
    status_code = 400
    action_hint = "n8n HTTP Request 노드의 body JSON 형식을 확인하세요."


class UnsupportedOperationError(AdapterError):
    error_code = "UNSUPPORTED_OPERATION"
    status_code = 400
    action_hint = "operation 이름 오타 또는 미구현 operation 여부를 확인하세요."


class ValidationError(AdapterError):
    error_code = "VALIDATION_ERROR"
    status_code = 400
    action_hint = "n8n HTTP Request 노드의 payload 값을 확인하세요."


class AuthError(AdapterError):
    error_code = "AUTH_ERROR"
    status_code = 502
    action_hint = "인증 Lambda URL, client ID/secret 환경변수, 인증 Lambda 로그를 확인하세요."


class NaverApiError(AdapterError):
    error_code = "NAVER_API_ERROR"
    status_code = 502
    action_hint = "네이버 응답 메시지와 요청 payload 값을 확인하세요."


class NaverTimeoutError(AdapterError):
    error_code = "NAVER_TIMEOUT"
    status_code = 504
    retryable = True
    action_hint = "잠시 후 같은 요청을 재시도하세요."
