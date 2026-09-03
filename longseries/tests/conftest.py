"""Shared fixtures. HTTP is faked with httpx.MockTransport — no monkeypatching
of httpx internals. An earlier draft of this chassis (from a Gemini session)
patched httpx.Client.get and inspected call kwargs for headers that the
implementation set on the Client constructor; that test could never pass
against its own implementation. Injecting a transport avoids the whole class."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from longseries.config import SourceConfig
from longseries.store import ContentAddressedStore


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 9, 3, 6, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path: Path) -> ContentAddressedStore:
    return ContentAddressedStore(tmp_path / "bronze")


@pytest.fixture
def config() -> SourceConfig:
    return SourceConfig(
        source_id="test-tso",
        publisher="Test TSO GmbH",
        landing_url="https://example.test/netz/anschluss/",
        declared_cadence=timedelta(days=30),
        polarity="lists_where_possible",
        contact="mailto:archive@example.test",
        accept_extensions=[".pdf", ".xlsx", ".csv"],
        min_payload_bytes=1024,
        licence="none-analysed",
        licence_evidence_url=None,
        heartbeat_url=None,
    )


class FakeSite:
    """A tiny in-memory web site. Map URL -> (status, headers, body). Records
    every request so tests can assert on headers, retries and order."""

    def __init__(self):
        self.routes: dict[str, list[tuple[int, dict, bytes]]] = {}
        self.requests: list[httpx.Request] = []

    def set(self, url: str, status: int, body: bytes = b"", headers: dict | None = None):
        self.routes[url] = [(status, headers or {}, body)]

    def sequence(self, url: str, responses: list[tuple[int, bytes]]):
        """Serve these responses in order; the last one repeats."""
        self.routes[url] = [(s, {}, b) for s, b in responses]

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        url = str(request.url)
        if url not in self.routes:
            return httpx.Response(404, request=request)
        seq = self.routes[url]
        status, headers, body = seq[0] if len(seq) == 1 else seq.pop(0)
        return httpx.Response(status, headers=headers, content=body, request=request)

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)


@pytest.fixture
def site() -> FakeSite:
    return FakeSite()


LANDING_HTML = """<html><body>
<h2>Download Kapazitäten</h2>
<p>Diese Angaben sind unverbindlich. Stand: 01.08.2026</p>
<a href="/files/Netzanschluss_Kapazitaeten_2026-08.pdf">Karte</a>
<a href="files/07_Anschluss_v2.xlsx">Tabelle</a>
<a href="https://example.test/unrelated.html">Kontakt</a>
<a href="mailto:info@example.test">Mail</a>
<a href="javascript:void(0)">JS</a>
<a href="#top">Top</a>
</body></html>"""


@pytest.fixture
def landing_html() -> str:
    return LANDING_HTML
