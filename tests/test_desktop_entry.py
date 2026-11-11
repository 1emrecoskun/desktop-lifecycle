import os
import tempfile
import unittest
from pathlib import Path

from desktop_lifecycle.desktop_entry import (
    build_entry,
    install_icon,
    install_menu_entry,
    remove_menu_entry,
)
from desktop_lifecycle.paths import Paths


class BuildEntryTest(unittest.TestCase):
    def test_required_keys(self):
        text = build_entry(
            name="My Tool", exec_parts=["/usr/bin/my-tool"], comment="Does a thing"
        )
        self.assertTrue(text.startswith("[Desktop Entry]\n"))
        self.assertIn("Type=Application\n", text)
        self.assertIn("Name=My Tool\n", text)
        self.assertIn("Comment=Does a thing\n", text)
        self.assertIn("Exec=\"/usr/bin/my-tool\"\n", text)
        self.assertIn("Terminal=false\n", text)
        self.assertIn("Categories=Utility;\n", text)
        self.assertTrue(text.endswith("\n"))

    def test_arguments_are_quoted_separately(self):
        text = build_entry(
            name="t", exec_parts=["/opt/my app/run", "--flag=a b", "--x"]
        )
        self.assertIn('Exec="/opt/my app/run" "--flag=a b" "--x"', text)

    def test_shell_metacharacters_are_escaped(self):
        text = build_entry(
            name="t", exec_parts=["/tmp/a$HOME", "`id`", 'quote"inside', "back\\slash"]
        )
        exec_line = next(line for line in text.splitlines() if line.startswith("Exec="))
        self.assertIn("\\$HOME", exec_line)
        self.assertIn("\\`id\\`", exec_line)
        self.assertIn('quote\\"inside', exec_line)
        self.assertIn("back\\\\slash", exec_line)

    def test_percent_is_doubled_for_field_codes(self):
        text = build_entry(name="t", exec_parts=["/opt/100%coverage/run"])
        exec_line = next(line for line in text.splitlines() if line.startswith("Exec="))
        self.assertIn("/opt/100%%coverage/run", exec_line)

    def test_newlines_in_values_are_escaped(self):
        text = build_entry(
            name="line\nbreak", exec_parts=["/bin/true"], comment="a\nb"
        )
        self.assertIn("Name=line\\nbreak\n", text)
        self.assertIn("Comment=a\\nb\n", text)
        self.assertNotIn("Name=line\nbreak", text)

    def test_extra_keys(self):
        text = build_entry(
            name="t", exec_parts=["/bin/true"], extra={"X-Custom": "1"}
        )
        self.assertIn("X-Custom=1\n", text)

    def test_rejects_string_command(self):
        with self.assertRaises(TypeError):
            build_entry(name="t", exec_parts="/bin/true")

    def test_rejects_empty_command(self):
        with self.assertRaises(ValueError):
            build_entry(name="t", exec_parts=[])


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.paths = Paths.for_app("my-tool", env={}, system="Linux", home=self.home)

    def test_install_and_remove(self):
        target = install_menu_entry(
            self.paths, "my-tool", ["/usr/bin/my-tool"], comment="Small tool"
        )
        self.assertEqual(
            target, self.home / ".local" / "share" / "applications" / "my-tool.desktop"
        )
        self.assertTrue(target.is_file())
        if os.name != "nt":
            self.assertEqual(target.stat().st_mode & 0o777, 0o644)
        self.assertIn("Exec=", target.read_text(encoding="utf-8"))
        self.assertTrue(remove_menu_entry(self.paths, "my-tool"))
        self.assertFalse(target.exists())
        self.assertFalse(remove_menu_entry(self.paths, "my-tool"))

    def test_install_is_atomic_and_overwrites(self):
        install_menu_entry(self.paths, "my-tool", ["/usr/bin/a"])
        install_menu_entry(self.paths, "my-tool", ["/usr/bin/b"])
        text = (
            self.home / ".local" / "share" / "applications" / "my-tool.desktop"
        ).read_text(encoding="utf-8")
        self.assertIn("/usr/bin/b", text)
        leftovers = list((self.home / ".local" / "share" / "applications").glob(".my-tool*"))
        self.assertEqual(leftovers, [])

    def test_install_icon(self):
        source = self.home / "icon.svg"
        source.write_text("<svg/>", encoding="utf-8")
        target = install_icon(self.paths, source, "my-tool")
        self.assertEqual(
            target,
            self.home
            / ".local"
            / "share"
            / "icons"
            / "hicolor"
            / "scalable"
            / "apps"
            / "my-tool.svg",
        )
        self.assertTrue(target.is_file())
        if os.name != "nt":
            self.assertEqual(target.stat().st_mode & 0o777, 0o644)

    def test_install_icon_missing_source(self):
        with self.assertRaises(FileNotFoundError):
            install_icon(self.paths, self.home / "nope.png", "my-tool")


if __name__ == "__main__":
    unittest.main()
