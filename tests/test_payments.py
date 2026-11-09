"""Tests for Nequi payment endpoints (signature, validation, mocked Wompi)."""

import hashlib
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agent.tools import (
    _ORDER_STORAGE,
    _PAYMENT_TXN_TO_ORDER,
    get_order,
    mark_order_paid,
    order_for_txn,
    register_payment_txn,
)
from app.config import settings
from app.main import app
from app.routers.payments import get_integrity_signature

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_orders():
    _ORDER_STORAGE.clear()
    _PAYMENT_TXN_TO_ORDER.clear()
    yield
    _ORDER_STORAGE.clear()
    _PAYMENT_TXN_TO_ORDER.clear()


def _seed_order(order_id: str = "ORD-9001", total: float = 35000.0, status: str = "Procesando"):
    _ORDER_STORAGE[order_id] = {
        "order_id": order_id,
        "items": [{"name": "Bandeja paisa", "price": total, "quantity": 1}],
        "total": total,
        "status": status,
    }
    return order_id


# --- Integrity signature -----------------------------------------------------


def test_integrity_signature_known_vector():
    # SHA256("TEST-1" + "100000" + "COP" + "test_integrity_x")
    expected = hashlib.sha256(b"TEST-1100000COPtest_integrity_x").hexdigest()
    assert get_integrity_signature("TEST-1", 100000, "COP", "test_integrity_x") == expected


def test_integrity_signature_with_expiration():
    expected = hashlib.sha256(b"TEST-1100000COP2030-01-01T00:00:00Zsec").hexdigest()
    assert (
        get_integrity_signature(
            "TEST-1", 100000, "COP", "sec", expiration_time="2030-01-01T00:00:00Z"
        )
        == expected
    )


# --- Order helpers -----------------------------------------------------------


def test_mark_and_lookup_order():
    oid = _seed_order()
    assert get_order(oid)["status"] == "Procesando"
    assert mark_order_paid(oid) is True
    assert get_order(oid)["status"] == "Pagado"
    assert mark_order_paid("ORD-NOPE") is False


def test_txn_mapping():
    register_payment_txn("txn-abc", "ORD-9001")
    assert order_for_txn("txn-abc") == "ORD-9001"
    assert order_for_txn("missing") is None


# --- POST /pay/nequi ---------------------------------------------------------


def test_pay_nequi_missing_config_returns_503():
    oid = _seed_order()
    with patch.object(settings, "WOMPI_PRIVATE_KEY", None):
        res = client.post(
            "/pay/nequi",
            data={"order_id": oid, "phone_number": "3991111111"},
            follow_redirects=False,
        )
    assert res.status_code == 503


def test_pay_nequi_unknown_order_returns_404():
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.post(
            "/pay/nequi",
            data={"order_id": "ORD-NOPE", "phone_number": "3991111111"},
            follow_redirects=False,
        )
    assert res.status_code == 404


def test_pay_nequi_invalid_phone_returns_422():
    oid = _seed_order()
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.post(
            "/pay/nequi",
            data={"order_id": oid, "phone_number": "12345"},
            follow_redirects=False,
        )
    assert res.status_code == 422


def test_pay_nequi_already_paid_returns_409():
    oid = _seed_order(status="Pagado")
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.post(
            "/pay/nequi",
            data={"order_id": oid, "phone_number": "3991111111"},
            follow_redirects=False,
        )
    assert res.status_code == 409


def test_pay_nequi_success_redirects_to_status():
    oid = _seed_order(total=50000.0)

    merchant = {
        "data": {
            "presigned_acceptance": {"acceptance_token": "acc_tok"},
            "presigned_personal_data_auth": {"acceptance_token": "pers_tok"},
        }
    }
    created = {
        "data": {
            "id": "wompi-txn-123",
            "status": "PENDING",
            "reference": "ORD-9001-1",
            "amount_in_cents": 5000000,
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=type("R", (), {"status_code": 200, "json": lambda self: merchant})())
    mock_client.post = AsyncMock(
        return_value=type("R", (), {"status_code": 201, "json": lambda self: created})()
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"), patch(
        "app.routers.payments.httpx.AsyncClient", return_value=mock_client
    ):
        res = client.post(
            "/pay/nequi",
            data={"order_id": oid, "phone_number": "3991111111"},
            follow_redirects=False,
        )

    assert res.status_code == 303
    assert res.headers["location"] == "/pay/status/wompi-txn-123"
    assert get_order(oid)["payment_txn_id"] == "wompi-txn-123"
    assert order_for_txn("wompi-txn-123") == oid

    # Verify amount in cents and integrity signature on the outbound payload
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    assert payload["amount_in_cents"] == 5000000
    assert payload["payment_method"] == {"type": "NEQUI", "phone_number": "3991111111"}
    expected_sig = hashlib.sha256(
        f"{payload['reference']}5000000COPtest_integrity_x".encode()
    ).hexdigest()
    assert payload["signature"] == expected_sig
    assert payload["acceptance_token"] == "acc_tok"
    assert payload["accept_personal_auth"] == "pers_tok"


def test_pay_nequi_reuses_inflight_txn():
    oid = _seed_order()
    _ORDER_STORAGE[oid]["payment_txn_id"] = "txn-existing"
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.post(
            "/pay/nequi",
            data={"order_id": oid, "phone_number": "3991111111"},
            follow_redirects=False,
        )
    assert res.status_code == 303
    assert res.headers["location"] == "/pay/status/txn-existing"


# --- Status endpoints --------------------------------------------------------


def test_status_api_marks_order_paid_on_approved():
    oid = _seed_order()
    register_payment_txn("txn-ok", oid)

    approved = {
        "data": {
            "id": "txn-ok",
            "status": "APPROVED",
            "reference": "ORD-9001-1",
            "amount_in_cents": 3500000,
            "currency": "COP",
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=type("R", (), {"status_code": 200, "json": lambda self: approved})()
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch(
        "app.routers.payments.httpx.AsyncClient", return_value=mock_client
    ):
        res = client.get("/pay/status/api/txn-ok")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "APPROVED"
    assert body["order_id"] == oid
    assert body["order_status"] == "Pagado"
    assert get_order(oid)["status"] == "Pagado"


def test_status_api_declined_updates_order():
    oid = _seed_order()
    register_payment_txn("txn-no", oid)

    declined = {
        "data": {
            "id": "txn-no",
            "status": "DECLINED",
            "status_message": "Rechazado por el banco",
            "reference": "ORD-9001-2",
            "amount_in_cents": 3500000,
            "currency": "COP",
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=type("R", (), {"status_code": 200, "json": lambda self: declined})()
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch(
        "app.routers.payments.httpx.AsyncClient", return_value=mock_client
    ):
        res = client.get("/pay/status/api/txn-no")

    assert res.status_code == 200
    assert res.json()["status"] == "DECLINED"
    assert get_order(oid)["status"] == "Rechazado"


def test_status_page_renders():
    res = client.get("/pay/status/txn-html")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "txn-html" in res.text
    assert "Nequi" in res.text or "Wompi" in res.text
    assert "poll" in res.text or "fetch" in res.text


# --- Card (Wompi Widget) -----------------------------------------------------


def test_place_order_html_includes_card_button():
    """place_order HTML must offer both Nequi and card payment."""
    from app.agent.tools import _CART_STORAGE, place_order

    tid = "thread-card-btn"
    _CART_STORAGE[tid] = [{"name": "Ajiaco", "price": 25000.0, "quantity": 1}]
    result = place_order.invoke({}, config={"configurable": {"thread_id": tid}})
    assert result.startswith("html:")
    assert "/pay/nequi" in result
    assert "Pagar con Nequi" in result
    assert "/pay/card/" in result
    assert "Pagar con tarjeta" in result
    assert "4242424242424242" in result


def test_card_page_missing_config_returns_503():
    oid = _seed_order()
    with patch.object(settings, "WOMPI_PRIVATE_KEY", None):
        res = client.get(f"/pay/card/{oid}")
    assert res.status_code == 503


def test_card_page_unknown_order_returns_404():
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.get("/pay/card/ORD-NOPE")
    assert res.status_code == 404


def test_card_page_already_paid_returns_409():
    oid = _seed_order(status="Pagado")
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.get(f"/pay/card/{oid}")
    assert res.status_code == 409


def test_card_page_renders_widget_with_valid_signature():
    oid = _seed_order(total=50000.0)
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.get(f"/pay/card/{oid}")

    assert res.status_code == 200
    body = res.text
    assert "checkout.wompi.co/widget.js" in body
    assert 'data-public-key="pub_test_x"' in body
    assert 'data-amount-in-cents="5000000"' in body
    assert "4242424242424242" in body

    # Extract data-reference and data-signature:integrity and verify SHA256
    import re as _re

    ref_m = _re.search(r'data-reference="([^"]+)"', body)
    sig_m = _re.search(r'data-signature:integrity="([^"]+)"', body)
    assert ref_m and sig_m
    reference = ref_m.group(1)
    signature = sig_m.group(1)
    expected = hashlib.sha256(
        f"{reference}5000000COPtest_integrity_x".encode()
    ).hexdigest()
    assert signature == expected
    assert reference.startswith(f"{oid}-")

    # Pending reference stashed for return linking
    assert get_order(oid)["payment_reference"] == reference


def test_card_return_missing_id_returns_400():
    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch.object(
        settings, "WOMPI_PUBLIC_KEY", "pub_test_x"
    ), patch.object(settings, "WOMPI_INTEGRITY_SECRET", "test_integrity_x"):
        res = client.get("/pay/card/return", follow_redirects=False)
    assert res.status_code == 400


def test_card_return_verifies_and_redirects():
    oid = _seed_order(total=50000.0)
    _ORDER_STORAGE[oid]["payment_reference"] = "ORD-9001-111"

    approved = {
        "data": {
            "id": "card-txn-1",
            "status": "APPROVED",
            "reference": "ORD-9001-111",
            "amount_in_cents": 5000000,
            "currency": "COP",
            "payment_method_type": "CARD",
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=type("R", (), {"status_code": 200, "json": lambda self: approved})()
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch(
        "app.routers.payments.httpx.AsyncClient", return_value=mock_client
    ):
        res = client.get("/pay/card/return?id=card-txn-1", follow_redirects=False)

    assert res.status_code == 303
    assert res.headers["location"] == "/pay/status/card-txn-1"
    assert order_for_txn("card-txn-1") == oid
    assert get_order(oid)["payment_txn_id"] == "card-txn-1"
    assert get_order(oid)["status"] == "Pagado"


def test_card_return_unknown_txn_from_wompi():
    not_found = type(
        "R",
        (),
        {"status_code": 404, "json": lambda self: {"error": {"type": "NOT_FOUND_ERROR"}}},
    )()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=not_found)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(settings, "WOMPI_PRIVATE_KEY", "prv_test_x"), patch(
        "app.routers.payments.httpx.AsyncClient", return_value=mock_client
    ):
        res = client.get("/pay/card/return?id=nope", follow_redirects=False)
    assert res.status_code == 404
