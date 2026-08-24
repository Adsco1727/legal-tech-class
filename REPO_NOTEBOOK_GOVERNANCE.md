# Repo Notebook Governance Rule

## Core rule

One repo owns one operational domain.
Many notebooks may live inside that repo when they serve different workflows in the same domain.

## Standard structure

Each DPO repo must follow this pattern:

- one repo per domain or product boundary
- one canonical notebook template per repo
- one notebook inventory folder per repo
- multiple operational notebooks inside the repo as needed
- no repo creation for a single notebook
- no notebook creation without using the canonical template

## Why this rule matters

This keeps the ecosystem:

- governed
- auditable
- discoverable
- consistent
- reusable
- aligned with repo ownership and operational scope

## Canonical model

The repo-level pattern is:

- Repo = ownership boundary
- Notebook = workflow execution
- Inventory folder = approved notebook registry
- Template = standard operating pattern

## Required repo naming convention

Each repo should keep:

- a canonical notebook starter
- a notebook_inventory folder
- repo-specific operational notebooks inside the repo

Example:

- dpo-ledger-tools/
  - NOTEBOOK_TEMPLATE_STANDARD.ipynb
  - notebook_inventory/
  - ledger_production_readiness.ipynb
  - ledger_audit_review.ipynb

## Governance rule

A notebook is approved only when it:

- follows the canonical template
- passes readiness checks
- passes gate validation
- records evidence
- receives operator sign-off

## Prohibited pattern

Do not create a new repo for every notebook.
Do not let notebooks drift outside the repo’s governance boundary.
Do not treat a notebook as a separate product unless it truly owns a separate product or service.

## Final principle

The repo defines the domain.
The notebook defines the workflow.
The template defines the standard.
The inventory defines the approved operating set.
