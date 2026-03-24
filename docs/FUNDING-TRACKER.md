# ML Upskill Agents UG — Funding Opportunity Tracker

> **Master list of all identified funding opportunities.**
> Updated by every Cowork session that touches funding strategy.
> See `FUNDING-PROJECT-INSTRUCTIONS.md` for intake protocol.

---

## Dashboard

| Metric | Value |
|--------|-------|
| **Opportunities tracked** | 16 (7 from Mistral research added, 4 eliminated after vetting) |
| **Actionable now (grants)** | 4 (Digitalbonus, BayTOU*, Innovationsgutscheine, Start?Zuschuss! 22nd round) |
| **Actionable now (loan)** | 2 (KfW StartGeld, LfA GuW) |
| **Backup grant** | 1 (BayTP+ — if BayTOU blocked by Nebenerwerb) |
| **Needs consortium** | 1 (BMBF AI-KMU) |
| **Non-financial / networking** | 2 (AI Accelerator, KI-Transfer Plus) |
| **Mezzanine (backup)** | 1 (Mikromezzaninfonds) |
| **Eliminated / Not applicable** | 5 (AI NATION, EXIST, HTGF, EIC Accelerator, GRW) |
| **⚠️ NEBENERWERB FLAG** | BayTOU requires Haupterwerb — Gewerbe currently Nebenerwerb |
| **Company founded** | ~August 2025 (~7 months old) |
| **Max stacked grant funding (realistic)** | €87,500–€126,500 (Digitalbonus reduced to €7.5K–€15K) |
| **ELSTER account** | ✅ Confirmed active |
| **Last full review** | 2026-03-24 |

---

## Tier 1 — Apply Now

### Digitalbonus Bayern — DIGBONUS

| Field | Value |
|-------|-------|
| **Program** | Digitalbonus Bayern (Plus + Standard combo) |
| **Funder** | Bayerisches Staatsministerium für Digitales |
| **Max Amount** | €30,000 (Digitalisierung Plus) + €7,500 (IT-Sicherheit Standard) = €37,500 |
| **Funding Rate** | 50% of eligible costs |
| **Duration** | Project-dependent (claim within program lifetime: Jul 2024 – Dec 2027) |
| **Deadline** | **NEW APPLICATIONS OPEN APRIL 1, 2026 at 10:00 AM** (monthly contingent) |
| **Eligible Expenses** | Software dev, consulting, licenses (2.1); Security hardware, firewall, NAS, pen testing (2.2) |
| **Eligibility** | Small businesses in Bayern (<50 employees, <€10M turnover). Requires ELSTER business account. |
| **Application Language** | DE |
| **Source URL** | https://www.digitalbonus.bayern/foerderprogramm/ |
| **Bezirksregierung** | Regierung der Oberpfalz, Abt. 27 — Tel: +49 (0)941 5680-1555, digitalbonus@reg-opf.bayern.de |
| **Confidence** | HIGH |
| **Last Verified** | 2026-03-24 |

**Fit Assessment (REVISED 2026-03-24):**
- Strategic fit: ~~9/10~~ → **5/10** — Program is designed for businesses ADOPTING tech, not BUILDING tech products
- Two key exclusions apply:
  1. **Eigenleistungen excluded** — Only external provider services are eligible, not your own dev work
  2. **Products for resale excluded** — "IKT-Lösungen, die gegen Entgelt in anderen Unternehmen zum Einsatz kommen sollen und dort eine förderfähige Maßnahme sind, sind nicht förderfähig"
- Track 2.2 (IT-Sicherheit) still viable for security hardware/services (€7,500)
- Track 2.1 (Digitalisierung) only viable if reframed as internal operations digitalization, NOT Data Forge development
- **Realistic revised amount: €7,500–€15,000** (down from €37,500)
- Effort to apply: MEDIUM — Detailed plan exists in GRANT-APPLICATION-PLAN.md but **NEEDS MAJOR REVISION** (currently frames this as Data Forge development)
- Expected outcome: LIKELY for Track 2.2; UNCLEAR for Track 2.1 — ask Bezirksregierung
- Stacking: Yes — different expense categories from BayTOU

**Status Updates (2026-03-24):**
- ✅ ELSTER account confirmed active
- ⚠️ Must contact Reg. Oberpfalz THIS WEEK for required pre-consultation
- ⚠️ CRITICAL QUESTION for consultation: Does the product-for-sale exclusion apply to synthetic data pipeline?
- ⚠️ April 1 opening is date-sensitive — monthly contingent means early submission matters

**Action Items:**
- [ ] URGENT: Call Reg. Oberpfalz (+49 941 5680-1555) — ask about product-for-sale exclusion applicability
- [ ] Test ELSTER certificate login on digitalbonus.bayern portal
- [ ] Gather cost quotes for Track 2.2 (security hardware/services) — this is the safe track
- [ ] If Track 2.1 confirmed eligible: reframe application around internal operations digitalization
- [ ] REVISE GRANT-APPLICATION-PLAN.md — current Data Forge framing likely violates exclusions
- [ ] Submit Track 2.2 on April 1; submit Track 2.1 only if confirmed eligible after consultation

**Detailed Plan:** See `GRANT-APPLICATION-PLAN.md` in repo root.

---

### BayTOU (Bayerische Technologieorientierte Unternehmensgründung) — BAYTOU

| Field | Value |
|-------|-------|
| **Program** | BayTOU — Technologieorientierte Unternehmensgründungen |
| **Funder** | Bayerisches Staatsministerium für Wirtschaft (StMWi) via Bayern Innovativ |
| **Max Amount** | €150,000 (software/services); €26,000 (concept phase) |
| **Funding Rate** | 35% (concept) to 45% (realization phase) |
| **Duration** | Project-dependent |
| **Deadline** | Continuous — no deadline |
| **Eligible Expenses** | R&D, software development, external consulting, personnel |
| **Eligibility** | Tech-oriented founders/young SMEs in Bavaria, <6 years old (~7 months ✅), <10 employees |
| **Application Language** | DE |
| **Source URL** | https://www.bayern-innovativ.de/en/page/baytou-requirements/ |
| **Confidence** | HIGH |
| **Last Verified** | 2026-03-24 |

**Fit Assessment:**
- Strategic fit: 9/10 — Directly funds Data Forge domain expansion development
- Effort to apply: MEDIUM — Requires project plan, budget, innovation narrative
- Expected outcome: POSSIBLE — Competitive but well-aligned
- Stacking: Yes — stacks with Digitalbonus (different expense categories)

**Risk Flag:** Program requires dedicating "most of working time" to the startup. PhD + WGU evaluator work could be questioned. Mitigation: PhD research (GRUND) directly feeds Data Forge product; WGU is part-time supplementary.

**Action Items:**
- [x] ~~Get ELSTER business account set up~~ ✅ Confirmed
- [ ] Contact Bayern Innovativ for initial consultation
- [ ] Draft project plan: Healthcare + Insurance domain expansion
- [ ] Prepare budget at €80K–€150K eligible costs (→ €36K–€67.5K grant at 45%)
- [ ] Prepare proof of co-financing ability (bank statements or KfW loan commitment)

---

## Tier 1.5 — Apply Next Round (Confirmed Eligible)

### Start? Zuschuss! — STARTZUSCHUSS

| Field | Value |
|-------|-------|
| **Program** | Start? Zuschuss! |
| **Funder** | Bayerisches Staatsministerium für Wirtschaft (StMWi) |
| **Max Amount** | €36,000/year |
| **Funding Rate** | 50% of eligible expenses |
| **Duration** | 12 months |
| **Deadline** | 22nd round est. ~Jul 2026 (not yet announced); 23rd round est. ~Jan 2027 |
| **Next Cycle** | Funding start October 1, 2026 |
| **Eligible Expenses** | Personnel, rent, product launch, R&D |
| **Eligibility** | Founded ≤2 years before deadline; registered in Bavaria; top 20 selected per cycle |
| **Application Language** | EN accepted |
| **Source URL** | https://www.stmwi.bayern.de/wettbewerbe/startzuschuss/ |
| **Confidence** | HIGH — eligibility confirmed; round dates estimated from pattern |
| **Last Verified** | 2026-03-24 |

**Round Schedule (from observed pattern):**

| Round | Application Window | Deadline | Funding Start |
|-------|-------------------|----------|---------------|
| 21st (most recent) | Nov 20, 2025 – Jan 9, 2026 | Jan 9, 2026 12:00 | Apr 1, 2026 |
| **22nd (target)** | ~May/Jun 2026 – ~Jul 2026 | ~Jul 2026 | Oct 1, 2026 |
| 23rd (backup) | ~Nov 2026 – ~Jan 2027 | ~Jan 2027 | Apr 1, 2027 |

**Eligibility Analysis:**
- Founded ~Aug 2025. At any 2026 or early-2027 deadline, company is well under 2 years old. ✅ CONFIRMED ELIGIBLE.
- Eligible for 22nd round AND 23rd round. Target the 22nd for earliest funding.

**Action Items:**
- [ ] Monitor gruenderland.bayern/startzuschuss monthly starting May 2026 for 22nd round announcement
- [ ] Begin pitch preparation NOW — competitive program (top 20 selected per cycle)
- [ ] Build evidence by June: revenue traction, 3+ Data Forge domains, Bavarian customer interest letters
- [ ] Study winning profiles from past rounds for pitch calibration

---

### BMBF AI Funding for KMU — BMBFAI

| Field | Value |
|-------|-------|
| **Program** | BMBF Förderung für KI-Projekte kleiner und mittlerer Unternehmen |
| **Funder** | Bundesministerium für Bildung und Forschung (BMBF) |
| **Max Amount** | €100,000/year for startups |
| **Funding Rate** | 50–75% of eligible project costs |
| **Duration** | Project-dependent |
| **Deadline** | 2026 calls planned for "KI — Data Science" (dates TBD) |
| **Eligible Expenses** | R&D, personnel, materials |
| **Eligibility** | KMU; requires consortium with science/industry partners |
| **Application Language** | DE |
| **Source URL** | https://www.bayernportal.de/dokumente/leistung/8034893005230 |
| **Confidence** | MEDIUM — needs consortium partner |
| **Last Verified** | 2026-03-24 |

**Fit Assessment:**
- Strategic fit: 8/10 — Synthetic data for AI is exactly "KI — Data Science"
- Effort to apply: HIGH — 10-page proposal + consortium formation + PT-Outline portal
- Expected outcome: POSSIBLE — Strong if FAU partners
- Stacking: Check rules, but likely compatible with Bavarian state grants

**Action Items:**
- [ ] Watch iuk-bayern.de for 2026 call announcements
- [ ] Discuss consortium possibility with FAU PhD supervisor
- [ ] If call opens, prepare 10-page project outline via PT-Outline portal

---

### KfW ERP-Gründerkredit StartGeld — KFW

| Field | Value |
|-------|-------|
| **Program** | ERP-Gründerkredit – StartGeld (067) |
| **Funder** | KfW (via commercial banks) |
| **Max Amount** | €200,000 (up to €80K working capital) |
| **Funding Rate** | Subsidized loan; KfW assumes 80% credit risk |
| **Duration** | Up to 10 years |
| **Deadline** | Continuous — apply through Hausbank |
| **Eligible Expenses** | Equipment, machinery, rent, personnel, inventory, working capital |
| **Eligibility** | Startups and young companies in first 5 years |
| **Application Language** | DE |
| **Source URL** | https://www.kfw.de/inlandsfoerderung/Unternehmen/Gründen-Nachfolgen/ |
| **Confidence** | HIGH |
| **Last Verified** | 2026-03-24 |

**Fit Assessment:**
- Strategic fit: 7/10 — Not a grant, but useful for co-financing BayTOU or scaling
- Effort to apply: LOW-MEDIUM — Through your commercial bank
- Expected outcome: LIKELY — KfW's 80% risk assumption makes banks willing
- Stacking: Excellent — loan can provide co-financing proof for BayTOU

**Action Items:**
- [ ] Contact Hausbank when co-financing needed (especially for BayTOU)

---

## Tier 3 — Non-Financial / Networking

### Bavarian AI Innovation Accelerator — BAIACC

| Field | Value |
|-------|-------|
| **Program** | Bavarian AI Innovation Accelerator for SMEs |
| **Funder** | Bavarian State Ministry for Digital Affairs via fortiss |
| **Max Amount** | Non-financial (training, workshops, networking) |
| **Duration** | Through December 2026 |
| **Source URL** | https://www.fortiss.org/en/news/details/bavaria-launches-ai-innovation-accelerator-for-smes |
| **Confidence** | MEDIUM |
| **Last Verified** | 2026-03-24 |

**Fit Assessment:**
- Strategic fit: 6/10 — Credibility + networking for future financial applications
- Effort to apply: LOW
- Expected outcome: LIKELY

---

### KI-Transfer Plus — KITRANSFER

| Field | Value |
|-------|-------|
| **Program** | KI-Transfer Plus (Bayern Innovativ) |
| **Funder** | Bayern Innovativ |
| **Max Amount** | Non-financial (9-month AI competency program) |
| **Duration** | 9 months |
| **Contact** | bewerbung-ki-transfer-plus@bayern-innovativ.de |
| **Source URL** | https://www.bayern-innovativ.de/en/detail/ai-transfer-plus/ |
| **Confidence** | MEDIUM |
| **Last Verified** | 2026-03-24 |

**Fit Assessment:**
- Strategic fit: 5/10 — Demonstrates Bavarian state alignment; networking
- Effort to apply: LOW

---

## Tier 4 — Backup / Conditional

### Mikromezzaninfonds Deutschland — MIKROMEZZ

| Field | Value |
|-------|-------|
| **Program** | Mikromezzaninfonds Deutschland III |
| **Funder** | BMWK / ESF |
| **Max Amount** | €150,000 |
| **Cost** | 11% annual (with 3% subsidy → ~8% effective) |
| **Duration** | Through 2029 |
| **Eligible** | Small/micro enterprises, founders, migration background |
| **Source URL** | https://www.mikromezzaninfonds-deutschland.de/ |
| **Confidence** | MEDIUM |
| **Last Verified** | 2026-03-24 |

**Note:** This is mezzanine capital (quasi-equity), NOT a grant. No voting rights, but costs 8%/year. Only consider if grants + KfW are insufficient.

---

### LfA Förderbank Bayern — Gründungs- und Wachstumskredit (GuW) — LFA

| Field | Value |
|-------|-------|
| **Program** | Gründungs- und Wachstumskredit (GuW) |
| **Funder** | LfA Förderbank Bayern (via Hausbank) |
| **Max Amount** | No fixed cap (formerly Startkredit was capped; GuW replaced it Jan 2024) |
| **Funding Rate** | Subsidized interest rate (below market; subsidized from Bavarian state budget + KfW refinancing) |
| **Duration** | Variable repayment terms |
| **Deadline** | Continuous — apply through Hausbank |
| **Eligible Expenses** | Startup investment, working capital, equipment |
| **Eligibility** | Founders and young companies in first 5 years in Bavaria |
| **Application Language** | DE |
| **Source URL** | https://www.lfa.de/website/de/foerderangebote/gruendung-wachstum/gruendung/Gruendungs-und-Wachstumskredit-GuW/ |
| **Confidence** | HIGH |
| **Last Verified** | 2026-03-24 |

**Note:** Complementary to KfW StartGeld. LfA is Bavaria-specific and may offer better terms for Bavarian startups. Apply through same Hausbank channel as KfW.

---

### Innovationsgutscheine Bayern — INNOGUTVOUCHER

| Field | Value |
|-------|-------|
| **Program** | Innovationsgutscheine für kleine Unternehmen und Handwerksbetriebe |
| **Funder** | Bayerisches Staatsministerium für Wirtschaft via Bayern Innovativ |
| **Max Amount** | €38,000 (Standard, as of 2026); up to €80,000 (Spezial) |
| **Funding Rate** | 40% standard; up to 60% if university/research institution involved |
| **Duration** | Project-dependent |
| **Deadline** | Continuous / rolling |
| **Eligible Expenses** | Planning, development, implementation of new products/processes/services; external R&D consulting |
| **Eligibility** | Small businesses <50 employees, <€10M turnover, in Bavaria; founders with HQ in Bavaria |
| **Application Language** | DE |
| **Source URL** | https://www.stmwi.bayern.de/foerderungen/innovationsgutscheine/ |
| **Confidence** | HIGH |
| **Last Verified** | 2026-03-24 |

**Fit Assessment:**
- Strategic fit: 8/10 — Funds external R&D consulting and product development for Data Forge
- Effort to apply: LOW-MEDIUM — Simpler than BayTOU
- Expected outcome: LIKELY — Program explicitly targets small businesses and founders
- Stacking: Check with Bayern Innovativ — may overlap with Digitalbonus eligible expenses

**Action Items:**
- [ ] Verify UG eligibility with Bayern Innovativ (program says "kleine Unternehmen" — UG should qualify)
- [ ] Check stacking rules with Digitalbonus (different programs, possibly different eligible expenses)
- [ ] If FAU partnership possible, funding rate rises to 60%

---

### BayTP+ (Bayerisches Technologieförderungs-Programm Plus) — BAYTPPLUS

| Field | Value |
|-------|-------|
| **Program** | Bayerisches Technologieförderungs-Programm Plus (BayTP+) |
| **Funder** | Bayerisches Staatsministerium für Wirtschaft via Bayern Innovativ |
| **Max Amount** | Up to 50% of eligible costs (no fixed cap stated) |
| **Funding Rate** | 25–50% depending on project type and company size |
| **Duration** | Project-dependent |
| **Deadline** | Continuous / rolling |
| **Eligible Expenses** | Development of technologically new products, production processes, knowledge-based services |
| **Eligibility** | SMEs in Bavaria, <400 employees for development projects |
| **Application Language** | DE |
| **Source URL** | https://www.bayern-innovativ.de/en/geschaeftsfelder/projekttraeger/project-sponsor-bavaria/bavarian-technology-promotion-program-plus-baytp/ |
| **Confidence** | MEDIUM — need to clarify overlap with BayTOU |
| **Last Verified** | 2026-03-24 |

**Fit Assessment:**
- Strategic fit: 7/10 — Covers R&D for Data Forge, but targeted more at established SMEs than startups
- Effort to apply: MEDIUM-HIGH
- Expected outcome: POSSIBLE — Good backup if BayTOU is blocked by Nebenerwerb issue
- Stacking: Both BayTOU and BayTP+ are administered by Bayern Innovativ — likely cannot apply to both for same project

**Note:** BayTP+ is the backup plan if BayTOU doesn't work (e.g., due to Nebenerwerb conflict). BayTP+ doesn't appear to have the "majority of working hours" requirement that BayTOU has.

---

## ⚠️ CRITICAL: Nebenerwerb Registration Issue

The Gewerbe-Anmeldung (14.08.2025) registers ML Upskill Agents UG as **Nebenerwerb** (side business). This creates a documented conflict with programs that require the founder to devote their primary working time to the startup:

| Program | Nebenerwerb Impact |
|---------|-------------------|
| **BayTOU** | ⚠️ DIRECT CONFLICT — Requires "majority of working hours" to startup |
| **Digitalbonus** | ✅ No Haupterwerb requirement found |
| **Start? Zuschuss!** | ⚠️ UNCLEAR — Competitive pitch; Nebenerwerb weakens narrative |
| **Innovationsgutscheine** | ✅ No Haupterwerb requirement found |
| **BayTP+** | ✅ No Haupterwerb requirement found |

**Resolution Options:**
1. Reclassify Gewerbe from Nebenerwerb → Haupterwerb at Gewerbeamt Vilseck (Gewerbeum- or -abmeldung)
2. This is typically a simple administrative change (Gewerbeummeldung) — but check implications for Krankenkasse/social insurance
3. Must be done BEFORE submitting BayTOU application
4. The PhD at FAU can still coexist with Haupterwerb — many founders are also students

---

## ❌ Eliminated Programs

### AI NATION GRANT — ELIMINATED 2026-03-24

**Reason:** Two structural disqualifiers:
1. Requires minimum 2 committed founders (solo founder ineligible)
2. 2026 application window (Jan 2 – Feb 1) already closed

### EXIST-Gründerstipendium — ELIMINATED 2026-03-24

**Reason:** The UG legal form (Kapitalgesellschaft) is a hard disqualifier. The directive explicitly prohibits funding already-founded Kapitalgesellschaften (GmbH, UG, etc.), regardless of revenue or activity status. Note: a mere Gewerbeanmeldung (sole proprietorship) would NOT be automatically disqualifying if the project is pre-revenue/not yet operative — but a UG is.

### HTGF (High-Tech Gründerfonds) — NOT APPLICABLE (Mistral research, vetted 2026-03-24)

**Reason:** Mistral listed this as a grant program. **It is NOT a grant — it is venture capital.** HTGF invests €800K+ for ~15% equity stake. This is fundamentally misaligned with a solo-founder micro-SaaS/digital-nomad business model. VC expects rapid scaling and eventual exit (acquisition or IPO). Additional concerns: solo founder with Nebenerwerb registration signals low commitment level for VC; Stammkapital of €1 is insufficient for VC expectations; founders must provide 5–10% co-investment. Only relevant if you pivot to a high-growth VC-backed strategy.

### GRW (Gemeinschaftsaufgabe Regionale Wirtschaftsstruktur) — LOW FIT (Mistral research, vetted 2026-03-24)

**Reason:** GRW funds regional economic development through capital investment and job creation. Vilseck (Landkreis Amberg-Sulzbach) may be in a GRW C-Fördergebiet, but the program targets manufacturing/industrial investments that create regional employment — not solo software companies. Funding rate up to 30% for small enterprises in C-areas. Could become relevant if you hire employees and invest in physical infrastructure, but not in current form. Would need to verify Vilseck's specific Fördergebiet status on the [interactive GRW map](https://www.deutsche-foerdermittelberatung.de/grw-foerderung/).

### BayVFP (Bayerisches Verbundforschungsprogramm) — SAME BARRIER AS BMBF (Mistral research, vetted 2026-03-24)

**Reason:** Requires consortium of ≥2 partners including ≥1 company. Same barrier as BMBF AI-KMU funding. FAU could be partner, but duplicates the BMBF application effort. Guidelines expired Dec 2025; new 2026 guidelines pending. Focus areas: Materials, Life Science, Digitalization, Mobility. If pursuing a consortium approach, BMBF is the better target (federal funding, larger amounts, clearer AI focus).

### EIC Accelerator — MISALIGNED (Mistral research, vetted 2026-03-24)

**Reason:** Up to €2.5M grant + €10M equity investment. Technically eligible as an EU-registered SME, but: extremely competitive (~5% acceptance rate), requires demonstrating "non-bankability" and high-impact market disruption, multi-step application process (short proposal → full proposal → interview → jury), equity component means giving up ownership, designed for companies seeking to scale across European markets. Effort-to-probability ratio is terrible for a solo founder. Only relevant if you pivot Data Forge into a venture-scale platform play.

---

## Stacking Strategy (Updated)

| Combination | Total Potential | Overlap Risk |
|------------|-----------------|--------------|
| Digitalbonus (both tracks) | €37,500 | NONE — separate Förderbereiche |
| Digitalbonus + Innovationsgutscheine | €75,500 | LOW — check expense overlap with Bayern Innovativ |
| Digitalbonus + BayTOU | €105,000 | MEDIUM — ensure distinct project scopes |
| Digitalbonus + BayTOU + Start?Zuschuss! | €141,000 | LOW — expense categories naturally separate |
| Digitalbonus + BayTOU + Innovationsgutscheine + Start?Zuschuss! | €179,000 | MEDIUM — verify stacking |
| All above + BMBF AI | €279,000 | Requires consortium; verify stacking rules |

**Key principle:** Each grant must fund DIFFERENT expenses. Never claim the same
invoice against two programs. Keep separate project scopes and budgets.

---

## Change Log

| Date | Change | Source |
|------|--------|--------|
| 2026-03-24 | Initial tracker created from Data Factory research + existing GRANT-APPLICATION-PLAN | Krankenkasse CTGAN thread + beelink-bonus existing docs |
| 2026-03-24 | Major update: eliminated AI NATION (2-founder req) + EXIST (company already registered); added KfW StartGeld, BMBF AI-KMU, Mikromezzaninfonds; confirmed ELSTER active; flagged Digitalbonus April 1 opening date; updated dashboard | Eligibility research session |
| 2026-03-24 | CORRECTION: Company founded Aug 2025 (not 2024). Start?Zuschuss! upgraded from borderline → confirmed eligible. EXIST remains eliminated (structural: company must not exist at application time). Realistic total raised to €109.5K–€141K | User correction + EXIST FAQ verification |
| 2026-03-24 | Vetted Mistral research output: Added Innovationsgutscheine (up to €38K, strong fit), BayTP+ (BayTOU backup), LfA GuW (loan). Eliminated HTGF (VC, not grant), GRW (industrial focus), EIC Accelerator (misaligned), BayVFP (same consortium barrier as BMBF). CRITICAL: Flagged Nebenerwerb registration conflict with BayTOU. Exact company dates from Handelsregisterauszug: Gesellschaftsvertrag 25.07.2025, HRB entry 11.08.2025, Gewerbe start 14.08.2025. | Mistral vetting + company reference PDF |
| 2026-03-24 | MAJOR REVISION: Digitalbonus scope significantly reduced. Program funds businesses ADOPTING tech, not BUILDING tech products. Two exclusions: (1) Eigenleistungen not eligible, must use external providers; (2) Products for paid use in other companies excluded. Track 2.2 (IT-Sicherheit, €7.5K) still viable. Track 2.1 must be reframed as internal operations. Realistic Digitalbonus total revised from €37.5K to €7.5K–€15K. GRANT-APPLICATION-PLAN.md needs major revision. | User flag + Vollzugshinweise/FAQ research |
