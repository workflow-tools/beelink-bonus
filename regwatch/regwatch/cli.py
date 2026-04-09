"""
CLI — manual operations for RegWatch.

Commands:
    regwatch test-triage <url> <diff_file>   — test triage against Ollama
    regwatch replay <product> <jsonl_line>    — replay a logged change
    regwatch digest [--days=7]               — compile and send weekly digest
    regwatch status                          — show watch counts and config health

Usage:
    python -m regwatch.cli <command> [args]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from regwatch.config import load_config
from regwatch.triage import triage_change
from regwatch.digest import send_digests

logger = logging.getLogger(__name__)


def cmd_test_triage(args, config):
    """Test triage: send a URL + diff text to Ollama and print the result."""
    url = args.url
    diff_path = Path(args.diff_file)

    if not diff_path.exists():
        print(f"Error: diff file not found: {diff_path}")
        sys.exit(1)

    diff_text = diff_path.read_text()

    # Find matching watch config or use product flag
    watch_config = config.get_watch_by_url(url)
    prompt_config = None

    if watch_config:
        product = watch_config["context"]["product"]
        prompt_config = config.get_prompt(product)
    elif args.product:
        prompt_config = config.get_prompt(args.product)
        watch_config = {
            "url": url,
            "context": {
                "product": args.product,
                "corridors": [],
                "likely_steps": [],
                "likely_fields": [],
                "note": "CLI test",
            },
        }
    else:
        watch_config = {
            "url": url,
            "context": {"product": "test", "note": "CLI test"},
        }

    print(f"Triaging: {url}")
    print(f"Diff length: {len(diff_text)} chars")
    print("Sending to Ollama...")

    try:
        result = triage_change(
            url=url,
            diff_text=diff_text,
            watch_config=watch_config,
            prompt_config=prompt_config,
        )
        print("\nTriage Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\nTriage failed: {e}")
        sys.exit(1)


def cmd_digest(args, config):
    """Compile and send weekly digest emails."""
    days = args.days or 7
    print(f"Compiling digest for the past {days} days...")
    send_digests(config, lookback_days=days)
    print("Done.")


def cmd_status(args, config):
    """Print configuration status."""
    print(f"RegWatch Configuration Status")
    print(f"{'='*40}")
    print(f"Products: {len(config.products)}")
    for name, product in config.products.items():
        print(f"  - {name}: {product.get('display_name', name)}")

    print(f"\nWatches: {config.watch_count()} total")
    for name, watches in config.get_all_watches().items():
        print(f"  - {name}: {len(watches)} URLs")

    print(f"\nPrompts: {len(config.prompts)}")
    for name in config.prompts:
        print(f"  - {name}_triage.yaml")


def main():
    parser = argparse.ArgumentParser(description="RegWatch CLI")
    parser.add_argument(
        "--config-dir",
        default=None,
        help="Path to RegWatch config directory",
    )
    subparsers = parser.add_subparsers(dest="command")

    # test-triage
    p_triage = subparsers.add_parser("test-triage", help="Test triage with Ollama")
    p_triage.add_argument("url", help="URL to simulate change for")
    p_triage.add_argument("diff_file", help="Path to a file containing diff text")
    p_triage.add_argument("--product", help="Product name for prompt context")

    # digest
    p_digest = subparsers.add_parser("digest", help="Compile and send weekly digest")
    p_digest.add_argument("--days", type=int, default=7, help="Lookback period in days")

    # status
    subparsers.add_parser("status", help="Show configuration status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    logging.basicConfig(level=logging.INFO)
    config = load_config(args.config_dir)

    if args.command == "test-triage":
        cmd_test_triage(args, config)
    elif args.command == "digest":
        cmd_digest(args, config)
    elif args.command == "status":
        cmd_status(args, config)


if __name__ == "__main__":
    main()
