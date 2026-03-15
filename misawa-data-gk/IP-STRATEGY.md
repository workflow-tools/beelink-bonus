# Misawa Data GK — IP Strategy & Licensing Architecture

> **Date:** March 2026
> **Current IP holder:** ML Upskill Agents UG (Germany)
> **Future IP holder:** Misawa Data GK (Japan) — once formed and capitalized
> **Tax residency:** Germany (current)

---

## Current Structure

All intellectual property (code, datasets, flaw taxonomies, YAML configs, R packages)
is currently owned by **ML Upskill Agents UG**, the German UG. This includes:

- VilseckKI Synth-Factory pipeline code
- EDINET scraper and flaw taxonomy system
- Generated synthetic datasets
- `edinetsynth` R package (when released)
- All YAML configuration schemas
- Documentation and marketplace listings

## Future Licensing Architecture

Once Misawa Data GK is formed:

### Option A: License from UG to GK

ML Upskill Agents UG retains IP ownership and licenses the pipeline + codebase
to Misawa Data GK for a royalty (e.g., 10-15% of GK dataset revenue).

**Advantages:**
- IP stays in Germany (stronger enforcement jurisdiction)
- Royalty payments create verifiable cross-border revenue (useful for tax treaty)
- UG maintains control even if GK relationship changes
- Royalty expense reduces GK taxable income in Japan

**Risks:**
- Transfer pricing scrutiny from German or Japanese tax authorities
- Royalty must be arm's-length (document comparable license rates)
- Japan withholding tax on royalties: 0% under Germany-Japan tax treaty (Article 12)

### Option B: New Datasets Created by GK

Misawa Data GK generates NEW datasets on Japanese hardware, using Japanese data
sources (EDINET, J-PlatPat, etc.), with employees/contractors in Japan.

**Advantages:**
- IP clearly originates in Japan → GK owns it outright
- No cross-border licensing complexity for new datasets
- Strengthens "genuine business activity" argument for Business Manager visa
- Revenue from Japanese IP → builds toward ¥30M capital threshold

**Risks:**
- Need to clearly separate "new GK datasets" from "UG-licensed pipeline output"
- If GK uses UG-owned pipeline to generate, the pipeline is licensed but the DATA
  output belongs to GK (per license terms you define)

### Recommended: Hybrid (A + B)

1. UG licenses the Synth-Factory pipeline to GK (royalty-free initially, then 10%)
2. GK creates new datasets using the licensed pipeline → GK owns the data
3. GK lists on JDEX under its own name
4. `edinetsynth` R package released under MIT by UG (free, drives data sales)
5. Once GK reaches revenue milestones, UG can assign full IP to GK for tax efficiency

---

## IP Protection by Type

### Code (Pipeline, Scrapers, Validators)

- Protected under both German (UrhG §69a) and Japanese (Copyright Act §10(1)(ix)) law
  as computer programs
- No registration needed; copyright automatic upon creation
- License: proprietary (not open-sourced), except edinetsynth R package (MIT)

### Datasets (Generated JSONL)

- **Germany:** Protected as database works (UrhG §87a-e) — the "sweat of the brow"
  doctrine protects substantial investment in data collection/arrangement
- **Japan:** Protected as 編集著作物 (compiled works, Copyright Act §12) if creative
  selection or systematic construction is demonstrated
- Quality tiers, taxonomy-weighted flaw injection, and segment structure demonstrate
  the required creative/systematic construction
- **Critical:** Include metadata asserting IP ownership in every dataset package

### Flaw Taxonomy (flaw_taxonomy.json)

- Original analytical work derived from public data (EDINET filings)
- Protected as a database/compiled work in both jurisdictions
- The taxonomy itself is commercially valuable standalone (compliance tool input)

### R Package (edinetsynth)

- MIT licensed (intentionally open) — creates ecosystem lock-in
- The package drives paid data sales; open license maximizes adoption
- Package code copyright: ML Upskill Agents UG (or GK, when formed)

---

## Permanent Residency Implications

For the Business Manager visa and HSP points:

- GK must hold or license IP that generates Japanese revenue
- Licensing model (Option A) is sufficient — GK doesn't need to OWN all IP
- But Option B (new datasets created by GK) is stronger for demonstrating
  "genuine business activity in Japan"
- The hybrid approach maximizes both: UG pipeline license + GK-originated data

### Revenue Attribution for ¥30M Capital

- Dataset sales through JDEX under GK name → GK revenue
- Royalties paid to UG are a GK expense (reduce GK profit, increase UG profit)
- Keep royalty rate reasonable to leave enough profit in GK for capital accumulation
- Reinvest ALL GK profits (no distributions) until ¥30M threshold reached

---

## Germany-Japan Double Taxation Treaty (DTA)

| Income Type | Taxing Right | Treaty Article | Withholding |
|-------------|-------------|----------------|-------------|
| Royalties (software license) | Residence state only | Art. 12 | 0% |
| Business profits (GK → owner) | Source state (Japan) | Art. 7 | Per Japan tax law |
| Dividends/distributions | Both (with cap) | Art. 10 | 5-15% |

**Key insight:** Royalty payments from GK to UG are tax-free at source (0%
withholding under Art. 12). This makes the licensing model tax-efficient.

---

## Open Questions (Verify with Professionals)

1. Does the Germany-Japan DTA Article 12 cover software pipeline licenses specifically?
   → Confirm with Steuerberater
2. Can GK claim database right protection on datasets generated using UG-licensed code?
   → Confirm with Japanese IP attorney
3. What transfer pricing documentation is needed for UG→GK license?
   → Minimum: comparable license rate analysis, written agreement
4. Does JDEX require the listing entity to own the IP outright, or is licensing sufficient?
   → Check JDEX terms of service

---

*Cross-references:*
- `MISAWA-DATA-GK-FEASIBILITY.md` (business plan)
- `../synth-factory/EDINET-ARCHITECTURE.md` (technical architecture)
- `../synth-factory/R-INTEGRATION-NOTES.md` (R validation layer, edinetsynth)
