"""
Lab 08 – Items Lambda Handler
CRUD handler for a simple items API deployed with CDK.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(os.environ["TABLE_NAME"])

_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


def _response(status: int, body) -> dict:
    return {"statusCode": status, "headers": _HEADERS, "body": json.dumps(body)}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _list_items() -> dict:
    result = _table.scan(
        FilterExpression="begins_with(PK, :prefix) AND SK = :sk",
        ExpressionAttributeValues={":prefix": "ITEM#", ":sk": "METADATA"},
    )
    items = [
        {k: v for k, v in item.items() if k not in ("PK", "SK")}
        for item in result.get("Items", [])
    ]
    return _response(200, {"items": items, "count": len(items)})


def _create_item(body: dict) -> dict:
    name = (body or {}).get("name", "").strip()
    price = float((body or {}).get("price", 0.0))
    if not name:
        return _response(400, {"error": "'name' is required"})

    item_id = str(uuid.uuid4())
    now = _now()
    item = {
        "PK": f"ITEM#{item_id}",
        "SK": "METADATA",
        "id": item_id,
        "name": name,
        "price": price,
        "createdAt": now,
        "updatedAt": now,
    }
    _table.put_item(Item=item, ConditionExpression="attribute_not_exists(PK)")
    return _response(201, {k: v for k, v in item.items() if k not in ("PK", "SK")})


def _get_item(item_id: str) -> dict:
    result = _table.get_item(Key={"PK": f"ITEM#{item_id}", "SK": "METADATA"})
    item = result.get("Item")
    if not item:
        return _response(404, {"error": "Item not found"})
    return _response(200, {k: v for k, v in item.items() if k not in ("PK", "SK")})


def _update_item(item_id: str, body: dict) -> dict:
    body = body or {}
    parts, values, names = ["updatedAt = :ts"], {":ts": _now()}, {}
    if "name" in body:
        parts.append("#n = :name")
        values[":name"] = body["name"]
        names["#n"] = "name"
    if "price" in body:
        parts.append("price = :price")
        values[":price"] = float(body["price"])
    if len(parts) == 1:
        return _response(400, {"error": "No updatable fields (name, price)"})
    try:
        result = _table.update_item(
            Key={"PK": f"ITEM#{item_id}", "SK": "METADATA"},
            UpdateExpression="SET " + ", ".join(parts),
            ConditionExpression="attribute_exists(PK)",
            ExpressionAttributeValues=values,
            ExpressionAttributeNames=names or None,
            ReturnValues="ALL_NEW",
        )
    except _dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return _response(404, {"error": "Item not found"})
    return _response(200, {k: v for k, v in result["Attributes"].items() if k not in ("PK", "SK")})


def _delete_item(item_id: str) -> dict:
    try:
        _table.delete_item(
            Key={"PK": f"ITEM#{item_id}", "SK": "METADATA"},
            ConditionExpression="attribute_exists(PK)",
        )
    except _dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return _response(404, {"error": "Item not found"})
    return _response(200, {"message": "Item deleted", "id": item_id})


def handler(event: dict, context) -> dict:
    method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
    item_id = (event.get("pathParameters") or {}).get("id")
    raw_body = event.get("body") or "{}"
    try:
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    try:
        if method == "GET" and not item_id:
            return _list_items()
        if method == "POST" and not item_id:
            return _create_item(body)
        if method == "GET" and item_id:
            return _get_item(item_id)
        if method == "PUT" and item_id:
            return _update_item(item_id, body)
        if method == "DELETE" and item_id:
            return _delete_item(item_id)
        return _response(400, {"error": f"Unknown route: {method}"})
    except Exception as exc:
        logger.exception("Unhandled error")
        return _response(500, {"error": str(exc)})
