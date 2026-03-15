"""
Tests for EDINET document parser.

Run: pytest tests/scrapers/test_edinet_parser.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.edinet.edinet_parser import EdinetParser, ParsedDocument


# ── Test HTML Parsing ───────────────────────────────────────────


def make_html(body_content: str) -> bytes:
    """Wrap content in a minimal HTML document."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Test</title></head>
<body>{body_content}</body></html>""".encode("utf-8")


def test_parse_html_extracts_text():
    """Parser extracts plain text from HTML."""
    parser = EdinetParser()
    html = make_html("""
        <h1>企業の概況</h1>
        <p>当社は1985年に設立された東京都千代田区に本社を置く製造業の企業です。</p>
        <p>従業員数は連結で5,000名を超えています。</p>
    """)
    result = parser.parse_zip_contents(
        {"XBRL/PublicDoc/report.htm": html},
        doc_id="TEST-001",
    )
    assert result.full_text
    assert "企業の概況" in result.full_text
    assert "1985年" in result.full_text
    assert "5,000名" in result.full_text


def test_parse_strips_html_tags():
    """Parser removes HTML tags from output."""
    parser = EdinetParser()
    html = make_html("""
        <div class="test"><span style="color:red">テスト文章</span></div>
    """)
    result = parser.parse_zip_contents(
        {"XBRL/PublicDoc/test.htm": html},
        doc_id="TEST-002",
    )
    assert "<div" not in result.full_text
    assert "<span" not in result.full_text
    assert "テスト文章" in result.full_text


def test_parse_removes_script_style():
    """Parser removes script and style blocks."""
    parser = EdinetParser()
    html = make_html("""
        <script>alert('xss')</script>
        <style>.test { color: red; }</style>
        <p>実際のコンテンツ</p>
    """)
    result = parser.parse_zip_contents(
        {"XBRL/PublicDoc/test.htm": html},
        doc_id="TEST-003",
    )
    assert "alert" not in result.full_text
    assert "color: red" not in result.full_text
    assert "実際のコンテンツ" in result.full_text


def test_parse_handles_japanese_encodings():
    """Parser handles Shift-JIS encoded content."""
    parser = EdinetParser()
    # Create Shift-JIS encoded content
    text = "日本語テスト内容です。企業の概況を記載します。"
    html_str = f"<html><body><p>{text}</p></body></html>"
    sjis_bytes = html_str.encode("shift_jis")

    result = parser.parse_zip_contents(
        {"XBRL/PublicDoc/report.htm": sjis_bytes},
        doc_id="TEST-SJIS",
    )
    assert "日本語テスト" in result.full_text


# ── Test Segment Extraction ─────────────────────────────────────


def test_extract_segments_finds_business_risks():
    """Parser identifies business risks section by heading."""
    parser = EdinetParser()
    html = make_html("""
        <h2>第2 事業の状況</h2>
        <p>経営方針について述べます。中期経営計画を策定しています。</p>
        <h3>事業等のリスク</h3>
        <p>当社グループの経営成績及び財政状態に影響を及ぼす可能性のあるリスクとして、
        以下のような事項があります。為替変動リスクについて、当社は海外売上比率が40%を超えており、
        円高による売上高の減少が見込まれます。また、原材料価格の変動により、
        製造原価が増加する可能性があります。</p>
        <h3>経営者による財政状態</h3>
        <p>次のセクションの内容</p>
    """)
    result = parser.parse_zip_contents(
        {"XBRL/PublicDoc/report.htm": html},
        doc_id="TEST-SEGMENTS",
    )
    assert "business_risks" in result.segments
    risk_text = result.segments["business_risks"]
    assert "為替変動" in risk_text


def test_extract_segments_finds_md_and_a():
    """Parser identifies MD&A section."""
    parser = EdinetParser()
    html = make_html("""
        <h3>経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析</h3>
        <p>当連結会計年度における当社グループの財政状態、経営成績及びキャッシュ・フローの
        状況の概要は次のとおりであります。売上高は前年同期比10.5%増加しました。</p>
        <h3>第3 設備の状況</h3>
    """)
    result = parser.parse_zip_contents(
        {"XBRL/PublicDoc/report.htm": html},
        doc_id="TEST-MDA",
    )
    assert "md_and_a" in result.segments
    assert "売上高" in result.segments["md_and_a"]


# ── Test XBRL Parsing ───────────────────────────────────────────


def test_parse_xbrl_text_blocks():
    """Parser extracts textBlock elements from XBRL."""
    parser = EdinetParser()
    xbrl_content = """<?xml version="1.0" encoding="utf-8"?>
    <xbrli:xbrl>
        <jpcrp_cor:BusinessRisksTextBlock contextRef="CurrentYearDuration">
            当社のリスク要因として、為替リスクと市場リスクがあります。
        </jpcrp_cor:BusinessRisksTextBlock>
        <jpcrp_cor:ManagementAnalysisTextBlock contextRef="CurrentYearDuration">
            経営成績の分析内容です。売上高は増加傾向にあります。
        </jpcrp_cor:ManagementAnalysisTextBlock>
    </xbrli:xbrl>""".encode("utf-8")

    result = parser.parse_zip_contents(
        {"XBRL/PublicDoc/data.xbrl": xbrl_content},
        doc_id="TEST-XBRL",
    )
    assert result.full_text
    assert "為替リスク" in result.full_text
    assert "売上高" in result.full_text


# ── Test File Inventory ─────────────────────────────────────────


def test_parse_records_file_inventory():
    """Parser records file sizes in inventory."""
    parser = EdinetParser()
    files = {
        "XBRL/PublicDoc/report.htm": make_html("<p>test</p>"),
        "XBRL/PublicDoc/manifest.xml": b"<manifest/>",
        "XBRL/PublicDoc/style.css": b"body { }",
    }
    result = parser.parse_zip_contents(files, doc_id="TEST-INV")
    assert result.total_files == 3
    assert result.total_bytes > 0
    assert "XBRL/PublicDoc/report.htm" in result.file_inventory


# ── Test Edge Cases ─────────────────────────────────────────────


def test_parse_empty_zip():
    """Parser handles empty file dict gracefully."""
    parser = EdinetParser()
    result = parser.parse_zip_contents({}, doc_id="EMPTY")
    assert not result.parsed
    assert result.error


def test_parse_no_parseable_files():
    """Parser handles ZIP with only non-parseable files."""
    parser = EdinetParser()
    result = parser.parse_zip_contents(
        {"readme.txt": b"This is a text file", "image.png": b"\x89PNG"},
        doc_id="NO-HTML",
    )
    assert not result.parsed


def test_parsed_document_summary():
    """ParsedDocument.summary() returns dict with key metrics."""
    doc = ParsedDocument(
        doc_id="TEST",
        content_format="html",
        full_text="x" * 1000,
        segments={"overview": "text", "risks": "more text"},
        parsed=True,
    )
    summary = doc.summary()
    assert summary["doc_id"] == "TEST"
    assert summary["segment_count"] == 2
    assert summary["text_length"] == 1000
    assert summary["parsed"] is True
