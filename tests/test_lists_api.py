"""CRUD, authentication, authorization and the greeting page."""
from conftest import auth

NEW_LIST = {
    "title": "Gifts for December",
    "description": "Ideas for the New Year.",
    "visibility": "personal",
    "items": [{"text": "Book for Leyla", "dueDate": "2026-12-20"}, {"text": "Scarf for Mom"}],
}


# --- CRUD as the owner -----------------------------------------------------

def test_user_a_lists_only_her_lists(client):
    response = client.get("/api/v1/lists", headers=auth("a"))
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"] == {"total": 6, "page": 1, "perPage": 10}
    assert {lst["ownerId"] for lst in body["data"]} == {"user-a"}


def test_paging_and_visibility_filter(client):
    body = client.get("/api/v1/lists?page=1&perPage=2", headers=auth("a")).json()
    assert [lst["id"] for lst in body["data"]] == ["list_101", "list_102"]
    public = client.get("/api/v1/lists?visibility=public", headers=auth("a")).json()
    assert public["meta"]["total"] == 4


def test_get_own_list(client):
    response = client.get("/api/v1/lists/list_101", headers=auth("a"))
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Books to read"


def test_create_list(client):
    response = client.post("/api/v1/lists", json=NEW_LIST, headers=auth("a"))
    data = response.json()["data"]
    assert response.status_code == 201
    assert response.headers["Location"] == "/api/v1/lists/list_301"
    assert data["id"] == "list_301"
    assert data["ownerId"] == "user-a"
    assert data["items"][1] == {"text": "Scarf for Mom", "done": False, "dueDate": None, "repeatDaily": False}


def test_create_uses_defaults(client):
    data = client.post("/api/v1/lists", json={"title": "  Plain list  "}, headers=auth("b")).json()["data"]
    assert data["title"] == "Plain list"
    assert data["visibility"] == "personal"
    assert data["description"] == ""
    assert data["items"] == []


def test_update_list(client):
    body = {"title": "SE midterm prep", "visibility": "network",
            "items": [{"text": "Re-read Pressman ch. 1-4 notes", "done": True}]}
    response = client.put("/api/v1/lists/list_103", json=body, headers=auth("a"))
    data = response.json()["data"]
    assert response.status_code == 200
    assert data["visibility"] == "network"
    assert data["createdAt"] == "2026-11-04T16:45:00Z"
    assert data["description"] == ""  # PUT replaces the whole list


def test_delete_list(client):
    response = client.delete("/api/v1/lists/list_105", headers=auth("a"))
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "List list_105 was deleted.", "data": None}
    assert client.get("/api/v1/lists/list_105", headers=auth("a")).status_code == 404
    assert client.delete("/api/v1/lists/list_105", headers=auth("a")).status_code == 404


# --- Authentication ----------------------------------------------------------

def test_missing_token(client):
    response = client.get("/api/v1/lists")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_invalid_token(client):
    for header in ("Bearer wrong-token", "user-a-token", "Basic abc"):
        response = client.get("/api/v1/lists", headers={"Authorization": header})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_token_checked_before_anything_else(client):
    response = client.post("/api/v1/lists", content="{broken")
    assert response.status_code == 401


# --- Authorization -----------------------------------------------------------

def test_user_a_cannot_touch_user_b_lists(client):
    assert client.get("/api/v1/lists/list_201", headers=auth("a")).status_code == 404
    assert client.put("/api/v1/lists/list_201", json={"title": "Mine now", "visibility": "public"},
                      headers=auth("a")).status_code == 404
    assert client.delete("/api/v1/lists/list_201", headers=auth("a")).status_code == 404


def test_user_b_cannot_touch_user_a_lists(client):
    for response in (client.get("/api/v1/lists/list_101", headers=auth("b")),
                     client.put("/api/v1/lists/list_101", json={"title": "Mine now", "visibility": "public"},
                                headers=auth("b")),
                     client.delete("/api/v1/lists/list_101", headers=auth("b"))):
        assert response.status_code == 404
        assert response.json()["error"] == {"code": "LIST_NOT_FOUND",
                                            "message": "No list with ID list_101 was found."}


def test_other_users_list_looks_like_a_missing_list(client):
    other = client.get("/api/v1/lists/list_201", headers=auth("a")).json()["error"]["code"]
    missing = client.get("/api/v1/lists/list_999", headers=auth("a")).json()["error"]["code"]
    assert other == missing == "LIST_NOT_FOUND"


def test_regular_user_cannot_filter_by_another_owner(client):
    response = client.get("/api/v1/lists?ownerId=user-b", headers=auth("a"))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert client.get("/api/v1/lists?ownerId=user-a", headers=auth("a")).status_code == 200


def test_admin_can_do_everything(client):
    assert client.get("/api/v1/lists", headers=auth("admin")).json()["meta"]["total"] == 9
    assert client.get("/api/v1/lists?ownerId=user-b", headers=auth("admin")).json()["meta"]["total"] == 3
    assert client.get("/api/v1/lists/list_201", headers=auth("admin")).status_code == 200
    updated = client.put("/api/v1/lists/list_201", json={"title": "Books I loved", "visibility": "network"},
                         headers=auth("admin"))
    assert updated.status_code == 200
    assert updated.json()["data"]["ownerId"] == "user-b"
    assert client.delete("/api/v1/lists/list_203", headers=auth("admin")).status_code == 200


# --- Greeting page -----------------------------------------------------------

def test_greeting_is_html(client):
    response = client.get("/api/v1/greeting")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "ListMates" in response.text
    assert "API is running" in response.text
    assert "9 lists" in response.text
    assert "{{" not in response.text


def test_home_redirects_to_greeting(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/api/v1/greeting"
