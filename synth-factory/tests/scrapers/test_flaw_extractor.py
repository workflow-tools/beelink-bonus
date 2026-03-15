"""
Tests for the financial report flaw taxonomy extractor.

Run: pytest tests/scrapers/test_flaw_extractor.py -v
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.base.base_scraper import DocumentRecord
from scrapers.edinet.flaw_extractor import FlawExtractor, FlawTaxonomy


# ── Helpers ─────────────────────────────────────────────────────


def make_record(
    source_id: str = "TEST-001",
    segments: dict[str, str] | None = None,
) -> DocumentRecord:
    """Create a DocumentRecord with test segments."""
    return DocumentRecord(
        source_id=source_id,
        source_name="edinet",
        title="Test Document",
        language="ja",
        filing_date="2026-01-15",
        document_type="120",
        document_type_label="有価証券報告書",
        segments=segments or {},
        parsed=True,
    )


# ── Tests: Pattern Detection ────────────────────────────────────


def test_detects_empty_section_pattern():
    """Detects 該当事項はありません patterns."""
    extractor = FlawExtractor()
    record = make_record(segments={
        "facilities": "設備の状況\n該当事項はありません。",
    })
    flaws = extractor.analyze(record)
    subtypes = [f.flaw_subtype for f in flaws]
    assert "empty_section" in subtypes


def test_detects_generic_language():
    """Detects vague/generic language in disclosures."""
    extractor = FlawExtractor()
    record = make_record(segments={
        "business_risks": "一般的に、市場環境の変化により業績が影響を受ける可能性があります。"
    })
    flaws = extractor.analyze(record)
    subtypes = [f.flaw_subtype for f in flaws]
    assert "generic_language" in subtypes


def test_detects_boilerplate_risk():
    """Detects common boilerplate risk factors."""
    extractor = FlawExtractor()
    record = make_record(segments={
        "business_risks": "為替変動リスクにより当社の業績に影響を及ぼす可能性があります。"
    })
    flaws = extractor.analyze(record)
    subtypes = [f.flaw_subtype for f in flaws]
    assert "boilerplate_risk" in subtypes


def test_detects_garbled_symbols():
    """Detects encoding artifacts (garbled symbols)."""
    extractor = FlawExtractor()
    record = make_record(segments={
        "company_overview": "当社は□□□□に設立されました。"
    })
    flaws = extractor.analyze(record)
    subtypes = [f.flaw_subtype for f in flaws]
    assert "garbled_symbols" in subtypes


def test_detects_missing_sections():
    """Detects when expected sections are missing."""
    extractor = FlawExtractor()
    # Only company_overview present — others should be flagged as missing
    record = make_record(segments={
        "company_overview": "当社は東京に本社を置く企業です。事業内容は製造業です。" * 5,
    })
    flaws = extractor.analyze(record)
    missing_flaws = [f for f in flaws if f.flaw_subtype == "missing_section"]
    # Should flag business_status, md_and_a, business_risks, financial_statements
    assert len(missing_flaws) >= 3


def test_detects_short_sections():
    """Detects unusually short sections."""
    extractor = FlawExtractor()
    record = make_record(segments={
        "business_risks": "リスクあり",  # Only 5 chars — too short
    })
    flaws = extractor.analyze(record)
    short_flaws = [f for f in flaws if f.flaw_subtype == "suspiciously_short"]
    assert len(short_flaws) > 0


# ── Tests: Taxonomy Building ────────────────────────────────────


def test_build_taxonomy_aggregates():
    """build_taxonomy() aggregates instances with frequency."""
    extractor = FlawExtractor()

    # Analyze 3 documents with varying flaws
    for i in range(3):
        segments = {
            "company_overview": "当社は企業です。" * 20,
            "business_status": "経営方針について述べます。" * 20,
            "business_risks": "一般的に、市場リスクがあります。為替変動リスクにより影響があります。",
            "md_and_a": "経営分析の内容です。" * 20,
            "financial_statements": "財務諸表の内容です。" * 20,
        }
        record = make_record(source_id=f"DOC-{i}", segments=segments)
        extractor.analyze(record)

    taxonomy = extractor.build_taxonomy()
    assert taxonomy.total_documents_analyzed == 3
    assert len(taxonomy.categories) > 0

    # generic_language should appear in all 3
    generic = [c for c in taxonomy.categories if c.flaw_subtype == "generic_language"]
    assert len(generic) > 0
    assert generic[0].count == 3
    assert generic[0].frequency == 1.0  # 3/3 = 100%


def test_taxonomy_save_load_roundtrip():
    """Taxonomy survives save→load round-trip."""
    extractor = FlawExtractor()
    record = make_record(segments={
        "business_risks": "一般的に、市場環境が影響します。",
        "company_overview": "x" * 200,
        "business_status": "x" * 200,
        "md_and_a": "x" * 200,
        "financial_statements": "x" * 200,
    })
    extractor.analyze(record)
    taxonomy = extractor.build_taxonomy()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "taxonomy.json"
        taxonomy.save(path)

        loaded = FlawTaxonomy.load(path)
        assert loaded.total_documents_analyzed == 1
        assert len(loaded.categories) == len(taxonomy.categories)
        assert loaded.source_name == "edinet"


def test_taxonomy_to_dict():
    """Taxonomy can be serialized to dict for JSON output."""
    extractor = FlawExtractor()
    record = make_record(segments={
        "company_overview": "x" * 200,
        "business_status": "x" * 200,
        "business_risks": "リスクに該当事項はありません。",
        "md_and_a": "x" * 200,
        "financial_statements": "x" * 200,
    })
    extractor.analyze(record)
    taxonomy = extractor.build_taxonomy()
    d = taxonomy.to_dict()
    assert isinstance(d, dict)
    assert "categories" in d
    # Should be JSON-serializable
    json_str = json.dumps(d, ensure_ascii=False)
    assert len(json_str) > 0


# ── Tests: Extractor Reset ──────────────────────────────────────


def test_extractor_reset():
    """reset() clears accumulated state."""
    extractor = FlawExtractor()
    record = make_record(segments={"business_risks": "一般的にリスクがあります。"})
    extractor.analyze(record)
    assert extractor._documents_analyzed == 1

    extractor.reset()
    assert extractor._documents_analyzed == 0
    assert len(extractor._instances) == 0
