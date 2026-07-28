"""Queue view helpers for operator control tower notebooks."""

from __future__ import annotations


def count_by_state(run_id: str | None = None, filters: dict | None = None) -> dict:
    """Count queue items by state."""

    raise NotImplementedError()


def list_items_by_state(
    states: list[str], run_id: str | None = None, filters: dict | None = None
) -> list[dict]:
    """List queue items for the requested states."""

    raise NotImplementedError()


def get_aging_metrics(run_id: str | None = None, threshold_hours: int = 24) -> dict:
    """Return queue aging metrics."""

    raise NotImplementedError()


def get_queue_item(item_id: str) -> dict:
    """Return a single queue item by identifier."""

    raise NotImplementedError()
