"""Shared test setup: a test client and fresh mock data before every test."""
import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app

TOKENS = {"a": "user-a-token", "b": "user-b-token", "admin": "admin-token"}


@pytest.fixture(autouse=True)
def fresh_data():
    store.reset()


@pytest.fixture
def client():
    return TestClient(app)


def auth(who: str) -> dict:
    """auth("a") -> {"Authorization": "Bearer user-a-token"}"""
    return {"Authorization": f"Bearer {TOKENS[who]}"}
