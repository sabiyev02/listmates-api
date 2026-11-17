"""Data access for lists.

The endpoints only talk to these functions. When we move to MongoDB later,
only this file changes.
"""
from datetime import datetime, timezone

from app.mock_data import FIRST_NEW_ID, seed_lists

_lists: dict[str, dict] = {}
_next_id = FIRST_NEW_ID


def reset() -> None:
    """Load the seed data again. Runs on startup and before every test."""
    global _lists, _next_id
    _lists = seed_lists()
    _next_id = FIRST_NEW_ID


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_lists(owner_id: str | None = None, visibility: str | None = None) -> list[dict]:
    """Lists matching the filters, oldest first. owner_id=None means every owner."""
    found = [lst for lst in _lists.values()
             if (owner_id is None or lst["ownerId"] == owner_id)
             and (visibility is None or lst["visibility"] == visibility)]
    return sorted(found, key=lambda lst: (lst["createdAt"], lst["id"]))


def get_list(list_id: str) -> dict | None:
    return _lists.get(list_id)


def create_list(owner_id: str, fields: dict) -> dict:
    """Save a new list. `fields` holds title, description, visibility and items."""
    global _next_id
    now = _now()
    new_list = {"id": f"list_{_next_id}", "ownerId": owner_id, **fields,
                "createdAt": now, "updatedAt": now}
    _next_id += 1
    _lists[new_list["id"]] = new_list
    return new_list


def replace_list(list_id: str, fields: dict) -> dict:
    """Replace a list's fields. id, ownerId and createdAt never change."""
    old = _lists[list_id]
    updated = {"id": old["id"], "ownerId": old["ownerId"], **fields,
               "createdAt": old["createdAt"], "updatedAt": _now()}
    _lists[list_id] = updated
    return updated


def delete_list(list_id: str) -> None:
    _lists.pop(list_id, None)


def count_public(owner_id: str, exclude_id: str | None = None) -> int:
    """How many Public lists this owner has, not counting exclude_id."""
    return sum(1 for lst in _lists.values()
               if lst["ownerId"] == owner_id and lst["visibility"] == "public"
               and lst["id"] != exclude_id)


def count_lists() -> int:
    return len(_lists)


reset()
