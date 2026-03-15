# Agricultural Data: National Market Beyond Aomori

## Scale of the Opportunity

Japan has over 1,700 municipalities, nearly all of which have agricultural commissions (農業委員会) — only municipalities with under 200ha of agricultural land (800ha in Hokkaido) may opt out, and fewer than 40 do. Each commission produces monthly meeting minutes. That's roughly 20,000+ documents per year nationally, all in non-standardized PDF format, scattered across individual municipal websites with no aggregation.

No synthetic dataset exists for this specific document type. However, JDocQA (published LREC-COLING 2024) already covers 5,504 Japanese administrative documents including government pamphlets, reports, and municipal materials — some touching on agricultural topics. The question is whether anyone needs *more* Japanese administrative text, and specifically agricultural commission minutes, badly enough to pay for it.

## Why Agricultural Administrative Japanese Is Valuable

Agricultural commission minutes sit at a unique intersection of three specialized vocabularies:

1. **Legal/administrative** — 農地法 (Agricultural Land Act) articles, 許可/不許可 (permitted/not permitted), 議案 (agenda items), 審議 (deliberation)
2. **Land registration** — 地番 (parcel ID), 地目 (land classification), 登記 (registration), 筆 (parcel counter)
3. **Agricultural domain** — 作付 (planting), 遊休農地 (abandoned farmland), 認定農業者 (certified farmer), 農業振興地域 (agricultural promotion zone)

Models trained only on general Japanese or legal Japanese underperform on this combined vocabulary. Synthetic training data with controlled quality tiers lets researchers measure exactly where their models fail.

## Demand Reality: What Research Shows

### The Macro Picture (Positive)

The Japan AI training dataset market is growing from ~$132M (2023) toward $1B+ by 2032. Synthetic data adoption grew 36% recently. Japan's 自治体DX push is real — AI-OCR vendors are actively deploying in municipalities, and the government itself publishes AI adoption guides for local government ([総務省 AI活用・導入ガイドブック](https://www.soumu.go.jp/main_content/000820109.pdf)). LAND INSIGHT's 圃場DX agricultural digitization service reached 110 municipalities across 38 prefectures with 500% YoY growth.

### The Micro Picture (Weak)

No evidence exists that anyone is specifically looking for synthetic agricultural commission minutes. Searches for "Nogyo Iinkai" + "NLP" or "training data" return zero relevant results. The specific buyer segments originally listed in this document need honest reassessment:

**Government DX vendors** — Real companies (NTT Data, Fujitsu, NEC) building municipal systems. But they build or commission their own training data. They don't browse JDEX for indie synthetic datasets. Selling to them would require enterprise sales motions (RFPs, procurement cycles, compliance reviews) that don't match a micro-SaaS model.

**Agricultural AI/IoT companies** — LAND INSIGHT, Sagri, and similar companies focus on satellite imagery, sensor data, and geospatial analysis. They do NOT process meeting minutes text. The "AgriTech needs NLP training data" claim doesn't hold up for this specific document type.

**Legal/compliance tech** — Plausible in theory (農地法 creates compliance workflows), but no evidence of companies building NLP-driven tools for agricultural land transaction compliance.

**Academic researchers** — The strongest signal. JDocQA proves researchers study Japanese administrative documents. But JDocQA already exists as a free dataset. The value proposition has to be "our synthetic data has controlled quality tiers for benchmarking" — a narrower sell than "we have Japanese administrative text."

### Who Might Actually Buy (Ranked)

1. **NLP researchers doing domain adaptation studies** — The most plausible buyer. "How well does Model X handle agricultural administrative Japanese?" is a publishable research question. But the total addressable market is probably dozens of research groups worldwide, not hundreds.

2. **AI-OCR vendors testing new deployments** — If a vendor wins a contract to digitize a specific municipality's agricultural commission archives, they might want synthetic test data. But this is opportunistic, not a reliable revenue stream.

3. **MAFF or prefectural government pilot projects** — Government agencies sometimes fund AI pilot projects. An agricultural data product could fit a MAFF-funded research initiative. But government procurement is slow and relationship-dependent.

### The Existing Competition (JDocQA)

JDocQA deserves specific attention as a quasi-competitor. It contains 5,504 real Japanese administrative documents with 11,600 QA pairs, published at LREC-COLING 2024, distributed under CC BY-SA 4.0. It covers government pamphlets, reports, slides, and websites from the National Diet Library and government ministries.

What JDocQA does NOT have that the synth-factory product would:

- Controlled quality tiers (the edinetsynth differentiator)
- Known injected flaws for benchmarking flaw detection
- Agricultural-specific domain coverage at scale
- JSONL format ready for HuggingFace `datasets` library

**With the triangulated QA framework** (from `EHCP-QA-TECHNIQUES-CROSS-POLLINATION.md`), the differentiation list grows significantly:

- **Blind extraction verification** — Every planted flaw has been independently confirmed by a different model architecture (Qwen 2.5 72B verifying Llama 3.3 70B output). JDocQA has no equivalent verification layer.
- **Dynamic ground truth with accidental flaws** — The ground truth includes both planted and naturally occurring errors, labeled and categorized. JDocQA's QA pairs are human-authored questions about document content, not error annotations.
- **Keyword detection signals** — Non-LLM verification for each flaw type (e.g., regex confirming absence of 農地法 reference in a "missing legal basis" flaw). Provides triangulation beyond LLM-only verification.
- **Published Cohen's Kappa scores** — Inter-rater reliability between human reviewer, LLM extractor, and keyword layer. This is the kind of methodological rigor that academic buyers look for in benchmark datasets.
- **Gradient prompting metadata** — Each flaw records which escalation attempt succeeded (subtle, forceful, mechanical), providing metadata about how "cooperative" each flaw type is with the generator model.
- **Peer-reviewed methodology** — Once the EHCP Audit dissertation publishes the Triangulated Probabilistic Ground Truth Framework, the agricultural dataset can cite it. JDocQA was published at LREC-COLING 2024, but its QA methodology is standard question-answer generation, not controlled error injection with adversarial verification.

Whether these differences matter enough to drive purchases is still the unproven question. But the gap between "synthetic text with quality tiers" and "verified benchmarking instrument with triangulated ground truth and published methodology" is substantially larger than the gap between "synthetic text" and "real text."

## If Demand Materializes: Expansion Path

These plans are explicitly gated behind proven demand (HuggingFace downloads or actual sales). Do not invest in any of this until the free 50-doc sample has been live for 3+ months.

### Geographic Variants (if warranted)

The YAML config system makes regional variants cheap to produce. Each region has distinct agricultural vocabulary:

- Aomori: apples (りんご), garlic (にんにく), nagaimo (長芋)
- Hokkaido: dairy (酪農), large-scale grain
- Niigata: rice (稲作)
- Kumamoto: livestock (畜産)

But producing regional variants without buyers is inventory, not product.

### Pricing (if warranted)

Start with one tier: 500 docs at ¥30,000 on JDEX. Add tiers only if the first tier sells. The R package, Datarade listing, and enterprise pricing are future possibilities, not plans.

## Competitive Position

No one sells synthetic Japanese agricultural commission minutes. "No competition" can mean "no market." But with the QA framework, the competitive question shifts. The product isn't competing with other synthetic agricultural text (there is none) — it's competing in the broader category of "verified benchmarking datasets for Japanese document understanding." In that category, the competition is JDocQA (real docs, no controlled errors, no verification pipeline) and whatever individual research groups produce for their own papers (usually small-scale, not shared).

The moat is the QA pipeline itself, not the agricultural domain. A competitor who wanted to replicate the product would need: a locally-run 70B generator, a different-architecture verifier, the flaw injection taxonomy, the blind extraction logic, keyword detection patterns for agricultural Japanese, HITL calibration with published Kappa scores, and the integration to ship all of this as metadata alongside the JSONL. That's not trivial to build, even though each individual piece is straightforward.

## Cross-Pollination: Multiple Dimensions

The QA framework creates cross-pollination in three directions:

1. **edinetsynth → agricultural data** — Same pipeline, different YAML config. Customers who buy one product trust the quality methodology of the other.

2. **Agricultural data → dissertation** — The agricultural dataset is a second domain for the Triangulated Probabilistic Ground Truth Framework. The dissertation is stronger if the methodology generalizes beyond EHCP (education) to a completely different domain (agriculture). This strengthens the academic publication, which in turn strengthens the dataset's credibility.

3. **QA pipeline → QA-as-a-Service** — The cross-pollination doc flags this explicitly: "Upload your synthetic dataset + flaw specification → Get a blind extraction QA report + enriched ground truth." If the pipeline proves valuable across 3+ domains (EHCP, EDINET, agricultural), it could be productized as a standalone service. This is the highest-ceiling micro-SaaS opportunity in the whole stack — every ML team generating synthetic test data needs quality verification, and nobody offers it as a service.

## Honest Risk Assessment

**The core risk**: This product has unproven demand for direct sales. The buyer segments that sound plausible on paper (AgriTech, DX vendors, legal tech) don't hold up under scrutiny.

**What the QA framework changes**: The product shifts from "synthetic text" (commodity, weak demand) to "verified benchmarking instrument" (specialized, potentially stronger demand among a smaller audience). The risk doesn't disappear, but the ceiling is higher because the QA metadata is the kind of artifact that academic conferences and enterprise procurement processes value.

**Why it's still worth building**:

1. **Marginal cost is near-zero.** YAML config: 1 day. QA pipeline: already built for other domains. Beelink compute: runs regardless.

2. **The banking lever has outsized value.** JA Oirase corporate account unlocks all future products.

3. **HuggingFace as free demand signal.** Post 50 documents with full QA metadata. The QA report itself is marketing — it demonstrates a quality standard no free dataset matches. Downloads + Stars are the signal.

4. **Subsidy justification.** "Agricultural data product" ties to Hachinohe's local relevance. (Note: the rent subsidy caps at ¥2M/year for software businesses and requires 3+ local employees — see AOMORI-GRANTS-SUBSIDIES.md for corrected details.)

5. **Dissertation generalizability.** A second domain for the QA methodology strengthens the PhD paper.

6. **QA-as-a-Service prototype.** Every domain you validate with the pipeline is another proof point for the potential standalone QA service.

**What NOT to build until demand is proven**: The R package, geographic expansion, Datarade listing, enterprise pricing. Ship the HuggingFace sample with full QA metadata and wait for signals.
