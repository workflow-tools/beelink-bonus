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
- Register entries for the new options: see below (appended when the screen finished).

## Session narrative

(appended at the end of the session)
