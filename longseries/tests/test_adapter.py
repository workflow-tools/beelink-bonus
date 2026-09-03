"""US-02..US-06 — discovery, politeness, retries, landing-404-as-P0, manifests."""
from __future__ import annotations

import inspect

import httpx
import pytest

import longseries.adapter as adapter_mod
from longseries.adapter import BaseAdapter, LandingVanished
from longseries.store import Disposition


def _mk(site, config, store, sleeper=None):
    return BaseAdapter(config, store, transport=site.transport, sleeper=sleeper or (lambda s: None))


# ---------------------------------------------------------------- discovery

def test_discover_finds_renamed_files_without_any_date_pattern(config, store, site, landing_html):
    a = _mk(site, config, store)
    urls = a.discover(landing_html, config.landing_url)
    assert "https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf" in urls
    assert "https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx" in urls
    assert not any(u.endswith("unrelated.html") for u in urls), "extension filter applies to RESULTS, never as a generator"


def test_discover_resolves_relative_links_to_absolute(config, store, site):
    a = _mk(site, config, store)
    urls = a.discover('<a href="../x/report.pdf">r</a>', "https://example.test/netz/anschluss/")
    assert urls == ["https://example.test/netz/x/report.pdf"]


def test_discover_ignores_mailto_javascript_and_fragment_links(config, store, site, landing_html):
    a = _mk(site, config, store)
    urls = a.discover(landing_html, config.landing_url)
    assert not any(u.startswith(("mailto:", "javascript:")) or "#" in u for u in urls)


def test_base_adapter_has_no_url_template_hook():
    """Architecture guardrail. The API must offer no place to construct URLs from
    dates. The one worked case where this mattered: naming convention changed
    three times in ten months; a template-based collector would have returned
    zero rows daily and reported success."""
    assert "url_template" not in vars(BaseAdapter)
    assert "url_pattern" not in vars(BaseAdapter)
    src = inspect.getsource(adapter_mod)
    assert "strftime(" not in src, "adapter module must not format dates into URLs"


# ---------------------------------------------------------------- politeness

def test_requests_carry_user_agent_with_contact(config, store, site, landing_html):
    site.set(config.landing_url, 200, landing_html.encode())
    a = _mk(site, config, store)
    a.fetch_landing()
    ua = site.requests[-1].headers["user-agent"]
    assert "longseries" in ua.lower()
    assert "archive@example.test" in ua


def test_transient_5xx_is_retried_with_backoff_then_succeeds(config, store, site, landing_html):
    site.sequence(config.landing_url, [(503, b""), (500, b""), (200, landing_html.encode())])
    sleeps: list[float] = []
    a = _mk(site, config, store, sleeper=sleeps.append)
    r = a.fetch_landing()
    assert r.status_code == 200
    assert len([q for q in site.requests if str(q.url) == config.landing_url]) == 3
    assert len(sleeps) == 2 and sleeps[1] > sleeps[0], "exponential backoff between attempts"


def test_429_is_retried(config, store, site, landing_html):
    site.sequence(config.landing_url, [(429, b""), (200, landing_html.encode())])
    a = _mk(site, config, store)
    assert a.fetch_landing().status_code == 200


def test_retries_are_bounded_and_then_raise(config, store, site):
    site.sequence(config.landing_url, [(503, b"")] * 10)
    a = _mk(site, config, store)
    with pytest.raises(httpx.HTTPStatusError):
        a.fetch_landing()
    assert len(site.requests) == a.max_attempts
    assert a.max_attempts <= 5


# ------------------------------------------------------------ landing = P0

def test_landing_404_raises_landing_vanished(config, store, site):
    site.set(config.landing_url, 404)
    with pytest.raises(LandingVanished):
        _mk(site, config, store).fetch_landing()
    assert len(site.requests) == 1, "a 404 is never retried"


def test_landing_410_raises_landing_vanished(config, store, site):
    site.set(config.landing_url, 410)
    with pytest.raises(LandingVanished):
        _mk(site, config, store).fetch_landing()


def test_landing_vanished_produces_p0_alert(config, store, site, now):
    site.set(config.landing_url, 404)
    run = _mk(site, config, store).poll(now=now, capture_id="c1")
    assert run.failed is True
    assert any(al.severity == "P0" and al.code == "LANDING_VANISHED" for al in run.alerts)
    m = store.read_manifest(config.source_id, "c1")
    assert m["landing_status"] == 404, "even a failed run leaves a manifest"


# --------------------------------------------------------------- full poll

def _happy_site(site, config, landing_html, pdf=b"%PDF-1.4 " + b"x" * 2000, xlsx=b"PK" + b"y" * 2000):
    site.set(config.landing_url, 200, landing_html.encode(), {"content-type": "text/html"})
    site.set("https://example.test/robots.txt", 200, b"User-agent: *\nAllow: /\n")
    site.set("https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf", 200, pdf, {"content-type": "application/pdf", "etag": '"p1"'})
    site.set("https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx", 200, xlsx, {"content-type": "application/vnd.ms-excel"})


def test_poll_first_run_captures_every_discovered_document(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    run = _mk(site, config, store).poll(now=now, capture_id="c1")
    assert run.failed is False
    disp = {d["url"]: d["disposition"] for d in run.dispositions}
    assert disp == {
        "https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf": "new",
        "https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx": "new",
    }


def test_run_snapshots_landing_html_every_poll_even_when_unchanged(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    a = _mk(site, config, store)
    a.poll(now=now, capture_id="c1")
    a.poll(now=now, capture_id="c2")
    for cid in ("c1", "c2"):
        p = store.capture_dir(config.source_id, cid) / "landing.html"
        assert p.exists() and b"Stand: 01.08.2026" in p.read_bytes()


def test_run_snapshots_robots_txt_every_poll(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    _mk(site, config, store).poll(now=now, capture_id="c1")
    p = store.capture_dir(config.source_id, "c1") / "robots.txt"
    assert p.read_bytes().startswith(b"User-agent")


def test_run_manifest_records_landing_sha_and_robots_sha(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    run = _mk(site, config, store).poll(now=now, capture_id="c1")
    m = store.read_manifest(config.source_id, "c1")
    assert len(m["landing_sha256"]) == 64 and m["landing_sha256"] == run.landing_sha256
    assert len(m["robots_sha256"]) == 64


def test_run_manifest_lists_every_discovered_url_with_a_disposition(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    _mk(site, config, store).poll(now=now, capture_id="c1")
    m = store.read_manifest(config.source_id, "c1")
    urls = {u["url"] for u in m["urls"]}
    assert urls == {
        "https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf",
        "https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx",
    }
    assert all(u["disposition"] in ("new", "unchanged", "changed", "failed") for u in m["urls"])
    for k in ("capture_id", "source_id", "started_at", "finished_at", "landing_url", "landing_status"):
        assert k in m


def test_run_manifest_counts_match_dispositions(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    a = _mk(site, config, store)
    a.poll(now=now, capture_id="c1")
    run2 = a.poll(now=now, capture_id="c2")
    m = store.read_manifest(config.source_id, "c2")
    assert m["counts"] == {"new": 0, "unchanged": 2, "changed": 0, "failed": 0}
    assert run2.counts == m["counts"]


def test_second_poll_with_one_changed_file_keeps_both_versions(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    a = _mk(site, config, store)
    a.poll(now=now, capture_id="c1")
    site.set("https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf", 200, b"%PDF-1.4 " + b"z" * 2000)
    run = a.poll(now=now, capture_id="c2")
    assert run.counts == {"new": 0, "unchanged": 1, "changed": 1, "failed": 0}
    vs = store.versions(config.source_id, "https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf")
    assert len(vs) == 2 and vs[0]["sha256"] != vs[1]["sha256"]


def test_failed_fetch_is_a_disposition_not_a_crash(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    site.set("https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx", 404)
    run = _mk(site, config, store).poll(now=now, capture_id="c1")
    assert run.failed is False, "one bad document does not fail the run"
    d = {x["url"]: x for x in run.dispositions}
    assert d["https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx"]["disposition"] == "failed"
    assert d["https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx"]["http_status"] == 404
    assert d["https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf"]["disposition"] == "new"


def test_404_on_a_document_is_not_retried_and_is_recorded_as_failed(config, store, site, landing_html, now):
    _happy_site(site, config, landing_html)
    site.set("https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf", 404)
    _mk(site, config, store).poll(now=now, capture_id="c1")
    hits = [q for q in site.requests if str(q.url).endswith("2026-08.pdf")]
    assert len(hits) == 1
