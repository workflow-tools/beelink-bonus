# Court Data Mining Strategy — Japan & Germany Real Estate

## The Insight

Court decisions in both Japan and Germany publicly document **exactly what goes wrong** with real estate contracts, housing forms, and financial statements. These decisions contain:

1. **Document type references** — which documents appear in disputes (Mietvertrag, 賃貸借契約書, Nebenkostenabrechnung, 敷金精算書)
2. **Flaw taxonomies** — what courts found wrong with those documents (missing signatures, calculation errors, formal defects, incomplete fields)
3. **Domain vocabulary** — the exact legal and administrative language used in real documents
4. **Error patterns** — recurring mistakes that real humans make when filling out or drafting these documents

This is not training data for the LLM itself (though it could be). This is **intelligence** for building better synthetic data — data that contains realistic, domain-authentic flaws that make it valuable for training document processing systems.

---

## Japan Strategy

### Data Sources

| Source | Access | Format | Best For |
|--------|--------|--------|----------|
| courts.go.jp 裁判例検索 | Free, public, GET scraping | HTML + PDF | Full decision text with document excerpts |
| 登記情報提供サービス | ¥332-370/lookup, API available | Structured data | Property registration patterns |
| TKC LEX/DB | Subscription | Structured | University library access |

### Site Architecture (confirmed 2026-03-13 via live exploration)

The courts.go.jp 裁判例検索 system uses **GET requests** (not POST) with query parameters.

**URL Patterns:**

| Page | URL Pattern | Notes |
|------|------------|-------|
| Unified search | `/hanrei/search1/index.html?query1=敷金返還&filter[...]` | Returns up to 2000+ results |
| Supreme Court | `/hanrei/search2/index.html?courtCaseType=1&query1=...` | Tab 2 adds courtCaseType param |
| Case detail | `/hanrei/{id}/detail2/index.html` | Uses DL/DT/DD HTML structure |
| Full text PDF | `/assets/hanrei/hanrei-pdf-{id}.pdf` | All full texts are PDFs, not HTML |

**Search Parameters:**
- `query1` — Main search keyword
- `query2` — Additional AND keyword
- `filter[judgeGengoFrom]` / `filter[judgeGengoTo]` — Japanese era (令和/平成/昭和)
- `filter[judgeYearFrom]` / `filter[judgeYearTo]` — Year within era
- `filter[judgeMonthFrom]` / `filter[judgeMonthTo]` — Month
- `filter[judgeDayFrom]` / `filter[judgeDayTo]` — Day
- `filter[courtType]` — Court type filter
- `filter[jikenGengo]`, `filter[jikenYear]`, `filter[jikenCode]`, `filter[jikenNumber]` — Case number parts
- `filter[courtSection]`, `filter[courtName]`, `filter[branchName]` — Court location

**Detail Page Structure (DL/DT/DD):**
```html
<dl>
  <dt>事件番号</dt><dd>令和5(オ)第1234号</dd>
  <dt>事件名</dt><dd>敷金返還等請求事件</dd>
  <dt>裁判年月日</dt><dd>令和6年3月15日</dd>
  <dt>法廷名</dt><dd>第二小法廷</dd>
  <dt>裁判種別</dt><dd>判決</dd>
  <dt>結果</dt><dd>破棄自判</dd>
  <dt>判例集等巻・号・頁</dt><dd>...</dd>
  <dt>原審裁判所名</dt><dd>...</dd>
  <dt>原審事件番号</dt><dd>...</dd>
  <dt>原審裁判年月日</dt><dd>...</dd>
  <dt>判示事項</dt><dd>...</dd>
  <dt>裁判要旨</dt><dd>(richest text source on detail page)</dd>
  <dt>参照法条</dt><dd>民法第622条の2...</dd>
  <dt>全文</dt><dd><a href="/assets/hanrei/hanrei-pdf-XXXX.pdf">全文</a></dd>
</dl>
```

**Key finding:** Full decision text is in PDFs only. The detail page itself contains metadata and the 裁判要旨 (judicial summary), which is still rich in document references and flaw patterns. Phase 2 will add PDF download and text extraction (pdfminer/pymupdf).

### Target Queries (20 predefined)

The scraper covers housing management (住宅管理, 管理組合, 公営住宅), lease disputes (賃貸借契約, 建物賃貸借), security deposits (敷金返還), evictions (建物明渡), rent adjustments (賃料増減額), real estate transactions (不動産売買, 重要事項説明), defect warranties (瑕疵担保), guarantor contracts (連帯保証), insurance (火災保険), and construction contracts (建築請負契約).

### Expected Yield

Japan's court database has decisions dating back to 1947. A single query like "敷金返還 賃貸借" returned 2,000+ results in live testing. Real estate disputes are one of the most common civil case categories. Conservative estimate: 500-2,000 relevant decisions accessible via the free public database, each containing references to specific document types and identified flaws.

### Key Document Types to Extract

From court decisions, we expect to find references to: 賃貸借契約書, 重要事項説明書, 管理規約, 敷金精算書, 入居申込書, 建物検査報告書, 登記事項証明書, 原状回復費用明細, 連帯保証契約書, 建築請負契約書, 火災保険証書.

### Flaw Pattern Categories

The scraper extracts 18 flaw pattern types: incomplete entries (記載不十分), missing entries (記載漏れ), unfilled fields (記入不備), missing signatures (署名不備), missing seals (押印不備), incorrect entries (記載誤り), calculation errors (計算誤り), date errors (日付誤り), amount errors (金額相違), contradictions (矛盾), inconsistencies (整合性欠如), legal defects (法的瑕疵), missing requirements (要件不充足), formal defects (形式不備), illegibility (判読困難), unclear images (不鮮明), falsification (改ざん), and forgery (偽造).

---

## Germany Strategy

### Data Sources

| Source | Access | Format | Best For |
|--------|--------|--------|----------|
| Open Legal Data API | Free, REST API, 251k+ decisions | JSON | Programmatic bulk access |
| dejure.org | Free, HTML | HTML | BGB section cross-references (richest index) |
| OpenJur.de | Free, HTML | HTML | Broad keyword search + full text |
| BGH (juris.bundesgerichtshof.de) | Free, HTML + PDF | PDF | Federal-level precedents |
| Berlin Rechtsprechungsdatenbank | Free, from 2021 | HTML | Berlin Mietrecht (highest volume) |
| NRWE.de | Free, daily updates | HTML | NRW court decisions |
| IMR-Online | Partial free | HTML | Specialized Mietrecht/Immobilienrecht |

### dejure.org Architecture (confirmed 2026-03-13 via live exploration)

dejure.org is the **single richest index** for German court decisions. It doesn't host full text itself but aggregates links to all full-text sources.

**URL Patterns:**

| Page | URL Pattern | Notes |
|------|------------|-------|
| BGB section | `/gesetze/BGB/{section}.html` | Statute text + embedded case list |
| Case list (paginated) | `/dienste/lex/BGB/{section}/{page}.html` | 50 cases/page, sorted by date |
| Case redirect | `/dienste/vernetzung/rechtsprechung?Gericht=...&Datum=...&Aktenzeichen=...` | Redirects to full-text source |

**Scale confirmed:** BGB §535 alone has **7,045 decisions across 141 pages**.

**Case list HTML structure:**
```html
<ul>
  <li>
    <a href="/dienste/vernetzung/rechtsprechung?Gericht=OLG+München&Datum=12.02.2026&Aktenzeichen=14+U+1880/25">
      OLG München, 12.02.2026 - 14 U 1880/25
    </a>
    <p class="kursiv">Nebenkostenabrechnung, Gewerberaummietvertrag, Wartungskosten, ...</p>
  </li>
</ul>
```

**Case detail page sections:**
1. **Volltextveröffentlichungen** — Links to full-text on openjur.de, bundesgerichtshof.de, rechtsinformationen.bund.de, rechtsprechung-im-internet.de
2. **Kurzfassungen/Presse** — Summaries and press coverage
3. **Besprechungen u.ä.** — Legal commentary/analysis
4. **Verfahrensgang** — Procedural history (links to lower court decisions)
5. **Papierfundstellen** — Print publication references
6. **Wird zitiert von / Zitiert selbst** — Citation network (traversable for graph building)

**Key finding:** dejure.org is an aggregator/index, not a full-text host. The scraper follows full-text links to openjur.de, bundesgerichtshof.de, etc. to get the actual decision text. The case detail page's "Zitiert selbst" section enables citation graph traversal.

**Cookie consent note:** The site uses a consent dialog that locks the page body with `position: fixed; overflow: hidden`. Scraper must handle this via appropriate headers or cookie acceptance.

### Target Queries (25 predefined)

Covers lease defects (Mietvertrag Mangel), invalid leases, invalid terminations, utility bill errors (Nebenkostenabrechnung fehlerhaft), operating cost allocation, security deposit disputes, rent reduction for mold and defects, cosmetic repairs (Schönheitsreparaturen), handover protocol disputes, rent increases, real estate purchase defects, construction contract disputes, WEG resolutions, and maintenance fee statements.

### BGB Section Traversal

The dejure.org scraper systematically visits every Mietrecht BGB section (§535-580a) via the paginated case list pages. For each section, it collects case metadata (court, date, Aktenzeichen, topic keywords) then follows full-text links. This captures the full breadth of tenancy law disputes, not just keyword matches.

**Estimated total for Mietrecht BGB sections:** Based on §535 having 7,045 decisions, and assuming decreasing density for more specific sections, the total across §535-580a is likely 30,000-50,000 decisions indexed on dejure.org.

### Expected Yield

Open Legal Data alone has 251,000+ decisions. Mietrecht is one of Germany's highest-volume civil law areas. Conservative estimate: 5,000-15,000 relevant decisions across all sources, with Berlin and NRW being the richest due to high rental density.

### Key Document Types to Extract

Mietvertrag (and variants: Staffelmietvertrag, Indexmietvertrag, Gewerbemietvertrag), Nebenkostenabrechnung, Betriebskostenabrechnung, Heizkostenabrechnung, Kündigungsschreiben, Mieterhöhungsverlangen, Mängelanzeige, Übergabeprotokoll, Kaufvertrag, Grundbuchauszug, Teilungserklärung, Bauvertrag, Sachverständigengutachten, Bürgschaftserklärung, Schufa-Auskunft, Mietschuldenfreiheitsbescheinigung.

### Flaw Pattern Categories

The scraper extracts 24 flaw pattern types: formal validity issues, form errors, written form violations, calculation errors, arithmetic mistakes, missing information, incomplete entries, gaps, unstated items, incorrect information, erroneous entries, deadline violations, late submissions, missing signatures, contradictions, unclear terms, ambiguity, non-transparency, surprising clauses, unfair disadvantage, AGB control violations, and void clauses.

---

## The Pipeline: From Court Data to Better Synthetic Data

```
Court Decisions (public records)
        │
        ▼
  Scraper extracts:
  ├── Document types referenced
  ├── Flaw patterns with context
  └── Domain vocabulary
        │
        ▼
  Flaw Taxonomy (flaw_taxonomy.json)
  ├── Ranked by frequency
  ├── With real-world examples
  └── Per document type
        │
        ▼
  Enhanced YAML Configs
  ├── Domain-aware error injection
  ├── Realistic flaw distributions
  └── Authentic vocabulary in prompts
        │
        ▼
  Synth-Factory generates documents
  with REAL error patterns at REAL frequencies
        │
        ▼
  Premium synthetic datasets
  that no generic data generator can match
```

---

## Phased Execution Plan

### Phase 1: Metadata & Summary Extraction (now)
- Japan: Scrape detail pages, extract DL/DT/DD metadata + 裁判要旨
- Germany (dejure): Traverse BGB §535-580a, collect case metadata + topic keywords, follow full-text links
- Germany (OLDP): Bulk API queries for Mietrecht keywords
- Output: flaw_taxonomy.json for both countries

### Phase 2: Full Text Extraction (Beelink deployment)
- Japan: Download PDFs from `/assets/hanrei/hanrei-pdf-{id}.pdf`, extract text via pymupdf
- Germany: Parse full text from openjur.de and bundesgerichtshof.de via the dejure redirect links
- Output: enriched flaw_taxonomy.json with full-text context, deeper document reference analysis

### Phase 3: Domain Fine-Tuning Integration
- Feed flaw taxonomies into synth-factory error injection system
- Replace "dumb noise" error injection with domain-authentic error patterns
- Generate fine-tuning datasets using the court-derived flaw distributions
- Train LoRA adapters on the 70B model using best synthetic outputs

---

## Legal Compliance

### Japan
- Court decisions are public records
- courts.go.jp allows non-commercial research access
- We respect rate limiting (4-second delays)
- 登記情報提供サービス requires API agreement for automated access (NOT scraped)

### Germany
- Court decisions are public records, published anonymized
- §60d UrhG permits text/data mining for non-commercial research
- BGH has ruled web scraping legal when robots.txt is respected
- We respect rate limiting and identify our bot via User-Agent

### What We Extract
- We extract **patterns and categories**, not reproduce copyrighted text
- Flaw taxonomy = aggregated statistical data about error types
- Document references = list of document type names (not document content)
- No PII involved (court decisions are already anonymized)

---

## How to Run

```bash
# Install dependencies
pip install httpx beautifulsoup4 lxml

# Japan: scrape all real estate queries
./scrape.sh japan --bulk --max 30

# Germany: scrape all Mietrecht queries
./scrape.sh germany --bulk --max 30

# Generate flaw taxonomies from scraped data
./scrape.sh taxonomy

# Output:
#   output/japan/flaw_taxonomy.json
#   output/germany/flaw_taxonomy.json
#   output/japan/cases_*.jsonl
#   output/germany/*.jsonl
```

---

## What This Enables

Once the flaw taxonomies are generated, the next step is to integrate them into the synth-factory error injection system. Instead of the current "dumb noise" error injection (random truncation, encoding artifacts), the document generator will inject **domain-authentic errors at realistic frequencies** — the exact patterns that courts have identified in real documents.

This makes the synthetic data uniquely valuable: it contains the specific edge cases that document processing companies need in their training data, because those are the exact errors their systems encounter in production.
