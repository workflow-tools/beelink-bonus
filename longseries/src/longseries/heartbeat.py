"""Positive proof of life (US-08), and the whole alert path.

Every run pings a watchdog URL (healthchecks.io convention): a plain GET on a
clean run, a POST to <url>/fail carrying the alert text on a failed run or
any P0/P1 alert. The watchdog alerting on a MISSING ping is the dead-man's
switch — a collector that dies quietly otherwise looks identical to one that
works — and its email/push on a /fail ping is the alert router. One external
service, both jobs. A failing watchdog must never mask the run's own result."""
from __future__ import annotations

import sys
import time
from typing import Callable, TypeVar
from urllib.parse import urlsplit

import httpx

T = TypeVar("T")

# There is no logging configuration anywhere in this package, so a logger.warning
# would rely on logging.lastResort. These go straight to stderr, where `docker
# logs` and a scheduler both look.
RETRY_STATUSES = (408, 429, 500, 502, 503, 504)


def redact(url: str) -> str:
    """A healthchecks.io ping URL is an unauthenticated capability: whoever holds
    it can forge success pings and mute this source's dead-man's switch forever.
    Log enough to identify the watchdog, never enough to use it."""
    try:
        parts = urlsplit(url)
    except Exception:
        return "<unparseable heartbeat url>"
    if not parts.netloc:
        return "<malformed heartbeat url>"
    path = parts.path.strip("/")
    head = path[:8] + "\u2026" if len(path) > 8 else path
    return f"{parts.netloc}/{head}" if head else parts.netloc


class Heartbeat:
    def __init__(self, url: str, *, transport: httpx.BaseTransport | None = None, timeout: float = 10.0,
                 sleeper: Callable[[float], None] = time.sleep):
        self.url = str(url).rstrip("/")
        self.transport = transport
        self.timeout = timeout
        self._sleep = sleeper

    def _send(self, suffix: str, body: str | None, *, attempts: int = 1) -> None:
        """Log and swallow, always. Narrowing this by exception class is exactly the
        sys.exit(1) mistake: httpx.InvalidURL and a bare ValueError from a malformed
        URL are not httpx.HTTPError, so they used to escape and REPLACE the run's own
        exception, and a non-2xx never raised at all — the alert was dropped with no
        log line and no retry."""
        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(transport=self.transport, timeout=self.timeout) as client:
                    if body is None:
                        response = client.get(self.url + suffix)
                    else:
                        response = client.post(self.url + suffix, content=body[:100_000].encode("utf-8"))
                if response.status_code < 300:
                    return
                problem: str = f"HTTP {response.status_code}"
                retryable = response.status_code in RETRY_STATUSES
            except Exception as e:  # never raise from a heartbeat, for ANY reason
                problem, retryable = repr(e), True
            if retryable and attempt < attempts:
                self._sleep(min(30.0, float(2 ** (attempt - 1))))
                continue
            print(f"[heartbeat] ping {redact(self.url)}{suffix} FAILED after {attempt} attempt(s): {problem}",
                  file=sys.stderr)
            return

    def success(self) -> None:
        self._send("", None)

    def fail(self, message: str = "") -> None:
        # A lost heartbeat is recoverable tomorrow; a lost alert is not.
        self._send("/fail", message or "run failed", attempts=3)


def _alert_text(result) -> str:
    alerts = getattr(result, "alerts", None) or []
    return "\n".join(f"{a.severity} {a.code}: {a.message}" for a in alerts)


def run_with_heartbeat(fn: Callable[[], T], heartbeat: Heartbeat | None) -> T:
    """Run fn(). Ping /fail (with the alert text) if it raises, returns a result
    with .failed set, or returns any P0/P1 alert; otherwise ping success. An
    exception propagates after the fail ping."""
    if heartbeat is None:
        print("[heartbeat] NO HEARTBEAT CONFIGURED — this source is UNMONITORED: "
              "nothing will notice if it stops collecting", file=sys.stderr)
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
