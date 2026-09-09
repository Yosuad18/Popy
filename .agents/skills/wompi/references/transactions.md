# Wompi — Transactions

## Creating a Card Transaction (Direct API)

### Prerequisites
1. Card token from Widget tokenization (see `references/payment-sources.md`)
2. Fresh acceptance tokens (see `references/auth-and-security.md`)
3. Integrity signature generated server-side

### Node.js
```js
const crypto = require('crypto');

async function createTransaction({
  privateKey,
  publicKey,
  amountInCents,
  reference,
  customerEmail,
  cardToken,
  installments = 1,
  taxes = [],         // see references/taxes.md
  baseUrl = 'https://production.wompi.co/v1'
}) {
  // 1. Fetch acceptance tokens (required by Colombian law)
  const merchantRes = await fetch(`${baseUrl}/merchants/${publicKey}`);
  const { data: merchant } = await merchantRes.json();
  const acceptanceToken = merchant.presigned_acceptance.acceptance_token;
  const personalDataAuth = merchant.presigned_personal_data_auth.acceptance_token;

  // 2. Generate integrity signature server-side
  const integrityStr = `${reference}${amountInCents}COP${process.env.WOMPI_INTEGRITY_SECRET}`;
  const signature = crypto.createHash('sha256').update(integrityStr).digest('hex');

  // 3. Create transaction
  const res = await fetch(`${baseUrl}/transactions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${privateKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      amount_in_cents: amountInCents,
      currency: 'COP',
      signature,
      customer_email: customerEmail,
      reference,
      acceptance_token: acceptanceToken,
      accept_personal_auth: personalDataAuth,
      payment_method: {
        type: 'CARD',
        token: cardToken,
        installments,
      },
      ...(taxes.length > 0 && { taxes }),
    }),
  });

  const body = await res.json();
  if (!res.ok) {
    const err = new Error(body.error?.type ?? 'WOMPI_ERROR');
    err.status = res.status;
    err.details = body.error;
    throw err;
  }
  return body.data;
}
```

### Python
```python
import hashlib, os, requests

def create_card_transaction(private_key, public_key, amount_in_cents, reference,
                             customer_email, card_token, installments=1,
                             taxes=None, base_url='https://production.wompi.co/v1'):
    # 1. Fetch acceptance tokens
    merchant = requests.get(f'{base_url}/merchants/{public_key}').json()['data']
    acceptance_token = merchant['presigned_acceptance']['acceptance_token']
    personal_data_auth = merchant['presigned_personal_data_auth']['acceptance_token']

    # 2. Generate integrity signature
    integrity_str = f"{reference}{amount_in_cents}COP{os.environ['WOMPI_INTEGRITY_SECRET']}"
    signature = hashlib.sha256(integrity_str.encode()).hexdigest()

    # 3. Create transaction
    payload = {
        'amount_in_cents': amount_in_cents,
        'currency': 'COP',
        'signature': signature,
        'customer_email': customer_email,
        'reference': reference,
        'acceptance_token': acceptance_token,
        'accept_personal_auth': personal_data_auth,
        'payment_method': {
            'type': 'CARD',
            'token': card_token,
            'installments': installments,
        },
    }
    if taxes:
        payload['taxes'] = taxes

    res = requests.post(
        f'{base_url}/transactions',
        headers={'Authorization': f'Bearer {private_key}'},
        json=payload
    )
    res.raise_for_status()
    return res.json()['data']
```

### PHP
```php
function createCardTransaction(array $params): array {
    $baseUrl = $params['base_url'] ?? 'https://production.wompi.co/v1';

    // 1. Fetch acceptance tokens
    $merchant = json_decode(file_get_contents("{$baseUrl}/merchants/{$params['public_key']}"), true)['data'];
    $acceptanceToken = $merchant['presigned_acceptance']['acceptance_token'];
    $personalDataAuth = $merchant['presigned_personal_data_auth']['acceptance_token'];

    // 2. Generate integrity signature
    $integrityStr = $params['reference'] . $params['amount_in_cents'] . 'COP' . getenv('WOMPI_INTEGRITY_SECRET');
    $signature = hash('sha256', $integrityStr);

    // 3. Build payload
    $payload = [
        'amount_in_cents'   => $params['amount_in_cents'],
        'currency'          => 'COP',
        'signature'         => $signature,
        'customer_email'    => $params['customer_email'],
        'reference'         => $params['reference'],
        'acceptance_token'  => $acceptanceToken,
        'accept_personal_auth' => $personalDataAuth,
        'payment_method'    => [
            'type'         => 'CARD',
            'token'        => $params['card_token'],
            'installments' => $params['installments'] ?? 1,
        ],
    ];

    $ch = curl_init("{$baseUrl}/transactions");
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($payload),
        CURLOPT_HTTPHEADER     => [
            'Authorization: Bearer ' . $params['private_key'],
            'Content-Type: application/json',
        ],
    ]);
    $res = json_decode(curl_exec($ch), true);
    curl_close($ch);
    return $res['data'];
}
```

---

## Creating a PSE Transaction

```js
// Node.js
async function createPSETransaction({
  privateKey, publicKey, amountInCents, reference,
  customerEmail, customerName, customerPhone,
  userLegalIdType, userLegalId, userType,
  financialInstitutionCode, redirectUrl,
  baseUrl = 'https://production.wompi.co/v1'
}) {
  const { data: merchant } = await fetch(`${baseUrl}/merchants/${publicKey}`).then(r => r.json());
  const integrityStr = `${reference}${amountInCents}COP${process.env.WOMPI_INTEGRITY_SECRET}`;
  const signature = require('crypto').createHash('sha256').update(integrityStr).digest('hex');

  const res = await fetch(`${baseUrl}/transactions`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${privateKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      amount_in_cents: amountInCents,
      currency: 'COP',
      signature,
      customer_email: customerEmail,
      customer_data: { phone_number: customerPhone, full_name: customerName },
      reference,
      acceptance_token: merchant.presigned_acceptance.acceptance_token,
      accept_personal_auth: merchant.presigned_personal_data_auth.acceptance_token,
      redirect_url: redirectUrl, // required for PSE
      payment_method: {
        type: 'PSE',
        user_type: userType, // 0 = natural person, 1 = legal entity
        user_legal_id_type: userLegalIdType, // CC | NIT | CE | PASSPORT | TI | RC | DE
        user_legal_id: userLegalId,
        financial_institution_code: financialInstitutionCode,
        payment_description: `Order ${reference}`.substring(0, 64), // max 64 chars
      },
    }),
  });
  return (await res.json()).data;
}

// Get bank list (cache this — it changes infrequently)
async function getPSEBanks(baseUrl = 'https://production.wompi.co/v1') {
  const { data } = await fetch(`${baseUrl}/pse/financial_institutions`).then(r => r.json());
  return data; // [{ financial_institution_code, financial_institution_name }]
}
```

---

## Creating a Nequi Transaction

```js
async function createNequiTransaction({
  privateKey, publicKey, amountInCents, reference, customerEmail, phoneNumber,
  baseUrl = 'https://production.wompi.co/v1'
}) {
  const { data: merchant } = await fetch(`${baseUrl}/merchants/${publicKey}`).then(r => r.json());
  const signature = require('crypto').createHash('sha256')
    .update(`${reference}${amountInCents}COP${process.env.WOMPI_INTEGRITY_SECRET}`).digest('hex');

  const res = await fetch(`${baseUrl}/transactions`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${privateKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      amount_in_cents: amountInCents,
      currency: 'COP',
      signature,
      customer_email: customerEmail,
      reference,
      acceptance_token: merchant.presigned_acceptance.acceptance_token,
      accept_personal_auth: merchant.presigned_personal_data_auth.acceptance_token,
      payment_method: { type: 'NEQUI', phone_number: phoneNumber },
    }),
  });
  return (await res.json()).data;
  // Returns PENDING — user gets push notification on Nequi app
  // Poll or use webhook to get final status
}
```

---

## Fetching a Transaction

```js
// Node.js
async function getTransaction(transactionId, baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/transactions/${transactionId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()).data;
}
```

```python
# Python
def get_transaction(transaction_id, base_url='https://production.wompi.co/v1'):
    res = requests.get(f'{base_url}/transactions/{transaction_id}')
    res.raise_for_status()
    return res.json()['data']
```

---

## Polling for Final Status (Async Methods)

Use for PSE, Nequi, Bancolombia QR/Button, PCOL, SU+:

```js
// Node.js — exponential backoff polling
async function pollUntilFinal(transactionId, { maxAttempts = 20, baseDelayMs = 2000, baseUrl } = {}) {
  const FINAL = new Set(['APPROVED', 'DECLINED', 'VOIDED', 'ERROR']);

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const txn = await getTransaction(transactionId, baseUrl);
    if (FINAL.has(txn.status)) return txn;

    // Exponential backoff: 2s, 4s, 8s... capped at 30s
    const delay = Math.min(baseDelayMs * Math.pow(2, attempt), 30000);
    await new Promise(r => setTimeout(r, delay));
  }
  throw new Error(`Transaction ${transactionId} did not reach final status after ${maxAttempts} attempts`);
}
```

```python
# Python
import time

def poll_until_final(transaction_id, max_attempts=20, base_delay_s=2, base_url='https://production.wompi.co/v1'):
    FINAL = {'APPROVED', 'DECLINED', 'VOIDED', 'ERROR'}
    for attempt in range(max_attempts):
        txn = get_transaction(transaction_id, base_url)
        if txn['status'] in FINAL:
            return txn
        delay = min(base_delay_s * (2 ** attempt), 30)
        time.sleep(delay)
    raise TimeoutError(f'Transaction {transaction_id} did not reach final status')
```

> **Prefer webhooks** over polling in production. Use polling only as a fallback or for user-facing status updates.

---

## Voiding / Refunds

**Wompi does not expose a public API endpoint to programmatically void or refund a transaction.**

- `VOIDED` status is applied by Wompi internally (cards only, within the same business day)
- For refunds after settlement, use the Wompi merchant dashboard or contact Wompi support
- There is no `DELETE /v1/transactions/:id` or `POST /v1/transactions/:id/void`

**What you CAN do via API:**
- Void a payment source (cancel a subscription): `PUT /v1/payment_sources/:id/void`

```js
async function voidPaymentSource(paymentSourceId, privateKey, baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/payment_sources/${paymentSourceId}/void`, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${privateKey}` },
  });
  return (await res.json()).data;  // data.status → "VOIDED"
}
```

**Handle VOIDED reactively:** Listen for `transaction.updated` webhook events where `status === 'VOIDED'` and update your internal order state accordingly.
