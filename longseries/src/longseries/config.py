from __future__ import annotations
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path


class ConfigError(ValueError):
    pass


POLARITIES = ("lists_where_possible", "lists_where_not_possible", "lists_state")


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


def parse_cadence(text: str) -> timedelta:
    raise NotImplementedError


def load_source_config(path: str | Path) -> SourceConfig:
    raise NotImplementedError
