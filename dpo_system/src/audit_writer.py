"""Audit writing helpers for the operator control tower workflow."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


_REQUIRED_EVENT_FIELDS = ("who", "when", "what", "why", "reason_code", "evidence_refs")


def _default_audit_log_path() -> Path:
    return Path(__file__).resolve().parents[1] / "evidence" / "operator_audit_events.jsonl"


def _audit_log_path() -> Path:
    env_path = os.getenv("DPO_AUDIT_LOG_PATH", "").strip()
    if env_path:
        return Path(env_path)
    return _default_audit_log_path()


def _canonical_payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def _load_all_events() -> list[dict]:
    path = _audit_log_path()
    if not path.exists():
        return []

    events: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def _validate_required_fields(event: dict) -> None:
    missing: list[str] = []
    for field in _REQUIRED_EVENT_FIELDS:
        value = event.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)
        if field == "evidence_refs" and (not isinstance(value, list) or len(value) == 0):
            missing.append(field)
    if missing:
        raise ValueError(f"Missing or empty required audit fields: {missing}")


def _build_dedup_index(events: list[dict]) -> dict[str, str]:
    index: dict[str, str] = {}
    for evt in events:
        key = evt.get("idempotency_key")
        payload_hash = evt.get("payload_hash")
        if isinstance(key, str) and isinstance(payload_hash, str):
            index[key] = payload_hash
    return index


def _current_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_decision_event(event: dict, idempotency_key: str) -> dict:
    """Write a single audited decision event."""
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise ValueError("idempotency_key is required")

    _validate_required_fields(event)

    # Hash only the semantic payload used for duplicate/conflict detection.
    semantic_payload = {
        "what": event.get("what"),
        "targets": event.get("targets", []),
        "who": event.get("who"),
        "why": event.get("why"),
        "reason_code": event.get("reason_code"),
        "evidence_refs": event.get("evidence_refs", []),
        "dry_run": bool(event.get("dry_run", False)),
    }
    payload_hash = _canonical_payload_hash(semantic_payload)

    events = _load_all_events()
    key_index = _build_dedup_index(events)
    prior_hash = key_index.get(idempotency_key)
    if prior_hash is not None:
        if prior_hash == payload_hash:
            return {
                "status": "duplicate_noop",
                "idempotency_key": idempotency_key,
                "payload_hash": payload_hash,
                "written": False,
            }
        raise RuntimeError("Conflicting duplicate write for same idempotency_key")

    path = _audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(event)
    record["idempotency_key"] = idempotency_key
    record["payload_hash"] = payload_hash
    record["event_time_utc"] = _current_utc()

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")

    return {
        "status": "written",
        "idempotency_key": idempotency_key,
        "payload_hash": payload_hash,
        "written": True,
    }


def load_recent_events(run_id: str | None = None, limit: int = 100) -> list[dict]:
    """Load recent audit events."""
    if limit <= 0:
        return []
    events = _load_all_events()
    if run_id:
        events = [evt for evt in events if evt.get("run_id") == run_id]
    return events[-limit:]


def load_events_for_batch(batch_id: str) -> list[dict]:
    """Load audit events for a specific batch."""
    events = _load_all_events()
    matches: list[dict] = []
    for evt in events:
        targets = evt.get("targets", [])
        if isinstance(targets, list) and batch_id in targets:
            matches.append(evt)
    return matches


def append_operator_notes(
    run_id: str,
    note: str,
    who: str,
    linked_ids: list[str] | None = None,
) -> dict:
    """Append operator notes to the audit trail."""
    if not run_id.strip():
        raise ValueError("run_id is required")
    if not note.strip():
        raise ValueError("note is required")
    if not who.strip():
        raise ValueError("who is required")

    event = {
        "run_id": run_id,
        "who": who,
        "when": _current_utc(),
        "what": "append_operator_note",
        "why": note,
        "reason_code": "OPERATOR_NOTE",
        "evidence_refs": ["operator_note"],
        "targets": linked_ids or [],
        "dry_run": False,
    }
    key = make_idempotency_key("append_operator_note", linked_ids or [run_id], who, "OPERATOR_NOTE")
    return write_decision_event(event, key)


def make_idempotency_key(
    action: str, target_ids: list[str], actor: str, reason_code: str
) -> str:
    """Create a deterministic idempotency key."""
    payload = {
        "action": action.strip(),
        "target_ids": sorted(t.strip() for t in target_ids),
        "actor": actor.strip(),
        "reason_code": reason_code.strip(),
        "policy_version": "v1",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()
