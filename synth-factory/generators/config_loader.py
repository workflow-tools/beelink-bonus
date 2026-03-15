"""
Load and validate dataset configuration from YAML files.
"""

from pathlib import Path
import yaml
from .config_schema import DatasetConfig


def load_config(config_path: str | Path) -> DatasetConfig:
    """
    Load a dataset config from a YAML file and validate it.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Validated DatasetConfig object.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        pydantic.ValidationError: If the config is invalid.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return DatasetConfig(**raw)


def list_configs(configs_dir: str | Path = "configs") -> list[Path]:
    """
    List all YAML config files in the configs directory.

    Returns:
        Sorted list of config file paths.
    """
    configs_dir = Path(configs_dir)
    if not configs_dir.exists():
        return []
    return sorted(configs_dir.glob("*.yaml"))
