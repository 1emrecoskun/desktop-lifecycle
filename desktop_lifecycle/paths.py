"""Where a small desktop application is allowed to write.

One source of truth for ``~/.config``, ``~/.local/state``, ``~/.local/share``
and ``~/.cache`` (and their Windows/macOS equivalents). Writing to the wrong
one is a classic bug: a state file in ``~/.config`` survives a settings reset,
and a config file in ``~/.local/state`` gets deleted by a log rotation.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import platform

from ._util import ensure_dir, validate_app_name

__all__ = ["Paths"]


def _absolute(value, fallback: Path) -> Path:
    """Honour an XDG variable only when it is absolute, as the spec requires."""
    if not value:
        return fallback
    candidate = Path(value).expanduser()
    return candidate if candidate.is_absolute() else fallback


def _home(home) -> Path:
    return Path(home) if home is not None else Path.home()


@dataclass(frozen=True)
class Paths:
    """Resolved directories for one application.

    ``config`` is for settings the user can edit, ``state`` for logs and
    locks, ``data`` for files the app owns, ``cache`` for anything that can be
    deleted at any time.
    """

    app: str
    config_home: Path
    state_home: Path
    data_home: Path
    cache_home: Path

    @property
    def config(self) -> Path:
        return self.config_home / self.app

    @property
    def state(self) -> Path:
        return self.state_home / self.app

    @property
    def data(self) -> Path:
        return self.data_home / self.app

    @property
    def cache(self) -> Path:
        return self.cache_home / self.app

    @property
    def logs(self) -> Path:
        return self.state / "logs"

    @property
    def lock(self) -> Path:
        return self.state / "instance.lock"

    @property
    def show_signal(self) -> Path:
        """A second launch touches this file to ask the first one to show."""
        return self.state / "show-window"

    @classmethod
    def for_app(
        cls,
        app: str,
        *,
        env=None,
        system=None,
        home=None,
    ) -> "Paths":
        name = validate_app_name(app)
        environment = os.environ if env is None else env
        operating_system = platform.system() if system is None else system
        home_path = _home(home)

        if operating_system == "Windows":
            roaming = _absolute(
                environment.get("APPDATA"), home_path / "AppData" / "Roaming"
            )
            local = _absolute(
                environment.get("LOCALAPPDATA"), home_path / "AppData" / "Local"
            )
            return cls(
                app=name,
                config_home=roaming,
                state_home=local,
                data_home=roaming,
                cache_home=local / "cache",
            )

        if operating_system == "Darwin":
            support = home_path / "Library" / "Application Support"
            return cls(
                app=name,
                config_home=support,
                state_home=support,
                data_home=support,
                cache_home=home_path / "Library" / "Caches",
            )

        return cls(
            app=name,
            config_home=_absolute(
                environment.get("XDG_CONFIG_HOME"), home_path / ".config"
            ),
            state_home=_absolute(
                environment.get("XDG_STATE_HOME"), home_path / ".local" / "state"
            ),
            data_home=_absolute(
                environment.get("XDG_DATA_HOME"), home_path / ".local" / "share"
            ),
            cache_home=_absolute(
                environment.get("XDG_CACHE_HOME"), home_path / ".cache"
            ),
        )

    def ensure(self) -> "Paths":
        """Create the four application directories with user-only permissions."""
        for directory in (self.config, self.state, self.data, self.cache):
            ensure_dir(directory)
        return self

    def as_dict(self) -> dict:
        return {
            "app": self.app,
            "config": str(self.config),
            "state": str(self.state),
            "data": str(self.data),
            "cache": str(self.cache),
            "logs": str(self.logs),
        }
