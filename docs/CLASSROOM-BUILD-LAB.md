# Classroom Build Lab — Students Building Their Own Apps on the Beelink

> **Date:** 2026-08-17 · **Status:** design study for a hypothetical teaching future, not a
> deployment plan. Every legal statement here is research, not advice.
> **Sibling doc:** [`OLLAMA-NIGHTWORK-DASHBOARDS.md`](OLLAMA-NIGHTWORK-DASHBOARDS.md) — same
> machine, same harness/brain/host model, opposite duty cycle. Nightwork is unattended
> batch, which this machine is *best* at; a classroom is attended interactive load, which
> it is *worst* at. That contrast drives most of what follows.

**Premise:** a 4-week unit in which each student ships a personal app, assisted by a
permitted cloud model plus the Beelink running open-weights models.

**Three design decisions were made during the session that produced this document, and
they matter enough to state up front**, because each one removed a serious flaw in the
first-pass architecture:

1. **A self-built portal**, not direct model access. Students get a browser tab, not an API
   key or a CLI.
2. **The Beelink can live at the school**, not in a Bavarian apartment.
3. **No interaction logging.** The teacher sees the code and the app, like any other
   project — not a transcript of what students typed.

Numbers not marked *measured* are calibrated from third-party benchmarks on other units.

---

## 1. Verdict

**The unit is good, the revised architecture is sound, and what remains is jurisdictional
rather than technical.** The three decisions above eliminated the worst problems in the
original sketch: a portal keeps the system prompt server-side where a student cannot edit
it and needs no client software on a managed Chromebook; school siting removes the
third-party tunnel provider, the cross-border transfer, and the residential-IP traffic
pattern that reads to a security team as data exfiltration; and not retaining content
removes most of the privacy surface along with the duty it would create.

What survives is a fork on **where you teach**:

- **At a US federal school (DoDEA), the hardware-in-the-loop version stays structurally
  hard** — not because the box is personal, but because a federal agency deploying ICT
  triggers an accreditation and accessibility regime that a self-built portal cannot
  satisfy. Run the cloud-only version there, and keep the Beelink strictly teacher-side.
- **At a private or international school, or an out-of-school cohort, the portal design
  works** and is genuinely good.

**One correction to advice given earlier in this session:** "have ML Upskill Agents UG sell
the service to the school" is *barred* in the case where Ryan himself is the federal
employee. FAR 3.601(a) states that a contracting officer "shall not knowingly award a
contract to a Government employee or to a business concern or other organization owned or
substantially owned or controlled by one or more Government employees." FAR 3.602 permits
an agency-head exception only for "a most compelling reason," which a classroom tool is
not. The nuance worth knowing: 18 U.S.C. § 208 imputes a *spouse's* financial interest to
the employee, which creates a **recusal duty on that employee** rather than a categorical
bar on the company — so the currently-real situation (spouse at DoDEA, Ryan owns the UG) is
a different and softer problem than the hypothetical one (Ryan at DoDEA, Ryan owns the UG).
Neither is a matter to settle from a web search; it is a question for agency ethics counsel.

**And one thing to test before building anything:** whether a 27B open-weights model can
actually drive a multi-file agentic coding loop. The entire "the Beelink unlocks something
cloud tools can't" argument rests on it, multi-file tool-calling is the known weak point of
quantized mid-size models, and nobody has checked. One afternoon settles it.

---

## 2. The Governance Fork

| Context | Verdict on student traffic to the Beelink | What would have to be true |
|---|---|---|
| **(A) DoDEA / US public school** | **Infeasible for a self-built system**, even sited on campus. | An authorization to operate under DoDI 8510.01; FERPA's school-official exception requires the outside party be "under the direct control of the agency" (34 CFR 99.31(a)(1)(i)(B)); and — the item most often missed — **Section 508 conformance**, normally evidenced by a VPAT, for any ICT a federal agency deploys. A teacher-built portal will never have one. This arrives *before* the privacy discussion. |
| **(B) Private / international school (Germany)** | **Workable.** Local hosting is a selling point here rather than a liability. | The school is the controller: an Art. 28 processing agreement, a documented lawful basis, an Art. 35 DPIA (children's data plus new technology), Art. 30 records. Plus an honest conflict to manage — teacher and vendor in one person. |
| **(C) After-school club, co-op, or tutoring** | **Works, and is where to start.** | Direct parental authorization, small cohort, not school-sponsored (a school-*sponsored* club collapses back into (A)). Note the trade: removing the school removes the blockers **and** removes the counsellor you would escalate a disclosure to. Charging money makes it worse, not better — it converts a hobby into a commercial AI service for minors. |
| **(D) Your own children** | **Fully feasible today.** | Nothing. This is where to prototype. |

**Sections 3–11 assume (B) or (C).** Where (A) changes the answer, it is flagged.

---

## 3. Which Brain, and Whose — the Portal Changes the Question

The age problem is a question about **who accepts the terms of service**, and a portal moves
that from the student to the operator. This is verified, not inferred:

- **Anthropic's consumer terms are 18+** ("at least 18 years old or the minimum age required
  to consent … whichever is higher"), enforced with Yoti age assurance. Claude Code through a
  Pro/Max subscription inherits that. **Claude for Teachers** (launched 14 July 2026, free
  year, sign-ups through 30 June 2027) is explicitly "for educators only, consistent with
  Claude's 18-and-over policy" — a teacher-side superpower and a student-side zero.
- **But the Usage Policy explicitly contemplates the portal pattern.** It defines a minor as
  anyone under 18 regardless of jurisdiction, and then says: "Products serving minors,
  including organizations providing minors with the ability to directly interact with
  products that incorporate our API(s), must comply with the additional guidelines outlined
  in our Help Center article." Those guidelines require **age verification, content
  filtering, monitoring mechanisms, and educational resources on safe AI use**, plus
  disclosure that the user is interacting with an AI rather than a human, and compliance
  with applicable child-privacy law. Anthropic audits, and can suspend accounts.

So the honest formulation is: **a student cannot hold a Claude account, but a teacher can
build an application that serves students** — subject to named, specific, satisfiable
requirements. That is a buildable path, not a wall, and it is the single most useful finding
in this document.

Two caveats. First, "monitoring mechanisms" sits in tension with zero retention; see §6,
which resolves it (real-time classification is monitoring; storage is not required for it).
Second, whether Claude Code accessed via an API key under the *Commercial* Terms carries an
explicit age floor could not be confirmed — the Commercial Terms contain no numeric age
clause on inspection, contrary to several secondary sources. Do not build on that ambiguity.

**What a class can use directly**, without a portal: GitHub (13+, and GitHub Education
covers K-12) with Copilot; Microsoft 365 Copilot Chat where a Global Admin has set
`ageGroup = NotAdult`; Gemini in Classroom where an admin has granted student access. The
common claim that "no age-cleared tool can write code" is false — all three do. The real gap
is narrower: **no age-cleared hosted vendor offers autonomous multi-file agentic
scaffolding.** That gap is the Beelink's actual job, and it is the thing §12 tells you to
test first.

---

## 4. The Portal Is the Architecture

Students never see a model endpoint. They see your app, and your app is the only door.

```
  STUDENT                     PORTAL (yours)                      BRAIN
  ┌──────────────┐      ┌──────────────────────────┐    ┌──────────────────────┐
  │ Chromebook   │      │ Next.js + Clerk          │    │ Beelink, isolated    │
  │ browser tab  │─────▶│  role gate: teacher/student│──▶│ segment              │
  │ (no install) │ LAN  │  per-student quota        │    │  llama-server        │
  └──────────────┘      │  input moderation         │    │  8B default / 27B    │
        │               │  ─ model call ─           │    │  agentic tier        │
        │ git           │  output moderation        │    └──────────────────────┘
        ▼               │  system prompt (server)   │                │
  ┌──────────────┐      │  NO content retention     │    ┌───────────▼──────────┐
  │ GitHub org   │      └──────────────────────────┘    │ cloud fallback       │
  │ 1 repo/student│                                      │ (disclosed, opt-in)  │
  │ + Pages       │                                      └──────────────────────┘
  └──────────────┘
```

**You have already built most of this twice.** In `upskill-news-app`: `proxy.ts` is a
role-gated network boundary with verified sessions; `app/api/**` route handlers call
`getServerIdentity()` and fail closed with 401/403; `lib/auth-config.ts` holds pure,
unit-tested gate rules; and `lib/pipeline/adapters/llm.ts` already auto-detects across
**ollama → openai-compat → anthropic → mock**. That adapter chain *is* the classroom
failover story: Beelink first because it is free, cloud when the Beelink is down or the task
is too hard, mock so a lesson never hard-fails. Rename the roles from `admin/iec/client` to
`teacher/student` and the skeleton is standing.

**What the portal buys, concretely:**

| Problem | How the portal solves it |
|---|---|
| Students can't hold vendor accounts | You are the API customer; they are your users |
| A managed Chromebook can't run a CLI or Docker | A browser tab needs nothing installed |
| A system prompt isn't a control if students run their own client | It lives server-side, unreachable |
| One student's runaway loop starves the class | Quota check happens in your route handler, before the model call |
| Moderation has to live somewhere | Same place, in and out |
| Keys leak | Students never hold one |

**Siting.** Put the Beelink at school on an **isolated segment** — its own router and access
point, not the district network. At DoDEA especially, connecting non-government equipment to
the DoD network is a much larger ask than putting a box in a classroom; an isolated lab
network is the well-trodden pattern (robotics teams and maker labs do it routinely). The
payoff is large: no tunnel provider, no third-party processor seeing plaintext prompts, no
cross-border transfer, and no thirty-endpoints-to-a-German-residential-IP pattern for a
security team to escalate. The cost is honest: **LAN-only means async access means "in the
building"** — library hours or study hall, not 2 a.m. from home. Given §6, that constraint is
a feature.

**One hard prerequisite:** this machine currently holds VilseckKI client documents and a
notary's corpus. A German *Notar* is a `§ 203 StGB` professional-secrecy holder, and since
2017 those obligations extend to service providers. An internet-or-classroom-reachable
service on the same host is not an acceptable neighbour for that data. **Either the notary
corpus moves off this machine before students touch it, or students get a different
machine.** Container isolation is not a security boundary against a motivated teenager.

---

## 5. Capacity: The Honest Arithmetic

First, a hardware correction this repo's `CLAUDE.md` should absorb: the iGPU is a **Radeon
8060S (gfx1151), 40 CUs**. The 890M is the 16-CU Strix Point part. Published benchmarks
worth citing are 8060S results.

**The binding constraint is prefill, not decode.** Everyone reasons about output tokens per
second, but the thing that falls over is *reading student code in*. Decode is
memory-bandwidth-bound and amortizes across a batch — the same weights are read once per
step whether one or thirty sequences are decoding, so aggregate throughput rises with
concurrency. Prefill is compute-bound and amortizes not at all. Order-of-magnitude prefill
ceilings, rounded deliberately because they are calibrated from a single measured anchor and
three significant figures would be false precision: roughly **800 prompt-tokens/sec for an
8B**, **400 for a 14B**, **200 for a 27B**, and a *measured* **266 for Qwen3.5-122B-A10B**.

Thirty students pasting a 6,000-token file every three minutes is about 1,000
prompt-tokens/sec of demand. Prefix caching is the lever — a warm follow-up turn costs a
~300-token delta instead of a cold 6,000 — but it only helps if a student's next turn lands
on the slot still holding their state. **That is session-affinity routing, and it is custom
middleware, not configuration**: `llama-server` does not route by identity, and with ~10
slots against 30 students only a third of the class can be warm at once. At 6–10 students it
closes comfortably. At 30 it does not.

**Why the 122B MoE is the wrong classroom default** — and not for the reason usually given.
The memory objection is wrong: it is a hybrid design with few full-attention layers, so
thirty students at 8k context costs roughly 3 GB of KV, not 30. Reject it on prefill (266
versus ~800) and on MoE concurrency, where expert routing diverges across concurrent
sequences and aggregate throughput peaks around 8 slots then regresses. It is a superb
Nightwork model and a poor classroom model. That is the whole thesis of the sibling doc,
arriving from the other direction.

**A budget that does not close, and must:** four resident tiers (122B ≈ 70 GB, 27B ≈ 18 GB,
14B ≈ 9 GB, 8B ≈ 5 GB) sum to ~102 GB against a practical ceiling near 100 GB — before KV
cache, before a guard model, before the OS. `llama-server` runs one model per process. **Pick
two tiers, not four.** Recommended: an **8B dense** as the default for chat, explanation and
debugging, plus **one** larger tier — the 27B if the agentic test in §12 passes, the 14B if
it doesn't.

Also: a guard model on "the idle CPU cores" is not free on this machine. Unified memory means
CPU inference draws from the same LPDDR5X bandwidth the GPU is saturating. Budget it as
competing load, not spare capacity.

**The number nobody has computed, and the one that decides feasibility:** per-student
wall-clock time for a *complete* agentic task. Single-stream figures do not answer it. At
eight concurrent slots, per-stream decode falls substantially even as aggregate rises; an
800-token file edit becomes minutes of decode alone, and a five-to-fifteen-call agent loop
plus prefills could exceed a class period. If a student gets less than one full agent run per
period, the agentic tier fails on latency regardless of everything else. **Measure it before
designing a syllabus around it.**

---

## 6. Data Minimization by Design

The decision not to log is the right one, and it is stronger when written down as a policy
than left as an absence. The move that makes it work is separating four things people lump
together:

| What | Keep? | Why |
|---|---|---|
| **Prompt and response content** | **No.** Zero retention. | The sensitive part, and not needed to run the class |
| **Operational metadata** — counts, tokens, latency, errors, quota | Yes, short window | You cannot run a shared service blind, and it reveals nothing said |
| **Real-time safety classification** | Yes, stateless | Classifies, decides, forgets — like a spam filter that doesn't archive mail |
| **Alerting on a safety hit** | Judgment call | Can be off, pseudonymous, or aggregate |

This resolves the tension with Anthropic's "monitoring mechanisms" requirement: monitoring is
the *classification*, not the *storage*. You can satisfy it with a real-time filter and no
transcript.

**Process visibility does not require surveillance, because the git history already is the
process record.** Four weeks of student-authored commits show what was tried, abandoned, and
fixed. Reading that is a normal thing a teacher does with a project. Pair it with a short
reflection and a required export button, and you are assessing process without reading a
single prompt.

**Two consequences to accept.** First, with no retrospective review, the guardrail has to
work in real time — this raises the stakes on §7 rather than lowering them. Second,
**institutions may require retention** for child-protection review. If one does, the workable
compromise is split stores: metadata always, *flagged* content only, in a separate
access-logged store on the institution's incident schedule — never a general transcript.

**Local inference is the privacy-maximizing choice here, and cloud fallback breaks that
promise.** With the model on the Beelink, "nobody sees this, including me" is literally true.
The moment a request fails over to a cloud API, that vendor retains it under its own abuse
terms. Make the fallback **visible and disclosed** — students should be able to see which
brain they are talking to. It is also an excellent teaching moment about where data goes.

---

## 7. Safety

**Open guard models are weaker than people assume.** Recent benchmarking of open guard models
reports recall as low as 0.455 for ShieldGemma 2B and 0.333 for Llama Guard 12B — that is,
the majority of unsafe content missed — with the best performer around 0.84. Automated
attacks bypass guard-protected models at high rates, and teenagers jailbreak recreationally.
"I put a guard model in front of it" is a compliance prop, not a safety posture.

Design accordingly: choose **recall over precision**, put a deterministic keyword/regex crisis
filter *underneath* the ML classifier (a regex has no distribution to fall off), and assume
bypass. Ensure the consequence of a bypass is "a student saw something crude," not "a student
in crisis got harmful advice" — which means the crisis path must not depend on the same
classifier a jailbreak defeats.

**The two design moves that beat any filter:**

1. **Do not offer open-ended chat.** A task-scoped interface — fixed server-side system
   prompt, no persona, no cross-session memory, oriented to code explanation and completion
   rather than free-form conversation — removes most of the disclosure surface that creates
   a duty in the first place.
2. **Time-gate the endpoint** to school hours plus a supervised window. LAN-only siting does
   most of this for free.

**The crisis path.** On a self-harm or abuse classification, return no completion — return a
fixed, human-written card with local resources (Telefonseelsorge 0800 111 0 111; 116 117; US
988; Military Crisis Line 988 press 1; the counsellor's name and hours), without moralizing.
If you alert at all, alert with **pseudonym and timestamp only**, so you cannot read a minor's
disclosure while standing in a supermarket, and route into an existing counsellor process
agreed in writing beforehand. In context (C) no such process exists, which is the strongest
argument for an explicit parent-facing escalation path in the consent pack.

**A correction on the EU AI Act, because the first-pass analysis got this wrong and it
mattered.** Article 5(1)(f)'s prohibition on inferring emotions in education institutions is
scoped by the Article 3(39) definition, which requires inference "on the basis of biometric
data." The European Commission's guidelines on prohibited practices state directly that
inferring emotions from written text falls outside the prohibition. **A text-based crisis
classifier is not the prohibited artifact.** Separately: Annex III high-risk deployer
obligations were **postponed from 2 August 2026 to 2 December 2027** by Regulation (EU)
2026/1744, in force 27 July 2026. Article 5 prohibitions are unaffected and have applied
since February 2025, as has the Article 4 AI-literacy duty, which reaches teachers.

The component that plausibly *does* touch Annex III 3(b) ("evaluate learning outcomes") is
not the safety classifier at all — it is any auto-grader that scores student work. Design that
one conservatively, or keep grading human.

---

## 8. The 4-Week Unit

**Grade the ownership, not the app.** The best available controlled evidence — a single
unreplicated preprint on adults, so treat it as a hypothesis rather than a finding — compared
unrestricted AI use against an "explanation gate" and found near-identical shipped output but
a large gap in ability to repair injected bugs afterward. It also roughly *doubled*
time-on-task. Plan for both effects.

**Week-by-week**, with a warning attached: this arc is sized for one section. A high school
teacher has four to six sections and 120–160 students, and Week 4's individual defenses at
eight minutes each become roughly twenty hours of one-on-one contact across a full load. **For
a full teaching load, either run it in one section, or halve the assessment ritual.**

- **Week 0 (teacher).** Build the exemplar end-to-end and *time it* — if it takes you more
  than three hours, the scope is too big. Confirm device image and network reachability. Write
  the Week 4 bug archetypes. Run the guardrail false-positive pilot. **Budget explicit class
  time for prerequisites** — git, a terminal, what a file is — because in FCS, English, art
  and PE these are not assumed knowledge, and the original plan budgeted zero.
- **Week 1 — spec, no code generation.** One page: who it's for, the single computation, the
  data model on paper, a wireframe, five to eight plain-language acceptance criteria. Teach
  *interrogative* prompting ("why does this work?") over *directive* ("build me X"). Code
  generation unlocks when the spec passes a short conference whose only purpose is shrinking
  scope.
- **Week 2 — build with the gate.** No generated block over a few lines enters the repo until
  the student explains it in their own words, as a commit-message field plus a short
  teach-back. Sample the blocks; gating all of them makes the friction the unit.
- **Week 3 — AI off.** Implement one feature by hand, write one test that fails before and
  passes after, keep an iteration log. This is the week to teach debugging. Be honest that
  this is an honour-code condition backed by observable artifacts, not an enforceable state —
  students have phones.
- **Week 4 — break, fix, defend.** Peer bug injection from a published archetype list, on a
  branch, with a teacher-authored fallback ready. Then a short defense and an ungraded
  showcase.

**Assessment weighting:** spec 15% · comprehension 25% · manual modification plus a
student-written test 20% · break-and-fix 20% · iteration log and AI-use disclosure 10% ·
artifact meets its own acceptance criteria 10%. The point is that **cheating does not pay** —
no detector, no accusation, no appealable false positive. A student who prompted their way
through scores near zero on most of the grade automatically.

**Three things the first draft missed and a real classroom will not:**

- **A non-AI track.** In any class of thirty, at least one family will decline AI use. Have
  the alternate assignment written before you need it.
- **Mid-year mobility.** In DoD schools especially, students arrive and depart mid-unit. A
  four-week individual capstone needs an explicit on-ramp and off-ramp.
- **Equivalent modes.** Offer the teach-back and defense as live, screencast, or written
  *universally*, plus an untimed equivalent of the break-and-fix. A timed one-period task is
  exactly what an extended-time accommodation exists for.

### Per-subject projects

The column that matters is not "why AI can't do this" — an LLM can fabricate any of it
competently. It is **what the teacher must require** so that automation stops being a
shortcut.

| Subject | Project | Learning objective | What the teacher must require |
|---|---|---|---|
| **FCS** | Per-serving cost calculator over a real local price list, with recipe rescaling | Unit-price comparison, proportional scaling | Prices collected as fieldwork, with receipts or photos |
| **English** | Revision tracker flagging the student's *own* documented weaknesses | Revising for concision and syntactic variety | The rule set derived from real returned feedback, cited |
| **Social science** | Primary-source analyzer exporting a corroboration/conflict table | Sourcing, contextualization, corroboration | The student's own judgment of which sources conflict, defended orally |
| **Art** | Offline portfolio PWA — works, medium, artist statements, filterable | Portfolio curation and statement writing | Original works and original statements; the app is the frame |
| **PE / Health** | FITT plan generator from a measured personal baseline | The FITT principle, progressive overload | A measured baseline, hand-encoded progression rules, teacher sign-off, non-medical-advice disclaimer |
| **CS** | Model comparison harness: same prompts to a cloud model and the Beelink, scored on a student rubric | Systems evaluation and AI literacy | Makes the local model an object of study — its slowness is the finding, not the obstacle |

---

## 9. App Shape and Deployment

**Ship a no-build, local-first, installable PWA.** Five files: `index.html`, `app.js`,
`style.css`, `manifest.webmanifest`, and — only in Week 4 — `sw.js`. No npm, no bundler. A
managed Chromebook may have no Node at all; a small open-weights model generates one-file HTML
far more reliably than multi-file framework scaffolding; and a novice can see the whole
program at once in DevTools.

**Leave the service worker until Week 4.** Install criteria are HTTPS plus manifest fields plus
an engagement heuristic — no service worker required — and adding one early buys offline
caching at the cost of the most demoralizing beginner failure mode there is: "I pushed my
change, reloaded, and nothing happened."

**Native is out of scope, and say so in Week 0 with the reason.** Apple Developer enrollment
requires the legal age of majority and the educational fee waiver requires a legal entity;
Google Play requires 18+. The age bar is the wall, not the testing rules. Demo an installed
PWA on day one — the felt difference is much smaller than the imagined one.

**Data: `localStorage`, with an export button as a graded Week-1 requirement.** A few MiB per
origin covers every realistic project. Eviction is all-or-nothing, and school devices get
reimaged, so the export button is the actual durability story. Call
`navigator.storage.persist()`. Note the archive trap: a PWA opened via `file://` loses its
service worker and manifest, so the end-of-unit handoff must include a way to serve it, not
"double-click index.html."

**One hard rule: student apps never call an LLM at runtime.** The AI helps build the app; it is
not a dependency of the app. This single decision eliminates key management, key leakage in a
public repo, per-student cost, runtime moderation exposure, and the most common reason a
project breaks a year later.

**Repos and hosting.** GitHub's 13+ floor is the most permissive of the hosts, and GitHub
Education explicitly covers K-12 students. **Time-sensitive:** GitHub Classroom sign-ups closed
in May 2026, the service retires **28 August 2026** — eleven days after this document's date —
and remaining data is deleted **4 September 2026**. Do not build on it. Provision repos with a
short `gh` CLI script; Codio and Classroom 50 are the named successors if you want a platform.
Note also that free-tier Pages publishes from public repos, and even GitHub Team publishes a
*public* site from a private repo — so require pseudonymous repo names, forbid real names,
photos, and location in committed content, and make the publish decision deliberately.

**On Codespaces:** the free allowance is smaller than it looks. Twenty core-hours is ten
wall-clock hours on a default two-core machine, less than the unit's own class time, and
codespaces bill while running rather than while typing. Also confirm the billing entity —
organization-owned repos may bill the organization rather than draw on students' personal
quotas. Treat browser dev environments as a convenience, not the plan.

---

## 10. Failure Modes

| Failure | Required plan-B |
|---|---|
| **The teacher is out sick** — the highest-probability outage, and the one the first draft omitted | A runbook a substitute can execute, a second admin, and a no-AI lesson variant that does not require you |
| **Beelink GTR9 Pro v1 board NIC defect** (documented instability under network load; later revisions differ) | `lspci \| grep -i ethernet` before anything else. Five minutes, gates everything |
| **ROCm/gfx1151 instability** (open reports of output degrading after several turns) | Pin kernel, ROCm and serving stack; freeze updates for the unit; systemd auto-restart plus an external canary probing end-to-end |
| **Synchronized burst** — one instruction produces thirty cold prefills | Stagger prompts, pre-warm slots, surface queue position. **Note:** a gateway's per-key parallel limit typically returns HTTP 429 rather than queueing, and agentic clients retry on 429 — so that setting *amplifies* a burst unless you add real queueing |
| **Mid-class outage** | Cloud failover configured from day one *and disclosed*; plus a printed no-AI variant of every lesson — and cost that writing, because it is twenty lesson plans written twice |
| **Guardrail bypassed** | Certain eventually. Ensure the crisis path does not depend on the classifier a jailbreak defeats |
| **The endpoint becomes a homework oracle for other classes** | Not technically solvable. Surface it to whoever is responsible before deployment rather than being discovered |

---

## 11. Cost and Time

**Electricity is a rounding error.** Measured draw is roughly 16–25 W idle and 125–128 W under
heavy inference. A 20-day unit at ~20 W idle plus five hours a day of incremental load is
about **20 kWh**, or roughly **€7.50** at current German rates. (The first-pass figure of 29
kWh / €11 was inconsistent with its own inputs — corrected here.) The point is the argument,
not the line item: **compute cost was never the constraint**, so a cloud fallback tier should
simply be bought.

**Setup:** roughly 25–40 hours for the portal, quotas, moderation, repos, exemplar project and
consent pack — less if the `upskill-news` skeleton is reused aggressively, which is the
strongest argument for doing so. **Weekly ops during the unit:** 4–10 hours, peaking in Week 4,
plus alert triage, which is unmeasured and is the number that decides everything.

**Compatible with a full-time job?** For 6–10 students, yes — roughly 4–6 hours a week during
the four weeks. For a full teaching load of 120–160 students, no, not as specified. And the
comparison that should govern the decision: thirty students' worth of tokens on a hosted model
for four weeks is tens to low hundreds of euros, while the compliance work around a
self-hosted alternative is weeks of your time. **The only thing that justifies the local leg is
a capability nothing else provides** — under-18 agentic coding — which brings us back to the
one untested assumption.

---

## 12. Verify These First

| # | Question | How to settle it |
|---|---|---|
| 1 | **Can a local 27B actually drive a multi-file agentic loop?** The whole premise rests on this. | One afternoon: point an agent at a real repo against `qwen3.8:27b` and see whether it completes multi-file tasks reliably. If it can't, the plan is cloud-only and everything else is moot. |
| 2 | **Per-student wall-clock for a complete agentic task at realistic concurrency** | Synthetic concurrent load test. If a student can't finish one run in a period, the tier fails on latency. |
| 3 | Is this unit an affected board revision? | `lspci \| grep -i ethernet`. Five minutes. |
| 4 | Real prefill/decode and multi-slot behaviour on this unit, ROCm vs Vulkan | `llama-bench` plus concurrent load. Every capacity number here is third-party-calibrated. |
| 5 | Guardrail false-positive rate on realistic teen prompts | Run the chain over 200–500 synthetic prompts (creative writing with violence, health topics, game design, lyrics, genuine distress). One evening. **This is the go/no-go on your time budget.** |
| 6 | Can the notary corpus move off this machine? | If not, students need different hardware. Non-negotiable. |
| 7 | Ethics-counsel read on the UG/federal-employment question, for the actual fact pattern | Agency ethics counsel, not a web search. |
| 8 | Are Crostini and PWA install permitted for the student OU? | One email to the school's IT office; both are admin-gated. |

---

## Sources

**Vendor policy** — [Anthropic Consumer Terms](https://www.anthropic.com/legal/terms) ·
[Usage Policy](https://www.anthropic.com/aup) ·
[Guidelines for organizations serving minors](https://support.claude.com/en/articles/9307344-responsible-use-of-anthropic-s-models-guidelines-for-organizations-serving-minors) ·
[Age assurance](https://support.claude.com/en/articles/15171100-age-assurance-on-claude) ·
[Claude for Teachers](https://www.anthropic.com/news/claude-for-teachers) ·
[GitHub ToS](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) ·
[GitHub Education](https://education.github.com/pack/join) ·
[GitHub Classroom retirement](https://github.com/orgs/community/discussions/196615)

**Law and governance** — [34 CFR 99.31](https://www.ecfr.gov/current/title-34/subtitle-A/part-99/subpart-D/section-99.31) ·
[FAR Subpart 3.6](https://www.acquisition.gov/far/subpart-3.6) ·
[18 U.S.C. § 208](https://www.law.cornell.edu/uscode/text/18/208) ·
[DoDI 8510.01](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/851001p.pdf) ·
[AI Act Art. 3](https://artificialintelligenceact.eu/article/3/) ·
[Art. 5](https://artificialintelligenceact.eu/article/5/) ·
[Annex III](https://artificialintelligenceact.eu/annex/3/) ·
[FPF on the emotion-recognition prohibition](https://fpf.org/blog/red-lines-under-eu-ai-act-unpacking-the-prohibition-of-emotion-recognition-in-the-workplace-and-education-institutions/) ·
[GDPR Art. 35](https://gdpr-info.eu/art-35-gdpr/)

**Hardware and serving** — [Strix Halo performance tracker](https://llm-tracker.info/AMD-Strix-Halo-(Ryzen-AI-Max+-395)-GPU-Performance) ·
[AMD ROCm Strix Halo optimization](https://rocm.docs.amd.com/en/docs-7.2.0/how-to/system-optimization/strixhalo.html) ·
[LiteLLM users and budgets](https://docs.litellm.ai/docs/proxy/users) ·
[Ollama FAQ (defaults)](https://docs.ollama.com/faq)

**Safety and pedagogy** — [Qwen3Guard](https://qwenlm.github.io/blog/qwen3guard/) ·
[CSTA Standards](https://csteachers.org/standards/) ·
[ISTE Standards for Students](https://iste.org/standards/students) ·
[UNESCO AI Competency Framework for Students](https://www.unesco.org/en/articles/ai-competency-framework-students)

**Deployment** — [Chrome install criteria](https://web.dev/articles/install-criteria) ·
[Storage quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria) ·
[Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces) ·
[GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)

---

*Produced by a six-dimension research workflow with per-dimension adversarial verification and
a hostile review pass. The review falsified several claims in the first synthesis — the
electricity arithmetic, the EU AI Act emotion-recognition analysis, a gateway rate-limit
mechanism, and a four-model memory budget that did not close — and those corrections are
folded in above. Where a claim could not be verified, it says so.*
