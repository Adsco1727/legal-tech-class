import pytest

from dpo_system.state.boundary_checker import assert_ltop_safe


def test_runtime_required_modules_pass():
    assert_ltop_safe([
        "integrations.docassemble_client",
        "integrations.legal_nlp_adapter",
        "pipelines.run_minimal_runtime_check",
    ])


def test_desktop_only_modules_fail():
    with pytest.raises(RuntimeError):
        assert_ltop_safe(["scrapers.na_scraper"])


def test_missing_boundary_fails():
    with pytest.raises(RuntimeError):
        assert_ltop_safe(["integrations.unknown_adapter"])
