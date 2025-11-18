from __future__ import annotations

import logging
import os

_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def setup_logging(level: str | int | None = None) -> None:
    """
    Configure application logging with a consistent, upgrade-friendly formatter.
    """
    if level is None:
        level = os.getenv("CRAWLER_LOG_LEVEL", "INFO")

    if isinstance(level, str):
        level = _LEVELS.get(level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
