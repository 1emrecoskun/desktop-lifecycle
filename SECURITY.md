# Security policy

## Supported versions

The latest release on PyPI receives fixes. Older versions are not supported.

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

* Use GitHub's private reporting: **Security → Report a vulnerability** on
  https://github.com/1emrecoskun/desktop-lifecycle
* Include the version, the operating system, and the smallest snippet that
  reproduces the problem.

You can expect an acknowledgement within a few days. Please give a reasonable
window before publishing details.

## What this library touches

`desktop-lifecycle` writes small text files inside the user's home directory:

* `~/.config/<app>/` — settings the user may edit
* `~/.local/state/<app>/` — lock file, logs, show-window signal
* `~/.local/share/<app>/` — menu entry and icons
* `~/.cache/<app>/` — disposable data

and on other platforms the equivalent `APPDATA` / `Application Support` paths.

It never asks for root, never writes outside those directories, never starts a
shell, and never makes a network request.

## Classes of issue that matter here

* **Command injection through a path or application name** — anything that can
  break out of a quoted `Exec=` argument.
* **Path traversal through the application name** — e.g. a name that escapes
  its own directory.
* **File permission problems** — a lock or log file another user can read.
* **Symlink attacks** — writing through a link planted in a shared directory.
* **Unexpected elevation** — any code path that requires or suggests `sudo`.

Out of scope: the behaviour of third-party desktops, and the fact that a
deliberately malicious program running as your user can edit your own files.

## Hardening already in place

* application names are validated against an allow-list pattern
* every write is atomic (`mkstemp` + `rename`), with an explicit mode
* lock files are `0600`, directories `0700`
* `Exec=` values are escaped for `"`, `` ` ``, `$` and `\`
* no `shell=True`, no `eval`, no executable path taken from user input
