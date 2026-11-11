# Tray icons on modern Linux desktops

Tray icons are the least standardised part of the Linux desktop. This page is
the short version of what actually works in 2026, and what to do when it does
not.

## The three protocols

| Protocol | Where it lives | Works on Wayland | Notes |
|---|---|---|---|
| StatusNotifierItem + D-Bus menu | KDE, GNOME (with an extension), most bars | yes | the only modern option |
| AppIndicator / Ayatana AppIndicator | the library API that wraps the above | yes | `libayatana-appindicator3` |
| XEmbed (`_NET_SYSTEM_TRAY`) | X11 only | no | legacy; XWayland does not expose it |

A Wayland session has no system tray whatsoever in the X11 sense. Bars such as
KDE Plasma, Waybar, `xfce4-panel` and COSMIC implement StatusNotifierItem;
GNOME needs the *AppIndicator and KStatusNotifierItem Support* extension.
Without them, an application cannot show an icon — no library can change that.

## What this library does about it

`desktop_lifecycle.tray.backend()` answers one question: *which backend should
I try?*

```python
from desktop_lifecycle import tray_backend

backend = tray_backend()
# "ayatana" | "appindicator" | "pystray" | "none"
```

The order on Linux is:

1. `ayatana` — `AyatanaAppIndicator3` through PyGObject
2. `appindicator` — the older `AppIndicator3`
3. `pystray` — only when there is an X11 display and no Wayland session
4. `none`

The reason `pystray` is last on Linux is that its Linux backend is XEmbed. It
works beautifully on X11 and cannot work under Wayland; pretending otherwise
just moves the failure into a thread where nobody sees the traceback.

`tray.create()` raises `TrayUnavailable` when the answer is `none`. That is
deliberate: an application must not end up as a window-less process the user
cannot reach.

## Installing a backend

Debian, Ubuntu, Mint, Pop!\_OS:

```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1
```

Fedora:

```bash
sudo dnf install libayatana-appindicator-gtk3
```

Arch:

```bash
sudo pacman -S libayatana-appindicator
```

Pure Python alternative for both X11 and Wayland-shaped environments where
PyGObject is not available:

```bash
pip install desktop-lifecycle[tray]
```

That pulls in `pystray` and `Pillow`. On Wayland it will still report `none`
unless an AppIndicator library exists, which is the honest answer.

## Writing your application for the "no tray" case

The pattern that never leaves a user stuck:

```python
from desktop_lifecycle import App, TrayUnavailable, create_tray

app = App("my-tool").ensure_dirs()
if not app.acquire():
    raise SystemExit(0)

tray = None
try:
    tray = create_tray("My Tool", on_show=show_window, on_quit=quit_app)
except TrayUnavailable:
    pass  # keep a visible window instead of hiding

# Only hide to the tray if a tray actually exists.
if tray is not None and app.background_requested:
    hide_window()
```

The rule of thumb: *hide to tray only when the tray exists*, and always keep a
menu entry or a window that can bring the application back.

## Checking a user's machine

Ask for this instead of a screenshot of their panel:

```bash
python -m desktop_lifecycle --json
```

It reports the session type and the backend without modifying anything, and it
contains no usernames or hostnames.
