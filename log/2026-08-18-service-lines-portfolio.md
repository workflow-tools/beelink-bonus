# 2026-08-18 — Service-line portfolio: monetising the inference layer

**Session type:** overnight research workflow (16 agents: 5 research dimensions, 5 adversarial
verifiers, 5 drafting agents, 1 hostile cross-document reviewer). Branch
`claude/ollama-beelink-dashboard-n6elb6`. Deliverable: `service-lines/`.

**Question:** what are the efficient ways to use the Beelink and the classroom research — adult
freelancer workshops, DoDEA consulting, an Upskill News expansion to schools, or something else?

**The finding that reframes the question.** Across five dimensions and roughly twenty proposed
opportunities, **none uses the Beelink for anything a laptop or a $20/month API could not do.**
Every service line researched is a business about time and credibility; inference cost rounds to
zero in all of them. The hardware is a private capability (Nightwork batch, dissertation compute,
private RAG), not a product. Recorded as the headline in `service-lines/README.md`.

**Arbitrated ranking** (the reviewer's, endorsed after checking the reasoning):
1. Ship ProPrecept Ireland + RSA — code-complete, known markets, no new regulatory surface.
   Appears in none of the service-line docs, which is itself evidence the research drifted.
2. UMGC Europe adjunct AI posting — one email, highest information per hour; likely forecloses
   the Line A cohort (same population), so it is a choice.
3. One Volkshochschule course — cheapest curriculum test; §127 SGB IV shield expires 31 Dec 2026.
4. Finish the Upskill News IEC motion — best-specified falsifiable gate in the set.
5. Line A Days 1-30 verification only — eight hours, the only real demand signal available.

**Kill list:** DoDEA as a customer (contestable market ~$12k/yr globally; FAR 19.502-2 + 13 CFR
121.105 close the $15k-$350k band to a foreign-organised entity; asymmetric 18 U.S.C. 208 exposure
landing on the spouse); Upskill News into US K-12; Army CA / SkillBridge / MSEP / VET TEC / direct
SpouseWorks provider status (all closed by accreditation rules); the PCS newsletter; and the
teaching portal as a build project — gated for want of a buyer, not for want of a design.

**What survives from the portal spec:** Q1 (can a 27B drive a multi-file agentic loop — one
afternoon, and it has been the load-bearing untested assumption for two sessions), Q2 (measured
concurrency), and the `OllamaAdapter` `num_ctx` fix, which is a real correctness bug in shipped
code — prompts silently truncate at 4,096 tokens.

**The omission worth acting on:** the only named human with a budget anywhere in this corpus is
the Notarin, already slated for a free VilseckKI RAG pilot. She has a confidentiality problem that
genuinely cannot go to a cloud — the one shape where local hardware is a real differentiator. She
appears in none of the three service-line documents.

**Defects corrected inline** (full record in `service-lines/REVIEW-FINDINGS.md`): Line A's FAR
3.601 scope error, which wrongly killed the organisational-contract shape; Line A's refuted SGB VI
18.6% comparison; the spec's zero-retention overclaim on the cloud path; the spec's `safety_events`
table labelled pseudonymous when one join identifies a person and infers mental health, with no
retention period or erasure path; and a history-moderation bypass (client-supplied history was
going to be trusted as already checked). Left open and flagged: the spec's `admin` -> `operator`
rename silently breaks `private.is_admin()` in the existing migrations.

**Decision rule adopted:** nothing gets built until a named human has agreed to pay for it.
