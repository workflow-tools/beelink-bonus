"""Positive proof of life (US-08). The collector pings a watchdog URL on
completion — plain on success, '/fail' on failure (healthchecks.io
convention). The watchdog alerting on a MISSING ping is the dead-man's
switch; a collector that dies quietly otherwise looks identical to one that
is working. A failing watchdog must never mask the run's own result."""
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

    def _ping(self, suffix: str) -> None:
        try:
            with httpx.Client(transport=self.transport, timeout=self.timeout) as client:
                client.get(self.url + suffix)
        except httpx.HTTPError as e:  # includes transport errors; never raise from a heartbeat
            logger.warning("heartbeat ping failed (%s%s): %s", self.url, suffix, e)

    def success(self) -> None:
        self._ping("")

    def fail(self) -> None:
        self._ping("/fail")


def run_with_heartbeat(fn: Callable[[], T], heartbeat: Heartbeat | None) -> T:
    """Run fn(); ping success if it returns a result whose .failed is falsy,
    otherwise ping fail. An exception pings fail and then propagates."""
    try:
        result = fn()
    except BaseException:
        if heartbeat is not None:
            heartbeat.fail()
        raise
    if heartbeat is not None:
        if getattr(result, "failed", False):
            heartbeat.fail()
        else:
            heartbeat.success()
    return result
