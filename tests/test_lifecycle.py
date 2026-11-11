import tempfile
import unittest
from pathlib import Path

from desktop_lifecycle.lifecycle import App


class AppTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)

    def make(self, argv=()):
        return App("my-tool", argv=list(argv), env={}, system="Linux", home=self.home)

    def test_paths_and_session_are_resolved(self):
        app = self.make()
        self.assertEqual(app.paths.app, "my-tool")
        self.assertEqual(app.session, "unknown")

    def test_background_flags(self):
        self.assertTrue(self.make(["--background"]).background_requested)
        self.assertTrue(self.make(["--tray"]).background_requested)
        self.assertTrue(self.make(["--minimized"]).background_requested)
        self.assertFalse(self.make([]).background_requested)
        self.assertFalse(self.make(["--verbose"]).background_requested)

    def test_background_flags_can_be_customised(self):
        app = App(
            "my-tool", argv=["-d"], env={}, system="Linux", home=self.home,
            background_flags=("-d",),
        )
        self.assertTrue(app.background_requested)

    def test_second_instance_requests_show(self):
        first = self.make()
        second = self.make()
        self.assertTrue(first.acquire())
        self.addCleanup(first.release)
        self.assertFalse(second.acquire())
        self.assertTrue(first.paths.show_signal.exists())
        self.assertTrue(first.poll_show_request())
        self.assertFalse(first.poll_show_request())

    def test_stale_show_request_is_cleared_on_acquire(self):
        app = self.make()
        app.paths.ensure()
        app.paths.show_signal.write_text("", encoding="utf-8")
        self.assertTrue(app.acquire())
        self.addCleanup(app.release)
        self.assertFalse(app.paths.show_signal.exists())
        self.assertFalse(app.poll_show_request())

    def test_release_allows_another_instance(self):
        first = self.make()
        first.acquire()
        first.release()
        second = self.make()
        self.assertTrue(second.acquire())
        second.release()

    def test_ensure_dirs_and_logging(self):
        app = self.make()
        log_path = app.setup_logging()
        self.assertTrue(log_path.is_file())
        self.assertEqual(log_path.parent, app.paths.logs)
        self.assertTrue(app.paths.config.is_dir())

    def test_describe(self):
        report = self.make(["--background"]).describe()
        for key in ("version", "name", "python", "platform", "session", "tray_backend", "paths"):
            self.assertIn(key, report)
        self.assertEqual(report["name"], "my-tool")
        self.assertTrue(report["background_requested"])

    def test_autostart_uses_given_command(self):
        app = self.make()
        autostart = app.autostart(["/usr/bin/my-tool"])
        self.assertTrue(autostart.enable())
        self.assertTrue(autostart.enabled)
        self.assertTrue(autostart.disable())

    def test_menu_entry(self):
        app = self.make()
        target = app.install_menu_entry(["/usr/bin/my-tool"], comment="Small tool")
        self.assertTrue(target.is_file())

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            App("../escape", env={}, system="Linux", home=self.home)


if __name__ == "__main__":
    unittest.main()
