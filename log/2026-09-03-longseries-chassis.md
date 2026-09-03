# 2026-09-03 — longseries: a capture chassis for vanishing data

**Branch:** `claude/longseries-chassis` · **Session:** Claude Code (remote), orchestrating from the `patterns` repo session that built the `vanishing-data-prospector` skill earlier the same day.

## What was built

`longseries/` — a Python package + Docker image + compose stack that polls a
public page on a schedule and stores everything it links to, content-addressed
and never overwritten. First series: Amprion's Schaltfeld capacity map.
Tests first (owner's stories → tests → design → dev model): 64 tests, all
green; verified against the live source from inside the container.

## Decisions

- **Collection is portable by construction; the Beelink is for extraction.**
  The owner's own rule (skill: "never design collection onto the Beelink")
  and the request for "containers on the Beelink" are both honoured: the
  compose stack runs anywhere; run it on a VPS *and* the Beelink.
- **healthchecks.io is the whole alert path.** Dead-man's switch (missing
  ping) plus `/fail` pings carrying alert text. No email code to maintain.
- **`LANDING_UNREACHABLE` (P1) ≠ `LANDING_VANISHED` (P0).** Unreachable is a
  routing problem, not a finding. Surfaced by the sandbox proxy.
- **Discovery follows `<a href>`, not `<img src>`.** What the publisher
  offers, not what the page embeds.
- **Ollama-on-host vs llama.cpp-in-container** for extraction: not decided
  here; the repo's existing convention (regwatch, OLLAMA-NIGHTWORK) is
  Ollama on the host, and that is the default unless the architecture panel
  finds a reason otherwise.

## Corrections made in this session

Commit `7846a11` claimed the image had been built and run; it had not (pip
failed behind the sandbox proxy; two shell constructs masked it). Corrected
in `d281473` rather than rewritten. The verification gate now checks exit
codes directly and asserts the image contains the new code before running.

## Source facts (fetched, [HIGH])

- Section index `…/Netzkunden/Netzanschluss/` links only a VDE FNN overview
  map. The Schaltfeld data is on the subpage
  "Darstellung der potenziellen Netzanschlussmöglichkeiten und der
  Kundenprojekte".
- Disclaimer verbatim: *"dienen der unverbindlichen Orientierung … ohne
  Gewähr für Richtigkeit und Vollständigkeit … Änderungen sind jederzeit
  möglich."*
- Categories: grün „Anschluss voraussichtlich realisierbar“, rot
  „Anschlussmöglichkeit nicht gegeben“ → polarity `lists_state`.
- Three PDFs (map 535 KB, supplementary 275 KB, Kundenprojekte **_v2** 412 KB),
  all Last-Modified 2026-06-04, two filename conventions on one page.
- Cadence: page says "zyklisches Reifegradverfahren", no period. `quarterly`
  is a `[LOW]` placeholder.

## Later the same day — extraction tier, sources 2–3, and what the sites actually do

- **Extraction needs no vision model.** Amprion's map PDF has no substation
  labels in its text layer (unlabeled vector dots); the substation table is
  in the supplementary PDF and pymupdf extracts it cleanly (10 rows, "Stand
  April 2026"). TransnetBW's Netzanschlusskarte is structured HTML tooltips:
  48 substations, three-valued availability (36 nicht / 8 mittelfristig / 4
  langfristig verfügbar), 12 with MW bands and n-0/n-1. Both parsers are
  pure, versioned, replayable; silver keeps publisher vocabulary.
- **Cadence is now evidence-based.** The joint 4-TSO Reifegradverfahren
  documentation (netztransparenz.de, 2026-02-05) says capacity data is
  published at the start of each three-month Phase 1 and the procedure
  repeats cyclically; offer phase ≈ 2 months. Working value P6M.
- **50Hertz:** map module unconfigured on the live page ("Karte nicht
  konfiguriert", `{#MAP_LINK#}`); no data route derivable without a
  browser. Landing-only source added to capture the prose and its date.
  Polarity differs: 50Hertz lists where connection is *not* possible.
- **TenneT:** every path returns a Cloudflare-style challenge to curl and to
  WebFetch alike; robots.txt names AI crawlers (a machine-readable
  reservation — station 4 and 5 material). No source configured. Owner to
  check from a browser: https://www.tennet.eu/de/strommarkt/kunden-deutschland/netzanschlussanfragen
- **Readers' findings acted on:** compose mounted `$LONGSERIES_DATA/<source_id>:/data`
  while the store already namespaces by source_id — the id nested twice on
  the host; all services now mount the shared root. Beelink is dual-boot
  (Windows 11 daily / Ubuntu for GPU). Ollama is a host systemd service;
  containers reach it via `host.docker.internal` (`extra_hosts: host-gateway`
  on Linux). llama.cpp-in-container has no precedent in either repo. regwatch
  has never run (no tests, unused `resend` dep) — its notify.py is reference
  shape only.
- **Verification lanes (interrupted by a usage limit; all nine fact lanes and
  five readers completed, refuters partly):** the Gemini notes' hardware
  stack is wrong in five places (kernel floor, `amdgpu.gttsize` deprecated
  in favour of `ttm.pages_limit`, ROCm 10.0 current, `HSA_OVERRIDE_GFX_VERSION`
  outdated for gfx1151 — the repo's own CLAUDE.md carries it — iGPU is the
  8060S not the 890M); the LiteLLM proxy advice is redundant and collides
  with Ollama's port; Gemini's own test suite fails 1/7 and did not compile
  as pasted. See `longseries/docs/ADR-001-architecture.md` appendix.
- **Architecture panel:** one of seven agents completed (risk-first). It
  found three real defects — a shared heartbeat masking a dead source, an
  index row aliased to a previous blob, and a 200-with-no-links silent for
  the whole cadence — fixed in 6cd5fdf. ADR-001 written from that design and
  marked single-perspective.
- **Corrections:** three commit messages claimed verification that had not
  happened (7846a11: image build; 1957242: 47 TransnetBW rows, actually 0
  because `role` was not persisted to the index). Both corrected in
  follow-up commits; the gate now asserts the numbers a message claims.

## Open

- Architecture panel + facts verification workflows still running at time of
  writing; results to be folded in (extraction tier, host provisioner docs).
- TenneT as source 4 (blocked from here — browser check); 50Hertz map data route (browser check).
- Gold layer: one availability vocabulary across two-valued (Amprion), three-valued (TransnetBW) and inverted-polarity (50Hertz) publishers; MW bands to numbers; entity crosswalk.
- Per-source expectation tests on silver row counts (a 48→3 drop should alert).
