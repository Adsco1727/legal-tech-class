from __future__ import annotations

from pathlib import Path
from typing import Dict, List

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from exc


BOUNDARY_FILE = Path(__file__).resolve().parent / "runtime_boundaries.yaml"


def load_boundaries() -> Dict[str, Dict[str, Dict[str, str]]]:
    with BOUNDARY_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def disallowed_for_ltop(imports: List[str]) -> List[str]:
    boundaries = load_boundaries()
    module_rules = boundaries.get("modules", {})
    pipeline_rules = boundaries.get("pipelines", {})

    blocked: List[str] = []
    for name in imports:
        deployment = None
        if name in module_rules:
            deployment = module_rules[name].get("deployment")
        elif name in pipeline_rules:
            deployment = pipeline_rules[name].get("deployment")

        if deployment is None:
            blocked.append(f"{name}: missing boundary declaration")
        elif deployment != "runtime_required":
            blocked.append(f"{name}: deployment={deployment}")

    return blocked


def assert_ltop_safe(imports: List[str]) -> None:
    blocked = disallowed_for_ltop(imports)
    if blocked:
        raise RuntimeError("ltop boundary check failed: " + "; ".join(blocked))
