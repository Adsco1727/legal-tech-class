from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from exc


@dataclass
class Result:
    ok: bool
    errors: List[str]


_CONTRACT_DIR = Path(__file__).resolve().parent


def _load_contract(file_name: str) -> Dict[str, Any]:
    with (_CONTRACT_DIR / file_name).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _validate_required(record: Dict[str, Any], required: List[str]) -> List[str]:
    return [f"missing required field: {name}" for name in required if name not in record]


def _validate_type(field_name: str, value: Any, spec: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    expected = spec.get("type")

    if value is None and spec.get("nullable"):
        return errors

    if expected == "string" and not isinstance(value, str):
        errors.append(f"{field_name} must be string")
    elif expected == "integer" and not isinstance(value, int):
        errors.append(f"{field_name} must be integer")
    elif expected == "number" and not isinstance(value, (int, float)):
        errors.append(f"{field_name} must be number")
    elif expected == "boolean" and not isinstance(value, bool):
        errors.append(f"{field_name} must be boolean")

    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"{field_name} must be one of {spec['enum']}")

    if isinstance(value, str):
        min_len = spec.get("min_length")
        max_len = spec.get("max_length")
        if min_len is not None and len(value) < min_len:
            errors.append(f"{field_name} must be at least {min_len} chars")
        if max_len is not None and len(value) > max_len:
            errors.append(f"{field_name} must be at most {max_len} chars")

    if isinstance(value, int):
        min_value = spec.get("min")
        if min_value is not None and value < min_value:
            errors.append(f"{field_name} must be >= {min_value}")

    return errors


def _validate_against_contract(record: Dict[str, Any], contract_file: str) -> Result:
    contract = _load_contract(contract_file)
    schema = contract.get("schema", {})
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    errors = _validate_required(record, required)

    for field_name, spec in properties.items():
        if field_name in record:
            errors.extend(_validate_type(field_name, record[field_name], spec))

    return Result(ok=len(errors) == 0, errors=errors)


def validate_transaction(record: Dict[str, Any]) -> Result:
    return _validate_against_contract(record, "transactions.yaml")


def validate_lead(record: Dict[str, Any]) -> Result:
    return _validate_against_contract(record, "leads.yaml")


def validate_filing(record: Dict[str, Any]) -> Result:
    return _validate_against_contract(record, "filings.yaml")


def validate_jurisdiction(record: Dict[str, Any]) -> Result:
    return _validate_against_contract(record, "jurisdictions.yaml")


def validate_accounting_event(record: Dict[str, Any]) -> Result:
    return _validate_against_contract(record, "accounting_events.yaml")
