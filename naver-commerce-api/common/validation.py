from common.errors import ValidationError


def validate_payload(payload, required_fields, conditional_required=None):
    if not isinstance(payload, dict):
        raise ValidationError(
            "payload는 object 형식이어야 합니다.",
            errors=[
                {
                    "source": "adapter",
                    "field": "payload",
                    "message": "payload must be an object.",
                }
            ],
        )

    errors = []
    for field_path in required_fields or []:
        errors.extend(_validate_required_path(payload, field_path))

    for rule in conditional_required or []:
        errors.extend(_validate_conditional_required(payload, rule))

    if errors:
        raise ValidationError(
            "필수 요청값이 누락되었습니다.",
            errors=errors,
        )


def pick_fields(payload, field_names):
    return {
        field_name: payload[field_name]
        for field_name in field_names or []
        if field_name in payload and payload[field_name] is not None
    }


def _validate_required_path(data, field_path):
    if "[]" not in field_path:
        value = _get_path(data, field_path)
        if _is_missing(value):
            return [_missing_error(field_path)]
        return []

    list_path, child_path = field_path.split("[].", 1)
    list_value = _get_path(data, list_path)
    if not isinstance(list_value, list) or not list_value:
        return [_missing_error(list_path)]

    errors = []
    for index, item in enumerate(list_value):
        value = _get_path(item, child_path)
        if _is_missing(value):
            errors.append(_missing_error(f"{list_path}[{index}].{child_path}"))
    return errors


def _validate_conditional_required(payload, rule):
    container_path = rule.get("path")
    condition = rule.get("when") or {}
    required_fields = rule.get("required") or []

    if container_path and container_path.endswith("[]"):
        list_path = container_path[:-2]
        list_value = _get_path(payload, list_path)
        if not isinstance(list_value, list):
            return []

        errors = []
        for index, item in enumerate(list_value):
            if _matches_condition(item, condition):
                for field in required_fields:
                    if _is_missing(_get_path(item, field)):
                        errors.append(_missing_error(f"{list_path}[{index}].{field}"))
        return errors

    container = _get_path(payload, container_path) if container_path else payload
    if not isinstance(container, dict) or not _matches_condition(container, condition):
        return []

    return [
        _missing_error(field)
        for field in required_fields
        if _is_missing(_get_path(container, field))
    ]


def _matches_condition(data, condition):
    field = condition.get("field")
    expected_value = condition.get("equals")
    if not field:
        return False

    return _get_path(data, field) == expected_value


def _get_path(data, field_path):
    value = data
    for part in field_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _is_missing(value):
    return value is None or value == "" or value == []


def _missing_error(field):
    return {
        "source": "adapter",
        "field": field,
        "message": f"{field} is required.",
    }
