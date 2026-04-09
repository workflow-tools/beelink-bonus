# RegWatch — Cowork Project Instructions

**Date:** 2026-04-09
**Status:** Ready for implementation
**Repo:** `beelink-bonus/regwatch/`
**Runs on:** Beelink GTR9 Pro (AMD AI Max+ 395, 128GB LPDDR5X, Ollama pre-installed)
**First consumer:** FarAfield (nurse migration pathway JSON freshness)
**R&D payload:** `beelink-bonus/docs/REGWATCH-RD-PAYLOAD.md` — read this FIRST for full architecture and config examples

---

## What RegWatch Is

A self-hosted, LLM-triaged web change detection system. It monitors regulatory and policy URLs, classifies detected changes by urgency and domain impact using a local LLM (Ollama), and routes structured notifications to the right product.

Three Docker containers + a ~400-line Python Flask orchestrator + Ollama (already running on the Beelink). Zero cloud cost.

**RegWatch is detection, not correction.** It tells a human "this regulatory page changed, here's what it means for your product content, and here's how urgent it is." The human then verifies and makes the content fix. This is a hard constraint — automated content patching is explicitly out of scope.

---

## Why This Exists

FarAfield's TR_DE pathway shipped with a family reunion step that was wrong for over a year (spouse A1 required → actually exempt since March 2024). The PflBG competency-based recognition shift went into effect January 2025 and still isn't reflected. These aren't edge cases — they're fundamental regulatory changes that affect every user of a product where wrong information causes real harm.

The manual monitoring cadence (documented in `farafield-app/docs/Regulatory-Monitor-Guide.md`) is correct but depends on a human remembering to check 40+ URLs on schedule. That human is a PhD student with four children. RegWatch automates the remembering.

The system is designed cross-product from day one because FarAfield is not the only ML Upskill Agents product with regulatory content freshness requirements. Upskill News, EHCP Audit, Pan-African Privacy, and VilseckKI all have the same pattern: content derived from external regulatory sources that goes stale when those sources change.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BEELINK GTR9 PRO                            │
│                                                                     │
│  ┌────────────────────┐   ┌───────────────────┐   ┌──────────────┐ │
│  │ changedetection.io │   │     Ollama         │   │ regwatch.py  │ │
│  │ (Docker)           │   │ (already running)  │   │ (orchestrator│ │
│  │ Web UI: :5000      │   │ llama3.1:8b /      │   │  + API)      │ │
│  │                    │   │  mistral:7b        │   │ Flask: :5050 │ │
│  └────────┬───────────┘   └─────────┬──────────┘   └──────┬───────┘ │
│           │ webhook                 │ Ollama API           │         │
│           ▼                         │ :11434               │         │
│  ┌────────────────────┐             │                      │         │
│  │ Playwright browser │             │                      │         │
│  │ (Docker, for JS    │             │                      │         │
│  │  rendered pages)   │             │                      │         │
│  └────────────────────┘             │                      │         │
│                                     │                      │         │
│  regwatch.py flow:                  │                      │         │
│  1. Receive webhook from cdio  ─────┘                      │         │
│  2. Look up watch config (YAML)                            │         │
│  3. Send diff + context to Ollama                          │         │
│  4. Parse structured triage JSON                           │         │
│  5. Route notification per product config                  │         │
│  6. Append to change log (JSONL)                           │         │
│  7. Optionally create GitHub Issue                         │         │
│  8. Expose query API ◄────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────┐    ┌────────────────┐    ┌──────────────────┐
  │ Email    │    │ GitHub Issues  │    │ Product APIs     │
  │ (Resend) │    │ (per-repo)     │    │ (Tailscale)      │
  └──────────┘    └────────────────┘    └──────────────────┘
```

---

## How RegWatch Connects to FarAfield (Primary Consumer)

This is the most important thing to understand. There are three systems and they interact through deliberate loose coupling:

### System 1: RegWatch (this project, beelink-bonus)

Monitors 35-40 regulatory URLs relevant to nurse migration to Germany. When a page changes, the Ollama LLM triage classifies the diff using context from `watches/farafield.yaml` — which pre-maps every URL to specific pathway corridors, step keys, and JSON fields.

The triage output is a structured JSON:
```json
{
  "relevance": "YES",
  "urgency": "P1",
  "affected_corridors": ["NG_DE", "PK_DE"],
  "affected_steps": ["research_orientation", "job_search"],
  "affected_fields": ["warnings"],
  "summary": "§38 BeschV updated: WHO safeguard enforcement expanded...",
  "recommended_action": "Update warning text in Steps 1 and 11 for NG_DE and PK_DE"
}
```

For P0/P1: RegWatch sends an email AND creates a GitHub Issue in the `farafield-app` repo with the structured template (diff summary, affected corridors/steps/fields, verification checklist, link to changedetection.io snapshot).

For P2/P3: logged to `changes/farafield.jsonl` and included in the weekly digest email.

### System 2: FarAfield Pathway Config JSONs (farafield-app/data/pathways/)

Each corridor is a JSON file conforming to `PathwayDefinition` in `lib/types/pathway.ts`. These are Layer 1 in FarAfield's three-layer architecture — static, versioned, read-only at runtime.

When RegWatch creates a GitHub Issue saying "§30 AufenthG changed, affects family_reunion_visa step in ALL corridors, fields: description, tasks, warnings," a human (or a FarAfield config thread) opens the relevant JSON files, makes the surgical edit, runs `lib/pathway/validator.ts`, verifies against the primary regulatory source, and commits.

**RegWatch never touches these files.** The watch config in `watches/farafield.yaml` maps URLs to step keys so the triage output can say exactly which JSON fields to check — but the edit is always human-verified. This respects FarAfield's Rule 13 (corridor authoring pipeline requires human verification of every regulatory claim).

### System 3: FarAfield Proper (farafield-app, Vercel)

The Next.js application reads the pathway JSONs at build time. When the config commit lands, Vercel auto-redeploys, and users see updated content on next page load (or service worker cache refresh).

FarAfield proper never knows about RegWatch directly. It just reads pathway JSONs. The deployment pipeline (git push → Vercel build → live) is the connection.

### The Data Flow

```
Regulatory source changes (e.g., gesetze-im-internet.de)
        │
        ▼
changedetection.io detects page diff
        │
        ▼
regwatch.py receives webhook + sends diff to Ollama with watch context
        │
        ▼
Ollama classifies: urgency, corridors, steps, fields, summary
        │
        ├─── P0/P1 → Email + GitHub Issue in farafield-app
        └─── P2/P3 → JSONL log + weekly digest
                │
                ▼
Human reviews GitHub Issue, verifies against primary source
                │
                ▼
Config thread edits pathway JSON(s), runs validator.ts, commits
                │
                ▼
Vercel auto-redeploys FarAfield with updated Layer 1 content
                │
                ▼
Users see corrected information
```

---

## The Three-Layer Config System

RegWatch is configured entirely through YAML. No code changes to add a URL, product, or triage prompt.

### Layer 1: `domains.yaml` — Product registry

Defines which products RegWatch serves, their notification preferences, and urgency routing.

```yaml
products:
  farafield:
    display_name: "FarAfield"
    repo: "farafield-app"
    notify:
      email: "workflow.tools@icloud.com"
      github_issues: true
      github_repo: "mlupskill/farafield-app"
    urgency_routing:
      P0: [email, github_issue]
      P1: [email, github_issue]
      P2: [weekly_digest]
      P3: [log_only]
```

### Layer 2: `watches/{product}.yaml` — URL watch lists

Each product has its own watch file. Every entry maps a URL to product-specific context: which corridors, which steps, which JSON fields.

```yaml
# watches/farafield.yaml — example entry
watches:
  - url: "https://www.gesetze-im-internet.de/aufenthg_2004/__30.html"
    check_interval: "1d"
    context:
      product: farafield
      corridors: ["ALL"]
      likely_steps: ["family_reunion_visa"]
      likely_fields: ["description", "tasks", "warnings"]
      note: "Spouse language requirement — monitors for changes to skilled worker exemption"
```

The `corridors`, `likely_steps`, and `likely_fields` values come from the FarAfield pathway JSON structure. Step keys must match the actual `key` field in `PathwayStep` objects in the pathway JSONs. The authoritative source for what to watch and why is `farafield-app/docs/Regulatory-Monitor-Guide.md`.

### Layer 3: `prompts/{product}_triage.yaml` — LLM triage prompts

Product-specific system prompts and templates that give Ollama the right domain context for classification.

```yaml
# prompts/farafield_triage.yaml
system: |
  You are a regulatory change analyst for FarAfield, a B2C app guiding
  international nurses through country-specific licensure pathways to
  Germany and Austria.
  
  Source countries: India, Nigeria, Colombia, Kenya, Nepal, Pakistan,
  Turkey, South Africa.
  Destinations: Germany (Bayern, NRW, Berlin), Austria (Wien, OÖ, Salzburg).
  
  Key regulatory domains: immigration law (AufenthG, BeschV), nursing
  recognition (PflBG, Anerkennung), WHO health workforce safeguards,
  language exam infrastructure (Goethe, telc, ÖSD), blocked account
  requirements, family reunion provisions.
```

---

## Orchestrator Module Structure

```
regwatch/
├── __init__.py
├── app.py              # Flask app — webhook receiver + query API
├── config.py           # Load domains.yaml + watches/*.yaml + prompts/*.yaml
├── triage.py           # Ollama triage call + JSON response parsing
├── notify.py           # Email (Resend), GitHub Issues, digest routing
├── log.py              # JSONL append-only change log per product
├── api.py              # GET /api/changes/{product}, GET /api/status
├── digest.py           # Weekly digest compiler + Resend sender
└── cli.py              # Manual: add watch, test triage, replay webhook
```

### API Endpoints

```
GET  /api/changes/{product}?since=2026-04-01&urgency=P0,P1
     → Returns JSONL of changes for that product since the given date

GET  /api/status
     → System health: watches count, last check time, queue depth

POST /api/triage/test
     → Manual triage test: send a URL + fake diff, get triage result
```

The API runs on `:5050` and is accessible over Tailscale from the MacBook. This is how Upskill News's assembler agent (future Phase 4) will pull classified changes.

---

## Implementation Roadmap

### Phase 1: Infrastructure (Evening 1, ~2 hours)

```bash
cd ~/regwatch
docker compose up -d  # changedetection.io + Playwright
# Add first 10 FarAfield Tier 1 URLs via web UI (:5000)
# Configure webhook to http://localhost:5050/webhook
```

Deliverables:
- [ ] changedetection.io running and monitoring 10 URLs
- [ ] Webhook fires on detected change
- [ ] Manual verification that diffs are captured

### Phase 2: Orchestrator + Triage (Evening 2, ~3 hours)

Deliverables:
- [ ] `regwatch.py` webhook receiver + Ollama triage working
- [ ] Email notification fires for P0/P1 via Resend
- [ ] JSONL log captures all triage results
- [ ] Test triage endpoint works (`POST /api/triage/test`)

### Phase 3: Full FarAfield Coverage + RSS (Evening 3, ~2 hours)

Deliverables:
- [ ] All 35-40 FarAfield URLs configured (from Regulatory-Monitor-Guide.md)
- [ ] RSS feeds (Bundesgesetzblatt, OffeneGesetze) configured with keyword filters
- [ ] GitHub Issue auto-creation for P0/P1
- [ ] Weekly digest cron job

### Phase 4: Upskill News Integration (when front-burner, ~2 hours)

Deliverables:
- [ ] `watches/upskill_news.yaml` with 20-30 education/visa URLs
- [ ] `prompts/upskill_news_triage.yaml` with news-specific classification
- [ ] API endpoint tested with assembler agent
- [ ] Newsletter compilation from RegWatch feed demonstrated

### Phase 5: Refinement + Extraction Assessment (ongoing)

- Tune triage prompts based on false positive/negative rate
- Add CSS selector refinement for noisy pages
- Assess micro-SaaS extraction readiness (idea #89 in pipeline)

---

## File Layout

```
beelink-bonus/
├── regwatch/                    # RegWatch system root
│   ├── docker-compose.yaml      # changedetection.io + Playwright
│   ├── regwatch/                # Python package
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── triage.py
│   │   ├── notify.py
│   │   ├── log.py
│   │   ├── api.py
│   │   ├── digest.py
│   │   └── cli.py
│   ├── domains.yaml             # Product registry
│   ├── watches/
│   │   ├── farafield.yaml       # 35-40 URLs from Regulatory-Monitor-Guide.md
│   │   ├── upskill_news.yaml    # Phase 4
│   │   └── ehcpaudit.yaml       # Placeholder
│   ├── prompts/
│   │   ├── farafield_triage.yaml
│   │   └── upskill_news_triage.yaml
│   ├── changes/                 # Per-product JSONL logs (gitignored)
│   ├── requirements.txt         # flask, requests, pyyaml, resend
│   └── README.md                # Setup guide
├── docs/
│   ├── REGWATCH-RD-PAYLOAD.md   # Full R&D design document
│   └── REGWATCH-PROJECT-INSTRUCTIONS.md  # This file
└── ...
```

---

## Development Rules

### Rule 1: Config-Driven, Not Code-Driven

Adding a new URL, product, or triage prompt must never require a code change. YAML only. The orchestrator is generic; the configuration is specific. This mirrors FarAfield's own Rule 1 ("Pathway is data, not code").

### Rule 2: Detection, Not Correction

RegWatch detects and classifies. It NEVER modifies product content. The output is always a notification (email, GitHub Issue, JSONL log entry, API response) that a human acts on. This is non-negotiable — FarAfield's Rule 13 requires human verification of regulatory claims, and RegWatch respects that boundary.

### Rule 3: Product Isolation

Each product's watches, prompts, change logs, and API responses are isolated. FarAfield cannot see Upskill News changes via the API. Change logs are separate JSONL files. This matters for future micro-SaaS extraction where products become tenants.

### Rule 4: Idempotent Triage

If changedetection.io fires the same webhook twice (network retry), regwatch deduplicates by hashing `(url + diff_text + timestamp_hour)`. Same change in the same hour = skip.

### Rule 5: Ollama Sharing

RegWatch shares the Ollama instance with Data Forge (which runs overnight in `vilseckki-datafactory-app/`). Ollama serializes requests, so if Data Forge is running a 70B job, RegWatch triage calls queue behind it. This is fine — regulatory changes aren't sub-second urgent. During the day when nothing else is running, triage calls complete in <5 seconds on llama3.1:8b.

### Rule 6: No Silent Failures

If Ollama is unreachable, if a webhook payload is malformed, if Resend email fails, if GitHub Issue creation fails — log the error AND send a fallback notification (email for Ollama failures, JSONL log for notification failures). The worst outcome is a regulatory change detected but silently dropped.

---

## Resource Budget

| Component | RAM | CPU | Disk | Network |
|-----------|-----|-----|------|---------|
| changedetection.io | ~200MB idle, ~500MB during checks | Negligible | ~1GB for snapshots | ~50 req/day |
| Playwright browser | ~300MB active, 0 idle | Burst during JS render | Minimal | Same requests |
| regwatch.py | ~50MB | Negligible | JSONL ~1KB/day | Webhook receiver |
| Ollama triage | Shares existing instance | ~5-10 calls/day, <1min each | N/A | Local only |
| **Total additional** | **~550MB idle** | **Negligible** | **~1GB/year** | **~50 req/day** |

On a 128GB machine, this is invisible.

---

## Beelink Overnight Pipeline (Target State)

```
22:00  RegWatch check cycle runs (all daily watches)
22:15  Data Forge starts overnight dataset generation (vilseckki-datafactory-app)
06:00  Data Forge completes
06:05  RegWatch compiles weekly digest (if it's digest day)
06:10  Upskill News assembler pulls changes, drafts newsletter (Phase 4)
```

---

## Cross-References

| Document | Location | Purpose |
|----------|----------|---------|
| RegWatch R&D Payload | `beelink-bonus/docs/REGWATCH-RD-PAYLOAD.md` | Full design with all YAML examples |
| Beelink CLAUDE.md | `beelink-bonus/CLAUDE.md` | Hardware specs, Ollama setup, GPU config |
| FA Regulatory Monitor Guide | `farafield-app/docs/Regulatory-Monitor-Guide.md` | What to watch and why — the requirements spec |
| FA Regulatory Change Detection Design | `farafield-app/docs/Regulatory-Change-Detection-Design.md` | FarAfield-specific system design |
| FA Pathway Types | `farafield-app/lib/types/pathway.ts` | PathwayDefinition — the JSON schema contract |
| FA Project Instructions | `farafield-app/PROJECT-INSTRUCTIONS.md` | 13 rules governing pathway content |
| Upskill News Agent Architecture | `upskill-news-app/AGENT_DEVELOPMENT.md` | Crawler/assembler pattern RegWatch replaces |
| Pattern Inbox PI-027 | `patterns/PATTERN-INBOX.md` | Cross-product monitoring pattern filing |
| Micro-SaaS Ideas #89 | `patterns/ideas/MICRO-SAAS-IDEAS.md` | RegWatch extraction criteria |

---

## Micro-SaaS Extraction Signal

RegWatch becomes a standalone product when five conditions are met:

1. It proves value for 2+ products (FarAfield + Upskill News)
2. LLM triage quality is consistently good (<10% false positive, <5% false negative on P0/P1)
3. Config-driven approach scales (new product < 30 min YAML)
4. Clear pricing model emerges (self-hosted license or hosted SaaS)
5. Market validation from compliance teams, immigration consultancies, regulatory affairs

Target market: any business where wrong regulatory information = liability.

---

## GRUND Dissertation Connection

The RegWatch → FarAfield pipeline creates a measurable case study:

- **Regulatory change velocity:** `changes/farafield.jsonl` provides empirical data on how often nurse migration regulations actually change.
- **AI triage accuracy:** Precision/recall of a 7-8B LLM classifying regulatory changes against human verification.
- **Single-agent baseline:** The triage prompt is a simplified version of GRUND's multi-agent debate — one agent reads, one classifies, the human verifies. This is the baseline that multi-agent should outperform.
