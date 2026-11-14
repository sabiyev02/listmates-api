"""ListMates API prototype (Assignment 2, Group 7).

Run with:  uvicorn app.main:app --reload
"""
from fastapi import FastAPI


app = FastAPI(
    title="ListMates API",
    version="1.0.0",
    description=(
        "Prototype REST API for ListMates, a social notes and to-do website. "
        "It uses in-memory mock data that resets whenever the server restarts. "
        "Click Authorize and paste user-a-token, user-b-token or admin-token."
    ),
)
