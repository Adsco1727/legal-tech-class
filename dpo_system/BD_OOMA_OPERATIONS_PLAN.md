# DPO BD + Ooma/CSF Operations Plan

## Objective
Create a simple, founder-controlled outbound pipeline that does not depend on a full CRM. Use the existing contract-first ledger and operator workflow as the control plane, with Ooma/CSF as the provider lane and a lightweight lead store as the data layer.

## Operating rule: three distinct pipelines

These are separate export universes and must never be merged or treated as interchangeable:

1. Standard pipeline (Google/Microsoft standard template)
   - Used for Ooma autodialer, Google Contacts, Microsoft Contacts.
   - Output: 500-contact CSV batches.
   - Commands: build-db-outbound, preflight-csf.
   - Destination: dialer systems and standard CRMs.

2. BD pipeline (Brilliant Directories 30-cell template)
   - BD = Brilliant Directories.
   - BD uploads are not autodialer CSVs.
   - Schema: 30 fixed BD fields.
   - Destination: www.directprivateoffers.net.

3. Internal / compliance pipeline (DPO evidence + outbound engine)
   - Used for evidence manifests, outbound engine specs, compliance panels.
   - Schema: strict outbound contract with registry-tracked IDs.
   - Destination: internal DPO compliance systems.

## 1. Operating model

### Core principle
Do not build a large CRM before the workflow is proven. Instead:
- keep the current ledger/workflow engine as the execution and audit layer
- use a lightweight lead table for BD records
- use Ooma/CSF as the outbound system of record for calls
- keep ownership and state transitions explicit

### Recommended lanes
- BD lane: lead intake, qualification, outbound call readiness
- Ops lane: workflow execution, queueing, audit, replay, failure handling
- Compliance lane: consent, DNC, opt-out, retention, access control

## 2. Data model

### Canonical lead fields
Use a minimal but robust schema:
- lead_id
- phone_number
- email
- source_system
- campaign_name
- jurisdiction
- consent_status
- do_not_contact
- owner
- stage
- status
- created_at
- updated_at

### Existing foundation
The existing lead contract in [dpo_system/contracts/leads.yaml](dpo_system/contracts/leads.yaml) is a strong starting point. It should be expanded rather than replaced.

### Storage recommendation
- Start with SQLite for the lead table and local operator workflow
- Keep the workbook/ledger as the workflow and audit surface
- Upgrade to Postgres only if volume and concurrency justify it

## 3. BD workflow

### Intake flow
1. Import a seed file from Ooma/CSF or a CSV upload
2. Validate lead shape and consent rules
3. Queue the record for outbound processing
4. Track disposition through a simple stage model:
   - new
   - queued
   - called
   - connected
   - qualified
   - converted
   - failed
   - opt_out

### Important design choice
Do not make the CRM the source of truth for outbound execution. The provider lane should be the operational source of truth for dial activity, while the ledger records the workflow state and audit trail.

## 4. Priority shift: media-first growth

The operating model should explicitly treat media as the message. The outbound system will not work well if we only optimize the dialer and ignore the content engine.

### Recommended sequence
1. Produce content quickly and repeatedly.
2. Use that content to drive lists, offers, and calls.
3. Use a simple fast autodial layer to push the message out.
4. Only after cashflow is visible should we layer in a more institutional customer-relations stack.

### Why this matters
If we build the institutional stack first, we will spend time on governance and architecture before we know which message, offer, and audience actually work. The right move is to prove the message and the list first, then add the heavier systems behind it.

### Suggested stack order
- Phase A: content engine + outbound engine + lead intake
- Phase B: Docassemble-driven list and document generation for specific use cases
- Phase C: Apache/Fineract-style customer and account layer once the business is generating real revenue

### Role of Docassemble
Docassemble is well suited to generate purpose-specific documents and data-driven lists. It can become a practical source layer for:
- targeted outreach lists by purpose
- document packs for specific campaigns
- templated follow-up packets
- purpose-specific intake outputs

This should be treated as an execution layer for content and list generation, not as the first version of the full CRM.

## 5. Compliance baseline

### Required controls
- consent capture and consent state
- opt-out and unsubscribe handling
- do-not-call / do-not-contact enforcement
- data minimization
- retention and deletion workflow
- audit logging for every disposition change

### Standards to align to
- Google Workspace baseline: SSO, MFA, restricted sharing, retention, audit logs
- Microsoft 365 / Entra baseline: MFA, conditional access, RBAC, audit logs, data loss prevention
- Privacy baseline: GDPR, CCPA/CPRA, and telemarketing/contact restrictions as applicable

### Practical rule
If a record lacks valid consent or is marked DNC, it should never enter the outbound queue.

## 5. Implementation phases

### Phase 1 — Foundation
- finalize lead schema and consent fields
- add validation tests around required fields and consent state
- maintain current ledger-based workflow

### Phase 2 — Provider integration
- import Ooma/CSF seed records
- emit outbound-ready queue rows
- record provider dispatch status and dispositions

### Phase 3 — Operator visibility
- add a simple dashboard for lead stage, queue state, and failure reasons
- include replay and diagnostics from the workflow ledger

### Phase 4 — Scale-up
- move to a proper relational store if lead volume grows materially
- add role-based access and export/deletion workflows

## 6. Near-term next actions
1. finalize the lead schema and consent rules
2. add a lead import command that reads Ooma/CSF CSVs
3. add the first outbound disposition states to the ledger/workflow
4. implement a small operator dashboard over lead stage + queue status
5. define the owner and approver roles before we scale the volume

## Recommended decision
Use the existing ledger as the operator control plane, add a lightweight lead database for BD records, and keep Ooma/CSF as the provider-facing outbound system. That gives us a practical path without overbuilding a CRM or losing auditability.
