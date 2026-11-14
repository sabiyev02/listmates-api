"""Response envelope and API errors used by every endpoint.

Success: {"success": true, "message": ..., "data": ..., "meta": ...}
Error:   {"success": false, "error": {"code": ..., "message": ..., "details": [...]}}

The error codes are the ones in docs/API.md, section 6.
"""
from typing import Any

from fastapi.responses import JSONResponse


def success(data: Any, message: str, status_code: int = 200,
            meta: dict | None = None, headers: dict | None = None) -> JSONResponse:
    """Build a success response. `meta` is only added for paged lists."""
    body: dict[str, Any] = {"success": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def error_body(code: str, message: str, details: list | None = None) -> dict:
    """Build the error envelope. `details` is only added for validation errors."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"success": False, "error": error}


class ApiError(Exception):
    """Raise this anywhere. The handler in app/handlers.py turns it into the error envelope."""

    def __init__(self, status_code: int, code: str, message: str,
                 details: list | None = None, headers: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


# Shortcuts for each error code in docs/API.md, section 6.

def validation_error(details: list) -> ApiError:
    return ApiError(400, "VALIDATION_ERROR", "The request contains invalid or missing fields.", details)


def invalid_json() -> ApiError:
    return ApiError(400, "INVALID_JSON", "The request body must be a valid JSON object.")


def auth_required() -> ApiError:
    return ApiError(401, "AUTH_REQUIRED",
                    "Sign in first: add the header Authorization: Bearer <token>.",
                    headers={"WWW-Authenticate": "Bearer"})


def invalid_token() -> ApiError:
    return ApiError(401, "INVALID_TOKEN",
                    "The token is missing its Bearer prefix or is not valid.",
                    headers={"WWW-Authenticate": "Bearer"})


def forbidden(message: str) -> ApiError:
    return ApiError(403, "FORBIDDEN", message)


def list_not_found(list_id: str) -> ApiError:
    return ApiError(404, "LIST_NOT_FOUND", f"No list with ID {list_id} was found.")


def public_limit_reached() -> ApiError:
    return ApiError(409, "PUBLIC_LIST_LIMIT_REACHED",
                    "You already have 4 Public lists. Make one of them Network or Personal first.")
