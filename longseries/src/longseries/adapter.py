from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import httpx

from .alerts import Alert
from .config import SourceConfig
from .store import ContentAddressedStore


class LandingVanished(Exception):
    """The landing page itself returned 404/410. P0."""


@dataclass
class RunResult:
    capture_id: str
    source_id: str
    started_at: datetime | None
    finished_at: datetime | None
    landing_url: str
    landing_status: int | None
    landing_sha256: str | None
    robots_sha256: str | None
    dispositions: list[dict]
    alerts: list[Alert]
    failed: bool

    @property
    def counts(self) -> dict:
        c = {"new": 0, "unchanged": 0, "changed": 0, "failed": 0}
        for d in self.dispositions:
            c[d["disposition"]] += 1
        return c


class BaseAdapter:
    max_attempts = 3

    def __init__(self, config: SourceConfig, store: ContentAddressedStore, *,
                 transport: httpx.BaseTransport | None = None,
                 sleeper: Callable[[float], None] | None = None):
        self.config = config
        self.store = store
        raise NotImplementedError

    def fetch_landing(self) -> httpx.Response:
        raise NotImplementedError

    def discover(self, html: str, base_url: str) -> list[str]:
        raise NotImplementedError

    def poll(self, *, now: datetime | None = None, capture_id: str | None = None) -> RunResult:
        raise NotImplementedError
