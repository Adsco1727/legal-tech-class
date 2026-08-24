import os

import pytest

from dpo_system.src.audit_writer import (
    append_operator_notes,
    load_events_for_batch,
    load_recent_events,
    make_idempotency_key,
)
from dpo_system.src.operator_actions import approve_batch, reject_batch


def test_make_idempotency_key_is_deterministic_on_target_order():
    key_a = make_idempotency_key("approve_batch", ["b2", "b1"], "operator_a", "REVIEW_OK")
    key_b = make_idempotency_key("approve_batch", ["b1", "b2"], "operator_a", "REVIEW_OK")
    assert key_a == key_b


def test_approve_duplicate_is_idempotent_noop(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    os.environ["DPO_AUDIT_LOG_PATH"] = str(log_path)

    key = make_idempotency_key("approve_batch", ["b1", "b2"], "operator_a", "REVIEW_OK")
    first = approve_batch(
        batch_ids=["b1", "b2"],
        who="operator_a",
        why="Validated by policy",
        reason_code="REVIEW_OK",
        evidence_refs=["E-004", "E-005"],
        idempotency_key=key,
        dry_run=False,
    )
    second = approve_batch(
        batch_ids=["b1", "b2"],
        who="operator_a",
        why="Validated by policy",
        reason_code="REVIEW_OK",
        evidence_refs=["E-004", "E-005"],
        idempotency_key=key,
        dry_run=False,
    )

    assert first["status"] == "written"
    assert first["mutated"] is True
    assert second["status"] == "duplicate_noop"
    assert second["mutated"] is False

    events = load_recent_events(limit=10)
    assert len(events) == 1


def test_conflicting_duplicate_is_blocked(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    os.environ["DPO_AUDIT_LOG_PATH"] = str(log_path)

    key = make_idempotency_key("approve_batch", ["b1", "b2"], "operator_a", "REVIEW_OK")
    approve_batch(
        batch_ids=["b1", "b2"],
        who="operator_a",
        why="Validated by policy",
        reason_code="REVIEW_OK",
        evidence_refs=["E-004", "E-005"],
        idempotency_key=key,
        dry_run=False,
    )

    with pytest.raises(RuntimeError):
        reject_batch(
            batch_ids=["b1", "b2"],
            who="operator_a",
            why="Changed decision",
            reason_code="REJECT_RULE",
            evidence_refs=["E-004", "E-005"],
            idempotency_key=key,
            dry_run=False,
        )


def test_approve_batch_writes_audit_event_once(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    os.environ["DPO_AUDIT_LOG_PATH"] = str(log_path)

    key = make_idempotency_key("approve_batch", ["c1", "c2"], "operator_a", "REVIEW_OK")
    result = approve_batch(
        batch_ids=["c1", "c2"],
        who="operator_a",
        why="Policy validation passed",
        reason_code="REVIEW_OK",
        evidence_refs=["E-010", "E-011"],
        idempotency_key=key,
        dry_run=False,
    )

    assert result["status"] == "written"
    assert result["mutated"] is True
    events = load_recent_events(limit=10)
    assert len(events) == 1
    assert events[0]["what"] == "approve_batch"
    assert events[0]["targets"] == ["c1", "c2"]


def test_reject_batch_writes_audit_event_once(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    os.environ["DPO_AUDIT_LOG_PATH"] = str(log_path)

    key = make_idempotency_key("reject_batch", ["d1"], "operator_a", "REJECT_RULE")
    result = reject_batch(
        batch_ids=["d1"],
        who="operator_a",
        why="Failed policy gate",
        reason_code="REJECT_RULE",
        evidence_refs=["E-020"],
        idempotency_key=key,
        dry_run=False,
    )

    assert result["status"] == "written"
    assert result["mutated"] is True
    events = load_recent_events(limit=10)
    assert len(events) == 1
    assert events[0]["what"] == "reject_batch"
    assert events[0]["reason_code"] == "REJECT_RULE"


def test_append_operator_notes_records_note_event(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    os.environ["DPO_AUDIT_LOG_PATH"] = str(log_path)

    result = append_operator_notes(
        "run-123",
        "Manual review held pending corrected registry",
        "operator_a",
        ["d1"],
    )

    assert result["status"] == "written"
    events = load_events_for_batch("d1")
    assert len(events) >= 1
    assert events[-1]["what"] == "append_operator_note"
    assert events[-1]["why"] == "Manual review held pending corrected registry"
