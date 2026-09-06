import json
import sqlite3

import pytest

from dpo_system.src.sqlite_manager import DPODatabaseManager


def _auth(tag: str) -> dict:
    return {
        "ledger_evidence_ref": f"ledger://{tag}",
        "authorized_by": "operator:test",
        "authorization_reason": tag,
        "hitl_approved": True,
        "promotion_authorized": True,
    }


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
        authorization=_auth("consent_gate"),
    )
    manager.queue_sync("standard", record_id, "google_contacts", lead_key, authorization=_auth("queue_sync"))
    manager.queue_sync("standard", record_id, "google_contacts", lead_key, authorization=_auth("queue_sync"))

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
        manager.queue_sync("standard", record_id, "google_contacts", lead_key, authorization=_auth("queue_sync"))

    manager.record_evidence(
        "standard",
        record_id,
        lead_key,
        "consent_gate",
        True,
        "operator:alice",
        {"consent_status": 1, "dnc_flag": 0},
        authorization=_auth("consent_gate"),
    )
    manager.queue_sync("standard", record_id, "google_contacts", lead_key, authorization=_auth("queue_sync"))

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
        authorization=_auth("record_rejection"),
    )
    manager.record_evidence(
        "bd",
        record_id,
        lead_key,
        "consent_gate",
        True,
        "operator:alice",
        {"consent_status": 1, "dnc_flag": 0},
        authorization=_auth("consent_gate"),
    )

    rejection = manager.get_rejections("bd", record_id)
    assert rejection[0]["rejection_code"] == "missing_consent"
    evidence = manager.get_evidence("bd", record_id)
    assert evidence[0]["gate_name"] == "consent_gate"
    payload = json.loads(evidence[0]["evidence_payload"])
    assert payload["authorization"]["authorized_by"] == "operator:test"
    assert payload["authorization"]["hitl_approved"] is True
    assert payload["authorization"]["promotion_authorized"] is True


def test_consequential_writes_require_authorization(tmp_path):
    manager = DPODatabaseManager(str(tmp_path / "dpo_auth.db"))

    lead_key = manager.ingest_lead(
        "standard",
        raw_id="seed-auth",
        source_system="ooma",
        entity_name="Auth Test Legal",
        email="auth@example.com",
        phone="5550109999",
        segment="estate_planning",
    )
    record_id = manager.get_record_id_for_lead_key("standard", lead_key)
    assert record_id is not None

    with pytest.raises(ValueError, match="authorization context"):
        manager.record_evidence(
            "standard",
            record_id,
            lead_key,
            "consent_gate",
            True,
            "operator:test",
            {"consent_status": 1, "dnc_flag": 0},
        )
    with pytest.raises(ValueError, match="authorization context"):
        manager.record_evidence(
            "standard",
            record_id,
            lead_key,
            "consent_gate",
            False,
            "operator:test",
            {"consent_status": 0, "dnc_flag": 1},
        )

    manager.record_evidence(
        "standard",
        record_id,
        lead_key,
        "consent_gate",
        True,
        "operator:test",
        {"consent_status": 1, "dnc_flag": 0},
        authorization=_auth("consent_gate"),
    )
    with pytest.raises(ValueError, match="authorization context"):
        manager.queue_sync("standard", record_id, "google_contacts", lead_key)
    manager.queue_sync("standard", record_id, "google_contacts", lead_key, authorization=_auth("queue_sync"))

    with pytest.raises(ValueError, match="authorization context"):
        manager.mark_sync_dispatched("standard", record_id, "google_contacts", lead_key)
    manager.mark_sync_dispatched("standard", record_id, "google_contacts", lead_key, authorization=_auth("dispatch"))

    with pytest.raises(ValueError, match="authorization context"):
        manager.mark_sync_synced("standard", record_id, "google_contacts", lead_key)
    manager.mark_sync_synced("standard", record_id, "google_contacts", lead_key, authorization=_auth("synced"))

    with pytest.raises(ValueError, match="requires an existing queued sync row"):
        manager.mark_sync_dispatched("standard", record_id, "missing_target", lead_key, authorization=_auth("dispatch_missing"))

    with pytest.raises(ValueError, match="requires an existing sync row"):
        manager.mark_sync_synced("standard", record_id, "missing_target", lead_key, authorization=_auth("synced_missing"))


def test_mark_sync_methods_normalize_target_system_whitespace(tmp_path):
    manager = DPODatabaseManager(str(tmp_path / "dpo_target_normalization.db"))

    lead_key = manager.ingest_lead(
        "standard",
        raw_id="seed-whitespace",
        source_system="ooma",
        entity_name="Whitespace Test Legal",
        email="whitespace@example.com",
        phone="5550101111",
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
        authorization=_auth("consent_gate"),
    )
    manager.queue_sync("standard", record_id, "google_contacts", lead_key, authorization=_auth("queue_sync"))

    manager.mark_sync_dispatched("standard", record_id, "  google_contacts  ", lead_key, authorization=_auth("dispatch"))
    manager.mark_sync_synced("standard", record_id, "\tgoogle_contacts\n", lead_key, authorization=_auth("synced"))

    with sqlite3.connect(tmp_path / "dpo_target_normalization.db") as conn:
        row = conn.execute(
            "SELECT sync_status FROM crm_sync_queue WHERE lane_type = ? AND record_id = ? AND target_system = ?",
            ("standard", record_id, "google_contacts"),
        ).fetchone()

    assert row is not None
    assert row[0] == "synced"
