# Beelink × Upskill News — Indexing & Production Plan

> **Date:** 2026-08-15 · **Branch:** `claude/beelink-upskill-news-indexing-anq2li`
> **Status:** Decision record + build plan, for owner review. Nothing here is built yet.
> **Method:** 13-agent exploration — 4 repo readers (beelink-bonus, patterns,
> upskill-news-app ×2), 2 web researchers (index-as-asset economics; Strix Halo
> serving practice, mid-2026), 4 competing designs from different lenses, and a
> 3-judge panel (engineering feasibility / revenue realism / ops-passivity).
> Plus a survey of the freshly-cloned canonical `vilseckki-datafactory-app`.
>
> **Companion docs:**
> `BEELINK-PROTOTYPE-RUNBOOK.md` (**execution checklist for Phases 0–2** — added
> 2026-08-15 evening; **supersedes this plan's fleet assumptions**: beeteam is now
> Ubuntu-primary with Claude Code on the box, the dev Mac is a new M5 Air without
> Tailscale, the old tailnet topology is defunct) ·
> `upskill-news-app/docs/BEELINK_FACTS_INDEX.md` (app-side integration contract) ·
> `patterns/docs/research/BEELINK_INDEX_ASSET_RESEARCH.md` (market + hardware research, with sources) ·
> patterns idea **#110** (Verified Education Facts Ledger + Change Feed).

---

## 0. TL;DR

**Decision:** Run the Beelink as the **Upskill Newsroom Server** — the single
production backend for upskill-news-app — with a persistent, provenance-stamped
**Verified Facts Store** (the "search index") underneath it. The index is the
accuracy moat under the newsletter product *first*; selling it (feed/licensing)
is a deliberately deferred option behind a dated kill gate. The VilseckKI
Notarin RAG pilot is carried as a **separate, owner-gated parallel track** that
shares the hardened box but never sits on upskill-news's critical path.

**Why this configuration won a 4-design judge panel (§4):** it has the smallest
gap between claimed reuse and code that verifiably exists, the only mechanically
credible low-touch steady state (batch-only box, no synchronous customers on
residential hardware), and every documented failure mode of this specific
machine has a specific countermeasure. Total scores: Newsroom 22 / Ledger 20.5 /
Bergfried 16.5 / Indexwerk 16 (of 30).

**The five moves, in order:**
1. **Phase 0** — make the machine trustworthy: Ubuntu default boot (self-healing),
   NIC-defect gauntlet, correct GPU config, first-ever benchmark of this unit,
   regwatch deployed, doc corrections (§3).
2. **Phase 1** — the Verified Facts Store (Postgres 16, four tables incl. a
   change-history layer) + the Newsroom Runner skeleton inside upskill-news-app.
3. **Phase 2** — kill the fixtures: Scorecard bulk, VA GI Bill feed, real
   admissions-page extraction; free weekly GI-Bill/deadlines changelog starts.
4. **Phase 3** — cloud edge go-live (owner-gated: Clerk/Supabase/Resend + the
   GDPR token infra hard stop).
5. **Phase 4** — two shadow cycles → 1–2 pilot IECs → first $99/mo conversions.

---

## 1. "Search indexes," explained (the fuzzy concept, made concrete)

A **search index** is a precomputed data structure over a corpus that makes
retrieval cheap. Three classic forms — **inverted index** (keyword/BM25: what
Postgres FTS, Meilisearch, Typesense serve), **vector index** (embeddings +
approximate-nearest-neighbor: semantic similarity), and **hybrid** (both +
rerank). There is a fourth form that matters most here: a **facts ledger** — a
structured store of *extracted facts*, each row carrying its source URL,
retrieval timestamp, and a verification verdict. That is what "indexing" means
when the promise you sell is *freshness and verifiability*, not text recall.

**The economics are asymmetric, and they are the whole strategy.** *Building*
an index (crawl politely, parse, extract, verify, embed) is the expensive,
recurring side. *Serving* a niche index is nearly free — 128GB holds 10–30M
full-precision vectors, far beyond any vertical's needs. Web scale inverts
this (serving ~3B embeddings: $21K–155K/month), which is why web-scale search
is closed to solo operators.

**Your Beelink's economic edge is therefore the BUILD side:** ~€15–25/month of
electricity buys unlimited overnight LLM extraction and verification labor that
would cost hundreds per month in cloud APIs. Build at home; publish compact
artifacts or serve consumers over the tailnet; never serve strangers from the
residential line.

**"Index as an asset" — who actually makes money** (full sourcing in
`patterns/docs/research/BEELINK_INDEX_ASSET_RESEARCH.md`):

- **Web-scale search APIs** (Exa, Brave): VC territory. Closed.
- **Hosted search infra** (Algolia-class): price-war territory. Closed as a
  product; open as a *service wrapper* — that's VilseckKI RAG-as-a-Service.
- **Indie general-purpose search** (Marginalia, Mwmbl, Stract): all
  grant/donation-funded. A warning, not a model.
- **Niche vertical data** — verified, fresh, provenance-stamped: **the open
  tier.** Peterson's licenses college data to counselor tools; CollegeAI sells
  a university-data API at near-solo scale; IECs pay $66–219/mo
  (CollegePlannerPro) and ~$110/student/yr (College Kickstart) for tools whose
  core value is current admissions data. Peterson's refreshes ~4×/year; a
  weekly primary-source verification cadence is structurally fresher.
- Bonus for an EU operator: an index built with substantial verified investment
  earns **sui generis database protection** — one of the few IP moats a solo
  data business can own. And German §44b UrhG permits commercial TDM of
  lawfully accessible works (honor machine-readable opt-outs; extract facts,
  never republish text).

**Honest ceiling** (corrected 2026-08-15 — the first draft counted IECA alone):
the organized core is ~2,800 IECA + ~2,000 HECA members, plus regional
associations and a largely unaffiliated majority — several times the IECA
figure in total — but platform buyers still number <10. As a *product*, the
index remains a niche, not a venture API. These counts fluctuate and are not a
lever we control: sized once here for calibration, not for ongoing tracking —
don't re-litigate them. As the *moat under Upskill News* — the defense against the #1 churn
driver (confidently-wrong facts) — it is load-bearing regardless. That is why
the plan builds it for internal use first and sells it only if a dated demand
probe (§8) says so.

**You already invented this once.** `docs/EU-AI-ACT-RAG-CORPUS-PLAN.md` (this
repo) is a complete index-as-product plan — pre-embedded regulatory corpora at
€79–299 — whose demand anchor (the Aug 2, 2026 AI-Act deadline) has now passed
unlaunched. Its 5-stage pipeline (acquire → chunk → embed → QA → package)
remains the reusable template; this plan redirects the concept at the one
vertical where you own a code-complete product and a warm channel.

---

## 2. What you already have (the convergence)

The striking finding of the asset sweep: **every serious document in the
portfolio already assumes this architecture — nobody ever built it.**

| Asset | Where | Status | Role in this plan |
|---|---|---|---|
| Verification-first pipeline (crawl → consensus → freshness SLAs → compose → QA → gate), React-free, 694 tests | `upskill-news-app/lib/pipeline/` | **Working library, zero runners** — `generateEditionForClient` has no call sites | The engine. Reused unchanged; the Beelink gives it a scheduler, persistence, and an LLM |
| "Verified Facts Database" shared-infrastructure diagram ("One crawl. One verification. Two apps updated.") | `upskill-news-app/docs/LOCAL_LLM_ARCHITECTURE.md` | Diagram only | This plan builds it (§5) |
| Confirmed production model: Qwen3.5-122B-A10B via official `ollama run qwen3.5:122b`, working on this unit incl. vision (2026-07-08, do-not-relitigate) | same doc | Decided | The compose/extraction engine; serving binary decided by benchmark (§3) |
| Backlog items **B1–B4** (runner, scheduler, live sources, local compose) | `upskill-news-app/docs/IMPROVEMENT_PLAN.md` | Named, unbuilt | Phases 1–3 = exactly B1–B4 |
| RegWatch change detection (changedetection.io + Flask + Ollama triage), **already carrying `watches/upskill_news.yaml`** + triage prompt + `GET /api/changes/{product}` | `regwatch/` (this repo) | **Working code, never deployed** | Freshness trigger; deployed in Phase 0 as the first unattended service |
| Court scrapers (httpx+bs4, rate limiting, resume) | `court-scraper/` (this repo) | Working CLI code | Politeness/resume machinery to port into the admissions crawler |
| EU AI Act corpus plan (5-stage index pipeline, QA harness, packaging, Lemon Squeezy) | `docs/EU-AI-ACT-RAG-CORPUS-PLAN.md` | Plan only; deadline anchor passed | Pipeline template; evergreen corpora (GDPR/Steuerrecht/UK SEND) stay a deferred option |
| "Festung Franken" serving shell (Hetzner gateway + Tailscale + Beelink, zero public ports, ~€33/mo) | `VILSECKKI-FINAL-ARCHITECTURE.md` | Architecture only | Deployment shell for any future client-facing serving; not on this plan's critical path |
| VilseckKI GTM: Notarin pilot plan, €49–349/mo tiers, capacity math, passive-ops checklist, 6 legal blockers | `BEELINK-PASSIVE-REVENUE-STRATEGY.md`, `VILSECKKI-IMPLEMENTATION-PLAN.md`, `CLAUDE.md` | Plans + a real relationship | Parallel Track B (§7) |
| Data Factory production patterns | `../vilseckki-datafactory-app/` (canonical repo; surveyed 2026-08-15) | Working, 1,266 passing tests | **Reuse:** `scrapers/health_check.py` + `auto_checker.py` (preflight/cron health), `scripts/ollama_models.py` (model-residency manager), `generators/ollama_augmenter.py` (async client w/ retry), `validators/blind_extractor.py` (blind-verifier pattern for extraction QA), `cron/nightly-run.sh` (lockfile/8h-cap/rotation), `fine-tuning/docs/BEELINK-RUNBOOK.md`, `scrapers/SCRAPER-PATTERNS.md`, `regupdate/` temporal-drift design. **Absent there:** any embedding/vector code, and the old `BaseScraper` abstraction was *not* carried forward (four hand-rolled copies exist) — the runner should use registry-based source dispatch, not copy the hardcoded if-chain |
| Patterns-repo prior art | `patterns/docs/BEELINK-AS-PRODUCTION-ASSET-STRATEGY.md` (Stream 1 = corpus products), `patterns/local-scraper-webapp/` (Flask ops shell for overnight scrapers), `config-to-voice-briefing/`, ideas #37/#89/#95/#100 | Docs + patterns | Superseded/extended by this plan; #110 filed as the new idea |
| Fleet ops record | `patterns/reference/machines.md` (beeteam, Tailscale FQDN/IP, Mutagen, `OLLAMA_HOST=http://beeteam:11434`) | **Stale: Windows-only, 2026-03-15** | Updated in Phase 0 *with measured state*, not guesses |
| Funding research (€117.5K–156.5K realistic stack; Digitalbonus 2.2 for UPS/NAS/firewall; BayTOU gated on Haupterwerb switch) | `docs/FUNDING-TRACKER.md` + companions | Dated Mar–Apr 2026 | Parallel Track C: re-verify, then fund the resilience hardware (§7) |

**The three gaps every asset shares:** a persistent store, a scheduler, and
deployment. That is why one hardening pass + one Postgres schema + systemd
timers unlocks the whole portfolio's Beelink ambitions at once.

---

## 3. Corrections to the record (do not build on these errors)

Surfaced by mid-2026 web research (sources in the patterns research doc) and
the repo sweep. This repo's `CLAUDE.md` has been corrected in this same change.

1. **`HSA_OVERRIDE_GFX_VERSION=11.0.0` is wrong for this chip.** Strix Halo's
   iGPU is **gfx1151**; 11.0.0 spoofs gfx1100 (RDNA3 dGPU) and can force
   mismatched kernels. Use **11.5.1** with Ollama (v0.18+), or no override at
   all with native-gfx1151 ROCm 7.x builds.
2. **The speed table was wrong in both directions.** Dense 70B Q4 runs ~5 tok/s
   (bandwidth-bound: ~212 GB/s measured), not 8–15; 7B runs ~50, not 80–120.
   And the table missed the machine's real strength: **100B+ MoE at 40–55 tok/s**
   (gpt-oss-120b ~48–55; 30B-A3B-class ~100; Qwen3.5-122B-A10B ~25–40 per the
   upskill-news measurement). MoE is the sweet spot; prompt *prefill* is the
   weak side (long-document latency).
3. **Ollama underperforms on this platform** (~56% tok/s gap vs standalone
   llama.cpp Vulkan; its Vulkan backend hangs on Qwen3.5-class models — never
   set `OLLAMA_VULKAN=1`). Production serving binary is a **Phase 0 benchmark
   decision**: Ollama/ROCm vs `llama-server` (Vulkan) — the app switches via
   `OPENAI_COMPAT_BASE_URL` with zero code changes.
4. **The headline 24/7 risk is this exact box's NIC.** The GTR9 Pro's Intel
   E610-XT2 dual 10GbE has a firmware-level deadlock under sustained
   GPU+network load, on Windows **and** Linux, only partially fixed by
   NVM 1.30 / BIOS 1.08 as of latest evidence. Mitigations are mandatory
   Phase 0 gates (§6). Thermals are *not* the risk on this platform; the NIC is.
5. **Cloudflare Tunnel decrypts at Cloudflare's edge.** For Notar/legal client
   data that breaks the §203/DSGVO pitch outright. The long-open "Tailscale vs
   Cloudflare Tunnel" question is resolved: **private Tailscale tailnet** for
   anything confidential; Cloudflare only ever for a public marketing site.
6. **Context caps are a safety rule:** 200K+ contexts on large models can
   exhaust kernel memory and crash the whole box. Cap 24/7 serving at ~64K.
7. **Company founding year:** 2025 (Gesellschaftsvertrag 25.07.2025, HRB 8114
   Amberg) — `GRANT-APPLICATION-PLAN.md` / `FUNDING-PROJECT-INSTRUCTIONS.md`
   say ~2024 and must not be copied into applications.
8. **The EU AI Act corpus plan's demand anchor (Aug 2, 2026) has passed**
   unlaunched. The pipeline design survives; the demand section doesn't.
   Evergreen corpora (GDPR, Steuerrecht, UK SEND) are the refresh path — later.
9. **This unit has never been benchmarked.** The results log in
   `mistral/open-source-models/BEELINK-FIT.md` is empty. Every throughput
   number above is community-sourced; Phase 0 measures before anything is
   promised to anyone.
10. **`patterns/reference/machines.md` still documents Windows 11 only** —
    update with measured Ubuntu state in Phase 0 (same session as the
    hardening, per that repo's DEV-LOG protocol).

---

## 4. The four designs and the verdict (decision record)

Four designers worked from the same intelligence dossier under different
lenses; three judges scored all four (1–10 per lens).

| # | Design | One-liner | Feas. | Rev. | Ops | Σ/30 |
|---|---|---|---|---|---|---|
| 1 | **Upskill Newsroom Server** | Beelink = upskill-news's production backend; the index exists to make the product accurate | **8** | 6 | **8** | **22** |
| 2 | Education Facts Ledger | The index IS the asset: crawl+verify+version education facts; newsletter is consumer #1, feed/licensing #2 | 7 | 7 | 6.5 | 20.5 |
| 3 | Bergfried (shared substrate) | One Postgres+Ollama+FastAPI substrate; upskill-news and VilseckKI clients as tenants | 5 | 7.5 | 4 | 16.5 |
| 4 | VilseckKI Indexwerk (passive ladder) | Four sequenced rungs ordered by human-minutes/month: corpora → RAG client → index → newsletter | 5.5 | 5 | 5.5 | 16 |

**Why Newsroom won:** smallest verified gap between plan and existing code
(runner *inside* upskill-news-app — decisive, since the pipeline imports via
the `@/` alias and cross-repo consumption would need packaging work the other
designs hand-waved); correct negative scope (no vector DB — nothing in the
pipeline contract consumes embeddings); the only steady-state claim the ops
judge found mechanically credible (batch-only box, no synchronous customers,
a down day delays a batch instead of breaking a client); and a config-only
fallback for the one big unproven dependency (serving throughput).

**Why the others lost (and what was taken from each):**
- *Ledger* (best technical idea on the panel: the change-history layer; best
  honesty: 2–3 hrs/week maintenance, dated kill gates) lost on building a
  second product — feed packaging, Hetzner edge, checkout, support — before
  the first product has a user. **Grafted:** `change_events` layer, free weekly
  GI-Bill/deadlines changelog, structured-sources-first sequencing, two-tier
  extraction, IPEDS unitid in the crosswalk, kill gates, verified restores.
- *Bergfried* (revenue judge's winner — the Notarin is the portfolio's only
  named warm customer, and it sequences the uncompressible §203 legal track
  from week 1) lost on platform-before-product: a 100% net-new FastAPI
  substrate, and daytime synchronous client serving that turns a solo parent's
  batch asset into an on-call obligation on a no-ECC box with a documented NIC
  defect. **Grafted:** the Notarin pilot as parallel Track B with the legal
  track started early; systemd `MemoryMax` guardrails; single-datastore
  doctrine; the quarterly maintenance calendar; the walk-away runbook.
- *Indexwerk* (best passivity methodology: per-rung human-minute budgets with
  a shed rule; best resilience posture: external watchdog + offsite restic)
  lost on five product lines, two serving stacks, two vector stores, and
  scheduling the portfolio's only code-complete product last. **Grafted:** the
  minute-budgets + shed rule, UptimeRobot-over-Uptime-Kuma, offsite backups +
  restore drills, regwatch deployed first, regwatch triage pointed at the main
  LLM endpoint (one fewer resident model), grant re-verification before any
  hardware purchase, the plain-language index explainer (§1).

---

## 5. The synthesized architecture ("Newsroom + Ledger")

One box, four layers, batch-first. Full app-side contract in
`upskill-news-app/docs/BEELINK_FACTS_INDEX.md`.

**Layer 0 — Platform (always-on):** headless Ubuntu 24.04 LTS, default boot
with self-healing boot order; Tailscale-only access (beeteam); BIOS
auto-power-on; TDP capped ~85–100W (NIC-deadlock trade); GTT kernel params
exposing ~110GB to the GPU; unattended-upgrades.

**Layer 1 — Inference (always-on):** one LLM service — Ollama/ROCm
(`HSA_OVERRIDE_GFX_VERSION=11.5.1`, `OLLAMA_FLASH_ATTENTION=1`) **or**
`llama-server` Vulkan, decided by the Phase 0 benchmark — serving
`qwen3.5:122b` (~90GB resident; keep-alive tuned on measured duty cycle);
context cap ~64K; sequential jobs only (the regwatch queueing doctrine).
Candidate second string, loaded only in the night window if the extraction
benchmark justifies it: a 30B-A3B-class MoE for bulk page extraction
(~3–5× faster), with 122B escalation for hard cases and CDS-PDF vision.

**Layer 2 — Verified Facts Store (always-on): the index.** PostgreSQL 16
(`MemoryMax` guarded, shared_buffers capped), tailnet-only:
- `fact_candidates` — append-only, exactly the pipeline's `FactCandidate`
  shape (value, numericValue, unit, academicYear, sourceTier, sourceName,
  **sourceUrl**, **retrievedAt**, agent) — the fields consensus requires to
  award `verified`;
- `fact_history` / `change_events` — diffs computed at ingest ("UC Davis moved
  its deadline from Jan 5 → Dec 15, detected {date}, prior value, source") —
  the compounding layer no competitor can backfill;
- `crawl_runs` — fetch log driving freshness-SLA due-sets;
- `schools` — ~6,000-institution crosswalk (names, aliases, `scorecard_id`,
  IPEDS `unitid`, ranks) replacing the app's 60-school fixture.
No PII by construction. No vector layer until a named consumer exists.
Append-only guard triggers (pattern from the app's Supabase migrations).

**Layer 3 — Newsroom Runner (scheduled, systemd timers, `Persistent=true`):**
a CLI package in `upskill-news-app/server/runner/` importing the React-free
pipeline barrel. `runner crawl` nightly (SLA-driven due-set → fetch → extract →
store + diff); `runner generate` biweekly (~1–1.5h per 15-client batch;
outbox-dir handoff until the cloud edge exists, then Supabase service-role
writes + `pipeline_runs`/`adapter_usage` telemetry the admin ops dashboard
already renders); `runner tts` post-approval (ElevenLabs). Sidecar: **regwatch**
(Docker) with its existing `upskill_news` watch list; the runner polls
`GET /api/changes/upskill_news` for targeted recrawls; triage calls the main
LLM endpoint (no separate 8B model). Weekly timer emits the **free GI-Bill +
deadlines changelog** (markdown/JSON from `change_events`) — the zero-touch
demand probe and pilot-recruitment artifact.

**Ops spine:** Uptime Kuma on-box + **UptimeRobot watching the watcher** +
healthchecks.io dead-man pings on every timer; morning exception digest through
regwatch's notify path; nightly `pg_dump` + restic **offsite** (Hetzner Storage
Box) + monthly restore drill; smart plug for remote hard power-cycle; quarterly
maintenance calendar (re-soak NIC after firmware updates, re-benchmark after
major llama.cpp/Ollama upgrades, docs updated same-session); a one-page
walk-away runbook executable from a phone over Tailscale.

**RAM budget (128GB):** 122B resident ~90GB · Postgres 2–4GB · regwatch stack
~1GB · Uptime Kuma ~0.2GB · OS ~2GB → **~30GB deliberately unallocated.** Never
a second large model resident.

**Cloud edge (not on the Beelink):** the Next.js app + Clerk + managed
Supabase + Resend, per `upskill-news-app/docs/HANDOFF.md` §3. Stripe and US
managed cloud are fine for *this* product line — the zero-US-dependency rule is
VilseckKI brand doctrine, not Upskill's. The Beelink never serves public HTTP.

**What is deliberately NOT in scope (with reactivation triggers):** vector/
embedding layer (trigger: a real semantic consumer — VilseckKI tenant or
program-matching feature); paid feed/licensing product (trigger: §8 gate);
corpus products (trigger: Newsroom steady-state + refreshed demand evidence);
interactive client serving from the box (trigger: Track B owner decision);
fine-tuning (standing rule: not before 10+ clients).

---

## 6. Phase 0 — Machine runbook (1 weekend + 1–2 evenings)

The gate for everything else. Order matters.

**Boot & recovery**
1. In Windows (one last visit): `powercfg /h off` (Fast Startup breaks boot
   handoff, locks NTFS, defeats WoL); apply BIOS ≥1.08 + Intel E610 NVM ≥1.30;
   check bbs.bee-link.com thread 7762 + Intel E610 release notes for any 2026
   firmware that finally fixes the deadlock.
2. BIOS: **Restore AC Power Loss = Power On** (menu path undocumented for the
   GTR9 Pro — find it and record it in `machines.md`); TDP cap ~85–100W; UMA
   carve-out to minimum (512MB–2GB); IOMMU stays **on**.
3. Ubuntu: `sudo efibootmgr -v` → note entry IDs; `sudo efibootmgr -o
   <ubuntu>,<windows>`; `/etc/default/grub`: `GRUB_DEFAULT=saved`,
   `GRUB_SAVEDEFAULT=true`, os-prober on; `sudo update-grub`.
4. Self-heal: oneshot `bootorder-assert.service` (re-runs the `efibootmgr -o`
   on every boot) — Windows updates are documented to re-steal BootOrder; this
   makes hijacks self-heal after one boot. Endgame (later): retire Windows to
   a VM and delete this failure-mode class.
5. Buy: smart plug (remote hard power-cycle), USB 2.5GbE NIC (~€25, fallback),
   external disk *and* Hetzner Storage Box for restic (see Track C for the
   grant-funded UPS/NAS upgrade path — but don't block on it).

**GPU & memory**
6. `GRUB_CMDLINE_LINUX += "amdgpu.gttsize=131072 ttm.pages_limit=31457280"`;
   reboot; verify ~110GB GPU-addressable.
7. LLM service env: `HSA_OVERRIDE_GFX_VERSION=11.5.1` (not 11.0.0; or none on
   native gfx1151 ROCm builds), `OLLAMA_FLASH_ATTENTION=1`, never
   `OLLAMA_VULKAN=1`, `OLLAMA_HOST=0.0.0.0:11434` firewalled to tailnet.

**NIC gauntlet (mandatory before any 24/7 promise)**
8. 4-hour soak: sustained generation loop + `iperf3` across the E610
   simultaneously. Lock-up ⇒ switch primary traffic to the USB NIC and log it.
   Re-run after every firmware update (quarterly calendar).

**Benchmark gate (fills the empty log in `mistral/open-source-models/BEELINK-FIT.md`)**
9. Measure and record: `qwen3.5:122b` decode + prefill (Ollama/ROCm **and**
   `llama-server` Vulkan — kyuz0 toolboxes); a 30B-A3B-class extraction model
   on real admissions-page prompts vs the 122B (quality + speed — decides
   two-tier extraction on evidence, not doctrine); bge-m3 embedding chunks/hour
   (CPU vs iGPU — sizes any future vector work); idle/load watts. **The serving
   binary and the batch-window math are decided here.**

**First unattended service + docs**
10. Deploy regwatch (`docker compose up -d` + systemd wrapper + healthcheck
    ping); confirm `watches/upskill_news.yaml` fires end-to-end. Cheapest
    possible proof the box runs something 24/7, and the change history starts
    accruing now.
11. Doc hygiene, same session: `CLAUDE.md` here corrected (done in this
    change); update `patterns/reference/machines.md` with *measured* Ubuntu
    state + DEV-LOG entry; session note in `log/`; supersede
    `TONIGHT-SETUP-CHECKLIST.md` with a pointer here.

---

## 7. Phases 1–4 and parallel tracks

Full app-side task detail lives in `upskill-news-app/docs/BEELINK_FACTS_INDEX.md`
§5; this is the machine/portfolio view. Time is evenings/weekends; honest
budget: the judges priced Phases 1–3 at 8–10 evening-weeks *optimistically*.

**Phase 1 — Facts Store + Runner skeleton (2–3 weeks)**
Postgres 16 install (tailnet-only) → four-table schema (append-only triggers;
`scorecard_id` + IPEDS `unitid` from day one) → `server/runner/` CLI in
upskill-news-app (`crawl`/`generate`/`tts`) → `FactsStoreSource` + history
wiring (zero changes to consensus/freshness/QA) → systemd timers
(`Persistent=true`, `RandomizedDelaySec`, `OnFailure=` alerts) → Uptime Kuma +
UptimeRobot + healthchecks.io → restic offsite + first restore drill → vitest
suites green. Reuse from the Data Factory repo: health-check/auto-checker
subsystem, `ollama_models.py` residency manager, `nightly-run.sh` lockfile
pattern, blind-verifier pattern for extraction QA.

**Phase 2 — Live data (3–4 weeks, structured sources first)**
`DATA_GOV_API_KEY` → Scorecard bulk pull (~6,000 institutions, 1,000 req/hr)
into `schools` + baseline facts → **VA GI Bill source** (unauthenticated,
versioned; the named best pilot fact type and the military-community
differentiator) → weekly changelog timer goes live → *then* the fragile part:
real admissions-page extraction (primary `.edu`/`.gov` only; robots + 3–5s
rate limits; port court-scraper politeness/resume; two-tier extraction per the
Phase 0 benchmark; written EDPB 03/2026 legitimate-interest assessment;
faculty/staff personal data excluded) → regwatch-triggered targeted recrawls →
**2-week measurement soak** (verified-share, conflicts, extraction error rate)
before any human sees an edition.

**Phase 3 — Cloud edge go-live (owner-gated; parallel to Phase 2)**
Execute `HANDOFF.md` §3 in order: Clerk instance + session-token
customization → **Supabase billing decision** (pending since 2026-07-14;
managed is correct for this line) → migrations applied *before* env vars →
Resend + DNS (the long pole — start early) → smoke test per
`SMOKE_TEST_MANUAL.md` → runner machine identity (service-role, Beelink-side
only) → **GDPR hard stop:** signed single-use-token infra for unsubscribe +
consent accept-link, plus the Art. 17 erasure runbook, before ANY real
recipient. Host the app on Vercel or similar — fine for this line.

**Phase 4 — Shadow cycles → pilot → first revenue (4–6 weeks elapsed)**
Two full shadow cycles (fictional personas, real facts; exit: zero
verified-fact errors, <10 min IEC approval per cycle) → TTS wiring → C0 pilot
terms → recruitment: (a) warm DoDEA/military-community channel led by the GI
Bill changelog; (b) 20 personalized IECA approaches, each with a **real sample
edition generated from that IEC's own published school list** at zero marginal
cost — the machine does the selling → convert at **$99/mo flat** (up to 15
clients; tiers only after >3 paying IECs; Stripe fine here). Success bar:
**3–5 paying IECs in 6 months is success.** Steady-state honesty: 2–3 hrs/week
for the first ~3 months (scraper rot, prompt tuning), decaying toward
3–5 hrs/month after two clean cycles; per-component minute budgets with the
shed rule (persistently over-budget component gets disabled or demoted, not
heroically maintained).

**Parallel Track B — VilseckKI Notarin pilot (owner decision, separate thread)**
The revenue judge's case: the Notarin is the portfolio's only named warm
customer; €149/mo + referrals into the Landkreis's Rechtsanwälte/Steuerberater;
break-even at one client. The ops judge's case: interactive daytime serving
from a residential box with the NIC defect is an on-call obligation that
punishes travel, and 2–4 hrs/month while operating client RAG is fantasy.
**Recommendation:** decide Track B *after* Phase 0 (the hardening + benchmark
serve it either way) — but start its uncompressible pieces now regardless,
because they cost no engineering time: the 6 legal research prompts +
IT-Recht-Kanzlei AVV/Verpflichtungserklärung track (§203 StGB is criminal law;
4–8 weeks, ~€1–3K — price it against first-year revenue), vilseckki.de
registration at INWX, and the pilot framed as **bounded and SLA-free** (free
4–6 weeks, English support, weekly 15-min check-in). If it converts, revisit
the Festung Franken shell before client #2. It shares the box; it never
blocks the Newsroom.

**Parallel Track C — Funding sprint (half a day, then waits)**
Re-verify as of Aug 2026 (all tracker dates are stale): Digitalbonus status +
the 2.2 IT-Sicherheit track for UPS/NAS/firewall at ~50%; Start?Zuschuss
round 23; the ~€30 Nebenerwerb→Haupterwerb switch decision (gates BayTOU).
Standing rule: **nothing purchased before Eingangsbestätigung** (Verbot des
vorzeitigen Maßnahmenbeginns). Use the correct founding year (2025).

**Parallel Track D — Dissertation co-tenancy (after Phase 4 exit criteria)**
GRUND local-model legs run in leftover night slots within the ~30GB headroom;
re-check llama.cpp #21416 (Gemma/gfx1151) before any Gemma plan. Free PhD
compute; never on the critical path.

---

## 8. Revenue map & kill gates

| Stream | Who pays | Realistic number | Gate |
|---|---|---|---|
| Upskill News subscriptions | Solo IECs (12–15 clients each; comps: CollegePlannerPro $66–219/mo) | $99/mo flat; 3–5 IECs in 6 months = success; 15–20 IECs ($1.5–2.5K/mo) = 18-month ceiling | Two clean shadow cycles before any pilot; pilot-conversion review after 2 paid cycles |
| Verified change feed (deferred) | IECs €29–49/mo; platform licenses €300–1K/mo (<10 buyers) | Five-figure/yr niche at best | Free changelog is the only outward artifact until **week 16 from changelog launch**: no paying interest AND no platform LOI ⇒ index is formally internal infrastructure; external spend stops |
| VilseckKI RAG (Track B) | Notarin → referrals; €149–349/mo + setup | €150–450/mo year-one realistic | Owner go/no-go after Phase 0; legal track must close before any money |
| Corpus products (dormant) | Compliance teams | May round to zero (deadline anchor passed) | Reactivate only after Newsroom steady state, with fresh demand evidence, capped at a two-weekend probe |
| Grants (Track C) | Bavaria | €7.5–15K near-term (Digitalbonus-class), more post-Haupterwerb | Re-verify first; never purchase before approval |

Fixed costs all-in: ~€40–50/month (electricity €15–25, Hetzner storage/edge
€5–10, domains, Supabase/Clerk entry tiers as they activate).

---

## 9. Open [OWNER] decisions

1. **Supabase billing** (pending since 2026-07-14) — Phase 3's gate.
2. **Clerk instance + Resend account/DNS** — same chain.
3. **Track B go/no-go** (Notarin pilot posture per §7) + commissioning the
   IT-Recht-Kanzlei legal work (~€1–3K).
4. **C0 pilot definition** (terms, success criteria, testimonial/referral ask).
5. **Haupterwerb switch** (~€30, unlocks BayTOU) — Track C.
6. **Publishing the free changelog** (where: Hetzner page, GitHub, newsletter?).
7. **Windows endgame** (VM-ify or keep dual-boot with self-heal).
8. Later, only if triggered: feed pricing, platform-license outreach, vector
   layer, QS/THE licensing.

## 10. Related files

| File | Why |
|---|---|
| `upskill-news-app/docs/BEELINK_FACTS_INDEX.md` | App-side integration contract + scoped to-do list |
| `patterns/docs/research/BEELINK_INDEX_ASSET_RESEARCH.md` | Market + hardware research with sources |
| `patterns/ideas/MICRO-SAAS-IDEAS.md` #110 | The index filed as a scored idea |
| `upskill-news-app/docs/LOCAL_LLM_ARCHITECTURE.md` | Model decision + batch math (do not relitigate) |
| `upskill-news-app/docs/HANDOFF.md` §3, `docs/SMOKE_TEST_MANUAL.md` | Go-live sequence + runbooks |
| `docs/EU-AI-ACT-RAG-CORPUS-PLAN.md` | The original index-as-product blueprint (pipeline still reusable) |
| `VILSECKKI-FINAL-ARCHITECTURE.md`, `VILSECKKI-IMPLEMENTATION-PLAN.md` §6 | Track B architecture + legal blockers |
| `regwatch/`, `court-scraper/`, `../vilseckki-datafactory-app/` | Reused code (§2 table) |
| `log/2026-08-15-upskill-indexing-synergy.md` | This session's note |
