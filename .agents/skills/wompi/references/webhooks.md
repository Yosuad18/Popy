# Wompi — Webhooks & Events

## Setup

Configure your webhook URL in the **Wompi dashboard** → Developers → "URL de eventos".

> Sandbox and Production have **separate webhook URL settings**. Configure both.

Requirements:
- Must be **HTTPS** (Wompi will not call HTTP endpoints)
- Must respond with **HTTP 200** within a reasonable time
- If no 200 is received, Wompi **retries** — handle idempotently

---

## Event Payload Structure

```json
{
  "event": "transaction.updated",
  "data": {
    "transaction": {
      "id": "01-1532941443-49201",
      "created_at": "2025-01-15T10:30:00.000Z",
      "finalized_at": "2025-01-15T10:30:45.000Z",
      "amount_in_cents": 5000000,
      "reference": "ORDER-001",
      "currency": "COP",
      "payment_method_type": "CARD",
      "payment_method": {
        "type": "CARD",
        "extra": {
          "bin": "411111",
          "name": "VISA-CREDIT",
          "brand": "VISA",
          "exp_year": "29",
          "exp_month": "12",
          "last_four": "1111",
          "card_holder": "JUAN PEREZ",
          "installments": 1
        }
      },
      "status": "APPROVED",
      "status_message": null,
      "customer_email": "juan@example.com",
      "merchant": { "name": "Mi Tienda" },
      "taxes": []
    }
  },
  "signature": {
    "checksum": "abc123def456...",
    "properties": ["transaction.id", "transaction.status", "transaction.amount_in_cents"]
  },
  "sent_at": "2025-01-15T10:30:46.000Z"
}
```

> `signature.properties` is **dynamic** — it can contain different fields for different events. Always read it from the event payload; never hardcode it.

---

## Checksum Validation

Formula: `SHA256( values_of_properties_in_order + events_secret )`

### Node.js (Express)

```js
const crypto = require('crypto');
const express = require('express');
const app = express();

/**
 * Validate Wompi webhook signature.
 * MUST be called before trusting any event data.
 */
function validateWompiSignature(body, eventsSecret) {
  const { signature, data } = body;

  if (!signature?.checksum || !Array.isArray(signature.properties)) {
    return false; // Malformed event
  }

  // Extract property values in the exact order listed in signature.properties
  const values = signature.properties.map(prop => {
    return prop.split('.').reduce((obj, key) => obj?.[key], data);
  });

  const str = [...values, eventsSecret].join('');
  const expected = crypto.createHash('sha256').update(str).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(signature.checksum));
}

app.post('/webhooks/wompi', express.json(), async (req, res) => {
  // 1. Validate signature — reject immediately if invalid
  if (!validateWompiSignature(req.body, process.env.WOMPI_EVENTS_SECRET)) {
    console.warn('Invalid Wompi webhook signature', { ip: req.ip });
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // 2. Respond 200 immediately — process async to avoid timeouts
  res.status(200).json({ received: true });

  // 3. Process event asynchronously
  try {
    await handleWompiEvent(req.body);
  } catch (err) {
    console.error('Webhook processing error:', err);
    // Don't throw — 200 already sent. Log and alert.
  }
});

async function handleWompiEvent({ event, data }) {
  if (event === 'transaction.updated') {
    const txn = data.transaction;

    // Idempotency: use transaction ID as dedup key
    const alreadyProcessed = await db.findProcessedEvent(txn.id);
    if (alreadyProcessed) return;

    switch (txn.status) {
      case 'APPROVED':
        await fulfillOrder(txn.reference);
        await db.markEventProcessed(txn.id, 'APPROVED');
        break;
      case 'DECLINED':
        await notifyCustomerDeclined(txn.reference, txn.customer_email);
        await db.markEventProcessed(txn.id, 'DECLINED');
        break;
      case 'VOIDED':
        await cancelOrder(txn.reference);
        await db.markEventProcessed(txn.id, 'VOIDED');
        break;
      case 'ERROR':
        await logPaymentError(txn);
        break;
    }
  }
}
```

### Python (Django)

```python
import hashlib, hmac, json, os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def validate_wompi_signature(body: dict, events_secret: str) -> bool:
    signature = body.get('signature', {})
    data = body.get('data', {})
    properties = signature.get('properties', [])
    checksum = signature.get('checksum', '')

    if not properties or not checksum:
        return False

    values = []
    for prop in properties:
        obj = data
        for key in prop.split('.'):
            obj = obj.get(key) if isinstance(obj, dict) else None
        values.append(str(obj) if obj is not None else '')

    string = ''.join(values) + events_secret
    expected = hashlib.sha256(string.encode('utf-8')).hexdigest()

    # Use hmac.compare_digest for timing-safe comparison
    return hmac.compare_digest(expected, checksum)


@csrf_exempt
@require_POST
def wompi_webhook(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not validate_wompi_signature(body, os.environ['WOMPI_EVENTS_SECRET']):
        return JsonResponse({'error': 'Invalid signature'}, status=401)

    # Respond 200 immediately
    response = JsonResponse({'received': True})

    # Process event (consider using Celery for production)
    event = body.get('event')
    if event == 'transaction.updated':
        txn = body['data']['transaction']
        process_transaction_update.delay(txn)  # async task

    return response
```

### PHP (Laravel)

```php
<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class WompiWebhookController extends Controller
{
    public function handle(Request $request): \Illuminate\Http\JsonResponse
    {
        $body = $request->all();

        if (!$this->validateSignature($body, env('WOMPI_EVENTS_SECRET'))) {
            Log::warning('Invalid Wompi webhook signature', ['ip' => $request->ip()]);
            return response()->json(['error' => 'Invalid signature'], 401);
        }

        // Respond 200 immediately
        if ($body['event'] === 'transaction.updated') {
            $txn = $body['data']['transaction'];
            dispatch(new ProcessWompiTransaction($txn));
        }

        return response()->json(['received' => true]);
    }

    private function validateSignature(array $body, string $eventsSecret): bool
    {
        $signature = $body['signature'] ?? [];
        $data = $body['data'] ?? [];
        $properties = $signature['properties'] ?? [];
        $checksum = $signature['checksum'] ?? '';

        if (empty($properties) || empty($checksum)) return false;

        $values = array_map(function ($prop) use ($data) {
            $keys = explode('.', $prop);
            $value = $data;
            foreach ($keys as $key) {
                $value = $value[$key] ?? null;
            }
            return (string)($value ?? '');
        }, $properties);

        $str = implode('', $values) . $eventsSecret;
        $expected = hash('sha256', $str);

        return hash_equals($expected, $checksum); // timing-safe
    }
}
```

---

## Idempotency Pattern

Wompi may deliver the same event more than once. Always deduplicate by `transaction.id`:

```sql
-- Migration: processed_events table
CREATE TABLE processed_wompi_events (
  transaction_id VARCHAR(64) PRIMARY KEY,
  status         VARCHAR(20) NOT NULL,
  processed_at   TIMESTAMP   NOT NULL DEFAULT NOW()
);
```

```js
// Node.js helper
async function processOnce(transactionId, status, handler) {
  const inserted = await db.query(
    `INSERT INTO processed_wompi_events (transaction_id, status)
     VALUES ($1, $2)
     ON CONFLICT (transaction_id) DO NOTHING
     RETURNING transaction_id`,
    [transactionId, status]
  );
  if (inserted.rowCount === 0) return; // Already processed
  await handler();
}
```

---

## Event Types

| Event | When |
|---|---|
| `transaction.updated` | Any transaction status change |
| `nequi_token.updated` | Nequi payment source status change |

---

## Testing Webhooks Locally

Use [ngrok](https://ngrok.com) or [localtunnel](https://localtunnel.me) to expose your local server:

```bash
# ngrok
npx ngrok http 3000

# Use the HTTPS URL in Wompi Sandbox dashboard → URL de eventos
# e.g. https://abc123.ngrok.io/webhooks/wompi
```

Or use [Wompi's webhook debugger](https://comercios.wompi.co) in the dashboard to inspect past event deliveries.
