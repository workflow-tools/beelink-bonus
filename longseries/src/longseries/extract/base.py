from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

GERMAN_MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}


class ParseError(Exception):
    pass


@runtime_checkable
class Parser(Protocol):
    """A parser is pure: bytes + capture record in, rows out. It is versioned so
    silver rows can be traced to the code that produced them and reprocessed
    selectively after a fix."""

    parser_id: str
    version: int

    def applies_to(self, record: dict) -> bool: ...

    def parse(self, content: bytes, record: dict) -> list[dict]:
        """Return rows. Each row MUST carry 'entity' (the publisher's own name for
        the thing) and 'edition' ('YYYY-MM'); everything else is source-specific
        and stays in the publisher's vocabulary — normalisation happens later."""
        ...


def edition_from_text(text: str) -> str | None:
    """'Stand April 2026' / 'Stand 04.2026' / 'Stand 05/2026' -> '2026-04'."""
    m = re.search(r"Stand\s*:?\s*(\d{1,2})[./](\d{4})", text)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    m = re.search(r"Stand\s*:?\s*([A-Za-zäöüÄÖÜ]+)\s+(\d{4})", text)
    if m and m.group(1).lower() in GERMAN_MONTHS:
        return f"{m.group(2)}-{GERMAN_MONTHS[m.group(1).lower()]:02d}"
    return None


def stamp(rows: list[dict], record: dict, parser: Parser) -> list[dict]:
    """Provenance on every row: straight back to the bytes and the code."""
    out = []
    for r in rows:
        if "entity" not in r or "edition" not in r:
            raise ParseError(f"{parser.parser_id}: row lacks entity/edition: {r}")
        out.append({
            **r,
            "source_id": record["source_id"],
            "capture_id": record["capture_id"],
            "observed_at": record["captured_at"],
            "sha256": record["sha256"],
            "source_url": record["source_url"],
            "parser_id": parser.parser_id,
            "parser_version": parser.version,
        })
    return out
