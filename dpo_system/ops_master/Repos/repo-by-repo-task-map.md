# Repo-by-Repo Task Map

## Purpose
Map the operational apparatus to the repositories that support it.

## Repositories
- legal-tech-class
  - Documentation and educational content backbone
  - Use as source material and reference for legal-tech structure

- dpo-ledger-tools
  - Ledger and tracking utilities
  - Candidate for evidence and run-state tooling

- dpo-interview-suite
  - Interview and intake support
  - Candidate for intake workflow integration

- dpo-integrations
  - Integration layer for external flows
  - Candidate for outbound and inbound connectors

- dpo-casework
  - Case handling and workflow logic
  - Candidate for operational case progression

- dpo-automation-suite
  - Automation orchestration and batch operations
  - Candidate for outbound engine execution

- dpo-admin-tools
  - Administrative tooling and process support
  - Candidate for compliance and operator utility features

- docassemble-dpolawstack
  - Document assembly engine
  - Candidate for legal document generation and packaging

## Recommended Mapping
- DT coordination layer -> ops_master
- Evidence and state -> dpo-ledger-tools
- Intake and interview flow -> dpo-interview-suite
- Integrations -> dpo-integrations
- Case operations -> dpo-casework
- Automation -> dpo-automation-suite
- Admin support -> dpo-admin-tools
- Document assembly -> docassemble-dpolawstack
