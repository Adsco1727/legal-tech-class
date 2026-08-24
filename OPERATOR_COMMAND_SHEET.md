# Operator Command Sheet

## Notebook First Pass

```powershell
cd "C:\Users\Gary\Documents\GitHub\legal-tech-class"
.\.venv\Scripts\python.exe --version
Get-ChildItem .\dpo_system\notebooks
```

```python
import sys
print(sys.executable)
print('kernel ok')
```

---

## Repo Gate Proof

```powershell
cd "C:\Users\Gary\Documents\GitHub\legal-tech-class"
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner status
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-a-readiness
```

```powershell
New-Item -ItemType Directory -Force -Path "dpo_system\vendor\ooma" | Out-Null
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

```powershell
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-b-readiness
```

---

## SEO / Site Setup

```powershell
cd "C:\Users\Gary\Documents\GitHub\legal-tech-class"
```

Then verify:

```text
- site metadata
- canonical URLs
- Open Graph / Twitter metadata
- sitemap / robots
- internal linking
- analytics / verification hooks
```

---

## Stop Conditions

```text
- notebook kernel fails
- repo status fails
- Gate A fails
- Gate B file missing
- runtime path does not match repo contract
```
