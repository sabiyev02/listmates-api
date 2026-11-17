"""Validation rules for list requests (docs/API.md, section 3).

Every check collects all problems first, then raises one VALIDATION_ERROR,
so the client can mark every wrong field at once.
"""
import json
import re
from datetime import date

from app.envelope import invalid_json, validation_error

VISIBILITIES = ("personal", "network", "public")
LIST_ID_PATTERN = re.compile(r"^list_[0-9]+$")


def check_list_id(list_id: str) -> None:
    if not LIST_ID_PATTERN.match(list_id):
        raise validation_error([{"field": "id", "message": "List IDs look like list_101."}])


def parse_json_object(raw: bytes) -> dict:
    """Turn the raw request body into a dict, or raise INVALID_JSON."""
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise invalid_json() from None
    if not isinstance(body, dict):
        raise invalid_json()
    return body


def _whole_number(value: str | None, default: int) -> int | None:
    if value is None:
        return default
    return int(value) if re.fullmatch(r"[0-9]+", value) else None


def check_list_query(page: str | None, per_page: str | None,
                     visibility: str | None) -> tuple[int, int, str | None]:
    """Check the query parameters of GET /lists. Returns (page, perPage, visibility)."""
    details = []
    page_number = _whole_number(page, default=1)
    if page_number is None or page_number < 1:
        details.append({"field": "page", "message": "Page must be a whole number of 1 or more."})
    per_page_number = _whole_number(per_page, default=10)
    if per_page_number is None or not 1 <= per_page_number <= 50:
        details.append({"field": "perPage", "message": "perPage must be between 1 and 50."})
    if visibility is not None and visibility not in VISIBILITIES:
        details.append({"field": "visibility", "message": "Visibility must be personal, network or public."})
    if details:
        raise validation_error(details)
    return page_number, per_page_number, visibility


READ_ONLY_FIELDS = ("id", "ownerId", "createdAt", "updatedAt")
LIST_FIELDS = ("title", "description", "visibility", "items")
ITEM_FIELDS = ("text", "done", "dueDate", "repeatDaily")
MAX_ITEMS = 50
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _is_real_date(value) -> bool:
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _check_item(item, prefix: str, details: list) -> dict | None:
    """Check one task in `items`. Adds problems to `details`; returns the clean item."""
    if not isinstance(item, dict):
        details.append({"field": prefix, "message": "Each item must be an object with a text field."})
        return None
    problems_before = len(details)

    text = item.get("text")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 120:
        details.append({"field": f"{prefix}.text", "message": "Item text must contain 1 to 120 characters."})
    done = item.get("done", False)
    if type(done) is not bool:
        details.append({"field": f"{prefix}.done", "message": "done must be true or false."})
    due_date = item.get("dueDate")
    if due_date is not None and not _is_real_date(due_date):
        details.append({"field": f"{prefix}.dueDate",
                        "message": "dueDate must be a real date in YYYY-MM-DD format."})
    repeat_daily = item.get("repeatDaily", False)
    if type(repeat_daily) is not bool:
        details.append({"field": f"{prefix}.repeatDaily", "message": "repeatDaily must be true or false."})
    for field in item:
        if field not in ITEM_FIELDS:
            details.append({"field": f"{prefix}.{field}", "message": "Unknown field."})

    if len(details) > problems_before:
        return None
    return {"text": text.strip(), "done": done, "dueDate": due_date, "repeatDaily": repeat_daily}


def check_list_body(body: dict, replacing: bool) -> dict:
    """Check a POST body (replacing=False) or a PUT body (replacing=True).

    Returns clean fields (title, description, visibility, items),
    or raises VALIDATION_ERROR listing every problem.
    """
    details: list[dict] = []

    title = body.get("title")
    if not isinstance(title, str) or len(title.strip()) < 3:
        details.append({"field": "title", "message": "Title is required and must contain at least 3 characters."})
    elif len(title.strip()) > 60:
        details.append({"field": "title", "message": "Title must be at most 60 characters."})

    description = body.get("description")
    if description is None:
        description = ""
    if not isinstance(description, str) or len(description.strip()) > 300:
        details.append({"field": "description", "message": "Description must be text of at most 300 characters."})

    if "visibility" in body:
        visibility = body["visibility"]
        if visibility not in VISIBILITIES:
            details.append({"field": "visibility", "message": "Visibility must be personal, network or public."})
    elif replacing:
        visibility = None
        details.append({"field": "visibility", "message": "Visibility is required when replacing a list."})
    else:
        visibility = "personal"

    for field in body:
        if field in READ_ONLY_FIELDS:
            details.append({"field": field, "message": "This field is set by the server."})
        elif field not in LIST_FIELDS:
            details.append({"field": field, "message": "Unknown field."})

    items = body.get("items")
    if items is None:
        items = []
    clean_items = []
    if not isinstance(items, list):
        details.append({"field": "items", "message": "items must be an array of items."})
    elif len(items) > MAX_ITEMS:
        details.append({"field": "items", "message": f"A list can have at most {MAX_ITEMS} items."})
    else:
        for index, item in enumerate(items):
            clean = _check_item(item, f"items[{index}]", details)
            if clean is not None:
                clean_items.append(clean)

    if details:
        raise validation_error(details)
    return {"title": title.strip(), "description": description.strip(),
            "visibility": visibility, "items": clean_items}
