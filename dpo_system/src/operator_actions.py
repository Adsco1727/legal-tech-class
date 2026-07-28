from datetime import datetime

from . import ledger_io as ledger

OPERATOR_NAME = "DPO"  # adjust if you want multi-operator support


def _now_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


# ---------------------------
# REPO STATE OPERATIONS
# ---------------------------

def register_repo(repo_name: str, repo_slug: str, wave: int, notes: str = ""):
    row = {
        "repo_name": repo_name,
        "repo_slug": repo_slug,
        "wave": wave,
        "enabled": True,
        "last_pull": "",
        "last_commit": "",
        "status": "OK",
        "notes": notes,
    }
    ledger.append_row("REPO_STATE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "register_repo",
        repo_slug,
        status="ok",
        notes=notes,
    )


def update_repo_status(repo_slug: str, status: str, last_commit: str = "", notes: str = ""):
    ledger.validate_enum(ledger.REPO_STATUS, status, "status")
    updates = {
        "status": status,
        "last_commit": last_commit,
        "last_pull": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("REPO_STATE", "repo_slug", repo_slug, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_repo_status",
        repo_slug,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# INGESTION QUEUE OPERATIONS
# ---------------------------

def queue_ingestion_batch(source_repo: str, source_path: str, ingestion_type: str, priority: int = 3, notes: str = ""):
    ledger.validate_enum(ledger.INGESTION_TYPES, ingestion_type, "ingestion_type")
    batch_id = _now_id("ingest")
    row = {
        "batch_id": batch_id,
        "source_repo": source_repo,
        "source_path": source_path,
        "ingestion_type": ingestion_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "notes": notes,
    }
    ledger.append_row("INGESTION_QUEUE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_ingestion_batch",
        batch_id,
        status="ok",
        notes=notes,
    )
    return batch_id


def update_ingestion_status(batch_id: str, status: str, notes: str = ""):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("INGESTION_QUEUE", "batch_id", batch_id, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_ingestion_status",
        batch_id,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# CLAUSE QUEUE OPERATIONS
# ---------------------------

def queue_clause_task(contract_id: str, clause_engine: str, analysis_type: str, priority: int = 3, notes: str = ""):
    ledger.validate_enum(ledger.CLAUSE_ENGINES, clause_engine, "clause_engine")
    ledger.validate_enum(ledger.ANALYSIS_TYPES, analysis_type, "analysis_type")
    task_id = _now_id("clause")
    row = {
        "clause_task_id": task_id,
        "contract_id": contract_id,
        "clause_engine": clause_engine,
        "analysis_type": analysis_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "notes": notes,
    }
    ledger.append_row("CLAUSE_QUEUE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_clause_task",
        task_id,
        status="ok",
        notes=notes,
    )
    return task_id


def update_clause_status(clause_task_id: str, status: str, notes: str = ""):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("CLAUSE_QUEUE", "clause_task_id", clause_task_id, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_clause_status",
        clause_task_id,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# CRM QUEUE OPERATIONS
# ---------------------------

def queue_crm_task(lead_id: str, action_type: str, priority: int = 3, notes: str = ""):
    ledger.validate_enum(ledger.CRM_ACTIONS, action_type, "action_type")
    task_id = _now_id("crm")
    row = {
        "crm_task_id": task_id,
        "lead_id": lead_id,
        "action_type": action_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "notes": notes,
    }
    ledger.append_row("CRM_QUEUE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_crm_task",
        task_id,
        status="ok",
        notes=notes,
    )
    return task_id


def update_crm_status(crm_task_id: str, status: str, notes: str = ""):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("CRM_QUEUE", "crm_task_id", crm_task_id, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_crm_status",
        crm_task_id,
        status="ok",
        notes=f"status={status}",
    )


# ---------------------------
# GOVERNANCE QUEUE OPERATIONS
# ---------------------------

def queue_governance_task(interview_name: str, action_type: str, priority: int = 3, notes: str = ""):
    ledger.validate_enum(ledger.GOV_ACTIONS, action_type, "action_type")
    gov_id = _now_id("gov")
    row = {
        "governance_id": gov_id,
        "interview_name": interview_name,
        "action_type": action_type,
        "priority": priority,
        "status": "pending",
        "created_at": ledger.timestamp(),
        "updated_at": "",
        "operator": OPERATOR_NAME,
        "notes": notes,
    }
    ledger.append_row("GOVERNANCE_QUEUE", row)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "queue_governance_task",
        gov_id,
        status="ok",
        notes=notes,
    )
    return gov_id


def update_governance_status(governance_id: str, status: str, notes: str = ""):
    ledger.validate_enum(ledger.TASK_STATUS, status, "status")
    updates = {
        "status": status,
        "updated_at": ledger.timestamp(),
        "notes": notes,
    }
    ledger.update_row("GOVERNANCE_QUEUE", "governance_id", governance_id, updates)
    ledger.log_operator_action(
        OPERATOR_NAME,
        "operator_actions",
        "update_governance_status",
        governance_id,
        status="ok",
        notes=f"status={status}",
    )
