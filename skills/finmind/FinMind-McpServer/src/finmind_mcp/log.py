"""日誌模組 — 使用 structlog 提供結構化日誌。"""

from __future__ import annotations

import logging

import structlog

from finmind_mcp.config import get_settings


def setup_logging() -> None:
    """初始化 structlog 日誌設定。"""
    settings = get_settings()

    # 設定 Python 標準日誌等級
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            # 遮蔽敏感資訊
            _redact_secrets,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _redact_secrets(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """遮蔽日誌中的敏感資訊（Token、密碼等）。"""
    sensitive_keys = {"token", "password", "secret", "api_key", "FINMIND_TOKEN"}
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in sensitive_keys):
            event_dict[key] = "***REDACTED***"
    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """取得具名日誌實例。"""
    return structlog.get_logger(name)
