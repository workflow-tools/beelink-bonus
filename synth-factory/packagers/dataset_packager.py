"""
Package generated + validated datasets into sellable bundles.

Creates:
  output/{dataset_name}/{version}/
  ├── data/
  │   ├── {table}.csv
  │   └── {table}.parquet  (optional)
  ├── samples/
  │   └── {table}_preview.csv  (first N rows, free preview for marketplace)
  ├── metadata/
  │   ├── datasheet.md     (Gebru-style dataset documentation)
  │   ├── schema.json      (column types, descriptions, constraints)
  │   └── generation_config.yaml  (exact config used, for reproducibility)
  ├── validation/
  │   ├── validation_{table}.json
  │   └── validation_{table}.html
  └── LICENSE.md

Extensibility: Add new output formats by extending _export_data().
"""

from __future__ import annotations
import json
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from generators.config_schema import DatasetConfig, LicenseType
from validators.quality_validator import ValidationReport

logger = logging.getLogger(__name__)


def package_dataset(
    tables: dict[str, pd.DataFrame],
    config: DatasetConfig,
    validation_reports: dict[str, ValidationReport],
    output_base: Path = Path("output"),
    config_path: Optional[Path] = None,
) -> Path:
    """
    Package generated tables into a sellable dataset bundle.

    Args:
        tables: Dict of table_name -> DataFrame.
        config: The dataset configuration.
        validation_reports: Dict of table_name -> ValidationReport.
        output_base: Base output directory.
        config_path: Path to the original YAML config (for reproduction).

    Returns:
        Path to the output directory (or zip file if configured).
    """
    meta = config.metadata
    version = meta.version
    name = meta.name

    output_dir = output_base / name / version
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Packaging dataset '{name}' v{version} to {output_dir}")

    # ── Export data ──────────────────────────────────────────────
    data_dir = output_dir / "data"
    data_dir.mkdir(exist_ok=True)

    for table_name, df in tables.items():
        _export_data(df, table_name, data_dir, config)

    # ── Export preview samples ───────────────────────────────────
    samples_dir = output_dir / "samples"
    samples_dir.mkdir(exist_ok=True)

    preview_rows = config.packaging.preview_rows
    doc_table_names = {dt.name for dt in config.document_tables}
    for table_name, df in tables.items():
        preview = df.head(preview_rows)
        if table_name in doc_table_names and config.packaging.output_jsonl:
            # Use JSONL for document table previews
            preview_path = samples_dir / f"{table_name}_preview.jsonl"
            with open(preview_path, "w", encoding="utf-8") as f:
                for _, row in preview.iterrows():
                    f.write(row.to_json(ensure_ascii=False) + "\n")
        else:
            preview.to_csv(
                samples_dir / f"{table_name}_preview.csv",
                index=False, encoding="utf-8"
            )

    # ── Export metadata ──────────────────────────────────────────
    meta_dir = output_dir / "metadata"
    meta_dir.mkdir(exist_ok=True)

    # Schema JSON
    schema = _build_schema(config)
    with open(meta_dir / "schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    # Datasheet (Gebru format)
    if config.packaging.generate_datasheet:
        datasheet = _generate_datasheet(config, tables, validation_reports)
        with open(meta_dir / "datasheet.md", "w", encoding="utf-8") as f:
            f.write(datasheet)

    # Copy original config for reproducibility
    if config_path and config_path.exists():
        shutil.copy2(config_path, meta_dir / "generation_config.yaml")
    else:
        # Serialize current config
        with open(meta_dir / "generation_config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(mode="json"), f, default_flow_style=False)

    # ── Export validation reports ─────────────────────────────────
    val_dir = output_dir / "validation"
    val_dir.mkdir(exist_ok=True)

    for table_name, report in validation_reports.items():
        report.save(val_dir)

    # ── License ──────────────────────────────────────────────────
    license_text = _get_license_text(meta.license)
    with open(output_dir / "LICENSE.md", "w", encoding="utf-8") as f:
        f.write(license_text)

    # ── Summary statistics ────────────────────────────────────────
    stats = _compute_statistics(tables)
    with open(meta_dir / "statistics.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # ── Create zip if configured ──────────────────────────────────
    if config.packaging.create_zip:
        zip_path = _create_zip(output_dir, name, version)
        logger.info(f"Dataset zip created: {zip_path}")

    # ── Create "latest" symlink ───────────────────────────────────
    latest_link = output_base / name / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(version, target_is_directory=True)

    logger.info(f"Dataset packaged: {output_dir}")
    return output_dir


def _export_data(df: pd.DataFrame, table_name: str, data_dir: Path, config: DatasetConfig):
    """Export a table in configured formats."""
    if config.packaging.output_csv:
        csv_path = data_dir / f"{table_name}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"Exported {csv_path} ({len(df)} rows)")

    if config.packaging.output_parquet:
        parquet_path = data_dir / f"{table_name}.parquet"
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Exported {parquet_path}")

    if config.packaging.output_jsonl:
        jsonl_path = data_dir / f"{table_name}.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for _, row in df.iterrows():
                f.write(row.to_json(ensure_ascii=False) + "\n")
        logger.info(f"Exported {jsonl_path} ({len(df)} records)")


def _build_schema(config: DatasetConfig) -> dict:
    """Build a JSON schema description of all tables."""
    schema = {
        "dataset": config.metadata.name,
        "version": config.metadata.version,
        "generated_at": datetime.now().isoformat(),
        "tables": {},
    }

    for table_def in config.tables:
        table_schema = {
            "description": table_def.description or "",
            "records": table_def.records,
            "columns": {},
        }
        for col in table_def.columns:
            col_info = {
                "type": col.type.value,
                "description": col.description or "",
                "nullable": col.nullable,
                "unique": col.unique,
            }
            if col.values:
                col_info["allowed_values"] = col.values
            if col.distribution:
                col_info["distribution"] = col.distribution.value
            table_schema["columns"][col.name] = col_info

        schema["tables"][table_def.name] = table_schema

    # Document tables
    for doc_table_def in config.document_tables:
        doc_type_name = doc_table_def.document_type
        doc_type = None
        for dt in config.document_types:
            if dt.name == doc_type_name:
                doc_type = dt
                break

        doc_schema = {
            "description": doc_table_def.description or "",
            "records": doc_table_def.records,
            "type": "document",
            "document_type": doc_type_name,
            "language": doc_type.language if doc_type else "unknown",
            "segments": {},
        }
        if doc_type:
            for seg in doc_type.segments:
                doc_schema["segments"][seg.name] = {
                    "type": seg.segment_type.value,
                    "description": seg.description or "",
                    "label": seg.label or "",
                    "max_tokens": seg.max_tokens,
                }
        schema["tables"][doc_table_def.name] = doc_schema

    return schema


def _compute_statistics(tables: dict[str, pd.DataFrame]) -> dict:
    """Compute summary statistics for each table."""
    stats = {}
    for table_name, df in tables.items():
        table_stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
        }
        for col in df.columns:
            col_stats = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_ratio": round(float(df[col].isna().mean()), 4),
                "unique_count": int(df[col].nunique()),
            }

            if pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe()
                col_stats.update({
                    "mean": round(float(desc.get("mean", 0)), 4),
                    "std": round(float(desc.get("std", 0)), 4),
                    "min": round(float(desc.get("min", 0)), 4),
                    "max": round(float(desc.get("max", 0)), 4),
                    "median": round(float(desc.get("50%", 0)), 4),
                })
            elif pd.api.types.is_string_dtype(df[col]):
                col_stats["avg_length"] = round(
                    float(df[col].dropna().str.len().mean()), 1
                )
                top_values = df[col].value_counts().head(5).to_dict()
                col_stats["top_values"] = {str(k): int(v) for k, v in top_values.items()}

            table_stats["columns"][col] = col_stats

        stats[table_name] = table_stats
    return stats


def _generate_datasheet(
    config: DatasetConfig,
    tables: dict[str, pd.DataFrame],
    reports: dict[str, ValidationReport],
) -> str:
    """
    Generate a Gebru-style datasheet for the dataset.

    Reference: Gebru et al., "Datasheets for Datasets" (2021).
    This format is also the basis for HuggingFace dataset cards
    and aligns with EU AI Act data governance documentation requirements.
    """
    meta = config.metadata
    total_rows = sum(len(df) for df in tables.values())
    table_names = ", ".join(tables.keys())
    quality_scores = {
        name: f"{r.quality_score:.0%}" for name, r in reports.items()
    }

    datasheet = f"""# Datasheet: {meta.name}

> Version: {meta.version}
> Generated: {datetime.now().strftime('%Y-%m-%d')}
> Author: {meta.author}
> License: {meta.license.value}

---

## Motivation

**Purpose:** {meta.description}

**Creator:** {meta.author}

**Funding:** This dataset was generated as part of the VilseckKI synthetic data initiative
using local compute infrastructure (no cloud dependencies, no US data processing).

---

## Composition

**Tables:** {table_names}

**Total records:** {total_rows:,}

**Language:** {meta.language}

"""

    # Add table details
    for table_def in config.tables:
        df = tables.get(table_def.name)
        if df is None:
            continue

        datasheet += f"### Table: {table_def.name}\n\n"
        if table_def.description:
            datasheet += f"{table_def.description}\n\n"
        datasheet += f"Records: {len(df):,}\n\n"
        datasheet += "| Column | Type | Description |\n|---|---|---|\n"
        for col in table_def.columns:
            desc = col.description or ""
            datasheet += f"| {col.name} | {col.type.value} | {desc} |\n"
        datasheet += "\n"

    # Add document table details
    for doc_table_def in config.document_tables:
        doc_type = None
        for dt in config.document_types:
            if dt.name == doc_table_def.document_type:
                doc_type = dt
                break

        df = tables.get(doc_table_def.name)
        if df is None:
            continue

        datasheet += f"### Document Table: {doc_table_def.name}\n\n"
        if doc_table_def.description:
            datasheet += f"{doc_table_def.description}\n\n"
        datasheet += f"Documents: {len(df):,}\n\n"
        if doc_type:
            datasheet += f"Document type: {doc_type.name} ({doc_type.language})\n\n"
            datasheet += "| Segment | Type | Label |\n|---|---|---|\n"
            for seg in doc_type.segments:
                label = seg.label or ""
                datasheet += f"| {seg.name} | {seg.segment_type.value} | {label} |\n"
            datasheet += "\n"

    datasheet += f"""---

## Collection Process

This is a **synthetic dataset** — no real data was collected.

**Generation method:** {config.generation.method.value}

**Tabular structure:** Generated using SDV (Synthetic Data Vault) with
distribution parameters derived from published German federal statistics
(Statistisches Bundesamt Unternehmensregister, KfW Mittelstandspanel,
IfM Bonn SME statistics).

**Text fields:** Augmented using locally-run large language models via Ollama.
Default model: {config.generation.ollama_default_model}.
All inference performed on-premises (Beelink GTR9 Pro, Vilseck, Bavaria).
No data was sent to any cloud API.

---

## Preprocessing / Cleaning

Post-generation validation was performed using Evidently AI.

Quality scores by table:
"""
    for name, score in quality_scores.items():
        datasheet += f"- **{name}:** {score}\n"

    datasheet += f"""
---

## Uses

### Intended Uses

"""
    for use in meta.intended_uses:
        datasheet += f"- {use}\n"

    if not meta.intended_uses:
        datasheet += "- AI/ML model development and testing\n"
        datasheet += "- EU AI Act compliance testing\n"
        datasheet += "- Software development test data\n"

    datasheet += f"""
### Out-of-Scope Uses

"""
    for use in meta.out_of_scope_uses:
        datasheet += f"- {use}\n"

    if not meta.out_of_scope_uses:
        datasheet += "- This data must NOT be represented as real data\n"
        datasheet += "- Not suitable for training models that will make decisions about real individuals\n"
        datasheet += "- Not a substitute for real data validation in production systems\n"

    datasheet += f"""
---

## Distribution

**License:** {meta.license.value}

**Available from:** Datarade, HuggingFace (preview), vilseckki.de (custom orders)

---

## Maintenance

**Contact:** {meta.contact}

**Update schedule:** Quarterly version refreshes with improved distributions and
expanded record counts.

---

*This datasheet follows the format proposed by Gebru et al. (2021),
"Datasheets for Datasets," Communications of the ACM.*
"""
    return datasheet


def _get_license_text(license_type: LicenseType) -> str:
    """Return license text for common licenses."""
    if license_type == LicenseType.CC_BY_4:
        return (
            "# Creative Commons Attribution 4.0 International (CC BY 4.0)\n\n"
            "You are free to share and adapt this dataset for any purpose, "
            "including commercial use, as long as you give appropriate credit.\n\n"
            "Full text: https://creativecommons.org/licenses/by/4.0/legalcode\n"
        )
    elif license_type == LicenseType.CC_BY_NC_4:
        return (
            "# Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)\n\n"
            "You are free to share and adapt this dataset for non-commercial purposes "
            "as long as you give appropriate credit.\n\n"
            "Full text: https://creativecommons.org/licenses/by-nc/4.0/legalcode\n"
        )
    elif license_type == LicenseType.COMMERCIAL:
        return (
            "# Commercial License\n\n"
            "This dataset is licensed for use by the purchasing organization only.\n"
            "Redistribution is prohibited. Contact workflow.tools@icloud.com for terms.\n"
        )
    else:
        return f"# License: {license_type.value}\n\nSee LICENSE terms from the data provider.\n"


def _create_zip(output_dir: Path, name: str, version: str) -> Path:
    """Create a zip archive of the output directory."""
    zip_name = f"{name}-v{version}"
    zip_path = output_dir.parent / f"{zip_name}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                arcname = f"{zip_name}/{file_path.relative_to(output_dir)}"
                zf.write(file_path, arcname)

    return zip_path
