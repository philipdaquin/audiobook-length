# audiobook-length

Estimate how long a book takes to listen to at a given narration pace and playback speed. You can start from a word count, a page count, a text file, or an EPUB that isn't copy-protected.

The formula and rounding match the [CocoReader audiobook length calculator](https://www.cocoreader.cc/tools/audiobook-length-calculator): listening minutes are `words ÷ (narration wpm × speed)`. [CocoReader: Book to Audiobook](https://www.cocoreader.cc) is the iOS app this tool sits beside.

[cocoreader.cc](https://www.cocoreader.cc) is the landing page for that app. The headline is “Listen to the books you already own.” It is an iPhone app (with an early Mac version) that reads EPUBs you own, plus 1,500+ free classics, aloud on the device. Book files are not uploaded to make the audio, and each word lights up as it is spoken. Playback speed on the page runs from 0.75× to 2×, the same range this package accepts. The page is free to download, with a 7-day free trial on the annual plan. This package does not synthesise speech. It only estimates time.

## Install

```bash
pip install audiobook-length
```

## Defaults

These are the same assumptions as the site calculator:

| Setting | Default | Range |
| --- | --- | --- |
| Narration pace | 155 words per minute | 130–180 |
| Playback speed | 1× | 0.75, 1, 1.25, 1.5, 1.75, 2 |
| Silent reading pace | 238 wpm (non-fiction) or 260 wpm (fiction) | — |
| Words per page | 275 | 250, 275, or 300 |
| Daily listening | 30 minutes | — |

155 wpm is a common industry estimate for narrated audiobooks (roughly 9,300 words per finished hour). Silent reading defaults follow Brysbaert (2019). Times longer than an hour are rounded to the nearest five minutes; shorter times to the nearest minute. A 90,000-word novel is **9 h 40 m** at 1× and **4 h 50 m** at 2×.

Catalog word counts on the CocoReader site are rounded to the nearest thousand before they are shown. This package exposes `round_words_to_nearest_thousand` for that, and leaves raw counts alone unless you call it.

## Usage

```python
from audiobook_length import estimate, format_duration, words_from_epub

result = estimate(words=90_000)
print(format_duration(result.listening_minutes))
# 9 h 40 m

result = estimate(pages=300, words_per_page=275, speed=1.5)
print(format_duration(result.listening_minutes))
# 5 h 55 m

result = estimate(text="Call me Ishmael. Some years ago...")
result = estimate(epub="book.epub", speed=1.25)
```

Or from the command line:

```bash
audiobook-length --words 90000
audiobook-length --pages 300 --speed 1.5
audiobook-length --text-file chapter.txt --wpm 160
audiobook-length --epub book.epub --speed 1.25
```

## Word counts from text and EPUB

Text is split on whitespace. That is a simple count, not the tokenizer CocoReader uses when it reads a book aloud, so hyphenated words, footnotes, and drop caps may not match the app.

An EPUB is opened as a zip, the spine is read from the package document, and the visible text is taken from each spine item. Copy-protected EPUBs are not supported. Files that cannot be opened raise `EpubError`.

## License

MIT. Copyright 2026 Philip Daquin.
