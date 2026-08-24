# DT Command Surface

## Purpose
This document defines the core command surface for the DT operator layer. It is the control plane for daily execution, status review, and evidence capture.

## Core Commands
- Start run
- Pause run
- Resume run
- Stop run
- Reconcile intake
- Validate evidence
- Publish summary
- Escalate issue

## Command Sequence
1. Confirm intake files are present.
2. Validate manifests and routing targets.
3. Execute batch operations.
4. Capture evidence and log outputs.
5. Publish operator summary.

## Operating Rules
- Never proceed without an intake source.
- Every action must be logged.
- Any failure must trigger a checkpoint update.
