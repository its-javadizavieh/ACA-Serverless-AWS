"""
Lab 07 – Process Payment Lambda
Simulates payment processing. Raises PaymentDeclinedException for declined cards.
Raises TransientPaymentError to demonstrate Retry behaviour.
"""

import json
import logging
import os
import random

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class PaymentDeclinedException(Exception):
    pass


class TransientPaymentError(Exception):
    pass


def handler(event: dict, context) -> dict:
    """
    Simulate payment processing.
    Set simulatePaymentFailure=true in the event to trigger PaymentDeclinedException.
    """
    order_id = event.get("orderId", "unknown")
    total = float(event.get("total", 0))
    simulate_failure = event.get("simulatePaymentFailure", False)

    logger.info(json.dumps({
        "action": "process_payment",
        "orderId": order_id,
        "total": total,
    }))

    if simulate_failure:
        logger.warning(json.dumps({"action": "payment_declined", "orderId": order_id}))
        raise PaymentDeclinedException(f"Payment declined for order {order_id}")

    # Simulate a 5% transient error rate (to demo Retry)
    if random.random() < 0.05:
        raise TransientPaymentError("Payment gateway temporarily unavailable")

    transaction_id = f"txn-{order_id}-{random.randint(1000, 9999)}"
    logger.info(json.dumps({
        "action": "payment_successful",
        "orderId": order_id,
        "transactionId": transaction_id,
        "amount": total,
    }))

    return {
        "transactionId": transaction_id,
        "status": "CHARGED",
        "amount": total,
    }
