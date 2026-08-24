"""Build canonical outbound seed batches from DB export files."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

CANONICAL_FIELDS = [
    "record_id",
    "phone_number",
    "full_name",
    "list_name",
    "outreach_purpose",
    "list_source",
    "notes",
    "email",
    "address",
    "source_system",
    "campaign_name",
    "outbound_status",
]

LEAD_ALIASES: dict[str, tuple[str, ...]] = {
    "record_id": ("record_id", "lead_id", "user_id", "userid", "sid", "id"),
    "phone_number": ("phone_number", "phone", "phone_number2", "mobile_phone", "cell_phone", "Phone Number"),
    "full_name": ("full_name", "name", "full_filename", "Contact Name"),
    "notes": ("notes", "note", "description"),
    "email": ("email", "email_address", "company_email", "SecondaryEmail"),
    "address": ("address", "street_address", "address1"),
    "source_system": ("source_system", "source", "source_db", "origin"),
    "campaign_name": ("campaign_name", "campaign", "campaign_id"),
}

WORKFLOW_ALIASES: dict[str, tuple[str, ...]] = {
    "record_id": ("record_id", "lead_id", "user_id", "userid", "sid", "workflow_id", "id"),
    "list_name": ("list_name", "list", "campaign_list"),
    "outreach_purpose": ("outreach_purpose", "purpose", "script_name"),
    "list_source": ("list_source", "source_list", "provenance"),
    "outbound_status": ("outbound_status", "status", "dialer_status"),
    "notes": ("notes", "workflow_notes"),
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _value_from_aliases(row: dict[str, Any], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        value = str(row.get(alias) or "").strip()
        if value:
            return value
    return ""


def _normalize_record_id(raw: str) -> str:
    value = str(raw or "").strip()
    for prefix in ("csf-", "dialer-"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value


def _lead_key(row: dict[str, Any]) -> str:
    return _normalize_record_id(_value_from_aliases(row, LEAD_ALIASES["record_id"]))


def _workflow_key(row: dict[str, Any]) -> str:
    return _normalize_record_id(_value_from_aliases(row, WORKFLOW_ALIASES["record_id"]))


def build_outbound_rows_from_db_exports(
    leads_path: str | Path,
    workflow_path: str | Path,
    *,
    default_list_source: str = "google_bd_db",
    default_source_system: str = "google_db",
    allowed_outbound_statuses: tuple[str, ...] = ("", "planned", "new", "queued"),
) -> list[dict[str, str]]:
    leads_rows = _read_csv(Path(leads_path))
    workflow_rows = _read_csv(Path(workflow_path))

    leads_by_key = {_lead_key(row): row for row in leads_rows if _lead_key(row)}
    built: list[dict[str, str]] = []

    for workflow_row in workflow_rows:
        key = _workflow_key(workflow_row)
        if not key:
            continue

        lead_row = leads_by_key.get(key)
        if lead_row is None:
            continue

        outbound_status = _value_from_aliases(workflow_row, WORKFLOW_ALIASES["outbound_status"]).lower()
        if outbound_status not in {status.lower() for status in allowed_outbound_statuses}:
            continue

        notes_parts = [
            _value_from_aliases(lead_row, LEAD_ALIASES["notes"]),
            _value_from_aliases(workflow_row, WORKFLOW_ALIASES["notes"]),
        ]
        combined_notes = " | ".join(part for part in notes_parts if part)

        built.append(
            {
                "record_id": key,
                "phone_number": _value_from_aliases(lead_row, LEAD_ALIASES["phone_number"]),
                "full_name": _value_from_aliases(lead_row, LEAD_ALIASES["full_name"]),
                "list_name": _value_from_aliases(workflow_row, WORKFLOW_ALIASES["list_name"]),
                "outreach_purpose": _value_from_aliases(workflow_row, WORKFLOW_ALIASES["outreach_purpose"]),
                "list_source": _value_from_aliases(workflow_row, WORKFLOW_ALIASES["list_source"]) or default_list_source,
                "notes": combined_notes,
                "email": _value_from_aliases(lead_row, LEAD_ALIASES["email"]),
                "address": _value_from_aliases(lead_row, LEAD_ALIASES["address"]),
                "source_system": _value_from_aliases(lead_row, LEAD_ALIASES["source_system"]) or default_source_system,
                "campaign_name": _value_from_aliases(lead_row, LEAD_ALIASES["campaign_name"]),
                "outbound_status": outbound_status or "planned",
            }
        )

    built.sort(key=lambda row: (row["list_name"], row["record_id"]))
    return built


def write_outbound_batches(
    rows: list[dict[str, str]],
    output_dir: str | Path,
    *,
    batch_size: int = 500,
    file_prefix: str = "csf_batch",
) -> dict[str, Any]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    total_rows = len(rows)
    total_batches = (total_rows + batch_size - 1) // batch_size if total_rows else 0
    written_files: list[str] = []
    batch_counts: list[int] = []

    for batch_index in range(total_batches):
        start = batch_index * batch_size
        end = start + batch_size
        chunk = rows[start:end]
        file_name = f"{file_prefix}_{batch_index + 1:03d}_of_{total_batches:03d}.csv"
        file_path = destination / file_name
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CANONICAL_FIELDS)
            writer.writeheader()
            writer.writerows(chunk)
        written_files.append(str(file_path))
        batch_counts.append(len(chunk))

    manifest = {
        "total_rows": total_rows,
        "batch_size": batch_size,
        "total_batches": total_batches,
        "files": written_files,
        "batch_counts": batch_counts,
    }
    manifest_path = destination / f"{file_prefix}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest