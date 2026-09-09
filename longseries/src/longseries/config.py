"""Sources are data, not code (US-09). One YAML per source; adding a source is
a file plus (optionally) an adapter subclass, never a deploy.

Polarity is mandatory and never implicit: some publishers list where a thing
is possible, others where it is not. Holding that in your head inverts every
answer, invisibly, until a customer notices."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import yaml


class ConfigError(ValueError):
    pass


POLARITIES = ("lists_where_possible", "lists_where_not_possible", "lists_state")

_CADENCE_WORDS = {"daily": 1, "weekly": 7, "monthly": 30, "quarterly": 90, "yearly": 365, "annual": 365}
_ISO_DURATION = re.compile(
    r"^P(?:(?P<y>\d+)Y)?(?:(?P<mo>\d+)M)?(?:(?P<w>\d+)W)?(?:(?P<d>\d+)D)?"
    r"(?:T(?:(?P<h>\d+)H)?(?:(?P<mi>\d+)M)?(?:(?P<s>\d+)S)?)?$"
)

REQUIRED = ("source_id", "publisher", "landing_url", "declared_cadence", "polarity", "contact")

# The source_id is joined into the data root and names the source's whole tree.
# A '/', a '..' or a stray space is a typo, not an attack (sources/ is a repo file
# on a read-only mount) — but a '/'-prefixed id writes outside the mounted volume,
# into the container's writable layer, which the next `up --build` destroys, and a
# 300-character id surfaces as an uncaught ENAMETOOLONG in the schedule loop.
_SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _coerce(fn, value, key: str, p: Path):
    """int()/float() raise a plain ValueError, and ConfigError SUBCLASSES ValueError:
    `except ConfigError` never caught it, so a malformed value escaped the schedule
    loop and exited the process into a restart loop that pinged nothing."""
    try:
        return fn(value)
    except (TypeError, ValueError) as e:
        raise ConfigError(f"{p}: {key} must be a {fn.__name__}, got {value!r}") from e


@dataclass
class SourceConfig:
    source_id: str
    publisher: str
    landing_url: str
    declared_cadence: timedelta
    polarity: str
    contact: str
    accept_extensions: list[str] = field(default_factory=lambda: [".pdf"])
    min_payload_bytes: int = 1024
    licence: str = "none-analysed"
    licence_evidence_url: str | None = None
    heartbeat_url: str | None = None
    declared_cadence_evidence: str | None = None
    stale_tolerance: float = 1.5
    # Structural expectations: a landing page that returns 200 with nothing behind it is
    # otherwise silent until the declared cadence elapses (180 days on P6M).
    expect_min_documents: int | None = None   # documents (non-landing, non-failed) a poll must find
    expect_landing_text: str | None = None    # a phrase the landing page's visible text must contain


def parse_cadence(text: str) -> timedelta:
    """'P1M', 'P7D', 'PT6H' (ISO-8601 duration subset) or daily/weekly/monthly/quarterly.
    Months are 30 days and years 365: this feeds a staleness alarm, not a calendar."""
    if not isinstance(text, str):
        raise ConfigError(f"declared_cadence must be a string, got {type(text).__name__}")
    t = text.strip()
    if t.lower() in _CADENCE_WORDS:
        return timedelta(days=_CADENCE_WORDS[t.lower()])
    m = _ISO_DURATION.match(t.upper())
    if not m or not any(m.groupdict().values()):
        raise ConfigError(f"unparseable declared_cadence {text!r}; use e.g. P1D, P7D, P1M, PT6H, or daily/weekly/monthly/quarterly")
    g = {k: int(v) if v else 0 for k, v in m.groupdict().items()}
    return timedelta(days=g["y"] * 365 + g["mo"] * 30 + g["w"] * 7 + g["d"], hours=g["h"], minutes=g["mi"], seconds=g["s"])


def load_source_config(path: str | Path) -> SourceConfig:
    p = Path(path)
    try:
        text = p.read_text()
    except OSError as e:  # a failed ./sources mount is a config problem, not a crash
        raise ConfigError(f"{p}: cannot be read: {e}") from e
    try:
        raw = yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"{p}: invalid YAML: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"{p}: top level must be a mapping")
    missing = [k for k in REQUIRED if k not in raw or raw[k] in (None, "")]
    if missing:
        raise ConfigError(f"{p}: missing required field(s): {', '.join(missing)}")
    if not _SOURCE_ID.match(str(raw["source_id"])):
        raise ConfigError(f"{p}: source_id {raw['source_id']!r} must match {_SOURCE_ID.pattern} — "
                          f"it names a directory under the data root, so no '/', '..', spaces or 64+ characters")
    heartbeat_url = raw.get("heartbeat_url")
    if heartbeat_url is not None:
        heartbeat_url = str(heartbeat_url)
        if not heartbeat_url.startswith(("http://", "https://")):
            raise ConfigError(f"{p}: heartbeat_url must be an http(s) URL, got {heartbeat_url!r} "
                              f"(an unexpanded ${{VAR}} or a bare host looks exactly like this)")
    if raw["polarity"] not in POLARITIES:
        raise ConfigError(f"{p}: polarity must be one of {POLARITIES}, got {raw['polarity']!r}")
    exts = raw.get("accept_extensions")
    if exts is None:
        exts = [".pdf"]
    if not isinstance(exts, list) or not all(isinstance(e, str) and e.startswith(".") for e in exts):
        raise ConfigError(f"{p}: accept_extensions must be a list of '.ext' strings (an empty list means landing-page-only)")
    return SourceConfig(
        source_id=str(raw["source_id"]),
        publisher=str(raw["publisher"]),
        landing_url=str(raw["landing_url"]),
        declared_cadence=parse_cadence(raw["declared_cadence"]),
        polarity=str(raw["polarity"]),
        contact=str(raw["contact"]),
        accept_extensions=[e.lower() for e in exts],
        min_payload_bytes=_coerce(int, raw.get("min_payload_bytes", 1024), "min_payload_bytes", p),
        licence=str(raw.get("licence", "none-analysed")),
        licence_evidence_url=raw.get("licence_evidence_url"),
        heartbeat_url=heartbeat_url,
        declared_cadence_evidence=raw.get("declared_cadence_evidence"),
        stale_tolerance=_coerce(float, raw.get("stale_tolerance", 1.5), "stale_tolerance", p),
        expect_min_documents=(_coerce(int, raw["expect_min_documents"], "expect_min_documents", p)
                              if raw.get("expect_min_documents") is not None else None),
        expect_landing_text=(str(raw["expect_landing_text"]) if raw.get("expect_landing_text") else None),
    )
