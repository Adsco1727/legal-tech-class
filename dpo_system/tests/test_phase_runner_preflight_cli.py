from __future__ import annotations

import json
from pathlib import Path

from dpo_system.src.ledger_io import create_ledger_workbook, read_rows
from dpo_system.src.phase_runner import main


def test_preflight_csf_cli_fails_and_writes_report(tmp_path: Path, monkeypatch) -> None:
    seed_path = tmp_path / "bad_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,list_name,outreach_purpose,list_source,notes,email,address,source_system\n"
        "dup-001,5550100,Alice Example,csf_launch,consent_follow_up,docassemble,seeded,alice@example.com,123 Main St,google_db\n"
        "dup-001,5550101,,csf_launch,consent_follow_up,docassemble,seeded,bob@example.com,456 Oak St,google_db\n",
        encoding="utf-8",
    )

    report_path = tmp_path / "preflight_report.json"
    registry_path = tmp_path / "registry.txt"

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "preflight-csf",
            str(seed_path),
            "--expected-rows",
            "2",
            "--registry",
            str(registry_path),
            "--report",
            str(report_path),
        ],
    )

    exit_code = main()

    assert exit_code == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "FAIL"
    assert report["summary"]["error_count"] >= 1


def test_preflight_csf_cli_allows_rerun_when_ids_are_already_registered(tmp_path: Path, monkeypatch) -> None:
    seed_path = tmp_path / "rerun_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,list_name,outreach_purpose,list_source,notes,email,address,source_system\n"
        "rec-100,5550100,Alice Example,csf_launch,consent_follow_up,docassemble,seeded,alice@example.com,123 Main St,google_db\n"
        "rec-101,5550101,Bob Example,csf_launch,consent_follow_up,docassemble,seeded,bob@example.com,456 Oak St,google_db\n",
        encoding="utf-8",
    )

    report_path = tmp_path / "preflight_report.json"
    registry_path = tmp_path / "registry.txt"
    registry_path.write_text("rec-100\nrec-101\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "preflight-csf",
            str(seed_path),
            "--expected-rows",
            "2",
            "--registry",
            str(registry_path),
            "--report",
            str(report_path),
        ],
    )

    exit_code = main()

    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["warnings"]


def test_docassemble_cli_runs_approved_workflow(tmp_path: Path, monkeypatch) -> None:
    payload_path = tmp_path / "docassemble_payload.json"
    result_path = tmp_path / "docassemble_result.json"
    payload_path.write_text(
        json.dumps(
            {
                "jurisdiction": "us",
                "matter_type": "employment",
                "client_name": "Acme Legal",
                "document_date": "2026-08-11",
                "source": "docassemble_cli_test",
                "list_name": "employment_launch",
                "outreach_purpose": "onboarding",
                "list_source": "docassemble_cli",
                "priority": 3,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "run-docassemble-workflow",
            str(payload_path),
            "--operator-id",
            "DPO",
            "--result-path",
            str(result_path),
        ],
    )

    exit_code = main()

    assert exit_code == 0
    assert result_path.exists()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "approved_and_synced"
    assert result["task_id"].startswith("doc-")


def test_run_standard_pipeline_builds_batches_and_preflights(tmp_path: Path, monkeypatch) -> None:
    leads_path = tmp_path / "leads.csv"
    workflow_path = tmp_path / "workflow.csv"
    output_dir = tmp_path / "outbound_batches"
    report_dir = tmp_path / "preflight_reports"
    registry_path = tmp_path / "registry.txt"

    leads_path.write_text(
        "lead_id,phone_number,full_name,email,address,notes,source_system,campaign_name\n"
        "rec-1,5550100,Alice Example,alice@example.com,123 Main St,seeded,google_db,csf_launch\n"
        "rec-2,5550101,Bob Example,bob@example.com,456 Oak St,seeded,google_db,csf_launch\n",
        encoding="utf-8",
    )
    workflow_path.write_text(
        "record_id,list_name,outreach_purpose,list_source,outbound_status,workflow_notes\n"
        "rec-1,csf_launch,onboarding,bd_live_db,planned,seeded\n"
        "rec-2,csf_launch,onboarding,bd_live_db,planned,seeded\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "run-standard-pipeline",
            str(leads_path),
            str(workflow_path),
            "--output-dir",
            str(output_dir),
            "--batch-size",
            "1",
            "--registry",
            str(registry_path),
            "--report-dir",
            str(report_dir),
        ],
    )

    exit_code = main()

    assert exit_code == 0
    manifest = json.loads((output_dir / "csf_batch_manifest.json").read_text(encoding="utf-8"))
    assert manifest["total_batches"] == 2
    assert (report_dir / "csf_batch_001_of_002_preflight_report.json").exists()
    assert (report_dir / "csf_batch_002_of_002_preflight_report.json").exists()


def test_ingest_csf_batch_blocks_on_preflight_failure(tmp_path: Path, monkeypatch) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)

    seed_path = tmp_path / "short_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,list_name,outreach_purpose,list_source,notes,email,address,source_system\n"
        "rec-001,5550100,Alice Example,csf_launch,consent_follow_up,docassemble,seeded,alice@example.com,123 Main St,google_db\n",
        encoding="utf-8",
    )

    report_path = tmp_path / "batch_preflight_report.json"
    registry_path = tmp_path / "registry.txt"

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "ingest-csf-batch",
            str(seed_path),
            "--ledger",
            str(ledger_path),
            "--expected-rows",
            "2",
            "--registry",
            str(registry_path),
            "--report",
            str(report_path),
        ],
    )

    exit_code = main()

    assert exit_code == 1
    rows = read_rows("GOVERNANCE_QUEUE", path=ledger_path)
    assert rows == []
    assert registry_path.exists() is False


def test_ingest_csf_batch_ingests_and_registers_ids(tmp_path: Path, monkeypatch) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)

    seed_path = tmp_path / "good_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,list_name,outreach_purpose,list_source,notes,email,address,source_system\n"
        "rec-100,5550100,Alice Example,csf_launch,consent_follow_up,docassemble,seeded,alice@example.com,123 Main St,google_db\n"
        "rec-101,5550101,Bob Example,csf_launch,consent_follow_up,docassemble,seeded,bob@example.com,456 Oak St,google_db\n",
        encoding="utf-8",
    )

    report_path = tmp_path / "batch_preflight_report.json"
    registry_path = tmp_path / "registry.txt"

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "ingest-csf-batch",
            str(seed_path),
            "--ledger",
            str(ledger_path),
            "--expected-rows",
            "2",
            "--registry",
            str(registry_path),
            "--report",
            str(report_path),
        ],
    )

    exit_code = main()

    assert exit_code == 0
    rows = read_rows("GOVERNANCE_QUEUE", path=ledger_path)
    assert len(rows) == 2
    registry_values = [line.strip() for line in registry_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert registry_values == ["rec-100", "rec-101"]
