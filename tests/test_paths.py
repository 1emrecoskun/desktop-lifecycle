import os
import tempfile
import unittest
from pathlib import Path

from desktop_lifecycle.paths import Paths


class LinuxPathsTest(unittest.TestCase):
    def setUp(self):
        self.home = Path("/home/tester")
        self.env = {"HOME": str(self.home)}

    def test_defaults_follow_xdg(self):
        paths = Paths.for_app("my-app", env=self.env, system="Linux", home=self.home)
        self.assertEqual(paths.config_home, self.home / ".config")
        self.assertEqual(paths.state_home, self.home / ".local" / "state")
        self.assertEqual(paths.data_home, self.home / ".local" / "share")
        self.assertEqual(paths.cache_home, self.home / ".cache")
        self.assertEqual(paths.config, self.home / ".config" / "my-app")
        self.assertEqual(paths.state, self.home / ".local" / "state" / "my-app")

    def test_state_is_never_the_filesystem_root(self):
        paths = Paths.for_app("my-app", env=self.env, system="Linux", home=self.home)
        self.assertTrue(str(paths.state).startswith(str(self.home)))
        self.assertNotEqual(paths.state.parent.parent, Path("/.local"))

    def test_absolute_overrides_win(self):
        env = {
            "XDG_CONFIG_HOME": "/opt/config",
            "XDG_STATE_HOME": "/var/state",
            "XDG_DATA_HOME": "/srv/data",
            "XDG_CACHE_HOME": "/tmp/cache",
        }
        paths = Paths.for_app("my-app", env=env, system="Linux", home=self.home)
        self.assertEqual(paths.config, Path("/opt/config/my-app"))
        self.assertEqual(paths.state, Path("/var/state/my-app"))
        self.assertEqual(paths.data, Path("/srv/data/my-app"))
        self.assertEqual(paths.cache, Path("/tmp/cache/my-app"))

    def test_relative_overrides_are_ignored(self):
        env = {"XDG_CONFIG_HOME": "relative/dir", "XDG_STATE_HOME": "./state"}
        paths = Paths.for_app("my-app", env=env, system="Linux", home=self.home)
        self.assertEqual(paths.config_home, self.home / ".config")
        self.assertEqual(paths.state_home, self.home / ".local" / "state")

    def test_derived_paths(self):
        paths = Paths.for_app("my-app", env=self.env, system="Linux", home=self.home)
        self.assertEqual(paths.logs, paths.state / "logs")
        self.assertEqual(paths.lock, paths.state / "instance.lock")
        self.assertEqual(paths.show_signal, paths.state / "show-window")

    def test_reversed_dns_name_is_accepted(self):
        paths = Paths.for_app(
            "com.example.app", env=self.env, system="Linux", home=self.home
        )
        self.assertEqual(paths.config.name, "com.example.app")


class WindowsPathsTest(unittest.TestCase):
    def test_appdata_and_localappdata(self):
        home = Path("C:/Users/tester")
        env = {
            "APPDATA": "C:/Users/tester/AppData/Roaming",
            "LOCALAPPDATA": "C:/Users/tester/AppData/Local",
        }
        paths = Paths.for_app("my-app", env=env, system="Windows", home=home)
        self.assertEqual(Path(paths.config), Path("C:/Users/tester/AppData/Roaming/my-app"))
        self.assertEqual(Path(paths.state), Path("C:/Users/tester/AppData/Local/my-app"))
        self.assertEqual(Path(paths.cache), Path("C:/Users/tester/AppData/Local/cache/my-app"))

    def test_falls_back_when_env_is_missing(self):
        home = Path("C:/Users/tester")
        paths = Paths.for_app("my-app", env={}, system="Windows", home=home)
        self.assertEqual(Path(paths.config), home / "AppData" / "Roaming" / "my-app")


class MacPathsTest(unittest.TestCase):
    def test_application_support(self):
        home = Path("/Users/tester")
        paths = Paths.for_app("my-app", env={}, system="Darwin", home=home)
        self.assertEqual(
            paths.config, home / "Library" / "Application Support" / "my-app"
        )
        self.assertEqual(paths.cache, home / "Library" / "Caches" / "my-app")


class ValidationTest(unittest.TestCase):
    def test_rejects_dangerous_names(self):
        for name in ("", " ", "../escape", "a/b", "a\\b", ".hidden", "x" * 65, "trailing."):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    Paths.for_app(name, env={}, system="Linux", home=Path("/home/t"))

    def test_rejects_non_string(self):
        with self.assertRaises(TypeError):
            Paths.for_app(None, env={}, system="Linux", home=Path("/home/t"))


class EnsureTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "POSIX permissions do not exist on Windows")
    def test_creates_directories_with_user_only_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = Paths.for_app("my-app", env={}, system="Linux", home=Path(temporary))
            paths.ensure()
            for directory in (paths.config, paths.state, paths.data, paths.cache):
                self.assertTrue(directory.is_dir())
                self.assertEqual(directory.stat().st_mode & 0o777, 0o700)

    def test_as_dict(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = Paths.for_app("my-app", env={}, system="Linux", home=Path(temporary))
            data = paths.as_dict()
            self.assertEqual(data["app"], "my-app")
            self.assertEqual(data["logs"], str(paths.logs))


if __name__ == "__main__":
    unittest.main()
