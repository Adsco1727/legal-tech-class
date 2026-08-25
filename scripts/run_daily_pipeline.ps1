$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Set-Location $RepoRoot

Write-Host "[1/3] Run ingestion..."
python .\pipelines\run_ingestion.py `
  --scraper scrapers\scrape_source_a.py `
  --scraper scrapers\scrape_source_b.py

Write-Host "[2/3] Run readiness gate..."
python .\gate_check.py

Write-Host "[3/3] Done."
