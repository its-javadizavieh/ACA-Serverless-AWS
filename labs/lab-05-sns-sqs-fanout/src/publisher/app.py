"""
Lab 05 – Order Event Publisher
Publishes order events to an SNS topic with message attributes for filtering.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

_sns = boto3.client("sns")
_TOPIC_ARN = os.environ["TOPIC_ARN"]


def handler(event: dict, context) -> dict:
    """
    Publish an order event to SNS.

    Input event:
        orderId    (str) – order identifier
        eventType  (str) – e.g. 'order.created', 'order.cancelled'
        email      (str) – customer email
        total      (float, optional) – order total
    """
    order_id = event.get("orderId", "unknown")
    event_type = event.get("eventType", "order.created")
    email = event.get("email", "customer@example.com")
    total = float(event.get("total", 0.0))

    message = {
        "orderId": order_id,
        "eventType": event_type,
        "email": email,
        "total": total,
    }

    response = _sns.publish(
        TopicArn=_TOPIC_ARN,
        Message=json.dumps(message),
        Subject=f"Order Event: {event_type}",
        MessageAttributes={
            "eventType": {
                "DataType": "String",
                "StringValue": event_type,
            }
        },
    )

    message_id = response["MessageId"]
    logger.info(json.dumps({
        "action": "published",
        "messageId": message_id,
        "orderId": order_id,
        "eventType": event_type,
    }))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Event published successfully",
            "messageId": message_id,
            "orderId": order_id,
            "eventType": event_type,
        }),
    }
