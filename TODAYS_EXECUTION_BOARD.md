# Today's Execution Board

## Objective

Get the notebook layer running cleanly first, then validate repo gates, then move into SEO/site work only after the repo is functionally stable.

---

## Phase 1 — Notebook First Pass

### Step 1: Confirm environment

```powershell
cd "C:\Users\Gary\Documents\GitHub\legal-tech-class"
.\.venv\Scripts\python.exe --version
```

Expected:

- Python is available in the repo venv
- version is compatible with the repo requirements

### Step 2: Confirm notebook directories

```powershell
Get-ChildItem .\dpo_system\notebooks
```

Expected:

- notebooks directory exists
- files are present

### Step 3: Open the first notebook in the environment

Open the notebook in VS Code and confirm the selected kernel is the repo venv interpreter.

If kernel selection is required, select the environment from:

```text
.venv\Scripts\python.exe
```

### Step 4: Run a minimal notebook smoke test

Execute the first notebook cell or run a simple import check in the notebook kernel:

```python
import sys
print(sys.executable)
print('kernel ok')
```

Expected:

- interpreter resolves to the repo venv
- notebook runs without import failure

### Step 5: Repeat notebook validation

Run the same notebook smoke test on each notebook in the stack until each is working in the same environment.

---

## Phase 2 — Repo Gate Proof

### Step 6: Run repo status

```powershell
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner status
```

### Step 7: Run Gate A

```powershell
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-a-readiness
```

### Step 8: Verify the actual Gate B artifact path

Check the runtime contract in code and confirm the file location is:

```text
dpo_system/vendor/ooma/ooma_response_fields.json
```

If it does not exist, create the folder and file before proceeding.

### Step 9: Create the missing Gate B vendor response file if needed

```powershell
New-Item -ItemType Directory -Force -Path "dpo_system\vendor\ooma" | Out-Null
```

Then write the JSON response payload:

```powershell
@'
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
'@ | Set-Content -Path "dpo_system\vendor\ooma\ooma_response_fields.json" -Encoding UTF8
```

### Step 10: Run Gate B

```powershell
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-b-readiness
```

Expected:

- Gate B passes once the artifact exists and the required values are valid

---

## Phase 3 — SEO + Site Setup

### Step 11: After notebook and gate proof, review SEO configuration

Check:

- site metadata
- canonical URLs
- page titles and descriptions
- Open Graph / Twitter metadata
- sitemap / robots files
- internal linking structure
- analytics hooks

### Step 12: Make only the necessary site changes

Do not broaden the task while the notebook or gate layer is still unstable.

### Step 13: Run final site quality check

Confirm:

- metadata is consistent
- links resolve
- sitemap is valid
- content hierarchy is coherent
- repo still passes the minimal operational checks

---

## Execution Order Summary

1. Notebook environment and kernel validation
2. Notebook smoke tests
3. Repo status
4. Gate A
5. Verify Gate B path and files
6. Create missing artifact if needed
7. Run Gate B
8. Only then move to SEO/site setup

---

## Stop Conditions

Stop immediately and fix the cause if any of the following occur:

- notebook kernel cannot resolve
- repo status fails
- Gate A fails
- Gate B artifact is missing
- path contracts do not match the runtime code

---

## Success Gate

The workday is successful only when:

- notebooks are operational
- repo gates are proven green
- the site/SEO layer is configured without breaking the functional stack
