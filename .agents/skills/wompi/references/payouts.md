# Wompi — Third-Party Payments (Dispersión de Pagos)

Disperse funds to bank accounts in Colombia — suppliers, employees, sellers, affiliates. Requires the Third-Party Payments product to be activated on your Wompi account.

**Separate auth system:** Third-Party Payments uses `x-api-key` + `user-principal-id` headers, NOT the standard `Authorization: Bearer` private key.

---

## Authentication

Get your API Key and Principal User ID from the Wompi dashboard under Third-Party Payments settings.

```js
const PAYOUT_HEADERS = {
  'x-api-key': process.env.WOMPI_PAYOUT_API_KEY,
  'user-principal-id': process.env.WOMPI_PAYOUT_USER_ID,
  'Content-Type': 'application/json',
};
```

---

## Limits & Constraints

| Limit | Value |
|---|---|
| Daily transaction total | $1,500,000,000 COP (adjustable) |
| Daily batches per client | 3,800 |
| Supported currencies | COP only |
| Amount format | Cents as integers (last 2 digits = cents) |

---

## Step 1: Get Available Banks

```js
// Node.js
async function getPayoutBanks(baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/banks`, { headers: PAYOUT_HEADERS });
  return (await res.json()).data;
  // Returns: [{ id: "uuid", name: "BANCOLOMBIA", code: "1007" }, ...]
}
```

```python
# Python
def get_payout_banks(base_url='https://production.wompi.co/v1'):
    res = requests.get(f'{base_url}/banks', headers=PAYOUT_HEADERS)
    res.raise_for_status()
    return res.json()['data']
```

---

## Step 2: Create a Payout Batch

### Single payout
```js
async function createPayout(payouts, baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/payouts`, {
    method: 'POST',
    headers: PAYOUT_HEADERS,
    body: JSON.stringify({
      transactions: payouts.map(p => ({
        legalIdType: p.legalIdType,       // CC | NIT | CE | PASSPORT | TI | RC | DE
        legalId: p.legalId,
        bankId: p.bankId,                 // UUID from /v1/banks
        accountType: p.accountType,       // AHORROS | CORRIENTE
        accountNumber: p.accountNumber,
        amount_in_cents: p.amountInCents,
        reference: p.reference,           // unique per payout
        description: p.description,       // appears on bank statement
      })),
    }),
  });
  return (await res.json()).data;
}

// Single payout example
const result = await createPayout([{
  legalIdType: 'CC',
  legalId: '1234567890',
  bankId: 'uuid-from-banks-endpoint',
  accountType: 'AHORROS',
  accountNumber: '1234567890',
  amountInCents: 50000000,   // $500,000 COP
  reference: 'PAYOUT-SUPPLIER-001',
  description: 'February invoice payment',
}]);
```

### Batch payout (multiple beneficiaries)
```js
const batch = await createPayout([
  {
    legalIdType: 'CC', legalId: '111111111',
    bankId: 'bank-uuid-1', accountType: 'AHORROS', accountNumber: '100001',
    amountInCents: 2500000, reference: 'SALARY-EMP001-FEB', description: 'February salary',
  },
  {
    legalIdType: 'NIT', legalId: '9001234560',
    bankId: 'bank-uuid-2', accountType: 'CORRIENTE', accountNumber: '200002',
    amountInCents: 15000000, reference: 'INV-SUPPLIER-042', description: 'Invoice #042',
  },
  // ... up to 3,800 per day
]);
```

---

## Check Service Health

```js
async function checkPayoutServiceHealth(baseUrl = 'https://production.wompi.co/v1') {
  const res = await fetch(`${baseUrl}/payouts/health`, { headers: PAYOUT_HEADERS });
  return (await res.json());
  // { status: "HEALTHY" | "PARTIAL_OUTAGE" | "UNHEALTHY", services: { ... } }
}
```

| Status | Meaning |
|---|---|
| `HEALTHY` | All services operational |
| `PARTIAL_OUTAGE` | Secondary service down; core functional |
| `UNHEALTHY` | Critical service down; do not send payouts |

> Always check health before sending large batches in production.

---

## Query Transactions

```js
// Filter payout transactions
async function queryPayouts({ fromDate, toDate, status, limit }, baseUrl = 'https://production.wompi.co/v1') {
  const params = new URLSearchParams({ fromDate, toDate });
  if (status) params.set('status', status);
  if (limit) params.set('limit', limit);

  const res = await fetch(`${baseUrl}/payouts/transactions?${params}`, { headers: PAYOUT_HEADERS });
  return (await res.json()).data;
}

// Usage
const results = await queryPayouts({
  fromDate: '2025-03-01',
  toDate: '2025-03-31',
  status: 'APPROVED',    // PROCESSING | PENDING | APPROVED | FAILED | REJECTED
});
```

---

## Sandbox Simulation

```js
// Add transactionStatus to simulate outcome
{
  transactions: [{
    // ... standard payout fields
    transactionStatus: 'APPROVED'  // APPROVED | FAILED
    // If omitted, defaults to APPROVED in sandbox
  }]
}
```

---

## Idempotency

Use unique `reference` values per payout. If you retry a failed request with the same reference, Wompi may reject it as a duplicate. Generate deterministic references:

```js
function payoutReference(beneficiaryId, periodKey) {
  return `PAY-${beneficiaryId}-${periodKey}`.substring(0, 50); // Keep references concise
}
// e.g. PAY-EMP001-2025-03
```

---

## Supported File Formats (Batch Upload via Dashboard)

For non-API batch uploads via the Wompi dashboard:
- Wompi Template (CSV/Excel)
- PAB and SAP Bancolombia
- DISFON Banco de Bogotá
- Banco de Occidente FC
- Davivienda

---

## Security Notes

- Store `WOMPI_PAYOUT_API_KEY` and `WOMPI_PAYOUT_USER_ID` in environment variables, never hardcoded.
- Third-Party Payments credentials are separate from your regular Wompi private key.
- Restrict payout API calls to specific server IPs where possible.
- Log all payout transactions with full audit trail (reference, amount, beneficiary ID, timestamp).
- Implement dual-approval for large batch payouts (human review before API call).
