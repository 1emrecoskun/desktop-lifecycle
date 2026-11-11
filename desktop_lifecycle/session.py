"""Which kind of desktop session are we running in?

Small applications gate features on this: screen capture usually needs X11,
global hotkeys usually need X11, and tray icons behave differently under
Wayland. Getting it wrong produces a crash instead of a disabled button.
"""

from __future__ import annotations

import os
import platform

__all__ = ["session_type", "has_gui", "is_x11", "is_wayland", "is_linux", "SESSION_TYPES"]

SESSION_TYPES = ("windows", "macos", "x11", "wayland", "unknown")


def session_type(env=None, system=None) -> str:
    """Return one of ``windows``, ``macos``, ``x11``, ``wayland``, ``unknown``.

    ``XDG_SESSION_TYPE`` wins when it is set, because a Wayland session that
    also exports ``DISPLAY`` (through XWayland) is still a Wayland session for
    anything that needs real screen content.
    """
    operating_system = platform.system() if system is None else system
    if operating_system == "Windows":
        return "windows"
    if operating_system == "Darwin":
        return "macos"
    if operating_system not in ("Linux", "FreeBSD", "OpenBSD", "NetBSD"):
        return "unknown"

    environment = os.environ if env is None else env
    declared = (environment.get("XDG_SESSION_TYPE") or "").strip().lower()
    if declared in ("x11", "wayland"):
        return declared
    if environment.get("WAYLAND_DISPLAY"):
        return "wayland"
    if environment.get("DISPLAY"):
        return "x11"
    return "unknown"


def has_gui(env=None, system=None) -> bool:
    """True when a graphical session is reachable (a display, not a tty)."""
    return session_type(env, system) != "unknown"


def is_x11(env=None, system=None) -> bool:
    return session_type(env, system) == "x11"


def is_wayland(env=None, system=None) -> bool:
    return session_type(env, system) == "wayland"


def is_linux(env=None, system=None) -> bool:
    operating_system = platform.system() if system is None else system
    return operating_system in ("Linux", "FreeBSD", "OpenBSD", "NetBSD")
