# Wompi — Payment Sources (Tokenization & Subscriptions)

Payment sources let you charge a customer repeatedly without re-entering payment details. Supported for **Cards** and **Nequi**.

---

## Card Tokenization Flow

### Step 1 — Tokenize via Widget
Embed a tokenize Widget on your "save card" or "checkout" page:

```html
<form method="POST" action="/api/save-card">
  <script
    src="https://checkout.wompi.co/widget.js"
    data-render="button"
    data-widget-operation="tokenize"
    data-public-key="pub_prod_YOUR_KEY"
    data-redirect-url="https://yoursite.com/card-saved">
  </script>
</form>
```

The Widget POSTs to your `redirect-url` with a `id` query param containing the **card token**.

> Tokens are single-use for creating payment sources. Never store the raw token in your DB — use the `payment_source_id` after Step 2.

### Step 2 — Create Payment Source (server-side)

```js
// Node.js
async function createPaymentSource({
  privateKey, publicKey, cardToken, customerEmail,
  baseUrl = 'https://production.wompi.co/v1'
}) {
  const { data: merchant } = await fetch(`${baseUrl}/merchants/${publicKey}`).then(r => r.json());

  const res = await fetch(`${baseUrl}/payment_sources`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${privateKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'CARD',
      token: cardToken,
      customer_email: customerEmail,
      acceptance_token: merchant.presigned_acceptance.acceptance_token,
      accept_personal_auth: merchant.presigned_personal_data_auth.acceptance_token,
    }),
  });
  const { data } = await res.json();
  // Store data.id (payment_source_id) in your database linked to the customer
  return data;
}
```

```python
# Python
def create_payment_source(private_key, public_key, card_token, customer_email,
                           base_url='https://production.wompi.co/v1'):
    merchant = requests.get(f'{base_url}/merchants/{public_key}').json()['data']

    res = requests.post(
        f'{base_url}/payment_sources',
        headers={'Authorization': f'Bearer {private_key}'},
        json={
            'type': 'CARD',
            'token': card_token,
            'customer_email': customer_email,
            'acceptance_token': merchant['presigned_acceptance']['acceptance_token'],
            'accept_personal_auth': merchant['presigned_personal_data_auth']['acceptance_token'],
        }
    )
    res.raise_for_status()
    return res.json()['data']
    # Store data['id'] as payment_source_id for this customer
```

### Step 3 — Charge a Payment Source

Use `payment_source_id` instead of a payment method token. No acceptance tokens needed.

```js
// Node.js
async function chargePaymentSource({
  privateKey, paymentSourceId, amountInCents, reference, customerEmail,
  installments = 1, taxes = [],
  baseUrl = 'https://production.wompi.co/v1'
}) {
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
      reference,   // must be unique for every charge
      payment_source_id: paymentSourceId,
      payment_method: { installments },
      ...(taxes.length > 0 && { taxes }),
    }),
  });
  return (await res.json()).data;
}
```

---

## Nequi Payment Sources

Tokenize a Nequi account for recurring charges.

### Step 1 — Create Nequi Payment Source

```js
async function createNequiPaymentSource({ privateKey, publicKey, phoneNumber, customerEmail, baseUrl }) {
  const { data: merchant } = await fetch(`${baseUrl}/merchants/${publicKey}`).then(r => r.json());

  const res = await fetch(`${baseUrl}/payment_sources`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${privateKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'NEQUI',
      phone_number: phoneNumber,
      customer_email: customerEmail,
      acceptance_token: merchant.presigned_acceptance.acceptance_token,
      accept_personal_auth: merchant.presigned_personal_data_auth.acceptance_token,
    }),
  });
  const { data } = await res.json();
  // data.status starts as PENDING — customer must approve via Nequi push notification
  // Poll or wait for nequi_token.updated webhook event
  return data;
}
```

> **Nequi tokens** start as `PENDING`. The customer receives a push notification to authorize. 
> Listen for `nequi_token.updated` webhook event with `status: "ACTIVE"` before attempting charges.

### Step 2 — Charge Nequi Source (same as card)

```js
await chargePaymentSource({
  privateKey,
  paymentSourceId: nequiSource.id,
  amountInCents: 2990000,
  reference: 'SUB-MARCH-2025',
  customerEmail: 'customer@example.com',
});
```

---

## Bancolombia Savings/Checking Payment Source

Creates a subscription linked to a Bancolombia account. Customer authorizes via redirect.

```js
async function createBancolombiaPaymentSource({ privateKey, publicKey, customerEmail, redirectUrl, baseUrl }) {
  const { data: merchant } = await fetch(`${baseUrl}/merchants/${publicKey}`).then(r => r.json());

  const res = await fetch(`${baseUrl}/payment_sources`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${privateKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'BANCOLOMBIA_TRANSFER',
      customer_email: customerEmail,
      redirect_url: redirectUrl,  // required — customer redirected here after authorization
      acceptance_token: merchant.presigned_acceptance.acceptance_token,
      accept_personal_auth: merchant.presigned_personal_data_auth.acceptance_token,
    }),
  });
  const { data } = await res.json();
  // Redirect customer to data.authorization_url to authorize the account link
  return data;
}
```

---

## Voiding (Cancelling) a Payment Source

```js
// Cancel subscription / remove saved card
async function voidPaymentSource(paymentSourceId, privateKey, baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/payment_sources/${paymentSourceId}/void`, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${privateKey}` },
  });
  const { data } = await res.json();
  return data; // data.status → "VOIDED"
}
```

---

## Subscription Billing Pattern

```js
// Full subscription lifecycle example
class SubscriptionBilling {
  constructor({ privateKey, publicKey, baseUrl }) {
    this.privateKey = privateKey;
    this.publicKey = publicKey;
    this.baseUrl = baseUrl;
  }

  async subscribe(customerEmail, cardToken) {
    const source = await createPaymentSource({
      privateKey: this.privateKey,
      publicKey: this.publicKey,
      cardToken,
      customerEmail,
      baseUrl: this.baseUrl,
    });
    // Persist: customer_id → payment_source_id in your DB
    return source;
  }

  async chargeMonthly(customerId, amountInCents) {
    const paymentSourceId = await db.getPaymentSourceId(customerId);
    const reference = `SUB-${customerId}-${new Date().toISOString().slice(0, 7)}`; // e.g. SUB-123-2025-03
    try {
      const txn = await chargePaymentSource({
        privateKey: this.privateKey,
        paymentSourceId,
        amountInCents,
        reference,
        customerEmail: await db.getCustomerEmail(customerId),
        baseUrl: this.baseUrl,
      });
      await db.recordCharge(customerId, txn.id, reference, 'PENDING');
      return txn;
    } catch (err) {
      await db.recordFailedCharge(customerId, reference, err.message);
      throw err;
    }
  }

  async cancel(customerId) {
    const paymentSourceId = await db.getPaymentSourceId(customerId);
    await voidPaymentSource(paymentSourceId, this.privateKey, this.baseUrl);
    await db.markSubscriptionCancelled(customerId);
  }
}
```

---

## Security Notes

- **Never store raw card tokens** — they're single-use. Store the `payment_source_id` from Step 2.
- **Tokens are merchant-scoped** — a token from one Wompi merchant account cannot be used with another.
- **Card tokens expire** — use them to create a payment source immediately.
- **Void payment sources** when customers cancel or request data deletion (GDPR/Colombian law compliance).
