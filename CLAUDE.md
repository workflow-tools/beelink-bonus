# Beelink Bonus — Claude Context Document

> **Purpose:** Single source of truth for any Claude session working on the Beelink AI server strategy.
> Any new thread should read this file first.
> Last updated: March 2026.

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

### Realistic Inference Speeds (ROCm/Vulkan via Ollama or llama.cpp)

| Model | Quant | VRAM Used | Est. Tok/s |
|-------|-------|-----------|------------|
| 7B | Q4_K_M | ~4.5GB | 80–120 |
| 13B | Q4_K_M | ~8GB | 40–70 |
| 34B | Q4_K_M | ~20GB | 15–30 |
| 70B | Q4_K_M | ~40GB | 8–15 |
| 70B | Q8 | ~75GB | 4–8 |

### Critical GPU Setup

```bash
export HSA_OVERRIDE_GFX_VERSION=11.0.0   # RDNA 3.5 compatibility flag
ollama serve                              # Ollama auto-detects 890M GPU
# Verify: rocm-smi in a second terminal while running inference
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

- [ ] Is Ollama + ROCm stable on this chip as of March 2026? Need to verify.
- [ ] What's the actual measured tok/s on this specific unit? Benchmark needed.
- [ ] NPU (XDNA 2) support status in llama.cpp — check GitHub PRs
- [ ] Tailscale vs Cloudflare Tunnel for client access — test both
- [ ] Which Mittelstand verticals in the region are most accessible? (Legal? Medical? Manufacturing?)
- [ ] Can the Beelink run 24/7 reliably as a headless server? Thermal/power testing needed.
- [ ] What's the electricity cost at current German rates for 24/7 operation? (~65W TDP, ~€0.30/kWh ≈ €14/month)

---

## Related Files

| File | Purpose |
|------|---------|
| `README.md` | Repo overview |
| `CLAUDE.md` | This file — Claude context |
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
