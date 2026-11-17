"""Who is calling? Reads the Bearer token and returns the matching mock user.

docs/API.md, section 4.
"""
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.envelope import auth_required, invalid_token
from app.mock_data import USERS_BY_TOKEN

# auto_error=False because we send our own 401 responses.
# Declaring it still adds the "Authorize" button to Swagger at /docs.
bearer_scheme = HTTPBearer(auto_error=False,
                           description="Paste user-a-token, user-b-token or admin-token.")


def get_current_user(request: Request,
                     credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    """Use as `user: dict = Depends(get_current_user)` in an endpoint."""
    if request.headers.get("Authorization") is None:
        raise auth_required()
    if credentials is None:  # the header is there, but it is not "Bearer <token>"
        raise invalid_token()
    user = USERS_BY_TOKEN.get(credentials.credentials)
    if user is None:
        raise invalid_token()
    return user
