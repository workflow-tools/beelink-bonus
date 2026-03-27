# Healthcare Dataset Corpus Research: Clinical, Medical NLP, and Synthetic Patient Data

## Purpose
Training corpuses for fine-tuning models on a 128GB RAM machine to generate privacy-safe synthetic healthcare data. Special focus on German-language medical datasets and underserved multilingual resources.

---

## 1. HuggingFace Datasets

### Synthetic Patient Records & Clinical Notes

| Dataset | Size | Format | License | Language | Fine-Tuning Use |
|---|---|---|---|---|---|
| [richardyoung/synthea-575k-patients](https://huggingface.co/datasets/richardyoung/synthea-575k-patients) | 575,415 patients | Tabular (FHIR-based structured EHR) | Apache 2.0 | EN | Train models on realistic EHR structure, demographics, medications, conditions |
| [starmpcc/Asclepius-Synthetic-Clinical-Notes](https://huggingface.co/datasets/starmpcc/Asclepius-Synthetic-Clinical-Notes) | Derived from MIMIC-III discharge summaries | Text (instruction-answer pairs) | PhysioNet credentialed | EN | Fine-tune for clinical note generation conditioned on structured data |
| [AGBonnet/augmented-clinical-notes](https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes) | 167K patient summaries + synthetic conversations | Text (clinical notes + dialogues) | Check HF page | EN | Train doctor-patient dialogue generation and clinical note writing |
| [ritaranx/clinical-synthetic-text-llm](https://huggingface.co/datasets/ritaranx/clinical-synthetic-text-llm) | Varies | Text | Check HF page | EN | LLM-generated clinical text for augmentation |
| [Technoculture/synthetic-clinical-notes-embedded](https://huggingface.co/datasets/Technoculture/synthetic-clinical-notes-embedded) | Varies | Text + embeddings | Check HF page | EN | Embedded clinical notes for retrieval-augmented generation |
| [GeorgiaTech/cnotesum](https://huggingface.co/datasets/GeorgiaTech/cnotesum) | Synthea-based | Text (notes + summaries) | Check HF page | EN | Clinical note summarization via LLaMA 2 |
| [ekacare/clinical_note_generation_dataset](https://huggingface.co/datasets/ekacare/clinical_note_generation_dataset) | Varies | Text | Check HF page | EN | Direct clinical note generation training |

### Medical QA & NLP

| Dataset | Size | Format | License | Language | Fine-Tuning Use |
|---|---|---|---|---|---|
| [Malikeh1375/medical-question-answering-datasets](https://huggingface.co/datasets/Malikeh1375/medical-question-answering-datasets) | Multiple merged QA sets | Text (Q&A pairs) | Check HF page | EN | Medical reasoning and QA generation |
| [openlifescienceai/medmcqa](https://huggingface.co/datasets/openlifescienceai/medmcqa) | Large MCQ dataset | Structured (multiple choice) | Check HF page | EN | Medical knowledge grounding including pathology |
| [BI55/MedText](https://huggingface.co/datasets/BI55/MedText) | ~0.8B tokens | Text | Check HF page | EN | General medical text generation pre-training |

### Drug Interaction & Pharmacology

| Dataset | Size | Format | License | Language | Fine-Tuning Use |
|---|---|---|---|---|---|
| [allenai/drug-combo-extraction](https://huggingface.co/datasets/allenai/drug-combo-extraction) | Varies | Text (entity extraction) | AI2 license | EN | Drug combination extraction from literature |
| [DrugBank DDI via TDC](https://tdcommons.ai/multi_pred_tasks/ddi/) | 191,808 DDI pairs, 1,706 drugs | Structured (SMILES + interaction types) | Academic | EN | Drug interaction prediction and description generation |
| [TWOSIDES DDI](https://tdcommons.ai/multi_pred_tasks/ddi/) | 4,649,441 DDI pairs, 645 drugs | Structured | Academic | EN | Large-scale polypharmacy side-effect modeling |
| [EvE Bio Pharmome Map](https://huggingface.co/blog/hugging-science/eve-bio-mapping-the-pharmone-drug-interaction) | Comprehensive drug-target map | Structured | Open | EN | Drug-target interaction and adverse event modeling |

### Radiology Reports

| Dataset | Size | Format | License | Language | Fine-Tuning Use |
|---|---|---|---|---|---|
| [farrell236/DRR-RATE](https://huggingface.co/datasets/farrell236/DRR-RATE) | 25,692 CT volumes, 21,304 patients | Multimodal (images + text reports + labels for 18 pathologies) | Check HF page | EN | Radiology report generation training |
| ReXGradient-160K | 160K chest radiographs | Multimodal (images + free-text reports) | Check HF page | EN | Chest X-ray report generation |

### Pathology & Histopathology

| Dataset | Size | Format | License | Language | Fine-Tuning Use |
|---|---|---|---|---|---|
| [serag-ai/Synthetic-Histopathology-Images](https://huggingface.co/datasets/serag-ai/Synthetic-Histopathology-Images) | Diffusion-generated | Images (breast cancer IDC classification) | Check HF page | EN | Synthetic pathology image generation |

### Curated Collections (Aggregators)

- [hf4h: Synthetic Medical Data and Models](https://huggingface.co/collections/hf4h/synthetic-medical-data-and-models-64f9bf3446f3f06f5abdb770) -- curated collection of synthetic medical datasets and models
- [openlifescienceai: Life Science, Health and Medical Datasets](https://huggingface.co/collections/openlifescienceai/life-science-health-and-medical-datasets-for-ml) -- broad medical dataset collection
- [Mdubbya: Datasets - Medical](https://huggingface.co/collections/Mdubbya/datasets-medical) -- updated March 2025
- [HuggingFace open-r1 Issue #31: Datasets for Medicine](https://github.com/huggingface/open-r1/issues/31) -- ongoing curation effort for verifiable medical pairs

---

## 2. German-Language Medical Datasets (HIGH PRIORITY)

| Dataset | Size | Format | License | Access | Fine-Tuning Use |
|---|---|---|---|---|---|
| [GGPONC 2.0](https://huggingface.co/datasets/bigbio/ggponc2) | 200,000+ entity annotations, largest freely distributable German medical corpus | Text (annotated oncology guidelines) | Free via Zenodo request | No patient data, no credentialing | Fine-tune German medical NER and entity-aware text generation |
| [CARDIO:DE](https://www.nature.com/articles/s41597-023-02128-9) | 500 doctor's letters, 993,143 tokens | Text (discharge letters, cardiovascular) | CC-BY (check paper) | Open | Fine-tune German clinical letter generation; largest publicly available German clinical document dataset |
| [GeMTeX](https://fit.uni-tuebingen.de/Project/Details?id=10290) | Multi-site corpus from 6 university hospitals | Text (annotated clinical texts, SNOMED CT, ICD-10) | Research agreement | Under development | Future gold standard for German clinical NLP |
| [stefan-m-lenz/UroLlmEvalSet](https://huggingface.co/datasets/stefan-m-lenz/UroLlmEvalSet) | Urological doctor's notes | Text (tumor diagnosis, ICD-10 codes) | Check HF page | Open | Benchmark for German medical LLM evaluation |
| [GERNERMED++](https://www.sciencedirect.com/science/article/pii/S1532046423002344) | Transfer-learned NER dataset | Text (annotated entities) | Open (GitHub) | No internal data needed | German medical NER without needing hospital data |
| Section-Annotated German Discharge Summaries | ~1,000 discharge summaries | Text (CDA-section annotated) | Academic | Request-based | Learn German discharge summary structure |
| [michael-eble/nlp-dataset-health-german-language](https://github.com/michael-eble/nlp-dataset-health-german-language) | 1,000+ records | Text (social-media-like health text) | CC-BY-4.0 | Open | German health text classification training |

**German Medical Models** (useful for transfer learning):
- [GerMedBERT/medbert-512](https://huggingface.co/GerMedBERT/medbert-512) -- BERT trained on German medical text, custom medical tokenizer
- [HUMADEX/german_medical_ner](https://huggingface.co/HUMADEX/german_medical_ner) -- NER for symptoms, tests, treatments in German

**Key insight**: A [comprehensive 2025 survey of German clinical corpora](https://pmc.ncbi.nlm.nih.gov/articles/PMC12077144/) documents real, translated, and synthetic substitutes available. German clinical NLP is severely constrained by GDPR (which lacks HIPAA's explicit identifier list), making synthetic generation especially valuable.

---

## 3. GitHub Repos -- Medical Data Generators & Corpus Tools

| Repository | Purpose | License |
|---|---|---|
| [synthetichealth/synthea](https://github.com/synthetichealth/synthea) | Full synthetic patient population simulator; 90+ disease modules; exports FHIR, C-CDA, CSV | Apache 2.0 |
| [FHOOEAIST/synthea-AT-implementation](https://github.com/FHOOEAIST/synthea-AT-implementation) | **Austrian** Synthea adaptation -- useful for German-language/European healthcare context | Check repo |
| [MIT-LCP/mimic-code](https://github.com/MIT-LCP/mimic-code) | Community code for working with MIMIC databases | Open |
| [geniusrise/awesome-healthcare-datasets](https://github.com/geniusrise/awesome-healthcare-datasets) | Comprehensive index of healthcare/biomedical datasets for AI/ML | Open |
| [openmedlab/Awesome-Medical-Dataset](https://github.com/openmedlab/Awesome-Medical-Dataset) | Medical datasets for imaging, EHR, NLP | Open |
| [McGill-NLP/medal](https://github.com/McGill-NLP/medal) | Large medical abbreviation disambiguation dataset for NLU pre-training | Open |
| [salgadev/medical-nlp](https://github.com/salgadev/medical-nlp) | Medical transcription corpus with clinical stopwords/vocabulary | Open |
| [adbar/German-NLP](https://github.com/adbar/German-NLP) | Comprehensive index of German NLP resources including medical | Open |
| [JULIELab/GGPOnc](https://github.com/JULIELab/GGPOnc) | Code for the GGPONC German oncology NLP corpus | Open |
| [lhs-open/synthetic-data](https://github.com/lhs-open/synthetic-data) | Pre-generated Synthea patient data ready for ML | Open |
| [mk-runner/Awesome-Radiology-Report-Generation](https://github.com/mk-runner/Awesome-Radiology-Report-Generation) | Papers, datasets, tools for radiology report generation | Open |
| [maduc7/Histopathology-Datasets](https://github.com/maduc7/Histopathology-Datasets) | Index of histopathology datasets | Open |

---

## 4. Academic / PhysioNet Datasets (Credentialed Access)

| Dataset | Size | Format | License | Access |
|---|---|---|---|---|
| [MIMIC-IV v3.1](https://physionet.org/content/mimiciv/3.1/) | 364,627 patients, 546,028 hospitalizations, 94,458 ICU stays | Structured (vitals, labs, meds, diagnoses, procedures) | PhysioNet Credentialed | CITI training + DUA |
| [MIMIC-IV-Note v2.2](https://physionet.org/content/mimic-iv-note/2.2/) | 331,794 discharge summaries + 2,321,355 radiology reports | Free text (deidentified) | PhysioNet Credentialed | Same as above |
| [MIMIC-IV Demo](https://physionet.org/content/mimic-iv-demo/2.2/) | 100 patients (subset) | Structured (no free-text notes) | Open / no credentialing | **Freely available** |
| [MIMIC-III](https://physionet.org/content/mimiciii/1.4/) | 40,000+ ICU patients, 2M+ free-text notes | Structured + text | PhysioNet Credentialed | CITI training + DUA |
| [eICU-CRD v2.0](https://physionet.org/content/eicu-crd/2.0/) | 200,000+ ICU admissions, multi-center | Structured (vitals, diagnoses, treatments) | PhysioNet Credentialed | CITI training + DUA |
| [EHR-DS-QA](https://physionet.org/content/ehr-ds-qa/1.0.0/) | 21,466 discharge summaries, 156,599 QA pairs | Text (Q&A from MIMIC-IV) | PhysioNet | Credentialed |
| [MIMIC-IV-Ext-BHC](https://physionet.org/content/labelled-notes-hospital-course/1.1.0/) | Labeled clinical notes | Text (hospital course summarization) | PhysioNet | Credentialed |
| [n2c2/i2b2 Shared Task Datasets](https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/) | Multiple years (2006-2022), hundreds of annotated clinical notes | Text (deidentified, annotated for NER, relations, etc.) | DUA required | DBMI Data Portal registration |

**PhysioNet credentialing process**: Complete CITI "Data or Specimens Only Research" course (affiliate with MIT), create PhysioNet account, provide reference/supervisor, sign DUA. Processing time: days to weeks.

---

## 5. Multilingual / Underserved Datasets

| Dataset | Language | Size | Access | Fine-Tuning Use |
|---|---|---|---|---|
| [TurkMedNLI](https://pmc.ncbi.nlm.nih.gov/articles/PMC11888880/) | Turkish | Medical NLI pairs | CC-BY | Template for creating German equivalents |
| [Spanish/Catalan Clinical Records](https://pmc.ncbi.nlm.nih.gov/articles/PMC12215073/) | ES/CA | De-identified clinical text | CC-BY-4.0 | Medical entity recognition in Romance languages |
| [MMedC](https://www.nature.com/articles/s41467-024-52417-z) | 6 languages (EN, ZH, JA, FR, RU, ES) | 25.5B tokens | CC-BY-4.0 | Multilingual medical corpus for cross-lingual medical LLM training |
| [PadChest](https://www.nature.com/articles/s41746-024-01339-7) | Spanish | 160,000+ labeled images + Spanish reports | Academic | Spanish radiology report generation |
| [Multilingual Biomedical Concept Normalization](https://www.medrxiv.org/content/10.1101/2025.01.15.25320579v1) | EN, FR, DE, ES, TR | 59,104 terms, 27,280 concepts | Academic | Cross-lingual biomedical concept grounding including German |

---

## 6. Strategic Recommendations for Fine-Tuning

**For generating privacy-safe synthetic German medical data specifically:**

1. **Start with CARDIO:DE** (500 real German discharge letters, open access) -- the single most valuable German clinical text resource for learning authentic German clinical writing style.

2. **Layer in GGPONC 2.0** (200K+ German medical entity annotations) -- provides the medical vocabulary and entity structure needed for realistic German medical text.

3. **Use Synthea (especially the Austrian fork)** to generate structured patient records that can serve as conditioning inputs for text generation.

4. **Leverage MMedC's German subset** (from the 25.5B token multilingual medical corpus) for broader German medical language pre-training.

5. **Use MIMIC-IV-Note** (2.3M radiology reports + 331K discharge summaries in English) as a high-volume training source, then apply cross-lingual transfer to German using medBERT.de or translation pipelines.

6. **For drug interactions**, combine DrugBank DDI (191K pairs) with allenai/drug-combo-extraction for text-based drug interaction description generation.

7. **The Asclepius pipeline** (synthetic clinical notes from MIMIC) demonstrates a proven methodology: take real structured data, generate synthetic free-text, then use that to train further generation models -- a "data flywheel" approach applicable to German data.

**Critical gap**: There is no large-scale open German clinical notes corpus comparable to MIMIC. The GeMTeX project (multi-site, 6 university hospitals) is under development and would be transformative when released. Until then, translation-based approaches (English clinical text translated to German, validated against CARDIO:DE style) combined with GGPONC entity knowledge represent the most viable path.

---

## Sources
- [Synthea](https://github.com/synthetichealth/synthea)
- [Synthea Austrian Implementation](https://github.com/FHOOEAIST/synthea-AT-implementation)
- [GGPONC 2.0](https://huggingface.co/datasets/bigbio/ggponc2)
- [CARDIO:DE](https://www.nature.com/articles/s41597-023-02128-9)
- [GeMTeX](https://fit.uni-tuebingen.de/Project/Details?id=10290)
- [GERNERMED++](https://www.sciencedirect.com/science/article/pii/S1532046423002344)
- [German Clinical Corpora Survey 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12077144/)
- [GerMedBERT](https://huggingface.co/GerMedBERT/medbert-512)
- [MMedC](https://www.nature.com/articles/s41467-024-52417-z)
- [MIMIC-IV](https://physionet.org/content/mimiciv/3.1/)
- [MIMIC-IV-Note](https://physionet.org/content/mimic-iv-note/2.2/)
- [eICU-CRD](https://physionet.org/content/eicu-crd/2.0/)
- [DrugBank DDI](https://tdcommons.ai/multi_pred_tasks/ddi/)
- [Asclepius](https://huggingface.co/datasets/starmpcc/Asclepius-Synthetic-Clinical-Notes)
- [hf4h Synthetic Medical Collection](https://huggingface.co/collections/hf4h/synthetic-medical-data-and-models-64f9bf3446f3f06f5abdb770)
- [Awesome Healthcare Datasets](https://github.com/geniusrise/awesome-healthcare-datasets)
- [Awesome Medical Dataset](https://github.com/openmedlab/Awesome-Medical-Dataset)
- [German NLP Resources](https://github.com/adbar/German-NLP)
