# desktop-lifecycle

**The boring parts of a small Python desktop app — before you write any UI.**

Single-instance lock, XDG directories, autostart, menu entry, session
detection, tray capability and rotating logs. No framework, no dependencies,
no root.

```bash
pip install desktop-lifecycle
```

```python
from desktop_lifecycle import App

app = App("my-tool").ensure_dirs()
app.setup_logging()

if not app.acquire():        # a second copy was launched
    raise SystemExit(0)      # it already asked the first one to show itself
```

That is the whole idea: the four things every small desktop app gets wrong,
in one small library you can read in ten minutes.

---

## Why this exists

Every Python utility that lives in the tray ends up re-implementing the same
six things, usually differently and often incorrectly:

| What you need | What usually happens instead |
|---|---|
| One process per session | a PID file that lies after a crash, because PIDs are reused |
| Somewhere to write | settings in `~/.config`, logs in the checkout, a state file at `/.local/state` |
| Start at login | three platform-specific files written by hand |
| A menu entry | an unescaped `Exec=` line that silently refuses to launch |
| Know the session | `DISPLAY` is set, so it must be X11 — except under XWayland it is not |
| A tray icon | `pystray` works on X11, does not on Wayland, and needs PyGObject built |

These are not interesting problems, but each one produces a bug report that
takes an evening to understand. `desktop-lifecycle` is the version that was
already debugged.

## What you get

| Module | What it does |
|---|---|
| `App` | ties everything below together in one object |
| `Paths` | `~/.config`, `~/.local/state`, `~/.local/share`, `~/.cache` (and the Windows/macOS equivalents), created with `0700` |
| `SingleInstance` | advisory `flock` / `msvcrt` lock, plus a signal file so a second launch can raise the existing window |
| `Autostart` | XDG autostart entry, per-user Windows `Run` key, macOS LaunchAgent — user-scoped, reversible |
| `install_menu_entry` | spec-correct `.desktop` file with properly escaped `Exec=` and atomic writes |
| `session_type` | `x11`, `wayland`, `windows`, `macos`, `unknown` — from `XDG_SESSION_TYPE`, not from `DISPLAY` |
| `tray.backend` | answers *which* tray backend will appear: `ayatana`, `appindicator`, `pystray` or `none` |
| `setup_logging` | rotating log in the state directory, so users can find it |

More detail, including package names per distribution:
[docs/tray-on-wayland.md](docs/tray-on-wayland.md).

## A complete tray application

See [`examples/tk_demo.py`](examples/tk_demo.py) — about sixty lines, and it
already handles the second launch, the tray, the hide-to-tray behaviour and
the log file. Run it twice to see the hand-over.

## What this is not

- **Not a GUI toolkit.** It does not draw anything. Tkinter, PyQt, GTK and
  wxPython all work with it.
- **Not a tray replacement.** It detects the right backend and builds a small
  menu, but it will not pretend a tray exists where the desktop has none.
- **Not a daemon framework.** It tells you where the lock and log live; how
  your process loops is your business.

## Platform support

| | Linux X11 | Linux Wayland | Windows | macOS |
|---|---|---|---|---|
| Paths | ✅ | ✅ | ✅ | ✅ |
| Single instance | ✅ | ✅ | ✅ | ✅ |
| Autostart | ✅ XDG | ✅ XDG | ✅ `HKCU\...\Run` | ✅ LaunchAgent |
| Menu entry | ✅ | ✅ | — | — |
| Session detection | ✅ | ✅ | ✅ | ✅ |
| Tray | ✅ AppIndicator | ✅ AppIndicator | ✅ pystray | ✅ pystray |

Tray icons on Wayland only exist through the AppIndicator / StatusNotifierItem
protocol. If a desktop has neither, the answer is `none` and your app must
keep working with a visible window — that is exactly the case this library
forces you to handle.

## Security notes

- Everything is **user-scoped**. Nothing here asks for root, writes outside
  your home directory, or edits system configuration.
- Lock files are created `0600`; configuration directories `0700`;
  desktop entries `0644`.
- Every file is written **atomically** (temporary file + `rename`) so a
  crash cannot leave half an autostart entry behind.
- `Exec=` values are escaped the way the specification requires — `"`, `` ` ``,
  `$`, `\` and `%` cannot break out of the quoted argument or become a field
  code.
- No `shell=True` anywhere, no `eval`, no dynamic imports from user input.
- Application names are validated, so a name cannot escape its own directory.
- No network access at runtime, no telemetry, no accounts.

Found a problem? See [SECURITY.md](SECURITY.md).

## Checking a machine

```bash
python -m desktop_lifecycle          # human-readable
python -m desktop_lifecycle --json   # for bug reports
```

It prints the resolved directories, the session type and the tray backend
without writing anything. Users can paste that into an issue instead of
`ls -la ~`.

## Compared to the alternatives

| | desktop-lifecycle | pystray | manual code |
|---|---|---|---|
| XDG paths | ✅ | — | usually wrong |
| Single-instance lock | ✅ | — | PID file |
| Autostart | ✅ | — | per project |
| Menu entry | ✅ | — | per project |
| Wayland-aware tray detection | ✅ | partial | rare |
| GUI toolkit required | no | no | no |
| Dependencies | none | Pillow, PyGObject | — |

`pystray` is good at what it does; this library answers the questions around
it, including "should I even try".

## Requirements

Python 3.9+. No third-party packages.

Optional tray fallback: `pip install desktop-lifecycle[tray]` (pystray + Pillow).
On Debian/Ubuntu/Mint the native way is `gir1.2-ayatanaappindicator3-0.1`.

## Development

```bash
git clone https://github.com/1emrecoskun/desktop-lifecycle
cd desktop-lifecycle
python -m unittest discover -s tests -v
```

79 tests, no hardware and no display required.

## License

MIT — see [LICENSE](LICENSE).

Türkçe: [README.tr.md](README.tr.md)
