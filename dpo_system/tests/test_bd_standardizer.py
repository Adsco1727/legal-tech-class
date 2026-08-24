from __future__ import annotations

import csv
from pathlib import Path

from dpo_system.src.bd_standardizer import convert_bd_csvs_to_standard, write_standard_exports


def test_convert_bd_csvs_to_standard_keeps_phone_and_user_id(tmp_path: Path) -> None:
    source = tmp_path / "bd_raw.csv"
    source.write_text(
        "user_id,phone_number,first_name,last_name,email,address1,city,state_code,zip_code,profession_name\n"
        "u-001,14165550100,Alice,Ng,alice@example.com,1 Main,Toronto,ON,M5V,Dentist\n"
        "u-002,14165550101,Bob,Li,bob@example.com,2 Main,Toronto,ON,M5V,Doctor\n",
        encoding="utf-8",
    )

    leads, workflow, stats = convert_bd_csvs_to_standard(
        [source],
        list_name="dr_dentist_bd",
        outreach_purpose="onboarding",
        list_source="bd_live_db",
        source_system="bd_db",
        campaign_name="csf_launch",
    )

    assert stats["kept"] == 2
    assert leads[0]["lead_id"] == "u-001"
    assert leads[0]["phone_number"] == "+14165550100"
    assert workflow[0]["record_id"] == "u-001"
    assert workflow[0]["outbound_status"] == "planned"


def test_write_standard_exports_writes_expected_headers(tmp_path: Path) -> None:
    leads = [
        {
            "lead_id": "u-001",
            "phone_number": "+14165550100",
            "full_name": "Alice Ng",
            "email": "alice@example.com",
            "address": "1 Main, Toronto",
            "notes": "Dentist",
            "source_system": "bd_db",
            "campaign_name": "csf_launch",
        }
    ]
    workflow = [
        {
            "record_id": "u-001",
            "list_name": "dr_dentist_bd",
            "outreach_purpose": "onboarding",
            "list_source": "bd_live_db",
            "outbound_status": "planned",
            "workflow_notes": "standardized",
        }
    ]

    leads_out = tmp_path / "google_standard_export_live.csv"
    workflow_out = tmp_path / "bd_workflow_export_live.csv"
    write_standard_exports(leads, workflow, leads_output=leads_out, workflow_output=workflow_out)

    with leads_out.open("r", encoding="utf-8", newline="") as handle:
        headers = csv.DictReader(handle).fieldnames
    with workflow_out.open("r", encoding="utf-8", newline="") as handle:
        workflow_headers = csv.DictReader(handle).fieldnames

    assert headers == [
        "lead_id",
        "phone_number",
        "full_name",
        "email",
        "address",
        "notes",
        "source_system",
        "campaign_name",
    ]
    assert workflow_headers == [
        "record_id",
        "list_name",
        "outreach_purpose",
        "list_source",
        "outbound_status",
        "workflow_notes",
    ]
