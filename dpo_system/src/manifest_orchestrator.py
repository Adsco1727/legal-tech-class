from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import ledger_io as ledger


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be a mapping: {path}")
    return data


def _validate_manifest_structure(bundle: dict[str, Any], source: str | Path) -> None:
    if not isinstance(bundle, dict):
        raise ValueError(f"invalid manifest: root must be a mapping: {source}")

    if "manifest_version" not in bundle:
        legacy_keys = {"repos", "notebooks", "scrapers", "processors"}
        if legacy_keys & set(bundle.keys()):
            return
        raise ValueError(f"invalid manifest: missing manifest_version: {source}")

    if "meta" not in bundle or not isinstance(bundle.get("meta"), dict):
        raise ValueError(f"invalid manifest: missing meta mapping: {source}")

    execution = bundle.get("execution")
    if not isinstance(execution, dict):
        raise ValueError(f"invalid manifest: execution must be a mapping: {source}")

    notebooks = execution.get("notebooks")
    if notebooks is None:
        raise ValueError(f"invalid manifest: execution.notebooks is required: {source}")
    if not isinstance(notebooks, list) or not notebooks:
        raise ValueError(f"invalid manifest: execution.notebooks must be a non-empty list: {source}")

    for notebook in notebooks:
        if not isinstance(notebook, dict):
            raise ValueError(f"invalid manifest: notebook entries must be mappings: {source}")
        if not notebook.get("id") or not notebook.get("path"):
            raise ValueError(f"invalid manifest: notebook requires id and path: {source}")

    processors = bundle.get("processors")
    if not isinstance(processors, dict):
        raise ValueError(f"invalid manifest: processors must be a mapping: {source}")
    registry = processors.get("registry")
    if not isinstance(registry, list) or not registry:
        raise ValueError(f"invalid manifest: processors.registry must be a non-empty list: {source}")
    for processor in registry:
        if not isinstance(processor, dict):
            raise ValueError(f"invalid manifest: processor entries must be mappings: {source}")
        if not processor.get("id") or not processor.get("module") or not processor.get("class"):
            raise ValueError(f"invalid manifest: processor requires id, module, and class: {source}")

    lanes = bundle.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise ValueError(f"invalid manifest: lanes must be a non-empty list: {source}")
    for lane in lanes:
        if not isinstance(lane, dict):
            raise ValueError(f"invalid manifest: lane entries must be mappings: {source}")
        if not lane.get("lane_id"):
            raise ValueError(f"invalid manifest: lane requires lane_id: {source}")


def load_manifest_bundle(manifests_dir: str | Path) -> dict[str, Any]:
    base = Path(manifests_dir)
    bundle: dict[str, Any] = {}

    if base.is_file():
        bundle = _read_yaml(base)
        _validate_manifest_structure(bundle, base)
        return bundle

    for filename in ["repos.yaml", "notebooks.yaml", "scrapers.yaml", "processors.yaml"]:
        path = base / filename
        if not path.exists():
            continue
        bundle[filename[:-5]] = _read_yaml(path)

    if "processors" in bundle and isinstance(bundle["processors"], dict):
        _validate_manifest_structure(bundle, base)
    return bundle


def _build_notebook_execution_plan(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    execution = bundle.get("execution", {})
    notebooks = execution.get("notebooks", []) if isinstance(execution, dict) else []
    if not notebooks:
        notebooks = bundle.get("notebooks", {}).get("notebooks", [])

    ordered: list[dict[str, Any]] = []
    for notebook in notebooks:
        order = notebook.get("order")
        if order is None:
            order = notebook.get("execution_order", 999)
        ordered.append(
            {
                "id": notebook.get("id"),
                "path": notebook.get("path"),
                "execution_order": order,
                "required": notebook.get("required", True),
                "requires": notebook.get("requires", []),
                "inputs": notebook.get("inputs", []),
                "outputs": notebook.get("outputs", []),
                "produces": notebook.get("produces", []),
            }
        )
    return sorted(ordered, key=lambda item: (item.get("execution_order", 999), str(item.get("id", ""))))


def _get_nested_value(data: Any, dotted_path: str) -> Any:
    current = data
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _lane_matches(routing_object: dict[str, Any], lane_entry: dict[str, Any]) -> bool:
    criteria = lane_entry.get("criteria", {})
    required_fields = criteria.get("required_fields", [])
    for field in required_fields:
        if _get_nested_value(routing_object, field) is None:
            return False

    for rule in criteria.get("rules", []):
        rule_type = rule.get("type")
        field = rule.get("field")
        if rule_type == "field_presence":
            must_exist = rule.get("must_exist", True)
            exists = _get_nested_value(routing_object, field) is not None
            if must_exist and not exists:
                return False
            if not must_exist and exists:
                return False
        elif rule_type == "validation_pass":
            expected = rule.get("equals")
            actual = _get_nested_value(routing_object, field)
            if actual != expected:
                return False
    return True


def _build_lane_response(processor: dict[str, Any] | None, decision: str, lane: str, bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    response_schema = None
    if bundle is not None:
        lane_entry = None
        for lane_item in bundle.get("lanes", []):
            if lane_item.get("lane_id") == lane:
                lane_entry = lane_item
                break
        if lane_entry is not None:
            response_schema = lane_entry.get("response_schema")

    processor_registration = None
    if processor is not None:
        processor_registration = {
            "id": processor.get("id"),
            "name": processor.get("name"),
            "description": processor.get("description"),
            "owner": processor.get("owner"),
            "tags": processor.get("tags", []),
            "priority": processor.get("priority"),
            "enabled": processor.get("enabled", True),
            "module": processor.get("module"),
            "class": processor.get("class"),
            "version": processor.get("version"),
            "capabilities": processor.get("capabilities", []),
        }

    return {
        "decision": decision,
        "lane": lane,
        "processor_registration": processor_registration,
        "write_target": processor.get("write_target") if processor is not None else None,
        "retry_policy": processor.get("retry_policy") if processor is not None else None,
        "allowed_actions": processor.get("allowed_actions", []) if processor is not None else [],
        "schema_version": processor.get("schema_version") if processor is not None else None,
        "response_schema": response_schema,
    }


def _ensure_ledger_schema(ledger_path: str | Path | None = None) -> None:
    path = Path(ledger_path) if ledger_path is not None else None
    if path is not None and not path.exists():
        ledger.create_ledger_workbook(path)
    elif path is None and not ledger.LEDGER_PATH.exists():
        ledger.create_ledger_workbook(ledger.LEDGER_PATH)


def _build_ledger_event(item: dict[str, Any], decision: str, lane: str, ledger_path: str | Path | None = None) -> dict[str, Any]:
    return {
        "event_id": f"evt-{ledger.timestamp()}",
        "timestamp": ledger.timestamp(),
        "operator": "DTO",
        "notebook": "manifest_orchestrator",
        "action": "route_item",
        "target": item.get("item_id", "unknown"),
        "status": "ok",
        "notes": f"decision={decision};lane={lane}",
        "item_id": item.get("item_id", "unknown"),
        "lane": lane,
        "decision": decision,
        "source_id": item.get("source_id", "unknown"),
        "evidence_ref": item.get("evidence_ref", ""),
    }


def route_item(routing_object: dict[str, Any], bundle: dict[str, Any], ledger_path: str | Path | None = None) -> dict[str, Any]:
    processors = bundle.get("processors", {}).get("processors", [])
    if not processors:
        processors = bundle.get("processors", {}).get("registry", [])
    if not processors:
        raise ValueError("no processors defined in manifest bundle")

    item_type = routing_object.get("classification", {}).get("type", "")
    jurisdiction = routing_object.get("jurisdiction", "")
    lane_hint = routing_object.get("lane_hint", "")

    manifest_lanes = bundle.get("lanes", [])
    for lane_entry in manifest_lanes:
        lane_id = lane_entry.get("lane_id")
        if _lane_matches(routing_object, lane_entry):
            decision = f"route_to_{lane_id}"
            lane_processor = processors[0] if processors else None
            lane_response = _build_lane_response(lane_processor, decision, lane_id, bundle)
            _ensure_ledger_schema(ledger_path)
            ledger.append_row("LEDGER_EVENTS", _build_ledger_event(routing_object, decision, lane_id, ledger_path), path=Path(ledger_path) if ledger_path is not None else None)
            return {
                "decision": decision,
                "lane": lane_id,
                "processor_id": lane_processor.get("id") if lane_processor is not None else None,
                "lane_response": lane_response,
                "notebook_execution_plan": _build_notebook_execution_plan(bundle),
                "ledger_event": _build_ledger_event(routing_object, decision, lane_id, ledger_path),
            }

    for processor in processors:
        routing_rule = processor.get("routing_rule", {})
        allowed_content = routing_rule.get("content_types", [])
        allowed_jurisdictions = routing_rule.get("jurisdictions", [])
        if item_type in allowed_content and (not allowed_jurisdictions or jurisdiction in allowed_jurisdictions):
            lane = processor.get("lane", "unknown")
            decision = f"route_to_{lane}"
            lane_response = _build_lane_response(processor, decision, lane, bundle)
            _ensure_ledger_schema(ledger_path)
            ledger.append_row("LEDGER_EVENTS", _build_ledger_event(routing_object, decision, lane, ledger_path), path=Path(ledger_path) if ledger_path is not None else None)
            return {
                "decision": decision,
                "lane": lane,
                "processor_id": processor.get("id"),
                "lane_response": lane_response,
                "notebook_execution_plan": _build_notebook_execution_plan(bundle),
                "ledger_event": _build_ledger_event(routing_object, decision, lane, ledger_path),
            }

    fallback_lane = lane_hint or "default"
    _ensure_ledger_schema(ledger_path)
    ledger.append_row("LEDGER_EVENTS", _build_ledger_event(routing_object, f"route_to_{fallback_lane}", fallback_lane, ledger_path), path=Path(ledger_path) if ledger_path is not None else None)
    return {
        "decision": f"route_to_{fallback_lane}",
        "lane": fallback_lane,
        "processor_id": None,
        "lane_response": {
            "decision": f"route_to_{fallback_lane}",
            "lane": fallback_lane,
            "processor_registration": None,
            "write_target": None,
            "retry_policy": None,
            "allowed_actions": [],
            "schema_version": None,
        },
        "notebook_execution_plan": _build_notebook_execution_plan(bundle),
        "ledger_event": _build_ledger_event(routing_object, f"route_to_{fallback_lane}", fallback_lane, ledger_path),
    }
