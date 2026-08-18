# Line C — Upskill News: Expansion from IECs to Schools

> **Review status:** reviewed 2026-08-17. Conclusion (not-yet, with a falsifiable trigger)
> upheld; the K-12 expansion is on the kill list in [`README.md`](README.md). Finishing the
> IEC motion ranks #4. Two overstatements flagged in [`REVIEW-FINDINGS.md`](REVIEW-FINDINGS.md):
> the 'no vendor generates per-student content' claim, and GDPR Art. 8's scope.

**Assessment date: 17 August 2026.** Prepared against a verified research dossier; every refuted or corrected claim from verification has been dropped or restated, and unverifiable figures are marked inline.

---

## 1. Verdict

**No-go on US K-12 schools, and not-yet on any second segment at all.** The school version fails on architecture before it fails on economics: Upskill News's safety model is a named human who approves every edition before it ships, which is tractable at an independent educational consultant with three to fifteen client families and collapses at a high school with four hundred seniors and nobody whose job it is to sign off. Remove the reviewer and the product becomes a machine that confidently states wrong application deadlines to families, attributed to the school. That is not a scaling problem to be engineered around; it is a different product with the differentiator deleted. The commercial case reinforces it — the delivery channel into families is already owned and consolidating, the per-student college-guidance workflow is already owned, and the sale takes six to eighteen months through procurement — but the architectural point would stand even if the market were wide open.

The separate and equally binding fact is that Upskill News has never had a paying customer in the easier segment it was built for. Adding a harder segment with a longer sales cycle and a per-district legal treadmill, before one IEC has paid one invoice for one delivered edition, is expansion as a substitute for validation. Finish the IEC motion. If a second segment is wanted after that, take association or membership briefings in English-speaking markets where per-recipient personalisation is already a paid product and where he already has an installed base — not schools.

Runner-up, briefly: fee-paying international schools in Europe under a data-sovereignty pitch. It is the only school-shaped variant where the local-inference story is an asset rather than a liability, and it sells to a head of school rather than a procurement committee. It is still a three-to-six-month sale with a DPIA attached, and no European price point for it could be verified, so it is a runner-up on principle, not a plan.

---

## 2. The incumbent landscape

The precise answer to the question: **no vendor in this category generates per-student narrative content.** The category is broadcast messaging plus, at the leading edge, per-student *data-merge* over structured internal records. ParentSquare's Auto Notices and Attendance Plus pull attendance, tardies and lunch or library balances from the SIS and send per-student notices pre-filled with that data, with students auto-assigned to intervention tiers. That is mail-merge over fields the district already holds — no external research, no verification, no narrative composition.

One correction to the usual framing: the incumbent has *not* abstained from family-facing AI. ParentSquare Intelligence, launched 4 March 2026, includes an AI Assistant that answers common family questions and "conversation starters" generated from school post content and delivered to families, alongside staff-facing analytics and drafting. Its stated position is that it does not use PII to train models and works from de-identified data. That is a training-data commitment, not a refusal to generate family-facing content. The gap between what ParentSquare ships today and per-student generated editions is one product iteration, held open by district privacy posture rather than by capability.

| Player | Positioning | Public pricing | Ownership / status |
|---|---|---|---|
| **ParentSquare** | Category leader. Mass notification, two-way messaging, translation, per-student SIS data-merge (Auto Notices, Attendance Plus), plus ParentSquare Intelligence AI layer (Mar 2026) | None published. FAQ states district-wide annual fee based on enrolment, quote only | Private. Acquired Remind (closed Nov 2023), Gabbart Communications, Signal Kit |
| **Remind** | Teacher-to-family texting; was in >80% of US public schools and used by 60% of US teachers | n/a | ParentSquare. Remind Hub does not renew beyond 2026-27 — districts are migrating now |
| **SchoolStatus / Smore** | Newsletter creation (Smore) plus attendance and family engagement | Not published | SchoolStatus. Acquired Smore (Dec 2022; ~1M educators, 10,000 schools), SchoolNow (Feb 2024), TeachBoost. Ownership/funding details [unverified] |
| **Bloomz** | Challenger. Explicitly price-led: "20-40% less than competitors", "we beat any competitor quote by 10%" | No absolute or per-student figure published | Independent |
| **ClassDojo** | Classroom communication; districts tier | **Free for schools, teachers and districts.** Monetised via optional family subscriptions | Independent. Penetration figures often quoted are not on the vendor's own district page [unverified] |
| **TalkingPoints** | Two-way family messaging with translation into 145 languages | Free to individual teachers | Nonprofit |
| **Finalsite** | Websites plus mass notification for K-12 | Not published | Acquired Anthology's entire Blackboard K-12 division (Web Community Manager, Connect, Reach, Mass Notifications) Sept 2022. Anthology filed Chapter 11 Oct 2025, re-emerged as Blackboard Mar 2026 with no K-12 comms business |
| **Naviance** | Per-student college and career readiness workflow — the incumbent in the adjacent budget line | Not published. Vendor page cites 8M students supported and 25M+ college applications submitted annually | PowerSchool |
| **Scoir** | Naviance challenger, same workflow category | **$4.80/student/yr (grades 9-12), $2.40 (6-8), plus a one-time $250 setup and training fee** | Independent |
| **Xello** | Same category | Free to Florida districts under a state contract | Independent |
| **The Parent Institute** | Prewritten parent newsletters, licensed to schools | **$399/yr per building, $669 small district, $929 medium, $1,239 large (>25,000 students)** — nine issues Sept-May. Each additional language or age level is a separate line item (+$179 building, +$209 small, +$329 medium, +$439 large) | Independent |
| **CollegeVine** | Formerly free AI college advising for students; as of Aug 2026 positions itself as "the AI operating system for universities" — an institutional B2B product | /pricing returns 404 | Independent. Earlier free-student-advising claims are stale and should not be relied on |

Two structural notes on this table. First, **the per-student price anchor everyone cites is not actually published by the family-communications vendors.** ParentSquare and Bloomz both quote-gate. The only publicly published per-student rate in the vicinity is Scoir's $2.40–$4.80, and that is the adjacent college-readiness category, not family comms. Quote-gating combined with a published offer to beat any competitor quote by 10% is itself evidence of margin compression — arguably stronger evidence than a published number would be — but the "$2 to $5 per student" figure that circulates should not be repeated as sourced fact.

Second, **2026-27 is the forced-migration year.** Every district still on Remind is being courted right now, with a hard sunset, by a vendor that already owns the SIS integration, the family contact database and the delivery channel. A solo foreign vendor entering this moment competes for procurement attention against a deadline he cannot influence, at the exact point districts are locking multi-year contracts.

---

## 3. The white-space analysis

The white space is real and narrow: **generated, externally-researched, per-recipient narrative content, delivered to families, with per-fact verification.** Nobody ships it into US K-12. The honest question is why.

Three explanations, and the evidence points at the third.

*It has not been thought of.* Implausible. Education raised roughly $4.09bn in 2025 with about 31% of that going to AI, and the funded AI-education companies cluster in tutoring, teacher tools, exam prep and coaching. Family communications attracted none of it. Meanwhile the nearest analog in any adjacent market — rasa.io, which sends a per-subscriber AI-personalised newsletter to association members — exists and has customers. Investors and founders looked at both categories; one drew a product, the other did not.

*It is technically hard.* Partly, but the hard part is not generation. It is the verification treadmill. College Scorecard carries no application deadlines, no essay prompts and no test policies; those live on several hundred individual institution sites and change every admissions cycle. Keeping them true is a scraping and reconciliation burden that scales with the size of the college universe, not with customer count — which makes the differentiator the most expensive part of the product to maintain, and makes it worse, not better, at a 15-25 minute daily budget.

*Schools do not buy it.* This is the one supported by evidence. Schools already buy newsletter content, and the price is known: The Parent Institute sells prewritten, zero-personalisation newsletters at $399–$1,239 per year, nine issues, with an upcharge per additional language or age level. That is the ceiling a school has demonstrated it will pay for newsletter content. Separately, schools already buy per-student college guidance, and that budget is spent — on Naviance or Scoir at $2.40–$4.80 per student, bundled with the college list, the Common App integration and the counsellor's daily workflow. Upskill News would arrive as an add-on to an add-on, with no data of its own, into a budget that is allocated.

The demand narrative — counsellors are overwhelmed, so schools will pay to personalise for each senior — is also weaker than it reads. ASCA reports the national student-to-counsellor ratio at 372:1 for 2024-25, improving. Among the 35 states that report high-school data separately the range is 195:1–224:1, but that is a self-selected subset and not a national high-school figure; on the all-grades national measure only four states met ASCA's 250:1 recommendation. The pain is real and unevenly distributed. It is also not the pain a communications budget pays for, and it is being addressed by hiring counsellors rather than by buying content.

The one place the white space is genuinely defensible is where a **named, paid, accountable human reviews each recipient's edition** — because that is what converts generated content from a liability into a service. That condition is satisfied by an IEC, by an IEC practice reselling under its own brand, and by an association with a communications lead. It is not satisfied by a school.

---

## 4. The buyer, the budget, and the sales cycle

**There is no single school buyer for this product.** It straddles two budgets owned by different people. Family communications sits with the superintendent, communications director or technology director, anchored to a district-wide platform contract. Per-student college guidance sits with the counselling department, anchored to Naviance or Scoir. A personalised per-senior briefing is a communications artefact funded from a counselling rationale, which is the classic shape of a purchase that nobody owns and therefore nobody makes.

**Cycle.** Six to eighteen months from first conversation to signature is the working assumption for K-12 procurement, with a formal RFP adding three to nine months on top. Districts typically require an RFP above roughly $50K; winning vendors are usually in the conversation six to twelve months before the solicitation is published; missing a budget window costs a full year. Faster paths exist — cooperative purchasing vehicles, sole-source — but they require pre-existing contract vehicles a new foreign vendor does not have. These figures are industry guidance rather than primary procurement data and should be treated as directional.

**Deal size against that cycle.** The comparables cap it: $399–$1,239 per school per year for newsletter content, or an add-on line inside a platform contract whose vendors will not publish a number. Even at the generous end, one school sale is a low-thousands annual figure earned across six to eighteen months of pursuit.

**Against the IEC motion, the comparison is not close.**

| | School | IEC |
|---|---|---|
| Buyer | Committee across two budget owners | One person, self-employed |
| First contact to cash | 6-18 months | Days |
| Procurement | RFP above ~$50K, budget windows | None |
| Legal | SDPC NDPA v2 plus state addenda, per district | Ordinary terms of service |
| Human reviewer per recipient | None exists | The consultant, by definition |
| Validated willingness to pay | $399-$1,239/school/yr for unpersonalised content | IECs buy monthly practice SaaS and buy newsletter content |
| Annual value | Low thousands | Tens of dollars to low hundreds per month |

Can a solo founder at 15-25 minutes a day run the school motion? No. Not "with difficulty" — the unit does not fit. A single district pursuit consumes more founder attention across a year than the entire IEC motion, produces revenue in the same order of magnitude as three or four IEC subscriptions, and adds a permanent, non-delegable legal obligation that persists after the sale.

One important correction to the IEC side of that table before it is used as a pricing model. The College Advisor sells IECs a white-labelled ten-issue newsletter at $475/year with the consultant's masthead and logo — but that is a **prospecting** tool, mailed to an inquiry list and past families to stay top-of-mind. It is not a per-client deliverable, and per-student personalisation is architecturally incompatible with it: you cannot mass-mail a personalised-per-student edition to a prospect list. So $475/year proves that IECs pay for newsletter content they can brand, and it does not price what Upskill News sells. The real question — never yet tested — is whether an IEC will pay anything for a deliverable aimed at families who have *already* paid $2,000-$10,000, or whether they treat it as a cost of service to be absorbed.

---

## 5. The compliance delta

### United States K-12 (public districts)

Selling into US districts means signing the Student Data Privacy Consortium National Data Privacy Agreement v2 (April 2024), which districts expect back "with minimal redlines". The SDPC registry holds over 130,000 signed DPAs across more than 12,000 districts and roughly 6,700 vendors — the agreement exists to standardise the paperwork, not to eliminate it. On top of the base agreement sit state statutes with their own vendor obligations:

- **New York Education Law §2-d** requires, in every contract: a data security and privacy plan describing how state, federal and local requirements will be implemented over the life of the contract; a signed copy of the Parents' Bill of Rights for Data Privacy and Security; and confirmation that contractor personnel with data access have received or will receive training on the applicable confidentiality law before access. No stated exception.
- **California SOPIPA** imposes categorical prohibitions — targeted advertising and student profiling — that parental consent cannot waive.
- Voluntary certifications (iKeepSafe FERPA/COPPA/California Student Privacy) are commonly requested; pricing is not published [unverified]. SOC 2 is commonly requested at district scale.

**Quantifying it honestly:** the work is not a one-time project, it is a per-customer legal artefact plus a recurring obligation set. Each new district is at minimum one agreement to read and countersign, one or more state exhibits, and a documented security plan and staff-training attestation to keep current. There is no automation path, no delegation path at this company size, and no economy of scale beyond the shared NDPA base. Any hour estimate would be invented; the structural point is sufficient. This scales linearly with customers and cannot be run at 15-25 minutes a day from Bavaria.

Two cross-border frictions compound it: US districts commonly write US data residency into their DPAs, which is in direct conflict with the only genuine differentiator on offer ("inference stays in Bavaria"); and a German UG selling to US districts faces W-8BEN-E paperwork, US-law-governed contracts, and typical E&O and cyber insurance requirements.

### International schools in Europe (GDPR)

Different regime, lighter procurement, real analytical work. The school is controller and the UG is processor, so the closing artefacts are an Article 28 data processing agreement, an Article 32 technical and organisational measures description, and the UG's own Article 30 record of processing (the under-250-employee exemption falls away where processing is not occasional, which a continuously running service is not). Processing children's personal data at scale is a plausible Article 35 DPIA trigger, and Article 8 conditions attach to children's data. Practically, a DPIA is a one-time template plus a per-client review — genuinely reusable across clients, unlike the US per-district treadmill.

The German public-school channel is close to shut and should not be attempted: the Datenschutzkonferenz concluded in November 2022 that Microsoft 365 was not demonstrably GDPR-compliant, several state authorities advised against school use, and school data protection remains a state-by-state matter with the school as controller. Fee-paying private and international schools are the addressable subset. The market is large in absolute terms — approaching 15,000 international schools worldwide with fee income surpassing US$67 billion and nearly 7.5 million students, per ISC Research figures as reported secondarily — but no European per-school price point for this product could be verified.

### DoDEA (now the Department of War Education Activity)

**DoDEA is not a FERPA institution.** Its student records regime runs through the Privacy Act via SORN "DoDEA 26 — Department of Defense Education Activity Educational Records" (established 29 April 2011, 76 FR 24001), authorised under 10 U.S.C. 113, 10 U.S.C. 2164, 20 U.S.C. 921-932, 29 U.S.C. 794 and DoD Directive 1342.20. No FERPA, no Department of Education authority anywhere in it.

That correction does not make the compliance load lighter. It makes it different and, in one respect, sharper:

- **FAR Subpart 24.1.** Where a contract provides for the *operation* of a Privacy Act system of records, the contractor and its employees are considered employees of the agency for purposes of the Act's **criminal** penalties, and clauses 52.224-1 and 52.224-2 are mandatory. (Design and development trigger the mandatory clauses but not the criminal-penalty deeming — a narrower exposure than sometimes stated, and still a bright line: never operate a system that retrieves records by student identifier.)
- **Section 508.** ICT bought by a federal agency must conform even at micro-purchase level; the pre-2003 micro-purchase exception is gone, and DoDEA requires Section 508 micro-purchase training for its own purchase-card holders. A learner-facing or family-facing portal is ICT and needs conformance evidence. A person-delivered service with accessible documents is not.
- **The company is structurally ineligible for the relevant contract band.** FAR 19.502-2 requires acquisitions above the micro-purchase threshold and not over the simplified acquisition threshold ($15,000 to $350,000 as of 1 October 2025) to be set aside for small business absent a rule-of-two determination, and 13 CFR 121.105 requires a small business concern to have a place of business located in the United States. A German UG with no US place of business cannot qualify. This closes the band where a product like this would be bought.
- **FAR 3.601** bars a contracting officer from knowingly awarding to a business owned or substantially owned or controlled by one or more Government employees; the FAR 3.602 exception requires a most compelling reason at agency-head level. Today that is not triggered — his spouse's employment raises a 18 U.S.C. §208 recusal question for *her*, not an award bar for the company. It would be triggered outright if he became a DoDEA employee.
- **Market size.** DoDEA operates roughly 161 schools with approximately 66,000 students. Its outside professional-learning purchasing is centralised and small, and the great majority of small awards are delivery orders placed against pre-existing indefinite-delivery vehicles that a new entrant cannot bid. The genuinely contestable new-entrant slice is on the order of ten thousand dollars a year across the entire global agency.

DoDEA looks like the nearest school customer and is in fact the worst entry point available.

---

## 6. The counter-case, argued properly

The counter-case deserves to be argued rather than dismissed, because the pattern-matching argument against expansion is weaker than it is usually presented.

**The case for finishing the narrow segment first.** Startup Genome's analysis of over 3,200 self-reporting high-growth startups found that roughly 70% scaled prematurely on at least one dimension, and that 93% of prematurely-scaling companies never crossed $100K per month in revenue. Customer segment is one of the dimensions studied. The mechanism is what matters more than the statistic: expanding the target segment before the first has converted means you never learn whether non-purchase was caused by the segment or by the product, because you have introduced a second uncontrolled variable while the first is still unresolved. That is a diagnostic argument, not a moral one.

Caveats that must be stated: the study is from September 2011, was never peer-reviewed, relies on self-reporting, and comes from an organisation whose methodology has been publicly criticised. The frequently-quoted "74% of failures are attributable to premature scaling" figure is not supported by the source. It should be used as a description of a mechanism, not as an actuarial probability applied to a one-person company in 2026.

**The genuine case for expanding anyway.** Three arguments have merit. First, a pre-revenue product has no sunk positioning to protect — the cost of switching segments now is lower than it will ever be again. Second, if the reason no IEC has bought is segment-specific (IECs are sole practitioners with no budget line for tooling, or the deliverable duplicates work they already do), then persisting inside that segment is sunk-cost behaviour and the correct move is to test a different buyer. Third, some products only have a coherent economic unit at institutional scale, and a per-recipient personalisation engine is plausibly one of them — 400 seniors at one school is a better fit for a fixed generation cost than 12 clients at one consultancy.

**Why the counter-case does not carry here.** The third argument is exactly the one the architecture refuses. Institutional scale is where the human reviewer disappears, and the reviewer is not a feature, it is the thing that makes generated content sellable at all in a domain where a wrong deadline is unrecoverable. The second argument is untestable in its current form because the IEC motion has never actually been run: no live Supabase project, no provisioned Clerk instance, no Stripe, no real send, no edition ever generated end-to-end against live data and hand-checked. You cannot conclude that a segment rejected a product that was never offered to it. And the first argument cuts both ways — low switching cost also means the cost of *finishing* the IEC test is low, and it is the cheaper experiment by a wide margin.

There is also a specific, unglamorous risk in expanding before the base is proven: **the Beelink is not an economic advantage at this scale, and the plan quietly assumes it is.** At the volumes contemplated — say twenty IECs with fifteen clients each, two editions a month, around 600 editions — commercial API inference costs single-digit to low-tens of dollars per month. Zero marginal inference cost saves nothing that matters against a business of this size, and it introduces a real liability: one consumer mini-PC on residential power and internet, no redundancy, no failover, no documented restore path, and an operator with 15-25 minutes a day, as the production backend for a paid subscription with contractual delivery dates. If local inference is meant to be the moat, none of these newsletter variants expresses it.

---

## 7. Easier adjacent variants, ranked by time to first paying customer

Ranked on time-to-first-euro, with the reviewer test applied to each.

**1. White-label tier sold to an existing IEC practice (weeks).** Strictly a pricing and branding variant of the base motion rather than a new segment, and it should be treated as part of finishing the IEC test, not as an alternative to it. The mechanism is that the consultant already charges families $2,000-$10,000 per engagement, so a branded briefing is bought out of a fee the family has already paid rather than from a new budget. The consultant approves each edition, so the reviewer requirement is satisfied by construction. Price to the practice on active-student tiers. No new compliance surface. IECA reports more than 2,800 members, which is the reachable universe alongside HECA.

**2. Professional association or membership-body briefings, sold in English into markets he already serves (two to four months).** This is the strongest genuine second segment, for one reason: per-recipient personalisation is already a *paid product* here. rasa.io sells associations a newsletter assembled per member around that member's interests, priced by organisation revenue with no per-contact fee. That validates the shape. Two adjustments to the version in the research. First, do not start with German Verbände: the sale requires German-language B2B selling, a German AVV and German landing-page copy, against a documented constraint that the owner's German is functional but not fluent — that is friction on top of an unproven product. Second, and more usefully, he already has an installed base in UK and Irish nursing and academic education through WritingPAD, ProPrecept and FacultyWizard. Associations and member bodies adjacent to those users are reachable in English, with existing credibility and an existing acquisition channel, which is the standard answer to "the founder has no audience in this niche". rasa.io publishes no dollar figures — its revenue bands run from under $5M to over $75M in organisational revenue — so any price point here must be discovered by asking, not assumed.

**3. University department (three to nine months).** A single department — graduate admissions, continuing education, an international office — is a lighter buyer than a district but still an institutional one, with procurement, accessibility review and a data protection assessment. No evidence was found either way on willingness to pay for this specific product. The reviewer requirement is satisfiable only if a named staff member owns approval, which is exactly the question to ask in the first conversation. Ranked third on the basis that it is plausible and unevidenced.

**4. Homeschool co-op or direct-to-family (four to nine months, and not recommended).** The demand base is real: NCES reports about 5.2% of US children aged 5-17 receiving academic instruction at home in 2022-23, up from 3.7% in 2018-19, with Household Pulse indicating roughly 5.9% in 2023-24, and these families already pay out of pocket for curriculum with no procurement in the way. But it fails the reviewer test in the same way schools do, at smaller N, while adding consumer payments, self-serve onboarding, minors' data, and structurally terminal churn — the need ends at graduation. It also requires Stripe, which is not integrated.

**5. Military-community PCS or transition briefing — do not build.** Genuinely differentiated on lived experience and locally distributable, and it has no school gatekeeper, which is why it keeps resurfacing. It fails on monetisation, not on appeal. DoD's Plan My Move and Military OneSource are free and authoritative, and AHRN's PCS planner is free and ad-funded, so families will not pay a subscription for relocation information the government supplies. The money in military relocation flows from realtors, lenders, movers, storage companies and insurers buying geographically-targeted attention — which makes this a sponsorship-funded media business with a twelve-to-twenty-four-month audience-building cost curve, not a software business. It also puts a spouse who is a DoD employee near a business selling sponsorship into the community she works in; that is a Joint Ethics Regulation question to be answered before, not after. Kill it.

**Schools, for completeness, rank below all of these.** If the segment is ever revisited it should be fee-paying international and private schools in Europe under a "no US cloud, inference in Bavaria, Article 28 processor agreement, no third-country transfer" pitch, sold to a head of school. Never US public districts.

---

## 8. If the answer is not-yet, what changes it

The verdict is split, so the triggers are split.

**US K-12 public districts: no-go, not not-yet.** No plausible trigger reverses this at solo scale. The blockers are structural — the reviewer architecture, the per-district legal treadmill, the six-to-eighteen-month cycle, and a deal size in the hundreds to low thousands. The only condition that would change the analysis is one that describes a different company: a US-based entity with staff, a signed cooperative purchasing vehicle, SOC 2, and a US reseller absorbing DPA administration. That is not an incremental trigger, it is a different business.

**A second segment of any kind: not-yet, with a specific and falsifiable trigger.**

> Three IEC customers, each having paid a real invoice for a real delivered edition, retained through one full admissions cycle (roughly August to January), with at least one renewal.

Three, not one, because one paying customer who is also an acquaintance is not a market. Through a full cycle, because US college counselling demand is concentrated August to January and dead from February to July — a monthly subscription against a seasonal workload invites a spring cancellation, and any ARR figure that assumes twelve-month retention is unevidenced. A renewal, because renewal is the only observation that distinguishes a product from a favour.

A second, independent gate applies to whatever segment is chosen after that trigger fires: **a named, paid, accountable human must review each recipient's edition before it ships.** Treat that as an architectural invariant, not a feature. It rules in IECs, IEC practices and associations with a communications lead; it rules out schools and direct-to-consumer. Applying that one rule mechanically resolves most future segment questions without further research.

---

## 9. What to verify before acting

1. **Has any IEC ever paid, or agreed in writing to pay?** Everything above turns on this and no record of it exists. Method: check invoicing and correspondence. If the answer is no, the next action is one paid pilot, not further segment analysis.
2. **Can the pipeline produce a correct edition?** The pipeline defaults to mocks and fixtures and has never run against live College Scorecard data and a live Ollama model in production. Method: generate one real edition end-to-end for one real student profile, then hand-check every fact against the source institution's own site. Count the errors. That number is the product.
3. **Cost the verification treadmill, not just the generation.** Method: take twenty target institutions, record where deadlines, essay prompts and test policies actually live, and time how long it takes to re-verify all twenty. Multiply by the college universe an IEC's clients actually apply to, and by cycles per year. If the answer is more than a few hours a month, the differentiator is unaffordable at 15-25 minutes a day and the product needs redesigning around a narrower factual scope.
4. **Buy or request one issue of The Parent Institute's newsletter and one issue of The College Advisor's IEC newsletter.** Method: direct purchase or sample request, under $500 total. This is the cheapest competitive intelligence available and settles both the content-quality bar and — critically — whether The College Advisor's product is prospecting or client-facing, which determines whether $475/year is a valid price anchor at all.
5. **Confirm the IECA and HECA vendor channel is open to a foreign micro-vendor, and at what cost.** Method: one email to IECA asking for vendor listing and conference exhibitor terms and eligibility. This is the primary acquisition channel and its accessibility has not been established.
6. **Get one real quote from ParentSquare and one from Bloomz** for a 600-student school and a 5,000-student district. Method: request a quote as a prospective buyer. This settles the actual price anchor, which no public source provides, and it costs nothing.
7. **For the association variant: get one rasa.io quote for a mid-size English-language association.** Method: mystery-shop the quote-only pricing. It sizes the wedge and tests whether a sovereignty or local-hosting premium is even conceivable, which is currently an assumption with no evidence behind it.
8. **Price a redundancy plan before selling any subscription.** Method: cost a small VPS front-end plus a documented restore path, and decide explicitly whether the Beelink is the serving path or a best-effort batch backend. Do not sign a delivery commitment the hardware and the operator's time budget cannot honour.
9. **Confirm the outside-employment and ethics position on anything touching the military community**, before any sponsorship or community-facing sale is attempted, given a spouse employed by DoDEA. Method: agency ethics counsel, in writing. Not a web search.

---

## 10. Sources

- [ParentSquare — Mass Notifications](https://www.parentsquare.com/platform/mass-notifications/)
- [ParentSquare — Auto Notices](https://www.parentsquare.com/mass-communications/auto-notices/)
- [ParentSquare — Attendance and lunch balances](https://www.parentsquare.com/mass-communications/attendance-lunch-balances/)
- [ParentSquare Intelligence](https://www.parentsquare.com/platform/parentsquare-intelligence/)
- [ParentSquare — FAQs (pricing posture)](https://www.parentsquare.com/resources/faqs/)
- [eSchool News — ParentSquare acquires Remind](https://www.eschoolnews.com/newsline/2023/12/08/parentsquare-acquires-remind-expanding-options-for-school-home-engagement/)
- [Bloomz — pricing](https://www.bloomz.com/bloomz-pricing)
- [ClassDojo for Districts](https://www.classdojo.com/districts/)
- [TalkingPoints](https://talkingpts.org/)
- [SchoolStatus acquires Smore](https://www.schoolstatus.com/blog/schoolstatus-acquires-smore)
- [Finalsite acquires the Blackboard K-12 division of Anthology](https://www.blackboard.com/news/finalsite-acquires-the-blackboard-k-12-division-of-anthology)
- [Campus Technology — Anthology rebrands as Blackboard](https://campustechnology.com/articles/2026/03/03/anthology-rebrands-as-blackboard-following-financial-restructuring.aspx)
- [PowerSchool — Naviance CCLR](https://www.powerschool.com/solutions/college-career-and-life-readiness/naviance-cclr/)
- [Scoir — high school pricing](https://www.scoir.com/high-schools/pricing)
- [The Parent Institute — Parents Make the Difference](https://parent-institute.com/products/parents-make-the-difference-newsletters)
- [The College Advisor — products for consultants](https://www.thecollegeadvisor.net/products-for-consultants)
- [CollegeVine](https://www.collegevine.com/)
- [IECA](https://www.iecaonline.com/)
- [rasa.io — pricing](https://rasa.io/pricing/)
- [ASCA — school counselor roles and ratios](https://www.schoolcounselor.org/about-school-counseling/school-counselor-roles-ratios)
- [SDPC — National Data Privacy Agreement](https://privacy.a4l.org/national-dpa/)
- [NY Education Law §2-d](https://codes.findlaw.com/ny/education-law/edn-sect-2-d/)
- [NYSED — Parents' Bill of Rights](https://www.nysed.gov/data-privacy-security/bill-rights-data-privacy-and-security-parents-bill-rights)
- [iKeepSafe certifications](https://ikeepsafe.org/certifications/)
- [SORN DoDEA 26 — Educational Records](https://pclt.defense.gov/DIRECTORATES/Privacy-and-Civil-Liberties-Directorate/Privacy/SORNsIndex/Article/4014257/dodea-26/)
- [DoDEA — 2025-26 school year enrolment](https://www.dodea.edu/news/press-releases/back-school-dodea-welcomes-students-worldwide-2025-26-school-year)
- [FAR Subpart 3.6 — Contracts with Government Employees](https://www.acquisition.gov/far/subpart-3.6)
- [FAR 19.502-2 — Total small business set-asides](https://www.acquisition.gov/far/19.502-2)
- [13 CFR 121.105 — What is a small business concern](https://www.law.cornell.edu/cfr/text/13/121.105)
- [FAR Subpart 24.1 — Protection of Individual Privacy](https://www.acquisition.gov/far/subpart-24.1)
- [Section508.gov — ICT micro-purchases](https://www.section508.gov/buy/understanding-ict-micro-purchases/)
- [EDRi — Microsoft Office 365 and German schools](https://edri.org/our-work/microsoft-office-365-banned-from-german-schools-over-privacy-concerns/)
- [ICEF Monitor — international schools five-year growth](https://monitor.icef.com/2025/05/international-schools-segment-registers-impressive-five-year-growth-numbers/)
- [Startup Genome — premature scaling](https://startupgenome.com/insights/premature-scaling-a-deep-dive)
- [CiviCIQ — selling to school districts](https://blogs.civiciq.com/2026/03/25/how-to-sell-to-school-districts-the-complete-b2g-guide-for-edtech-vendors-2026/)
