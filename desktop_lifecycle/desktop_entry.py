"""Menu entries and icons, written the way the specification asks for them.

This module is pure and testable: :func:`build_entry` returns text, and
:func:`install_menu_entry` only does file I/O. Nothing here runs a shell.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ._util import (
    atomic_write,
    ensure_dir,
    escape_entry_value,
    quote_exec,
    validate_app_name,
)

__all__ = [
    "build_entry",
    "install_menu_entry",
    "remove_menu_entry",
    "install_icon",
    "applications_dir",
]


def build_entry(
    *,
    name: str,
    exec_parts,
    comment: str = "",
    icon=None,
    terminal: bool = False,
    categories=("Utility",),
    startup_notify: bool = True,
    extra: dict | None = None,
) -> str:
    """Return a complete ``.desktop`` file as text.

    ``exec_parts`` is a sequence (command, arg, arg...). Each part is quoted
    separately, so paths with spaces, ``$``, backticks or quotes survive.
    """
    if isinstance(exec_parts, (str, Path)):
        raise TypeError("exec_parts must be a sequence, not a single string")
    parts = [str(part) for part in exec_parts]
    if not parts or not parts[0]:
        raise ValueError("exec_parts must contain at least the program to run")

    lines = [
        "[Desktop Entry]",
        "Type=Application",
        "Version=1.0",
        f"Name={escape_entry_value(name)}",
    ]
    if comment:
        lines.append(f"Comment={escape_entry_value(comment)}")
    lines.append(f"Exec={quote_exec(parts, windows=False)}")
    if icon:
        lines.append(f"Icon={escape_entry_value(str(icon))}")
    lines.append(f"Terminal={'true' if terminal else 'false'}")
    lines.append(f"Categories={';'.join(categories)};")
    if startup_notify:
        lines.append("StartupNotify=true")
    for key, value in (extra or {}).items():
        lines.append(f"{key}={escape_entry_value(value)}")
    return "\n".join(lines) + "\n"


def applications_dir(paths) -> Path:
    """``$XDG_DATA_HOME/applications`` for the given :class:`Paths`."""
    return Path(paths.data_home) / "applications"


def install_menu_entry(paths, name: str, exec_parts, **kwargs) -> Path:
    """Write ``<data_home>/applications/<name>.desktop`` and refresh the cache."""
    safe_name = validate_app_name(name)
    target = applications_dir(paths) / f"{safe_name}.desktop"
    text = build_entry(name=kwargs.pop("display_name", name), exec_parts=exec_parts, **kwargs)
    atomic_write(target, text, mode=0o644)
    _refresh_desktop_database(target.parent)
    return target


def remove_menu_entry(paths, name: str) -> bool:
    """Delete the menu entry. Returns ``True`` when a file was removed."""
    target = applications_dir(paths) / f"{validate_app_name(name)}.desktop"
    try:
        target.unlink()
    except FileNotFoundError:
        return False
    _refresh_desktop_database(target.parent)
    return True


def install_icon(paths, icon_source, name: str) -> Path:
    """Copy an icon into ``<data_home>/icons/hicolor/scalable/apps``.

    The returned path is what belongs in ``Icon=``. SVG stays SVG; anything
    else is copied byte-for-byte with its own suffix.
    """
    safe_name = validate_app_name(name)
    source = Path(icon_source)
    if not source.is_file():
        raise FileNotFoundError(f"icon not found: {source}")
    suffix = source.suffix.lower() or ".png"
    target_dir = ensure_dir(
        Path(paths.data_home) / "icons" / "hicolor" / "scalable" / "apps"
    )
    target = target_dir / f"{safe_name}{suffix}"
    shutil.copyfile(source, target)
    target.chmod(0o644)
    return target


def _refresh_desktop_database(directory: Path) -> None:
    """Best-effort ``update-desktop-database``; never required, never a shell."""
    executable = shutil.which("update-desktop-database")
    if not executable:
        return
    try:
        subprocess.run(
            [executable, str(directory)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        pass
