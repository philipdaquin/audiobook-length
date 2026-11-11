from __future__ import annotations

import re

_WORD_RE = re.compile(r"\S+")


def words_from_text(text: str) -> int:
    """Count whitespace-separated tokens in plain text."""
    if not text:
        return 0
    return len(_WORD_RE.findall(text))
