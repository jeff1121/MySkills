"""
Structured logging configuration using structlog.

Provides JSON-formatted logs with automatic secret redaction for sensitive fields.
"""

import logging
import structlog
from typing import Any, Dict, Optional


# Sensitive field patterns to redact
SENSITIVE_KEYS = {"password", "api_key", "secret", "token"}


def _redact_secrets(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processor that redacts sensitive values from log events.

    Masks values for keys containing: password, api_key, secret, token.
    """
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            event_dict[key] = "***REDACTED***"
    return event_dict


def setup_logging(json_output: bool = True) -> None:
    """
    Configure structlog for structured logging.

    Args:
        json_output: If True, use JSONRenderer for production logs.
                     If False, use ConsoleRenderer for dev logs.
    """
    # Standard shared processors
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _redact_secrets,
    ]

    # Add renderer based on output format
    if json_output:
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=None,  # structlog handles output
        level=logging.INFO,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Logger name, typically __name__.

    Returns:
        A bound logger instance with automatic context tracking.
    """
    return structlog.get_logger(name)


# Initialize logging on module import
setup_logging(json_output=True)
