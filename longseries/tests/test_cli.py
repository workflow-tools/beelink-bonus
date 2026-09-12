"""The commands an operator actually runs when something looks wrong. These must
work on a DAMAGED store: that is the only situation in which they are run."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from longseries.__main__ import main
from longseries.store import ContentAddressedStore

NOW = datetime(2026, 9, 3, 6, 0, tzinfo=timezone.utc)

SOURCE_YAML = """
source_id: test-tso
publisher: Test TSO GmbH
landing_url: https://example.test/netz/
declared_cadence: P1M
polarity: lists_where_possible
contact: mailto:archive@example.test
"""


def _source(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(SOURCE_YAML, encoding="utf-8")
    return str(p)


def test_repair_trims_a_torn_trailing_index_line_from_the_cli(tmp_path, capsys):
    store = ContentAddressedStore(tmp_path / "data")
    store.save("test-tso", "https://example.test/a", b"a", NOW, http_status=200, headers={},
               discovered_on="x", capture_id="c1")
    with open(store.index_path("test-tso"), "a", encoding="utf-8") as f:
        f.write('{"capture_id": "c2", "sour')
    assert main(["repair", _source(tmp_path), "--data", str(tmp_path / "data")]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["repaired"] is True and out["bytes_removed"] == 26
    assert len(store.versions("test-tso", "https://example.test/a")) == 1


def test_validate_does_not_print_the_watchdog_token(tmp_path, capsys):
    """M-2: `validate` output is the other thing an operator pastes into an issue."""
    p = tmp_path / "s.yaml"
    p.write_text(SOURCE_YAML + "heartbeat_url: https://hc-ping.com/8f3c1e2a-SECRET-TOKEN-amprion\n", encoding="utf-8")
    assert main(["validate", str(p)]) == 0
    out = capsys.readouterr().out
    assert "SECRET-TOKEN" not in out
    assert "hc-ping.com" in out, "the operator still needs to see that one is configured, and which host"


def test_show_survives_a_capture_that_has_no_manifest(tmp_path, capsys):
    """LS-7u: PID 1 is python with no SIGTERM handler, so `docker stop` SIGKILLs
    it 10 s later — landing on a poll leaves a capture directory with no
    manifest.json. cmd_show read caps[-1] unconditionally and raised
    FileNotFoundError: the one command an operator runs to check on a collector."""
    store = ContentAddressedStore(tmp_path / "data")
    store.write_manifest("test-tso", "2026-09-01T120000Z", {"counts": {"new": 2}, "failed": False})
    store.claim_capture_dir("test-tso", "2026-09-02T120000Z")  # killed mid-poll
    assert main(["show", _source(tmp_path), "--data", str(tmp_path / "data")]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["latest"] == "2026-09-01T120000Z"
    assert out["counts"] == {"new": 2}
    assert "2026-09-02T120000Z" in json.dumps(out), "the incomplete capture must be named, not hidden"


AMPRION_YAML = """
source_id: de-tso-amprion-netzanschluss
publisher: Amprion GmbH
landing_url: https://www.amprion.net/landing
declared_cadence: P1M
polarity: lists_state
contact: mailto:archive@example.test
"""


def test_extract_does_not_report_success_when_a_document_lost_its_parser(tmp_path, capsys):
    """D3: cmd_extract returned `3 if counts['failed'] else 0` and never consulted
    no_parser, so a renamed document — the other filename convention already used
    on the same Amprion page — gave {'no_parser': 2, 'parsed': 0} and exit 0 while
    the series quietly froze."""
    p = tmp_path / "amprion.yaml"
    p.write_text(AMPRION_YAML, encoding="utf-8")
    store = ContentAddressedStore(tmp_path / "data")
    store.save("de-tso-amprion-netzanschluss", "https://x/2026.10_Ergaenzendes_Dokument_v2.pdf",
               b"%PDF-1.4 renamed", NOW, http_status=200, headers={}, discovered_on="x", capture_id="c1")
    store.save("de-tso-amprion-netzanschluss", "https://www.amprion.net/landing", b"<html/>", NOW,
               http_status=200, headers={}, discovered_on="x", capture_id="c1", role="landing")
    rc = main(["extract", str(p), "--data", str(tmp_path / "data")])
    counts = json.loads(capsys.readouterr().out)
    assert counts["no_parser_documents"] == 1, "the landing page having no parser is normal; a document is not"
    assert rc == 3


def test_show_says_never_when_nothing_has_changed_yet(tmp_path, capsys):
    """`(x or "never") and str(x)` is the string "None" when x is None — a
    timestamp field reading "None" is a value, not an answer."""
    store = ContentAddressedStore(tmp_path / "data")
    store.write_manifest("test-tso", "2026-09-01T120000Z", {"counts": {"new": 0}, "failed": False})
    assert main(["show", _source(tmp_path), "--data", str(tmp_path / "data")]) == 0
    assert json.loads(capsys.readouterr().out)["last_change_at"] == "never"


def test_setup_is_wired_into_the_cli_and_needs_no_terminal(tmp_path, capsys, monkeypatch):
    """US-10: the compose `setup` service runs exactly this. Without an API key it
    must still finish, write .env and the marker, and say UNMONITORED in capitals."""
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "test.yaml").write_text(SOURCE_YAML, encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setenv("LONGSERIES_CONTACT", "mailto:archive@example.test")
    monkeypatch.setenv("LONGSERIES_DATA", "/srv/longseries")
    monkeypatch.delenv("HEALTHCHECKS_API_KEY", raising=False)
    env = tmp_path / ".env"
    assert main(["setup", str(sources), "--data", str(data), "--env-file", str(env)]) == 0
    out = capsys.readouterr().out
    assert "UNMONITORED" in out
    assert (data / ".longseries-root").is_file()
    text = env.read_text(encoding="utf-8")
    assert "LONGSERIES_CONTACT=mailto:archive@example.test" in text
    assert "LONGSERIES_DATA=/srv/longseries" in text
    assert "LONGSERIES_HEARTBEAT_URL_TEST=" in text
