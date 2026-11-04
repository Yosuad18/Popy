"""Wompi webhook router — receives and validates transaction events."""

import hashlib
import hmac
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("wompi.webhook")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/webhooks", tags=["Wompi"])

# In-memory store of processed transactions (idempotency + temporary record).
# Keyed by transaction id, value is the last status processed.
PROCESSED_TRANSACTIONS: dict[str, str] = {}


def _resolve_property(data: dict, prop: str):
    """Resolve a dotted property path (e.g. 'transaction.status') from data."""
    value = data
    for key in prop.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def validate_wompi_signature(body: dict, events_secret: str) -> bool:
    """Validate the Wompi event checksum.

    Formula: SHA256(values of signature.properties in order + events_secret).
    `signature.properties` is dynamic — always read it from the payload.
    """
    signature = body.get("signature") or {}
    data = body.get("data") or {}

    properties = signature.get("properties")
    checksum = signature.get("checksum")

    if not isinstance(properties, list) or not properties or not checksum:
        return False

    values = []
    for prop in properties:
        value = _resolve_property(data, prop)
        values.append(str(value) if value is not None else "")

    expected = hashlib.sha256(("".join(values) + events_secret).encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, checksum)


def _handle_event(body: dict) -> None:
    """Process a validated Wompi event (logging + in-memory record only)."""
    if body.get("event") != "transaction.updated":
        logger.info("Wompi event ignored: %s", body.get("event"))
        return

    txn = (body.get("data") or {}).get("transaction") or {}
    txn_id = txn.get("id")
    status = txn.get("status")

    if not txn_id or not status:
        logger.warning("Wompi event missing transaction id/status: %s", txn)
        return

    # Idempotency: Wompi may deliver the same event more than once.
    if txn_id in PROCESSED_TRANSACTIONS:
        logger.info(
            "Wompi event already processed (dedup): id=%s status=%s",
            txn_id,
            status,
        )
        return

    if status == "APPROVED":
        logger.info(
            "Wompi payment APPROVED: id=%s reference=%s amount_in_cents=%s "
            "currency=%s payment_method=%s",
            txn_id,
            txn.get("reference"),
            txn.get("amount_in_cents"),
            txn.get("currency"),
            txn.get("payment_method_type"),
        )
    else:
        logger.warning(
            "Wompi transaction %s: id=%s reference=%s message=%s",
            status,
            txn_id,
            txn.get("reference"),
            txn.get("status_message"),
        )

    PROCESSED_TRANSACTIONS[txn_id] = status


@router.post("/wompi", summary="Wompi webhook receiver")
async def wompi_webhook(request: Request) -> JSONResponse:
    """Receive Wompi events, validate the checksum, and record the transaction."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})

    events_secret = settings.WOMPI_EVENTS_SECRET
    if not events_secret:
        logger.error("WOMPI_EVENTS_SECRET is not configured")
        return JSONResponse(status_code=500, content={"error": "Webhook not configured"})

    if not validate_wompi_signature(body, events_secret):
        logger.warning("Invalid Wompi webhook signature received")
        return JSONResponse(status_code=401, content={"error": "Invalid signature"})

    # Process synchronously (fast, in-memory) then respond 200.
    try:
        _handle_event(body)
    except Exception:
        logger.exception("Error processing Wompi event")

    return JSONResponse(status_code=200, content={"received": True})
