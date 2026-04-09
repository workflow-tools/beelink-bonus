"""
Configuration loader — reads domains.yaml, watches/*.yaml, and prompts/*.yaml.

Rule 1: Config-Driven, Not Code-Driven.
Adding a new URL, product, or triage prompt must never require a code change.
This module loads all YAML config at startup and provides lookup methods.
"""

import os
import logging
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


class RegWatchConfig:
    """Holds the fully-loaded RegWatch configuration.

    Attributes:
        products: Product registry from domains.yaml
        watches: Dict mapping product name → list of watch entries
        prompts: Dict mapping product name → triage prompt config
    """

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.products: dict[str, Any] = {}
        self.watches: dict[str, list[dict]] = {}
        self.prompts: dict[str, dict] = {}
        self._url_index: dict[str, dict] = {}

        self._load_domains()
        self._load_watches()
        self._load_prompts()
        self._build_url_index()

    def _load_domains(self):
        """Load domains.yaml — the product registry."""
        domains_path = self.config_dir / "domains.yaml"
        if not domains_path.exists():
            logger.warning(f"domains.yaml not found at {domains_path}")
            return
        with open(domains_path, "r") as f:
            data = yaml.safe_load(f) or {}
        self.products = data.get("products", {})
        logger.info(f"Loaded {len(self.products)} products from domains.yaml")

    def _load_watches(self):
        """Load all watch files from watches/ directory."""
        watches_dir = self.config_dir / "watches"
        if not watches_dir.exists():
            logger.warning(f"watches/ directory not found at {watches_dir}")
            return
        for watch_file in sorted(watches_dir.glob("*.yaml")):
            product_name = watch_file.stem
            with open(watch_file, "r") as f:
                data = yaml.safe_load(f) or {}
            self.watches[product_name] = data.get("watches", [])
            logger.info(
                f"Loaded {len(self.watches[product_name])} watches "
                f"from {watch_file.name}"
            )

    def _load_prompts(self):
        """Load all triage prompt templates from prompts/ directory."""
        prompts_dir = self.config_dir / "prompts"
        if not prompts_dir.exists():
            logger.warning(f"prompts/ directory not found at {prompts_dir}")
            return
        for prompt_file in sorted(prompts_dir.glob("*.yaml")):
            # Extract product name: farafield_triage.yaml → farafield
            product_name = prompt_file.stem.replace("_triage", "")
            with open(prompt_file, "r") as f:
                data = yaml.safe_load(f) or {}
            self.prompts[product_name] = data
            logger.info(f"Loaded triage prompt from {prompt_file.name}")

    def _build_url_index(self):
        """Build a URL → watch config index for fast webhook lookup."""
        for product_name, watch_list in self.watches.items():
            for watch in watch_list:
                url = watch.get("url", "")
                if url:
                    self._url_index[url] = watch

    def get_watch_by_url(self, url: str) -> Optional[dict]:
        """Look up a watch configuration by URL.

        Args:
            url: The URL to look up (exact match).

        Returns:
            Watch config dict or None if not found.
        """
        return self._url_index.get(url)

    def get_product(self, product_name: str) -> Optional[dict]:
        """Get product configuration from domains.yaml.

        Args:
            product_name: Product key (e.g., 'farafield').

        Returns:
            Product config dict or None.
        """
        return self.products.get(product_name)

    def get_prompt(self, product_name: str) -> Optional[dict]:
        """Get triage prompt config for a product.

        Args:
            product_name: Product key (e.g., 'farafield').

        Returns:
            Prompt config dict with 'system' and 'template' keys, or None.
        """
        return self.prompts.get(product_name)

    def get_all_watches(self) -> dict[str, list[dict]]:
        """Return all watches grouped by product."""
        return self.watches

    def watch_count(self) -> int:
        """Total number of configured watches across all products."""
        return sum(len(w) for w in self.watches.values())


def load_config(config_dir: str = None) -> RegWatchConfig:
    """Load RegWatch configuration from the given directory.

    Args:
        config_dir: Path to config root. Defaults to the regwatch project root
                    (parent of the regwatch/ Python package).

    Returns:
        Populated RegWatchConfig instance.
    """
    if config_dir is None:
        # Default: two levels up from this file (regwatch/regwatch/config.py → regwatch/)
        config_dir = str(Path(__file__).parent.parent)
    return RegWatchConfig(config_dir)
