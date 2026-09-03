"""The bronze layer (US-01..03). This is the asset. Everything above it is
rebuildable from it; it is rebuildable from nothing.

Layout, per source (sources never share a directory — regwatch Rule 3):

    {base}/{source_id}/blobs/{sha[:2]}/{sha}       raw bytes, verbatim, never rewritten
    {base}/{source_id}/index.jsonl                 append-only capture records
    {base}/{source_id}/captures/{capture_id}/      manifest.json, landing.html, robots.txt, ...
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class Disposition(str, Enum):
    NEW = "new"            # URL never seen for this source
    UNCHANGED = "unchanged"  # same bytes as the URL's latest version
    CHANGED = "changed"    # new bytes at a URL we have seen; both versions kept
    FAILED = "failed"      # fetch failed; recorded, not raised


@dataclass
class Capture:
    disposition: Disposition
    sha256: str
    bytes_written: int
    record: dict


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class ContentAddressedStore:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    # ----------------------------------------------------------- paths
    def source_dir(self, source_id: str) -> Path:
        return self.base_dir / source_id

    def blob_path(self, source_id: str, sha256: str) -> Path:
        return self.source_dir(source_id) / "blobs" / sha256[:2] / sha256

    def index_path(self, source_id: str) -> Path:
        return self.source_dir(source_id) / "index.jsonl"

    def capture_dir(self, source_id: str, capture_id: str) -> Path:
        return self.source_dir(source_id) / "captures" / capture_id

    # ----------------------------------------------------------- blobs
    def _write_blob_if_absent(self, path: Path, content: bytes) -> int:
        """Atomic, and a no-op if the blob exists. An existing blob is never
        opened for writing — not even to rewrite identical bytes."""
        if path.exists():
            return 0
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return len(content)

    def save(self, source_id: str, source_url: str, content: bytes, captured_at: datetime, *,
             http_status: int, headers: dict, discovered_on: str, capture_id: str,
             role: str = "document") -> Capture:
        sha = sha256_hex(content)
        previous = self.versions(source_id, source_url)
        if not previous:
            disposition = Disposition.NEW
        elif previous[-1]["sha256"] == sha:
            disposition = Disposition.UNCHANGED
        else:
            disposition = Disposition.CHANGED

        bytes_written = self._write_blob_if_absent(self.blob_path(source_id, sha), content)

        record = {
            "capture_id": capture_id,
            "source_id": source_id,
            "source_url": source_url,
            "sha256": sha,
            "http_status": http_status,
            "headers": {str(k).lower(): str(v) for k, v in dict(headers or {}).items()},
            "captured_at": captured_at.isoformat(),
            "discovered_on": discovered_on,
            "bytes": len(content),
            "disposition": disposition.value,
            "role": role,  # "landing" or "document"; parsers select on it
        }
        self._append_index(source_id, record)
        return Capture(disposition=disposition, sha256=sha, bytes_written=bytes_written, record=record)

    # ----------------------------------------------------------- index
    def _append_index(self, source_id: str, record: dict) -> None:
        p = self.index_path(source_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _iter_index(self, source_id: str):
        p = self.index_path(source_id)
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def versions(self, source_id: str, source_url: str) -> list[dict]:
        """Every capture record for a URL, in append (chronological) order."""
        return [r for r in self._iter_index(source_id) if r["source_url"] == source_url]

    def last_change_at(self, source_id: str, *, exclude_capture_id: str | None = None) -> datetime | None:
        """When did any URL of this source last get NEW or CHANGED bytes? Feeds the
        zero-new-files and staleness alarms. Excludes the current run so a run can
        evaluate itself against history."""
        latest: datetime | None = None
        for r in self._iter_index(source_id):
            if exclude_capture_id and r["capture_id"] == exclude_capture_id:
                continue
            if r["disposition"] in (Disposition.NEW.value, Disposition.CHANGED.value):
                t = datetime.fromisoformat(r["captured_at"])
                if latest is None or t > latest:
                    latest = t
        return latest

    # ------------------------------------------------------- snapshots
    def write_snapshot(self, source_id: str, capture_id: str, name: str, content: bytes) -> str:
        d = self.capture_dir(source_id, capture_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_bytes(content)
        return sha256_hex(content)

    def write_manifest(self, source_id: str, capture_id: str, manifest: dict) -> None:
        d = self.capture_dir(source_id, capture_id)
        d.mkdir(parents=True, exist_ok=True)
        tmp = d / "manifest.json.tmp"
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        os.replace(tmp, d / "manifest.json")

    def read_manifest(self, source_id: str, capture_id: str) -> dict:
        return json.loads((self.capture_dir(source_id, capture_id) / "manifest.json").read_text(encoding="utf-8"))
