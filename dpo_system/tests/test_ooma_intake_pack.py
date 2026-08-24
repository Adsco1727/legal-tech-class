from __future__ import annotations

from dpo_system.src.ooma_intake_pack import process_ooma_rows


def test_ooma_intake_acceptance_rules() -> None:
    rows = [
        {
            "First Name": "alice",
            "Last Name": "example",
            "Phone Number": "(555) 123-4567",
            "External ID": "",
            "Notes": "urgent callback requested",
            "Auxiliary Data": "a",
        },
        {
            "First Name": "bob",
            "Last Name": "example",
            "Phone Number": "1-555-123-4567",
            "External ID": "ext-2",
            "Notes": "",
            "Auxiliary Data": "",
        },
        {
            "First Name": "",
            "Last Name": "",
            "Phone Number": "555123456",
            "External ID": "ext-3",
            "Notes": "priority",
            "Auxiliary Data": "",
        },
    ]

    result = process_ooma_rows(rows)

    assert result["summary"]["total_rows"] == 3
    assert result["summary"]["accepted_count"] == 2
    assert result["summary"]["rejected_count"] == 1

    first = result["accepted"][0]
    second = result["accepted"][1]

    assert first["phone"] == "+15551234567"
    assert first["lane"] == "founder"
    assert first["full_name"] == "Alice Example"
    assert first["lead_id"]

    assert second["phone"] == "+15551234567"
    assert second["lane"] == "BD"
    assert second["lead_id"] == "ext-2"

    rejected = result["rejected"][0]
    assert rejected["rejection_reason"] == "missing_name"


def test_ooma_intake_rejects_non_numeric_phone() -> None:
    rows = [
        {
            "First Name": "Alice",
            "Last Name": "Example",
            "Phone Number": "555-ABC-4567",
            "External ID": "ext-1",
            "Notes": "",
            "Auxiliary Data": "",
        }
    ]

    result = process_ooma_rows(rows)

    assert result["summary"]["accepted_count"] == 0
    assert result["summary"]["rejected_count"] == 1
    assert result["rejected"][0]["rejection_reason"] == "non_numeric_phone"
