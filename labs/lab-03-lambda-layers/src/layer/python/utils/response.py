"""HTTP response builder helpers for Lambda Proxy integrations."""

import json
from typing import Any

_DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "X-Powered-By": "ACA-Serverless-Course",
}


def _build(status_code: int, body: Any, extra_headers: dict = None) -> dict:
    headers = {**_DEFAULT_HEADERS, **(extra_headers or {})}
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body),
    }


def ok(body: Any = None) -> dict:
    """Return HTTP 200 OK."""
    return _build(200, body if body is not None else {"message": "OK"})


def created(body: Any = None) -> dict:
    """Return HTTP 201 Created."""
    return _build(201, body if body is not None else {"message": "Created"})


def bad_request(message: str = "Bad Request") -> dict:
    """Return HTTP 400 Bad Request."""
    return _build(400, {"error": message})


def not_found(message: str = "Not Found") -> dict:
    """Return HTTP 404 Not Found."""
    return _build(404, {"error": message})


def internal_error(message: str = "Internal Server Error") -> dict:
    """Return HTTP 500 Internal Server Error."""
    return _build(500, {"error": message})
