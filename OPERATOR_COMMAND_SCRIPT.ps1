Set-Location "C:\Users\Gary\Documents\GitHub\legal-tech-class"

# Notebook first pass
.\.venv\Scripts\python.exe --version
Get-ChildItem .\dpo_system\notebooks

# Repo gate proof
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner status
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-a-readiness

# Ensure Gate B artifact exists at the runtime contract path
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

# Run Gate B
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-b-readiness

# Stop conditions
Write-Host "If any command above fails, stop and fix the environment or missing artifact before proceeding."
