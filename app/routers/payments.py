"""Payment endpoints (Wompi sandbox): Nequi + card via Widget, status polling."""

import hashlib
import html
import logging
import re
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.agent.tools import get_order, mark_order_paid, order_for_txn, register_payment_txn
from app.config import settings

logger = logging.getLogger("payments")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/pay", tags=["Payments"])

_PHONE_RE = re.compile(r"^3\d{9}$")
_FINAL_STATUSES = {"APPROVED", "DECLINED", "VOIDED", "ERROR"}


def get_integrity_signature(
    reference: str,
    amount_in_cents: int,
    currency: str,
    integrity_secret: str,
    expiration_time: Optional[str] = None,
) -> str:
    """SHA256(reference + amount_in_cents + currency [+ expiration_time] + secret)."""
    parts = [str(reference), str(amount_in_cents), currency]
    if expiration_time:
        parts.append(expiration_time)
    parts.append(integrity_secret)
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


def _require_wompi_config() -> None:
    missing = [
        name
        for name, value in (
            ("WOMPI_PUBLIC_KEY", settings.WOMPI_PUBLIC_KEY),
            ("WOMPI_PRIVATE_KEY", settings.WOMPI_PRIVATE_KEY),
            ("WOMPI_INTEGRITY_SECRET", settings.WOMPI_INTEGRITY_SECRET),
        )
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Pagos no configurados. Falta: {', '.join(missing)} en .env",
        )


async def _fetch_acceptance_tokens(client: httpx.AsyncClient) -> tuple[str, str]:
    """GET /v1/merchants/:pub_key → (acceptance_token, personal_data_auth)."""
    url = f"{settings.WOMPI_BASE_URL}/merchants/{settings.WOMPI_PUBLIC_KEY}"
    res = await client.get(url)
    if res.status_code != 200:
        logger.error("Merchant fetch failed: %s %s", res.status_code, res.text)
        raise HTTPException(status_code=502, detail="No se pudo consultar el comercio en Wompi")
    data = res.json().get("data") or {}
    acceptance = (data.get("presigned_acceptance") or {}).get("acceptance_token")
    personal = (data.get("presigned_personal_data_auth") or {}).get("acceptance_token")
    if not acceptance or not personal:
        raise HTTPException(status_code=502, detail="Tokens de aceptación no disponibles en Wompi")
    return acceptance, personal


async def _create_nequi_transaction(
    client: httpx.AsyncClient,
    *,
    amount_in_cents: int,
    reference: str,
    phone_number: str,
    acceptance_token: str,
    personal_data_auth: str,
) -> dict:
    """POST /v1/transactions with type NEQUI. Returns Wompi `data` dict."""
    signature = get_integrity_signature(
        reference, amount_in_cents, "COP", settings.WOMPI_INTEGRITY_SECRET or ""
    )
    payload = {
        "amount_in_cents": amount_in_cents,
        "currency": "COP",
        "signature": signature,
        "customer_email": "cliente@popy.test",
        "reference": reference,
        "acceptance_token": acceptance_token,
        "accept_personal_auth": personal_data_auth,
        "payment_method": {
            "type": "NEQUI",
            "phone_number": phone_number,
        },
    }
    res = await client.post(
        f"{settings.WOMPI_BASE_URL}/transactions",
        headers={"Authorization": f"Bearer {settings.WOMPI_PRIVATE_KEY}"},
        json=payload,
    )
    body = res.json()
    if res.status_code >= 400:
        err = body.get("error") or {}
        messages = err.get("messages") or {}
        logger.warning("Wompi create txn failed: %s %s", res.status_code, body)
        raise HTTPException(
            status_code=502,
            detail={
                "type": err.get("type", "WOMPI_ERROR"),
                "messages": messages,
            },
        )
    return body.get("data") or {}


async def _get_transaction(client: httpx.AsyncClient, txn_id: str) -> dict:
    """GET /v1/transactions/:id → `data` dict."""
    res = await client.get(f"{settings.WOMPI_BASE_URL}/transactions/{txn_id}")
    if res.status_code == 404:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    if res.status_code != 200:
        raise HTTPException(status_code=502, detail="No se pudo consultar la transacción en Wompi")
    return res.json().get("data") or {}


def _apply_status_to_order(txn_id: str, status: str) -> None:
    """Sync local order state from a Wompi status (polling + webhook)."""
    order_id = order_for_txn(txn_id)
    if not order_id:
        return
    if status == "APPROVED":
        mark_order_paid(order_id)
    elif status in ("DECLINED", "ERROR", "VOIDED"):
        order = get_order(order_id)
        if order and order.get("status") != "Pagado":
            order["status"] = {
                "DECLINED": "Rechazado",
                "ERROR": "Error",
                "VOIDED": "Anulado",
            }.get(status, status)


def _page(title: str, body: str, status_code: int = 200) -> HTMLResponse:
    content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)} — Popy</title>
<style>
  body {{ font-family: system-ui, sans-serif; background:#f9fafb; margin:0;
         display:flex; justify-content:center; padding:40px 16px; }}
  .card {{ background:#fff; border-radius:12px; box-shadow:0 4px 24px rgba(0,0,0,.08);
           padding:28px; max-width:400px; width:100%; text-align:center; }}
  h1 {{ font-size:1.15rem; margin:0 0 8px; }}
  p {{ color:#4b5563; margin:6px 0; }}
  .spinner {{ width:36px; height:36px; border:4px solid #fce4ec; border-top-color:#C2185B;
             border-radius:50%; margin:16px auto; animation:spin .8s linear infinite; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .ok {{ color:#15803d; font-weight:600; }}
  .bad {{ color:#b91c1c; font-weight:600; }}
  .muted {{ font-size:.85rem; color:#6b7280; }}
  a {{ color:#C2185B; }}
</style>
</head>
<body>
<div class="card">{body}</div>
</body>
</html>"""
    return HTMLResponse(content=content, status_code=status_code)


_STATUS_PAGE_JS = """
<script>
(function () {
  var txnId = %s;
  var attempts = 0;
  var maxAttempts = 40;
  var delay = 2000;
  var statusEl = document.getElementById('status');
  var spinEl = document.getElementById('spinner');

  function poll() {
    fetch('/pay/status/api/' + encodeURIComponent(txnId))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          spinEl.style.display = 'none';
          statusEl.className = 'bad';
          statusEl.textContent = data.error;
          return;
        }
        var s = data.status || 'PENDING';
        if (s === 'APPROVED') {
          spinEl.style.display = 'none';
          statusEl.className = 'ok';
          statusEl.textContent = 'Pago aprobado ✅';
          document.getElementById('detail').textContent =
            'Pedido ' + (data.order_id || '') + ' marcado como Pagado.';
          document.getElementById('done').style.display = 'block';
          return;
        }
        if (s === 'DECLINED' || s === 'ERROR' || s === 'VOIDED') {
          spinEl.style.display = 'none';
          statusEl.className = 'bad';
          statusEl.textContent = 'Pago ' + s.toLowerCase() + ' ❌';
          document.getElementById('detail').textContent =
            data.status_message || 'Intenta de nuevo desde el chat.';
          document.getElementById('done').style.display = 'block';
          return;
        }
        statusEl.textContent = 'Procesando pago… (PENDING)';
        attempts += 1;
        if (attempts >= maxAttempts) {
          spinEl.style.display = 'none';
          statusEl.textContent = 'Todavía pendiente. El webhook confirmará el pago.';
          document.getElementById('done').style.display = 'block';
          return;
        }
        delay = Math.min(delay * 1.3, 15000);
        setTimeout(poll, delay);
      })
      .catch(function () {
        attempts += 1;
        if (attempts < maxAttempts) setTimeout(poll, delay);
      });
  }
  poll();
})();
</script>
"""


@router.post("/nequi", response_class=HTMLResponse, summary="Create Nequi transaction")
async def pay_nequi(
    order_id: str = Form(...),
    phone_number: str = Form(...),
):
    """Create a Wompi NEQUI transaction for an order and redirect to the status page."""
    _require_wompi_config()

    order_id = order_id.strip()
    phone_number = phone_number.strip().replace(" ", "").replace("+57", "")
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Pedido {order_id} no encontrado")
    if order.get("status") == "Pagado":
        raise HTTPException(status_code=409, detail=f"Pedido {order_id} ya está pagado")
    if not _PHONE_RE.match(phone_number):
        raise HTTPException(status_code=422, detail="Celular Nequi inválido (10 dígitos, empieza por 3)")

    # Reuse an in-flight transaction so double submits do not create two charges.
    existing_txn = order.get("payment_txn_id")
    if existing_txn and order.get("status") == "Procesando":
        return RedirectResponse(url=f"/pay/status/{existing_txn}", status_code=303)

    amount_in_cents = int(round(float(order["total"]) * 100))
    if amount_in_cents <= 0:
        raise HTTPException(status_code=422, detail="El total del pedido debe ser mayor a 0")

    # Unique reference per attempt (never reuse — Wompi rejects duplicates).
    reference = f"{order_id}-{int(time.time() * 1000)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        acceptance, personal = await _fetch_acceptance_tokens(client)
        txn = await _create_nequi_transaction(
            client,
            amount_in_cents=amount_in_cents,
            reference=reference,
            phone_number=phone_number,
            acceptance_token=acceptance,
            personal_data_auth=personal,
        )

    txn_id = txn.get("id")
    if not txn_id:
        raise HTTPException(status_code=502, detail="Wompi no devolvió id de transacción")

    register_payment_txn(txn_id, order_id)
    order["payment_txn_id"] = txn_id
    order["payment_reference"] = reference
    order["payment_status"] = txn.get("status", "PENDING")

    logger.info(
        "Nequi txn created: id=%s ref=%s order=%s amount_in_cents=%s status=%s",
        txn_id, reference, order_id, amount_in_cents, txn.get("status"),
    )
    return RedirectResponse(url=f"/pay/status/{txn_id}", status_code=303)


@router.get("/status/api/{txn_id}", summary="Transaction status JSON (polling)")
async def pay_status_api(txn_id: str):
    """Proxy GET /v1/transactions/:id; syncs local order on final statuses."""
    _require_wompi_config()
    async with httpx.AsyncClient(timeout=15.0) as client:
        txn = await _get_transaction(client, txn_id)

    status = txn.get("status") or "PENDING"
    _apply_status_to_order(txn_id, status)
    order_id = order_for_txn(txn_id)
    order = get_order(order_id) if order_id else None

    return JSONResponse(
        content={
            "id": txn.get("id"),
            "status": status,
            "status_message": txn.get("status_message"),
            "reference": txn.get("reference"),
            "amount_in_cents": txn.get("amount_in_cents"),
            "currency": txn.get("currency"),
            "order_id": order_id,
            "order_status": order.get("status") if order else None,
        }
    )


@router.get("/status/{txn_id}", response_class=HTMLResponse, summary="Payment status page")
async def pay_status_page(txn_id: str):
    """HTML page that polls /pay/status/api/{txn_id} until a final status."""
    js = _STATUS_PAGE_JS % _js_string(txn_id)
    body = f"""
<div class="spinner" id="spinner"></div>
<h1>Pago con Wompi</h1>
<p id="status" role="status">Consultando estado…</p>
<p id="detail" class="muted"></p>
<p id="done" class="muted" style="display:none">
  <a href="/demo">← Volver al chat</a>
</p>
<p class="muted">Transacción: <code>{html.escape(txn_id)}</code></p>
{js}
"""
    return _page("Pago Wompi", body)


def _js_string(value: str) -> str:
    return (
        "'" + value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"
    )


def _load_order_or_404(order_id: str) -> dict:
    order_id = order_id.strip()
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Pedido {order_id} no encontrado")
    if order.get("status") == "Pagado":
        raise HTTPException(status_code=409, detail=f"Pedido {order_id} ya está pagado")
    return order


def _amount_in_cents(order: dict) -> int:
    amount = int(round(float(order["total"]) * 100))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="El total del pedido debe ser mayor a 0")
    return amount


# NOTE: /card/return must be registered BEFORE /card/{order_id}
# so FastAPI does not match "return" as an order_id path param.
@router.get("/card/return", summary="Card Widget return — verify txn server-side")
async def pay_card_return(id: Optional[str] = Query(default=None)):
    """Never trust the redirect alone: fetch the transaction from Wompi first."""
    _require_wompi_config()
    if not id:
        raise HTTPException(status_code=400, detail="Falta el id de la transacción")

    async with httpx.AsyncClient(timeout=15.0) as client:
        txn = await _get_transaction(client, id)

    txn_id = txn.get("id") or id
    reference = txn.get("reference") or ""

    # Link txn → order: prefer reference prefix (ORD-…), else scan pending orders.
    order_id = None
    if reference:
        candidate = reference.rsplit("-", 1)[0]
        if get_order(candidate):
            order_id = candidate
    if order_id is None:
        # Fall back: any Procesando order whose pending reference matches.
        from app.agent.tools import _ORDER_STORAGE

        for oid, o in _ORDER_STORAGE.items():
            if o.get("payment_reference") == reference and o.get("status") == "Procesando":
                order_id = oid
                break

    if order_id:
        register_payment_txn(txn_id, order_id)
        order = get_order(order_id)
        if order:
            order["payment_txn_id"] = txn_id
            order["payment_reference"] = reference or order.get("payment_reference")
            order["payment_status"] = txn.get("status", "PENDING")

    status = txn.get("status") or "PENDING"
    _apply_status_to_order(txn_id, status)

    logger.info(
        "Card return: id=%s ref=%s order=%s status=%s",
        txn_id, reference, order_id, status,
    )
    return RedirectResponse(url=f"/pay/status/{txn_id}", status_code=303)


@router.get("/card/{order_id}", response_class=HTMLResponse, summary="Card payment (Wompi Widget)")
async def pay_card_page(order_id: str):
    """Serve the official Wompi Widget page for paying an order with a card."""
    _require_wompi_config()
    order = _load_order_or_404(order_id)
    amount_in_cents = _amount_in_cents(order)

    # Reuse an in-flight transaction (e.g. user went back from the Widget).
    existing_txn = order.get("payment_txn_id")
    if existing_txn and order.get("status") == "Procesando":
        return RedirectResponse(url=f"/pay/status/{existing_txn}", status_code=303)

    reference = f"{order_id}-{int(time.time() * 1000)}"
    signature = get_integrity_signature(
        reference, amount_in_cents, "COP", settings.WOMPI_INTEGRITY_SECRET or ""
    )

    # Stash pending reference so the return handler can link txn → order
    # even before Wompi's webhook arrives (return only gets txn id).
    order["payment_reference"] = reference
    order["payment_pending_amount"] = amount_in_cents

    public_key = html.escape(settings.WOMPI_PUBLIC_KEY or "", quote=True)
    redirect_url = html.escape("/pay/card/return", quote=True)
    reference_esc = html.escape(reference, quote=True)
    signature_esc = html.escape(signature, quote=True)

    body = f"""
<h1>Pagar con tarjeta</h1>
<p><strong>Pedido {html.escape(order_id)}</strong> — Total:
   <strong>${order['total']:.2f}</strong></p>
<p class="muted">Widget oficial de Wompi (sandbox). Tu tarjeta no pasa por este servidor.</p>
<div id="wompi-widget"></div>
<script
  src="https://checkout.wompi.co/widget.js"
  data-render="button"
  data-public-key="{public_key}"
  data-currency="COP"
  data-amount-in-cents="{amount_in_cents}"
  data-reference="{reference_esc}"
  data-signature:integrity="{signature_esc}"
  data-redirect-url="{redirect_url}">
</script>
<p class="muted" style="margin-top:16px">
  Sandbox: <code>4242424242424242</code> · respaldo Wompi
  <code>4111111111111111</code> / <code>5204730000001003</code><br />
  cvv ≠ <code>111</code>, fecha de expiración futura
</p>
<p class="muted"><a href="/demo">← Volver al chat</a></p>
"""
    return _page("Pagar con tarjeta", body)
