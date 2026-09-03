"""US-01, US-02, US-03 — the bronze layer. This is the asset; everything else
is disposable. Nothing here may ever overwrite."""
from __future__ import annotations

import hashlib
import json
from datetime import timedelta

import pytest

from longseries.store import ContentAddressedStore, Disposition


def _hdrs():
    return {"etag": '"abc"', "last-modified": "Mon, 01 Sep 2026 10:00:00 GMT", "content-type": "application/pdf"}


def test_store_new_payload_is_written_under_its_sha256(store, now):
    content = b"%PDF-1.4 fake grid map"
    sha = hashlib.sha256(content).hexdigest()
    cap = store.save("test-tso", "https://example.test/a.pdf", content, now,
                     http_status=200, headers=_hdrs(), discovered_on="https://example.test/", capture_id="c1")
    assert cap.disposition == Disposition.NEW
    assert cap.sha256 == sha
    assert cap.bytes_written == len(content)
    assert store.blob_path("test-tso", sha).read_bytes() == content


def test_store_blobs_are_partitioned_by_hash_prefix(store, now):
    content = b"partition me"
    sha = hashlib.sha256(content).hexdigest()
    store.save("test-tso", "https://example.test/p.pdf", content, now,
               http_status=200, headers={}, discovered_on="x", capture_id="c1")
    p = store.blob_path("test-tso", sha)
    assert p.parent.name == sha[:2], "blobs must be sharded by the first two hex chars (ext4 inode hygiene)"
    assert p.name == sha


def test_store_identical_bytes_write_zero_new_bytes(store, now):
    content = b"identical"
    a = store.save("test-tso", "https://example.test/x", content, now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    b = store.save("test-tso", "https://example.test/x", content, now + timedelta(days=1), http_status=200, headers={}, discovered_on="x", capture_id="c2")
    assert a.disposition == Disposition.NEW
    assert b.disposition == Disposition.UNCHANGED
    assert b.bytes_written == 0
    assert a.sha256 == b.sha256


def test_store_changed_bytes_at_same_url_keep_both_versions(store, now):
    url = "https://example.test/cap.json"
    v1 = store.save("test-tso", url, b'{"v":1,"state":"GREEN"}', now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    v2 = store.save("test-tso", url, b'{"v":2,"state":"RED"}', now + timedelta(days=30), http_status=200, headers={}, discovered_on="x", capture_id="c2")
    assert v1.sha256 != v2.sha256
    assert v2.disposition == Disposition.CHANGED, "a new hash at a URL we have seen before is CHANGED, not NEW"
    assert store.blob_path("test-tso", v1.sha256).exists()
    assert store.blob_path("test-tso", v2.sha256).exists()
    assert store.blob_path("test-tso", v1.sha256).read_bytes() == b'{"v":1,"state":"GREEN"}'


def test_store_never_rewrites_an_existing_blob_even_if_asked(store, now):
    content = b"immutable"
    sha = hashlib.sha256(content).hexdigest()
    store.save("test-tso", "https://example.test/i", content, now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    p = store.blob_path("test-tso", sha)
    mtime = p.stat().st_mtime_ns
    store.save("test-tso", "https://example.test/i", content, now + timedelta(days=1), http_status=200, headers={}, discovered_on="x", capture_id="c2")
    assert p.stat().st_mtime_ns == mtime, "an existing blob must not be touched"


def test_store_record_carries_url_headers_status_timestamp_and_discovered_on(store, now):
    cap = store.save("test-tso", "https://example.test/r.pdf", b"rec", now,
                     http_status=200, headers=_hdrs(), discovered_on="https://example.test/landing", capture_id="c9")
    r = cap.record
    assert r["source_id"] == "test-tso"
    assert r["source_url"] == "https://example.test/r.pdf"
    assert r["sha256"] == cap.sha256
    assert r["http_status"] == 200
    assert r["headers"]["etag"] == '"abc"'
    assert r["captured_at"] == now.isoformat()
    assert r["discovered_on"] == "https://example.test/landing"
    assert r["capture_id"] == "c9"
    assert r["bytes"] == 3
    assert r["disposition"] == "new"


def test_store_versions_lists_every_capture_of_a_url_in_order(store, now):
    url = "https://example.test/v"
    store.save("test-tso", url, b"one", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    store.save("test-tso", url, b"one", now + timedelta(days=1), http_status=200, headers={}, discovered_on="x", capture_id="c2")
    store.save("test-tso", url, b"two", now + timedelta(days=2), http_status=200, headers={}, discovered_on="x", capture_id="c3")
    vs = store.versions("test-tso", url)
    assert [v["capture_id"] for v in vs] == ["c1", "c2", "c3"]
    assert [v["disposition"] for v in vs] == ["new", "unchanged", "changed"]
    assert vs[0]["sha256"] == vs[1]["sha256"] != vs[2]["sha256"]


def test_store_index_is_append_only_jsonl(store, now):
    store.save("test-tso", "https://example.test/a", b"a", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    store.save("test-tso", "https://example.test/b", b"b", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    idx = store.index_path("test-tso")
    lines = idx.read_text().strip().splitlines()
    assert len(lines) == 2
    assert all(json.loads(l)["capture_id"] == "c1" for l in lines)


def test_store_snapshot_writes_landing_html_under_capture(store):
    sha = store.write_snapshot("test-tso", "c1", "landing.html", b"<html>Stand: 01.08.2026</html>")
    p = store.capture_dir("test-tso", "c1") / "landing.html"
    assert p.read_bytes() == b"<html>Stand: 01.08.2026</html>"
    assert sha == hashlib.sha256(b"<html>Stand: 01.08.2026</html>").hexdigest()


def test_store_manifest_round_trips(store):
    m = {"capture_id": "c1", "source_id": "test-tso", "urls": [{"url": "u", "disposition": "new"}]}
    store.write_manifest("test-tso", "c1", m)
    assert store.read_manifest("test-tso", "c1") == m
    assert (store.capture_dir("test-tso", "c1") / "manifest.json").exists()


def test_store_isolates_sources(store, now):
    """Rule 3 from regwatch, carried over: one source's data never mixes with another's."""
    store.save("a", "https://example.test/x", b"same", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    store.save("b", "https://example.test/x", b"same", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    assert store.blob_path("a", hashlib.sha256(b"same").hexdigest()).exists()
    assert store.blob_path("b", hashlib.sha256(b"same").hexdigest()).exists()
    assert store.versions("a", "https://example.test/x")[0]["source_id"] == "a"
    assert store.versions("b", "https://example.test/x")[0]["source_id"] == "b"
