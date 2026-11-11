import os
import plistlib
import tempfile
import unittest
from pathlib import Path

from desktop_lifecycle.autostart import Autostart


class LinuxAutostartTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)

    def make(self, **kwargs):
        kwargs.setdefault("exec_parts", ["/usr/bin/python3", "-m", "my_app"])
        kwargs.setdefault("env", {})
        kwargs.setdefault("system", "Linux")
        kwargs.setdefault("home", self.home)
        return Autostart("my-app", comment="Small tool", **kwargs)

    def test_enable_writes_xdg_entry(self):
        autostart = self.make()
        self.assertTrue(autostart.enable())
        self.assertTrue(autostart.enabled)
        self.assertEqual(
            autostart.target, self.home / ".config" / "autostart" / "my-app.desktop"
        )
        text = autostart.target.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("[Desktop Entry]"))
        self.assertIn('Exec="/usr/bin/python3" "-m" "my_app" "--background"', text)
        self.assertIn("X-GNOME-Autostart-enabled=true", text)
        self.assertIn("Comment=Small tool", text)

    def test_disable_removes_entry(self):
        autostart = self.make()
        autostart.enable()
        self.assertTrue(autostart.disable())
        self.assertFalse(autostart.enabled)
        self.assertFalse(autostart.target.exists())

    def test_disable_is_idempotent(self):
        autostart = self.make()
        self.assertTrue(autostart.disable())
        self.assertFalse(autostart.enabled)

    def test_toggle(self):
        autostart = self.make()
        self.assertTrue(autostart.toggle())
        self.assertTrue(autostart.enabled)
        self.assertTrue(autostart.toggle())
        self.assertFalse(autostart.enabled)

    def test_hidden_argument_can_be_disabled(self):
        autostart = self.make(hidden_arg=None)
        autostart.enable()
        self.assertNotIn("--background", autostart.target.read_text(encoding="utf-8"))

    def test_custom_arguments_are_kept(self):
        autostart = self.make(args=["--quiet"])
        autostart.enable()
        text = autostart.target.read_text(encoding="utf-8")
        self.assertIn('"--quiet"', text)
        self.assertIn('"--background"', text)

    def test_paths_with_spaces_and_dollars_are_escaped(self):
        autostart = self.make(exec_parts=["/opt/my app/bin/python", "-m", "my_app"])
        autostart.enable()
        text = autostart.target.read_text(encoding="utf-8")
        self.assertIn('Exec="/opt/my app/bin/python"', text)

    def test_rejects_path_like_names(self):
        with self.assertRaises(ValueError):
            Autostart("../evil", ["/bin/true"], env={}, system="Linux", home=self.home)

    def test_rejects_single_string_command(self):
        with self.assertRaises(TypeError):
            Autostart("my-app", "/bin/true", env={}, system="Linux", home=self.home)

    def test_describe(self):
        info = self.make().describe()
        self.assertEqual(info["app"], "my-app")
        self.assertFalse(info["enabled"])
        self.assertIn("--background", info["exec_line"])


class MacAutostartTest(unittest.TestCase):
    def test_writes_launch_agent(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            autostart = Autostart(
                "my-app",
                ["/usr/local/bin/my-app"],
                env={},
                system="Darwin",
                home=home,
            )
            self.assertTrue(autostart.enable())
            target = home / "Library" / "LaunchAgents" / "my-app.plist"
            self.assertEqual(autostart.target, target)
            payload = plistlib.loads(target.read_bytes())
            self.assertTrue(payload["RunAtLoad"])
            self.assertEqual(
                payload["ProgramArguments"], ["/usr/local/bin/my-app", "--background"]
            )
            self.assertTrue(autostart.disable())
            self.assertFalse(target.exists())


class WindowsAutostartTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "runs on a non-Windows host on purpose")
    def test_registry_is_not_touched_off_windows(self):
        with tempfile.TemporaryDirectory() as temporary:
            autostart = Autostart(
                "my-app",
                ["C:/Python/python.exe", "-m", "my_app"],
                env={"APPDATA": "C:/Users/t/AppData/Roaming"},
                system="Windows",
                home=Path(temporary),
            )
            self.assertIn("HKCU:", str(autostart.target))
            self.assertFalse(autostart.enabled)
            self.assertFalse(autostart.enable())
            self.assertTrue(autostart.disable())


if __name__ == "__main__":
    unittest.main()
