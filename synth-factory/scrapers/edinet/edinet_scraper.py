"""
EDINET scraper — high-level orchestrator implementing BaseScraper.

Connects the EDINET API client and parser into the standard scraper
pipeline that the synth-factory can consume.

Usage:
    from scrapers.edinet import EdinetScraper, EdinetConfig

    config = EdinetConfig(api_key="YOUR_KEY")
    scraper = EdinetScraper(config=config)

    # List + download + parse all annual reports filed on a date
    result = scraper.scrape(date="2026-01-15")

    # Or use the date range helper
    result = scraper.scrape_date_range("2026-01-01", "2026-01-31")
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..base.base_scraper import (
    BaseScraper,
    DocumentRecord,
    HttpClient,
    ScraperResult,
)
from .edinet_client import EdinetClient, EdinetConfig, EdinetDocumentInfo
from .edinet_parser import EdinetParser

logger = logging.getLogger(__name__)


class EdinetScraper(BaseScraper):
    """
    Scraper for EDINET (Electronic Disclosure for Investors' NETwork).

    Implements the BaseScraper interface to provide a uniform API
    for the synth-factory pipeline.

    Lifecycle:
        list_documents(date=...) → download_document(record) → parse_document(record)
    """

    def __init__(
        self,
        config: EdinetConfig | None = None,
        http_client: HttpClient | None = None,
        output_dir: Path = Path("output/scraped"),
        rate_limit_seconds: float = 1.0,
        max_retries: int = 3,
    ):
        super().__init__(
            source_name="edinet",
            http_client=http_client,
            output_dir=output_dir,
            rate_limit_seconds=rate_limit_seconds,
            max_retries=max_retries,
        )
        self.edinet_config = config or EdinetConfig()
        self.client = EdinetClient(config=self.edinet_config, http_client=self.http)
        self.parser = EdinetParser()

    # ── BaseScraper implementation ──────────────────────────────

    def list_documents(self, **kwargs) -> list[DocumentRecord]:
        """
        List available EDINET filings for a given date.

        Kwargs:
            date: str — YYYY-MM-DD format (required)

        Returns:
            List of DocumentRecord with metadata (no content yet).
        """
        date = kwargs.get("date")
        if not date:
            raise ValueError("EdinetScraper.list_documents requires 'date' kwarg")

        docs = self.client.list_documents_by_date(date)
        records = []
        for doc in docs:
            record = self._doc_info_to_record(doc)
            records.append(record)

        return records

    def download_document(self, record: DocumentRecord) -> DocumentRecord:
        """
        Download a single EDINET filing ZIP and extract contents.
        """
        try:
            files = self.client.download_document(
                doc_id=record.source_id,
                output_dir=self.output_dir / "raw",
            )
            record.downloaded = True
            record.download_path = str(self.output_dir / "raw" / record.source_id)
            record.file_size_bytes = sum(len(v) for v in files.values())
            record.content_format = "zip"
            # Store file map in metadata for the parser
            record.metadata["extracted_files"] = {
                name: len(content) for name, content in files.items()
            }
            # Store actual content for parsing (held in memory)
            record.metadata["_file_contents"] = files
        except Exception as e:
            record.error = str(e)
            logger.error(f"Download failed for {record.source_id}: {e}")

        return record

    def parse_document(self, record: DocumentRecord) -> DocumentRecord:
        """
        Parse downloaded EDINET filing into structured segments.
        """
        files = record.metadata.get("_file_contents")
        if not files:
            record.error = "No file contents available for parsing"
            return record

        try:
            parsed = self.parser.parse_zip_contents(
                files=files,
                doc_id=record.source_id,
            )

            record.segments = parsed.segments
            record.raw_content = parsed.full_text
            record.content_format = parsed.content_format
            record.parsed = parsed.parsed

            if parsed.error:
                record.error = parsed.error

            # Clean up in-memory file contents to save RAM
            record.metadata.pop("_file_contents", None)
            record.metadata["parse_summary"] = parsed.summary()

        except Exception as e:
            record.error = f"Parse failed: {e}"
            logger.error(f"Parse failed for {record.source_id}: {e}")

        return record

    # ── Extended methods ────────────────────────────────────────

    def scrape_date_range(
        self,
        start_date: str,
        end_date: str,
        download: bool = True,
        parse: bool = True,
    ) -> ScraperResult:
        """
        Scrape all filings across a date range.

        Iterates day-by-day (EDINET API requires single-date queries).

        Args:
            start_date: Start date (YYYY-MM-DD), inclusive.
            end_date: End date (YYYY-MM-DD), inclusive.
            download: Whether to download content.
            parse: Whether to parse content.

        Returns:
            Aggregated ScraperResult.
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        aggregate = ScraperResult(source_name="edinet")
        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            logger.info(f"Scraping EDINET for {date_str}")

            try:
                result = self.scrape(
                    download=download,
                    parse=parse,
                    date=date_str,
                )
                aggregate.total_listed += result.total_listed
                aggregate.total_downloaded += result.total_downloaded
                aggregate.total_parsed += result.total_parsed
                aggregate.total_errors += result.total_errors
                aggregate.errors.extend(result.errors)
            except Exception as e:
                logger.error(f"Failed to scrape {date_str}: {e}")
                aggregate.total_errors += 1
                aggregate.errors.append(f"{date_str}: {e}")

            current += timedelta(days=1)

        aggregate.started_at = start_date
        aggregate.finished_at = end_date

        logger.info(
            f"Date range scrape {start_date} to {end_date}: "
            f"listed={aggregate.total_listed}, "
            f"downloaded={aggregate.total_downloaded}, "
            f"parsed={aggregate.total_parsed}"
        )

        return aggregate

    def list_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> list[DocumentRecord]:
        """
        List (but don't download) all matching filings in a date range.

        Useful for assessing volume before committing to download.
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        all_records = []
        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            try:
                records = self.list_documents(date=date_str)
                all_records.extend(records)
            except Exception as e:
                logger.warning(f"Failed to list {date_str}: {e}")
            current += timedelta(days=1)

        return all_records

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _doc_info_to_record(doc: EdinetDocumentInfo) -> DocumentRecord:
        """Convert EDINET API response to universal DocumentRecord."""
        return DocumentRecord(
            source_id=doc.doc_id,
            source_name="edinet",
            title=doc.doc_description or doc.doc_type_label,
            language="ja",
            filing_date=doc.filing_date,
            document_type=doc.doc_type_code,
            document_type_label=doc.doc_type_label,
            filer_name=doc.filer_name,
            filer_code=doc.edinet_code,
            url=f"https://disclosure.edinet-fsa.go.jp/E01EW/BLMainServlet?"
                f"uji.verb=W1E62071InitDisplay&uji.bean=ee.bean.W1E62071.EEW1E62071Bean"
                f"&TID=2&PID=currentPage&SESSIONKEY=&lgKbn=2&dflg=0&iflg=0"
                f"&dispKbn=1&psr=1&pid=0&dte={doc.filing_date}",
            metadata={
                "edinet_code": doc.edinet_code,
                "ordinance_code": doc.ordinance_code,
                "form_code": doc.form_code,
                "period_start": doc.period_start,
                "period_end": doc.period_end,
                "submit_date_time": doc.submit_date_time,
            },
        )
