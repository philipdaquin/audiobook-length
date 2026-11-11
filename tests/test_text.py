import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from audiobook_length import estimate, words_from_text


class TextCountTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(words_from_text(""), 0)
        self.assertEqual(words_from_text("   \n\t"), 0)

    def test_simple_sentence(self):
        self.assertEqual(words_from_text("Call me Ishmael."), 3)

    def test_collapses_whitespace(self):
        self.assertEqual(words_from_text("one   two\nthree"), 3)

    def test_estimate_from_text_and_file(self):
        text = "one two three four five"
        result = estimate(text=text, narration_wpm=155, speed=1)
        self.assertEqual(result.words, 5)
        with NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            handle.write(text)
            path = Path(handle.name)
        try:
            self.assertEqual(estimate(text_file=path).words, 5)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
