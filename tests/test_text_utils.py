import unittest

from simagent import is_blank, normalize_whitespace


class TestTextUtils(unittest.TestCase):
    def test_normalize_whitespace(self) -> None:
        self.assertEqual(normalize_whitespace("  a\t b\n c  "), "a b c")

    def test_is_blank(self) -> None:
        self.assertTrue(is_blank(None))
        self.assertTrue(is_blank("   \n\t"))
        self.assertFalse(is_blank("ok"))


if __name__ == "__main__":
    unittest.main()
