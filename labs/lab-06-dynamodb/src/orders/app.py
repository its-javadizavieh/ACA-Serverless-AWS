"""
Lab 06 – Orders Manager Lambda
Demonstrates DynamoDB single-table design with customers and orders.
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

_HEADERS = {"Content-Type": "application/json"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _response(status: int, body) -> dict:
    return {"statusCode": status, "headers": _HEADERS, "body": json.dumps(body)}


# ── Customer operations ───────────────────────────────────────────────────────

def create_customer(event: dict) -> dict:
    customer_id = event.get("customerId") or f"cust-{uuid.uuid4().hex[:8]}"
    name = event.get("name", "").strip()
    email = event.get("email", "").strip()

    if not name or not email:
        return _response(400, {"error": "Fields 'name' and 'email' are required"})

    now = _now()
    item = {
        "PK": f"CUSTOMER#{customer_id}",
        "SK": "PROFILE",
        "customerId": customer_id,
        "name": name,
        "email": email,
        "createdAt": now,
        "updatedAt": now,
    }
    _table.put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(PK)",
    )
    logger.info(json.dumps({"action": "create_customer", "customerId": customer_id}))
    return _response(201, {k: v for k, v in item.items() if k not in ("PK", "SK")})


def get_customer(customer_id: str) -> dict:
    result = _table.get_item(Key={"PK": f"CUSTOMER#{customer_id}", "SK": "PROFILE"})
    item = result.get("Item")
    if not item:
        return _response(404, {"error": "Customer not found"})
    return _response(200, {k: v for k, v in item.items() if k not in ("PK", "SK")})


# ── Order operations ──────────────────────────────────────────────────────────

def create_order(event: dict) -> dict:
    customer_id = event.get("customerId", "").strip()
    total = float(event.get("total", 0.0))

    if not customer_id:
        return _response(400, {"error": "Field 'customerId' is required"})

    order_id = f"ord-{uuid.uuid4().hex[:8]}"
    now = _now()
    status = "PENDING"

    # Write two items in one transaction:
    # 1. ORDER#{orderId} METADATA – for order-level queries
    # 2. CUSTOMER#{customerId} ORDER#{orderId} – for customer-order queries
    _table.meta.client.transact_write(
        TransactItems=[
            {
                "Put": {
                    "TableName": _table.name,
                    "Item": {
                        "PK": {"S": f"ORDER#{order_id}"},
                        "SK": {"S": "METADATA"},
                        "GSI1PK": {"S": f"STATUS#{status}"},
                        "orderId": {"S": order_id},
                        "customerId": {"S": customer_id},
                        "total": {"N": str(total)},
                        "status": {"S": status},
                        "createdAt": {"S": now},
                        "updatedAt": {"S": now},
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": _table.name,
                    "Item": {
                        "PK": {"S": f"CUSTOMER#{customer_id}"},
                        "SK": {"S": f"ORDER#{order_id}"},
                        "orderId": {"S": order_id},
                        "total": {"N": str(total)},
                        "status": {"S": status},
                        "createdAt": {"S": now},
                    },
                }
            },
        ]
    )
    logger.info(json.dumps({"action": "create_order", "orderId": order_id, "customerId": customer_id}))
    return _response(201, {"orderId": order_id, "customerId": customer_id, "total": total, "status": status, "createdAt": now})


def list_customer_orders(customer_id: str) -> dict:
    """List all orders for a customer using the main table."""
    result = _table.query(
        KeyConditionExpression=(
            Key("PK").eq(f"CUSTOMER#{customer_id}") & Key("SK").begins_with("ORDER#")
        )
    )
    orders = [
        {k: v for k, v in item.items() if k not in ("PK", "SK")}
        for item in result.get("Items", [])
    ]
    return _response(200, {"customerId": customer_id, "orders": orders, "count": len(orders)})


def list_orders_by_status(status: str) -> dict:
    """List orders by status using GSI1."""
    result = _table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"STATUS#{status.upper()}"),
        ScanIndexForward=False,  # newest first
    )
    orders = [
        {k: v for k, v in item.items() if k not in ("PK", "SK", "GSI1PK")}
        for item in result.get("Items", [])
    ]
    return _response(200, {"status": status, "orders": orders, "count": len(orders)})


# ── Router ────────────────────────────────────────────────────────────────────

def handler(event: dict, context) -> dict:
    action = event.get("action", "")
    logger.info(json.dumps({"action": action, "requestId": context.aws_request_id}))

    try:
        if action == "createCustomer":
            return create_customer(event)
        if action == "getCustomer":
            return get_customer(event.get("customerId", ""))
        if action == "createOrder":
            return create_order(event)
        if action == "listCustomerOrders":
            return list_customer_orders(event.get("customerId", ""))
        if action == "listOrdersByStatus":
            return list_orders_by_status(event.get("status", "PENDING"))
        return _response(400, {"error": f"Unknown action: {action}"})
    except Exception as exc:
        logger.exception("Unhandled error")
        return _response(500, {"error": str(exc)})
