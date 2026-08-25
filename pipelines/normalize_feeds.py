from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
CURATED_DIR = REPO_ROOT / "data" / "curated"
MANIFEST_PATH = CURATED_DIR / "feed_manifest.json"


@dataclass
class CuratedFileMeta:
    name: str
    path: Path
    rows: int
    sha256: str
    source_runs: list[str]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_latest_source_dirs(raw_dir: Path) -> dict[str, Path]:
    latest: dict[str, Path] = {}
    if not raw_dir.exists():
        return latest

    for source_dir in raw_dir.iterdir():
        if not source_dir.is_dir():
            continue
        dated = [p for p in source_dir.iterdir() if p.is_dir()]
        if not dated:
            continue
        latest[source_dir.name] = sorted(dated, key=lambda p: p.name)[-1]
    return latest


def read_csv_rows(csv_path: Path) -> list[dict]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
            count += 1
    return count


def normalize() -> list[CuratedFileMeta]:
    latest_sources = discover_latest_source_dirs(RAW_DIR)
    all_rows: list[dict] = []
    source_runs: list[str] = []
    ingest_ts = utc_now_iso()

    for source, run_dir in latest_sources.items():
        source_runs.append(f"{source}:{run_dir.name}")
        for csv_path in run_dir.glob("*.csv"):
            rows = read_csv_rows(csv_path)
            for r in rows:
                r["_source"] = source
                r["_source_file"] = csv_path.name
                r["_ingest_ts"] = ingest_ts
            all_rows.extend(rows)

    curated_files: list[CuratedFileMeta] = []
    out_csv = CURATED_DIR / "cases.csv"

    if all_rows:
        base_fields = sorted({k for row in all_rows for k in row.keys()})
        rows_written = write_csv(out_csv, all_rows, base_fields)
        curated_files.append(
            CuratedFileMeta(
                name="cases",
                path=out_csv,
                rows=rows_written,
                sha256=sha256_file(out_csv),
                source_runs=source_runs,
            )
        )
    else:
        rows_written = write_csv(out_csv, [], ["_source", "_source_file", "_ingest_ts"])
        curated_files.append(
            CuratedFileMeta(
                name="cases",
                path=out_csv,
                rows=rows_written,
                sha256=sha256_file(out_csv),
                source_runs=source_runs,
            )
        )

    return curated_files


def write_manifest(curated_files: list[CuratedFileMeta]) -> None:
    manifest = {
        "manifest_version": "1.0.0",
        "generated_at": utc_now_iso(),
        "freshness_hours": 24,
        "datasets": [
            {
                "name": f.name,
                "path": str(f.path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "rows": f.rows,
                "sha256": f.sha256,
                "source_runs": f.source_runs,
            }
            for f in curated_files
        ],
    }
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[OK] wrote manifest: {MANIFEST_PATH}")


def main() -> None:
    curated = normalize()
    write_manifest(curated)
    print("[DONE] normalize_feeds complete")


if __name__ == "__main__":
    main()
