# Wompi — Sandbox Testing

Sandbox is a fully isolated test environment. No real money moves. Use it to build and verify your integration before going live.

**Sandbox API base:** `https://sandbox.wompi.co/v1`
**Keys:** Use `pub_test_`, `prv_test_`, `test_integrity_`, `test_events_` prefixes.

---

## Test Card Numbers

| Card Network | Number | Type | CVV | Expiry | Result |
|---|---|---|---|---|---|
| Visa | `4111111111111111` | Credit | Any ≠ `111` | Any future | APPROVED |
| Mastercard | `5204730000001003` | Credit | Any ≠ `111` | Any future | APPROVED |
| Any card | Any valid | Any | `111` | Any future | DECLINED |

**3DS testing:** The sandbox Widget may simulate 3DS — follow the prompts.

---

## Simulate Non-Card Payment Outcomes

For async payment methods (PSE, Nequi, Bancolombia QR/Button, PCOL, etc.), pass `sandbox_status` inside `payment_method`:

```json
{
  "payment_method": {
    "type": "BANCOLOMBIA_QR",
    "payment_description": "Test",
    "sandbox_status": "APPROVED"
  }
}
```

| `sandbox_status` | Works with |
|---|---|
| `"APPROVED"` | PSE, NEQUI, BANCOLOMBIA_TRANSFER, BANCOLOMBIA_QR, BANCOLOMBIA_COLLECT, SU_PLUS |
| `"DECLINED"` | Same as above |
| `"ERROR"` | Same as above |

### PCOL (Puntos Colombia) Sandbox Statuses

```json
{ "payment_method": { "type": "PCOL", "sandbox_status": "APPROVED_ONLY_POINTS" } }
```

| `sandbox_status` | Meaning |
|---|---|
| `APPROVED_ONLY_POINTS` | 100% paid with points |
| `APPROVED_HALF_POINTS` | 50% points + 50% second payment method |
| `DECLINED` | Declined |
| `ERROR` | Error |

---

## Nequi Sandbox Phone Numbers

| Phone | Result |
|---|---|
| `3991111111` | APPROVED |
| Any other valid number | Pending (requires manual approval in sandbox portal) |

---

## Third-Party Payouts Sandbox

```json
{
  "transactions": [{
    "legalIdType": "CC",
    "legalId": "1234567890",
    "bankId": "bank-uuid",
    "accountType": "AHORROS",
    "accountNumber": "1234567890",
    "amount_in_cents": 50000000,
    "reference": "TEST-PAYOUT-001",
    "description": "Test payout",
    "transactionStatus": "APPROVED"
  }]
}
```

Omit `transactionStatus` to default to `APPROVED`.

---

## Testing Webhooks Locally

### Option 1: ngrok
```bash
npx ngrok http 3000
# Copy the HTTPS URL → paste in Wompi Sandbox dashboard → URL de eventos
```

### Option 2: localtunnel
```bash
npx localtunnel --port 3000
```

### Option 3: Simulate locally
Write a test that calls your webhook handler directly with a crafted payload and valid checksum:

```js
// Node.js test helper
const crypto = require('crypto');

function buildWompiWebhookPayload(transactionData, eventsSecret) {
  const properties = ['transaction.id', 'transaction.status', 'transaction.amount_in_cents'];
  const values = properties.map(prop =>
    prop.split('.').reduce((obj, key) => obj?.[key], { transaction: transactionData })
  );
  const checksum = crypto.createHash('sha256').update([...values, eventsSecret].join('')).digest('hex');

  return {
    event: 'transaction.updated',
    data: { transaction: transactionData },
    signature: { checksum, properties },
    sent_at: new Date().toISOString(),
  };
}

// Usage in tests
const payload = buildWompiWebhookPayload({
  id: 'test-txn-001',
  status: 'APPROVED',
  amount_in_cents: 5000000,
  reference: 'ORDER-TEST-001',
  currency: 'COP',
  payment_method_type: 'CARD',
  customer_email: 'test@example.com',
}, process.env.WOMPI_EVENTS_SECRET);

// POST payload to your webhook handler in your test
```

---

## Integration Test Checklist

Before going to production, verify each scenario in sandbox:

### Card Payments
- [ ] Successful card payment (APPROVED)
- [ ] Declined card payment (CVV `111`)
- [ ] Widget renders correctly and redirects to `redirect-url`
- [ ] Transaction verified server-side after redirect
- [ ] Webhook received and processed for APPROVED
- [ ] Webhook received and processed for DECLINED

### Async Methods (PSE / Nequi / QR)
- [ ] Transaction created — starts as PENDING
- [ ] Customer redirect / push notification simulated
- [ ] Webhook received when status changes to APPROVED
- [ ] Polling fallback works correctly

### Payment Sources / Subscriptions
- [ ] Card tokenized via Widget
- [ ] Payment source created with `payment_source_id`
- [ ] Recurring charge against `payment_source_id` succeeds
- [ ] Payment source voided correctly

### Payment Links
- [ ] Link created with correct amount
- [ ] Link URL opens Wompi checkout
- [ ] Single-use link disabled after APPROVED payment
- [ ] Webhook received for payment link transaction

### Webhooks
- [ ] Checksum validated correctly
- [ ] Duplicate events handled idempotently (same `transaction.id`)
- [ ] Server responds 200 in < 5 seconds

### Error Handling
- [ ] 422 validation error handled gracefully
- [ ] 401 unauthorized handled (wrong key)
- [ ] Network timeout handled with retry logic

---

## Sandbox Limitations vs Production

| Feature | Sandbox | Production |
|---|---|---|
| Real money | No | Yes |
| 3DS authentication | Simulated | Real bank flow |
| Nequi push notification | Simulated | Real app notification |
| PSE bank redirect | Sandbox simulation | Real bank |
| Daviplata OTP | Sandbox flow | Real SMS |
| Settlement / payouts | No real transfer | Real bank transfer |
