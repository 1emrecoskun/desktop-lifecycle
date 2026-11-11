"""One process per user session, and a way to ask it to show its window.

The lock is an advisory file lock, not a PID file: a PID file lies after a
crash or a reboot (PIDs are reused), while the kernel drops an ``flock`` the
moment the process dies. The second launch does not fail silently either - it
writes a signal file, which the running instance watches.
"""

from __future__ import annotations

import os
from pathlib import Path

from ._util import atomic_write, ensure_dir

try:  # POSIX
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]
    import msvcrt

__all__ = ["SingleInstance", "AlreadyRunning"]


class AlreadyRunning(RuntimeError):
    """Raised by :meth:`SingleInstance.acquire_or_raise`."""


class SingleInstance:
    """A non-blocking, cross-platform single-instance guard.

    >>> instance = SingleInstance("/tmp/example.lock")
    >>> instance.acquire()
    True
    """

    def __init__(self, lock_path, show_signal=None):
        self.lock_path = Path(lock_path)
        self.show_signal = Path(show_signal) if show_signal is not None else None
        self._handle = None

    # -- locking ---------------------------------------------------------
    def acquire(self) -> bool:
        """Try to take the lock. Returns ``False`` when another process has it."""
        if self._handle is not None:
            return True
        ensure_dir(self.lock_path.parent)
        descriptor = os.open(
            str(self.lock_path),
            os.O_RDWR | os.O_CREAT,
            0o600,
        )
        handle = os.fdopen(descriptor, "r+", encoding="utf-8")
        if not self._lock(handle):
            handle.close()
            return False
        try:
            handle.seek(0)
            handle.truncate()
            handle.write(f"{os.getpid()}\n")
            handle.flush()
        except OSError:
            # A read-only home is not a reason to refuse to start.
            pass
        self._handle = handle
        return True

    def _lock(self, handle) -> bool:
        if fcntl is not None:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                return False
            return True
        try:  # pragma: no cover - Windows
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def acquire_or_raise(self) -> None:
        if not self.acquire():
            raise AlreadyRunning(f"another instance holds {self.lock_path}")

    def release(self) -> None:
        """Drop the lock. Safe to call more than once."""
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            else:  # pragma: no cover - Windows
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        finally:
            handle.close()

    @property
    def held(self) -> bool:
        return self._handle is not None

    def __enter__(self) -> "SingleInstance":
        self.acquire()
        return self

    def __exit__(self, *_) -> None:
        self.release()

    # -- asking the running instance for its window ----------------------
    def request_show(self) -> bool:
        """Touch the signal file. Called by the *second* launch."""
        if self.show_signal is None:
            return False
        try:
            atomic_write(self.show_signal, "", mode=0o600)
        except OSError:
            return False
        return True

    def consume_show_request(self) -> bool:
        """Return ``True`` once per request. Called by the *running* instance."""
        if self.show_signal is None:
            return False
        try:
            self.show_signal.unlink()
        except FileNotFoundError:
            return False
        except OSError:
            return False
        return True

    def owner_pid(self):
        """PID written by the current lock holder, or ``None``."""
        try:
            text = self.lock_path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return int(text) if text.isdigit() else None
