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
| **TransnetBW** | `…/netzzugang-und-entgelt/netzanschlusskarte` | the page itself: 52 `div.tooltip` blocks (four carry the name in `<h2>`, not `<h3>`) | "Stand 05/2026" on page; assessment "zum 01. April 2026" | 🔴 *nicht* / 🟢 *mittelfristig* / 🟡 *langfristig verfügbar*; kV, earliest year, n-0/n-1, feed-in and load MW bands, free-text qualifiers | `lists_state` | **collecting + parsing** |
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
   in a normal browser. The verification lane found the map is an ArcGIS
   Experience Builder app
   (`https://experience.arcgis.com/experience/b5f2b335e4224d60bbaf1d3f33248a1e`)
   whose item is 403 to anonymous REST; in DevTools → Network look for the
   feature-service URL it queries. Does it load? Does it publish a list/map of
   substations with capacity? Is there a document? If it loads for a
   browser but not for `curl`, that is a publisher posture (station 5), not
   a routing problem, and the robots.txt reservation (station 4) needs a
   decision before a collector is pointed at it.
2. **50Hertz map** — the verification lane found the app and its API
   `[HIGH on discovery; the API host is unreachable from the agent network]`:
   the map is an Angular/Leaflet app ("Digitale Netzbilder") served by
   `https://www.50hertz.com/DesktopModules/Lotes/FrequentModules/API/DigitalMap/GetDnbMap?dnbMapId=netzkapazitaet/production-map`
   (≈17 MB, GET only), whose data comes from
   `https://api-digitale-netzbilder.50hertz.com/api/api/` — routes seen in
   the bundle: `GridLoadMapVersion/map/type/gridcapacity`,
   `GeoData/transformerStations`, `GeoShapes/All/MapVersion/{id}`. From a
   browser: open the page, then in DevTools → Network capture the exact
   request and response for `gridcapacity` and `transformerStations`. If the
   response is JSON with substation status, that URL becomes a landing-only
   50Hertz source with `accept_extensions: []`.
3. **Archive probe** — from your machine, run the skill's
   `archive-probe.mjs probe` against the three landing URLs above; this
   container cannot reach web.archive.org. Any recoverable earlier editions
   are free backfill for the series.

## Addendum 2026-09-05 — the legal floor under the maps, and the register

Facts verified on 2026-09-05 (details and tags in the patterns dossier
`docs/research/2026-09-05-vanishing-data-rescore-schaltfeld-and-orbital-prospect.md`):

- **Netzanschlusspaket, BR-Drs. 471/26 (cabinet bill of 2026-07-29, 81 pp).** § 17c(1) EnWG-RegE
  obliges every *Betreiber von Elektrizitätsversorgungsnetzen* to publish available connection
  capacity at the HöS/HS and HS/MS transformation levels *"auf ihrer jeweiligen Internetseite auf
  einer geografischen Karte"* and to update it **monthly**; *"Auf die tatsächliche Verfügbarkeit …
  besteht kein Rechtsanspruch."* The bill contains **no retention, archive or history duty** (zero
  hits for `archiv|histori|vorherige Fassung|aufbewahr`) and no BNetzA Festlegung power over § 17c(1)
  `[HIGH]`. Entry into force: the day after promulgation; the DSO Auskunft in § 17c(2) from
  2028-01-01. Status: Bundesrat first passage 2026-09-25; Bundestag pending — owner check.
- **Reg. (EU) 2019/943 Art. 50(4a)** already requires TSOs to publish available capacity for new
  connections *"at least every month"*, with no retention duty `[HIGH]`. Amprion's page still read
  *"Stand: April 2026"* and TransnetBW's *"Stand 05/2026"* on 2026-09-05.
- **Consequences for this chassis:** the vanishing property survives the law; the cadence becomes
  monthly (raise `declared_cadence` when the first monthly edition is observed, never before); the
  publisher set grows from four TSOs to every operator with a 110 kV grid, which is a parser-per-
  operator *product* decision, not an option (see `registry/schaltfeld.yaml`).
- **Withdrawal in reverse, watched:** Capacitypedia (ENTSO-E / EU DSO Entity, launched 2026-05-22)
  links to national maps and archives nothing; Commission Notice C/2025/6703 recommends single
  national platforms and forward-looking maps; VNBdigital (§ 14e) sits under a BNetzA Festlegung
  power. Any of these adding a dated archive is a kill criterion in the register.
- **BK6-25-287 (BNetzA, 2026-05-04), BESS Germany 1 GmbH v 50Hertz:** a dispute decided on
  *"verfügbare Schaltfelder"* and *"zeitlich frühere Netzanschlussanträge"* — the past state of a bay
  is already argued over `[HIGH]`.

The option register for this and other series lives in `registry/` (schema in
`registry/README.md`); `pytest` checks it against `sources/`.

## Addendum 2026-09-05 (evening) — owner browser check 3 closed from a cloud container; Directive half of kill criterion 3 closed

`archive-probe.mjs` runs end to end from the cloud containers once Node is told to honour the
proxy (`NODE_USE_ENV_PROXY=1`); the CDX preflight occasionally times out and a retry succeeds.
Results, all `[HIGH]` on the CDX calls and the live re-fetch, `[MED]` on any absence:

| Landing URL | Attested captures | Window | Live | Reading |
|---|---|---|---|---|
| Amprion "Darstellung der potenziellen Netzanschlussmöglichkeiten…" | **0** (exact, prefix and `Darstellung*`) | — | — | No Wayback backfill exists for the map or the supplementary PDFs; the series starts with our 2026-09-03 capture |
| TransnetBW `netzanschlusskarte` | **0** (exact, prefix) | — | — | Same: no third-party backfill of the tooltip dataset |
| 50Hertz `Vertragspartner/Netzkunden/Netzanschluss` | 29 captures of the page | 2019-02 → 2026 | 1 LIVE | Page prose only (the map is client-rendered); a prose backfill 2019–2026 exists if ever needed |
| Amprion `/Netzkunden/Netzanschluss/` section prefix | 8 URLs, 34 captures | 2025-08 → 2026-04 | 3 LIVE, 3 MOVED, 2 GONE | The GONE pair is `Karten-über-das-Netzgebiet.html` (+utm variant): the VDE overview-map page was removed or moved, unrelated to the capacity series |

Probe JSON is kept with the session's scratch material, not in this repo.

**Directive (EU) 2019/944 Art. 31(3) as amended by Directive (EU) 2024/1711** (EUR-Lex
consolidated text 02019L0944-20240716, fetched 2026-09-05) `[HIGH]`: distribution system
operators "shall publish in a transparent manner clear information on the capacity available
for new connections in their area of operation with high spatial granularity, respecting
public security and data confidentiality, including the capacity under connection request and
the possibility of flexible connection in congested areas … shall update that information on a
regular basis, at least quarterly", and shall inform applicants of the status of their
requests, updated at least quarterly; Art. 31(3b) lets Member States exempt undertakings
serving fewer than 100,000 connected customers. **No retention, archive, versioning or
central-platform duty.** The Directive half of `registry/schaltfeld.yaml` kill criterion 3
therefore does not fire; the Regulation half was closed on 2026-09-05 (morning). Note the
"respecting public security" clause: it is the hook under which the Bavarian DSOs withdrew
their grid-display services from the Energie-Atlas Bayern (observed 2026-09-05, evening
session; see the patterns dossier of that date).
