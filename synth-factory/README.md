# Synthetic Data Factory

> ⚠️ **DEPRECATED — March 2026.** This directory was the prototype workspace.
> The canonical codebase has been migrated to **`../../vilseckki-datafactory-app/`**.
> All future development, configs, and documentation live there.
> This directory is retained for reference only.

Config-driven synthetic data generation pipeline for the Beelink GTR9 Pro.

## Architecture

```
YAML Config → Tabular Generator (SDV) → LLM Augmenter (Ollama) → Validator (Evidently) → Packager → Marketplace
```

Each dataset is defined by a single YAML config file. The pipeline reads the
config, generates tabular structure with realistic statistical distributions,
augments text columns using locally-run LLMs, validates quality, and packages
everything into a sellable bundle with documentation.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Bootstrap seed data (PLZ, cities)
python seeds/bootstrap_seeds.py

# 3. Test the pipeline (100 rows, no LLM)
python run.py configs/test-tiny.yaml --skip-llm

# 4. Generate the real Mittelstand dataset (tabular only, ~10 min)
python run.py configs/mittelstand-b2b.yaml --skip-llm

# 5. Generate with LLM augmentation (requires Ollama running, ~8+ hours)
python run.py configs/mittelstand-b2b.yaml

# 6. Check Ollama health
python run.py --health

# 7. List available configs
python run.py --list
```

## Project Structure

```
synth-factory/
├── configs/                    # Dataset YAML definitions
│   ├── mittelstand-b2b.yaml   # First real dataset (50K German SMEs)
│   └── test-tiny.yaml         # 100-row test config
├── generators/                 # Data generation modules
│   ├── config_schema.py       # Pydantic models for YAML validation
│   ├── config_loader.py       # YAML loading + validation
│   ├── tabular_generator.py   # SDV/CTGAN tabular generation
│   └── ollama_augmenter.py    # LLM text augmentation via Ollama
├── validators/                 # Quality validation
│   └── quality_validator.py   # Evidently + custom domain checks
├── packagers/                  # Output bundling
│   └── dataset_packager.py    # CSV/Parquet + datasheet + zip
├── seeds/                      # Reference data for distributions
│   ├── bootstrap_seeds.py     # Generate placeholder seed files
│   └── README.md              # Where to get real seed data
├── cron/                       # Scheduling scripts
│   └── nightly-run.sh         # Cron-compatible nightly runner
├── output/                     # Generated datasets (gitignored)
├── logs/                       # Generation logs (gitignored)
├── tests/                      # Pytest test suite
│   └── test_config.py         # Config validation tests
├── run.py                      # Main entry point / orchestrator
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## How to Add a New Dataset

1. Create a new YAML file in `configs/`, following `test-tiny.yaml` as a template
2. Define tables, columns, distributions, and LLM prompts
3. Add any custom validation checks in `validators/quality_validator.py`
4. Run: `python run.py configs/your-dataset.yaml --skip-llm` (test tabular first)
5. Run: `python run.py configs/your-dataset.yaml` (full generation with LLM)
6. Output lands in `output/your-dataset-name/version/`

## Configuration Reference

See `generators/config_schema.py` for the full Pydantic schema.

### Column Types

| Type | Description | Key Parameters |
|------|-------------|----------------|
| `text` | String data | `generator` (faker/ollama/template/weighted_sample) |
| `numeric` | Numbers | `distribution`, `dist_params`, `decimals` |
| `categorical` | Fixed set | `values`, `weights` |
| `datetime` | Timestamps | `start_date`, `end_date` |
| `boolean` | True/False | — |
| `id` | Identifiers | `prefix`, `sequential`, `unique` |

### Text Generators

| Generator | Speed | Quality | Use Case |
|-----------|-------|---------|----------|
| `faker` | Instant | Generic | Addresses, phone numbers, basic names |
| `ollama` | Slow (2-5s/cell) | High | Company names, descriptions, invoices |
| `template` | Instant | Deterministic | Combining other columns: `{name} {suffix}` |
| `weighted_sample` | Instant | Realistic | PLZ codes, city names from reference lists |

### Generation Methods

| Method | Speed | Quality | When to Use |
|--------|-------|---------|-------------|
| `gaussian_copula` | Fast (~10s/50K) | Good | First pass, testing |
| `ctgan` | Slow (~30min/50K) | Better | Production datasets |
| `tvae` | Medium | Good | Alternative to CTGAN |

## Nightly Cron Job

```bash
# Linux crontab
0 22 * * * /opt/vilseckki/factory/cron/nightly-run.sh

# Windows Task Scheduler: trigger daily at 22:00, action:
# bash.exe -c "C:/VilseckKI/factory/cron/nightly-run.sh"
```

The nightly script auto-selects the next config that needs generation,
runs with an 8-hour time limit, and logs everything.

## Hardware Requirements

- **Tabular generation (SDV):** Any machine. CPU only, <8GB RAM.
- **LLM augmentation (7B model):** 8GB+ RAM, ~30 min for 1K text cells.
- **LLM augmentation (70B model):** 64GB+ RAM/VRAM, ~3 hours for 1K text cells.
- **Recommended:** Beelink GTR9 Pro (AMD AI Max+ 395, 128GB) or similar.

## Extending the Framework

### Add a custom validation check:

```python
# In validators/quality_validator.py
from validators.quality_validator import register_check, CheckResult

def my_custom_check(df, config):
    # Your validation logic
    passed = df["my_column"].between(0, 100).all()
    return CheckResult("my_check", passed, "Values in range" if passed else "Out of range")

register_check("my_custom_check", my_custom_check)
```

Then reference it in your YAML config:
```yaml
validation:
  custom_checks:
    - my_custom_check
```

### Add a new dataset domain:

Copy `configs/mittelstand-b2b.yaml`, change the metadata, tables, and columns.
The framework handles the rest — generation, validation, packaging.

Future dataset configs planned:
- `configs/krankenkasse-dialogues.yaml` — German health insurance conversations
- `configs/ai-act-compliance.yaml` — EU AI Act stress-test datasets
- `configs/ehcp-synthetic.yaml` — Synthetic EHCP plans (dissertation)
