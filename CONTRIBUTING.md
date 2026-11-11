# Contributing

Thanks for taking the time. This project is deliberately small; keeping it
small is part of the design.

## Before you start

Open an issue first for anything larger than a bug fix. The scope is "the
boring parts around a GUI application", not "a desktop framework".

## What fits

* fixing a platform-specific path, quoting or locking bug
* supporting a desktop environment or tray backend that genuinely misbehaves
* tests that reproduce a real bug report
* documentation fixes, especially for Wayland and Windows

## What does not fit

* drawing UI, a widget set, or a tray implementation of our own
* network features, telemetry, accounts
* anything that needs `sudo` or writes outside the user's home directory
* new runtime dependencies (the zero-dependency promise is the point)

## Development

```bash
git clone https://github.com/1emrecoskun/desktop-lifecycle
cd desktop-lifecycle
python -m unittest discover -s tests -v
```

There is nothing to install: the package has no runtime dependencies, and the
tests need neither a display nor hardware.

A quick sanity check of the code itself:

```bash
python -m compileall -q desktop_lifecycle tests
python -m desktop_lifecycle
```

## Pull requests

* one topic per pull request
* a test for every behaviour change — tests that fail before your fix
* keep the public API additive where possible; this library is used by
  applications that cannot be updated in lockstep
* do not add a `CHANGELOG` entry; the maintainer writes it at release time

## Sign-off (Developer Certificate of Origin)

Every commit must carry a `Signed-off-by` line:

```bash
git commit -s -m "Fix Exec quoting for paths containing a dollar sign"
```

That line certifies the [Developer Certificate of Origin 1.1](https://developercertificate.org/):
you wrote the change, or you have the right to submit it under this project's
licence. It is what keeps the project MIT without asking every contributor to
sign a separate contract.

## Commit messages

Short imperative subject, for example:

```
Fix Exec quoting for paths containing a dollar sign
```

## Code style

Plain Python, no formatter required. Type hints where they help. Comments
should explain *why*, not restate the code. Keep functions small enough to
read on one screen.

## Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
