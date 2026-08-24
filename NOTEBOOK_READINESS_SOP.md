# Notebook Readiness SOP

## Purpose

This SOP defines the required notebook operating standard for all DPO repos.

## Required Readiness Panel

Every notebook must begin with a readiness panel containing:

- runtime paths
- gate states
- artifact checks
- vendor decision state
- operator state

## Required Checks

- confirm repo root
- confirm Python version
- confirm kernel selection
- confirm required directories exist
- confirm required files exist
- confirm required JSON values are present
- confirm Gate A status
- confirm Gate B status
- confirm no path drift between docs and runtime

## Mandatory HITL Checklist

1. Confirm runtime paths
2. Confirm artifact existence
3. Confirm required files
4. Confirm Gate A
5. Confirm Gate B
6. Confirm vendor decision
7. Stop if any contract is missing

## Execution Rule

A notebook must not run if any readiness check fails.

## Evidence Capture

A notebook should record:

- date and time
- operator
- runtime paths
- gate state
- artifact status
- decision state
