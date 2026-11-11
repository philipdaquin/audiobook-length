import unittest

from audiobook_length import (
    DEFAULT_NARRATION_WPM,
    clamp_words,
    days_at_pace,
    estimate,
    format_days,
    format_duration,
    listening_minutes,
    reading_minutes,
    round_words_to_nearest_thousand,
    words_from_pages,
)
from audiobook_length.calc import format_approx_words, format_speed_table, round_output_minutes


class CalculatorAcceptanceTests(unittest.TestCase):
    """PHI-639 cases from the CocoReader site calculator."""

    def test_90000_words_at_1x_is_9h_40m(self):
        self.assertEqual(
            format_duration(listening_minutes(90_000, DEFAULT_NARRATION_WPM, 1)),
            "9 h 40 m",
        )

    def test_90000_words_at_2x_is_4h_50m(self):
        self.assertEqual(
            format_duration(listening_minutes(90_000, DEFAULT_NARRATION_WPM, 2)),
            "4 h 50 m",
        )

    def test_300_pages_at_1_5x_is_5h_55m(self):
        self.assertEqual(
            format_duration(
                listening_minutes(words_from_pages(300, 275), DEFAULT_NARRATION_WPM, 1.5)
            ),
            "5 h 55 m",
        )

    def test_90000_words_reading_at_238_is_6h_20m(self):
        self.assertEqual(format_duration(reading_minutes(90_000, 238)), "6 h 20 m")

    def test_library_word_counts_round_to_nearest_thousand(self):
        self.assertEqual(round_words_to_nearest_thousand(48_465), 48_000)
        self.assertEqual(round_words_to_nearest_thousand(77_898), 78_000)
        self.assertEqual(round_words_to_nearest_thousand(121_970), 122_000)
        self.assertEqual(format_approx_words(48_465), "about 48,000 words")

    def test_rounded_library_examples_at_1x(self):
        self.assertEqual(format_duration(listening_minutes(48_000, DEFAULT_NARRATION_WPM, 1)), "5 h 10 m")
        self.assertEqual(format_duration(listening_minutes(78_000, DEFAULT_NARRATION_WPM, 1)), "8 h 25 m")
        self.assertEqual(format_duration(listening_minutes(122_000, DEFAULT_NARRATION_WPM, 1)), "13 h 5 m")


class RoundingAndHelpersTests(unittest.TestCase):
    def test_under_an_hour_rounds_to_nearest_minute(self):
        self.assertEqual(round_output_minutes(14.4), 14)
        self.assertEqual(format_duration(14.4), "14 m")

    def test_over_an_hour_rounds_to_nearest_five(self):
        self.assertEqual(round_output_minutes(61), 60)
        self.assertEqual(format_duration(62), "1 h 0 m")

    def test_days_at_pace(self):
        minutes = listening_minutes(90_000, DEFAULT_NARRATION_WPM, 1)
        self.assertAlmostEqual(days_at_pace(minutes, 30), 580 / 30)
        self.assertEqual(
            format_days(minutes, 30),
            "≈ 19 days at 30 minutes a day",
        )

    def test_clamp_words(self):
        self.assertEqual(clamp_words(10), 1_000)
        self.assertEqual(clamp_words(2_000_000), 1_000_000)
        self.assertEqual(clamp_words(float("nan")), 90_000)

    def test_estimate_default_and_pages(self):
        default = estimate()
        self.assertEqual(default.words, 90_000)
        self.assertEqual(default.listening_label, "9 h 40 m")
        paged = estimate(pages=300, speed=1.5)
        self.assertEqual(paged.words, 82_500)
        self.assertEqual(paged.listening_label, "5 h 55 m")

    def test_fiction_reading_pace(self):
        result = estimate(words=90_000, fiction=True)
        self.assertEqual(result.reading_wpm, 260)
        self.assertEqual(result.reading_label, "5 h 45 m")

    def test_rejects_multiple_sources(self):
        with self.assertRaises(ValueError):
            estimate(words=1000, pages=10)

    def test_speed_table_covers_standard_speeds(self):
        table = format_speed_table(90_000)
        self.assertEqual([row[0] for row in table], [0.75, 1.0, 1.25, 1.5, 1.75, 2.0])
        self.assertEqual(dict(table)[1.0], "9 h 40 m")
        self.assertEqual(dict(table)[2.0], "4 h 50 m")


if __name__ == "__main__":
    unittest.main()
