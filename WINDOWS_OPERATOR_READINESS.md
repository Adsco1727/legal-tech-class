# Windows Operator Readiness & PowerShell Caution Guide

## Understanding Missing-Artifact Failures, Path Drift, and Shell-Layer Noise

## Purpose

This guide exists because Windows operators frequently encounter failures that look like PowerShell issues but are actually caused by missing artifacts, path drift, or repo contract violations.

This document teaches operators how to distinguish:

- shell symptoms
- from structural causes

so they can diagnose failures deterministically instead of chasing noise.

---

## 1. The Core Principle

> When a system behaves irrationally, the operator must check the contract, not the shell.

PowerShell is rarely the root cause. It is simply the layer that exposes deeper structural problems.

---

## 2. The Three Structural Failure Modes

### A. Missing Artifact

The repo expects a file or folder that does not exist locally.

Symptoms:

- "Command not found"
- silent VS Code or Notepad opens
- gate failures that make no sense
- JSON instructions that cannot be applied

Cause:

- Git does not track empty folders
- the repo assumes the folder exists
- the operator's machine does not have it

Fix:

- create the folder manually
- create the required JSON file
- re-run the gate

### B. Path Drift

Documentation and runtime contract disagree.

Symptoms:

- instructions point to one path
- code reads from another
- operators create files in the wrong place
- gates fail despite “correct” JSON

Cause:

- the repo evolved
- docs did not
- the runtime contract changed
- operators follow outdated paths

Fix:

- trust the runtime contract
- search the code for default path helpers
- create artifacts where the code expects them

### C. Shell-Layer Amplification

PowerShell errors look like logic errors.

Symptoms:

- JSON pasted into the terminal throws syntax errors
- file paths typed directly are not recognized
- commands appear random or hostile
- the operator feels jerked around

Cause:

- the shell tries to execute paths
- the shell cannot open files by typing their name
- shell errors mask the real missing artifact

Fix:

- use Get-ChildItem to verify existence
- use notepad or code to open files directly
- never paste JSON into the terminal unless it is intentionally being used as a command payload

---

## 3. The Operator Mindset Checklist

Before debugging any gate or pipeline, apply these rules:

### Rule 1 — Trust the runtime, not the docs

Docs drift. Runtime does not lie.

### Rule 2 — Gates never fail randomly

If a gate fails, a required artifact is missing or invalid.

### Rule 3 — Path drift is the primary cause of irrational behavior

If the system feels “crazy,” check the paths.

### Rule 4 — Shell errors are symptoms, not causes

PowerShell is just the messenger.

### Rule 5 — Always verify existence before debugging logic

If the file does not exist, nothing else matters.

---

## 4. The Minimal Diagnostic Commands

### Check if a folder exists

```powershell
Get-ChildItem <path>
```

### Create a missing folder

```powershell
New-Item -ItemType Directory -Force -Path "<path>"
```

### Open a file in Notepad

```powershell
notepad <path>
```

### Open a file in VS Code

```powershell
code <path>
```

### Verify the actual configured runtime contract

Search for the path definition in code rather than trusting a runbook.

For example, in this repo the Gate B contract is resolved in the phase runner:

```python
_default_gate_b_response_path() -> dpo_system/vendor/ooma/ooma_response_fields.json
```

This is the canonical runtime reference.

---

## 5. Example: Vendor Response File (Gate B)

The correct runtime path for the vendor response data is:

```text
dpo_system/vendor/ooma/ooma_response_fields.json
```

This is not the same as a stale config path that may appear in older documentation or operator notes.

### Create the folder

```powershell
New-Item -ItemType Directory -Force -Path "dpo_system\vendor\ooma"
```

### Create the JSON file

```powershell
notepad dpo_system\vendor\ooma\ooma_response_fields.json
```

Paste the vendor-confirmed JSON, save it, and then re-run Gate B.

Example JSON structure:

```json
{
  "csv_import_supported": true,
  "required_optional_fields_confirmed": true,
  "phone_format_rule_confirmed": true,
  "identifier_roundtrip_confirmed": true,
  "custom_fields_behavior_confirmed": true,
  "upload_limits_confirmed": true,
  "dedupe_behavior_confirmed": true,
  "append_replace_behavior_confirmed": true,
  "disposition_export_confirmed": true,
  "pilot_10_row_approved": true,
  "pilot_25_to_50_row_approved": true,
  "decision": "accepted_as_is",
  "notes": "Vendor confirmed import contract and pilot acceptance."
}
```

Then run the gate:

```powershell
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-b-readiness
```

---

## 6. Why This Document Exists

Operators on Windows often experience:

- silent failures
- misleading errors
- contradictory instructions
- “irrational” pipeline behavior

This guide prevents that by teaching:

- how to detect missing artifacts
- how to identify path drift
- how to separate shell noise from structural truth
- how to restore repo contract integrity

This is the operator's shield against chaos.

---

## 7. Operator Survival Rule

> If the system feels irrational, do not start by blaming the shell. Start by verifying the artifacts, the path, and the runtime contract.

That is the fastest path to reliable diagnosis.

---

## 8. Recommended Operational Habit

For any repo, before running a gate or batch process, check three things:

1. the required folder exists
2. the required file exists
3. the runtime path matches the repo code contract

If any of those are false, do not continue to logic-debugging.

Fix the contract first.

---

## 9. Conclusion

The correct response to a confusing Windows workflow is not panic and shell blame. It is:

- verify existence
- verify the path
- verify the contract
- validate the artifact
- then run the gate

This mindset keeps operators grounded, deterministic, and proactive.
