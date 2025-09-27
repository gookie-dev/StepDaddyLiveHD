from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "daddyliveproxy"
LOG_FILE = Path("daddyliveproxy.log")


def configure_logging(level: int = logging.DEBUG) -> logging.Logger:
    """
    Configure the root application logger 'daddyliveproxy' exactly once.
    Returns the configured logger.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False  # we attach our own handlers

    # If already configured, do nothing
    if getattr(logger, "_configured_once", False):
        return logger

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Make uvicorn loggers forward to us
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        ulog = logging.getLogger(name)
        ulog.setLevel(level)
        ulog.propagate = True
        # IMPORTANT: do not add handlers here; let them bubble to our logger

    logger._configured_once = True  # type: ignore[attr-defined]
    return logger


def get_logger(child: str | None = None) -> logging.Logger:
    """
    Get a child logger under 'daddyliveproxy', e.g. 'daddyliveproxy.step_daddy'.
    """
    name = LOGGER_NAME if not child else f"{LOGGER_NAME}.{child}"
    return logging.getLogger(name)


def get_log_file() -> Path:
    return LOG_FILE
