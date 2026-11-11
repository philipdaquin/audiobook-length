from __future__ import annotations

import argparse
import sys

from . import __version__
from .calc import (
    DEFAULT_NARRATION_WPM,
    DEFAULT_READING_WPM,
    DEFAULT_SPEED,
    DEFAULT_WORDS_PER_PAGE,
    PLAYBACK_SPEEDS,
    estimate,
    format_duration,
    format_speed_table,
)
from .epub import EpubError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audiobook-length",
        description=(
            "Estimate how long a book takes to listen to at a given narration "
            "pace and playback speed. Defaults match the CocoReader calculator."
        ),
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--words", type=float, help="Word count")
    source.add_argument("--pages", type=float, help="Page count")
    source.add_argument("--text", help="Literal text to count")
    source.add_argument("--text-file", help="Path to a UTF-8 text file")
    source.add_argument("--epub", help="Path to an EPUB")
    parser.add_argument(
        "--words-per-page",
        type=float,
        default=DEFAULT_WORDS_PER_PAGE,
        help=f"Used with --pages (default {DEFAULT_WORDS_PER_PAGE})",
    )
    parser.add_argument(
        "--wpm",
        type=float,
        default=DEFAULT_NARRATION_WPM,
        help=f"Narration pace (default {DEFAULT_NARRATION_WPM})",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=DEFAULT_SPEED,
        help="Playback speed, for example 1.5 (default 1)",
    )
    parser.add_argument(
        "--reading-wpm",
        type=float,
        default=DEFAULT_READING_WPM,
        help=f"Silent reading pace (default {DEFAULT_READING_WPM})",
    )
    parser.add_argument(
        "--fiction",
        action="store_true",
        help="Use 260 wpm for silent reading instead of 238",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="Print listening time at every standard playback speed",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = estimate(
            words=args.words,
            pages=args.pages,
            words_per_page=args.words_per_page,
            text=args.text,
            text_file=args.text_file,
            epub=args.epub,
            narration_wpm=args.wpm,
            speed=args.speed,
            reading_wpm=args.reading_wpm,
            fiction=args.fiction,
        )
    except (EpubError, ValueError, OSError) as exc:
        print(f"audiobook-length: {exc}", file=sys.stderr)
        return 1

    print(f"{result.words:,} words")
    print(f"Listening at {result.speed:g}×, {result.narration_wpm:g} wpm: {result.listening_label}")
    print(f"Reading at {result.reading_wpm:g} wpm: {result.reading_label}")
    print(result.days_label)
    if args.table:
        print()
        for speed, label in format_speed_table(result.words, result.narration_wpm, PLAYBACK_SPEEDS):
            print(f"{speed:g}×  {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
