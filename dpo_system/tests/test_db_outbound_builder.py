from __future__ import annotations

import csv
import json
from pathlib import Path

from dpo_system.src.db_outbound_builder import build_outbound_rows_from_db_exports, write_outbound_batches
from dpo_system.src.phase_runner import main


def test_build_outbound_rows_from_db_exports_merges_leads_and_workflow(tmp_path: Path) -> None:
    leads_path = tmp_path / "google_standard.csv"
    leads_path.write_text(
        "lead_id,phone_number,full_name,email,address,notes,source_system,campaign_name\n"
        "rec-100,5550100,Alice Example,alice@example.com,123 Main St,google note,google_db,CSF Launch\n"
        "rec-101,5550101,Bob Example,bob@example.com,456 Oak St,second note,google_db,CSF Launch\n",
        encoding="utf-8",
    )

    workflow_path = tmp_path / "bd_workflow.csv"
    workflow_path.write_text(
        "record_id,list_name,outreach_purpose,list_source,outbound_status,workflow_notes\n"
        "rec-100,csf_launch,consent_follow_up,bd32,planned,founder ok\n"
        "rec-101,csf_launch,consent_follow_up,bd32,queued,ready to dial\n"
        "rec-999,csf_launch,consent_follow_up,bd32,planned,missing in lead db\n",
        encoding="utf-8",
    )

    rows = build_outbound_rows_from_db_exports(leads_path, workflow_path)

    assert len(rows) == 2
    assert rows[0]["record_id"] == "rec-100"
    assert rows[0]["list_name"] == "csf_launch"
    assert rows[0]["list_source"] == "bd32"
    assert rows[0]["notes"] == "google note | founder ok"
    assert rows[1]["record_id"] == "rec-101"


def test_write_outbound_batches_splits_rows_into_deterministic_files(tmp_path: Path) -> None:
    rows = [
        {
            "record_id": f"rec-{index:03d}",
            "phone_number": f"55501{index:02d}",
            "full_name": f"Lead {index}",
            "list_name": "csf_launch",
            "outreach_purpose": "consent_follow_up",
            "list_source": "bd32",
            "notes": "",
            "email": "",
            "address": "",
            "source_system": "google_db",
            "campaign_name": "CSF Launch",
            "outbound_status": "planned",
        }
        for index in range(5)
    ]

    manifest = write_outbound_batches(rows, tmp_path, batch_size=2, file_prefix="csf_batch")

    assert manifest["total_batches"] == 3
    assert manifest["batch_counts"] == [2, 2, 1]
    first_batch = Path(manifest["files"][0])
    with first_batch.open("r", encoding="utf-8", newline="") as handle:
        written_rows = list(csv.DictReader(handle))
    assert len(written_rows) == 2
    assert written_rows[0]["record_id"] == "rec-000"


def test_build_db_outbound_cli_writes_manifest(tmp_path: Path, monkeypatch) -> None:
    leads_path = tmp_path / "google_standard.csv"
    leads_path.write_text(
        "lead_id,phone_number,full_name,email,address,notes,source_system,campaign_name\n"
        "rec-100,5550100,Alice Example,alice@example.com,123 Main St,google note,google_db,CSF Launch\n"
        "rec-101,5550101,Bob Example,bob@example.com,456 Oak St,second note,google_db,CSF Launch\n",
        encoding="utf-8",
    )

    workflow_path = tmp_path / "bd_workflow.csv"
    workflow_path.write_text(
        "record_id,list_name,outreach_purpose,list_source,outbound_status,workflow_notes\n"
        "rec-100,csf_launch,consent_follow_up,bd32,planned,founder ok\n"
        "rec-101,csf_launch,consent_follow_up,bd32,queued,ready to dial\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "outbound_batches"
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "build-db-outbound",
            str(leads_path),
            str(workflow_path),
            "--output-dir",
            str(output_dir),
            "--batch-size",
            "1",
        ],
    )

    exit_code = main()

    assert exit_code == 0
    manifest = json.loads((output_dir / "csf_batch_manifest.json").read_text(encoding="utf-8"))
    assert manifest["total_rows"] == 2
    assert manifest["total_batches"] == 2
