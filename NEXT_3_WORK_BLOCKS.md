# Next 3 Work Blocks

## Purpose

This is the immediate execution checklist for the repo. It is intentionally narrow, deterministic, and designed to prevent rework caused by missing artifacts, path drift, or shell confusion.

---

## Work Block 1 — Notebook Readiness

### Goal

Get the notebooks functioning in the local environment without broad scope expansion.

### Checklist

- [ ] Confirm the Python environment and active interpreter
- [ ] Confirm the repo root and working directory are correct
- [ ] Verify notebook folders exist and are discoverable
- [ ] Open the first notebook and verify kernel resolution
- [ ] Run a minimal notebook smoke test
- [ ] Fix import and path issues before touching content logic
- [ ] Repeat for each notebook until each launches cleanly
- [ ] Capture working notebook status in a short operator note

### Guardrails

- Do not expand SEO or content work while notebook runtime is unstable.
- Do not assume a notebook works because the file exists.
- If a notebook fails, fix the environment or path issue before editing content.

---

## Work Block 2 — Repo Governance and Gate Proof

### Goal

Prove the repo is operational before any downstream work proceeds.

### Checklist

- [ ] Run repo status
- [ ] Run Gate A readiness
- [ ] Run Gate B readiness
- [ ] Verify required vendor artifact path exists
- [ ] Verify the actual Gate B response file is present at:
  - `dpo_system/vendor/ooma/ooma_response_fields.json`
- [ ] Verify required JSON fields are populated and valid
- [ ] Confirm decision state is explicit and accepted or pending
- [ ] Record evidence paths and pass/fail results
- [ ] Do not continue to broader operations unless Gate proof is clean

### Required path check

This repo’s runtime contract is tied to the vendor Ooma response under:

```text
dpo_system/vendor/ooma/
```

Do not rely on stale doc paths or prior operator assumptions.

### Guardrails

- Missing artifacts are not “minor issues”; they block the control plane.
- If Gate B is failing, check the actual file path and contract before debugging anything else.
- Validate the runtime, not the memoized path.

---

## Work Block 3 — SEO + Site Setup

### Goal

Once the environment and repo control flow are stable, configure the site and content stack for discoverability and growth.

### Checklist

- [ ] Confirm site metadata and base configuration
- [ ] Check canonical URL structure
- [ ] Configure Open Graph and Twitter card metadata
- [ ] Validate sitemap and robots configuration
- [ ] Review internal linking structure
- [ ] Check page title and description quality
- [ ] Review keyword targeting and content hierarchy
- [ ] Confirm analytics and verification hooks are present
- [ ] Run a final structural site quality check

### Guardrails

- Do not start with SEO before notebook readiness and gate proof are stable.
- Treat SEO as installation and polishing work, not a substitute for repo health.
- Any search or site optimization changes should be validated after the repo is functionally green.

---

## Operating Rule

> The repo must be functionally stable before any broad SEO or content expansion begins.

If a gate fails, a path is wrong, or a required artifact is missing, stop and fix that first. Do not build on an unstable foundation.

---

## Minimal Success Criteria

The next three blocks are complete when:

- all notebooks launch and run smoke checks
- Gate A and Gate B are verified
- the vendor response contract is present and valid
- the SEO/site setup is configured and reviewed

At that point, the repo is ready for continued execution without reintroducing the same class of failure.
