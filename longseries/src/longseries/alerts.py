from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from .config import SourceConfig

if TYPE_CHECKING:
    from .adapter import RunResult


@dataclass
class Alert:
    severity: str  # P0 | P1 | P2
    code: str
    message: str


def evaluate(run: "RunResult", config: SourceConfig, *, last_change_at: datetime | None, now: datetime) -> list[Alert]:
    raise NotImplementedError
