# Tax Reserve Calculator & Operating Cash Model

This document provides the formula for calculating your actual available operating cash at any point in time, after setting aside all tax obligations and the GmbH reserve.

---

## The Formula

```
Operating Cash = Total Wise Balances
              − VAT/GST Reserves (all jurisdictions)
              − German Corporate Tax Reserve
              − GmbH 25% Profit Retention Reserve
              − US Personal Tax Reserve (GILTI/income)
              − Upcoming Fixed Expenses (next 30 days)
```

---

## Step-by-Step Monthly Calculation

### Step 1: Gross Revenue (from Stripe)

Sum all Stripe payouts received in the month, by currency:

| Source | Currency | Gross Revenue | Stripe Fees | Net Payout |
|--------|----------|--------------|-------------|-----------|
| WritingPAD UK | GBP | £_____ | £_____ | £_____ |
| ProPrecept IE | EUR | €_____ | €_____ | €_____ |
| PraxisProfi | EUR | €_____ | €_____ | €_____ |
| ProPrecept RSA | ZAR | R_____ | R_____ | R_____ |
| ProPrecept AU | AUD | $_____ | $_____ | $_____ |
| WriteRLE | PHP | ₱_____ | ₱_____ | ₱_____ |

### Step 2: VAT/GST Already Collected (Set Aside Immediately)

Stripe Tax collects VAT/GST from customers. This money is NOT yours — it must be remitted to tax authorities. Move it to VAT reserve jars immediately.

| Jurisdiction | VAT Rate | VAT Collected This Month | Cumulative (Quarter) |
|-------------|----------|-------------------------|---------------------|
| UK | 20% | £_____ | £_____ |
| Ireland (via OSS) | 23% | €_____ | €_____ |
| Germany | 19% | €_____ | €_____ |
| South Africa | 15% | R_____ | R_____ |
| Australia | 10% | $_____ | $_____ |
| Philippines | 12% | ₱_____ | ₱_____ |

### Step 3: Net Revenue (After Stripe Fees and VAT)

```
Net Revenue = Stripe Payout − VAT Collected
```

Convert all to EUR equivalent for the overall picture (use Wise mid-market rates):

| Source | Net Revenue (local) | EUR Equivalent |
|--------|-------------------|----------------|
| UK | £_____ | €_____ |
| Ireland | €_____ | €_____ |
| Germany | €_____ | €_____ |
| RSA | R_____ | €_____ |
| Australia | $_____ | €_____ |
| Philippines | ₱_____ | €_____ |
| **Total Net Revenue** | | **€_____** |

### Step 4: Operating Expenses (Deductible)

| Expense | EUR Amount |
|---------|-----------|
| Anthropic API | €_____ |
| Deepgram API | €_____ |
| Vercel hosting | €_____ |
| Clerk | €_____ |
| SevDesk | €_____ |
| Make.com | €_____ |
| Domain costs | €_____ |
| Marketing (Google Ads, LinkedIn) | €_____ |
| Filing services (Taxually/Marosa) | €_____ |
| Steuerberater (amortized monthly) | €_____ |
| US tax advisor (amortized monthly) | €_____ |
| Geschäftsführer salary (if applicable) | €_____ |
| Other | €_____ |
| **Total Expenses** | **€_____** |

### Step 5: Taxable Profit

```
Taxable Profit = Total Net Revenue (EUR) − Total Expenses (EUR)
```

**Taxable Profit this month: €_____**

### Step 6: German Corporate Tax Reserve

```
Federal Tax Reserve = Taxable Profit × 15.825%    (KSt + Soli)

If Taxable Profit > €24,500 (annualized):
  Trade Tax Reserve = Taxable Profit × Gewerbesteuer Rate (~11.9%)
Else:
  Trade Tax Reserve = €0    (below Freibetrag)

Total Corporate Tax Reserve = Federal + Trade Tax
```

| Component | Rate | Amount |
|-----------|------|--------|
| Körperschaftsteuer | 15% | €_____ |
| Solidaritätszuschlag | 0.825% | €_____ |
| Gewerbesteuer | ~11.9%* | €_____ |
| **Total Corporate Tax** | **~27.7%** | **€_____** |

*Gewerbesteuer only applies when annualized profit exceeds €24,500*

### Step 7: GmbH 25% Profit Retention

```
After-Tax Profit = Taxable Profit − Corporate Tax Reserve
GmbH Reserve Addition = After-Tax Profit × 25%
```

| Calculation | Amount |
|-------------|--------|
| After-tax profit | €_____ |
| 25% retention | €_____ |
| Cumulative GmbH reserve | €_____ / €25,000 target |

### Step 8: US Tax Reserve (Conservative Estimate)

As a US citizen, you may owe US tax on UG profits via GILTI, even if not distributed. However, German taxes paid provide Foreign Tax Credits. In most scenarios where German effective rate is ~28%, GILTI liability is minimal or zero. Set aside a conservative 5% buffer:

```
US Tax Reserve = After-Tax Profit × 5%
```

*Adjust after first US tax filing with your advisor's guidance.*

### Step 9: Operating Cash Available

```
Operating Cash = Total Wise Balances (all currencies, EUR equivalent)
              − VAT Reserves (all jurisdictions)
              − Corporate Tax Reserve
              − GmbH Reserve (cumulative)
              − US Tax Reserve
              − Next Month's Fixed Expenses (prepaid)
```

---

## Worked Example: Month with €5,000 Net Revenue

| Line | Calculation | Amount |
|------|------------|--------|
| Net revenue (after Stripe fees + VAT removed) | | €5,000 |
| Less: operating expenses | | (€1,200) |
| **Taxable profit** | | **€3,800** |
| Less: KSt + Soli (15.825%) | €3,800 × 15.825% | (€601) |
| Less: Gewerbesteuer | €0 (below €24.5K annualized) | (€0) |
| **After-tax profit** | | **€3,199** |
| Less: GmbH 25% reserve | €3,199 × 25% | (€800) |
| Less: US tax reserve (5%) | €3,199 × 5% | (€160) |
| **Distributable / operating cash from this month** | | **€2,239** |

So from €5,000 in net revenue, you have **€2,239 in actual operating cash** — about 45%.

At higher revenue levels where Gewerbesteuer kicks in (annualized profit > €24,500):

| Line | Amount |
|------|--------|
| Net revenue | €10,000 |
| Expenses | (€2,000) |
| **Taxable profit** | **€8,000** |
| KSt + Soli (15.825%) | (€1,266) |
| Gewerbesteuer (~11.9%) | (€952) |
| **After-tax profit** | **€5,782** |
| GmbH 25% | (€1,446) |
| US reserve (5%) | (€289) |
| **Operating cash** | **€4,047** (~40%) |

---

## Quick Reference: Percentage of Revenue Available as Operating Cash

| Annual Revenue Level | Approx % Available as Operating Cash | Notes |
|---------------------|--------------------------------------|-------|
| < €24,500 profit | ~45% | No Gewerbesteuer |
| €24,500–100,000 profit | ~38–42% | Full tax + GmbH reserve |
| > €100,000 profit | ~40% | Scale efficiencies, GmbH reserve becomes smaller % |
| Post-GmbH conversion | ~50–55% | No more 25% retention |

---

## Automation Goal

Ultimately, this calculation should run automatically:

1. **Stripe** reports revenue and VAT via API → feeds SevDesk
2. **SevDesk** calculates profit after expenses
3. **Make.com** workflow triggers monthly:
   - Calculates tax reserves using the formulas above
   - Moves money to Wise jars (VAT, tax reserve, GmbH reserve)
   - Outputs a "Monthly Operating Cash Report" to your email or Notion/spreadsheet
4. **You see one number:** "You have €X,XXX available to spend this month"

This is a buildable automation — a Make.com scenario with Stripe + SevDesk + Wise API connections. Implementation estimate: 8–12 hours once all accounts are connected.

---

## Micro-SaaS Opportunity Note

This exact problem — "how much of my SaaS revenue can I actually spend?" — is a pain point for every solo developer and micro-SaaS founder operating internationally. A lightweight dashboard that connects Stripe + Wise + a tax rules engine and shows "real operating cash after all obligations" could itself be a product. Worth noting for your dissertation pipeline as well — the automation of financial clarity for independent developers is an underserved niche.
