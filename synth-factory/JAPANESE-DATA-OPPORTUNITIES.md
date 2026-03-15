# Japanese Long-Text Data Opportunities — Research & Schema

## Market Context

Japan's AI training dataset market is projected to grow from USD 132M (2023) to over USD 1B by 2032 (25.5% CAGR). Major buyers include Rakuten, Preferred Networks, Fujitsu, CyberAgent, and Cinnamon AI. The EU AI Act (effective 2026) creates mandatory training data documentation requirements, and Japan's own AI Promotion Act (effective June 2025) signals regulatory alignment. There is no dominant player in Japanese synthetic data — the market is sold through data service bundles, not standalone products. That's the opening.

Documented data scarcity exists in legal, financial, and real estate domains specifically. EDINET-Bench (2025) was created specifically because Japanese financial benchmarks were "underserved and underrepresented." Only ~1% of Japan's 200,000 annual civil case documents are released digitally. The real estate sector just saw MLIT open historical transaction data for the first time, explicitly to enable AI training.

---

## Opportunity Matrix

### Tier 1: Highest Value (free access, long text, proven demand)

| Domain | Source | Access | Format | Doc Length | API | Demand Signal |
|--------|--------|--------|--------|------------|-----|---------------|
| **Financial reports** | EDINET (金融庁) | Free + registration | XBRL, PDF, CSV | 50-100+ pages | Yes (v2, Jan 2026) | EDINET-Bench gap paper; Rakuten, Fugaku training efforts |
| **Patent filings** | J-PlatPat (INPIT) | Free | HTML | 10-50+ pages | Partial | ML patent classification research; WIPO demand |
| **Court decisions** | courts.go.jp | Free | HTML + PDF | 5-50+ pages | No | COLIEE legal AI competition (since 2014); 1% digital release rate |
| **Gov procurement** | JETRO procurement DB | Free | HTML | 5-30 pages | Partial | AI bid analysis emerging; underexploited source |

### Tier 2: High Value (free, specialized)

| Domain | Source | Access | Format | Doc Length | API | Demand Signal |
|--------|--------|--------|--------|------------|-----|---------------|
| **Doctoral dissertations** | National Diet Library | Free | PDF | 100-300 pages | NDL search | Academic Japanese prose; 2013+ all online |
| **Construction accidents** | MLIT safety DB | Free CSV | CSV + narrative | Variable | Yes (CSV) | Safety compliance AI; 1,600+ reports |
| **Environmental assessments** | EADAS (環境省) | Free | HTML + PDF | 20-100+ pages | Partial | ESG compliance; sustainability reporting AI |
| **PMDA drug approvals** | PMDA search | Free | PDF | 10-50 pages | Partial | Pharma AI; clinical NLP in Japanese |
| **Labor dispute cases** | Central Labor Commission | Free | HTML | 5-30 pages | No | Employment law AI; cases from 1959+ |

### Tier 3: Moderate Value (useful but constrained)

| Domain | Source | Access | Format | Doc Length | API | Demand Signal |
|--------|--------|--------|--------|------------|-----|---------------|
| **University self-eval** | Individual university sites | Free | PDF | 50-150 pages | No | Accreditation AI; scattered across sites |
| **Property registration** | touki.or.jp | ¥480-600/doc | Structured text | 2-10 pages | Limited | PropTech valuation; fee barrier to bulk |
| **Standard contracts** | NEDO, construction committees | Free templates | Word/PDF | 5-30 pages | No | Contract analysis; templates only (limited variation) |
| **Insurance policies** | Insurer websites | Free templates | PDF | 10-30 pages | No | InsurTech; standardized but domain-rich |

---

## Deep Dives on Top 3 Opportunities

### 1. EDINET Financial Reports (有価証券報告書)

**Why this is the #1 expansion target:**
- Free API access (v2 launched January 2026) — no scraping needed
- Thousands of companies filing annually, each report 50-100+ pages
- Mix of regulated language (financial statements, risk disclosures) with business narrative (strategy, governance)
- SakanaAI created EDINET-Bench specifically because this data gap was blocking research
- Directly feeds AI for: fraud detection, earnings forecasting, industry classification, ESG analysis

**Document structure:** Business description, corporate governance, financial condition analysis, consolidated financial statements, audit reports, risk factors, officer compensation, stock information.

**Synthetic data angle:** Generate realistic-but-fictional 有価証券報告書 with domain-authentic flaws (mismatched figures between narrative and tables, incomplete risk disclosures, governance gaps). Buyers: fintech compliance companies, audit automation tools, financial NLP researchers.

**Flaw intelligence source:** Financial Services Agency (FSA) enforcement actions (処分事例) document exactly what goes wrong in real filings — the same court-scraping pattern applied to financial regulators.

### 2. J-PlatPat Patent Filings (特許公報)

**Why this is the #2 expansion target:**
- Completely free, full-text searchable, patents from 1871 onwards
- Highly structured: claims, descriptions, drawings, prior art — standard format but rich technical language
- Prior art citation network enables the same graph-traversal strategy as dejure.org citations
- International demand: WIPO, EPO, and USPTO all need Japanese patent NLP for cross-border search

**Document structure:** Title, abstract, claims (請求の範囲), detailed description (発明の詳細な説明), drawings, prior art references, applicant/inventor information.

**Synthetic data angle:** Generate realistic patent applications in specific technology domains (construction materials, real estate IoT, building automation) with authentic flaw patterns (overly broad claims, insufficient prior art disclosure, unclear claim boundaries). Buyers: patent search companies, IP law firms, patent examination AI.

**Flaw intelligence source:** Patent examination guidelines from JPO + rejection decisions (拒絶理由通知) document exactly what examiners find wrong with applications.

### 3. Government Procurement (政府公共調達)

**Why this is the #3 expansion target:**
- Free, published same-day, combines legal language with technical specifications
- WTO Government Procurement Agreement compliance means structured format
- Underexploited: no one is systematically mining this for AI training data
- Cross-domain: procurement docs span IT, construction, consulting, equipment — one source, many verticals

**Document structure:** Procurement notice, technical specifications, qualification requirements, evaluation criteria, contract terms, bid submission instructions.

**Synthetic data angle:** Generate realistic procurement documents for specific sectors with domain-authentic issues (ambiguous specifications, contradictory requirements, missing evaluation criteria). Buyers: GovTech companies, bid automation tools, compliance checkers.

---

## Market Demand Validation Questions

For each promising domain, answer these to validate before investing scraping effort:

### The Suite of 12 Questions

1. **Who is buying this type of data today?** (Named companies, not categories)
2. **What are they paying?** (Per-document, per-dataset, subscription — with actual numbers)
3. **What format do they need it in?** (Raw text, annotated, JSONL, XBRL, structured pairs)
4. **What quality threshold matters?** (Domain accuracy, format compliance, flaw realism)
5. **How much data do they need?** (100 docs? 10,000? 1M tokens?)
6. **Is there an existing benchmark that measures quality in this domain?** (If yes, we can target benchmark performance)
7. **What's the current best alternative?** (Manual creation, crowd annotation, existing datasets)
8. **What does the current alternative cost per unit?** (This sets our price ceiling)
9. **Is there a regulatory driver creating urgency?** (EU AI Act, Japan AI Promotion Act, sector-specific rules)
10. **Can we access the intelligence source** (courts, regulators, standards bodies) **to build flaw taxonomies?**
11. **Does the domain have enough structural variation** to make synthetic data non-trivial? (If every document looks the same, buyers can template it themselves)
12. **Can this be produced on a Beelink with a 70B model?** (Token length, complexity, domain knowledge requirements)

### Applying the Questions to Our Top 3

**EDINET Financial Reports:**
1. Rakuten, SakanaAI, Cinnamon AI, fintech compliance vendors
2. Annotation services: $40-100/hr for financial domain experts; bulk datasets: likely ¥500K-5M per curated set
3. XBRL + narrative text pairs; JSONL for NLP training
4. High — numerical consistency between narrative and tables is critical
5. Hundreds to thousands of realistic filings per sector
6. Yes — EDINET-Bench (SakanaAI, 2025) with 4 tasks
7. Real EDINET data (free but requires cleaning) + manual annotation
8. Manual annotation: $40-100/hr × 4-8 hrs per report = $160-800 per annotated document
9. Yes — EU AI Act documentation + Japan FSA enforcement
10. Yes — FSA enforcement actions are published
11. Yes — huge variation across industries, company sizes, reporting periods
12. Yes — segment-based generation handles 50+ page documents

**J-PlatPat Patents:**
1. Patent search companies (Clarivate, PatSnap), IP law firms, JPO itself
2. Patent annotation: $50-150/hr for patent attorneys; curated training sets: $5K-50K
3. Structured claims + description pairs; classification labels
4. High — claim structure must follow patent drafting conventions exactly
5. Thousands per technology class for meaningful training
6. NTCIR Patent Retrieval tasks; COLIEE-like competitions
7. Real patents (free but massive volume, need filtering) + manual review
8. Manual patent drafting: $5,000-15,000 per patent from a professional
9. Moderate — AI patent examination tools being developed by JPO
10. Yes — rejection decisions (拒絶理由通知) are published
11. Yes — enormous variation across technology domains
12. Stretch — patent language is extremely precise; may need fine-tuning first

**Government Procurement:**
1. GovTech startups, bid management platforms, public sector consultants
2. Unknown — market is nascent; likely ¥100K-1M per curated domain set
3. Structured notices + specifications; evaluation criteria tables
4. Medium — format compliance matters more than content depth
5. Hundreds per procurement category
6. No established benchmark — opportunity to create one
7. Manual procurement document preparation (expensive, slow)
8. Procurement consulting: ¥50,000-200,000 per bid document set
9. Yes — digital government push; e-procurement mandates
10. Yes — all procurement is public record
11. Moderate — more standardized than financial reports but cross-domain variation helps
12. Yes — fits well within current architecture

---

## Discovery Schema for Data Factory Integration

This schema lets us systematically evaluate new data sources and plug them into the existing synth-factory architecture. Every new opportunity gets scored against the same criteria, and the schema itself can be stored as YAML to drive automated discovery.

### `data_source_schema.yaml`

```yaml
# Schema for evaluating and integrating new data sources
# into the VilseckKI Synthetic Data Factory
#
# Usage: Create one file per data source domain.
# The synth-factory reads this to configure new document types.

source_metadata:
  domain: "financial_reporting"           # Machine-readable domain tag
  domain_display: "有価証券報告書"         # Human-readable (Japanese)
  domain_en: "Securities Reports"          # Human-readable (English)
  country: "JP"
  language: "ja"

  # Where the real data lives
  primary_source:
    name: "EDINET"
    url: "https://www.edinet-fsa.go.jp/"
    access_type: "api"                    # api | scrape | download | fee_per_doc
    api_endpoint: "https://api.edinet-fsa.go.jp/api/v2/documents/"
    authentication: "api_key"             # none | api_key | oauth | registration
    rate_limit: "10/minute"
    cost_per_unit: 0                      # JPY per document (0 = free)

  # Where flaw intelligence comes from
  flaw_intelligence_source:
    name: "FSA Enforcement Actions"
    url: "https://www.fsa.go.jp/sesc/actions/"
    access_type: "scrape"
    scraper_exists: false                 # true if we've built a scraper for this
    estimated_flaw_types: 15              # How many distinct flaw categories we expect

market_validation:
  # Answers to the 12 questions
  known_buyers:
    - "Rakuten (LLM training)"
    - "SakanaAI (EDINET-Bench)"
    - "Cinnamon AI (document automation)"
  estimated_price_per_unit: "¥500-5000"   # Per synthetic document
  required_format: "jsonl"                # jsonl | xbrl | pdf | pairs
  quality_threshold: "numerical_consistency + regulatory_compliance"
  volume_needed: "500-5000"               # Documents per dataset release
  existing_benchmark: "EDINET-Bench (SakanaAI 2025)"
  current_alternative: "Real EDINET data + manual annotation"
  alternative_cost_per_unit: "¥20000-100000"  # Manual annotation cost
  regulatory_driver: "EU AI Act 2026 + Japan AI Promotion Act"
  structural_variation: "high"            # low | medium | high
  beelink_feasible: true

  # Market maturity assessment
  demand_confidence: 0.85                 # 0-1 scale
  competition_level: "low"               # none | low | medium | high
  time_to_first_sale: "2-4 months"

document_architecture:
  # Maps to synth-factory config schema
  typical_length_pages: 75
  typical_token_count: 50000

  # Segment definitions (maps to synth-factory segments)
  segments:
    - name: "company_overview"
      description: "企業の概況 — Business description and history"
      typical_length: 3000
      required_fields:
        - "company_name"
        - "establishment_date"
        - "business_description"
        - "employee_count"
      flaw_prone_fields:
        - field: "employee_count"
          common_flaw: "inconsistent_with_consolidated_figures"

    - name: "business_risks"
      description: "事業等のリスク — Risk factors disclosure"
      typical_length: 5000
      required_fields:
        - "risk_category"
        - "risk_description"
        - "mitigation_measures"
      flaw_prone_fields:
        - field: "risk_description"
          common_flaw: "vague_or_boilerplate"
        - field: "mitigation_measures"
          common_flaw: "missing_or_generic"

    - name: "financial_condition"
      description: "経理の状況 — Financial statements and analysis"
      typical_length: 15000
      required_fields:
        - "revenue"
        - "operating_profit"
        - "net_income"
        - "total_assets"
        - "narrative_analysis"
      flaw_prone_fields:
        - field: "narrative_analysis"
          common_flaw: "figures_mismatch_tables"
        - field: "revenue"
          common_flaw: "segment_totals_dont_sum"

    - name: "governance"
      description: "コーポレートガバナンスの状況 — Corporate governance"
      typical_length: 4000
      required_fields:
        - "board_composition"
        - "audit_committee"
        - "compensation_policy"
      flaw_prone_fields:
        - field: "board_composition"
          common_flaw: "missing_independence_disclosure"

    - name: "audit_report"
      description: "監査報告書 — External auditor's report"
      typical_length: 2000
      required_fields:
        - "auditor_name"
        - "opinion_type"
        - "key_audit_matters"
      flaw_prone_fields:
        - field: "key_audit_matters"
          common_flaw: "insufficient_detail"

flaw_taxonomy:
  # Populated from intelligence source scraping
  # Maps to synth-factory error injection system
  source: "fsa_enforcement_actions"
  taxonomy_file: "output/japan_financial/flaw_taxonomy.json"
  last_updated: null                      # Set when taxonomy is generated

  # Known flaw categories (pre-populated from research)
  known_categories:
    - type: "figures_mismatch"
      description: "Numbers in narrative text don't match financial tables"
      estimated_frequency: 0.25
      severity: "high"

    - type: "segment_arithmetic_error"
      description: "Business segment figures don't sum to consolidated total"
      estimated_frequency: 0.15
      severity: "high"

    - type: "risk_disclosure_boilerplate"
      description: "Risk factors copied from previous year without updates"
      estimated_frequency: 0.30
      severity: "medium"

    - type: "governance_gap"
      description: "Missing required governance disclosures"
      estimated_frequency: 0.10
      severity: "high"

    - type: "date_inconsistency"
      description: "Reporting period dates inconsistent across sections"
      estimated_frequency: 0.08
      severity: "medium"

    - type: "incomplete_related_party"
      description: "Related party transactions missing or inadequately described"
      estimated_frequency: 0.12
      severity: "high"

integration:
  # How this plugs into the existing synth-factory
  config_template: "configs/securities-report-jp.yaml"
  generator_compatible: true              # Uses existing document_generator.py
  validator_compatible: true              # Uses existing document_validator.py
  packager_format: "jsonl_zip"

  # What needs to be built
  new_components_needed:
    - "configs/securities-report-jp.yaml"
    - "scrapers/edinet_scraper.py"        # Flaw taxonomy from FSA enforcement
    - "scrapers/fsa_enforcement.py"       # Enforcement action scraper

  # Reuses from existing architecture
  reused_components:
    - "generators/document_generator.py"  # Segment-based generation
    - "validators/document_validator.py"  # Quality validation
    - "packagers/dataset_packager.py"     # JSONL + metadata packaging
    - "run.py"                            # CLI runner
    - "run.sh"                            # Beelink deployment
```

### How the Schema Drives Automation

The schema serves two purposes:

**1. Systematic evaluation:** When you discover a new potential data source, fill in one of these YAML files. If `demand_confidence > 0.7`, `beelink_feasible: true`, and `flaw_intelligence_source.access_type` is not "fee_per_doc", it's worth building.

**2. Factory integration:** The `document_architecture.segments` section maps directly to the existing synth-factory's segment-based generation config. A script can read this schema and auto-generate a starter `configs/{domain}.yaml` file, pre-populated with segment definitions, required fields, and flaw-prone fields. The flaw taxonomy section connects the scraper output to the error injection system.

**3. Discovery automation:** A crawler script can scan known databases (EDINET API, JETRO, PMDA, courts.go.jp) for new document types or high-volume categories, score them against the market validation criteria, and flag opportunities that meet the threshold. This is the "pipeline from domain intelligence extraction to synthetic data generation" that aligns with your dissertation.

---

## Recommended Build Sequence

### Phase 1: EDINET Financial Reports (weeks 1-3)
1. Register for EDINET API access
2. Build `edinet_scraper.py` to download real securities reports (for structure learning, not redistribution)
3. Build `fsa_enforcement.py` to scrape FSA enforcement actions (flaw intelligence)
4. Create `configs/securities-report-jp.yaml` using the schema above
5. Generate first batch of synthetic 有価証券報告書
6. List on Hugging Face with EDINET-Bench compatibility framing

### Phase 2: Patent Filings (weeks 3-5)
1. Build J-PlatPat scraper for construction/real estate technology patents
2. Build JPO rejection scraper for flaw intelligence
3. Create `configs/patent-application-jp.yaml`
4. Generate first batch of synthetic patent applications
5. Cross-reference with real estate domain for IP-adjacent datasets

### Phase 3: Government Procurement (weeks 5-7)
1. Build JETRO procurement scraper
2. Create `configs/procurement-notice-jp.yaml`
3. Generate synthetic procurement docs spanning IT, construction, consulting
4. Package as cross-domain training sets

### Running in parallel: Court scraping improvements
- Japan court PDF extraction (Phase 2 of existing scraper)
- Germany dejure.org bulk traversal on Beelink
- UK EHCP tribunal scraper build

---

## Connection to Existing Architecture

Everything above plugs into what's already built:

```
data_source_schema.yaml     ← NEW: Evaluates opportunities
        │
        ▼
court-scraper/              ← EXISTS: Extracts flaw intelligence
  ├── japan_courts.py       ← EXISTS: Real estate disputes
  ├── germany_courts.py     ← EXISTS: Mietrecht disputes
  ├── edinet_scraper.py     ← NEW: Financial report structure
  └── fsa_enforcement.py    ← NEW: Financial flaw intelligence
        │
        ▼
output/flaw_taxonomy.json   ← EXISTS: Aggregated flaw data
        │
        ▼
synth-factory/              ← EXISTS: Generates documents
  ├── configs/
  │   ├── housing-management-jp.yaml    ← EXISTS
  │   ├── compliance-report-de.yaml     ← EXISTS
  │   ├── securities-report-jp.yaml     ← NEW
  │   └── patent-application-jp.yaml    ← NEW
  ├── generators/
  │   └── document_generator.py         ← EXISTS (error injection upgrade pending)
  └── run.sh                            ← EXISTS (Beelink deployment)
```

The data source schema is the missing piece that turns this from "I built some scrapers" into "I have a systematic pipeline for discovering and exploiting data generation opportunities." That's the dissertation contribution.
