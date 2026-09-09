# Wompi — Production Go-Live Checklist

Run through this checklist before switching from sandbox to production.

---

## Security

- [ ] **All secrets in environment variables** — `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET` (and payout keys if applicable)
- [ ] **No secrets in git** — run `git log --all -S "prv_prod_"` and `git log --all -S "prod_integrity_"` to confirm
- [ ] **No secrets in client-side code** — grep your JS bundle / frontend code
- [ ] **Integrity signature generated server-side only**
- [ ] **Private key never logged** — check your log aggregator
- [ ] **HTTPS enforced everywhere** — API calls, webhook endpoint, checkout redirect URLs
- [ ] **TLS certificate validation enabled** — `verify=True` in Python, default behavior in Node.js
- [ ] **Webhook endpoint is HTTPS**

---

## Keys

- [ ] Switched to **production keys** (`pub_prod_`, `prv_prod_`, `prod_integrity_`, `prod_events_`)
- [ ] Sandbox keys (`pub_test_`, `prv_test_`) **not present** in production config
- [ ] **API base URL** set to `https://production.wompi.co/v1`
- [ ] Widget/Checkout public key updated to `pub_prod_` key
- [ ] Keys obtained from the **Production** section of the Wompi dashboard (not Sandbox)

---

## Webhook

- [ ] **Production webhook URL configured** in Wompi dashboard → Developers → URL de eventos → Production tab
- [ ] Webhook endpoint responds with **HTTP 200** reliably and quickly (< 5 seconds)
- [ ] Webhook **signature validation** enabled and tested with production events secret
- [ ] **Idempotency** implemented — duplicate events don't cause double-fulfillment
- [ ] Webhook processing is **async** (queue) to avoid timeouts on slow operations

---

## Transactions

- [ ] **Acceptance tokens** fetched fresh before each transaction creation
- [ ] **Transaction verified server-side** after redirect — never trust `?id=` alone
- [ ] **Unique references** generated per transaction — no reuse ever
- [ ] **Async payment methods polled** (PSE, Nequi, QR) or handled via webhook
- [ ] **Error handling** implemented for all Wompi API calls
- [ ] **Retry logic** for 5xx errors with exponential backoff
- [ ] **No double-charge risk** — idempotent transaction creation pattern in place

---

## Testing Completed

- [ ] Successful card payment end-to-end in sandbox
- [ ] Declined card handled gracefully
- [ ] At least one async method tested (PSE or Nequi)
- [ ] Webhook received and validated in sandbox
- [ ] Duplicate webhook event handled correctly
- [ ] Payment source / tokenization flow tested (if used)
- [ ] Payment links working (if used)
- [ ] All error responses handled (401, 404, 422)

---

## Dashboard

- [ ] Registered and verified at [comercios.wompi.co](https://comercios.wompi.co)
- [ ] Business information complete (required for production approval)
- [ ] Bank account for settlements configured
- [ ] Notification email set for payment alerts
- [ ] Webhook event URL set for **Production** environment (separate from Sandbox)
- [ ] If using Third-Party Payments: feature activated and API keys obtained

---

## Compliance

- [ ] Acceptance token (`presigned_acceptance`) shown to customers before card tokenization (Habeas Data)
- [ ] Personal data auth (`presigned_personal_data_auth`) token included in API transactions
- [ ] Privacy policy on your site describes how payment data is processed
- [ ] PCI compliance: card numbers never touch your servers (handled by Wompi Widget/tokenization)

---

## Monitoring

- [ ] Logging enabled for all Wompi API calls (method, URL, status, duration, reference)
- [ ] Alerts set for DECLINED rate spikes
- [ ] Alerts set for any 401 errors in production (possible key leak)
- [ ] Alerts set for webhook validation failures
- [ ] Wompi status page bookmarked: check https://status.wompi.co (or contact support)

---

## Incident Response

- [ ] Know how to **rotate all Wompi keys** quickly in case of suspected compromise
- [ ] Contact info for Wompi support saved: https://wompi.co/contacto
- [ ] Runbook exists for: payment processing outage, webhook delivery failure, key rotation

---

## Final Smoke Test in Production

After go-live, run a real low-amount test transaction ($500–$1,000 COP) end-to-end:

1. Create transaction with production keys
2. Complete payment (use your own card)
3. Verify webhook received and processed
4. Verify order fulfilled correctly in your system
5. Verify transaction appears in Wompi production dashboard
