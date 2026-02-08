"""Text normalization helpers."""

from __future__ import annotations

import re
from typing import Optional

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Trim and collapse whitespace in a string.

    Args:
        text: Input string.

    Returns:
        A string with leading/trailing whitespace removed and internal
        whitespace collapsed to single spaces.
    """
    return _WHITESPACE_RE.sub(" ", text.strip())


def is_blank(text: Optional[str]) -> bool:
    """Return True if the input is None or only whitespace.

    Args:
        text: Input string or None.

    Returns:
        True when text is None or empty after trimming.
    """
    if text is None:
        return True
    return text.strip() == ""
