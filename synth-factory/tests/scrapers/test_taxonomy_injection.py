"""
Tests for taxonomy-driven error injection and temperature tier system.

Tests:
1. TaxonomyErrorInjector loads JSON correctly
2. TaxonomyErrorInjector falls back gracefully when no file exists
3. Taxonomy-driven injection produces different error types
4. Segment-targeted flaw selection works
5. QUALITY_TIERS has expected values
6. DEFAULT_MIXED_DISTRIBUTION sums to ~1.0
7. _naive_inject_error produces mutations
8. DocumentGenerator wires taxonomy_path correctly
9. Schema fields flaw_taxonomy_path and use_taxonomy_errors work
"""

import json
import tempfile
from pathlib import Path

import pytest

from generators.document_generator import (
    TaxonomyErrorInjector,
    QUALITY_TIERS,
    DEFAULT_MIXED_DISTRIBUTION,
    _naive_inject_error,
    DocumentGenerator,
)
from generators.config_schema import DocumentTypeDef, SegmentDef, SegmentType


# ── Fixtures ──────────────────────────────────────────────────

SAMPLE_TAXONOMY = {
    "source_name": "edinet",
    "document_type": "securities_report_jp",
    "total_documents_analyzed": 50,
    "last_updated": "2026-03-15T00:00:00+00:00",
    "categories": [
        {
            "flaw_type": "structural",
            "flaw_subtype": "empty_section",
            "description": "Section marked as empty",
            "segment": "business_risks",
            "count": 10,
            "frequency": 0.20,
            "severity": "low",
            "examples": ["該当事項はありません"],
        },
        {
            "flaw_type": "formatting",
            "flaw_subtype": "garbled_symbols",
            "description": "Consecutive special symbols",
            "segment": "",
            "count": 5,
            "frequency": 0.10,
            "severity": "high",
            "examples": ["□■◆◇"],
        },
        {
            "flaw_type": "disclosure",
            "flaw_subtype": "generic_language",
            "description": "Generic vague language",
            "segment": "business_risks",
            "count": 15,
            "frequency": 0.30,
            "severity": "medium",
            "examples": ["一般的に"],
        },
        {
            "flaw_type": "temporal",
            "flaw_subtype": "reference_date",
            "description": "Stale date reference",
            "segment": "",
            "count": 3,
            "frequency": 0.06,
            "severity": "low",
            "examples": [],
        },
    ],
}


@pytest.fixture
def taxonomy_file(tmp_path):
    """Create a temporary taxonomy JSON file."""
    path = tmp_path / "flaw_taxonomy.json"
    path.write_text(json.dumps(SAMPLE_TAXONOMY, ensure_ascii=False))
    return path


# ── Tests ─────────────────────────────────────────────────────


def test_taxonomy_injector_loads_json(taxonomy_file):
    """TaxonomyErrorInjector should load categories from JSON."""
    injector = TaxonomyErrorInjector(str(taxonomy_file))
    assert injector.is_loaded
    assert len(injector._category_weights) == 4


def test_taxonomy_injector_fallback_missing_file():
    """Should fall back gracefully when taxonomy file doesn't exist."""
    injector = TaxonomyErrorInjector("/nonexistent/path.json")
    assert not injector.is_loaded


def test_taxonomy_injector_fallback_none():
    """Should work fine with no taxonomy path."""
    injector = TaxonomyErrorInjector(None)
    assert not injector.is_loaded


def test_taxonomy_inject_produces_mutation(taxonomy_file):
    """Taxonomy injection should produce a different result than input."""
    injector = TaxonomyErrorInjector(str(taxonomy_file))
    original = "これは事業等のリスクに関する詳細な記述です。当社は様々なリスクに直面しています。"

    # Run many times — at least one should differ from original
    mutations = set()
    for _ in range(50):
        result = injector.inject(original, "business_risks", "ja")
        mutations.add(result)

    # We should get at least 2 different outputs (original is not always returned)
    assert len(mutations) >= 2, "Taxonomy injection should produce varied outputs"


def test_taxonomy_select_flaw_segment_targeting(taxonomy_file):
    """Flaw selection should prefer segment-specific flaws."""
    injector = TaxonomyErrorInjector(str(taxonomy_file))

    # business_risks has segment-specific flaws (empty_section, generic_language)
    # plus segment-agnostic ones (garbled_symbols, reference_date)
    selections = []
    for _ in range(100):
        flaw = injector.select_flaw("business_risks")
        if flaw:
            selections.append(flaw["flaw_subtype"])

    # Should include segment-targeted flaws
    assert "empty_section" in selections or "generic_language" in selections


def test_quality_tiers_values():
    """QUALITY_TIERS should have expected tier names and ordered rates."""
    assert "perfect" in QUALITY_TIERS
    assert "near" in QUALITY_TIERS
    assert "moderate" in QUALITY_TIERS
    assert "severe" in QUALITY_TIERS

    assert QUALITY_TIERS["perfect"] == 0.0
    assert QUALITY_TIERS["near"] < QUALITY_TIERS["moderate"]
    assert QUALITY_TIERS["moderate"] < QUALITY_TIERS["severe"]


def test_mixed_distribution_sums_to_one():
    """DEFAULT_MIXED_DISTRIBUTION fractions should sum to ~1.0."""
    total = sum(DEFAULT_MIXED_DISTRIBUTION.values())
    assert abs(total - 1.0) < 0.01, f"Distribution sums to {total}, expected ~1.0"


def test_naive_inject_produces_output():
    """Naive injection should always return a string."""
    content = "This is test content with enough length to be interesting for testing"
    for _ in range(20):
        result = _naive_inject_error(content, "ja")
        assert isinstance(result, str)


def test_document_generator_wires_taxonomy(taxonomy_file):
    """DocumentGenerator should accept and wire taxonomy_path."""
    gen = DocumentGenerator(taxonomy_path=str(taxonomy_file))
    assert gen._taxonomy_injector.is_loaded


def test_document_generator_no_taxonomy():
    """DocumentGenerator should work without taxonomy."""
    gen = DocumentGenerator(taxonomy_path=None)
    assert not gen._taxonomy_injector.is_loaded


def test_schema_new_fields():
    """DocumentTypeDef should accept flaw_taxonomy_path and use_taxonomy_errors."""
    dt = DocumentTypeDef(
        name="test",
        segments=[],
        flaw_taxonomy_path="output/flaw_taxonomy.json",
        use_taxonomy_errors=True,
        error_injection_rate=0.15,
    )
    assert dt.flaw_taxonomy_path == "output/flaw_taxonomy.json"
    assert dt.use_taxonomy_errors is True
    assert dt.error_injection_rate == 0.15


def test_schema_defaults():
    """New fields should default to None/False."""
    dt = DocumentTypeDef(name="test", segments=[])
    assert dt.flaw_taxonomy_path is None
    assert dt.use_taxonomy_errors is False
