from __future__ import annotations

from pathlib import Path

from dpo_system.src.csf_ingest import ingest_csf_seed
from dpo_system.src.ledger_io import create_ledger_workbook, read_rows
from dpo_system.src.operator_actions import record_outbound_disposition


def test_record_outbound_disposition_creates_a_new_hop_row(tmp_path: Path) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)

    seed_path = tmp_path / "csf_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,email,address,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-300,(555) 010-9,Carol Example,carol@example.com,654 Maple St,CSF-Ooma-Launch,Ooma/CSF,seeded,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    ingest_csf_seed(seed_path, ledger_path)

    record_outbound_disposition("csf-rec-300", "voicemail", notes="left a message", ledger_path=ledger_path)

    rows = read_rows("GOVERNANCE_QUEUE", path=ledger_path)
    assert len(rows) == 2
    assert rows[-1]["workflow_id"] == "csf-rec-300"
    assert rows[-1]["hop_count"] == 2
    assert rows[-1]["outbound_status"] == "voicemail"
    assert "voicemail" in rows[-1]["notes"]
    assert rows[-1]["status"] == "complete"
