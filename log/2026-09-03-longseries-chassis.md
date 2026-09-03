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

## Open

- Architecture panel + facts verification workflows still running at time of
  writing; results to be folded in (extraction tier, host provisioner docs).
- Other three TSOs (50Hertz, TenneT DE, TransnetBW) as sources 2–4.
- Extraction tier (Epic 2) — not started; see `longseries/docs/USER-STORIES.md`.
