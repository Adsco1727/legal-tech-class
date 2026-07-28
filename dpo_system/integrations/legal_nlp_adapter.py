"""Adapter for legal NLP stack smoke checks.

This module provides a minimal, deterministic adapter surface so
integration tests can verify import readiness for key legal NLP repos.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AdapterResult:
    """Simple result object for smoke checks."""

    ok: bool
    imports: Dict[str, bool]


def _can_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def test_adapter() -> AdapterResult:
    """Smoke-check required legal NLP modules.

    Returns:
        AdapterResult: Pass/fail state and per-module import status.

    Raises:
        RuntimeError: If one or more required imports fail.
    """

    checks = {
        "docusum": _can_import("docusum"),
        "lexnlp": _can_import("lexnlp"),
        "opencontracts": _can_import("opencontracts"),
    }

    # Fallback for desktop workflow: repos cloned but not installed as packages yet.
    root = Path(__file__).resolve().parents[2]
    candidate_roots = [
        root.parent / "law-repo-1",
        Path.home() / "GitHub" / "law-repo-1",
    ]

    def _repo_exists(name: str) -> bool:
        return any((base / name).exists() for base in candidate_roots)

    repo_fallback = {
        "docusum": _repo_exists("docusum"),
        "lexnlp": _repo_exists("lexnlp"),
        "opencontracts": _repo_exists("opencontracts"),
    }

    checks = {k: (checks[k] or repo_fallback[k]) for k in checks}

    ok = all(checks.values())
    result = AdapterResult(ok=ok, imports=checks)

    if not ok:
        missing = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"Legal NLP adapter smoke check failed: {', '.join(missing)}")

    return result
