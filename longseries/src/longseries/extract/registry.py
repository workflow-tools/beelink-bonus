from __future__ import annotations

from .amprion import AmprionSupplementaryParser
from .base import Parser
from .transnetbw import TransnetBWLandingParser

PARSERS: list[Parser] = [AmprionSupplementaryParser(), TransnetBWLandingParser()]


def select(record: dict) -> Parser | None:
    for p in PARSERS:
        if p.applies_to(record):
            return p
    return None
