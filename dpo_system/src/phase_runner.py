from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from typing import Any

from . import ledger_io as ledger
from . import operator_actions as ops

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
    req = urllib.request.Request(url, headers={"User-Agent": "dpo-phase-runner"})
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
    rows = _read_csv(path)
    planned: list[dict[str, Any]] = []
    for row in rows:
        lead_id = (row.get("lead_id") or "").strip()
        action_type = (row.get("action_type") or "").strip()
        if not lead_id or not action_type:
            continue
        priority = int((row.get("priority") or "3").strip())
        notes = (row.get("notes") or "").strip()
        planned.append(
            {
                "lead_id": lead_id,
                "action_type": action_type,
                "priority": priority,
                "notes": notes,
            }
        )
        if apply:
            ops.queue_crm_task(lead_id=lead_id, action_type=action_type, priority=priority, notes=notes)
    return planned


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

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
