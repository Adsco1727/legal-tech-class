from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
import urllib.error
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from typing import Any

from . import ledger_io as ledger
from . import operator_actions as ops
from .bd_standardizer import convert_bd_csvs_to_standard, write_standard_exports
from .csf_ingest import ingest_csf_seed
from .db_outbound_builder import build_outbound_rows_from_db_exports, write_outbound_batches
from .docassemble_workflow import approved_docassemble_workflow
from .list_builder import export_provider_ready_outbound_list
from .ooma_export_pack import export_ooma_batch_from_db_csv
from .ooma_intake_pack import process_ooma_csv_file, write_json, write_rejections_csv
from .ooma_dialer import build_ooma_autodialer_plan, export_provider_ready_csv
from .preflight_validator import (
    persist_record_id_registry,
    validate_csf_seed_batch,
    write_preflight_report,
)
from .regd_scraper_pack import run_regd_scrape

REQUIRED_SHEETS = [
    "REPO_STATE",
    "INGESTION_QUEUE",
    "CLAUSE_QUEUE",
    "CRM_QUEUE",
    "GOVERNANCE_QUEUE",
    "OPERATOR_LOG",
]

NOTEBOOK_FILES = [
    "dpo_system/notebooks/clause-intelligence-console.ipynb",
    "dpo_system/notebooks/law-ingestion-console.ipynb",
    "dpo_system/notebooks/docassemble-governance-console.ipynb",
    "dpo_system/notebooks/orchestrator-console.ipynb",
]


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_repo_manifest() -> Path:
    return _root() / "dpo_system" / "config" / "repo_wave_manifest.csv"


def _default_dialer_seed() -> Path:
    return _root() / "dpo_system" / "config" / "dialer_seed.csv"


def _default_registry_path() -> Path:
    return _root() / "dpo_system" / "state" / "outbound_record_id_registry.txt"


def _default_preflight_report(seed_path: Path) -> Path:
    safe_name = seed_path.stem or "seed"
    return _root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "preflight" / f"{safe_name}_preflight_report.json"


def _default_gate_b_response_path() -> Path:
    return _root() / "dpo_system" / "vendor" / "ooma" / "ooma_response_fields.json"


def _default_gate_b_template_path() -> Path:
    return _root() / "dpo_system" / "vendor" / "ooma" / "ooma_response_fields_template.json"


def _to_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def _slug_from_url(repo_url: str) -> str:
    raw = repo_url.strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        path = urlparse(raw).path.strip("/")
        return path[:-4] if path.endswith(".git") else path
    return raw[:-4] if raw.endswith(".git") else raw


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_repo_manifest(path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    repos_by_slug: dict[str, dict[str, Any]] = {}
    ordered_slugs: list[str] = []
    for row in rows:
        repo_url = (row.get("repo_url") or "").strip()
        slug = (row.get("repo_slug") or "").strip() or _slug_from_url(repo_url)
        name = (row.get("repo_name") or "").strip()
        if not slug:
            continue
        if slug not in repos_by_slug:
            ordered_slugs.append(slug)
        repos_by_slug[slug] = {
            "repo_name": name or slug.split("/")[-1],
            "repo_slug": slug,
            "repo_url": repo_url,
            "branch": (row.get("branch") or "main").strip() or "main",
            "wave": int((row.get("wave") or "4").strip()),
            "enabled": _to_bool(
                row.get("enabled")
                or row.get("install_enabled")
                or "false"
            ),
            "github_enabled": _to_bool(
                row.get("github_enabled")
                or row.get("gh_enabled")
                or "true"
            ),
            "ingestion_type": (row.get("ingestion_type") or "custom").strip() or "custom",
            "source_path": (row.get("source_path") or "").strip(),
            "priority": int((row.get("priority") or "3").strip()),
            "notes": (row.get("notes") or "").strip(),
        }
    return [repos_by_slug[slug] for slug in ordered_slugs]


def _gh_latest_commit(repo_slug: str, timeout_sec: int = 12) -> tuple[bool, str, str]:
    url = f"https://api.github.com/repos/{repo_slug}/commits?per_page=1"
    headers = {"User-Agent": "dpo-phase-runner"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            if not payload:
                return False, "", "no commits returned"
            sha = str(payload[0].get("sha") or "").strip()
            if not sha:
                return False, "", "missing commit sha"
            return True, sha, ""
    except urllib.error.HTTPError as exc:
        return False, "", f"http {exc.code}"
    except Exception as exc:
        return False, "", str(exc)


def check_github(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for repo in repos:
        if not repo.get("github_enabled", True):
            results.append(
                {
                    "repo_slug": repo["repo_slug"],
                    "ok": True,
                    "latest_commit": "",
                    "error": "github check skipped",
                }
            )
            continue
        ok, sha, error = _gh_latest_commit(repo["repo_slug"])
        results.append(
            {
                "repo_slug": repo["repo_slug"],
                "ok": ok,
                "latest_commit": sha,
                "error": error,
            }
        )
    return results


def sync_repo_state(repos: list[dict[str, Any]], apply: bool = False) -> list[dict[str, Any]]:
    existing_rows = ledger.read_rows("REPO_STATE")
    existing_by_slug = {str(r.get("repo_slug")).strip(): r for r in existing_rows}
    planned: list[dict[str, Any]] = []

    for repo in repos:
        slug = repo["repo_slug"]
        prior = existing_by_slug.get(slug)

        if prior is None:
            action = "create"
            planned.append({"action": action, "repo_slug": slug, "wave": repo["wave"], "enabled": repo["enabled"]})
            if apply:
                ledger.append_row(
                    "REPO_STATE",
                    {
                        "repo_name": repo["repo_name"],
                        "repo_slug": slug,
                        "wave": repo["wave"],
                        "enabled": repo["enabled"],
                        "last_pull": "",
                        "last_commit": "",
                        "status": "OK",
                        "notes": repo["notes"],
                    },
                )
                ledger.log_operator_action("DPO", "phase_runner", "create_repo", slug, status="ok", notes=repo["notes"])
            continue

        updates = {
            "repo_name": repo["repo_name"],
            "wave": repo["wave"],
            "enabled": repo["enabled"],
            "notes": repo["notes"] or str(prior.get("notes") or ""),
        }
        action = "update"
        planned.append({"action": action, "repo_slug": slug, "wave": repo["wave"], "enabled": repo["enabled"]})
        if apply:
            ledger.update_row("REPO_STATE", "repo_slug", slug, updates)
            ledger.log_operator_action("DPO", "phase_runner", "update_repo", slug, status="ok", notes=updates["notes"])

    return planned


def queue_notebook_ingestion(repos: list[dict[str, Any]], apply: bool = False) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    for repo in repos:
        if not repo["enabled"]:
            continue
        notes = f"wave={repo['wave']} | seeded from repo manifest"
        planned.append(
            {
                "repo_slug": repo["repo_slug"],
                "ingestion_type": repo["ingestion_type"],
                "source_path": repo["source_path"],
                "priority": repo["priority"],
            }
        )
        if apply:
            ops.queue_ingestion_batch(
                source_repo=repo["repo_slug"],
                source_path=repo["source_path"],
                ingestion_type=repo["ingestion_type"],
                priority=repo["priority"],
                notes=notes,
            )
    return planned


def queue_dialer_tasks(path: Path, apply: bool = False) -> list[dict[str, Any]]:
    plan = build_ooma_autodialer_plan(path)
    planned: list[dict[str, Any]] = []
    for row in plan:
        record_id = (row.get("record_id") or "").strip()
        phone_number = (row.get("phone_number") or "").strip()
        campaign_name = (row.get("campaign_name") or "").strip()
        source_system = (row.get("source_system") or "Ooma/CSF").strip() or "Ooma/CSF"
        notes = (row.get("notes") or "").strip()
        list_name = (row.get("list_name") or "").strip()
        outreach_purpose = (row.get("outreach_purpose") or "").strip()
        list_source = (row.get("list_source") or "").strip()
        outbound_status = (row.get("outbound_status") or "planned").strip() or "planned"
        if not record_id or not phone_number:
            continue
        planned.append(
            {
                "record_id": record_id,
                "phone_number": phone_number,
                "campaign_name": campaign_name,
                "source_system": source_system,
                "notes": notes,
                "list_name": list_name,
                "outreach_purpose": outreach_purpose,
                "list_source": list_source,
                "outbound_status": outbound_status,
            }
        )
        if apply:
            ops.queue_governance_task(
                interview_name="ooma-autodialer",
                action_type="validate",
                priority=3,
                notes=(
                    f"record_id={record_id} | campaign={campaign_name} | phone={phone_number} | source={source_system}"
                    f" | list={list_name} | purpose={outreach_purpose} | list_source={list_source}"
                ),
                workflow_id=f"dialer-{record_id}",
                origin_repo="dpo-system",
                hop_count=1,
                list_name=list_name,
                outreach_purpose=outreach_purpose,
                list_source=list_source,
                outbound_status=outbound_status,
            )
    return planned


def queue_regd_enrichment_tasks(
    targets_csv_path: Path,
    ledger_path: Path | None = None,
    default_priority: int = 1,
) -> dict[str, Any]:
    with targets_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]

    queued: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    existing_crm_rows = ledger.read_rows("CRM_QUEUE", path=ledger_path)
    existing_pairs = {
        (
            str(item.get("lead_id") or "").strip(),
            str(item.get("action_type") or "").strip().lower(),
        )
        for item in existing_crm_rows
    }

    for index, row in enumerate(rows, start=2):
        lead_id = str(row.get("lead_id") or "").strip()
        if not lead_id:
            skipped.append({"row_number": index, "reason": "missing_lead_id"})
            continue

        action_type = str(row.get("action_type") or "enrich").strip() or "enrich"
        pair_key = (lead_id, action_type.lower())
        if pair_key in existing_pairs:
            skipped.append(
                {
                    "row_number": index,
                    "lead_id": lead_id,
                    "action_type": action_type,
                    "reason": "duplicate_lead_action_pair",
                }
            )
            continue

        priority_raw = str(row.get("priority") or "").strip()
        try:
            priority = int(priority_raw) if priority_raw else int(default_priority)
        except ValueError:
            priority = int(default_priority)

        notes = str(row.get("notes") or "").strip()
        task_id = ops.queue_crm_task(
            lead_id=lead_id,
            action_type=action_type,
            priority=priority,
            notes=notes,
            ledger_path=ledger_path,
        )
        queued.append(
            {
                "row_number": index,
                "crm_task_id": task_id,
                "lead_id": lead_id,
                "action_type": action_type,
                "priority": priority,
            }
        )
        existing_pairs.add(pair_key)

    return {
        "source": str(targets_csv_path),
        "queued_count": len(queued),
        "skipped_count": len(skipped),
        "queued": queued,
        "skipped": skipped,
    }


def d_base_health() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": True, "missing_sheets": [], "header_mismatch": []}
    wb = ledger.safe_load_workbook()
    sheetnames = set(wb.sheetnames)

    missing = [name for name in REQUIRED_SHEETS if name not in sheetnames]
    if missing:
        result["ok"] = False
        result["missing_sheets"] = missing

    for name in REQUIRED_SHEETS:
        if name not in sheetnames:
            continue
        ws = wb[name]
        expected = ledger.SHEET_HEADERS[name]
        actual = [cell.value for cell in ws[1]]
        if actual != expected:
            result["ok"] = False
            result["header_mismatch"].append(name)

    return result


def notebook_health() -> dict[str, Any]:
    missing: list[str] = []
    for rel in NOTEBOOK_FILES:
        if not (_root() / rel).exists():
            missing.append(rel)
    return {"ok": len(missing) == 0, "missing": missing, "total": len(NOTEBOOK_FILES)}


def run_status(repo_manifest: Path, dialer_seed: Path) -> dict[str, Any]:
    repos = load_repo_manifest(repo_manifest)
    return {
        "repos_total": len(repos),
        "repos_enabled": sum(1 for r in repos if r["enabled"]),
        "d_base": d_base_health(),
        "notebooks": notebook_health(),
        "github": check_github(repos),
        "ingestion_plan": queue_notebook_ingestion(repos, apply=False),
        "dialer_plan": queue_dialer_tasks(dialer_seed, apply=False),
    }


def run_preflight(
    seed_path: Path,
    expected_rows: int,
    registry_path: Path,
    report_path: Path,
) -> tuple[dict[str, Any], list[str], Path]:
    report, record_ids = validate_csf_seed_batch(
        seed_path=seed_path,
        expected_rows=expected_rows,
        registry_path=registry_path,
    )
    written_report = write_preflight_report(report, report_path)
    return report, record_ids, written_report


def run_gate_a_readiness(report_path: Path | None = None) -> tuple[dict[str, Any], Path]:
    """Run Gate A readiness checks and produce a deterministic report."""
    vendor_files = [
        _root() / "dpo_system" / "vendor" / "ooma" / "ooma_vendor_email_draft.md",
        _root() / "dpo_system" / "vendor" / "ooma" / "ooma_sample_outbound_pilot.csv",
        _root() / "dpo_system" / "vendor" / "ooma" / "ooma_capability_checklist.md",
    ]
    missing_vendor = [str(path) for path in vendor_files if not path.exists()]

    report: dict[str, Any] = {
        "gate": "A",
        "status": "FAIL",
        "checks": [
            {
                "name": "vendor_packet_present",
                "passed": len(missing_vendor) == 0,
                "missing": missing_vendor,
            }
        ],
        "synthetic": {},
    }

    with tempfile.TemporaryDirectory(prefix="dpo_gate_a_") as tmp_dir_raw:
        tmp_dir = Path(tmp_dir_raw)
        leads_path = tmp_dir / "google_standard_export.csv"
        workflow_path = tmp_dir / "bd_workflow_export.csv"
        output_dir = tmp_dir / "outbound_batches"
        registry_path = tmp_dir / "registry.txt"
        preflight_path = tmp_dir / "preflight_report.json"

        with leads_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["lead_id", "phone_number", "full_name", "email", "address", "notes", "source_system", "campaign_name"],
            )
            writer.writeheader()
            for index in range(1, 501):
                writer.writerow(
                    {
                        "lead_id": f"rec-{index:06d}",
                        "phone_number": f"1416555{index:04d}",
                        "full_name": f"Lead {index}",
                        "email": f"lead{index}@example.com",
                        "address": f"{index} Main St",
                        "notes": "gate a synthetic",
                        "source_system": "google_db",
                        "campaign_name": "csf_launch",
                    }
                )

        with workflow_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["record_id", "list_name", "outreach_purpose", "list_source", "outbound_status", "workflow_notes"],
            )
            writer.writeheader()
            for index in range(1, 501):
                writer.writerow(
                    {
                        "record_id": f"rec-{index:06d}",
                        "list_name": "csf_launch",
                        "outreach_purpose": "onboarding",
                        "list_source": "bd32",
                        "outbound_status": "planned",
                        "workflow_notes": "gate a synthetic",
                    }
                )

        rows = build_outbound_rows_from_db_exports(leads_path, workflow_path)
        manifest = write_outbound_batches(rows, output_dir, batch_size=500, file_prefix="gate_a_batch")
        batch_file = output_dir / "gate_a_batch_001_of_001.csv"
        preflight_report, _, _ = run_preflight(batch_file, 500, registry_path, preflight_path)

        synthetic_ok = (
            manifest.get("total_rows") == 500
            and manifest.get("total_batches") == 1
            and preflight_report.get("status") == "PASS"
        )
        report["synthetic"] = {
            "rows_built": manifest.get("total_rows", 0),
            "batches": manifest.get("total_batches", 0),
            "preflight_status": preflight_report.get("status", "FAIL"),
        }
        report["checks"].append({"name": "synthetic_500_build_and_preflight", "passed": synthetic_ok})

    overall_ok = all(bool(check.get("passed")) for check in report["checks"])
    report["status"] = "PASS" if overall_ok else "FAIL"

    destination = report_path or (_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "gate_a" / "gate_a_readiness_report.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report, destination


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "approved"}
    return False


def run_gate_b_readiness(
    response_path: Path | None = None,
    report_path: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    """Run Gate B readiness checks from Ooma response fields."""
    response_file = response_path or _default_gate_b_response_path()
    template_file = _default_gate_b_template_path()

    required_fields = [
        "csv_import_supported",
        "required_optional_fields_confirmed",
        "phone_format_rule_confirmed",
        "identifier_roundtrip_confirmed",
        "custom_fields_behavior_confirmed",
        "upload_limits_confirmed",
        "dedupe_behavior_confirmed",
        "append_replace_behavior_confirmed",
        "disposition_export_confirmed",
        "pilot_10_row_approved",
        "pilot_25_to_50_row_approved",
    ]
    allowed_decisions = {"accepted_as_is", "accepted_with_changes", "not_accepted"}

    report: dict[str, Any] = {
        "gate": "B",
        "status": "FAIL",
        "response_path": str(response_file),
        "template_path": str(template_file),
        "checks": [],
        "missing_fields": [],
        "decision": "",
        "notes": "",
    }

    if not response_file.exists():
        report["checks"].append(
            {
                "name": "response_file_present",
                "passed": False,
                "missing": str(response_file),
            }
        )
        destination = report_path or (_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "gate_b" / "gate_b_readiness_report.json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report, destination

    try:
        payload = json.loads(response_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("response file must contain a JSON object")
    except Exception as exc:
        report["checks"].append(
            {
                "name": "response_file_valid_json",
                "passed": False,
                "error": str(exc),
            }
        )
        destination = report_path or (_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "gate_b" / "gate_b_readiness_report.json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report, destination

    report["checks"].append({"name": "response_file_present", "passed": True})
    report["checks"].append({"name": "response_file_valid_json", "passed": True})

    field_results: list[dict[str, Any]] = []
    missing_fields: list[str] = []
    for field in required_fields:
        raw_value = payload.get(field)
        present = field in payload
        passed = present and _truthy(raw_value)
        field_results.append({"field": field, "present": present, "passed": passed, "value": raw_value})
        if not present:
            missing_fields.append(field)

    report["checks"].append(
        {
            "name": "required_response_fields",
            "passed": all(item["passed"] for item in field_results),
            "fields": field_results,
        }
    )
    report["missing_fields"] = missing_fields

    decision = str(payload.get("decision") or "").strip().lower()
    decision_ok = decision in allowed_decisions and decision != "not_accepted"
    report["decision"] = decision
    report["checks"].append(
        {
            "name": "decision_state",
            "passed": decision_ok,
            "allowed": sorted(allowed_decisions),
            "value": decision,
        }
    )

    report["notes"] = str(payload.get("notes") or "").strip()

    overall_ok = all(bool(check.get("passed")) for check in report["checks"])
    report["status"] = "PASS" if overall_ok else "FAIL"

    destination = report_path or (_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "gate_b" / "gate_b_readiness_report.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report, destination


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DPO phase runner for repos, GH checks, D-base, notebooks, and dialer seed.")
    parser.add_argument("--repo-manifest", default=str(_default_repo_manifest()))
    parser.add_argument("--dialer-seed", default=str(_default_dialer_seed()))

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")

    p_sync = sub.add_parser("sync-repos")
    p_sync.add_argument("--apply", action="store_true")

    sub.add_parser("check-gh")

    p_ing = sub.add_parser("queue-notebooks")
    p_ing.add_argument("--apply", action="store_true")

    p_dial = sub.add_parser("queue-dialer")
    p_dial.add_argument("--apply", action="store_true")

    p_export = sub.add_parser("export-provider-csv")
    p_export.add_argument("--output", default=str(_root() / "dpo_system" / "config" / "provider_ready_export.csv"))

    p_ooma_batch = sub.add_parser("export-ooma-batch")
    p_ooma_batch.add_argument("db_csv_path")
    p_ooma_batch.add_argument("--output", default=str(_root() / "dpo_system" / "config" / "ooma" / "ooma_batch_001.csv"))
    p_ooma_batch.add_argument("--batch-size", type=int, default=500)
    p_ooma_batch.add_argument("--watermark", default=str(_root() / "dpo_system" / "state" / "ooma_export_watermark.json"))

    p_ooma_validate = sub.add_parser("validate-ooma-csv")
    p_ooma_validate.add_argument("csv_path")
    p_ooma_validate.add_argument("--report", default=str(_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "ooma" / "ooma_intake_report.json"))
    p_ooma_validate.add_argument("--rejections", default=str(_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "ooma" / "ooma_rejections.csv"))

    p_export_list = sub.add_parser("export-provider-list")
    p_export_list.add_argument("list_name")
    p_export_list.add_argument("--output", default=str(_root() / "dpo_system" / "config" / "provider_ready_outbound.csv"))
    p_export_list.add_argument("--ledger", default=str(_root() / "dpo_system" / "operator_ledger.xlsx"))

    p_ingest = sub.add_parser("ingest-csf")
    p_ingest.add_argument("seed_path")
    p_ingest.add_argument("--ledger", default=str(_root() / "dpo_system" / "operator_ledger.xlsx"))

    p_build_db = sub.add_parser("build-db-outbound")
    p_build_db.add_argument("leads_path")
    p_build_db.add_argument("workflow_path")
    p_build_db.add_argument("--output-dir", default=str(_root() / "dpo_system" / "config" / "outbound_batches"))
    p_build_db.add_argument("--batch-size", type=int, default=500)
    p_build_db.add_argument("--file-prefix", default="csf_batch")
    p_build_db.add_argument("--default-list-source", default="google_bd_db")
    p_build_db.add_argument("--default-source-system", default="google_db")

    p_convert_bd = sub.add_parser("convert-bd-standard")
    p_convert_bd.add_argument("input_csv", nargs="+")
    p_convert_bd.add_argument(
        "--leads-out",
        default=str(_root() / "dpo_system" / "config" / "exports" / "google_standard_export_live.csv"),
    )
    p_convert_bd.add_argument(
        "--workflow-out",
        default=str(_root() / "dpo_system" / "config" / "exports" / "bd_workflow_export_live.csv"),
    )
    p_convert_bd.add_argument("--list-name", default="dr_dentist_bd")
    p_convert_bd.add_argument("--outreach-purpose", default="onboarding")
    p_convert_bd.add_argument("--list-source", default="bd_live_db")
    p_convert_bd.add_argument("--source-system", default="bd_db")
    p_convert_bd.add_argument("--campaign-name", default="csf_launch")
    p_convert_bd.add_argument("--outbound-status", default="planned")

    p_preflight = sub.add_parser("preflight-csf")
    p_preflight.add_argument("seed_path")
    p_preflight.add_argument("--expected-rows", type=int, default=500)
    p_preflight.add_argument("--registry", default=str(_default_registry_path()))
    p_preflight.add_argument("--report")

    p_standard = sub.add_parser("run-standard-pipeline")
    p_standard.add_argument("leads_path")
    p_standard.add_argument("workflow_path")
    p_standard.add_argument("--output-dir", default=str(_root() / "dpo_system" / "config" / "outbound_batches"))
    p_standard.add_argument("--batch-size", type=int, default=500)
    p_standard.add_argument("--registry", default=str(_default_registry_path()))
    p_standard.add_argument("--report-dir", default=str(_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "preflight"))
    p_standard.add_argument("--file-prefix", default="csf_batch")
    p_standard.add_argument("--default-list-source", default="google_bd_db")
    p_standard.add_argument("--default-source-system", default="google_db")

    p_ingest_batch = sub.add_parser("ingest-csf-batch")
    p_ingest_batch.add_argument("seed_path")
    p_ingest_batch.add_argument("--ledger", default=str(_root() / "dpo_system" / "operator_ledger.xlsx"))
    p_ingest_batch.add_argument("--expected-rows", type=int, default=500)
    p_ingest_batch.add_argument("--registry", default=str(_default_registry_path()))
    p_ingest_batch.add_argument("--report")

    p_disposition = sub.add_parser("record-disposition")
    p_disposition.add_argument("workflow_id")
    p_disposition.add_argument("status")
    p_disposition.add_argument("--notes", default="")
    p_disposition.add_argument("--ledger", default=str(_root() / "dpo_system" / "operator_ledger.xlsx"))

    p_gate_a = sub.add_parser("gate-a-readiness")
    p_gate_a.add_argument("--report")

    p_gate_b = sub.add_parser("gate-b-readiness")
    p_gate_b.add_argument("--response", default=str(_default_gate_b_response_path()))
    p_gate_b.add_argument("--report")

    p_docassemble = sub.add_parser("run-docassemble-workflow")
    p_docassemble.add_argument("payload_path")
    p_docassemble.add_argument("--operator-id", default="DPO")
    p_docassemble.add_argument("--result-path", default=str(_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "docassemble" / "docassemble_result.json"))

    p_regd = sub.add_parser("scrape-regd")
    p_regd.add_argument("--output-dir", default=str(_root() / "dpo_system" / "evidence" / "EXECUTED_EVIDENCE" / "regd"))
    p_regd.add_argument("--user-agent", default="DPORegDScraper/1.0 (operations@directprivateoffers.net)")
    p_regd.add_argument("--max-entries", type=int, default=200)
    p_regd.add_argument("--page-size", type=int, default=100)

    p_queue_regd = sub.add_parser("queue-regd-enrichment")
    p_queue_regd.add_argument("targets_csv_path")
    p_queue_regd.add_argument("--ledger", default=str(_root() / "dpo_system" / "operator_ledger.xlsx"))
    p_queue_regd.add_argument("--default-priority", type=int, default=1)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    repo_manifest = Path(args.repo_manifest)
    dialer_seed = Path(args.dialer_seed)
    repos = load_repo_manifest(repo_manifest)

    if args.command == "status":
        print(json.dumps(run_status(repo_manifest, dialer_seed), indent=2))
        return 0

    if args.command == "sync-repos":
        plan = sync_repo_state(repos, apply=bool(args.apply))
        print(json.dumps({"apply": bool(args.apply), "sync_plan": plan}, indent=2))
        return 0

    if args.command == "check-gh":
        print(json.dumps({"github": check_github(repos)}, indent=2))
        return 0

    if args.command == "queue-notebooks":
        plan = queue_notebook_ingestion(repos, apply=bool(args.apply))
        print(json.dumps({"apply": bool(args.apply), "queue_notebooks": plan}, indent=2))
        return 0

    if args.command == "queue-dialer":
        plan = queue_dialer_tasks(dialer_seed, apply=bool(args.apply))
        print(json.dumps({"apply": bool(args.apply), "queue_dialer": plan}, indent=2))
        return 0

    if args.command == "export-provider-csv":
        output_path = Path(args.output)
        export_provider_ready_csv(dialer_seed, output_path)
        print(json.dumps({"output": str(output_path), "rows_written": 0}, indent=2))
        return 0

    if args.command == "export-ooma-batch":
        result = export_ooma_batch_from_db_csv(
            db_csv_path=args.db_csv_path,
            output_csv_path=args.output,
            batch_size=int(args.batch_size),
            watermark_path=args.watermark,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "validate-ooma-csv":
        result = process_ooma_csv_file(args.csv_path)
        report_path = write_json(args.report, result)
        rejection_path = write_rejections_csv(args.rejections, result["rejected"])
        print(
            json.dumps(
                {
                    "status": "PASS" if result["summary"]["rejected_count"] == 0 else "FAIL",
                    "summary": result["summary"],
                    "report": str(report_path),
                    "rejections": str(rejection_path),
                },
                indent=2,
            )
        )
        return 0 if result["summary"]["rejected_count"] == 0 else 1

    if args.command == "export-provider-list":
        output_path = Path(args.output)
        export_provider_ready_outbound_list(args.list_name, output_path, ledger_path=args.ledger)
        print(json.dumps({"list_name": args.list_name, "output": str(output_path)}, indent=2))
        return 0

    if args.command == "ingest-csf":
        ingested = ingest_csf_seed(args.seed_path, args.ledger)
        print(json.dumps({"seed_path": args.seed_path, "rows_ingested": len(ingested)}, indent=2))
        return 0

    if args.command == "build-db-outbound":
        rows = build_outbound_rows_from_db_exports(
            args.leads_path,
            args.workflow_path,
            default_list_source=args.default_list_source,
            default_source_system=args.default_source_system,
        )
        manifest = write_outbound_batches(
            rows,
            args.output_dir,
            batch_size=int(args.batch_size),
            file_prefix=args.file_prefix,
        )
        print(
            json.dumps(
                {
                    "status": "BUILT",
                    "rows_built": manifest["total_rows"],
                    "total_batches": manifest["total_batches"],
                    "batch_counts": manifest["batch_counts"],
                    "manifest_path": manifest["manifest_path"],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "convert-bd-standard":
        leads_rows, workflow_rows, stats = convert_bd_csvs_to_standard(
            [Path(path) for path in args.input_csv],
            list_name=args.list_name,
            outreach_purpose=args.outreach_purpose,
            list_source=args.list_source,
            source_system=args.source_system,
            campaign_name=args.campaign_name,
            outbound_status=args.outbound_status,
        )
        leads_out = Path(args.leads_out)
        workflow_out = Path(args.workflow_out)
        write_standard_exports(
            leads_rows,
            workflow_rows,
            leads_output=leads_out,
            workflow_output=workflow_out,
        )
        print(
            json.dumps(
                {
                    "status": "STANDARDIZED",
                    "inputs": args.input_csv,
                    "leads_out": str(leads_out),
                    "workflow_out": str(workflow_out),
                    "stats": stats,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "preflight-csf":
        seed_path = Path(args.seed_path)
        report_path = Path(args.report) if args.report else _default_preflight_report(seed_path)
        report, _, written_report = run_preflight(
            seed_path=seed_path,
            expected_rows=int(args.expected_rows),
            registry_path=Path(args.registry),
            report_path=report_path,
        )
        print(
            json.dumps(
                {
                    "seed_path": str(seed_path),
                    "status": report["status"],
                    "summary": report.get("summary", {}),
                    "report": str(written_report),
                },
                indent=2,
            )
        )
        return 0 if report["status"] == "PASS" else 1

    if args.command == "run-standard-pipeline":
        rows = build_outbound_rows_from_db_exports(
            args.leads_path,
            args.workflow_path,
            default_list_source=args.default_list_source,
            default_source_system=args.default_source_system,
        )
        manifest = write_outbound_batches(
            rows,
            args.output_dir,
            batch_size=int(args.batch_size),
            file_prefix=args.file_prefix,
        )
        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        failures: list[str] = []

        for file_name in manifest.get("files", []):
            seed_path = Path(file_name)
            report_path = report_dir / f"{seed_path.stem}_preflight_report.json"
            report, _, _ = run_preflight(
                seed_path=seed_path,
                expected_rows=int(args.batch_size),
                registry_path=Path(args.registry),
                report_path=report_path,
            )
            if report["status"] != "PASS":
                failures.append(str(seed_path))

        print(
            json.dumps(
                {
                    "status": "PASS" if not failures else "FAIL",
                    "rows_built": manifest["total_rows"],
                    "total_batches": manifest["total_batches"],
                    "batch_counts": manifest["batch_counts"],
                    "manifest_path": manifest["manifest_path"],
                    "report_dir": str(report_dir),
                    "failures": failures,
                },
                indent=2,
            )
        )
        return 0 if not failures else 1

    if args.command == "ingest-csf-batch":
        seed_path = Path(args.seed_path)
        report_path = Path(args.report) if args.report else _default_preflight_report(seed_path)
        report, record_ids, written_report = run_preflight(
            seed_path=seed_path,
            expected_rows=int(args.expected_rows),
            registry_path=Path(args.registry),
            report_path=report_path,
        )
        if report["status"] != "PASS":
            print(
                json.dumps(
                    {
                        "seed_path": str(seed_path),
                        "status": "BLOCKED",
                        "reason": "preflight_failed",
                        "summary": report.get("summary", {}),
                        "report": str(written_report),
                    },
                    indent=2,
                )
            )
            return 1

        ingested = ingest_csf_seed(args.seed_path, args.ledger)
        persisted_registry = persist_record_id_registry(record_ids, Path(args.registry))
        print(
            json.dumps(
                {
                    "seed_path": str(seed_path),
                    "status": "INGESTED",
                    "rows_ingested": len(ingested),
                    "report": str(written_report),
                    "registry": str(persisted_registry),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "record-disposition":
        result = ops.record_outbound_disposition(args.workflow_id, args.status, notes=args.notes, ledger_path=args.ledger)
        print(json.dumps({"workflow_id": args.workflow_id, "disposition": args.status, "hop": result}, indent=2))
        return 0

    if args.command == "gate-a-readiness":
        report, destination = run_gate_a_readiness(Path(args.report) if args.report else None)
        print(json.dumps({"status": report["status"], "report": str(destination), "checks": report["checks"]}, indent=2))
        return 0 if report["status"] == "PASS" else 1

    if args.command == "gate-b-readiness":
        report, destination = run_gate_b_readiness(
            response_path=Path(args.response) if args.response else None,
            report_path=Path(args.report) if args.report else None,
        )
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "report": str(destination),
                    "decision": report.get("decision", ""),
                    "missing_fields": report.get("missing_fields", []),
                    "checks": report["checks"],
                },
                indent=2,
            )
        )
        return 0 if report["status"] == "PASS" else 1

    if args.command == "run-docassemble-workflow":
        payload_path = Path(args.payload_path)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        result = approved_docassemble_workflow(payload, operator_id=args.operator_id)
        result_path = Path(args.result_path)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"status": result["status"], "task_id": result.get("task_id"), "result_path": str(result_path)}, indent=2))
        return 0 if result["status"] == "approved_and_synced" else 1

    if args.command == "scrape-regd":
        manifest = run_regd_scrape(
            output_dir=args.output_dir,
            user_agent=args.user_agent,
            max_entries=int(args.max_entries),
            page_size=int(args.page_size),
        )
        print(json.dumps(manifest, indent=2))
        return 0

    if args.command == "queue-regd-enrichment":
        result = queue_regd_enrichment_tasks(
            targets_csv_path=Path(args.targets_csv_path),
            ledger_path=Path(args.ledger) if args.ledger else None,
            default_priority=int(args.default_priority),
        )
        print(json.dumps(result, indent=2))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
