"""The commands an operator actually runs when something looks wrong. These must
work on a DAMAGED store: that is the only situation in which they are run."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

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
