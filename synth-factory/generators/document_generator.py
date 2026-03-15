"""
Long-text document generation via segment-based LLM calls.

This module generates entire documents (housing forms, compliance reports,
immigration applications) by breaking them into ordered segments, generating
each segment with context from prior segments, and assembling the result.

Key design principles:
- Segment-based: each section gets its own LLM call (quality over speed)
- Context threading: later segments see earlier segments for coherence
- Config-driven: new document types = new YAML configs, no code changes
- Resumable: progress saved per-document to JSONL; interrupted runs pick up
  where they left off
- Language-agnostic: German and Japanese are first-class via prompt engineering

Architecture:
    DocumentContext   — tracks generated segments for coherence within one doc
    DocumentAssembler — combines segments into formatted output
    DocumentGenerator — orchestrates async generation with Ollama
"""

from __future__ import annotations
import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import pandas as pd

from .config_schema import (
    DatasetConfig,
    DocumentTableDef,
    DocumentTypeDef,
    SegmentDef,
    SegmentType,
)

logger = logging.getLogger(__name__)


# ─── Flaw Taxonomy Integration ──────────────────────────────────

# Quality tiers map a human-readable label to an error_injection_rate.
# Used by generate_edinet.py to produce temperature-controlled datasets.
QUALITY_TIERS = {
    "perfect":   0.00,   # Zero flaws — pristine documentation
    "near":      0.03,   # 3% of documents get a realistic error
    "moderate":  0.12,   # 12% — noticeable noise
    "severe":    0.30,   # 30% — "land you in a lawsuit or five"
}

# Mixed-flaw distribution: within a single dataset, different documents
# get different severity tiers.  Values = fraction of total records.
DEFAULT_MIXED_DISTRIBUTION = {
    "perfect":  0.80,   # 80% clean
    "near":     0.10,   # 10% lightly flawed
    "moderate": 0.08,   # 8% moderately flawed
    "severe":   0.02,   # 2% severely flawed
}


class TaxonomyErrorInjector:
    """
    Taxonomy-aware error injector that replaces the naive random injector.

    Instead of picking uniformly from [truncate, missing, encoding, duplicate],
    this selects flaw types weighted by their real-world frequency from
    flaw_taxonomy.json.  Falls back to the original naive approach when
    no taxonomy is loaded.
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        self.taxonomy = None
        self._category_weights: list[tuple[dict, float]] = []
        if taxonomy_path:
            self._load_taxonomy(taxonomy_path)

    def _load_taxonomy(self, path_str: str) -> None:
        """Load flaw taxonomy JSON and build weighted selection table."""
        path = Path(path_str)
        if not path.exists():
            logger.warning(f"Flaw taxonomy not found at {path} — using naive injection")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.taxonomy = data
            # Build weighted list from categories
            for cat in data.get("categories", []):
                freq = cat.get("frequency", 0.01)
                self._category_weights.append((cat, freq))
            logger.info(
                f"Loaded flaw taxonomy: {len(self._category_weights)} categories "
                f"from {data.get('total_documents_analyzed', '?')} analyzed docs"
            )
        except Exception as e:
            logger.warning(f"Failed to load flaw taxonomy: {e}")

    @property
    def is_loaded(self) -> bool:
        return self.taxonomy is not None and len(self._category_weights) > 0

    def select_flaw(self, segment_name: str) -> Optional[dict]:
        """
        Select a flaw category weighted by real-world frequency.

        Prefers flaws that target the given segment, but allows
        segment-agnostic flaws too.
        """
        if not self._category_weights:
            return None

        # Separate segment-specific and generic flaws
        segment_cats = [
            (cat, w) for cat, w in self._category_weights
            if cat.get("segment", "") in ("", segment_name)
        ]
        if not segment_cats:
            segment_cats = self._category_weights

        cats, weights = zip(*segment_cats)
        total = sum(weights)
        if total == 0:
            return random.choice(cats)
        normalized = [w / total for w in weights]
        return random.choices(cats, weights=normalized, k=1)[0]

    def inject(self, content: str, segment_name: str, language: str) -> str:
        """
        Inject a taxonomy-driven flaw into content.

        Maps flaw_type/flaw_subtype from the taxonomy to concrete
        text mutations.  Falls back to naive injection for unknown types.
        """
        flaw = self.select_flaw(segment_name)
        if not flaw:
            return _naive_inject_error(content, language)

        flaw_type = flaw.get("flaw_type", "")
        subtype = flaw.get("flaw_subtype", "")
        severity = flaw.get("severity", "medium")

        # Map taxonomy categories to concrete mutations
        if flaw_type == "structural":
            if subtype == "empty_section":
                placeholders = {
                    "ja": ["該当事項はありません", "（未記入）", ""],
                    "de": ["Nicht zutreffend.", "(nicht ausgefüllt)", ""],
                }
                return random.choice(placeholders.get(language, ["[N/A]", ""]))
            elif subtype in ("suspiciously_short", "stale_reference"):
                # Truncate to 10-40% of content
                cut = int(len(content) * random.uniform(0.1, 0.4))
                return content[:max(cut, 20)]
            elif subtype == "missing_section":
                return ""

        elif flaw_type == "numerical":
            if subtype == "potential_duplicate_figure":
                # Duplicate a number-like substring
                import re as _re
                nums = list(_re.finditer(r'[\d,]+', content))
                if nums:
                    m = random.choice(nums)
                    pos = m.end()
                    return content[:pos] + m.group() + content[pos:]
            # Fallback for other numerical flaws
            return content

        elif flaw_type == "disclosure":
            if subtype == "generic_language":
                # Prepend a vague hedge
                hedges = {
                    "ja": "一般的に、",
                    "de": "Im Allgemeinen ",
                }
                return hedges.get(language, "Generally, ") + content
            elif subtype == "boilerplate_risk":
                boilerplate = {
                    "ja": "為替変動リスク、金利変動リスク、及び自然災害リスクが存在します。",
                    "de": "Es bestehen Risiken durch Wechselkursschwankungen, Zinsschwankungen und Naturkatastrophen.",
                }
                return boilerplate.get(language, content)

        elif flaw_type == "formatting":
            if subtype == "garbled_symbols":
                chars = list(content)
                garble_count = max(2, len(chars) // 30)
                garble_chars = "□■◆◇▲△▽▼●○★☆♦♣♠♥"
                for _ in range(garble_count):
                    if chars:
                        pos = random.randint(0, len(chars) - 1)
                        chars[pos] = random.choice(garble_chars)
                return "".join(chars)
            elif subtype == "mojibake":
                # Insert mojibake sequences
                mojibake = ["â€", "ã€", "Ã¤", "Ã¶", "Ã¼", "â€™"]
                chars = list(content)
                for _ in range(random.randint(2, 5)):
                    if chars:
                        pos = random.randint(0, max(0, len(chars) - 1))
                        chars[pos] = random.choice(mojibake)
                return "".join(chars)
            elif subtype == "control_characters":
                chars = list(content)
                for _ in range(random.randint(1, 3)):
                    if chars:
                        pos = random.randint(0, len(chars) - 1)
                        chars[pos] = chr(random.randint(0x01, 0x08))
                return "".join(chars)

        elif flaw_type == "temporal":
            # Insert a stale date reference
            stale = {
                "ja": "令和3年3月31日現在",
                "de": "(Stand: 31.03.2021)",
            }
            return content + " " + stale.get(language, "(as of 2021-03-31)")

        # Fallback: use severity to scale naive injection
        return _naive_inject_error(content, language)


# ─── Document Context ────────────────────────────────────────────

class DocumentContext:
    """
    Tracks generated segments for a single document to maintain coherence.

    As each segment is generated, its output is stored here. Later segments
    can reference earlier ones via context_dependencies, which injects the
    prior text into the prompt template.
    """

    def __init__(
        self,
        document_id: str,
        seed_data: Optional[dict[str, str]] = None,
    ):
        self.document_id = document_id
        self.segments: dict[str, str] = {}
        self.seed_data = seed_data or {}

    def add_segment(self, name: str, content: str) -> None:
        """Record a generated segment."""
        self.segments[name] = content

    def get_context(self, dependency_names: list[str]) -> str:
        """
        Build context string from previously generated segments.

        Returns concatenated text of referenced segments, separated by
        newlines. Used for injecting into the next segment's prompt.
        """
        parts = []
        for name in dependency_names:
            if name in self.segments:
                parts.append(self.segments[name])
            else:
                logger.warning(
                    f"Context dependency '{name}' not found in document "
                    f"{self.document_id} — skipping"
                )
        return "\n\n".join(parts)

    def get_prompt_vars(self) -> dict[str, str]:
        """
        Build a dict of all available template variables.

        Includes:
        - document_id
        - All seed data columns (e.g., applicant_name, birth_date)
        - All previously generated segment names → their content
        """
        variables = {"document_id": self.document_id}
        variables.update(self.seed_data)
        variables.update(self.segments)
        return variables


# ─── Document Assembler ──────────────────────────────────────────

class DocumentAssembler:
    """
    Combine generated segments into a final formatted document.

    Supports markdown, JSON, and plain text output formats.
    """

    @staticmethod
    def assemble(
        segments: dict[str, str],
        doc_type: DocumentTypeDef,
        context: DocumentContext,
    ) -> str:
        """
        Assemble segments into a complete document.

        Args:
            segments: {segment_name: generated_text}
            doc_type: Document type definition with format and preamble.
            context: Document context (for preamble variable interpolation).

        Returns:
            Formatted document string.
        """
        fmt = doc_type.format.lower()
        if fmt == "json":
            return DocumentAssembler._assemble_json(segments, doc_type, context)
        elif fmt == "plain":
            return DocumentAssembler._assemble_plain(segments, doc_type, context)
        else:
            return DocumentAssembler._assemble_markdown(segments, doc_type, context)

    @staticmethod
    def _assemble_markdown(
        segments: dict[str, str],
        doc_type: DocumentTypeDef,
        context: DocumentContext,
    ) -> str:
        parts = []

        # Preamble
        if doc_type.preamble:
            try:
                preamble = doc_type.preamble.format(**context.get_prompt_vars())
            except KeyError:
                preamble = doc_type.preamble
            parts.append(preamble)
            parts.append("")

        # Segments in definition order
        for seg_def in doc_type.segments:
            if seg_def.name not in segments:
                continue
            content = segments[seg_def.name]

            if seg_def.label:
                parts.append(f"### {seg_def.label}")
                parts.append("")
            parts.append(content)
            parts.append("")
            parts.append("---")
            parts.append("")

        return "\n".join(parts).rstrip("\n- ")

    @staticmethod
    def _assemble_json(
        segments: dict[str, str],
        doc_type: DocumentTypeDef,
        context: DocumentContext,
    ) -> str:
        doc = {
            "document_id": context.document_id,
            "document_type": doc_type.name,
            "language": doc_type.language,
            "segments": {},
        }
        for seg_def in doc_type.segments:
            if seg_def.name in segments:
                doc["segments"][seg_def.name] = {
                    "label": seg_def.label,
                    "content": segments[seg_def.name],
                }
        return json.dumps(doc, ensure_ascii=False, indent=2)

    @staticmethod
    def _assemble_plain(
        segments: dict[str, str],
        doc_type: DocumentTypeDef,
        context: DocumentContext,
    ) -> str:
        parts = []
        if doc_type.preamble:
            try:
                parts.append(doc_type.preamble.format(**context.get_prompt_vars()))
            except KeyError:
                parts.append(doc_type.preamble)
            parts.append("")

        for seg_def in doc_type.segments:
            if seg_def.name not in segments:
                continue
            if seg_def.label:
                parts.append(f"[{seg_def.label}]")
            parts.append(segments[seg_def.name])
            parts.append("")

        return "\n".join(parts).rstrip()


# ─── Document Generator ─────────────────────────────────────────

class DocumentGenerator:
    """
    Orchestrate segment-based document generation with Ollama.

    For each record:
    1. Create a DocumentContext
    2. Generate each segment in order, threading context from prior segments
    3. Assemble into final document
    4. Save progress incrementally (resumability)

    Reuses the same Ollama API pattern as OllamaAugmenter but at the
    document level rather than the cell level.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        max_concurrent: int = 2,
        timeout: float = 180.0,
        max_retries: int = 3,
        taxonomy_path: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self._taxonomy_injector = TaxonomyErrorInjector(taxonomy_path)

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

    def generate_table(
        self,
        doc_table_def: DocumentTableDef,
        doc_types_map: dict[str, DocumentTypeDef],
        config: DatasetConfig,
        seed_df: Optional[pd.DataFrame] = None,
        progress_callback=None,
        resume_from: Optional[Path] = None,
    ) -> pd.DataFrame:
        """
        Generate a table of documents.

        Args:
            doc_table_def: Table definition (how many records, which doc type).
            doc_types_map: {name: DocumentTypeDef} for lookup.
            config: Full dataset config.
            seed_df: Optional DataFrame to pull seed context from.
            progress_callback: Optional callable(completed, total).
            resume_from: Path to .progress.jsonl for resuming interrupted runs.

        Returns:
            DataFrame with columns:
            - document_id (str)
            - document_content (str, full assembled document)
            - One column per segment (str, individual segment text)
        """
        doc_type = doc_types_map.get(doc_table_def.document_type)
        if not doc_type:
            raise ValueError(
                f"Document type '{doc_table_def.document_type}' not found. "
                f"Available: {list(doc_types_map.keys())}"
            )

        return asyncio.run(
            self._generate_all(
                doc_table_def, doc_type, config,
                seed_df, progress_callback, resume_from,
            )
        )

    async def _generate_all(
        self,
        doc_table_def: DocumentTableDef,
        doc_type: DocumentTypeDef,
        config: DatasetConfig,
        seed_df: Optional[pd.DataFrame],
        progress_callback,
        resume_from: Optional[Path],
    ) -> pd.DataFrame:
        """Async orchestration of all document generation."""
        total = doc_table_def.records
        segment_names = [s.name for s in doc_type.segments]

        # Load progress if resuming
        completed_docs: dict[str, dict] = {}
        if resume_from and resume_from.exists():
            completed_docs = self._load_progress(resume_from)
            logger.info(
                f"Resuming: {len(completed_docs)} documents already generated"
            )

        # Prepare progress file
        progress_path = resume_from
        if not progress_path:
            progress_dir = Path("output") / config.metadata.name / ".progress"
            progress_dir.mkdir(parents=True, exist_ok=True)
            progress_path = progress_dir / f"{doc_table_def.name}.jsonl"

        progress_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare seed data lookup
        seed_rows = None
        if seed_df is not None and doc_table_def.seed_columns:
            seed_cols = [
                c for c in doc_table_def.seed_columns if c in seed_df.columns
            ]
            seed_rows = seed_df[seed_cols] if seed_cols else None

        records = []
        generated_count = len(completed_docs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(total):
                doc_id = f"DOC-{i + 1:06d}"

                # Skip if already generated (resume mode)
                if doc_id in completed_docs:
                    records.append(completed_docs[doc_id])
                    continue

                # Build seed data for this document
                seed_data = {}
                if seed_rows is not None and i < len(seed_rows):
                    seed_data = {
                        k: str(v) for k, v in seed_rows.iloc[i].to_dict().items()
                    }

                context = DocumentContext(doc_id, seed_data)

                # Generate all segments in order
                doc_start = time.time()
                segments = await self._generate_document(
                    client, doc_type, context, config
                )

                # Assemble final document
                assembled = DocumentAssembler.assemble(segments, doc_type, context)

                # Build row
                row = {
                    "document_id": doc_id,
                    "document_content": assembled,
                }
                for seg_name in segment_names:
                    row[f"seg_{seg_name}"] = segments.get(seg_name, "")

                records.append(row)
                generated_count += 1

                # Save progress incrementally
                self._save_progress_line(progress_path, row)

                elapsed = time.time() - doc_start

                # Calculate ETA based on rolling average
                if not hasattr(self, '_doc_times'):
                    self._doc_times = []
                self._doc_times.append(elapsed)
                # Keep last 20 for rolling average
                if len(self._doc_times) > 20:
                    self._doc_times = self._doc_times[-20:]
                avg_time = sum(self._doc_times) / len(self._doc_times)
                remaining = total - generated_count
                eta_seconds = remaining * avg_time
                eta_str = _format_eta(eta_seconds)

                logger.info(
                    f"Document {doc_id} generated in {elapsed:.1f}s "
                    f"({generated_count}/{total} | "
                    f"avg {avg_time:.1f}s/doc | ETA: {eta_str})"
                )

                if progress_callback:
                    progress_callback(generated_count, total)

        # Build DataFrame
        df = pd.DataFrame(records)

        # Clean up progress file on successful completion
        if progress_path.exists() and generated_count == total:
            logger.info(f"All {total} documents generated — removing progress file")
            progress_path.unlink()
            # Remove .progress dir if empty
            try:
                progress_path.parent.rmdir()
            except OSError:
                pass

        return df

    async def _generate_document(
        self,
        client: httpx.AsyncClient,
        doc_type: DocumentTypeDef,
        context: DocumentContext,
        config: DatasetConfig,
    ) -> dict[str, str]:
        """
        Generate all segments for a single document.

        Segments are generated in definition order. Each segment can
        reference prior segments via context_dependencies.

        If error_injection_rate > 0, a fraction of documents will have
        realistic errors injected (missing fields, truncation, typos)
        to simulate real-world OCR and data entry imperfections.
        """
        segments: dict[str, str] = {}
        inject_errors = (
            doc_type.error_injection_rate > 0
            and random.random() < doc_type.error_injection_rate
        )

        for seg_def in doc_type.segments:
            if seg_def.segment_type == SegmentType.LIST_FIELD:
                content = await self._generate_list_segment(
                    client, seg_def, context, config
                )
            else:
                content = await self._generate_segment(
                    client, seg_def, context, config
                )

            # Apply error injection to this segment (if selected for this doc)
            if inject_errors:
                content = self._inject_error(
                    content, seg_def, doc_type.language,
                    use_taxonomy=doc_type.use_taxonomy_errors,
                )

            segments[seg_def.name] = content
            context.add_segment(seg_def.name, content)

        return segments

    def _inject_error(
        self,
        content: str,
        seg_def: SegmentDef,
        language: str,
        use_taxonomy: bool = False,
    ) -> str:
        """
        Inject a realistic error into segment content.

        If the taxonomy injector is loaded and use_taxonomy=True, errors
        are selected weighted by real-world flaw frequencies from
        flaw_taxonomy.json.  Otherwise falls back to naive random injection.

        Only one error type is applied per segment, and not every segment
        in an error-injected document gets an error (50% chance per segment).
        """
        # 50% chance to skip this particular segment
        if random.random() > 0.5:
            return content

        if use_taxonomy and self._taxonomy_injector.is_loaded:
            return self._taxonomy_injector.inject(content, seg_def.name, language)

        return _naive_inject_error(content, language)

    async def _generate_segment(
        self,
        client: httpx.AsyncClient,
        seg_def: SegmentDef,
        context: DocumentContext,
        config: DatasetConfig,
    ) -> str:
        """Generate a single SECTION or FORM_FIELD segment."""
        prompt = self._build_segment_prompt(seg_def, context)
        model = seg_def.model or config.generation.ollama_default_model

        result = await self._call_ollama(
            client, model, prompt,
            seg_def.system_prompt, seg_def.temperature, seg_def.max_tokens,
        )
        return result

    async def _generate_list_segment(
        self,
        client: httpx.AsyncClient,
        seg_def: SegmentDef,
        context: DocumentContext,
        config: DatasetConfig,
    ) -> str:
        """
        Generate a LIST_FIELD segment with multiple items.

        Each item is generated individually with context from prior items,
        then joined into a single string.
        """
        min_items = seg_def.list_min or 1
        max_items = seg_def.list_max or 3
        count = random.randint(min_items, max_items)

        model = seg_def.model or config.generation.ollama_default_model
        items = []

        for item_idx in range(count):
            # Build prompt with context + prior items in this list
            prompt_vars = context.get_prompt_vars()
            prompt_vars["count"] = str(count)
            prompt_vars["item_number"] = str(item_idx + 1)

            # Inject previously generated items from THIS list for coherence
            if items:
                prompt_vars[seg_def.name] = "\n".join(items)
            else:
                prompt_vars[seg_def.name] = "(first entry)"

            try:
                prompt = seg_def.prompt.format(**prompt_vars)
            except KeyError as e:
                logger.warning(f"Missing prompt variable {e} in list segment {seg_def.name}")
                prompt = seg_def.prompt

            result = await self._call_ollama(
                client, model, prompt,
                seg_def.system_prompt, seg_def.temperature, seg_def.max_tokens,
            )
            items.append(result)

        return "\n\n".join(items)

    def _build_segment_prompt(
        self,
        seg_def: SegmentDef,
        context: DocumentContext,
    ) -> str:
        """
        Build the final prompt for a segment by injecting all available variables.

        Available variables in prompts:
        - {document_id} — the document ID
        - {segment_name} — content of any prior segment by name
        - {seed_column} — any seed data column value
        """
        prompt_vars = context.get_prompt_vars()
        try:
            return seg_def.prompt.format(**prompt_vars)
        except KeyError as e:
            logger.warning(
                f"Missing prompt variable {e} in segment {seg_def.name} "
                f"of document {context.document_id}"
            )
            return seg_def.prompt

    async def _call_ollama(
        self,
        client: httpx.AsyncClient,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Call Ollama API with retry logic.

        Same pattern as OllamaAugmenter._generate_one() but without
        semaphore (documents are generated sequentially per-document,
        not in parallel, to preserve segment ordering).
        """
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

                logger.warning(f"Empty Ollama response, attempt {attempt + 1}")

            except httpx.TimeoutException:
                logger.warning(f"Ollama timeout, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama HTTP error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return f"[GENERATION_FAILED_AFTER_{self.max_retries}_RETRIES]"

    # ─── Progress / Resumability ─────────────────────────────────

    @staticmethod
    def _save_progress_line(path: Path, row: dict) -> None:
        """Append one completed document to the progress JSONL file."""
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    @staticmethod
    def _load_progress(path: Path) -> dict[str, dict]:
        """
        Load completed documents from a progress JSONL file.

        Returns {document_id: row_dict} for all previously completed docs.
        """
        completed = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    doc_id = row.get("document_id")
                    if doc_id:
                        completed[doc_id] = row
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading progress file {path}: {e}")
        return completed


# ─── Naive Error Injection (fallback) ────────────────────────────

def _naive_inject_error(content: str, language: str) -> str:
    """
    Original naive error injector: uniform random over 4 error types.

    Used when no flaw taxonomy is loaded.
    """
    error_type = random.choice(["truncate", "missing", "encoding", "duplicate"])

    if error_type == "truncate":
        cut_point = int(len(content) * random.uniform(0.4, 0.7))
        space_idx = content.rfind(" ", 0, cut_point)
        if space_idx > cut_point * 0.3:
            cut_point = space_idx
        return content[:cut_point]

    elif error_type == "missing":
        placeholders = {
            "ja": ["（未記入）", "＿＿＿＿＿", "※記入漏れ", ""],
            "de": ["(nicht ausgefüllt)", "_____", "[FEHLT]", ""],
        }
        options = placeholders.get(language, ["[MISSING]", "", "_____"])
        return random.choice(options)

    elif error_type == "encoding":
        chars = list(content)
        garble_count = max(1, len(chars) // 50)
        garble_chars = "□■◆◇▲△▽▼●○★☆♦♣♠♥"
        for _ in range(garble_count):
            pos = random.randint(0, len(chars) - 1)
            chars[pos] = random.choice(garble_chars)
        return "".join(chars)

    elif error_type == "duplicate":
        if len(content) < 30:
            return content
        start = random.randint(0, len(content) // 2)
        max_len = max(11, min(50, len(content) // 3))
        length = random.randint(10, max_len)
        chunk = content[start:start + length]
        insert_at = random.randint(
            min(start + length, len(content)),
            len(content),
        )
        return content[:insert_at] + chunk + content[insert_at:]

    return content


# ─── Helpers ─────────────────────────────────────────────────────

def _format_eta(seconds: float) -> str:
    """Format seconds into a human-readable ETA string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s}s"
    elif seconds < 86400:
        h, remainder = divmod(int(seconds), 3600)
        m, _ = divmod(remainder, 60)
        return f"{h}h {m}m"
    else:
        d, remainder = divmod(int(seconds), 86400)
        h, _ = divmod(remainder, 3600)
        return f"{d}d {h}h"
