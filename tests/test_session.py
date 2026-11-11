import unittest

from desktop_lifecycle.session import has_gui, is_linux, is_wayland, is_x11, session_type


class SessionDetectionTest(unittest.TestCase):
    def test_declared_wayland_wins_over_xwayland_display(self):
        env = {"XDG_SESSION_TYPE": "wayland", "DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"}
        self.assertEqual(session_type(env, "Linux"), "wayland")

    def test_declared_x11(self):
        env = {"XDG_SESSION_TYPE": "X11", "DISPLAY": ":0"}
        self.assertEqual(session_type(env, "Linux"), "x11")

    def test_wayland_display_without_declaration(self):
        env = {"WAYLAND_DISPLAY": "wayland-0"}
        self.assertEqual(session_type(env, "Linux"), "wayland")

    def test_display_only_is_x11(self):
        env = {"DISPLAY": ":1"}
        self.assertEqual(session_type(env, "Linux"), "x11")

    def test_headless_is_unknown(self):
        self.assertEqual(session_type({}, "Linux"), "unknown")
        self.assertFalse(has_gui({}, "Linux"))

    def test_windows_and_macos_ignore_display_variables(self):
        self.assertEqual(session_type({}, "Windows"), "windows")
        self.assertEqual(session_type({}, "Darwin"), "macos")
        self.assertTrue(has_gui({}, "Windows"))

    def test_helpers(self):
        self.assertTrue(is_linux({}, "Linux"))
        self.assertFalse(is_linux({}, "Windows"))
        self.assertTrue(is_x11({"DISPLAY": ":0"}, "Linux"))
        self.assertTrue(is_wayland({"WAYLAND_DISPLAY": "w"}, "Linux"))

    def test_does_not_mutate_environment(self):
        env = {"DISPLAY": ":0"}
        session_type(env, "Linux")
        self.assertEqual(env, {"DISPLAY": ":0"})


if __name__ == "__main__":
    unittest.main()
