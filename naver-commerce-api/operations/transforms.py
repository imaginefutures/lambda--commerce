from common.validation import pick_fields


def build_request(base_url, definition, payload):
    path = _build_path(definition["path"], definition.get("path_params", []), payload)
    query = pick_fields(payload, definition.get("query", []))
    body = pick_fields(payload, definition.get("body", []))
    return {
        "method": definition["method"],
        "url": f"{base_url}{path}",
        "params": query or None,
        "json_payload": body if definition["method"] in ("POST", "PUT", "PATCH") else None,
    }


def _build_path(path_template, path_params, payload):
    path = path_template
    for param in path_params or []:
        path = path.replace(f"{{{param}}}", str(payload[param]))
    return path
