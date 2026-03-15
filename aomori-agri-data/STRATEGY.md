# Aomori Agricultural Data Product Strategy

## The Product: Synthetic Nogyo Iinkai Gijiroku (農業委員会議事録)

Agricultural Commission minutes are publicly mandated municipal documents published as PDFs. Every municipality in Japan with agricultural land has a Nogyo Iinkai (農業委員会) that meets monthly to deliberate on land-use transfers, farmland conversion applications, zoning changes, and Agricultural Land Act (農地法) compliance.

These documents combine structured legal/administrative Japanese with domain-specific agricultural terminology, land parcel identifiers, and deliberation language that doesn't appear in standard corpora. However, the demand picture for this specific data product needs honest scrutiny — see the "Demand Reality Check" section below.

### What the Synthetic Dataset Contains

Each synthetic document models one monthly commission meeting with segments:

| Segment | Japanese | Content |
|---------|----------|---------|
| Meeting header | 会議録ヘッダー | Date, location, attendees, quorum confirmation |
| Agenda items | 議案一覧 | Numbered list of applications under review |
| Land transfer deliberations | 農地法第3条許可 | Buyer/seller, parcel ID (地番), area (反/㎡), intended use, commission vote |
| Farmland conversion | 農地法第4条/第5条許可 | Conversion from agricultural to other use, with conditions |
| Activity reports | 活動報告 | Agricultural promotion activities, inspection results |
| Administrative matters | その他行政事項 | Budget, schedule, policy updates |

### Why This Data Is Hard to Get

Real Nogyo Iinkai minutes are published as scanned PDFs on individual municipal websites with no central repository, no API, and no standard format. A researcher wanting to train an NLP model on agricultural administrative Japanese would need to manually collect PDFs from hundreds of municipal websites, OCR them (often poor scan quality), and normalize wildly different formats.

The synthetic version solves this by generating structurally consistent documents based on real format patterns, with controlled quality tiers and known flaw injection — the same approach as edinetsynth for EDINET filings.

### Generation Approach

Reuses the synth-factory pipeline with a new YAML config (`configs/agricultural-minutes-jp.yaml`). The 70B locally-run LLM generates each segment sequentially with context from prior segments (e.g., the deliberation segment references parcel IDs from the agenda). Error injection follows the same taxonomy: empty sections, stub text, garbled characters, generic boilerplate, repetition.

Seed data for realistic parcel IDs, area measurements, and crop types can be drawn from MAFF's publicly available agricultural census data (農林業センサス) and the National Land Numerical Information (国土数値情報) farmland datasets.

### Triangulated QA: The Real Differentiator

The cross-pollination document (`vilseckki-datafactory-app/EHCP-QA-TECHNIQUES-CROSS-POLLINATION.md`) describes five QA techniques developed for the EHCP Audit dissertation that transfer directly to the agricultural data product. These techniques transform what would otherwise be "just more synthetic text" into something no competitor offers: **verified labeled data with triangulated ground truth**.

**Why this matters for the demand problem:**

The demand weakness identified earlier was: "why pay for synthetic agricultural minutes when real ones exist as free PDFs?" The answer is that real PDFs have no labels. You can't benchmark a flaw detector, train a quality classifier, or evaluate a document understanding model against unlabeled data. The synth-factory product ships every document with:

1. **Planted flaws** (from `FlawInjector`) — known errors at known locations
2. **Verified flaws** (from blind extraction) — an independent model confirms each flaw actually manifests in the text
3. **Accidental flaws** (from dynamic ground truth) — naturally occurring errors captured and labeled, not just planted ones
4. **Keyword verification signals** — non-LLM confirmation layer for each flaw type
5. **Cohen's Kappa scores** (from HITL calibration) — publishable inter-rater agreement between human, LLM, and keyword layers

This is the difference between "synthetic text" and "a benchmarking instrument." JDocQA has 5,504 documents with QA pairs but no controlled error injection, no quality tiers, and no verification methodology. The synth-factory product is designed for a different use case: measuring how well your system detects known flaws at known difficulty levels.

**Specific agricultural application of each technique:**

| Technique | Agricultural Application |
|-----------|------------------------|
| Blind extraction | Verify that a planted "missing 地番" flaw actually manifests — send the generated deliberation to Qwen 2.5 72B with the full agricultural flaw taxonomy, without telling it what was planted |
| Dynamic ground truth | When generating text about farmland conversion (農地法第5条), the LLM may accidentally produce inconsistent area measurements (反 vs ㎡ conversion errors). Capture these as labeled accidental flaws. |
| Gradient prompting | Agricultural terminology is niche; the 70B model may fail to inject subtle flaws like "incorrect crop classification code." Escalate: subtle → forceful → mechanical insertion. |
| Keyword detection | Fast regex: does a "missing quorum" flaw actually lack the word "定足数"? Does a "missing legal basis" flaw actually lack "農地法第X条"? Free, instant verification. |
| HITL calibration | 15-minute daily review of 4-8 disagreement cases. The resulting Kappa scores go into the Gebru-style datasheet. |

**Model heterogeneity on the Beelink:**

The Beelink GTR9 Pro (64GB RAM) can run two different model families. For agricultural data: generate with Llama 3.3 70B, verify with Qwen 2.5 72B. Different architectures prevent correlated blind spots — if Llama fails to inject a flaw properly, Qwen is more likely to catch it than another Llama instance would be.

**Implementation cost:** The five QA techniques are estimated at 10-14 hours total across the data factory, and the agricultural product benefits from them at zero additional cost once they're built for any domain. The highest-impact single technique (blind extraction alone) takes ~3 hours and catches the most critical failure mode: flaws that were requested but didn't manifest.

## The Banking Lever: JA Oirase Strategy

### Why JA Bank

JA (Japan Agricultural Cooperatives / 農業協同組合) is a cooperative banking system with a mandate to support agricultural communities. JA Oirase (JA おいらせ) serves the Misawa/Hachinohe area and, as a cooperative rather than a commercial bank, has different incentive structures from megabanks.

The strategic insight: a foreign-owned GK (合同会社) applying for a corporate account at MUFG or SMBC faces intense AML scrutiny and frequent rejection. A GK whose stated business purpose is "generating synthetic agricultural data products for NLP research, with specific relevance to Aomori's agricultural sector" has a natural relationship story at JA Oirase that no Tokyo megabank would appreciate.

### The Relationship Sequence

1. **Hachinohe Trial Satellite Office** (八戸市おためしサテライトオフィス) — Participate in this real subsidized program where the city covers travel costs and provides free coworking. This creates a documented physical presence and relationship with Hachinohe's enterprise recruitment office.

2. **Agricultural data product development** — While using the satellite office, begin developing the agricultural minutes dataset. This is genuine work — but be realistic about its commercial value (see Demand Reality Check above). The important thing is that it's a credible business activity, not that it generates revenue immediately.

3. **JA Oirase introduction** — Hachinohe's enterprise recruitment office (企業立地推進課) regularly facilitates introductions to local financial institutions for incoming businesses. Request an introduction to JA Oirase, citing the agricultural data product as the business purpose.

4. **Corporate account application** — Apply with: GK registration (登記簿謄本), business plan emphasizing agricultural data, evidence of the satellite office participation, and the Hachinohe subsidy application (showing the city itself is supporting the business).

### Why This Works Better Than Direct Application

JA cooperatives evaluate corporate accounts partly on relevance to their cooperative mission. A data company producing agricultural NLP training data has an obvious connection that a generic "IT company" does not. The satellite office participation demonstrates commitment to the region rather than being a paper-only entity.

### Requirements for Foreign Nationals

JA Bank corporate accounts require the representative director to present a residence card (在留カード). For a GK where the representative is a non-resident, this means either obtaining a Business Manager visa (経営・管理) or appointing a Japan-resident representative. The agricultural data product strengthens a Business Manager visa application by demonstrating genuine business operations in Japan.

## Demand Reality Check

**What the research shows:**

The Japan AI training dataset market is real and growing — projected from $132M (2023) to over $1B by 2032, with 36% synthetic data adoption growth ([Credence Research](https://www.credenceresearch.com/report/japan-ai-training-datasets-market)). The municipal DX push is real — AI-OCR vendors like FROG, DX Suite, and NTT Data's NaNaTsu are actively selling to municipalities. LAND INSIGHT's 圃場DX has reached 110 municipalities with 500% YoY growth ([INCLUSIVE Holdings](https://inclusive.co.jp/2025/06/23/20250623_li_farm_field_dx/)).

**What the research does NOT show:**

No evidence that anyone is currently buying or requesting synthetic agricultural commission minutes specifically. Zero search results for "Nogyo Iinkai" + "NLP dataset" or "training data." The existing JDocQA dataset (5,504 Japanese administrative documents published at LREC-COLING 2024) already covers Japanese government document QA including some agricultural topics ([arxiv](https://arxiv.org/abs/2403.19454)). AgriTech companies like LAND INSIGHT and Sagri focus on satellite/sensor data, not text NLP on meeting minutes. AI-OCR vendors build their own training pipelines rather than buying domain-specific synthetic text.

**The honest picture (updated with QA framework):**

The "NLP researchers buying agricultural training data" buyer is speculative for *plain synthetic text*. JDocQA proves academic interest in Japanese administrative documents, but it already exists and is free. The question is whether the synth-factory product offers something JDocQA doesn't.

With the triangulated QA framework (see above), the answer shifts from "probably not" to "maybe." The product isn't competing as "more Japanese text" — it's competing as "a benchmarking instrument with verified ground truth, controlled quality tiers, and published inter-rater reliability." That's a different product category. Researchers building flaw detection systems, document quality classifiers, or OCR evaluation pipelines need labeled data with known error distributions. Real PDFs and JDocQA don't provide that.

**Does this fully solve the demand problem?** No. The market for "Japanese agricultural administrative benchmarking instruments" is still small. But it's a more defensible position than "more synthetic text," and the triangulated QA methodology is the same one heading toward publication as part of the EHCP Audit dissertation — which means the agricultural dataset can cite a peer-reviewed methodology paper. That's a signal that academic buyers respond to.

**What this means for the product's role:**

The agricultural data product's primary value remains strategic rather than revenue-driven:

1. **Banking lever** — Gives JA Oirase a reason to care about the GK
2. **Subsidy justification** — Genuine business purpose for Hachinohe's IT subsidies
3. **Near-zero marginal cost** — YAML config + QA pipeline costs ~1 day of work on top of infrastructure built for other domains
4. **Portfolio diversification** — Multiple products on JDEX, each with the same QA methodology
5. **Dissertation showcase** — The agricultural dataset demonstrates the QA methodology in a second domain (beyond EHCP), strengthening the dissertation's generalizability claim

Don't build the R package, the elaborate geographic expansion, or the Datarade listing until someone actually buys. But DO apply the full QA pipeline (blind extraction, dynamic ground truth, keyword verification) to whatever you generate — the QA report and Kappa scores are the product's moat, and they cost nothing extra once the pipeline exists.

## Possible Buyers (Ranked by Likelihood)

### Most likely: AI-OCR / Municipal DX Vendors

The strongest signal. Japan has an active push to digitize municipal documents. Vendors like NTT Data, Fujitsu, and smaller 自治体DX specialists are deploying AI-OCR systems and need test documents. However, these companies typically generate their own test data or use anonymized real documents — they're not accustomed to buying synthetic datasets from indie producers. The sales motion would require direct outreach and probably a free trial.

### Plausible (stronger with QA framework): NLP Researchers

JDocQA's existence at LREC-COLING 2024 proves researchers study Japanese administrative documents. JDocQA uses real documents — but with the triangulated QA framework, the synth-factory product isn't competing with JDocQA on "more text." It's competing on "labeled benchmarking data with known error distributions." A researcher building a document quality classifier can't use JDocQA for that — they need data where the ground truth is verified, the flaws are categorized by type and severity, and the quality tiers have known statistical properties. That's what the QA framework produces.

The dissertation publication angle strengthens this: once the EHCP Audit methodology is published, the agricultural dataset can cite it. That transforms the HuggingFace listing from "some random synthetic data" to "data produced using the methodology from [Published Paper]." Researchers respond to that signal.

### Speculative: AgriTech Companies

Japanese AgriTech is focused on sensors, satellites, and IoT — not on text NLP. LAND INSIGHT processes satellite imagery, not meeting minutes. Companies building farm management systems work with structured data (soil readings, weather, yields), not unstructured administrative text. This buyer segment is largely imaginary for this specific product.

### Speculative: Legal/Compliance Tech

Could exist in theory (the Agricultural Land Act creates compliance workflows), but no evidence of companies building NLP-driven compliance tools specifically for agricultural land transactions.

## Revenue Model (Scaled Down, QA-Enhanced)

Given the unproven demand, start minimal — but ship with full QA from day one:

- **Free sample on HuggingFace** — 50 documents with full QA metadata: planted flaws, blind extraction results, keyword verification signals, Kappa scores. The QA report IS the marketing material — it demonstrates a quality standard no competitor matches. Downloads are the demand signal.
- **JDEX listing** — 500-doc dataset at ¥30,000, only if the HuggingFace sample gets traction. Include the Gebru-style datasheet with triangulated QA metrics and methodology citation.
- **R package only if edinetsynth proves the flywheel** — If edinetsynth on CRAN drives data sales, clone for agrisynth. If not, don't.
- **QA-as-a-Service angle** — The cross-pollination doc flags this: "Upload your synthetic dataset + flaw specification → Get a blind extraction QA report + enriched ground truth." If the QA pipeline proves its value across edinetsynth and agricultural data, it could become a standalone product. This is speculative but worth noting as a potential pivot.

Revenue expectation: Still treat as ¥0 until proven. But the QA framework raises the ceiling — verified labeled benchmarking data commands higher prices than unlabeled synthetic text if there's a buyer.

## Synth-Factory Integration

The agricultural data product requires no new synth-factory code — only a new YAML config file and potentially new seed data sources. The document generation extension (currently in the plan at `concurrent-questing-canyon.md`) is the infrastructure that enables this.

### Config Concept: `configs/agricultural-minutes-jp.yaml`

```yaml
metadata:
  name: nogyo-iinkai-gijiroku
  version: "1.0.0"
  description: "Synthetic Agricultural Commission Meeting Minutes"
  language: ja
  license: CC-BY-4.0

document_types:
  - name: monthly_minutes
    language: ja
    format: markdown
    segments:
      - name: meeting_header
        segment_type: form_field
        label: "会議録"
        prompt: >
          Generate a realistic meeting header for a municipal Agricultural
          Commission (農業委員会) monthly meeting. Include: date, location
          (meeting room in city hall), start/end times, attendee count with
          quorum confirmation, chairperson name. Municipality: {municipality}.
        max_tokens: 200
        required_keywords: ["農業委員会", "定例会", "出席委員"]

      - name: agenda_items
        segment_type: list_field
        label: "議案"
        prompt: >
          Generate a numbered agenda item for an agricultural land transfer
          application under Article 3 of the Agricultural Land Act (農地法第3条).
          Include: application number, applicant name, parcel location (地番),
          area in square meters, current use, intended use, transfer type.
          This is item {item_number} of {total_items}.
        list_min: 3
        list_max: 8
        max_tokens: 300
        context_dependencies: [meeting_header]
        required_keywords: ["農地法"]

      - name: deliberation
        segment_type: section
        label: "審議"
        prompt: >
          Generate the deliberation section where the commission discusses
          the agenda items. Reference specific agenda items by number.
          Include commissioner questions, staff explanations, and the
          vote result (許可/不許可). Maintain formal meeting minutes style.
          Agenda items for reference: {agenda_items}
        max_tokens: 800
        context_dependencies: [meeting_header, agenda_items]

      - name: activity_report
        segment_type: section
        label: "活動報告"
        prompt: >
          Generate an agricultural promotion activity report. Include:
          farmland patrol results, abandoned land (遊休農地) survey findings,
          new farmer consultation summary. Reference the municipality's
          agricultural characteristics. Municipality: {municipality}.
        max_tokens: 400
        context_dependencies: [meeting_header]

      - name: admin_matters
        segment_type: section
        label: "その他"
        prompt: >
          Generate administrative matters section: next meeting date,
          budget items, policy updates from prefectural agriculture
          department. Keep brief and procedural.
        max_tokens: 200

document_tables:
  - name: aomori_minutes
    records: 500
    document_type: monthly_minutes
    seed_table: municipalities
```

## Downstream Market: Food Self-Sufficiency & Farmland Abandonment

### The Crisis Is Real and Urgent

Japan's food self-sufficiency has been stuck at 38% (calorie basis) for four consecutive years, far below the 45% target for 2030. MAFF warned in 2025 that by 2035, one-third of farmland (1.3 million hectares of 4.22 million) could be abandoned due to a labor crisis — average farmer age is above 67 and successors are disappearing as younger generations migrate to cities. The 2024 revision of the Basic Act on Food, Agriculture and Rural Areas (食料・農業・農村基本法) — the first major revision in 25 years — elevated food security (食料安全保障) to a core legal principle.

This creates genuine urgency and research attention around agricultural land management. The question is whether that attention connects to the meeting minutes.

### How Agricultural Commissions Connect to the Crisis

Agricultural commissions aren't peripheral observers — they're the statutory gatekeepers. Under the Agricultural Land Act, commissions must:

1. **Conduct annual farmland patrols** (利用状況調査) — mandatory inspection of ALL agricultural land in their jurisdiction, at least once per year. Results feed into GIS databases tracking abandoned/underutilized land.
2. **Survey landowner intentions** (利用意向調査) — for land flagged as idle, commissions must survey owners about future use plans.
3. **Approve or deny all agricultural land transactions** — every sale, lease, or conversion under Articles 3, 4, and 5 of the Agricultural Land Act goes through commission deliberation.
4. **Report abandoned land data** — feeds into MAFF's national tracking and the farmland bank (農地中間管理機構) consolidation efforts.

The commissions are where Japan's farmland abandonment data *originates*. The meeting minutes document the deliberation behind every permit and denial.

### Where the Research Actually Lives (and Where It Doesn't)

**Where researchers DO use commission-adjacent data:**

Published research on Japanese farmland abandonment uses three main data sources: MAFF census data (農林業センサス, every 5 years, self-reported), satellite/aerial imagery (JAXA, LAND INSIGHT's 圃場DX, OPTiM's Digital Earth Scanning), and GIS databases compiled from farmland patrol results. Multiple peer-reviewed papers in MDPI's *Land* and *Sustainability* journals, PLOS ONE, and Springer Nature analyze spatial patterns and determinants of abandonment using these sources.

Key papers: [Estimation of Determinants of Farmland Abandonment and Its Data Problems](https://www.mdpi.com/2073-445X/10/6/596) (MDPI Land, 2021), [Spatial Pattern of Farmland Abandonment in Japan](https://www.mdpi.com/2071-1050/10/10/3676) (Sustainability, 2018), [Socio-economic drivers of irrigated paddy land abandonment](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0266997) (PLOS ONE, 2022).

**Where researchers do NOT (yet) use the data:**

No published research uses the *text* of meeting minutes for NLP analysis. The meeting minutes are published for transparency and accountability, not as a research dataset. Researchers use the GIS patrol results (spatial data) and census data (structured/numeric), not the deliberation transcripts (unstructured text).

The GIS patrol data is particularly interesting: it's compiled by individual municipalities, contains sensitive personal information (landowner identities, parcel details), and is NOT publicly available. Researchers obtain access through academic cooperation agreements with individual municipalities.

### The Untapped NLP Opportunity

Here's what no one has done yet: **extract structured decision data from commission deliberation text.**

The meeting minutes contain structured information embedded in unstructured text: which applications were approved vs. denied, under what conditions, what factors commissioners discussed, what land use changes were proposed. A researcher who wanted to analyze patterns in commission decisions — what predicts permit vs. deny? how do conditions vary by region? how has decision-making changed as the abandonment crisis worsened? — would need to extract that structured data from the text. That's an NLP information extraction task.

Synthetic commission minutes with planted decision patterns (e.g., "this document contains a denied Article 5 conversion application due to insufficient agricultural promotion zone justification") would let researchers train and evaluate information extraction models without needing access to the restricted real GIS databases.

**Is anyone doing this today?** No. This is a "should exist" argument, not a "people are buying this" observation. But the policy urgency is real (the Basic Act revision, the MAFF 2035 warning, the fourfold budget increase request for farmland banks), and the NLP community's interest in Japanese administrative documents is demonstrated by JDocQA. The gap between "nobody has done this" and "nobody wants this" may be narrower for this specific application than for generic agricultural NLP.

### NARO's AI Prediction Model: A Demand Signal

NARO (National Agriculture and Food Research Organization / 農研機構) built an AI model to predict farm exit rates at the municipality level, supporting the 人・農地プラン (People and Farmland Plan) initiative. This demonstrates that Japan's agricultural research establishment is actively using AI for farmland management analysis. NARO uses structured data (census, survey results), but a research team that wanted to incorporate commission deliberation text into predictive models would need the kind of labeled training data the synth-factory produces.

This isn't a confirmed buyer. But it's a confirmed use case direction — Japan's agricultural research infrastructure is moving toward AI-driven analysis of the farmland crisis, and commission meeting minutes are an untapped text source for that analysis.

### What This Means for Positioning

The food self-sufficiency angle doesn't change the core demand assessment (unproven), but it changes the *story* in three ways:

1. **Grant applications** — Framing the data product as supporting food security research (食料安全保障研究支援) is more compelling than "NLP training data" when applying for MAFF-adjacent grants or explaining the business to Hachinohe's enterprise recruitment office.

2. **HuggingFace dataset description** — Tagging the dataset with food security, farmland abandonment, and agricultural land governance keywords connects it to an active research community that might not search for "agricultural commission minutes" but would search for "Japanese food security data."

3. **Dissertation angle** — The synth-factory methodology (controlled error injection + triangulated QA) applied to agricultural governance documents is a publishable contribution to the intersection of NLP and agricultural policy research. That's a conference paper independent of the EHCP Audit dissertation.

## Timeline (Lean Approach)

1. **Now**: Document strategy, verify grants, establish directory (this document)
2. **After edinetsynth proves the flywheel works**: Decide whether the agricultural data product justifies R package investment
3. **After document generation extension is built**: Create `agricultural-minutes-jp.yaml` config (1 day of work)
4. **Generate 50-doc sample**: Post to HuggingFace as free dataset, measure downloads over 3 months
5. **If downloads are promising OR when GK formation begins**: Generate full 500-doc dataset for JDEX
6. **After GK formation**: Apply for Hachinohe Trial Satellite Office
7. **During satellite office period**: Use agricultural data product as the business story for JA Oirase introduction

The key gate is step 4 — HuggingFace downloads are a free demand signal. If nobody downloads a free sample, nobody will pay ¥30,000 for a larger one. If that happens, the agricultural product still works as a banking lever (JA Oirase doesn't need to verify your sales figures), but adjust expectations accordingly.
