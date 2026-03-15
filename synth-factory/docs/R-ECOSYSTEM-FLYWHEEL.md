# R Ecosystem Flywheel Strategy

> How free R packages drive paid dataset sales on JDEX and Datarade.

*IP: ML Upskill Agents UG (Germany). Future datasets: Misawa Data GK (Japan) once formed.*

---

## The Core Idea

Give away the analysis tool. Sell the data it consumes.

This is the same model as Databricks (free Spark → paid platform), Elastic (free Elasticsearch → paid cloud), or Hugging Face (free transformers library → paid Inference API). The difference is that our "free tool" is an R package and our "paid platform" is structured synthetic data sold on marketplaces.

## Why R (and Not Just Python)

R is back in the TIOBE top 10 (rank 10, December 2025) after years outside it. More importantly for us, R's resurgence is concentrated in exactly our customer segments: academic researchers, government statisticians, and domain-specialist data scientists — people who analyze data but don't build production ML pipelines.

These are the people who buy datasets on marketplaces. They're not training foundation models (that's Big Tech with Python/PyTorch). They're running statistical analyses, building domain-specific classifiers, and validating compliance systems. R is their daily driver.

### Japan Market (edinetsynth)

R has a meaningful presence in Japanese academic NLP research. Japanese universities use R for computational linguistics (quanteda + RMeCab is a common stack). Financial researchers at institutions like the Bank of Japan, RIETI, and university finance departments use R for econometric analysis. These researchers are the natural buyers of synthetic EDINET data — they need realistic Japanese financial text for training document understanding models, and they already work in R.

The edinetsynth package meets them where they are. Instead of asking a researcher to write custom JSONL parsing code, they `install.packages("edinetsynth")` and get:
- `load_securities_report()` → instant tibble
- `segment_summary()` → publication-ready statistics
- `plot_quality_report()` → figures they can paste into papers

The package README links to JDEX where they buy the actual data.

### Germany Market (decompliancesynth — future)

The German picture is different but equally promising. R has strong institutional adoption in two relevant sectors:

**Government and official statistics.** Eurostat (the EU statistical office) has an official R package (`eurostat` on CRAN) and actively promotes R for working with European statistical data. Germany's Destatis (Statistisches Bundesamt / 統計連邦庁 — Federal Statistical Office) and BaFin (Bundesanstalt für Finanzdienstleistungsaufsicht / 連邦金融監督庁 — Federal Financial Supervisory Authority) employ data analysts who use R. The `eurostat` R package is a direct precedent for our approach.

**Auditing and Wirtschaftsprüfung (監査 / かんさ).** Germany's Big Four offices and the Wirtschaftsprüfer (公認会計士 / こうにんかいけいし — certified auditors) at mid-size firms increasingly use R for audit analytics. The IDW (Institut der Wirtschaftsprüfer / ドイツ監査人協会) has published guidance on data analytics in auditing. R's `benford.analysis` package is already used for fraud detection in German audit contexts.

**But here's the honest nuance:** Python is dominant for production RegTech systems in Germany. Companies building BaFin compliance platforms (FinregE, Regnology, etc.) use Python, not R. The R opportunity is in the *analysis and validation* layer — the people who evaluate whether compliance systems work correctly, not the people who build them. This is actually a better customer profile for us because evaluators need test data (our product) while builders need code.

A future `decompliancesynth` package would target:
- Audit analytics teams at WP-Gesellschaften (accounting firms)
- BaFin's own internal data analysis teams
- University researchers studying German regulatory compliance
- RegTech startups who need test data for their BaFin compliance tools

### R's Structural Advantage Over Python for This Strategy

Python users tend to write their own data loaders. R users expect packages. This cultural difference means an R package creates stickier adoption — once a researcher's workflow depends on `edinetsynth::load_securities_report()`, switching to a competitor's data format means rewriting their analysis scripts. The package IS the lock-in.

## The Flywheel Mechanics

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   1. Publish free R package to CRAN                  │
│      ↓                                               │
│   2. Researchers discover via CRAN search,           │
│      academic citations, R-bloggers                  │
│      ↓                                               │
│   3. Package README + vignettes show what's          │
│      possible with the data                          │
│      ↓                                               │
│   4. Researcher needs actual data →                  │
│      links to JDEX / Datarade listing                │
│      ↓                                               │
│   5. Purchase happens                                │
│      ↓                                               │
│   6. Researcher publishes paper citing the           │
│      dataset AND the package                         │
│      ↓                                               │
│   7. Other researchers find the citation →           │
│      back to step 2                                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

Step 6 → 7 is the flywheel. Academic citations are permanent, discoverable, and trusted. Every paper that cites edinetsynth becomes a free advertisement that compounds over time.

## Competitive Moat

Even if a competitor generates similar synthetic EDINET data:

1. They'd need to build and maintain their own R package (ongoing effort)
2. They'd need CRAN acceptance (quality bar, review process)
3. They'd need to match the citation graph (takes years to accumulate)
4. Researchers already using edinetsynth won't switch unless the new package is dramatically better (switching cost = rewriting scripts)

This is a distribution moat, not a product moat. The data itself is defensible (70B local model, real flaw taxonomy), but the R package ecosystem makes it durable.

## Package Roadmap

### edinetsynth (Japan, current)

| Version | Features | Status |
|---------|----------|--------|
| 0.1.0 | Core 6 functions: load, extract, detect, compare, plot, summary | Built |
| 0.2.0 | +3 functions: inject_anomalies, export_to_hf_dataset, citation; confidence scores; ANOVA; Kanji validator | Built |
| 0.3.0 | Vignettes + `compare_to_baseline` overlay (ship aggregate EDINET statistics as inst/extdata) | Planned |
| 0.4.0 | `evaluate_utility()` — correlation matrices + propensity scores vs real EDINET aggregates | Planned |
| 1.0.0 | CRAN submission + Zenodo DOI | After first JDEX sale |

**Note on v0.3.0 baseline data:** EDINET filings are 法定開示書類 (legally mandated disclosure documents) — public record, not copyrightable by the filing companies. We can freely compute and ship aggregate statistics (mean/median/sd of segment lengths, vocabulary frequency distributions) derived from real filings as a small `.rds` file in `inst/extdata/`. No verbatim text needed, just numbers. This is not a copyright issue.

### decompliancesynth (Germany, future)

| Version | Features | Status |
|---------|----------|--------|
| 0.1.0 | Core functions: load, extract, validate, compare | Not started |
| 0.2.0 | BaFin compliance-specific validators | Not started |
| 0.3.0 | German text analysis (quanteda + SnowballC) | Not started |
| 1.0.0 | CRAN submission | After first Datarade sale |

## Risk Assessment

**R declining further:** Mitigated by recent TIOBE resurgence. Even if R drops again, academic users are slow to switch. The citation flywheel still works even at lower overall R adoption.

**Python package demanded instead:** We can build `edinetsynth-py` as a pip package later. The R package comes first because it has higher lock-in value per user.

**CRAN rejection:** CRAN has strict quality requirements. We need proper documentation (roxygen2), passing R CMD check, and no external dependencies that break on all platforms. Building tests now (21 testthat tests) de-risks this.

**Data quality complaints:** The R validation tools (validate_dataset.R, plot_quality_report) let us catch issues before listing. The user story simulation script serves as a pre-launch QA tool.

---

*Last updated: 2026-03-15*
