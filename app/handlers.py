"""Turns every error into the JSON error envelope (docs/API.md, sections 5 and 6)."""
import logging
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.envelope import ApiError, error_body

logger = logging.getLogger("listmates")

METHOD_ORDER = ["GET", "POST", "PUT", "PATCH", "DELETE"]


def _allowed_methods(request: Request) -> list[str]:
    """Every method the app accepts on this path, for the Allow header of a 405.

    Read from the OpenAPI schema, e.g. "/api/v1/lists/{list_id}" -> GET, PUT, DELETE.
    """
    methods: set[str] = set()
    for template, operations in request.app.openapi().get("paths", {}).items():
        pattern = "^" + re.sub(r"\{[^/]+\}", "[^/]+", template) + "$"
        if re.match(pattern, request.url.path):
            methods |= {method.upper() for method in operations}
    return [method for method in METHOD_ORDER if method in methods]


def _join_or(words: list[str]) -> str:
    """["GET", "PUT", "DELETE"] -> "GET, PUT or DELETE"."""
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " or " + words[-1]


def register_exception_handlers(app: FastAPI) -> None:
    """Call once in app/main.py."""

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code,
                            content=error_body(exc.code, exc.message, exc.details),
                            headers=exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return JSONResponse(status_code=404, content=error_body(
                "ROUTE_NOT_FOUND", f"There is no endpoint at {request.url.path}."))
        if exc.status_code == 405:
            allowed = _allowed_methods(request)
            return JSONResponse(
                status_code=405,
                content=error_body("METHOD_NOT_ALLOWED",
                                   f"{request.method} is not supported here. Use {_join_or(allowed)}."),
                headers={"Allow": ", ".join(allowed)})
        code = "INTERNAL_ERROR" if exc.status_code >= 500 else "VALIDATION_ERROR"
        return JSONResponse(status_code=exc.status_code, content=error_body(code, str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Our endpoints validate input themselves, so this is only a safety net.
        details = []
        for err in exc.errors():
            if err.get("type") == "json_invalid":
                return JSONResponse(status_code=400, content=error_body(
                    "INVALID_JSON", "The request body must be a valid JSON object."))
            location = [str(part) for part in err.get("loc", []) if part not in ("body", "query", "path")]
            details.append({"field": ".".join(location) or "request",
                            "message": err.get("msg", "Invalid value.")})
        return JSONResponse(status_code=400, content=error_body(
            "VALIDATION_ERROR", "The request contains invalid or missing fields.", details))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # The real error goes to the server log only, never to the client.
        logger.exception("Unexpected error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content=error_body(
            "INTERNAL_ERROR", "Something went wrong on our side. Please try again."))
