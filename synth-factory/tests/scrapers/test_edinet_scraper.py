"""
Tests for the EDINET scraper (high-level orchestrator).

Run: pytest tests/scrapers/test_edinet_scraper.py -v
"""

import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base.base_scraper import HttpResponse
from scrapers.edinet.edinet_client import EdinetConfig
from scrapers.edinet.edinet_scraper import EdinetScraper


# ── Mock HTTP Client ────────────────────────────────────────────


class MockScraperHttp:
    """Mock HTTP client for full scraper pipeline testing."""

    def __init__(self):
        self.requests: list[tuple[str, dict]] = []

    def get(self, url, params=None, headers=None, timeout=30.0):
        self.requests.append((url, params or {}))

        # Listing endpoint
        if "documents.json" in url:
            return self._listing_response(params or {})

        # Download endpoint
        if "/documents/" in url and "documents.json" not in url:
            return self._download_response()

        return HttpResponse(status_code=404, content=b"Not found")

    def _listing_response(self, params: dict) -> HttpResponse:
        """Return mock listing with 2 securities reports."""
        body = {
            "metadata": {"status": "200", "message": "OK"},
            "results": [
                {
                    "docID": "S100MOCK01",
                    "edinetCode": "E00001",
                    "filerName": "テスト工業株式会社",
                    "docTypeCode": "120",
                    "docDescription": "有価証券報告書",
                    "filingDate": params.get("date", "2026-01-15"),
                    "submitDateTime": "2026-01-15 09:00",
                    "ordinanceCode": "010",
                    "formCode": "030000",
                    "periodStart": "2025-04-01",
                    "periodEnd": "2025-12-31",
                    "withdrawalStatus": "0",
                },
                {
                    "docID": "S100MOCK02",
                    "edinetCode": "E00002",
                    "filerName": "サンプル電機株式会社",
                    "docTypeCode": "120",
                    "docDescription": "有価証券報告書",
                    "filingDate": params.get("date", "2026-01-15"),
                    "submitDateTime": "2026-01-15 10:00",
                    "ordinanceCode": "010",
                    "formCode": "030000",
                    "periodStart": "2025-04-01",
                    "periodEnd": "2025-12-31",
                    "withdrawalStatus": "0",
                },
                {
                    "docID": "S100MOCK03",
                    "edinetCode": "E00003",
                    "filerName": "別の会社",
                    "docTypeCode": "140",  # Quarterly — should be filtered out
                    "docDescription": "四半期報告書",
                    "filingDate": params.get("date", "2026-01-15"),
                    "withdrawalStatus": "0",
                },
            ],
        }
        return HttpResponse(
            status_code=200,
            content=json.dumps(body).encode("utf-8"),
        )

    def _download_response(self) -> HttpResponse:
        """Return mock ZIP with HTML content."""
        html_content = """<!DOCTYPE html><html><head><meta charset="utf-8"></head>
        <body>
        <h2>企業の概況</h2>
        <p>当社は東京都に本社を置くテスト企業です。設立は1990年。
        主な事業内容は製造業であり、従業員数は3,000名です。</p>

        <h3>事業等のリスク</h3>
        <p>当社グループの事業に影響を及ぼすリスクとして以下があります。
        為替変動リスク、原材料価格の変動リスク、技術革新への対応リスクが
        主要なリスク要因として認識されています。</p>

        <h3>経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析</h3>
        <p>売上高は前年同期比で増加しました。営業利益も改善傾向にあります。</p>

        <h3>コーポレート・ガバナンスの状況等</h3>
        <p>当社は監査役会設置会社です。取締役は8名で、うち社外取締役が3名です。</p>
        </body></html>""".encode("utf-8")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("XBRL/PublicDoc/0000000.htm", html_content)
        return HttpResponse(
            status_code=200,
            content=buf.getvalue(),
            headers={"content-type": "application/octet-stream"},
        )


# ── Tests ───────────────────────────────────────────────────────


def test_scraper_list_filters_by_doc_type():
    """EdinetScraper.list_documents returns only target doc types."""
    http = MockScraperHttp()
    config = EdinetConfig(target_doc_types=["120"])

    scraper = EdinetScraper(config=config, http_client=http, rate_limit_seconds=0)
    records = scraper.list_documents(date="2026-01-15")

    # Should get 2 (type 120) out of 3 total
    assert len(records) == 2
    assert all(r.document_type == "120" for r in records)
    assert records[0].filer_name == "テスト工業株式会社"
    assert records[1].filer_name == "サンプル電機株式会社"


def test_scraper_list_maps_fields():
    """list_documents correctly maps EDINET fields to DocumentRecord."""
    http = MockScraperHttp()
    scraper = EdinetScraper(
        config=EdinetConfig(target_doc_types=["120"]),
        http_client=http,
        rate_limit_seconds=0,
    )
    records = scraper.list_documents(date="2026-01-15")

    r = records[0]
    assert r.source_name == "edinet"
    assert r.language == "ja"
    assert r.filing_date == "2026-01-15"
    assert r.document_type_label == "有価証券報告書"
    assert r.metadata["edinet_code"] == "E00001"
    assert r.metadata["period_start"] == "2025-04-01"


def test_scraper_full_pipeline():
    """Full scrape pipeline: list → download → parse works end-to-end."""
    http = MockScraperHttp()

    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = EdinetScraper(
            config=EdinetConfig(target_doc_types=["120"]),
            http_client=http,
            output_dir=Path(tmpdir),
            rate_limit_seconds=0,
        )
        result = scraper.scrape(date="2026-01-15", checkpoint=False)

    assert result.total_listed == 2
    assert result.total_downloaded == 2
    assert result.total_parsed == 2
    assert result.total_errors == 0


def test_scraper_download_populates_record():
    """download_document fills in record fields correctly."""
    http = MockScraperHttp()

    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = EdinetScraper(
            config=EdinetConfig(target_doc_types=["120"]),
            http_client=http,
            output_dir=Path(tmpdir),
            rate_limit_seconds=0,
        )
        records = scraper.list_documents(date="2026-01-15")
        record = scraper.download_document(records[0])

    assert record.downloaded is True
    assert record.file_size_bytes > 0
    assert "_file_contents" in record.metadata


def test_scraper_parse_extracts_segments():
    """parse_document extracts structured segments from HTML."""
    http = MockScraperHttp()

    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = EdinetScraper(
            config=EdinetConfig(target_doc_types=["120"]),
            http_client=http,
            output_dir=Path(tmpdir),
            rate_limit_seconds=0,
        )
        records = scraper.list_documents(date="2026-01-15")
        record = scraper.download_document(records[0])
        record = scraper.parse_document(record)

    assert record.parsed is True
    assert record.raw_content  # Full text populated
    assert len(record.segments) > 0
    # Should find at least business_risks since our mock has that heading
    assert "business_risks" in record.segments


def test_scraper_requires_date():
    """list_documents raises ValueError without date kwarg."""
    scraper = EdinetScraper(rate_limit_seconds=0)
    try:
        scraper.list_documents()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "date" in str(e).lower()
