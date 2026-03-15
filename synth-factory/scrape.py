#!/usr/bin/env python3
"""
Synth-Factory Scraper CLI
==========================

Unified CLI for all data source scrapers. Follows the same subcommand
pattern as dissertation/simulated-corpus/scrapers/uk_tribunals.py.

Usage:
  # List available scrapers:
  python scrape.py list

  # EDINET: List filings for a date (no download):
  python scrape.py edinet list --date 2026-03-01

  # EDINET: Full pipeline for a date range:
  python scrape.py edinet pipeline --start 2026-03-01 --end 2026-03-15

  # EDINET: Download + parse + extract flaw taxonomy:
  python scrape.py edinet pipeline --start 2026-03-01 --end 2026-03-07 --taxonomy

  # Resume interrupted scrape:
  python scrape.py edinet pipeline --start 2026-03-01 --end 2026-03-15 --resume

  # Quick volume check (list only, no download):
  python scrape.py edinet scout --start 2026-01-01 --end 2026-03-31

Prerequisites:
  - EDINET API key: export EDINET_API_KEY=your_key
  - pip install httpx pyyaml pydantic rich
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.base.base_scraper import DocumentRecord, ScraperResult


# ── Optional rich console (graceful fallback like uk_tribunals.py) ───

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    class _FallbackConsole:
        @staticmethod
        def print(*args, **kwargs):
            cleaned = []
            for a in args:
                s = str(a)
                # Strip rich markup
                import re
                s = re.sub(r'\[/?[a-z_ ]+\]', '', s)
                cleaned.append(s)
            print(*cleaned)
    console = _FallbackConsole()


# ── EDINET Commands ──────────────────────────────────────────────

def _get_edinet_scraper(args):
    """Build an EdinetScraper from CLI args."""
    from scrapers.edinet import EdinetScraper, EdinetConfig

    api_key = args.api_key or os.environ.get("EDINET_API_KEY", "")
    if not api_key:
        console.print("[red]ERROR: EDINET API key required.[/red]")
        console.print("  Set EDINET_API_KEY environment variable, or pass --api-key")
        console.print("  Register free at: https://disclosure.edinet-fsa.go.jp")
        sys.exit(1)

    doc_types = args.doc_types.split(",") if hasattr(args, "doc_types") and args.doc_types else ["120"]
    config = EdinetConfig(
        api_key=api_key,
        target_doc_types=doc_types,
    )
    scraper = EdinetScraper(
        config=config,
        output_dir=Path(args.output_dir),
        rate_limit_seconds=args.delay,
    )
    return scraper


def cmd_edinet_list(args):
    """List EDINET filings for a specific date (no download)."""
    scraper = _get_edinet_scraper(args)

    console.print(f"[bold]Listing EDINET filings for {args.date}[/bold]")
    records = scraper.list_documents(date=args.date)

    if not records:
        console.print(f"[yellow]No matching filings found for {args.date}[/yellow]")
        return

    console.print(f"[green]Found {len(records)} filings[/green]\n")

    if HAS_RICH:
        table = Table(title=f"EDINET Filings — {args.date}")
        table.add_column("Doc ID", style="bold")
        table.add_column("Type")
        table.add_column("Filer")
        table.add_column("Description")
        for r in records[:50]:  # Cap display at 50
            table.add_row(r.source_id, r.document_type_label, r.filer_name, r.title)
        console.print(table)
        if len(records) > 50:
            console.print(f"  ... and {len(records) - 50} more")
    else:
        for r in records:
            print(f"  {r.source_id}  {r.filer_name}  {r.title}")


def cmd_edinet_scout(args):
    """Quick volume check across a date range (no download)."""
    scraper = _get_edinet_scraper(args)

    console.print(f"[bold]Scouting EDINET {args.start} → {args.end}[/bold]")
    records = scraper.list_date_range(args.start, args.end)

    console.print(f"\n[green]Total matching filings: {len(records)}[/green]")

    # Group by date
    by_date: dict[str, int] = {}
    for r in records:
        by_date[r.filing_date] = by_date.get(r.filing_date, 0) + 1

    if by_date and HAS_RICH:
        table = Table(title="Filings by Date")
        table.add_column("Date")
        table.add_column("Count", justify="right")
        for date in sorted(by_date.keys()):
            table.add_row(date, str(by_date[date]))
        console.print(table)

    # Estimate generation time
    if records:
        est_time_70b = len(records) * 8 * 90  # 8 segments × 90 sec on 70B
        est_time_8b = len(records) * 8 * 10   # 8 segments × 10 sec on 8B
        console.print(f"\n[bold]Generation time estimates:[/bold]")
        console.print(f"  70B model: ~{est_time_70b / 3600:.0f} hours ({est_time_70b / 86400:.1f} days)")
        console.print(f"  8B model:  ~{est_time_8b / 3600:.0f} hours ({est_time_8b / 86400:.1f} days)")


def cmd_edinet_pipeline(args):
    """Full pipeline: search → download → parse → (optional) extract taxonomy."""
    scraper = _get_edinet_scraper(args)
    start_time = time.time()

    console.print(f"[bold]EDINET Pipeline: {args.start} → {args.end}[/bold]")
    console.print(f"  Output: {args.output_dir}")
    console.print(f"  Delay: {args.delay}s between requests")
    console.print(f"  Resume: {'yes' if args.resume else 'no'}")
    console.print()

    # Phase 1-3: Scrape (list → download → parse)
    console.print("[bold]Phase 1-3: Scraping filings...[/bold]")
    result = scraper.scrape_date_range(
        start_date=args.start,
        end_date=args.end,
        download=True,
        parse=True,
    )

    console.print(f"\n[green]Scrape complete:[/green]")
    console.print(f"  Listed:     {result.total_listed}")
    console.print(f"  Downloaded: {result.total_downloaded}")
    console.print(f"  Parsed:     {result.total_parsed}")
    console.print(f"  Errors:     {result.total_errors}")

    if result.errors:
        console.print(f"\n[yellow]Errors:[/yellow]")
        for err in result.errors[:10]:
            console.print(f"  {err}")
        if len(result.errors) > 10:
            console.print(f"  ... and {len(result.errors) - 10} more")

    # Phase 4: Extract flaw taxonomy (optional)
    if args.taxonomy:
        console.print(f"\n[bold]Phase 4: Extracting flaw taxonomy...[/bold]")
        _extract_taxonomy_from_checkpoint(scraper, args)

    elapsed = time.time() - start_time
    console.print(f"\n[bold green]Pipeline complete in {elapsed:.0f}s[/bold green]")

    # Save run summary
    summary_path = Path(args.output_dir) / "edinet" / "last_run.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = result.to_dict()
    summary["elapsed_seconds"] = round(elapsed, 1)
    summary["cli_args"] = {
        "start": args.start,
        "end": args.end,
        "doc_types": args.doc_types if hasattr(args, "doc_types") else "120",
    }
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    console.print(f"  Run summary: {summary_path}")


def _extract_taxonomy_from_checkpoint(scraper, args):
    """Build flaw taxonomy from checkpoint data."""
    from scrapers.edinet.flaw_extractor import FlawExtractor

    checkpoint_path = Path(args.output_dir) / "edinet" / "checkpoint.jsonl"
    raw_dir = Path(args.output_dir) / "edinet" / "raw"

    if not checkpoint_path.exists():
        console.print("[yellow]No checkpoint file found — skipping taxonomy extraction[/yellow]")
        return

    extractor = FlawExtractor()
    analyzed = 0

    # Re-parse and analyze from saved files
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if not entry.get("parsed"):
                    continue

                # Reconstruct record from checkpoint + raw files
                source_id = entry["source_id"]
                doc_dir = raw_dir / source_id
                if doc_dir.exists():
                    # Re-parse the raw files
                    files = {}
                    for fp in doc_dir.rglob("*"):
                        if fp.is_file():
                            files[str(fp.relative_to(doc_dir))] = fp.read_bytes()

                    if files:
                        from scrapers.edinet.edinet_parser import EdinetParser
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

            except (json.JSONDecodeError, Exception) as e:
                continue

    if analyzed == 0:
        console.print("[yellow]No parsed documents found for taxonomy extraction[/yellow]")
        return

    taxonomy = extractor.build_taxonomy()
    taxonomy_path = Path(args.output_dir) / "edinet" / "flaw_taxonomy.json"
    taxonomy.save(taxonomy_path)

    console.print(f"[green]Taxonomy built from {analyzed} documents[/green]")
    console.print(f"  Categories: {len(taxonomy.categories)}")
    console.print(f"  Saved to:   {taxonomy_path}")

    if HAS_RICH and taxonomy.categories:
        table = Table(title="Top Flaw Categories")
        table.add_column("Type", style="bold")
        table.add_column("Subtype")
        table.add_column("Segment")
        table.add_column("Frequency", justify="right")
        table.add_column("Severity")
        for cat in taxonomy.categories[:15]:
            table.add_row(
                cat.flaw_type, cat.flaw_subtype, cat.segment or "any",
                f"{cat.frequency:.0%}", cat.severity,
            )
        console.print(table)


# ── Top-level Commands ───────────────────────────────────────────

def cmd_list_scrapers(args):
    """List available scrapers."""
    console.print("[bold]Available scrapers:[/bold]\n")
    scrapers = [
        ("edinet", "EDINET API v2", "Japanese securities reports (有価証券報告書)", "API key (free)"),
    ]
    if HAS_RICH:
        table = Table()
        table.add_column("Name", style="bold")
        table.add_column("Source")
        table.add_column("Description")
        table.add_column("Auth")
        for name, source, desc, auth in scrapers:
            table.add_row(name, source, desc, auth)
        console.print(table)
    else:
        for name, source, desc, auth in scrapers:
            print(f"  {name:12s}  {source:20s}  {desc}")

    console.print("\nUsage: python scrape.py <scraper> <command> [options]")
    console.print("  e.g.: python scrape.py edinet pipeline --start 2026-03-01 --end 2026-03-07")


# ── Main CLI ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Synth-Factory Scraper CLI — search, download, parse, and extract",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape.py list                                     # Show available scrapers
  python scrape.py edinet list --date 2026-03-01            # List filings for a date
  python scrape.py edinet scout --start 2026-01-01 --end 2026-03-31   # Volume check
  python scrape.py edinet pipeline --start 2026-03-01 --end 2026-03-07  # Full run
  python scrape.py edinet pipeline --start 2026-03-01 --end 2026-03-07 --taxonomy  # + flaw extraction
        """,
    )
    subparsers = parser.add_subparsers(dest="scraper", help="Scraper to use")

    # ── list command ──
    list_parser = subparsers.add_parser("list", help="List available scrapers")
    list_parser.set_defaults(func=cmd_list_scrapers)

    # ── edinet commands ──
    edinet_parser = subparsers.add_parser("edinet", help="EDINET (Japan FSA securities filings)")
    edinet_sub = edinet_parser.add_subparsers(dest="command", required=True)

    # Shared EDINET args
    def add_common_edinet_args(p):
        p.add_argument("--api-key", type=str, default="", help="EDINET API key (or set EDINET_API_KEY env)")
        p.add_argument("--output-dir", type=str, default="output/scraped", help="Output directory")
        p.add_argument("--delay", type=float, default=1.0, help="Seconds between API requests")
        p.add_argument("--doc-types", type=str, default="120", help="Comma-separated doc type codes (120=annual)")

    # edinet list
    el = edinet_sub.add_parser("list", help="List filings for a specific date")
    el.add_argument("--date", type=str, required=True, help="Date (YYYY-MM-DD)")
    add_common_edinet_args(el)
    el.set_defaults(func=cmd_edinet_list)

    # edinet scout
    es = edinet_sub.add_parser("scout", help="Volume check across a date range (no download)")
    es.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    es.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    add_common_edinet_args(es)
    es.set_defaults(func=cmd_edinet_scout)

    # edinet pipeline
    ep = edinet_sub.add_parser("pipeline", help="Full pipeline: list → download → parse → extract")
    ep.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    ep.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    ep.add_argument("--taxonomy", action="store_true", help="Also extract flaw taxonomy after scraping")
    ep.add_argument("--resume", action="store_true", help="Resume from checkpoint (skip completed docs)")
    add_common_edinet_args(ep)
    ep.set_defaults(func=cmd_edinet_pipeline)

    # Parse and dispatch
    args = parser.parse_args()

    if not args.scraper:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
