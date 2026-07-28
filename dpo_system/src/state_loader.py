"""State loading helpers for operator control tower notebooks."""

from __future__ import annotations


def load_run_context(run_id: str | None = None) -> dict:
    """Load the current run context."""

    raise NotImplementedError()


def load_boundary_map() -> dict:
    """Load the runtime boundary map."""

    raise NotImplementedError()


def load_contract_status() -> dict:
    """Load contract validation status."""

    raise NotImplementedError()


def get_current_run_summary(run_id: str | None = None) -> dict:
    """Return a summary of the current run."""

    raise NotImplementedError()


def get_state_snapshot(scope: str, run_id: str | None = None) -> dict:
    """Return a state snapshot for a given scope."""

    raise NotImplementedError()
