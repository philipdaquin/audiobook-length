import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from audiobook_length import EpubError, estimate, words_from_epub

FIXTURE = Path(__file__).parent / "fixtures" / "lane.epub"


class EpubCountTests(unittest.TestCase):
    def test_fixture_word_count_ignores_css_and_script(self):
        # <h1>Lane</h1> + "The house stood at the end of the lane." = 10 words
        self.assertEqual(words_from_epub(FIXTURE), 10)
        self.assertEqual(estimate(epub=FIXTURE).words, 10)

    def test_missing_file(self):
        with self.assertRaises(EpubError):
            words_from_epub("/tmp/does-not-exist-cocoreader.epub")

    def test_not_a_zip(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake.epub"
            path.write_text("not an epub", encoding="utf-8")
            with self.assertRaises(EpubError):
                words_from_epub(path)

    def test_copy_protected_epub_is_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "locked.epub"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("mimetype", "application/epub+zip")
                zf.writestr(
                    "META-INF/container.xml",
                    """<?xml version="1.0"?>
                    <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                      <rootfiles>
                        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
                      </rootfiles>
                    </container>""",
                )
                zf.writestr("META-INF/encryption.xml", "<encryption/>")
                zf.writestr(
                    "content.opf",
                    """<?xml version="1.0"?>
                    <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bid" version="3.0">
                      <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                        <dc:identifier id="bid">x</dc:identifier>
                        <dc:title>X</dc:title>
                        <dc:language>en</dc:language>
                      </metadata>
                      <manifest>
                        <item id="ch1" href="ch.xhtml" media-type="application/xhtml+xml"/>
                      </manifest>
                      <spine><itemref idref="ch1"/></spine>
                    </package>""",
                )
                zf.writestr("ch.xhtml", "<html><body><p>Hello world</p></body></html>")
            with self.assertRaises(EpubError) as ctx:
                words_from_epub(path)
            self.assertIn("copy-protected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
