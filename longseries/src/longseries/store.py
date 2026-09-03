from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class Disposition(str, Enum):
    NEW = "new"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    FAILED = "failed"


@dataclass
class Capture:
    disposition: Disposition
    sha256: str
    bytes_written: int
    record: dict


class ContentAddressedStore:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def blob_path(self, source_id: str, sha256: str) -> Path:
        raise NotImplementedError

    def index_path(self, source_id: str) -> Path:
        raise NotImplementedError

    def capture_dir(self, source_id: str, capture_id: str) -> Path:
        raise NotImplementedError

    def save(self, source_id: str, source_url: str, content: bytes, captured_at: datetime, *,
             http_status: int, headers: dict, discovered_on: str, capture_id: str) -> Capture:
        raise NotImplementedError

    def versions(self, source_id: str, source_url: str) -> list[dict]:
        raise NotImplementedError

    def write_snapshot(self, source_id: str, capture_id: str, name: str, content: bytes) -> str:
        raise NotImplementedError

    def write_manifest(self, source_id: str, capture_id: str, manifest: dict) -> None:
        raise NotImplementedError

    def read_manifest(self, source_id: str, capture_id: str) -> dict:
        raise NotImplementedError
