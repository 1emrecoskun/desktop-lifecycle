## What this changes

<!-- One paragraph. Link the issue if there is one: Fixes #123 -->

## Why

<!-- The bug report or the use case, not the implementation. -->

## How it was verified

- [ ] `python -m unittest discover -s tests -v` passes
- [ ] `python -m compileall -q desktop_lifecycle tests` is clean
- [ ] A new or updated test fails without this change
- [ ] `python -m desktop_lifecycle` still runs

## Platform notes

<!-- Which of Linux X11 / Wayland / Windows / macOS did you actually run this
on? Be honest about what you could not test. -->

## Checklist

- [ ] The public API only grew; nothing existing was renamed or removed
- [ ] No new runtime dependency (`pyproject.toml` declares `dependencies = []`)
- [ ] No `sudo`, no writes outside the user's home directory
- [ ] No personal paths, tokens, MAC addresses or usernames in the diff
- [ ] Documentation updated when behaviour is user-visible
- [ ] No `CHANGELOG.md` entry (the maintainer writes it at release time)
