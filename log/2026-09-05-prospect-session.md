# 2026-09-05 (evening) — Prospect session: nine markets through the vanishing-data-prospector

**Session:** Claude Code (cloud container), branch `claude/vanishing-data-prospector-setup-e37mz6` in
`beelink-bonus` and `patterns`. Driven by `patterns/prompts/vanishing-data-prospect-session.md`.
Dossiers (one per market that reached link 3) are in `patterns/docs/research/`; this log carries what
touched *this* repo and the environment facts a Beelink session will want.

## Environment facts (all [HIGH], observed this session)

- **The archive probe works from the cloud containers** once Node honours the proxy:
  `NODE_USE_ENV_PROXY=1 node archive-probe.mjs probe --url …` exits 0 with a real coverage map.
  Without the flag the CDX preflight sees a 403 from direct egress and the script correctly
  refuses (exit 3). The CDX preflight (`example.com&limit=1`, 20 s) occasionally times out; a
  retry succeeds. The skill README's "never exercised end to end" caveat is closed by this run.
- **Cloudflare managed challenge to every non-browser client** (403, `cf-mitigated: challenge`,
  also with a browser User-Agent string): bayernwerk-netz.de, bayernwerk.de, westnetz.de,
  avacon-netz.de, e-dis.de, hansewerk.com, syna.de, energienetze-bayern.com, tennet.eu. A
  collector for these would need a browser engine: **project, not option**. No answer at all
  (routing, not findings): sh-netz.de, kfw.de, edis.de, rest.arbeitsagentur.de, interamt.de.
- Reachable with an honest User-Agent: netze-bw.de (25–30 s TTFB), mitnetz-strom.de,
  ewe-netz.de, stromnetz.berlin, enercity-netz.de, wesernetz.de, netz-leipzig.de,
  swm-infrastruktur.de, rheinnetz.de, pfalzwerke-netz.de, vnbdigital.de, smard.de,
  bundesnetzagentur.de, eskom.co.za, sepush.co.za, nmc.org.uk, ebutilities.at, ris.bka.gv.at,
  eur-lex.europa.eu (browser UA needed).

## What changed in this repo

- `longseries/docs/SOURCES.md`: addendum (evening) — probe results for the three TSO landing pages
  (owner check 3 closed) and Directive (EU) 2019/944 Art. 31(3) as amended, read verbatim: a
  quarterly DSO publication duty with no retention — the Directive half of the Schaltfeld kill
  criterion 3 does not fire.
- `longseries/registry/schaltfeld.yaml`: kill criterion 3 and the owner-check line updated with
  those results. No status change.
- `CLAUDE.md`: the open-question bullet on the probe marked done.
- `longseries/registry/`: four new option entries — `bnetza-ladesaeulenregister.yaml`,
  `dso-allocation-rounds.yaml`, `dso-storage-queue-register.yaml` (drafted by the screen lane,
  reviewed by the orchestrator), `bfee-plattform-abwaerme.yaml`; `schaltfeld.yaml` gains the APG
  KILL (with its reopen trigger and the Austrian legal note) under `collector.not_built` and the
  Amprion `/Netzanschlussregeln/` deletion evidence (60 of 77 attested URLs GONE) in station 5.
  `pytest` in `longseries/`: 105 passed.

## Session narrative (2026-09-05 21:30 → 2026-09-06 ~11:00 UTC; closed 2026-09-09)

Four Workflow rounds. **W1** — link 1 across nine markets as nine evidence lanes plus nine skeptics
that re-fetched every URL: all nine cleared the drop rule (money moving in 2025/2026 with two items
at [MED] or better); nothing refuted; hydrogen did not fall as the owner expected. Ranking after the
skeptics: battery storage, DSO grid connection, data-centre siting, EV charging, heat planning,
hydrogen, South Africa, nursing placement, EU AI Act. **W2** — links 2–4 on the top four: a link-2
lane (future questions disputed / traded / underwritten; a bottleneck table with "where published
today"), two link-3 hunters from different angles (by publisher; by question and incumbents), and a
link-4 merge that re-fetched every deciding artefact and, for data-centre siting, found a fifth
publisher (wesernetz Bremen). The session's usage limit interrupted W1 and W2 once each; both were
resumed from cache. **W3** — six-station option-mode screens for the seven candidates that reached
link 4, each followed by a skeptic lane; the screens all completed, but the usage credits ran out
while the skeptics ran, and only two (BNetzA register, MobiData BW) finished. The orchestrator
re-verified the deciding artefact of every candidate itself (APG live page 166 × "0 MW"; the EWE
page live and both Wayback captures; the WWN table; the Berlin page and the 2025 Topogramm at its
attested path; the BfEE landing; the BNetzA file host: two attested superseded editions 404, the
June and July 2026 editions still live).

**Outcome for this repo:** four register options, one register kill. The Schaltfeld option's
proposed fifth publisher (APG) died at station 3 — 1,158 capacity cells across seven editions all
"0 MW" — and lives on only as a reopen trigger. The BNetzA Ladesäulenregister entry is the one the
owner assumed was archived: it is deleted after a two-to-four-month lag, so three still-live editions
should be downloaded before October–November 2026 (owner check). The DSO allocation-round family is
the first option whose review date is set by a court (OLG Düsseldorf, 08.10.2026). The BfEE entry is
the first with a licence gate (CC BY-NC 4.0 inside the file versus DNG § 4).

**Reconciliation (2026-09-09):** the parallel `claude/keen-einstein-03b947` hunt in `patterns` rated
APG an OPTION from the live page alone and called ebUtilities.at login-gated; both are corrected in
`patterns/docs/PORTFOLIO-STATE.md` (APG KILL on the seven-edition count; ebUtilities' substation JSON
answers anonymously — the Austrian DSO series died on VNEP-V § 11(1) instead). Its four remaining
foreign extensions (France, Denmark, Poland, Czechia) have a dossier but no register entry here yet.

**Chassis notes for the next build session:** (1) an `<img>`-capture extension is needed for
Stromnetz Berlin's Topogramm and legend PNGs (`/images/<uuid>/ta-l/`, real `last-modified` and `etag`);
(2) the fetcher must accept brotli or ask for gzip (stromnetz.berlin serves `br` only); (3) hosts
without validators (`no-store`: EWE, NRM, wesernetz) need daily polls with content hashing, and the
staleness alarm must not fire on a `no-store` page polled at P1D against a declared P6M; (4) the
BfEE XLSX host answers HEAD with a 303 to an error page — GET only with `If-None-Match`; (5) the
BNetzA data host is slow — a generous per-request timeout, and count the dated register URLs that
still answer 200 on every poll (the deletion-lag gauge); (6) the BfEE source must strip three contact
columns at ingest and store only a scrubbed copy plus the original's SHA-256 — a deliberate deviation
from the store-every-byte rule, recorded in the register entry.
