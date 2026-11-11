"""The boring parts of a small Python desktop application.

Single-instance guard, XDG paths, autostart, menu entries, session detection,
tray capability and rotating logs - without a framework and without a
dependency.

    from desktop_lifecycle import App

    app = App("my-tool").ensure_dirs()
    app.setup_logging()
    if not app.acquire():
        raise SystemExit(0)          # asked the running copy to show itself
"""

from __future__ import annotations

from ._util import validate_app_name
from .autostart import Autostart
from .desktop_entry import (
    build_entry,
    install_icon,
    install_menu_entry,
    remove_menu_entry,
)
from .lifecycle import App
from .logging_setup import setup_logging
from .paths import Paths
from .session import has_gui, is_linux, is_wayland, is_x11, session_type
from .single_instance import AlreadyRunning, SingleInstance
from .tray import TrayUnavailable, available as tray_available, backend as tray_backend, create as create_tray

__version__ = "0.1.1"

__all__ = [
    "App",
    "Autostart",
    "AlreadyRunning",
    "Paths",
    "SingleInstance",
    "TrayUnavailable",
    "build_entry",
    "create_tray",
    "has_gui",
    "install_icon",
    "install_menu_entry",
    "is_linux",
    "is_wayland",
    "is_x11",
    "remove_menu_entry",
    "session_type",
    "setup_logging",
    "tray_available",
    "tray_backend",
    "validate_app_name",
    "__version__",
]
