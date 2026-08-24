# QUEUE.md — DTO Finite-State Machine Specification (Governed v2.0)

## 1. DTO Operating Model

The queue is governance infrastructure, not workflow plumbing.

Every lane is either:

- ACTIVE — live, proven, operator-stable
- STAGED — mapped, reviewed, and documented, but not activated until its Need / Value / Risk profile is approved

No lane transitions to ACTIVE without:

- evidence stability
- operator load availability
- audit spine compliance
- schema alignment
- deterministic handoff metadata
- a defined human-in-the-loop review gate

The operating principle is simple:

> A lane is not considered ready because it is useful. A lane is ready because it is governed, auditable, and operationally proven.

---

## 2. Common Vocabulary (Global)

All lanes use the same DTO vocabulary.

### States
- `raw_input`
- `queue_intake`
- `hitl_review`
- `publish_or_reject`
- `archive_or_outbound`
- `audit_logged`

### Required Metadata
Every item carries:

- `lane_id` — which lane owns the item
- `batch_id` — batch grouping
- `item_id` — unique item identifier
- `origin_state` — state before transition
- `timestamp` — UTC
- `operator_id` — HITL reviewer
- `payload_hash` — integrity check
- `evidence_blob` — raw source data or captured source artifact

### Handoff Contract
Cross-lane handoffs must include:

- `handoff_from_lane`
- `handoff_to_lane`
- `handoff_reason`
- `handoff_payload`
- `handoff_timestamp`

This prevents drift and ensures every item remains traceable across the ecosystem.

---

## 3. Lane Status

### ACTIVE LANE
#### Ooma Validation Lane
- Status: ACTIVE
- Reason: Proven throughput, stable operator workflow, consistent evidence output, and documented review path.

### NEXT LANE
#### BD Ingestion & Outbound Campaign Lane
- Status: STAGED → NEXT
- Reason: Schema mapped and payload defined, but not yet activated beyond the initial proof path.

### FUTURE LANES (STAGED)
- SEO Intelligence Lane
- Geo-Governance Lane
- Law Ingestion Lane
- Clause Intelligence Lane
- Docassemble Governance Lane

None of these lanes activate until the Need / Value / Risk test is passed.

---

## 4. Global State Machine (All Lanes)

All lanes follow the same finite-state progression.

### 4.1 State Definitions

#### `raw_input`
- Initial state for any item entering a lane.
- Unvalidated, unnormalized, unreviewed, and not yet trusted.

#### `queue_intake`
- Item is accepted into the lane queue.
- Assigned lane ID, batch ID, item ID, and timestamps.
- Item is now formally under governance.

#### `hitl_review`
- Human-in-the-loop operator reviews the item.
- Operator may inspect, correct, annotate, approve, reject, or requeue with a reason.
- This is the mandatory governance checkpoint.

#### `publish_or_reject`
- Decision state after review.
- The item is either:
  - `approved` and moved toward downstream publication
  - `rejected` and routed to archive with reason

#### `archive_or_outbound`
- Approved items move to outbound or downstream processing.
- Rejected items move to archive with an evidence record.
- Requeues are explicit and logged.

#### `audit_logged`
- Final state for all terminal paths.
- All transitions are written to the audit spine.
- Includes before/after snapshots, payload hash, operator action, and timestamp.

### 4.2 Canonical Transition Flow

The standard DTO transition path is:

1. `raw_input`
2. `queue_intake`
3. `hitl_review`
4. `publish_or_reject`
5. `archive_or_outbound`
6. `audit_logged`

This is the canonical model for every lane.

### 4.3 Required Transition Rules

Every transition must satisfy all of the following:

- a valid source state exists
- a valid destination state is declared
- lane metadata is present
- operator or system actor is recorded
- timestamp is present in UTC
- payload hash is captured
- event is written to the audit spine

### 4.4 Transition Examples

#### Standard approved path
- `raw_input` → `queue_intake`
- `queue_intake` → `hitl_review`
- `hitl_review` → `publish_or_reject`
- `publish_or_reject` → `archive_or_outbound`
- `archive_or_outbound` → `audit_logged`

#### Rejected path
- `raw_input` → `queue_intake`
- `queue_intake` → `hitl_review`
- `hitl_review` → `publish_or_reject`
- `publish_or_reject` → `archive_or_outbound`
- `archive_or_outbound` → `audit_logged`

#### Requeue path
- `hitl_review` → `queue_intake` (explicitly reasoned and logged)
- requeue requires operator override and a reason code

### 4.5 Global Rule

No lane may bypass `hitl_review` for initial activation.
No terminal state may skip `audit_logged`.
No state transition may be implicit.

---

## 5. Approval Gate

Every lane must include a formal approval gate before a record, batch, or artifact is considered publishable.

### Approval Gate Requirements

Before any item is marked approved or published, the following must be true:

- validation succeeded
- schema alignment passed
- duplicate detection passed
- required metadata exists
- operator review was recorded
- reason code was captured for any rejection or override
- evidence artifact was retained

### Approval Fields
Each approval entry must include:

- `lane_id`
- `batch_id`
- `item_id`
- `operator_id`
- `decision` — approve / reject / requeue
- `decision_reason`
- `timestamp_utc`
- `evidence_reference`

### Approval Principle

Approval is not a convenience metric. It is a governance action.

The operator is not a passive user of the system; the operator is a governed decision-maker inside the production line.

---

## 6. Lane-Specific Status Model

### 6.1 Ooma Validation Lane
Status: ACTIVE

Canonical flow:

- `raw_batch` → `queue_intake` → `hitl_review` → `approved` or `rejected` → `outbound_queue` or `archive` → `audit_logged`

Purpose:
- validate contact records
- normalize names and phone data
- remove malformed or duplicate rows
- keep a reviewable evidence package

### 6.2 BD Ingestion Lane
Status: STAGED → NEXT

Typical flow:

- `raw_scraper_json` → `normalized` → `schema_valid` → `hitl_review` → `bd_published` or `rejected` → `audit_logged`

Purpose:
- normalize scraped data into a structured lead or BD format
- enforce schema before publication

### 6.3 Outbound Campaign Lane
Status: STAGED

Typical flow:

- `bd_event` → `queue_intake` → `hitl_review` → `published_outbound` → `kpi_logged` → `audit_logged`

Purpose:
- orchestrate outbound actions across channels
- keep a governed campaign record with KPI evidence

### 6.4 SEO Intelligence Lane
Status: STAGED

Typical flow:

- `bd_listing` → `seo_signal_extraction` → `hitl_review` → `seo_publish` → `audit_logged`

Purpose:
- detect trend signals, content gaps, and opportunity signals
- add proactive market intelligence without bypassing governance

### 6.5 Geo-Governance Lane
Status: STAGED

Typical flow:

- `jurisdiction_data` → `normalization` → `hitl_review` → `geo_rules_published` → `audit_logged`

Purpose:
- normalize jurisdictional data and routing rules for expansion

### 6.6 Law Ingestion Lane
Status: STAGED

Typical flow:

- `raw_law_text` → `structured_extraction` → `hitl_review` → `law_published` → `audit_logged`

Purpose:
- turn raw legal input into structured, reviewable content

### 6.7 Clause Intelligence Lane
Status: STAGED

Typical flow:

- `raw_contract` → `clause_extraction` → `hitl_review` → `clause_map_published` → `audit_logged`

Purpose:
- extract and classify clause logic from legal content

### 6.8 Docassemble Governance Lane
Status: STAGED

Typical flow:

- `bd_listing_plus_signals` → `yaml_generation` → `hitl_review` → `docassemble_publish` → `audit_logged`

Purpose:
- generate governed document artifacts from normalized system inputs

---

## 7. Activation Rules for New Lanes

A new lane may only move from STAGED to ACTIVE when all of the following are satisfied:

### 7.1 Need
- there is a real operational requirement
- the lane solves a defined bottleneck or throughput problem
- the requirement is not theoretical, speculative, or opportunistic

### 7.2 Value
- the lane materially improves a core process
- the output is measurable and reviewable
- the lane creates a clear user or operator benefit

### 7.3 Risk
- risk is understood and controlled
- schema rules are defined
- review and audit requirements are in place
- failure modes are known and manageable

### 7.4 Governance Proof
A lane must have:

- explicit states and transitions
- a HITL review gate
- evidence capture
- metadata and handoff contracts
- a valid audit path

### 7.5 Operational Proof
A lane must demonstrate:

- stable execution on a test or production batch
- repeatable review outcomes
- traceable evidence output
- no silent failure paths

### 7.6 Activation Rule

A lane becomes ACTIVE only after it has produced a clean, reviewable execution cycle and is governed by the same audit and review model as the Ooma lane.

Until then, it remains STAGED.

---

## 8. Final Policy

- No lane bypasses HITL review.
- No terminal state bypasses audit logging.
- No cross-lane handoff omits metadata.
- No staged lane is treated as active simply because it is conceptually useful.
- The queue is a control plane, not an inbox.

# End of QUEUE.md
