from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .ledger_io import read_rows
from .ooma_dialer import normalize_contact_record


def build_provider_ready_outbound_rows(
    ledger_path: str | Path | None = None,
    list_name: str | None = None,
) -> list[dict[str, Any]]:
    """Build provider-ready outbound rows from ledger-backed governance queue entries."""
    rows = read_rows("GOVERNANCE_QUEUE", path=Path(ledger_path) if ledger_path is not None else None)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if list_name and str(row.get("list_name") or "").strip() != str(list_name).strip():
            continue

        notes_payload: dict[str, Any] = {}
        notes_text = str(row.get("notes") or "")
        if notes_text:
            try:
                parsed = json.loads(notes_text)
            except json.JSONDecodeError:
                parsed = {}
            if isinstance(parsed, dict):
                notes_payload = parsed

        payload = {
            "record_id": str(notes_payload.get("record_id") or row.get("workflow_id") or "").replace("csf-", ""),
            "full_name": str(notes_payload.get("full_name") or ""),
            "phone_number": str(notes_payload.get("phone_number") or ""),
            "email": str(notes_payload.get("email") or ""),
            "address": str(notes_payload.get("address") or ""),
            "campaign_name": str(notes_payload.get("campaign_name") or ""),
            "source_system": str(notes_payload.get("source_system") or "Ooma/CSF"),
            "notes": notes_text,
            "list_name": str(row.get("list_name") or notes_payload.get("list_name") or ""),
            "outreach_purpose": str(row.get("outreach_purpose") or notes_payload.get("outreach_purpose") or ""),
            "list_source": str(row.get("list_source") or notes_payload.get("list_source") or ""),
            "outbound_status": str(row.get("outbound_status") or notes_payload.get("outbound_status") or "planned").strip() or "planned",
        }
        normalized = normalize_contact_record(payload)
        filtered.append(normalized)

    return filtered


def export_provider_ready_outbound_list(
    list_name: str,
    output_path: str | Path,
    ledger_path: str | Path | None = None,
) -> Path:
    """Export a provider-ready outbound list from the governance queue in the ledger."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    rows = build_provider_ready_outbound_rows(ledger_path=ledger_path, list_name=list_name)
    fieldnames = [
        "record_id",
        "full_name",
        "first_name",
        "last_name",
        "phone_number",
        "normalized_phone_number",
        "email",
        "address",
        "campaign_name",
        "source_system",
        "notes",
        "list_name",
        "outreach_purpose",
        "list_source",
        "outbound_status",
        "provider_format",
    ]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return destination
