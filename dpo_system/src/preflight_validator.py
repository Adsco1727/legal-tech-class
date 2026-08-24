"""Strict preflight validation for outbound CSF/Ooma seed batches."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ooma_dialer import normalize_contact_record

REQUIRED_FIELDS = [
    "record_id",
    "phone_number",
    "full_name",
    "list_name",
    "outreach_purpose",
    "list_source",
]

OPTIONAL_FIELDS = [
    "notes",
    "email",
    "address",
    "source_system",
    "campaign_name",
    "outbound_status",
]

ALLOWED_FIELDS = set(REQUIRED_FIELDS + OPTIONAL_FIELDS)
RECORD_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,128}$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_csv_rows(seed_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with seed_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return fieldnames, rows


def _load_registry_ids(registry_path: Path | None) -> set[str]:
    if registry_path is None or not registry_path.exists():
        return set()
    values = registry_path.read_text(encoding="utf-8").splitlines()
    return {v.strip() for v in values if v.strip()}


def _canonical_digest(rows: list[dict[str, str]]) -> str:
    serializable: list[dict[str, str]] = []
    for row in rows:
        serializable.append({key: (row.get(key) or "").strip() for key in sorted(ALLOWED_FIELDS)})
    payload = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_csf_seed_batch(
    seed_path: str | Path,
    expected_rows: int = 500,
    registry_path: str | Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Validate a CSF seed file against strict outbound preflight rules."""
    path = Path(seed_path)
    registry = Path(registry_path) if registry_path is not None and str(registry_path).strip() else None

    report: dict[str, Any] = {
        "validator": "dpo_csf_preflight",
        "version": 1,
        "seed_path": str(path),
        "generated_at": _utc_now_iso(),
        "expected_rows": expected_rows,
        "actual_rows": 0,
        "status": "FAIL",
        "errors": [],
        "warnings": [],
        "checks": [],
        "input_digest_sha256": "",
    }

    if not path.exists():
        report["errors"].append(
            {
                "code": "seed_not_found",
                "message": f"seed file does not exist: {path}",
            }
        )
        report["checks"].append({"name": "seed_exists", "passed": False})
        return report, []

    fieldnames, rows = _read_csv_rows(path)
    report["actual_rows"] = len(rows)
    report["input_digest_sha256"] = _canonical_digest(rows)

    missing_headers = [h for h in REQUIRED_FIELDS if h not in fieldnames]
    unknown_headers = [h for h in fieldnames if h not in ALLOWED_FIELDS]

    report["checks"].append({"name": "required_headers_present", "passed": len(missing_headers) == 0, "missing_headers": missing_headers})
    if missing_headers:
        report["errors"].append(
            {
                "code": "missing_headers",
                "message": "required headers are missing",
                "missing_headers": missing_headers,
            }
        )

    report["checks"].append({"name": "no_unknown_headers", "passed": len(unknown_headers) == 0, "unknown_headers": unknown_headers})
    if unknown_headers:
        report["errors"].append(
            {
                "code": "unknown_headers",
                "message": "seed contains headers outside canonical outbound schema",
                "unknown_headers": unknown_headers,
            }
        )

    actual_rows = len(rows)
    row_count_ok = expected_rows <= 0 or actual_rows == expected_rows
    report["checks"].append(
        {
            "name": "row_count_matches_expected",
            "passed": row_count_ok,
            "expected_rows": expected_rows,
            "actual_rows": actual_rows,
        }
    )
    if not row_count_ok:
        report["errors"].append(
            {
                "code": "row_count_mismatch",
                "message": f"expected {expected_rows} rows but found {actual_rows}",
            }
        )

    existing_ids = _load_registry_ids(registry)
    record_ids: list[str] = []
    seen_in_batch: set[str] = set()

    for idx, row in enumerate(rows, start=2):
        normalized = normalize_contact_record(row)
        record_id = str(row.get("record_id") or "").strip()
        record_ids.append(record_id)

        if not record_id:
            report["errors"].append(
                {
                    "code": "missing_record_id",
                    "message": "record_id is required",
                    "row": idx,
                }
            )
        elif not RECORD_ID_PATTERN.match(record_id):
            report["errors"].append(
                {
                    "code": "invalid_record_id",
                    "message": "record_id must match ^[A-Za-z0-9_-]{3,128}$",
                    "row": idx,
                    "record_id": record_id,
                }
            )
        elif record_id in seen_in_batch:
            report["errors"].append(
                {
                    "code": "duplicate_record_id_in_batch",
                    "message": "duplicate record_id found in current batch",
                    "row": idx,
                    "record_id": record_id,
                }
            )
        else:
            seen_in_batch.add(record_id)

        if record_id and record_id in existing_ids:
            report["warnings"].append(
                {
                    "code": "record_id_already_in_registry",
                    "message": "record_id already exists in global registry; treating as rerun warning",
                    "row": idx,
                    "record_id": record_id,
                }
            )

        for required in REQUIRED_FIELDS:
            value = str(row.get(required) or "").strip()
            if required == "phone_number":
                value = str(normalized.get("normalized_phone_number") or "").strip()
            if not value:
                report["errors"].append(
                    {
                        "code": "missing_required_value",
                        "message": f"{required} is required",
                        "row": idx,
                        "column": required,
                    }
                )

    no_errors = len(report["errors"]) == 0
    report["checks"].append({"name": "rows_valid", "passed": no_errors})
    report["status"] = "PASS" if no_errors else "FAIL"
    report["summary"] = {
        "error_count": len(report["errors"]),
        "warning_count": len(report["warnings"]),
        "unique_record_ids": len({rid for rid in record_ids if rid}),
    }
    return report, record_ids


def write_preflight_report(report: dict[str, Any], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return destination


def persist_record_id_registry(record_ids: list[str], registry_path: str | Path) -> Path:
    destination = Path(registry_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_registry_ids(destination)
    ordered_new: list[str] = []
    for record_id in record_ids:
        if not record_id or record_id in existing:
            continue
        existing.add(record_id)
        ordered_new.append(record_id)

    if ordered_new:
        with destination.open("a", encoding="utf-8", newline="") as handle:
            for record_id in ordered_new:
                handle.write(f"{record_id}\n")
    return destination