from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def _parse_iso(ts: str) -> datetime:
    ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts).astimezone(UTC)


def assert_datafeed_ready(
    repo_root: str | Path = "..",
    required_datasets: tuple[str, ...] = ("cases",),
    max_freshness_hours: int = 24,
) -> dict:
    root = Path(repo_root).resolve()
    manifest_path = root / "data" / "curated" / "feed_manifest.json"

    if not manifest_path.exists():
        raise RuntimeError(f"Missing manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    generated_at = _parse_iso(manifest["generated_at"])
    age_hours = (datetime.now(UTC) - generated_at).total_seconds() / 3600.0
    if age_hours > max_freshness_hours:
        raise RuntimeError(
            f"Data manifest stale ({age_hours:.1f}h old > {max_freshness_hours}h). "
            "Run ingestion pipeline."
        )

    datasets = {d["name"]: d for d in manifest.get("datasets", [])}
    missing = [name for name in required_datasets if name not in datasets]
    if missing:
        raise RuntimeError(f"Missing required datasets in manifest: {missing}")

    for name in required_datasets:
        rel = datasets[name]["path"]
        path = root / rel
        if not path.exists():
            raise RuntimeError(f"Dataset file missing on disk: {path}")

    print(f"[OK] Datafeed ready. Manifest age: {age_hours:.1f}h")
    return manifest
