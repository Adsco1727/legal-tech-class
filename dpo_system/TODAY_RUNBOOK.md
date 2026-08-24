# Today Runbook

Purpose: make forward progress today without waiting on Ooma appointment timing.

## Pipeline SOP Update

The system operates three distinct export universes. They must not be merged, conflated, or treated as interchangeable.

1. Standard pipeline (Google/Microsoft standard template)
   - Used for Ooma autodialer, Google Contacts, Microsoft Contacts.
   - Schema: standard contact fields.
   - Output: 500-contact CSV batches.
   - Commands: build-db-outbound, preflight-csf.
   - Destination: dialer systems and standard CRMs.

2. BD pipeline (Brilliant Directories 30-cell template)
   - BD = Brilliant Directories.
   - BD uploads are not autodialer CSVs.
   - Schema: 30 fixed BD fields.
   - Populated by scrapers and enrichment routines.
   - Destination: www.directprivateoffers.net.
   - BD uploads must always match the exact BD schema and ordering.

3. Internal / compliance pipeline (DPO evidence + outbound engine)
   - Used for evidence manifests, outbound engine specs, compliance panels.
   - Schema: strict outbound contract with registry-tracked IDs.
   - Commands: build-db-outbound, preflight-csf, checkpoint bundle generation.
   - Destination: internal DPO compliance systems.

Rules:
- These pipelines are separate export universes.
- They have different schemas, validators, and destinations.
- When the task says "BD upload," assume the 30-cell BD template.
- When the task says "Ooma autodialer," assume 500-contact CSV batches.
- When the task says "compliance outbound," assume strict schema plus registry.

## Step 1 - Baseline Checkpoint

Run:

```powershell
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner gate-a-readiness
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner gate-b-readiness
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner status
```

Expected:

1. Gate A PASS.
2. Gate B FAIL unless Ooma fields are confirmed.
3. Capture current header mismatch list from `status` output.

## Step 2 - Build Real Outbound Batches from DB Exports

Run:

```powershell
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner build-db-outbound <path-to-google-export.csv> <path-to-bd-workflow-export.csv> --output-dir dpo_system/config/outbound_batches --batch-size 500
```

Expected:

1. Manifest file generated.
2. Batch files generated.
3. Row counts in manifest match source expectations.

## Step 3 - Preflight First Batch

Run:

```powershell
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner preflight-csf dpo_system/config/outbound_batches/csf_batch_001_of_00N.csv --expected-rows 500
```

Expected:

1. Status PASS for clean batch.
2. Report path produced under preflight evidence folder.

## Step 4 - Capture Evidence

Save command outputs and report paths in a short end-of-day note.

Minimum evidence list:

1. Gate A report path.
2. Gate B report path.
3. Batch manifest path.
4. Preflight report path.

## Step 5 - Ooma Packet Ready State

Confirm these files are ready to send:

1. `dpo_system/vendor/ooma/ooma_vendor_email_draft.md`
2. `dpo_system/vendor/ooma/ooma_sample_outbound_pilot.csv`
3. `dpo_system/vendor/ooma/ooma_capability_checklist.md`
4. `dpo_system/vendor/ooma/ooma_response_fields_template.json`

Completion criteria:

1. Internal outbound production path demonstrated.
2. Vendor packet ready.
3. Gate A still PASS.
4. Gate B waiting only on vendor response.
