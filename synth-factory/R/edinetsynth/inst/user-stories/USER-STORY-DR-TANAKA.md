# User Story: Dr. Yuki Tanaka Evaluates the VilseckKI EDINET Dataset

**Persona:** Dr. Yuki Tanaka (田中 有紀), Senior NLP Researcher
**Affiliation:** 架空テック研究所 (Kakuu Tech Research Institute), Tokyo
**Task:** Evaluate synthetic EDINET data for fine-tuning a Japanese financial document classifier
**Budget authority:** ¥500,000/year for external datasets (team discretionary)
**Technical profile:** R + Python bilingual, publishes in ACL/EMNLP, maintains 2 HuggingFace models

---

## Act 1: Discovery (Tuesday morning, 10:15 AM)

Tanaka-san's team is building a compliance anomaly detector for a financial regulator
client. They need training data — real 有価証券報告書 with labeled flaws — but real
filings with known flaws are rare, and the ones that exist are locked behind EDINET's
raw XBRL with no flaw labels.

She opens JDEX (Japan Data Exchange) and searches: `EDINET 合成データ`.

### What she sees on the JDEX listing:

**VilseckKI Synthetic EDINET Securities Reports (有価証券報告書)**
- 500 documents, 4 quality tiers, 8 report sections
- 4 FSA compliance flaw types with verified injection
- Quality-tiered: Tier 1 (clean) through Tier 4 (severe)
- Format: JSONL (one document per line)
- Companion R package: `edinetsynth` on GitHub
- License: CC-BY-4.0

What catches her eye: the listing includes a **flaw survival heatmap** and an
**FSA verification summary chart** showing 97.8% survival rate on VAGUE_RISK_FACTOR
and 100% on SOFTENED_GOING_CONCERN. She has never seen a synthetic dataset vendor
publish verification metrics at the individual flaw level. Every other dataset she
has evaluated simply says "human-reviewed" with no quantitative evidence.

She clicks "Free Sample (50 documents)" and downloads `vilseckki_edinet_sample.jsonl`.

---

## Act 2: First Look with edinetsynth (Tuesday, 10:45 AM)

She installs the companion package:

```r
# install.packages("devtools")
devtools::install_github("misawa-data-gk/edinetsynth")
library(edinetsynth)
```

### Step 1: Load

```r
reports <- load_securities_report("vilseckki_edinet_sample.jsonl")
```

She sees: 50 rows, columns including `document_id`, `quality_tier`, `error_rate`,
and 8 segment columns (`seg_company_overview`, `seg_business_status`,
`seg_business_risks`, `seg_md_and_a`, etc.).

Her first thought: "8 sections? Most synthetic Japanese datasets I've seen only
have 2-3 fields. This has the full 有報 structure."

### Step 2: Segment statistics

```r
stats <- segment_summary(reports)
```

She checks: are the segment lengths realistic? Do they match what real EDINET
filings look like? She has benchmarks from her own corpus of 200 real filings.

Key observations:
- `seg_business_risks` has mean ~400 chars — realistic for mid-cap companies
- `seg_md_and_a` is the longest section — correct, MD&A is always the densest
- No segments are >50% empty — the generator didn't collapse on any section

### Step 3: Tier distribution

```r
tiers <- compare_tiers(reports)
```

She sees the 80/10/8/2 split (perfect/near/moderate/severe). The deviation is
within sampling noise for n=50. The ANOVA p-value (attached as attribute) shows
flaw count is significantly different across tiers — the tiers aren't just labels,
they correspond to genuinely different error densities.

### Step 4: Flaw detection

```r
flaws <- detect_flaws(reports)
```

This is the moment that matters. She sees 12 flaws detected across the 50 documents:
- 6 in `seg_business_risks` (vague risk language)
- 3 structural flaws (empty sections in Tier 4)
- 2 stub sections
- 1 generation artifact

She cross-references with the `quality_tier` column: all 12 flaws are in Tier 2-4
documents. Zero false positives in Tier 1. She opens a few Tier 4 documents and reads
the Japanese — the vague risk language is genuinely vague, not artificially truncated.
It reads like a real 有報 that a lazy IR officer wrote.

Her reaction: "This is actually usable for training a flaw classifier."

### Step 5: Extract for NLP pipeline

```r
risks <- extract_segment(reports, "business_risks", with_id = TRUE)
```

She feeds the risk sections into her tokenizer. The mean token count (~270 tokens
per section) is in the right range for her BERT-based classifier. She runs a quick
embedding similarity check against her real EDINET corpus — the synthetic text
clusters near the real text in embedding space, not in a separate synthetic island.

### Step 6: Visualization

```r
plot_quality_report(reports, output_dir = "eval_plots/")
plot_advanced_quality(reports, output_dir = "eval_plots/")
```

She generates the same heatmap she saw on the JDEX listing. It matches. The tier
density chart confirms the controlled injection pattern. She pastes the section
quality scorecard into her Slack channel for the team to review.

---

## Act 3: The Decision (Tuesday, 2:00 PM)

Tanaka-san's evaluation checklist:

1. ✓ Structural completeness — 8 sections, matches real 有報
2. ✓ Content quality — Japanese Keigo, no English leakage, realistic lengths
3. ✓ Flaw labeling — tiers correspond to actual error density
4. ✓ NLP suitability — tokens are in fine-tuning range, embeddings cluster correctly
5. ✓ Verification evidence — heatmaps prove flaws survived generation

She opens a Slack thread:

> 田中: サンプルデータを評価しました。VilseckKI EDINET合成データは品質が高い。
> フル500件（¥XXX,XXX）の購入を推薦します。
> 理由：欠陥検証が定量的に実証されている（生存率97%以上）。
> 比較した他のデータセットにはこのレベルのQAがない。
>
> (Tanaka: I've evaluated the sample data. VilseckKI EDINET synthetic data is
> high quality. I recommend purchasing the full 500 documents (¥XXX,XXX).
> Reason: Flaw verification is quantitatively demonstrated (>97% survival rate).
> Other datasets I've compared don't have this level of QA.)

She downloads the full dataset, runs the same pipeline on all 500 documents, and
exports to HuggingFace format:

```r
full <- load_securities_report("vilseckki_edinet_full.jsonl")
export_to_hf_dataset(full, output_dir = "hf_export/", stratify_by = "quality_tier")
```

Her Python colleague loads it that afternoon:
```python
from datasets import load_dataset
ds = load_dataset("json", data_files={"train": "train.jsonl", "test": "test.jsonl"})
```

---

## Act 4: The Referral (Two weeks later)

Tanaka-san presents preliminary results at an internal review. Her flaw classifier,
trained on VilseckKI data, achieves 0.91 F1 on detecting vague risk language in a
held-out set of real EDINET filings.

A colleague from the compliance tools team asks: "Where did you get labeled data
with this kind of flaw taxonomy?"

She sends them the JDEX listing and the edinetsynth GitHub link. The colleague,
who is building an internal compliance checker (not unlike the FSA Compliance Linter
idea), realizes the taxonomy itself is valuable — not just the synthetic text.

---

## What Made the Sale

1. **The free sample was evaluable, not just browsable.** The edinetsynth R package
   turned a JSONL file into a structured evaluation in 15 minutes. Without the package,
   she would have spent 2 hours writing ad-hoc parsing scripts.

2. **The visualizations were the proof.** The flaw survival heatmap is something no
   competitor can produce because no competitor has a triangulated QA pipeline.
   Screenshots of those plots went into the purchase justification.

3. **The bidirectional verification.** Tier 1 documents pass all checks AND Tier 4
   documents fail the right checks. This is what convinced her the tiers aren't
   arbitrary labels.

4. **Zero friction to NLP pipeline.** `extract_segment()` → tokenizer → fine-tuning.
   No format wrestling, no encoding nightmares, no undocumented schema.

5. **The citation function.** She knew she could cite the dataset properly in her
   paper. Academic buyers need this.

---

## Touchpoints Where We Could Lose the Sale

- **If segment lengths were unrealistically uniform** — real 有報 sections vary
  widely. Synthetic data with suspiciously identical lengths signals template-based
  generation.

- **If Tier 1 had flaws** — false positives in "clean" documents destroy trust
  instantly. The bidirectional verification catches this.

- **If the Japanese was unnatural** — financial Keigo is specific. Generic Japanese
  reads as obviously synthetic to anyone who has read real filings.

- **If there was no R package** — forcing the buyer to write their own JSONL parser
  adds 2 hours of friction and signals amateur packaging.

- **If there was no free sample** — Japanese enterprise procurement requires
  evaluation before purchase. No sample = no evaluation = no purchase.

---

## Key Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| Time from download to first plot | < 15 min | Attention span of evaluator |
| Flaw survival rate (displayed) | > 90% | Below this, verification isn't credible |
| False positive rate in Tier 1 | 0% | Any false positive kills trust |
| HF export round-trip | < 5 min | Buyer must reach their Python pipeline same day |
| Sample → purchase conversion | > 20% | Industry standard for data marketplace samples |

---

*This user story drives the design of edinetsynth, the JDEX listing,
and the marketplace visualizations. Every function in the package exists
because Tanaka-san needs it during her 15-minute evaluation window.*
