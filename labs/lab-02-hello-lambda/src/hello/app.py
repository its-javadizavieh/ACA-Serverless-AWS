"""
Lab 02 – Hello Lambda
Demonstrates handler structure, context object usage, env vars and logging.
"""

import json
import logging
import os
import time

# ── Initialise logger and SDK clients OUTSIDE the handler (warm start reuse) ──
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# Record the module load time to demonstrate cold start initialisation
_module_loaded_at = time.time()

GREETING = os.environ.get("GREETING", "Hello")


def handler(event: dict, context) -> dict:
    """
    Main Lambda handler.

    Args:
        event   – Input payload (JSON object).
        context – Lambda runtime context object.

    Returns:
        dict with statusCode and body.
    """
    # Log request information
    logger.info(
        json.dumps({
            "action": "invocation_start",
            "requestId": context.aws_request_id,
            "functionName": context.function_name,
            "memoryLimitMB": context.memory_limit_in_mb,
        })
    )

    # Extract the name from the event payload (default to "Lambda Learner")
    name = event.get("name", "Lambda Learner")

    # Build the response body
    body = {
        "message": f"{GREETING}, {name}! 👋",
        "requestId": context.aws_request_id,
        "functionName": context.function_name,
        "functionVersion": context.function_version,
        "memoryLimitMB": context.memory_limit_in_mb,
        "remainingTimeMs": context.get_remaining_time_in_millis(),
        "moduleAgeSeconds": round(time.time() - _module_loaded_at, 3),
    }

    logger.info(json.dumps({"action": "invocation_end", "statusCode": 200}))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
