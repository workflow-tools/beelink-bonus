# Misawa Data GK — Formation Checklist

> Operational checklist for incorporating a Godo Kaisha in Japan as a
> foreign-owned subsidiary of ML Upskill Agents UG (Germany).
>
> **Source:** Compiled from Gemini analysis (March 2026), cross-verified
> against FEASIBILITY.md and IP-STRATEGY.md. Items marked ⚠ need
> professional verification before acting.

---

## Phase 1: Pre-Formation & Structuring

- [ ] **Determine ownership structure:** Will ML Upskill Agents UG own
  the GK directly (wholly-owned subsidiary), or will Ryan Hill own it
  as an individual?
  - Corporate ownership is cleaner for B2B IP licensing and transfer pricing
  - But individual ownership may simplify banking (fewer layers of foreign docs)
  - ⚠ Confirm with Steuerberater which structure is better for German tax reporting

- [ ] **Secure a Resident Representative (業務執行社員 / ぎょうむしっこうしゃいん)**
  - Japanese law no longer strictly requires a resident director for a GK
  - **But Japanese banks effectively require one** to open the corporate account
  - This is the single hardest step in the process — banking depends on it
  - Options: nominee director service (¥75K-150K/month per FEASIBILITY.md),
    trusted local contact, or SOFA-status hire (temporary)
  - ⚠ Vet nominee providers carefully — they carry full Companies Act liability

- [ ] **Establish a Registered Address (本店所在地 / ほんてんしょざいち)**
  - Virtual offices work for registration but are heavily penalized by banks
  - Physical office required if using GK to sponsor a Business Manager Visa
  - Misawa / Hachinohe area: cheap commercial space available
  - The Beelink server room can double as the registered address if it's
    a physical location you control (not a PO box)

- [ ] **Draft Articles of Incorporation (定款 / ていかん)**
  - Must be drafted in Japanese
  - Define business purposes broadly:
    - データ処理サービス業 (Data processing services)
    - ソフトウェアの開発及び販売 (Software development and sales)
    - 知的財産の使用許諾 (Intellectual property licensing)
    - 各種データセットの企画、制作及び販売 (Planning, creation, and sales of datasets)
  - GK定款 does NOT require notarization (unlike KK)
  - ⚠ Have a Judicial Scrivener (司法書士 / しほうしょし) draft this

---

## Phase 2: Capitalization & Registration

- [ ] **Transfer initial capital to Japan**
  - Capital must be deposited into a Japanese personal bank account of one
    of the investors or the resident representative
  - This is why the resident representative is crucial — they need a personal
    account to receive the capital before the company exists
  - GK can incorporate with ¥1, but ¥3M-5M is the practical minimum to be
    taken seriously by banks and landlords
  - The ¥30M target (Business Manager Visa) is a long-term accumulation goal,
    not a formation requirement

- [ ] **Execute incorporation documents**
  - Apply personal/corporate seals (判子 / はんこ — also called 印鑑 / いんかん)
  - If ML Upskill Agents UG is the parent:
    - Need notarized affidavits from Germany proving the UG's existence
    - Need certified German-to-Japanese translation of UG registration documents
    - Need proof of Ryan Hill's authority to act for the UG
  - ⚠ This is the step where a Judicial Scrivener earns their fee

- [ ] **File with the Legal Affairs Bureau (法務局 / ほうむきょく)**
  - The Judicial Scrivener handles this filing
  - Registration takes approximately 1-2 weeks
  - Once approved, the GK officially exists as a legal entity
  - Registration tax: ~¥60,000 (GK is cheaper than KK)

---

## Phase 3: Post-Registration ("Valley of Death")

This phase is called the "valley of death" because many foreign-owned
startups stall here. The company legally exists but cannot function without
a bank account.

- [ ] **Open the corporate bank account**
  - **Apply to multiple banks simultaneously** — expect rejections
  - Startup-friendly options (from most to least accessible):
    1. GMO Aozora Net Bank — online-first, more tolerant of foreign ownership
    2. PayPay Bank — relatively new, less bureaucratic
    3. SBI Sumishin Net Bank — online-friendly
    4. SMBC (三井住友 / みついすみとも) — traditional, harder but more credible
  - Be prepared to show:
    - Business plan (in Japanese)
    - IP architecture documentation
    - German UG history and registration proof
    - Explanation of revenue model (JDEX data sales)
  - The resident representative's personal relationship with a bank branch
    can make or break this step
  - ⚠ Budget 2-4 weeks for this process

- [ ] **Transfer capital from representative's personal account to corporate account**
  - Once the corporate account is open, move the initial capital
  - Keep transfer records for tax documentation

- [ ] **File tax notifications (within 2 months of incorporation)**
  - National Tax Agency (国税庁 / こくぜいちょう): 法人設立届出書
  - Prefectural tax office: 法人設立届出書 (separate form)
  - City/town tax office: 法人設立届出書 (yet another form)
  - ⚠ A Tax Accountant (税理士 / ぜいりし) handles all of these

- [ ] **Register for Social Insurance (社会保険 / しゃかいほけん)**
  - Required immediately if the GK pays a salary to anyone, including
    a resident director
  - Health insurance (健康保険 / けんこうほけん) + pension (厚生年金 / こうせいねんきん)
  - Even for a single-employee company

---

## Required Professionals

| Role | Japanese | Why | When |
|------|----------|-----|------|
| Judicial Scrivener | 司法書士 (しほうしょし) | Drafts 定款, handles 法務局 filing | Phase 1-2 |
| Tax Accountant | 税理士 (ぜいりし) | Transfer pricing docs, NTA filings, ongoing compliance | Phase 2 onwards |
| Nominee Service | 代表社員サービス | Resident representative for banking | Phase 1 onwards |
| IP Attorney | 弁理士 (べんりし) | Verify database IP rights for GK-generated datasets | Before first JDEX listing |

---

## Transfer Pricing Warning

Gemini flags this accurately: the UG→GK license (where UG charges the GK
a royalty for using the Synth-Factory pipeline) is a **transfer pricing
audit trigger** for both the German Finanzamt (税務署 / ぜいむしょ) and the
Japanese NTA (国税庁 / こくぜいちょう).

**Mitigation (from IP-STRATEGY.md hybrid approach):**
- License the software pipeline at a standard, benchmarkable SaaS rate
  (not an inflated royalty)
- Have the GK own the output data (Option B) — clearly separates value creation
- Document comparable license rates for similar software tools
- Keep the royalty rate reasonable (10%) to avoid "profit stripping" accusations
- The Germany-Japan DTA Article 12 makes royalties 0% withholding at source,
  which is legitimate — but the rate itself must be arm's-length

⚠ Get a Steuerberater AND a Zeirishi to sign off on the transfer pricing
arrangement BEFORE the first royalty payment flows.

---

## JDEX Procurement Reality

Japanese B2B procurement — even on marketplace platforms — follows
specific documentation conventions for amounts over ¥30,000:

- **見積書 (みつもりしょ — Estimate/Quote):** Formal price quotation
  with company seal, before purchase approval
- **請求書 (せいきゅうしょ — Invoice):** After delivery, for payment processing
- **納品書 (のうひんしょ — Delivery Note):** Proof of delivery,
  triggers payment release in accounting systems
- **領収書 (りょうしゅうしょ — Receipt):** After payment, for records

Dr. Tanaka's accounting department at Sakura AI Research Institute would
likely require at least a 見積書 and 請求書 in standard Japanese format
with proper company information and seals.

**Action items:**
- [ ] Verify whether JDEX auto-generates these documents for sellers
- [ ] If not, prepare templates with VilseckKI/GK letterhead
- [ ] UG's German registration is fine as the seller, but the paperwork
  format should look natively Japanese to avoid procurement delays

---

*Cross-references:*
- `MISAWA-DATA-GK-FEASIBILITY.md` — overall business plan
- `IP-STRATEGY.md` — licensing architecture and DTA analysis
- `../synth-factory/docs/USER-STORY-DR-TANAKA.md` — procurement in context
- `../synth-factory/docs/R-ECOSYSTEM-FLYWHEEL.md` — commercial strategy
