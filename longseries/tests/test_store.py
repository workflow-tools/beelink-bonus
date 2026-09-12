"""US-01, US-02, US-03 — the bronze layer. This is the asset; everything else
is disposable. Nothing here may ever overwrite."""
from __future__ import annotations

import hashlib
import json
from datetime import timedelta

import pytest

from longseries.store import Disposition


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
    assert r["role"] == "document"


def test_store_record_role_is_persisted_in_the_index(store, now):
    """Parsers select on role from the INDEX record. An earlier build put role only
    in the manifest; the synthetic test fixture injected it by hand and hid the
    gap, and the live TransnetBW extract returned zero rows."""
    store.save("test-tso", "https://example.test/landing", b"<html>", now, http_status=200, headers={},
               discovered_on="https://example.test/landing", capture_id="c1", role="landing")
    assert store.versions("test-tso", "https://example.test/landing")[0]["role"] == "landing"


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
    assert all(json.loads(line)["capture_id"] == "c1" for line in lines)


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


# --------------------------------------------------------- torn index (LS-1s)
# A partial trailing line — what ENOSPC or a SIGKILL inside a buffered flush
# leaves — used to poison the whole index permanently: versions(), last_change_at()
# and the next save() (which calls versions()) all raised a bare JSONDecodeError,
# so every future poll died at the landing page over years of undamaged rows.

def test_a_torn_trailing_index_line_names_itself_instead_of_raising_json_errors(store, now):
    from longseries.store import IndexCorrupt
    for i in range(3):
        store.save("test-tso", f"https://example.test/{i}", f"v{i}".encode(), now,
                   http_status=200, headers={}, discovered_on="x", capture_id="c1")
    idx = store.index_path("test-tso")
    with open(idx, "a", encoding="utf-8") as f:
        f.write('{"capture_id": "c2", "source_url": "https://example.test/3", "sha2')
    with pytest.raises(IndexCorrupt) as e:
        store.versions("test-tso", "https://example.test/0")
    assert e.value.source_id == "test-tso" and e.value.lineno == 4
    assert str(idx) in str(e.value), "the operator must be told which file to repair"


def test_repair_trims_a_torn_trailing_line_and_keeps_every_good_row(store, now):
    for i in range(3):
        store.save("test-tso", f"https://example.test/{i}", f"v{i}".encode(), now,
                   http_status=200, headers={}, discovered_on="x", capture_id="c1")
    intact = store.index_path("test-tso").read_bytes()
    with open(store.index_path("test-tso"), "a", encoding="utf-8") as f:
        f.write('{"capture_id": "c2", "sha2')
    assert store.repair_index("test-tso") == 26
    assert store.index_path("test-tso").read_bytes() == intact
    assert len(store.versions("test-tso", "https://example.test/0")) == 1
    store.save("test-tso", "https://example.test/9", b"after", now,
               http_status=200, headers={}, discovered_on="x", capture_id="c3")


def test_repair_refuses_to_drop_a_corrupt_line_that_is_not_the_last(store, now):
    from longseries.store import IndexCorrupt
    store.save("test-tso", "https://example.test/0", b"v0", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    idx = store.index_path("test-tso")
    idx.write_bytes(b'{"broken\n' + idx.read_bytes())
    with pytest.raises(IndexCorrupt):
        store.repair_index("test-tso"), "silently dropping a mid-file row would lose a capture"


def test_a_failed_index_append_leaves_the_index_byte_identical(store, now, monkeypatch):
    """ENOSPC halfway through the row. Without a rollback the torn line stays on
    disk and every later read AND write of this source dies on it."""
    for i in range(3):
        store.save("test-tso", f"https://example.test/{i}", f"v{i}".encode(), now,
                   http_status=200, headers={}, discovered_on="x", capture_id="c1")
    idx = store.index_path("test-tso")
    intact = idx.read_bytes()

    real_open = open

    def flaky_open(path, mode="r", *a, **kw):
        f = real_open(path, mode, *a, **kw)
        if "a" in mode:
            def half(s, _w=f.write):
                _w(s[: len(s) // 2])
                f.flush()
                raise OSError(28, "No space left on device")
            f.write = half
        return f

    monkeypatch.setattr("longseries.store.open", flaky_open, raising=False)
    with pytest.raises(OSError):
        store.save("test-tso", "https://example.test/4", b"v4", now,
                   http_status=200, headers={}, discovered_on="x", capture_id="c2")
    monkeypatch.undo()
    assert idx.read_bytes() == intact
    assert len(store.versions("test-tso", "https://example.test/0")) == 1
    store.save("test-tso", "https://example.test/5", b"v5", now,
               http_status=200, headers={}, discovered_on="x", capture_id="c3")
    assert len(store.versions("test-tso", "https://example.test/5")) == 1


# ------------------------------------------------- concurrent writers (LS-2s)

def test_a_concurrent_writer_cannot_publish_a_truncated_blob(store, now, monkeypatch):
    """Two writers holding the same bytes used to share one deterministic
    '<sha>.tmp'. A second writer killed mid-write left a PREFIX of the payload
    there, which the first writer then os.replace()d into place under the full
    content hash: a corrupt blob, reported as a clean 'new', never re-fetched."""
    import longseries.store as store_mod
    content = b"%PDF-1.4 " + b"x" * 4000
    sha = hashlib.sha256(content).hexdigest()
    path = store.blob_path("test-tso", sha)
    real_fsync = store_mod.os.fsync

    def sabotage(fd):
        real_fsync(fd)
        deterministic = path.with_name(path.name + ".tmp")
        if deterministic.exists():   # the other writer reopened it and was SIGKILLed
            deterministic.write_bytes(b"%PDF-trunc")

    monkeypatch.setattr(store_mod.os, "fsync", sabotage)
    cap = store.save("test-tso", "https://example.test/big.pdf", content, now,
                     http_status=200, headers={}, discovered_on="x", capture_id="c1")
    monkeypatch.undo()
    assert cap.sha256 == sha
    assert path.read_bytes() == content, "the blob must hash to the name it was filed under"
    assert not list(path.parent.glob("*.tmp")), "no scratch file may be left where a writer can publish it"


def test_an_existing_blob_is_never_replaced_by_a_second_writer(store, now):
    content = b"same bytes"
    sha = hashlib.sha256(content).hexdigest()
    store.save("test-tso", "https://example.test/a", content, now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    p = store.blob_path("test-tso", sha)
    ino = p.stat().st_ino
    store.save("test-tso", "https://example.test/b", content, now, http_status=200, headers={}, discovered_on="x", capture_id="c2")
    assert p.stat().st_ino == ino, "an existing blob is not re-published, not even with identical bytes"


# ------------------------------------------------- capture directory (LS-3s)

def test_two_runs_in_the_same_second_do_not_share_a_capture_directory(store):
    """_capture_id is second-precision. Two runs in one second used to write into
    one directory: the second run's landing.html and manifest.json overwrote the
    first run's, destroying the record of which alerts fired."""
    first = store.claim_capture_dir("test-tso", "2026-09-01T120000Z")
    second = store.claim_capture_dir("test-tso", "2026-09-01T120000Z")
    assert first == "2026-09-01T120000Z"
    assert second != first
    store.write_snapshot("test-tso", first, "landing.html", b"<html>run one</html>")
    store.write_manifest("test-tso", first, {"counts": {"new": 3}})
    store.write_snapshot("test-tso", second, "landing.html", b"<html>run two</html>")
    store.write_manifest("test-tso", second, {"counts": {"new": 0}})
    assert store.read_manifest("test-tso", first) == {"counts": {"new": 3}}
    assert (store.capture_dir("test-tso", first) / "landing.html").read_bytes() == b"<html>run one</html>"


def test_poll_claims_its_own_capture_directory(config, store, site, landing_html, now):
    from longseries.adapter import BaseAdapter
    site.set(config.landing_url, 200, landing_html.encode())
    site.set("https://example.test/robots.txt", 404)
    site.set("https://example.test/files/Netzanschluss_Kapazitaeten_2026-08.pdf", 200, b"%PDF-1.4 " + b"x" * 2000)
    site.set("https://example.test/netz/anschluss/files/07_Anschluss_v2.xlsx", 200, b"PK\x03\x04" + b"y" * 2000)
    a = BaseAdapter(config, store, transport=site.transport, sleeper=lambda s: None)
    r1 = a.poll(now=now, capture_id="2026-09-01T120000Z")
    r2 = a.poll(now=now, capture_id="2026-09-01T120000Z")
    assert r1.capture_id != r2.capture_id
    assert store.read_manifest(config.source_id, r1.capture_id)["counts"]["new"] == 3
    assert store.read_manifest(config.source_id, r2.capture_id)["counts"]["unchanged"] == 3


def test_a_complete_row_missing_only_its_newline_is_not_glued_to_the_next_append(store, now):
    """A writer killed between a row's bytes and its newline leaves a valid,
    unterminated last line. Reads coped; the next append did not — it wrote
    straight after it, gluing two rows into one line no reader could parse, and
    `repair` then trimmed BOTH as one torn line."""
    store.save("test-tso", "https://example.test/0", b"v0", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    idx = store.index_path("test-tso")
    idx.write_bytes(idx.read_bytes().rstrip(b"\n"))
    store.save("test-tso", "https://example.test/1", b"v1", now, http_status=200, headers={}, discovered_on="x", capture_id="c2")
    assert [r["source_url"] for r in store._iter_index("test-tso")] == ["https://example.test/0", "https://example.test/1"]
    assert idx.read_bytes().endswith(b"\n")


def test_repair_leaves_a_complete_but_unterminated_last_row_alone(store, now):
    store.save("test-tso", "https://example.test/0", b"v0", now, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    idx = store.index_path("test-tso")
    unterminated = idx.read_bytes().rstrip(b"\n")
    idx.write_bytes(unterminated)
    assert store.repair_index("test-tso") == 0, "a row that parses is a capture record, never damage"
    assert idx.read_bytes() == unterminated
    assert len(store.versions("test-tso", "https://example.test/0")) == 1
