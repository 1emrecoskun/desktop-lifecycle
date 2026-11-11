"""Rotating file logging in the right directory, with no configuration.

Users report bugs with a log file; they should never have to find it. Put it
in ``state`` (never in ``config``, which users reset, and never in the
installation directory, which may be read-only).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

__all__ = ["setup_logging", "get_logger"]


def setup_logging(
    paths,
    *,
    level=logging.INFO,
    filename: str = "app.log",
    max_bytes: int = 1_000_000,
    backups: int = 2,
    console: bool = False,
) -> Path:
    """Attach a rotating handler to the root logger and return the log path."""
    if any(character in filename for character in ("/", "\\")) or filename in (".", ".."):
        raise ValueError("filename must be a plain file name, not a path")

    directory = Path(paths.logs)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / filename

    handler = RotatingFileHandler(
        target, maxBytes=max_bytes, backupCount=backups, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger()
    for existing in list(root.handlers):
        if isinstance(existing, RotatingFileHandler):
            root.removeHandler(existing)
            existing.close()
    root.addHandler(handler)
    root.setLevel(level)
    if console:
        # Do not stack stream handlers when an application calls this more
        # than once (a settings window that re-opens, a restart in-process).
        already = any(
            type(existing) is logging.StreamHandler for existing in root.handlers
        )
        if not already:
            stream = logging.StreamHandler()
            stream.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
            root.addHandler(stream)
    return target


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
