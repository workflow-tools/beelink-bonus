"""
LLM text augmentation via Ollama.

After tabular generation produces a DataFrame with placeholder text columns,
this module replaces those placeholders with LLM-generated text using Ollama.

The augmenter:
1. Identifies columns marked with generator: ollama
2. For each row, builds a prompt using the column's OllamaConfig
3. Optionally injects context from other columns (e.g., {branche} in the prompt)
4. Calls the local Ollama API with concurrency control
5. Replaces placeholder values with generated text

This is the slow step — a 70B model generates ~8-15 tok/s on the Beelink.
Budget ~2-5 seconds per cell. 50K rows × 3 text columns = ~40-80 hours on 70B.
Use 7B for volume, 70B for premium quality.

Extensibility: Add new augmentation strategies by subclassing BaseAugmenter.
"""

from __future__ import annotations
import asyncio
import logging
import time
from typing import Optional

import httpx
import pandas as pd

from .config_schema import DatasetConfig, TableDef, ColumnDef, TextGenerator

logger = logging.getLogger(__name__)


class OllamaAugmenter:
    """Augment DataFrame text columns using Ollama LLM inference."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        max_concurrent: int = 2,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self._semaphore: Optional[asyncio.Semaphore] = None

    def augment_table(
        self,
        df: pd.DataFrame,
        table_def: TableDef,
        config: DatasetConfig,
        progress_callback=None,
    ) -> pd.DataFrame:
        """
        Replace placeholder text columns with LLM-generated content.

        Args:
            df: DataFrame with placeholder values.
            table_def: Table schema definition.
            config: Full dataset config.
            progress_callback: Optional callable(completed, total) for progress.

        Returns:
            DataFrame with LLM-generated text columns.
        """
        ollama_columns = [
            col for col in table_def.columns
            if col.generator == TextGenerator.OLLAMA and col.ollama
        ]

        if not ollama_columns:
            logger.info("No Ollama columns to augment")
            return df

        logger.info(
            f"Augmenting {len(ollama_columns)} columns × {len(df)} rows "
            f"using Ollama (max_concurrent={self.max_concurrent})"
        )

        # Run async augmentation
        return asyncio.run(
            self._augment_async(df, ollama_columns, config, progress_callback)
        )

    async def _augment_async(
        self,
        df: pd.DataFrame,
        columns: list[ColumnDef],
        config: DatasetConfig,
        progress_callback,
    ) -> pd.DataFrame:
        """Async implementation of augmentation with concurrency control."""
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        total_cells = len(df) * len(columns)
        completed = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for col_def in columns:
                logger.info(f"Augmenting column: {col_def.name}")
                ollama_cfg = col_def.ollama
                model = ollama_cfg.model or config.generation.ollama_default_model

                # Build all prompts for this column
                tasks = []
                for idx, row in df.iterrows():
                    prompt = self._build_prompt(ollama_cfg.prompt, row, ollama_cfg.context_columns)
                    tasks.append(self._generate_one(
                        client, model, prompt,
                        ollama_cfg.system_prompt,
                        ollama_cfg.temperature,
                        ollama_cfg.max_tokens,
                        idx,
                    ))

                # Execute with concurrency control
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Apply results
                for idx, result in zip(df.index, results):
                    if isinstance(result, Exception):
                        logger.error(f"Row {idx}, column {col_def.name}: {result}")
                        df.at[idx, col_def.name] = f"[GENERATION_ERROR: {type(result).__name__}]"
                    else:
                        df.at[idx, col_def.name] = result

                    completed += 1
                    if progress_callback and completed % 100 == 0:
                        progress_callback(completed, total_cells)

        return df

    async def _generate_one(
        self,
        client: httpx.AsyncClient,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        row_idx: int,
    ) -> str:
        """Generate text for a single cell with retry logic."""
        async with self._semaphore:
            for attempt in range(self.max_retries):
                try:
                    payload = {
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    }
                    if system_prompt:
                        payload["system"] = system_prompt

                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                    )
                    response.raise_for_status()
                    result = response.json()
                    text = result.get("response", "").strip()

                    if text:
                        return text

                    logger.warning(f"Empty response for row {row_idx}, attempt {attempt + 1}")

                except httpx.TimeoutException:
                    logger.warning(f"Timeout for row {row_idx}, attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)

                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error for row {row_idx}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)

            return f"[GENERATION_FAILED_AFTER_{self.max_retries}_RETRIES]"

    @staticmethod
    def _build_prompt(
        template: str,
        row: pd.Series,
        context_columns: list[str],
    ) -> str:
        """
        Build a prompt by injecting context from other columns.

        Example template: "Generate a German company name in the {branche} sector"
        If the row has branche="Maschinenbau", the prompt becomes:
        "Generate a German company name in the Maschinenbau sector"
        """
        context = {}
        for col in context_columns:
            if col in row.index:
                context[col] = str(row[col])

        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing context column in prompt template: {e}")
            return template

    def check_health(self) -> dict:
        """Check if Ollama is running and which models are available."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"status": "healthy", "models": models}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class TemplateAugmenter:
    """
    Fill template-based text columns using values from other columns.

    Example: template="{firma_name} {rechtsform}"
    With firma_name="Müller Maschinenbau" and rechtsform="GmbH",
    produces: "Müller Maschinenbau GmbH"
    """

    @staticmethod
    def augment_table(df: pd.DataFrame, table_def: TableDef) -> pd.DataFrame:
        """Fill template columns using other column values."""
        template_columns = [
            col for col in table_def.columns
            if col.generator == TextGenerator.TEMPLATE and col.template
        ]

        for col_def in template_columns:
            df[col_def.name] = df.apply(
                lambda row: col_def.template.format(**row.to_dict()),
                axis=1,
            )

        return df
