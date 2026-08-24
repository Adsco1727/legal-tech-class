# Operations Index

## Repository
- Name: legal-tech-class
- Owner: DPO
- Purpose: repo operations, governance, notebook readiness, and operational tooling

## Required Environment
- Python version: 3.9.11 where required by Solidity/DPO-connected tooling
- Virtual environment: .venv
- Kernel: repo venv interpreter

## Required Runtime Paths
- dpo_system/vendor/ooma/
- dpo_system/config/
- dpo_system/src/
- dpo_system/notebooks/

## Gate Status
- Gate A: validate after environment and repo readiness
- Gate B: requires vendor response payload at dpo_system/vendor/ooma/ooma_response_fields.json

## Standard Docs
- README.md
- NOTEBOOK_READINESS_SOP.md
- WINDOWS_OPERATOR_READINESS.md
- OPERATOR_COMMAND_SHEET.md
- NEXT_3_WORK_BLOCKS.md
- ORG_SOP_TEMPLATE.md

## Operational Notes
- Trust the runtime contract over stale documentation.
- Verify path existence before debugging logic.
- Stop on missing artifacts or gate failure.
