---
name: wompi
description: >
  Expert developer guide and working code generator for Wompi, Colombia's leading payment gateway 
  (backed by Bancolombia). ALWAYS use this skill when the user mentions Wompi, wants to integrate 
  Colombian payments, or asks about PSE, Nequi, Daviplata, Bancolombia Button/QR/Transfer, card 
  tokenization, or accepting payments in COP. Also trigger for: Wompi API keys, integrity signatures, 
  Wompi webhooks/events, payment links in Colombia, transaction voiding/refunds, payment sources 
  (subscriptions/recurring billing), PCOL/Puntos Colombia, SU+ Pay, third-party payouts/dispersión 
  de pagos, taxes/IVA on transactions, sandbox testing, or production deployment checklist for Wompi. 
  Generates precise, secure, production-ready code in Node.js, Python, and PHP. Covers the full 
  gateway integration lifecycle end-to-end.
---

# Wompi — Complete Developer Skill

Wompi is Colombia's leading payment gateway, backed by Bancolombia. It processes COP payments via 
cards, PSE, Nequi, Daviplata, Bancolombia Button/QR, cash (Corresponsales), Puntos Colombia, and SU+ Pay.

**Docs:** https://docs.wompi.co | **Dashboard:** https://comercios.wompi.co

---

## Reference Files — Read These As Needed

| File | Read when... |
|---|---|
| `references/auth-and-security.md` | Setting up keys, generating signatures, securing the integration |
| `references/payment-methods.md` | Choosing or implementing a specific payment method |
| `references/transactions.md` | Creating transactions, polling status, handling voids |
| `references/webhooks.md` | Receiving and validating Wompi events |
| `references/payment-links.md` | Generating shareable payment links programmatically |
| `references/payment-sources.md` | Tokenization, subscriptions, recurring billing |
| `references/payouts.md` | Dispersión de pagos / third-party payments API |
| `references/taxes.md` | Sending IVA / consumption tax in transactions |
| `references/sandbox.md` | Sandbox testing data, simulating outcomes |
| `references/production-checklist.md` | Pre-launch security and integration checklist |
| `references/errors.md` | Error codes, retry logic, idempotency patterns |

---

## Environments & Keys (Quick Reference)

| Environment | API Base URL |
|---|---|
| **Sandbox** | `https://sandbox.wompi.co/v1` |
| **Production** | `https://production.wompi.co/v1` |

| Key | Prefix | Use |
|---|---|---|
| Public key | `pub_test_` / `pub_prod_` | Frontend only. Safe to expose. |
| Private key | `prv_test_` / `prv_prod_` | Server-side only. **Never expose.** |
| Integrity secret | `test_integrity_` / `prod_integrity_` | Sign transactions. Server-side only. |
| Events secret | `test_events_` / `prod_events_` | Validate webhooks. Server-side only. |

> ⚠️ Sandbox and Production are **completely independent** environments — separate keys, separate webhook URLs, separate dashboard settings.

---

## Amounts
All amounts are **Colombian pesos in cents** as integers.
`$35,000 COP → 3500000` | `$1,000 COP → 100000`

---

## Payment Methods Overview

| Method | `type` | Sync? | Notes |
|---|---|---|---|
| Credit/Debit Card | `CARD` | ✅ | Tokenization required; supports installments (credit only) |
| PSE Bank Transfer | `PSE` | ❌ Async | Requires bank list + ID; `redirect_url` required |
| Nequi | `NEQUI` | ❌ Async | Phone number; push notification; up to 10 min |
| Daviplata | `DAVIPLATA` | ❌ Async | OTP flow — see `references/payment-methods.md` |
| Bancolombia Button | `BANCOLOMBIA_TRANSFER` | ❌ Async | Redirects to Bancolombia app/web |
| Bancolombia QR | `BANCOLOMBIA_QR` | ❌ Async | Natural persons only; returns QR image URL |
| Cash Corresponsal | `BANCOLOMBIA_COLLECT` | ❌ Async | Cash at 15,000+ Bancolombia points |
| Puntos Colombia | `PCOL` | ❌ Async | Loyalty points; optional 2nd payment method |
| SU+ Pay | `SU_PLUS` | ❌ Async | Supermarket loyalty — redirect flow |

> For any **async** method: always start as `PENDING` → use webhooks or polling to get final status.

---

## Core Flow (Every Integration)

```
1. Server: Fetch acceptance tokens  →  GET /v1/merchants/:pub_key
2. Server: Generate integrity signature  →  SHA256(ref + amount + currency + secret)
3. Client/Server: Present payment UI  →  Widget, Checkout Web, or direct API
4. Server: Verify transaction  →  GET /v1/transactions/:id  (never trust redirect alone)
5. Server: Handle webhook  →  POST from Wompi → validate checksum → update order
```

---

## Integration Methods (Summary)

### Widget (Recommended — handles all complexity)
```html
<form>
  <script
    src="https://checkout.wompi.co/widget.js"
    data-render="button"
    data-public-key="pub_test_YOUR_KEY"
    data-currency="COP"
    data-amount-in-cents="5000000"
    data-reference="ORDER-001"
    data-signature:integrity="SERVER_GENERATED_HASH"
    data-redirect-url="https://yoursite.com/confirmation">
  </script>
</form>
```

### Web Checkout (Redirect)
```html
<form method="GET" action="https://checkout.wompi.co/p/">
  <input type="hidden" name="public-key"        value="pub_test_YOUR_KEY" />
  <input type="hidden" name="currency"           value="COP" />
  <input type="hidden" name="amount-in-cents"    value="5000000" />
  <input type="hidden" name="reference"          value="ORDER-001" />
  <input type="hidden" name="signature:integrity" value="SERVER_GENERATED_HASH" />
  <input type="hidden" name="redirect-url"       value="https://yoursite.com/ok" />
  <button type="submit">Pagar con Wompi</button>
</form>
```

### Direct API
See `references/transactions.md` for complete server-side transaction creation in Node.js, Python, and PHP.

---

## Transaction Statuses

| Status | Meaning | Action |
|---|---|---|
| `PENDING` | Awaiting action or processing | Poll or wait for webhook |
| `APPROVED` | Payment successful ✅ | Fulfill order |
| `DECLINED` | Rejected by bank ❌ | Notify customer; allow retry |
| `VOIDED` | Annulled (cards only) | Update order; no refund via API |
| `ERROR` | Payment method error | Log; allow retry |

---

## Common Mistakes — Never Do These

1. **Private key or integrity secret in frontend code** — attackers can forge any transaction amount.
2. **Generating integrity signature on the frontend** — same consequence as above.
3. **Trusting redirect URL `?id=` to confirm payment** — easily spoofed; always verify server-side.
4. **Reusing references** — must be unique per Wompi account, ever.
5. **Skipping acceptance tokens on API calls** — violates Colombian Habeas Data law; call will fail.
6. **Hardcoding `signature.properties`** in webhook handler — array changes; always read dynamically.
7. **Same webhook URL for Sandbox and Production** — configure them separately in the dashboard.
8. **Not polling / not using webhooks for async methods** — PSE/Nequi/QR always start as `PENDING`.
9. **Adding taxes on top of `amount_in_cents`** — taxes are **included in** the total, not added to it.
10. **Reusing card tokens across merchants** — tokens are merchant-scoped and expire.
