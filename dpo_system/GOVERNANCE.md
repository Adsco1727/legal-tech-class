# GOVERNANCE.md — DTO Doctrine & Control Plane (v1.0)

## 1. Purpose

This document defines the governance doctrine for the DPO ecosystem.
It ensures that every lane, notebook, transition, and operator action follows a strict, deterministic, auditable, and reversible operating model.

The queue is not workflow plumbing.
The queue is the governance control plane.

All lanes must comply with:

- Global State Machine
- Metadata Contract
- Governance Gates
- Activation Rules
- Reversibility Requirements
- Audit Spine Logging

No lane may activate without passing all gates.

The operating principle is simple:

> A lane is not considered ready because it is useful. A lane is ready because it is governed, auditable, and operationally proven.

---

## 2. Lane Status Model (ACTIVE vs STAGED)

### ACTIVE Lane
A lane is ACTIVE only when:

- throughput is stable
- evidence is consistent
- operator load is sufficient
- audit spine is complete
- metadata contract is fully implemented

Current ACTIVE lane:
- Ooma Validation Lane

### STAGED Lane
A lane is STAGED when:

- architecture is mapped
- schema is defined
- state machine is documented
- governance rules exist
- evidence is not yet sufficient for activation

Current STAGED lanes:
- BD Ingestion
- Outbound Campaigns
- SEO Intelligence
- Geo-Governance
- Law Ingestion
- Clause Intelligence
- Docassemble Governance

No STAGED lane may activate without passing the Governance Gates.

---

## 3. Governance Gates (Mandatory)

The canonical DTO transition path is:

1. `raw_input`
2. `queue_intake`
3. `hitl_review`
4. `publish_or_reject`
5. `archive_or_outbound`
6. `audit_logged`

### Gate 1 — Evidence Gate
A lane activates only when the previous lane produces:

- stable outputs
- consistent evidence blobs
- predictable KPIs
- no schema drift

If evidence is incomplete, the lane remains STAGED.

### Gate 2 — Operator Load Gate
A lane activates only when:

- operator bandwidth exists
- human-in-the-loop review burden is manageable
- queue latency is acceptable
- no overload risk exists

If operator load is insufficient, the lane remains STAGED.

### Gate 3 — Audit Spine Gate
A lane activates only when:

- all transitions write to the audit spine
- metadata contract is enforced
- payload hash enforcement is implemented
- reversibility is guaranteed

If audit integrity is incomplete, the lane remains STAGED.

### Gate 4 — Channel Separation Gate
Outbound channels must remain isolated:

- LinkedIn
- Twitter/X
- Telegram
- Instagram
- Tumblr

No cross-posting without explicit mapping.
If channel separation is violated, activation is blocked.

### Gate 5 — No Platform Drift Gate
A lane activates only when:

- notebooks remain scoped
- no mega-notebook emerges
- no accidental platform expansion occurs
- DTO boundaries remain intact

If drift is detected, activation is blocked.

---

## 4. Activation Rules (Need / Value / Risk)

A STAGED lane becomes ACTIVE only if it passes all three criteria.

### Need
Does the lane materially support governance, compliance, or throughput?

### Value
Does the lane materially improve acceptance, conversion, or signal quality?

### Risk
Does activating the lane now introduce compliance, quality, or execution risk?

If any criterion fails, the lane remains STAGED.

---

## 5. Global Activation Sequence

Lanes must activate in the following order:

1. Ooma Validation (ACTIVE)
2. BD Ingestion (NEXT)
3. Outbound Campaigns (NEXT)
4. SEO Intelligence (STAGED)
5. Geo-Governance (STAGED)
6. Law Ingestion (STAGED)
7. Clause Intelligence (STAGED)
8. Docassemble Governance (STAGED)

This sequence prevents premature activation and ensures DTO stability.

---

## 6. Reversibility Requirements

Every lane must support deterministic rollback:

- previous stable commit
- previous stable payload
- previous stable state
- previous metadata contract

Rollback is mandatory for:

- rejected transitions
- operator corrections
- schema drift
- governance violations

Rollback is enforced through `rollback_hash` in the Metadata Contract.

---

## 7. Audit Spine Requirements

Every transition must write:

- `transition_id`
- `lane_id`
- `batch_id`
- `item_id`
- `origin_state`
- `target_state`
- `timestamp`
- `operator_id`
- `payload_hash`
- `evidence_blob`
- `rollback_hash`

Audit entries are immutable and cannot be altered or deleted.

---

## 8. Metadata Contract

The Metadata Contract is the strict API for all transitions.

A transition without a valid metadata payload is hard rejected.

For schema, required fields, and transition expectations, see:
- `QUEUE.md` Section 2 (Common Vocabulary and Required Metadata)
- `QUEUE.md` Section 4 (Global State Machine transition rules)

All transitions should use the same transition terms as `QUEUE.md`:

- source state
- destination state
- operator or system actor
- timestamp in UTC
- payload hash
- audit event write

---

## 9. Lane Promotion Rules

A lane may be promoted from STAGED to ACTIVE only when:

1. All Governance Gates pass
2. Need / Value / Risk criteria pass
3. Audit spine is complete
4. Metadata Contract is enforced
5. Operator load is sufficient
6. Reversibility is guaranteed
7. No platform drift is detected

Promotion must be logged with a full metadata payload.

---

## 10. Governance Summary

- The queue is the control plane
- Metadata Contract is mandatory
- Audit Spine is immutable
- human-in-the-loop review is required
- ACTIVE vs STAGED is explicit
- Activation is gated
- Sequence is enforced
- Reversibility is guaranteed
- Drift is prohibited

This is the DTO doctrine.

# End of GOVERNANCE.md
