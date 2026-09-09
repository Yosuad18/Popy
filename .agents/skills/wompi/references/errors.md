# Wompi — Error Handling, Retries & Idempotency

## Error Response Structure

```json
{
  "error": {
    "type": "INPUT_VALIDATION_ERROR",
    "messages": {
      "reference": ["has already been taken"],
      "amount_in_cents": ["must be greater than 0"],
      "payment_method.token": ["is invalid or expired"]
    }
  }
}
```

---

## HTTP Error Codes

| HTTP | `error.type` | Meaning | Action |
|---|---|---|---|
| `400` | `BAD_REQUEST` | Malformed request body | Fix JSON structure |
| `401` | `INVALID_ACCESS_TOKEN` | Wrong/missing key | Check key prefix matches environment |
| `404` | `NOT_FOUND_ERROR` | Resource doesn't exist | Verify ID |
| `409` | `CONFLICT` | Duplicate reference or idempotency conflict | Use unique reference |
| `422` | `INPUT_VALIDATION_ERROR` | Invalid field values | Read `messages` for details |
| `429` | `RATE_LIMITED` | Too many requests | Backoff and retry |
| `500` | Various | Wompi server error | Retry with exponential backoff |
| `503` | `SERVICE_UNAVAILABLE` | Wompi down | Retry later; check status page |

---

## Error Handler Wrapper

### Node.js
```js
class WompiError extends Error {
  constructor(type, status, messages) {
    super(type);
    this.name = 'WompiError';
    this.type = type;
    this.status = status;
    this.messages = messages ?? {};
  }

  isValidationError() { return this.status === 422; }
  isDuplicateReference() {
    return this.status === 422 && this.messages?.reference?.includes('has already been taken');
  }
  isAuthError() { return this.status === 401; }
  isRateLimited() { return this.status === 429; }
  isServerError() { return this.status >= 500; }
}

async function wompiRequest(url, options = {}) {
  const res = await fetch(url, options);
  const body = await res.json();

  if (!res.ok) {
    throw new WompiError(
      body.error?.type ?? 'UNKNOWN_ERROR',
      res.status,
      body.error?.messages
    );
  }

  return body;
}
```

### Python
```python
import requests

class WompiError(Exception):
    def __init__(self, error_type, status, messages=None):
        super().__init__(error_type)
        self.type = error_type
        self.status = status
        self.messages = messages or {}

    @property
    def is_validation_error(self): return self.status == 422
    @property
    def is_duplicate_reference(self):
        return self.status == 422 and 'has already been taken' in str(self.messages.get('reference', []))
    @property
    def is_auth_error(self): return self.status == 401
    @property
    def is_rate_limited(self): return self.status == 429
    @property
    def is_server_error(self): return self.status >= 500


def wompi_request(method, url, headers, **kwargs):
    res = requests.request(method, url, headers=headers, **kwargs)
    if not res.ok:
        err = res.json().get('error', {})
        raise WompiError(
            err.get('type', 'UNKNOWN_ERROR'),
            res.status_code,
            err.get('messages')
        )
    return res.json()
```

---

## Retry with Exponential Backoff

Only retry on transient errors (5xx, 429). Never auto-retry 4xx errors (fix the request first).

### Node.js
```js
async function wompiRequestWithRetry(url, options = {}, { maxRetries = 3, baseDelayMs = 1000 } = {}) {
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await wompiRequest(url, options);
    } catch (err) {
      lastError = err;

      // Don't retry client errors
      if (err instanceof WompiError && !err.isRateLimited() && !err.isServerError()) {
        throw err;
      }

      if (attempt < maxRetries) {
        const delay = baseDelayMs * Math.pow(2, attempt) + Math.random() * 200; // jitter
        console.warn(`Wompi request failed (attempt ${attempt + 1}), retrying in ${Math.round(delay)}ms...`);
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }

  throw lastError;
}
```

### Python
```python
import time, random

def wompi_request_with_retry(method, url, headers, max_retries=3, base_delay_s=1, **kwargs):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return wompi_request(method, url, headers, **kwargs)
        except WompiError as e:
            last_error = e
            if not (e.is_rate_limited or e.is_server_error):
                raise  # Don't retry client errors
            if attempt < max_retries:
                delay = base_delay_s * (2 ** attempt) + random.uniform(0, 0.2)
                time.sleep(delay)
    raise last_error
```

---

## Idempotency

### Transaction References
- Every transaction reference must be globally unique per Wompi account
- If a network error occurs during `POST /v1/transactions`, you don't know if Wompi processed it
- **Never blindly retry** a transaction creation — you might double-charge
- Instead: check if a transaction with that reference already exists, then decide

```js
async function safeCreateTransaction(params) {
  const reference = params.reference;

  try {
    return await wompiRequest(`${params.baseUrl}/transactions`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${params.privateKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(params.body),
    });
  } catch (err) {
    if (err instanceof WompiError && err.isDuplicateReference()) {
      // Transaction may have been created — look it up by reference
      // (Wompi doesn't have a GET /transactions?reference= endpoint — check your own DB)
      const existing = await db.getTransactionByReference(reference);
      if (existing) return existing;
    }
    throw err;
  }
}
```

### Webhook Idempotency
Always store processed event IDs to prevent double-fulfillment:

```js
// Pattern: INSERT ... ON CONFLICT DO NOTHING
async function processWebhookOnce(transactionId, status, handler) {
  const result = await db.query(
    `INSERT INTO wompi_processed_events (transaction_id, status, created_at)
     VALUES ($1, $2, NOW())
     ON CONFLICT (transaction_id) DO NOTHING
     RETURNING 1`,
    [transactionId, status]
  );

  if (result.rowCount === 0) {
    console.log(`Event ${transactionId} already processed — skipping`);
    return;
  }

  await handler();
}
```

---

## Common Validation Errors and Fixes

| Error | `messages` value | Fix |
|---|---|---|
| Duplicate reference | `reference: ["has already been taken"]` | Generate a new unique reference |
| Invalid token | `payment_method.token: ["is invalid or expired"]` | Re-tokenize the card; tokens are single-use |
| Invalid amount | `amount_in_cents: ["must be greater than 0"]` | Ensure positive integer > 0 |
| Missing acceptance token | `acceptance_token: ["can't be blank"]` | Fetch fresh tokens from `/merchants/:pub_key` |
| Wrong environment | 401 INVALID_ACCESS_TOKEN | Verify key prefix matches API URL (test ↔ prod) |
| Invalid installments | `payment_method.installments: [...]` | Use 1 for debit cards; check merchant config |
| PSE missing redirect_url | `redirect_url: ["can't be blank"]` | Required for PSE, BANCOLOMBIA_TRANSFER |

---

## Monitoring Recommendations

```js
// Structured logging for all Wompi API calls
async function trackedWompiRequest(url, options, context = {}) {
  const start = Date.now();
  try {
    const result = await wompiRequestWithRetry(url, options);
    console.info('wompi_request_success', {
      url, duration_ms: Date.now() - start, ...context
    });
    return result;
  } catch (err) {
    console.error('wompi_request_error', {
      url, error_type: err.type, status: err.status,
      duration_ms: Date.now() - start, ...context
    });
    throw err;
  }
}
```

Alert on:
- High rate of `DECLINED` transactions (possible fraud or misconfiguration)
- Any `401` in production (key rotation needed or leak)
- `5xx` errors from Wompi (service degradation)
- Webhook validation failures (possible replay attack or misconfigured secret)
