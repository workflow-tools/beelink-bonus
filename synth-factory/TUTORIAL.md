# Japan Data Factory for Dummies

> A plain-English guide to generating synthetic Japanese financial documents
> with the VilseckKI Synth-Factory running on your Beelink GTR9 Pro.

---

## What Are We Building?

The synth-factory produces **synthetic Japanese securities reports** (有価証券報告書 / ゆうかしょうけんほうこくしょ — "yūka shōken hōkokusho"). These are the annual disclosure filings that every publicly listed company in Japan must submit to the Financial Services Agency (金融庁 / きんゆうちょう — FSA) through the EDINET system.

Each synthetic document has 8 sections generated segment-by-segment by a 70-billion-parameter language model running locally on your machine. No data leaves your network. The output is sold on data marketplaces (JDEX, Datarade) to AI researchers who need high-quality Japanese financial text for training NLP models.

**Who buys this?** Companies building document understanding AI, compliance testing tools, financial text extractors, and benchmark datasets — anyone who needs realistic Japanese financial prose but cannot use real filings (due to privacy, licensing, or volume constraints).


## Hardware Setup

You need one machine with a GPU that can run a 70B quantized model at acceptable speed:

**Beelink GTR9 Pro** (or equivalent)
- AMD Ryzen 9 7940HS
- 64 GB RAM (minimum 32 GB for the 4-bit quantized model)
- Ollama installed and running

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model (this downloads ~40 GB)
ollama pull llama3.1:70b-instruct-q4_K_M

# Verify it's running
ollama list
```


## Software Setup

```bash
# Clone the repo
git clone <your-repo-url> synth-factory
cd synth-factory

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install R for post-generation validation
sudo apt install r-base
Rscript -e 'install.packages(c("jsonlite", "dplyr", "tidyr", "ggplot2", "optparse", "fitdistrplus"))'

# Optional: Install the edinetsynth R package for tidy data access
Rscript -e 'devtools::install("R/edinetsynth")'
```


## Your First Dataset (5-Minute Test Run)

Before committing to a multi-day generation run, verify everything works with a tiny test:

```bash
# Generate 3 documents with a small model (fast, low quality)
python generate_edinet.py \
  --skip-scrape \
  --records 3 \
  --config configs/test-tiny.yaml

# Check the output
ls output/test-tiny/
cat output/test-tiny/data/test_docs.jsonl | python -m json.tool | head -50
```

If you see JSON documents with `seg_company_overview`, `seg_business_risks`, etc., you're in business.


## The Full Pipeline

The `generate_edinet.py` script chains three phases:

### Phase 1: Scrape (optional)

Downloads real EDINET filings to build a flaw taxonomy — a statistical profile of common issues in real securities reports (empty sections, boilerplate language, formatting problems).

```bash
# Scrape the last 30 days of EDINET filings
python generate_edinet.py --api-key YOUR_EDINET_KEY --scrape-days 30
```

You need an EDINET API key from the FSA (free registration at https://disclosure2.edinet-fsa.go.jp/). If you already have a flaw taxonomy from a previous run, skip this step with `--skip-scrape`.

### Phase 2: Taxonomy Update

Automatically analyzes scraped filings and builds `flaw_taxonomy.json` — a weighted table of real-world document issues. This feeds the error injection system so synthetic flaws match the statistical distribution of real ones.

### Phase 3: Generate

Produces the actual synthetic documents. Each document is generated segment-by-segment:

1. **Company Overview** (企業の概況 / きぎょうのがいきょう) — Creates a fictional company
2. **Business Status** (事業の状況 / じぎょうのじょうきょう) — Strategy and KPIs, referencing the company created in step 1
3. **Business Risks** (事業等のリスク / じぎょうとうのリスク) — Risk factors specific to this company
4. **MD&A** (経営分析 / けいえいぶんせき) — Financial analysis with numbers matching the overview
5. **Corporate Governance** (ガバナンス) — Board structure and compliance
6. **Stock Information** (株式等の状況 / かぶしきとうのじょうきょう) — Share data
7. **Directors** (役員の状況 / やくいんのじょうきょう) — 5-8 board members with unique biographies
8. **Financial Highlights** (経理の状況 / けいりのじょうきょう) — Accounting policies

Each segment receives context from prior segments, so a company's risk factors reference the specific business described in its overview, and the MD&A numbers align with the overview's financial indicators.


## Quality Tiers

Not all synthetic documents are "perfect." Real filings have flaws — empty sections, generic boilerplate, formatting issues. The factory generates documents at four quality levels:

| Tier | Error Rate | Description |
|------|-----------|-------------|
| **perfect** | 0% | Flawless documents for positive-example training |
| **near** | 3% | Subtle issues — slightly generic language, minor gaps |
| **moderate** | 12% | Noticeable problems — missing subsections, vague content |
| **severe** | 30% | Major issues — empty sections, garbled text, repetition |

### Single-Tier Generation

Generate a dataset where every document is the same quality:

```bash
# All perfect
python generate_edinet.py --skip-scrape --tiers perfect --records 100

# All severe (useful for flaw-detection model training)
python generate_edinet.py --skip-scrape --tiers severe --records 100
```

### Mixed-Tier Generation (Recommended)

Generate one dataset with a realistic distribution of quality levels:

```bash
# Default mix: 80% perfect, 10% near, 8% moderate, 2% severe
python generate_edinet.py --skip-scrape --mixed --records 500

# Custom distribution
python generate_edinet.py --skip-scrape --mixed \
  --mixed-dist "perfect:0.6,near:0.2,moderate:0.15,severe:0.05" \
  --records 500
```

Each document in a mixed dataset has a `quality_tier` field and an `error_rate` field, so buyers can filter or stratify the data however they need.


## Resumability

Generating 500 documents at ~5 minutes each takes 40+ hours. The pipeline saves progress after every document:

```bash
# Start a big run
python generate_edinet.py --skip-scrape --mixed --records 500

# ... power outage, Ctrl+C, system update, etc. ...

# Resume from where you left off
python generate_edinet.py --resume
```

Progress is stored in `output/{dataset}/.progress/`. On resume, completed documents are skipped.


## Validation

After generation, validate the output:

### Python Validation (built-in)

The pipeline runs document validators automatically:
- Language consistency (is it actually Japanese?)
- Structural completeness (all 8 segments present?)
- Segment length (within expected ranges?)
- Keyword presence (domain terms present?)
- Generation error detection (no `[GENERATION_FAILED]` sentinels?)

### R Validation (optional, recommended)

For deeper statistical analysis and marketplace-quality plots:

```bash
# Run the R validation script
Rscript R/validate_dataset.R \
  --input output/securities-report-jp/data/securities_reports.jsonl \
  --output output/securities-report-jp/quality-report/ \
  --taxonomy output/scraped/edinet/flaw_taxonomy.json
```

This produces:
- `validation_summary.json` — machine-readable quality metrics
- `plots/segment_lengths.png` — violin plots of segment character counts
- `plots/tier_distribution.png` — observed vs. expected tier breakdown
- `plots/flaw_taxonomy.png` — flaw type frequency chart


## Using edinetsynth (R Package)

If you or your customers use R for NLP research, the `edinetsynth` package provides tidy accessors:

```r
library(edinetsynth)

# Load a dataset
reports <- load_securities_report("securities_reports_mixed.jsonl")
nrow(reports)  # 500

# Segment-level statistics
segment_summary(reports)
#   segment           n mean_chars median_chars sd_chars pct_empty est_tokens
#   business_risks  500      2450         2380      620       0.4      1225
#   business_status 500      1680         1620      410       0.0       840
#   ...

# Extract just the risk sections
risks <- extract_segment(reports, "business_risks")
head(risks$seg_business_risks, 1)

# Compare quality tiers
compare_tiers(reports)
#   quality_tier   n   pct mean_error_rate expected_pct deviation
#   perfect      402  80.4           0.00         80.0       0.4
#   near          48   9.6           0.03         10.0      -0.4
#   ...

# Detect flaws programmatically
flaws <- detect_flaws(reports)
table(flaws$flaw_type)

# Generate marketplace-ready plots
plot_quality_report(reports, output_dir = "marketplace_plots/")
```


## Packaging for Sale

The packager creates a marketplace-ready ZIP:

```bash
# After generation and validation
ls output/securities-report-jp/package/
```

The package includes:
- `data/securities_reports.jsonl` — the dataset
- `schema/` — JSON Schema describing each field
- `datasheet.md` — auto-generated data card
- `quality-report/` — validation results and plots
- `LICENSE` — CC-BY-4.0
- `README.md` — buyer-facing documentation

Upload the ZIP to JDEX or Datarade. The bilingual documentation (`EDINET-DATASET-DOCUMENTATION.docx`) provides Japanese descriptions for JDEX buyers.


## Configuration Files

All generation parameters live in YAML configs under `configs/`:

| Config | Language | Description |
|--------|----------|-------------|
| `securities-report-jp.yaml` | Japanese | 500 synthetic 有価証券報告書 (the main product) |
| `housing-management-jp.yaml` | Japanese | Housing management forms |
| `compliance-report-de.yaml` | German | Compliance audit reports |
| `mittelstand-b2b.yaml` | German | B2B tabular data |
| `test-tiny.yaml` | — | 3-record smoke test |
| `dryrun-jp.yaml` | Japanese | Dry-run config for testing |

To create a new document type, copy an existing YAML and modify the segments. The factory's architecture means **adding a new product = writing a new config file, not new code**.


## Troubleshooting

**"Ollama not responding"**
```bash
systemctl status ollama
ollama list  # Verify model is downloaded
curl http://localhost:11434/api/tags  # Test API
```

**"Generation is slow"**
- The 70B model on CPU-only is ~5 min/segment. With GPU offloading, 1-2 min/segment.
- Use `--config configs/test-tiny.yaml` with a smaller model first.
- Consider running overnight with `--batch-size 50` for checkpointed batches.

**"R validation fails"**
```bash
# Check R packages
Rscript -e 'cat(requireNamespace("jsonlite", quietly=TRUE))'  # Should print TRUE
Rscript -e 'cat(requireNamespace("ggplot2", quietly=TRUE))'
```

**"Resume picks up wrong documents"**
- Delete the `.progress/` directory to start fresh
- Or specify `--records` to override the target count


## Architecture at a Glance

```
synth-factory/
├── generate_edinet.py      ← One-command pipeline entry point
├── run.py                  ← General-purpose pipeline runner
├── configs/                ← YAML configs (one per product)
│   └── securities-report-jp.yaml
├── generators/
│   ├── config_schema.py    ← Pydantic models for YAML validation
│   ├── document_generator.py ← Segment-by-segment LLM generation
│   └── ...
├── scrapers/
│   ├── edinet_scraper.py   ← EDINET API client
│   └── flaw_extractor.py   ← Builds flaw_taxonomy.json
├── validators/
│   ├── document_validator.py ← Python-side validation
│   └── r_validator.py      ← Python wrapper for R validation
├── packagers/
│   └── dataset_packager.py ← ZIP packaging for marketplace
├── R/
│   ├── validate_dataset.R  ← Statistical validation + plots
│   └── edinetsynth/        ← R package for data consumers
└── tests/                  ← pytest suite (65+ tests)
```

## What's Next?

Once you have a validated 500-document dataset:

1. **List on JDEX** — Use the bilingual documentation and quality plots
2. **List on Datarade** — English-focused listing with the data card
3. **Iterate** — Generate German compliance reports with the same factory
4. **Scale** — Add new document types by writing YAML configs
5. **Ecosystem** — Publish `edinetsynth` to CRAN to drive organic traffic to your datasets
