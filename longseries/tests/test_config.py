"""US-09 — sources are data, not code."""
from __future__ import annotations

from datetime import timedelta

import pytest

from longseries.config import ConfigError, load_source_config, parse_cadence

YAML_OK = """
source_id: de-tso-amprion-netzanschluss
publisher: Amprion GmbH
landing_url: https://www.amprion.net/Strommarkt/Netzkunden/Netzanschluss/
declared_cadence: P1M
declared_cadence_evidence: "Stand: monthly per page footer, fetched 2026-09-03"
polarity: lists_where_possible
contact: mailto:archive@example.test
accept_extensions: [".pdf", ".xlsx"]
min_payload_bytes: 4096
licence: none-analysed
heartbeat_url: https://hc.test/ping/abc
"""


def test_source_config_loads_required_fields(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(YAML_OK)
    c = load_source_config(p)
    assert c.source_id == "de-tso-amprion-netzanschluss"
    assert c.landing_url.startswith("https://www.amprion.net/")
    assert c.declared_cadence == timedelta(days=30)
    assert c.polarity == "lists_where_possible"
    assert c.accept_extensions == [".pdf", ".xlsx"]
    assert c.min_payload_bytes == 4096
    assert c.heartbeat_url == "https://hc.test/ping/abc"


def test_source_config_rejects_missing_polarity(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(YAML_OK.replace("polarity: lists_where_possible\n", ""))
    with pytest.raises(ConfigError, match="polarity"):
        load_source_config(p)


def test_source_config_rejects_unknown_polarity(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(YAML_OK.replace("lists_where_possible", "sometimes"))
    with pytest.raises(ConfigError, match="polarity"):
        load_source_config(p)


def test_source_config_rejects_missing_contact(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(YAML_OK.replace("contact: mailto:archive@example.test\n", ""))
    with pytest.raises(ConfigError, match="contact"):
        load_source_config(p)


@pytest.mark.parametrize("text,expected", [
    ("P1D", timedelta(days=1)),
    ("P7D", timedelta(days=7)),
    ("P1M", timedelta(days=30)),
    ("P3M", timedelta(days=90)),
    ("PT6H", timedelta(hours=6)),
    ("daily", timedelta(days=1)),
    ("weekly", timedelta(days=7)),
    ("monthly", timedelta(days=30)),
    ("quarterly", timedelta(days=90)),
])
def test_source_config_parses_declared_cadence_to_timedelta(text, expected):
    assert parse_cadence(text) == expected


def test_source_config_accepts_empty_extensions_meaning_landing_only(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(YAML_OK.replace('accept_extensions: [".pdf", ".xlsx"]', "accept_extensions: []"))
    assert load_source_config(p).accept_extensions == []


def test_parse_cadence_rejects_garbage():
    with pytest.raises(ConfigError):
        parse_cadence("whenever")


def test_source_config_parses_structural_expectations(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(YAML_OK + "expect_min_documents: 3\nexpect_landing_text: Schaltfeld\n")
    c = load_source_config(p)
    assert c.expect_min_documents == 3 and c.expect_landing_text == "Schaltfeld"
    p.write_text(YAML_OK)
    c = load_source_config(p)
    assert c.expect_min_documents is None and c.expect_landing_text is None
