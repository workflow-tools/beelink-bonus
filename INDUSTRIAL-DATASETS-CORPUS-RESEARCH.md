# Industrial & Manufacturing Datasets: Comprehensive Corpus Research

## Purpose
Training corpuses for fine-tuning models on a 128GB RAM machine to generate synthetic industrial data at scale. Focus on UNCOMMON and UNDERSERVED datasets.

---

## TIER 1: RARE / HARD-TO-FIND DATASETS (Highest Value for Differentiation)

### 1. Bosch CNC Machining Dataset
- **URL**: https://github.com/boschresearch/CNC_Machining | https://archive.ics.uci.edu/dataset/752/bosch+cnc+machining+dataset
- **Size**: Real-world vibration data from 3 CNC milling machines, each executing 15 processes, collected over ~3 years (Oct 2018 - Aug 2021)
- **Format**: Time-series (tri-axial accelerometer at 2 kHz sampling rate, X/Y/Z axes)
- **License**: Research use (Bosch)
- **Rarity**: VERY RARE -- real industrial CNC data from Bosch, not simulated
- **Synthetic potential**: EXCELLENT. High-frequency real vibration data could train a generative model to produce realistic CNC vibration signatures for anomaly detection training. The multi-machine, multi-process structure provides rich diversity.

### 2. Purdue Machine Tool Cutting Sound Dataset
- **URL**: https://github.com/purduelamm/mt_cutting_dataset
- **Size**: Sound data from 4-axis horizontal CNC mill (Mazak HCN-6000) and 3-axis vertical CNC mill (Hurco VM20i)
- **Format**: Audio time-series (USB microphone + 2 Internal Sound Sensors per machine)
- **License**: Academic
- **Rarity**: EXTREMELY RARE -- acoustic data from real CNC cutting operations with multiple sensor types
- **Synthetic potential**: EXCELLENT. Audio-domain industrial data is almost nonexistent in public datasets. A generative model trained on this could produce synthetic machining sounds for acoustic-based predictive maintenance.

### 3. MIMII Dataset (Malfunctioning Industrial Machine Investigation and Inspection)
- **URL**: https://zenodo.org/records/3384388
- **Size**: 26,092+ normal sound segments; ~1,000 seconds anomalous per machine type. 4 machine types (valves, pumps, fans, slide rails), 7 models each
- **Format**: Audio (8-channel microphone array, 16 kHz, 16-bit)
- **License**: CC BY-SA 4.0
- **Rarity**: RARE -- real factory background noise mixed with machine sounds
- **Synthetic potential**: EXCELLENT. Multi-channel industrial audio with labeled anomalies (contamination, leakage, rotating unbalance, rail damage). Perfect for training audio generation models.

### 4. ToyADMOS2 Dataset
- **URL**: https://github.com/nttcslab/ToyADMOS2-dataset
- **Size**: 27,000+ normal samples, 8,000+ anomalous samples per subdataset, 5-8 microphones
- **Format**: Audio time-series
- **License**: Research
- **Rarity**: RARE -- controlled depth-of-damage data with domain shift scenarios
- **Synthetic potential**: GOOD. The controlled damage progression makes this excellent for training models that generate degradation-aware audio.

### 5. ESPset -- Electrical Submersible Pump Vibration (Oil & Gas)
- **URL**: https://github.com/NINFA-UFES/ESPset
- **Size**: Real vibration data from ESP pumps used in offshore oil exploration
- **Format**: Time-series vibration signals
- **License**: Open source
- **Rarity**: EXTREMELY RARE -- real offshore oil & gas equipment vibration data
- **Synthetic potential**: EXCELLENT. Oil & gas predictive maintenance data is almost impossible to find publicly. Generating synthetic ESP vibration data would be highly valuable.

### 6. Paderborn University Bearing Dataset
- **URL**: https://mb.uni-paderborn.de/kat/forschung/datacenter/bearing-datacenter
- **Size**: 32 bearings (6 healthy, 12 artificial damage, 14 real damage from accelerated life tests)
- **Format**: Vibration + motor current signals at 64 kHz sampling, .mat format
- **License**: Academic
- **Rarity**: RARE -- combines vibration AND motor current signals; includes both artificial and natural faults
- **Synthetic potential**: EXCELLENT. Dual-modality (vibration + current) at very high sampling rate. Training a model on this enables generating realistic correlated multi-sensor data.

### 7. XJTU-SY Bearing Dataset
- **URL**: https://biaowang.tech/xjtu-sy-bearing-datasets/
- **Size**: 15 bearings, complete run-to-failure, horizontal + vertical vibration at 25.6 kHz
- **Format**: Time-series, 1.28-second snapshots at 1-minute intervals
- **License**: Academic
- **Rarity**: RARE -- complete degradation trajectory from healthy to failure
- **Synthetic potential**: EXCELLENT. Full lifecycle degradation data is the holy grail for synthetic RUL (Remaining Useful Life) data generation.

### 8. Additive Manufacturing Digital Twin Dataset
- **URL**: https://huggingface.co/datasets/g4ndh1/Additive-Manufacturing-Digital-Twin
- **Size**: Varies (check HuggingFace page)
- **Format**: Tabular / process parameters
- **License**: Check HuggingFace
- **Rarity**: VERY RARE -- additive manufacturing + digital twin combination on HuggingFace
- **Synthetic potential**: HIGH. Additive manufacturing process data is extremely underserved. Could generate synthetic 3D printing process parameters and outcomes.

### 9. GainEnergy Oil & Gas Engineering Dataset
- **URL**: https://huggingface.co/datasets/GainEnergy/oilandgas-engineering-dataset
- **Size**: Check HuggingFace
- **Format**: Text/engineering documents
- **License**: Check HuggingFace
- **Rarity**: RARE -- domain-specific engineering text for oil & gas
- **Synthetic potential**: HIGH. Fine-tuning an LLM on oil & gas engineering text could generate realistic technical documentation, procedures, and specifications.

### 10. SISO-RAW Control Loop Dataset
- **URL**: https://www.sciencedirect.com/science/article/abs/pii/S0098135420312412
- **Size**: 2.5 days of SISO control loop data from a real oil & gas facility
- **Format**: Time-series (non-constant sampling time)
- **License**: Academic
- **Rarity**: EXTREMELY RARE -- real process control data from an operating facility
- **Synthetic potential**: EXCELLENT. Process control loop data is one of the most underserved categories. Generating synthetic SISO control data would be highly valuable for control system tuning and anomaly detection.

---

## TIER 2: UNCOMMON BUT KNOWN IN SPECIALIST CIRCLES

### 11. FEMTO-ST / PRONOSTIA Bearing Dataset
- **URL**: https://github.com/topics/pronostia-dataset
- **Size**: 17 accelerated run-to-failures, 25.6 kHz sampling, 2560 samples every 10 seconds
- **Format**: Time-series (vibration + temperature)
- **License**: Academic (IEEE PHM 2012 Challenge)
- **Rarity**: UNCOMMON -- known in PHM community but not widely used outside it
- **Synthetic potential**: GOOD. Accelerated degradation data with temperature correlation.

### 12. Tennessee Eastman Process (TEP) Simulation
- **URL**: https://www.kaggle.com/datasets/averkij/tennessee-eastman-process-simulation-dataset | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/6C3JR1
- **Size**: Multivariate time-series, 52 variables, 21 fault scenarios
- **Format**: Tabular time-series
- **License**: Open
- **Rarity**: UNCOMMON -- standard benchmark in process control, but the Harvard Dataverse extended version with additional fault scenarios is less known
- **Synthetic potential**: EXCELLENT. A model trained on TEP could generate unlimited synthetic chemical process scenarios with configurable fault types. 128GB RAM is more than sufficient.

### 13. WM-811K Wafer Map Dataset
- **URL**: https://www.kaggle.com/datasets (search WM-811K)
- **Size**: 811,457 wafer maps from real semiconductor fabs, ~20% expert-annotated
- **Format**: Image (wafer maps) + tabular metadata
- **License**: Research
- **Rarity**: UNCOMMON -- large but underutilized for generative purposes
- **Synthetic potential**: EXCELLENT. 800K+ wafer maps is a substantial corpus. A generative model could produce infinite synthetic wafer defect patterns for semiconductor yield analysis.

### 14. GC10-DET Steel Surface Defect Dataset
- **URL**: https://github.com/lvxiaoming2019/GC10-DET-Metallic-Surface-Defect-Datasets | https://www.kaggle.com/datasets/alex000kim/gc10det
- **Size**: 2,298 images, 10 defect types (punching, welding line, crescent gap, water spot, oil spot, silk spot, inclusion, rolled pit, crease, waist fold)
- **Format**: Images (from linear CCD cameras)
- **License**: Research
- **Rarity**: UNCOMMON -- overshadowed by NEU-DET but has more defect categories
- **Synthetic potential**: GOOD. 10 defect types provides good diversity. Could train an image generation model for steel surface QC.

### 15. Innodisk PCB Datasets
- **URL**: https://huggingface.co/datasets/evan6007/Innodisk_PCB_datasets
- **Size**: AOI raw images + ROI crops + Canny edge maps
- **Format**: Images
- **License**: CC BY-NC 4.0
- **Rarity**: UNCOMMON -- real production PCB images from Innodisk Corporation
- **Synthetic potential**: HIGH. Real AOI production images (not lab photos) are rare. Good for training PCB defect image generators.

### 16. DefectSpectrum Dataset
- **URL**: https://huggingface.co/datasets/DefectSpectrum/Defect_Spectrum
- **Size**: Check HuggingFace
- **Format**: Images
- **License**: Check HuggingFace
- **Rarity**: UNCOMMON -- multi-domain defect detection
- **Synthetic potential**: HIGH. Cross-domain defect data enables training generalized defect generators.

### 17. N-CMAPSS (New C-MAPSS) Turbofan Dataset
- **URL**: https://data.phmsociety.org/nasa/ (PHM 2021 Challenge)
- **Size**: Significantly larger than original C-MAPSS, real flight conditions
- **Format**: Time-series (21+ sensor channels per engine)
- **License**: NASA/PHM Society
- **Rarity**: UNCOMMON -- many people use original C-MAPSS but not the newer N-CMAPSS
- **Synthetic potential**: EXCELLENT. More realistic than C-MAPSS with real flight profiles. Training a generative model could produce unlimited synthetic engine degradation trajectories.

### 18. Gas Sensor Array Drift Dataset
- **URL**: UCI ML Repository
- **Size**: 13,910 measurements from 16 chemical sensors, 6 gases at various concentrations
- **Format**: Tabular time-series
- **License**: Open (UCI)
- **Rarity**: UNCOMMON
- **Synthetic potential**: GOOD. Sensor drift modeling is important for industrial IoT calibration.

---

## TIER 3: WELL-KNOWN BENCHMARKS (Still Valuable for Baseline Training)

### 19. NASA IMS Bearing Dataset
- **URL**: https://data.nasa.gov/dataset/ims-bearings | https://phm-datasets.s3.amazonaws.com/NASA/4.+Bearings.zip
- **Size**: 3 test-to-failure experiments, 20,480 points per file at 20 kHz, files every 10 minutes
- **Format**: Time-series vibration
- **License**: Public domain (NASA)
- **Rarity**: COMMON but essential baseline
- **Synthetic potential**: GOOD. Standard bearing degradation data.

### 20. CWRU Bearing Dataset
- **URL**: https://engineering.case.edu/bearingdatacenter
- **Size**: Multiple fault diameters (0.007-0.040 inches), 12 kHz and 48 kHz sampling
- **Format**: Time-series (.mat files)
- **License**: Open academic
- **Rarity**: VERY COMMON -- most cited bearing dataset
- **Synthetic potential**: GOOD as baseline. Everyone uses it, but synthetic CWRU-like data could help augment it.

### 21. C-MAPSS Turbofan Engine Degradation
- **URL**: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps | https://data.phmsociety.org/nasa/
- **Size**: 4 sub-datasets (FD001-FD004), 218 engines, 21 sensor channels each
- **Format**: Tabular time-series
- **License**: Public (NASA)
- **Rarity**: VERY COMMON
- **Synthetic potential**: GOOD for baseline RUL training.

### 22. MVTec AD / MVTec AD 2
- **URL**: https://www.mvtec.com/company/research/datasets/mvtec-ad
- **Size**: MVTec AD: 5,000+ images, 15 categories, 70+ defect types. MVTec AD 2: 8,000+ images, 8 categories
- **Format**: Images (high-resolution)
- **License**: CC BY-NC-SA 4.0
- **Rarity**: COMMON in anomaly detection community
- **Synthetic potential**: EXCELLENT. High-quality pixel-annotated industrial images. MVTec AD 2 specifically has challenging scenarios (transparent objects, dark-field illumination, extremely small defects).

### 23. VisA Dataset
- **URL**: https://github.com/amazon-science/spot-diff
- **Size**: 10,821 images (9,621 normal, 1,200 anomalous), 12 objects including 4 PCB types
- **Format**: Images
- **License**: CC BY-NC 4.0 (Amazon)
- **Rarity**: MODERATE
- **Synthetic potential**: GOOD. Multiple PCB types and multi-instance scenarios.

### 24. NEU Surface Defect Database
- **URL**: https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
- **Size**: 1,800 grayscale images, 6 defect types, 300 per class
- **Format**: Images
- **License**: Open academic
- **Rarity**: COMMON
- **Synthetic potential**: MODERATE. Small dataset but good class balance.

### 25. AI4I 2020 Predictive Maintenance Dataset
- **URL**: https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset
- **Size**: 10,000 rows, 14 features
- **Format**: Tabular (CSV)
- **License**: CC BY 4.0
- **Rarity**: COMMON
- **Synthetic potential**: MODERATE. Already synthetic data reflecting real patterns. Meta-training on synthetic-of-synthetic is less valuable.

### 26. SECOM Semiconductor Dataset
- **URL**: http://archive.ics.uci.edu/ml/datasets/SECOM
- **Size**: 1,567 samples, 591 sensor measurements, severe class imbalance (1:14)
- **Format**: Tabular
- **License**: Open (UCI)
- **Rarity**: MODERATE
- **Synthetic potential**: HIGH. Extreme class imbalance makes synthetic minority oversampling very valuable.

### 27. Microsoft Azure Predictive Maintenance
- **URL**: https://www.kaggle.com/datasets/arnabbiswas1/microsoft-azure-predictive-maintenance
- **Size**: Multi-table (telemetry, errors, maintenance logs, failures, machines)
- **Format**: Tabular (CSV)
- **License**: Microsoft
- **Rarity**: MODERATE
- **Synthetic potential**: GOOD. Multi-table relational structure is realistic and useful for training.

---

## TIER 4: CURATED META-REPOSITORIES (Discovery Resources)

### 28. awesome-industrial-machine-datasets
- **URL**: https://github.com/makinarocks/awesome-industrial-machine-datasets
- **Coverage**: Semiconductor, CNC, chemical process, gas sensors, engines
- **Value**: Discovery of 50+ datasets across categories

### 29. industrial-ml-datasets
- **URL**: https://github.com/nicolasj92/industrial-ml-datasets
- **Coverage**: Milling, cutting blade degradation, Tennessee Eastman, tool wear
- **Value**: Manufacturing-ML-specific curation

### 30. awesome-industrial-datasets
- **URL**: https://github.com/jonathanwvd/awesome-industrial-datasets
- **Coverage**: Broadest collection, hundreds of datasets
- **Value**: Best single discovery resource

### 31. Open-industrial-datasets
- **URL**: https://github.com/AndreaPi/Open-industrial-datasets
- **Coverage**: Oil & gas, aerospace, multivariate time series
- **Value**: Includes hard-to-find Airbus and Cognite/Aker BP datasets

### 32. awesome-bearing-dataset
- **URL**: https://github.com/VictorBauler/awesome-bearing-dataset
- **Coverage**: All known public bearing fault datasets
- **Value**: Comprehensive for rotating machinery domain

### 33. PHM-Datasets (Consolidated)
- **URL**: https://github.com/alovberg/PHM-Datasets
- **Coverage**: All PHM Society and NASA prognostics datasets
- **Value**: Single-stop for prognostics data

### 34. awesome-industrial-anomaly-detection
- **URL**: https://github.com/M-3LAB/awesome-industrial-anomaly-detection
- **Coverage**: Papers + datasets for industrial visual anomaly detection
- **Value**: Cutting-edge methods (2025-2026) with associated datasets

---

## STRATEGIC RECOMMENDATIONS FOR 128GB RAM FINE-TUNING

### Highest-Value Targets for Synthetic Data Generation

1. **Time-Series Generative Models** (fit in 128GB easily):
   - Train on: Bosch CNC + XJTU-SY + Paderborn + FEMTO-ST + NASA IMS
   - Output: Synthetic vibration/current signals for any industrial rotating machinery
   - Model: TimeGAN, DiffusionTS, or fine-tuned Chronos

2. **Industrial Audio Generation** (unique differentiator):
   - Train on: MIMII + ToyADMOS2 + Purdue CNC Sound
   - Output: Synthetic factory machine sounds with configurable anomalies
   - Model: AudioLDM fine-tuned or custom WaveNet

3. **Industrial Image Generation** (large corpus available):
   - Train on: MVTec AD 2 + WM-811K + GC10-DET + NEU-DET + VisA + Innodisk PCB
   - Output: Synthetic defect images for any manufacturing surface
   - Model: Stable Diffusion fine-tuned with ControlNet for defect placement

4. **Process/Sensor Tabular Generation** (most scalable):
   - Train on: Tennessee Eastman + C-MAPSS/N-CMAPSS + SECOM + AI4I + Azure PM
   - Output: Synthetic multi-sensor process data with configurable fault scenarios
   - Model: CTGAN, TabDDPM, or fine-tuned tabular transformer

5. **Industrial Text/Documentation Generation** (least explored):
   - Train on: GainEnergy Oil & Gas + maintenance logs + PHM competition descriptions
   - Output: Synthetic maintenance logs, inspection reports, work orders
   - Model: Fine-tuned Llama/Mistral on industrial text

### Memory Considerations for 128GB RAM
- All tabular datasets combined: <10GB -- trivially fits
- All bearing/vibration datasets combined: ~50-100GB raw -- fits with streaming
- WM-811K wafer maps: ~20GB -- fits easily
- MVTec AD + AD2 + VisA: ~15GB -- fits easily
- Audio datasets (MIMII + ToyADMOS2): ~30GB -- fits
- Total combined corpus: 128GB RAM is sufficient for any single-domain fine-tuning run; for multi-domain, use data streaming/sharding

---

## DATASETS MOST PEOPLE DO NOT KNOW ABOUT (True Hidden Gems)

1. **Bosch CNC_Machining** -- Real Bosch factory data, buried in a GitHub repo
2. **ESPset** -- Offshore oil pump vibration, almost zero visibility
3. **Purdue mt_cutting_dataset** -- CNC cutting SOUND data, unique modality
4. **SISO-RAW** -- Real oil & gas process control loops
5. **MIMII DG** -- Domain generalization variant of MIMII, very few people use it
6. **N-CMAPSS** -- The "v2" of C-MAPSS that most tutorials ignore
7. **Paderborn Bearing** -- 64 kHz dual-modality, far richer than CWRU
8. **Mixed-type Wafer Defect** -- Goes beyond WM-811K with mixed defect patterns
9. **GainEnergy oil & gas text** -- One of the only industrial engineering text corpora on HuggingFace
10. **Additive Manufacturing Digital Twin** -- Essentially the only AM+DT dataset on HuggingFace
