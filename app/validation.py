"""Validation rules for list requests (docs/API.md, section 3).

Every check collects all problems first, then raises one VALIDATION_ERROR,
so the client can mark every wrong field at once.
"""
import json
import re

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
