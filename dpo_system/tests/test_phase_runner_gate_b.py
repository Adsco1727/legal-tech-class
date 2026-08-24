from __future__ import annotations

import csv
import json
from pathlib import Path

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


def test_gate_b_readiness_passes_with_complete_response(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "repo_manifest.csv"
    seed = tmp_path / "seed.csv"
    response = tmp_path / "ooma_response_fields.json"
    report = tmp_path / "gate_b_report.json"

    _write_min_manifest(manifest)
    _write_seed(seed)

    response_payload = {
        "csv_import_supported": True,
        "required_optional_fields_confirmed": True,
        "phone_format_rule_confirmed": True,
        "identifier_roundtrip_confirmed": True,
        "custom_fields_behavior_confirmed": True,
        "upload_limits_confirmed": True,
        "dedupe_behavior_confirmed": True,
        "append_replace_behavior_confirmed": True,
        "disposition_export_confirmed": True,
        "pilot_10_row_approved": True,
        "pilot_25_to_50_row_approved": True,
        "decision": "accepted_with_changes",
        "notes": "Approved pending minor column rename.",
    }
    response.write_text(json.dumps(response_payload, indent=2), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "--repo-manifest",
            str(manifest),
            "--dialer-seed",
            str(seed),
            "gate-b-readiness",
            "--response",
            str(response),
            "--report",
            str(report),
        ],
    )

    exit_code = main()
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["decision"] == "accepted_with_changes"


def test_gate_b_readiness_fails_when_response_is_incomplete(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "repo_manifest.csv"
    seed = tmp_path / "seed.csv"
    response = tmp_path / "ooma_response_fields.json"
    report = tmp_path / "gate_b_report.json"

    _write_min_manifest(manifest)
    _write_seed(seed)

    response_payload = {
        "csv_import_supported": True,
        "required_optional_fields_confirmed": True,
        "decision": "not_accepted",
        "notes": "Need more detail.",
    }
    response.write_text(json.dumps(response_payload, indent=2), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "--repo-manifest",
            str(manifest),
            "--dialer-seed",
            str(seed),
            "gate-b-readiness",
            "--response",
            str(response),
            "--report",
            str(report),
        ],
    )

    exit_code = main()
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "FAIL"
    assert "phone_format_rule_confirmed" in payload["missing_fields"]
