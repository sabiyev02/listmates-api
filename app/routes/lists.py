"""CRUD endpoints for the main resource, lists (docs/API.md, section 7)."""
from fastapi import APIRouter, Depends, Query

from app import store
from app.auth import get_current_user
from app.envelope import success
from app.permissions import get_accessible_list, owner_filter_for
from app.validation import check_list_id, check_list_query

router = APIRouter(prefix="/api/v1/lists", tags=["lists"])


@router.get("", summary="List your lists (all lists for admin)")
def list_lists(
    user: dict = Depends(get_current_user),
    page: str | None = Query(None, description="Page number, 1 or more. Default 1."),
    per_page: str | None = Query(None, alias="perPage", description="Lists per page, 1-50. Default 10."),
    visibility: str | None = Query(None, description="personal, network or public"),
    owner_id: str | None = Query(None, alias="ownerId", description="Admin only: show this user's lists"),
):
    page_number, per_page_number, visibility = check_list_query(page, per_page, visibility)
    owner = owner_filter_for(user, owner_id)
    found = store.find_lists(owner_id=owner, visibility=visibility)
    start = (page_number - 1) * per_page_number
    noun = "list" if len(found) == 1 else "lists"
    return success(found[start:start + per_page_number], f"Found {len(found)} {noun}.",
                   meta={"total": len(found), "page": page_number, "perPage": per_page_number})


@router.get("/{list_id}", summary="Get one list")
def get_one_list(list_id: str, user: dict = Depends(get_current_user)):
    check_list_id(list_id)
    return success(get_accessible_list(user, list_id), "List found.")
