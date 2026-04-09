# RegWatch — Beelink R&D Payload

**Date:** 2026-04-07
**Status:** R&D — ready for implementation
**Beelink Role:** Role 2 (overnight batch jobs) + new Role 4 (continuous monitoring)
**First consumer:** FarAfield (nurse migration pathway freshness)
**Second consumer:** Upskill News (regulatory/policy change feeds)
**Extraction target:** Standalone micro-SaaS or open-source tool

---

## 1. What This Is

A self-hosted, LLM-triaged web change detection system that monitors regulatory and policy sources, classifies detected changes by urgency and domain impact, and routes notifications to the right product or person.

It runs entirely on the Beelink GTR9 Pro. Zero cloud cost. Three Docker containers + a Python orchestrator + Ollama (already installed).

### Why It Matters Across Products

| Product | What RegWatch Monitors | Business Impact |
|---------|----------------------|-----------------|
| **FarAfield** | German immigration law (AufenthG, BeschV, PflBG), recognition authority procedures, WHO HWSS list, embassy/VFS changes, exam center availability, blocked account amounts | Pathway JSON accuracy — wrong regulatory info causes real harm to migrating nurses |
| **Upskill News** | University tuition changes, visa policy shifts, scholarship deadlines, program launches/closures, accreditation changes | Newsletter/podcast content freshness — stale news loses subscribers |
| **EHCP Audit / EDINET** | UK SEND Code of Practice updates, tribunal ruling patterns, local authority policy changes | Compliance corpus accuracy — GRUND evaluation requires current regulatory ground truth |
| **Pan-African Privacy** | NDPA (Nigeria), POPIA (SA), Kenya Data Protection Act amendments, AU convention updates | Compliance rule accuracy — wrong regulatory mapping = legal liability |
| **VilseckKI** | German data protection (DSGVO) guidance updates, BfDI opinions, state DPA enforcement actions | Client advisory accuracy — Notarin/Rechtsanwalt clients need current guidance |

The Beelink already runs overnight Data Forge synthetic data generation (primary development in `vilseckki-datafactory-app/`). RegWatch slots in as a continuous low-resource daemon alongside it — the monitoring checks are I/O-bound (HTTP fetches), not compute-bound, so they don't compete with LLM inference jobs.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BEELINK GTR9 PRO                            │
│                                                                     │
│  ┌────────────────────┐   ┌───────────────────┐   ┌──────────────┐ │
│  │ changedetection.io │   │     Ollama         │   │ regwatch.py  │ │
│  │ (Docker)           │   │ (already running)  │   │ (orchestrator│ │
│  │                    │   │                    │   │  + API)      │ │
│  │ Web UI: :5000      │   │ llama3.1:8b        │   │ Flask: :5050 │ │
│  │ REST API: :5000/api│   │ mistral:7b         │   │              │ │
│  └────────┬───────────┘   │ (or whatever's     │   └──────┬───────┘ │
│           │ webhook       │  loaded for other   │          │         │
│           │ on change     │  tasks)             │          │         │
│           ▼               └─────────┬───────────┘          │         │
│  ┌────────────────────┐             │                      │         │
│  │ Playwright browser │             │ Ollama API           │         │
│  │ (Docker, for JS    │             │ :11434               │         │
│  │  rendered pages)   │             │                      │         │
│  └────────────────────┘             │                      │         │
│                                     │                      │         │
│  regwatch.py flow:                  │                      │         │
│  1. Receive webhook ◄──────────────►│                      │         │
│  2. Look up domain config           │                      │         │
│  3. Send diff + context to Ollama ──┘                      │         │
│  4. Parse structured triage response                       │         │
│  5. Route notification per product config                  │         │
│  6. Append to change log (JSONL)                           │         │
│  7. Optionally create GitHub Issue                         │         │
│  8. Expose API for product queries ◄───────────────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────┐    ┌────────────────┐    ┌──────────────────┐
  │ Email    │    │ GitHub Issues  │    │ Product APIs     │
  │ (Resend) │    │ (per-repo)     │    │ (Tailscale)      │
  │          │    │ farafield-app  │    │ upskill-news-app │
  │          │    │ ehcpaudit-app  │    │ farafield-app    │
  └──────────┘    │ pap-app        │    └──────────────────┘
                  └────────────────┘
```

### Resource Budget on Beelink

| Component | RAM | CPU | Disk | Network |
|-----------|-----|-----|------|---------|
| changedetection.io | ~200MB idle, ~500MB during checks | Negligible | ~1GB for snapshots | ~50 requests/day |
| Playwright browser | ~300MB when active, 0 when idle | Burst during JS render | Minimal | Same requests |
| regwatch.py | ~50MB | Negligible | JSONL log grows ~1KB/day | Webhook receiver |
| Ollama triage calls | Shares existing Ollama instance | ~5-10 triage calls/day, <1min each | N/A | Local only |
| **Total additional** | **~550MB idle** | **Negligible** | **~1GB/year** | **~50 req/day** |

On a 128GB machine running Data Forge overnight jobs (see `vilseckki-datafactory-app/`), this is invisible.

---

## 3. Configuration System

### 3.1 Domain Registry (`domains.yaml`)

Each monitored product gets a domain configuration. This is the declarative heart of the system — adding a new product or URL requires only a YAML edit, no code changes.

```yaml
# domains.yaml — RegWatch domain registry

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

  upskill_news:
    display_name: "Upskill News"
    repo: "upskill-news-app"
    notify:
      email: "workflow.tools@icloud.com"
      github_issues: true
      github_repo: "mlupskill/upskill-news-app"
    urgency_routing:
      P0: [email]
      P1: [email]
      P2: [weekly_digest]
      P3: [log_only]

  ehcpaudit:
    display_name: "EHCP Audit / EDINET"
    repo: "ehcpaudit-app"
    notify:
      email: "workflow.tools@icloud.com"
    urgency_routing:
      P0: [email]
      P1: [weekly_digest]
      P2: [log_only]
      P3: [log_only]
```

### 3.2 Watch Lists (`watches/farafield.yaml`, `watches/upskill_news.yaml`, etc.)

Each product has its own watch list file. This keeps configs manageable and lets you add a new product without touching existing files.

```yaml
# watches/farafield.yaml

watches:
  # === TIER 1: DAILY ===
  - url: "https://www.make-it-in-germany.com/en/working-in-germany/professions-in-demand/nursing"
    check_interval: "1d"
    css_selector: ".content-main"  # skip nav/footer noise
    context:
      product: farafield
      corridors: ["ALL"]
      likely_steps: ["research_orientation", "visa_application", "job_search"]
      likely_fields: ["description", "resources", "tips"]

  - url: "https://www.gesetze-im-internet.de/aufenthg_2004/__16d.html"
    check_interval: "1d"
    context:
      product: farafield
      corridors: ["ALL"]
      likely_steps: ["visa_application"]
      likely_fields: ["description", "tasks"]

  - url: "https://www.gesetze-im-internet.de/aufenthg_2004/__30.html"
    check_interval: "1d"
    context:
      product: farafield
      corridors: ["ALL"]
      likely_steps: ["family_reunion_visa"]
      likely_fields: ["description", "tasks", "warnings"]
      note: "Spouse language requirement — monitors for changes to skilled worker exemption"

  - url: "https://www.gesetze-im-internet.de/beschv_2013/__38.html"
    check_interval: "1d"
    context:
      product: farafield
      corridors: ["NG_DE", "PK_DE"]
      likely_steps: ["research_orientation", "job_search"]
      likely_fields: ["warnings"]
      note: "WHO safeguard enforcement — §38 BeschV"

  # === TIER 1: WEEKLY ===
  - url: "https://www.nmcn.gov.ng/"
    check_interval: "7d"
    context:
      product: farafield
      corridors: ["NG_DE"]
      likely_steps: ["nmcn_clearance", "credential_documents"]
      likely_fields: ["tasks", "estimatedCostEur", "warnings"]

  - url: "https://visa.vfsglobal.com/nga/en/deu"
    check_interval: "7d"
    context:
      product: farafield
      corridors: ["NG_DE"]
      likely_steps: ["visa_application"]
      likely_fields: ["resources", "tips"]

  - url: "https://www.goethe.de/ins/tr/en/sta.html"
    check_interval: "7d"
    context:
      product: farafield
      corridors: ["TR_DE"]
      likely_steps: ["language_a1_a2", "language_b1", "language_b2"]

  - url: "https://www.goethe.de/ins/ng/en/sta.html"
    check_interval: "7d"
    context:
      product: farafield
      corridors: ["NG_DE"]
      likely_steps: ["language_a1_a2", "language_b1", "language_b2"]

  # === TIER 1: MONTHLY ===
  - url: "https://www.who.int/publications/i/item/9789240069787"
    check_interval: "30d"
    context:
      product: farafield
      corridors: ["NG_DE", "PK_DE"]
      likely_steps: ["research_orientation"]
      likely_fields: ["whoSafeguardListed", "warnings"]
      note: "WHO HWSS list — next update expected 2026"

  - url: "https://www.expatrio.com/"
    check_interval: "30d"
    css_selector: ".blocked-account, .pricing"
    context:
      product: farafield
      corridors: ["ALL"]
      likely_steps: ["blocked_account"]
      likely_fields: ["estimatedCostEur"]

  # === RSS FEEDS ===
  - url: "https://www.recht.bund.de/de/serviceseiten/rss/rss_node.html"
    type: rss
    check_interval: "1d"
    keyword_filter: "Pflege|Pflegefachkraft|Anerkennung|Fachkräfte|Aufenthaltsgesetz|Beschäftigungsverordnung|Pflegeberufegesetz"
    context:
      product: farafield
      corridors: ["ALL"]
      note: "Bundesgesetzblatt — German federal law gazette"

  - url: "https://offenegesetze.de/feeds"
    type: rss
    check_interval: "1d"
    keyword_filter: "Pflege|Anerkennung|Aufenthalt|Fachkräfte"
    context:
      product: farafield
      corridors: ["ALL"]
```

```yaml
# watches/upskill_news.yaml

watches:
  # University tuition / program changes
  - url: "https://www.daad.de/en/study-and-research-in-germany/plan-your-studies/costs-of-education-and-living/"
    check_interval: "7d"
    context:
      product: upskill_news
      categories: ["tuition", "germany"]
      note: "DAAD cost of studying in Germany — tuition policy changes"

  - url: "https://www.studis-online.de/StudInfo/Gebuehren/"
    check_interval: "30d"
    context:
      product: upskill_news
      categories: ["tuition", "germany"]
      note: "German university fees overview — tracks Bundesland-level tuition policy"

  - url: "https://www.make-it-in-germany.com/en/study-training"
    check_interval: "7d"
    context:
      product: upskill_news
      categories: ["visa", "study", "germany"]

  # UK student visa changes
  - url: "https://www.gov.uk/student-visa"
    check_interval: "7d"
    context:
      product: upskill_news
      categories: ["visa", "uk"]

  - url: "https://www.gov.uk/government/publications/immigration-rules-appendix-student"
    check_interval: "7d"
    context:
      product: upskill_news
      categories: ["visa", "uk", "immigration_rules"]

  # Scholarship feeds
  - url: "https://www.daad.de/en/study-and-research-in-germany/scholarships/"
    check_interval: "7d"
    context:
      product: upskill_news
      categories: ["scholarships", "germany"]

  # Accreditation / program changes
  - url: "https://www.wgu.edu/online-nursing-health-degrees.html"
    check_interval: "30d"
    context:
      product: upskill_news
      categories: ["programs", "nursing", "us"]
      note: "WGU nursing programs — tracks program launches/changes (NOT targeting WGU employees)"
```

### 3.3 Triage Prompt Templates (`prompts/`)

Product-specific triage prompts that give the LLM the right context for classification:

```yaml
# prompts/farafield_triage.yaml
system: |
  You are a regulatory change analyst for FarAfield, a B2C app guiding
  international nurses through country-specific licensure pathways to
  Germany and Austria. Pathway content is stored in JSON files with
  step-level granularity.

  Source countries: India, Nigeria, Colombia, Kenya, Nepal, Pakistan,
  Turkey, South Africa.
  Destinations: Germany (Bayern, NRW, Berlin), Austria (Wien, OÖ, Salzburg).

  Key regulatory domains: immigration law (AufenthG, BeschV), nursing
  recognition (PflBG, Anerkennung), WHO health workforce safeguards,
  language exam infrastructure (Goethe, telc, ÖSD), blocked account
  requirements, family reunion provisions.

template: |
  A monitored web page has changed. Analyze the diff and classify:

  MONITORED URL: {url}
  TAGGED CORRIDORS: {corridors}
  LIKELY STEPS: {likely_steps}
  CONTEXT NOTE: {note}

  DIFF:
  ---
  {diff_text}
  ---

  Respond in JSON:
  {{
    "relevance": "YES|NO|UNCLEAR",
    "urgency": "P0|P1|P2|P3",
    "affected_corridors": [],
    "affected_steps": [],
    "affected_fields": [],
    "summary": "",
    "recommended_action": ""
  }}

  Urgency guide:
  P0 = Active misinformation in current pathway (wrong requirement, wrong cost, wrong exemption)
  P1 = Missing new provision that benefits users (new visa type, fee reduction, processing speedup)
  P2 = Contextual update (processing time shift, new resource link, exam schedule change)
  P3 = No pathway impact (cosmetic page change, unrelated content, navigation restructure)
```

```yaml
# prompts/upskill_news_triage.yaml
system: |
  You are a news relevance analyst for Upskill News, a personalized
  newsletter and podcast service for international education seekers.
  Target audience: students and professionals considering study or
  career transitions in Germany, UK, US, Japan, and other destinations.

  Key domains: university tuition policy, student visa requirements,
  scholarship opportunities, program accreditation, admission deadlines,
  post-study work visa rules.

template: |
  A monitored web page has changed. Classify whether this is newsworthy:

  URL: {url}
  CATEGORIES: {categories}

  DIFF:
  ---
  {diff_text}
  ---

  Respond in JSON:
  {{
    "newsworthy": true|false,
    "urgency": "P0|P1|P2|P3",
    "categories": [],
    "headline": "",
    "summary": "",
    "affected_countries": [],
    "newsletter_priority": "lead|secondary|brief|skip"
  }}

  P0 = Major policy change affecting many students (tuition introduced/removed, visa category eliminated)
  P1 = Significant change (new scholarship, deadline moved, processing time shift)
  P2 = Minor update (fee adjustment, new resource link, minor program change)
  P3 = Not newsworthy (page redesign, unrelated content)
```

---

## 4. The Orchestrator (`regwatch.py`)

### Core Modules (~400 lines total)

```
regwatch/
├── __init__.py
├── app.py              # Flask app — webhook receiver + API
├── config.py           # Load domains.yaml + watches/*.yaml
├── triage.py           # Ollama triage call + response parsing
├── notify.py           # Email (Resend), GitHub Issues, digest
├── log.py              # JSONL append-only change log
├── api.py              # Query API for products to pull their changes
├── digest.py           # Weekly digest compiler + sender
└── cli.py              # Manual operations (add watch, test triage, replay)
```

### Key Design Decisions

**Webhook-driven, not polling.** changedetection.io does the polling and fires a webhook when a diff exceeds the threshold. regwatch.py only wakes up when there's actual work.

**Ollama model sharing.** regwatch uses whatever model is currently loaded in Ollama. If Data Forge is running a 70B overnight job (see `vilseckki-datafactory-app/`), regwatch queues behind it (Ollama serializes requests). During the day when nothing else is running, triage calls complete in <5 seconds on llama3.1:8b. This is fine — regulatory changes aren't sub-second urgent.

**Product-isolated change logs.** Each product gets its own JSONL file (`changes/farafield.jsonl`, `changes/upskill_news.jsonl`). Products can query their own changes via the API without seeing other products' data.

**Idempotent triage.** If changedetection.io fires the same webhook twice (network retry), regwatch deduplicates by hashing (url + diff_text + timestamp_hour). Same change in the same hour = skip.

### API Endpoints (for product consumption)

```
GET /api/changes/{product}?since=2026-04-01&urgency=P0,P1
  → Returns JSONL of changes for that product since the given date

GET /api/status
  → Returns system health: watches count, last check time, queue depth

POST /api/triage/test
  → Manual triage test: send a URL + fake diff, get triage result
```

The API runs on `:5050` and is accessible over Tailscale from the MacBook. This is how the upskill-news-app's assembler agent will pull detected changes to compile into newsletter content.

---

## 5. Integration with Upskill News

The upskill-news-app already has a crawler/assembler agent architecture (see `AGENT_DEVELOPMENT.md`):

| Agent Type | Current Purpose | RegWatch Enhancement |
|------------|----------------|---------------------|
| School Crawler | Fetches tuition updates from university websites | **Replace with RegWatch watches** — no custom scraping per school |
| Country Crawler | Extracts visa/admission requirements per country | **Replace with RegWatch watches** — monitor gov.uk, make-it-in-germany.com, etc. |
| Program Assembler | Structures data into newsletter/podcast formats | **Consumes RegWatch API** — pulls classified changes, assembles into content |

### How It Works

1. RegWatch monitors 20-30 education/visa/scholarship URLs (configured in `watches/upskill_news.yaml`)
2. When changes are detected and triaged, they're logged to `changes/upskill_news.jsonl`
3. The Upskill News assembler agent calls `GET /api/changes/upskill_news?since={last_newsletter_date}&urgency=P0,P1,P2`
4. The assembler uses the pre-triaged, pre-classified changes to compile the newsletter
5. Each change already has: `headline`, `summary`, `categories`, `affected_countries`, `newsletter_priority`

This means the Upskill News assembler doesn't need to crawl, parse, or classify — RegWatch already did that. The assembler focuses on editorial: ordering, tone, narrative, and podcast script generation.

**Beelink overnight pipeline becomes:**
```
22:00  RegWatch check cycle runs (all daily watches)
22:15  Data Forge starts overnight dataset generation (vilseckki-datafactory-app)
06:00  Data Forge completes
06:05  RegWatch compiles weekly digest (if it's digest day)
06:10  Upskill News assembler pulls changes, drafts newsletter
```

---

## 6. Integration with FarAfield

FarAfield's integration is notification-focused (not API-pull), because pathway JSON updates are manual (Rule 13: human verification required).

### Notification Flow

1. RegWatch detects change on a FarAfield-tagged URL
2. LLM triages → determines urgency and affected steps/corridors
3. P0/P1: Immediate email + GitHub Issue in farafield-app repo
4. GitHub Issue includes:
   - Diff summary
   - Affected corridors and steps
   - Specific JSON fields to check
   - Link to changedetection.io snapshot for full before/after
5. Human (you) verifies the change against primary source
6. Config thread updates the pathway JSON
7. Issue closed with commit reference

### Proposed GitHub Issue Template

```markdown
## Regulatory Change Detected

**Source:** {url}
**Detected:** {timestamp}
**Urgency:** {urgency}

### Impact
- **Corridors:** {corridors}
- **Steps:** {steps}
- **Fields:** {fields}

### Summary
{llm_summary}

### Recommended Action
{llm_recommended_action}

### Verification Needed
- [ ] Confirm change against primary regulatory source
- [ ] Update pathway JSON(s)
- [ ] Run validator.ts
- [ ] Remove any // UNVERIFIED markers after confirmation
- [ ] Update Regulatory-Monitor-Guide.md if landscape changed

### Diff Snapshot
[View in changedetection.io](http://100.x.y.z:5000/watch/{watch_id})
```

---

## 7. Future Product Integrations

### EHCP Audit / EDINET (when front-burner)

```yaml
# watches/ehcpaudit.yaml — example
watches:
  - url: "https://www.gov.uk/government/publications/send-code-of-practice-0-to-25"
    check_interval: "7d"
    context:
      product: ehcpaudit
      categories: ["send_code", "uk"]
      note: "SEND Code of Practice — foundational document for EHCP compliance"

  - url: "https://www.legislation.gov.uk/ukpga/2014/6/contents"
    check_interval: "30d"
    context:
      product: ehcpaudit
      categories: ["legislation", "uk"]
      note: "Children and Families Act 2014 — primary legislation"

  - url: "https://www.gov.uk/government/collections/send-tribunal-decisions"
    check_interval: "7d"
    context:
      product: ehcpaudit
      categories: ["tribunal", "uk"]
      note: "SEND tribunal decisions — tracks precedent-setting rulings"
```

### Pan-African Privacy (when front-burner)

```yaml
# watches/pap.yaml — example
watches:
  - url: "https://ndpc.gov.ng/"
    check_interval: "7d"
    context:
      product: pap
      categories: ["ndpa", "nigeria"]

  - url: "https://www.justice.gov.za/inforeg/"
    check_interval: "7d"
    context:
      product: pap
      categories: ["popia", "south_africa"]
```

Adding a new product to RegWatch is: (1) add a product entry to `domains.yaml`, (2) create `watches/{product}.yaml`, (3) optionally create `prompts/{product}_triage.yaml` for domain-specific triage. No code changes.

---

## 8. Implementation Roadmap

### Phase 1: Scaffold + FarAfield Core (Evening 1, ~2 hours)

```bash
# On Beelink via SSH/Tailscale
cd ~/regwatch
mkdir -p watches prompts changes

# Docker Compose up
docker compose up -d  # changedetection.io + Playwright

# Add first 10 FarAfield Tier 1 URLs via web UI (:5000)
# Configure webhook to http://localhost:5050/webhook
```

Deliverables:
- [ ] changedetection.io running and monitoring 10 URLs
- [ ] Webhook fires on detected change
- [ ] Manual verification that diffs are captured

### Phase 2: Orchestrator + Triage (Evening 2, ~3 hours)

```bash
# Write regwatch.py core modules
# Test with a synthetic diff against Ollama
# Verify email notification via Resend
```

Deliverables:
- [ ] `regwatch.py` webhook receiver + Ollama triage working
- [ ] Email notification fires for P0/P1
- [ ] JSONL log captures all triage results
- [ ] Test triage endpoint works

### Phase 3: Full FarAfield Coverage + RSS (Evening 3, ~2 hours)

Deliverables:
- [ ] All 35-40 FarAfield URLs configured
- [ ] RSS feeds (Bundesgesetzblatt, OffeneGesetze) configured with keyword filters
- [ ] GitHub Issue auto-creation for P0s
- [ ] Weekly digest cron job

### Phase 4: Upskill News Integration (When front-burner, ~2 hours)

Deliverables:
- [ ] `watches/upskill_news.yaml` with 20-30 education/visa URLs
- [ ] `prompts/upskill_news_triage.yaml` with news-specific classification
- [ ] API endpoint tested with assembler agent
- [ ] Newsletter compilation from RegWatch feed demonstrated

### Phase 5: Refinement + Extraction Assessment (~ongoing)

- Tune triage prompts based on false positive/negative rate
- Add CSS selector refinement for noisy pages
- Assess whether the tool is extractable as standalone product
- If yes, create dedicated `regwatch-app/` repo with clean packaging

---

## 9. File Layout in beelink-bonus

```
beelink-bonus/
├── regwatch/                    # NEW — RegWatch system
│   ├── docker-compose.yaml      # changedetection.io + Playwright
│   ├── regwatch/                # Python package
│   │   ├── __init__.py
│   │   ├── app.py               # Flask webhook receiver + API
│   │   ├── config.py            # YAML loader
│   │   ├── triage.py            # Ollama integration
│   │   ├── notify.py            # Resend + GitHub Issues
│   │   ├── log.py               # JSONL writer
│   │   ├── api.py               # Product query API
│   │   ├── digest.py            # Weekly digest
│   │   └── cli.py               # Manual operations
│   ├── domains.yaml             # Product registry
│   ├── watches/                 # Per-product watch lists
│   │   ├── farafield.yaml
│   │   ├── upskill_news.yaml
│   │   └── ehcpaudit.yaml       # Placeholder for when front-burner
│   ├── prompts/                 # Per-product triage prompts
│   │   ├── farafield_triage.yaml
│   │   └── upskill_news_triage.yaml
│   ├── changes/                 # Per-product JSONL logs
│   │   ├── farafield.jsonl
│   │   └── upskill_news.jsonl
│   ├── requirements.txt         # flask, requests, pyyaml, resend
│   └── README.md                # Setup guide
├── data-forge/                  # Symlink or reference — primary development in vilseckki-datafactory-app/
├── docs/
│   ├── REGWATCH-RD-PAYLOAD.md   # This document
│   └── ...
└── ...
```

---

## 10. Micro-SaaS Extraction Criteria

RegWatch becomes a standalone product when:

1. **It proves value for 2+ products** — FarAfield + Upskill News confirms the pattern generalizes
2. **The LLM triage quality is consistently good** — <10% false positive rate, <5% false negative on P0/P1
3. **The config-driven approach scales** — adding a new product takes <30 minutes of YAML writing
4. **There's a clear pricing model** — self-hosted ($49/mo license?), or hosted SaaS ($19-99/mo by watch count?)
5. **The market is validated** — compliance teams, immigration consultancies, regulatory affairs departments

If all five are true, extract to `regwatch-app/` and list on Product Hunt / Indie Hackers. The Beelink continues running the internal instance; the product version adds multi-user auth, a web dashboard, and Stripe billing.

Target market: any business where wrong regulatory information = liability. Immigration law firms, pharma regulatory affairs, financial compliance, professional licensing boards, EdTech platforms with visa/accreditation content.

---

## 11. Relationship to Dissertation (GRUND)

The RegWatch → FarAfield pipeline creates a measurable case study for GRUND:

- **Regulatory change velocity:** How often do nurse migration regulations actually change? The `changes/farafield.jsonl` log provides empirical data.
- **AI triage accuracy:** How well does a 7-8B parameter LLM classify regulatory changes? Precision/recall against human verification.
- **Compliance monitoring automation:** The triage prompt is a simplified version of GRUND's multi-agent debate — one agent reads, one classifies, the human verifies. This is the "single-agent baseline" that GRUND's multi-agent approach should outperform.

If you write up the RegWatch evaluation methodology, it could serve as preliminary work for a GRUND paper section on "automated regulatory monitoring as input to compliance evaluation systems."
