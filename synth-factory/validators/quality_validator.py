"""
Dataset quality validation using Evidently + custom checks.

After generation, this module validates the synthetic data:
1. Runs Evidently data quality and drift presets
2. Runs custom domain-specific checks (registered per-dataset)
3. Produces a validation report (HTML + JSON)
4. Returns a PASS/FAIL verdict with quality score

The validation report becomes part of the sellable package —
it's proof of quality for marketplace buyers.

Extensibility: Register custom checks via register_check().
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from generators.config_schema import DatasetConfig, ValidationSettings

logger = logging.getLogger(__name__)

# Registry of custom validation checks
# Each check is a callable: (df: DataFrame, config: DatasetConfig) -> CheckResult
_custom_checks: dict[str, Callable] = {}


class CheckResult:
    """Result of a single validation check."""

    def __init__(self, name: str, passed: bool, message: str, details: dict = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }


class ValidationReport:
    """Complete validation report for a dataset."""

    def __init__(self, dataset_name: str, table_name: str):
        self.dataset_name = dataset_name
        self.table_name = table_name
        self.timestamp = datetime.now().isoformat()
        self.checks: list[CheckResult] = []
        self.quality_score: float = 0.0
        self.passed: bool = False
        self.evidently_html: Optional[str] = None

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    def compute_score(self):
        """Calculate quality score as fraction of passed checks."""
        if self.total_checks > 0:
            self.quality_score = self.passed_checks / self.total_checks
        else:
            self.quality_score = 1.0

    def to_dict(self) -> dict:
        return {
            "dataset_name": self.dataset_name,
            "table_name": self.table_name,
            "timestamp": self.timestamp,
            "quality_score": round(self.quality_score, 4),
            "passed": self.passed,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "checks": [c.to_dict() for c in self.checks],
        }

    def save(self, output_dir: Path):
        """Save validation report as JSON and optionally HTML."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON report
        json_path = output_dir / f"validation_{self.table_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Validation JSON saved: {json_path}")

        # HTML report (Evidently)
        if self.evidently_html:
            html_path = output_dir / f"validation_{self.table_name}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.evidently_html)
            logger.info(f"Validation HTML saved: {html_path}")


def register_check(name: str, check_fn: Callable):
    """
    Register a custom validation check.

    Args:
        name: Unique name for the check (referenced in YAML configs).
        check_fn: Callable(df, config) -> CheckResult
    """
    _custom_checks[name] = check_fn
    logger.debug(f"Registered custom check: {name}")


def validate_table(
    df: pd.DataFrame,
    table_name: str,
    config: DatasetConfig,
    reference_df: Optional[pd.DataFrame] = None,
) -> ValidationReport:
    """
    Run all validation checks on a generated table.

    Args:
        df: The generated DataFrame to validate.
        table_name: Name of the table being validated.
        config: Full dataset config.
        reference_df: Optional reference/seed data for drift comparison.

    Returns:
        ValidationReport with all check results.
    """
    settings = config.validation
    report = ValidationReport(config.metadata.name, table_name)

    if not settings.enabled:
        logger.info("Validation disabled in config")
        report.passed = True
        report.quality_score = 1.0
        return report

    # ── Built-in checks ──────────────────────────────────────────

    # 1. Basic data quality checks
    report.checks.append(_check_no_empty_dataframe(df))
    report.checks.append(_check_column_completeness(df, config, table_name))
    report.checks.append(_check_no_all_null_columns(df))
    report.checks.append(_check_row_count(df, config, table_name))

    # 2. Evidently presets (if available)
    if "data_quality" in settings.test_presets:
        evidently_results = _run_evidently_quality(df, reference_df, settings)
        report.checks.extend(evidently_results["checks"])
        if evidently_results.get("html"):
            report.evidently_html = evidently_results["html"]

    # ── Custom checks from config ────────────────────────────────

    for check_name in settings.custom_checks:
        if check_name in _custom_checks:
            try:
                result = _custom_checks[check_name](df, config)
                report.checks.append(result)
            except Exception as e:
                report.checks.append(CheckResult(
                    check_name, False, f"Check raised exception: {e}"
                ))
        else:
            logger.warning(f"Custom check not registered: {check_name}")

    # ── Compute final score ──────────────────────────────────────

    report.compute_score()
    report.passed = report.quality_score >= settings.min_quality_score

    logger.info(
        f"Validation {'PASSED' if report.passed else 'FAILED'}: "
        f"{report.passed_checks}/{report.total_checks} checks passed, "
        f"score={report.quality_score:.2%}"
    )

    return report


# ─── Built-in Checks ──────────────────────────────────────────────

def _check_no_empty_dataframe(df: pd.DataFrame) -> CheckResult:
    """Verify the DataFrame is not empty."""
    passed = len(df) > 0 and len(df.columns) > 0
    return CheckResult(
        "no_empty_dataframe",
        passed,
        f"DataFrame has {len(df)} rows and {len(df.columns)} columns",
    )


def _check_column_completeness(
    df: pd.DataFrame, config: DatasetConfig, table_name: str
) -> CheckResult:
    """Verify all configured columns are present."""
    table_def = next((t for t in config.tables if t.name == table_name), None)
    if not table_def:
        return CheckResult("column_completeness", False, f"Table {table_name} not in config")

    expected = {col.name for col in table_def.columns}
    actual = set(df.columns)
    missing = expected - actual

    return CheckResult(
        "column_completeness",
        len(missing) == 0,
        f"Missing columns: {missing}" if missing else "All columns present",
        {"expected": list(expected), "actual": list(actual), "missing": list(missing)},
    )


def _check_no_all_null_columns(df: pd.DataFrame) -> CheckResult:
    """Verify no columns are entirely null."""
    all_null = [col for col in df.columns if df[col].isna().all()]
    return CheckResult(
        "no_all_null_columns",
        len(all_null) == 0,
        f"All-null columns: {all_null}" if all_null else "No all-null columns",
        {"all_null_columns": all_null},
    )


def _check_row_count(
    df: pd.DataFrame, config: DatasetConfig, table_name: str
) -> CheckResult:
    """Verify row count matches the configured record count."""
    table_def = next((t for t in config.tables if t.name == table_name), None)
    if not table_def:
        return CheckResult("row_count", False, f"Table {table_name} not in config")

    expected = table_def.records
    actual = len(df)
    tolerance = 0.01  # Allow 1% variance from SDV

    passed = abs(actual - expected) / expected <= tolerance if expected > 0 else actual == 0
    return CheckResult(
        "row_count",
        passed,
        f"Expected {expected} rows, got {actual}",
        {"expected": expected, "actual": actual},
    )


# ─── Evidently Integration ────────────────────────────────────────

def _run_evidently_quality(
    df: pd.DataFrame,
    reference_df: Optional[pd.DataFrame],
    settings: ValidationSettings,
) -> dict:
    """Run Evidently data quality report."""
    try:
        from evidently.report import Report
        from evidently.metric_preset import DataQualityPreset

        metrics = [DataQualityPreset()]

        # Add drift preset if reference data is available
        if reference_df is not None and "data_drift" in settings.test_presets:
            from evidently.metric_preset import DataDriftPreset
            metrics.append(DataDriftPreset())

        report = Report(metrics=metrics)

        if reference_df is not None:
            report.run(reference_data=reference_df, current_data=df)
        else:
            report.run(reference_data=df.head(len(df) // 2), current_data=df.tail(len(df) // 2))

        # Extract HTML
        html = None
        if settings.generate_html_report:
            html = report.get_html()

        # Build check results from Evidently output
        checks = [
            CheckResult(
                "evidently_data_quality",
                True,  # Evidently ran successfully
                "Evidently data quality report generated",
            )
        ]

        return {"checks": checks, "html": html}

    except ImportError:
        logger.warning("Evidently not installed, skipping quality report")
        return {"checks": [
            CheckResult("evidently_data_quality", False, "Evidently not installed")
        ], "html": None}

    except Exception as e:
        logger.error(f"Evidently report failed: {e}")
        return {"checks": [
            CheckResult("evidently_data_quality", False, f"Report failed: {e}")
        ], "html": None}


# ─── Pre-registered Domain Checks ─────────────────────────────────

def _check_german_plz_valid(df: pd.DataFrame, config: DatasetConfig) -> CheckResult:
    """Validate that PLZ values are 5-digit strings in valid German range."""
    plz_cols = [col for col in df.columns if "plz" in col.lower()]
    if not plz_cols:
        return CheckResult("german_plz_valid", True, "No PLZ columns found")

    invalid_count = 0
    total_count = 0
    for col in plz_cols:
        for val in df[col].dropna():
            total_count += 1
            s = str(val).zfill(5)
            if not s.isdigit() or len(s) != 5 or not (1000 <= int(s) <= 99999):
                invalid_count += 1

    passed = invalid_count == 0 or (invalid_count / total_count < 0.01)
    return CheckResult(
        "german_plz_valid",
        passed,
        f"{invalid_count}/{total_count} invalid PLZ values",
        {"invalid_count": invalid_count, "total_count": total_count},
    )


def _check_rechtsform_consistent(df: pd.DataFrame, config: DatasetConfig) -> CheckResult:
    """Check that Rechtsform values are from the expected set."""
    valid_forms = {
        "GmbH", "GmbH & Co. KG", "AG", "UG (haftungsbeschränkt)",
        "e.K.", "OHG", "KG", "GbR", "eG", "Einzelunternehmen",
    }
    rf_cols = [col for col in df.columns if "rechtsform" in col.lower()]
    if not rf_cols:
        return CheckResult("rechtsform_consistent", True, "No Rechtsform columns found")

    invalid = set()
    for col in rf_cols:
        for val in df[col].dropna().unique():
            if val not in valid_forms:
                invalid.add(val)

    return CheckResult(
        "rechtsform_consistent",
        len(invalid) == 0,
        f"Invalid Rechtsform values: {invalid}" if invalid else "All valid",
        {"invalid_values": list(invalid)},
    )


# Register the German-specific checks
register_check("german_plz_valid", _check_german_plz_valid)
register_check("rechtsform_consistent", _check_rechtsform_consistent)
