"""Structured JSON logging helper for Lambda functions."""

import json
import logging
import os


def get_logger(name: str = __name__, level: str = None) -> logging.Logger:
    """
    Return a logger configured for structured JSON output.

    Usage:
        from utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Processing order", extra={"orderId": "42"})
    """
    log_level = level or os.environ.get("LOG_LEVEL", "INFO")
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


class _JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include any extra fields passed via the `extra` parameter
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                log_entry[key] = value
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)
