# Japanese NLP + Hokkaido Agriculture: Fine-Tuning Research

## Purpose
Research into combining Japanese NLP resources with Hokkaido agricultural data for fine-tuning models (particularly Qwen 72B) to generate high-quality Japanese synthetic data on the Beelink GTR9 Pro.

---

## 1. Qwen 72B for Japanese: Confirmed Working on Beelink

### Real-World Status
**Qwen 72B fine-tuning is confirmed working on the Beelink GTR9 Pro** (owner's direct experience). This supersedes theoretical concerns about ROCm compatibility.

### Japanese Capability
- **Qwen2.5-72B-Instruct** scores **0.7594** on Japanese MT-Bench, trailing only GPT-4o (0.7791)
- Japanese understanding score: **0.6232** on Swallow Leaderboard, outperforming Llama 3.1 Swallow 70B (0.5932)
- Trained on 18 trillion tokens covering 29+ languages including Japanese

### Memory Budget for QLoRA on Beelink

| Component | VRAM |
|---|---|
| Base model weights (4-bit NF4) | ~35-40 GB |
| LoRA adapters (BF16) | ~0.1-0.5 GB |
| Gradients + optimizer states | ~0.5-1.5 GB |
| Activations (gradient checkpointing) | ~2-5 GB |
| **Total** | **~40-46 GB** |

With 96-110GB GPU-accessible memory, this leaves 50-70GB headroom for longer context windows and batch processing.

### Alternative: Qwen3-32B
- Matches Qwen2.5-72B-Base in Japanese benchmarks at half the size
- QLoRA needs only ~18-24GB
- Useful as a faster iteration model for testing before committing to 72B fine-tuning runs
- Framework community has confirmed Qwen3 fine-tuning on Strix Halo

### Quantization for Inference After Fine-Tuning

| Quantization | Size (72B) | Quality | Recommended? |
|---|---|---|---|
| Q4_K_M | ~42GB | Good | Yes -- fast generation |
| Q5_K_M | ~50GB | Very good | Yes -- best balance |
| Q6_K | ~59GB | Near-lossless | Yes -- if quality critical |
| Q8_0 | ~76GB | Excellent | Yes -- fits with room to spare |

---

## 2. Tohoku University NLP Lab (cl-tohoku)

### Overview
- **GitHub:** https://github.com/cl-tohoku (70 repositories)
- **HuggingFace:** https://huggingface.co/tohoku-nlp
- **Open Resources:** https://www.nlp.ecei.tohoku.ac.jp/research/open-resources/

### Major Models

| Model | Training Data | Size | License |
|-------|---------------|------|---------|
| [bert-base-japanese-v3](https://huggingface.co/tohoku-nlp/bert-base-japanese-v3) | CC-100 (74.3GB) + Wikipedia (4.9GB) | 110M | Apache-2.0 |
| [bert-large-japanese-v2](https://huggingface.co/tohoku-nlp/bert-large-japanese-v2) | CC-100 + Wikipedia | 340M | Apache-2.0 |
| Character-level variants | Same | Same | Apache-2.0 |

These are the most widely used Japanese BERT models in the NLP community.

### Key Datasets from Tohoku

| Dataset | Description | Relevance |
|---------|-------------|-----------|
| [quiz-datasets](https://github.com/cl-tohoku/quiz-datasets) | Japanese QA from quiz/trivia for AI-Ou competition | Japanese knowledge evaluation |
| [JAQKET](https://github.com/cl-tohoku/JAQKET_baseline) | Japanese QA with Knowledge of Entity Types | Entity-aware Japanese QA |
| [PheMT](https://github.com/cl-tohoku/PheMT) | Phenomenon-wise JA-EN MT evaluation | Translation quality |
| [keigo_transfer_task](https://github.com/cl-tohoku/keigo_transfer_task) | Honorific language (keigo) conversion | Formal Japanese generation |
| [J-UniMorph](https://github.com/cl-tohoku/J-UniMorph) | Japanese morphology dataset | CC-BY-4.0 |
| Answerability-Annotated RC | 56,651 QA-article triplets with confidence | Reading comprehension |
| Japanese Wikification Corpus | 340 newspaper articles with Wikipedia alignments | Entity linking |
| Japanese Sentiment Polarity Dict | Verb and noun sentiment annotations | Sentiment analysis |

### SHINRA Project (Connected to Tohoku)
- 730K Japanese Wikipedia entities classified into ~200 Extended Named Entity categories
- Structured attribute-value extraction
- Includes agricultural entities (crops, organisms, geographical locations)
- Could supplement agricultural domain knowledge for fine-tuning

---

## 3. Hokkaido Connection

### Hokkaido University Araki Lab
- **URL:** http://arakilab.media.eng.hokudai.ac.jp/Araki_Lab/about_E.html
- **Led by:** Prof. Kenji Araki
- **Focus:** Dialogue systems, commonsense knowledge, spoken language processing
- **Notable:** AI Pirika -- Ainu language preservation dialogue system
- Natural partner for agricultural dialogue/advisory system work

### Tohoku-Hokkaido Infrastructure
Both universities share **JHPCN** (Joint Usage/Research Center for Interdisciplinary Large-scale Information Infrastructures) supercomputing resources. This provides a potential pathway for collaborative LLM training.

### Geographic Synergy
Tohoku (Sendai) and Hokkaido are adjacent regions sharing:
- Cold-climate agriculture (rice, dairy, root vegetables)
- Similar digitalization challenges (rural, aging population)
- Complementary strengths: Tohoku has NLP expertise, Hokkaido has agricultural research

---

## 4. Japanese NLP Ecosystem: Major Players

### Tier 1: Model Producers

| Organization | Key Resources | Notes |
|---|---|---|
| **LLM-jp (NII)** | llm-jp-3 series (1.8B-172B), fully open | https://llm-jp.nii.ac.jp/en/ |
| **Swallow (Tokyo Tech)** | Llama-3.3-Swallow-70B, Swallow Corpus V2 (3.2T chars) | Best Japanese-adapted 70B |
| **Rinna** | Sarashina2.2, Llama 3 Youko 8B | |
| **CyberAgent** | OpenCALM (160M-6.8B), CALM3-22B-Chat | Apache-2.0 |
| **Preferred Networks** | PLaMo 2.2 Prime 31B, PLaMo Lite 1B | |
| **Stockmark** | Stockmark-2-100B | MIT license |

### Tier 2: Academic Labs

| Lab | GitHub | Focus |
|---|---|---|
| **NAIST NLP** | https://github.com/naist-nlp | MT, lexical complexity, entity linking |
| **RIKEN AIP** | https://github.com/riken-grp | Dialogue, reference resolution, toxicity |
| **Kyoto Univ. LMP** | https://nlp.ist.i.kyoto-u.ac.jp/EN/ | JSNLI, syntactic/semantic analysis |
| **U. Tokyo (Miyao Lab)** | https://mynlp.is.s.u-tokyo.ac.jp/en/ | Computational linguistics |

### Meta-Resources (Essential Bookmarks)
- [awesome-japanese-nlp-resources](https://github.com/taishi-i/awesome-japanese-nlp-resources) -- **1,274 models + 477 datasets**
- [awesome-japanese-llm](https://github.com/llm-jp/awesome-japanese-llm) -- comprehensive overview of 30+ Japanese LLM variants

### Key Benchmarks
- **JGLUE** (https://github.com/yahoojapan/JGLUE) -- Japanese GLUE: sentiment, NLI, QA, commonsense
- **Swallow Leaderboard** (https://swallow-llm.github.io/leaderboard/) -- comparative Japanese LLM evaluation
- **JMTEB** (https://github.com/sbintuitions/JMTEB) -- 28 Japanese text embedding benchmark datasets

---

## 5. The Gap: No Japanese Agricultural NLP Corpus Exists

**This is the single most important finding.** Despite Japan's massive agricultural sector and advanced NLP ecosystem, no dedicated publicly available Japanese agricultural NLP text corpus exists.

### What This Means for You
Whoever builds the first Japanese agricultural NLP corpus + fine-tuned model owns the niche. Your Beelink can generate synthetic Japanese agricultural text at 72B quality 24/7.

### Sources to Build the Corpus From

| Source | Type | Access | Content |
|---|---|---|---|
| **NARO (農研機構)** | Research reports, technical bulletins | https://www.naro.go.jp/ | Agricultural research publications |
| **MAFF (農林水産省) white papers** | Annual agricultural policy documents | https://www.maff.go.jp/ | Government open data |
| **J-STAGE agricultural journals** | Peer-reviewed Japanese papers | https://www.jstage.jst.go.jp/ | Open access agricultural science |
| **JA (農協) publications** | Cooperative newsletters, farming guides | Regional JA websites | Practical farming advice |
| **Hokkaido Prefecture agricultural reports** | Regional crop data, advisories | Hokkaido government sites | Hokkaido-specific |
| **Wikipedia agricultural articles** | Already in Tohoku BERT training | Via SHINRA | Plant, crop, farming entries |
| **MAFF e-Stat** | Statistical tables | https://www.e-stat.go.jp/en | All prefectural agriculture data |

### Methodology Precedent: AgriGPT
- **Paper:** https://arxiv.org/html/2508.08632v1
- Used continual pretraining + SFT on Agri-342K dataset
- Significantly outperformed general-purpose LLMs on agricultural tasks
- Demonstrated that domain-specific agricultural fine-tuning works

### Methodology Precedent: Agricultural Advisory Fine-Tuning
- **Paper:** https://arxiv.org/html/2603.03294
- Hybrid architecture using LoRA fine-tuning on expert-curated "Golden Facts"
- Improved fact recall from 26.2% to 50.3%
- Applicable methodology for Japanese agricultural advisory generation

---

## 6. Phytosanitary Data Angle

### What Exists Publicly
- **PhytoPipe** (USDA/APHIS) -- phytosanitary pipeline that generated synthetic sequencing datasets from 12 crop genomes including rice, potato, wheat, soybean (all Hokkaido crops). Code: https://github.com/healthyPlant/PhytoPipe
- **APHIS Phytosanitary Regulation Dataset** -- https://catalog.data.gov/dataset/phytosanitary-regulation -- country-level import/export eligibility
- **Plant disease image datasets** -- PlantDoc, PlantVillage, Paddy Doctor (16K images, 13 classes)

### Japan-Specific Opportunity
Japan has extremely strict phytosanitary import/export rules (Plant Protection Act, 植物防疫法). Synthetic inspection record data could be valuable for:
- AgTech companies building compliance tools
- JA cooperatives modernizing inspection workflows
- Export documentation automation (fruits/vegetables to Asia-Pacific markets)
- Training AI models for visual plant health inspection

### Connection to Previous Research
The phytosanitary work from the vilseckki-data/factory-app repo (not publicly accessible) could potentially inform schema design for synthetic phytosanitary inspection datasets targeting the Japanese market.

---

## 7. Recommended Fine-Tuning Pipeline for Japanese Agricultural Synthetic Data

### Phase 1: Corpus Assembly (Low Effort, High Value)
1. Scrape NARO publications and MAFF white papers (open government data)
2. Collect J-STAGE agricultural journal articles (open access)
3. Download Hokkaido Prefecture agricultural reports
4. Pull MAFF e-Stat data via API for statistical grounding
5. Extract agricultural entities from SHINRA project

### Phase 2: Fine-Tune Qwen 72B (On Beelink)
1. **Base:** Qwen2.5-72B (already confirmed working on Beelink)
2. **Method:** QLoRA 4-bit (~40-46GB, fits in 96-110GB GPU memory)
3. **Training data:** Japanese agricultural corpus from Phase 1, formatted as instruction pairs
4. **Validation:** Test against JGLUE to ensure general Japanese capability retained
5. **Iterate:** Use Qwen3-32B for fast iteration, 72B for final quality

### Phase 3: Generate Synthetic Data (Overnight Runs)
1. Hokkaido crop management advisory text
2. Synthetic JA cooperative inspection records
3. Agricultural sensor data descriptions (paired with MmCows/TERRA-REF structured data)
4. Phytosanitary compliance documentation
5. Smart farming equipment maintenance logs

### Phase 4: Sell
1. List on Datarade targeting Japanese AgTech companies
2. Approach Hokkaido JA cooperatives directly
3. Partner with Hokkaido University (academic credibility)
4. No competition — nobody else has a Japanese agricultural NLP model

---

## 8. Swallow Corpus: The Secret Weapon

The **Swallow Corpus V2** deserves special mention:
- **Size:** 3.2 trillion characters from Common Crawl
- **Source:** https://github.com/swallow-llm/swallow-corpus
- **Paper:** https://arxiv.org/html/2404.17733v1
- **What it is:** The largest curated Japanese web text corpus, used to train the Swallow series of Japanese LLMs
- **Why it matters:** It likely contains Japanese agricultural web content that could be filtered and extracted as a starting corpus, saving months of manual scraping

---

## Sources
- [Qwen2.5 Technical Report](https://arxiv.org/abs/2412.15115)
- [Qwen3 Blog Post](https://qwenlm.github.io/blog/qwen3/)
- [Shisa.AI - Qwen3 Japanese Performance](https://shisa.ai/posts/qwen3-japanese-performance/)
- [Swallow LLM Leaderboard](https://swallow-llm.github.io/leaderboard/about.en.html)
- [Llama 3.3 Swallow 70B](https://swallow-llm.github.io/llama3.3-swallow.en.html)
- [Swallow Corpus V2](https://github.com/swallow-llm/swallow-corpus)
- [Framework Community: Finetuning on Strix Halo](https://community.frame.work/t/finetuning-llms-on-strix-halo-full-lora-and-qlora-on-gemma-3-qwen-3-and-gpt-oss-20b/76986)
- [Tohoku NLP Group GitHub](https://github.com/cl-tohoku)
- [tohoku-nlp on HuggingFace](https://huggingface.co/tohoku-nlp/bert-base-japanese-v3)
- [Tohoku NLP Open Resources](https://www.nlp.ecei.tohoku.ac.jp/research/open-resources/)
- [SHINRA Project](http://shinra-project.info/shinra2020ml/?lang=en)
- [Hokkaido Univ. Araki Lab](http://arakilab.media.eng.hokudai.ac.jp/Araki_Lab/about_E.html)
- [LLM-jp at NII](https://llm-jp.nii.ac.jp/en/home-en/)
- [awesome-japanese-nlp-resources](https://github.com/taishi-i/awesome-japanese-nlp-resources)
- [awesome-japanese-llm](https://github.com/llm-jp/awesome-japanese-llm)
- [JGLUE](https://github.com/yahoojapan/JGLUE)
- [AgriGPT](https://arxiv.org/html/2508.08632v1)
- [Agricultural Advisory Fine-Tuning](https://arxiv.org/html/2603.03294)
- [NARO](https://www.naro.go.jp/)
- [MAFF](https://www.maff.go.jp/)
- [PhytoPipe](https://github.com/healthyPlant/PhytoPipe)
- [APHIS Phytosanitary Regulation](https://catalog.data.gov/dataset/phytosanitary-regulation)
- [QLoRA Memory Analysis](https://devtechtools.org/en/blog/qlora-internals-fine-tuning-70b-models-on-single-gpu)
- [Strix Halo LLM Tracker](https://llm-tracker.info/AMD-Strix-Halo-(Ryzen-AI-Max+-395)-GPU-Performance)
