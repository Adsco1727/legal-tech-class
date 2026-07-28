"""Downstream sync status helpers for operator control tower notebooks."""

from __future__ import annotations


def get_sync_summary(
    destinations: list[str] | None = None, window: str = "24h"
) -> dict:
    """Return sync summary across downstream destinations."""

    raise NotImplementedError()


def get_pending_retries(destination: str | None = None) -> list[dict]:
    """Return pending retry items."""

    raise NotImplementedError()


def get_last_errors(destination: str | None = None, limit: int = 50) -> list[dict]:
    """Return recent sync errors."""

    raise NotImplementedError()


def trigger_retry(
    destination: str,
    retry_ids: list[str],
    idempotency_key: str,
    dry_run: bool = False,
) -> dict:
    """Trigger a downstream retry with explicit idempotency controls."""

    raise NotImplementedError()
