"""Workflow replay and diagnostics helpers for the DPO operator ledger."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dpo_ledger_tools import LedgerAPI


def _normalize_repo(repo: str) -> str:
    repo = str(repo).strip()
    if not repo:
        return ""
    if repo.startswith("dpo-"):
        return repo
    return f"dpo-{repo}"


def _extract_repo_history(row: dict[str, Any]) -> list[str]:
    repos: list[str] = []
    notes = str(row.get("notes", ""))
    for token in notes.split("|"):
        token = token.strip()
        if token.startswith("processed_by="):
            repo = _normalize_repo(token.split("=", 1)[1].strip())
            if repo and repo not in repos:
                repos.append(repo)
        elif token.startswith("source_repo="):
            repo = _normalize_repo(token.split("=", 1)[1].strip())
            if repo and repo not in repos:
                repos.append(repo)

    origin_repo = _normalize_repo(str(row.get("origin_repo", "")).strip())
    if origin_repo and origin_repo not in repos:
        repos.append(origin_repo)

    return repos


def build_workflow_replay(ledger_path: str | Path, workflow_id: str) -> dict[str, Any]:
    """Reconstruct the hop history for a workflow from ledger queue rows."""
    ledger = LedgerAPI(ledger_path)
    rows: list[dict[str, Any]] = []

    for sheet_name in ["INGESTION_QUEUE", "CLAUSE_QUEUE", "CRM_QUEUE", "GOVERNANCE_QUEUE"]:
        for row in ledger.read_rows(sheet_name):
            if str(row.get("workflow_id", "")).strip() != str(workflow_id):
                continue
            rows.append({"sheet": sheet_name, **row})

    if not rows:
        raise KeyError(f"no workflow rows found for {workflow_id}")

    ordered_rows = sorted(rows, key=lambda row: (int(str(row.get("hop_count", 0))), row.get("sheet", "")))

    chain: list[str] = []
    for row in ordered_rows:
        for repo in _extract_repo_history(row):
            if repo:
                chain.append(repo)

    hop_chain = " → ".join(chain)

    return {
        "workflow_id": str(workflow_id),
        "total_hops": len(ordered_rows),
        "hop_chain": hop_chain,
        "rows": ordered_rows,
    }
