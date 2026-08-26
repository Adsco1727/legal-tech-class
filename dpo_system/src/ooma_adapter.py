from __future__ import annotations

import csv
import os
from typing import Any

from dpo_system.src.sqlite_manager import DPODatabaseManager


def seed_ooma_contacts_to_db(csv_path: str, db_path: str, operator_id: str = "operator:system") -> dict[str, Any]:
    """
    Ingest Ooma contact lists, normalize them into standard_leads,
    record compliance evidence, and queue only compliant rows for dialer dispatch.
    """
    manager = DPODatabaseManager(db_path)
    manifest: dict[str, Any] = {
        "run_at": None,
        "total_rows": 0,
        "ingested": 0,
        "passed_compliance": 0,
        "queued": 0,
        "rejected": 0,
        "errors": 0,
    }

    ingested_keys: list[str] = []

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Ooma contact CSV not found at: {csv_path}")

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            manifest["total_rows"] += 1
            try:
                entity_name = row.get("Name") or row.get("Company") or "Unknown Contact"
                contact_email = row.get("Email") or None
                contact_phone = row.get("Phone") or row.get("Work Phone") or None
                raw_id = row.get("ID") or row.get("ContactID") or f"ooma-{manifest['total_rows']}"

                dnc_flag = int(row.get("DNC", 0) or 0)
                consent_status = int(row.get("Consent", 0) or 0)

                lead_key = manager.ingest_lead(
                    lane_type="standard",
                    raw_id=raw_id,
                    source_system="OOMA_OFFICE",
                    entity_name=entity_name,
                    email=contact_email,
                    phone=contact_phone,
                    segment="ooma_dialer_list",
                )
                manifest["ingested"] += 1
                ingested_keys.append(lead_key)

                record_id = manager.get_record_id_for_lead_key("standard", lead_key)
                if record_id is None:
                    raise ValueError(f"Lead row not found after ingest: {lead_key}")

                manager.set_lead_compliance_flags("standard", record_id, lead_key, consent_status, dnc_flag)

                is_valid = (consent_status == 1) and (dnc_flag == 0)

                manager.record_compliance_evidence(
                    lane_type="standard",
                    record_id=record_id,
                    lead_key=lead_key,
                    gate_name="ooma_consent_and_dnc_check",
                    passed=is_valid,
                    operator=operator_id,
                    payload={
                        "consent_status": consent_status,
                        "dnc_flag": dnc_flag,
                        "reason": "Passed Ooma pre-screen" if is_valid else "Failed consent/DNC requirements",
                    },
                )

                if is_valid:
                    manifest["passed_compliance"] += 1
                    queued_ok = manager.enqueue_for_sync(
                        lane_type="standard",
                        record_id=record_id,
                        lead_key=lead_key,
                        target_system="ooma_auto_dialer",
                    )
                    if queued_ok:
                        manifest["queued"] += 1
                else:
                    manifest["rejected"] += 1

            except Exception as exc:
                manifest["errors"] += 1
                print(f"[X] Error processing Ooma contact row: {exc}")

    manifest["run_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "manifest": manifest,
        "lead_keys": ingested_keys,
    }
