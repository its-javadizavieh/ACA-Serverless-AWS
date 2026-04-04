"""
Lab 04 – Todos CRUD API
Single Lambda function handling all HTTP methods for /todos and /todos/{id}.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# Initialise DynamoDB outside handler for connection reuse
_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(os.environ["TABLE_NAME"])

_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


# ── Response helpers ──────────────────────────────────────────────────────────

def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": _HEADERS,
        "body": json.dumps(body),
    }


def _ok(body):
    return _response(200, body)


def _created(body):
    return _response(201, body)


def _bad_request(message: str):
    return _response(400, {"error": message})


def _not_found(message: str = "Todo not found"):
    return _response(404, {"error": message})


def _internal_error(message: str = "Internal server error"):
    return _response(500, {"error": message})


# ── CRUD operations ───────────────────────────────────────────────────────────

def _list_todos() -> dict:
    """List all todo items."""
    result = _table.scan(
        FilterExpression="begins_with(PK, :prefix) AND SK = :sk",
        ExpressionAttributeValues={":prefix": "TODO#", ":sk": "METADATA"},
    )
    todos = [_format_item(item) for item in result.get("Items", [])]
    todos.sort(key=lambda x: x["createdAt"], reverse=True)
    return _ok({"todos": todos, "count": len(todos)})


def _create_todo(body: dict) -> dict:
    """Create a new todo item."""
    title = (body or {}).get("title", "").strip()
    if not title:
        return _bad_request("Field 'title' is required")

    todo_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "PK": f"TODO#{todo_id}",
        "SK": "METADATA",
        "id": todo_id,
        "title": title,
        "done": bool(body.get("done", False)),
        "createdAt": now,
        "updatedAt": now,
    }
    _table.put_item(Item=item)
    logger.info(json.dumps({"action": "create_todo", "todoId": todo_id}))
    return _created(_format_item(item))


def _get_todo(todo_id: str) -> dict:
    """Get a single todo by ID."""
    result = _table.get_item(Key={"PK": f"TODO#{todo_id}", "SK": "METADATA"})
    item = result.get("Item")
    if not item:
        return _not_found()
    return _ok(_format_item(item))


def _update_todo(todo_id: str, body: dict) -> dict:
    """Update a todo item."""
    body = body or {}
    # Build update expression dynamically from provided fields
    update_parts = ["updatedAt = :updatedAt"]
    values = {":updatedAt": datetime.now(timezone.utc).isoformat()}

    if "title" in body:
        title = body["title"].strip()
        if not title:
            return _bad_request("'title' cannot be empty")
        update_parts.append("title = :title")
        values[":title"] = title

    if "done" in body:
        update_parts.append("#done = :done")
        values[":done"] = bool(body["done"])

    if len(update_parts) == 1:
        return _bad_request("No updatable fields provided (title, done)")

    expression_names = {"#done": "done"} if "done" in body else {}

    try:
        result = _table.update_item(
            Key={"PK": f"TODO#{todo_id}", "SK": "METADATA"},
            UpdateExpression="SET " + ", ".join(update_parts),
            ConditionExpression="attribute_exists(PK)",
            ExpressionAttributeValues=values,
            ExpressionAttributeNames=expression_names or None,
            ReturnValues="ALL_NEW",
        )
    except _dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return _not_found()

    logger.info(json.dumps({"action": "update_todo", "todoId": todo_id}))
    return _ok(_format_item(result["Attributes"]))


def _delete_todo(todo_id: str) -> dict:
    """Delete a todo item."""
    try:
        _table.delete_item(
            Key={"PK": f"TODO#{todo_id}", "SK": "METADATA"},
            ConditionExpression="attribute_exists(PK)",
        )
    except _dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return _not_found()

    logger.info(json.dumps({"action": "delete_todo", "todoId": todo_id}))
    return _ok({"message": "Todo deleted", "id": todo_id})


def _format_item(item: dict) -> dict:
    """Remove DynamoDB-internal keys from an item."""
    return {k: v for k, v in item.items() if k not in ("PK", "SK")}


# ── Router ────────────────────────────────────────────────────────────────────

def handler(event: dict, context) -> dict:
    """Route HTTP method + path to the appropriate CRUD function."""
    method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
    path_params = event.get("pathParameters") or {}
    todo_id = path_params.get("id")

    raw_body = event.get("body") or "{}"
    try:
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except json.JSONDecodeError:
        return _bad_request("Request body is not valid JSON")

    logger.info(json.dumps({
        "action": "request",
        "method": method,
        "todoId": todo_id,
        "requestId": context.aws_request_id,
    }))

    try:
        if method == "GET" and not todo_id:
            return _list_todos()
        if method == "POST" and not todo_id:
            return _create_todo(body)
        if method == "GET" and todo_id:
            return _get_todo(todo_id)
        if method == "PUT" and todo_id:
            return _update_todo(todo_id, body)
        if method == "DELETE" and todo_id:
            return _delete_todo(todo_id)
        return _bad_request(f"Unknown route: {method} {event.get('rawPath')}")
    except Exception as exc:
        logger.exception("Unhandled error")
        return _internal_error(str(exc))
