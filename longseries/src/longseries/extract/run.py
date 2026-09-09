"""bronze -> silver. Idempotent: a (parser@version, sha256) pair is parsed once
unless --replay. Failures are files, not log lines."""
from __future__ import annotations

import json
from pathlib import Path

from ..config import SourceConfig
from ..store import ContentAddressedStore, sha256_hex
from .base import ParseError, stamp
from .registry import select


def silver_dir(store: ContentAddressedStore, source_id: str, parser) -> Path:
    return store.source_dir(source_id) / "silver" / f"{parser.parser_id}-v{parser.version}"


def extract_source(store: ContentAddressedStore, config: SourceConfig, *, replay: bool = False) -> dict:
    source_id = config.source_id
    counts = {"parsed": 0, "skipped": 0, "no_parser": 0, "no_parser_documents": 0, "failed": 0, "rows": 0}
    for record in store._iter_index(source_id):
        if record["disposition"] not in ("new", "changed"):
            continue
        if "role" not in record:  # records written before role was stored: derive it, never guess
            record["role"] = "landing" if record["source_url"] == config.landing_url else "document"
        parser = select(record)
        if parser is None:
            counts["no_parser"] += 1
            # A landing page with no parser is normal on most sources; a DOCUMENT with
            # no parser is a renamed file or a changed convention, and the derived
            # series freezes silently while collection carries on looking healthy.
            if record.get("role") != "landing":
                counts["no_parser_documents"] += 1
            continue
        out_dir = silver_dir(store, source_id, parser)
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{record['sha256']}.jsonl"
        err = out_dir / f"{record['sha256']}.error.json"
        if out.exists() and not replay:
            counts["skipped"] += 1
            continue
        try:
            # Inside the try: a missing or short blob is a known gap in one document,
            # never a traceback that stops the whole source (and, because the index is
            # append-only, stops it again on every later run). Re-hashing here turns
            # silent blob corruption into the same visible gap.
            content = store.blob_path(source_id, record["sha256"]).read_bytes()
            actual = sha256_hex(content)
            if actual != record["sha256"]:
                raise ParseError(f"blob does not match its own name: sha256 on disk {actual}, "
                                 f"index row says {record['sha256']}")
            rows = stamp(parser.parse(content, record), record, parser)
        except Exception as e:  # a bad document is a known gap, never a crash
            err.write_text(json.dumps({"sha256": record["sha256"], "source_url": record["source_url"],
                                       "capture_id": record["capture_id"], "parser": parser.parser_id,
                                       "parser_version": parser.version, "error": f"{type(e).__name__}: {e}"}, indent=2))
            counts["failed"] += 1
            continue
        tmp = out.with_suffix(".jsonl.tmp")
        tmp.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
        tmp.replace(out)
        if err.exists():
            err.unlink()
        counts["parsed"] += 1
        counts["rows"] += len(rows)
    return counts


def load_silver(store: ContentAddressedStore, source_id: str) -> list[dict]:
    rows: list[dict] = []
    base = store.source_dir(source_id) / "silver"
    if not base.exists():
        return rows
    # One directory per parser, and only its newest version. Both used to be read:
    # a bug fix reappeared as a restatement the publisher never made, and at v10
    # sorted() put v10 before v2, so 'latest state per entity' silently reverted to
    # the old parser's answer.
    newest: dict[str, tuple[int, Path]] = {}
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        parser_id, _, version = d.name.rpartition("-v")
        key, n = (parser_id, int(version)) if parser_id and version.isdigit() else (d.name, -1)
        if key not in newest or n > newest[key][0]:
            newest[key] = (n, d)
    for _, d in sorted(newest.values(), key=lambda t: t[1].name):
        for f in sorted(d.glob("*.jsonl")):
            with open(f, encoding="utf-8") as fh:
                rows.extend(json.loads(l) for l in fh if l.strip())
    return rows
