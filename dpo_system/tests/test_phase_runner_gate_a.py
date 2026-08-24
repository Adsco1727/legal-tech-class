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


def _write_vendor_packet(root: Path) -> None:
    ooma_dir = root / "dpo_system" / "vendor" / "ooma"
    ooma_dir.mkdir(parents=True, exist_ok=True)
    (ooma_dir / "ooma_vendor_email_draft.md").write_text("ok", encoding="utf-8")
    (ooma_dir / "ooma_sample_outbound_pilot.csv").write_text("record_id,phone_number,full_name,list_name,outreach_purpose,list_source\n", encoding="utf-8")
    (ooma_dir / "ooma_capability_checklist.md").write_text("ok", encoding="utf-8")


def test_gate_a_readiness_passes_with_vendor_packet(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "repo_manifest.csv"
    seed = tmp_path / "seed.csv"
    report = tmp_path / "gate_a_report.json"

    _write_min_manifest(manifest)
    _write_seed(seed)
    _write_vendor_packet(tmp_path)

    monkeypatch.setattr("dpo_system.src.phase_runner._root", lambda: tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "--repo-manifest",
            str(manifest),
            "--dialer-seed",
            str(seed),
            "gate-a-readiness",
            "--report",
            str(report),
        ],
    )

    exit_code = main()
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["synthetic"]["rows_built"] == 500
    assert payload["synthetic"]["preflight_status"] == "PASS"


def test_gate_a_readiness_fails_without_vendor_packet(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "repo_manifest.csv"
    seed = tmp_path / "seed.csv"
    report = tmp_path / "gate_a_report.json"

    _write_min_manifest(manifest)
    _write_seed(seed)

    monkeypatch.setattr("dpo_system.src.phase_runner._root", lambda: tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase_runner",
            "--repo-manifest",
            str(manifest),
            "--dialer-seed",
            str(seed),
            "gate-a-readiness",
            "--report",
            str(report),
        ],
    )

    exit_code = main()
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "FAIL"
    checks = {row["name"]: row for row in payload["checks"]}
    assert checks["vendor_packet_present"]["passed"] is False
