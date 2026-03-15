#!/usr/bin/env python3
"""
EDINET Dataset Generator — Single-Command Pipeline
====================================================

One command to rule them all: scrape → update flaw taxonomy → generate data.

This is the "press play and walk away" entry point for the Beelink.
It chains every step of the EDINET dataset pipeline and produces
temperature-controlled datasets with realistic, taxonomy-driven flaws.

Usage:
  # Full pipeline: scrape recent filings, build taxonomy, generate 500 docs
  python generate_edinet.py --api-key YOUR_KEY

  # Quick test run: 5 docs, 7-day scrape window
  python generate_edinet.py --api-key YOUR_KEY --records 5 --scrape-days 7

  # Skip scraping (reuse existing taxonomy), generate only
  python generate_edinet.py --skip-scrape --records 100

  # Generate temperature-tiered datasets (one dataset per tier)
  python generate_edinet.py --tiers perfect,near,moderate,severe --records 200

  # Generate a mixed-flaw dataset (80% clean, 10% near, 8% moderate, 2% severe)
  python generate_edinet.py --mixed --records 500

  # Resume an interrupted generation run
  python generate_edinet.py --resume

  # Pause-friendly: generate in batches of 50
  python generate_edinet.py --batch-size 50 --records 500

Prerequisites:
  - EDINET API key: export EDINET_API_KEY=your_key  (or --api-key)
  - Ollama running with 70B model: ollama pull llama3.1:70b-instruct-q4_K_M
  - pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from generators.config_loader import load_config
from generators.config_schema import DatasetConfig, DocumentTypeDef
from generators.document_generator import (
    DocumentGenerator,
    QUALITY_TIERS,
    DEFAULT_MIXED_DISTRIBUTION,
)


# ── Logging ──────────────────────────────────────────────────────

def setup_logging(log_dir: Path = Path("logs")) -> logging.Logger:
    log_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y-%m-%d_%H%M%S")
    log_file = log_dir / f"{ts}_generate_edinet.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    return logging.getLogger("generate_edinet")


# ── Phase 1: Scrape ─────────────────────────────────────────────

def phase_scrape(
    api_key: str,
    scrape_days: int,
    output_dir: Path,
    delay: float,
    logger: logging.Logger,
) -> Path:
    """Scrape EDINET filings and return path to checkpoint."""
    from scrapers.edinet import EdinetScraper, EdinetConfig

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=scrape_days)).strftime("%Y-%m-%d")

    logger.info(f"Phase 1: Scraping EDINET {start_date} → {end_date}")
    logger.info(f"  Output: {output_dir / 'edinet'}")

    config = EdinetConfig(api_key=api_key, target_doc_types=["120"])
    scraper = EdinetScraper(
        config=config,
        output_dir=output_dir,
        rate_limit_seconds=delay,
    )

    result = scraper.scrape_date_range(
        start_date=start_date,
        end_date=end_date,
        download=True,
        parse=True,
    )

    logger.info(f"  Listed:     {result.total_listed}")
    logger.info(f"  Downloaded: {result.total_downloaded}")
    logger.info(f"  Parsed:     {result.total_parsed}")
    logger.info(f"  Errors:     {result.total_errors}")

    checkpoint_path = output_dir / "edinet" / "checkpoint.jsonl"
    return checkpoint_path


# ── Phase 2: Update Flaw Taxonomy ─────────────────────────────

def phase_update_taxonomy(
    output_dir: Path,
    logger: logging.Logger,
) -> Path:
    """Build/update flaw taxonomy from scraped filings."""
    from scrapers.edinet.flaw_extractor import FlawExtractor
    from scrapers.edinet.edinet_parser import EdinetParser
    from scrapers.base.base_scraper import DocumentRecord

    logger.info("Phase 2: Updating flaw taxonomy from scraped filings")

    checkpoint_path = output_dir / "edinet" / "checkpoint.jsonl"
    raw_dir = output_dir / "edinet" / "raw"
    taxonomy_path = output_dir / "edinet" / "flaw_taxonomy.json"

    if not checkpoint_path.exists():
        logger.warning("  No checkpoint file — skipping taxonomy update")
        if taxonomy_path.exists():
            logger.info(f"  Using existing taxonomy: {taxonomy_path}")
            return taxonomy_path
        return taxonomy_path  # Will be missing; generate_edinet handles gracefully

    extractor = FlawExtractor()
    analyzed = 0

    with open(checkpoint_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if not entry.get("parsed"):
                    continue

                source_id = entry["source_id"]
                doc_dir = raw_dir / source_id
                if not doc_dir.exists():
                    continue

                files = {}
                for fp in doc_dir.rglob("*"):
                    if fp.is_file():
                        files[str(fp.relative_to(doc_dir))] = fp.read_bytes()

                if files:
                    parser = EdinetParser()
                    parsed = parser.parse_zip_contents(files, doc_id=source_id)

                    if parsed.segments:
                        record = DocumentRecord(
                            source_id=source_id,
                            source_name="edinet",
                            title=entry.get("title", ""),
                            language="ja",
                            filing_date=entry.get("filing_date", ""),
                            document_type=entry.get("document_type", "120"),
                            document_type_label="有価証券報告書",
                            segments=parsed.segments,
                            parsed=True,
                        )
                        extractor.analyze(record)
                        analyzed += 1

            except Exception:
                continue

    if analyzed == 0:
        logger.warning("  No parsed documents for taxonomy extraction")
        return taxonomy_path

    taxonomy = extractor.build_taxonomy()
    taxonomy.save(taxonomy_path)

    logger.info(f"  Analyzed: {analyzed} documents")
    logger.info(f"  Categories: {len(taxonomy.categories)}")
    logger.info(f"  Saved: {taxonomy_path}")

    return taxonomy_path


# ── Phase 3: Generate Documents ──────────────────────────────

def phase_generate(
    config: DatasetConfig,
    doc_type: DocumentTypeDef,
    records: int,
    taxonomy_path: Path,
    output_base: Path,
    tier_name: str,
    error_rate: float,
    resume: bool,
    batch_size: int,
    logger: logging.Logger,
) -> Path:
    """Generate a single tier's worth of documents."""
    logger.info(f"Phase 3: Generating {records} documents (tier={tier_name}, error_rate={error_rate:.0%})")

    # Override config for this tier
    doc_type_copy = copy.deepcopy(doc_type)
    doc_type_copy.error_injection_rate = error_rate

    # Wire taxonomy if available
    tax_path_str = None
    if taxonomy_path.exists() and error_rate > 0:
        doc_type_copy.use_taxonomy_errors = True
        doc_type_copy.flaw_taxonomy_path = str(taxonomy_path)
        tax_path_str = str(taxonomy_path)
        logger.info(f"  Taxonomy: {taxonomy_path}")
    elif error_rate > 0:
        logger.info("  No taxonomy found — using naive error injection")

    doc_gen = DocumentGenerator(
        base_url=config.generation.ollama_base_url,
        max_concurrent=config.generation.ollama_concurrent,
        taxonomy_path=tax_path_str,
    )

    # Health check
    health = doc_gen.check_health()
    if health["status"] != "healthy":
        logger.error(f"Ollama is not healthy: {health}")
        logger.error("Ensure Ollama is running: ollama serve")
        sys.exit(1)
    logger.info(f"  Ollama: healthy ({len(health['models'])} models loaded)")

    # Build a temporary DocumentTableDef
    from generators.config_schema import DocumentTableDef
    table_def = DocumentTableDef(
        name=f"securities_reports_{tier_name}",
        description=f"Securities reports — {tier_name} quality tier",
        records=records,
        document_type=doc_type_copy.name,
    )

    # Resume path
    progress_dir = output_base / config.metadata.name / ".progress"
    progress_dir.mkdir(parents=True, exist_ok=True)
    resume_path = progress_dir / f"{table_def.name}.jsonl" if resume else None

    doc_types_map = {doc_type_copy.name: doc_type_copy}

    gen_start = time.time()
    df = doc_gen.generate_table(
        table_def, doc_types_map, config,
        progress_callback=lambda done, total: (
            logger.info(f"  Progress: {done}/{total} ({done/total:.0%})")
            if done % max(1, total // 20) == 0 else None
        ),
        resume_from=resume_path,
    )
    gen_elapsed = time.time() - gen_start

    # Save output
    out_dir = output_base / config.metadata.name / tier_name
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"{table_def.name}.jsonl"

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")

    # Save tier metadata
    meta = {
        "tier": tier_name,
        "error_rate": error_rate,
        "records": len(df),
        "taxonomy_used": tax_path_str is not None,
        "generation_time_seconds": round(gen_elapsed, 1),
        "avg_seconds_per_doc": round(gen_elapsed / max(1, len(df)), 1),
        "model": config.generation.ollama_default_model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "tier_metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False)
    )

    logger.info(f"  Generated {len(df)} documents in {gen_elapsed:.0f}s")
    logger.info(f"  Output: {jsonl_path}")

    return jsonl_path


def phase_generate_mixed(
    config: DatasetConfig,
    doc_type: DocumentTypeDef,
    total_records: int,
    taxonomy_path: Path,
    output_base: Path,
    distribution: dict[str, float],
    resume: bool,
    batch_size: int,
    logger: logging.Logger,
) -> Path:
    """
    Generate a single dataset with mixed flaw levels.

    Documents are shuffled so flaw tiers are distributed randomly
    throughout the dataset, not grouped.
    """
    import random
    import pandas as pd

    logger.info(f"Phase 3: Generating mixed-flaw dataset ({total_records} records)")
    logger.info(f"  Distribution: {distribution}")

    all_rows = []

    for tier_name, fraction in distribution.items():
        tier_records = max(1, round(total_records * fraction))
        error_rate = QUALITY_TIERS.get(tier_name, 0.0)

        logger.info(f"  Sub-tier '{tier_name}': {tier_records} records @ {error_rate:.0%} error rate")

        # Override config
        doc_type_copy = copy.deepcopy(doc_type)
        doc_type_copy.error_injection_rate = error_rate

        tax_path_str = None
        if taxonomy_path.exists() and error_rate > 0:
            doc_type_copy.use_taxonomy_errors = True
            doc_type_copy.flaw_taxonomy_path = str(taxonomy_path)
            tax_path_str = str(taxonomy_path)

        doc_gen = DocumentGenerator(
            base_url=config.generation.ollama_base_url,
            max_concurrent=config.generation.ollama_concurrent,
            taxonomy_path=tax_path_str,
        )

        from generators.config_schema import DocumentTableDef
        table_def = DocumentTableDef(
            name=f"securities_reports_mixed_{tier_name}",
            records=tier_records,
            document_type=doc_type_copy.name,
        )

        doc_types_map = {doc_type_copy.name: doc_type_copy}

        resume_path = None
        if resume:
            progress_dir = output_base / config.metadata.name / ".progress"
            progress_dir.mkdir(parents=True, exist_ok=True)
            resume_path = progress_dir / f"{table_def.name}.jsonl"

        df = doc_gen.generate_table(
            table_def, doc_types_map, config,
            resume_from=resume_path,
        )

        # Tag each row with its quality tier
        df["quality_tier"] = tier_name
        df["error_rate"] = error_rate
        all_rows.append(df)

    # Combine and shuffle
    combined = pd.concat(all_rows, ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    # Reassign document IDs after shuffle
    combined["document_id"] = [f"DOC-{i+1:06d}" for i in range(len(combined))]

    # Save
    out_dir = output_base / config.metadata.name / "mixed"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "securities_reports_mixed.jsonl"

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for _, row in combined.iterrows():
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")

    # Save distribution metadata
    meta = {
        "mode": "mixed",
        "total_records": len(combined),
        "distribution": distribution,
        "tier_counts": {
            tier: int((combined["quality_tier"] == tier).sum())
            for tier in distribution
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "mixed_metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False)
    )

    logger.info(f"  Mixed dataset: {len(combined)} records → {jsonl_path}")
    return jsonl_path


# ── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EDINET Dataset Generator — scrape → taxonomy → generate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality tiers:
  perfect    0% error rate   — pristine documentation
  near       3% error rate   — occasional minor issues
  moderate  12% error rate   — noticeable noise
  severe    30% error rate   — "land you in a lawsuit or five"

Examples:
  # Full pipeline with defaults (500 docs, 30-day scrape)
  python generate_edinet.py --api-key YOUR_KEY

  # Quick test (5 docs, 7-day scrape)
  python generate_edinet.py --api-key YOUR_KEY --records 5 --scrape-days 7

  # Temperature tiers (one dataset per tier)
  python generate_edinet.py --tiers perfect,moderate,severe --records 200

  # Mixed distribution (single dataset, varied quality)
  python generate_edinet.py --mixed --records 500

  # Skip scraping, reuse existing taxonomy
  python generate_edinet.py --skip-scrape --records 100

  # Resume interrupted run
  python generate_edinet.py --resume
        """,
    )

    # Scraping
    parser.add_argument("--api-key", type=str, default="",
                        help="EDINET API key (or set EDINET_API_KEY env)")
    parser.add_argument("--scrape-days", type=int, default=30,
                        help="How many days back to scrape (default: 30)")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="Skip scraping, reuse existing taxonomy")
    parser.add_argument("--scrape-delay", type=float, default=1.0,
                        help="Seconds between EDINET API requests")

    # Generation
    parser.add_argument("--records", type=int, default=500,
                        help="Documents per tier (default: 500)")
    parser.add_argument("--config", type=Path,
                        default=Path("configs/securities-report-jp.yaml"),
                        help="YAML config to use")
    parser.add_argument("--output", type=Path, default=Path("output"),
                        help="Output base directory")

    # Quality tiers
    parser.add_argument("--tiers", type=str, default="",
                        help="Comma-separated quality tiers to generate "
                             "(e.g., 'perfect,near,moderate,severe')")
    parser.add_argument("--mixed", action="store_true",
                        help="Generate a single mixed-flaw dataset")
    parser.add_argument("--mixed-dist", type=str, default="",
                        help="Custom mixed distribution as JSON "
                             "(e.g., '{\"perfect\":0.8,\"near\":0.1,\"moderate\":0.08,\"severe\":0.02}')")

    # Resumability
    parser.add_argument("--resume", action="store_true",
                        help="Resume from progress file")
    parser.add_argument("--batch-size", type=int, default=0,
                        help="Generate in batches of N (0=all at once)")

    args = parser.parse_args()

    logger = setup_logging()
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("EDINET Dataset Generator")
    logger.info("=" * 60)

    # ── Resolve API key ──
    api_key = args.api_key or os.environ.get("EDINET_API_KEY", "")
    if not api_key and not args.skip_scrape:
        logger.error("EDINET API key required. Set EDINET_API_KEY or pass --api-key")
        logger.error("Register free at: https://disclosure.edinet-fsa.go.jp")
        sys.exit(1)

    # ── Scrape directory (shared across phases) ──
    scrape_dir = args.output / "scraped"
    scrape_dir.mkdir(parents=True, exist_ok=True)

    # ── Phase 1: Scrape ──
    if not args.skip_scrape:
        phase_scrape(api_key, args.scrape_days, scrape_dir, args.scrape_delay, logger)
    else:
        logger.info("Phase 1: Skipped (--skip-scrape)")

    # ── Phase 2: Update Taxonomy ──
    taxonomy_path = phase_update_taxonomy(scrape_dir, logger)

    # ── Phase 3: Generate ──
    logger.info(f"\nLoading config: {args.config}")
    config = load_config(args.config)

    # Find the document type
    if not config.document_types:
        logger.error("Config has no document_types defined")
        sys.exit(1)
    doc_type = config.document_types[0]

    output_paths = []

    if args.mixed:
        # Mixed-flaw dataset
        dist = DEFAULT_MIXED_DISTRIBUTION
        if args.mixed_dist:
            try:
                dist = json.loads(args.mixed_dist)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid --mixed-dist JSON: {e}")
                sys.exit(1)

        path = phase_generate_mixed(
            config, doc_type, args.records, taxonomy_path,
            args.output, dist, args.resume, args.batch_size, logger,
        )
        output_paths.append(path)

    else:
        # Temperature tiers (or single default tier)
        tiers = {}
        if args.tiers:
            for t in args.tiers.split(","):
                t = t.strip().lower()
                if t not in QUALITY_TIERS:
                    logger.error(f"Unknown tier '{t}'. Available: {list(QUALITY_TIERS.keys())}")
                    sys.exit(1)
                tiers[t] = QUALITY_TIERS[t]
        else:
            # Default: use the config's built-in error_injection_rate
            tiers = {"default": doc_type.error_injection_rate}

        for tier_name, error_rate in tiers.items():
            path = phase_generate(
                config, doc_type, args.records, taxonomy_path,
                args.output, tier_name, error_rate,
                args.resume, args.batch_size, logger,
            )
            output_paths.append(path)

    # ── Summary ──
    elapsed = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"PIPELINE COMPLETE — {elapsed:.0f}s ({elapsed/3600:.1f} hours)")
    logger.info(f"Output files:")
    for p in output_paths:
        logger.info(f"  {p}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
