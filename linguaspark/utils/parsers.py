r"""Input parsing helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List


# Top-level (record) separator: a newline. A line is one vocabulary entry,
# so multi-word phrases like "to evaluate" or "to be" stay intact.
#
# In-line (extra) separators inside a single line: comma, semicolon, pipe.
# These are useful for paste-as-CSV but rare; the dominant case is one
# term per line.
_RECORD_SEP_RE = re.compile(r"[\r\n]+")
_INLINE_SEP_RE = re.compile(r"[,;|]+")


def parse_word_list(text: str) -> List[str]:
    """Parse a free-form block of text into a clean, deduplicated word list.

    Default rule: **one vocabulary entry per line**. This preserves
    multi-word phrases such as ``to evaluate``, ``to be``, ``at once``.

    Secondary rules:
      - Inline separators (``,``, ``;``, ``|``) also split a line, so a
        single-line paste like ``apple, banana; cherry`` becomes three
        entries.
      - Whitespace inside a line is collapsed (so ``to  evaluate``
        becomes ``to evaluate``).
      - Each entry is trimmed of surrounding whitespace and outer
        punctuation: double quote, single quote, backtick, asterisk,
        underscore, parentheses, period, colon, exclamation, question
        mark, hyphen.
      - Empty entries are dropped.
      - Duplicates are removed case-insensitively, preserving the casing
        of the first occurrence.
    """
    if not text:
        return []

    seen: set[str] = set()
    out: List[str] = []
    _PUNCT = "\"'`*_().:!?-"

    for raw_line in _RECORD_SEP_RE.split(text):
        # Optional: split this line on inline separators too.
        for raw in _INLINE_SEP_RE.split(raw_line):
            # Collapse runs of internal whitespace so "to  evaluate" and
            # "to\tevaluate" both become "to evaluate".
            cleaned = re.sub(r"\s+", " ", raw.strip().strip(_PUNCT).strip())
            if not cleaned:
                continue
            key = cleaned.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(cleaned)
    return out


def load_words_from_file(path: str | Path) -> List[str]:
    """Read a UTF-8 text file and return a parsed word list."""
    content = Path(path).read_text(encoding="utf-8")
    return parse_word_list(content)


def chunked(items: Iterable, size: int) -> List[List]:
    """Split an iterable into fixed-size chunks (last chunk may be smaller)."""
    if size <= 0:
        raise ValueError("chunk size must be positive")
    items = list(items)
    return [items[i : i + size] for i in range(0, len(items), size)]
