import sqlite3

import pytest

from dpo_system.src.sqlite_manager import DPODatabaseManager


def test_database_initializes_expected_tables(tmp_path):
    db_path = tmp_path / "dpo_test.db"
    manager = DPODatabaseManager(str(db_path))

    with sqlite3.connect(db_path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

    names = {row[0] for row in tables}
    assert {"standard_leads", "bd_leads", "evidence_blocks", "crm_sync_queue", "compliance_rejections"}.issubset(names)


def test_standard_lead_ingest_and_queue_are_idempotent(tmp_path):
    manager = DPODatabaseManager(str(tmp_path / "dpo_queue.db"))

    lead_key = manager.ingest_lead(
        "standard",
        raw_id="seed-42",
        source_system="ooma",
        entity_name="Acme Legal",
        email="hello@example.com",
        phone="5550102020",
        segment="estate_planning",
    )

    record_id = manager.get_record_id_for_lead_key("standard", lead_key)
    assert record_id is not None

    manager.record_evidence(
        "standard",
        record_id,
        lead_key,
        "consent_gate",
        True,
        "operator:test",
        {"consent_status": 1, "dnc_flag": 0},
    )
    manager.queue_sync("standard", record_id, "google_contacts", lead_key)
    manager.queue_sync("standard", record_id, "google_contacts", lead_key)

    row_count = manager.get_pending_sync_rows("standard")
    assert len(row_count) == 1
    assert row_count[0]["target_system"] == "google_contacts"


def test_queue_requires_compliance_gate(tmp_path):
    manager = DPODatabaseManager(str(tmp_path / "dpo_gate.db"))

    lead_key = manager.ingest_lead(
        "standard",
        raw_id="seed-gate",
        source_system="ooma",
        entity_name="Gate Test Legal",
        email="gate@example.com",
        phone="5550106789",
        segment="estate_planning",
    )

    record_id = manager.get_record_id_for_lead_key("standard", lead_key)
    with pytest.raises(ValueError, match="compliance_gate"):
        manager.queue_sync("standard", record_id, "google_contacts", lead_key)

    manager.record_evidence(
        "standard",
        record_id,
        lead_key,
        "consent_gate",
        True,
        "operator:alice",
        {"consent_status": 1, "dnc_flag": 0},
    )
    manager.queue_sync("standard", record_id, "google_contacts", lead_key)

    pending = manager.get_pending_sync_rows("standard")
    assert pending[0]["target_system"] == "google_contacts"

    assert manager.get_lead_row("standard", lead_key)["state"] == "queued"


def test_rejection_and_evidence_are_recorded(tmp_path):
    manager = DPODatabaseManager(str(tmp_path / "dpo_evidence.db"))

    lead_key = manager.ingest_lead(
        "bd",
        raw_id="bd-17",
        source_system="bd_platform",
        entity_name="Northwind Advisory",
        email="ops@example.com",
        phone="5550103000",
        bd_metadata={"firm_type": "family_law"},
    )

    record_id = manager.get_record_id_for_lead_key("bd", lead_key)
    manager.record_rejection(
        "bd",
        record_id,
        lead_key,
        "missing_consent",
        "No valid consent captured",
        "bd_platform",
    )
    manager.record_evidence(
        "bd",
        record_id,
        lead_key,
        "consent_gate",
        True,
        "operator:alice",
        {"consent_status": 1, "dnc_flag": 0},
    )

    rejection = manager.get_rejections("bd", record_id)
    assert rejection[0]["rejection_code"] == "missing_consent"
    evidence = manager.get_evidence("bd", record_id)
    assert evidence[0]["gate_name"] == "consent_gate"
