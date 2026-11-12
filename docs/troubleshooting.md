# Troubleshooting

## The tray icon never appears

A tray host is required, not just the AppIndicator library. Check the session bus:

```bash
gdbus call --session --dest org.freedesktop.DBus \
  --object-path /org/freedesktop/DBus \
  --method org.freedesktop.DBus.NameHasOwner org.kde.StatusNotifierWatcher
```

If it prints `false`, nothing on this desktop can show a tray icon. On GNOME,
install and enable *AppIndicator and KStatusNotifierItem Support*; on KDE and
most bars it is part of the panel. `desktop_lifecycle.tray.backend()` returns
`none` in that case, on purpose.

If the command prints `true` but still no icon appears, the application is
probably hiding it behind a stale `pystray` fallback. Check
`python -m desktop_lifecycle --json` and look at `tray_backend`.

## The second launch does nothing

The running instance has to ask for the signal. With `App` that happens in your
event loop:

```python
if app.poll_show_request():
    window.deiconify()
```

`SingleInstance` alone never polls anything; it only writes and removes the
signal file.

## Autostart entry does not run at login

* Check that the file exists: `~/.config/autostart/<app>.desktop` on Linux.
* Open the `Exec=` line and run it by hand; a missing interpreter path is the
  usual cause.
* Some desktops only read autostart entries when the session starts, so log
  out and back in.

## The lock file looks stale

It is an advisory `flock`, not a PID file. When the process dies the kernel
releases it, so the file stays but the lock does not. Do not delete it; a
second launch should be able to take it immediately.

## Where are the logs?

`~/.local/state/<app>/logs/` on Linux, `%LOCALAPPDATA%\<app>\logs\` on Windows,
`~/Library/Application Support/<app>/logs/` on macOS. `python -m
desktop_lifecycle --json` prints the exact paths for an application name.

## A path is wrong

`XDG_*` values are honoured only when they are absolute, as the specification
requires. A relative `XDG_STATE_HOME=./state` is ignored on purpose.
