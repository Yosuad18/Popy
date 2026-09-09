# Wompi — Cursor Agent Skill

A comprehensive [Agent Skill](https://docs.cursor.com/context/skills) for integrating [Wompi](https://wompi.co), Colombia's leading payment gateway (backed by Bancolombia).

This skill teaches AI agents how to generate secure, production-ready code for Wompi integrations in **Node.js**, **Python**, and **PHP**.

## What's Covered

- Authentication, API keys, and integrity signatures
- All payment methods: Cards, PSE, Nequi, Daviplata, Bancolombia (Button/QR/Cash), Puntos Colombia, SU+ Pay
- Transactions: creation, polling, status handling, voiding
- Webhooks: event handling, checksum validation, idempotency
- Payment Links: creation, batch invoicing, open-amount links
- Payment Sources: card tokenization, Nequi subscriptions, recurring billing
- Third-Party Payouts (Dispersiones): batch payments to bank accounts
- Taxes: IVA and consumption tax handling
- Sandbox: test data, simulating outcomes, local webhook testing
- Production checklist: security, compliance, go-live verification

## Installation

### As a personal skill (all your projects)

```bash
git clone https://github.com/NoxAI-co/wompi-skills.git ~/.cursor/skills/wompi
```

### As a project skill (shared with your team)

```bash
git clone https://github.com/NoxAI-co/wompi-skills.git .cursor/skills/wompi
```

Or add as a git submodule:

```bash
git submodule add https://github.com/NoxAI-co/wompi-skills.git .cursor/skills/wompi
```

## Usage

Once installed, the skill activates automatically when you mention Wompi, Colombian payments, PSE, Nequi, or any related topic in Cursor's agent chat. The agent will read the relevant reference files on demand to generate accurate code.

## Structure

```
SKILL.md                         Main skill file (agent reads this first)
references/
  auth-and-security.md           API keys, signatures, Habeas Data compliance
  transactions.md                Creating and managing transactions
  webhooks.md                    Event handling and checksum validation
  payment-methods.md             All supported payment methods
  payment-links.md               Shareable payment URLs
  payment-sources.md             Tokenization and recurring billing
  payouts.md                     Third-party payments / dispersiones
  taxes.md                       IVA and consumption tax
  sandbox.md                     Test data and local testing
  production-checklist.md        Go-live verification checklist
  errors.md                      Error codes, retries, idempotency
```

## License

MIT
