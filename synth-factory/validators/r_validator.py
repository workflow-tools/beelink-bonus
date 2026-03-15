"""
R-based dataset validation wrapper.

Calls validate_dataset.R via subprocess after document generation completes.
Produces quality reports and marketplace-ready visualizations.

Usage:
    from validators.r_validator import run_r_validation

    result = run_r_validation(
        input_path="output/securities-report-jp/mixed/reports.jsonl",
        output_dir="output/securities-report-jp/quality-report",
        taxonomy_path="output/scraped/edinet/flaw_taxonomy.json",
    )
    if result.success:
        print(f"Validation passed: {result.summary_path}")
    else:
        print(f"Validation issues: {result.stderr}")
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to the R validation script relative to project root
R_SCRIPT = Path(__file__).parent.parent / "R" / "validate_dataset.R"


@dataclass
class RValidationResult:
    """Result from R validation subprocess."""
    success: bool
    return_code: int
    summary_path: Optional[Path] = None
    plots_dir: Optional[Path] = None
    summary: dict = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""


def check_r_available() -> bool:
    """Check if Rscript is available on the system."""
    return shutil.which("Rscript") is not None


def check_r_packages() -> dict[str, bool]:
    """Check which required R packages are installed."""
    required = ["jsonlite", "dplyr", "tidyr", "ggplot2", "optparse"]
    optional = ["fitdistrplus", "RMeCab", "quanteda"]

    results = {}
    for pkg in required + optional:
        try:
            proc = subprocess.run(
                ["Rscript", "-e", f'cat(requireNamespace("{pkg}", quietly=TRUE))'],
                capture_output=True, text=True, timeout=10,
            )
            results[pkg] = proc.stdout.strip() == "TRUE"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results[pkg] = False

    return results


def run_r_validation(
    input_path: str | Path,
    output_dir: str | Path = "quality-report",
    reference_path: Optional[str | Path] = None,
    taxonomy_path: Optional[str | Path] = None,
    timeout: int = 300,
) -> RValidationResult:
    """
    Run the R validation script via subprocess.

    Args:
        input_path: Path to the generated JSONL dataset.
        output_dir: Directory for validation output (plots, summary).
        reference_path: Optional path to reference (scraped) dataset for comparison.
        taxonomy_path: Optional path to flaw_taxonomy.json.
        timeout: Maximum seconds to wait for R script.

    Returns:
        RValidationResult with success flag, summary, and paths.
    """
    if not check_r_available():
        logger.warning("Rscript not found — skipping R validation")
        return RValidationResult(
            success=False, return_code=-1,
            stderr="Rscript not available. Install R: sudo apt install r-base",
        )

    if not R_SCRIPT.exists():
        logger.error(f"R validation script not found: {R_SCRIPT}")
        return RValidationResult(
            success=False, return_code=-1,
            stderr=f"Script not found: {R_SCRIPT}",
        )

    cmd = [
        "Rscript", str(R_SCRIPT),
        "--input", str(input_path),
        "--output", str(output_dir),
    ]

    if reference_path:
        cmd.extend(["--reference", str(reference_path)])
    if taxonomy_path:
        cmd.extend(["--taxonomy", str(taxonomy_path)])

    logger.info(f"Running R validation: {' '.join(cmd)}")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(R_SCRIPT.parent.parent),  # Run from project root
        )

        output_path = Path(output_dir)
        summary_path = output_path / "validation_summary.json"
        plots_dir = output_path / "plots"

        summary = {}
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        result = RValidationResult(
            success=proc.returncode == 0,
            return_code=proc.returncode,
            summary_path=summary_path if summary_path.exists() else None,
            plots_dir=plots_dir if plots_dir.exists() else None,
            summary=summary,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

        if result.success:
            logger.info("R validation passed")
            if plots_dir.exists():
                plot_files = list(plots_dir.glob("*.png"))
                logger.info(f"  Generated {len(plot_files)} plots")
        else:
            logger.warning(f"R validation returned code {proc.returncode}")
            if proc.stderr:
                logger.warning(f"  stderr: {proc.stderr[:500]}")

        return result

    except subprocess.TimeoutExpired:
        logger.error(f"R validation timed out after {timeout}s")
        return RValidationResult(
            success=False, return_code=-2,
            stderr=f"Timeout after {timeout} seconds",
        )
    except Exception as e:
        logger.error(f"R validation failed: {e}")
        return RValidationResult(
            success=False, return_code=-3,
            stderr=str(e),
        )
