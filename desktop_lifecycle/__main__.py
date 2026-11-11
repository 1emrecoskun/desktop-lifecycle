"""``python -m desktop_lifecycle`` - a read-only environment report.

Paste this into a bug report instead of pasting ``ls -la ~``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys

from . import __version__
from .lifecycle import App
from .tray import _INSTALL_HINT, backend as tray_backend


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="desktop-lifecycle",
        description="Report where a desktop application would write and which "
        "tray backend this session can use.",
    )
    parser.add_argument(
        "--app",
        default="desktop-lifecycle-example",
        help="application name to resolve paths for (default: %(default)s)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--init",
        action="store_true",
        help="create the directories (all other runs are read-only)",
    )
    return parser


def main(argv=None) -> int:
    arguments = _build_parser().parse_args(argv)
    try:
        app = App(arguments.app, argv=[])
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if arguments.init:
        app.ensure_dirs()

    report = app.describe()
    report["tray_install_hint"] = "" if report["tray_backend"] != "none" else _INSTALL_HINT
    report["directories_exist"] = {
        key: Path(value).is_dir()
        for key, value in report["paths"].items()
        if key != "app"
    }

    if arguments.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"desktop-lifecycle {__version__}")
    print(f"  python        {platform.python_version()}")
    print(f"  platform      {report['platform']}")
    print(f"  session       {report['session']}")
    print(f"  tray backend  {report['tray_backend']}")
    print(f"  app name      {report['name']}")
    print("  directories")
    for key, value in report["paths"].items():
        if key == "app":
            continue
        state = "exists" if report["directories_exist"].get(key) else "missing"
        print(f"    {key:<7} {value}  [{state}]")
    if report["tray_install_hint"]:
        print(f"  note          {report['tray_install_hint']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
