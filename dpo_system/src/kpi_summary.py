"""KPI summary helpers for operator control tower notebooks."""

from __future__ import annotations


def build_snapshot(run_id: str | None = None, window: str = "24h") -> dict:
    """Build a KPI snapshot for the requested window."""

    raise NotImplementedError()


def compute_trends(run_id: str | None = None, window: str = "7d") -> dict:
    """Compute KPI trends."""

    raise NotImplementedError()


def compute_idempotency_health(run_id: str | None = None) -> dict:
    """Assess idempotency health for the current run."""

    raise NotImplementedError()


def validate_kpi_totals(snapshot: dict) -> None:
    """Validate KPI totals and raise if they do not reconcile."""

    raise NotImplementedError()
