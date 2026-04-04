"""
Lab 05 – Warehouse Update Consumer
Processes order.created events and simulates updating warehouse inventory.
Only order.created events reach this queue (SNS filter policy).
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def _reserve_inventory(order_id: str, total: float) -> None:
    """Simulate reserving warehouse inventory for an order."""
    logger.info(json.dumps({
        "action": "reserve_inventory",
        "orderId": order_id,
        "total": total,
        "status": "reserved",
    }))
    # In production: update DynamoDB inventory records


def handler(event: dict, context) -> dict:
    """
    SQS consumer for warehouse updates.
    Only receives order.created events due to SNS filter policy.
    """
    failures = []

    for record in event.get("Records", []):
        message_id = record["messageId"]
        try:
            body = json.loads(record["body"])
            order_id = body.get("orderId", "unknown")
            total = float(body.get("total", 0.0))

            _reserve_inventory(order_id, total)

        except Exception as exc:
            logger.error(json.dumps({
                "action": "processing_failed",
                "messageId": message_id,
                "error": str(exc),
            }))
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
