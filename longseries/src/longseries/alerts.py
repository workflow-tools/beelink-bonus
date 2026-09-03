"""Fail loudly (US-07). The operator will be mid-relocation when something
breaks and cannot be relied on to notice silence.

Two alarms most home-built collectors lack: STALE (bytes identical for longer
than the declared cadence allows — every naive check passes while the source
is dead or you are eating a cache) and the heartbeat in heartbeat.py (a
missing ping is the only way to see a collector that died quietly)."""
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

    def as_dict(self) -> dict:
        return {"severity": self.severity, "code": self.code, "message": self.message}


def evaluate(run: "RunResult", config: SourceConfig, *, last_change_at: datetime | None, now: datetime) -> list[Alert]:
    alerts: list[Alert] = []

    if run.failed and run.landing_status in (404, 410):
        alerts.append(Alert("P0", "LANDING_VANISHED",
                            f"{config.source_id}: landing page {run.landing_url} returned {run.landing_status}. "
                            f"Either the section moved (needs a human) or the source is gone."))

    for d in run.dispositions:
        if d.get("disposition") in ("new", "changed") and int(d.get("bytes") or 0) < config.min_payload_bytes:
            alerts.append(Alert("P1", "PAYLOAD_TOO_SMALL",
                                f"{config.source_id}: {d['url']} is {d.get('bytes')} bytes "
                                f"(< {config.min_payload_bytes}); an error page served with a 200?"))

    if last_change_at is not None and not run.failed:
        age = now - last_change_at
        cadence = config.declared_cadence
        c = run.counts
        if c["new"] == 0 and c["changed"] == 0 and age > cadence:
            alerts.append(Alert("P1", "ZERO_NEW_FILES",
                                f"{config.source_id}: no new or changed files; last change {age.days} days ago, "
                                f"declared cadence {cadence.days} days. Collector broke, or publisher stopped."))
        if age > cadence * config.stale_tolerance:
            alerts.append(Alert("P1", "STALE",
                                f"{config.source_id}: content unchanged for {age.days} days, more than "
                                f"{config.stale_tolerance}x the declared cadence of {cadence.days} days. "
                                f"Publisher broke, or you are being served a cache."))
    return alerts
