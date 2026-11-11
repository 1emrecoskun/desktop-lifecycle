import unittest
from unittest import mock

from desktop_lifecycle import tray


class BackendTest(unittest.TestCase):
    def test_result_is_always_a_known_backend(self):
        self.assertIn(tray.backend(), tray.BACKENDS)
        self.assertIn(tray.backend(system="Windows"), tray.BACKENDS)

    def test_none_when_nothing_is_installed(self):
        with mock.patch.object(tray, "_has_namespace", return_value=False), mock.patch.object(
            tray, "_has_pystray", return_value=False
        ):
            self.assertEqual(tray.backend(env={"DISPLAY": ":0"}, system="Linux"), "none")
            self.assertFalse(tray.available(env={"DISPLAY": ":0"}, system="Linux"))

    def test_ayatana_is_preferred(self):
        with mock.patch.object(
            tray, "_has_namespace", side_effect=lambda ns: ns == "AyatanaAppIndicator3"
        ), mock.patch.object(tray, "_has_pystray", return_value=True):
            self.assertEqual(tray.backend(env={"DISPLAY": ":0"}, system="Linux"), "ayatana")

    def test_appindicator_fallback(self):
        with mock.patch.object(
            tray, "_has_namespace", side_effect=lambda ns: ns == "AppIndicator3"
        ), mock.patch.object(tray, "_has_pystray", return_value=True):
            self.assertEqual(
                tray.backend(env={"DISPLAY": ":0"}, system="Linux"), "appindicator"
            )

    def test_pystray_fallback_needs_x11_on_linux(self):
        with mock.patch.object(tray, "_has_namespace", return_value=False), mock.patch.object(
            tray, "_has_pystray", return_value=True
        ):
            self.assertEqual(tray.backend(env={"DISPLAY": ":0"}, system="Linux"), "pystray")
            self.assertEqual(
                tray.backend(env={"WAYLAND_DISPLAY": "w"}, system="Linux"), "none"
            )

    def test_pystray_is_used_off_linux(self):
        with mock.patch.object(tray, "_has_pystray", return_value=True):
            self.assertEqual(tray.backend(env={}, system="Windows"), "pystray")
            self.assertTrue(tray.available(env={}, system="Windows"))


class CreateTest(unittest.TestCase):
    def test_gi_namespace_is_not_the_short_name(self):
        """gi.require_version('ayatana', ...) fails at runtime; the real
        namespace must be passed to the tray implementation."""
        for chosen, expected in (
            ("ayatana", "AyatanaAppIndicator3"),
            ("appindicator", "AppIndicator3"),
        ):
            with self.subTest(chosen=chosen), mock.patch.object(
                tray, "backend", return_value=chosen
            ), mock.patch.object(tray, "_AppIndicatorTray") as implementation:
                tray.create("Title")
            self.assertEqual(implementation.call_args.kwargs["namespace"], expected)

    def test_create_without_backend_raises_with_a_hint(self):
        with mock.patch.object(tray, "backend", return_value="none"):
            with self.assertRaises(tray.TrayUnavailable) as caught:
                tray.create("Title")
        message = str(caught.exception)
        self.assertIn("gir1.2-ayatanaappindicator3-0.1", message)
        self.assertIn("without a tray", message)


if __name__ == "__main__":
    unittest.main()
