# Production Rollout Memo

## Purpose

This memo is the execution master for the remaining repo and notebook rollout. It converts the repo governance rule into an operating sequence so each notebook is assembled, validated, approved, and enabled in the correct order before data is pushed into the database.

## Execution order

1. dpo-ledger-tools
   - Notebook: ledger_production_readiness.ipynb
   - Purpose: establish ledger control plane and canonical data state
   - Status: active baseline and reference implementation
   - Rule: complete before any downstream repo is allowed to load validated operational data

2. dpo-casework
   - Notebook: casework_production_readiness.ipynb
   - Purpose: validate case lifecycle, status transitions, and case dataset integrity
   - Rule: enabled only after ledger contracts are proven and stable

3. dpo-admin-tools
   - Notebook: admin_tools_production_readiness.ipynb
   - Purpose: support admin controls, operational oversight, and governance actions
   - Rule: feed only after casework ledger state is stable

4. dpo-integrations
   - Notebook: integrations_production_readiness.ipynb
   - Purpose: validate external connectors, API passes, and data intake contracts
   - Rule: must pass integration gate checks before any downstream orchestration relies on it

5. dpo-automation-suite
   - Notebook: automation_production_readiness.ipynb
   - Purpose: orchestration, queue handling, and scheduled operational workflows
   - Rule: only enable after ledger + casework + admin + integrations are validated

6. dpo-interview-suite
   - Notebook: interview_suite_production_readiness.ipynb
   - Purpose: intake and interview processing workflows
   - Rule: turned on when upstream data model, validation gates, and persistence are stable

7. docassemble-dpolawstack
   - Notebook: docassemble_production_readiness.ipynb
   - Purpose: document assembly and output generation based on validated data
   - Rule: last in the sequence so it consumes only proven, structured records

## Required operating rule

Each repo follows the same approval flow:

- assemble notebook in repo
- validate repo structure and artifacts
- run readiness checks
- pass gate validation
- capture evidence
- obtain operator sign-off
- enable notebook
- push validated data to the database
- continue population only after proof is confirmed

## What is going where

- Ledger repo contains the foundation data contract and canonical evidence pattern.
- Casework repo owns operational case progression and status integrity.
- Admin repo owns operational governance and oversight actions.
- Integrations repo owns external interfaces and inbound data contracts.
- Automation repo owns orchestration and process control.
- Interview repo owns intake and interview-generated content.
- Docassemble repo owns final assembly and generated output.

## Decision

Yes, we had the repo governance pattern and a general domain plan, but we did not yet have a single execution master for the notebook rollout. This memo is that missing execution layer. Going forward, each repo is turned on in sequence, not by notebook count or urgency.

## Immediate next action

The next active work is to create the remaining repo-specific readiness notebooks in this exact order and run them through the validation and evidence gate before enabling database feeds.
