from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union

DEFAULT_WORDS = 90_000
MIN_WORDS = 1_000
MAX_WORDS = 1_000_000
DEFAULT_NARRATION_WPM = 155
MIN_NARRATION_WPM = 130
MAX_NARRATION_WPM = 180
DEFAULT_READING_WPM = 238
FICTION_READING_WPM = 260
DEFAULT_SPEED = 1.0
DEFAULT_DAILY_MINUTES = 30
DEFAULT_WORDS_PER_PAGE = 275
WORDS_PER_PAGE_OPTIONS = (250, 275, 300)
PLAYBACK_SPEEDS = (0.75, 1.0, 1.25, 1.5, 1.75, 2.0)

PathLike = Union[str, Path]


def words_from_pages(pages: float, words_per_page: float = DEFAULT_WORDS_PER_PAGE) -> int:
    if pages < 0 or words_per_page < 0:
        raise ValueError("pages and words_per_page must be zero or greater")
    return int(round(pages * words_per_page))


def listening_minutes(words: float, narration_wpm: float, speed: float) -> float:
    if narration_wpm <= 0 or speed <= 0:
        raise ValueError("narration_wpm and speed must be greater than zero")
    return words / (narration_wpm * speed)


def reading_minutes(words: float, reading_wpm: float = DEFAULT_READING_WPM) -> float:
    if reading_wpm <= 0:
        raise ValueError("reading_wpm must be greater than zero")
    return words / reading_wpm


def round_output_minutes(minutes: float) -> int:
    if minutes != minutes or minutes < 0:  # NaN or negative
        return 0
    if minutes > 60:
        return int(round(minutes / 5.0) * 5)
    return int(round(minutes))


def format_duration(minutes: float) -> str:
    total = round_output_minutes(minutes)
    hours, mins = divmod(total, 60)
    if hours == 0:
        return f"{mins} m"
    return f"{hours} h {mins} m"


def days_at_pace(minutes: float, daily_minutes: float = DEFAULT_DAILY_MINUTES) -> float:
    if daily_minutes <= 0 or daily_minutes != daily_minutes:
        return 0.0
    return round_output_minutes(minutes) / daily_minutes


def format_days(minutes: float, daily_minutes: float = DEFAULT_DAILY_MINUTES) -> str:
    days = days_at_pace(minutes, daily_minutes)
    n = round(days * 10) / 10 if days < 10 else float(round(days))
    if n == int(n):
        n_label = str(int(n))
    else:
        n_label = f"{n:.1f}"
    label = "day" if n == 1 else "days"
    return f"≈ {n_label} {label} at {daily_minutes:g} minutes a day"


def clamp_words(words: float) -> int:
    if words != words:  # NaN
        return DEFAULT_WORDS
    return min(MAX_WORDS, max(MIN_WORDS, int(round(words))))


def round_words_to_nearest_thousand(words: float) -> int:
    if words != words or words < 0:
        return 0
    return int(round(words / 1000.0) * 1000)


def format_approx_words(words: float) -> str:
    return f"about {round_words_to_nearest_thousand(words):,} words"


def _clamp_wpm(narration_wpm: float) -> float:
    if narration_wpm <= 0:
        raise ValueError("narration_wpm must be greater than zero")
    return min(MAX_NARRATION_WPM, max(MIN_NARRATION_WPM, narration_wpm))


@dataclass(frozen=True)
class Estimate:
    words: int
    narration_wpm: float
    speed: float
    reading_wpm: float
    listening_minutes: float
    reading_minutes: float
    daily_minutes: int

    @property
    def listening_label(self) -> str:
        return format_duration(self.listening_minutes)

    @property
    def reading_label(self) -> str:
        return format_duration(self.reading_minutes)

    @property
    def days_label(self) -> str:
        return format_days(self.listening_minutes, self.daily_minutes)


def estimate(
    *,
    words: float | None = None,
    pages: float | None = None,
    words_per_page: float = DEFAULT_WORDS_PER_PAGE,
    text: str | None = None,
    text_file: PathLike | None = None,
    epub: PathLike | None = None,
    narration_wpm: float = DEFAULT_NARRATION_WPM,
    speed: float = DEFAULT_SPEED,
    reading_wpm: float = DEFAULT_READING_WPM,
    fiction: bool = False,
    daily_minutes: int = DEFAULT_DAILY_MINUTES,
    clamp: bool = False,
) -> Estimate:
    """Estimate listening and reading time from one of the supported inputs."""
    supplied = [value is not None for value in (words, pages, text, text_file, epub)]
    if sum(supplied) > 1:
        raise ValueError("pass only one of words, pages, text, text_file, or epub")

    if pages is not None:
        count = words_from_pages(pages, words_per_page)
    elif text is not None:
        from .text import words_from_text

        count = words_from_text(text)
    elif text_file is not None:
        from .text import words_from_text

        count = words_from_text(Path(text_file).read_text(encoding="utf-8"))
    elif epub is not None:
        from .epub import words_from_epub

        count = words_from_epub(epub)
    elif words is not None:
        count = int(round(words))
    else:
        count = DEFAULT_WORDS

    if clamp:
        count = clamp_words(count)
    elif count < 0:
        raise ValueError("word count must be zero or greater")

    pace = _clamp_wpm(narration_wpm)
    read_pace = FICTION_READING_WPM if fiction else reading_wpm
    listen = listening_minutes(count, pace, speed)
    read = reading_minutes(count, read_pace)
    return Estimate(
        words=count,
        narration_wpm=pace,
        speed=speed,
        reading_wpm=read_pace,
        listening_minutes=listen,
        reading_minutes=read,
        daily_minutes=daily_minutes,
    )


def format_speed_table(
    words: float,
    narration_wpm: float = DEFAULT_NARRATION_WPM,
    speeds: Iterable[float] = PLAYBACK_SPEEDS,
) -> list[tuple[float, str]]:
    return [
        (item, format_duration(listening_minutes(words, narration_wpm, item)))
        for item in speeds
    ]
