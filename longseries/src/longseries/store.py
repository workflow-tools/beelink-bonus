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
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class IndexCorrupt(Exception):
    """A line in index.jsonl is not a JSON object. Never skipped silently: a row
    that cannot be read is a capture that cannot be accounted for, and the store
    is the whole asset. `longseries repair` trims a TRAILING partial line (the
    only damage a killed writer can leave); anything else is a human's job."""

    def __init__(self, source_id: str, path: Path, lineno: int, detail: str):
        super().__init__(f"{path}: line {lineno} is not valid JSON ({detail}). "
                         f"Run `longseries repair` if it is a torn trailing line; do not edit blind.")
        self.source_id = source_id
        self.path = path
        self.lineno = lineno


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
        # The scratch name must be unique per writer. It used to be a pure function of
        # the content hash, so two processes holding the same bytes shared one file:
        # one of them killed mid-write left a PREFIX there, which the other then
        # published under the full content hash — a corrupt blob reported as a clean
        # capture. os.link (not os.replace) finalises, so an existing blob is never
        # overwritten even under a race; the loser just returns 0.
        tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            with open(tmp, "wb") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            try:
                os.link(tmp, path)
            except FileExistsError:
                return 0
        finally:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
        return len(content)

    def save(self, source_id: str, source_url: str, content: bytes, captured_at: datetime, *,
             http_status: int, headers: dict, discovered_on: str, capture_id: str,
             role: str = "document", content_sha256: str | None = None) -> Capture:
        """content_sha256, when given, is the hash of a CANONICAL form of the payload
        (for landing pages: the visible text). Disposition is decided on it, so a
        page whose only change is a CSRF token or a viewstate is UNCHANGED. The raw
        bytes are never altered and always kept, keyed by their own hash."""
        sha = sha256_hex(content)
        key = content_sha256 or sha
        previous = self.versions(source_id, source_url)
        if not previous:
            disposition = Disposition.NEW
        elif (previous[-1].get("content_sha256") or previous[-1]["sha256"]) == key:
            disposition = Disposition.UNCHANGED
        else:
            disposition = Disposition.CHANGED

        # The row's sha256 is always the hash of the bytes THIS poll received, and those
        # bytes are always kept: a row must describe the blob it points at. An earlier
        # version aliased the row to the previous blob when only volatile tokens
        # differed; that saved ~0.1 GB/year per volatile source and broke the one
        # invariant everything above relies on. Dedup by raw hash still writes
        # nothing for a byte-identical fetch.
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
            "content_sha256": content_sha256 or sha,
        }
        self._append_index(source_id, record)
        return Capture(disposition=disposition, sha256=sha, bytes_written=bytes_written, record=record)

    # ----------------------------------------------------------- index
    def _append_index(self, source_id: str, record: dict) -> None:
        p = self.index_path(source_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        size = p.stat().st_size if p.exists() else 0
        try:
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except BaseException:
            # A half-written row poisons every later READ and every later WRITE of this
            # source (save() reads the index first), over years of undamaged rows. Roll
            # back to the last complete row before re-raising: the failed capture is
            # lost, the archive is not.
            try:
                with open(p, "r+b") as f:
                    f.truncate(size)
                    f.flush()
                    os.fsync(f.fileno())
            except OSError:
                pass
            raise

    def _iter_index(self, source_id: str):
        p = self.index_path(source_id)
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    raise IndexCorrupt(source_id, p, lineno, str(e)) from e

    def repair_index(self, source_id: str) -> int:
        """Trim a TRAILING partial line and return the bytes removed. That is the
        only damage a killed or out-of-space writer can leave. A corrupt line
        anywhere else means something else happened; it is raised, never dropped."""
        p = self.index_path(source_id)
        if not p.exists():
            return 0
        raw = p.read_bytes()
        lines = raw.split(b"\n")
        trailing = lines.pop() if raw.endswith(b"\n") is False else b""
        for lineno, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise IndexCorrupt(source_id, p, lineno, str(e)) from e
        if not trailing:
            return 0
        with open(p, "r+b") as f:
            f.truncate(len(raw) - len(trailing))
            f.flush()
            os.fsync(f.fileno())
        return len(trailing)

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
    def claim_capture_dir(self, source_id: str, capture_id: str) -> str:
        """Create the capture directory and return the capture id that was actually
        claimed. The DIRECTORY is the uniqueness token: capture ids are precise to
        the second, and two runs in one second used to write into one directory,
        the second overwriting the first's landing.html and manifest.json — the
        record of what the earlier run saw and which alerts it fired."""
        base = self.source_dir(source_id) / "captures"
        base.mkdir(parents=True, exist_ok=True)
        for n in range(1, 1000):
            cid = capture_id if n == 1 else f"{capture_id}.{n}"
            try:
                (base / cid).mkdir(exist_ok=False)
                return cid
            except FileExistsError:
                continue
        raise OSError(f"cannot claim a capture directory for {source_id} at {capture_id}")

    def write_snapshot(self, source_id: str, capture_id: str, name: str, content: bytes) -> str:
        d = self.capture_dir(source_id, capture_id)
        d.mkdir(parents=True, exist_ok=True)
        tmp = d / f"{name}.{os.getpid()}.tmp"
        with open(tmp, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, d / name)
        return sha256_hex(content)

    def write_manifest(self, source_id: str, capture_id: str, manifest: dict) -> None:
        d = self.capture_dir(source_id, capture_id)
        d.mkdir(parents=True, exist_ok=True)
        tmp = d / "manifest.json.tmp"
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        os.replace(tmp, d / "manifest.json")

    def read_manifest(self, source_id: str, capture_id: str) -> dict:
        return json.loads((self.capture_dir(source_id, capture_id) / "manifest.json").read_text(encoding="utf-8"))
