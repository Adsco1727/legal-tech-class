# Org-Wide Governance Statement

## Policy

The operating unit of the organization is the repo. The workflow unit is the notebook. The database is the downstream consumer of validated operational output.

One repo owns one operational domain. Many notebooks may live inside that repo when they serve different workflows in the same domain. A notebook is never treated as a standalone product or a justification for creating a new repo unless it is itself a distinct business domain with independent ownership, controls, and operating lifecycle.

## Repo policy

Each DPO repository must:

- map to a single domain or operational boundary
- contain a canonical notebook template
- contain a notebook inventory registry
- maintain a clear repo-level ownership model
- operate as a governed execution environment, not a collection of ad hoc notebooks

Examples of valid repo ownership:

- dpo-ledger-tools = ledger and control-plane data
- dpo-casework = case progression and workflow execution
- dpo-admin-tools = administration and operational support
- dpo-integrations = external data connectors and system interfaces
- dpo-automation-suite = automation and operational orchestration
- dpo-interview-suite = interview and intake workflows
- docassemble-dpolawstack = document assembly and output generation

## Notebook policy

Each notebook must:

- follow the canonical template
- be stored within its owning repo
- be listed in the repo notebook inventory
- be assigned an operational purpose tied to the repo domain
- be tested before enablement
- produce evidence before it is allowed to feed data downstream

No repo may be created for a single notebook. No notebook may bypass the template and inventory process. No notebook may be treated as production-ready without validation.

## Approval flow

A notebook is approved only through the following sequence:

1. Repo readiness check
   - repo structure is correct
   - required artifacts exist
   - canonical template and inventory are in place

2. Notebook readiness check
   - notebook is aligned to the repo domain
   - dependencies are valid
   - execution path and outputs are explicit

3. Gate validation
   - required data contracts, schema checks, and operational gates pass
   - validation fails fast on missing files, bad paths, or invalid vendor artifacts

4. Evidence capture
   - logs, validation output, and artifact proof are recorded
   - each notebook must preserve evidence of proof, not assumptions

5. Operator sign-off
   - a human operator verifies readiness and approves enablement

6. Controlled enablement
   - the notebook is activated in sequence only when its upstream dependencies are confirmed

7. Data feed to database
   - once enabled, the output is passed into the database only under controlled validation and monitoring
   - no downstream data push occurs without upstream proof and evidence

## Operational doctrine

We are not enabling notebooks in parallel just because they exist. We are enabling them in order, validating each result, and proving that the system can feed the data model before additional notebooks are turned on.

This means the rollout sequence is intentionally disciplined:

- assemble
- validate
- harden
- approve
- enable
- feed data to the database
- continue population

## Prohibited patterns

The organization will not permit:

- one repo per notebook
- notebooks outside their owning repo boundary
- production enablement without evidence
- upstream data feeds without validation gates
- untracked notebook drift or hidden operational work

## Final principle

The repo defines the domain. The notebook defines the workflow. The validation gate defines the standard. The evidence record defines whether the workflow may operate. The database is the downstream destination for validated operational output, not the place where unproven work is allowed to accumulate.
