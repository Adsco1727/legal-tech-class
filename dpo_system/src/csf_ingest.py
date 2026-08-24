"""CSF seed ingestion helpers for the DPO operator pipeline."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .ledger_io import LEDGER_PATH, append_row, read_rows
from .ooma_dialer import normalize_contact_record


def ingest_csf_seed(seed_path: str | Path, ledger_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Ingest a CSF seed CSV into the ledger-backed workflow history."""
    source_path = Path(seed_path)
    target_path = Path(ledger_path) if ledger_path is not None else LEDGER_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with source_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    ingested: list[dict[str, Any]] = []
    for raw_row in rows:
        normalized = normalize_contact_record(raw_row)
        if not normalized["record_id"] or not normalized["normalized_phone_number"]:
            continue

        workflow_id = f"csf-{normalized['record_id']}"
        notes_payload = {
            "source_file": str(source_path),
            "source_system": normalized["source_system"],
            "record_id": normalized["record_id"],
            "full_name": normalized["full_name"],
            "first_name": normalized["first_name"],
            "last_name": normalized["last_name"],
            "phone_number": normalized["phone_number"],
            "email": normalized["email"],
            "address": normalized["address"],
            "list_name": normalized["list_name"],
            "outreach_purpose": normalized["outreach_purpose"],
            "list_source": normalized["list_source"],
            "outbound_status": normalized["outbound_status"],
        }
        ledger_row = {
            "governance_id": workflow_id,
            "interview_name": "csf-ingestion",
            "action_type": "validate",
            "priority": 3,
            "status": "pending",
            "created_at": "",
            "updated_at": "",
            "operator": "DPO",
            "workflow_id": workflow_id,
            "origin_repo": "dpo-system",
            "hop_count": 1,
            "notes": json.dumps(notes_payload, sort_keys=True),
            "list_name": normalized["list_name"],
            "outreach_purpose": normalized["outreach_purpose"],
            "list_source": normalized["list_source"],
            "outbound_status": normalized["outbound_status"],
        }
        append_row("GOVERNANCE_QUEUE", ledger_row, path=target_path)
        ingested.append(ledger_row)

    return ingested
