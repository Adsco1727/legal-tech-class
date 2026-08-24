from __future__ import annotations

import csv
import json
from pathlib import Path

from dpo_system.src.ledger_io import create_ledger_workbook, read_rows
from dpo_system.src.phase_runner import main


def _write_min_manifest(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "repo_name",
                "repo_url",
                "branch",
                "install_enabled",
                "github_enabled",
                "wave",
                "repo_slug",
                "ingestion_type",
                "source_path",
                "priority",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "repo_name": "legal-tech-class",
                "repo_url": "https://github.com/Adsco1727/legal-tech-class.git",
                "branch": "main",
                "install_enabled": "yes",
                "github_enabled": "no",
                "wave": "4",
                "repo_slug": "Adsco1727/legal-tech-class",
                "ingestion_type": "custom",
                "source_path": "docs/",
                "priority": "2",
                "notes": "test",
            }
        )


def _write_seed(path: Path) -> None:
    path.write_text("record_id,phone_number,campaign_name\nrec-1,5550100,csf\n", encoding="utf-8")


def test_validate_ooma_csv_cli_writes_report_and_rejections(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "repo_manifest.csv"
    seed = tmp_path / "seed.csv"
    csv_path = tmp_path / "ooma.csv"
    report = tmp_path / "report.json"
    rejections = tmp_path / "rejections.csv"

    _write_min_manifest(manifest)
    _write_seed(seed)

    csv_path.write_text(
        "First Name,Last Name,Phone Number,External ID,Notes,Auxiliary Data\n"
        "Alice,Example,(555) 123-4567,ext-1,urgent callback requested,aux\n"
        "Bob,Example,555123456,ext-2,,\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "--repo-manifest",
            str(manifest),
            "--dialer-seed",
            str(seed),
            "validate-ooma-csv",
            str(csv_path),
            "--report",
            str(report),
            "--rejections",
            str(rejections),
        ],
    )

    exit_code = main()

    assert exit_code == 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["summary"]["accepted_count"] == 1
    assert payload["summary"]["rejected_count"] == 1
    assert rejections.exists()


def test_export_ooma_batch_cli_writes_template_csv(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "repo_manifest.csv"
    seed = tmp_path / "seed.csv"
    db_csv = tmp_path / "db.csv"
    output = tmp_path / "ooma_batch.csv"
    watermark = tmp_path / "watermark.json"

    _write_min_manifest(manifest)
    _write_seed(seed)

    db_csv.write_text(
        "lead_id,first_name,last_name,phone_number,external_id,notes,auxiliary_data,updated_at,status,is_callable,is_suppressed\n"
        "lead-1,Alice,Example,(555) 123-4567,ext-1,urgent,aux,2026-08-12T12:00:00Z,active,true,false\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "--repo-manifest",
            str(manifest),
            "--dialer-seed",
            str(seed),
            "export-ooma-batch",
            str(db_csv),
            "--output",
            str(output),
            "--batch-size",
            "500",
            "--watermark",
            str(watermark),
        ],
    )

    exit_code = main()

    assert exit_code == 0
    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["First Name"] == "Alice"
    assert rows[0]["Phone Number"] == "+15551234567"


def test_queue_regd_enrichment_cli_writes_crm_queue(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "repo_manifest.csv"
    seed = tmp_path / "seed.csv"
    ledger_path = tmp_path / "operator_ledger.xlsx"
    targets_csv = tmp_path / "regd_enrichment_targets.csv"

    _write_min_manifest(manifest)
    _write_seed(seed)
    create_ledger_workbook(ledger_path)

    targets_csv.write_text(
        "lead_id,action_type,priority,notes\n"
        "0001193125-26-347217,enrich,1,rss_seed_missing_phone\n"
        ",enrich,1,missing id should skip\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("dpo_system.src.ledger_io.LEDGER_PATH", ledger_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "--repo-manifest",
            str(manifest),
            "--dialer-seed",
            str(seed),
            "queue-regd-enrichment",
            str(targets_csv),
            "--ledger",
            str(ledger_path),
        ],
    )

    exit_code = main()

    assert exit_code == 0
    crm_rows = read_rows("CRM_QUEUE", path=ledger_path)
    assert len(crm_rows) == 1
    assert crm_rows[0]["lead_id"] == "0001193125-26-347217"
    assert crm_rows[0]["action_type"] == "enrich"

    exit_code_second = main()
    assert exit_code_second == 0
    crm_rows_second = read_rows("CRM_QUEUE", path=ledger_path)
    assert len(crm_rows_second) == 1
