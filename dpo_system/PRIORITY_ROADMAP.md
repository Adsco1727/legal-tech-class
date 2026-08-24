# DPO Priority Roadmap (Execution Order)

## Current Snapshot

- Gate A: PASS
- Gate B: FAIL (expected until Ooma confirms response fields)
- Core remaining internal blocker: live ledger workbook header mismatch on queue sheets.

## Priority Buckets

### P0 - Must Do Now (Internal Execution Reliability)

1. Resolve live ledger header mismatch in `operator_ledger.xlsx`.
2. Keep `gate-a-readiness` passing.
3. Confirm DB-to-outbound batch builder and preflight commands run end-to-end on real source exports.
4. Produce at least one real 500-row batch artifact with preflight PASS.

### P1 - Must Do Before Ooma Call

1. Lock one operator-facing source template for DB exports (Google + BD workflow source columns).
2. Keep Ooma packet updated:
   - email draft
   - sample CSV
   - capability checklist
3. Ensure Gate B response template is ready for direct fill during/after vendor call.

### P2 - Must Do Before Pilot

1. Run 10-row internal dry-run against exact pilot CSV shape.
2. Define disposition reconciliation mapping from vendor export back to `record_id`.
3. Record pilot acceptance criteria and rollback criteria.

### P3 - Must Do Before Production

1. Obtain Ooma-confirmed response fields and switch Gate B to PASS.
2. Run 25-50 row acceptance.
3. Scale in 500-row batches with stop-on-fail policy.
4. Align budget + appointment + execution window.

## Sequencing Rule

1. Repos and core orchestration logic first.
2. Notebook operator surfaces second.
3. Content and campaign payloads third.
4. Vendor validation fourth.
5. Scale-up last.

## Immediate Next Actions

1. Execute `TODAY_RUNBOOK.md`.
2. Capture evidence files for each completed step under `dpo_system/evidence/EXECUTED_EVIDENCE/`.
3. Reassess status at end of day with Gate A, Gate B, and phase status outputs.
