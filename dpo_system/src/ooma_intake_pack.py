from __future__ import annotations

import csv
import json
import re
import uuid
from pathlib import Path
from typing import Any

OOMA_SOURCE = "ooma_autodialer_csv"
OOMA_COLUMNS = [
    "First Name",
    "Last Name",
    "Phone Number",
    "External ID",
    "Notes",
    "Auxiliary Data",
]

URGENCY_KEYWORDS = ("hot", "urgent", "priority", "callback", "founder")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _title_case_name(value: str) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    if not compact:
        return ""
    return compact.title()


def normalize_usca_phone(raw_phone: str) -> tuple[str | None, str | None]:
    cleaned = _clean(raw_phone)
    digits = re.sub(r"[\s()\-\.+]", "", cleaned)

    if not digits:
        return None, "missing_phone"
    if not digits.isdigit():
        return None, "non_numeric_phone"

    if len(digits) == 10:
        return f"+1{digits}", None
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}", None
    return None, "invalid_phone_length"


def assign_lane(notes: str) -> str:
    lowered = _clean(notes).lower()
    for keyword in URGENCY_KEYWORDS:
        if keyword in lowered:
            return "founder"
    return "BD"


def normalize_ooma_row(row: dict[str, Any], row_number: int) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    first_name = _clean(row.get("First Name"))
    last_name = _clean(row.get("Last Name"))
    phone_raw = _clean(row.get("Phone Number"))
    external_id = _clean(row.get("External ID"))
    notes = _clean(row.get("Notes"))
    aux = _clean(row.get("Auxiliary Data"))

    if not first_name and not last_name:
        return None, {
            "row_number": row_number,
            "external_id": external_id,
            "raw_phone": phone_raw,
            "rejection_reason": "missing_name",
            "source": OOMA_SOURCE,
        }

    normalized_phone, phone_error = normalize_usca_phone(phone_raw)
    if phone_error:
        return None, {
            "row_number": row_number,
            "external_id": external_id,
            "raw_phone": phone_raw,
            "rejection_reason": phone_error,
            "source": OOMA_SOURCE,
        }

    lead_id = external_id if external_id else str(uuid.uuid4())
    full_name = _title_case_name(f"{first_name} {last_name}")

    dto_lead = {
        "lead_id": lead_id,
        "full_name": full_name,
        "phone": normalized_phone,
        "lane": assign_lane(notes),
        "status": "new",
        "last_call_result": None,
        "next_action": None,
        "notes": notes,
        "aux": aux,
        "source": OOMA_SOURCE,
    }
    return dto_lead, None


def process_ooma_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=2):
        accepted_row, rejected_row = normalize_ooma_row(row, row_number=index)
        if accepted_row is not None:
            accepted.append(accepted_row)
        if rejected_row is not None:
            rejected.append(rejected_row)

    summary = {
        "total_rows": len(rows),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
    }

    return {
        "accepted": accepted,
        "rejected": rejected,
        "summary": summary,
    }


def read_ooma_csv(path: str | Path) -> list[dict[str, Any]]:
    source_path = Path(path)
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = [column for column in OOMA_COLUMNS if column not in headers]
        if missing:
            raise ValueError(f"missing required Ooma headers: {missing}")
        return [dict(row) for row in reader]


def process_ooma_csv_file(path: str | Path) -> dict[str, Any]:
    rows = read_ooma_csv(path)
    return process_ooma_rows(rows)


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def write_rejections_csv(path: str | Path, rejected: list[dict[str, Any]]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["row_number", "external_id", "raw_phone", "rejection_reason", "source"],
        )
        writer.writeheader()
        writer.writerows(rejected)
    return destination
