"""Exception reporting helpers for operator control tower notebooks."""

from __future__ import annotations


def load_failures(run_id: str | None = None, severity: str | None = None) -> list[dict]:
    """Load failure records."""

    raise NotImplementedError()


def load_validation_errors(run_id: str | None = None) -> list[dict]:
    """Load validation errors."""

    raise NotImplementedError()


def load_boundary_violations(run_id: str | None = None) -> list[dict]:
    """Load boundary violation records."""

    raise NotImplementedError()


def summarize_exceptions(run_id: str | None = None) -> dict:
    """Summarize exceptions for the current run."""

    raise NotImplementedError()
