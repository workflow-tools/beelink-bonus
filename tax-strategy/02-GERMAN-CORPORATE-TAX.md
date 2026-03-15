# German Corporate Tax — ML Upskill Agents UG

---

## Tax Components

### 1. Körperschaftsteuer (Corporate Income Tax)

**Rate:** 15% of taxable profit
**Applies to:** All worldwide profits of the UG
**Filed:** Annually via Körperschaftsteuererklärung
**Advance payments:** Quarterly (10 Mar, 10 Jun, 10 Sep, 10 Dec) if annual liability exceeds €400

### 2. Solidaritätszuschlag (Solidarity Surcharge)

**Rate:** 5.5% of the Körperschaftsteuer amount = 0.825% effective rate on profit
**Example:** On €10,000 profit → €1,500 KSt → €82.50 Soli

### 3. Gewerbesteuer (Trade Tax)

**Formula:** Taxable profit × 3.5% (base rate) × Hebesatz (municipal multiplier) ÷ 100

**Vilseck Hebesatz:** *TO BE CONFIRMED — contact Rathaus Vilseck or your Steuerberater*

Typical Bavarian small-town Hebesatz ranges from 300% to 380%. Using 340% as a working estimate:

- Effective Gewerbesteuer rate = 3.5% × 340% ÷ 100 = **11.9%**

**Important:** The UG receives a Freibetrag (allowance) of €24,500 for Gewerbesteuer. Profits below this threshold are exempt from trade tax. This is significant in early-stage operations — if your annual profit stays under €24,500, you pay no Gewerbesteuer at all.

### Combined Rate Estimate

| Component | Rate |
|-----------|------|
| Körperschaftsteuer | 15.000% |
| Solidaritätszuschlag | 0.825% |
| Gewerbesteuer (est. 340% Hebesatz) | 11.900% |
| **Total** | **~27.7%** |

*On profits above the €24,500 Gewerbesteuer Freibetrag. Below that, effective rate is ~15.8%.*

---

## The 25% Profit Retention Rule (UG → GmbH Path)

As a UG (haftungsbeschränkt), you are legally required to retain 25% of annual net profit (after taxes) as a reserve until accumulated Stammkapital reaches €25,000.

### How It Works

Each fiscal year:
1. Calculate net profit after all taxes
2. Set aside 25% of that net profit into the "gesetzliche Rücklage" (statutory reserve)
3. The remaining 75% is theoretically distributable (but see personal tax and GILTI implications)

### Example Progression

| Year | Net Profit | 25% Reserve | Cumulative Reserve | Remaining to €25K |
|------|-----------|-------------|-------------------|-------------------|
| 2026 | €15,000 | €3,750 | €3,750 | €21,250 |
| 2027 | €30,000 | €7,500 | €11,250 | €13,750 |
| 2028 | €50,000 | €12,500 | €23,750 | €1,250 |
| 2029 | €60,000 | €15,000 | €25,000+ | **GmbH eligible** |

### Practical Handling

The 25% reserve does NOT need to be in a separate bank account — it is a balance sheet entry. However, for your own clarity and discipline, it is strongly recommended to either:

- Maintain a separate sub-account in Wise labeled "GmbH Reserve" and transfer 25% of each quarter's net profit there, OR
- Track it meticulously in SevDesk as a separate ledger entry

Your Steuerberater will handle the formal accounting. The reserve becomes the new Stammkapital upon GmbH conversion.

### GmbH Conversion — Two Paths

**Legal basis:** §5a GmbHG (Gesetzliche Rücklage der Unternehmergesellschaft)

The 25% reserve is calculated on the Jahresüberschuss (annual profit after taxes, minus any loss carryforward from prior years). You do NOT have to wait for the reserve to reach €25,000 organically — you have two paths:

**Path A: Organic (wait for 25% reserves to accumulate)**
- Slower but requires no out-of-pocket cash
- Typical timeline: 4–8+ years depending on profitability
- Risk: Profits remain locked as long as you stay a UG

**Path B: Cash injection (Bareinlage) — accelerated**
- Inject personal funds directly into Stammkapital to reach €25,000 at any time
- Can combine with accumulated reserves (e.g., if reserves are at €10,000, inject €15,000)
- Much faster — you can convert whenever you have the cash
- Simpler documentation than reserve conversion (no audited balance sheet required)
- Can set Stammkapital to any amount ≥€25,000 (e.g., €50,000 if you want extra buffer)

**Important:** If converting using accumulated reserves (Path A), you MUST have an audited balance sheet prepared per §57e–57f GmbHG by a Wirtschaftsprüfer or vereidigter Buchprüfer. With a cash injection (Path B), this audit is not required — making it cheaper and simpler.

### Step-by-Step Conversion Process

1. **Shareholder resolution** — You (sole shareholder) resolve to increase Stammkapital to ≥€25,000 and change the company name from "UG (haftungsbeschränkt)" to "GmbH"
2. **Notarization** — Resolution and amended Gesellschaftsvertrag must be notarized (Notar appointment, ~1–2 weeks to schedule)
3. **Capital payment** (if Bareinlage) — Transfer funds to the UG bank account with Verwendungszweck: "Bareinlage zum Stammkapital der ML Upskill Agents GmbH durch den Gesellschafter Ryan Robert Hill"
4. **Handelsregister filing** — Notary submits notarized documents to Amtsgericht Amberg. Court processes the change (2–4 weeks typical, up to 6 weeks if busy)
5. **Registration complete** — HRB 8114 entry updated to show "GmbH" and new Stammkapital. Conversion is legally complete.

**Cost:** €800–2,000 (notary fees + Handelsregister fees). Higher Stammkapital does not significantly increase these costs.

**Timeline:** 4–8 weeks from notary appointment to completed registration.

### What Changes (and Doesn't Change) After Conversion

| Item | Changes? | Details |
|------|----------|---------|
| HRB number | **No** | Stays HRB 8114 at Amtsgericht Amberg |
| Steuernummer | **Usually no** | May be reassigned by Finanzamt; confirm after conversion |
| USt-IdNr | **No** | Can retain DE457209466 upon request |
| Bank accounts | **No** | Existing accounts continue; notify bank of name change |
| Contracts | **No** | Contracts continue; notify major partners of form change |
| 25% retention | **YES — eliminated** | Full profit distribution flexibility |
| Legal name | **YES** | "ML Upskill Agents GmbH" (no more "haftungsbeschränkt") |
| Tax treatment | **No** | Same KSt, Soli, GewSt rates; no taxable event from conversion itself |

### Common Pitfalls

- **Don't use reserves without an audit.** If converting via accumulated reserves (not cash injection), you need an audited balance sheet. Missing this = Handelsregister rejection.
- **Bank transfer memo matters.** Cash injections must clearly state "Bareinlage zum Stammkapital" — ambiguous transfers can be challenged.
- **Don't convert right before selling the company.** Tax authorities may view it as avoidance. Wait 6–12 months between conversion and any sale.
- **Negative capital accounts.** If you've withdrawn more than invested, a "Beitragsverlust II" can trigger unexpected tax liability at conversion. Ensure your shareholder account is positive.

### When to Convert — Decision Framework

| Trigger | Action |
|---------|--------|
| Reserves reach €25,000 organically | Convert (no reason not to — unlocks trapped capital) |
| You have €25,000+ personal cash and want to unlock retained profits now | Convert via Bareinlage |
| Annual profits exceed €50,000 | Strongly consider accelerated conversion — 25% lock-in is costing you meaningful liquidity |
| Preparing to bring on investors or partners | Convert first — GmbH is far more attractive to external parties |
| UK Ltd subsidiary planned | Convert first — GmbH parent looks more credible than UG parent |

---

## Nebenerwerb → Haupterwerb Transition

The Gewerbe-Anmeldung (14.08.2025) classifies the business as **Nebenerwerb** (side business). This section covers what happens as UG income grows relative to your WGU evaluator income.

### When Does Nebenerwerb Become Haupterwerb?

There is no single hard threshold. The determination is made by your Krankenkasse (health insurance fund) based on:

- Which income source is larger in absolute terms
- How many hours you dedicate to each activity
- The overall economic picture (Gesamteindruck)

**Practical rule:** Once your self-employment/business income exceeds your employee salary, it's considered Haupterwerb.

### Why This Matters Less Than You Might Think (UG Edition)

For a Kapitalgesellschaft (UG/GmbH), the Nebenerwerb/Haupterwerb distinction works differently than for an Einzelunternehmen:

- The UG is a **separate legal entity** — its profits are corporate income, not your personal self-employment income
- Your personal Neben/Haupt classification only matters for **social insurance** (health, pension), not for the UG's tax treatment
- The UG pays Körperschaftsteuer + Gewerbesteuer regardless of your personal classification
- What affects YOUR personal classification: any Geschäftsführer salary you draw from the UG (treated as employee income from the UG)

### SOFA + Aetna Foreign Service Simplification

Under SOFA status with Aetna Foreign Service health coverage (via spouse's DoDEA civilian employment), many of the Nebenerwerb→Haupterwerb headaches are significantly reduced:

- **Health insurance:** Your Aetna Foreign Service coverage continues regardless of your business classification — you're not in the German statutory health insurance system. The usual Krankenkasse reclassification that triggers cost increases for German self-employed doesn't apply to you.
- **Pension:** SOFA-status persons are generally not in the German Rentenversicherung system. No mandatory pension contribution changes.
- **The main impact is tax, not social insurance.** German personal income tax applies to your Geschäftsführer salary regardless of Neben/Haupt. US tax filing (Form 1040) captures everything worldwide.

### What You Should Update

When UG income meaningfully surpasses your WGU income:

1. **Gewerbeamt notification** — Update the Gewerbe-Anmeldung from Nebenerwerb to Haupterwerb at the Vilseck Rathaus (~€10–30 fee)
2. **Finanzamt** — Inform them of the change (practically, this changes nothing about how they tax you — they care about actual earnings, not the label)
3. **IHK fees** — Will increase proportionally with revenue (base fee ~€150–300/year + ~0.09% of business profits). Modest increases.

### Your WGU Income — Special Considerations

Your WGU evaluator income is paid in USD from a US employer with no German establishment. Under SOFA status:

- This income is subject to US taxation (reported on Form 1040)
- German taxation of this income depends on your tax residency classification (beschränkt vs. unbeschränkt steuerpflichtig) — discuss with Steuerberater
- It is a separate income stream from your UG activities
- It counts toward your total income picture for Neben/Haupt classification purposes, but given SOFA + Aetna Foreign Service coverage, the practical impact is limited to the Gewerbeamt paperwork

---

## VAT (Umsatzsteuer) — Domestic

Your UG is registered for German VAT (USt-IdNr: DE457209466). For domestic German sales (PraxisProfi):

**Rate:** 19% standard rate
**Filing frequency rules:**
- Annual VAT liability > €7,500 → monthly advance returns
- Annual VAT liability €1,000–7,500 → quarterly
- Annual VAT liability < €1,000 → annual only

**Current status:** The Steuernummer notification from Finanzamt Amberg (01.10.2025) set the Voranmeldungszeitraum to Kalendermonat (monthly). However, with no revenue yet, **quarterly filing is acceptable for now**. The Finanzamt will reassess the filing period once revenue data is available — and getting bumped to monthly is a good problem to have (it means revenue has grown). When the time comes, consider applying for a Dauerfristverlängerung (permanent one-month extension) to ease monthly deadlines.

**Kleinunternehmerregelung (§19 UStG):** If annual revenue is under €22,000, you could opt for small business exemption (no VAT charged, no input VAT reclaimed). However, this is likely inadvisable given your international sales — you need full VAT registration for EU OSS and UK VAT compliance.

---

## Quarterly Advance Payments (Vorauszahlung) Schedule

Once your Steuerberater files your first corporate tax return and the Finanzamt assesses your liability, they will set quarterly advance payment amounts.

| Quarter | Due Date | What's Due |
|---------|----------|-----------|
| Q1 | 10 March | Körperschaftsteuer + Soli advance |
| Q2 | 10 June | Körperschaftsteuer + Soli advance |
| Q3 | 10 September | Körperschaftsteuer + Soli advance |
| Q4 | 10 December | Körperschaftsteuer + Soli advance |

Gewerbesteuer advances are billed separately by the municipality (Vilseck), typically on 15 Feb, 15 May, 15 Aug, 15 Nov.

**Tip:** If your projected profit changes significantly, file a Herabsetzungsantrag (request to reduce advance payments) to avoid overpaying.

---

## Deductible Expenses to Track

These reduce your taxable profit:

- Geschäftsführer salary (once you start paying yourself)
- Anthropic API costs (Claude usage for all products)
- Deepgram API costs (voice-to-text)
- Vercel hosting (all deployments)
- Clerk authentication (per-product)
- Stripe fees (2.9% + €0.25 per transaction + 0.5% Stripe Tax fee)
- Domain registrations (all markets)
- Google Ads and LinkedIn Ads marketing spend
- Conference attendance (RCN Education Forum, etc.)
- SevDesk subscription
- Wise Business account fees
- Professional services (Steuerberater, US tax advisor, legal counsel)
- Home office deduction (Arbeitszimmer) if applicable
- Computer equipment, software licenses
- PhD-related expenses IF directly connected to business operations (discuss with Steuerberater)

---

## Action Items

- [ ] Confirm Vilseck Gewerbesteuer Hebesatz
- [ ] Ask Steuerberater: Given early-stage revenue, should Vorauszahlung be set to €0 initially?
- [ ] Set up a "GmbH Reserve" tracking mechanism (Wise sub-account or SevDesk ledger)
- [ ] Ensure all deductible expenses are being captured in SevDesk from day one
- [ ] Discuss Kleinunternehmerregelung decision with Steuerberater (likely: opt out and register fully)
