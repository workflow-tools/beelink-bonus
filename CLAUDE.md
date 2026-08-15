# Beelink Bonus — Claude Context Document

> **Purpose:** Single source of truth for any Claude session working on the Beelink AI server strategy.
> Any new thread should read this file first.
> Last updated: August 2026.
> **Current master plan:** `BEELINK-UPSKILL-INDEXING-PLAN.md` (2026-08-15) — decision record
> + phased build plan for the Beelink as upskill-news production server + Verified Facts
> Store. It supersedes `TONIGHT-SETUP-CHECKLIST.md` and corrects several hardware facts
> that older docs in this repo still carry (see its §3 "Corrections to the record").

---

## What This Repo Is

This is the planning, experimentation, and documentation home for putting a **Beelink GTR9 Pro (AMD AI Max+ 395, 128GB LPDDR5X)** to productive use as a revenue-generating local AI server.

The machine is owned by Ryan Hill, founder of ML Upskill Agents UG (haftungsbeschränkt), a German-registered company building micro-SaaS products for clinical nursing education and adjacent domains.

> **Note — Data Factory spun out (March 2026):** The synthetic dataset generation pipeline has been extracted into its own dedicated repository at `../vilseckki-datafactory-app/`. That repo contains all framework code, YAML dataset configs, and its own CLAUDE.md and LECHAT-PROJECT-DESCRIPTION.md. The remaining scope of *this* repo (beelink-bonus) is: (1) VilseckKI RAG-as-a-Service architecture and client work, (2) general Beelink infrastructure / hardware experiments, and (3) the LLM Factory planning (fine-tuned SLM delivery) once the Data Factory is generating revenue.

---

## Hardware Summary

| Spec | Detail |
|------|--------|
| **Chip** | AMD Ryzen AI Max+ 395 (Strix Halo) |
| **RAM** | 128GB LPDDR5X unified memory (CPU + GPU shared) |
| **GPU** | Radeon 890M — 40 RDNA 3.5 CUs, accesses full 128GB |
| **NPU** | XDNA 2 (~50 TOPS) — not yet well-supported by inference frameworks |
| **CPU** | 16 Zen 5 cores |
| **Key insight** | Apple Silicon-class unified memory on AMD. GPU can address all 128GB, enabling large model inference that discrete GPU machines cannot match at this price point. |

### Realistic Inference Speeds (community figures, mid-2026 — this unit still unbenchmarked)

> Corrected 2026-08-15: the previous table overstated dense models and missed the
> platform's real strength entirely. Token generation is memory-bandwidth-bound
> (~212 GB/s measured); **MoE models are the sweet spot, dense 70B is not.**
> Prompt *prefill* is the weak side vs discrete GPUs. First-party numbers for this
> unit are a Phase 0 task of `BEELINK-UPSKILL-INDEXING-PLAN.md` — record them in
> `mistral/open-source-models/BEELINK-FIT.md` (its results log is still empty).

| Model class | Example | Est. Tok/s (decode) |
|-------|-------|------------|
| 7–8B dense Q4 | llama3.1:8b | ~50 |
| 30B-A3B-class MoE | Qwen3-30B family | ~100 |
| 100B+ MoE | gpt-oss-120b | ~48–55 |
| 122B MoE (production model) | Qwen3.5-122B-A10B Q4 | ~25–40 (per upskill-news LOCAL_LLM_ARCHITECTURE) |
| 70B dense Q4 | llama3.3:70b | ~5 (batch only) |
| 235B MoE Q3 | Qwen3-235B | ~12 |

### Critical GPU Setup

```bash
# CORRECTED 2026-08-15: this chip is gfx1151 (Strix Halo). The old 11.0.0 value
# spoofs gfx1100 (RDNA3 dGPU) and can force mismatched kernels — do not use it.
export HSA_OVERRIDE_GFX_VERSION=11.5.1   # for Ollama/ROCm; omit entirely on native-gfx1151 ROCm 7.x builds
ollama serve                              # never set OLLAMA_VULKAN=1 (hangs on Qwen3.5-class models)
# Verify: rocm-smi in a second terminal while running inference
# ~110GB GPU-addressable on Linux needs kernel params: amdgpu.gttsize=131072 ttm.pages_limit=31457280
# Cap 24/7 serving contexts at ~64K (200K+ can exhaust kernel memory and crash the box)
# Note: llama-server (Vulkan/RADV) measures ~2x Ollama throughput on this platform —
# serving binary is decided by the Phase 0 benchmark, not by default.
```

---

## Owner Context

- **Company:** ML Upskill Agents UG (haftungsbeschränkt), Vilseck, Germany
- **Founder:** Ryan Hill — PhD student (CS, FAU), digital nomad, 4 children, spouse in DoDEA
- **Primary dev environment:** MacBook Air + VS Code
- **Beelink role:** Dedicated local AI server, experimentation platform, potential revenue generator
- **Physical location:** Currently Oberpfalz region (Vilseck), near Nürnberg-Amberg-Weiden-Bayreuth corridor

---

## Existing Product Portfolio (Relevant Context)

### Live / Code-Complete Products
- **WritingPAD** (writingpad.co.uk) — UK nursing feedback transformation. LIVE.
- **ProPrecept Ireland** (proprecept.ie) — Irish nursing feedback. Code complete.
- **ProPrecept RSA** — South African variant. Code complete.
- **FacultyWizard** (facultywizard.com) — Academic feedback transformation. Deployed.
- **Assessment Wizard** — Academic assessment workflows. Early stage.

### Pre-MVP / Design Phase
- **EHCP Audit** — UK SEND compliance analysis (GRUND framework, multi-agent). Dissertation Paper 2.
- **IEP Checker** — US IEP compliance (IDEA + 50 states + DoDEA). Dissertation extension.
- **Rebeka** — SA clinical placement management platform (B2B, multi-market).

### Architecture Patterns
- WritingPAD family: stateless one-shot transforms, prompt contract pattern, Next.js/Clerk/Stripe/Claude API
- EHCP/IEP: multi-agent debate (GRUND), regulatory corpus, cloud + local model comparison
- Rebeka: full B2B platform with Supabase, offline-first, market config system

---

## How the Beelink Connects to Existing Products

1. **EHCP Audit local inference** — The GRUND framework already has provider abstraction for cloud + local models. The Beelink running Qwen-3.5 or Mistral via Ollama is the "self-hosted" leg of the 2×2 factorial design (cloud vs local × debate vs no-debate). This is both product feature AND dissertation experiment.

2. **Assessment Wizard "Private Cloud"** — FERPA-compliant local deployment for US institutions that cannot send student data to cloud APIs. Natural premium tier.

3. **Faculty Wizard "Private Cloud"** — Same concept for universities with strict data policies.

4. **Fine-tuning lab** — QLoRA fine-tuning on domain-specific data (nursing terminology, SEND law, etc.) for improved product quality.

5. **Dissertation compute** — Running controlled experiments locally eliminates API cost as a variable.

---

## Three Revenue Strategies (from brainstorming prompt)

### Strategy 1: Privacy-First Fine-Tuned Model Shop
- Fine-tune small open models on client domain data
- Deliver as downloadable bundle (model + local UI installer)
- Target: SMBs in regulated industries (legal, medical, finance)
- Revenue: $200–$500 one-time, $50–$100/mo subscription, $2K–$10K custom

### Strategy 2: Local AI Agent-as-a-Service
- Multi-agent systems on client hardware or served via secure tunnel
- No data leaves client network
- Target: regulated industries needing compliant local AI replacement
- Revenue: $3K–$10K setup, $500–$2K/mo service

### Strategy 3: Privacy-First RAG Systems
- "Chat with your documents" deployed locally
- Target: law firms, consulting, medical, academic institutions
- Revenue: $3K–$8K setup, $300–$1K/mo maintenance, $50–$200/user/mo

---

## Local Market Context (Nürnberg-Bayreuth-Weiden-Amberg Corridor)

The Oberpfalz / Franken region presents specific opportunities:
- **Mittelstand density** — Many SMBs in manufacturing, legal, medical that are privacy-conscious and skeptical of US cloud AI
- **German data sovereignty concerns** — DSGVO enforcement is real here; "your data never leaves Germany" is a strong selling point
- **University hospitals** — Erlangen-Nürnberg (FAU), Bayreuth, Regensburg all have medical/research needs
- **Military community** — Grafenwöhr/Vilseck has US military families (DoDEA connection, potential IEP Checker beta users)

---

## Priority Assessment (Low-Touch Preference)

The owner explicitly needs **passive, low-maintenance** revenue. Ranked by automation potential:

1. **RAG-as-a-Service for local Mittelstand** — Once deployed, runs itself. Monthly check-ins. Highest passive potential.
2. **Fine-tuned model delivery** — Automatable pipeline (intake → train → package → deliver). ~30 min human per job.
3. **Agent-as-a-Service** — Requires more ongoing client interaction. Least passive.

---

## Session Log

All Claude session notes go in `./log/` with filename format: `YYYY-MM-DD-topic.md`

---

## Go-To-Market Decisions (March 2026)

### Brand & Domain
- **Trade name:** VilseckKI
- **Primary domain:** vilseckki.de (confirmed available as of March 2026; registration pending)
- **Backup domains checked:** oberpfalzki.de, kioberpfalz.de, kivilseck.de, vilseki.de, kivils.de — all available as of March 2026
- **Rationale:** Hyper-local trust signal. People in Amberg-Sulzbach Landkreis know Vilseck. Military community knows Vilseck. "Small town, I can drive to your office" is a feature for privacy services. Oberpfalz-level branding felt too big for a one-server operation and could imply Regensburg-based.
- **Legal setup:** Operates as a trade name of ML Upskill Agents UG. Impressum reads "ML Upskill Agents UG (haftungsbeschränkt), handelnd unter VilseckKI" or similar. No separate Gewerbeanmeldung needed for a trade name.

### First Client: The Notarin
- Existing personal relationship with a local Notarin
- She speaks perfect English (studied in Chicago)
- Notare/Notarinnen handle highly confidential documents (Kaufverträge, Testamente, Gesellschaftsverträge, Grundbucheinträge) — cloud AI is essentially off-limits for this work
- **Pilot plan:** Free 4-6 week trial → feedback → referral request
- **Referral value:** A Notarin knows every Rechtsanwalt, Steuerberater, and Makler in the area. One recommendation from her > 50 LinkedIn posts.

### Language Strategy
- Owner's German is functional but not fluent
- Landing page and AGB: professional German (IT-Recht-Kanzlei for legal, native speaker review for marketing copy)
- Client conversations: English where possible (Notarin speaks English; many professionals do)
- Being an American tech founder in Vilseck is a memorable differentiator, not a weakness

---

## Open Questions

Statuses updated 2026-08-15 (evidence + sources: `BEELINK-UPSKILL-INDEXING-PLAN.md` §3
and `patterns/docs/research/BEELINK_INDEX_ASSET_RESEARCH.md`):

- [x] ~~Is Ollama + ROCm stable on this chip?~~ **Answered:** yes with the corrected
      config (gfx1151 → HSA override 11.5.1, never `OLLAMA_VULKAN=1`, contexts ≤~64K),
      but Ollama leaves ~2× throughput vs `llama-server` (Vulkan) — benchmark decides
      the serving binary.
- [ ] Actual measured tok/s + embedding throughput on THIS unit — still open; Phase 0
      benchmark gate; record in `mistral/open-source-models/BEELINK-FIT.md`.
- [x] ~~NPU (XDNA 2) support status~~ **Answered:** usable on Linux since Mar 2026 via
      FastFlowLM + Lemonade (small ~3B models, <2W, needs IOMMU **on**); irrelevant to
      the main GPU serving path — sidecar use only, never load-bearing.
- [x] ~~Tailscale vs Cloudflare Tunnel~~ **Resolved:** private Tailscale tailnet for
      anything confidential — Cloudflare Tunnel decrypts at its US edge, which breaks
      the §203/DSGVO pitch; Cloudflare only ever for a public marketing site.
- [ ] Which Mittelstand verticals in the region are most accessible? (Legal? Medical? Manufacturing?)
- [ ] Can the Beelink run 24/7 reliably headless? **Reframed:** thermals are fine on this
      platform; the risk is the documented Intel E610 NIC firmware deadlock under
      sustained GPU+network load — Phase 0 NIC gauntlet (NVM ≥1.30 + BIOS ≥1.08 + 4h
      soak test + USB NIC fallback) before any 24/7 commitment.
- [x] ~~Electricity cost for 24/7?~~ **Refined:** ~10–15W idle, 60–120W under load;
      €15–25/month at a batch-heavy duty cycle (€0.30/kWh); TDP capped ~85–100W as the
      NIC/thermal-margin trade.

---

## Related Files

| File | Purpose |
|------|---------|
| `README.md` | Repo overview |
| `CLAUDE.md` | This file — Claude context |
| `BEELINK-UPSKILL-INDEXING-PLAN.md` | **Master plan (2026-08-15)** — decision record (4 designs, 3-judge panel), Verified Facts Store + Newsroom Runner architecture, Phase 0 hardware runbook, phased to-dos, kill gates |
| `VILSECKKI-FINAL-ARCHITECTURE.md` | Full VilseckKI RAG + services architecture |
| `VILSECKKI-IMPLEMENTATION-PLAN.md` | RAG service implementation roadmap |
| `AUTH-AND-BACKEND-COMPARISON.md` | Auth/backend options analysis |
| `VILSECKKI-DATA-FACTORY-MARKET-INSIGHTS.md` | **Data Factory market research** — demand assessment, pricing, channels, risks |
| `GRANT-APPLICATION-PLAN.md` | **Bavarian grant plan** — Digitalbonus Plus + Start?Zuschuss! eligibility, application steps, pitch framing |
| `log/` | Session notes |
| `../vilseckki-datafactory-app/CLAUDE.md` | **Data Factory** — Claude context (spun out repo) |
| `../vilseckki-datafactory-app/LECHAT-PROJECT-DESCRIPTION.md` | Data Factory — Mistral/Le Chat briefing |
| `../PROJECT-INVENTORY-2026-03-09.md` | Full company project inventory |
| `../rebeka-app/ARCHITECTURE.md` | Rebeka system map |
| `../ehcpaudit-app/ARCHITECTURE-SELF-CHALLENGE.md` | EHCP architecture analysis |
