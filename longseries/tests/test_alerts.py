"""US-07, US-08 — fail loudly; positive proof of life."""
from __future__ import annotations

from datetime import timedelta

import httpx

from longseries.alerts import Alert, evaluate
from longseries.heartbeat import Heartbeat, run_with_heartbeat
from longseries.adapter import RunResult


def _run(dispositions, failed=False):
    return RunResult(capture_id="c", source_id="test-tso", started_at=None, finished_at=None,
                     landing_url="u", landing_status=200, landing_sha256="a" * 64, robots_sha256="b" * 64,
                     dispositions=dispositions, alerts=[], failed=failed)


def _d(url, disposition, size=5000, status=200):
    return {"url": url, "disposition": disposition, "sha256": "c" * 64, "http_status": status, "bytes": size}


def test_alerts_carry_severity_code_and_human_message():
    a = Alert(severity="P1", code="ZERO_NEW_FILES", message="no new or changed files in 45 days; declared cadence 30 days")
    assert a.severity in ("P0", "P1", "P2") and a.code and a.message


def test_alert_zero_new_files_when_cadence_expected_change(config, now):
    run = _run([_d("u1", "unchanged"), _d("u2", "unchanged")])
    alerts = evaluate(run, config, last_change_at=now - timedelta(days=45), now=now)
    assert any(a.code == "ZERO_NEW_FILES" and a.severity == "P1" for a in alerts)


def test_no_zero_new_alert_when_within_cadence_window(config, now):
    run = _run([_d("u1", "unchanged")])
    alerts = evaluate(run, config, last_change_at=now - timedelta(days=10), now=now)
    assert not any(a.code == "ZERO_NEW_FILES" for a in alerts)


def test_no_zero_new_alert_on_very_first_run(config, now):
    run = _run([_d("u1", "new")])
    alerts = evaluate(run, config, last_change_at=None, now=now)
    assert not any(a.code in ("ZERO_NEW_FILES", "STALE") for a in alerts)


def test_alert_stale_when_unchanged_longer_than_cadence_times_tolerance(config, now):
    run = _run([_d("u1", "unchanged")])
    alerts = evaluate(run, config, last_change_at=now - timedelta(days=60), now=now)
    assert any(a.code == "STALE" and a.severity == "P1" for a in alerts)
    alerts_ok = evaluate(run, config, last_change_at=now - timedelta(days=40), now=now)
    assert not any(a.code == "STALE" for a in alerts_ok), "STALE needs cadence * tolerance (1.5x); 40 < 45"


def test_alert_payload_too_small(config, now):
    run = _run([_d("u1", "new", size=120)])
    alerts = evaluate(run, config, last_change_at=None, now=now)
    a = next(x for x in alerts if x.code == "PAYLOAD_TOO_SMALL")
    assert a.severity == "P1" and "u1" in a.message


def test_unchanged_small_payload_does_not_realert(config, now):
    run = _run([_d("u1", "unchanged", size=120)])
    alerts = evaluate(run, config, last_change_at=now - timedelta(days=1), now=now)
    assert not any(a.code == "PAYLOAD_TOO_SMALL" for a in alerts)


def test_alert_landing_vanished_is_p0(config, now):
    run = _run([], failed=True)
    run.landing_status = 404
    alerts = evaluate(run, config, last_change_at=None, now=now)
    assert any(a.code == "LANDING_VANISHED" and a.severity == "P0" for a in alerts)


# ---------------------------------------------------------------- heartbeat

class _Pinger:
    def __init__(self):
        self.urls: list[str] = []
        self.bodies: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.urls.append(str(request.url))
        self.bodies.append(request.content.decode("utf-8") if request.content else "")
        return httpx.Response(200, request=request)


def test_heartbeat_pings_success_url_after_successful_run():
    p = _Pinger()
    hb = Heartbeat("https://hc.test/ping/abc", transport=httpx.MockTransport(p.handler))
    result = run_with_heartbeat(lambda: _run([_d("u", "new")]), hb)
    assert result.failed is False
    assert p.urls == ["https://hc.test/ping/abc"]


def test_heartbeat_pings_fail_url_when_run_fails():
    p = _Pinger()
    hb = Heartbeat("https://hc.test/ping/abc", transport=httpx.MockTransport(p.handler))
    run_with_heartbeat(lambda: _run([], failed=True), hb)
    assert p.urls == ["https://hc.test/ping/abc/fail"]


def test_heartbeat_pings_fail_url_when_run_raises():
    p = _Pinger()
    hb = Heartbeat("https://hc.test/ping/abc", transport=httpx.MockTransport(p.handler))

    def boom():
        raise RuntimeError("disk full")

    try:
        run_with_heartbeat(boom, hb)
    except RuntimeError:
        pass
    else:
        raise AssertionError("the original exception must propagate after the fail ping")
    assert p.urls == ["https://hc.test/ping/abc/fail"]


def test_heartbeat_pings_fail_with_alert_text_on_p1():
    """P1 alerts must reach a human. The watchdog's /fail carries the text, so
    healthchecks.io is the whole alert router — no email code to maintain."""
    p = _Pinger()
    hb = Heartbeat("https://hc.test/ping/abc", transport=httpx.MockTransport(p.handler))
    r = _run([_d("u", "unchanged")])
    r.alerts = [Alert("P1", "STALE", "content unchanged for 60 days")]
    run_with_heartbeat(lambda: r, hb)
    assert p.urls == ["https://hc.test/ping/abc/fail"]
    assert "P1 STALE: content unchanged for 60 days" in p.bodies[0]


def test_heartbeat_success_when_only_p2_alerts():
    p = _Pinger()
    hb = Heartbeat("https://hc.test/ping/abc", transport=httpx.MockTransport(p.handler))
    r = _run([_d("u", "new")])
    r.alerts = [Alert("P2", "NOTE", "informational")]
    run_with_heartbeat(lambda: r, hb)
    assert p.urls == ["https://hc.test/ping/abc"]


def test_heartbeat_crash_ping_carries_the_exception():
    p = _Pinger()
    hb = Heartbeat("https://hc.test/ping/abc", transport=httpx.MockTransport(p.handler))

    def boom():
        raise RuntimeError("disk full")

    try:
        run_with_heartbeat(boom, hb)
    except RuntimeError:
        pass
    assert p.urls == ["https://hc.test/ping/abc/fail"] and "disk full" in p.bodies[0]


def test_heartbeat_failure_itself_does_not_mask_the_run_result():
    def down(request):
        raise httpx.ConnectError("watchdog down", request=request)

    hb = Heartbeat("https://hc.test/ping/abc", transport=httpx.MockTransport(down))
    result = run_with_heartbeat(lambda: _run([_d("u", "new")]), hb)
    assert result.failed is False, "an unreachable watchdog is logged, not raised"


def test_no_heartbeat_configured_is_a_noop():
    result = run_with_heartbeat(lambda: _run([_d("u", "new")]), None)
    assert result.failed is False
