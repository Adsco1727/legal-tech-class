from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

DB_PATH = "dispatcher.db"


class DPODatabaseManager:
    """Production-safe SQLite control layer for DPO lead intake and dispatch.

    The repository already treats the ledger workbook as the operational audit layer,
    while SQLite is used as the local source-of-truth for lead records and sync
    state. This manager enforces that distinction with explicit lane isolation,
    idempotent queueing, evidence capture, and compliance rejections.
    """

    VALID_LANES = ("standard", "bd")
    VALID_STATES = (
        "raw_ingestion",
        "normalized",
        "compliance_gate",
        "queued",
        "dispatched",
        "synced",
        "rejected",
    )

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _validate_lane(self, lane_type: str) -> str:
        lane = str(lane_type or "").strip().lower()
        if lane not in self.VALID_LANES:
            raise ValueError(f"Unsupported lane_type: {lane_type!r}. Expected one of {self.VALID_LANES}.")
        return lane

    def _table_for_lane(self, lane_type: str) -> str:
        return "standard_leads" if self._validate_lane(lane_type) == "standard" else "bd_leads"

    def _state_is_allowed(self, state: str) -> bool:
        return state in self.VALID_STATES

    def _serialize_payload(self, payload: Any) -> str:
        if payload is None:
            return json.dumps({})
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _initialize_database(self) -> None:
        schema_script = """
        CREATE TABLE IF NOT EXISTS standard_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_key TEXT NOT NULL UNIQUE,
            raw_id TEXT NOT NULL,
            source_system TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            contact_email TEXT,
            contact_phone TEXT,
            segment_category TEXT,
            consent_status INTEGER NOT NULL DEFAULT 0,
            dnc_flag INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'raw_ingestion',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (consent_status IN (0, 1)),
            CHECK (dnc_flag IN (0, 1)),
            CHECK (state IN (
                'raw_ingestion', 'normalized', 'compliance_gate',
                'queued', 'dispatched', 'synced', 'rejected'
            ))
        );

        CREATE TABLE IF NOT EXISTS bd_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_key TEXT NOT NULL UNIQUE,
            raw_id TEXT NOT NULL,
            source_system TEXT NOT NULL DEFAULT 'BD_PLATFORM',
            entity_name TEXT NOT NULL,
            contact_email TEXT,
            contact_phone TEXT,
            bd_metadata_json TEXT,
            consent_status INTEGER NOT NULL DEFAULT 0,
            dnc_flag INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'raw_ingestion',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (consent_status IN (0, 1)),
            CHECK (dnc_flag IN (0, 1)),
            CHECK (state IN (
                'raw_ingestion', 'normalized', 'compliance_gate',
                'queued', 'dispatched', 'synced', 'rejected'
            ))
        );

        CREATE TABLE IF NOT EXISTS evidence_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lane_type TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            lead_key TEXT NOT NULL,
            gate_name TEXT NOT NULL,
            validation_passed INTEGER NOT NULL,
            operator_signoff TEXT NOT NULL,
            evidence_payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (lane_type IN ('standard', 'bd')),
            CHECK (validation_passed IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS crm_sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lane_type TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            lead_key TEXT NOT NULL,
            target_system TEXT NOT NULL,
            sync_status TEXT NOT NULL DEFAULT 'queued',
            synced_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (lane_type, record_id, target_system),
            CHECK (lane_type IN ('standard', 'bd')),
            CHECK (sync_status IN ('queued', 'dispatched', 'synced', 'failed'))
        );

        CREATE TABLE IF NOT EXISTS compliance_rejections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lane_type TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            lead_key TEXT NOT NULL,
            rejection_code TEXT NOT NULL,
            rejection_reason TEXT NOT NULL,
            source_system TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (lane_type IN ('standard', 'bd'))
        );

        CREATE INDEX IF NOT EXISTS idx_standard_lookup ON standard_leads(entity_name, contact_email, contact_phone);
        CREATE INDEX IF NOT EXISTS idx_bd_lookup ON bd_leads(entity_name, contact_email, contact_phone);
        CREATE INDEX IF NOT EXISTS idx_evidence_record ON evidence_blocks(lane_type, record_id, lead_key);
        CREATE INDEX IF NOT EXISTS idx_queue_status ON crm_sync_queue(sync_status, target_system);
        CREATE INDEX IF NOT EXISTS idx_rejection_lookup ON compliance_rejections(lane_type, record_id, rejection_code);
        """

        with self._get_connection() as conn:
            conn.executescript(schema_script)
            conn.commit()

    def _generate_lead_key(self) -> str:
        return f"LEAD-{uuid.uuid4().hex[:10].upper()}"

    def _update_record_state(self, lane_type: str, record_id: int, lead_key: str, next_state: str) -> None:
        if not self._state_is_allowed(next_state):
            raise ValueError(f"Invalid state transition target: {next_state!r}")

        table = self._table_for_lane(lane_type)

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE {table} SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND lead_key = ?",
                (next_state, record_id, lead_key),
            )
            conn.commit()

    def ingest_lead(
        self,
        lane_type: str,
        raw_id: str,
        source_system: str,
        entity_name: str,
        email: str | None = None,
        phone: str | None = None,
        segment: str | None = None,
        bd_metadata: dict[str, Any] | None = None,
    ) -> str:
        lane = self._validate_lane(lane_type)
        lead_key = self._generate_lead_key()
        table = self._table_for_lane(lane)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if lane == "standard":
                cursor.execute(
                    f"""
                    INSERT INTO {table} (
                        lead_key, raw_id, source_system, entity_name,
                        contact_email, contact_phone, segment_category, state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'raw_ingestion')
                    """,
                    (lead_key, str(raw_id), str(source_system), str(entity_name), email, phone, segment),
                )
            else:
                cursor.execute(
                    f"""
                    INSERT INTO {table} (
                        lead_key, raw_id, source_system, entity_name,
                        contact_email, contact_phone, bd_metadata_json, state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'raw_ingestion')
                    """,
                    (
                        lead_key,
                        str(raw_id),
                        str(source_system),
                        str(entity_name),
                        email,
                        phone,
                        self._serialize_payload(bd_metadata or {}),
                    ),
                )
            conn.commit()
            return lead_key

    def get_record_id_for_lead_key(self, lane_type: str, lead_key: str) -> int | None:
        table = self._table_for_lane(lane_type)
        with self._get_connection() as conn:
            row = conn.execute(
                f"SELECT id FROM {table} WHERE lead_key = ? LIMIT 1",
                (lead_key,),
            ).fetchone()
            return int(row["id"]) if row else None

    def get_lead_row(self, lane_type: str, lead_key: str) -> dict[str, Any] | None:
        table = self._table_for_lane(lane_type)
        with self._get_connection() as conn:
            row = conn.execute(f"SELECT * FROM {table} WHERE lead_key = ? LIMIT 1", (lead_key,)).fetchone()
            return dict(row) if row else None

    def set_lead_compliance_flags(
        self,
        lane_type: str,
        record_id: int,
        lead_key: str,
        consent_status: int,
        dnc_flag: int,
    ) -> None:
        lane = self._validate_lane(lane_type)
        table = self._table_for_lane(lane)
        consent_value = int(consent_status)
        dnc_value = int(dnc_flag)

        if consent_value not in (0, 1):
            raise ValueError(f"Invalid consent_status value: {consent_status!r}")
        if dnc_value not in (0, 1):
            raise ValueError(f"Invalid dnc_flag value: {dnc_flag!r}")

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE {table} SET consent_status = ?, dnc_flag = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND lead_key = ?",
                (consent_value, dnc_value, record_id, lead_key),
            )
            conn.commit()

    def update_lead_state(self, lane_type: str, record_id: int, lead_key: str, next_state: str) -> None:
        self._update_record_state(lane_type, record_id, lead_key, next_state)

    def _require_compliance_gate(self, lane_type: str, record_id: int, lead_key: str, target_system: str) -> None:
        table = self._table_for_lane(lane_type)
        with self._get_connection() as conn:
            row = conn.execute(
                f"SELECT state FROM {table} WHERE id = ? AND lead_key = ? LIMIT 1",
                (record_id, lead_key),
            ).fetchone()

        if row is None:
            raise ValueError(f"Lead '{lead_key}' not found for lane '{lane_type}' and record_id {record_id}.")

        if row["state"] != "compliance_gate":
            raise ValueError(
                f"Lead '{lead_key}' in lane '{lane_type}' must be in 'compliance_gate' before queueing to '{target_system}'. "
                f"Current state: '{row['state']}'."
            )

    def queue_sync(self, lane_type: str, record_id: int, target_system: str, lead_key: str) -> None:
        lane = self._validate_lane(lane_type)
        target = str(target_system or "").strip()
        if not target:
            raise ValueError("target_system must not be empty")

        self._require_compliance_gate(lane, record_id, lead_key, target)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO crm_sync_queue (lane_type, record_id, lead_key, target_system, sync_status)
                VALUES (?, ?, ?, ?, 'queued')
                ON CONFLICT(lane_type, record_id, target_system)
                DO UPDATE SET sync_status = 'queued', synced_at = NULL
                """,
                (lane, record_id, lead_key, target),
            )
            conn.commit()

        self._update_record_state(lane, record_id, lead_key, "queued")

    def validate_dispatch_preflight(self, lane_type: str, record_id: int) -> bool:
        """Enforces the hard compliance gate for downstream dispatch."""
        lane = self._validate_lane(lane_type)
        table = self._table_for_lane(lane)

        with self._get_connection() as conn:
            row = conn.execute(
                f"SELECT consent_status, dnc_flag, state FROM {table} WHERE id = ? LIMIT 1",
                (record_id,),
            ).fetchone()

        if row is None:
            return False

        return row["consent_status"] == 1 and row["dnc_flag"] == 0 and row["state"] == "compliance_gate"

    def enqueue_for_sync(self, lane_type: str, record_id: int, lead_key: str, target_system: str) -> bool:
        """Queue a lead only after the hard compliance preflight passes."""
        if not self.validate_dispatch_preflight(lane_type, record_id):
            return False

        self.queue_sync(lane_type, record_id, target_system, lead_key)
        return True

    def get_pending_sync_rows(self, lane_type: str) -> list[dict[str, Any]]:
        lane = self._validate_lane(lane_type)
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM crm_sync_queue WHERE lane_type = ? AND sync_status = 'queued' ORDER BY created_at, id",
                (lane,),
            ).fetchall()
            return [dict(row) for row in rows]

    def mark_sync_dispatched(self, lane_type: str, record_id: int, target_system: str, lead_key: str) -> None:
        lane = self._validate_lane(lane_type)
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE crm_sync_queue SET sync_status = 'dispatched', synced_at = NULL WHERE lane_type = ? AND record_id = ? AND target_system = ? AND lead_key = ?",
                (lane, record_id, target_system, lead_key),
            )
            conn.commit()
        self._update_record_state(lane, record_id, lead_key, "dispatched")

    def mark_sync_synced(self, lane_type: str, record_id: int, target_system: str, lead_key: str) -> None:
        lane = self._validate_lane(lane_type)
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE crm_sync_queue SET sync_status = 'synced', synced_at = CURRENT_TIMESTAMP WHERE lane_type = ? AND record_id = ? AND target_system = ? AND lead_key = ?",
                (lane, record_id, target_system, lead_key),
            )
            conn.commit()
        self._update_record_state(lane, record_id, lead_key, "synced")

    def record_evidence(
        self,
        lane_type: str,
        record_id: int,
        lead_key: str,
        gate_name: str,
        validation_passed: bool,
        operator_signoff: str,
        evidence_payload: dict[str, Any],
    ) -> None:
        lane = self._validate_lane(lane_type)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO evidence_blocks (
                    lane_type, record_id, lead_key, gate_name,
                    validation_passed, operator_signoff, evidence_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lane,
                    record_id,
                    lead_key,
                    str(gate_name),
                    1 if validation_passed else 0,
                    str(operator_signoff),
                    self._serialize_payload(evidence_payload),
                ),
            )
            conn.commit()

        if validation_passed:
            self._update_record_state(lane, record_id, lead_key, "compliance_gate")

    def record_compliance_evidence(
        self,
        lane_type: str,
        record_id: int,
        lead_key: str,
        gate_name: str,
        passed: bool,
        operator: str,
        payload: dict[str, Any],
    ) -> None:
        """Compatibility wrapper for compliance evidence ingestion."""
        self.record_evidence(
            lane_type,
            record_id,
            lead_key,
            gate_name,
            passed,
            operator,
            payload,
        )

    def get_evidence(self, lane_type: str, record_id: int) -> list[dict[str, Any]]:
        lane = self._validate_lane(lane_type)
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM evidence_blocks WHERE lane_type = ? AND record_id = ? ORDER BY created_at DESC, id DESC",
                (lane, record_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_rejection(
        self,
        lane_type: str,
        record_id: int,
        lead_key: str,
        rejection_code: str,
        rejection_reason: str,
        source_system: str,
    ) -> None:
        lane = self._validate_lane(lane_type)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO compliance_rejections (
                    lane_type, record_id, lead_key, rejection_code,
                    rejection_reason, source_system
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (lane, record_id, lead_key, str(rejection_code), str(rejection_reason), str(source_system)),
            )
            conn.commit()

        self._update_record_state(lane, record_id, lead_key, "rejected")

    def get_rejections(self, lane_type: str, record_id: int) -> list[dict[str, Any]]:
        lane = self._validate_lane(lane_type)
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM compliance_rejections WHERE lane_type = ? AND record_id = ? ORDER BY created_at DESC, id DESC",
                (lane, record_id),
            ).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    db = DPODatabaseManager()
    print(f"SQLite manager initialized at: {db.db_path}")
