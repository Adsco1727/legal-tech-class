# Notebook and Pipeline Operating Doctrine

## One-line doctrine statement

The system is a governed production pipeline in which raw signals become validated operational truth through explicit state transitions, human oversight, and auditable decisions.

---

## 1. Purpose

This document defines the operating doctrine for the DPO stack before implementation expands further. It establishes the control model for notebooks, queues, promotion gates, and downstream execution so the system remains governed, reviewable, and auditable.

This document is intentionally architecture-first. It is meant to prevent script sprawl, uncontrolled automation, and silent drift across data, content, and operational state.

---

## 2. Core doctrine

### 2.1 Notebooks are HITL control desks
Notebooks are not background script runners. They are human-in-the-loop operational control surfaces for review, tuning, validation, and approval.

### 2.2 The ledger is the system of record
The ledger and queue hold the operational truth of the workflow and must remain the source of authority for state transitions.

### 2.3 Scrapers generate signals, not truth
Scraper output is provisional evidence. It must be normalized, enriched, validated, reviewed, and approved before it becomes valid operational data.

### 2.4 The queue is a state machine
The queue is not a list or bucket. It is a sequence of explicit workflow states with defined transitions and approval gates.

### 2.5 Downstream systems consume truth, they do not create it
Omnisend, CRM tools, Docassemble, dashboards, and content distribution systems are execution surfaces. They do not own the system of record.

### 2.6 Audit events are governance artifacts
Audit events record who decided what, under which rule-set, with what threshold, and why. They are not just logs.

---

## 3. Notebook Operating Doctrine

### 3.1 Mission
The notebook exists to allow an operator to:
- inspect raw signal and staged records
- tune thresholds and filters
- review exceptions and failures
- harden or override logic with reason
- approve or reject promotion to the next operational state
- trigger downstream actions only after approval

### 3.2 Notebook operator roles
Every notebook must support four stages:

#### A. Ingest & Inspect
- load raw outputs from scrapers or upstream sources
- display counts, samples, source metadata, and exceptions
- separate raw signal from approved operational records

#### B. Tweak & Adjust
- expose thresholds, filters, prompt parameters, confidence values, and overrides
- allow operators to tune rules without editing backend logic blindly
- preserve the distinction between operator tuning and system-of-record state

#### C. Harden & Validate
- perform required schema checks
- run dedupe and compliance checks
- show failed validations and reasons
- provide a clear review path before promotion

#### D. Promote & Execute
- approve or reject records
- record human reasoning in the audit trail
- emit the required ledger state change
- trigger only the next allowed downstream action

### 3.3 Required behaviors for every notebook
- no hidden state transitions
- no silent promotion
- no raw scraper output treated as operational truth
- no downstream firing without approval gate
- no state transition without an audit artifact

### 3.4 Notebook design rule
Notebook UX must be operator-first, not developer-first. The notebook should feel like a control desk, not a raw debugging environment.

---

## 4. Queue / State Machine Manual

### 4.1 Purpose
The queue is the operational control plane for state progression. It defines how a signal becomes a valid record, and how that record may be promoted to a live operational state.

### 4.2 Core rule
A queue record is not just a row in a table. It is an entity in a workflow with explicit state transitions, approval criteria, and governance artifacts.

### 4.3 Marketing lane state model
- raw_harvested
- normalized
- enriched
- valid_email
- compliance_approved
- campaign_ready
- queued_for_omnisend
- sent
- suppressed
- bounced

### 4.4 Issuer lane state model
- raw_ingest
- normalized
- schema_valid
- entity_enriched
- governance_approved
- downstream_ready
- rejected

### 4.5 State transition rules
- A raw signal cannot bypass normalization.
- An enriched record cannot bypass validation.
- A campaign-ready record cannot bypass compliance and dedupe rules.
- A downstream action cannot trigger unless the record is in an approved or promoted state.
- Rejected records must remain visible in exception review and audit history.

### 4.6 Promotion rules
- Marketing lane promotion requires valid email, enrichment success, confidence threshold, dedupe check, compliance status, and approval.
- Issuer lane promotion requires schema validity, entity confidence, governance review, and audit completeness.
- Any override requires reason and audit capture.

---

## 5. Audit Event Contract

### 5.1 Purpose
Audit events are governance artifacts that record decision history. They make the system auditable, reversible, and defensible.

### 5.2 Core principle
Audit events are not logs. Logs describe what happened. Audit events explain what was decided, who decided it, and under what rule-set.

### 5.3 Required audit event fields
- event_id
- event_type
- actor
- actor_type
- lane
- state_before
- state_after
- reason
- rule_set_version
- prompt_version
- threshold_values
- override_flags
- timestamp_utc
- provenance_hash
- source_id
- downstream_action
- related_record_id

### 5.4 Required event types
- lead approved
- lead rejected
- override applied
- normalization accepted
- enrichment accepted
- validation passed
- compliance approved
- campaign promoted
- downstream execution triggered
- record reverted

### 5.5 Governance rule
Every material decision must produce an audit event. Every state transition must be traceable across the ledger and all downstream executions.

### 5.6 Why this matters
Audit artifacts provide:
- legal and operational defensibility
- reversibility of bad decisions
- replayability of state transitions
- confidence for human operators and downstream systems
- evidence for governance, compliance, and accountability

---

## 6. Lane Specification

### 6.1 Purpose
A shared queue architecture should serve multiple lanes, but each lane must maintain a distinct meaning and separate approval logic.

### 6.2 Shared infrastructure, distinct business meaning
The queue infrastructure can be shared, but the data semantics must not be merged.

### 6.3 Marketing lane
Purpose:
- outbound lead preparation and campaign generation

Typical inputs:
- scraped emails
- domain and company identifiers
- marketing persona data
- outreach context

Required gates:
- valid email present
- enrichment success
- compliance / opt-in status
- dedupe pass
- confidence threshold
- human approval

Allowed downstream consumers:
- Omnisend
- campaign payload generation
- CRM sync for marketing use

### 6.4 Issuer lane
Purpose:
- regulated or governance-sensitive workflow records

Typical inputs:
- regulator filings
- registry data
- issuer identifiers
- legal or compliance evidence

Required gates:
- schema validity
- entity resolution
- confidence threshold
- governance approval
- audit completeness

Allowed downstream consumers:
- governance review flows
- regulated document workflows
- issuer tracking systems

### 6.5 Cross-lane boundary rule
Marketing and issuer records must remain separate operational categories even if they share the same queue platform.

---

## 7. Signal-to-Truth Pipeline

### 7.1 Purpose
This section makes explicit that scraper output is not operational truth. It is raw signal that must be transformed into valid operational state.

### 7.2 Pipeline stages

#### Stage 1: Signal generation
- scrapers and source adapters emit raw candidate records
- evidence is incomplete, noisy, and provisional

#### Stage 2: Normalization
- map source-specific fields into a canonical schema
- standardize names, IDs, timestamps, and common attributes

#### Stage 3: Enrichment
- append confidence, metadata, persona, or entity context
- resolve identifiers and enrich the payload

#### Stage 4: Validation
- confirm required fields are present
- run dedupe and confidence checks
- apply compliance or channel filters

#### Stage 5: Human review
- notebook operator reviews the signal
- threshold and prompt tuning may occur here
- decision is made to approve or reject

#### Stage 6: Promotion
- approved record moves into ledger-backed operational state
- audit event is emitted
- downstream system may act on the record

#### Stage 7: Downstream consumption
- Omnisend sends campaigns
- Docassemble generates final materials
- dashboards and review surfaces display approved operational truth

### 7.3 Key rule
Raw signal becomes truth only when it clears normalization, enrichment, validation, approval, and promotion gates.

---

## 8. Implementation Guardrails

These guardrails apply before any new script, notebook, or channel is added to the stack.

### 8.1 Guardrail 1: Define the stage before adding the script
Every script must be assigned to a role in the pipeline:
- signal generation
- normalization
- enrichment
- validation
- review
- promotion
- downstream delivery

### 8.2 Guardrail 2: Define the lane before adding the workflow
Every workflow must be tagged as marketing lane or issuer lane. Do not mix lane meaning in a shared queue without preserving lane identity.

### 8.3 Guardrail 3: Every state transition must be audit-backed
No approval, override, or downstream action should occur without an audit event.

### 8.4 Guardrail 4: Notebook UX must be operator-first
Notebooks should be built for review, tuning, approval, and exception handling, not for raw scripting convenience.

### 8.5 Guardrail 5: DB truth is distinct from content output
Operational database state, campaign content, and raw scraped evidence are not the same category. They must not be conflated in the workflow.

### 8.6 Guardrail 6: Upstream systems do not define truth
Scrapers, source adapters, and draft content generators are not the system of record. They are sources of signal and output that must be validated before promotion.

### 8.7 Guardrail 7: Only approved records cross governance boundaries
Do not allow unreviewed records to enter downstream delivery systems or audit-sensitive workflows.

### 8.8 Guardrail 8: The architecture must stay pipeline-first
Scripts are adapters. The system is the pipeline. Protect the operation model before expanding the tool set.

---

## Closing statement

The system is a governed production pipeline. It is not a pile of scripts. It is a disciplined operating model in which signals flow through explicit states, human operators make control decisions, audit artifacts prove governance, and the ledger holds the truth consumed by downstream systems.

---

## 9. Additional operational doctrine

### 9.1 Notebook operator roles are governance responsibilities
Every notebook must support four operational stages, each representing a distinct human responsibility inside the governed pipeline:

#### Stage A — Ingest & Inspect
The operator reviews:
- raw signals from scrapers or source adapters
- provenance metadata
- sample rows and exception logs
- confidence distributions and enrichment summaries

This stage ensures the operator understands what the machine produced before any tuning or validation occurs.

#### Stage B — Tweak & Adjust
The operator modifies:
- thresholds
- filters
- segmentation rules
- prompt templates
- enrichment overrides
- dedupe logic

This stage allows the operator to tune the machine without modifying backend code.

#### Stage C — Harden & Validate
The operator verifies:
- schema correctness
- dedupe outcomes
- compliance filters
- confidence thresholds
- exception handling
- rule-set behavior

This stage ensures the record is safe, complete, and compliant before promotion.

#### Stage D — Promote & Execute
The operator:
- approves or rejects records
- emits audit events
- triggers queue state transitions
- initiates downstream actions such as Omnisend, Docassemble, or CRM updates
- confirms ledger updates

This stage is the governance checkpoint where signals become operational truth.

### 9.2 Notebook design rules
All notebooks must follow these rules:

- No hidden state. Operators must see all relevant data before making decisions.
- No silent promotion. Every transition requires explicit approval.
- No raw signal treated as truth. Scraper output must pass through normalization, enrichment, validation, and human review.
- No downstream execution without approval. Campaigns, documents, and CRM syncs must only occur after promotion.
- No auditless transitions. Every material action must produce an audit artifact.

### 9.3 Notebook failure modes
A notebook is considered unsafe if:
- raw signals are promoted without review
- overrides occur without reason
- thresholds drift without operator awareness
- lane contamination occurs
- downstream actions trigger without audit trace
- rejected records disappear instead of being logged

These failure modes must be prevented through notebook design and operator discipline.

### 9.4 Queue responsibilities
The queue is responsible for:
- holding the current operational state
- enforcing valid transitions
- preventing invalid or unsafe transitions
- ensuring lane separation
- emitting audit events
- enabling reversibility
- providing a consistent interface for downstream systems

The queue is the operational backbone of the pipeline.

### 9.5 State transition guarantees
Every transition must guarantee:
- determinism
- auditability
- reversibility
- lane correctness
- rule-set version capture
- threshold capture
- provenance preservation

If any of these guarantees fail, the transition must be rejected.

### 9.6 Queue failure modes
The queue becomes unsafe if:
- transitions occur without audit events
- transitions occur without human approval
- transitions bypass validation
- transitions bypass enrichment
- transitions bypass compliance gates
- transitions merge lanes
- transitions lose provenance

These must be prevented through strict enforcement of the doctrine.

### 9.7 Audit event lifecycle
Audit events must be:
- created at the moment of decision
- written to the ledger
- immutable
- queryable
- reversible through counter-events
- linked to the record and lane
- versioned with rule-set and prompt metadata

Audit events are the memory of human judgment inside the system.

### 9.8 Audit event categories
Audit events fall into these categories:
- normalization events
- enrichment events
- validation events
- approval events
- override events
- promotion events
- downstream execution events
- rejection events
- reversion events

Each category must follow the canonical schema.

### 9.9 Lane identity rules
Every record must carry an explicit lane identity:
- lane = marketing
- lane = issuer

Lane identity determines:
- required fields
- validation rules
- enrichment logic
- approval gates
- downstream consumers

Lane identity must never change after normalization.

### 9.10 Lane contamination prevention
The system must enforce:
- no marketing logic applied to issuer records
- no issuer logic applied to marketing records
- no shared enrichment models unless explicitly lane-safe
- no shared compliance filters unless explicitly lane-safe
- no downstream system pulling from the wrong lane

Lane contamination is a critical failure mode.

### 9.11 Pipeline invariants
The pipeline must enforce these invariants:
- raw signals are never truth
- truth only exists after promotion
- promotion only occurs after human approval
- downstream systems only consume promoted truth
- audit artifacts must accompany every transition
- provenance must be preserved end-to-end

These invariants define the safety of the system.

### 9.12 Pipeline failure modes
The pipeline becomes unsafe if:
- raw signals bypass normalization
- enriched signals bypass validation
- validated signals bypass approval
- approved signals bypass audit
- downstream systems consume unapproved data
- provenance is lost
- rule-set versions are not captured

These must be prevented through strict adherence to the doctrine.

### 9.13 Guardrails before coding
No implementation work may begin until:
- the notebook doctrine is finalized
- the queue state machine is finalized
- the audit event contract is finalized
- lane specifications are finalized
- the signal-to-truth pipeline is finalized

This prevents premature coding and architecture drift.

### 9.14 Guardrails during coding
During implementation:
- no module may bypass the queue
- no scraper may write directly to downstream systems
- no notebook may execute without approval gates
- no audit event may be optional
- no lane may be implicitly inferred
- no state transition may be silent

These guardrails ensure the system remains governed.

### 9.15 Guardrails after deployment
After deployment:
- operator training must follow the doctrine
- notebooks must remain HITL control desks
- audit events must remain governance artifacts
- queue transitions must remain explicit
- lane separation must remain strict
- downstream systems must remain consumers only

This preserves long-term system integrity.

---

## 10. Outbound content mapping by channel

### 10.1 Principle
Each outbound channel is a distinct campaign, a distinct lane, a distinct audience, and a distinct purpose. It must not share content, routing, approval, or audit meaning with any other channel without explicit design intent.

### 10.2 Notebook-controlled outbound design
The notebook is the controlled outbound content desk. It is where the operator selects:
- segment
- persona
- lane
- channel
- content template
- approval status
- routing intent

This creates the outbound intent before any campaign payload is generated.

### 10.3 Channel-specific messaging model
Each channel owns its own templates, routing rules, and approval states.

#### Email (Omnisend)
- cold outreach
- warm follow-up
- authority-site CTA
- issuer engagement
- newsletter or nurture drip

#### LinkedIn
- connection request
- authority message
- issuer intro
- BD outreach

#### Twitch
- creator outreach
- community warm-up
- brand presence
- funnel activation

#### Social media
- persona-based post sets
- campaign bursts
- inbound warm-signal triggers

These channels may be sequenced, but they must never be treated as interchangeable content surfaces.

### 10.4 Outbound content assembly
The notebook must assemble all outbound content in a governed way:
- subject line or opening message
- body copy
- CTA
- link or destination
- personalization fields
- segment match
- compliance flags
- approval state

No unapproved outbound message may leave the notebook layer.

### 10.5 Channel routing rules
The operator decides the routing path:
- email only
- email + LinkedIn
- LinkedIn only
- Twitch only
- social only
- multi-channel burst

Every routing decision must produce an audit event and be tracked in the ledger.

### 10.6 Campaign payload generation
The notebook must generate outbound payloads, not scripts alone. Each payload belongs to a channel and is built from the approved content intent.

Canonical payload categories include:
- Omnisend CSV payload
- LinkedIn outreach payload
- Twitch campaign script payload
- social post payload

All payloads are downstream outputs of approved notebook decisions.

### 10.7 Channel isolation rules
The system must enforce these rules:
- each channel has its own campaign identity
- each channel has its own templates
- each channel has its own audience constraints
- each channel has its own compliance logic
- each channel has its own approval gate
- each channel has its own audit event stream

Channel isolation is a critical governance requirement.

### 10.8 Minimal launch path
The fastest correct production path is:
1. produce the initial 300-lead CSV
2. normalize and validate the record set
3. route the validated leads through the notebook review layer
4. map the approved segment to a content template
5. generate the Omnisend payload
6. approve and send the minimal outbound batch
7. stand up separate channel accounts only after the first campaign proves stable
8. capture replies manually and feed them back into the ledger and queue

This preserves momentum while keeping the system governed.

### 10.9 Guardrails for outbound execution
The outbound system must never do the following:
- send unreviewed content
- route a lead to the wrong channel
- reuse a template across unrelated lanes without explicit review
- create campaign output without an audit trail
- mix channel-specific campaign accounts without identity separation
- allow downstream systems to consume unapproved content

These are preventable failure modes and must be enforced in the notebook layer and the queue layer.

---

## Final doctrine statement

The DPO system is a governed production pipeline where scrapers generate signals, notebooks provide human control, queues define state transitions, audit events preserve governance, channels enforce campaign identity, outbound content is mapped per channel, and the ledger holds the operational truth consumed by downstream systems.
