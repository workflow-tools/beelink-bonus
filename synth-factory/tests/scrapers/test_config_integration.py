"""
Integration tests: verify EDINET configs load and validate correctly
through the existing synth-factory config pipeline.

Run: pytest tests/scrapers/test_config_integration.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generators.config_loader import load_config
from generators.config_schema import DatasetConfig


def test_securities_report_config_loads():
    """securities-report-jp.yaml loads and validates."""
    config = load_config(Path("configs/securities-report-jp.yaml"))
    assert config.metadata.name == "securities-report-jp"
    assert config.metadata.language == "ja"
    assert "edinet" in config.metadata.tags
    assert len(config.document_types) == 1
    assert len(config.document_tables) == 1


def test_securities_report_document_type():
    """Document type has correct segment structure."""
    config = load_config(Path("configs/securities-report-jp.yaml"))
    doc_type = config.document_types[0]
    assert doc_type.name == "securities_report_jp"
    assert doc_type.language == "ja"
    assert doc_type.format == "json"
    assert doc_type.error_injection_rate == 0.08

    # Should have 8 segments
    assert len(doc_type.segments) == 8
    segment_names = [s.name for s in doc_type.segments]
    assert "company_overview" in segment_names
    assert "business_risks" in segment_names
    assert "md_and_a" in segment_names
    assert "corporate_governance" in segment_names
    assert "directors" in segment_names
    assert "financial_highlights" in segment_names


def test_securities_report_context_threading():
    """Segments have correct context dependencies."""
    config = load_config(Path("configs/securities-report-jp.yaml"))
    doc_type = config.document_types[0]
    segments_map = {s.name: s for s in doc_type.segments}

    # company_overview has no dependencies (first segment)
    assert segments_map["company_overview"].context_dependencies == []

    # business_risks depends on company_overview and business_status
    assert "company_overview" in segments_map["business_risks"].context_dependencies
    assert "business_status" in segments_map["business_risks"].context_dependencies

    # md_and_a depends on company_overview and business_status
    assert "company_overview" in segments_map["md_and_a"].context_dependencies

    # financial_highlights depends on company_overview and md_and_a
    assert "company_overview" in segments_map["financial_highlights"].context_dependencies
    assert "md_and_a" in segments_map["financial_highlights"].context_dependencies


def test_securities_report_document_table():
    """Document table references the correct type."""
    config = load_config(Path("configs/securities-report-jp.yaml"))
    doc_table = config.document_tables[0]
    assert doc_table.name == "securities_reports"
    assert doc_table.records == 500
    assert doc_table.document_type == "securities_report_jp"


def test_securities_report_validation_settings():
    """Validation includes document-specific validators."""
    config = load_config(Path("configs/securities-report-jp.yaml"))
    assert config.validation.enabled is True
    assert "language_detection" in config.validation.document_validators
    assert "structural_completeness" in config.validation.document_validators


def test_securities_report_packaging():
    """Packaging set for JSONL output (preferred for document datasets)."""
    config = load_config(Path("configs/securities-report-jp.yaml"))
    assert config.packaging.output_jsonl is True
    assert config.packaging.output_csv is False
    assert config.packaging.generate_datasheet is True


def test_all_document_configs_load_cleanly():
    """All document-type YAML configs load without validation errors.

    Note: mittelstand-b2b.yaml has a known pre-existing issue with
    numeric values in categorical columns (floats/ints where strings
    are expected). This test covers document-generation configs only.
    """
    configs_dir = Path("configs")
    document_configs = [
        "housing-management-jp.yaml",
        "securities-report-jp.yaml",
        "compliance-report-de.yaml",
        "dryrun-jp.yaml",
        "test-tiny.yaml",
    ]
    for name in document_configs:
        config_path = configs_dir / name
        if config_path.exists():
            config = load_config(config_path)
            assert config.metadata.name, f"{config_path} has no name"
            # Verify document types referenced by tables actually exist
            doc_type_names = {dt.name for dt in config.document_types}
            for dt in config.document_tables:
                assert dt.document_type in doc_type_names, (
                    f"{config_path}: document table '{dt.name}' references "
                    f"unknown type '{dt.document_type}'"
                )
