"""
Lab 07 – Send Notification Lambda
Publishes an order confirmation notification to SNS.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

_sns = boto3.client("sns")
_TOPIC_ARN = os.environ.get("TOPIC_ARN", "")


def handler(event: dict, context) -> dict:
    order_id = event.get("orderId", "unknown")
    customer_id = event.get("customerId", "unknown")
    total = event.get("total", 0)

    message = {
        "orderId": order_id,
        "customerId": customer_id,
        "total": total,
        "status": "CONFIRMED",
        "message": f"Your order #{order_id} has been confirmed!",
    }

    if _TOPIC_ARN:
        response = _sns.publish(
            TopicArn=_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f"Order #{order_id} Confirmed",
            MessageAttributes={
                "eventType": {"DataType": "String", "StringValue": "order.confirmed"}
            },
        )
        notification_id = response["MessageId"]
    else:
        notification_id = "local-test"
        logger.warning("TOPIC_ARN not set – skipping SNS publish")

    logger.info(json.dumps({
        "action": "notification_sent",
        "orderId": order_id,
        "notificationId": notification_id,
    }))

    return {"notificationId": notification_id, "channel": "SNS"}
