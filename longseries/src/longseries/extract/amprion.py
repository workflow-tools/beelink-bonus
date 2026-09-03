"""Amprion — 'Ergänzendes Dokument zu potenziellen Netzanschlussmöglichkeiten'.

A one-page PDF table: Schaltanlage · Spannungsebene · Stadt/Gemeinde ·
Anschlussauslegung · Voraussichtlich frühestes Inbetriebnahmejahr · Anmerkungen,
one row per substation shown GREEN on the map ("Anschluss voraussichtlich
realisierbar"). Red substations are on the map only, unlabeled; a substation
leaving this table is the signal that it stopped being available.

Footnote (verbatim, April 2026 edition): "(n-0): ein Anschlussfeld vsl.
realisierbar; (n-1): mindestens zwei Anschlussfelder vsl. realisierbar".

Two extraction paths: pymupdf's table detection when it finds the table, else a
line-layout state machine (get_text() yields one cell per line, 5 or 6 lines a
row, the sixth being an optional remark)."""
from __future__ import annotations

import contextlib
import re
import sys

from .base import ParseError, edition_from_text

_KV = re.compile(r"^(\d+)\s*kV$")
_DESIGN = re.compile(r"^\((n-\d)\)$")
_YEAR = re.compile(r"^(20\d\d)$")


class AmprionSupplementaryParser:
    parser_id = "amprion-supplementary"
    version = 1

    def applies_to(self, record: dict) -> bool:
        return (record.get("source_id", "").startswith("de-tso-amprion")
                and record.get("role") != "landing"
                and "Ergaenzendes-Dokument" in record.get("source_url", ""))

    def parse(self, content: bytes, record: dict) -> list[dict]:
        import pymupdf  # heavy; only the extraction tier needs it
        doc = pymupdf.open(stream=content, filetype="pdf")
        page = doc[0]
        text = page.get_text("text")
        edition = edition_from_text(text)
        if not edition:
            raise ParseError("no 'Stand <month> <year>' in document")
        rows = self._via_tables(page) or self._via_lines(text)
        if not rows:
            raise ParseError("no rows found by either path")
        return [{**r, "edition": edition, "state": "available"} for r in rows]

    @staticmethod
    def _row(name, kv, muni, design, year, remark):
        return {"entity": name.strip(), "voltage_kv": int(kv), "municipality": muni.strip(),
                "design": design, "earliest_year": int(year), "remarks": remark.strip()}

    def _via_tables(self, page) -> list[dict]:
        try:
            # pymupdf prints a "consider pymupdf_layout" advisory to STDOUT, which would
            # corrupt the CLI's JSON output; keep the library's chatter on stderr.
            with contextlib.redirect_stdout(sys.stderr):
                tabs = page.find_tables()
        except Exception:
            return []
        for t in getattr(tabs, "tables", []):
            cells = t.extract()
            rows = []
            for c in cells:
                if len(c) < 5:
                    continue
                c = [(x or "").strip() for x in c] + [""] * (6 - len(c))
                mk, md, my = _KV.match(c[1]), _DESIGN.match(c[3]), _YEAR.match(c[4])
                if mk and md and my:
                    rows.append(self._row(c[0], mk.group(1), c[2], md.group(1), my.group(1), c[5]))
            if rows:
                return rows
        return []

    def _via_lines(self, text: str) -> list[dict]:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        try:
            start = lines.index("Anmerkungen") + 1
        except ValueError:
            return []
        end = next((i for i, l in enumerate(lines) if l.startswith("Haftungsausschluss")), len(lines))
        rows, i = [], start
        while i + 4 < end:
            name, kv, muni, design, year = lines[i:i + 5]
            mk, md, my = _KV.match(kv), _DESIGN.match(design), _YEAR.match(year)
            if not (mk and md and my):
                raise ParseError(f"unexpected row shape at line {i}: {lines[i:i + 5]}")
            i += 5
            remark = ""
            next_is_name = i + 1 < end and _KV.match(lines[i + 1]) is not None
            if i < end and not next_is_name:
                remark = lines[i]
                i += 1
            rows.append(self._row(name, mk.group(1), muni, md.group(1), my.group(1), remark))
        return rows
