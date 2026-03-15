"""
Document-specific validation for segment-based generated datasets.

Validates:
- Language consistency (heuristic character-range detection)
- Structural completeness (all segments present and non-null)
- Segment lengths (within configured min/max)
- Required keywords (if specified per segment)
- Generation errors (no sentinel failure strings)

Uses the same ValidationReport class from quality_validator for consistency.
"""

from __future__ import annotations
import logging
import re
import unicodedata
from typing import Optional

import pandas as pd

from generators.config_schema import (
    DatasetConfig,
    DocumentTableDef,
    DocumentTypeDef,
    SegmentDef,
)
from validators.quality_validator import CheckResult, ValidationReport

logger = logging.getLogger(__name__)


def validate_document_table(
    df: pd.DataFrame,
    doc_table_def: DocumentTableDef,
    doc_type: DocumentTypeDef,
    config: DatasetConfig,
) -> ValidationReport:
    """
    Validate a table of generated documents.

    Args:
        df: DataFrame with document_id, document_content, and seg_* columns.
        doc_table_def: Document table definition.
        doc_type: Document type definition (segment blueprints).
        config: Full dataset config.

    Returns:
        ValidationReport with pass/fail and quality score.
    """
    report = ValidationReport(
        dataset_name=config.metadata.name,
        table_name=doc_table_def.name,
    )

    # Always run core checks
    report.checks.append(_check_row_count(df, doc_table_def))
    report.checks.append(_check_no_empty(df))
    report.checks.append(_check_generation_errors(df))
    report.checks.append(_check_structural_completeness(df, doc_type))

    # Run configured document validators
    validators = config.validation.document_validators
    if "language_detection" in validators:
        report.checks.append(
            _check_language_consistency(df, doc_type.language)
        )
    if "segment_length_check" in validators:
        for seg_def in doc_type.segments:
            result = _check_segment_length(df, seg_def)
            if result:
                report.checks.append(result)
    if "keyword_presence" in validators:
        for seg_def in doc_type.segments:
            if seg_def.required_keywords:
                report.checks.append(
                    _check_keyword_presence(df, seg_def)
                )

    report.compute_score()
    report.passed = report.quality_score >= config.validation.min_quality_score
    return report


# ─── Individual Checks ───────────────────────────────────────────

def _check_row_count(df: pd.DataFrame, doc_table_def: DocumentTableDef) -> CheckResult:
    """Verify row count matches expected."""
    actual = len(df)
    expected = doc_table_def.records
    passed = actual == expected
    return CheckResult(
        name="document_row_count",
        passed=passed,
        message=(
            f"Expected {expected} documents, got {actual}"
            if not passed else f"Row count correct: {actual}"
        ),
        details={"expected": expected, "actual": actual},
    )


def _check_no_empty(df: pd.DataFrame) -> CheckResult:
    """Verify no empty documents."""
    if "document_content" not in df.columns:
        return CheckResult(
            "no_empty_documents", False,
            "Missing document_content column",
        )
    empty_count = df["document_content"].isna().sum() + (df["document_content"] == "").sum()
    passed = empty_count == 0
    return CheckResult(
        name="no_empty_documents",
        passed=passed,
        message=(
            f"{empty_count} empty documents found" if not passed
            else "All documents have content"
        ),
        details={"empty_count": int(empty_count)},
    )


def _check_generation_errors(df: pd.DataFrame) -> CheckResult:
    """Check for LLM generation failure sentinel strings."""
    error_pattern = r"\[GENERATION_FAILED"
    error_count = 0
    for col in df.columns:
        if df[col].dtype == object:
            matches = df[col].str.contains(error_pattern, na=False, regex=True)
            error_count += matches.sum()
    passed = error_count == 0
    return CheckResult(
        name="no_generation_errors",
        passed=passed,
        message=(
            f"{error_count} generation failures found" if not passed
            else "No generation failures"
        ),
        details={"error_count": int(error_count)},
    )


def _check_structural_completeness(
    df: pd.DataFrame, doc_type: DocumentTypeDef
) -> CheckResult:
    """Verify all expected segment columns exist and are non-null."""
    missing_cols = []
    null_cols = []
    for seg_def in doc_type.segments:
        col_name = f"seg_{seg_def.name}"
        if col_name not in df.columns:
            missing_cols.append(col_name)
        elif df[col_name].isna().any() or (df[col_name] == "").any():
            null_count = df[col_name].isna().sum() + (df[col_name] == "").sum()
            null_cols.append((col_name, int(null_count)))

    passed = len(missing_cols) == 0 and len(null_cols) == 0
    msg_parts = []
    if missing_cols:
        msg_parts.append(f"Missing columns: {missing_cols}")
    if null_cols:
        msg_parts.append(f"Null segments: {null_cols}")
    if not msg_parts:
        msg_parts.append("All segments present and non-null")

    return CheckResult(
        name="structural_completeness",
        passed=passed,
        message="; ".join(msg_parts),
        details={"missing_columns": missing_cols, "null_columns": null_cols},
    )


def _check_language_consistency(
    df: pd.DataFrame, expected_language: str
) -> CheckResult:
    """
    Heuristic language detection based on character ranges.

    - Japanese (ja): checks for presence of hiragana/katakana/CJK characters
    - German (de): checks for presence of common German characters (ä, ö, ü, ß)
    - Other: skips (always passes)

    This is a lightweight check that avoids heavy dependencies like langdetect.
    """
    if "document_content" not in df.columns:
        return CheckResult("language_consistency", True, "No document_content column")

    sample_size = min(50, len(df))
    sample = df["document_content"].head(sample_size)
    correct_count = 0

    for text in sample:
        if not isinstance(text, str) or not text.strip():
            continue
        if expected_language == "ja":
            # Check for Japanese characters (hiragana, katakana, or CJK)
            if _has_japanese_chars(text):
                correct_count += 1
        elif expected_language == "de":
            # Check for German-specific characters or common German words
            if _has_german_markers(text):
                correct_count += 1
        else:
            correct_count += 1  # Unknown language, assume correct

    ratio = correct_count / sample_size if sample_size > 0 else 0
    passed = ratio >= 0.8  # 80% of sampled docs should match expected language
    return CheckResult(
        name="language_consistency",
        passed=passed,
        message=(
            f"Language detection: {ratio:.0%} of sampled docs appear to be "
            f"{expected_language} (threshold: 80%)"
        ),
        details={
            "expected_language": expected_language,
            "correct_ratio": round(ratio, 3),
            "sample_size": sample_size,
        },
    )


def _check_segment_length(
    df: pd.DataFrame, seg_def: SegmentDef
) -> Optional[CheckResult]:
    """Check that a segment's character count is within configured bounds."""
    col_name = f"seg_{seg_def.name}"
    if col_name not in df.columns:
        return None
    if seg_def.min_length is None and seg_def.max_length is None:
        return None

    lengths = df[col_name].str.len().dropna()
    violations = 0
    details = {"segment": seg_def.name}

    if seg_def.min_length is not None:
        too_short = (lengths < seg_def.min_length).sum()
        violations += too_short
        details["too_short"] = int(too_short)

    if seg_def.max_length is not None:
        too_long = (lengths > seg_def.max_length).sum()
        violations += too_long
        details["too_long"] = int(too_long)

    passed = violations == 0
    return CheckResult(
        name=f"segment_length_{seg_def.name}",
        passed=passed,
        message=(
            f"Segment '{seg_def.name}': {violations} length violations"
            if not passed
            else f"Segment '{seg_def.name}': all lengths within bounds"
        ),
        details=details,
    )


def _check_keyword_presence(
    df: pd.DataFrame, seg_def: SegmentDef
) -> CheckResult:
    """Check that required keywords appear in a segment's content."""
    col_name = f"seg_{seg_def.name}"
    if col_name not in df.columns or not seg_def.required_keywords:
        return CheckResult(
            f"keyword_{seg_def.name}", True,
            f"No keywords to check for {seg_def.name}",
        )

    missing_counts = {}
    for keyword in seg_def.required_keywords:
        mask = df[col_name].str.contains(keyword, na=False, regex=False)
        missing = (~mask).sum()
        if missing > 0:
            missing_counts[keyword] = int(missing)

    passed = len(missing_counts) == 0
    return CheckResult(
        name=f"keyword_{seg_def.name}",
        passed=passed,
        message=(
            f"Segment '{seg_def.name}': missing keywords in some docs: {missing_counts}"
            if not passed
            else f"Segment '{seg_def.name}': all required keywords present"
        ),
        details={"missing_keywords": missing_counts},
    )


# ─── Language Detection Helpers ──────────────────────────────────

def _has_japanese_chars(text: str) -> bool:
    """Check if text contains hiragana, katakana, or CJK ideographs."""
    for char in text:
        cp = ord(char)
        # Hiragana: U+3040–U+309F
        if 0x3040 <= cp <= 0x309F:
            return True
        # Katakana: U+30A0–U+30FF
        if 0x30A0 <= cp <= 0x30FF:
            return True
        # CJK Unified Ideographs: U+4E00–U+9FFF
        if 0x4E00 <= cp <= 0x9FFF:
            return True
    return False


def _has_german_markers(text: str) -> bool:
    """Check if text contains German-specific characters or common words."""
    german_chars = set("äöüÄÖÜß")
    if any(c in german_chars for c in text):
        return True
    # Check for very common German words as fallback
    german_words = {"und", "der", "die", "das", "ist", "für", "mit", "von", "auf"}
    words = set(text.lower().split())
    if len(words & german_words) >= 2:
        return True
    return False
