from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .ooma_intake_pack import OOMA_COLUMNS, normalize_usca_phone


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _truthy(value: Any) -> bool:
    normalized = _clean(value).lower()
    return normalized in {"1", "true", "yes", "y"}


def _parse_utc(value: str) -> datetime:
    raw = _clean(value)
    if not raw:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _title_case_name(value: str) -> str:
    compact = " ".join(_clean(value).split())
    return compact.title() if compact else ""


def _derive_names(row: dict[str, Any]) -> tuple[str, str]:
    first_name = _clean(row.get("first_name"))
    last_name = _clean(row.get("last_name"))
    if first_name or last_name:
        return first_name, last_name

    full_name = _clean(row.get("full_name"))
    if not full_name:
        return "", ""

    parsed = urlparse(full_name)
    candidate = full_name
    if parsed.scheme and parsed.path:
        candidate = unquote(parsed.path.rstrip("/").split("/")[-1])

    candidate = candidate.replace("_", " ").replace("-", " ")
    parts = [part for part in candidate.split() if part]
    if parts and parts[-1].isdigit():
        parts = parts[:-1]
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def _dedupe_latest_by_lead(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_by_lead: dict[str, dict[str, Any]] = {}
    for row in rows:
        lead_id = _clean(row.get("lead_id"))
        if not lead_id:
            continue
        current = latest_by_lead.get(lead_id)
        if current is None:
            latest_by_lead[lead_id] = row
            continue
        current_ts = _parse_utc(_clean(current.get("updated_at")))
        row_ts = _parse_utc(_clean(row.get("updated_at")))
        if (row_ts, lead_id) >= (current_ts, lead_id):
            latest_by_lead[lead_id] = row
    return list(latest_by_lead.values())


def _apply_relevance_filter(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for row in rows:
        is_callable = _clean(row.get("is_callable"))
        is_suppressed = _clean(row.get("is_suppressed"))
        status = _clean(row.get("status")).lower()

        if is_callable and not _truthy(is_callable):
            continue
        if is_suppressed and _truthy(is_suppressed):
            continue
        if status in {"closed", "converted", "do_not_call", "dnc"}:
            continue
        filtered.append(row)
    return filtered


def _sort_key(row: dict[str, Any]) -> tuple[datetime, str]:
    updated_at = _parse_utc(_clean(row.get("updated_at")))
    lead_id = _clean(row.get("lead_id"))
    return (updated_at, lead_id)


def _load_watermark(path: Path | None) -> tuple[datetime, str] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    updated_at = _parse_utc(_clean(payload.get("updated_at")))
    lead_id = _clean(payload.get("lead_id"))
    if not lead_id:
        return None
    return (updated_at, lead_id)


def _save_watermark(path: Path, updated_at: datetime, lead_id: str) -> Path:
    payload = {
        "updated_at": updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lead_id": lead_id,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _to_ooma_row(row: dict[str, Any]) -> dict[str, str]:
    raw_first_name, raw_last_name = _derive_names(row)
    first_name = _title_case_name(raw_first_name)
    last_name = _title_case_name(raw_last_name)
    phone_input = _clean(row.get("phone_number"))
    normalized_phone, _ = normalize_usca_phone(phone_input)

    if not normalized_phone:
        normalized_phone = ""

    external_id = _clean(row.get("external_id")) or _clean(row.get("lead_id"))
    notes = _clean(row.get("notes"))
    aux = _clean(row.get("auxiliary_data"))

    return {
        "First Name": first_name,
        "Last Name": last_name,
        "Phone Number": normalized_phone,
        "External ID": external_id,
        "Notes": notes,
        "Auxiliary Data": aux,
    }


def export_ooma_batch_from_db_csv(
    db_csv_path: str | Path,
    output_csv_path: str | Path,
    batch_size: int = 500,
    watermark_path: str | Path | None = None,
) -> dict[str, Any]:
    source_path = Path(db_csv_path)
    output_path = Path(output_csv_path)
    watermark_file = Path(watermark_path) if watermark_path else None

    with source_path.open("r", encoding="utf-8", newline="") as handle:
        input_rows = [dict(row) for row in csv.DictReader(handle)]

    filtered_rows = _apply_relevance_filter(input_rows)
    deduped_rows = _dedupe_latest_by_lead(filtered_rows)

    watermark = _load_watermark(watermark_file)
    if watermark is not None:
        deduped_rows = [row for row in deduped_rows if _sort_key(row) > watermark]

    ordered = sorted(deduped_rows, key=_sort_key, reverse=True)
    selected = ordered[:batch_size]
    ooma_rows = [_to_ooma_row(row) for row in selected]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OOMA_COLUMNS)
        writer.writeheader()
        writer.writerows(ooma_rows)

    saved_watermark = None
    if watermark_file is not None and selected:
        latest_row = max(selected, key=_sort_key)
        latest_ts, latest_lead = _sort_key(latest_row)
        saved_watermark = str(_save_watermark(watermark_file, latest_ts, latest_lead))

    return {
        "source_rows": len(input_rows),
        "filtered_rows": len(filtered_rows),
        "deduped_rows": len(deduped_rows),
        "exported_rows": len(ooma_rows),
        "output_csv": str(output_path),
        "watermark": saved_watermark,
    }
