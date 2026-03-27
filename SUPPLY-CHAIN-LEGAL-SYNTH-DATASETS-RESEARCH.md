# Corpus Library Research: Supply Chain, Legal/Compliance, and Synthetic Data Meta-Resources

## Purpose
Training corpuses for fine-tuning models on a 128GB RAM machine to generate synthetic data in supply chain, legal/compliance, and regulatory domains. Focus on UNCOMMON and UNDERSERVED datasets.

---

## DOMAIN 1: Synthetic Data Generation / Meta-Datasets

### 1.1 PleIAs/SYNTH
- **URL:** https://huggingface.co/datasets/PleIAs/SYNTH
- **Size:** 79.6M text samples, ~75B tokens (41B words)
- **Format:** Parquet
- **License:** CDLA-Permissive-2.0
- **Language:** English (80%), French, German, Italian, Spanish, Polish, Dutch, Latin
- **Rarity:** MEDIUM -- first fully-open generalist synthetic dataset; seed texts are CC-BY-SA Wikipedia; generated with models that allow output reuse
- **Fine-tuning potential:** HIGH -- demonstrates a complete synthetic amplification pipeline from 58K Wikipedia articles to 79.6M samples

### 1.2 NIST SDNist -- Benchmark Data for Synthetic Data Evaluators
- **URL:** https://github.com/usnistgov/SDNist
- **Size:** ACS excerpt: 24 features, 40K records; SBO excerpt (new 2025): 130 features, 161K records
- **Format:** CSV/Python package (auto-downloads)
- **License:** Public domain (NIST)
- **Rarity:** HIGH -- most people in ML do not know NIST maintains a standard benchmark for evaluating synthetic data generators; the 2025 SBO dataset with 130 features is particularly rare
- **Fine-tuning potential:** HIGH -- the gold standard for benchmarking privacy/utility tradeoffs

### 1.3 SDV SDMetrics + SDGym
- **URL:** https://github.com/sdv-dev/SDMetrics | https://github.com/sdv-dev/SDGym
- **Size:** 30+ metrics; SDGym includes bundled benchmark datasets
- **Format:** Python library with built-in demo datasets
- **License:** MIT (SDMetrics), source-available (SDGym)
- **Rarity:** MEDIUM -- well-known in the synthetic data community but underused by LLM researchers
- **Fine-tuning potential:** MEDIUM -- useful as evaluation infrastructure; benchmark datasets bundled with SDGym could seed generation tasks

### 1.4 SynthEval Framework
- **URL:** https://arxiv.org/abs/2404.15821
- **Size:** Framework with integrated metrics
- **Format:** Open-source Python
- **License:** Open source
- **Rarity:** HIGH -- a 2024 framework from University of Southern Denmark; very few people know about it
- **Fine-tuning potential:** MEDIUM -- useful for building evaluation pipelines for synthetic data quality

### 1.5 DBbun LLC (HuggingFace Organization)
- **URL:** https://huggingface.co/DBbun
- **Size:** Varies by model/dataset
- **Rarity:** HIGH -- focuses specifically on synthetic data quality validation: detecting implausible records, alignment of distributions
- **Fine-tuning potential:** HIGH -- directly addresses the meta-problem of "synthetic data about synthetic data quality"

### 1.6 LLM-Synthetic-Data Reading List
- **URL:** https://github.com/pengr/LLM-Synthetic-Data
- **Size:** Curated list (updated to July 2025)
- **Rarity:** MEDIUM -- comprehensive index of the field
- **Fine-tuning potential:** META-RESOURCE -- use this to find additional training corpora

### 1.7 Meta Synthetic Data Kit
- **URL:** https://github.com/meta-llama/synthetic-data-kit
- **Format:** Lance format by default
- **License:** Open source
- **Rarity:** LOW -- well-publicized Meta release
- **Fine-tuning potential:** TOOL -- can generate training data using Llama models; useful for pipeline construction

---

## DOMAIN 2: Supply Chain / Logistics

### 2.1 SupplyGraph -- Real-World FMCG Supply Chain GNN Benchmark
- **URL:** https://huggingface.co/datasets/azminetoushikwasi/SupplyGraph | https://github.com/ciol-researchlab/SupplyGraph
- **Size:** 41 product nodes, 684 edges, temporal features across production/sales/delivery/factory-issues
- **Format:** PyTorch Geometric compatible
- **License:** Academic paper (AAAI 2024 workshop)
- **Rarity:** VERY HIGH -- the only real-world supply chain GNN benchmark from an actual FMCG company
- **Fine-tuning potential:** HIGH -- could train models to generate realistic supply chain graph structures with temporal dynamics

### 2.2 Cargo 2000 (C2K) Air Freight Dataset
- **URL:** https://www.kaggle.com/datasets/crawford/cargo-2000-dataset
- **Size:** 3,942 process instances, 7,932 transport legs, 56,082 activities
- **Format:** CSV (multivariate, sequential)
- **License:** CC BY 4.0
- **Rarity:** VERY HIGH -- real IATA air cargo tracking data; one of the only publicly available freight logistics process mining datasets in existence
- **Fine-tuning potential:** VERY HIGH -- could train models to generate realistic air freight process sequences; extremely underserved domain

### 2.3 SAP RecSys Challenge 2022 -- First Real ERP Dataset
- **URL:** Referenced via SAP News Center
- **Size:** Real-world enterprise process data (purchasing, sales, finance, manufacturing)
- **Format:** Anonymized ERP transactions
- **License:** Research use
- **Rarity:** EXTREMELY HIGH -- the first non-simulated ERP dataset ever published; most enterprise data of this kind is entirely proprietary
- **Fine-tuning potential:** VERY HIGH -- could enable generation of realistic ERP/procurement transaction patterns

### 2.4 Automotive Supply Chain Dataset Generator (NebulaGraph)
- **URL:** https://github.com/wey-gu/supplychain-dataset-gen
- **Size:** Synthetic generator (configurable)
- **Format:** Graph data (car models, features, parts, suppliers with relationships)
- **License:** Open source
- **Rarity:** HIGH -- specifically models automotive manufacturing supply chain as a graph
- **Fine-tuning potential:** HIGH -- directly relevant to German Mittelstand automotive supply chains

### 2.5 Northwind Purchase Orders
- **URL:** https://huggingface.co/datasets/AyoubChLin/northwind_PurchaseOrders
- **Size:** Small (PDF + CSV)
- **Format:** PDF + CSV (order_id, date, customer, products with quantity/price)
- **Rarity:** MEDIUM -- synthetic purchase orders, useful as a template
- **Fine-tuning potential:** MEDIUM -- small but demonstrates the document format well

### 2.6 GitHub Shipping & Logistics Dataset Collection
- **URL:** https://github.com/austinlasseter/datasets-shipping-logistics
- **Size:** Curated collection of public datasets
- **Rarity:** MEDIUM -- aggregation resource
- **Fine-tuning potential:** META-RESOURCE -- index of available shipping/logistics datasets

### 2.7 Kaggle Warehouse/Inventory Datasets
- **URLs:** Various on Kaggle (Warehouse Inventory, Logistics Warehouse, Dynamic Inventory Kaizen Analytics)
- **Size:** Small to medium
- **Format:** CSV
- **Rarity:** LOW-MEDIUM -- generic but useful for structural patterns
- **Fine-tuning potential:** MEDIUM -- useful to understand the shape of inventory data for generation

---

## DOMAIN 3: Legal / Compliance / Regulatory

### 3.1 AGB-DE -- German Consumer Contract Clause Assessment (ACL 2024)
- **URL:** https://huggingface.co/datasets/d4br4/agb-de | https://github.com/DaBr01/AGB-DE/
- **Size:** 3,764 clauses from 93 contracts, 8,582 labels
- **Format:** HuggingFace dataset
- **License:** Academic (funded by German Federal Ministry of Justice)
- **Language:** German
- **Rarity:** EXTREMELY HIGH -- expert-annotated German consumer contract clauses with validity/voidness labels by five qualified lawyers; published at ACL 2024; virtually unknown outside German legal NLP circles
- **Fine-tuning potential:** VERY HIGH -- perfect for training models to generate and assess German contract clauses (AGB)

### 3.2 German Employment Contract Review Benchmark (TU Munich, 2025)
- **URL:** https://arxiv.org/abs/2501.17194
- **Size:** Annotated employment contract clauses
- **Format:** Benchmark dataset
- **License:** Academic
- **Language:** German
- **Rarity:** EXTREMELY HIGH -- the only dataset specifically for German Arbeitsvertrag (employment contract) review; 96.4% inter-annotator agreement by two lawyers
- **Fine-tuning potential:** VERY HIGH -- could train models to generate realistic German employment contract clauses and flag legal issues

### 3.3 Open Legal Data -- German Court Decisions
- **URL:** https://huggingface.co/datasets/openlegaldata/court-decisions-germany
- **Size:** ~442K court decisions, 444K citations; segmented version: 251K decisions (1.57 GB)
- **Format:** Parquet (HF) / JSONL (segmented version)
- **License:** Public domain (German UrhG SS 5 -- court decisions have no copyright)
- **Language:** German
- **Rarity:** HIGH -- the largest freely available corpus of German court decisions with structured sections (Tenor, Tatbestand, Entscheidungsgruende)
- **Fine-tuning potential:** VERY HIGH -- train models to generate realistic German legal reasoning, court decision structures, and legal citations

### 3.4 LEXam -- German/English Legal Exam Benchmark (ICLR 2026)
- **URL:** https://huggingface.co/datasets/LEXam-Benchmark/LEXam
- **Size:** 4,886 questions from 340 law exams across 116 courses
- **Format:** HuggingFace dataset
- **License:** CC BY 4.0
- **Language:** German and English
- **Rarity:** VERY HIGH -- brand new (ICLR 2026); includes both open-ended legal reasoning questions and MCQs with reference answers from ETH Zurich / Max Planck Institute
- **Fine-tuning potential:** VERY HIGH -- train models to generate legal reasoning tasks and evaluate legal knowledge

### 3.5 German Legal Entity Recognition (german-ler)
- **URL:** https://huggingface.co/datasets/elenanereiss/german-ler
- **Size:** ~67K sentences, 54K annotated entities, 19 entity classes
- **Format:** HuggingFace dataset
- **License:** CC BY 4.0
- **Language:** German
- **Rarity:** HIGH -- human-annotated NER for German federal court decisions (BAG, BFH, BGH, BPatG, BSG, BVerfG, BVerwG)
- **Fine-tuning potential:** HIGH -- train models to generate text with proper German legal entity references

### 3.6 GerDaLIR -- German Dataset for Legal Information Retrieval
- **URL:** https://github.com/lavis-nlp/GerDaLIR
- **Size:** 123K queries, 131K case documents, 144K relevance labels
- **Format:** TSV (gzipped)
- **License:** Academic
- **Language:** German
- **Rarity:** HIGH -- German legal precedent retrieval benchmark based on Open Legal Data
- **Fine-tuning potential:** HIGH -- train models to understand legal citation patterns

### 3.7 German Legal Sentences (Semantic Similarity)
- **URL:** https://huggingface.co/datasets/lavis-nlp/german_legal_sentences
- **Size:** Automatically generated sentence pairs from judicial decisions
- **License:** Not specified
- **Language:** German
- **Rarity:** HIGH -- weak supervision approach combining citation matching with BM25 similarity
- **Fine-tuning potential:** HIGH -- train models to generate semantically related legal sentence pairs

### 3.8 ftopal/german-law-dataset
- **URL:** https://huggingface.co/datasets/ftopal/german-law-dataset
- **Language:** German
- **Rarity:** HIGH -- likely contains texts of German Gesetze (statutes); poorly documented
- **Fine-tuning potential:** MEDIUM-HIGH -- if it contains German statute text, very useful for generating legal language

### 3.9 Multi_Legal_Pile -- Multilingual Legal Corpus (689 GB)
- **URL:** https://huggingface.co/datasets/joelniklaus/Multi_Legal_Pile
- **Size:** 689 GB, 24 languages, 17 jurisdictions
- **Format:** JSONL.XZ (compressed)
- **License:** CC BY-NC-SA 4.0 (commercial version also available under CC BY-SA 4.0)
- **Language:** 24 languages including German (de_caselaw, de_legislation, de_contracts, de_other)
- **Rarity:** MEDIUM -- well-known in legal NLP but underused for fine-tuning
- **Fine-tuning potential:** VERY HIGH -- the largest multilingual legal corpus; German configs are directly usable

### 3.10 Pile of Law
- **URL:** https://huggingface.co/datasets/pile-of-law/pile-of-law
- **Size:** 256 GB (44 GB compressed), 35 data sources
- **Format:** JSONL.XZ
- **License:** CC BY-NC-SA 4.0
- **Language:** English
- **Rarity:** MEDIUM -- well-cited but underused for domain-specific fine-tuning
- **Fine-tuning potential:** HIGH -- covers court opinions, contracts, regulations, legislative records

### 3.11 CUAD -- Contract Understanding Atticus Dataset (NeurIPS 2021)
- **URL:** https://huggingface.co/datasets/theatticusproject/cuad-qa
- **Size:** 510 contracts, 13,000+ annotations across 41 clause types
- **License:** CC BY 4.0
- **Language:** English
- **Rarity:** LOW-MEDIUM -- well-known in legal NLP
- **Fine-tuning potential:** HIGH -- train models to identify and generate specific types of contract clauses

### 3.12 LEDGAR -- Labeled EDGAR Contract Provisions
- **URL:** Part of https://huggingface.co/datasets/coastalcph/lex_glue
- **Size:** ~80K provisions from 60K+ contracts, 100 label categories
- **License:** Public domain (SEC filings)
- **Language:** English
- **Rarity:** MEDIUM
- **Fine-tuning potential:** HIGH -- massive labeled corpus of contract provision types

### 3.13 UNFAIR-ToS -- Unfair Terms of Service
- **URL:** Part of https://huggingface.co/datasets/coastalcph/lex_glue (config: unfair_tos)
- **Size:** 50 Terms of Service documents, sentence-level annotations with 8 unfair clause types
- **License:** CC BY (within LexGLUE)
- **Language:** English (multilingual extension exists)
- **Rarity:** MEDIUM-HIGH -- specifically about EU consumer law compliance in digital contracts
- **Fine-tuning potential:** HIGH -- train models to generate and detect unfair contractual terms under European consumer law

### 3.14 GDPR Datasets on HuggingFace
- **URLs:**
  - https://huggingface.co/datasets/AndreaSimeri/GDPR -- 99 articles, 173 recitals
  - https://huggingface.co/datasets/PaDaS-Lab/gdpr-compliant-ner -- 44 privacy policies annotated for GDPR compliance
  - https://huggingface.co/datasets/JinuAugustine/gdpr-classification -- GDPR classification
  - https://huggingface.co/datasets/Johny201/gdpr-articles -- multi-label GDPR articles
- **Language:** English
- **Rarity:** HIGH -- GDPR-specific NLP datasets are scarce; the privacy policy NER dataset (PaDaS-Lab) is particularly rare
- **Fine-tuning potential:** HIGH -- could train models to generate GDPR-compliant privacy policies or assess compliance

### 3.15 FiNER-139 -- XBRL-Tagged Financial Reports (Audit/Compliance)
- **URL:** https://huggingface.co/datasets/nlpaueb/finer-139
- **Size:** ~10K annual/quarterly SEC reports, 2016-2020, annotated with XBRL tags by professional auditors
- **License:** Academic
- **Language:** English
- **Rarity:** VERY HIGH -- the only publicly available dataset where professional auditors have tagged financial text with XBRL entities; directly relevant to SOX compliance
- **Fine-tuning potential:** VERY HIGH -- train models to generate properly XBRL-tagged financial text

### 3.16 PleIAs/SEC -- Full SEC 10-K Corpus (1993-2024)
- **URL:** https://huggingface.co/datasets/PleIAs/SEC
- **Size:** 7.2 billion words, 245K filings
- **Format:** Parquet (yearly files)
- **License:** Public domain (SEC filings)
- **Language:** English
- **Rarity:** MEDIUM
- **Fine-tuning potential:** HIGH -- massive corpus of financial regulatory language

### 3.17 LegalBench (NeurIPS 2023)
- **URL:** https://huggingface.co/datasets/nguha/legalbench
- **Size:** 162 tasks from 40 contributors, drawn from 36 distinct corpora
- **License:** Mostly CC BY 4.0
- **Language:** English
- **Rarity:** MEDIUM -- well-known benchmark
- **Fine-tuning potential:** HIGH -- covers evidence, contracts, civil procedure across multiple task types

---

## TOP PICKS: Most Rare and Underserved (Highest Value for Niche Corpus Library)

| Rank | Dataset | Domain | Rarity | Why It Matters |
|------|---------|--------|--------|----------------|
| 1 | **AGB-DE** | Legal/German | Extremely high | Expert-annotated German consumer contract validity; almost unknown |
| 2 | **German Employment Contract Benchmark** | Legal/German | Extremely high | Only German Arbeitsvertrag review dataset; 2025 |
| 3 | **SAP RecSys 2022 ERP Dataset** | Supply Chain | Extremely high | First real non-simulated ERP data ever published |
| 4 | **Cargo 2000** | Logistics | Very high | Only public air freight process mining dataset |
| 5 | **NIST SDNist (2025 SBO)** | Synthetic Meta | Very high | 130-feature stress-test for synthetic generators |
| 6 | **FiNER-139** | Compliance/Audit | Very high | XBRL-tagged by auditors; closest to SOX NLP data |
| 7 | **SupplyGraph** | Supply Chain | Very high | Only real-world supply chain GNN benchmark |
| 8 | **LEXam** | Legal/German | Very high | ICLR 2026; German+English legal exam reasoning |
| 9 | **PaDaS-Lab GDPR NER** | Compliance/GDPR | High | GDPR-annotated privacy policies; very rare |
| 10 | **Open Legal Data (segmented)** | Legal/German | High | 251K structured German court decisions |

---

## Sources
- [PleIAs/SYNTH](https://huggingface.co/datasets/PleIAs/SYNTH)
- [NIST SDNist](https://github.com/usnistgov/SDNist)
- [SDMetrics](https://github.com/sdv-dev/SDMetrics)
- [SDGym](https://github.com/sdv-dev/SDGym)
- [SynthEval](https://arxiv.org/abs/2404.15821)
- [DBbun](https://huggingface.co/DBbun)
- [LLM-Synthetic-Data Reading List](https://github.com/pengr/LLM-Synthetic-Data)
- [Meta Synthetic Data Kit](https://github.com/meta-llama/synthetic-data-kit)
- [SupplyGraph](https://huggingface.co/datasets/azminetoushikwasi/SupplyGraph)
- [Cargo 2000](https://www.kaggle.com/datasets/crawford/cargo-2000-dataset)
- [SAP ERP Dataset](https://holisticrm.com/sap-publishes-first-real-erp-dataset-to-advance-enterprise-ai-research-sap-news-center/)
- [Automotive Supply Chain Generator](https://github.com/wey-gu/supplychain-dataset-gen)
- [Northwind Purchase Orders](https://huggingface.co/datasets/AyoubChLin/northwind_PurchaseOrders)
- [Shipping & Logistics Datasets](https://github.com/austinlasseter/datasets-shipping-logistics)
- [AGB-DE](https://huggingface.co/datasets/d4br4/agb-de)
- [German Employment Contract Review](https://arxiv.org/abs/2501.17194)
- [Open Legal Data](https://huggingface.co/datasets/openlegaldata/court-decisions-germany)
- [LEXam](https://huggingface.co/datasets/LEXam-Benchmark/LEXam)
- [German-LER](https://huggingface.co/datasets/elenanereiss/german-ler)
- [GerDaLIR](https://github.com/lavis-nlp/GerDaLIR)
- [German Legal Sentences](https://huggingface.co/datasets/lavis-nlp/german_legal_sentences)
- [ftopal/german-law-dataset](https://huggingface.co/datasets/ftopal/german-law-dataset)
- [Multi_Legal_Pile](https://huggingface.co/datasets/joelniklaus/Multi_Legal_Pile)
- [Pile of Law](https://huggingface.co/datasets/pile-of-law/pile-of-law)
- [CUAD](https://huggingface.co/datasets/theatticusproject/cuad-qa)
- [LexGLUE (LEDGAR + UNFAIR-ToS)](https://huggingface.co/datasets/coastalcph/lex_glue)
- [GDPR Datasets](https://huggingface.co/datasets?other=gdpr)
- [PaDaS-Lab GDPR NER](https://huggingface.co/datasets/PaDaS-Lab/gdpr-compliant-ner)
- [FiNER-139](https://huggingface.co/datasets/nlpaueb/finer-139)
- [PleIAs/SEC](https://huggingface.co/datasets/PleIAs/SEC)
- [LegalBench](https://huggingface.co/datasets/nguha/legalbench)
- [HFforLegal German Collection](https://huggingface.co/collections/HFforLegal/german-datasets-66e308fb947656e7cff28787)
