"""Logging configuration for the trading bot."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

LOGGER_NAME: Final[str] = "trading_bot"
DEFAULT_LOG_LEVEL: Final[int] = logging.INFO
DEFAULT_LOG_FILE: Final[Path] = (
    Path(__file__).resolve().parent.parent / "logs" / "trading_bot.log"
)
MAX_LOG_BYTES: Final[int] = 5 * 1024 * 1024
BACKUP_COUNT: Final[int] = 5
LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def _build_file_handler(log_file: Path) -> RotatingFileHandler:
    """Create the rotating file handler used by the application."""

    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(DEFAULT_LOG_LEVEL)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def _build_stream_handler() -> logging.Handler:
    """Create the console handler for operational visibility."""

    handler = logging.StreamHandler()
    handler.setLevel(DEFAULT_LOG_LEVEL)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def get_logger(
    name: str | None = None,
    *,
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Path = DEFAULT_LOG_FILE,
) -> logging.Logger:
    """Return a configured logger for the trading bot.

    The configuration is applied once per logger instance and is safe to call
    repeatedly from different modules.
    """

    logger_name = LOGGER_NAME if not name else f"{LOGGER_NAME}.{name}"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    logger.addHandler(_build_file_handler(log_file))
    logger.addHandler(_build_stream_handler())

    return logger
