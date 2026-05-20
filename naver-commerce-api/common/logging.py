import json
import logging


SENSITIVE_KEYS = {
    "access_token",
    "authorization",
    "client_secret",
    "client_secret_sign",
    "token",
    "tel1",
    "tel2",
    "phone",
    "detailedAddress",
    "shippingAddress",
}


def configure_logging(level_name):
    logging.getLogger().setLevel(getattr(logging, level_name.upper(), logging.INFO))


def log_event(level, message, **fields):
    payload = {
        "level": level.upper(),
        "message": message,
        **_mask(fields),
    }
    logging.log(
        getattr(logging, level.upper(), logging.INFO),
        json.dumps(payload, ensure_ascii=False),
    )


def payload_summary(payload):
    if not isinstance(payload, dict):
        return {}

    summary = {}
    if "productOrderIds" in payload and isinstance(payload["productOrderIds"], list):
        summary["productOrderIdCount"] = len(payload["productOrderIds"])
    if "productOrderId" in payload:
        summary["productOrderId"] = payload["productOrderId"]
    if "dispatchProductOrders" in payload and isinstance(payload["dispatchProductOrders"], list):
        summary["dispatchProductOrderCount"] = len(payload["dispatchProductOrders"])
        first = payload["dispatchProductOrders"][0] if payload["dispatchProductOrders"] else {}
        if isinstance(first, dict):
            summary["deliveryCompanyCode"] = first.get("deliveryCompanyCode")
    return summary


def _mask(value):
    if isinstance(value, dict):
        masked = {}
        for key, child in value.items():
            if key in SENSITIVE_KEYS or key.lower() in SENSITIVE_KEYS:
                masked[key] = "***"
            else:
                masked[key] = _mask(child)
        return masked
    if isinstance(value, list):
        return [_mask(item) for item in value]
    return value
