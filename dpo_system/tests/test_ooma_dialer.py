from __future__ import annotations

import csv
from pathlib import Path

from dpo_system.src.ledger_io import create_ledger_workbook, read_rows
from dpo_system.src.ooma_dialer import (
    build_ooma_autodialer_plan,
    export_provider_ready_csv,
    normalize_contact_record,
)
from dpo_system.src.phase_runner import queue_dialer_tasks


def test_build_ooma_autodialer_plan_uses_csf_ooma_fields(tmp_path: Path) -> None:
    seed_path = tmp_path / "ooma_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,campaign_name,source_system,notes\n"
        "rec-001,5550100,CSF-Ooma-Launch,Ooma/CSF,initial outbound\n"
        "rec-002,5550101,CSF-Ooma-Launch,Ooma/CSF,follow up\n",
        encoding="utf-8",
    )

    plan = build_ooma_autodialer_plan(seed_path)

    assert len(plan) == 2
    assert plan[0]["source_system"] == "Ooma/CSF"
    assert plan[0]["campaign_name"] == "CSF-Ooma-Launch"
    assert plan[0]["record_id"] == "rec-001"


def test_build_ooma_autodialer_plan_includes_list_generation_metadata(tmp_path: Path) -> None:
    seed_path = tmp_path / "ooma_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-003,5550102,CSF-Ooma-Launch,Ooma/CSF,initial outbound,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    plan = build_ooma_autodialer_plan(seed_path)

    assert len(plan) == 1
    assert plan[0]["list_name"] == "csf_launch"
    assert plan[0]["outreach_purpose"] == "consent_follow_up"
    assert plan[0]["list_source"] == "docassemble"
    assert plan[0]["outbound_status"] == "planned"


def test_queue_dialer_tasks_preserves_outbound_metadata(tmp_path: Path) -> None:
    seed_path = tmp_path / "ooma_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-004,5550103,CSF-Ooma-Launch,Ooma/CSF,initial outbound,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    plan = queue_dialer_tasks(seed_path, apply=False)

    assert len(plan) == 1
    assert plan[0]["list_name"] == "csf_launch"
    assert plan[0]["outreach_purpose"] == "consent_follow_up"
    assert plan[0]["list_source"] == "docassemble"
    assert plan[0]["outbound_status"] == "planned"


def test_queue_dialer_tasks_writes_outbound_metadata_to_ledger(tmp_path: Path, monkeypatch) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)
    monkeypatch.setattr("dpo_system.src.ledger_io.LEDGER_PATH", ledger_path)

    seed_path = tmp_path / "ooma_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-005,5550104,CSF-Ooma-Launch,Ooma/CSF,initial outbound,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    queue_dialer_tasks(seed_path, apply=True)

    rows = read_rows("GOVERNANCE_QUEUE", path=ledger_path)
    assert len(rows) == 1
    assert rows[0]["workflow_id"] == "dialer-rec-005"
    assert rows[0]["origin_repo"] == "dpo-system"
    assert rows[0]["hop_count"] == 1
    assert rows[0]["list_name"] == "csf_launch"
    assert rows[0]["outreach_purpose"] == "consent_follow_up"
    assert rows[0]["list_source"] == "docassemble"
    assert rows[0]["outbound_status"] == "planned"


def test_normalize_contact_record_formats_e164_and_email() -> None:
    normalized = normalize_contact_record(
        {
            "record_id": "rec-006",
            "full_name": "Jane Doe",
            "phone_number": "(555) 010-5",
            "email": " Jane@Example.com ",
            "address": "123 Main St",
        }
    )

    assert normalized["record_id"] == "rec-006"
    assert normalized["first_name"] == "Jane"
    assert normalized["last_name"] == "Doe"
    assert normalized["phone_number"] == "+15550105"
    assert normalized["email"] == "jane@example.com"
    assert normalized["address"] == "123 Main St"


def test_export_provider_ready_csv_writes_canonical_fields(tmp_path: Path) -> None:
    seed_path = tmp_path / "ooma_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,email,address,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-007,(555) 010-6,John Smith,john@example.com,456 Oak St,CSF-Ooma-Launch,Ooma/CSF,ready,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "provider_ready.csv"

    export_provider_ready_csv(seed_path, output_path)

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["record_id"] == "rec-007"
    assert rows[0]["normalized_phone_number"] == "+15550106"
    assert rows[0]["list_name"] == "csf_launch"
    assert rows[0]["outbound_status"] == "planned"
    assert rows[0]["provider_format"] == "csv"
