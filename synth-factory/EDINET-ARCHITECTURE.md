# EDINET Scraper Architecture — Design Decisions & Expansion Guide

## What Was Built

A test-driven, modular EDINET scraping and synthetic data generation system
that plugs directly into the existing synth-factory pipeline. The system
scrapes Japan's FSA disclosure database (EDINET), parses securities reports
into structured segments, extracts a flaw taxonomy from real filing patterns,
and generates synthetic documents with domain-authentic errors.

## Directory Structure

```
synth-factory/
├── scrapers/                          # NEW — modular data source scrapers
│   ├── base/
│   │   ├── __init__.py
│   │   └── base_scraper.py            # Abstract base: BaseScraper, DocumentRecord, HttpClient
│   ├── edinet/
│   │   ├── __init__.py
│   │   ├── edinet_client.py           # Low-level EDINET API v2 HTTP client
│   │   ├── edinet_scraper.py          # High-level orchestrator (BaseScraper impl)
│   │   ├── edinet_parser.py           # HTML/XBRL → structured text segments
│   │   └── flaw_extractor.py          # Pattern-based flaw taxonomy builder
│   └── parsers/
│       └── __init__.py                # Future: shared parsing utilities
├── configs/
│   └── securities-report-jp.yaml      # NEW — 8-segment securities report config
├── schemas/
│   ├── data_source_schema.yaml        # Reusable evaluation template
│   └── edinet-securities-jp.yaml      # NEW — filled-in evaluation for EDINET
├── tests/
│   └── scrapers/                      # NEW — 56 tests, all passing
│       ├── test_base_scraper.py       # 10 tests: data types, pipeline, checkpoints
│       ├── test_edinet_client.py      # 11 tests: API listing, download, error handling
│       ├── test_edinet_parser.py      # 11 tests: HTML/XBRL parsing, segments, edge cases
│       ├── test_edinet_scraper.py     # 6 tests: end-to-end pipeline
│       ├── test_flaw_extractor.py     # 11 tests: pattern detection, taxonomy building
│       └── test_config_integration.py # 7 tests: YAML config validation
└── [existing files unchanged]
```

## Architecture Decisions

### 1. Abstract Base Scraper

**Decision:** All scrapers implement `BaseScraper` with three abstract methods:
`list_documents()`, `download_document()`, `parse_document()`.

**Why:** Adding a new data source (J-PlatPat, UK tribunals, government procurement)
requires only implementing those three methods. The base class provides rate limiting,
checkpoint/resume, retry logic, and progress tracking for free.

**Expansion pattern:**
```python
from scrapers.base import BaseScraper, DocumentRecord

class JPatPatScraper(BaseScraper):
    def list_documents(self, **kwargs) -> list[DocumentRecord]: ...
    def download_document(self, record) -> DocumentRecord: ...
    def parse_document(self, record) -> DocumentRecord: ...
```

### 2. Injectable HTTP Client

**Decision:** All HTTP calls go through an `HttpClient` protocol. Tests inject
`MockHttpClient` instead of making real network calls.

**Why:** Tests run in <1 second with zero network dependency. The mock client
records all requests for assertion. Production uses `RealHttpClient` (httpx wrapper).

### 3. Universal DocumentRecord

**Decision:** Every scraper produces `DocumentRecord` objects regardless of source.

**Why:** The synth-factory pipeline, flaw extractor, and packager all consume
the same data type. Adding a new source doesn't require changing downstream code.

**Key fields:**
- `source_id` — unique within source (EDINET docID, J-PlatPat application number)
- `segments` — dict of {segment_name: text}, maps directly to synth-factory segments
- `metadata` — source-specific extra data (flexible dict)

### 4. Segment-Aligned Parsing

**Decision:** The parser extracts text into named segments that match the
synth-factory YAML config's segment definitions exactly.

**Why:** This creates a direct feedback loop:
1. Scrape real filing → parse into segments
2. Flaw extractor analyzes each segment for error patterns
3. Flaw taxonomy feeds into YAML config's error_injection rules
4. Synth-factory generates documents with segments matching real structure
5. Error injection applies the exact flaw types found in step 2

### 5. Self-Refining Flaw Taxonomy

**Decision:** The `FlawExtractor` accumulates flaw instances across documents
and builds a `FlawTaxonomy` with frequency data that gets saved as JSON.

**Why:** As more documents are scraped, the taxonomy grows more specific sub-types.
The YAML config's `error_injection_rate` combined with the taxonomy's frequency
data produces documents with statistically authentic error distributions.

**Current flaw categories:**
- STRUCTURAL (empty sections, missing sections, short content)
- NUMERICAL (duplicate figures, stale data)
- DISCLOSURE (generic language, boilerplate risks, negative assurance)
- FORMATTING (garbled symbols, control characters, mojibake)
- REGULATORY (missing sustainability/ESG disclosure, human capital)
- TEMPORAL (stale date references)

## How to Add a New Data Source

1. **Create scraper directory:** `scrapers/{source_name}/`
2. **Implement three methods** in a class extending `BaseScraper`
3. **Create YAML config** in `configs/{source}-{lang}.yaml` using the segment structure
4. **Fill in evaluation schema** by copying `schemas/data_source_schema.yaml`
5. **Write tests** in `tests/scrapers/test_{source_name}.py`
6. **Optionally add flaw extractor** for domain-specific error patterns

Time to add a new source: ~2-4 hours for a clean API, ~4-8 hours for scraping.

## Deployment Steps (Beelink)

1. Register for EDINET API key at https://disclosure.edinet-fsa.go.jp
2. Set environment variable: `export EDINET_API_KEY=your_key_here`
3. Install dependencies: `pip install -r requirements.txt`
4. Test connectivity:
   ```bash
   python -c "
   from scrapers.edinet import EdinetClient, EdinetConfig
   client = EdinetClient(EdinetConfig(api_key='YOUR_KEY'))
   docs = client.list_documents_by_date('2026-03-01')
   print(f'Found {len(docs)} annual reports')
   "
   ```
5. Run scraper for a month of filings:
   ```bash
   python -c "
   from scrapers.edinet import EdinetScraper, EdinetConfig
   scraper = EdinetScraper(EdinetConfig(api_key='YOUR_KEY'))
   result = scraper.scrape_date_range('2026-03-01', '2026-03-15')
   print(result.to_dict())
   "
   ```
6. Generate synthetic reports:
   ```bash
   python run.py configs/securities-report-jp.yaml
   ```

## Micro-SaaS Opportunity Note

The flaw taxonomy output (`flaw_taxonomy.json`) has standalone commercial value
beyond synthetic data generation. A queryable database of "what goes wrong with
Japanese financial filings, ranked by frequency, with real examples" serves:
- Compliance teams preparing filings
- Auditors checking filing quality
- RegTech products validating documents pre-submission
- Academic researchers studying disclosure quality

See `/dev/patterns/ideas/MICRO-SAAS-IDEAS.md` idea #20 for full evaluation.
