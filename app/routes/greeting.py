"""GET /api/v1/greeting: an HTML page about the project, the team and the API."""
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from app import store
from app.mock_data import USERS

router = APIRouter(tags=["greeting"])

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "greeting.html"
STARTED_AT = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


@router.get("/api/v1/greeting", response_class=HTMLResponse, summary="HTML greeting page")
def greeting() -> HTMLResponse:
    html = TEMPLATE.read_text(encoding="utf-8")
    html = (html.replace("{{LIST_COUNT}}", str(store.count_lists()))
                .replace("{{USER_COUNT}}", str(len(USERS)))
                .replace("{{STARTED_AT}}", STARTED_AT))
    return HTMLResponse(html)  # sent as text/html; charset=utf-8


@router.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    """Opening http://127.0.0.1:8000 goes straight to the greeting page."""
    return RedirectResponse("/api/v1/greeting")
