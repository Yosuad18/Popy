"""Tests for the Wompi webhook endpoint (signature validation + idempotency)."""

import hashlib

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers.wompi import PROCESSED_TRANSACTIONS

client = TestClient(app)

EVENTS_SECRET = settings.WOMPI_EVENTS_SECRET

pytestmark = pytest.mark.skipif(
    not EVENTS_SECRET, reason="WOMPI_EVENTS_SECRET not configured"
)


def _make_event(
    txn_id: str,
    status: str = "APPROVED",
    reference: str = "ORDER-001",
    amount_in_cents: int = 5000000,
    properties=None,
    tamper_checksum: bool = False,
) -> dict:
    """Build a Wompi transaction.updated payload with a valid checksum."""
    if properties is None:
        properties = [
            "transaction.id",
            "transaction.status",
            "transaction.amount_in_cents",
        ]

    data = {
        "transaction": {
            "id": txn_id,
            "reference": reference,
            "amount_in_cents": amount_in_cents,
            "currency": "COP",
            "status": status,
            "payment_method_type": "CARD",
        }
    }

    values = []
    for prop in properties:
        value = data
        for key in prop.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        values.append(str(value) if value is not None else "")

    checksum = hashlib.sha256(("".join(values) + EVENTS_SECRET).encode("utf-8")).hexdigest()
    if tamper_checksum:
        checksum = "0" * 64

    return {
        "event": "transaction.updated",
        "data": data,
        "signature": {"checksum": checksum, "properties": properties},
        "sent_at": "2025-01-15T10:30:46.000Z",
    }


@pytest.fixture(autouse=True)
def _clean_processed():
    PROCESSED_TRANSACTIONS.clear()
    yield
    PROCESSED_TRANSACTIONS.clear()


def test_valid_approved_event_returns_200_and_records():
    event = _make_event("01-TEST-APPROVED-001", status="APPROVED")
    response = client.post("/webhooks/wompi", json=event)
    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert PROCESSED_TRANSACTIONS["01-TEST-APPROVED-001"] == "APPROVED"


def test_declined_event_returns_200_and_records():
    event = _make_event("01-TEST-DECLINED-001", status="DECLINED")
    response = client.post("/webhooks/wompi", json=event)
    assert response.status_code == 200
    assert PROCESSED_TRANSACTIONS["01-TEST-DECLINED-001"] == "DECLINED"


def test_invalid_signature_returns_401():
    event = _make_event("01-TEST-BAD-SIG-001", tamper_checksum=True)
    response = client.post("/webhooks/wompi", json=event)
    assert response.status_code == 401
    assert "01-TEST-BAD-SIG-001" not in PROCESSED_TRANSACTIONS


def test_signature_with_wrong_secret_returns_401():
    event = _make_event("01-TEST-WRONG-SECRET-001")
    values = [
        event["data"]["transaction"]["id"],
        str(event["data"]["transaction"]["status"]),
        str(event["data"]["transaction"]["amount_in_cents"]),
    ]
    wrong = hashlib.sha256(("".join(values) + "not_the_secret").encode()).hexdigest()
    event["signature"]["checksum"] = wrong
    response = client.post("/webhooks/wompi", json=event)
    assert response.status_code == 401


def test_missing_signature_returns_401():
    event = _make_event("01-TEST-NO-SIG-001")
    del event["signature"]
    response = client.post("/webhooks/wompi", json=event)
    assert response.status_code == 401


def test_invalid_json_returns_400():
    response = client.post(
        "/webhooks/wompi",
        content=b"not-json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400


def test_duplicate_event_is_idempotent():
    event = _make_event("01-TEST-DUP-001", status="APPROVED")
    first = client.post("/webhooks/wompi", json=event)
    assert first.status_code == 200

    # Same transaction id delivered again with a different status must not overwrite.
    duplicate = _make_event("01-TEST-DUP-001", status="PENDING")
    second = client.post("/webhooks/wompi", json=duplicate)
    assert second.status_code == 200
    assert PROCESSED_TRANSACTIONS["01-TEST-DUP-001"] == "APPROVED"


def test_dynamic_properties_are_honored():
    # Checksum computed over a different (dynamic) properties list.
    event = _make_event(
        "01-TEST-DYN-001",
        status="APPROVED",
        properties=["transaction.reference", "transaction.currency"],
    )
    response = client.post("/webhooks/wompi", json=event)
    assert response.status_code == 200
    assert PROCESSED_TRANSACTIONS["01-TEST-DYN-001"] == "APPROVED"
