from __future__ import annotations

import json
from pathlib import Path


def test_feed_manifest_exists_and_has_required_keys():
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "data" / "curated" / "feed_manifest.json"

    assert manifest_path.exists(), "feed_manifest.json is missing"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "manifest_version" in data
    assert "generated_at" in data
    assert "freshness_hours" in data
    assert "datasets" in data`
powershell -ExecutionPolicy Bypass -File C:\Users\Gary\Documents\GitHub\deploy-starter-pack-to-5-repos.ps1
@'
from __future__ import annotations

import json
from pathlib import Path


def test_feed_manifest_exists_and_has_required_keys():
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "data" / "curated" / "feed_manifest.json"

    assert manifest_path.exists(), "feed_manifest.json is missing"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "manifest_version" in data
    assert "generated_at" in data
    assert "freshness_hours" in data
    assert "datasets" in data
    assert isinstance(data["datasets"], list)

    for ds in data["datasets"]:
        assert "name" in ds
        assert "path" in ds
        assert "rows" in ds
        assert "sha256" in ds
        assert "source_runs" in ds
        assert isinstance(ds["source_runs"], list)
