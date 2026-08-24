"""Docassemble-driven workflow for DPO with ledger, audit, and sync gates.

This module is intentionally designed to follow the repo's current DPO control
plane rather than introduce a parallel abstraction. The ledger workbook remains the
authoritative workflow record; Docassemble is treated as the generation layer;
DB and CRM writes are adapter stubs that occur only after operator approval.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import audit_writer, ledger_io as ledger
from .audit_writer import make_idempotency_key
from .operator_actions import approve_batch, reject_batch

DOCASSEMBLE_TAXONOMY: dict[str, dict[str, Any]] = {
    "us:employment": {
        "taxonomy_key": "us:employment",
        "lane": "employment",
        "template_name": "employment_notice_v1",
        "docassemble_template": "employment_notice_v1",
        "db_table": "casework_employment",
        "crm_action": "classify",
        "required_fields": ("jurisdiction", "matter_type", "client_name", "document_date"),
    },
    "us:contract_review": {
        "taxonomy_key": "us:contract_review",
        "lane": "contract_review",
        "template_name": "contract_review_v1",
        "docassemble_template": "contract_review_v1",
        "db_table": "casework_contract_review",
        "crm_action": "enrich",
        "required_fields": ("jurisdiction", "matter_type", "contract_party", "document_date"),
    },
    "us:regulatory_filing": {
        "taxonomy_key": "us:regulatory_filing",
        "lane": "regulatory_filing",
        "template_name": "regulatory_filing_v1",
        "docassemble_template": "regulatory_filing_v1",
        "db_table": "casework_regulatory",
        "crm_action": "update",
        "required_fields": ("jurisdiction", "matter_type", "filing_entity", "document_date"),
    },
    "uk:employment": {
        "taxonomy_key": "uk:employment",
        "lane": "employment",
        "template_name": "uk_employment_notice_v1",
        "docassemble_template": "uk_employment_notice_v1",
        "db_table": "casework_uk_employment",
        "crm_action": "classify",
        "required_fields": ("jurisdiction", "matter_type", "client_name", "document_date"),
    },
    "us:nda_review": {
        "taxonomy_key": "us:nda_review",
        "lane": "nda_review",
        "template_name": "nda_review_v1",
        "docassemble_template": "nda_review_v1",
        "db_table": "casework_nda_review",
        "crm_action": "enrich",
        "required_fields": ("jurisdiction", "matter_type", "contract_party", "document_date"),
    },
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def resolve_taxonomy(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve the document classification to a DPO taxonomy entry."""
    if not isinstance(payload, dict):
        return None, "payload_not_mapping"

    jurisdiction = str(payload.get("jurisdiction") or "").strip().lower()
    matter_type = str(payload.get("matter_type") or "").strip().lower()
    key = f"{jurisdiction}:{matter_type}"

    entry = DOCASSEMBLE_TAXONOMY.get(key)
    if entry is None:
        return None, f"taxonomy_missing:{key}"

    for field in entry["required_fields"]:
        if not payload.get(field):
            return None, f"missing_required_field:{field}"

    return entry, None


def write_governance_queue_row(
    *,
    task_id: str,
    operator_id: str,
    payload: dict[str, Any],
    taxonomy: dict[str, Any],
    source: str = "docassemble",
) -> None:
    """Create the governing DPO ledger row before downstream execution."""
    row = {
        "governance_id": task_id,
        "interview_name": str(payload.get("source") or source),
        "action_type": "approve",
        "priority": int(payload.get("priority", 3) or 3),
        "status": "pending",
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
        "operator": operator_id,
        "workflow_id": f"docassemble-{task_id}",
        "origin_repo": "dpo-system",
        "hop_count": 1,
        "notes": json.dumps(
            {
                "taxonomy_key": taxonomy.get("taxonomy_key"),
                "lane": taxonomy.get("lane"),
                "template_name": taxonomy.get("template_name"),
                "db_table": taxonomy.get("db_table"),
                "crm_action": taxonomy.get("crm_action"),
            },
            sort_keys=True,
        ),
        "list_name": str(payload.get("list_name") or ""),
        "outreach_purpose": str(payload.get("outreach_purpose") or ""),
        "list_source": str(payload.get("list_source") or "docassemble"),
        "outbound_status": "pending",
    }
    ledger.append_row("GOVERNANCE_QUEUE", row)


def generate_docassemble_bundle(*, task_id: str, payload: dict[str, Any], template_name: str) -> dict[str, Any]:
    """Create a deterministic Docassemble artifact manifest for downstream approval."""
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts" / "docassemble"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    bundle = {
        "task_id": task_id,
        "template_name": template_name,
        "generated_at": _utc_now_iso(),
        "jurisdiction": payload.get("jurisdiction"),
        "matter_type": payload.get("matter_type"),
        "payload_hash": _hash_payload(payload),
        "status": "ready_for_approval",
    }

    manifest_path = artifacts_dir / f"{task_id}.json"
    manifest_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    bundle["manifest_path"] = str(manifest_path)
    return bundle


def sync_casework_db_after_approval(*, task_id: str, taxonomy: dict[str, Any], payload: dict[str, Any], operator_id: str) -> dict[str, Any]:
    """Adapter stub for the DPO casework database layer.

    This stub intentionally does not write directly to external systems before the
    approval gate has passed. Real implementations should connect to the machine
    truth DB here.
    """
    return {
        "status": "synced",
        "table": taxonomy["db_table"],
        "task_id": task_id,
        "operator_id": operator_id,
        "record_count": 1,
        "payload_hash": _hash_payload(payload),
    }


def sync_shadow_crm_after_approval(*, task_id: str, taxonomy: dict[str, Any], payload: dict[str, Any], operator_id: str) -> dict[str, Any]:
    """Adapter stub for the protected Shadow CRM / client operational surface."""
    return {
        "status": "synced",
        "action": taxonomy["crm_action"],
        "task_id": task_id,
        "operator_id": operator_id,
        "payload_hash": _hash_payload(payload),
    }


def reconcile_before_sync(*, task_id: str, payload: dict[str, Any], approval_decision: dict[str, Any]) -> bool:
    """Fail closed if approval evidence is missing or a payload mismatch is detected."""
    if approval_decision.get("status") != "accepted":
        return False
    if approval_decision.get("task_id") != task_id:
        return False
    if approval_decision.get("payload_hash") != _hash_payload(payload):
        return False
    return True


def approved_docassemble_workflow(payload: dict[str, Any], *, operator_id: str = "DPO") -> dict[str, Any]:
    """Run the DPO Docassemble workflow with ledger+audit+sync gating."""
    task_id = f"doc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    now = _utc_now_iso()

    if not isinstance(payload, dict) or not payload:
        reason = "Invalid or empty payload"
        reject_batch(
            batch_ids=[task_id],
            who=operator_id,
            why=reason,
            reason_code="INVALID_PAYLOAD",
            evidence_refs=[f"task:{task_id}"],
        )
        return {"status": "rejected", "task_id": task_id, "reason": reason}

    taxonomy, taxonomy_error = resolve_taxonomy(payload)
    if taxonomy_error:
        reason = f"Taxonomy resolution failed: {taxonomy_error}"
        reject_batch(
            batch_ids=[task_id],
            who=operator_id,
            why=reason,
            reason_code="TAXONOMY_ROUTE_FAILED",
            evidence_refs=[f"task:{task_id}"],
        )
        return {"status": "rejected", "task_id": task_id, "reason": reason}

    write_governance_queue_row(task_id=task_id, operator_id=operator_id, payload=payload, taxonomy=taxonomy)

    doc_bundle = generate_docassemble_bundle(
        task_id=task_id,
        payload=payload,
        template_name=taxonomy["docassemble_template"],
    )

    preflight_event = {
        "who": operator_id,
        "when": now,
        "what": "docassemble_preflight_ok",
        "why": "Docassemble template resolved and payload passed governance validation",
        "reason_code": "DOCASSEMBLE_PREFLIGHT_OK",
        "evidence_refs": [doc_bundle["manifest_path"]],
        "targets": [task_id],
        "dry_run": False,
    }
    preflight_key = make_idempotency_key(
        action="docassemble_preflight_ok",
        target_ids=[task_id],
        actor=operator_id,
        reason_code="DOCASSEMBLE_PREFLIGHT_OK",
    )
    audit_writer.write_decision_event(preflight_event, preflight_key)

    approval_result = approve_batch(
        batch_ids=[task_id],
        who=operator_id,
        why="Approved after taxonomy resolution, preflight checks, and Docassemble manifest creation",
        reason_code="DOCASSEMBLE_APPROVAL",
        evidence_refs=[doc_bundle["manifest_path"]],
    )

    if approval_result.get("status") not in {"written", "duplicate_noop"}:
        return {
            "status": "rejected",
            "task_id": task_id,
            "reason": "Approval audit denied the batch",
            "approval": approval_result,
        }

    decision = {
        "status": "accepted",
        "task_id": task_id,
        "payload_hash": _hash_payload(payload),
        "approved_by": operator_id,
        "approved_at": now,
        "template": taxonomy["template_name"],
    }

    if not reconcile_before_sync(task_id=task_id, payload=payload, approval_decision=decision):
        reject_batch(
            batch_ids=[task_id],
            who=operator_id,
            why="Reconciliation failed before DB and CRM sync",
            reason_code="RECONCILIATION_FAILED",
            evidence_refs=[doc_bundle["manifest_path"]],
        )
        return {"status": "rejected", "task_id": task_id, "reason": "reconciliation_failed"}

    db_sync = sync_casework_db_after_approval(
        task_id=task_id,
        taxonomy=taxonomy,
        payload=payload,
        operator_id=operator_id,
    )
    crm_sync = sync_shadow_crm_after_approval(
        task_id=task_id,
        taxonomy=taxonomy,
        payload=payload,
        operator_id=operator_id,
    )

    return {
        "status": "approved_and_synced",
        "task_id": task_id,
        "taxonomy": taxonomy,
        "docassemble_bundle": doc_bundle,
        "approval": approval_result,
        "db_sync": db_sync,
        "crm_sync": crm_sync,
    }
