import json


def success_payload(operation, request_id, data, *, naver_status_code=200, naver_trace_id=None):
    return {
        "ok": True,
        "operation": operation,
        "requestId": request_id,
        "message": "요청이 성공했습니다.",
        "data": data,
        "errors": [],
        "meta": {
            "naverStatusCode": naver_status_code,
            "naverTraceId": naver_trace_id or extract_trace_id(data),
            "retryable": False,
        },
    }


def error_payload(operation, request_id, error):
    return {
        "ok": False,
        "operation": operation,
        "requestId": request_id,
        "errorCode": getattr(error, "error_code", "LAMBDA_INTERNAL_ERROR"),
        "message": str(error),
        "actionHint": getattr(error, "action_hint", "Lambda 로그의 requestId를 확인하세요."),
        "data": None,
        "errors": getattr(error, "errors", []) or [_fallback_error(error)],
        "meta": {
            "naverStatusCode": getattr(error, "naver_status_code", None),
            "naverTraceId": getattr(error, "naver_trace_id", None),
            "retryable": getattr(error, "retryable", False),
        },
    }


def api_response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
        },
        "body": json.dumps(payload, ensure_ascii=False),
    }


def extract_trace_id(data):
    if isinstance(data, dict):
        if data.get("traceId"):
            return data["traceId"]
        nested = data.get("data")
        if isinstance(nested, dict) and nested.get("traceId"):
            return nested["traceId"]
    return None


def _fallback_error(error):
    return {
        "source": "adapter",
        "message": str(error),
    }
