# Service Lines — Monetising the Inference Layer

> **Date:** 2026-08-18 · **Status:** research complete, arbitrated. No commitments made.
> **How this folder was produced:** a 16-agent research workflow — five market and legal
> dimensions, each adversarially verified, then five drafted documents, then a hostile
> cross-document review ([`REVIEW-FINDINGS.md`](REVIEW-FINDINGS.md)).
> **Reading order:** this file, then `REVIEW-FINDINGS.md`, then whichever line you are acting on.

---

## The headline, stated plainly

The question that started this work was "how do I use my Beelink better." The research
answered a different question, and the answer is more useful than the one that was asked:

**Across five dimensions and roughly twenty proposed opportunities, none of them needs the
Beelink.** Not one uses the hardware for anything a laptop or a twenty-dollar-a-month API
could not do. Every service line here — teaching adults, selling PD to institutions,
expanding a newsletter product — is a business about *your time and credibility*, and the
inference cost in all of them rounds to nothing. The hardware is not the constraint, so
owning it is not an advantage.

That is not a failure of the research. It is the finding. Acting on it means separating two
things that have been tangled together for several sessions:

- **The Beelink earns its keep as a private capability**, not as a product. Overnight batch
  work you would not otherwise pay for — the dashboards in
  [`../docs/OLLAMA-NIGHTWORK-DASHBOARDS.md`](../docs/OLLAMA-NIGHTWORK-DASHBOARDS.md),
  dissertation compute, fine-tuning experiments, private RAG over documents that must not go
  to a cloud. That is real value. It is not revenue.
- **Revenue comes from things you have already built.** The strongest recommendation to come
  out of this entire programme is one that appears in none of the service-line documents as
  anything more than a footnote, which is itself the clearest sign the research drifted.

And one omission worth naming: **the only human being with a budget named anywhere in this
corpus is the Notarin** — the local notary already slated for a free pilot of the VilseckKI
RAG service. She has a confidentiality problem that genuinely cannot go to a cloud, which is
the one shape where local hardware is a real differentiator rather than a hobby. She appears
in none of the three service-line documents. If the question is "what makes the Beelink pay,"
the answer was probably already in this repository before this research started.

---

## Arbitrated ranking

Five documents produced five recommendations and no ranking. This is the ranking. It follows
the hostile reviewer's assessment, which I endorse after checking its reasoning.

| # | Action | Why it ranks here | Effort |
|---|---|---|---|
| **1** | **Ship ProPrecept Ireland and ProPrecept RSA** | Code-complete. Markets you already understand. No accreditation gate, no garrison approval, no new regulatory surface, no audience to build, no new legal opinion. Every option below competes with this and loses on time-to-first-euro, marginal hours, and regulatory surface. | Deployment, not development |
| **2** | **Apply for the UMGC Europe adjunct AI posting** | One email, and the highest information-per-hour in the corpus. It is a job, not a business — roughly €30–60/hour at best, unverified for the Europe Division, and it uses no hardware — but it converts an unpriced credibility deficit into a real credential and is the only route by which federal education money legitimately reaches you. **Note:** per Line B it likely forecloses Line A's private cohort into the same population. Pick one. | One email, then two gates |
| **3** | **Teach one Volkshochschule course** | €400–800 for a term of evenings. Not revenue, and both documents say so. It is the cheapest possible test of the curriculum in front of real adults, with an institution absorbing enrolment and solicitation risk. **Time-boxed:** the §127 SGB IV transitional shield for Honorarlehrkräfte expires 31 December 2026, so the clean-contract window is about four months. | A term of evenings |
| **4** | **Finish the Upskill News IEC motion** | Line C sets the best-specified falsifiable gate in the set: three IECs who have each paid a real invoice for a real delivered edition, retained through one admissions cycle, with at least one renewal. Cheap, already built, and it settles a question that has been open long enough to become sunk cost. | Sales, not code |
| **5** | **Run Line A's Days 1–30 verification only** | Eight hours, and it produces the only genuine demand signal in the corpus. **Do not build the curriculum** unless #1 has shipped and the UMGC conflict is resolved. Line A's own arithmetic lands at roughly €21/hour after tax against an audience with a median income of $35,000 facing free alternatives. | Eight hours |

### Kill list

These are closed on evidence, not on preference. Stop revisiting them.

- **DoDEA as a customer.** Three independent grounds converge: a contestable new-entrant
  market of roughly $12,000/year globally; FAR 19.502-2 with 13 CFR 121.105 structurally
  closing the $15k–$350k band to a foreign-organised entity; and asymmetric 18 U.S.C. 208
  exposure that lands on your wife's compliance with a criminal statute, not yours. This is
  the best-evidenced conclusion in the corpus.
- **Upskill News into US K-12 schools.** It fails on architecture before it fails on
  economics: remove the named human reviewer and the differentiator is deleted.
- **Army Credentialing Assistance, SkillBridge, MSEP, VET TEC, and direct SpouseWorks
  provider status.** All closed by written rule — accreditation requirements a solo operator
  cannot meet.
- **The military PCS/transition newsletter.** Free authoritative government substitutes,
  sponsorship-media economics, and JER exposure through your spouse.
- **The teaching portal as a build project, for now.** Not because the engineering is wrong —
  the codebase analysis in the spec is accurate and the reuse thesis is sound — but because
  **no buyer exists**. Line A rules the portal out of the only paid cohort anyone recommends;
  Line B says nothing in institutional PD uses the Beelink. Building 18–40 hours of moderated
  multi-tenant inference gateway against zero named demand, at 15–25 minutes a day, is
  building the thing that is most enjoyable to build.

### What survives from the portal spec

Three things, all cheap, all worth doing regardless of whether a portal is ever built:

1. **Q1 — can a 27B open-weights model actually drive a multi-file agentic loop?** One
   afternoon. It decides whether "you will build your own app" is an honest promise in any
   teaching context, and it has been the load-bearing untested assumption for two sessions.
2. **Q2 — measured concurrent capacity on the actual unit.** One evening. Every capacity
   claim across five documents is currently a third-party estimate.
3. **The `OllamaAdapter` fix.** `lib/pipeline/adapters/llm.ts` sets no `num_ctx`, so prompts
   are silently truncated at the 4,096-token default with no error. That is a real
   correctness bug in shipped code, independent of this whole enquiry.

---

## A decision rule

The recurring failure mode across this corpus is designing infrastructure for demand that has
not been demonstrated. One rule prevents it:

> **Nothing gets built until a named human has agreed to pay for it.** Not a market segment,
> not a persona — a person with a name, who has said yes.

By that rule, the correct next actions are #1 and #2 above, and the correct amount of portal
code to write today is none.

---

## The documents

| File | What it is |
|---|---|
| [`REVIEW-FINDINGS.md`](REVIEW-FINDINGS.md) | **Read this second.** The hostile cross-document review: contradictions between documents, unsupported claims, revenue estimates that do not survive, and a verified audit of the technical spec against the real codebase. Where it disagrees with a service-line document, it wins. |
| [`LINE-A-SPOUSE-FREELANCER-WORKSHOPS.md`](LINE-A-SPOUSE-FREELANCER-WORKSHOPS.md) | Teaching app-building to adults in the Grafenwöhr/Vilseck military community. The funding-rail analysis is the durable part: it establishes that every federal rail is closed to a solo operator, which saves the next session from re-researching it. |
| [`LINE-B-DODEA-AND-INSTITUTIONAL-PD.md`](LINE-B-DODEA-AND-INSTITUTIONAL-PD.md) | Selling PD to DoDEA and adjacent institutions. Concludes against DoDEA. Contains the conflict-of-interest analysis in both cases (spouse employed today; you employed hypothetically) and the Volkshochschule route. |
| [`LINE-C-UPSKILL-NEWS-SCHOOLS.md`](LINE-C-UPSKILL-NEWS-SCHOOLS.md) | Whether to expand Upskill News from IECs to schools. Concludes not-yet, with an explicit trigger. |
| [`TECHNICAL-SPEC-TEACHING-PORTAL.md`](TECHNICAL-SPEC-TEACHING-PORTAL.md) | The buildable portal specification. **Gated — do not build yet.** Its codebase analysis was verified accurate module-by-module, so it remains the design of record if a buyer ever appears. Carries corrected defects marked inline. |
| [`MARKET-EVIDENCE.md`](MARKET-EVIDENCE.md) | The evidence appendix: funding rails, DoD acquisition thresholds, competitor pricing, German business and training law, and a table of every claim where researcher and verifier disagreed. Cite from here, not from the line documents. |

### Known open defects

Corrected inline in the source documents and recorded here so nothing is quietly lost:

- **Line A** wrongly claimed FAR 3.601 bars federal instruments because of a DoDEA-employed
  spouse. It does not — it runs against the contracting officer and reaches businesses owned
  by a Government *employee*. The organisational-contract shape it deferred on that ground
  deserves re-evaluation on its real merits.
- **Line A** repeated a refuted claim that §2 SGB VI pension liability at 18.6% is "worse than
  the trade tax it avoids." The comparison omits the corporate stack and the contribution cap.
- **The technical spec** claimed zero prompt retention "on any code path" while its own routing
  ladder falls back to cloud providers that retain text. Now carries an explicit carve-out.
- **The technical spec's** `safety_events` table was labelled pseudonymous. It is not: one join
  yields an identified person and a mental-health inference, with no retention period and no
  erasure path. This is the most serious open compliance defect and blocks any EU minor cohort.
- **The technical spec** planned to skip re-moderating conversation history because it "was
  already moderated." History is client-supplied, so that was a bypass. Corrected.
- **Unresolved:** the role rename in the spec (`admin` → `operator`) silently breaks
  `private.is_admin()` in the existing migrations, which would deny every operator policy.
  Flagged, not fixed, because the spec is gated.
