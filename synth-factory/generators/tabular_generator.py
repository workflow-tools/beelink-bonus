"""
Tabular data generation using SDV (Synthetic Data Vault).

This module handles the core tabular structure generation:
1. If seed data exists, fit the SDV model to it
2. If no seed data, build a synthetic seed from distribution parameters
3. Generate the requested number of records
4. Return a raw DataFrame (text augmentation happens separately)

Extensibility: To add a new generation method, add a case to _create_synthesizer().
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from faker import Faker

from .config_schema import (
    DatasetConfig, TableDef, ColumnDef, ColumnType,
    Distribution, GenerationMethod, TextGenerator,
)

logger = logging.getLogger(__name__)

# Initialize Faker with German locale
fake = Faker("de_DE")
Faker.seed(42)


def generate_table(
    table_def: TableDef,
    config: DatasetConfig,
    seeds_dir: Path = Path("seeds"),
) -> pd.DataFrame:
    """
    Generate a single table according to its definition.

    Args:
        table_def: The table schema definition.
        config: The full dataset config (for generation settings).
        seeds_dir: Directory containing seed CSV files.

    Returns:
        Generated DataFrame with all columns (text placeholders for LLM columns).
    """
    logger.info(f"Generating table '{table_def.name}' with {table_def.records} records")

    # Check for seed data
    seed_df = _load_seed_data(table_def, seeds_dir)

    if seed_df is not None:
        # Fit SDV model to seed data
        df = _generate_from_seed(seed_df, table_def, config)
    else:
        # Build synthetic seed from distribution parameters, then generate
        df = _generate_from_distributions(table_def, config)

    logger.info(f"Generated {len(df)} records for table '{table_def.name}'")
    return df


def _load_seed_data(table_def: TableDef, seeds_dir: Path) -> Optional[pd.DataFrame]:
    """Load seed CSV if specified in the table definition."""
    if table_def.seed_file is None:
        return None

    seed_path = seeds_dir / table_def.seed_file
    if not seed_path.exists():
        logger.warning(f"Seed file not found: {seed_path}, falling back to distributions")
        return None

    logger.info(f"Loading seed data from {seed_path}")
    return pd.read_csv(seed_path)


def _generate_from_seed(
    seed_df: pd.DataFrame,
    table_def: TableDef,
    config: DatasetConfig,
) -> pd.DataFrame:
    """Fit an SDV synthesizer to seed data and generate records."""
    from sdv.single_table import (
        CTGANSynthesizer,
        GaussianCopulaSynthesizer,
        CopulaGANSynthesizer,
        TVAESynthesizer,
    )
    from sdv.metadata import SingleTableMetadata

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(seed_df)

    # Apply column type overrides from config
    for col_def in table_def.columns:
        if col_def.name in seed_df.columns:
            sdtype = _column_type_to_sdv(col_def.type)
            if sdtype:
                metadata.update_column(col_def.name, sdtype=sdtype)

    synthesizer = _create_synthesizer(config.generation.method, metadata, config)
    synthesizer.fit(seed_df)
    return synthesizer.sample(num_rows=table_def.records)


def _generate_from_distributions(
    table_def: TableDef,
    config: DatasetConfig,
) -> pd.DataFrame:
    """
    Build a synthetic seed DataFrame from column distribution parameters,
    then optionally fit an SDV model to it for more realistic correlations.
    """
    n_seed = min(1000, table_def.records)  # Build a small seed
    seed_data = {}

    for col_def in table_def.columns:
        seed_data[col_def.name] = _generate_column_seed(col_def, n_seed)

    seed_df = pd.DataFrame(seed_data)

    # If we're using a simple method and the seed is large enough, just scale it
    if config.generation.method == GenerationMethod.GAUSSIAN_COPULA:
        from sdv.single_table import GaussianCopulaSynthesizer
        from sdv.metadata import SingleTableMetadata

        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(seed_df)

        for col_def in table_def.columns:
            sdtype = _column_type_to_sdv(col_def.type)
            if sdtype and col_def.name in seed_df.columns:
                metadata.update_column(col_def.name, sdtype=sdtype)

        synth = GaussianCopulaSynthesizer(metadata)
        synth.fit(seed_df)
        return synth.sample(num_rows=table_def.records)

    # For GAN-based methods, use the seed directly
    return _generate_from_seed(seed_df, table_def, config)


def _generate_column_seed(col_def: ColumnDef, n: int) -> list:
    """Generate seed values for a single column based on its definition."""

    if col_def.type == ColumnType.CATEGORICAL:
        return _generate_categorical(col_def, n)

    elif col_def.type == ColumnType.NUMERIC:
        return _generate_numeric(col_def, n)

    elif col_def.type == ColumnType.TEXT:
        return _generate_text_placeholder(col_def, n)

    elif col_def.type == ColumnType.BOOLEAN:
        return list(np.random.choice([True, False], size=n))

    elif col_def.type == ColumnType.ID:
        return _generate_ids(col_def, n)

    elif col_def.type == ColumnType.DATETIME:
        return _generate_datetimes(col_def, n)

    else:
        # Fallback: empty strings
        return [""] * n


def _generate_categorical(col_def: ColumnDef, n: int) -> list:
    """Generate categorical values with optional weights."""
    if not col_def.values:
        return [f"category_{i % 5}" for i in range(n)]

    weights = col_def.weights
    if weights:
        # Normalize weights to sum to 1
        total = sum(weights)
        weights = [w / total for w in weights]

    return list(np.random.choice(col_def.values, size=n, p=weights))


def _generate_numeric(col_def: ColumnDef, n: int) -> list:
    """Generate numeric values from a statistical distribution."""
    params = col_def.dist_params
    dist = col_def.distribution or Distribution.NORMAL

    if dist == Distribution.NORMAL:
        mean = params.mean if params and params.mean is not None else 0
        std = params.std if params and params.std is not None else 1
        values = np.random.normal(mean, std, n)

    elif dist == Distribution.LOGNORMAL:
        mean = params.mean if params and params.mean is not None else 0
        std = params.std if params and params.std is not None else 1
        values = np.random.lognormal(mean, std, n)

    elif dist == Distribution.UNIFORM:
        lo = params.min_val if params and params.min_val is not None else 0
        hi = params.max_val if params and params.max_val is not None else 1
        values = np.random.uniform(lo, hi, n)

    elif dist == Distribution.EXPONENTIAL:
        rate = params.rate if params and params.rate is not None else 1
        values = np.random.exponential(1 / rate, n)

    elif dist == Distribution.POISSON:
        mean = params.mean if params and params.mean is not None else 5
        values = np.random.poisson(mean, n)

    elif dist == Distribution.BETA:
        a = params.alpha if params and params.alpha is not None else 2
        b = params.beta if params and params.beta is not None else 5
        values = np.random.beta(a, b, n)

    else:
        values = np.random.normal(0, 1, n)

    # Apply rounding
    if col_def.decimals is not None:
        values = np.round(values, col_def.decimals)

    # Apply min/max bounds
    if params:
        if params.min_val is not None:
            values = np.maximum(values, params.min_val)
        if params.max_val is not None:
            values = np.minimum(values, params.max_val)

    return list(values)


def _generate_text_placeholder(col_def: ColumnDef, n: int) -> list:
    """
    Generate placeholder text.
    - For faker: use the Faker library
    - For ollama: placeholder strings (augmented later)
    - For template: placeholder strings (filled later)
    - For weighted_sample: load and sample from source file
    """
    gen = col_def.generator or TextGenerator.FAKER

    if gen == TextGenerator.FAKER and col_def.faker:
        provider = col_def.faker.provider
        locale = col_def.faker.locale
        loc_fake = Faker(locale)
        func = getattr(loc_fake, provider, None)
        if func:
            return [func(**col_def.faker.kwargs) for _ in range(n)]
        return [f"faker_{provider}_{i}" for i in range(n)]

    elif gen == TextGenerator.OLLAMA:
        # Placeholder — will be replaced by ollama_augmenter.py
        return [f"__OLLAMA_PLACEHOLDER_{col_def.name}_{i}__" for i in range(n)]

    elif gen == TextGenerator.WEIGHTED_SAMPLE and col_def.sample_source:
        return _sample_from_file(col_def.sample_source, n)

    elif gen == TextGenerator.TEMPLATE:
        # Templates are filled post-generation by the augmenter
        return [f"__TEMPLATE_{col_def.name}_{i}__" for i in range(n)]

    else:
        # Default: use Faker for German company names
        return [fake.company() for _ in range(n)]


def _generate_ids(col_def: ColumnDef, n: int) -> list:
    """Generate ID values."""
    prefix = col_def.prefix or ""
    if col_def.sequential:
        return [f"{prefix}{i + 1:06d}" for i in range(n)]
    else:
        import uuid
        return [f"{prefix}{uuid.uuid4().hex[:8].upper()}" for i in range(n)]


def _generate_datetimes(col_def: ColumnDef, n: int) -> list:
    """Generate datetime values within a range."""
    start = col_def.start_date or "2020-01-01"
    end = col_def.end_date or "2026-03-11"
    dates = pd.date_range(start=start, end=end, periods=n)
    # Add some noise
    noise = pd.to_timedelta(np.random.randint(0, 86400, n), unit="s")
    return list((dates + noise).strftime("%Y-%m-%d %H:%M:%S"))


def _sample_from_file(source_path: str, n: int) -> list:
    """Load a CSV/text file and sample with replacement."""
    path = Path("seeds") / source_path
    if not path.exists():
        logger.warning(f"Sample source not found: {path}")
        return [f"missing_sample_{i}" for i in range(n)]

    if path.suffix == ".csv":
        df = pd.read_csv(path)
        col = df.columns[0]  # Use first column
        pool = df[col].dropna().tolist()
    else:
        with open(path, "r", encoding="utf-8") as f:
            pool = [line.strip() for line in f if line.strip()]

    return list(np.random.choice(pool, size=n, replace=True))


def _column_type_to_sdv(col_type: ColumnType) -> Optional[str]:
    """Map our column types to SDV sdtypes."""
    mapping = {
        ColumnType.TEXT: "text",
        ColumnType.NUMERIC: "numerical",
        ColumnType.CATEGORICAL: "categorical",
        ColumnType.DATETIME: "datetime",
        ColumnType.BOOLEAN: "boolean",
        ColumnType.ID: "id",
    }
    return mapping.get(col_type)


def _create_synthesizer(method, metadata, config):
    """Factory for SDV synthesizer instances."""
    from sdv.single_table import (
        CTGANSynthesizer,
        GaussianCopulaSynthesizer,
        CopulaGANSynthesizer,
        TVAESynthesizer,
    )

    gen = config.generation

    if method == GenerationMethod.CTGAN:
        return CTGANSynthesizer(
            metadata,
            epochs=gen.epochs,
            batch_size=gen.batch_size,
        )
    elif method == GenerationMethod.TVAE:
        return TVAESynthesizer(
            metadata,
            epochs=gen.epochs,
            batch_size=gen.batch_size,
        )
    elif method == GenerationMethod.COPULA:
        return CopulaGANSynthesizer(
            metadata,
            epochs=gen.epochs,
            batch_size=gen.batch_size,
        )
    else:  # GAUSSIAN_COPULA (default, fastest)
        return GaussianCopulaSynthesizer(metadata)
