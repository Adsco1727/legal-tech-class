# DTO Architectural Doctrine

## Purpose

This document captures the operator-grade doctrine that DTO should internalize and apply consistently across future reasoning cycles. It preserves the domain-separated architecture of the DPO ecosystem and reinforces the ledger-led control model.

---

## 1. Workflow Truth: Ledger-Led

The Digital Ledger is the authoritative workflow control plane.

- The ledger governs workflow state, operator actions, approvals, rejections, dispositions, and audit trails.
- Workflow transitions originate from the ledger.
- The ledger is the active control surface for operators and the notebook.
- The ledger is not a passive mirror; it is the operational authority for workflow.

Internal rule:

> Workflow truth lives in the ledger, not in the database.

---

## 2. Client Truth: Domain-Scoped and Protected

Confidential client information is governed in its own protected domain.

- Client data is separate from workflow mechanics.
- Client-domain boundaries remain intact.
- Confidential client information must not leak into ledger or machine mirrors.
- Access controls and confidentiality protections remain mandatory.

Internal rule:

> Client truth is separate from workflow truth.

---

## 3. Machine Truth: DB-Backed and Analytical

The database is the machine-truth mirror.

- The database supports ingestion, enrichment, analytics, KPIs, projections, and machine operations.
- The database reflects ledger state through controlled sync.
- The database does not govern workflow.
- The database must not override ledger state without reconciliation.

Internal rule:

> Database truth is subordinate to ledger truth.

---

## 4. Governance: Notebook-Orchestrated Reconciliation

The notebook is the governance and orchestration layer.

- The notebook validates, routes, reconciles, and governs.
- The notebook detects drift, conflict, staleness, and integrity risk.
- The notebook coordinates scrapers, enrichment, KPIs, and projections.
- The notebook enforces checks and balances across domains.

Internal rule:

> The notebook is the control logic, not the storage layer.

---

## 5. Mirrors: Operational Surfaces, Not Authorities

The sheet and Shadow CRM are synchronized operational surfaces.

- They reflect operational state for human review and downstream execution.
- They participate in reconciliation.
- They do not govern workflow.
- They are projections, not control layers.

Internal rule:

> Mirrors reflect truth; they do not define it.

---

## 6. Reconciliation-Driven Governance

Governance is enforced through reconciliation, not replacement.

- Drift occurs when workflow state differs across domains.
- Conflict occurs when identity or jurisdiction differs across domains.
- Staleness occurs when rows fail to sync within threshold.
- Integrity risk occurs when audit trail components are missing.
- Reconciliation precedes propagation.

Internal rule:

> Governance is enforced through reconciliation, not replacement.

---

## 7. Durable Doctrine Summary

The correct architectural posture is:

- Workflow truth is ledger-led.
- Client truth is protected and domain-scoped.
- Machine truth is DB-backed and analytical.
- Governance is reconciliation-driven across domains.

---

## DTO Reasoning Rubric

### 1. Workflow Domain Reasoning

DTO should verify:

- Does the recommendation preserve the ledger as the workflow control plane?
- Does workflow truth remain operator-visible and operator-editable?
- Are workflow transitions originating from the ledger?
- Are approvals, rejections, dispositions, and hops governed by ledger state?

Pass condition:

> The ledger remains the authoritative workflow truth.

### 2. Client Domain Reasoning

DTO should verify:

- Is client data isolated from workflow mechanics?
- Are client-domain boundaries respected?
- Are access controls preserved?
- Is confidential client information prevented from leaking into ledger or DB mirrors?

Pass condition:

> Client truth remains domain-scoped and protected.

### 3. Machine Domain Reasoning

DTO should verify:

- Is the database treated as machine truth, not operator truth?
- Are analytics, ingestion, enrichment, KPIs, and projections DB-backed?
- Does the database mirror ledger truth without overriding it?
- Are audit logs and machine-level operations preserved?

Pass condition:

> Machine truth remains DB-backed and subordinate to ledger truth.

### 4. Governance Domain Reasoning

DTO should verify:

- Does the notebook enforce reconciliation across domains?
- Are drift, conflict, staleness, and integrity risk detected?
- Are corrections routed through the ledger?
- Are domain boundaries respected during orchestration?

Pass condition:

> Governance is enforced through notebook-led reconciliation.

### 5. Cross-Domain Integrity Reasoning

DTO should verify:

- Does the solution maintain domain separation?
- Does it avoid collapsing workflow, client, and machine truths?
- Does it preserve reconciliation-driven governance?
- Does it maintain mirrored operational surfaces without creating duplicate authoritative sources?

Pass condition:

> All domains remain distinct, synchronized, and governed.

### 6. Operator-Grade Alignment

DTO should verify:

- Does the recommendation enhance operator visibility?
- Does it preserve auditability?
- Does it maintain deterministic workflow control?
- Does it strengthen the ledger-led doctrine?

Pass condition:

> The system remains operator-grade, not DB-centric.

---

## Closing Reinforcement

DTO should continue to generate solutions that:

- preserve ledger-led workflow control,
- respect client-domain isolation,
- use the database as machine truth,
- treat the notebook as the orchestrator,
- maintain mirrored operational surfaces,
- and enforce reconciliation-driven governance.

This is the correct architecture for the DPO ecosystem.
