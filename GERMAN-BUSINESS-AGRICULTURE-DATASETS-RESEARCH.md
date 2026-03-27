# Dataset Corpus Research: German Business/Financial + Agriculture/Smart Farming

## Purpose
Training corpuses for fine-tuning models on a 128GB RAM machine to generate synthetic data in German business/Mittelstand and agriculture/smart farming domains. Focus on UNCOMMON and UNDERSERVED datasets.

---

## DOMAIN 1: German Business / Mittelstand / Financial

### 1. FinCorpus-DE-10k (UNCOMMON -- HIGH VALUE)
- **URL:** https://huggingface.co/datasets/anhaltai/fincorpus-de-10k
- **Size:** 12,235 PDFs, ~10,500 with plaintext; 165M+ tokens
- **Format:** PDF + extracted plaintext
- **License:** CC BY-NC 4.0 (monthly/annual reports: CC BY-NC-ND 4.0)
- **Language:** German (71%), bilingual DE/EN (29%)
- **Rarity:** HIGH -- one of very few large German financial text corpora
- **Content:** Security prospectuses, base prospectuses, final terms, 838 Bundesbank monthly reports (1949-2022), annual reports
- **Synthetic data potential:** Excellent. Could fine-tune models to generate realistic German financial prospectus language, Bundesbank-style reporting, and securities terminology.

### 2. German-MultiFin (UNCOMMON)
- **URL:** https://huggingface.co/datasets/anhaltai/german-multifin
- **Size:** 10,048 financial article headlines
- **Format:** HuggingFace dataset (text classification)
- **License:** Not specified (derived from MultiFin + GPT-3.5 translations)
- **Language:** German
- **Rarity:** MEDIUM -- German translation of multilingual financial dataset
- **Synthetic data potential:** Good for financial headline classification and generating financial news-style German text.

### 3. German Financial Statements BERT (Model -- implies training data)
- **URL:** https://huggingface.co/fabianrausch/german-financial-statements-bert
- **Size:** Trained on 100K sentences from 5,500 financial statement documents
- **Format:** Model (BERT fine-tune)
- **License:** Not specified
- **Language:** German
- **Rarity:** HIGH -- German Jahresabschluss (annual financial statements) domain
- **Synthetic data potential:** The model itself can inform what vocabulary/style is needed; the underlying training data (if obtainable) would be very valuable for Mittelstand document generation.

### 4. Aoschu/German_invoices_dataset (UNCOMMON)
- **URL:** https://huggingface.co/datasets/Aoschu/German_invoices_dataset
- **Size:** Small (exact size not listed)
- **Format:** Image + annotations (for Donut/OCR models)
- **License:** Not specified
- **Language:** German
- **Rarity:** HIGH -- very few German invoice image datasets exist
- **Synthetic data potential:** Good for training document understanding models; could be used to generate synthetic German invoice layouts and content.

### 5. CourtPressGER (2025 -- VERY NEW)
- **URL:** https://arxiv.org/pdf/2512.09434
- **Size:** 6,432 court decision / press release pairs (1995-2023)
- **Format:** Aligned text pairs
- **License:** Likely open (from federal courts)
- **Language:** German
- **Rarity:** HIGH -- brand new dataset, court-to-plain-language summarization
- **Synthetic data potential:** Excellent for training models to translate dense German legal text into plain German -- directly useful for Mittelstand compliance summaries.

### 6. Open Legal Data -- Segmented (Jan 2026 -- BRAND NEW)
- **URL:** https://arxiv.org/abs/2601.01449
- **Size:** 251,038 German court decisions (cleaned, sectioned)
- **Format:** JSONL
- **License:** Open
- **Language:** German
- **Rarity:** HIGH -- latest cleaned version of the corpus
- **Synthetic data potential:** Very strong. Structured sections (Tenor, Tatbestand, Entscheidungsgruende) enable fine-tuning for generating structured German legal documents.

### 7. OffeneRegister.de -- German Company Registry (UNCOMMON)
- **URL:** https://offeneregister.de/daten/ | https://www.opensanctions.org/datasets/de_offeneregister/
- **Size:** 5M+ companies and their officers
- **Format:** JSON / CSV
- **License:** Open (OpenCorporates open license)
- **Language:** German
- **Rarity:** MEDIUM -- known in open data circles, but uncommon in ML
- **Synthetic data potential:** Good for generating realistic German company names, Handelsregister entries, officer records, and corporate structures typical of Mittelstand firms.

### 8. IHK Berlin Gewerbedaten (UNCOMMON)
- **URL:** https://github.com/IHKBerlin/IHKBerlin_Gewerbedaten
- **Size:** Not large, but structured
- **Format:** Open data (CSV-like)
- **License:** Open Data
- **Language:** German
- **Rarity:** HIGH -- real IHK business classification data, almost unknown
- **Synthetic data potential:** Useful for generating realistic German business registration metadata, IHK branch classifications, and Kleingewerbe vs. Handelsregister distinctions.

### 9. MultiEURLEX
- **URL:** https://huggingface.co/datasets/nlpaueb/multi_eurlex
- **Size:** 65K EU laws in 23 languages (including German)
- **Format:** HuggingFace dataset
- **License:** CC BY 4.0 (EUR-Lex reuse policy)
- **Language:** 23 EU languages including German
- **Rarity:** LOW-MEDIUM (well known in research)
- **Synthetic data potential:** Good for generating EU regulatory text in German; useful for compliance document generation for Mittelstand firms dealing with EU regulations.

### 10. DFKI SmartData Corpus (UNCOMMON)
- **URL:** https://github.com/DFKI-NLP/smartdata-corpus
- **Size:** ~2,600 German documents
- **Format:** Annotated NER + relation extraction
- **License:** Open
- **Language:** German
- **Rarity:** HIGH -- DFKI industrial/traffic domain, NER annotations
- **Synthetic data potential:** Moderate. 15 industry-related relation types could help generate structured German industrial/business text.

### 11. Bundesbank Time Series + Destatis Open Data (Structured)
- **Bundesbank:** https://www.bundesbank.de/en/statistics/time-series-databases -- CSV/SDMX-ML, free download, macroeconomic time series
- **Destatis:** https://www.destatis.de/EN/Service/OpenData/_node.html -- Data Licence Germany 2.0 (open), GENESIS-Online API
- **Rarity:** LOW (well-known) but underused in ML contexts
- **Synthetic data potential:** Tabular/numeric data good for generating realistic German economic statistics, but not directly NLP fine-tuning material.

---

## DOMAIN 2: Agriculture / Smart Farming

### 12. MmCows -- Multimodal Dairy Cattle Monitoring (UNCOMMON -- HIGH VALUE)
- **URL:** https://github.com/neis-lab/mmcows
- **Size:** 2 weeks of multimodal data, 20K annotated frames, 213K bounding boxes
- **Format:** Sensor CSVs (UWB, IMU, temperature, pressure, ankle) + camera images
- **License:** Open (NeurIPS 2024 Datasets track)
- **Rarity:** VERY HIGH -- only comprehensive multimodal dairy cattle sensor dataset
- **Synthetic data potential:** Excellent. Wearable sensor time series (acceleration, temperature, pressure) + milk yield data could fine-tune models to generate realistic dairy cattle monitoring data. Directly relevant to Hokkaido dairy farming.

### 13. TERRA-REF (UNCOMMON -- MASSIVE)
- **URL:** https://terraref.org/ | https://data.nal.usda.gov/dataset/data-terra-ref-open-reference-data-set-high-resolution-genomics-phenomics-and-imaging-sensors
- **Size:** ~1 PB (petabyte) of sensor data
- **Format:** Hyperspectral imagery, thermal, 3D point clouds, genomics, phenomics
- **License:** Public domain (ARPA-E funded)
- **Rarity:** VERY HIGH -- world's largest agricultural sensor dataset from the world's largest agricultural robot
- **Synthetic data potential:** Excellent for generating realistic agricultural sensor readings (environmental, spectral, phenotypic). Sorghum + wheat focus, but sensor patterns transferable.

### 14. CropNet -- Multi-Modal Crop Yield Prediction (UNCOMMON)
- **URL:** https://huggingface.co/datasets/CropNet/CropNet
- **Size:** Terabyte-scale (2,200 U.S. counties, 6 years, 3 modalities)
- **Format:** Satellite images (224x224 RGB), weather grids (9 parameters), USDA yield tables
- **License:** Open
- **Rarity:** HIGH -- first TB-scale multi-modal crop yield dataset
- **Synthetic data potential:** Strong for generating synthetic weather-crop-yield relationships. Weather/yield patterns transferable to other regions including Japan.

### 15. Paddy Rice Imagery Dataset -- Hokkaido University (UNCOMMON -- HIGH VALUE)
- **URL:** https://datasetninja.com/paddy-rice-panicle-detection | https://www.mdpi.com/2073-4395/11/8/1542
- **Size:** 400 images (train/test/val split)
- **Format:** Images with segmentation annotations
- **License:** CC BY 4.0
- **Language:** English (annotations), Japanese origin
- **Rarity:** VERY HIGH -- specifically from Hokkaido University experimental paddy fields
- **Synthetic data potential:** Moderate (small size). But the Hokkaido provenance makes it directly relevant. Could be used as seed data for generating synthetic rice panicle imagery.

### 16. Japan 140-Year Prefectural Crop Production Dataset (BRAND NEW -- UNCOMMON)
- **URL:** https://www.nature.com/articles/s41597-025-06394-7 (Scientific Data, Dec 2025)
- **Size:** 140 years (1883-2022), 6 crops, 47 prefectures
- **Format:** Tabular (production, area, yield)
- **License:** Open (Scientific Data)
- **Language:** English/Japanese
- **Rarity:** VERY HIGH -- brand new, covers all of Hokkaido's agricultural history
- **Synthetic data potential:** Excellent for generating realistic long-term Japanese crop yield trends. Hokkaido-specific data (rice, wheat, potato, soybean) directly usable.

### 17. MAFF e-Stat Agriculture Data (UNCOMMON in ML contexts)
- **URL:** https://www.e-stat.go.jp/en | https://www.maff.go.jp/e/data/stat/
- **Size:** Comprehensive (all prefectures, all years, all crop/livestock categories)
- **Format:** Excel, CSV, API (JSON)
- **License:** Open government data
- **Language:** Japanese (some English)
- **Rarity:** HIGH in ML context -- underused outside Japanese government circles
- **Synthetic data potential:** Good for generating realistic Japanese agricultural statistics, especially Hokkaido dairy cattle counts, rice production volumes, and seasonal patterns.

### 18. Paddy Doctor -- Paddy Disease Classification
- **URL:** https://www.kaggle.com/competitions/paddy-disease-classification | https://ieee-dataport.org/documents/paddy-doctor-visual-image-dataset-automated-paddy-disease-classification-and-benchmarking
- **Size:** 16,225 images, 13 classes (12 diseases + healthy)
- **Format:** Images (1080x1440px)
- **License:** Research use
- **Rarity:** MEDIUM (well-known Kaggle competition)
- **Synthetic data potential:** Good for generating synthetic paddy disease imagery. Indian origin but diseases are universal to rice cultivation including Japan.

### 19. PlantSeg -- In-the-Wild Plant Disease Segmentation (UNCOMMON)
- **URL:** https://arxiv.org/html/2409.04038v1
- **Size:** 11,458 images, 115 disease categories, 34 plant hosts
- **Format:** Images with segmentation masks
- **License:** Research
- **Rarity:** HIGH -- much more diverse than PlantVillage, field conditions
- **Synthetic data potential:** Strong. Real-world field conditions make it better than PlantVillage for training realistic disease detection models applicable to actual farming.

### 20. GloRice / GCD-Rice -- Global Rice Distribution Maps
- **URL:** https://www.nature.com/articles/s41597-025-04483-1 (GloRice) | https://www.nature.com/articles/s41597-025-05374-1 (GCD-Rice)
- **Size:** Global, 5-arcminute / 30m resolution, 1961-2021 / 1990-2023
- **Format:** Gridded geospatial (raster)
- **License:** Open (Scientific Data)
- **Rarity:** MEDIUM-HIGH
- **Synthetic data potential:** Good for generating realistic rice cultivation extent maps and temporal patterns across Asia including Japan.

### 21. KaraAgroAI Drone-based Crop Yield Estimation (UNCOMMON)
- **URL:** https://huggingface.co/datasets/KaraAgroAI/Drone-based-Agricultural-Dataset-for-Crop-Yield-Estimation
- **Size:** 8,784 images (16000x13000px each)
- **Format:** High-res drone images + annotations
- **License:** Not specified
- **Rarity:** HIGH -- drone imagery from Ghana, uncommon origin
- **Synthetic data potential:** Moderate. Drone imagery patterns transferable but crop types differ from Japanese/German agriculture.

### 22. awesome-agriculture (Meta-Resource)
- **URL:** https://github.com/brycejohnston/awesome-agriculture
- **Content:** Curated list of open-source agriculture technology including datasets, APIs, sensor frameworks (FIWARE AgriFood, Farm-Data-Relay-System)
- **Rarity:** MEDIUM -- good starting point for finding more niche resources
- **Synthetic data potential:** Index resource; links to many tools and data sources.

---

## Summary: Top Picks by Rarity and Synthetic Data Potential

### German Business/Financial (Top 5)

| Rank | Dataset | Rarity | Why It Matters |
|------|---------|--------|----------------|
| 1 | **FinCorpus-DE-10k** | HIGH | 165M tokens of German financial text, Bundesbank reports |
| 2 | **CourtPressGER** | HIGH | Court-to-plain-language pairs, brand new |
| 3 | **Open Legal Data Segmented (251K)** | HIGH | Structured German court decisions |
| 4 | **OffeneRegister.de** | MEDIUM | 5M+ real German company records |
| 5 | **IHK Berlin Gewerbedaten** | HIGH | Real IHK business classifications (almost unknown) |

### Agriculture/Smart Farming (Top 5)

| Rank | Dataset | Rarity | Why It Matters |
|------|---------|--------|----------------|
| 1 | **MmCows** | VERY HIGH | Multimodal dairy cattle sensor data (NeurIPS 2024) |
| 2 | **Japan 140-Year Crop Dataset** | VERY HIGH | Hokkaido prefectural data, brand new |
| 3 | **Hokkaido Paddy Rice Imagery** | VERY HIGH | From Hokkaido University, CC BY 4.0 |
| 4 | **TERRA-REF** | VERY HIGH | 1PB agricultural sensor data, public domain |
| 5 | **MAFF e-Stat API** | HIGH | All Japanese agriculture/livestock data programmatically accessible |

---

## Sources
- [FinCorpus-DE-10k](https://huggingface.co/datasets/anhaltai/fincorpus-de-10k)
- [German-MultiFin](https://huggingface.co/datasets/anhaltai/german-multifin)
- [German Financial Statements BERT](https://huggingface.co/fabianrausch/german-financial-statements-bert)
- [German Invoices Dataset](https://huggingface.co/datasets/Aoschu/German_invoices_dataset)
- [CourtPressGER](https://arxiv.org/pdf/2512.09434)
- [Open Legal Data Segmented](https://arxiv.org/abs/2601.01449)
- [OffeneRegister.de](https://offeneregister.de/daten/)
- [IHK Berlin Gewerbedaten](https://github.com/IHKBerlin/IHKBerlin_Gewerbedaten)
- [MultiEURLEX](https://huggingface.co/datasets/nlpaueb/multi_eurlex)
- [DFKI SmartData Corpus](https://github.com/DFKI-NLP/smartdata-corpus)
- [Bundesbank Time Series](https://www.bundesbank.de/en/statistics/time-series-databases)
- [Destatis Open Data](https://www.destatis.de/EN/Service/OpenData/_node.html)
- [MmCows](https://github.com/neis-lab/mmcows)
- [TERRA-REF](https://terraref.org/)
- [CropNet](https://huggingface.co/datasets/CropNet/CropNet)
- [Hokkaido Paddy Rice](https://www.mdpi.com/2073-4395/11/8/1542)
- [Japan 140-Year Crop Dataset](https://www.nature.com/articles/s41597-025-06394-7)
- [MAFF e-Stat](https://www.e-stat.go.jp/en)
- [Paddy Doctor](https://www.kaggle.com/competitions/paddy-disease-classification)
- [PlantSeg](https://arxiv.org/html/2409.04038v1)
- [GloRice](https://www.nature.com/articles/s41597-025-04483-1)
- [KaraAgroAI Drone Dataset](https://huggingface.co/datasets/KaraAgroAI/Drone-based-Agricultural-Dataset-for-Crop-Yield-Estimation)
- [awesome-agriculture](https://github.com/brycejohnston/awesome-agriculture)
