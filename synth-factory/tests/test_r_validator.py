"""
Tests for the R validation wrapper (validators/r_validator.py).

These tests verify the Python-side integration without requiring R.
The R script itself is tested by R/tests/test_validate.R (run with testthat).
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from validators.r_validator import (
    RValidationResult,
    check_r_available,
    run_r_validation,
    R_SCRIPT,
)


# ── R_SCRIPT path ──

def test_r_script_path_is_correct():
    """R_SCRIPT should point to R/validate_dataset.R relative to project."""
    assert R_SCRIPT.name == "validate_dataset.R"
    assert "R" in R_SCRIPT.parts


def test_r_script_exists():
    """The actual R script file should exist in the repo."""
    assert R_SCRIPT.exists(), f"Expected R script at {R_SCRIPT}"


# ── RValidationResult ──

def test_result_defaults():
    """RValidationResult should have sane defaults."""
    r = RValidationResult(success=True, return_code=0)
    assert r.summary == {}
    assert r.stdout == ""
    assert r.summary_path is None


# ── check_r_available ──

@patch("validators.r_validator.shutil.which")
def test_check_r_available_true(mock_which):
    mock_which.return_value = "/usr/bin/Rscript"
    assert check_r_available() is True


@patch("validators.r_validator.shutil.which")
def test_check_r_available_false(mock_which):
    mock_which.return_value = None
    assert check_r_available() is False


# ── run_r_validation ──

@patch("validators.r_validator.check_r_available", return_value=False)
def test_run_validation_no_r(mock_check):
    """Should return failure gracefully when R is not installed."""
    result = run_r_validation("some_file.jsonl")
    assert result.success is False
    assert result.return_code == -1
    assert "Rscript" in result.stderr


@patch("validators.r_validator.check_r_available", return_value=True)
@patch("validators.r_validator.subprocess.run")
def test_run_validation_success(mock_run, mock_check, tmp_path):
    """Should parse successful R execution."""
    # Create mock output
    output_dir = tmp_path / "report"
    output_dir.mkdir()
    plots_dir = output_dir / "plots"
    plots_dir.mkdir()

    summary = {
        "dataset": {"total_documents": 10},
        "overall_quality": {"validation_passed": True},
    }
    (output_dir / "validation_summary.json").write_text(json.dumps(summary))

    mock_run.return_value = MagicMock(
        returncode=0, stdout="PASS", stderr=""
    )

    result = run_r_validation("input.jsonl", output_dir=str(output_dir))
    assert result.success is True
    assert result.summary["dataset"]["total_documents"] == 10


@patch("validators.r_validator.check_r_available", return_value=True)
@patch("validators.r_validator.subprocess.run")
def test_run_validation_with_reference(mock_run, mock_check, tmp_path):
    """Should pass --reference flag when reference_path is provided."""
    output_dir = tmp_path / "report"
    output_dir.mkdir()
    (output_dir / "validation_summary.json").write_text("{}")

    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    run_r_validation("input.jsonl", output_dir=str(output_dir),
                     reference_path="ref.jsonl")

    called_cmd = mock_run.call_args[0][0]
    assert "--reference" in called_cmd
    assert "ref.jsonl" in called_cmd


@patch("validators.r_validator.check_r_available", return_value=True)
@patch("validators.r_validator.subprocess.run")
def test_run_validation_with_taxonomy(mock_run, mock_check, tmp_path):
    """Should pass --taxonomy flag when taxonomy_path is provided."""
    output_dir = tmp_path / "report"
    output_dir.mkdir()
    (output_dir / "validation_summary.json").write_text("{}")

    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    run_r_validation("input.jsonl", output_dir=str(output_dir),
                     taxonomy_path="flaw_taxonomy.json")

    called_cmd = mock_run.call_args[0][0]
    assert "--taxonomy" in called_cmd
    assert "flaw_taxonomy.json" in called_cmd


@patch("validators.r_validator.check_r_available", return_value=True)
@patch("validators.r_validator.subprocess.run",
       side_effect=Exception("subprocess exploded"))
def test_run_validation_exception(mock_run, mock_check):
    """Should handle unexpected exceptions gracefully."""
    result = run_r_validation("input.jsonl")
    assert result.success is False
    assert result.return_code == -3
    assert "exploded" in result.stderr
