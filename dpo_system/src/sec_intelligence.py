"""SEC Intelligence slice.

Provides lightweight helpers for parsing and classifying SEC EDGAR
Regulation D (Form D) feed entries.  This module does NOT contact any
live SEC endpoint; all network I/O is injected via optional callables so
the logic can be exercised fully offline in tests.
"""
from __future__ import annotations

import re
import sys
from typing import Any


def python_version() -> str:
    """Return the running Python version string, e.g. '3.11.13'."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def classify_exemption(raw: str) -> str:
    """Return a canonical exemption label from a raw SEC filing text excerpt.

    Recognised patterns
    -------------------
    ``506(b)`` → ``"506b"``
    ``506(c)`` → ``"506c"``
    ``504``    → ``"504"``
    Anything else → ``"unknown"``
    """
    if re.search(r"506\s*\(\s*b\s*\)", raw, re.IGNORECASE):
        return "506b"
    if re.search(r"506\s*\(\s*c\s*\)", raw, re.IGNORECASE):
        return "506c"
    if re.search(r"\b504\b", raw, re.IGNORECASE):
        return "504"
    return "unknown"


def extract_cik(raw: str) -> str:
    """Return the first CIK found in *raw*, zero-padded to 10 digits.

    Returns an empty string when no CIK-like sequence is found.
    """
    match = re.search(r"(?:CIK|cik)[^\d]*(\d{1,10})", raw, re.IGNORECASE)
    if match:
        return match.group(1).zfill(10)
    return ""


def score_lead(entry: dict[str, Any]) -> int:
    """Return a simple integer priority score for a RegD lead entry.

    Scoring rules (additive):
    - Exemption is ``506b`` or ``506c`` → +10
    - CIK is non-empty → +5
    - Title contains ``"Inc"`` or ``"LLC"`` → +2
    """
    score = 0
    if entry.get("exemption") in ("506b", "506c"):
        score += 10
    if entry.get("cik"):
        score += 5
    title: str = entry.get("title", "")
    if re.search(r"\b(Inc|LLC)\b", title, re.IGNORECASE):
        score += 2
    return score
