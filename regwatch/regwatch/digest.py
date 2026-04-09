"""
Weekly digest compiler — aggregates JSONL changes and sends a summary email.

Runs on a cron schedule (e.g., Sunday 06:05 UTC) and compiles all P2/P3
changes from the past week into a single digest email per product.

The digest is the notification path for lower-urgency changes that don't
warrant immediate email/GitHub Issue alerts.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from regwatch.config import RegWatchConfig
from regwatch.log import read_changes
from regwatch.notify import _send_email

logger = logging.getLogger(__name__)


def compile_digest(
    config: RegWatchConfig,
    lookback_days: int = 7,
) -> dict[str, list[dict]]:
    """Compile weekly digest for all products.

    Args:
        config: Loaded RegWatch configuration.
        lookback_days: Number of days to look back for changes.

    Returns:
        Dict mapping product name → list of change entries in the digest.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    digests: dict[str, list[dict]] = {}

    for product_name in config.products:
        changes = read_changes(product_name, since=since)
        if changes:
            digests[product_name] = changes
            logger.info(
                f"Digest for {product_name}: {len(changes)} changes "
                f"in the past {lookback_days} days"
            )

    return digests


def send_digests(config: RegWatchConfig, lookback_days: int = 7) -> None:
    """Compile and send weekly digest emails for all products.

    Args:
        config: Loaded RegWatch configuration.
        lookback_days: Number of days to look back.
    """
    digests = compile_digest(config, lookback_days)

    for product_name, changes in digests.items():
        product_config = config.get_product(product_name)
        if not product_config:
            continue

        notify_config = product_config.get("notify", {})

        # Build digest triage result for the email formatter
        digest_result = _format_digest_as_triage(product_name, changes, lookback_days)

        try:
            _send_email(
                product=product_name,
                triage_result=digest_result,
                notify_config=notify_config,
            )
            logger.info(f"Weekly digest sent for {product_name}")
        except Exception as e:
            logger.error(f"Failed to send digest for {product_name}: {e}")


def _format_digest_as_triage(
    product: str, changes: list[dict], lookback_days: int
) -> dict[str, Any]:
    """Format a list of changes into a triage-like dict for the email sender.

    Args:
        product: Product name.
        changes: List of change entries.
        lookback_days: Period covered.

    Returns:
        Dict compatible with notify._format_email_body().
    """
    # Group by urgency
    by_urgency: dict[str, list] = {}
    for change in changes:
        urg = change.get("urgency", "P3")
        by_urgency.setdefault(urg, []).append(change)

    summary_parts = []
    for urg in ["P0", "P1", "P2", "P3"]:
        count = len(by_urgency.get(urg, []))
        if count:
            summary_parts.append(f"{count} {urg}")

    summary = f"Weekly digest ({lookback_days}d): {', '.join(summary_parts) or 'no changes'}"

    detail_lines = []
    for change in changes[:20]:  # Cap at 20 entries in digest
        detail_lines.append(
            f"  [{change.get('urgency', '??')}] {change.get('url', '?')}: "
            f"{change.get('summary', 'No summary')[:100]}"
        )

    return {
        "urgency": "DIGEST",
        "url": f"Digest for {product}",
        "summary": summary,
        "recommended_action": "\n".join(detail_lines) if detail_lines else "No changes this period.",
    }
