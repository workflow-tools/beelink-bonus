"""TransnetBW — 'Netzanschlusskarte'. The payload is the landing page itself.

Each substation is a tooltip block:
  <div class="tooltip is-hidden tooltip-uw-<slug> tooltip-uw-type--red|yellow|green">
    <p class="h2--preheadline">🔴 nicht verfügbar</p>       (or 🟡 langfristig / 🟢 mittelfristig verfügbar)
    <h3 class="h3">Umspannwerk Daxlanden</h3>
    <ul><li>Spannungsebene: 380 kV</li>
        <li>Inbetriebnahme Netzanschluss: voraussichtlich frühestens 2035</li>
        <li>Anschlussart: n–1</li>
        <li>Verfügbare Einspeisekapazität: 0 MW</li>
        <li>Verfügbare Lastkapazität: 500 – 1.000 MW</li>
        <li>temporärer Anschluss bis 2045</li>                (free-text qualifiers occur)
    </ul>

State comes from the CSS class (stable) and is cross-checked against the
preheadline text (what a human sees); a disagreement is flagged, not resolved.
Three availability values here vs Amprion's two: publisher vocabulary is kept
verbatim in silver, normalisation is a gold-layer decision."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import ParseError, edition_from_text

_STATE_BY_CLASS = {"red": "nicht verfügbar", "yellow": "langfristig verfügbar", "green": "mittelfristig verfügbar"}
_DASHES = str.maketrans({"\u2013": "-", "\u2014": "-", "\u2011": "-"})


class TransnetBWLandingParser:
    parser_id = "transnetbw-netzanschlusskarte"
    version = 1

    def applies_to(self, record: dict) -> bool:
        return record.get("source_id", "").startswith("de-tso-transnetbw") and record.get("role") == "landing"

    def parse(self, content: bytes, record: dict) -> list[dict]:
        soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
        edition = edition_from_text(soup.get_text(" "))
        if not edition:
            raise ParseError("no 'Stand MM/YYYY' on page")
        rows = []
        for div in soup.select("div.tooltip"):
            color = next((c.rsplit("--", 1)[-1] for c in div.get("class", []) if c.startswith("tooltip-uw-type--")), None)
            h3 = div.find(["h2", "h3", "h4", "h5"])
            if not color or not h3:
                continue
            name = h3.get_text(" ", strip=True)
            pre = div.find("p", class_="h2--preheadline")
            shown = re.sub(r"^[^\w]+", "", pre.get_text(" ", strip=True)).strip() if pre else ""
            row: dict = {
                "entity": re.sub(r"^Umspannwerk\s+", "", name),
                "edition": edition,
                "availability": _STATE_BY_CLASS.get(color, color),
                "availability_shown": shown,
                "state_class": color,
                "qualifiers": [],
            }
            if shown and color in _STATE_BY_CLASS and shown.casefold() != _STATE_BY_CLASS[color].casefold():
                row["availability_mismatch"] = True  # class and text disagree: flag it, never pick one silently
            for li in div.select("li"):
                t = li.get_text(" ", strip=True).translate(_DASHES)
                if m := re.match(r"Spannungsebene:\s*(\d+)\s*kV", t):
                    row["voltage_kv"] = int(m.group(1))
                elif m := re.search(r"fr\u00fchestens\s*(20\d\d)", t):
                    row["earliest_year"] = int(m.group(1))
                elif m := re.match(r"Anschlussart:\s*(.+)$", t):
                    row["design"] = re.sub(r"\s+", " ", m.group(1)).strip()
                elif m := re.match(r"Verf\u00fcgbare Einspeisekapazit\u00e4t:\s*(.+)$", t):
                    row["feed_in_mw"] = re.sub(r"\s+", " ", m.group(1)).strip()
                elif m := re.match(r"Verf\u00fcgbare Lastkapazit\u00e4t:\s*(.+)$", t):
                    row["load_mw"] = re.sub(r"\s+", " ", m.group(1)).strip()
                else:
                    row["qualifiers"].append(t)
            rows.append(row)
        if not rows:
            raise ParseError("no tooltip blocks found — page structure changed?")
        return rows
