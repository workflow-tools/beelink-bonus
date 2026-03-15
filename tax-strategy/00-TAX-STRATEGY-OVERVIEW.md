# ML Upskill Agents UG — Tax Strategy Overview

**Last Updated:** 22 February 2026
**Entity:** ML Upskill Agents UG (haftungsbeschränkt)
**Geschäftsführer:** Ryan Robert Hill (US citizen, SOFA status)
**Registered Address:** Hohe Straße 13, 92249 Vilseck, Deutschland
**Handelsregister:** Amtsgericht Amberg, HRB 8114
**USt-IdNr:** DE457209466
**Steuernummer:** 201/132/50136
**Finanzamt:** Amberg (Kirchensteig 2, 92224 Amberg)
**Stammkapital:** €1,00
**Gewerbe registered:** 14.08.2025 (Nebenerwerb)
**Handelsregister entry:** 11.08.2025
**SOFA-Stamp (Aufenthaltstitel):** dated 01.11.2024
**Gegenstand:** Datengestützte Studien- und Karriereberatung; Beratungen in Datenanalyse, KI, Instructional Design

---

## Purpose of This Directory

This directory tracks all tax obligations, money flows, reserve calculations, and compliance requirements for ML Upskill Agents UG as it scales WritingPAD and its international ports. The goal is to ensure that at any given moment you know exactly how much operating cash you have after all tax obligations are accounted for, and that the path from UG to GmbH is clear and automated.

---

## Document Index

| File | Purpose |
|------|---------|
| `00-TAX-STRATEGY-OVERVIEW.md` | This file — master index and quick reference |
| `01-SOFA-STATUS-AND-PERSONAL-TAX.md` | Your personal tax situation as a US citizen on SOFA status |
| `02-GERMAN-CORPORATE-TAX.md` | Körperschaftsteuer, Gewerbesteuer, UG-to-GmbH retention rules |
| `03-VAT-OBLIGATIONS-BY-COUNTRY.md` | VAT/GST registration thresholds, rates, and timelines per market |
| `04-WISE-MULTI-CURRENCY-FLOWS.md` | How money moves: Stripe → Wise → SevDesk, currency by currency |
| `05-SEVDESK-STRIPE-AUTOMATION.md` | Accounting automation plan: invoices, reconciliation, reporting |
| `06-TAX-RESERVE-CALCULATOR.md` | Formula for calculating operating cash after all reserves |
| `07-SUBSIDIARY-STRATEGY.md` | UK Ltd, and potential future subsidiaries in IE, ZA, AU, PH |
| `STEUERBERATER-BRIEFING.md` | Complete briefing document for Steuerberater meeting |
| `legal-docs/COMPANY-REFERENCE.md` | Compiled reference from all official registration documents |
| `legal-docs/*.pdf` | Original PDFs: Handelsregister, Gewerbe-Anmeldung, Steuernummer, USt-IdNr |

---

## Quick Reference: What You Owe Where

### German Corporate Taxes (on ALL worldwide UG profits)

| Tax | Rate | Notes |
|-----|------|-------|
| Körperschaftsteuer | 15% | Federal corporate income tax |
| Solidaritätszuschlag | 0.825% | 5.5% surcharge on Körperschaftsteuer |
| Gewerbesteuer | ~12–14%* | Vilseck Hebesatz × 3.5% base rate |
| **Combined effective** | **~28–30%** | *Confirm Vilseck Hebesatz with Steuerberater* |

*Plus the mandatory 25% profit retention for UG → GmbH conversion.*

### Consumer Tax (VAT/GST) by Market

| Market | Product | Currency | VAT/GST Rate | Registration Trigger | Status |
|--------|---------|----------|-------------|---------------------|--------|
| UK | WritingPAD | GBP | 20% | First sale (zero threshold for non-UK businesses) | **Register before launch** |
| Ireland | ProPrecept IE | EUR | 23% | Via EU OSS (Union scheme) from Germany | **Use OSS** |
| Germany | PraxisProfi | EUR | 19% | Already registered (DE457209466) | **Active** |
| South Africa | ProPrecept RSA | ZAR | 15% | ZAR 1M annual B2C sales | Post-revenue |
| Australia | ProPrecept AU | AUD | 10% | AUD 75K annual AU sales | Post-revenue |
| Philippines | WriteRLE | PHP | 12% | First sale (RA 12023, effective July 2025) | **Register by July 2025** |

### Personal Tax (You, Ryan)

| Jurisdiction | What | Rate | Notes |
|-------------|------|------|-------|
| USA (IRS) | Worldwide income | Marginal rates up to 37% | Must file annually as US citizen regardless of residence |
| Germany | Geschäftsführer salary from UG | German income tax rates (14–45%) | SOFA does NOT exempt private business income |
| Germany | Dividend/profit distributions from UG | 25% Abgeltungsteuer + 5.5% Soli | Only after GmbH conversion and retained earnings met |

---

## The Big Picture: Money Flow

```
Customer pays (GBP/EUR/ZAR/AUD/PHP)
        │
        ▼
   Stripe collects payment + calculates VAT/GST via Stripe Tax
        │
        ├── VAT/GST portion → held for remittance (you file/pay quarterly)
        │
        └── Net revenue → Stripe payout
                │
                ▼
        Wise Business Account (multi-currency)
                │
                ├── Hold in original currency (GBP, ZAR, AUD, PHP)
                │   or
                ├── Convert to EUR at mid-market rate (~0.4–0.6% fee)
                │
                └── EUR operating account
                        │
                        ├── 25% of profit → GmbH conversion reserve
                        ├── ~30% of remaining → German corporate tax reserve
                        ├── Geschäftsführer salary → personal account (taxed)
                        │
                        └── = Actual operating cash
```

---

## Immediate Action Items

1. **Confirm Vilseck Gewerbesteuer Hebesatz** — Call the Vilseck Rathaus or ask your Steuerberater. This determines your exact combined tax rate.

2. **Discuss SOFA implications with Steuerberater** — Critical: Your Geschäftsführer salary from the UG is NOT SOFA-exempt income. You need to understand German personal income tax obligations on this salary and how it interacts with your US filing obligations.

3. **Register for UK VAT** — Non-UK businesses have a ZERO threshold. Register with HMRC before WritingPAD UK launches. Consider using Stripe Tax + a filing partner (Taxually or Marosa) to automate quarterly UK VAT returns.

4. **Register for Philippines VAT** — RA 12023 requires foreign digital service providers to register with BIR by July 1, 2025. If WriteRLE will be live by then, register proactively.

5. **Set up EU OSS** — Register for the Union scheme through BZSt (Bundeszentralamt für Steuern) to handle Irish VAT (and future EU market VAT) through a single German return.

6. **Connect SevDesk to Stripe** — Via Make.com or the Stripe App Marketplace connector. Automate invoice creation for every subscription payment.

7. **Open Wise Business account currency balances** — Activate GBP, ZAR, AUD, and PHP sub-accounts alongside EUR. Each provides local receiving details.

---

## Key Dates & Deadlines

| Date | Obligation |
|------|-----------|
| 10th after quarter end | German VAT advance return (Umsatzsteuervoranmeldung) — quarterly while pre-revenue; monthly once VAT liability > €7,500/year |
| 10th of Mar/Jun/Sep/Dec | German corporate tax advance payments (Vorauszahlung) |
| Quarterly (varies) | UK VAT return filing |
| Quarterly | EU OSS VAT return |
| 28th after quarter end | Australia GST return (once registered) |
| Annual (April 15) | US personal tax return (Form 1040 + FBAR/FATCA + Form 5471) |
| Annual | German corporate tax return (via Steuerberater) |
| Annual | Jahresabschluss (annual financial statements) filed with Handelsregister |

---

## Steuerberater Discussion Checklist

Bring these questions to your next meeting:

- [ ] What is the exact Vilseck Gewerbesteuer Hebesatz for 2026?
- [ ] Given my SOFA status, how should my Geschäftsführer salary be structured? What is the minimum defensible salary?
- [ ] Should I take a salary at all initially, or can I defer compensation until the UG is profitable?
- [ ] How do I handle the 25% profit retention practically — does it need to be in a separate bank account, or is it just a balance sheet entry?
- [ ] Should I register for EU OSS now (before Ireland launches) or wait until the first Irish sale?
- [ ] For UK VAT: should we use Stripe Tax for collection and a filing partner for remittance, or handle it differently?
- [ ] At what revenue level does it make sense to convert from UG to GmbH?
- [ ] How do I coordinate US tax filing (Form 1040) with German corporate and personal tax obligations to avoid double taxation?
- [ ] Is the US-Germany tax treaty applicable given my SOFA status, or does SOFA override treaty provisions?
- [ ] Should I consider the Kleinunternehmerregelung (small business VAT exemption) for early-stage revenue, or is it better to be fully VAT-registered from day one given my international sales?
