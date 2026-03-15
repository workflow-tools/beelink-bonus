"""
Tests for config loading and validation.
Run: pytest tests/ -v
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.config_loader import load_config, list_configs
from generators.config_schema import DatasetConfig, ColumnType, GenerationMethod


def test_load_test_tiny_config():
    """Verify the test-tiny config loads and validates."""
    config = load_config(Path("configs/test-tiny.yaml"))
    assert config.metadata.name == "test-tiny"
    assert len(config.tables) == 1
    assert config.tables[0].records == 100


def test_load_mittelstand_config():
    """Verify the mittelstand-b2b config loads and validates."""
    config = load_config(Path("configs/mittelstand-b2b.yaml"))
    assert config.metadata.name == "synthetic-bavarian-mittelstand-b2b"
    assert len(config.tables) == 2
    assert config.tables[0].name == "companies"
    assert config.tables[1].name == "transactions"
    assert config.tables[0].records == 50000
    assert config.tables[1].records == 200000


def test_column_types_valid():
    """Verify all column types in configs are valid enum values."""
    for config_path in list_configs(Path("configs")):
        config = load_config(config_path)
        for table in config.tables:
            for col in table.columns:
                assert isinstance(col.type, ColumnType), (
                    f"{config_path}: column {col.name} has invalid type {col.type}"
                )


def test_weights_sum_approximately_one():
    """Verify categorical weights sum to ~1.0."""
    for config_path in list_configs(Path("configs")):
        config = load_config(config_path)
        for table in config.tables:
            for col in table.columns:
                if col.weights:
                    total = sum(col.weights)
                    assert 0.99 <= total <= 1.01, (
                        f"{config_path}: {col.name} weights sum to {total}"
                    )


def test_ollama_columns_have_prompts():
    """Verify all ollama-type columns have prompt configs."""
    for config_path in list_configs(Path("configs")):
        config = load_config(config_path)
        for table in config.tables:
            for col in table.columns:
                if col.generator and col.generator.value == "ollama":
                    assert col.ollama is not None, (
                        f"{config_path}: {col.name} is ollama but has no ollama config"
                    )
                    assert col.ollama.prompt, (
                        f"{config_path}: {col.name} ollama config has no prompt"
                    )
