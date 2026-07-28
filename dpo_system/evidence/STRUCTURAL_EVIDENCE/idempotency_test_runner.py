from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


@dataclass
class TestCaseResult:
    name: str
    expected: str
    actual: str
    outcome: str
    notes: str


def make_idempotency_key(
    action: str,
    target_ids: List[str],
    actor: str,
    reason_code: str,
    policy_version: str = "v1",
) -> str:
    """Deterministic key from canonicalized action payload."""

    payload = {
        "action": action.strip(),
        "target_ids": sorted([t.strip() for t in target_ids]),
        "actor": actor.strip(),
        "reason_code": reason_code.strip(),
        "policy_version": policy_version.strip(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def payload_hash(payload: Dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def run() -> int:
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results: List[TestCaseResult] = []

    key_a = make_idempotency_key("approve_batch", ["b2", "b1"], "operator_a", "REVIEW_OK")
    key_b = make_idempotency_key("approve_batch", ["b1", "b2"], "operator_a", "REVIEW_OK")
    results.append(
        TestCaseResult(
            name="S1 Deterministic ordering",
            expected="SAME",
            actual="SAME" if key_a == key_b else "DIFFERENT",
            outcome="PASS" if key_a == key_b else "FAIL",
            notes="Target order normalization should produce identical key.",
        )
    )

    key_reason = make_idempotency_key("approve_batch", ["b1", "b2"], "operator_a", "MANUAL_OVERRIDE")
    results.append(
        TestCaseResult(
            name="S2 Reason code changes key",
            expected="DIFFERENT",
            actual="DIFFERENT" if key_a != key_reason else "SAME",
            outcome="PASS" if key_a != key_reason else "FAIL",
            notes="Reason code must be part of idempotency signature.",
        )
    )

    key_actor = make_idempotency_key("approve_batch", ["b1", "b2"], "operator_b", "REVIEW_OK")
    results.append(
        TestCaseResult(
            name="S3 Actor changes key",
            expected="DIFFERENT",
            actual="DIFFERENT" if key_a != key_actor else "SAME",
            outcome="PASS" if key_a != key_actor else "FAIL",
            notes="Actor should change key to avoid cross-actor collisions.",
        )
    )

    key_action = make_idempotency_key("reject_batch", ["b1", "b2"], "operator_a", "REVIEW_OK")
    results.append(
        TestCaseResult(
            name="S4 Action changes key",
            expected="DIFFERENT",
            actual="DIFFERENT" if key_a != key_action else "SAME",
            outcome="PASS" if key_a != key_action else "FAIL",
            notes="Action name must be part of signature.",
        )
    )

    ledger: Dict[str, str] = {}
    original_payload = {
        "action": "approve_batch",
        "target_ids": ["b1", "b2"],
        "actor": "operator_a",
        "reason_code": "REVIEW_OK",
        "approved": True,
    }
    key = make_idempotency_key("approve_batch", ["b1", "b2"], "operator_a", "REVIEW_OK")
    first_hash = payload_hash(original_payload)
    ledger[key] = first_hash

    duplicate_hash = payload_hash(original_payload)
    duplicate_outcome = "PASS" if ledger.get(key) == duplicate_hash else "FAIL"
    results.append(
        TestCaseResult(
            name="S5 Exact duplicate write",
            expected="NO-OP/PASS",
            actual="NO-OP/PASS" if duplicate_outcome == "PASS" else "CONFLICT/FAIL",
            outcome=duplicate_outcome,
            notes="Exact duplicate payload should be treated as idempotent no-op.",
        )
    )

    conflicting_payload = dict(original_payload)
    conflicting_payload["approved"] = False
    conflict_hash = payload_hash(conflicting_payload)
    conflict_outcome = "PASS" if ledger.get(key) != conflict_hash else "FAIL"
    results.append(
        TestCaseResult(
            name="S6 Conflicting duplicate write",
            expected="CONFLICT/FAIL",
            actual="CONFLICT/FAIL" if conflict_outcome == "PASS" else "NO-OP/PASS",
            outcome=conflict_outcome,
            notes="Same key with different payload must fail closed.",
        )
    )

    passed = sum(1 for r in results if r.outcome == "PASS")
    total = len(results)
    overall = "PASS" if passed == total else "FAIL"

    report_lines = [
        "IDEMPOTENCY TEST REPORT",
        f"Timestamp(UTC): {now_utc}",
        "Scope: Deterministic key generation and duplicate-write behavior simulation",
        "Execution mode: Simulation (no external writes)",
        "",
        f"Overall Result: {overall} ({passed}/{total} scenarios passed)",
        "",
        "Scenario Results:",
    ]

    for r in results:
        report_lines.extend(
            [
                f"- {r.name}",
                f"  Expected: {r.expected}",
                f"  Actual: {r.actual}",
                f"  Outcome: {r.outcome}",
                f"  Notes: {r.notes}",
                "",
            ]
        )

    print("\n".join(report_lines))

    out_json = Path(__file__).resolve().parent / "idempotency_test_results.json"
    out_json.write_text(
        json.dumps(
            {
                "timestamp_utc": now_utc,
                "overall": overall,
                "passed": passed,
                "total": total,
                "results": [r.__dict__ for r in results],
                "sample_key": key,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(run())
