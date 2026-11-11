import os
import tempfile
import unittest
from pathlib import Path

from desktop_lifecycle.single_instance import AlreadyRunning, SingleInstance


class SingleInstanceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.lock = self.root / "state" / "instance.lock"
        self.signal = self.root / "state" / "show-window"

    def make(self):
        return SingleInstance(self.lock, self.signal)

    def test_second_acquire_fails(self):
        first = self.make()
        second = self.make()
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        first.release()
        self.assertTrue(second.acquire())
        second.release()

    def test_release_then_reacquire(self):
        instance = self.make()
        self.assertTrue(instance.acquire())
        instance.release()
        self.assertFalse(instance.held)
        again = self.make()
        self.assertTrue(again.acquire())
        again.release()

    def test_acquire_is_idempotent(self):
        instance = self.make()
        self.assertTrue(instance.acquire())
        self.assertTrue(instance.acquire())
        instance.release()

    @unittest.skipIf(os.name == "nt", "POSIX permissions do not exist on Windows")
    def test_lock_file_is_private_and_contains_pid(self):
        instance = self.make()
        instance.acquire()
        self.addCleanup(instance.release)
        self.assertEqual(self.lock.stat().st_mode & 0o777, 0o600)
        self.assertEqual(instance.owner_pid(), os.getpid())

    def test_show_signal_round_trip(self):
        first = self.make()
        second = self.make()
        first.acquire()
        self.addCleanup(first.release)
        self.assertFalse(second.acquire())
        # The losing instance is the one that asks; ``App.acquire()`` does this
        # for you, ``SingleInstance`` keeps the two concerns separate.
        self.assertTrue(second.request_show())
        self.assertTrue(self.signal.exists())
        self.assertTrue(first.consume_show_request())
        self.assertFalse(first.consume_show_request())
        self.assertFalse(self.signal.exists())

    def test_request_show_without_signal_path_is_a_noop(self):
        instance = SingleInstance(self.lock)
        self.assertFalse(instance.request_show())
        self.assertFalse(instance.consume_show_request())

    def test_context_manager(self):
        with self.make() as instance:
            self.assertTrue(instance.held)
        self.assertFalse(instance.held)

    def test_acquire_or_raise(self):
        first = self.make()
        first.acquire()
        self.addCleanup(first.release)
        with self.assertRaises(AlreadyRunning):
            self.make().acquire_or_raise()

    def test_missing_lock_file_owner_is_none(self):
        self.assertIsNone(self.make().owner_pid())


if __name__ == "__main__":
    unittest.main()
