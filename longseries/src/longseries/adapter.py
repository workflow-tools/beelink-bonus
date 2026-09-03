"""Discovery, politeness, retries, and the poll loop (US-02, US-04..06).

Discovery is by scraping links from the landing page. There is deliberately
no hook for building a URL from a date: in one worked case the naming
convention changed three times in ten months and the landing page moved
sections; a template-based collector would have returned zero rows every
day and reported success, which is the same error as a self-constructed 404
running unattended forever."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from . import __version__
from .alerts import Alert, evaluate
from .config import SourceConfig
from .store import ContentAddressedStore, sha256_hex


def canonical_text_sha256(html_bytes: bytes) -> str:
    """Hash of what a reader would see: scripts, styles and tags removed, entities
    unescaped, whitespace collapsed. CSRF tokens, viewstates and cache-busters
    live in attributes and vanish here. Verified against 50Hertz, whose page
    differs in __VIEWSTATE/__EVENTVALIDATION on every fetch."""
    soup = BeautifulSoup(html_bytes.decode("utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return sha256_hex(text.encode("utf-8"))


class LandingVanished(Exception):
    """The landing page itself returned 404/410. P0: the section moved or the source is gone."""

    def __init__(self, url: str, status: int):
        super().__init__(f"landing page vanished: {url} -> {status}")
        self.url = url
        self.status = status


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
    error: str | None = None

    @property
    def counts(self) -> dict:
        c = {"new": 0, "unchanged": 0, "changed": 0, "failed": 0}
        for d in self.dispositions:
            c[d["disposition"]] += 1
        return c


_SKIP_SCHEMES = ("mailto:", "javascript:", "tel:", "data:")


class BaseAdapter:
    max_attempts = 3
    retry_statuses = (429, 500, 502, 503, 504)
    timeout_seconds = 60.0
    inter_request_delay = 1.5  # seconds between document fetches; 1-2s is the floor for public bodies

    def __init__(self, config: SourceConfig, store: ContentAddressedStore, *,
                 transport: httpx.BaseTransport | None = None,
                 sleeper: Callable[[float], None] | None = None):
        self.config = config
        self.store = store
        self._sleep = sleeper or time.sleep
        # Honest, identifiable, with a way to reach us: this is the station-5
        # withdrawal-risk mitigation, not politeness theatre.
        ua = f"longseries/{__version__} (+{config.contact}; source={config.source_id})"
        self.client = httpx.Client(
            headers={"user-agent": ua, "accept": "*/*"},
            transport=transport,
            timeout=self.timeout_seconds,
            follow_redirects=True,
        )

    # ------------------------------------------------------------ fetch
    def _backoff(self, attempt: int) -> float:
        return min(30.0, float(2 ** (attempt - 1)))

    def _get(self, url: str) -> httpx.Response:
        """GET with bounded exponential retry on 429/5xx and transport errors.
        A 404/410 is returned immediately — a dead URL is never hammered."""
        attempt = 0
        while True:
            attempt += 1
            try:
                response = self.client.get(url)
            except httpx.TransportError:
                if attempt >= self.max_attempts:
                    raise
                self._sleep(self._backoff(attempt))
                continue
            if response.status_code in self.retry_statuses and attempt < self.max_attempts:
                self._sleep(self._backoff(attempt))
                continue
            return response

    def fetch_landing(self) -> httpx.Response:
        response = self._get(self.config.landing_url)
        if response.status_code in (404, 410):
            raise LandingVanished(self.config.landing_url, response.status_code)
        response.raise_for_status()
        return response

    # -------------------------------------------------------- discovery
    def discover(self, html: str, base_url: str) -> list[str]:
        """Absolute document URLs linked from the landing page, filtered by
        accepted extension. The filter is applied to RESULTS; nothing here
        generates a URL."""
        exts = tuple(e.lower() for e in self.config.accept_extensions)
        if not exts:
            return []  # landing-only source: the page text is the payload, nothing is linked worth keeping
        soup = BeautifulSoup(html, "html.parser")
        found: list[str] = []
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            if not href or href.startswith("#") or href.lower().startswith(_SKIP_SCHEMES):
                continue
            absolute, _fragment = urldefrag(urljoin(base_url, href))
            if not absolute.lower().startswith(("http://", "https://")):
                continue
            if not urlparse(absolute).path.lower().endswith(exts):
                continue
            if absolute not in found:
                found.append(absolute)
        return found

    # ------------------------------------------------------------- poll
    @staticmethod
    def _capture_id(now: datetime) -> str:
        return now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z").replace(":", "")

    def poll(self, *, now: datetime | None = None, capture_id: str | None = None) -> RunResult:
        injected_clock = now is not None
        now = now or datetime.now(timezone.utc)
        cid = capture_id or self._capture_id(now)
        sid = self.config.source_id
        manifest: dict = {
            "capture_id": cid,
            "source_id": sid,
            "publisher": self.config.publisher,
            "started_at": now.isoformat(),
            "landing_url": self.config.landing_url,
            "polarity": self.config.polarity,
            "chassis_version": __version__,
        }

        def finish(run: RunResult) -> RunResult:
            finished = now if injected_clock else datetime.now(timezone.utc)
            run.finished_at = finished
            run.alerts = evaluate(run, self.config, last_change_at=self.store.last_change_at(sid, exclude_capture_id=cid), now=now)
            manifest.update({
                "finished_at": finished.isoformat(),
                "landing_status": run.landing_status,
                "landing_sha256": run.landing_sha256,
                "robots_sha256": run.robots_sha256,
                "urls": run.dispositions,
                "counts": run.counts,
                "failed": run.failed,
                "error": run.error,
                "alerts": [a.as_dict() for a in run.alerts],
            })
            self.store.write_manifest(sid, cid, manifest)
            return run

        try:
            landing = self.fetch_landing()
        except LandingVanished as e:
            return finish(RunResult(cid, sid, now, None, self.config.landing_url, e.status, None, None, [], [], failed=True))
        except httpx.HTTPError as e:
            # Unreachable, or still 5xx after retries. NOT vanished: a routing problem is not a
            # finding, and must never be recorded as though the source were gone.
            status = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else None
            return finish(RunResult(cid, sid, now, None, self.config.landing_url, status, None, None, [], [], failed=True,
                                    error=f"{type(e).__name__}: {e}"))

        landing_sha = self.store.write_snapshot(sid, cid, "landing.html", landing.content)
        # The landing page is itself a payload, not just metadata: TransnetBW publishes
        # its per-substation availability list as page text, and every publisher's
        # prose qualifiers drift independently of the files. Track it like a document.
        landing_cap = self.store.save(sid, self.config.landing_url, landing.content, now,
                                      http_status=landing.status_code, headers=dict(landing.headers),
                                      discovered_on=self.config.landing_url, capture_id=cid, role="landing",
                                      content_sha256=canonical_text_sha256(landing.content))
        dispositions: list[dict] = [{"url": self.config.landing_url, "role": "landing",
                                     "disposition": landing_cap.disposition.value, "sha256": landing_cap.sha256,
                                     "http_status": landing.status_code, "bytes": len(landing.content)}]

        robots_sha: str | None = None
        try:
            robots = self.client.get(urljoin(str(landing.url), "/robots.txt"))
            if robots.status_code == 200:
                robots_sha = self.store.write_snapshot(sid, cid, "robots.txt", robots.content)
        except httpx.HTTPError:
            robots_sha = None

        for i, url in enumerate(self.discover(landing.text, str(landing.url))):
            if i:
                self._sleep(self.inter_request_delay)
            try:
                response = self._get(url)
            except httpx.TransportError as e:
                dispositions.append({"url": url, "disposition": "failed", "sha256": None, "http_status": None, "bytes": 0, "error": str(e)})
                continue
            if response.status_code != 200:
                dispositions.append({"url": url, "disposition": "failed", "sha256": None, "http_status": response.status_code, "bytes": len(response.content)})
                continue
            cap = self.store.save(sid, url, response.content, now,
                                  http_status=response.status_code, headers=dict(response.headers),
                                  discovered_on=str(landing.url), capture_id=cid)
            dispositions.append({"url": url, "disposition": cap.disposition.value, "sha256": cap.sha256,
                                 "http_status": response.status_code, "bytes": len(response.content)})

        return finish(RunResult(cid, sid, now, None, self.config.landing_url, landing.status_code, landing_sha, robots_sha, dispositions, [], failed=False))
