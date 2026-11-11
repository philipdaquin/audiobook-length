import unittest
from io import StringIO
from unittest.mock import patch

from audiobook_length.cli import main

FIXTURE = __import__("pathlib").Path(__file__).parent / "fixtures" / "lane.epub"


class CliTests(unittest.TestCase):
    def test_words_output(self):
        stdout = StringIO()
        with patch("sys.stdout", stdout):
            code = main(["--words", "90000"])
        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("90,000 words", text)
        self.assertIn("9 h 40 m", text)

    def test_epub_output(self):
        stdout = StringIO()
        with patch("sys.stdout", stdout):
            code = main(["--epub", str(FIXTURE)])
        self.assertEqual(code, 0)
        self.assertIn("10 words", stdout.getvalue())

    def test_missing_epub_fails(self):
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            code = main(["--epub", "/tmp/missing-coco-fixture.epub"])
        self.assertEqual(code, 1)
        self.assertIn("audiobook-length:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
