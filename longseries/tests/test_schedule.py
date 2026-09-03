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
