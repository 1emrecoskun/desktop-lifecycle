# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-11-11

### Fixed

- `tray.create()` passed the short backend name to `gi.require_version`, so
  every GTK tray raised `Namespace ayatana not available`. The real GI
  namespace (`AyatanaAppIndicator3` / `AppIndicator3`) is used now.
- A `None` menu entry crashed both tray backends instead of becoming a
  separator.

Both were found by moving an application onto the library and watching its
tray fail in a real session, which is precisely what the unit tests mocked.

## [0.1.1] - 2026-11-11

### Added

- `Autostart(..., display_name=...)`: the `Name=` a login-items editor shows can
  now differ from the directory-safe application id.
- `tray.create(..., items=[...])` accepts `None` as a menu separator, so an
  application can keep the menu structure it already had.

## [0.1.0] - 2026-11-11

First release.

### Added

- `App` — one object that resolves paths, detects the session and guards
  against a second instance.
- `Paths` — XDG base directories on Linux/BSD, `APPDATA`/`LOCALAPPDATA` on
  Windows, `Application Support`/`Caches` on macOS; created `0700`.
- `SingleInstance` — advisory `flock`/`msvcrt` lock with a `0600` lock file,
  plus a signal file so a second launch can ask the running copy to show its
  window.
- `Autostart` — XDG autostart entry, per-user Windows `Run` value, macOS
  LaunchAgent; enable, disable, toggle and describe.
- `build_entry` / `install_menu_entry` / `install_icon` / `remove_menu_entry` —
  `.desktop` files with spec-correct `Exec=` escaping and atomic writes.
- `session_type` — `x11`, `wayland`, `windows`, `macos` or `unknown`, based on
  `XDG_SESSION_TYPE` rather than on `DISPLAY`.
- `tray.backend` — reports `ayatana`, `appindicator`, `pystray` or `none`, so an
  application can decide whether a tray is possible at all.
- `setup_logging` — rotating log in the state directory.
- `python -m desktop_lifecycle` — read-only environment report for bug reports.

[Unreleased]: https://github.com/1emrecoskun/desktop-lifecycle/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/1emrecoskun/desktop-lifecycle/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/1emrecoskun/desktop-lifecycle/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/1emrecoskun/desktop-lifecycle/releases/tag/v0.1.0
