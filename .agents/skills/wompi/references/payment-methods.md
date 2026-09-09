# Wompi — Payment Methods

## Cards (CARD)

Supports Visa, Mastercard, and American Express. Requires tokenization via the Widget.

```json
{
  "payment_method": {
    "type": "CARD",
    "token": "tok_prod_...",
    "installments": 3
  }
}
```

**Installments:**
- Only valid for **credit cards** — debit must use `1`
- Supported range depends on merchant configuration and issuing bank (1–36)
- The Widget automatically shows installment options to the customer

**Card extra fields in response:**
```json
{
  "extra": {
    "bin": "411111",
    "name": "VISA-CREDIT",
    "brand": "VISA",
    "last_four": "1111",
    "exp_year": "29",
    "exp_month": "12",
    "card_holder": "JOHN DOE",
    "installments": 3,
    "is_three_ds": true,
    "three_ds_auth": {
      "three_ds_auth": { "current_step": "AUTHENTICATION", "current_step_status": "APPROVED" }
    }
  }
}
```

---

## PSE (Bank Transfer)

Supports all Colombian banks affiliated with ACH Colombia. Customer pays with their savings or checking account.

```js
// Step 1: Get bank list (cache for up to 24h — changes infrequently)
const banks = await fetch('https://production.wompi.co/v1/pse/financial_institutions')
  .then(r => r.json()).then(b => b.data);
// Returns: [{ financial_institution_code: "1007", financial_institution_name: "BANCOLOMBIA" }, ...]

// Step 2: Collect from customer:
//  - bank selection (financial_institution_code)
//  - person type: natural (0) or legal entity (1)
//  - ID type: CC | NIT | CE | PASSPORT | TI | RC | DE
//  - ID number
//  - full name and phone

// Step 3: Create transaction
{
  payment_method: {
    type: 'PSE',
    user_type: 0,
    user_legal_id_type: 'CC',
    user_legal_id: '1234567890',
    financial_institution_code: '1007',
    payment_description: 'Order #001',  // max 64 chars — appears on bank statement
  },
  redirect_url: 'https://yoursite.com/confirmation',  // REQUIRED for PSE
}
```

**Response includes** `data.payment_method.extra.async_payment_url` — redirect the customer here to complete payment at their bank.

**Colombian ID Types:**
| Code | Document |
|---|---|
| `CC` | Cédula de Ciudadanía |
| `NIT` | NIT (legal entities) |
| `CE` | Cédula de Extranjería |
| `PASSPORT` | Passport |
| `TI` | Tarjeta de Identidad |
| `RC` | Registro Civil |
| `DE` | Documento Extranjero |

---

## Nequi

Customer receives a push notification on their Nequi app to approve the payment.

```json
{
  "payment_method": {
    "type": "NEQUI",
    "phone_number": "3107654321"
  }
}
```

- Phone must be a Nequi-registered Colombian number
- Transaction starts as `PENDING` — customer has ~10 minutes to approve in the app
- Use webhooks or polling to get final status
- Also supports **payment sources** (recurring billing via Nequi — see `references/payment-sources.md`)

---

## Daviplata

Requires a 3-step OTP flow. The full flow is complex — always use the official Wompi Widget to handle Daviplata, unless you need a fully custom UX.

**Manual flow (advanced):**

```
Step 1: POST /v1/transactions with type: "DAVIPLATA"
        → Returns url_services: { token, code_otp_send, code_otp_validate }

Step 2: POST to code_otp_send URL with Bearer token
        → Sends OTP to customer's phone

Step 3: POST to code_otp_validate URL with Bearer token + customer's OTP
        → Completes the subscription

Step 4: POST /v1/transactions with the Daviplata subscription PK
```

> Recommendation: Use the Widget for Daviplata. The manual flow is fragile and error-prone.

---

## Bancolombia Transfer Button (BANCOLOMBIA_TRANSFER)

Redirects the customer to Bancolombia's web or app to authorize the payment.

```json
{
  "payment_method": { "type": "BANCOLOMBIA_TRANSFER" },
  "redirect_url": "https://yoursite.com/confirmation"
}
```

Response contains `data.payment_method.extra.async_payment_url` — redirect customer here.

---

## Bancolombia QR (BANCOLOMBIA_QR)

Generates a QR code the customer scans with their Bancolombia app. Natural persons only.

```json
{
  "payment_method": {
    "type": "BANCOLOMBIA_QR",
    "payment_description": "Order #001"
  }
}
```

Response contains `data.payment_method.extra.qr_image` — a URL to the QR image PNG. Display it to the customer.

---

## Cash — Corresponsal Bancario (BANCOLOMBIA_COLLECT)

Generates a payment reference the customer presents at any of Bancolombia's 15,000+ physical cash points.

```json
{
  "payment_method": { "type": "BANCOLOMBIA_COLLECT" }
}
```

Response contains `data.payment_method.extra.external_identifier` — the code the customer shows at the Corresponsal.

Transaction starts `PENDING` and may take hours or days to be confirmed as `APPROVED`.

---

## Puntos Colombia (PCOL)

Loyalty points redemption. Two modes: (1) full payment with points, or (2) partial points + second payment method.

```js
// Create PCOL transaction
const txn = await createTransaction({
  // ... standard fields
  payment_method: { type: 'PCOL' },
  customer_data: {
    phone_number: '+573121111111',
    full_name: 'Nombre Apellido',
  },
});

// Poll until async_payment_url is available in extra
// Then redirect customer to txn.payment_method.extra.async_payment_url

// If partial points payment: check txn.payment_method.extra.child_transaction_id
// That child transaction handles the second payment method
```

**Sandbox statuses for PCOL:**
```json
{ "payment_method": { "type": "PCOL", "sandbox_status": "APPROVED_ONLY_POINTS" } }
```
| `sandbox_status` | Meaning |
|---|---|
| `APPROVED_ONLY_POINTS` | Total payment with points |
| `APPROVED_HALF_POINTS` | 50% points + 50% second method |
| `DECLINED` | Declined |
| `ERROR` | Error |

---

## SU+ Pay (SU_PLUS)

Supermarket loyalty program payment. Redirect flow.

```json
{
  "payment_method": { "type": "SU_PLUS" },
  "customer_data": {
    "phone_number": "+573121111111",
    "full_name": "Nombre Apellido"
  },
  "user_legal_id": "53234234",
  "user_legal_id_type": "CC"
}
```

Response contains `data.payment_method.extra.url` — redirect customer here.

---

## Choosing the Right Method

```
E-commerce (most merchants)     → CARD + PSE (covers ~95% of Colombian online shoppers)
Mobile-first or young users     → Add NEQUI
Bancolombia customers           → Add BANCOLOMBIA_TRANSFER or BANCOLOMBIA_QR
Unbanked customers              → BANCOLOMBIA_COLLECT (cash)
Loyalty/retail                  → PCOL
Subscriptions / recurring       → CARD or NEQUI via payment sources
```
