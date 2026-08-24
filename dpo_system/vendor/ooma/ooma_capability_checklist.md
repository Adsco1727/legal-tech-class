# Ooma Capability Checklist for DPO Outbound Pilot

Purpose: confirm the exact Ooma import and export contract before a larger production run.

## 1. CSV Import Acceptance

- [ ] Ooma can ingest a flat CSV outbound list by upload.
- [ ] The attached sample CSV can be accepted as-is.
- [ ] If not, Ooma has identified the exact required column names.
- [ ] Ooma has identified the exact unsupported columns.
- [ ] Ooma has identified any required column order.
- [ ] Ooma has identified required file encoding and delimiter rules.

## 2. Required vs Optional Fields

- [ ] `record_id` can be supplied by the customer.
- [ ] `record_id` is preserved during import.
- [ ] `record_id` is returned in disposition export or reporting.
- [ ] `phone_number` is required.
- [ ] Phone values must be strict E.164.
- [ ] `full_name` is accepted.
- [ ] `list_name` or campaign field is accepted.
- [ ] `outreach_purpose` is accepted.
- [ ] `list_source` is accepted.
- [ ] `email` is accepted.
- [ ] `address` is accepted.
- [ ] `notes` is accepted.
- [ ] `source_system` is accepted.

## 3. Agent Screen and Workflow Behavior

- [ ] Custom fields can be displayed to agents during live calls.
- [ ] `notes` can be displayed to agents.
- [ ] `list_name` affects routing or campaign behavior.
- [ ] Ooma supports campaign-level grouping at import.
- [ ] One CSV row maps to one call target record.

## 4. Upload and Batch Limits

- [ ] Ooma has provided maximum row count per upload.
- [ ] Ooma has provided file size limits.
- [ ] Ooma has provided rate or frequency limits for repeated uploads.
- [ ] Ooma has explained duplicate handling rules.
- [ ] Ooma has explained append vs replace behavior for list uploads.

## 5. Disposition Export and Reconciliation

- [ ] Ooma can export dispositions after calling.
- [ ] Export includes a stable identifier that matches imported records.
- [ ] Export includes call outcomes or disposition codes.
- [ ] Export includes timestamps.
- [ ] Export includes campaign or list context.
- [ ] Export is available by CSV, API, or both.

## 6. Pilot Approval

- [ ] Ooma approves a 10-row pilot upload using the attached sample file.
- [ ] Ooma approves a 25- to 50-row acceptance run after the pilot.
- [ ] Ooma has identified any changes required before a 3,000-row production run.

## 7. Decision

- [ ] Accepted for pilot as-is.
- [ ] Accepted with changes.
- [ ] Not accepted.

Notes:

