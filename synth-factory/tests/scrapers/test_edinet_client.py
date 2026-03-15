"""
Tests for EDINET API v2 client.

Uses mock HTTP responses — no network calls needed.

Run: pytest tests/scrapers/test_edinet_client.py -v
"""

import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base.base_scraper import HttpResponse
from scrapers.edinet.edinet_client import (
    EdinetClient,
    EdinetConfig,
    EdinetDocumentInfo,
    EdinetApiError,
)


# ── Mock HTTP Client ────────────────────────────────────────────


class MockEdinetHttp:
    """Mock HTTP client returning canned EDINET API responses."""

    def __init__(self):
        self.requests: list[tuple[str, dict]] = []
        self._responses: dict[str, HttpResponse] = {}

    def set_response(self, url_pattern: str, response: HttpResponse):
        self._responses[url_pattern] = response

    def get(self, url, params=None, headers=None, timeout=30.0):
        self.requests.append((url, params or {}))
        for pattern, resp in self._responses.items():
            if pattern in url:
                return resp
        return HttpResponse(status_code=404, content=b"Not found")


# ── Fixtures ────────────────────────────────────────────────────


def make_listing_response(documents: list[dict]) -> HttpResponse:
    """Build a mock EDINET documents.json response."""
    body = {
        "metadata": {
            "title": "提出書類一覧API",
            "parameter": {"date": "2026-01-15", "type": "2"},
            "resultset": {"count": len(documents)},
            "processDateTime": "2026-01-15T23:00:00.000",
            "status": "200",
            "message": "OK",
        },
        "results": documents,
    }
    return HttpResponse(
        status_code=200,
        content=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json"},
    )


def make_sample_doc(
    doc_id="S100TEST",
    doc_type="120",
    filer="テスト株式会社",
    withdrawn="0",
) -> dict:
    """Build a sample EDINET document result dict."""
    return {
        "docID": doc_id,
        "edinetCode": "E12345",
        "filerName": filer,
        "docTypeCode": doc_type,
        "docDescription": "有価証券報告書",
        "filingDate": "2026-01-15",
        "submitDateTime": "2026-01-15 09:30",
        "ordinanceCode": "010",
        "formCode": "030000",
        "periodStart": "2025-04-01",
        "periodEnd": "2025-12-31",
        "withdrawalStatus": withdrawn,
        "docInfoEditStatus": "0",
        "disclosureStatus": "0",
    }


def make_zip_response(files: dict[str, bytes]) -> HttpResponse:
    """Build a mock ZIP download response."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return HttpResponse(
        status_code=200,
        content=buf.getvalue(),
        headers={"content-type": "application/octet-stream"},
    )


# ── Tests: Document Listing ─────────────────────────────────────


def test_list_documents_returns_matching_types():
    """list_documents_by_date returns only target doc types."""
    http = MockEdinetHttp()
    http.set_response("documents.json", make_listing_response([
        make_sample_doc("DOC-A", "120"),   # Annual report — should match
        make_sample_doc("DOC-B", "140"),   # Quarterly — should NOT match
        make_sample_doc("DOC-C", "120"),   # Annual report — should match
    ]))

    client = EdinetClient(
        config=EdinetConfig(target_doc_types=["120"]),
        http_client=http,
    )
    docs = client.list_documents_by_date("2026-01-15")
    assert len(docs) == 2
    assert all(d.doc_type_code == "120" for d in docs)


def test_list_documents_filters_withdrawn():
    """Withdrawn documents are excluded from results."""
    http = MockEdinetHttp()
    http.set_response("documents.json", make_listing_response([
        make_sample_doc("DOC-A", "120", withdrawn="0"),   # Active
        make_sample_doc("DOC-B", "120", withdrawn="1"),   # Withdrawn
    ]))

    client = EdinetClient(
        config=EdinetConfig(target_doc_types=["120"]),
        http_client=http,
    )
    docs = client.list_documents_by_date("2026-01-15")
    assert len(docs) == 1
    assert docs[0].doc_id == "DOC-A"


def test_list_documents_passes_api_key():
    """API key is included in request parameters."""
    http = MockEdinetHttp()
    http.set_response("documents.json", make_listing_response([]))

    client = EdinetClient(
        config=EdinetConfig(api_key="MY_TEST_KEY"),
        http_client=http,
    )
    client.list_documents_by_date("2026-01-15")

    assert len(http.requests) == 1
    _, params = http.requests[0]
    assert params.get("Subscription-Key") == "MY_TEST_KEY"
    assert params.get("date") == "2026-01-15"
    assert params.get("type") == 2


def test_list_documents_handles_empty_results():
    """Empty results array returns empty list."""
    http = MockEdinetHttp()
    body = {
        "metadata": {"status": "200", "message": "OK"},
        "results": None,
    }
    http.set_response("documents.json", HttpResponse(
        status_code=200,
        content=json.dumps(body).encode("utf-8"),
    ))

    client = EdinetClient(http_client=http)
    docs = client.list_documents_by_date("2026-01-15")
    assert docs == []


def test_list_documents_handles_api_error():
    """API error in metadata raises EdinetApiError."""
    http = MockEdinetHttp()
    body = {
        "metadata": {"status": "400", "message": "Invalid date format"},
        "results": [],
    }
    http.set_response("documents.json", HttpResponse(
        status_code=200,
        content=json.dumps(body).encode("utf-8"),
    ))

    client = EdinetClient(http_client=http)
    try:
        client.list_documents_by_date("bad-date")
        assert False, "Should have raised EdinetApiError"
    except EdinetApiError as e:
        assert "Invalid date format" in str(e)


# ── Tests: EdinetDocumentInfo ────────────────────────────────────


def test_document_info_from_api_dict():
    """EdinetDocumentInfo parses API response correctly."""
    raw = make_sample_doc("S100ABC", "120", "テスト社")
    doc = EdinetDocumentInfo.from_api_dict(raw)
    assert doc.doc_id == "S100ABC"
    assert doc.filer_name == "テスト社"
    assert doc.doc_type_code == "120"
    assert doc.filing_date == "2026-01-15"
    assert doc.period_start == "2025-04-01"


def test_document_info_type_label():
    """doc_type_label returns human-readable type name."""
    doc = EdinetDocumentInfo.from_api_dict(make_sample_doc(doc_type="120"))
    assert doc.doc_type_label == "有価証券報告書"

    doc2 = EdinetDocumentInfo.from_api_dict(make_sample_doc(doc_type="999"))
    assert "999" in doc2.doc_type_label


def test_document_info_withdrawn():
    """is_withdrawn flags withdrawn documents."""
    active = EdinetDocumentInfo.from_api_dict(make_sample_doc(withdrawn="0"))
    assert not active.is_withdrawn

    withdrawn = EdinetDocumentInfo.from_api_dict(make_sample_doc(withdrawn="1"))
    assert withdrawn.is_withdrawn


# ── Tests: Document Download ─────────────────────────────────────


def test_download_extracts_zip():
    """download_document extracts files from ZIP response."""
    http = MockEdinetHttp()
    http.set_response("documents/DOC-001", make_zip_response({
        "XBRL/PublicDoc/report.htm": b"<html>test</html>",
        "XBRL/PublicDoc/data.xbrl": b"<xbrl>data</xbrl>",
    }))

    client = EdinetClient(http_client=http)
    files = client.download_document("DOC-001")

    assert len(files) == 2
    assert b"<html>test</html>" in files["XBRL/PublicDoc/report.htm"]


def test_download_handles_json_error():
    """JSON error response raises EdinetApiError."""
    http = MockEdinetHttp()
    error_body = {
        "metadata": {"status": "404", "message": "Document not found"},
    }
    http.set_response("documents/DOC-BAD", HttpResponse(
        status_code=200,
        content=json.dumps(error_body).encode("utf-8"),
        headers={"content-type": "application/json"},
    ))

    client = EdinetClient(http_client=http)
    try:
        client.download_document("DOC-BAD")
        assert False, "Should have raised"
    except EdinetApiError as e:
        assert "not found" in str(e).lower()


def test_download_handles_bad_zip():
    """Invalid ZIP content raises EdinetApiError."""
    http = MockEdinetHttp()
    http.set_response("documents/DOC-CORRUPT", HttpResponse(
        status_code=200,
        content=b"not a zip file at all",
        headers={"content-type": "application/octet-stream"},
    ))

    client = EdinetClient(http_client=http)
    try:
        client.download_document("DOC-CORRUPT")
        assert False, "Should have raised"
    except EdinetApiError as e:
        assert "invalid ZIP" in str(e).lower() or "zip" in str(e).lower()
