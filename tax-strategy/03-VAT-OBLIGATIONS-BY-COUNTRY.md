# VAT/GST Obligations by Country

All products are B2C digital SaaS subscriptions sold by ML Upskill Agents UG (German entity) to individual consumers (nurse assessors/educators) in each market.

---

## Handling Strategy: Stripe Tax + Filing Partners

**Collection:** Stripe Tax calculates and collects the correct VAT/GST at checkout for each jurisdiction. Cost: 0.5% of transaction value.

**Filing & Remittance:** Stripe does NOT file returns or remit taxes to authorities. You need either:
- Your Steuerberater (for German VAT and EU OSS)
- A filing partner like Taxually or Marosa (for UK, AU, PH, ZA)
- Direct filing (possible but time-consuming)

---

## 1. United Kingdom — WritingPAD

| Detail | Value |
|--------|-------|
| **Product** | WritingPAD |
| **Currency** | GBP |
| **VAT Rate** | 20% |
| **Registration Threshold** | £0 (zero — non-UK businesses must register from first sale) |
| **Registration Body** | HMRC Non-Established Taxable Persons Unit (NETPU) |
| **Filing Frequency** | Quarterly |
| **How to Register** | Apply to HMRC NETPU (Ruby House, Aberdeen) or online via MTD |
| **VAT Number Format** | GB + 9 digits |
| **B2B Reverse Charge?** | Yes — if selling to VAT-registered UK businesses, reverse charge applies |

### Timeline
- **Register:** BEFORE launching WritingPAD UK
- **Stripe Tax:** Enable UK VAT collection in Stripe Tax settings
- **First return:** Due ~1 month after end of first VAT quarter

### Pricing Impact
- Customer sees: £9.99/month (VAT inclusive) → you receive £8.33 net + £1.66 VAT
- OR: £9.99 + VAT = £11.99 displayed price (decide with Steuerberater — inclusive pricing is more consumer-friendly)

### Action Items
- [ ] Register with HMRC for UK VAT before first UK sale
- [ ] Decide: VAT-inclusive or VAT-exclusive displayed pricing
- [ ] Enable UK in Stripe Tax product tax codes
- [ ] Set up quarterly UK VAT return process (Steuerberater or filing partner)

---

## 2. Ireland — ProPrecept Ireland

| Detail | Value |
|--------|-------|
| **Product** | ProPrecept Ireland (WritingNCAD) |
| **Currency** | EUR |
| **VAT Rate** | 23% |
| **Registration Threshold** | N/A — handled via EU OSS |
| **Filing Mechanism** | EU One-Stop-Shop (Union Scheme) via BZSt |
| **Filing Frequency** | Quarterly |

### EU OSS (One-Stop-Shop) — Union Scheme

As a German-registered business selling digital services to consumers in other EU countries, you use the **Union Scheme** of the EU One-Stop-Shop. This means:

- You register ONCE through Germany's BZSt (Bundeszentralamt für Steuern)
- You file ONE quarterly return covering ALL EU B2C digital service sales
- The OSS distributes the VAT to each member state's tax authority
- You do NOT need to register separately in Ireland (or any other EU country)

This covers Ireland now and will automatically cover any future EU market: Germany (domestic, separate), Austria, France, Spain, Finland, Sweden (if EU sales), etc.

### Timeline
- **Register for EU OSS:** Before first Irish sale. Apply via BZSt online portal (BZStOnline)
- **First return:** Due by end of month following the quarter (e.g., Q1 Jan-Mar → due April 30)

### Pricing Impact
- Customer sees: €10.99/month → you receive €8.93 net + €2.06 VAT (at 23%)

### Action Items
- [ ] Register for EU OSS Union Scheme via BZSt
- [ ] Enable Ireland in Stripe Tax
- [ ] Coordinate OSS quarterly returns with Steuerberater

---

## 3. Germany — PraxisProfi (Future)

| Detail | Value |
|--------|-------|
| **Product** | PraxisProfi |
| **Currency** | EUR |
| **VAT Rate** | 19% |
| **Registration** | Already registered (USt-IdNr: DE457209466) |
| **Filing** | Standard German Umsatzsteuervoranmeldung (not via OSS — domestic sales excluded from OSS) |

Domestic German sales are handled through your regular German VAT returns, NOT through EU OSS.

---

## 4. South Africa — ProPrecept RSA

| Detail | Value |
|--------|-------|
| **Product** | ProPrecept RSA |
| **Currency** | ZAR |
| **VAT Rate** | 15% |
| **Registration Threshold** | ZAR 1,000,000 annual B2C sales (~€50K) |
| **Registration Body** | SARS (South African Revenue Service) |
| **Voluntary Registration** | Possible if annual sales exceed ZAR 50,000 |
| **B2B Exception** | As of April 2025, foreign suppliers to VAT-registered SA businesses are exempt from SA VAT registration (reverse charge applies) |

### Key Detail: Threshold-Based Registration
You do NOT need to register until B2C sales exceed ZAR 1M/year. Given WritingPAD RSA pricing (R149–R1,499/year), you would need roughly 670+ monthly subscribers to hit this threshold. This is likely a Year 2+ concern.

### When to Register
- Monitor cumulative ZAR B2C revenue quarterly
- When approaching ZAR 800K trailing 12-month, begin registration process
- SARS provides a simplified registration for foreign electronic services providers

### Action Items
- [ ] No immediate action required — post-revenue concern
- [ ] Track ZAR revenue in SevDesk with running 12-month total
- [ ] When approaching ZAR 800K, engage South African tax consultant for SARS registration

---

## 5. Australia — ProPrecept Australia

| Detail | Value |
|--------|-------|
| **Product** | ProPrecept Australia |
| **Currency** | AUD |
| **GST Rate** | 10% |
| **Registration Threshold** | AUD 75,000 annual Australian sales |
| **Registration Body** | ATO (Australian Taxation Office) |
| **Simplified Registration** | Available for foreign digital service providers — no ABN needed |
| **Filing Frequency** | Quarterly (due 28th of month after quarter end) |

### When to Register
Similar to South Africa, this is threshold-based. At AUD $12.99/month pricing, you'd need roughly 480+ monthly subscribers to hit AUD 75K. Likely Year 2+.

### Simplified Registration Benefits
- No ABN (Australian Business Number) required
- Online registration and filing through ATO non-resident portal
- Cannot claim input tax credits (simplified status limitation)

### Action Items
- [ ] No immediate action — post-revenue concern
- [ ] Track AUD revenue with running 12-month total
- [ ] Register within 21 days of exceeding AUD 75K threshold

---

## 6. Philippines — WriteRLE

| Detail | Value |
|--------|-------|
| **Product** | WriteRLE |
| **Currency** | PHP |
| **VAT Rate** | 12% |
| **Registration Threshold** | ZERO — all foreign digital service providers must register (RA 12023) |
| **Registration Body** | BIR (Bureau of Internal Revenue) |
| **Effective Date** | July 2, 2025 |
| **Filing Frequency** | Quarterly VAT returns |

### Critical: Registration Required Before First Sale

Unlike South Africa and Australia, the Philippines has NO threshold exemption. Republic Act 12023 (signed October 2024, effective July 2025) requires ALL foreign providers of digital services to Philippine consumers to register with BIR.

If WriteRLE will be operational by July 2025, register proactively. If launch is later, register before the first sale.

### B2B Treatment
Reverse charge applies for B2B sales to Philippine businesses — but WriteRLE is predominantly B2C (individual clinical instructors), so VAT registration is unavoidable.

### Action Items
- [ ] Register with BIR before WriteRLE launches (or by July 1, 2025, whichever is earlier)
- [ ] Enable Philippines in Stripe Tax
- [ ] Identify a Philippine tax compliance partner or use a filing automation service

---

## Summary: Registration Priority & Timeline

| Priority | Market | Action | When |
|----------|--------|--------|------|
| **URGENT** | UK | Register for UK VAT with HMRC | Before WritingPAD UK launch |
| **URGENT** | EU (Ireland+) | Register for EU OSS Union Scheme via BZSt | Before ProPrecept Ireland launch |
| **SOON** | Philippines | Register with BIR for VAT | Before WriteRLE launch or July 2025 |
| **LATER** | South Africa | Register when B2C revenue approaches ZAR 1M | Monitor quarterly |
| **LATER** | Australia | Register when AU revenue approaches AUD 75K | Monitor quarterly |

---

## Stripe Tax Configuration Checklist

In Stripe Dashboard → Settings → Tax:

- [ ] Set business address (Hohe Straße 13, 92249 Vilseck, Germany)
- [ ] Add tax registration: Germany (DE457209466)
- [ ] Add tax registration: UK (once received from HMRC)
- [ ] Set product tax code: "Software as a Service (SaaS)" — txcd_10103000
- [ ] Enable automatic tax calculation for each product/price
- [ ] Configure per-market pricing (ensure prices are inclusive or exclusive of tax consistently)
- [ ] Test checkout flows to verify correct VAT/GST appears at checkout
