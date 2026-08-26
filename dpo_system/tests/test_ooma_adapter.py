from __future__ import annotations

import csv
from pathlib import Path

from dpo_system.src.ooma_adapter import seed_ooma_contacts_to_db


def test_seed_ooma_contacts_to_db(tmp_path: Path) -> None:
    csv_path = tmp_path / "ooma_contacts.csv"
    db_path = tmp_path / "ooma_dispatch.db"

    rows = [
        {
            "ID": "ooma-1",
            "Name": "Acme Legal",
            "Email": "ops@example.com",
            "Phone": "5550101234",
            "Consent": "1",
            "DNC": "0",
        },
        {
            "ID": "ooma-2",
            "Name": "Do Not Call Co",
            "Email": "noreply@example.com",
            "Phone": "5550109999",
            "Consent": "1",
            "DNC": "1",
        },
        {
            "ID": "ooma-3",
            "Name": "Unverified Contact",
            "Email": "hello@example.com",
            "Phone": "5550103333",
            "Consent": "0",
            "DNC": "0",
        },
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["ID", "Name", "Email", "Phone", "Consent", "DNC"])
        writer.writeheader()
        writer.writerows(rows)

    result = seed_ooma_contacts_to_db(str(csv_path), str(db_path), operator_id="operator:test")

    manifest = result["manifest"]
    assert manifest["total_rows"] == 3
    assert manifest["ingested"] == 3
    assert manifest["passed_compliance"] == 1
    assert manifest["queued"] == 1
    assert manifest["rejected"] == 2
    assert manifest["errors"] == 0
    assert len(result["lead_keys"]) == 3
