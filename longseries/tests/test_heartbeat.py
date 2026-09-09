"""The alert path itself. Everything else in this chassis is safe because a
failure reaches a human through here; a ping that is silently dropped, or one
that replaces the run's own exception, breaks that and nothing says so."""
from __future__ import annotations

import httpx
import pytest

from longseries.heartbeat import Heartbeat, run_with_heartbeat

TOKEN_URL = "https://hc-ping.com/8f3c1e2a-SECRET-TOKEN-amprion"


def _recorder(status=200):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(status, request=request)

    return seen, httpx.MockTransport(handler)


def test_a_rejected_fail_ping_is_retried_then_shouted_about(capsys):
    """F4: the watchdog's HTTP status was never inspected. A 404/429/503 POST
    returned normally, raised nothing and logged nothing — the alert vanished
    with zero trace, and `except httpx.HTTPError` is never reached by a non-2xx."""
    seen, transport = _recorder(503)
    Heartbeat(TOKEN_URL, transport=transport, sleeper=lambda s: None).fail("P0 LANDING_VANISHED: gone")
    assert len(seen) == 3, "a lost alert is not recoverable tomorrow; retry it"
    err = capsys.readouterr().err
    assert "503" in err and "hc-ping.com" in err


def test_a_permanently_rejected_ping_is_not_retried_but_is_still_shouted_about(capsys):
    seen, transport = _recorder(404)
    Heartbeat(TOKEN_URL, transport=transport, sleeper=lambda s: None).fail("P1 STALE: 400 days")
    assert len(seen) == 1, "404 means the check is gone; hammering it helps nobody"
    assert "404" in capsys.readouterr().err


def test_a_ping_url_is_never_printed_in_full(capsys):
    """M-2: a healthchecks ping URL is an unauthenticated capability. Anyone
    holding it can forge success pings and mute the dead-man's switch forever —
    and this log line is what an operator pastes into an issue asking for help."""
    _, transport = _recorder(500)
    Heartbeat(TOKEN_URL, transport=transport, sleeper=lambda s: None).fail("boom")
    err = capsys.readouterr().err
    assert "SECRET-TOKEN" not in err and "8f3c1e2a-SECRET" not in err
    assert "hc-ping.com" in err, "the operator still needs to know which watchdog"


@pytest.mark.parametrize("url", [
    "https://hc-ping.com:notaport/uuid",   # httpx.InvalidURL — not an HTTPError
    "hc-ping.com/uuid",                    # bare ValueError
    "${LONGSERIES_HEARTBEAT_URL_AMPRION}",  # unexpanded compose variable
])
def test_a_broken_watchdog_url_never_masks_the_runs_own_exception(url):
    """F5: `except httpx.HTTPError` let InvalidURL and ValueError out of the
    heartbeat, so the schedule log read 'poll crashed: InvalidURL(...)' and the
    real cause (disk full) survived only in __context__, which is never printed.
    Narrowing this handler by exception class is the sys.exit(1) mistake again."""
    _, transport = _recorder()
    hb = Heartbeat(url, transport=transport, sleeper=lambda s: None)

    def boom():
        raise RuntimeError("disk full writing blob")

    with pytest.raises(RuntimeError, match="disk full"):
        run_with_heartbeat(boom, hb)


def test_an_unmonitored_source_says_so(capsys):
    """compose passes LONGSERIES_HEARTBEAT_URL= (empty) when the per-source var is
    unset and no source YAML sets heartbeat_url, so heartbeat is None and the run
    printed rc=0 exactly as if it were watched."""
    run_with_heartbeat(lambda: None, None)
    assert "UNMONITORED" in capsys.readouterr().err.upper()
