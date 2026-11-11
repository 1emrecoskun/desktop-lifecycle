"""Is a tray icon going to appear, and with which backend?

Tray icons are the least standardised part of Linux desktops: AppIndicator,
Ayatana AppIndicator, XEmbed and StatusNotifierItem all coexist, and under
Wayland there is no XEmbed at all. This module answers the only question an
application can reliably ask - *which backend should I try* - and degrades to
``none`` instead of crashing when the answer is "none".

The application must still work without a tray. :class:`TrayUnavailable` is
raised (or ``None`` is returned) rather than leaving a window-less process.
"""

from __future__ import annotations

import importlib
import os
import platform
import threading

from .session import is_linux

__all__ = ["backend", "available", "create", "TrayUnavailable", "BACKENDS"]

BACKENDS = ("ayatana", "appindicator", "pystray", "none")

# Short names for the public API, real GI namespaces for PyGObject. Passing
# the short name to gi.require_version raises "Namespace ayatana not
# available" at runtime, which is exactly the kind of failure a unit test with
# a mocked backend cannot see.
_GI_NAMESPACE = {
    "ayatana": "AyatanaAppIndicator3",
    "appindicator": "AppIndicator3",
}

_INSTALL_HINT = (
    "No tray backend is available. Install gir1.2-ayatanaappindicator3-0.1 "
    "(Debian/Ubuntu/Mint) or 'pip install desktop-lifecycle[tray]' for the "
    "pystray fallback. The application must keep working without a tray."
)


class TrayUnavailable(RuntimeError):
    """Raised when no tray backend can be used on this machine."""


def _has_namespace(namespace: str) -> bool:
    try:
        import gi  # noqa: PLC0415 - optional dependency

        gi.require_version("Gtk", "3.0")
        gi.require_version(namespace, "0.1")
        importlib.import_module(f"gi.repository.{namespace}")
    except Exception:  # noqa: BLE001 - any failure means "not usable here"
        return False
    return True


def _has_pystray() -> bool:
    try:
        importlib.import_module("pystray")
        importlib.import_module("PIL.Image")
    except Exception:  # noqa: BLE001
        return False
    return True


def backend(env=None, system=None) -> str:
    """Return ``ayatana``, ``appindicator``, ``pystray`` or ``none``.

    On Linux the GTK/AppIndicator families win because they are the only ones
    that work under Wayland. ``pystray`` is used as a fallback and with its
    XEmbed backend, which needs an X11 session.
    """
    operating_system = platform.system() if system is None else system
    if is_linux(env=env, system=operating_system):
        if _has_namespace("AyatanaAppIndicator3"):
            return "ayatana"
        if _has_namespace("AppIndicator3"):
            return "appindicator"
    if _has_pystray():
        if not is_linux(env=env, system=operating_system):
            return "pystray"
        environment = os.environ if env is None else env
        if environment.get("DISPLAY") and not environment.get("WAYLAND_DISPLAY"):
            return "pystray"
    return "none"


def available(env=None, system=None) -> bool:
    return backend(env=env, system=system) != "none"


def create(
    title: str,
    icon=None,
    items=None,
    *,
    on_show=None,
    on_quit=None,
    show_label: str = "Show",
    quit_label: str = "Quit",
    env=None,
    system=None,
):
    """Build a tray object, or raise :class:`TrayUnavailable`.

    ``items`` is a sequence of ``(label, callback)`` pairs; a ``None`` entry
    inserts a separator, and ``show_label`` / ``quit_label`` are translatable
    so the menu can match the rest of your UI.
    The object exposes ``set_label(text)``, ``pump()`` and ``stop()``.

    ``pump()`` exists because an AppIndicator needs a GLib main loop that a
    Tk/Qt application does not otherwise run; call it from a periodic timer.
    """
    chosen = backend(env=env, system=system)
    if chosen in ("ayatana", "appindicator"):
        return _AppIndicatorTray(
            title,
            icon,
            items or (),
            on_show=on_show,
            on_quit=on_quit,
            namespace=_GI_NAMESPACE[chosen],
            show_label=show_label,
            quit_label=quit_label,
        )
    if chosen == "pystray":
        return _PystrayTray(
            title,
            icon,
            items or (),
            on_show=on_show,
            on_quit=on_quit,
            show_label=show_label,
            quit_label=quit_label,
        )
    raise TrayUnavailable(_INSTALL_HINT)


class _AppIndicatorTray:
    def __init__(
        self, title, icon, items, *, on_show, on_quit, namespace, show_label, quit_label
    ):
        import gi  # noqa: PLC0415 - optional dependency

        gi.require_version("Gtk", "3.0")
        namespace = _GI_NAMESPACE.get(namespace, namespace)
        gi.require_version(namespace, "0.1")
        from gi.repository import GLib, Gtk  # noqa: PLC0415

        indicator_module = importlib.import_module(f"gi.repository.{namespace}")
        self._Gtk = Gtk
        self._GLib = GLib
        self._module = indicator_module
        self._indicator = indicator_module.Indicator.new(
            title,
            str(icon or "application-x-executable"),
            indicator_module.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(indicator_module.IndicatorStatus.ACTIVE)
        self._indicator.set_title(title)
        self._menu = Gtk.Menu()
        self._label = Gtk.MenuItem(label=title)
        self._label.set_sensitive(False)
        self._menu.append(self._label)
        for item in items:
            if item is None:
                self._menu.append(Gtk.SeparatorMenuItem())
                continue
            label, callback = item
            entry = Gtk.MenuItem(label=label)
            entry.connect("activate", lambda *_args, cb=callback: cb())
            self._menu.append(entry)
        if on_show or on_quit:
            self._menu.append(Gtk.SeparatorMenuItem())
        if on_show:
            entry = Gtk.MenuItem(label=show_label)
            entry.connect("activate", lambda *_: on_show())
            self._menu.append(entry)
        if on_quit:
            entry = Gtk.MenuItem(label=quit_label)
            entry.connect("activate", lambda *_: on_quit())
            self._menu.append(entry)
        self._menu.show_all()
        self._indicator.set_menu(self._menu)

    def set_label(self, text: str) -> None:
        try:
            self._label.set_label(str(text)[:120])
        except Exception:  # noqa: BLE001 - cosmetic only
            pass

    def pump(self) -> None:
        context = self._GLib.MainContext.default()
        for _ in range(20):
            if not context.pending():
                break
            context.iteration(False)

    def stop(self) -> None:
        try:
            self._indicator.set_status(self._module.IndicatorStatus.PASSIVE)
        except Exception:  # noqa: BLE001 - shutting down anyway
            pass


class _PystrayTray:
    def __init__(
        self, title, icon, items, *, on_show, on_quit, show_label, quit_label
    ):
        import pystray  # noqa: PLC0415 - optional dependency

        image = _pystray_image(icon)
        menu = []
        for item in items:
            if item is None:
                menu.append(pystray.Menu.SEPARATOR)
                continue
            label, callback = item
            menu.append(pystray.MenuItem(label, lambda _icon, _item, cb=callback: cb()))
        if on_show:
            menu.append(pystray.MenuItem(show_label, lambda *_: on_show(), default=True))
        if on_quit:
            menu.append(pystray.MenuItem(quit_label, lambda *_: on_quit()))
        self._icon = pystray.Icon(title, image, title, pystray.Menu(*menu) if menu else None)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def set_label(self, text: str) -> None:
        try:
            self._icon.title = str(text)[:120]
        except Exception:  # noqa: BLE001
            pass

    def pump(self) -> None:
        """pystray drives its own loop; nothing to do."""

    def stop(self) -> None:
        try:
            self._icon.stop()
        except Exception:  # noqa: BLE001
            pass


def _pystray_image(icon):
    """Load an icon for pystray, drawing a neutral fallback if needed."""
    from PIL import Image, ImageDraw  # noqa: PLC0415

    if icon is not None:
        try:
            return Image.open(str(icon)).convert("RGBA")
        except Exception:  # noqa: BLE001 - never fail over a decoration
            pass
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(220, 38, 38, 255))
    return image
