# DPO Org SOP Template

## Purpose

This template defines the minimum standard operating procedure for every repository in the DPO org.

## Required Repository Files

Each repository should include the following standard markdown documents:

- `README.md`
- `OPERATIONS_INDEX.md`
- `NOTEBOOK_READINESS_SOP.md`
- `WINDOWS_OPERATOR_READINESS.md`
- `OPERATOR_COMMAND_SHEET.md`
- `NEXT_3_WORK_BLOCKS.md`

## Standard Repo Template

```text
repo-root/
├── README.md
├── OPERATIONS_INDEX.md
├── NOTEBOOK_READINESS_SOP.md
├── WINDOWS_OPERATOR_READINESS.md
├── OPERATOR_COMMAND_SHEET.md
├── NEXT_3_WORK_BLOCKS.md
├── .venv/
├── dpo_system/
├── notebooks/
├── docs/
└── src/
```

## Shared Markdown Naming Convention

Use the following naming pattern for org-wide operational documents:

- `OPERATIONS_INDEX.md`
- `NOTEBOOK_READINESS_SOP.md`
- `WINDOWS_OPERATOR_READINESS.md`
- `OPERATOR_COMMAND_SHEET.md`
- `NEXT_3_WORK_BLOCKS.md`
- `GATE_CHECKLIST.md`
- `PYTHON_ENVIRONMENT_SOP.md`
- `REPO_SEARCHABILITY_GUIDE.md`

Naming rules:

- uppercase words separated by underscores
- use descriptive, operational names
- avoid ad hoc names or one-off labels
- keep the same names across repos

## Repository Index Pattern

Every repository must include an `OPERATIONS_INDEX.md` that lists:

- repo purpose
- repo owner / operator context
- required Python version
- required venv or environment setup
- notebook readiness status
- gate status
- required artifact paths
- critical runbook links
- repo-specific SOPs

Example structure:

```markdown
# Operations Index

## Repository
- Name:
- Owner:
- Purpose:

## Required Environment
- Python version:
- Virtual environment:
- Kernel:

## Required Runtime Paths
- Path A:
- Path B:

## Gate Status
- Gate A:
- Gate B:
- Preflight:

## Standard Docs
- NOTEBOOK_READINESS_SOP.md
- WINDOWS_OPERATOR_READINESS.md
- OPERATOR_COMMAND_SHEET.md
- NEXT_3_WORK_BLOCKS.md
```

## Notebook Readiness Template

Every notebook must include the following first cells:

```markdown
# Notebook Readiness

## Environment
- Python version:
- Kernel:
- Repo root:

## Runtime Paths
- path 1:
- path 2:

## Artifact Checks
- folder exists:
- JSON exists:
- template exists:

## Gate Status
- Gate A:
- Gate B:

## HITL Checklist
- confirm runtime paths
- confirm artifact existence
- confirm gate status
- confirm vendor decision
- confirm no path drift
```

## Cross-Repo Searchability Rule Set

- every repo must use the same operational doc names
- every critical doc must be in the repo root
- every notebook must reference the same readiness pattern
- every repo must maintain a root-level operations index
- operators must search by standard names, not ad hoc filenames
- AI systems should be able to locate the same SOPs across repos by predictable naming

## Operational Rules

1. No notebook runs without readiness verification.
2. No gate runs without artifact existence checks.
3. No stale docs override the runtime contract.
4. No repo uses unstandardized operational markdown naming.
5. No repo is accepted without a root-level operations index.

## Completion Standard

A repository is considered operationally ready when:

- the standard docs exist
- the index is populated
- notebook readiness is documented
- gate check paths are defined
- Windows operator guidance is included
- the repo can be searched and understood by another operator or AI agent without hidden assumptions
