# Wompi — Payment Links

Shareable payment URLs for email, WhatsApp, social media, or invoices. No code on the customer side.

---

## Create a Payment Link

```js
// Node.js
async function createPaymentLink(privateKey, options, baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/payment_links`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${privateKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: options.name,                          // Shown to customer at checkout
      description: options.description,
      single_use: options.singleUse ?? true,       // true = stops after 1 APPROVED payment
      currency: 'COP',
      amount_in_cents: options.amountInCents,      // null = customer enters any amount
      collect_shipping: options.collectShipping ?? false,
      redirect_url: options.redirectUrl,
      expires_at: options.expiresAt ?? null,       // ISO 8601, e.g. "2025-12-31T23:59:59.000Z"
      taxes: options.taxes ?? [],                  // see references/taxes.md
      customer_data: options.customerData ?? null, // collect extra fields
    }),
  });

  if (!res.ok) {
    const body = await res.json();
    throw Object.assign(new Error(body.error?.type), { status: res.status, details: body.error });
  }

  const { data } = await res.json();
  return {
    id: data.id,
    url: `https://checkout.wompi.co/l/${data.id}`,
    ...data,
  };
}
```

```python
# Python
def create_payment_link(private_key, options, base_url='https://production.wompi.co/v1'):
    payload = {
        'name': options['name'],
        'description': options.get('description', ''),
        'single_use': options.get('single_use', True),
        'currency': 'COP',
        'amount_in_cents': options.get('amount_in_cents'),   # None = open amount
        'collect_shipping': options.get('collect_shipping', False),
        'redirect_url': options.get('redirect_url'),
        'expires_at': options.get('expires_at'),
        'taxes': options.get('taxes', []),
    }
    res = requests.post(
        f'{base_url}/payment_links',
        headers={'Authorization': f'Bearer {private_key}'},
        json={k: v for k, v in payload.items() if v is not None}
    )
    res.raise_for_status()
    data = res.json()['data']
    data['url'] = f"https://checkout.wompi.co/l/{data['id']}"
    return data
```

---

## Collect Extra Customer Data

```json
{
  "customer_data": {
    "customer_references": [
      { "label": "Order number",  "is_required": true  },
      { "label": "Company name",  "is_required": false }
    ]
  }
}
```

---

## Taxes on Payment Links

For fixed-amount links:
```json
{
  "taxes": [{ "type": "VAT", "amount_in_cents": 1900000 }]
}
```

For open-amount links (tax as percentage):
```json
{
  "taxes": [{ "type": "VAT", "percentage": 19 }]
}
```

> See `references/taxes.md` for full tax reference.

---

## Get a Payment Link

```js
async function getPaymentLink(linkId, privateKey, baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/payment_links/${linkId}`, {
    headers: { 'Authorization': `Bearer ${privateKey}` },
  });
  return (await res.json()).data;
}
```

---

## Use Cases

| Use case | Config |
|---|---|
| One-time invoice | `single_use: true`, `amount_in_cents: <amount>` |
| Donation / pay-what-you-want | `single_use: false`, `amount_in_cents: null` |
| Subscription sign-up page | `single_use: false`, use webhook to trigger tokenization |
| Limited-time offer | `expires_at: <date>` |
| Collect shipping info | `collect_shipping: true` |
| Mass invoicing (batch create) | Loop `createPaymentLink` for each invoice; store `id` ↔ invoice mapping |

---

## Batch Link Creation (Mass Invoicing)

```js
async function createPaymentLinksInBatch(privateKey, invoices, concurrency = 5) {
  const results = [];
  for (let i = 0; i < invoices.length; i += concurrency) {
    const batch = invoices.slice(i, i + concurrency);
    const created = await Promise.all(
      batch.map(invoice => createPaymentLink(privateKey, {
        name: `Invoice #${invoice.number}`,
        description: invoice.description,
        singleUse: true,
        amountInCents: invoice.amountInCents,
        redirectUrl: `https://yoursite.com/invoice/${invoice.number}/paid`,
      }))
    );
    results.push(...created);
    // Small delay between batches to avoid rate limits
    if (i + concurrency < invoices.length) await new Promise(r => setTimeout(r, 200));
  }
  return results;
}
```
