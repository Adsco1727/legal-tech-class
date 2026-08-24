from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for repo_name in [
    "dpo-ledger-tools",
    "dpo-interview-suite",
    "dpo-integrations",
    "dpo-admin-tools",
    "dpo-casework",
    "dpo-automation-suite",
]:
    repo_path = REPO_ROOT / repo_name
    if str(repo_path) not in sys.path:
        sys.path.insert(0, str(repo_path))

from dpo_admin_tools import process_governance_admin_handoff
from dpo_automation_suite import process_casework_automation_handoff
from dpo_casework import process_admin_case_handoff
from dpo_integrations import process_automation_integration_handoff
from dpo_integrations.integration_ops import IntegrationOps
from dpo_interview_suite import process_governance_handoff
from dpo_ledger_tools import LedgerAPI

from dpo_system.src.workflow_replay import build_workflow_replay


def test_full_workflow_loop_runs_through_all_repos(tmp_path: Path):
    ledger_path = tmp_path / "operator_ledger.xlsx"
    ledger = LedgerAPI(ledger_path)
    ledger.ensure_exists()

    integration_ops = IntegrationOps(ledger)
    initial_handoff = integration_ops.activate_ingestion_handoff(
        {"task_id": "WF-001", "action": "sync", "source_repo": "dpo-integrations"},
        ledger_path,
    )
    assert initial_handoff["governance_id"] == "WF-001"

    interview_result = process_governance_handoff(ledger_path, "WF-001")
    assert interview_result["status"] == "running"

    admin_result = process_governance_admin_handoff(ledger_path, "WF-001")
    assert admin_result["status"] == "running"

    casework_result = process_admin_case_handoff(ledger_path, "WF-001")
    assert casework_result["status"] == "pending"

    clause_rows = ledger.read_rows("CLAUSE_QUEUE")
    assert len(clause_rows) == 1
    assert clause_rows[0]["clause_task_id"] == "WF-001"

    automation_result = process_casework_automation_handoff(ledger_path, "WF-001")
    assert automation_result["status"] == "pending"

    crm_rows = ledger.read_rows("CRM_QUEUE")
    assert len(crm_rows) == 1
    assert crm_rows[0]["crm_task_id"] == "WF-001"

    feedback_result = process_automation_integration_handoff(ledger_path, "WF-001")
    assert feedback_result["status"] == "pending"

    governance_rows = ledger.read_rows("GOVERNANCE_QUEUE")
    assert len(governance_rows) == 2
    assert governance_rows[-1]["governance_id"] == "WF-001"
    assert governance_rows[-1]["interview_name"] == "automation-handoff"


def test_build_workflow_replay_reconstructs_operator_trace(tmp_path: Path):
    ledger_path = tmp_path / "operator_ledger.xlsx"
    ledger = LedgerAPI(ledger_path)
    ledger.ensure_exists()

    integration_ops = IntegrationOps(ledger)
    integration_ops.activate_ingestion_handoff(
        {"task_id": "WF-002", "action": "sync", "source_repo": "dpo-integrations"},
        ledger_path,
    )
    process_governance_handoff(ledger_path, "WF-002")
    process_governance_admin_handoff(ledger_path, "WF-002")
    process_admin_case_handoff(ledger_path, "WF-002")
    process_casework_automation_handoff(ledger_path, "WF-002")
    process_automation_integration_handoff(ledger_path, "WF-002")

    replay = build_workflow_replay(ledger_path, "WF-002")

    assert replay["workflow_id"] == "WF-002"
    assert replay["total_hops"] >= 3
    assert replay["hop_chain"] == (
        "dpo-integrations → dpo-interview-suite → dpo-admin-tools → "
        "dpo-casework → dpo-automation-suite → dpo-integrations"
    )
