# Cross-Document Review Findings

> Hostile review of the five service-line documents in this folder, produced 2026-08-17 by the
> final stage of the research workflow that wrote them. The reviewer verified every codebase
> claim in the technical spec against `/home/user/upskill-news-app` and cross-checked the
> documents against each other.
>
> **This file is the audit trail. Where it contradicts a service-line document, it wins.**
> The most severe defects it found have been corrected inline in the source documents and are
> marked there as corrections. The rest stand as open findings.

---

Read all five, plus verified every codebase claim in the technical spec against `/home/user/upskill-news-app`. Report follows.

---

# 1. CONTRADICTIONS BETWEEN THE DOCUMENTS

These are the highest-value findings. Ordered by severity.

**1.1 — FAR 3.601: Line A says it bites today; Line B and MARKET-EVIDENCE say it does not.**

Line A §7: *"FAR 3.601 bars contracting officers from awarding to an entity substantially owned or controlled by Government employees... **This bites on any federal instrument** — RCO instructor contracts, Army CA vendor status, SKIES contracts."* And Line A §4 kills the SKIES/RCO row because it *"walks into FAR 3.601 territory given a DoDEA-employed spouse."*

Line B §2 states the opposite in bold: *"**FAR 3.601 does not bar your company.** The text prohibits the contracting officer, not the vendor... Your spouse's employment does not make her an owner or a controller of a UG whose shares you hold."* MARKET-EVIDENCE §3.3 agrees: *"**Today, with Ryan not a federal employee, FAR 3.601 does not bar the UG.**"*

Line A has deferred an entire product shape (organisational contracts — the one shape that *solves the enrolment problem it calls "the honest biggest risk"*) on a legal ground its own appendix refutes. This must be resolved before the ranking in Line A §4 means anything.

**1.2 — §2 SGB VI at 18.6%: Line A repeats a claim MARKET-EVIDENCE explicitly marks as refuted.**

Line A §7: *"§2 Satz 1 Nr. 1 SGB VI, which makes self-employed 'Lehrer und Erzieher' without an insured employee compulsorily insured... at 18.6% of income. **That is worse than the trade tax it avoids**, and it forfeits the liability shield."*

MARKET-EVIDENCE §6.3, under a heading meaning "do not repeat this": *"**The '18.6% is worse than 12%' comparison does not hold as stated.** Three defects: pension contributions are capped at the Beitragsbemessungsgrenze and purchase an entitlement rather than disappearing; the comparison omits the corporate stack (~30% at entity level, then ~26.4% Abgeltungsteuer on distribution, ≈48% combined on money reaching him personally)... **This needs a Steuerberater, not a heuristic.**"* It is repeated again in the §7.2 "Overstated" table.

MARKET-EVIDENCE §1 says *"the verifier wins without exception — refuted claims... are never propagated as fact elsewhere in this file **or in the service-line documents**."* Line A violates its own governing rule.

**1.3 — UMGC: Line B says "pick one"; Line A's 90-day plan does both.**

Line B §6: *"teaching AI for UMGC while separately selling a competing private AI course to the same garrison population is an outside-activity conflict UMGC would likely have views on. **Pick one.**"*

Line A §9 (Days 1–30) instructs: *"Send one email to UMGC Europe HR about the adjunct posting"* — while simultaneously running twelve prospect conversations to fill a private paid cohort from that same population. Line A never mentions the conflict. Two documents dated the same day, one telling him to choose, the other scheduling both in the same 30 days.

**1.4 — Section 508 and SKIES: Line A says no blocker; the classroom study and the tech spec say the opposite.**

Line A §4: *"SKIES sits under Child & Youth Services, not DoDEA, so it **carries none of the accreditation or Section 508 blockers**."*

Tech spec N-8: *"Any federal-agency deployment would require Section 508 conformance evidence."* `docs/CLASSROOM-BUILD-LAB.md` §(A): *"Section 508 conformance, normally evidenced by a VPAT, for **any ICT a federal agency deploys**."* CYS/SKIES is Army NAF — still a federal agency deploying ICT. Line B §7 states the rule generally and does not carve out SKIES. Line A is the outlier and is probably wrong; it also contradicts its own §7 prohibition on *"using FMWR facilities or Government property in support of the business."*

**1.5 — The Beelink: three documents say it monetises nothing; the fifth is 905 lines of engineering to monetise it.**

MARKET-EVIDENCE §7.5: *"**The Beelink.** Across four dimensions and roughly twenty proposed opportunities, **none uses the hardware for anything a laptop or a $20/month API could not do**... If the honest conclusion is that these audiences do not monetise the hardware, that is the headline."*

Line B §1: *"**Nothing in this line uses the Beelink.**"* Line A §6: *"**Where it does not fit: as the students' model backend**... Teaching them to build against a Qwen behind a portal in Vilseck hands them a stack they cannot reproduce at home... The classroom design study's portal architecture existed to solve a K-12 governance problem... **the constraint was never a feature.**"* Line C §6: *"the Beelink is not an economic advantage at this scale, and the plan quietly assumes it is."*

The TECHNICAL SPEC then opens: *"This is a single-tenant multi-cohort inference gateway with a teaching UI... **the shared substrate under every service line that involves other people using models: a paid live cohort**..."* Line A has already ruled that use out for the only paid cohort anyone recommended. The spec is a build plan for a thing four documents say has no buyer.

**1.6 — Guard models: the spec's minor-safety story contradicts the document it cites as authoritative.**

Tech spec §7 rests N-2 ("Minor-safe by configuration, not by hope") on *"A small guard model (Llama Guard-class, ~8B, Q4)."*

`docs/CLASSROOM-BUILD-LAB.md` §7, which the spec cites twice as a source: *"**Open guard models are weaker than people assume.** Recent benchmarking... reports recall as low as 0.455 for ShieldGemma 2B and **0.333 for Llama Guard 12B** — that is, the majority of unsafe content missed... **'I put a guard model in front of it' is a compliance prop, not a safety posture.**"* That document's prescribed mitigations are *"**Do not offer open-ended chat**"* and *"**Time-gate the endpoint**."* The spec ships open-ended chat (`tier: 'chat'`), has no time gating, and carries neither the recall figure nor the caveat.

**1.7 — AER 210-70 online courses: Line A says the ICAO regime captures the product; MARKET-EVIDENCE says online-only is exempt.**

MARKET-EVIDENCE §2.3: *"An online evening cohort delivered from private rental quarters requires German tax compliance, **not HBB approval**. The '3–5 month lead time before the first legal euro' does not apply to that product."*

Line A §7 presents §16–17 as governing the courses themselves: *"AER 210-70 Section IV, §16 and §17, governs 'online, virtual, hybrid, or blended courses' sold to the military community... approval comes in writing from the IMCOM-Europe ICAO."* MARKET-EVIDENCE §7.2 resolves this correctly (*"For online-only with no in-person clients, yes. For anything involving **solicitation on the installation**, the IMCOM-Europe ICAO regime applies"*) — but Line A never makes the solicitation/sale distinction, and therefore overstates the barrier to the one format that would fit a 15-25 min/day budget.

**1.8 — VHS rate, three different numbers.**

Line A §8: *"€20–45 per 45-minute Unterrichtseinheit, so a 20-UE course pays €400–900."* Line B §6: *"€20–40... roughly €400–800."* MARKET-EVIDENCE §6.11: *"€20–40 per UE (a competing figure of €15–45 also appears)."* Small, but it is the same recommendation in two documents with a 12% spread and no reason given.

**1.9 — Line A recommends VHS teaching and omits the §127 SGB IV cliff that Line B calls a four-month deadline.**

Line B §6: *"The §127 SGB IV transitional shield for Honorarlehrkräfte **expires 31 December 2026**; insurance and contribution liability begins 1 January 2027... **That is roughly four and a half months of runway, not sixteen.**"* Line A §8 recommends *"One Volkshochschule course... as a paid live test of the material"* with no mention of Herrenberg or §127 at all. Same action, one document flags a hard deadline four months out, the other is silent.

**1.10 — Five documents, five different top recommendations, none reconciled.**

Line A: run one paid in-person cohort. Line B: apply to UMGC. Line C: finish the IEC motion. MARKET-EVIDENCE: *"**Recommended path: launch ProPrecept Ireland and ProPrecept RSA**... That is the benchmark every option in this dossier should have been measured against and none was."* Tech spec: build a nine-evening portal. Three of the five explicitly nominate a runner-up that is another document's headline. Nobody wrote the arbitration.

---

# 2. CLAIMS THAT ARE WRONG, UNSUPPORTED, OR DANGEROUSLY OPTIMISTIC

**2.1 — Line A §8 recommends the exact conduct Line A §7 lists as prohibited.**

§7 prohibited list, verbatim: *"unsolicited in-person or telephone contact."* §8 channel 1: *"**Direct personal invitation.** He knows people... A named individual asked directly is the **highest-converting and most clearly lawful approach available**."* The prohibition attaches to solicitation on the installation, so the two can be reconciled — but §8 does not reconcile them, and the entire go-to-market is that one channel. Somebody reading §8 alone will approach DoD personnel on post. Fix or delete.

**2.2 — Line A §2: "Nobody local delivers hands-on applied-AI instruction in English."**

Contradicted three pages later in the same document (§3): UMGC Europe *"has posted an adjunct faculty vacancy in Artificial Intelligence at Grafenwöhr."* An institution actively hiring an AI instructor at that location is about to deliver exactly that, with SpouseWorks/TA/GI Bill funding attached, into the same room. The claimed white space is being filled by the entity Line B recommends he join.

**2.3 — Tech spec: "Total to a portal that can run a paid adult cohort or a supervised youth class: nine evenings."**

Nine evenings ≈ 18 hours to deliver: a role-model rename with test updates, an inference route, an extended Ollama adapter, a workspace UI, three quota windows, a bounded queue, a two-layer moderation stage, four RLS migrations with a posture test, a service-role roster writer, an operator console, and a WCAG 2.2 AA pass. `docs/CLASSROOM-BUILD-LAB.md` — cited by the spec as a source — budgets *"roughly **25–40 hours** for the portal, quotas, moderation, repos, exemplar project and consent pack — less if the `upskill-news` skeleton is reused aggressively."* The spec reuses the skeleton and still adds scope (RLS, operator console, a11y) while cutting the low end by 30%. At the documented 15–25 min/day this is 43–72 days of the entire budget, with zero revenue at the end.

**2.4 — Tech spec N-1 is not true on the cloud path.**

N-1: *"**Zero prompt-content retention.** No prompt or completion text is written to disk, to a database, to a log line, or to a third-party observability service, **on any code path** including error paths."* The routing ladder's step 3 ships the full prompt to Anthropic or an OpenAI-compatible host, which retain it under their own abuse-monitoring terms. `CLASSROOM-BUILD-LAB.md` §6 says so directly: *"The moment a request fails over to a cloud API, that vendor retains it under its own abuse terms."* N-1 is the requirement the spec says *"is the only claim that makes the 'your material does not leave the room' B2B pitch honest."* It needs an explicit carve-out, not a softer sentence in §9(B).

**2.5 — Line C's "no vendor in this category generates per-student narrative content" is presented as a durable finding and then refuted in the next paragraph.**

Line C §2 opens with *"The precise answer to the question: **no vendor in this category generates per-student narrative content**"* and then: *"the incumbent has not abstained from family-facing AI... an AI Assistant that answers common family questions and 'conversation starters' generated from school post content and **delivered to families**... The gap... is one product iteration." * The honest headline is the second sentence, not the first.

**2.6 — Line A §2: "roughly level with nobody."**

*"A resident with a German company, a local address and four children in the community starts ahead of any outside vendor, and roughly level with nobody."* This is the entire competitive claim and it is asserted, not evidenced. MARKET-EVIDENCE §7.5 records the opposite as a structural gap: *"**Nobody was identified who signs a cheque.**"* And Line A §2's own §"What the location does not give him" concedes *"PCS cycles of two to three years mean the audience fully replaces itself, so **every year is a cold start on relationships**."* A one-year-half-life relationship advantage is not a moat.

**2.7 — Line A §6's Beelink use cases do not survive the geography problem MARKET-EVIDENCE raises.**

Line A §6: *"the inhouse workshop for a German firm whose exercises run against their own contracts and personnel files — **the one thing a cloud-based competitor structurally cannot offer**."* MARKET-EVIDENCE §4.10: *"**The Beelink is in Vilseck; an inhouse workshop is at the client's office.** Either the client's confidential documents leave their network over a tunnel to his home hardware — which is exactly what the pitch promises does not happen — or he carries a 128GB mini-PC to every engagement."* Line A restates the pitch without answering the objection.

---

# 3. REVENUE ESTIMATES THAT DO NOT SURVIVE SCRUTINY

**3.1 — Line A's €8,000–12,000/yr steady state is pre-tax and pre-cost, and the document knows it.**

The chain: €4,000 gross → €3,361 net of VAT → less €300 room → *"Call it €3,000 net."* Then *"three cohorts a year... €8,000–12,000 net per year."* But "net" here means net of VAT only. Not subtracted: Gewerbesteuer + Körperschaftsteuer (Line A §7 itself says *"Gewerbesteuer applies from the first euro of profit with no €24,500 Freibetrag"*; MARKET-EVIDENCE §6.3 puts the entity stack at ~30% and ~48% on money reaching him personally), the €145–1,065/yr insurance Line A §9 mandates, the Steuerberater opinion Line A §7 mandates, the IT-Recht-Kanzlei opinion Line A §7 mandates (MARKET-EVIDENCE: *"Expect €500–1,500"*), and OSS filings if anything is ever sold online. Run the same arithmetic to the bank account: €9,183/yr × 0.52 ≈ **€4,800/year**, minus €500–1,000 of fixed professional and insurance costs, against 75–90 hours. That is **€45–55/hour gross of tax, ~€21/hour after**. The document's own conclusion — *"That is a supplementary income, not a business"* — is right, and still generous by roughly a factor of two.

**3.2 — Line A's steady state assumes a funnel that cannot mathematically repeat.**

*"Twelve seats is twelve conversations, not a campaign"* and *"If twelve conversations do not produce eight deposits, that is the market speaking."* A 67% close rate on cold-ish personal asks is already heroic. Three cohorts a year then requires 24–36 more named prospects from one personal network in twelve months, inside a population that fully turns over every 2–3 years, with the legal funnel restricted to word of mouth. The steady-state figure implicitly assumes an acquisition channel the document elsewhere says does not exist. MARKET-EVIDENCE §4.2 names this exactly: *"an instructor with no audience in the niche has no mechanism to fill a cohort... **This is the single largest unpriced cost in every consumer-course model in the dossier.**"* Line A leaves it unpriced too.

**3.3 — Line A's SOFA VAT lever contradicts its own price model.**

§7 says price on net (*"a €500 sticker price is roughly €420 net to the UG"*) and, four paragraphs earlier, that SOFA households buy VAT-free via AE Form 215-6B, calling it *"a genuine ~19% price lever."* Almost the entire target audience is SOFA households. So either the base case is €500 net (not €420) and the whole model is 19% understated, or the price lever is spent on the customer and there is no lever. The document does not pick. And whether the tax relief office will issue the forms **for a training service** is marked `[unverified]` in both Line A and MARKET-EVIDENCE §7.3 — meaning the base-case revenue line rests on an unconfirmed administrative practice.

**3.4 — Line B: "$250–400 per seat × 20–30 attendees ≈ $5,000–12,000 per engagement" for DoDEA.**

The same document, §1, states the entire contestable new-entrant DoDEA market is *"roughly $12,000 per year, globally."* A single engagement at the top of this range would consume 100% of the annual global contestable market. The cell also concedes *"**and quite possibly zero**."* It also ignores that DoDEA PD time is bargained (FEA/NEA) and that GAO found *"teacher time, not money, to be the top reported barrier"* — 20–30 attendees requires the school to fund release time on top. This row should be deleted, not caveated; leaving a five-figure number in a table invites it to be quoted later.

**3.5 — Line A's "workshop-in-a-box" at "$3,000–50,000/yr" is unusable.**

Marked in-table as *"[unverified — SEO-grade sources, no German comparables found]"* and *"Realistically €0 in year one"* — and still ranked *"Theoretically highest"* revenue per hour and named the **runner-up recommendation**. A €0-in-year-one line with an unverified 16× range is not a runner-up, it is a note. Cut it or cost it.

**3.6 — Line C's own table does not support "the comparison is not close" on deal size.**

School: *"Low thousands"* annual. IEC: *"Tens of dollars to low hundreds per month"* = $240–2,400/yr. Those are the same order of magnitude. The argument that actually carries — cycle length (days vs 6–18 months), no procurement, no per-district DPA treadmill, reviewer exists by construction — is strong and sufficient. Presenting the deal-size row as if it favours the IEC weakens a correct conclusion.

**3.7 — Line B's recommended option is the only one never subjected to an hourly-rate test.**

Line A computes ~€40/hour for the cohort in order to argue it is *"worse than his existing consulting-grade time is worth."* Line B recommends UMGC adjunct and reports revenue as *"**[unverified]**, do not model until HR answers"* while noting *"several hours a week per active section."* A US-benchmark $3,000–4,500/section over a 12–16 week term at ~6 hours/week is **$30–60/hour before prep**, likely lower in the Europe Division. Apply the same standard to the recommendation as to the thing being rejected.

---

# 4. LEGAL AND COMPLIANCE CLAIMS THAT ARE WRONG OR OVERSTATED

**4.1 — Line A §7 on FAR 3.601 (see 1.1). Wrong as written.** It states the prohibition bites on "any federal instrument" because of the spouse's employment. It runs against the contracting officer, and — per Line B and MARKET-EVIDENCE — is not triggered by a spouse who is neither owner nor controller. What actually binds is **18 U.S.C. 208** and **5 CFR 2635.502**, and those bind *her*, not the UG. Line A's framing would cause him to abandon accessible channels for the wrong reason.

**4.2 — Tech spec R-13's FernUSG rationale is close to worthless and the spec half-admits it.**

R-13: *"Building assessment into the portal manufactures the second element for every deployment that uses it."* But the recommended deployment (topology B, remote paid adult cohort) has a live instructor. `BGH III ZR 109/24` — quoted in both Line A and Line B — sets the monitoring bar at *"merely being able to ask follow-up questions by chat or email suffices."* An instructor answering a participant's question in a live session monitors learning success whether or not the portal has a grading table. R-13 is a reasonable data-minimisation decision; as a FernUSG mitigation it is decorative, and presenting it as *"a deliberate product decision with a legal edge"* overstates it.

**4.3 — Line C §5 overstates GDPR Article 8 for international schools.**

*"Processing children's personal data at scale is a plausible Article 35 DPIA trigger, and **Article 8 conditions attach to children's data**."* Art. 8 applies only to information society services **offered directly to a child** on the legal basis of **consent**. A school-commissioned newsletter, school as controller, UG as Art. 28 processor, on a contract/legitimate-interest basis, does not engage Art. 8. The DPIA point stands; the Art. 8 point does not.

**4.4 — Tech spec §4's claim that `safety_events` is "PSEUDONYMOUS" is false.**

The table's own comment says *"APPEND-ONLY, **PSEUDONYMOUS**, CONTENT-FREE"* and lists what it omits. But `safety_events.participant_id` is a direct FK to `participants`, whose comment says `email` is *"the ONLY personal datum the portal holds."* One join yields "this named person tripped `self_harm` at 14:32 on 3 October." That is identified personal data, and a `self_harm` category is an inference about mental health — arguably Art. 9 special-category data. Compounding it: `safety_events.participant_id ... on delete restrict` plus the `raise_append_only` trigger (which the source migration says *"Blocks EVERY role including the table owner and service_role"*) means **the row can never be deleted and the participant can never be deleted**. There is no retention period, no erasure path, and no lawful-basis analysis anywhere in the spec. For an EU-resident minor cohort this is the most serious compliance defect in the document, and it sits inside the section that claims to have made the privacy posture *"verifiable by reading `supabase/migrations/`"*.

**4.5 — Line A's §4 Nr. 21 UStG analysis leads with the point MARKET-EVIDENCE calls second-order.**

Line A: *"letter c) covers Schul- und Hochschulunterricht delivered by Privatlehrer — **natural persons only**, and limited by subject matter."* MARKET-EVIDENCE §6.4: *"the commonly-repeated framing... **fixates on the second-order obstacle**. The controlling limit on letter c) is **subject matter**."* Line A gets the letter right (an improvement on the refuted version) but keeps the wrong emphasis. The practical conclusion — don't chase the exemption — is correct either way.

**4.6 — Line B §3's "The Privacy Act has no such exception" is too absolute.**

*"FERPA has a 'school official' exception... **The Privacy Act has no such exception.**"* The Privacy Act's analogue is 5 U.S.C. 552a(m)(1) (contractor deeming) plus (b)(1) intra-agency need-to-know and routine uses. The operational conclusion (sell instruction, never operate a system of records) is right; the statement as written would not survive a lawyer's read.

**4.7 — Genuinely sound, and worth saying so.** The Privacy-Act-not-FERPA correction is handled correctly and consistently in all three documents that touch it. The FAR 19.502-2 / 13 CFR 121.105 set-aside analysis is the strongest single finding in the whole set and is stated identically in Line B §1, Line C §5 and MARKET-EVIDENCE §3.2. The FernUSG two-prong analysis and the "no 50% safe harbour" correction are correct and consistently applied. The AER 210-70 §17.a(4)/§19(e) citation fix is right. The AI Act Article 4 / Article 99 correction in MARKET-EVIDENCE §4.8 is the most valuable thing in the appendix.

---

# 5. TECHNICAL SPEC — VERIFIED AGAINST `/home/user/upskill-news-app`

## 5.1 Path and symbol verification — this part is clean

I checked every named module, export, migration helper and route wrapper. **All of them exist and are named correctly.** Verified present:

- `proxy.ts` with `buildClerkProxy()` / `buildMisconfiguredProxy()` / `cookieProxy` selected at module load (proxy.ts:212–216) — exactly as described.
- `lib/api-server.ts`: `isServerBoundaryActive`, `ApiOutcome`, `ApiDeps`, `apiJson`, `identityDeniedOutcome`, `resolveAppUserId`, `unprovisionedOutcome`, `boundaryInactiveOutcome`, `readJsonBody`, `logServerError`, `unauthenticatedOutcome` — all exported, all as documented.
- `lib/auth-server.ts`: `getServerIdentity`, `identityFromClerkAuth`, `getClerkSessionToken` — present.
- `lib/auth-config.ts`: `dashboardRedirectPath`, `apiAccessDeniedStatus`, `roleFromClerkMetadata`, `roleFromClerkSessionClaims` — present; the 401-vs-403 normalisation the spec asks to preserve is real (auth-config.ts:186–192).
- `lib/supabase-server.ts`: `createUserScopedServerClient`, `createServiceRoleServerClient`, `NO_COOKIES` / `NO_SESSION_AUTH` — present.
- `lib/pipeline/http-timeout.ts` `httpTimeoutSignal` — present.
- `handleGateActionRequest` / `handleCorrectionRequest` / `handleSendDeliveryRequest` / `handleUsersRoleRequest` — all real, all thin-wrapped by the route files named.
- Migration helpers `private.clerk_user_id / app_user_id / app_role / is_admin / raise_append_only / set_updated_at / owns_client / is_client_self` and the `consent_audit.seq` tie-breaker — all present as described.
- `assertSafeApiKey`, `parseJsonBody`, `redirect: 'error'` in llm.ts — present. `scripts/a11y-audit.mjs` and `npm run a11y` — present.

**No invented paths or function names.** One stale number: the spec says *"672 tests, 54 files as of the source repo"*; the tree now has 56 test files and ~685 `it/test` calls. Copied from `CLAUDE.md`, not load-bearing. `qwen3.8:27b` is real — documented in `docs/OLLAMA-NIGHTWORK-DASHBOARDS.md` §2.

## 5.2 Architectural errors

**(a) The role rename breaks the migrations the spec says to reuse verbatim.** Spec §3 Layer 2: *"`UserRole` in `lib/types.ts` becomes `'guest' | 'participant' | 'instructor' | 'operator'`."* Spec §4: *"Reuses the `private.*` helper seam... **verbatim**."* But `supabase/migrations/20260714100000_identity_and_rls_helpers.sql:62` is:
```sql
role text not null check (role in ('client', 'iec', 'admin')),
```
and line 131:
```sql
create or replace function private.is_admin() ... select private.app_role() = 'admin';
```
Every RLS policy in spec §4 calls `private.is_admin()`. With roles renamed, no user can hold `admin`, `is_admin()` is permanently false, and **every operator policy denies**. Either `public.users` gets an `alter table ... drop constraint` migration and `is_admin()` is rewritten, or the operator role keeps the literal string `admin`. The spec says neither.

**(b) `LLMAdapter.generate()` returns `Promise<string>` — there are no token counts to account.** llm.ts:43–48:
```ts
export interface LLMAdapter {
  readonly name: string;
  readonly isMock: boolean;
  generate(opts: LLMGenerateOptions): Promise<string>;
}
```
The spec's `InferenceResponse.usage.promptTokens / completionTokens / tokensRemaining` and §8's *"After the call: increment `tokens_used` by the actual usage"* require the adapter to surface `prompt_eval_count` / `eval_count` (Ollama) and the equivalents for all four providers. That is a breaking change to a shared interface used across `lib/pipeline/**`, and it is not in the build sequence. Token quota — described as *"The real cost control"* — is currently unbuildable on the stated reuse plan.

**(c) Phase 1 is self-contradicting.** §10 Phase 1: *"**Phase 1 has no database.** The roster is a hard-coded array of Clerk user ids in an environment variable."* §5 conventions: *"all handlers answer **503** when `isServerBoundaryActive` is false."* Verified in api-server.ts:34: `isServerBoundaryActive = isClerkServerConfigured && isSupabaseServerConfigured`. No Supabase means the boundary is inactive means `/api/inference` returns 503 to everyone. Phase 1 as specified ships a portal that cannot answer a request. Either Phase 1 breaks the convention the spec insists on, or Phase 1 needs Supabase after all — and the *"defers the entire Supabase provisioning decision... by three weeks"* benefit evaporates.

**(d) Moderation runs outside the queue it needs.** §3 orders the handler `4 consumeQuota → 5 moderateInput → 6 enqueue → 7 routeAndGenerate`. The guard model runs on the **same Ollama instance** with `OLLAMA_NUM_PARALLEL=2`. So guard calls contend for the exact slots `admit()` exists to ration, while sitting outside the queue. Under the burst the spec is designed for (*"thirty people hit 'send' within the same ten seconds because the instructor just said 'try it now'"*) the guard calls will themselves stall or fail — and a guard-model failure in a minor cohort must fail closed, which means the whole cohort blocks. The failure mode of the moderation layer under load is never specified.

**(e) The module-scoped queue cannot be pinned on Vercel.** §8: *"On a single-instance deployment... that is the whole system."* §9(B): *"If the portal is serverless, module-scoped state (the §8 queue, health cache) is per-instance; **pin to one instance**." * Vercel serverless functions do not offer a one-instance guarantee; each concurrent request may be its own isolate, making `maxConcurrent` meaningless and the queue a no-op. This is presented as a deployment setting; it is an architectural constraint that forces a long-running server (VPS or fluid/edge-persistent runtime). Recommending topology B as *"**The default. Recommend this one**"* without resolving it means the recommended topology cannot honour the spec's own headline risk mitigation.

**(f) `model_profile` ships in Phase 3, the feature ships in Phase 4.** The `cohorts` DDL carries `model_profile check in ('default','strict','agentic')` and N-2 says *"the system prompt is pinned to the strict profile."* §10 Phase 4 lists *"per-cohort system prompts"* as a candidate. The column enforcing the minor-safety requirement has no implementation in any planned phase.

**(g) Output-block DoS.** §7: *"the completion is discarded and never rendered. **The tokens still count against quota — they were generated.**"* With no streaming, one participant can repeatedly trigger output blocks, each consuming a full 27B generation on a box the spec caps at 8–12 concurrent users. Quota bounds the abuser's total, not their impact on the other eleven within a session. Not addressed.

## 5.3 Security holes

**(h) THE BIG ONE — client-supplied `history` bypasses input moderation entirely.**

The request contract:
```ts
history?: Array<{ role: 'user' | 'assistant'; content: string }>;
```
with the comment *"Prior turns, supplied by the CLIENT from sessionStorage."* §8 correctly says *"`history` is client-supplied and therefore **hostile**"* — and then §7 mitigation 1 says:

> *"**Do not moderate the history on every turn.** Moderate only the new user turn on input. History was already moderated when it was new."*

It was not. A participant (or any browser devtools console) can POST arbitrary content in `history`, including forged `assistant` turns, and it reaches the model unmoderated. That defeats:
- F-5 ("Each request passes a deterministic filter, then an ML classifier, on the way in")
- N-2 ("Minor-safe by configuration, not by hope... The code path must make the unsafe combination **unrepresentable**")
- the server-side system prompt (forged assistant turns are the standard jailbreak against a pinned prompt — and `CLASSROOM-BUILD-LAB.md` §4's whole rationale is *"a portal keeps the system prompt server-side where a student cannot edit"*).

Output moderation would still fire, so it is not unbounded — but the input layer, which the spec calls the floor that *"exists because a classifier can be slow, wrong, or down"*, is trivially bypassable in the deployment aimed at minors. This single line invalidates the safety claim the whole architecture is built to support.

**(i) `grant select, insert on public.safety_events to authenticated` with no INSERT policy.** RLS default-deny makes it inert today, so the grant is dead code — but it is a loaded gun: the day anyone adds a permissive insert policy, a participant can forge safety events against a classmate. And the spec never states which client writes safety events; the default in §3 Layer 4 is `createUserScopedServerClient`, which cannot write them. The writer must be the service-role client and the grant to `authenticated` should be dropped.

**(j) `OLLAMA_HOST=0.0.0.0` with no authentication, justified only by N-7.** §6: *"acceptable **only** because Tailscale ACLs are the firewall and no inbound port is open on the residential line (N-7)."* N-7 covers inbound WAN. It does not cover the LAN. In **topology A** — which the spec calls *"The right answer for **youth classes** and family use"* — the Beelink sits on a home or school segment with Ollama listening on every interface with no auth. Any device on that segment (a student's phone, an IoT device, a guest) has unmetered, unmoderated, unquota'd access to the raw model endpoint. That is precisely the thing F-2 exists to prevent: *"No admin routes, no other cohort, **no model endpoint**, no key."* Bind to the tailnet interface or loopback and front it, or drop the claim.

**(k) Nothing disables Clerk self-signup.** F-1: *"No self-registration, **ever**."* Verified in auth-config.ts:106–113, `roleFromClerkMetadata()` defaults an unrecognised role to the least-privileged authenticated role. Under the renamed vocabulary, anyone who creates a Clerk account becomes a `participant`. The only thing standing between them and `/api/inference` is the cohort-membership check at handler step 3. That is probably sufficient, but F-1 is an identity-provider configuration requirement and the spec never states it. Add "Clerk instance restricted to invitation-only" to the requirements, since it is the actual enforcement.

## 5.4 Asserted as configuration, actually custom code

- **Session-affinity routing.** §6 flags this honestly and correctly: *"session-affinity routing is custom middleware, not configuration."* Good — this is the one the spec gets right, and the table row for it is the best line in §6.
- **The queue** is presented in §8 as a component to build (correct), but §9(B)'s *"pin to one instance"* presents the *precondition* for it as a config setting. It is a platform choice.
- **The Ollama options.** §6 says *"Extend `OllamaAdapterOptions` and the request body"* — correct, that is code — but it is bundled visually with the systemd block, which is config. Note the spec's systemd block adds `Environment="OLLAMA_NUM_PARALLEL=2"` which is **not** in the source block in `OLLAMA-NIGHTWORK-DASHBOARDS.md` §1, and that document's own guidance is *"Leave 1 for the 70B+ window; 2–4 for the 8B triage model"* — i.e. it is per-workload, and a single server-wide value cannot satisfy both the 27B build tier and the 8B guard. Silently added, and it is the value `maxConcurrent` is supposed to match.
- **`format` / `think: false`.** §7 specifies the guard call uses `format` and `think:false`. `LLMGenerateOptions` today carries only `prompt / system / temperature / maxTokens`. Both need adding to the shared interface, not just the Ollama body.

---

# 6. WHAT IS MISSING ACROSS THE WHOLE SET

1. **An arbitration document.** Five recommendations, no ranking, no shared decision rule, no owner. This is the single biggest gap. MARKET-EVIDENCE's verdict (launch ProPrecept) is the one option that appears in no service-line document as anything but a footnote.
2. **A cost line anywhere.** Not one document nets German corporate tax, insurance, Steuerberater, legal opinions, room hire beyond €300, or OSS filings out of a revenue figure. MARKET-EVIDENCE §6.3 has the tax stack; no service-line document uses it.
3. **What happens if he does become a DoDEA employee.** Line B §2(b) sketches it; nothing else does. Line A's entire business — selling training into the garrison community — would come under 5 CFR 2635 subpart H and the JER on day one. The 90-day plan in Line A §9 should have a "does he intend to apply to DoDEA in the next 24 months" gate at the top. It does not.
4. **Anthropic's terms for the Q1 test.** Tech spec §11 Q1 step 2: *"`ollama launch claude` (v0.15+) runs the Claude Code harness against a local model."* Pointing a vendor's agent harness at a competitor model to benchmark it, then productising the finding, is at minimum a terms question. Free to check, never mentioned.
5. **What the participant actually gets when the Beelink is down.** N-4 promises graceful degradation to *"read-only mode with a clear banner."* In a paid evening class, read-only mode is a refunded session. No SLA language, no refund policy, no cancellation term for a hardware failure — and MARKET-EVIDENCE §6.9 flags exactly this: *"a paid service with an SLA on a consumer line with no Entstörung guarantee is a contract that cannot be honoured."*
6. **Data retention and erasure for the portal** (see 4.4). No retention period, no GDPR Art. 17 path, no Art. 30 record, no AVV template, no DPIA — for a system explicitly designed to serve minors in the EU.
7. **The Notarin.** MARKET-EVIDENCE §7.5: *"The only named prospect in the entire business — the Notarin — is slated for a free 4–6 week pilot."* She is the single named human with a budget anywhere in this corpus, and she appears in none of the three service-line documents. The §203 StGB / BNotO analysis in MARKET-EVIDENCE §6.8 is the most commercially specific work in the set and has no home.
8. **A German-language delivery decision.** MARKET-EVIDENCE §7.5 raises it; Line A dodges it by staying inside the English-speaking garrison; Line B recommends VHS and IHK, both of which teach in German, without addressing it.
9. **Concurrency measurement.** Every document says "load-test before selling a seat" and none has been run. The tech spec's entire capacity claim (§6: *"cap a synchronous cohort at 8–12 participants... **not a soft target; it is the number the hardware supports**"*) rests on order-of-magnitude third-party figures the source document itself flags as *"third-party-calibrated."* Saying "it is the number the hardware supports" about an unmeasured number is exactly the overclaim the same paragraph warns against.

---

# 7. PADDING TO CUT

- **Line A §5 (Curriculum), all four weeks.** ~1,000 words of syllabus for a course that §9 says should not be built until twelve conversations come back warm. It is generic ("Ship something ugly to a real URL"), it presupposes the go decision, and it is the cheapest part to write later. Cut to five lines.
- **Line A §2's national spouse statistics table.** Seven rows of DoD-wide figures for a decision about twelve named people in one town. The only two that matter (median $35,000; 20–22% unemployment) are restated in the verdict. Cut the table.
- **The funding-rail tables, duplicated three times.** SpouseWorks / SkillBridge / MSEP / VET TEC / Army CA appear in near-identical form in Line A §3, Line B §6, and MARKET-EVIDENCE §2. All three conclude "no." One table, referenced twice.
- **Tech spec §6's llama.cpp flag table.** §11 Q5 says the Ollama-vs-llama.cpp question should be *"Answer[ed] after Q1 and Q2"* — i.e. after the two experiments that have not been run. A flag reference for a server that may not be chosen is premature. Keep only the last row (session affinity is custom middleware), which is the finding.
- **Tech spec §9's three-topology comparison.** Two of the three are dismissed in one line each in their own verdict rows. Compress to a paragraph naming (B) and the two conditions under which (A) wins.
- **MARKET-EVIDENCE §8, the source list.** ~160 links across nine subsections, largely duplicating the per-document source lists. Since MARKET-EVIDENCE is explicitly the appendix of record, the service-line documents should carry inline citations only and drop their own §Sources entirely.
- **Line B §4's threshold table.** Five rows to establish that the doorway is $15,000, in a section whose own conclusion is *"**None of this rescues the DoDEA case**."* Two sentences.

---

# 8. BLUNT RANKING BY EXPECTED VALUE

**1. Launch ProPrecept Ireland and ProPrecept RSA.** Code-complete, markets he already understands, no accreditation gate, no garrison approval, no new regulatory surface, no audience to build, no new legal opinion. MARKET-EVIDENCE is right that *"That is the benchmark every option in this dossier should have been measured against and none was."* Everything below competes with this and loses on every axis that matters — time-to-first-euro, marginal hours, regulatory surface. That it is the recommendation of the appendix and appears in none of the three service-line documents is the clearest sign the research programme lost the plot.

**2. UMGC Europe adjunct application.** One email. Highest information-per-hour in the whole corpus. It is a job, not a business — €30–60/hour at best, unverified for the Europe Division, non-passive, uses no hardware — but it converts an unpriced credibility deficit into a real credential, the institution owns enrolment and billing, and it is the only route by which federal education money reaches him. Two free gates first (completed master's; SOFA read in writing) and one decision he has not made (it forecloses the Line A cohort, per Line B's "pick one").

**3. One Volkshochschule course.** €400–800 for a term of evenings — not revenue, and both documents say so. It is worth doing as the cheapest possible curriculum test in front of real adults with an institution absorbing enrolment and solicitation risk. Do it before Line A, not after. **Caveat that Line A omits:** the §127 SGB IV shield expires 31 December 2026, so the clean-Honorarvertrag window is roughly four months.

**4. Finish the Upskill News IEC motion.** Line C's trigger is the best-specified falsifiable gate in the set: *"Three IEC customers, each having paid a real invoice for a real delivered edition, retained through one full admissions cycle... with at least one renewal."* Cheap, already built, and it settles a question that has been open long enough to become sunk cost. Rank 4 only because it competes with #1 for the same evenings and #1 is closer to money.

**5. Line A — one paid in-person cohort, as an experiment.** Line A's own analysis is honest and its own numbers do not support it: ~€21/hour after tax, an audience with a median income of $35,000 facing free 20-week alternatives from Microsoft, a marketing funnel legally reduced to word of mouth, and a population that fully replaces itself every 2–3 years. The **Days 1–30 verification block is worth running** — it costs eight hours and produces the only demand signal in the corpus. But do not build the curriculum in Days 31–60 unless #1 has already shipped, and resolve the UMGC conflict first.

**6. Workshop-in-a-box licensing.** €0 in year one by its own admission, with an unverified 16× revenue range. Not a line; a note attached to #5.

## KILL

- **DoDEA as a customer.** All three documents converge, on three independent grounds (~$12k/yr global contestable market; FAR 19.502-2 + 13 CFR 121.105 structurally closes the $15k–$350k band; asymmetric 18 U.S.C. 208 exposure landing on his wife's criminal-statute compliance). This is the single best-evidenced conclusion in the corpus. Kill it and stop revisiting.
- **Upskill News → US K-12 schools.** Line C is right that it fails on architecture before economics: remove the named human reviewer and the differentiator is deleted.
- **Army Credentialing Assistance, SkillBridge, MSEP, VET TEC 2.0, direct SpouseWorks provider status.** All closed by written rule. Well evidenced.
- **The military PCS/transition briefing.** Correctly killed in Line C §7: free authoritative government substitutes, sponsorship-media economics, JER exposure via the spouse.
- **The teaching portal, as a build project right now.** Not because the engineering is bad — the codebase analysis is accurate and the reuse thesis is genuinely sound — but because **there is no buyer**. Line A rules the portal out of the only paid adult cohort anyone recommends. Line B says nothing in institutional PD uses the Beelink. MARKET-EVIDENCE §7.5 says no proposed opportunity uses the hardware for anything a laptop cannot do. Building 18–40 hours of moderated multi-tenant inference gateway against zero named demand, at 15–25 minutes a day, is the definition of building the thing you enjoy building.

  What survives from the spec: **Q1** (can a 27B drive an agentic loop — one afternoon, decides whether "build your own app" is an honest promise at all) and **Q2** (measured concurrent capacity — one evening, and every capacity claim in five documents is currently an estimate). Run those two. Bank the `OllamaAdapter` `num_ctx`/`keep_alive`/`format` fix, which is a real correctness bug in the existing pipeline (prompts are silently truncated at 4,096 tokens with no error) and is worth doing regardless of whether any portal is ever built.

## THE ONE THING TO FIX BEFORE ANYTHING ELSE

If the portal is ever built, fix **§7 mitigation 1** first. *"History was already moderated when it was new"* is false — `history` is client-supplied, and that one sentence makes the input moderation layer, and with it every claim in N-2 about minor cohorts, bypassable from a browser console.
