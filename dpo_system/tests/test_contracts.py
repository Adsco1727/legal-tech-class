from dpo_system.contracts.validator import (
    validate_accounting_event,
    validate_filing,
    validate_lead,
    validate_transaction,
)


def test_valid_transaction_passes():
    record = {
        "transaction_id": "txn_12345678",
        "run_id": "run_12345678",
        "wave_id": 1,
        "jurisdiction": "US",
        "queue_state": "new",
        "risk_class": "auto",
        "amount": 10.0,
        "currency": "USD",
    }
    result = validate_transaction(record)
    assert result.ok, result.errors


def test_invalid_transaction_fails():
    record = {
        "transaction_id": "short",
        "run_id": "run_12345678",
        "wave_id": 0,
        "jurisdiction": "US",
        "queue_state": "unknown",
        "risk_class": "auto",
        "amount": "bad",
        "currency": "USD",
    }
    result = validate_transaction(record)
    assert not result.ok


def test_valid_lead_passes():
    record = {
        "lead_id": "lead_12345678",
        "source": "seo",
        "jurisdiction": "US",
        "created_at": "2026-07-19T10:00:00Z",
    }
    result = validate_lead(record)
    assert result.ok, result.errors


def test_valid_filing_passes():
    record = {
        "filing_id": "filing01",
        "filing_type": "RegD",
        "jurisdiction": "US",
        "source_url": "https://example.org/filing",
    }
    result = validate_filing(record)
    assert result.ok, result.errors


def test_valid_accounting_event_passes():
    record = {
        "event_id": "evt_12345678",
        "transaction_id": "txn_12345678",
        "event_type": "accrual",
        "debit_account": "1000",
        "credit_account": "2000",
        "amount": 100.5,
    }
    result = validate_accounting_event(record)
    assert result.ok, result.errors
