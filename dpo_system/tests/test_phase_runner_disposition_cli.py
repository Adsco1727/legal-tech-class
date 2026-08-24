from __future__ import annotations

from pathlib import Path

from dpo_system.src.csf_ingest import ingest_csf_seed
from dpo_system.src.ledger_io import create_ledger_workbook, read_rows
from dpo_system.src.phase_runner import main


def test_record_disposition_cli_writes_a_new_hop(tmp_path: Path, monkeypatch) -> None:
    ledger_path = tmp_path / "operator_ledger.xlsx"
    create_ledger_workbook(ledger_path)

    seed_path = tmp_path / "csf_seed.csv"
    seed_path.write_text(
        "record_id,phone_number,full_name,email,address,campaign_name,source_system,notes,list_name,outreach_purpose,list_source\n"
        "rec-400,(555) 010-10,Dana Example,dana@example.com,987 Cedar St,CSF-Ooma-Launch,Ooma/CSF,seeded,csf_launch,consent_follow_up,docassemble\n",
        encoding="utf-8",
    )

    ingest_csf_seed(seed_path, ledger_path)

    monkeypatch.setattr("sys.argv", ["phase_runner", "record-disposition", "csf-rec-400", "voicemail", "--notes", "left a message", "--ledger", str(ledger_path)])

    exit_code = main()

    assert exit_code == 0
    rows = read_rows("GOVERNANCE_QUEUE", path=ledger_path)
    assert len(rows) == 2
    assert rows[-1]["outbound_status"] == "voicemail"
    assert rows[-1]["hop_count"] == 2
