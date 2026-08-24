"""Ooma/CSF autodialer planning helpers for the DPO operator pipeline."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


def normalize_contact_record(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a seed row into a provider-ready contact shape."""
    raw_name = str(row.get("full_name") or row.get("name") or "").strip()
    names = [part for part in re.split(r"\s+", raw_name) if part]
    first_name = names[0] if names else ""
    last_name = " ".join(names[1:]) if len(names) > 1 else ""

    phone = str(row.get("phone_number") or "").strip()
    digits = re.sub(r"\D", "", phone)
    if digits:
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) in {7, 10}:
            normalized_phone = f"+1{digits}"
        else:
            normalized_phone = f"+{digits}"
    else:
        normalized_phone = ""

    email = str(row.get("email") or "").strip().lower()
    address = str(row.get("address") or "").strip()

    return {
        "record_id": str(row.get("record_id") or "").strip(),
        "full_name": raw_name,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": normalized_phone,
        "normalized_phone_number": normalized_phone,
        "email": email,
        "address": address,
        "campaign_name": str(row.get("campaign_name") or "").strip(),
        "source_system": str(row.get("source_system") or "Ooma/CSF").strip() or "Ooma/CSF",
        "notes": str(row.get("notes") or "").strip(),
        "list_name": str(row.get("list_name") or "").strip(),
        "outreach_purpose": str(row.get("outreach_purpose") or "").strip(),
        "list_source": str(row.get("list_source") or "").strip(),
        "outbound_status": str(row.get("outbound_status") or "planned").strip() or "planned",
        "provider_format": "csv",
    }


def export_provider_ready_csv(seed_path: str | Path, output_path: str | Path) -> Path:
    """Export a provider-ready CSV from an Ooma/CSF seed file."""
    source_path = Path(seed_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with source_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    normalized_rows: list[dict[str, Any]] = []
    for raw_row in rows:
        normalized = normalize_contact_record(raw_row)
        if not normalized["record_id"] or not normalized["normalized_phone_number"]:
            continue
        normalized_rows.append(normalized)

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
        writer.writerows(normalized_rows)

    return destination


def build_ooma_autodialer_plan(seed_path: str | Path) -> list[dict[str, Any]]:
    """Build a deterministic outbound plan from an Ooma/CSF seed file.

    The plan is intentionally CRM-free and is meant to feed a provider-side
    autodialer setup rather than relying on an internal CRM implementation.
    The returned records also carry list-generation metadata so outbound work
    can be traced back to the purpose and source list that produced it.
    """
    path = Path(seed_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    plan: list[dict[str, Any]] = []
    for row in rows:
        record_id = (row.get("record_id") or "").strip()
        phone_number = (row.get("phone_number") or "").strip()
        campaign_name = (row.get("campaign_name") or "").strip()
        source_system = (row.get("source_system") or "Ooma/CSF").strip() or "Ooma/CSF"
        notes = (row.get("notes") or "").strip()
        list_name = (row.get("list_name") or "").strip()
        outreach_purpose = (row.get("outreach_purpose") or "").strip()
        list_source = (row.get("list_source") or "").strip()
        if not record_id or not phone_number:
            continue
        plan.append(
            {
                "record_id": record_id,
                "phone_number": phone_number,
                "campaign_name": campaign_name,
                "source_system": source_system,
                "notes": notes,
                "list_name": list_name,
                "outreach_purpose": outreach_purpose,
                "list_source": list_source,
                "outbound_status": "planned",
            }
        )

    return plan
