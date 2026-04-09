"""
Notification routing — email (Resend), GitHub Issues, digest queue.

Routes triage results to the appropriate channels based on the product's
urgency_routing configuration in domains.yaml.

Rule 6: No Silent Failures — if a notification channel fails, log the error
AND send a fallback notification through an alternative channel.
"""

import os
import json
import logging
from typing import Any, Optional
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

# Environment variables for secrets (never in YAML)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "regwatch@updates.mlupskill.com")


def route_notification(
    product: str,
    triage_result: dict[str, Any],
    product_config: Optional[dict],
    is_error: bool = False,
) -> None:
    """Route a triage result to the appropriate notification channels.

    Args:
        product: Product name (e.g., 'farafield').
        triage_result: Parsed triage result from Ollama.
        product_config: Product config from domains.yaml.
        is_error: If True, this is an error notification (bypass urgency routing).
    """
    if not product_config:
        logger.error(f"No product config for {product}, cannot route notification")
        return

    notify_config = product_config.get("notify", {})
    urgency_routing = product_config.get("urgency_routing", {})
    urgency = triage_result.get("urgency", "P3")

    if is_error:
        # Errors always go to email
        channels = ["email"]
    else:
        channels = urgency_routing.get(urgency, ["log_only"])

    for channel in channels:
        try:
            if channel == "email":
                _send_email(product, triage_result, notify_config, is_error)
            elif channel == "github_issue":
                _create_github_issue(product, triage_result, notify_config)
            elif channel == "weekly_digest":
                # Digest is compiled from JSONL logs by digest.py — no action needed here
                logger.info(f"[{product}] {urgency} change queued for weekly digest")
            elif channel == "log_only":
                logger.info(f"[{product}] {urgency} change logged only (no notification)")
            else:
                logger.warning(f"Unknown notification channel: {channel}")
        except Exception as e:
            logger.error(f"Notification failed for {product} via {channel}: {e}")
            # Rule 6: try fallback
            if channel != "email":
                try:
                    _send_email(
                        product,
                        triage_result,
                        notify_config,
                        is_error=True,
                        fallback_note=f"Original {channel} notification failed: {e}",
                    )
                except Exception as e2:
                    logger.critical(
                        f"BOTH {channel} and email fallback failed for {product}: {e2}"
                    )


def _send_email(
    product: str,
    triage_result: dict[str, Any],
    notify_config: dict,
    is_error: bool = False,
    fallback_note: str = "",
) -> None:
    """Send an email notification via Resend.

    Args:
        product: Product name.
        triage_result: Triage result dict.
        notify_config: Notification config from domains.yaml.
        is_error: Whether this is an error notification.
        fallback_note: Optional note if this is a fallback from another channel.
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email notification")
        return

    to_email = notify_config.get("email", "")
    if not to_email:
        logger.warning(f"No email configured for {product}")
        return

    urgency = triage_result.get("urgency", "??")
    url = triage_result.get("url", "unknown URL")
    summary = triage_result.get("summary", "No summary available")

    if is_error:
        subject = f"[RegWatch ERROR] {product}: Triage failure"
        body = (
            f"RegWatch encountered an error processing a change for {product}.\n\n"
            f"URL: {url}\n"
            f"Error: {triage_result.get('error', 'Unknown')}\n"
            f"Time: {datetime.now(timezone.utc).isoformat()}\n"
        )
        if fallback_note:
            body += f"\nNote: {fallback_note}\n"
    else:
        subject = f"[RegWatch {urgency}] {product}: {summary[:80]}"
        body = _format_email_body(product, triage_result)

    payload = {
        "from": RESEND_FROM,
        "to": [to_email],
        "subject": subject,
        "text": body,
    }

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    logger.info(f"Email sent for {product} ({urgency}) to {to_email}")


def _create_github_issue(
    product: str,
    triage_result: dict[str, Any],
    notify_config: dict,
) -> None:
    """Create a GitHub Issue with the regulatory change details.

    Args:
        product: Product name.
        triage_result: Triage result dict.
        notify_config: Notification config from domains.yaml.
    """
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not set, skipping GitHub Issue creation")
        return

    if not notify_config.get("github_issues"):
        return

    repo = notify_config.get("github_repo", "")
    if not repo:
        logger.warning(f"No github_repo configured for {product}")
        return

    urgency = triage_result.get("urgency", "??")
    summary = triage_result.get("summary", "Regulatory change detected")
    url = triage_result.get("url", "")

    title = f"[RegWatch {urgency}] {summary[:100]}"
    body = _format_github_issue_body(product, triage_result)

    labels = ["regwatch", f"urgency:{urgency.lower()}"]

    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        },
        json={
            "title": title,
            "body": body,
            "labels": labels,
        },
        timeout=30,
    )
    resp.raise_for_status()
    issue_url = resp.json().get("html_url", "")
    logger.info(f"GitHub Issue created for {product}: {issue_url}")


def _format_email_body(product: str, triage_result: dict) -> str:
    """Format a plain-text email body from a triage result."""
    lines = [
        f"RegWatch detected a regulatory change relevant to {product}.",
        "",
        f"  Urgency:     {triage_result.get('urgency', '??')}",
        f"  URL:         {triage_result.get('url', 'N/A')}",
        f"  Relevance:   {triage_result.get('relevance', 'N/A')}",
        "",
        f"Summary: {triage_result.get('summary', 'N/A')}",
        "",
        f"Recommended Action: {triage_result.get('recommended_action', 'N/A')}",
        "",
    ]

    corridors = triage_result.get("affected_corridors", [])
    if corridors:
        lines.append(f"Affected Corridors: {', '.join(corridors)}")

    steps = triage_result.get("affected_steps", [])
    if steps:
        lines.append(f"Affected Steps: {', '.join(steps)}")

    fields = triage_result.get("affected_fields", [])
    if fields:
        lines.append(f"Affected Fields: {', '.join(fields)}")

    lines.extend([
        "",
        f"Detected: {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "This is an automated notification from RegWatch.",
    ])

    return "\n".join(lines)


def _format_github_issue_body(product: str, triage_result: dict) -> str:
    """Format a GitHub Issue body in markdown from a triage result."""
    corridors = triage_result.get("affected_corridors", [])
    steps = triage_result.get("affected_steps", [])
    fields = triage_result.get("affected_fields", [])

    body = f"""## Regulatory Change Detected

**Source:** {triage_result.get('url', 'N/A')}
**Detected:** {datetime.now(timezone.utc).isoformat()}
**Urgency:** {triage_result.get('urgency', '??')}

### Impact

- **Corridors:** {', '.join(corridors) if corridors else 'N/A'}
- **Steps:** {', '.join(steps) if steps else 'N/A'}
- **Fields:** {', '.join(fields) if fields else 'N/A'}

### Summary

{triage_result.get('summary', 'No summary available.')}

### Recommended Action

{triage_result.get('recommended_action', 'Review the change manually.')}

### Verification Needed

- [ ] Confirm change against primary regulatory source
- [ ] Update pathway JSON(s)
- [ ] Run validator.ts
- [ ] Remove any // UNVERIFIED markers after confirmation
- [ ] Update Regulatory-Monitor-Guide.md if landscape changed

---
*This issue was created automatically by [RegWatch](https://github.com/mlupskill/regwatch).*
"""
    return body
