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

## Development Best Practices

> These conventions are informed by current research on LLM-assisted coding
> workflows (Osmani 2026, Willison 2025, Honeycomb 2025) and are designed to
> make the codebase productive for both human developers and AI assistants
> (Claude, Cursor, Cursor BugBot). A solo founder with four children cannot
> afford debugging sessions caused by ambiguous code.

### DP-1: Small, Focused Files (~200 Lines Max)

Each Python module in `regwatch/` handles exactly one concern. If a module
grows past ~200 lines, split it. LLMs perform measurably better when given
a single focused file as context rather than a large monolith — they produce
fewer hallucinated imports, maintain consistent style, and are less likely
to lose track of state. This also means Cursor's inline edits and BugBot's
per-file analysis stay within their optimal context window.

### DP-2: Type Hints on Every Public Interface

All function signatures must include type hints for parameters and return
values. This is non-negotiable. Type hints serve triple duty:

1. **Human readability** — intent is explicit without reading the body.
2. **LLM grounding** — models generate significantly more correct code when
   they can see typed signatures in context. Research consistently shows
   that type annotations reduce LLM hallucination of incorrect parameter
   types and return shapes.
3. **Cursor/BugBot analysis** — static type information enables BugBot to
   catch type mismatches across call sites, not just within the changed file.

Use `dict[str, Any]` over bare `dict`. Use `Optional[X]` or `X | None`
explicitly. Import from `typing` only when needed for older Python compat.

### DP-3: Docstrings on Every Module, Class, and Public Function

Follow Google-style or NumPy-style docstrings consistently (this project
uses Google-style). Every docstring must include:

- **One-line summary** in imperative mood ("Send a triage result to Ollama.")
- **Args section** with parameter names, types, and purpose
- **Returns section** describing the return value
- **Raises section** if the function raises exceptions intentionally

Well-structured docstrings are the single highest-impact investment for
LLM-assisted development. They serve as the "specification" that both
Cursor's autocomplete and Claude's code generation use to infer intent.
Vague or missing docstrings force the LLM to guess — and guessing is
where bugs come from.

### DP-4: Explicit Error Handling — No Bare Excepts

Every `try/except` block must catch specific exception types. Bare
`except:` or `except Exception:` at a high level is only acceptable in
the webhook handler and CLI entry points where Rule 6 (No Silent Failures)
requires a catch-all with logging.

Log the error with enough context to reproduce: the URL, the product name,
the operation that failed, and the exception message. Use Python's
`logging` module, not `print()`.

### DP-5: Test-Driven Iteration

Write tests before or alongside implementation, not after. The test suite
is the specification that both humans and LLMs work against.

**Test structure:**
```
regwatch/
├── tests/
│   ├── __init__.py
│   ├── test_config.py      # YAML loading, watch lookup, URL index
│   ├── test_triage.py      # Prompt building, response parsing (mock Ollama)
│   ├── test_log.py         # JSONL append, dedup, read with filters
│   ├── test_notify.py      # Email/GitHub formatting (mock HTTP)
│   ├── test_api.py         # Flask test client for all endpoints
│   ├── test_digest.py      # Digest compilation logic
│   └── conftest.py         # Shared fixtures (sample configs, mock data)
```

**Testing conventions:**
- Use `pytest` as the test runner.
- Mock external services (Ollama, Resend, GitHub API) — never make real
  HTTP calls in tests.
- Each test function tests one behaviour and is named
  `test_{module}_{behaviour}_{scenario}`.
- Fixtures in `conftest.py` provide sample YAML configs and triage results
  so test data is consistent and DRY.
- Target: 80%+ line coverage on the orchestrator modules. Config loading
  and JSONL parsing are especially important to cover since they're the
  most likely source of subtle bugs.

### DP-6: Cursor + BugBot Integration

This project uses Cursor as the primary IDE alongside VS Code. To maximise
BugBot's effectiveness:

**`.cursor/BUGBOT.md`** — Create this file in the regwatch project root with
project-specific review rules. BugBot reads this on every PR review. Include:
- Rule 6 enforcement: "Flag any `except` block that does not log or notify."
- YAML contract: "Flag any Python code that hardcodes a URL, product name,
  or urgency level that should come from YAML config."
- Type safety: "Flag any public function missing type hints."
- No silent drops: "Flag any code path where a webhook could be received
  and no log entry or notification is produced."

**`.cursor/rules/`** — Create Cursor project rules for inline AI assistance:
- Remind Cursor of the module structure and which file handles which concern.
- Include the six Development Rules so Cursor's suggestions don't violate them.
- Reference the YAML config schema so Cursor doesn't hallucinate config keys.

**BugBot Autofix** — When BugBot identifies issues on PRs, its Autofix
feature can spawn cloud agents to propose fixes. Given this is a solo project,
Autofix is valuable for catching issues you might miss during late-night
commits. Review Autofix suggestions with the same rigour as any other code.

### DP-7: Commit Hygiene

- **Atomic commits:** One logical change per commit. "Add dedup logic to
  log.py" is good. "Add dedup + fix email + update README" is three commits.
- **Conventional commit messages:** Use the format `type(scope): description`.
  Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
  Examples: `feat(triage): add JSON extraction fallback for markdown-wrapped responses`,
  `fix(notify): handle missing github_repo in product config`.
- **Never commit secrets.** The `.gitignore` already excludes `.env`. If you
  need to reference API keys in docs, use placeholder format: `re_...` or
  `ghp_...`.

### DP-8: LLM Context Files

Maintain these files to help any AI assistant (Claude, Cursor, future tools)
understand the project quickly:

- **`CLAUDE.md`** (project root or `beelink-bonus/regwatch/`) — Machine-readable
  project context: what the system does, module responsibilities, config schema
  summary, and the six rules. This is the "llms.txt" equivalent for Claude sessions.
- **`.cursor/BUGBOT.md`** — BugBot-specific review rules (see DP-6).
- **`.cursor/rules/regwatch.mdc`** — Cursor project rules for inline suggestions.
- **`README.md`** — Human-readable setup guide (already exists).

When making significant architectural changes, update these context files in
the same commit. Stale context files are worse than no context files — they
cause LLMs to generate code against outdated assumptions.

### DP-9: Dependency Minimalism

RegWatch has exactly four runtime dependencies: `flask`, `requests`, `pyyaml`,
`resend`. Adding a new dependency requires justification — each dependency is
a surface area for security issues, version conflicts, and LLM confusion
(models are more reliable with well-known, stable libraries than with niche
packages).

If a task can be accomplished with the Python standard library in roughly the
same number of lines, prefer the standard library.

### DP-10: YAML Schema Discipline

YAML config files are the public API of this system (Rule 1). Treat them with
the same rigour as a code interface:

- **Document every key** with inline comments in the example configs.
- **Validate on load** — `config.py` should warn (not crash) on unrecognised
  keys, and error on missing required keys.
- **Version the schema** — if the YAML structure changes, increment a
  `schema_version` key so older configs can be migrated or rejected with a
  clear error message.
- **Never add a YAML key without updating the context files** (CLAUDE.md,
  BUGBOT.md) in the same commit.

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
