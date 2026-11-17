"""Validation, status codes and the error envelope."""
from conftest import auth


def error(response) -> dict:
    body = response.json()
    assert body["success"] is False
    assert "data" not in body
    return body["error"]


def test_many_validation_problems_at_once(client):
    body = {
        "title": "Hi",
        "visibility": "secret",
        "ownerId": "user-b",
        "items": [{"text": "", "done": "yes"}, {"text": "Pay rent", "dueDate": "2026-02-30"}],
    }
    response = client.post("/api/v1/lists", json=body, headers=auth("a"))
    err = error(response)
    assert response.status_code == 400
    assert err["code"] == "VALIDATION_ERROR"
    assert [d["field"] for d in err["details"]] == [
        "title", "visibility", "ownerId", "items[0].text", "items[0].done", "items[1].dueDate"]


def test_wrong_types_and_lengths(client):
    body = {"title": "x" * 61, "description": 5, "items": [{"text": "ok", "repeatDaily": 1, "color": "red"}]}
    err = error(client.post("/api/v1/lists", json=body, headers=auth("a")))
    fields = [d["field"] for d in err["details"]]
    assert fields == ["title", "description", "items[0].repeatDaily", "items[0].color"]


def test_items_must_be_an_array_of_up_to_50(client):
    err = error(client.post("/api/v1/lists", json={"title": "Many", "items": "milk"}, headers=auth("a")))
    assert err["details"] == [{"field": "items", "message": "items must be an array of items."}]
    too_many = {"title": "Many", "items": [{"text": f"Task {n}"} for n in range(51)]}
    err = error(client.post("/api/v1/lists", json=too_many, headers=auth("a")))
    assert err["details"][0]["field"] == "items"


def test_broken_json(client):
    response = client.post("/api/v1/lists", content='{"title": "Gifts",',
                           headers={**auth("a"), "Content-Type": "application/json"})
    assert response.status_code == 400
    assert error(response) == {"code": "INVALID_JSON", "message": "The request body must be a valid JSON object."}


def test_body_must_be_an_object(client):
    response = client.post("/api/v1/lists", json=["not", "an", "object"], headers=auth("a"))
    assert error(response)["code"] == "INVALID_JSON"


def test_put_needs_title_and_visibility(client):
    response = client.put("/api/v1/lists/list_103", json={"description": "Only a description"}, headers=auth("a"))
    assert response.status_code == 400
    assert [d["field"] for d in error(response)["details"]] == ["title", "visibility"]


def test_badly_formed_id(client):
    response = client.get("/api/v1/lists/abc", headers=auth("a"))
    assert response.status_code == 400
    assert error(response)["details"] == [{"field": "id", "message": "List IDs look like list_101."}]


def test_bad_query_parameters(client):
    response = client.get("/api/v1/lists?page=0&perPage=200&visibility=friends", headers=auth("a"))
    assert response.status_code == 400
    assert [d["field"] for d in error(response)["details"]] == ["page", "perPage", "visibility"]


def test_fifth_public_list_conflicts(client):
    response = client.post("/api/v1/lists", json={"title": "Places to visit in Baku", "visibility": "public"},
                           headers=auth("a"))
    assert response.status_code == 409
    assert error(response)["code"] == "PUBLIC_LIST_LIMIT_REACHED"
    # Freeing a slot makes the same request work.
    client.delete("/api/v1/lists/list_105", headers=auth("a"))
    retry = client.post("/api/v1/lists", json={"title": "Places to visit in Baku", "visibility": "public"},
                        headers=auth("a"))
    assert retry.status_code == 201


def test_making_a_list_public_on_update_conflicts(client):
    response = client.put("/api/v1/lists/list_103", json={"title": "SE midterm prep", "visibility": "public"},
                          headers=auth("a"))
    assert response.status_code == 409
    # A list that is already Public can be saved again.
    same = client.put("/api/v1/lists/list_101", json={"title": "Books to read", "visibility": "public"},
                      headers=auth("a"))
    assert same.status_code == 200


def test_ownership_checked_before_body(client):
    response = client.put("/api/v1/lists/list_201", content="{broken",
                          headers={**auth("a"), "Content-Type": "application/json"})
    assert response.status_code == 404


def test_method_not_allowed(client):
    response = client.patch("/api/v1/lists/list_101", headers=auth("a"))
    assert response.status_code == 405
    assert response.headers["Allow"] == "GET, PUT, DELETE"
    assert error(response) == {"code": "METHOD_NOT_ALLOWED",
                               "message": "PATCH is not supported here. Use GET, PUT or DELETE."}
    assert client.delete("/api/v1/lists", headers=auth("a")).headers["Allow"] == "GET, POST"


def test_unknown_route(client):
    response = client.get("/api/v1/listz", headers=auth("a"))
    assert response.status_code == 404
    assert error(response)["code"] == "ROUTE_NOT_FOUND"


def test_unexpected_error_hides_details(client, monkeypatch):
    from fastapi.testclient import TestClient
    from app import store
    from app.main import app

    def broken(*args, **kwargs):
        raise RuntimeError("database password is hunter2")

    monkeypatch.setattr(store, "find_lists", broken)
    response = TestClient(app, raise_server_exceptions=False).get("/api/v1/lists", headers=auth("a"))
    assert response.status_code == 500
    assert "hunter2" not in response.text
    assert error(response)["code"] == "INTERNAL_ERROR"
