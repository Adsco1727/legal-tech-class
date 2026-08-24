from __future__ import annotations

import csv
import json
from pathlib import Path

from dpo_system.src.ooma_export_pack import export_ooma_batch_from_db_csv


def _write_db_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "lead_id",
                "first_name",
                "last_name",
                "phone_number",
                "external_id",
                "notes",
                "auxiliary_data",
                "updated_at",
                "status",
                "is_callable",
                "is_suppressed",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "lead_id": "lead-1",
                "first_name": "alice",
                "last_name": "example",
                "phone_number": "(555) 123-0001",
                "external_id": "ext-1",
                "notes": "hot",
                "auxiliary_data": "aux-1",
                "updated_at": "2026-08-12T10:00:00Z",
                "status": "active",
                "is_callable": "true",
                "is_suppressed": "false",
            }
        )
        writer.writerow(
            {
                "lead_id": "lead-1",
                "first_name": "alice",
                "last_name": "example",
                "phone_number": "(555) 123-0001",
                "external_id": "ext-1",
                "notes": "hot",
                "auxiliary_data": "aux-1b",
                "updated_at": "2026-08-12T11:00:00Z",
                "status": "active",
                "is_callable": "true",
                "is_suppressed": "false",
            }
        )
        writer.writerow(
            {
                "lead_id": "lead-2",
                "first_name": "bob",
                "last_name": "example",
                "phone_number": "555-123-0002",
                "external_id": "",
                "notes": "normal",
                "auxiliary_data": "aux-2",
                "updated_at": "2026-08-12T09:00:00Z",
                "status": "active",
                "is_callable": "true",
                "is_suppressed": "false",
            }
        )
        writer.writerow(
            {
                "lead_id": "lead-3",
                "first_name": "c",
                "last_name": "d",
                "phone_number": "555-123-0003",
                "external_id": "ext-3",
                "notes": "suppressed",
                "auxiliary_data": "aux-3",
                "updated_at": "2026-08-12T12:00:00Z",
                "status": "active",
                "is_callable": "true",
                "is_suppressed": "true",
            }
        )


def test_export_ooma_batch_is_deduped_and_watermarked(tmp_path: Path) -> None:
    source = tmp_path / "db.csv"
    output = tmp_path / "ooma.csv"
    watermark = tmp_path / "watermark.json"
    _write_db_csv(source)

    first = export_ooma_batch_from_db_csv(source, output, batch_size=500, watermark_path=watermark)

    assert first["source_rows"] == 4
    assert first["filtered_rows"] == 3
    assert first["deduped_rows"] == 2
    assert first["exported_rows"] == 2
    assert watermark.exists()

    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["External ID"] == "ext-1"
    assert rows[0]["Phone Number"] == "+15551230001"
    assert rows[1]["External ID"] == "lead-2"

    watermark_payload = json.loads(watermark.read_text(encoding="utf-8"))
    assert watermark_payload["lead_id"] == "lead-1"

    second = export_ooma_batch_from_db_csv(source, output, batch_size=500, watermark_path=watermark)
    assert second["exported_rows"] == 0


def test_export_ooma_batch_derives_names_from_full_name_url(tmp_path: Path) -> None:
    source = tmp_path / "db_url_name.csv"
    output = tmp_path / "ooma_url_name.csv"

    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "lead_id",
                "first_name",
                "last_name",
                "full_name",
                "phone_number",
                "external_id",
                "notes",
                "auxiliary_data",
                "updated_at",
                "status",
                "is_callable",
                "is_suppressed",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "lead_id": "35674",
                "first_name": "",
                "last_name": "",
                "full_name": "https://www.directprivateoffers.net/philadelphia/ellen-weber-35674",
                "phone_number": "+16109939060",
                "external_id": "35674",
                "notes": "Robin Hood Ventures",
                "auxiliary_data": "",
                "updated_at": "2026-08-12T10:00:00Z",
                "status": "active",
                "is_callable": "true",
                "is_suppressed": "false",
            }
        )

    result = export_ooma_batch_from_db_csv(source, output, batch_size=500)

    assert result["exported_rows"] == 1
    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["First Name"] == "Ellen"
    assert rows[0]["Last Name"] == "Weber"
