import json

import pytest

from repo_readiness_batch import extract_evidence_from_notebook


def test_extracts_approval_evidence_from_notebook_output():
    sample_notebook = {
        "cells": [
            {
                "outputs": [
                    {
                        "text": [
                            "Evidence Summary:\n",
                            json.dumps(
                                {
                                    "timestamp": "2026-08-24T00:00:00Z",
                                    "repo_name": "dpo-casework",
                                    "repo_root": "C:/repo/dpo-casework",
                                    "gate_a_status": "PASS",
                                    "gate_b_status": "PASS",
                                    "approval_decision": "APPROVE",
                                    "next_action": "Proceed to production workflow",
                                },
                                indent=2,
                            )
                        ]
                    }
                ]
            }
        ]
    }

    evidence = extract_evidence_from_notebook(sample_notebook)

    assert evidence["approval_decision"] == "APPROVE"
    assert evidence["gate_a_status"] == "PASS"
    assert evidence["gate_b_status"] == "PASS"
