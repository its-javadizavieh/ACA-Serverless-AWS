"""
Lab 07 – Validate Order Lambda
Validates incoming order data. Raises ValidationError for invalid orders.
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class ValidationError(Exception):
    pass


def handler(event: dict, context) -> dict:
    """
    Validate order input.
    Raises ValidationError if validation fails (caught by Step Functions Catch).
    """
    order_id = event.get("orderId", "")
    items = event.get("items", [])
    customer_id = event.get("customerId", "")
    total = event.get("total", 0)

    errors = []
    if not order_id:
        errors.append("orderId is required")
    if not customer_id:
        errors.append("customerId is required")
    if not items:
        errors.append("items cannot be empty")
    if total <= 0:
        errors.append("total must be greater than 0")

    if errors:
        logger.error(json.dumps({"action": "validation_failed", "errors": errors}))
        raise ValidationError(f"Validation failed: {'; '.join(errors)}")

    logger.info(json.dumps({
        "action": "validation_passed",
        "orderId": order_id,
        "itemCount": len(items),
        "total": total,
    }))

    return {"valid": True, "orderId": order_id, "itemCount": len(items)}
