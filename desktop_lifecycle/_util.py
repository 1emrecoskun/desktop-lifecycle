"""Internal helpers: name validation, atomic writes and Exec= quoting.

Everything in here is deliberately small and dependency-free. The quoting
rules matter: a wrong ``Exec=`` line is the number one reason a desktop entry
silently refuses to launch, and an unescaped ``$`` or backtick in a path can be
executed by the shell that some launchers still use.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

__all__ = [
    "validate_app_name",
    "ensure_dir",
    "atomic_write",
    "quote_exec_arg",
    "quote_exec",
    "escape_entry_value",
]

# 1-64 characters, must start with a letter or digit, no path separators.
# Reversed-DNS names (com.example.app) are accepted on purpose.
_APP_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def validate_app_name(name: str) -> str:
    """Return a safe application name or raise ``ValueError``.

    The name becomes a directory name, a file name and a registry value, so it
    must not be able to escape any of those places.
    """
    if not isinstance(name, str):
        raise TypeError("application name must be a string")
    candidate = name.strip()
    if (
        not candidate
        or not _APP_NAME_RE.match(candidate)
        or ".." in candidate
        or candidate.endswith(".")
    ):
        raise ValueError(
            f"invalid application name {name!r}: use 1-64 characters from "
            "[A-Za-z0-9._-], starting with a letter or digit"
        )
    return candidate


def ensure_dir(path, mode: int = 0o700) -> Path:
    """Create ``path`` (and parents) if needed and return it as a ``Path``."""
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True, mode=mode)
    return target


def atomic_write(path, text: str, mode: int = 0o644) -> Path:
    """Write ``text`` to ``path`` atomically with an explicit mode.

    A half-written autostart entry or settings file is worse than no file at
    all, so the data goes to a temporary file in the same directory first and
    is then renamed into place.
    """
    target = Path(path)
    ensure_dir(target.parent, mode=0o700)
    fd, temporary = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return target


def escape_entry_value(value: str) -> str:
    """Escape a desktop-entry *value* (``Name=``, ``Comment=``, ...).

    The specification reserves backslash and newline inside values.
    """
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r", "")
        .replace("\n", "\\n")
    )


def quote_exec_arg(value: str) -> str:
    """Quote a single argument for a desktop-entry ``Exec=`` field.

    Follows the rules every mainstream launcher applies: backslash escapes
    ``"``, `````, ``$`` and ``\\`` inside a double-quoted argument, and ``%``
    is doubled because a single ``%`` starts a field code (``%f``, ``%U``).
    """
    text = str(value).replace("\r", " ").replace("\n", " ")
    if os.name == "nt":
        # Windows command lines use their own quoting rules; only quote when
        # the argument actually needs it.
        if text and not any(character in text for character in ' \t"'):
            return text
        return '"' + text.replace('"', '\\"') + '"'
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("%", "%%")
    )
    return f'"{escaped}"'


def quote_exec(parts) -> str:
    """Quote a whole command line for ``Exec=`` / autostart use."""
    return " ".join(quote_exec_arg(part) for part in parts)
