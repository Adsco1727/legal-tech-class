# Ooma Pack Runbook

This runbook activates the generated packs without changing the telephony decision (Ooma-only).

## 1. Export a deterministic 500-row Ooma batch from DB CSV

```powershell
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner export-ooma-batch dpo_system/config/exports/db_live_snapshot.csv --output dpo_system/config/ooma/ooma_batch_001.csv --batch-size 500 --watermark dpo_system/state/ooma_export_watermark.json
```

Expected:
- Ooma CSV with exact column order.
- Deterministic ordering by updated_at desc then lead_id asc.
- Watermark updated for incremental reruns.

## 2. Validate Ooma batch with hardened DTO rules

```powershell
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner validate-ooma-csv dpo_system/config/ooma/ooma_batch_001.csv --report dpo_system/evidence/EXECUTED_EVIDENCE/ooma/ooma_intake_report.json --rejections dpo_system/evidence/EXECUTED_EVIDENCE/ooma/ooma_rejections.csv
```

Expected:
- Accepted and rejected records are written.
- Batch summary is written.
- Exit code 0 when rejected_count is 0.

## 3. Run Reg D scraper pack

```powershell
c:/Users/Gary/Documents/GitHub/legal-tech-class/.venv/Scripts/python.exe -m dpo_system.src.phase_runner scrape-regd --output-dir dpo_system/evidence/EXECUTED_EVIDENCE/regd --user-agent "DPORegDScraper/1.0 (operations@directprivateoffers.net)" --max-entries 200 --page-size 100
```

Expected outputs:
- regd_filings.csv
- regd_raw_entries.jsonl
- regd_error_ledger.jsonl
- regd_run_manifest.json

## 4. Notebook QA pass

Open `dpo_system/notebooks/ooma-csv-qa-console.ipynb` and run all cells against the latest Ooma batch.

Expected:
- Summary counts are visible.
- Rejection reason distribution is visible.
- Lane distribution is visible.
- Notebook JSON report is emitted under evidence path.
