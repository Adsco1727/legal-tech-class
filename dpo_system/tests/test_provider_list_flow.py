from __future__ import annotations

import csv
from pathlib import Path

from dpo_system.src.csf_ingest import ingest_csf_seed
from dpo_system.src.ledger_io import create_ledger_workbook
from dpo_system.src.list_builder import build_provider_ready_outbound_rows, export_provider_ready_outbound_list


def test_ingested_rows_can_be_assembled_into_provider_ready_outbound_rows(tmp_path: Path) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)

    seed_path = tmp_path / "csf_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,email,address,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-100,(555) 010-7,Alice Example,alice@example.com,789 Pine St,CSF-Ooma-Launch,Ooma/CSF,seeded,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    ingest_csf_seed(seed_path, ledger_path)

    rows = build_provider_ready_outbound_rows(ledger_path=ledger_path, list_name="csf_launch")

    assert len(rows) == 1
    assert rows[0]["record_id"] == "rec-100"
    assert rows[0]["normalized_phone_number"] == "+15550107"
    assert rows[0]["list_name"] == "csf_launch"
    assert rows[0]["outbound_status"] == "planned"


def test_export_provider_ready_outbound_list_writes_csv(tmp_path: Path) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)

    seed_path = tmp_path / "csf_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,email,address,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-200,(555) 010-8,Bob Example,bob@example.com,321 Elm St,CSF-Ooma-Launch,Ooma/CSF,seeded,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    ingest_csf_seed(seed_path, ledger_path)
    output_path = tmp_path / "provider_ready_outbound.csv"

    export_provider_ready_outbound_list("csf_launch", output_path, ledger_path=ledger_path)

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["record_id"] == "rec-200"
    assert rows[0]["normalized_phone_number"] == "+15550108"
    assert rows[0]["provider_format"] == "csv"
