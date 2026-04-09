"""
JSONL append-only change log — one file per product.

Rule 3: Product Isolation — each product gets its own JSONL file.
Rule 4: Idempotent Triage — deduplication by hashing (url + diff + hour).

Change logs live in changes/ directory and are gitignored (they contain
operational data, not configuration).
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# In-memory set of recent hashes for deduplication within this process.
# On restart, duplicates within the same hour could reprocess — acceptable.
_recent_hashes: set[str] = set()
_MAX_HASH_CACHE = 10000

# Default changes directory (relative to config root)
_changes_dir: Path | None = None


def set_changes_dir(path: str | Path) -> None:
    """Set the directory for JSONL change log files.

    Args:
        path: Absolute or relative path to the changes/ directory.
    """
    global _changes_dir
    _changes_dir = Path(path)
    _changes_dir.mkdir(parents=True, exist_ok=True)


def _get_changes_dir() -> Path:
    """Get the changes directory, creating it if needed."""
    global _changes_dir
    if _changes_dir is None:
        # Default: changes/ in the regwatch project root
        _changes_dir = Path(__file__).parent.parent / "changes"
        _changes_dir.mkdir(parents=True, exist_ok=True)
    return _changes_dir


def compute_dedup_hash(url: str, diff_text: str) -> str:
    """Compute a deduplication hash for a change event.

    Hash is based on URL + diff text + current hour (UTC).
    Same change in the same hour = same hash = skip.

    Args:
        url: The changed URL.
        diff_text: The diff text.

    Returns:
        Hex digest of the dedup hash.
    """
    hour_key = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
    content = f"{url}|{diff_text}|{hour_key}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def is_duplicate(url: str, diff_text: str) -> bool:
    """Check if this change has already been processed this hour.

    Args:
        url: The changed URL.
        diff_text: The diff text.

    Returns:
        True if this is a duplicate (should be skipped).
    """
    h = compute_dedup_hash(url, diff_text)
    if h in _recent_hashes:
        return True

    # Evict oldest entries if cache is too large
    if len(_recent_hashes) > _MAX_HASH_CACHE:
        _recent_hashes.clear()

    _recent_hashes.add(h)
    return False


def append_change(
    product: str,
    url: str,
    triage_result: dict[str, Any],
    watch_uuid: str = "",
) -> Path:
    """Append a triage result to the product's JSONL change log.

    Args:
        product: Product name (determines which .jsonl file).
        url: The URL that changed.
        triage_result: The parsed triage result from Ollama.
        watch_uuid: changedetection.io watch UUID (for cross-reference).

    Returns:
        Path to the JSONL file that was written to.
    """
    changes_dir = _get_changes_dir()
    log_file = changes_dir / f"{product}.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "watch_uuid": watch_uuid,
        **{k: v for k, v in triage_result.items() if k != "_raw_response"},
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(
        f"Logged change for {product}: {url} "
        f"({triage_result.get('urgency', '??')})"
    )
    return log_file


def read_changes(
    product: str,
    since: str | None = None,
    urgency_filter: list[str] | None = None,
) -> list[dict]:
    """Read changes from a product's JSONL log, with optional filters.

    Args:
        product: Product name.
        since: ISO date string — only return changes after this date.
        urgency_filter: List of urgency levels to include (e.g., ['P0', 'P1']).

    Returns:
        List of change entry dicts, newest first.
    """
    changes_dir = _get_changes_dir()
    log_file = changes_dir / f"{product}.jsonl"

    if not log_file.exists():
        return []

    entries = []
    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Apply date filter
            if since:
                entry_ts = entry.get("timestamp", "")
                if entry_ts < since:
                    continue

            # Apply urgency filter
            if urgency_filter:
                entry_urgency = entry.get("urgency", "")
                if entry_urgency not in urgency_filter:
                    continue

            entries.append(entry)

    # Return newest first
    entries.reverse()
    return entries
