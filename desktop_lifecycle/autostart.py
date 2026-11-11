"""Start at login, on every platform, without asking for root.

Linux uses an XDG autostart entry, Windows uses the per-user ``Run`` registry
key, macOS uses a LaunchAgent. All three are user-scoped: no administrator
rights, no system-wide changes, and turning it off leaves nothing behind.
"""

from __future__ import annotations

import os
import platform
import plistlib
from pathlib import Path

from ._util import (
    atomic_write,
    ensure_dir,
    escape_entry_value,
    quote_exec,
    validate_app_name,
)
from .paths import Paths

__all__ = ["Autostart"]


class Autostart:
    """Toggle "start when I log in" for one application.

    >>> autostart = Autostart("my-app", ["/usr/bin/python3", "-m", "my_app"])
    >>> autostart.enable()
    True
    >>> autostart.enabled
    True
    """

    def __init__(
        self,
        app: str,
        exec_parts,
        *,
        args=(),
        comment: str = "",
        display_name: str | None = None,
        icon=None,
        hidden_arg: str | None = "--background",
        paths=None,
        system=None,
        home=None,
        env=None,
    ):
        self.app = validate_app_name(app)
        if isinstance(exec_parts, (str, Path)):
            raise TypeError("exec_parts must be a sequence, not a single string")
        self.exec_parts = [str(part) for part in exec_parts]
        if not self.exec_parts:
            raise ValueError("exec_parts must contain at least the program to run")
        self.args = [str(arg) for arg in args]
        if hidden_arg and hidden_arg not in self.args:
            self.args.append(hidden_arg)
        self.comment = comment
        # The entry's Name= is what a login-items editor shows, so it can
        # differ from the directory-safe application id.
        self.display_name = display_name or self.app
        self.icon = icon
        self.system = platform.system() if system is None else system
        self.env = os.environ if env is None else env
        self.home = Path(home) if home is not None else Path.home()
        self.paths = paths or Paths.for_app(
            self.app, env=self.env, system=self.system, home=self.home
        )

    # -- locations -------------------------------------------------------
    @property
    def command(self) -> list[str]:
        return [*self.exec_parts, *self.args]

    @property
    def target(self) -> Path:
        """The file (or registry value) that represents the autostart entry."""
        if self.system == "Windows":
            return Path(f"HKCU:Software/Microsoft/Windows/CurrentVersion/Run/{self.app}")
        if self.system == "Darwin":
            return (
                self.home
                / "Library"
                / "LaunchAgents"
                / f"{self._label}.plist"
            )
        return Path(self.paths.config_home) / "autostart" / f"{self.app}.desktop"

    @property
    def _label(self) -> str:
        """Reverse-DNS-ish launchd label; ``my-app`` becomes ``my-app``."""
        return self.app

    # -- state -----------------------------------------------------------
    @property
    def enabled(self) -> bool:
        if self.system == "Windows":
            return self._windows_value() is not None
        return self.target.exists()

    # -- public API ------------------------------------------------------
    def enable(self) -> bool:
        """Create the entry. Returns ``True`` when it is in place afterwards."""
        if self.system == "Windows":
            return self._windows_set(quote_exec(self.command))
        if self.system == "Darwin":
            return self._macos_set()
        return self._linux_set()

    def disable(self) -> bool:
        """Remove the entry. Returns ``True`` when nothing is left behind."""
        if self.system == "Windows":
            self._windows_delete()
            return not self.enabled
        try:
            self.target.unlink()
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return True

    def toggle(self) -> bool:
        return self.disable() if self.enabled else self.enable()

    # -- Linux -----------------------------------------------------------
    def _linux_set(self) -> bool:
        lines = [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={escape_entry_value(self.display_name)}",
        ]
        if self.comment:
            lines.append(f"Comment={escape_entry_value(self.comment)}")
        lines.append(f"Exec={quote_exec(self.command, windows=False)}")
        if self.icon:
            # Desktop entries want an absolute path here; a bare name has to be
            # looked up through the icon theme and often silently fails.
            lines.append(f"Icon={escape_entry_value(str(self.icon))}")
        lines.extend(
            [
                "Terminal=false",
                "X-GNOME-Autostart-enabled=true",
                "Hidden=false",
                "",
            ]
        )
        try:
            atomic_write(self.target, "\n".join(lines), mode=0o644)
        except OSError:
            return False
        return True

    # -- macOS -----------------------------------------------------------
    def _macos_set(self) -> bool:
        payload = {
            "Label": self._label,
            "ProgramArguments": list(self.command),
            "RunAtLoad": True,
            "ProcessType": "Interactive",
        }
        try:
            ensure_dir(self.target.parent)
            data = plistlib.dumps(payload, fmt=plistlib.FMT_XML)
            self.target.write_bytes(data)
            self.target.chmod(0o644)
        except OSError:
            return False
        return True

    # -- Windows ---------------------------------------------------------
    def _windows_key(self):
        import winreg  # noqa: PLC0415 - Windows-only import

        return winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )

    def _windows_value(self):
        try:
            import winreg  # noqa: PLC0415 - Windows-only import

            with self._windows_key() as key:
                value, _ = winreg.QueryValueEx(key, self.app)
            return value
        except (ImportError, OSError):
            return None

    def _windows_set(self, command: str) -> bool:
        try:
            import winreg  # noqa: PLC0415 - Windows-only import

            with self._windows_key() as key:
                winreg.SetValueEx(key, self.app, 0, winreg.REG_SZ, command)
        except (ImportError, OSError):
            return False
        return True

    def _windows_delete(self) -> bool:
        try:
            import winreg  # noqa: PLC0415 - Windows-only import

            with self._windows_key() as key:
                winreg.DeleteValue(key, self.app)
        except FileNotFoundError:
            return True
        except (ImportError, OSError):
            return False
        return True

    # -- diagnostics -----------------------------------------------------
    def describe(self) -> dict:
        return {
            "app": self.app,
            "display_name": self.display_name,
            "system": self.system,
            "enabled": self.enabled,
            "target": str(self.target),
            "command": self.command,
            "exec_line": quote_exec(self.command, windows=self.system == "Windows"),
        }
