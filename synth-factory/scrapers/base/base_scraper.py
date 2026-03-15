"""
Abstract base scraper for all data sources.

Every new data source (EDINET, J-PlatPat, UK tribunals, etc.) implements
this interface. This ensures consistent behavior across scrapers and lets
the synth-factory pipeline treat all sources uniformly.

Design principles:
- Resumable: track progress via checkpoint files
- Rate-limited: configurable delay between requests
- Testable: inject HTTP client for mocking
- Observable: structured logging + metrics
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Protocol

logger = logging.getLogger(__name__)


# ─── Data Transfer Objects ──────────────────────────────────────


@dataclass
class DocumentRecord:
    """
    A single document retrieved from a data source.

    This is the universal exchange format between scrapers and the
    synth-factory. Every scraper produces DocumentRecords; the pipeline
    consumes them regardless of source.
    """
    source_id: str                     # Source-specific unique ID (e.g., EDINET docID)
    source_name: str                   # Which scraper produced this (e.g., "edinet")
    title: str                         # Document title / description
    language: str                      # ISO 639-1 (ja, de, en)
    filing_date: str                   # ISO date string
    document_type: str                 # Source-specific type code
    document_type_label: str           # Human-readable type name
    filer_name: str = ""               # Company / person who filed
    filer_code: str = ""               # Source-specific filer identifier

    # Content — populated after download
    raw_content: str = ""              # Raw text extracted from filing
    segments: dict[str, str] = field(default_factory=dict)  # Parsed segments
    content_format: str = ""           # "xbrl", "html", "pdf", "text"

    # Metadata
    url: str = ""                      # Source URL for this document
    download_path: str = ""            # Local path where raw file was saved
    file_size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)  # Extra source-specific data

    # Processing state
    downloaded: bool = False
    parsed: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ScraperResult:
    """
    Result of a scrape run — metadata about what was fetched.
    """
    source_name: str
    started_at: str = ""
    finished_at: str = ""
    total_listed: int = 0              # Documents found in listing
    total_downloaded: int = 0          # Documents successfully downloaded
    total_parsed: int = 0              # Documents successfully parsed
    total_errors: int = 0
    checkpoint_path: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ─── HTTP Client Protocol ───────────────────────────────────────


class HttpClient(Protocol):
    """Protocol for injectable HTTP clients (for testing)."""

    def get(self, url: str, params: dict | None = None,
            headers: dict | None = None, timeout: float = 30.0) -> "HttpResponse":
        ...


@dataclass
class HttpResponse:
    """Simple HTTP response wrapper for testability."""
    status_code: int
    content: bytes
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.content)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HttpError(self.status_code, self.text[:500])


class HttpError(Exception):
    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


# ─── Real HTTP Client (thin wrapper around httpx) ──────────────


class RealHttpClient:
    """Production HTTP client using httpx."""

    def __init__(self, default_headers: dict[str, str] | None = None):
        self._default_headers = default_headers or {}

    def get(self, url: str, params: dict | None = None,
            headers: dict | None = None, timeout: float = 30.0) -> HttpResponse:
        import httpx
        merged = {**self._default_headers, **(headers or {})}
        resp = httpx.get(url, params=params, headers=merged, timeout=timeout)
        return HttpResponse(
            status_code=resp.status_code,
            content=resp.content,
            headers=dict(resp.headers),
        )


# ─── Abstract Base Scraper ──────────────────────────────────────


class BaseScraper(ABC):
    """
    Abstract base class for all data source scrapers.

    Subclasses implement:
    - list_documents(): discover available documents for a date/query
    - download_document(): fetch raw content for a single document
    - parse_document(): extract structured segments from raw content

    The base class provides:
    - Rate limiting
    - Checkpoint/resume support
    - Progress tracking
    - Error handling with continue-on-error semantics
    """

    def __init__(
        self,
        source_name: str,
        http_client: HttpClient | None = None,
        output_dir: Path = Path("output/scraped"),
        rate_limit_seconds: float = 1.0,
        max_retries: int = 3,
    ):
        self.source_name = source_name
        self.http = http_client or RealHttpClient()
        self.output_dir = Path(output_dir) / source_name
        self.rate_limit_seconds = rate_limit_seconds
        self.max_retries = max_retries
        self._last_request_time: float = 0.0

    # ── Abstract methods (subclasses must implement) ────────────

    @abstractmethod
    def list_documents(self, **kwargs) -> list[DocumentRecord]:
        """
        List available documents from the source.

        Returns lightweight DocumentRecord objects with metadata only
        (no content). The caller decides which ones to download.
        """
        ...

    @abstractmethod
    def download_document(self, record: DocumentRecord) -> DocumentRecord:
        """
        Download raw content for a single document.

        Populates record.raw_content, record.download_path, etc.
        Returns the updated record.
        """
        ...

    @abstractmethod
    def parse_document(self, record: DocumentRecord) -> DocumentRecord:
        """
        Parse raw content into structured segments.

        Populates record.segments with {segment_name: text} mapping.
        Returns the updated record.
        """
        ...

    # ── Orchestration (shared logic) ────────────────────────────

    def scrape(
        self,
        download: bool = True,
        parse: bool = True,
        checkpoint: bool = True,
        **list_kwargs,
    ) -> ScraperResult:
        """
        Full scrape pipeline: list → download → parse.

        Args:
            download: If True, download raw content for each document.
            parse: If True, parse downloaded content into segments.
            checkpoint: If True, save progress to checkpoint file.
            **list_kwargs: Passed to list_documents().

        Returns:
            ScraperResult with statistics.
        """
        result = ScraperResult(
            source_name=self.source_name,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load checkpoint if resuming
        completed_ids = set()
        checkpoint_path = self.output_dir / "checkpoint.jsonl"
        if checkpoint and checkpoint_path.exists():
            completed_ids = self._load_checkpoint(checkpoint_path)
            logger.info(f"Resuming: {len(completed_ids)} documents already processed")

        # 1. List
        logger.info(f"[{self.source_name}] Listing documents...")
        try:
            records = self.list_documents(**list_kwargs)
        except Exception as e:
            logger.error(f"[{self.source_name}] Listing failed: {e}")
            result.errors.append(f"list_documents: {e}")
            result.total_errors = 1
            result.finished_at = datetime.now(timezone.utc).isoformat()
            return result

        result.total_listed = len(records)
        logger.info(f"[{self.source_name}] Found {len(records)} documents")

        # Filter already-completed
        pending = [r for r in records if r.source_id not in completed_ids]
        logger.info(f"[{self.source_name}] {len(pending)} new documents to process")

        # 2. Download + Parse
        for i, record in enumerate(pending):
            try:
                if download:
                    self._rate_limit()
                    record = self._retry(lambda r=record: self.download_document(r))
                    result.total_downloaded += 1

                if parse and record.downloaded:
                    record = self.parse_document(record)
                    if record.parsed:
                        result.total_parsed += 1

                # Save checkpoint
                if checkpoint:
                    self._save_checkpoint_line(checkpoint_path, record)

            except Exception as e:
                logger.error(
                    f"[{self.source_name}] Error processing {record.source_id}: {e}"
                )
                record.error = str(e)
                result.total_errors += 1
                result.errors.append(f"{record.source_id}: {e}")

            if (i + 1) % 50 == 0:
                logger.info(
                    f"[{self.source_name}] Progress: {i + 1}/{len(pending)} "
                    f"(downloaded={result.total_downloaded}, "
                    f"parsed={result.total_parsed}, "
                    f"errors={result.total_errors})"
                )

        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.checkpoint_path = str(checkpoint_path)

        logger.info(
            f"[{self.source_name}] Scrape complete: "
            f"listed={result.total_listed}, downloaded={result.total_downloaded}, "
            f"parsed={result.total_parsed}, errors={result.total_errors}"
        )

        return result

    # ── Rate limiting ───────────────────────────────────────────

    def _rate_limit(self) -> None:
        """Enforce minimum delay between requests."""
        if self.rate_limit_seconds <= 0:
            return
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_time = time.time()

    # ── Retry logic ─────────────────────────────────────────────

    def _retry(self, fn, retries: int | None = None):
        """Retry a function with exponential backoff."""
        max_retries = retries or self.max_retries
        last_error = None
        for attempt in range(max_retries):
            try:
                return fn()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(
                        f"[{self.source_name}] Retry {attempt + 1}/{max_retries} "
                        f"after {delay}s: {e}"
                    )
                    time.sleep(delay)
        raise last_error

    # ── Checkpoint persistence ──────────────────────────────────

    @staticmethod
    def _load_checkpoint(path: Path) -> set[str]:
        """Load set of completed source_ids from checkpoint file."""
        ids = set()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    sid = record.get("source_id")
                    if sid:
                        ids.add(sid)
                except json.JSONDecodeError:
                    continue
        return ids

    @staticmethod
    def _save_checkpoint_line(path: Path, record: DocumentRecord) -> None:
        """Append one completed record to the checkpoint JSONL file."""
        # Save metadata only (not full raw_content) to keep checkpoints small
        checkpoint_data = {
            "source_id": record.source_id,
            "title": record.title,
            "filing_date": record.filing_date,
            "document_type": record.document_type,
            "filer_name": record.filer_name,
            "downloaded": record.downloaded,
            "parsed": record.parsed,
            "error": record.error,
            "download_path": record.download_path,
            "segment_count": len(record.segments),
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(checkpoint_data, ensure_ascii=False) + "\n")
