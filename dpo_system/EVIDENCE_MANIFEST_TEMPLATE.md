# Evidence Manifest (One-Page Template)

Use one copy of this form per gate artifact. Keep all fields populated. Times are UTC.

## 1) Artifact Identity

- Artifact ID: ____________________
- Gate: [ ] Gate 0  [ ] Gate 1  [ ] Gate 2  [ ] Gate 3  [ ] Gate 4  [ ] Gate 5  [ ] Gate 6
- Control ID(s): ____________________
- Artifact title: ____________________
- Artifact type: [ ] Report  [ ] Log  [ ] Test Output  [ ] Config Snapshot  [ ] Approval Record  [ ] Other: ____________

## 2) Source and Provenance

- Repository: ____________________
- Branch: ____________________
- Commit hash: ____________________
- Run ID: ____________________
- Wave ID: ____________________
- Environment: [ ] Desktop  [ ] Staging  [ ] Runtime
- Produced by (person or job): ____________________
- Produced at (UTC): ____________________

## 3) Storage and Integrity

- Storage location (path/URI): ____________________
- File name: ____________________
- File format: ____________________
- File size: ____________________
- Checksum algorithm: [ ] SHA-256  [ ] SHA-512  [ ] Other: ____________
- Checksum value: ____________________
- Immutable storage flag: [ ] Yes  [ ] No
- Retention class: [ ] Audit-Critical  [ ] Standard  [ ] Temporary

## 4) Validation Result

- Validation command/tool: ____________________
- Validation scope: ____________________
- Result: [ ] PASS  [ ] FAIL
- Severity if FAIL: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
- Failed controls (if any): ____________________
- Exception approved: [ ] Yes  [ ] No
- Exception reference (if yes): ____________________

## 5) Boundary and Secrets Checks

- Boundary compliance checked: [ ] Yes  [ ] No
- Boundary result: [ ] PASS  [ ] FAIL
- Secrets scan executed: [ ] Yes  [ ] No
- Secrets result: [ ] PASS  [ ] FAIL
- Sensitive fields redacted: [ ] Yes  [ ] No  [ ] N/A

## 6) Idempotency and Audit Linkage

- Idempotency key(s) covered: ____________________
- Duplicate-write test included: [ ] Yes  [ ] No  [ ] N/A
- Audit event ID(s): ____________________
- Linked state transition ID(s): ____________________
- Traceability complete (artifact -> event -> state): [ ] Yes  [ ] No

## 7) Approvals (Maker-Checker)

### Maker
- Name: ____________________
- Role: ____________________
- Signature/Initials: ____________________
- Date (UTC): ____________________

### Checker
- Name: ____________________
- Role: ____________________
- Signature/Initials: ____________________
- Date (UTC): ____________________

## 8) Release Decision Contribution

- Contributes to gate decision: [ ] GO evidence  [ ] NO-GO evidence
- Blocking issue present: [ ] Yes  [ ] No
- Blocking issue summary (if yes): ____________________
- Required follow-up action: ____________________
- Follow-up owner: ____________________
- Follow-up due date (UTC): ____________________

## 9) Cross-References

- Related artifact IDs: ____________________
- Related risk register IDs: ____________________
- Related change request IDs: ____________________
- Related incident/problem IDs: ____________________

## 10) Notes

________________________________________________________________________________
________________________________________________________________________________
________________________________________________________________________________

---

## Quick Completeness Checklist

- [ ] Artifact ID assigned
- [ ] Commit hash and run ID filled
- [ ] Storage path and checksum filled
- [ ] Validation result recorded
- [ ] Boundary and secrets checks recorded
- [ ] Audit linkage recorded
- [ ] Maker and checker signed
- [ ] GO/NO-GO contribution marked
