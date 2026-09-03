"""Positive proof of life (US-08), and the whole alert path.

Every run pings a watchdog URL (healthchecks.io convention): a plain GET on a
clean run, a POST to <url>/fail carrying the alert text on a failed run or
any P0/P1 alert. The watchdog alerting on a MISSING ping is the dead-man's
switch — a collector that dies quietly otherwise looks identical to one that
works — and its email/push on a /fail ping is the alert router. One external
service, both jobs. A failing watchdog must never mask the run's own result."""
from __future__ import annotations

import logging
from typing import Callable, TypeVar

import httpx

logger = logging.getLogger(__name__)
T = TypeVar("T")


class Heartbeat:
    def __init__(self, url: str, *, transport: httpx.BaseTransport | None = None, timeout: float = 10.0):
        self.url = url.rstrip("/")
        self.transport = transport
        self.timeout = timeout

    def _send(self, suffix: str, body: str | None) -> None:
        try:
            with httpx.Client(transport=self.transport, timeout=self.timeout) as client:
                if body is None:
                    client.get(self.url + suffix)
                else:
                    client.post(self.url + suffix, content=body[:100_000].encode("utf-8"))
        except httpx.HTTPError as e:  # never raise from a heartbeat
            logger.warning("heartbeat ping failed (%s%s): %s", self.url, suffix, e)

    def success(self) -> None:
        self._send("", None)

    def fail(self, message: str = "") -> None:
        self._send("/fail", message or "run failed")


def _alert_text(result) -> str:
    alerts = getattr(result, "alerts", None) or []
    return "\n".join(f"{a.severity} {a.code}: {a.message}" for a in alerts)


def run_with_heartbeat(fn: Callable[[], T], heartbeat: Heartbeat | None) -> T:
    """Run fn(). Ping /fail (with the alert text) if it raises, returns a result
    with .failed set, or returns any P0/P1 alert; otherwise ping success. An
    exception propagates after the fail ping."""
    try:
        result = fn()
    except BaseException as e:
        if heartbeat is not None:
            heartbeat.fail(f"crashed: {e!r}")
        raise
    if heartbeat is not None:
        alerts = getattr(result, "alerts", None) or []
        severe = any(getattr(a, "severity", "") in ("P0", "P1") for a in alerts)
        if getattr(result, "failed", False) or severe:
            heartbeat.fail(_alert_text(result) or "run failed")
        else:
            heartbeat.success()
    return result
