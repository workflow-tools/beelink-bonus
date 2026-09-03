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
    elif run.failed:
        alerts.append(Alert("P1", "LANDING_UNREACHABLE",
                            f"{config.source_id}: landing page {run.landing_url} could not be fetched "
                            f"(status {run.landing_status}, {run.error}). Unreachable is a routing problem, "
                            f"not a finding: check the network before concluding anything about the source."))

    for d in run.dispositions:
        if d.get("disposition") in ("new", "changed") and int(d.get("bytes") or 0) < config.min_payload_bytes:
            alerts.append(Alert("P1", "PAYLOAD_TOO_SMALL",
                                f"{config.source_id}: {d['url']} is {d.get('bytes')} bytes "
                                f"(< {config.min_payload_bytes}); an error page served with a 200?"))

    if not run.failed:
        docs = [d for d in run.dispositions if d.get("role") != "landing"]
        ok_docs = [d for d in docs if d.get("disposition") != "failed"]
        if config.accept_extensions and not docs:
            alerts.append(Alert("P1", "DISCOVERY_EMPTY",
                                f"{config.source_id}: landing page returned {run.landing_status} but no link matched "
                                f"{config.accept_extensions}. A redesign or a moved section looks exactly like this, and "
                                f"without this alert it would stay silent until the declared cadence elapsed."))
        if config.expect_min_documents is not None and len(ok_docs) < config.expect_min_documents:
            alerts.append(Alert("P1", "STRUCTURE_MISSING",
                                f"{config.source_id}: expected at least {config.expect_min_documents} documents, "
                                f"found {len(ok_docs)}."))
        if run.landing_expectation_met is False:
            alerts.append(Alert("P1", "STRUCTURE_MISSING",
                                f"{config.source_id}: landing page no longer contains the expected text "
                                f"{config.expect_landing_text!r}; the page structure probably changed."))

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
