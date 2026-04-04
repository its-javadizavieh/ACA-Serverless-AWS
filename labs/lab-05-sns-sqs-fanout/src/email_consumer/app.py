"""
Lab 05 – Email Notification Consumer
Processes order events from SQS and simulates sending email notifications.
Uses partial batch response to handle individual message failures gracefully.
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def _send_email(order_id: str, email: str, event_type: str, total: float) -> None:
    """Simulate sending an email notification (replace with SES in production)."""
    subject_map = {
        "order.created": f"Order #{order_id} confirmed!",
        "order.cancelled": f"Order #{order_id} has been cancelled",
        "order.shipped": f"Order #{order_id} is on its way!",
    }
    subject = subject_map.get(event_type, f"Update for order #{order_id}")
    logger.info(json.dumps({
        "action": "send_email",
        "to": email,
        "subject": subject,
        "orderId": order_id,
        "eventType": event_type,
        "total": total,
    }))
    # In production: ses_client.send_email(...)


def handler(event: dict, context) -> dict:
    """
    SQS consumer with partial batch response.
    Returns only the message IDs that failed processing.
    """
    failures = []

    for record in event.get("Records", []):
        message_id = record["messageId"]
        try:
            body = json.loads(record["body"])
            order_id = body.get("orderId", "unknown")
            email = body.get("email", "")
            event_type = body.get("eventType", "order.created")
            total = float(body.get("total", 0.0))

            _send_email(order_id, email, event_type, total)

        except Exception as exc:
            logger.error(json.dumps({
                "action": "processing_failed",
                "messageId": message_id,
                "error": str(exc),
            }))
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
