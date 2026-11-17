"""Is this user allowed? Ownership and role rules (docs/API.md, section 4)."""
from app import store
from app.envelope import list_not_found


def is_admin(user: dict) -> bool:
    return user["role"] == "admin"


def get_accessible_list(user: dict, list_id: str) -> dict:
    """Return the list if the user owns it or is an admin.

    Other users' lists answer 404, exactly like a missing list, so nobody can
    find out which IDs exist ("Our choice: 404 instead of 403" in docs/API.md).
    """
    found = store.get_list(list_id)
    if found is None or (not is_admin(user) and found["ownerId"] != user["id"]):
        raise list_not_found(list_id)
    return found
