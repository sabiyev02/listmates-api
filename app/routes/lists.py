"""CRUD endpoints for the main resource, lists (docs/API.md, section 7)."""
from fastapi import APIRouter, Depends, Query, Request

from app import store
from app.auth import get_current_user
from app.envelope import success
from app.permissions import get_accessible_list, owner_filter_for
from app.validation import check_list_body, check_list_id, check_list_query, parse_json_object

router = APIRouter(prefix="/api/v1/lists", tags=["lists"])

# We read the body ourselves (after the token and ownership checks), so this
# only tells Swagger at /docs what a body looks like.
LIST_BODY_DOCS = {
    "requestBody": {
        "required": True,
        "content": {"application/json": {
            "schema": {"type": "object", "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 60},
                "description": {"type": "string", "maxLength": 300},
                "visibility": {"type": "string", "enum": ["personal", "network", "public"]},
                "items": {"type": "array", "maxItems": 50, "items": {"type": "object", "properties": {
                    "text": {"type": "string", "minLength": 1, "maxLength": 120},
                    "done": {"type": "boolean"},
                    "dueDate": {"type": "string", "format": "date", "nullable": True},
                    "repeatDaily": {"type": "boolean"}}}}}},
            "example": {"title": "Gifts for December", "description": "Ideas for the New Year.",
                        "visibility": "personal",
                        "items": [{"text": "Book for Leyla", "dueDate": "2026-12-20"}]},
        }},
    }
}


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


@router.post("", status_code=201, summary="Create a list", openapi_extra=LIST_BODY_DOCS)
async def create_list(request: Request, user: dict = Depends(get_current_user)):
    fields = check_list_body(parse_json_object(await request.body()), replacing=False)
    new_list = store.create_list(user["id"], fields)
    return success(new_list, "List created successfully.", status_code=201,
                   headers={"Location": f"/api/v1/lists/{new_list['id']}"})


@router.put("/{list_id}", summary="Replace a list", openapi_extra=LIST_BODY_DOCS)
async def replace_list(list_id: str, request: Request, user: dict = Depends(get_current_user)):
    check_list_id(list_id)
    get_accessible_list(user, list_id)
    fields = check_list_body(parse_json_object(await request.body()), replacing=True)
    return success(store.replace_list(list_id, fields), "List updated successfully.")


@router.delete("/{list_id}", summary="Delete a list")
def delete_list(list_id: str, user: dict = Depends(get_current_user)):
    check_list_id(list_id)
    get_accessible_list(user, list_id)
    store.delete_list(list_id)
    return success(None, f"List {list_id} was deleted.")
