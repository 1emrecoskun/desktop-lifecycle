"""The one object that wires the pieces together.

>>> from desktop_lifecycle import App
>>> app = App("my-tool")
>>> app.ensure_dirs().setup_logging()
>>> if not app.acquire():      # another copy is already running
...     raise SystemExit(0)    # it was asked to show its window

Nothing here touches the network, spawns a shell, or needs root.
"""

from __future__ import annotations

import os
import platform
import sys

from .autostart import Autostart
from .desktop_entry import install_menu_entry
from .logging_setup import setup_logging as _setup_logging
from .paths import Paths
from .session import session_type
from .single_instance import SingleInstance
from .tray import backend as tray_backend
from ._util import validate_app_name

__all__ = ["App"]

DEFAULT_BACKGROUND_FLAGS = ("--background", "--tray", "--minimized", "--hidden")


class App:
    """Resolved paths, session type and a single-instance guard for one app."""

    def __init__(
        self,
        name: str,
        *,
        argv=None,
        env=None,
        system=None,
        home=None,
        background_flags=DEFAULT_BACKGROUND_FLAGS,
    ):
        self.name = validate_app_name(name)
        self.env = os.environ if env is None else env
        self.system = platform.system() if system is None else system
        self.argv = list(sys.argv[1:] if argv is None else argv)
        self.background_flags = tuple(background_flags)
        self.paths = Paths.for_app(
            self.name, env=self.env, system=self.system, home=home
        )
        self.session = session_type(self.env, self.system)
        self._instance = None

    # -- setup -----------------------------------------------------------
    def ensure_dirs(self) -> "App":
        self.paths.ensure()
        return self

    def setup_logging(self, **kwargs):
        """Rotating log in ``paths.logs``; returns the log file path."""
        self.ensure_dirs()
        return _setup_logging(self.paths, **kwargs)

    # -- process lifetime -------------------------------------------------
    def acquire(self) -> bool:
        """Become the one running instance.

        Returns ``False`` when another copy already holds the lock; that copy
        is asked to bring its window to the front before this method returns.
        """
        instance = SingleInstance(self.paths.lock, self.paths.show_signal)
        if instance.acquire():
            self._instance = instance
            instance.consume_show_request()  # ignore a request from a dead run
            return True
        instance.request_show()
        return False

    def poll_show_request(self) -> bool:
        """``True`` when a second launch asked this instance to show itself."""
        if self._instance is None:
            return False
        return self._instance.consume_show_request()

    def release(self) -> None:
        if self._instance is not None:
            self._instance.release()
            self._instance = None

    @property
    def running(self) -> bool:
        return self._instance is not None

    # -- conveniences -----------------------------------------------------
    @property
    def background_requested(self) -> bool:
        """``True`` when the app was started to live in the tray only."""
        flags = {flag.lower() for flag in self.background_flags}
        return any(argument.lower() in flags for argument in self.argv)

    def autostart(self, exec_parts=None, **kwargs) -> Autostart:
        """An :class:`Autostart` for this app, defaulting to the current command."""
        parts = exec_parts or [sys.executable, "-m", self._module_guess()]
        return Autostart(
            self.name,
            parts,
            paths=self.paths,
            system=self.system,
            env=self.env,
            **kwargs,
        )

    def install_menu_entry(self, exec_parts=None, **kwargs):
        """Write a ``.desktop`` menu entry for this app."""
        parts = exec_parts or [sys.executable, "-m", self._module_guess()]
        return install_menu_entry(self.paths, self.name, parts, **kwargs)

    def _module_guess(self) -> str:
        """Best-effort ``package.module`` of the process that created this App."""
        main = sys.modules.get("__main__")
        path = getattr(main, "__file__", None)
        if not path:
            return self.name.replace("-", "_")
        stem = os.path.splitext(os.path.basename(path))[0]
        package = getattr(main, "__package__", None)
        if package and stem == "__main__":
            return f"{package}.__main__"
        return package or stem

    # -- diagnostics ------------------------------------------------------
    def describe(self) -> dict:
        return {
            "version": _version(),
            "name": self.name,
            "python": platform.python_version(),
            "platform": self.system,
            "session": self.session,
            "tray_backend": tray_backend(env=self.env, system=self.system),
            "background_requested": self.background_requested,
            "argv": self.argv,
            "paths": self.paths.as_dict(),
        }


def _version() -> str:
    from . import __version__

    return __version__
