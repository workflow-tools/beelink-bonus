# Sources — what the four German TSOs actually publish (fetched 2026-09-03)

Everything below was read from the live pages or the captured documents on
2026-09-03 and is `[HIGH]` unless tagged. The per-source YAML under
`sources/` carries the same facts as comments, next to the config they justify.

## The series

Which substations (Schaltanlagen / Umspannwerke) in each TSO's control area
have a free bay (Schaltfeld) and connection capacity, as the TSO itself
assesses it, per edition of the Reifegradverfahren cycle. Publishers disagree
about vocabulary and polarity; that disagreement is the normalisation moat.

| Publisher | Landing page | Payload | Edition marker | Vocabulary | Polarity | Status |
|---|---|---|---|---|---|---|
| **Amprion** | `…/Netzanschluss/Darstellung-der-potenziellen-Netzanschlussmoeglichkeiten-und-der-Kundenprojekte.html` | 3 PDFs: map (unlabeled vector dots), **supplementary table** (10 substations, kV, municipality, n-0/n-1, earliest year, remarks), customer projects (`_v2`) | "Stand April 2026" inside the PDFs; "04.2026" / "2026.04_" in two filename conventions on one page | green *voraussichtlich realisierbar* / red *nicht gegeben*; supplementary lists green only | `lists_state` | **collecting + parsing** |
| **TransnetBW** | `…/netzzugang-und-entgelt/netzanschlusskarte` | the page itself: 48 `div.tooltip` blocks | "Stand 05/2026" on page; assessment "zum 01. April 2026" | 🔴 *nicht* / 🟢 *mittelfristig* / 🟡 *langfristig verfügbar*; kV, earliest year, n-0/n-1, feed-in and load MW bands, free-text qualifiers | `lists_state` | **collecting + parsing** |
| **50Hertz** | `…/Vertragspartner/Netzkunden/Netzanschluss` | page prose only so far; the map is client-rendered and on 2026-09-03 shows "Karte nicht konfiguriert" with an unrendered `{#MAP_LINK#}` | "zum 31.03.2026 bestmöglichen Einschätzung" | "an welchen Standorten … **kein** Netzanschluss möglich ist, da kein Schaltfeld verfügbar ist … wo ein Netzanschluss möglich wäre, sofern ein Schaltfeld errichtet werden kann" | `lists_where_not_possible` | **collecting prose; map needs browser** |
| **TenneT DE** | `…/strommarkt/kunden-deutschland/netzanschlussanfragen` (from search) | unknown | unknown | unknown | unknown | **blocked: browser challenge to every non-browser client; robots.txt names AI crawlers** |

Disclaimers, verbatim — the promulgation tell on each page:

- Amprion: *"Die Karten inklusive des ergänzenden Dokuments dienen der unverbindlichen Orientierung und geben eine Indikation. … ohne Gewähr für Richtigkeit und Vollständigkeit … Änderungen sind jederzeit möglich."*
- TransnetBW: *"Sie stellen eine unverbindliche Darstellung der Anschlussperspektive dar. Aus der Veröffentlichung der Netzkarte kann kein Anspruch auf einen Netzanschluss abgeleitet werden."* — *"Die Karte wird zyklisch aktualisiert."*
- 50Hertz: *"Sie stellen eine unverbindliche Darstellung der Anschlussperspektive dar. Alle Angaben sind nur informatorisch und unterliegen fortlaufend Veränderungen."*

## Cadence — from the joint procedure document `[MED]`

Four-TSO *Reifegradverfahren* documentation (netztransparenz.de, 2026-02-05,
V1.00, "Stand Q3 2025"), §4.3: *"zu Beginn der Phase 1, also drei Monate vor
dem Stichtag für die Einreichung der Anträge, werden unter anderem Daten zu
verfügbaren Netzanschlusskapazitäten veröffentlicht"*; Phase 1 *"eine Dauer
von drei Monaten"*; offer phase *"etwas über zwei Monate"*; the procedure
*"wiederholt sich zyklisch"*. First Phase 1 began 2026-04-01. Working value
`P6M` until a second edition is observed; replace with the observed gap.

## Things the collector had to learn from these pages

- The obvious Amprion URL (`/Netzanschluss/`) 404s and the section index
  links only a VDE grid overview map. Discovery by reading links found the
  real subpage. A guessed URL would have "worked" and captured nothing useful.
- Two filename conventions on one Amprion page (`-04.2026` vs `2026.04_`),
  and a `_v2` restatement — the reasons for link discovery and for keeping
  both versions.
- Amprion's rendered map PNG is embedded via `<img>`, not linked; the
  chassis follows what is offered, not what is embedded.
- TransnetBW's whole dataset is page text; the landing page had to become a
  tracked payload.
- 50Hertz's page changes bytes on every fetch (ASP.NET viewstate / CSRF);
  change detection had to move to visible text.
- Three publishers, three vocabularies, two polarities. Nothing merges
  without an explicit gold-layer mapping.

## Owner browser checks (cannot be done from an agent container)

1. **TenneT** — open
   https://www.tennet.eu/de/strommarkt/kunden-deutschland/netzanschlussanfragen
   in a normal browser. Does it load? Does it publish a list/map of
   substations with capacity? Is there a document? If it loads for a
   browser but not for `curl`, that is a publisher posture (station 5), not
   a routing problem, and the robots.txt reservation (station 4) needs a
   decision before a collector is pointed at it.
2. **50Hertz map** — open
   https://www.50hertz.com/de/Vertragspartner/Netzkunden/Netzanschluss,
   click "Karte im neuen Tab öffnen" if it renders, and in DevTools →
   Network find the request the map makes (JSON/GeoJSON/tiles). That URL
   becomes a second 50Hertz source.
3. **Archive probe** — from your machine, run the skill's
   `archive-probe.mjs probe` against the three landing URLs above; this
   container cannot reach web.archive.org. Any recoverable earlier editions
   are free backfill for the series.
