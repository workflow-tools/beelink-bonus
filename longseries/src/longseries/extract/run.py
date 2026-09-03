"""bronze -> silver. Idempotent: a (parser@version, sha256) pair is parsed once
unless --replay. Failures are files, not log lines."""
from __future__ import annotations

import json
from pathlib import Path

from ..config import SourceConfig
from ..store import ContentAddressedStore
from .base import ParseError, stamp
from .registry import select


def silver_dir(store: ContentAddressedStore, source_id: str, parser) -> Path:
    return store.source_dir(source_id) / "silver" / f"{parser.parser_id}-v{parser.version}"


def extract_source(store: ContentAddressedStore, config: SourceConfig, *, replay: bool = False) -> dict:
    source_id = config.source_id
    counts = {"parsed": 0, "skipped": 0, "no_parser": 0, "failed": 0, "rows": 0}
    for record in store._iter_index(source_id):
        if record["disposition"] not in ("new", "changed"):
            continue
        if "role" not in record:  # records written before role was stored: derive it, never guess
            record["role"] = "landing" if record["source_url"] == config.landing_url else "document"
        parser = select(record)
        if parser is None:
            counts["no_parser"] += 1
            continue
        out_dir = silver_dir(store, source_id, parser)
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{record['sha256']}.jsonl"
        err = out_dir / f"{record['sha256']}.error.json"
        if out.exists() and not replay:
            counts["skipped"] += 1
            continue
        content = store.blob_path(source_id, record["sha256"]).read_bytes()
        try:
            rows = stamp(parser.parse(content, record), record, parser)
        except (ParseError, Exception) as e:  # a bad document is a known gap, never a crash
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
    for f in sorted(base.glob("*/*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            rows.extend(json.loads(l) for l in fh if l.strip())
    return rows
