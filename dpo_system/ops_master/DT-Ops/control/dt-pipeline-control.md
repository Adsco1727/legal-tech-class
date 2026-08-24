# DT Pipeline Control

## Objective
Define the control flow for the DT pipeline so that execution is repeatable and auditable.

## Pipeline Stages
1. Intake
2. Validation
3. Routing
4. Execution
5. Evidence capture
6. Summary publication

## Required Controls
- Intake source check
- File integrity check
- Routing check
- Execution checkpoint
- Evidence confirmation

## Failure Handling
If any stage fails, mark the run as degraded and create a corrective task before continuing.
