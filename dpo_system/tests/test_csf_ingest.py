from __future__ import annotations

from pathlib import Path

from dpo_system.src.csf_ingest import ingest_csf_seed
from dpo_system.src.ledger_io import create_ledger_workbook, read_rows


def test_ingest_csf_seed_writes_normalized_rows_to_ledger(tmp_path: Path) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)

    seed_path = tmp_path / "csf_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,email,address,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-100,(555) 010-7,Alice Example,alice@example.com,789 Pine St,CSF-Ooma-Launch,Ooma/CSF,seeded,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    ingested = ingest_csf_seed(seed_path, ledger_path)

    assert len(ingested) == 1
    assert ingested[0]["workflow_id"] == "csf-rec-100"
    assert ingested[0]["list_name"] == "csf_launch"
    assert ingested[0]["outreach_purpose"] == "consent_follow_up"
    assert ingested[0]["list_source"] == "docassemble"
    assert ingested[0]["outbound_status"] == "planned"

    rows = read_rows("GOVERNANCE_QUEUE", path=ledger_path)
    assert len(rows) == 1
    assert rows[0]["workflow_id"] == "csf-rec-100"
    assert rows[0]["list_name"] == "csf_launch"
    assert rows[0]["outbound_status"] == "planned"
