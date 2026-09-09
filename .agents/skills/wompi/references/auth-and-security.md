# Wompi — Authentication & Security

## API Key Management

### Key Types
| Key | Prefix | Where | Never |
|---|---|---|---|
| Public key | `pub_test_` / `pub_prod_` | Frontend, Widget, Checkout form | — |
| Private key | `prv_test_` / `prv_prod_` | Server HTTP header `Authorization: Bearer` | In client code, git, logs |
| Integrity secret | `test_integrity_` / `prod_integrity_` | Server: signature generation only | In client code, git, logs |
| Events secret | `test_events_` / `prod_events_` | Server: webhook validation only | In client code, git, logs |

### Secure Key Storage
Store secrets in **environment variables**, never hardcoded:

```bash
# .env (never commit to git — add to .gitignore)
WOMPI_PUBLIC_KEY=pub_prod_...
WOMPI_PRIVATE_KEY=prv_prod_...
WOMPI_INTEGRITY_SECRET=prod_integrity_...
WOMPI_EVENTS_SECRET=prod_events_...
```

**Node.js:**
```js
// Load with dotenv in dev; use platform secrets manager in production
require('dotenv').config();
const WOMPI_PRIVATE_KEY = process.env.WOMPI_PRIVATE_KEY;
if (!WOMPI_PRIVATE_KEY) throw new Error('WOMPI_PRIVATE_KEY is not set');
```

**Python:**
```python
import os
WOMPI_PRIVATE_KEY = os.environ['WOMPI_PRIVATE_KEY']  # Raises KeyError if missing — good
```

---

## Integrity Signature

Required on **every transaction**. Prevents tampering with amount or reference.

### Formula
```
SHA256( reference + amount_in_cents + currency + integrity_secret )
```
If `expiration_time` is set on the Widget/Checkout:
```
SHA256( reference + amount_in_cents + currency + expiration_time + integrity_secret )
```

### Implementation

**Node.js:**
```js
const crypto = require('crypto');

/**
 * Generate Wompi integrity signature.
 * @param {string} reference - Unique order reference
 * @param {number} amountInCents - Integer, e.g. 3500000 for $35,000 COP
 * @param {string} currency - Always 'COP'
 * @param {string} integritySecret - From env, never expose
 * @param {string|null} expirationTime - ISO 8601 string, only if used in Widget
 */
function getIntegritySignature(reference, amountInCents, currency, integritySecret, expirationTime = null) {
  const parts = [reference, amountInCents, currency];
  if (expirationTime) parts.push(expirationTime);
  parts.push(integritySecret);
  return crypto.createHash('sha256').update(parts.join('')).digest('hex');
}
```

**Python:**
```python
import hashlib

def get_integrity_signature(reference, amount_in_cents, currency, integrity_secret, expiration_time=None):
    parts = [str(reference), str(amount_in_cents), currency]
    if expiration_time:
        parts.append(expiration_time)
    parts.append(integrity_secret)
    data = ''.join(parts)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
```

**PHP:**
```php
function getIntegritySignature(string $reference, int $amountInCents, string $currency, string $integritySecret, ?string $expirationTime = null): string {
    $parts = [$reference, (string)$amountInCents, $currency];
    if ($expirationTime !== null) $parts[] = $expirationTime;
    $parts[] = $integritySecret;
    return hash('sha256', implode('', $parts));
}
```

> ⚠️ Always generate signatures **server-side**. If you generate on the frontend, the integrity secret is exposed and attackers can craft arbitrary amounts.

---

## Acceptance Tokens (Habeas Data Compliance)

Colombian Law 1581/2012 (Habeas Data) requires explicit consent before storing or processing personal data. Wompi enforces this via acceptance tokens on all direct API transactions.

### Fetch Tokens
```js
// Node.js — always fetch fresh; tokens expire
async function getAcceptanceTokens(publicKey, baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/merchants/${publicKey}`);
  if (!res.ok) throw new Error(`Failed to fetch merchant: ${res.status}`);
  const { data } = await res.json();
  return {
    acceptanceToken: data.presigned_acceptance.acceptance_token,
    personalDataAuth: data.presigned_personal_data_auth.acceptance_token,
  };
}
```

```python
# Python
import requests

def get_acceptance_tokens(public_key, base_url='https://production.wompi.co/v1'):
    res = requests.get(f'{base_url}/merchants/{public_key}')
    res.raise_for_status()
    data = res.json()['data']
    return {
        'acceptance_token': data['presigned_acceptance']['acceptance_token'],
        'personal_data_auth': data['presigned_personal_data_auth']['acceptance_token'],
    }
```

### Required Fields on Every POST /v1/transactions and POST /v1/payment_sources
```json
{
  "acceptance_token": "<presigned_acceptance.acceptance_token>",
  "accept_personal_auth": "<presigned_personal_data_auth.acceptance_token>"
}
```

---

## Transport Security

- All Wompi API calls **must use HTTPS** (TLS 1.2+). Never call over HTTP.
- Validate TLS certificates — do not disable certificate verification in production.
- Your webhook endpoint must also be HTTPS.

**Node.js — enforce TLS in fetch:**
The built-in `fetch` (Node 18+) validates certificates by default. For older environments:
```js
const https = require('https');
const agent = new https.Agent({ rejectUnauthorized: true }); // default, but explicit
```

**Python — never do this in production:**
```python
# ❌ NEVER in production
requests.post(url, json=body, verify=False)

# ✅ Always
requests.post(url, json=body, verify=True)  # default
```

---

## Protecting Your Webhook Endpoint

1. **Always validate the checksum** before trusting any event (see `references/webhooks.md`).
2. **Use HTTPS only** — Wompi will not POST to HTTP endpoints.
3. **Respond 200 quickly** — do heavy processing asynchronously (queue job, etc.). If Wompi doesn't receive 200, it retries.
4. **Idempotency** — the same event may be delivered more than once. Use the `transaction.id` as an idempotency key in your database:
```js
// Postgres example
await db.query(
  `INSERT INTO processed_events (transaction_id, status, processed_at)
   VALUES ($1, $2, NOW())
   ON CONFLICT (transaction_id) DO NOTHING`,
  [txn.id, txn.status]
);
```

---

## Unique References

Every transaction must use a **unique reference** per Wompi account. A good pattern:

```js
// Combine order ID + timestamp to guarantee uniqueness
function generateReference(orderId) {
  return `ORD-${orderId}-${Date.now()}`;
}
```

Trying to reuse a reference returns a 422 `INPUT_VALIDATION_ERROR` with `"reference": ["has already been taken"]`.

---

## Security Checklist for Wompi Integrations

- [ ] Private key and secrets stored in environment variables / secrets manager
- [ ] No secrets in git history (`git log --all -S "prv_prod_"` to verify)
- [ ] Integrity signature generated server-side only
- [ ] Acceptance tokens fetched fresh per transaction
- [ ] Webhook checksum validated before any order update
- [ ] Transaction verified via `GET /v1/transactions/:id` after redirect
- [ ] All API calls and webhook endpoint use HTTPS
- [ ] Idempotency handled on webhook handler (de-duplicate by `transaction.id`)
- [ ] Unique references used for every transaction
- [ ] Sandbox key prefixes (`pub_test_`, `prv_test_`) never used in production
- [ ] Separate webhook URLs configured for Sandbox and Production in dashboard
