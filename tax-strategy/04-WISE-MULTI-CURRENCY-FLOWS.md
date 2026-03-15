# Wise Business — Multi-Currency Money Flows

---

## Account Structure

Your Wise Business account serves as the central treasury for ML Upskill Agents UG, receiving payouts from Stripe in multiple currencies and holding balances until needed for expenses, tax payments, or conversion to EUR.

### Currency Balances to Activate

| Currency | Products Served | Wise Receiving Details |
|----------|----------------|----------------------|
| **EUR** | PraxisProfi, ProPrecept Ireland, EU OSS VAT | IBAN (SEPA) — free to receive |
| **GBP** | WritingPAD UK | UK sort code + account number — free to receive |
| **ZAR** | ProPrecept RSA | ZAR account details — verify receiving fees |
| **AUD** | ProPrecept Australia | BSB + account number — free to receive |
| **PHP** | WriteRLE | PHP account details — verify receiving fees |

### Wise Fees Summary

| Action | Fee |
|--------|-----|
| Receiving EUR (SEPA) | Free |
| Receiving GBP (domestic) | Free |
| Receiving AUD (domestic) | Free |
| Receiving via SWIFT | ~€2–6 per payment (varies by currency) |
| Currency conversion | 0.4–0.6% for major pairs (EUR↔GBP), up to 1.5% for exotic pairs |
| Holding balances | Free (no monthly fees) |
| Account setup | One-time ~€30 |

---

## Money Flow: Stripe → Wise → Operations

### Step 1: Customer Pays via Stripe

```
Customer in UK pays £9.99
  → Stripe deducts: transaction fee (1.5% + £0.20 for European cards)
  → Stripe deducts: Stripe Tax fee (0.5% of transaction)
  → Stripe holds VAT portion (£1.67 at 20%)
  → Net to you: ~£7.82
```

### Step 2: Stripe Payouts to Wise

Configure Stripe to pay out to your Wise account in the ORIGINAL CURRENCY of the transaction:

| Stripe Product | Payout Currency | Wise Destination |
|---------------|----------------|-----------------|
| WritingPAD UK | GBP | Wise GBP balance |
| ProPrecept Ireland | EUR | Wise EUR balance |
| PraxisProfi | EUR | Wise EUR balance |
| ProPrecept RSA | ZAR | Wise ZAR balance |
| ProPrecept AU | AUD | Wise AUD balance |
| WriteRLE | PHP | Wise PHP balance |

**Why hold in original currency first:** Wise gives you mid-market exchange rates. Stripe's built-in conversion is typically more expensive. By receiving in original currency and converting yourself via Wise, you save on every transaction.

**Stripe payout frequency:** Set to weekly or daily depending on cash flow needs. Weekly is fine for early-stage.

### Step 3: Currency Conversion Strategy

**Rule of thumb:** Convert to EUR only when needed for:
- German corporate tax payments
- German VAT payments
- Steuerberater fees
- Other EUR-denominated expenses

**Hold non-EUR balances when:**
- You have upcoming expenses in that currency (e.g., Google Ads in GBP for UK marketing)
- The exchange rate is unfavorable — Wise lets you set rate alerts
- You're accumulating for a quarterly VAT payment in that currency

**Auto-conversion option:** Wise offers rate alerts and auto-conversion at your target rate. Consider setting target rates for recurring conversions.

---

## Recommended Wise Sub-Accounts (Jars)

Organize your Wise account into labeled jars for clarity:

| Jar Name | Currency | Purpose |
|----------|----------|---------|
| **Operating EUR** | EUR | Day-to-day expenses, API costs, hosting |
| **GmbH Reserve** | EUR | 25% profit retention for GmbH conversion |
| **German Tax Reserve** | EUR | Körperschaftsteuer + Gewerbesteuer quarterly advances |
| **UK VAT Reserve** | GBP | Accumulated UK VAT for quarterly remittance |
| **EU OSS VAT Reserve** | EUR | Accumulated EU VAT for quarterly OSS return |
| **GBP Operating** | GBP | UK marketing spend, UK-denominated expenses |
| **ZAR Holding** | ZAR | SA revenue before conversion |
| **AUD Holding** | AUD | AU revenue before conversion |
| **PHP Holding** | PHP | PH revenue before conversion |
| **US Tax Reserve** | EUR or USD | Set aside for potential US GILTI/personal tax |

---

## Monthly Cash Flow Routine

### Week 1 of Each Month

1. Review Stripe Dashboard: total revenue by product and currency for prior month
2. Verify all Stripe payouts landed in correct Wise currency balances
3. In SevDesk: confirm all invoices match Stripe transactions (automated via integration)

### Week 2 of Each Month

4. Calculate tax obligations:
   - VAT collected (UK, EU OSS, and any others) → move to respective VAT reserve jars
   - Estimated corporate tax (15.825% federal + Gewerbesteuer) on net profit → move to German Tax Reserve
   - 25% of after-tax profit → move to GmbH Reserve
5. Convert non-EUR balances to EUR as needed (or hold if rate is unfavorable)

### Quarterly

6. File/pay UK VAT return (from GBP VAT reserve)
7. File/pay EU OSS return (from EUR OSS VAT reserve)
8. Pay German corporate tax advance (from German Tax Reserve)
9. Update the operating cash balance in your tracking spreadsheet

### Annually

10. Steuerberater prepares Jahresabschluss and corporate tax return
11. US tax advisor prepares Form 1040 + Form 5471 + FBAR
12. True-up any over/underpayment of tax advances
13. Assess GmbH conversion readiness (is reserve at €25K?)

---

## Connecting Stripe Payouts to Wise

### Setup Steps

1. In Stripe Dashboard → Settings → Payouts → Bank accounts
2. Add your Wise account details for each currency:
   - GBP: UK sort code + account number (from Wise GBP balance details)
   - EUR: IBAN (from Wise EUR balance details)
   - For ZAR/AUD/PHP: Check if Stripe supports direct payout in these currencies to your Wise account. If not, Stripe will convert to EUR first (less ideal but functional)
3. Set payout schedule (recommend: weekly for each currency)
4. Enable payout notifications

### If Stripe Cannot Pay Out in ZAR/AUD/PHP Directly

Fallback: Accept Stripe's conversion to EUR and receive all payouts in EUR. This is simpler but you lose the mid-market rate advantage. The conversion loss is typically 1–2% compared to Wise's rates.

**Alternative for ZAR:** If using Paystack for South Africa, configure Paystack to pay out to Wise ZAR directly.

---

## SevDesk Connection to Wise

SevDesk can import bank transactions from Wise for automatic reconciliation. Setup:

1. In SevDesk → Banking → Add bank account
2. Connect via finAPI or manual CSV import
3. SevDesk will match incoming Wise transactions to invoices
4. Review and confirm matches monthly

See `05-SEVDESK-STRIPE-AUTOMATION.md` for the full automation plan.

---

## Key Metrics to Track Monthly

| Metric | Source | Purpose |
|--------|--------|---------|
| Gross revenue by currency | Stripe Dashboard | Top-line growth |
| Stripe fees by product | Stripe Dashboard | Cost tracking |
| VAT collected by jurisdiction | Stripe Tax reports | Compliance |
| Net revenue after fees + VAT | Calculated | True revenue |
| Wise conversion fees | Wise statements | Hidden cost tracking |
| Operating cash available | Wise balances minus all reserves | What you can actually spend |
