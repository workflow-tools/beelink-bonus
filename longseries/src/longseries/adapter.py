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


def visible_text(html_bytes: bytes) -> str:
    """What a reader sees: scripts, styles and tags removed, whitespace collapsed."""
    soup = BeautifulSoup(html_bytes.decode("utf-8", errors="replace"), "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return " ".join(soup.get_text(" ").split())


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


class PayloadLimitExceeded(httpx.HTTPError):
    """A fetch that refused to end. httpx's Timeout is per connect/read/write/pool:
    there is no whole-request budget, so a server dribbling bytes just inside the
    read timeout holds one _get() open for hundreds of hours. poll() then never
    returns, so NOTHING pings — not success, not /fail — and the process is alive,
    so `restart: unless-stopped` never fires either. An httpx.HTTPError so a
    landing page becomes a failed run and a document becomes a failed disposition."""


class OversizedPayload(PayloadLimitExceeded):
    pass


class StalledDownload(PayloadLimitExceeded):
    pass


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
    landing_expectation_met: bool | None = None  # None = no expectation configured

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
    max_bytes = 256 * 1024 * 1024   # ceiling on ONE document; the biggest real one is ~10 MB
    max_request_seconds = 900.0     # whole-request wall clock, which httpx does not offer

    def __init__(self, config: SourceConfig, store: ContentAddressedStore, *,
                 transport: httpx.BaseTransport | None = None,
                 sleeper: Callable[[float], None] | None = None,
                 monotonic: Callable[[], float] | None = None):
        self.config = config
        self.store = store
        self._sleep = sleeper or time.sleep
        self._monotonic = monotonic or time.monotonic
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
                # Streamed, so the two hard limits below are enforced WHILE the bytes
                # arrive rather than after; a retryable status never downloads a body.
                with self.client.stream("GET", url) as response:
                    if response.status_code in self.retry_statuses and attempt < self.max_attempts:
                        self._sleep(self._backoff(attempt))
                        continue
                    data = bytearray()
                    deadline = self._monotonic() + self.max_request_seconds
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > self.max_bytes:
                            raise OversizedPayload(f"{url}: over {self.max_bytes} bytes; refusing to buffer it")
                        if self._monotonic() > deadline:
                            raise StalledDownload(f"{url}: still arriving after {self.max_request_seconds}s "
                                                  f"({len(data)} bytes); abandoning this fetch")
                    # iter_bytes() has already applied the content-encoding (gzip, deflate,
                    # br), so `data` is plain. Rebuilding the Response with the ORIGINAL
                    # headers made httpx decode it a second time — DecodingError on every
                    # compressed response, and every TSO serves its landing page gzipped.
                    # Drop the headers that describe the wire, not the document; the
                    # content-length httpx then fills in matches the stored blob.
                    headers = httpx.Headers(response.headers)
                    for wire_only in ("content-encoding", "content-length", "transfer-encoding"):
                        headers.pop(wire_only, None)
                    return httpx.Response(response.status_code, headers=headers, content=bytes(data),
                                          request=response.request, history=list(response.history))
            except httpx.TransportError:
                if attempt >= self.max_attempts:
                    raise
                self._sleep(self._backoff(attempt))
                continue

    def fetch_landing(self) -> httpx.Response:
        response = self._get(self.config.landing_url)
        if response.status_code in (404, 410):
            raise LandingVanished(self.config.landing_url, response.status_code)
        response.raise_for_status()
        return response

    # ------------------------------------------------- is this the document?
    # Looked for anywhere in the first KB, not only at byte 0: a maintenance page
    # served under a wrong content-type often opens with a comment or a BOM. `<!--`
    # and `<head` on their own are not HTML — an XML feed may start with either.
    _HTML_SNIFF = (b"<!doctype html", b"<html")

    @staticmethod
    def _extension(url: str) -> str:
        name = urlparse(url).path.rsplit("/", 1)[-1].lower()
        return "." + name.rsplit(".", 1)[-1] if "." in name else ""

    def _content_mismatch(self, url: str, response: httpx.Response) -> str | None:
        """A 200 whose body is not the kind of thing the URL promised. min_payload_bytes
        catches an 8 KB interstitial; a 60 KB maintenance page served at a .pdf URL
        sails past it and was recorded as a new edition — then as another one when the
        real document came back: two transitions of a document that never changed. The
        content-type header was already in the index row and read nowhere."""
        ext = self._extension(url)
        ctype = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
        head = response.content[:1024].lower()
        if ext not in (".html", ".htm", ".xhtml") and (ctype in ("text/html", "application/xhtml+xml")
                                                       or any(sig in head for sig in self._HTML_SNIFF)):
            return f"is HTML (content-type {ctype!r}) at a {ext or 'document'} URL"
        if ext == ".pdf" and not response.content.startswith(b"%PDF-"):
            return f"does not begin with %PDF- (content-type {ctype!r})"
        return None

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
        sid = self.config.source_id
        # Claim the directory before anything is written into it: it is what makes two
        # runs starting in the same second two runs on disk instead of one overwritten
        # record. The claimed id (possibly suffixed) is the run's id from here on.
        cid = self.store.claim_capture_dir(sid, capture_id or self._capture_id(now))
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
            roles = ("document",) if self.config.accept_extensions else None
            run.alerts = evaluate(
                run, self.config,
                last_change_at=self.store.last_change_at(sid, exclude_capture_id=cid, roles=roles),
                now=now,
                previously_captured=self.store.captured_urls(sid, exclude_capture_id=cid))
            manifest.update({
                "finished_at": finished.isoformat(),
                "landing_status": run.landing_status,
                "landing_sha256": run.landing_sha256,
                "robots_sha256": run.robots_sha256,
                "urls": run.dispositions,
                "counts": run.counts,
                "failed": run.failed,
                "error": run.error,
                "landing_expectation_met": run.landing_expectation_met,
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
            except (httpx.TransportError, PayloadLimitExceeded) as e:
                dispositions.append({"url": url, "disposition": "failed", "sha256": None, "http_status": None, "bytes": 0, "error": str(e)})
                continue
            if response.status_code != 200:
                dispositions.append({"url": url, "disposition": "failed", "sha256": None, "http_status": response.status_code, "bytes": len(response.content)})
                continue
            cap = self.store.save(sid, url, response.content, now,
                                  http_status=response.status_code, headers=dict(response.headers),
                                  discovered_on=str(landing.url), capture_id=cid)
            row = {"url": url, "disposition": cap.disposition.value, "sha256": cap.sha256,
                   "http_status": response.status_code, "bytes": len(response.content)}
            problem = self._content_mismatch(url, response)
            if problem:
                # Stored regardless: a block page is the evidence of when access was
                # denied, and this store never discards bytes it received.
                row["content_problem"] = problem
            dispositions.append(row)

        expect = self.config.expect_landing_text
        met = None if not expect else (expect.casefold() in visible_text(landing.content).casefold())
        return finish(RunResult(cid, sid, now, None, self.config.landing_url, landing.status_code, landing_sha, robots_sha, dispositions, [], failed=False,
                                landing_expectation_met=met))
