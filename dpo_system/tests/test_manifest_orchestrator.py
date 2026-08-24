from pathlib import Path

import pytest

from dpo_system.src.manifest_orchestrator import load_manifest_bundle, route_item


def test_manifest_orchestrator_supports_new_manifest_shape(tmp_path: Path) -> None:
    manifest_path = tmp_path / "dto_manifest.yaml"
    manifest_path.write_text(
        """
manifest_version: "0.3"

meta:
  manifest_id: "example_manifest_001"
  description: "DTO routing manifest for sample ingestion flow"
  jurisdiction_tags:
    - "US"
    - "federal"
  evidence_contract:
    required_fields:
      - "source_id"
      - "item_id"
      - "evidence_ref"

execution:
  notebooks:
    - id: "refinery_preprocess"
      path: "notebooks/refinery/preprocess.ipynb"
      order: 1
      required: true
      produces:
        - "preprocessed_item"
        - "refinery_log"

    - id: "refinery_extract"
      path: "notebooks/refinery/extract.ipynb"
      order: 2
      required: true
      produces:
        - "extracted_fields"
        - "evidence_bundle"

    - id: "refinery_validate"
      path: "notebooks/refinery/validate.ipynb"
      order: 3
      required: true
      produces:
        - "validation_report"

processors:
  registry:
    - id: "dto_router"
      module: "dpo_system.src.processors.router"
      class: "DTORouter"
      version: "1.0.0"
      capabilities:
        - "lane_selection"
        - "decision_evaluation"
        - "evidence_binding"

    - id: "evidence_attacher"
      module: "dpo_system.src.processors.evidence"
      class: "EvidenceAttacher"
      version: "1.0.0"
      capabilities:
        - "attach_evidence"
        - "normalize_refs"

lanes:
  - lane_id: "center_lane"
    description: "Primary DTO lane for compliant items"
    criteria:
      required_fields:
        - "item_id"
        - "extracted_fields"
        - "validation_report"
      rules:
        - id: "rule_center_001"
          type: "field_presence"
          field: "extracted_fields"
          must_exist: true
        - id: "rule_center_002"
          type: "validation_pass"
          field: "validation_report.status"
          equals: "PASS"

    response_schema:
      lane_status:
        type: "string"
        enum: ["PASS", "FAIL", "REVIEW"]
      lane_payload:
        type: "object"
        properties:
          normalized_item:
            type: "object"
          evidence_bundle:
            type: "object"
""".strip()
    )

    bundle = load_manifest_bundle(manifest_path)
    routing_object = {
        "item_id": "item-002",
        "source_id": "rss_canada",
        "evidence_ref": "source://rss_canada/2",
        "extracted_fields": {"title": "Example"},
        "validation_report": {"status": "PASS"},
    }

    result = route_item(routing_object, bundle, ledger_path=tmp_path / "operator_ledger.xlsx")

    assert result["decision"] == "route_to_center_lane"
    assert result["lane"] == "center_lane"
    assert result["notebook_execution_plan"][0]["id"] == "refinery_preprocess"
    assert result["lane_response"]["response_schema"]["lane_status"]["enum"] == ["PASS", "FAIL", "REVIEW"]


def test_load_manifest_bundle_rejects_invalid_manifest_shape(tmp_path: Path) -> None:
    manifest_path = tmp_path / "invalid_manifest.yaml"
    manifest_path.write_text(
        """
manifest_version: "0.3"
meta:
  manifest_id: "broken"
execution:
  notebooks:
    - id: "broken_notebook"
      path: "notebooks/broken.ipynb"
      required: true
      produces:
        - "output"
processors:
  registry: []
lanes: []
""".strip()
    )

    with pytest.raises(ValueError, match="invalid manifest"):
        load_manifest_bundle(manifest_path)


def test_manifest_orchestrator_routes_and_writes_ledger(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    (manifests_dir / "repos.yaml").write_text(
        """
repos:
  - id: dpo_system
    slug: legal-tech-class/dpo_system
    branch: main
    install: pip
    depends_on: []
    health_check: operator_actions:import
""".strip()
    )
    (manifests_dir / "notebooks.yaml").write_text(
        """
notebooks:
  - id: refinery
    path: notebooks/refinery.ipynb
    execution_order: 2
    requires: [dpo_system]
    inputs: [raw_content]
    outputs: [normalized_item]
  - id: normalization
    path: notebooks/normalization.ipynb
    execution_order: 1
    requires: [dpo_system]
    inputs: [raw_content]
    outputs: [normalized_item]
""".strip()
    )
    (manifests_dir / "scrapers.yaml").write_text(
        """
scrapers:
  - id: rss_canada
    type: rss
    cadence: daily
    endpoint: https://example.ca/rss
    jurisdiction: CA
    content_types: [news, regulation]
    routing_hints: [authority_site]
""".strip()
    )
    (manifests_dir / "processors.yaml").write_text(
        """
processors:
  - id: authority_processor
    lane: authority_site
    name: Authority Processor
    description: Routes authority-site content into the intake queue.
    owner: dto
    tags: [authority, intake]
    priority: 10
    enabled: true
    schema_version: "1.0"
    write_target: INGESTION_QUEUE
    retry_policy: linear
    allowed_actions: [ingest, classify, update]
    routing_rule:
      content_types: [case_law, regulation]
      jurisdictions: [US, EU, UK, CA]
  - id: bd_processor
    lane: bd_lane
    name: BD Processor
    description: Handles BD pipeline intake.
    owner: bd
    tags: [bd]
    priority: 20
    enabled: true
    schema_version: "1.0"
    write_target: INGESTION_QUEUE
    retry_policy: exponential
    allowed_actions: [ingest, update]
    routing_rule:
      content_types: [press_release]
      jurisdictions: [CA]
""".strip()
    )

    bundle = load_manifest_bundle(manifests_dir)
    ledger_path = tmp_path / "operator_ledger.xlsx"

    routing_object = {
        "item_id": "item-001",
        "source_id": "rss_canada",
        "content_hash": "abc123",
        "normalized_payload": {"title": "New regulation update"},
        "classification": {"type": "case_law", "subtype": "regulation"},
        "jurisdiction": "CA",
        "urgency": 2,
        "lane_hint": "authority_site",
        "policy_flags": [],
        "evidence_ref": "source://rss_canada/1",
    }

    result = route_item(routing_object, bundle, ledger_path=ledger_path)

    assert result["decision"] == "route_to_authority_site"
    assert result["lane_response"]["processor_registration"]["name"] == "Authority Processor"
    assert result["lane_response"]["write_target"] == "INGESTION_QUEUE"
    assert result["notebook_execution_plan"][0]["id"] == "normalization"
    assert result["ledger_event"]["item_id"] == "item-001"
    assert ledger_path.exists()

    from dpo_system.src.ledger_io import read_rows

    events = read_rows("LEDGER_EVENTS", path=ledger_path)
    assert events[0]["item_id"] == "item-001"
    assert events[0]["lane"] == "authority_site"
