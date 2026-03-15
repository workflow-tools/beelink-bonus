# Synthetic Data Factory — Beelink Passive Revenue Plan

> **Purpose:** Turn the Beelink GTR9 Pro into a synthetic data generation factory that runs on cron jobs overnight, packages sellable datasets, and lists them on Datarade + HuggingFace.
> **Owner:** Ryan Hill / ML Upskill Agents UG
> **Date:** March 2026
> **Time budget:** 15-25 min/day maintenance once set up
> **Revenue target:** EUR 200-600/month within 3-6 months (covers itself + funds other projects)

---

## Why This Track Instead Of (Or Alongside) the RAG Service

The VilseckKI RAG service (documented in `VILSECKKI-FINAL-ARCHITECTURE.md`) requires active client acquisition, legal contracts (AVV, § 203 StGB), and ongoing support. It's the higher-ceiling play but demands more attention.

The **Synthetic Data Factory** is the hands-off complement:

| | RAG Service | Data Factory |
|---|---|---|
| Revenue model | Monthly retainer per client | Per-dataset sales + marketplace royalties |
| Client interaction | Ongoing support | Zero (marketplace handles it) |
| Legal complexity | AVV, § 203, DSGVO per client | Minimal (you're selling synthetic data, not processing anyone's real data) |
| Time to first euro | 3-4 weeks (pilot + legal) | 1-2 weeks (generate + list) |
| Scaling | Limited by hardware capacity | Unlimited (generate more datasets) |
| Daily attention | Client issues, uptime monitoring | Check generation logs, package results |

**These two tracks share the same Beelink setup.** Ollama, the OS, Tailscale — all identical. The factory runs when clients aren't querying. They're not competing; they're complementary.

---

## The Pipeline: How It Actually Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYNTHETIC DATA FACTORY                        │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  DEFINE   │───>│ GENERATE │───>│ VALIDATE │───>│ PACKAGE  │  │
│  │          │    │          │    │          │    │          │  │
│  │ Schema   │    │ SDV/     │    │ Evidently│    │ CSV +    │  │
│  │ Config   │    │ CTGAN +  │    │ stats    │    │ metadata │  │
│  │ YAML     │    │ Ollama   │    │ tests    │    │ card +   │  │
│  │          │    │ for text │    │          │    │ report   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                       │         │
│                                              ┌────────┴───────┐ │
│                                              │    PUBLISH     │ │
│                                              │                │ │
│                                              │ • Datarade     │ │
│                                              │ • HuggingFace  │ │
│                                              │ • vilseckki.de │ │
│                                              └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: DEFINE — Dataset Schema Configs

Each dataset type gets a YAML config file:

```yaml
# configs/mittelstand-b2b.yaml
dataset:
  name: "synthetic-bavarian-mittelstand-b2b"
  version: "1.0"
  records: 50000
  language: "de"
  description: "Synthetic German SME business dataset with companies, financials, supplier relationships"

schema:
  tables:
    - name: companies
      columns:
        - name: firma_name
          type: text
          generator: ollama  # LLM-generated German company names
          model: "llama3.1:70b-instruct-q4_K_M"
          prompt: "Generate a realistic German Mittelstand company name in the {industry} sector, located in {region}. Return ONLY the company name."
        - name: rechtsform
          type: categorical
          values: ["GmbH", "GmbH & Co. KG", "AG", "UG (haftungsbeschränkt)", "e.K.", "OHG"]
          weights: [0.45, 0.20, 0.05, 0.15, 0.10, 0.05]
        - name: branche
          type: categorical
          values: ["Maschinenbau", "Automotive", "Elektrotechnik", "Chemie", "Pharma", "IT-Dienstleistungen", "Handwerk", "Logistik"]
        - name: jahresumsatz_eur
          type: numeric
          distribution: lognormal
          params: {mean: 14.5, std: 1.8}  # centered around EUR 2M
        - name: mitarbeiter_anzahl
          type: numeric
          distribution: lognormal
          params: {mean: 3.5, std: 1.2}  # centered around 33 employees
        - name: plz
          type: text
          generator: weighted_sample
          source: "data/german_plz_bayern.csv"
        # ... more columns

generation:
  method: "ctgan"  # or "copula", "gaussiancopula"
  epochs: 500
  batch_size: 500
  ollama_concurrent: 2  # parallel LLM calls for text fields
  ollama_model: "llama3.1:70b-instruct-q4_K_M"  # or 7b for faster runs

validation:
  evidently_tests:
    - column_distribution_similarity
    - column_value_range
    - no_nulls
    - unique_ratio
  custom_checks:
    - german_plz_valid
    - rechtsform_consistent_with_size
```

### Step 2: GENERATE — The Cron Job

The generation script reads a config, runs SDV/CTGAN for tabular structure, then calls Ollama for text augmentation.

```
Cron schedule: Run nightly 22:00 - 06:00 (when you're not using the Beelink)
              Or: Run whenever Beelink is idle (detect via load average)
```

**Generation flow per dataset:**
1. Load schema config YAML
2. If seed/reference data exists, fit CTGAN model to it
3. If no seed data, use GaussianCopula with distribution parameters from config
4. Generate N records of tabular data
5. For each text field marked `generator: ollama`:
   - Queue Ollama inference calls (batched, 2 concurrent)
   - Replace placeholder values with LLM-generated German text
6. Save raw output to `/opt/vilseckki/factory/output/{dataset_name}/{version}/raw/`

**Time estimates per dataset (on Beelink):**

| Dataset Size | Tabular Only | + LLM Text (7B) | + LLM Text (70B) |
|---|---|---|---|
| 10K records | ~2 min | ~30 min | ~3 hours |
| 50K records | ~10 min | ~2.5 hours | ~15 hours |
| 100K records | ~20 min | ~5 hours | ~30 hours |

The 70B model is slow but produces dramatically better German text. Use 70B for premium datasets, 7B for volume.

### Step 3: VALIDATE — Automated Quality Checks

After generation completes, run Evidently + custom validators:

```python
# validate.py (simplified)
from evidently.report import Report
from evidently.metric_preset import DataQualityPreset, DataDriftPreset

report = Report(metrics=[DataQualityPreset(), DataDriftPreset()])
report.run(reference_data=seed_data, current_data=synthetic_data)
report.save_html(f"output/{name}/{version}/validation_report.html")

# Custom: check German PLZ validity, name plausibility, etc.
# Custom: statistical representativeness tests
# Output: PASS/FAIL + detailed metrics JSON
```

**Validation generates three artifacts:**
1. `validation_report.html` — visual report (include as preview for buyers)
2. `validation_metrics.json` — machine-readable quality scores
3. `PASS`/`FAIL` flag file — only PASS datasets get packaged

### Step 4: PACKAGE — Dataset Card + Delivery Bundle

Each sellable dataset is a zip containing:

```
synthetic-bavarian-mittelstand-b2b-v1.0/
├── data/
│   ├── companies.csv
│   ├── transactions.csv  (if relational)
│   └── supplier_relationships.csv  (if relational)
├── metadata/
│   ├── datasheet.md          # Gebru-style dataset datasheet
│   ├── schema.json           # Column types, descriptions, constraints
│   ├── generation_config.yaml # Reproducibility: exact config used
│   └── statistics.json       # Summary stats per column
├── validation/
│   ├── validation_report.html
│   └── quality_metrics.json
├── samples/
│   └── preview_100_rows.csv  # Free preview for marketplace listing
└── LICENSE.md                # CC-BY-4.0 or commercial license
```

The **datasheet.md** is the key differentiator. It follows the "Datasheets for Datasets" standard (Gebru et al.) and includes:
- Motivation: why this dataset was created
- Composition: what's in it, what's NOT in it
- Collection process: generation methodology (CTGAN + LLM augmentation)
- Preprocessing: cleaning steps applied
- Uses: intended use cases, out-of-scope uses
- Distribution: how it's licensed
- Maintenance: update schedule, contact

**This datasheet is what the EU AI Act compliance micro-SaaS opportunity looks like in practice.** Each datasheet you produce is a template for the eventual "AI Act Dataset Card Generator" tool.

### Step 5: PUBLISH — Marketplace Listings

**Datarade (primary revenue):**
- Commission-based: you list for free, Datarade takes a cut on sales
- Create a provider profile for "ML Upskill Agents UG" or "VilseckKI"
- Each dataset gets a listing with: description, preview sample, schema, use cases
- Pricing: set per dataset (one-time purchase or subscription for updates)

**HuggingFace (visibility + lead generation):**
- List a free preview version (1K records instead of 50K)
- Full version links to Datarade or vilseckki.de for purchase
- Builds academic credibility (PhD + citations)
- HuggingFace dataset cards use the same format as your datasheets

**vilseckki.de (boutique orders, later):**
- Simple order form: "I need a synthetic dataset for [domain]. [Schema requirements]. [Size]."
- You generate it on the Beelink, validate, deliver via email/download link
- Premium pricing: EUR 500-5,000 per custom dataset
- This is the "local Bavarian AI boutique" positioning

---

## What To Generate First (Priority Order)

### Dataset 1: Synthetic Bavarian Mittelstand B2B (FIRST — do this)

**Why first:**
- You identified this already in the briefing — it's the fastest to market
- German SME data is genuinely scarce (most synthetic datasets are US-centric)
- Buyers: SAP ecosystem vendors, Datev integrators, IHK tech programs, AI startups testing German-market products
- No real data privacy issues (companies are fictional)
- Exercises the full pipeline end-to-end

**What's in it:**
- 50K synthetic German companies (name, Rechtsform, Branche, Umsatz, Mitarbeiter, PLZ, Ort, Bundesland)
- 200K synthetic transactions between companies (Rechnungen, Bestellungen, Lieferungen)
- 30K synthetic employee records (anonymized HR data: Abteilung, Gehalt range, Betriebszugehörigkeit)
- German-language free text fields: Firmenname, Produktbeschreibung, Rechnungstext

**LLM advantage:** The 70B model generates convincingly German company names like "Müller Maschinenbau GmbH & Co. KG" or "Bayerische Präzisionstechnik UG" — things that look real but aren't. A 7B model or rule-based generator can't match this quality.

**Time to generate:** ~1 overnight run (8 hours) for full 50K + text augmentation on 70B
**Time to validate + package:** ~2 hours manual review + automated Evidently run
**Time to list on Datarade:** ~1 hour (create listing, write description, upload sample)

**Price point:** EUR 300-500 one-time, or EUR 99/month for quarterly refreshed versions

### Dataset 2: German Customer Service Dialogues (Krankenkasse)

**Why second:**
- Your 70B model competitive moat is strongest here
- Nobody else can generate 50K realistic German Krankenkasse conversations locally
- Insurtech/fintech startups building German chatbots need this desperately
- The conversations are multi-turn JSONL — a format AI teams consume directly

**What's in it:**
- 50K synthetic multi-turn dialogues (3-8 turns each)
- Domain: health insurance (Krankenkasse) customer service
- Topics: Beitragssatz, Krankengeld, Zahnersatz, Kündigung, Familienversicherung, Bonusprogramm
- Annotations: speaker role, topic label, sentiment, resolution status
- Mix of formal (schriftlich) and informal (telefonisch) register

**LLM advantage:** This is almost entirely LLM-generated. The 70B model understands German insurance terminology and can produce natural-sounding multi-turn conversations. This dataset literally cannot be made without a large language model.

**Time to generate:** ~2-3 overnight runs (each producing ~15-20K dialogues)
**Price point:** EUR 1,000-2,000

### Dataset 3: EU AI Act Compliance Stress-Test Data

**Why third:**
- Directly tied to the Bavarian AI Act Accelerator funding (LMU/TUM project, EUR 1.6M through Dec 2026)
- Bavarian SMEs are being handed money to achieve compliance but need test data
- This is the most defensible niche — you understand both the AI Act requirements AND how to generate the data
- PhD alignment: simulated data validation methodology

**What's in it:**
- 5 domain packages (employment screening, credit scoring, educational access, insurance pricing, housing allocation)
- Each package: 10K records with protected attributes (age, gender, origin — synthetically generated)
- Intentionally includes both balanced and imbalanced versions (so companies can test their bias detection)
- Metadata card documenting exactly which AI Act requirements each dataset helps test
- Statistical validation report per Evidently

**Price point:** EUR 500-2,500 per domain package

### Datasets 4-5: Healthcare (EHDS) and Agricultural Time-Series

These are higher-value, more specialized datasets that build on the pipeline you've already proven with datasets 1-3. They also connect to your other projects (EHCP Audit needs simulated patient data methodology; agriculture connects to the Japan market). Generate these after the pipeline is proven and the first sales validate demand.

---

## Beelink Setup for the Factory

### What Needs to Be Installed

The Beelink needs the same base setup as the RAG service, plus the data generation stack:

```
Beelink GTR9 Pro (AMD AI Max+ 395, 128GB)
├── OS: Windows initially, Ubuntu Server later
├── Ollama (GPU-accelerated inference)
│   ├── llama3.1:70b-instruct-q4_K_M    (~40GB VRAM)
│   ├── mistral:7b-instruct-q4_K_M      (~4.5GB)
│   └── nomic-embed-text                 (for any RAG needs)
├── Python 3.11+ environment
│   ├── sdv                    # Synthetic Data Vault (CTGAN, GaussianCopula)
│   ├── evidently              # Data validation & quality reports
│   ├── pdfplumber             # (shared with RAG pipeline)
│   ├── langchain              # (shared with RAG pipeline)
│   ├── faker                  # Supplementary fake data (addresses, phone numbers)
│   ├── pyyaml                 # Config parsing
│   └── requests / httpx       # Ollama API calls
├── Tailscale (remote access from MacBook)
└── Factory scripts
    ├── factory/
    │   ├── configs/           # Dataset schema YAML files
    │   ├── generators/        # Python generation scripts
    │   ├── validators/        # Evidently + custom validation
    │   ├── packagers/         # Bundle into deliverable zips
    │   ├── seeds/             # Reference/seed data for fitting models
    │   ├── output/            # Generated datasets (organized by name/version)
    │   └── cron/              # Scheduler scripts
    └── logs/                  # Generation run logs
```

### Cron Architecture

**Option A: Simple cron (recommended for start)**
```bash
# /etc/crontab (Linux) or Task Scheduler (Windows)
# Run factory at 22:00 every night, kill at 06:00
0 22 * * * /opt/vilseckki/factory/cron/start-generation.sh
0  6 * * * /opt/vilseckki/factory/cron/stop-generation.sh
```

**Option B: Smart scheduling (later)**
```bash
# Only run when system load is below threshold (no RAG clients active)
# Check every 15 minutes, start generation if idle
*/15 * * * * /opt/vilseckki/factory/cron/idle-check-and-generate.sh
```

The `start-generation.sh` script:
1. Checks which datasets in `configs/` are due for (re)generation
2. Picks the highest-priority unfinished dataset
3. Runs the generation script with a time limit (kills at 06:00)
4. If generation completes, runs validation
5. If validation passes, runs packaging
6. Logs everything to `logs/YYYY-MM-DD-{dataset_name}.log`
7. Sends a summary notification (email, Telegram, or Tailscale push)

### Remote Monitoring (Your 15-25 min/day)

From your MacBook via Tailscale:

```bash
# SSH into Beelink
ssh beelink

# Check last night's generation
cat /opt/vilseckki/factory/logs/$(date -d yesterday +%Y-%m-%d)*.log | tail -50

# Check output directory for new completed datasets
ls -la /opt/vilseckki/factory/output/*/latest/

# Check disk usage
df -h

# Check Ollama is healthy
curl http://localhost:11434/api/tags
```

That's a 5-minute check. The rest of your 15-25 minutes goes to:
- Reviewing validation reports for completed datasets (~5 min)
- Tweaking configs for next generation run (~5 min)
- Listing completed datasets on Datarade/HuggingFace (~10 min, only when new datasets are ready)

---

## Tailscale: Controlling Beelink from MacBook

You mentioned Google gave you Tailscale directions previously. Here's the verified setup:

### Initial Setup (One-Time, In-Person)

**On the Beelink:**
1. Install Tailscale: https://tailscale.com/download (Windows installer or `curl -fsSL https://tailscale.com/install.sh | sh` on Linux)
2. Sign in with your Google/GitHub account
3. Note the Tailscale IP (e.g., `100.x.y.z`)
4. Enable SSH: in Tailscale admin console (https://login.tailscale.com/admin/machines), click the Beelink machine → enable SSH

**On your MacBook:**
1. Install Tailscale: `brew install tailscale` or download from https://tailscale.com/download/mac
2. Sign in with the SAME account
3. Test: `ssh ryan@100.x.y.z` (or whatever user the Beelink runs as)
4. Test: `curl http://100.x.y.z:11434/api/tags` (should show Ollama models)

**After initial setup, you can control the Beelink from anywhere in the world:**
- SSH for terminal access (check logs, restart services, tweak configs)
- SCP/rsync for file transfer (download completed datasets to MacBook for listing)
- Tailscale is free for personal use (up to 100 devices)
- Works through NATs, firewalls, hotel Wi-Fi, military base networks — no port forwarding needed

### Daily Workflow

```
Morning (5 min from MacBook):
  ssh beelink → check overnight logs → verify datasets generated

If new dataset completed (10-15 min, once per week):
  rsync beelink:/opt/vilseckki/factory/output/latest/ ~/Downloads/datasets/
  Review validation report in browser
  Upload to Datarade / HuggingFace

Evening (2 min):
  ssh beelink → verify cron job is queued for tonight → logout
```

---

## Revenue Model

### Datarade Listings (Primary)

| Dataset | Price (One-Time) | Price (Subscription) | Est. Sales/Month |
|---|---|---|---|
| Bavarian Mittelstand B2B (50K) | EUR 499 | EUR 99/mo | 1-2 |
| German Krankenkasse Dialogues (50K) | EUR 1,499 | EUR 199/mo | 0-1 |
| AI Act Compliance Stress-Test (per domain) | EUR 999 | EUR 149/mo | 1-2 |
| German Legal Document Templates (synthetic) | EUR 799 | — | 0-1 |
| Agricultural Time-Series (Bavaria) | EUR 599 | EUR 99/mo | 0-1 |

**Conservative month 3 estimate:** 2-3 one-time sales + 1-2 subscriptions = EUR 200-600/month

### HuggingFace (Lead Generation)

- Free preview versions (1K records) of each dataset
- Links to Datarade for full version
- Builds citation count and academic credibility
- Some researchers will contact you directly for custom versions → boutique orders

### vilseckki.de Boutique Orders (Later)

Once you have 5+ datasets listed and some Datarade sales proving demand:
- Simple contact form: "Describe the synthetic dataset you need"
- You quote, they pay via Überweisung, you generate on the Beelink
- Premium pricing: EUR 500-5,000 per custom dataset
- The existing datasets serve as your portfolio/examples

---

## Connection to Your Other Projects

### EHCP Audit / IEP Checker
- The synthetic patient/student data generation methodology you develop here directly feeds into the GRUND framework's need for test data
- Synthetic EHCP documents (generated by the 70B model) could be used to benchmark the multi-agent debate system
- The validation pipeline (Evidently) transfers directly to validating AI outputs in those products

### Dissertation
- **Seed 4 (solo developer automation stack):** The factory pipeline IS an automation stack — idea → generate → validate → package → sell, all automated
- **Methodology contribution:** Synthetic data validation methodology using Evidently + custom domain checks is publishable
- **Data for experiments:** You can generate controlled synthetic datasets for any dissertation experiment without API costs

### Assessment Wizard / Faculty Wizard
- Synthetic student assessment data (grades, feedback, rubric scores) could be a sellable dataset AND useful for testing your own products
- The "AI Act Dataset Card Generator" micro-SaaS idea from the briefing builds directly on the datasheet.md templates you'll create for each dataset

### EU AI Act Compliance Micro-SaaS (Flagged Opportunity)
The briefing correctly identified this: a lightweight tool that takes ANY dataset and auto-generates a compliant EU AI Act dataset card. You'll build this capability for your own datasets first. Once it works, productize it as a standalone tool at EUR 29-99/month. The Bavarian AI Act Accelerator audience (LMU/TUM companies) is the exact customer.

---

## Implementation Timeline

### Week 1: Foundation (In-Person at Beelink)

- [ ] **Day 1-2: Beelink base setup**
  - Install Ollama, set `HSA_OVERRIDE_GFX_VERSION=11.0.0`
  - Pull models: `llama3.1:70b-instruct-q4_K_M`, `mistral:7b-instruct-q4_K_M`
  - Benchmark: actual tok/s on your hardware (this determines generation time estimates)
  - Install Python 3.11+, create venv, install sdv + evidently + faker + pyyaml
  - Install Tailscale, verify SSH from MacBook

- [ ] **Day 3: First generation test**
  - Write a minimal config for a 1K-record test dataset (simple Mittelstand companies)
  - Run CTGAN generation (tabular only, no LLM text yet)
  - Run Evidently validation on the output
  - Verify the end-to-end pipeline works

- [ ] **Day 4-5: Add LLM text augmentation**
  - Write Ollama integration: Python script that takes a tabular dataset + column config and replaces placeholder text fields with LLM-generated German text
  - Test with 7B model first (fast), then 70B (quality check)
  - Measure: how long does 1K records × 3 text fields take on each model?

### Week 2: First Real Dataset (Can Be Remote via Tailscale)

- [ ] **Day 6-7: Mittelstand B2B dataset config**
  - Write full YAML config for 50K-record Mittelstand dataset
  - Gather seed data: German PLZ list, Branche categories, Rechtsform distribution stats
  - Set up generation script that reads config and produces output

- [ ] **Day 8: Overnight generation run**
  - Start 50K generation at 22:00, check progress at 06:00
  - Validate output with Evidently
  - Manual spot-check: do the German company names look real? Are the financial distributions plausible?

- [ ] **Day 9-10: Package and list**
  - Create datasheet.md (Gebru format)
  - Create schema.json
  - Bundle into deliverable zip
  - Create 100-row preview CSV
  - Sign up for Datarade provider account
  - Create first listing
  - Upload preview to HuggingFace

### Week 3: Cron Automation + Second Dataset

- [ ] Set up cron job for nightly generation
- [ ] Write `start-generation.sh` and `stop-generation.sh`
- [ ] Set up log rotation and monitoring
- [ ] Start German Krankenkasse dialogue dataset config
- [ ] Begin generating dialogue data (this takes 2-3 overnight runs)

### Week 4+: Iterate and Expand

- [ ] List Krankenkasse dialogues on Datarade
- [ ] Start AI Act compliance stress-test dataset design
- [ ] Monitor Datarade analytics: views, inquiries, downloads
- [ ] Adjust pricing based on market response
- [ ] Begin planning vilseckki.de boutique order page (simple static site)

---

## Cost Analysis

| Item | Monthly Cost |
|---|---|
| Beelink electricity (~65W, 24/7) | ~EUR 14 |
| Tailscale (free tier) | EUR 0 |
| Datarade provider account | EUR 0 (commission on sales) |
| HuggingFace | EUR 0 |
| Python packages (all open-source) | EUR 0 |
| vilseckki.de domain (when ready) | ~EUR 0.50 |
| **Total monthly operating cost** | **~EUR 15** |

**Break-even: one EUR 99/month subscription or one EUR 300+ one-time sale every 2 months.**

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| No one buys on Datarade | MEDIUM | HuggingFace visibility drives direct inquiries. Datarade is one channel, not the only one. |
| Generated data quality too low | LOW | Evidently validation catches issues before listing. 70B model produces high-quality German text. |
| CTGAN/SDV don't run on AMD | LOW | These tools are CPU-based (no GPU needed). They'll run on literally any computer. |
| Ollama GPU issues on Beelink | MEDIUM | Test Day 1. Fall back to CPU-only Ollama if needed (slower but works). |
| Someone else does this first | LOW | German-language synthetic data is a niche nobody is serving. Your 70B local model is a genuine competitive advantage. |
| Dataset gets pirated/reshared | MEDIUM | Offer free previews to reduce piracy incentive. Premium value is in the validation report + datasheet, not just the CSV. |

---

## Decision: Can It Be Done?

**Yes.** Here's why this is realistic for your situation:

1. **The tools exist and are free.** SDV, CTGAN, Evidently, Ollama, Faker — all open-source, all CPU-compatible, all well-documented.

2. **The hardware is overkill for tabular generation.** CTGAN training on 50K records uses maybe 8GB RAM and one CPU core. Your 128GB machine laughs at this. The 70B model for text augmentation is where the hardware shines — nobody on a consumer GPU can match this.

3. **The time budget works.** Once the pipeline is built (Week 1-2 investment), the daily maintenance is genuinely 15-25 minutes: check logs, review output, occasionally tweak a config or list a new dataset.

4. **The market gap is real.** Search Datarade for "synthetic German business data" or "synthetische Unternehmensdaten" right now. You'll find almost nothing. The EU AI Act is creating forced demand for exactly this.

5. **It compounds.** Each dataset you list is a permanent asset. Month 1 you have 1 listing. Month 6 you have 8-10 listings. The catalog grows while your daily effort stays constant.

6. **It feeds everything else.** The methodology becomes dissertation material. The validation pipeline helps your other products. The EU AI Act datasheet templates become a micro-SaaS. The Datarade presence makes the vilseckki.de boutique credible.

The honest constraint: **Week 1 requires in-person time at the Beelink** (2-3 focused evenings for setup and testing). After that, it's all remote via Tailscale.

---

## Files in This Plan

| File | Purpose |
|---|---|
| `SYNTHETIC-DATA-FACTORY-PLAN.md` | **This file** — the master plan |
| `CLAUDE.md` | Beelink hardware context + existing project portfolio |
| `VILSECKKI-FINAL-ARCHITECTURE.md` | RAG service architecture (complementary track) |
| `BEELINK-PASSIVE-REVENUE-STRATEGY.md` | Original market analysis (still valid for pricing/GTM) |

---

## Open Questions

- [ ] Is the Beelink currently set up (OS installed, powered on, network connected)?
- [ ] Do you have physical access to it right now, or do you need to wait for a trip home?
- [ ] Is Tailscale already installed from the previous Google directions?
- [ ] Do you want to register vilseckki.de now, or wait until the first dataset is listed?
- [ ] For the Mittelstand dataset: do you have access to any real German business statistics (Statistisches Bundesamt, IHK reports) to use as seed distributions? (Not required — we can use published aggregate statistics.)
