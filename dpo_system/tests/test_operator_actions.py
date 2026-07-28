import os

import pytest

from dpo_system.src.audit_writer import load_recent_events, make_idempotency_key
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
