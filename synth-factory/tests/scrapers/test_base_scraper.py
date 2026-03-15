"""
Tests for the abstract BaseScraper and shared data types.

Run: pytest tests/scrapers/test_base_scraper.py -v
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base.base_scraper import (
    BaseScraper,
    DocumentRecord,
    HttpClient,
    HttpResponse,
    ScraperResult,
)


# ── Test DocumentRecord ─────────────────────────────────────────


def test_document_record_creation():
    """DocumentRecord can be created with minimal fields."""
    record = DocumentRecord(
        source_id="TEST-001",
        source_name="test",
        title="Test Document",
        language="ja",
        filing_date="2026-01-15",
        document_type="120",
        document_type_label="有価証券報告書",
    )
    assert record.source_id == "TEST-001"
    assert record.language == "ja"
    assert record.downloaded is False
    assert record.parsed is False
    assert record.segments == {}


def test_document_record_roundtrip():
    """DocumentRecord survives to_dict → from_dict round-trip."""
    original = DocumentRecord(
        source_id="TEST-002",
        source_name="edinet",
        title="テスト書類",
        language="ja",
        filing_date="2026-03-01",
        document_type="120",
        document_type_label="有価証券報告書",
        filer_name="テスト株式会社",
        segments={"overview": "会社概要テキスト"},
        downloaded=True,
        parsed=True,
    )
    data = original.to_dict()
    restored = DocumentRecord.from_dict(data)
    assert restored.source_id == original.source_id
    assert restored.filer_name == "テスト株式会社"
    assert restored.segments == {"overview": "会社概要テキスト"}
    assert restored.downloaded is True


def test_document_record_ignores_unknown_fields():
    """from_dict ignores fields not in the dataclass."""
    data = {
        "source_id": "X",
        "source_name": "test",
        "title": "T",
        "language": "en",
        "filing_date": "2026-01-01",
        "document_type": "999",
        "document_type_label": "Unknown",
        "unknown_field": "should be ignored",
    }
    record = DocumentRecord.from_dict(data)
    assert record.source_id == "X"
    assert not hasattr(record, "unknown_field")


# ── Test ScraperResult ──────────────────────────────────────────


def test_scraper_result_defaults():
    """ScraperResult has sensible defaults."""
    result = ScraperResult(source_name="test")
    assert result.total_listed == 0
    assert result.total_downloaded == 0
    assert result.errors == []


# ── Test HttpResponse ───────────────────────────────────────────


def test_http_response_json():
    """HttpResponse can parse JSON content."""
    resp = HttpResponse(
        status_code=200,
        content=b'{"key": "value"}',
    )
    assert resp.json() == {"key": "value"}


def test_http_response_text():
    """HttpResponse decodes bytes to text."""
    resp = HttpResponse(status_code=200, content="日本語テスト".encode("utf-8"))
    assert resp.text == "日本語テスト"


def test_http_response_raise_for_status():
    """raise_for_status raises on 4xx/5xx."""
    resp = HttpResponse(status_code=200, content=b"ok")
    resp.raise_for_status()  # Should not raise

    resp_err = HttpResponse(status_code=404, content=b"not found")
    try:
        resp_err.raise_for_status()
        assert False, "Should have raised"
    except Exception as e:
        assert "404" in str(e)


# ── Test Concrete Scraper ───────────────────────────────────────


class MockHttpClient:
    """Mock HTTP client for testing."""

    def __init__(self, responses: dict[str, HttpResponse] | None = None):
        self.responses = responses or {}
        self.requests: list[tuple[str, dict]] = []

    def get(self, url, params=None, headers=None, timeout=30.0):
        self.requests.append((url, params or {}))
        for pattern, resp in self.responses.items():
            if pattern in url:
                return resp
        return HttpResponse(status_code=404, content=b"Not found")


class TestScraper(BaseScraper):
    """Concrete test scraper for testing base class logic."""

    def __init__(self, records=None, **kwargs):
        super().__init__(source_name="test", **kwargs)
        self._records = records or []

    def list_documents(self, **kwargs):
        return self._records

    def download_document(self, record):
        record.downloaded = True
        record.raw_content = f"Content for {record.source_id}"
        return record

    def parse_document(self, record):
        record.parsed = True
        record.segments = {"main": record.raw_content}
        return record


def test_scraper_full_pipeline():
    """BaseScraper.scrape() runs list → download → parse."""
    records = [
        DocumentRecord(
            source_id=f"DOC-{i}",
            source_name="test",
            title=f"Doc {i}",
            language="en",
            filing_date="2026-01-01",
            document_type="test",
            document_type_label="Test",
        )
        for i in range(3)
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = TestScraper(
            records=records,
            output_dir=Path(tmpdir),
            rate_limit_seconds=0,
        )
        result = scraper.scrape(checkpoint=False)

    assert result.total_listed == 3
    assert result.total_downloaded == 3
    assert result.total_parsed == 3
    assert result.total_errors == 0


def test_scraper_checkpoint_resume():
    """Checkpoint file prevents re-downloading completed documents."""
    records = [
        DocumentRecord(
            source_id=f"DOC-{i}",
            source_name="test",
            title=f"Doc {i}",
            language="en",
            filing_date="2026-01-01",
            document_type="test",
            document_type_label="Test",
        )
        for i in range(5)
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = TestScraper(
            records=records,
            output_dir=Path(tmpdir),
            rate_limit_seconds=0,
        )

        # First run: process all 5
        result1 = scraper.scrape(checkpoint=True)
        assert result1.total_downloaded == 5

        # Second run: all should be skipped
        result2 = scraper.scrape(checkpoint=True)
        assert result2.total_downloaded == 0
        assert result2.total_listed == 5


def test_scraper_skip_download():
    """scrape(download=False) lists but doesn't download."""
    records = [
        DocumentRecord(
            source_id="DOC-1",
            source_name="test",
            title="Doc 1",
            language="en",
            filing_date="2026-01-01",
            document_type="test",
            document_type_label="Test",
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = TestScraper(
            records=records,
            output_dir=Path(tmpdir),
            rate_limit_seconds=0,
        )
        result = scraper.scrape(download=False, parse=False, checkpoint=False)

    assert result.total_listed == 1
    assert result.total_downloaded == 0
    assert result.total_parsed == 0
