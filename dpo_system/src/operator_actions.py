from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from . import audit_writer, ledger_io as ledger
from .audit_writer import make_idempotency_key

OPERATOR_NAME = "DPO"  # adjust if you want multi-operator support


def approve_batch(
    *,
    batch_ids: list[str],
    who: str,
    why: str,
    reason_code: str,
    evidence_refs: list[str],
    idempotency_key: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Write an audited approval decision for one or more batches."""
    if idempotency_key is None:
        idempotency_key = make_idempotency_key(
            "approve_batch",
            list(batch_ids),
            who,
            reason_code,
        )

    event = {
        "who": who,
        "when": audit_writer._current_utc(),
        "what": "approve_batch",
        "why": why,
        "reason_code": reason_code,
        "evidence_refs": list(evidence_refs),
        "targets": list(batch_ids),
        "dry_run": bool(dry_run),
    }
    result = audit_writer.write_decision_event(event, idempotency_key)
    return {
        "status": result["status"],
        "mutated": bool(result.get("written", False)),
        "idempotency_key": idempotency_key,
        "payload_hash": result.get("payload_hash"),
    }


def reject_batch(
    *,
    batch_ids: list[str],
    who: str,
    why: str,
    reason_code: str,
    evidence_refs: list[str],
    idempotency_key: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Write an audited rejection decision for one or more batches."""
    if idempotency_key is None:
        idempotency_key = make_idempotency_key(
            "reject_batch",
            list(batch_ids),
            who,
            reason_code,
        )

    event = {
        "who": who,
        "when": audit_writer._current_utc(),
        "what": "reject_batch",
        "why": why,
        "reason_code": reason_code,
        "evidence_refs": list(evidence_refs),
        "targets": list(batch_ids),
        "dry_run": bool(dry_run),
    }
    result = audit_writer.write_decision_event(event, idempotency_key)
    return {
        "status": result["status"],
        "mutated": bool(result.get("written", False)),
        "idempotency_key": idempotency_key,
        "payload_hash": result.get("payload_hash"),
    }


def _now_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


# ---------------------------
# REPO STATE OPERATIONS
# ---------------------------

def register_repo(repo_name: str, repo_slug: str, wave: int, notes: str = ""):
    row = {
        "repo_name": repo_name,
        "repo_slug": repo_slug,
        "wave": wave,
        "enabled": True,
        "last_pull": "",
        "last_commit": "",
        "status": "OK",
        "notes": notes,
    }
    ledger.append_row("REPO_STATE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "register_repo",
        repo_slug,
        status="ok",
        notes=notes,
    )


def update_repo_status(repo_slug: str, status: str, last_commit: str = "", notes: str = ""):
    ledger.validate_enum(ledger.REPO_STATUS, status, "status")
    updates = {
        "status": status,
        "last_commit": last_commit,
        "last_pull": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("REPO_STATE", "repo_slug", repo_slug, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_repo_status",
        repo_slug,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# INGESTION QUEUE OPERATIONS
# ---------------------------

def queue_ingestion_batch(source_repo: str, source_path: str, ingestion_type: str, priority: int = 3, notes: str = ""):
    ledger.validate_enum(ledger.INGESTION_TYPES, ingestion_type, "ingestion_type")
    batch_id = _now_id("ingest")
    row = {
        "batch_id": batch_id,
        "source_repo": source_repo,
        "source_path": source_path,
        "ingestion_type": ingestion_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "notes": notes,
    }
    ledger.append_row("INGESTION_QUEUE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_ingestion_batch",
        batch_id,
        status="ok",
        notes=notes,
    )
    return batch_id


def update_ingestion_status(batch_id: str, status: str, notes: str = ""):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("INGESTION_QUEUE", "batch_id", batch_id, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_ingestion_status",
        batch_id,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# CLAUSE QUEUE OPERATIONS
# ---------------------------

def queue_clause_task(contract_id: str, clause_engine: str, analysis_type: str, priority: int = 3, notes: str = ""):
    ledger.validate_enum(ledger.CLAUSE_ENGINES, clause_engine, "clause_engine")
    ledger.validate_enum(ledger.ANALYSIS_TYPES, analysis_type, "analysis_type")
    task_id = _now_id("clause")
    row = {
        "clause_task_id": task_id,
        "contract_id": contract_id,
        "clause_engine": clause_engine,
        "analysis_type": analysis_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "notes": notes,
    }
    ledger.append_row("CLAUSE_QUEUE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_clause_task",
        task_id,
        status="ok",
        notes=notes,
    )
    return task_id


def update_clause_status(clause_task_id: str, status: str, notes: str = ""):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("CLAUSE_QUEUE", "clause_task_id", clause_task_id, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_clause_status",
        clause_task_id,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# CRM QUEUE OPERATIONS
# ---------------------------

def queue_crm_task(
    lead_id: str,
    action_type: str,
    priority: int = 3,
    notes: str = "",
    ledger_path: str | Path | None = None,
    workflow_id: str = "",
    origin_repo: str = "dpo-system",
    hop_count: int = 1,
    list_name: str = "",
    outreach_purpose: str = "",
    list_source: str = "",
    outbound_status: str = "planned",
):
    ledger.validate_enum(ledger.CRM_ACTIONS, action_type, "action_type")
    task_id = _now_id("crm")
    row = {
        "crm_task_id": task_id,
        "lead_id": lead_id,
        "action_type": action_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "workflow_id": workflow_id or f"crm-{lead_id}",
        "origin_repo": origin_repo,
        "hop_count": hop_count,
        "notes": notes,
        "list_name": list_name,
        "outreach_purpose": outreach_purpose,
        "list_source": list_source,
        "outbound_status": outbound_status,
    }
    ledger.append_row("CRM_QUEUE", row, path=Path(ledger_path) if ledger_path is not None else None)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_crm_task",
        task_id,
        status="ok",
        notes=notes,
        path=Path(ledger_path) if ledger_path is not None else None,
    )
    return task_id


def update_crm_status(crm_task_id: str, status: str, notes: str = ""):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("CRM_QUEUE", "crm_task_id", crm_task_id, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_crm_status",
        crm_task_id,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# GOVERNANCE QUEUE OPERATIONS
# ---------------------------

def queue_governance_task(
    interview_name: str,
    action_type: str,
    priority: int = 3,
    notes: str = "",
    workflow_id: str = "",
    origin_repo: str = "dpo-system",
    hop_count: int = 1,
    list_name: str = "",
    outreach_purpose: str = "",
    list_source: str = "",
    outbound_status: str = "planned",
):
    ledger.validate_enum(ledger.GOV_ACTIONS, action_type, "action_type")
    gov_id = _now_id("gov")
    row = {
        "governance_id": gov_id,
        "interview_name": interview_name,
        "action_type": action_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "workflow_id": workflow_id or f"dialer-{gov_id}",
        "origin_repo": origin_repo,
        "hop_count": hop_count,
        "notes": notes,
        "list_name": list_name,
        "outreach_purpose": outreach_purpose,
        "list_source": list_source,
        "outbound_status": outbound_status,
    }
    ledger.append_row("GOVERNANCE_QUEUE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_governance_task",
        gov_id,
        status="ok",
        notes=notes,
    )
    return gov_id


def update_governance_status(governance_id: str, status: str, notes: str = "", ledger_path: str | Path | None = None):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("GOVERNANCE_QUEUE", "governance_id", governance_id, updates, path=Path(ledger_path) if ledger_path is not None else None)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_governance_status",
        governance_id,
        status="ok",
        notes=f"status={status}",
        path=Path(ledger_path) if ledger_path is not None else None,
    )


def record_outbound_disposition(
    workflow_id: str,
    disposition: str,
    notes: str = "",
    ledger_path: str | Path | None = None,
) -> dict[str, Any]:
    """Record a new outbound disposition hop for an existing workflow row."""
    rows = ledger.read_rows("GOVERNANCE_QUEUE", path=Path(ledger_path) if ledger_path is not None else None)
    prior_rows = [row for row in rows if str(row.get("workflow_id") or "").strip() == str(workflow_id).strip()]
    if not prior_rows:
        raise KeyError(f"no governance rows found for workflow {workflow_id}")

    prior = prior_rows[-1]
    prior_id = str(prior.get("governance_id") or "").strip()
    if prior_id:
        update_governance_status(
            prior_id,
            "complete",
            notes=f"prior disposition recorded: {disposition}",
            ledger_path=ledger_path,
        )

    outcome_row = {
        "governance_id": _now_id("gov"),
        "interview_name": "outbound-disposition",
        "action_type": "validate",
        "priority": 3,
        "status": "complete",
        "created_at": ledger.timestamp(),
        "updated_at": ledger.timestamp(),
        "operator": OPERATOR_NAME,
        "workflow_id": workflow_id,
        "origin_repo": str(prior.get("origin_repo") or "dpo-system"),
        "hop_count": int(str(prior.get("hop_count") or 1)) + 1,
        "notes": f"disposition={disposition} | {notes}".strip(),
        "list_name": str(prior.get("list_name") or ""),
        "outreach_purpose": str(prior.get("outreach_purpose") or ""),
        "list_source": str(prior.get("list_source") or ""),
        "outbound_status": disposition,
    }
    ledger.append_row("GOVERNANCE_QUEUE", outcome_row, path=Path(ledger_path) if ledger_path is not None else None)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "record_outbound_disposition",
        workflow_id,
        status="ok",
        notes=f"disposition={disposition}",
        path=Path(ledger_path) if ledger_path is not None else None,
    )
    return outcome_row
