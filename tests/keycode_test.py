import unittest
from interactive_python import keycode

class TestKeycode(unittest.TestCase):
    def test_gives_aliased_codes(self):
        self.assertEqual(91, keycode.cmd)

    def test_gives_non_aliawses(self):
        self.assertEqual(65, keycode.a)

    def test_raises_on_invalid_codes(self):
        with self.assertRaises(AttributeError):
            keycode.A

        with self.assertRaises(AttributeError):
            keycode.wut
