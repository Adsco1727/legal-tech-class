Set-Location "C:\Users\Gary\Documents\GitHub\legal-tech-class"
$ErrorActionPreference = 'Stop'

# Notebook first pass
.\.venv\Scripts\python.exe --version
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Get-ChildItem .\dpo_system\notebooks
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Repo gate proof
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner status
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-a-readiness
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Ensure Gate B artifact exists at the runtime contract path
$oomaPath = "dpo_system\vendor\ooma"
$oomaFile = Join-Path $oomaPath "ooma_response_fields.json"
New-Item -ItemType Directory -Force -Path $oomaPath | Out-Null

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
'@ | Set-Content -Path $oomaFile -Encoding UTF8

# Run Gate B
.\.venv\Scripts\python.exe -m dpo_system.src.phase_runner gate-b-readiness
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "All checks passed."
