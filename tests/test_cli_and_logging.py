import contextlib
import io
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from desktop_lifecycle.__main__ import main
from desktop_lifecycle.logging_setup import setup_logging
from desktop_lifecycle.paths import Paths


class CliTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)

    def environment(self):
        """A home directory for every platform, so nothing escapes to the real one."""
        return {
            "HOME": str(self.home),
            "USERPROFILE": str(self.home),
            "APPDATA": str(self.home / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(self.home / "AppData" / "Local"),
        }

    def run_cli(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.dict("os.environ", self.environment()), contextlib.redirect_stdout(
            stdout
        ), contextlib.redirect_stderr(stderr):
            code = main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def files(self):
        return sorted(str(path.relative_to(self.home)) for path in self.home.rglob("*"))

    def test_json_report_is_valid_and_read_only(self):
        before = self.files()
        code, out, _ = self.run_cli(["--app", "cli-test", "--json"])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["name"], "cli-test")
        self.assertIn("session", report)
        self.assertIn("tray_backend", report)
        self.assertEqual(before, self.files(), "the report created files")
        self.assertFalse(
            any(report["directories_exist"].values()), report["directories_exist"]
        )

    def test_bad_app_name_is_a_usage_error(self):
        code, out, err = self.run_cli(["--app", "../escape"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("invalid application name", err)

    def test_init_creates_directories(self):
        with mock.patch.dict("os.environ", self.environment()), contextlib.redirect_stdout(
            io.StringIO()
        ):
            code = main(["--app", "cli-test", "--init", "--json"])
            paths = Paths.for_app("cli-test")
        self.assertEqual(code, 0)
        self.assertTrue(paths.state.is_dir())
        self.assertTrue(paths.config.is_dir())

    def test_text_report_mentions_the_version(self):
        code, out, _ = self.run_cli(["--app", "cli-test"])
        self.assertEqual(code, 0)
        self.assertIn("desktop-lifecycle", out)
        self.assertIn("tray backend", out)


class LoggingTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self._reset_root_logger)
        self.home = Path(self.temporary.name)
        self.paths = Paths.for_app("log-test", env={}, system="Linux", home=self.home)

    @staticmethod
    def _reset_root_logger():
        root = logging.getLogger()
        for handler in list(root.handlers):
            root.removeHandler(handler)
            handler.close()

    def test_writes_to_the_state_directory(self):
        target = setup_logging(self.paths)
        self.assertEqual(target.parent, self.paths.logs)
        logging.getLogger("test").warning("hello")
        for handler in logging.getLogger().handlers:
            handler.flush()
        self.assertIn("hello", target.read_text(encoding="utf-8"))

    def test_rejects_a_path_as_filename(self):
        with self.assertRaises(ValueError):
            setup_logging(self.paths, filename="../escape.log")
        with self.assertRaises(ValueError):
            setup_logging(self.paths, filename="..")

    def test_replaces_an_existing_rotating_handler(self):
        first = setup_logging(self.paths)
        setup_logging(self.paths, filename="other.log")
        rotating = [
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, logging.handlers.RotatingFileHandler)
        ]
        self.assertEqual(len(rotating), 1)
        logging.getLogger("test").warning("only-once")
        for handler in logging.getLogger().handlers:
            handler.flush()
        self.assertNotIn("only-once", first.read_text(encoding="utf-8"))
        self.assertIn(
            "only-once", (self.paths.logs / "other.log").read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
