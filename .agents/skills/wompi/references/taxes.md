# Wompi — Taxes (IVA & Consumption Tax)

## Key Rule: Taxes Are Included in `amount_in_cents`

> ⚠️ Wompi does **NOT** add taxes on top of the amount. The `taxes` field only tells the payment processor how much of the total is tax — it is informational only.

Example: Product costs $100,000 COP, IVA is 19% ($19,000 COP):
```
amount_in_cents = 11900000   ← $100,000 + $19,000 = $119,000 total
taxes[0].amount_in_cents = 1900000   ← just the tax portion
```

**Never do:** `amount = base + tax` AND `taxes = [{ amount_in_cents: tax }]` — that would double-count.

---

## Transaction with Taxes

```json
{
  "amount_in_cents": 11900000,
  "currency": "COP",
  "taxes": [
    {
      "type": "VAT",
      "amount_in_cents": 1900000
    }
  ]
}
```

## Tax Types

| `type` | Meaning |
|---|---|
| `VAT` | IVA (Impuesto sobre el Valor Añadido) — standard 19% |
| `CONSUMPTION` | Impuesto al consumo (e.g. restaurants: 8%) |

You can include both if applicable:
```json
{
  "taxes": [
    { "type": "VAT",         "amount_in_cents": 1900000 },
    { "type": "CONSUMPTION", "amount_in_cents":  800000 }
  ]
}
```

---

## Helper: Calculate Tax Amount

```js
// Node.js
function calculateTaxes(baseAmountCents, vatRate = 0.19, consumptionRate = 0) {
  const taxes = [];

  if (vatRate > 0) {
    taxes.push({
      type: 'VAT',
      amount_in_cents: Math.round(baseAmountCents * vatRate),
    });
  }

  if (consumptionRate > 0) {
    taxes.push({
      type: 'CONSUMPTION',
      amount_in_cents: Math.round(baseAmountCents * consumptionRate),
    });
  }

  const totalTax = taxes.reduce((sum, t) => sum + t.amount_in_cents, 0);
  const totalAmount = baseAmountCents + totalTax;

  return { taxes, totalAmountInCents: totalAmount };
}

// Usage:
const { taxes, totalAmountInCents } = calculateTaxes(10000000); // $100,000 COP base
// → taxes: [{ type: 'VAT', amount_in_cents: 1900000 }]
// → totalAmountInCents: 11900000  ← use this as amount_in_cents in the transaction
```

```python
# Python
def calculate_taxes(base_amount_cents, vat_rate=0.19, consumption_rate=0):
    taxes = []
    if vat_rate > 0:
        taxes.append({'type': 'VAT', 'amount_in_cents': round(base_amount_cents * vat_rate)})
    if consumption_rate > 0:
        taxes.append({'type': 'CONSUMPTION', 'amount_in_cents': round(base_amount_cents * consumption_rate)})

    total_tax = sum(t['amount_in_cents'] for t in taxes)
    return {'taxes': taxes, 'total_amount_in_cents': base_amount_cents + total_tax}
```

---

## Payment Links with Taxes

**Fixed amount link:**
```json
{ "taxes": [{ "type": "VAT", "amount_in_cents": 1900000 }] }
```

**Open amount link (customer enters amount):**
```json
{ "taxes": [{ "type": "VAT", "percentage": 19 }] }
```

When using `percentage` on an open-amount link, Wompi calculates the tax from whatever amount the customer enters.

---

## Important Notes for Colombia

- Wompi charges **19% IVA** on their own transaction fees (separate from your product's taxes).
- The `taxes` field in your transaction payload refers to **your product's taxes**, not Wompi's fees.
- Taxes are passed to the payment processor for reporting and reconciliation purposes.
- If your business is IVA-exempt (e.g. healthcare, education), simply omit the `taxes` field.
