from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

LEADS_HEADERS = [
    "lead_id",
    "phone_number",
    "full_name",
    "email",
    "address",
    "notes",
    "source_system",
    "campaign_name",
]

WORKFLOW_HEADERS = [
    "record_id",
    "list_name",
    "outreach_purpose",
    "list_source",
    "outbound_status",
    "workflow_notes",
]

ID_ALIASES = (
    "record_id",
    "lead_id",
    "user_id",
    "userid",
    "id",
    "sid",
)

PHONE_ALIASES = (
    "phone_number",
    "phone",
    "phone_number2",
    "mobile_phone",
    "cell_phone",
    "Phone Number",
)

EMAIL_ALIASES = ("email", "company_email", "SecondaryEmail")

NAME_ALIASES = ("full_name", "name", "full_filename", "Contact Name")

NOTES_ALIASES = ("notes", "description", "profession_name", "service", "company")


def _pick(row: dict[str, Any], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        value = str(row.get(alias) or "").strip()
        if value:
            return value
    return ""


def _compose_name(row: dict[str, Any]) -> str:
    named = _pick(row, NAME_ALIASES)
    if named:
        return named

    first = str(row.get("first_name") or "").strip()
    last = str(row.get("last_name") or "").strip()
    return f"{first} {last}".strip()


def _compose_address(row: dict[str, Any]) -> str:
    if str(row.get("address") or "").strip():
        return str(row.get("address") or "").strip()

    parts = [
        str(row.get("address1") or "").strip(),
        str(row.get("address2") or "").strip(),
        str(row.get("city") or "").strip(),
        str(row.get("state_code") or row.get("state") or "").strip(),
        str(row.get("zip_code") or row.get("ZIP Code") or "").strip(),
    ]
    return ", ".join([p for p in parts if p])


def _read_rows(csv_paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in csv_paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows.extend(dict(row) for row in reader)
    return rows


def _normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw or "").strip())
    if not digits:
        return ""
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) in {7, 10}:
        return f"+1{digits}"
    return f"+{digits}" if len(digits) >= 7 else ""


def convert_bd_csvs_to_standard(
    csv_paths: list[Path],
    *,
    list_name: str,
    outreach_purpose: str,
    list_source: str,
    source_system: str,
    campaign_name: str,
    outbound_status: str = "planned",
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]]:
    raw_rows = _read_rows(csv_paths)

    leads_by_id: dict[str, dict[str, str]] = {}
    workflow_rows: list[dict[str, str]] = []
    stats = {
        "raw_rows": len(raw_rows),
        "missing_id": 0,
        "missing_phone": 0,
        "kept": 0,
    }

    for row in raw_rows:
        record_id = _pick(row, ID_ALIASES)
        if not record_id:
            stats["missing_id"] += 1
            continue

        phone_number = _normalize_phone(_pick(row, PHONE_ALIASES))
        if not phone_number:
            stats["missing_phone"] += 1
            continue

        lead_row = {
            "lead_id": record_id,
            "phone_number": phone_number,
            "full_name": _compose_name(row),
            "email": _pick(row, EMAIL_ALIASES),
            "address": _compose_address(row),
            "notes": _pick(row, NOTES_ALIASES),
            "source_system": source_system,
            "campaign_name": campaign_name,
        }

        existing = leads_by_id.get(record_id)
        if existing is None:
            leads_by_id[record_id] = lead_row
        elif not _normalize_phone(existing.get("phone_number", "")) and phone_number:
            leads_by_id[record_id] = lead_row

    for record_id, lead in leads_by_id.items():
        workflow_rows.append(
            {
                "record_id": record_id,
                "list_name": list_name,
                "outreach_purpose": outreach_purpose,
                "list_source": list_source,
                "outbound_status": outbound_status,
                "workflow_notes": f"standardized_from_bd | source={source_system} | phone={lead['phone_number']}",
            }
        )

    leads_rows = sorted(leads_by_id.values(), key=lambda r: r["lead_id"])
    workflow_rows.sort(key=lambda r: r["record_id"])
    stats["kept"] = len(leads_rows)
    return leads_rows, workflow_rows, stats


def write_standard_exports(
    leads_rows: list[dict[str, str]],
    workflow_rows: list[dict[str, str]],
    *,
    leads_output: Path,
    workflow_output: Path,
) -> None:
    leads_output.parent.mkdir(parents=True, exist_ok=True)
    workflow_output.parent.mkdir(parents=True, exist_ok=True)

    with leads_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEADS_HEADERS)
        writer.writeheader()
        writer.writerows(leads_rows)

    with workflow_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WORKFLOW_HEADERS)
        writer.writeheader()
        writer.writerows(workflow_rows)
