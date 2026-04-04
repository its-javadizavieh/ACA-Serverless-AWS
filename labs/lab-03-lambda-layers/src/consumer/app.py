"""
Lab 03 – Layer Consumer Function
Demonstrates using shared utilities from the ACA Utils Lambda Layer.
"""

import sys

# The layer is extracted to /opt/python; when running locally, add it to path:
sys.path.insert(0, "/opt/python")

from utils.response import ok, bad_request
from utils.logging import get_logger

logger = get_logger(__name__)


def handler(event: dict, context) -> dict:
    logger.info("Received request", extra={"event": event})

    name = event.get("name", "")
    if not name:
        logger.warning("Missing 'name' in event")
        return bad_request("Field 'name' is required")

    result = {"greeting": f"Hello, {name}!", "fromLayer": True}
    logger.info("Returning response", extra={"name": name})
    return ok(result)
