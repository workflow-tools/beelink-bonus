"""
Synthetic Data Factory — Main Orchestrator

Usage:
    python run.py configs/mittelstand-b2b.yaml
    python run.py configs/mittelstand-b2b.yaml --skip-llm    # Tabular only, no Ollama
    python run.py configs/mittelstand-b2b.yaml --skip-validate
    python run.py --list                                       # Show available configs
    python run.py --health                                     # Check Ollama status

This is the single entry point for the factory. It:
1. Loads the config
2. Generates tabular data
3. Augments text columns via Ollama (optional)
4. Validates the output
5. Packages into a sellable bundle

The cron job calls this script.
"""

from __future__ import annotations
import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from generators.config_loader import load_config, list_configs
from generators.config_schema import DatasetConfig, TextGenerator
from generators.tabular_generator import generate_table
from generators.ollama_augmenter import OllamaAugmenter, TemplateAugmenter
from generators.document_generator import DocumentGenerator
from validators.quality_validator import validate_table
from validators.document_validator import validate_document_table
from packagers.dataset_packager import package_dataset


# ─── Logging Setup ────────────────────────────────────────────────

def setup_logging(log_dir: Path = Path("logs"), dataset_name: str = "factory"):
    """Configure logging to both console and file."""
    log_dir.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d_%H%M%S")
    log_file = log_dir / f"{timestamp}_{dataset_name}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    return logging.getLogger(__name__)


# ─── Pipeline Steps ──────────────────────────────────────────────

def run_pipeline(
    config_path: Path,
    skip_llm: bool = False,
    skip_validate: bool = False,
    skip_package: bool = False,
    skip_docs: bool = False,
    resume: bool = False,
    output_base: Path = Path("output"),
    seeds_dir: Path = Path("seeds"),
):
    """
    Execute the full generation pipeline for a dataset config.

    Args:
        config_path: Path to the YAML config.
        skip_llm: If True, skip Ollama text augmentation.
        skip_validate: If True, skip validation step.
        skip_package: If True, skip packaging step.
        skip_docs: If True, skip document table generation.
        resume: If True, resume from progress file for document generation.
        output_base: Base directory for output.
        seeds_dir: Directory containing seed data files.
    """
    start_time = time.time()

    # 1. Load config
    logger.info(f"Loading config: {config_path}")
    config = load_config(config_path)
    table_count = len(config.tables)
    doc_count = len(config.document_tables)
    parts = []
    if table_count:
        parts.append(f"{table_count} tabular table{'s' if table_count != 1 else ''}")
    if doc_count:
        parts.append(f"{doc_count} document table{'s' if doc_count != 1 else ''}")
    logger.info(
        f"Dataset: {config.metadata.name} v{config.metadata.version} "
        f"({', '.join(parts) or 'empty config'})"
    )

    tables = {}
    validation_reports = {}

    for table_def in config.tables:
        table_start = time.time()

        # 2. Generate tabular structure
        logger.info(f"\n{'='*60}")
        logger.info(f"TABLE: {table_def.name} ({table_def.records} records)")
        logger.info(f"{'='*60}")

        df = generate_table(table_def, config, seeds_dir)
        logger.info(f"Tabular generation: {time.time() - table_start:.1f}s")

        # 3. Template augmentation (fast, no LLM)
        template_cols = [
            c for c in table_def.columns if c.generator == TextGenerator.TEMPLATE
        ]
        if template_cols:
            logger.info(f"Filling {len(template_cols)} template columns")
            df = TemplateAugmenter.augment_table(df, table_def)

        # 4. LLM augmentation (slow, optional)
        if not skip_llm:
            ollama_cols = [
                c for c in table_def.columns
                if c.generator == TextGenerator.OLLAMA and c.ollama
            ]
            if ollama_cols:
                augmenter = OllamaAugmenter(
                    base_url=config.generation.ollama_base_url,
                    max_concurrent=config.generation.ollama_concurrent,
                )

                # Health check first
                health = augmenter.check_health()
                if health["status"] != "healthy":
                    logger.error(f"Ollama is not healthy: {health}")
                    logger.error("Run with --skip-llm to generate tabular data only")
                    sys.exit(1)

                logger.info(f"Available models: {health['models']}")
                llm_start = time.time()
                df = augmenter.augment_table(
                    df, table_def, config,
                    progress_callback=lambda done, total: logger.info(
                        f"  LLM progress: {done}/{total} cells ({done/total:.0%})"
                    ),
                )
                logger.info(f"LLM augmentation: {time.time() - llm_start:.1f}s")
        else:
            logger.info("Skipping LLM augmentation (--skip-llm)")

        tables[table_def.name] = df

        # 5. Validate
        if not skip_validate:
            logger.info("Running validation...")
            report = validate_table(df, table_def.name, config)
            validation_reports[table_def.name] = report

            if not report.passed:
                logger.warning(
                    f"VALIDATION FAILED for {table_def.name}: "
                    f"score={report.quality_score:.2%}"
                )
        else:
            logger.info("Skipping validation (--skip-validate)")

        logger.info(f"Table {table_def.name} complete: {time.time() - table_start:.1f}s")

    # ─── Document Generation ─────────────────────────────────────
    if config.document_tables and not skip_docs:
        logger.info(f"\n{'='*60}")
        logger.info("DOCUMENT GENERATION")
        logger.info(f"{'='*60}")

        doc_types_map = {dt.name: dt for dt in config.document_types}

        for doc_table_def in config.document_tables:
            doc_start = time.time()
            logger.info(f"\nDOCUMENT TABLE: {doc_table_def.name} ({doc_table_def.records} records)")
            logger.info(f"  Type: {doc_table_def.document_type}")

            # Resolve taxonomy path for taxonomy-aware error injection
            doc_type = doc_types_map[doc_table_def.document_type]
            taxonomy_path = doc_type.flaw_taxonomy_path if doc_type.use_taxonomy_errors else None

            doc_gen = DocumentGenerator(
                base_url=config.generation.ollama_base_url,
                max_concurrent=config.generation.ollama_concurrent,
                taxonomy_path=taxonomy_path,
            )

            # Health check before document generation
            if not skip_llm:
                health = doc_gen.check_health()
                if health["status"] != "healthy":
                    logger.error(f"Ollama is not healthy: {health}")
                    logger.error("Cannot generate documents without Ollama")
                    sys.exit(1)
                logger.info(f"Available models: {health['models']}")

            # Load seed data if referencing a tabular table
            seed_df = None
            if doc_table_def.seed_table and doc_table_def.seed_table in tables:
                seed_df = tables[doc_table_def.seed_table]
                if doc_table_def.seed_columns:
                    available = [c for c in doc_table_def.seed_columns if c in seed_df.columns]
                    seed_df = seed_df[available]
                logger.info(f"  Seeding from table: {doc_table_def.seed_table} ({len(seed_df)} rows)")

            # Resume path
            resume_path = None
            if resume:
                resume_path = (
                    output_base / config.metadata.name / ".progress"
                    / f"{doc_table_def.name}.jsonl"
                )

            doc_df = doc_gen.generate_table(
                doc_table_def, doc_types_map, config,
                seed_df=seed_df,
                progress_callback=lambda done, total: logger.info(
                    f"  Document progress: {done}/{total} ({done/total:.0%})"
                ),
                resume_from=resume_path,
            )

            tables[doc_table_def.name] = doc_df

            # Validate documents
            if not skip_validate:
                logger.info("Validating documents...")
                doc_type = doc_types_map[doc_table_def.document_type]
                report = validate_document_table(
                    doc_df, doc_table_def, doc_type, config
                )
                validation_reports[doc_table_def.name] = report
                if not report.passed:
                    logger.warning(
                        f"DOCUMENT VALIDATION FAILED for {doc_table_def.name}: "
                        f"score={report.quality_score:.2%}"
                    )

            logger.info(
                f"Document table {doc_table_def.name} complete: "
                f"{time.time() - doc_start:.1f}s"
            )
    elif config.document_tables and skip_docs:
        logger.info("Skipping document generation (--skip-docs)")

    # 6. Package
    if not skip_package:
        logger.info("\nPackaging dataset...")
        output_dir = package_dataset(
            tables, config, validation_reports,
            output_base=output_base,
            config_path=config_path,
        )
        logger.info(f"Output: {output_dir}")
    else:
        logger.info("Skipping packaging (--skip-package)")

    # Summary
    elapsed = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"PIPELINE COMPLETE: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    logger.info(f"Tables generated: {len(tables)}")
    logger.info(f"Total rows: {sum(len(df) for df in tables.values()):,}")

    for name, report in validation_reports.items():
        status = "PASS" if report.passed else "FAIL"
        logger.info(f"  {name}: {status} (score={report.quality_score:.2%})")

    logger.info(f"{'='*60}")


# ─── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Synthetic Data Factory — Generate, validate, and package datasets",
    )
    parser.add_argument(
        "config", nargs="?", type=Path,
        help="Path to dataset YAML config file",
    )
    parser.add_argument(
        "--skip-llm", action="store_true",
        help="Skip Ollama text augmentation (tabular only)",
    )
    parser.add_argument(
        "--skip-validate", action="store_true",
        help="Skip validation step",
    )
    parser.add_argument(
        "--skip-package", action="store_true",
        help="Skip packaging step",
    )
    parser.add_argument(
        "--skip-docs", action="store_true",
        help="Skip document table generation",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume document generation from progress file",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output"),
        help="Output base directory (default: output/)",
    )
    parser.add_argument(
        "--seeds", type=Path, default=Path("seeds"),
        help="Seeds directory (default: seeds/)",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_configs",
        help="List available dataset configs",
    )
    parser.add_argument(
        "--health", action="store_true",
        help="Check Ollama health and available models",
    )

    args = parser.parse_args()

    if args.health:
        augmenter = OllamaAugmenter()
        health = augmenter.check_health()
        print(f"Ollama status: {health['status']}")
        if health['status'] == 'healthy':
            print(f"Models: {', '.join(health['models'])}")
        else:
            print(f"Error: {health.get('error', 'unknown')}")
        sys.exit(0 if health['status'] == 'healthy' else 1)

    if args.list_configs:
        configs = list_configs()
        if configs:
            print("Available dataset configs:")
            for p in configs:
                print(f"  {p}")
        else:
            print("No configs found in configs/")
        sys.exit(0)

    if not args.config:
        parser.print_help()
        sys.exit(1)

    global logger
    dataset_name = args.config.stem if args.config else "factory"
    logger = setup_logging(dataset_name=dataset_name)

    try:
        run_pipeline(
            config_path=args.config,
            skip_llm=args.skip_llm,
            skip_validate=args.skip_validate,
            skip_package=args.skip_package,
            skip_docs=args.skip_docs,
            resume=args.resume,
            output_base=args.output,
            seeds_dir=args.seeds,
        )
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    main()
