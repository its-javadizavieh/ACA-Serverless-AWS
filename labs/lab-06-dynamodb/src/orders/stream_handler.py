"""
Lab 06 – DynamoDB Stream Consumer
Processes change events from the orders DynamoDB table stream.
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def _deserialize(dynamo_item: dict) -> dict:
    """Convert DynamoDB JSON format to plain Python dict."""
    result = {}
    for key, value in dynamo_item.items():
        if "S" in value:
            result[key] = value["S"]
        elif "N" in value:
            result[key] = float(value["N"])
        elif "BOOL" in value:
            result[key] = value["BOOL"]
        elif "NULL" in value:
            result[key] = None
        elif "L" in value:
            result[key] = [_deserialize({"v": v})["v"] for v in value["L"]]
        elif "M" in value:
            result[key] = _deserialize(value["M"])
        else:
            result[key] = str(value)
    return result


def handler(event: dict, context) -> dict:
    """Process DynamoDB Stream records with partial batch response support."""
    failures = []

    for record in event.get("Records", []):
        sequence_number = record.get("dynamodb", {}).get("SequenceNumber", "unknown")
        try:
            event_name = record["eventName"]  # INSERT, MODIFY, REMOVE
            dynamo = record.get("dynamodb", {})

            new_image = _deserialize(dynamo.get("NewImage", {}))
            old_image = _deserialize(dynamo.get("OldImage", {}))

            # Only process order metadata items
            pk = new_image.get("PK") or old_image.get("PK", "")
            sk = new_image.get("SK") or old_image.get("SK", "")
            if not pk.startswith("ORDER#") or sk != "METADATA":
                continue

            order_id = new_image.get("orderId") or old_image.get("orderId", "unknown")

            if event_name == "INSERT":
                logger.info(json.dumps({
                    "action": "order_created",
                    "orderId": order_id,
                    "status": new_image.get("status"),
                    "total": new_image.get("total"),
                }))
            elif event_name == "MODIFY":
                old_status = old_image.get("status")
                new_status = new_image.get("status")
                if old_status != new_status:
                    logger.info(json.dumps({
                        "action": "order_status_changed",
                        "orderId": order_id,
                        "from": old_status,
                        "to": new_status,
                    }))
            elif event_name == "REMOVE":
                logger.info(json.dumps({
                    "action": "order_deleted",
                    "orderId": order_id,
                }))

        except Exception as exc:
            logger.error(json.dumps({
                "action": "stream_processing_failed",
                "sequenceNumber": sequence_number,
                "error": str(exc),
            }))
            failures.append({"itemIdentifier": sequence_number})

    return {"batchItemFailures": failures}
