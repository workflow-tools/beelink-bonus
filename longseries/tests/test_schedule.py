"""Restart-safe scheduling: a container in a restart loop must not hammer the publisher."""
from datetime import datetime, timezone, timedelta

from longseries.__main__ import seconds_until_due
from longseries.store import ContentAddressedStore


def test_no_captures_means_poll_now(tmp_path):
    assert seconds_until_due(ContentAddressedStore(tmp_path), "s", 3600, datetime.now(timezone.utc)) == 0


def test_recent_capture_waits_out_the_remainder(tmp_path):
    store = ContentAddressedStore(tmp_path)
    now = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
    store.capture_dir("s", (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H%M%SZ")).mkdir(parents=True)
    assert 2990 <= seconds_until_due(store, "s", 3600, now) <= 3010


def test_old_capture_polls_immediately(tmp_path):
    store = ContentAddressedStore(tmp_path)
    now = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
    store.capture_dir("s", (now - timedelta(days=2)).strftime("%Y-%m-%dT%H%M%SZ")).mkdir(parents=True)
    assert seconds_until_due(store, "s", 3600, now) == 0


# --- a bad source YAML must not kill the collector silently -------------------
# Regression: _load called sys.exit(1), which raises SystemExit. SystemExit is not
# an Exception, so the schedule loop's `except Exception` never caught it: the
# container exited into `restart: unless-stopped` and, because the Heartbeat is
# built after the config loads, nothing ever pinged. The only signal was a check
# going stale ~30 h later. sources/ is a mounted volume, so this fires on a hot
# edit too — the very repair path an operator abroad would use.

import httpx
import pytest

from longseries.__main__ import _load, _ping_config_failure, cmd_schedule, main
from longseries.config import ConfigError


class _Args:
    def __init__(self, source, data, every="PT1S"):
        self.source, self.data, self.every = str(source), str(data), every


class _Stop(BaseException):
    """Breaks the loop the way Ctrl-C would — deliberately not an Exception."""


def _bad_source(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("source_id: x\npublisher: y\n", encoding="utf-8")  # no landing_url/polarity/contact
    return p


def test_load_raises_instead_of_exiting(tmp_path):
    with pytest.raises(ConfigError):
        _load(str(_bad_source(tmp_path)))


def test_main_still_exits_1_on_a_bad_config(tmp_path, capsys):
    assert main(["validate", str(_bad_source(tmp_path))]) == 1
    assert "config error" in capsys.readouterr().err


def test_schedule_retries_a_bad_config_instead_of_dying(tmp_path):
    calls = []

    def sleeper(_s):
        calls.append(_s)
        if len(calls) >= 3:
            raise _Stop()

    with pytest.raises(_Stop):
        cmd_schedule(_Args(_bad_source(tmp_path), tmp_path / "data"), sleeper=sleeper)
    assert len(calls) == 3, "loop must keep retrying so a repaired YAML recovers with no restart"


def test_schedule_pings_the_watchdog_with_the_reason(tmp_path, monkeypatch):
    seen = []

    def handler(request):
        seen.append((str(request.url), request.content.decode()))
        return httpx.Response(200)

    monkeypatch.setenv("LONGSERIES_HEARTBEAT_URL", "https://hc-ping.com/uuid-test")
    transport = httpx.MockTransport(handler)

    def sleeper(_s):
        raise _Stop()

    with pytest.raises(_Stop):
        cmd_schedule(_Args(_bad_source(tmp_path), tmp_path / "data"),
                     sleeper=sleeper, heartbeat_transport=transport)
    assert len(seen) == 1
    url, body = seen[0]
    assert url.endswith("/fail"), "a config error is a failure, not a heartbeat"
    assert "config error" in body and "bad.yaml" in body


def test_config_failure_ping_is_a_noop_without_an_env_url(tmp_path, monkeypatch):
    monkeypatch.delenv("LONGSERIES_HEARTBEAT_URL", raising=False)
    assert _ping_config_failure("s.yaml", ConfigError("x")) is False


# --- a crash inside the loop must still reach the watchdog --------------------
# LS-5s: the loop's `except Exception` swallowed anything that went wrong BEFORE
# the per-source Heartbeat existed (a non-string heartbeat_url made
# Heartbeat.__init__ raise AttributeError), printed one line and slept. Three
# iterations, zero pings, `docker ps` showing the container Up. F3 is the same
# shape one class further out: only ConfigError was caught around _load.

def _watchdog(monkeypatch):
    seen = []

    def handler(request):
        seen.append((str(request.url), request.content.decode()))
        return httpx.Response(200)

    monkeypatch.setenv("LONGSERIES_HEARTBEAT_URL", "https://hc-ping.com/uuid-test")
    return seen, httpx.MockTransport(handler)


def _good_source(tmp_path):
    p = tmp_path / "good.yaml"
    p.write_text("source_id: test-tso\npublisher: p\nlanding_url: https://example.test/\n"
                 "declared_cadence: P1D\npolarity: lists_state\ncontact: mailto:a@b.test\n", encoding="utf-8")
    return p


def test_schedule_pings_when_the_poll_itself_crashes(tmp_path, monkeypatch):
    seen, transport = _watchdog(monkeypatch)

    def boom(_args):
        raise AttributeError("'int' object has no attribute 'rstrip'")

    monkeypatch.setattr("longseries.__main__.cmd_poll", boom)

    def sleeper(_s):
        raise _Stop()

    with pytest.raises(_Stop):
        cmd_schedule(_Args(_good_source(tmp_path), tmp_path / "data"),
                     sleeper=sleeper, heartbeat_transport=transport)
    assert len(seen) == 1, "a crash with no Heartbeat yet must still reach the watchdog"
    url, body = seen[0]
    assert url.endswith("/fail") and "AttributeError" in body


def test_schedule_survives_a_config_failure_that_is_not_a_config_error(tmp_path, monkeypatch):
    seen, transport = _watchdog(monkeypatch)
    monkeypatch.setattr("longseries.__main__._load",
                        lambda _p: (_ for _ in ()).throw(ValueError("invalid literal for int()")))
    calls = []

    def sleeper(_s):
        calls.append(_s)
        if len(calls) >= 2:
            raise _Stop()

    with pytest.raises(_Stop):
        cmd_schedule(_Args(_good_source(tmp_path), tmp_path / "data"),
                     sleeper=sleeper, heartbeat_transport=transport)
    assert len(calls) == 2, "the loop must retry, not exit into `restart: unless-stopped`"
    assert all(u.endswith("/fail") for u, _ in seen) and len(seen) == 2
