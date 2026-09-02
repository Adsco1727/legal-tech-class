"""Tests for dpo_system.src.sec_intelligence.

These tests are fully offline – no network calls are made.
"""
from __future__ import annotations

import sys

import pytest

from dpo_system.src.sec_intelligence import (
    classify_exemption,
    extract_cik,
    python_version,
    score_lead,
)


# ---------------------------------------------------------------------------
# python_version
# ---------------------------------------------------------------------------

def test_python_version_matches_runtime() -> None:
    """python_version() must return the same version the interpreter reports."""
    expected = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    assert python_version() == expected


# ---------------------------------------------------------------------------
# classify_exemption
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Rule 506(b)", "506b"),
        ("Rule 506(c)", "506c"),
        ("Exemption: 506 ( b )", "506b"),
        ("Section 504 exemption", "504"),
        ("No matching rule here", "unknown"),
        ("", "unknown"),
    ],
)
def test_classify_exemption(raw: str, expected: str) -> None:
    assert classify_exemption(raw) == expected


# ---------------------------------------------------------------------------
# extract_cik
# ---------------------------------------------------------------------------

def test_extract_cik_standard() -> None:
    assert extract_cik("Issuer CIK 0001234567") == "0001234567"


def test_extract_cik_short_number_padded() -> None:
    assert extract_cik("CIK 12345") == "0000012345"


def test_extract_cik_missing() -> None:
    assert extract_cik("no cik here") == ""


# ---------------------------------------------------------------------------
# score_lead
# ---------------------------------------------------------------------------

def test_score_lead_full_score() -> None:
    entry = {"title": "Example Inc", "exemption": "506b", "cik": "0001234567"}
    assert score_lead(entry) == 17  # 10 + 5 + 2


def test_score_lead_506c() -> None:
    entry = {"title": "Fund LLC", "exemption": "506c", "cik": "0009876543"}
    assert score_lead(entry) == 17


def test_score_lead_unknown_exemption() -> None:
    entry = {"title": "Boring Corp", "exemption": "unknown", "cik": "0001111111"}
    assert score_lead(entry) == 5  # 0 + 5 + 0


def test_score_lead_no_cik() -> None:
    entry = {"title": "Widget Inc", "exemption": "506b", "cik": ""}
    assert score_lead(entry) == 12  # 10 + 0 + 2


def test_score_lead_empty() -> None:
    assert score_lead({}) == 0
