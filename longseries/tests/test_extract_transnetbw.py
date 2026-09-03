"""TransnetBW landing-page parser against a synthetic copy of the real DOM."""
from __future__ import annotations

import pytest

from longseries.extract.base import ParseError
from longseries.extract.transnetbw import TransnetBWLandingParser

HTML = """<html><body><main>
<h1>Netzanschlusskarte</h1><p>… Höchstspannungsnetz TransnetBW Stand 05/2026 …</p>
<div class="tooltip is-hidden tooltip-uw-heidelbergsued tooltip-uw-type--red"><button class="tooltip__button"></button>
 <div class="text tooltip__text"><p class="h2--preheadline">🔴 nicht verfügbar</p><h3 class="h3">Umspannwerk Heidelberg-Süd</h3></div></div>
<div class="tooltip is-hidden tooltip-uw-daxlanden tooltip-uw-type--yellow"><button class="tooltip__button"></button>
 <div class="text tooltip__text"><p class="h2--preheadline">🟡 langfristig verfügbar</p><h3 class="h3">Umspannwerk Daxlanden</h3>
 <ul><li>Spannungsebene: 380 kV</li><li>Inbetriebnahme Netzanschluss: voraussichtlich frühestens 2035</li><li>Anschlussart: n–1</li>
 <li>Verfügbare Einspeisekapazität: 0 MW</li><li>Verfügbare Lastkapazität: 500 – 1.000 MW</li></ul></div></div>
<div class="tooltip is-hidden tooltip-uw-altbach tooltip-uw-type--green"><button class="tooltip__button"></button>
 <div class="text tooltip__text"><p class="h2--preheadline">🟢 mittelfristig verfügbar</p><h3 class="h3">Umspannwerk Altbach</h3>
 <ul><li>temporärer Anschluss bis 2045</li><li>Spannungsebene: 380 kV</li><li>Inbetriebnahme Netzanschluss: voraussichtlich frühestens 2032</li>
 <li>Anschlussart: n–0 und n–1</li><li>Verfügbare Einspeisekapazität: 500 - 1.000 MW</li><li>Verfügbare Lastkapazität: &lt; 500 MW</li></ul></div></div>
</main></body></html>"""

REC = {"source_id": "de-tso-transnetbw-netzanschlusskarte", "role": "landing"}


def test_applies_only_to_transnetbw_landing():
    p = TransnetBWLandingParser()
    assert p.applies_to(REC)
    assert not p.applies_to({"source_id": "de-tso-transnetbw-netzanschlusskarte"})
    assert not p.applies_to({"source_id": "de-tso-amprion-netzanschluss", "role": "landing"})


def test_parses_state_from_class_and_details_from_list_items():
    rows = TransnetBWLandingParser().parse(HTML.encode(), REC)
    assert [r["entity"] for r in rows] == ["Heidelberg-Süd", "Daxlanden", "Altbach"]
    assert all(r["edition"] == "2026-05" for r in rows)
    hs, dax, alt = rows
    assert hs["availability"] == "nicht verfügbar" and hs["state_class"] == "red" and "voltage_kv" not in hs
    assert dax["availability"] == "langfristig verfügbar" and dax["voltage_kv"] == 380 and dax["earliest_year"] == 2035
    assert dax["design"] == "n-1" and dax["feed_in_mw"] == "0 MW" and dax["load_mw"] == "500 - 1.000 MW"
    assert alt["availability"] == "mittelfristig verfügbar" and alt["design"] == "n-0 und n-1"
    assert alt["qualifiers"] == ["temporärer Anschluss bis 2045"] and alt["load_mw"] == "< 500 MW"
    assert not any(r.get("availability_mismatch") for r in rows)


def test_class_and_text_disagreement_is_flagged_not_resolved():
    html = HTML.replace("🟡 langfristig verfügbar", "🟡 mittelfristig verfügbar")
    rows = TransnetBWLandingParser().parse(html.encode(), REC)
    dax = next(r for r in rows if r["entity"] == "Daxlanden")
    assert dax["availability_mismatch"] is True
    assert dax["availability"] == "langfristig verfügbar" and dax["availability_shown"] == "mittelfristig verfügbar"


def test_block_with_h2_instead_of_h3_is_still_parsed():
    """The live page has 52 tooltip blocks; four carry the name in <h2 class="h2">."""
    html = HTML.replace('<h3 class="h3">Umspannwerk Altbach</h3>', '<h2 class="h2">Umspannwerk Altbach</h2>')
    rows = TransnetBWLandingParser().parse(html.encode(), REC)
    assert any(r["entity"] == "Altbach" for r in rows)


def test_capitalisation_difference_is_not_a_mismatch():
    """The live page has 'Mittelfristig verfügbar' for two entries; that is not a disagreement."""
    html = HTML.replace("🟢 mittelfristig verfügbar", "🟢 Mittelfristig verfügbar")
    rows = TransnetBWLandingParser().parse(html.encode(), REC)
    assert not any(r.get("availability_mismatch") for r in rows)


def test_fails_loudly_without_edition_or_blocks():
    with pytest.raises(ParseError, match="Stand"):
        TransnetBWLandingParser().parse(HTML.replace("Stand 05/2026", "").encode(), REC)
    with pytest.raises(ParseError, match="tooltip"):
        TransnetBWLandingParser().parse(b"<html><body>Stand 05/2026</body></html>", REC)
