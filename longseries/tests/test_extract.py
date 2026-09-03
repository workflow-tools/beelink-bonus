"""Epic 2 — extraction framework, Amprion parser, series. Fixtures are synthetic:
a PDF generated here with the same line layout as Amprion's supplementary
document. The real document is never committed (derived facts only)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pymupdf
import pytest

from longseries.extract.amprion import AmprionSupplementaryParser
from longseries.extract.base import ParseError, edition_from_text
from longseries.extract.run import extract_source, load_silver
from longseries.extract.series import build_series, render_markdown
from longseries.store import ContentAddressedStore

LINES = ["Schaltanlage", "Spannungs-", "ebene", "Stadt/Gemeinde", "Anschlussauslegung*",
         "Voraussichtlich frühestes ", "Inbetriebnahmejahr**", "Anmerkungen",
         "Clusorth", "380 kV", "Lingen (Ems)", "(n-1)", "2035", "Es sind ausschließlich Lastanschlüsse möglich.",
         "Esch", "380 kV", "Pulheim", "(n-1)", "2032",
         "Wittenhorst", "380 kV", "Hamminkeln", "(n-0)", "2033", "Einspeisungen nur mit reduzierter Leistung.",
         "Haftungsausschluss:", "Unverbindliche Ersteinschätzung", "Stand April 2026"]


def make_pdf(lines=LINES) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    y = 40
    for l in lines:
        page.insert_text((40, y), l, fontsize=9)
        y += 14
    return doc.tobytes()


def _rec(store, content, url, sha_suffix="", role=None, captured="2026-09-03T06:00:00+00:00", cid="c1"):
    r = store.save("de-tso-amprion-netzanschluss", url, content, datetime.fromisoformat(captured),
                   http_status=200, headers={}, discovered_on="x", capture_id=cid)
    rec = r.record
    if role:
        rec["role"] = role
    return rec


# ---------------------------------------------------------------- edition

@pytest.mark.parametrize("text,expected", [
    ("… Stand April 2026", "2026-04"), ("Stand 04.2026", "2026-04"), ("Stand 05/2026", "2026-05"),
    ("Stand: 12.2025", "2025-12"), ("Stand Dezember 2025", "2025-12"), ("no date here", None),
])
def test_edition_from_text(text, expected):
    assert edition_from_text(text) == expected


# ---------------------------------------------------------------- amprion

def test_amprion_parser_applies_only_to_the_supplementary_pdf():
    p = AmprionSupplementaryParser()
    assert p.applies_to({"source_id": "de-tso-amprion-netzanschluss", "source_url": "https://x/Ergaenzendes-Dokument-04.2026.pdf"})
    assert not p.applies_to({"source_id": "de-tso-amprion-netzanschluss", "source_url": "https://x/Karte-04.2026.pdf"})
    assert not p.applies_to({"source_id": "de-tso-amprion-netzanschluss", "source_url": "https://x/Ergaenzendes.pdf", "role": "landing"})
    assert not p.applies_to({"source_id": "de-tso-transnetbw", "source_url": "https://x/Ergaenzendes.pdf"})


def test_amprion_parser_extracts_rows_with_optional_remarks():
    rows = AmprionSupplementaryParser().parse(make_pdf(), {"source_id": "de-tso-amprion-netzanschluss"})
    assert [r["entity"] for r in rows] == ["Clusorth", "Esch", "Wittenhorst"]
    assert rows[0] == {"entity": "Clusorth", "voltage_kv": 380, "municipality": "Lingen (Ems)", "design": "n-1",
                       "earliest_year": 2035, "remarks": "Es sind ausschließlich Lastanschlüsse möglich.",
                       "edition": "2026-04", "state": "available"}
    assert rows[1]["remarks"] == "" and rows[1]["design"] == "n-1"
    assert rows[2]["remarks"].startswith("Einspeisungen")


def test_amprion_parser_fails_loudly_without_an_edition():
    lines = [l for l in LINES if not l.startswith("Stand")]
    with pytest.raises(ParseError, match="Stand"):
        AmprionSupplementaryParser().parse(make_pdf(lines), {})


def test_amprion_parser_fails_loudly_on_unexpected_row_shape():
    lines = LINES[:8] + ["Clusorth", "380 kV", "Lingen", "2035", "(n-1)", "Haftungsausschluss:", "Stand April 2026"]
    with pytest.raises(ParseError, match="row shape"):
        AmprionSupplementaryParser().parse(make_pdf(lines), {})


# ------------------------------------------------------------ extract_source

def test_extract_writes_silver_rows_with_provenance(tmp_path):
    store = ContentAddressedStore(tmp_path)
    pdf = make_pdf()
    _rec(store, pdf, "https://www.amprion.net/.../Ergaenzendes-Dokument-04.2026.pdf")
    _rec(store, b"%PDF map", "https://www.amprion.net/.../Karte-04.2026.pdf")
    counts = extract_source(store, "de-tso-amprion-netzanschluss")
    assert counts == {"parsed": 1, "skipped": 0, "no_parser": 1, "failed": 0, "rows": 3}
    rows = load_silver(store, "de-tso-amprion-netzanschluss")
    assert len(rows) == 3
    r = rows[0]
    assert r["parser_id"] == "amprion-supplementary" and r["parser_version"] == 1
    assert r["observed_at"] == "2026-09-03T06:00:00+00:00" and r["capture_id"] == "c1" and len(r["sha256"]) == 64


def test_extract_is_idempotent_and_replay_reparses(tmp_path):
    store = ContentAddressedStore(tmp_path)
    _rec(store, make_pdf(), "https://x/Ergaenzendes-Dokument-04.2026.pdf")
    assert extract_source(store, "de-tso-amprion-netzanschluss")["parsed"] == 1
    assert extract_source(store, "de-tso-amprion-netzanschluss")["skipped"] == 1
    assert extract_source(store, "de-tso-amprion-netzanschluss", replay=True)["parsed"] == 1


def test_extract_failure_is_a_file_not_a_crash(tmp_path):
    store = ContentAddressedStore(tmp_path)
    rec = _rec(store, b"%PDF-1.4 not really", "https://x/Ergaenzendes-Dokument-04.2026.pdf")
    counts = extract_source(store, "de-tso-amprion-netzanschluss")
    assert counts["failed"] == 1 and counts["parsed"] == 0
    errs = list((tmp_path / "de-tso-amprion-netzanschluss" / "silver").glob("*/*.error.json"))
    assert len(errs) == 1 and json.loads(errs[0].read_text())["sha256"] == rec["sha256"]


# ------------------------------------------------------------------ series

def _row(entity, edition, observed, **f):
    return {"entity": entity, "edition": edition, "observed_at": observed, "state": "available", **f}


def test_series_detects_transitions_appearance_disappearance_and_restatement():
    rows = [
        _row("Esch", "2026-04", "2026-06-04T00:00:00+00:00", earliest_year=2032, remarks=""),
        _row("Esch", "2026-07", "2026-09-04T00:00:00+00:00", earliest_year=2034, remarks=""),   # slipped two years
        _row("Clusorth", "2026-04", "2026-06-04T00:00:00+00:00", earliest_year=2035, remarks="nur Last"),
        # Clusorth absent from 2026-07 -> disappeared (no longer listed as available)
        _row("Neu", "2026-07", "2026-09-04T00:00:00+00:00", earliest_year=2033, remarks=""),       # appeared
        _row("Kötz", "2026-04", "2026-06-04T00:00:00+00:00", earliest_year=2035, remarks="A"),
        _row("Kötz", "2026-04", "2026-06-20T00:00:00+00:00", earliest_year=2035, remarks="B"),     # restated in place
        _row("Kötz", "2026-07", "2026-09-04T00:00:00+00:00", earliest_year=2035, remarks="B"),
    ]
    s = build_series(rows)
    assert s["editions"] == ["2026-04", "2026-07"]
    assert s["transitions"] == [{"entity": "Esch", "from_edition": "2026-04", "to_edition": "2026-07",
                                 "changes": {"earliest_year": {"from": 2032, "to": 2034}}}]
    assert s["appeared"] == [{"entity": "Neu", "edition": "2026-07"}]
    assert s["disappeared"] == [{"entity": "Clusorth", "last_edition": "2026-04", "absent_from": "2026-07"}]
    assert len(s["restatements"]) == 1 and s["restatements"][0]["entity"] == "Kötz"
    assert s["restatements"][0]["changes"] == {"remarks": {"from": "A", "to": "B"}}
    md = render_markdown(s, "test")
    assert "Esch" in md and "2032" in md and "Restatements" in md
