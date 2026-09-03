# ADR-001 — Long-series chassis architecture

**Status:** proposed, single-perspective. The three-design judge panel was
interrupted by a usage limit after one design (risk-first) completed; the
two other designs and all three judges did not run. This record is written
from that design, the five reader lanes (regwatch, datafactory scrapers,
court-scraper, Beelink ops, conventions), the nine adversarially-checked fact
lanes on the Gemini notes, and the code as built. The owner ratifies.

**Date:** 2026-09-03 · **Code:** `longseries/` at the commit carrying this file.

## Context

The chassis polls public grid-connection publications from the four German
TSOs, stores raw bytes content-addressed, and turns them into a series of
per-substation availability with two clocks. The owner's rules: collection
must survive an international relocation; derived facts only; fail loudly;
sources are data; polarity explicit; bitemporal; low maintenance; a €5/month
VPS is fine, a €50/month bill is not. Today's evidence removed the Gemini
notes' premise that extraction needs a vision model: Amprion's substation
table is text in a PDF, TransnetBW's is page HTML.

## Q1 — Where collection runs, and how bronze reaches extraction

**Decision.** A cheap VPS runs the compose stack as the canonical always-on
collector. The Beelink runs the *same* stack as a second, independent
replica when it is up, and is the extraction host. Bronze moves VPS → Beelink
by a pull-only `rsync -az --ignore-existing` from a systemd timer on the
Beelink into a separate mirror root (`/srv/longseries-mirror/vps/`), never
merged into the Beelink's own tree; extraction reads the mirror. Provider
backups on for the VPS.

**Rationale.** `collector-design.md` makes relocation survival a design
requirement, and the ops reader found the Beelink is dual-boot (Windows 11
daily, Ubuntu for GPU work), so it is routinely "off" for the Ubuntu stack
anyway. Two independent replicas give two capture histories; the mirror
gives the extraction host the canonical one without a merge.

**Rejected.** Beelink-only (dies in the shipping container). GitHub Actions
cron (no persistent disk; the bronze store is the asset and must not live in
a workflow cache). Serverless (same, plus cold-start cost for nothing).

**Consequences.** Two `index.jsonl` trees exist; never `rsync --delete`
either into the other. Extraction unions by sha256 if it ever reads both.
Cost ≈ €4–5/month `[LOW — pricing pages are client-rendered; confirm in the
provider console]`.

## Q2 — Extraction hosting

**Decision.** (a) No language model by default. Parsers are pure, versioned
functions of `(bytes, capture record)`; replay is the repair mechanism. When
a model is needed (free-text remarks, a PDF-only publisher, cross-publisher
entity matching), its output is written as a **proposal**
(`gold/proposals/*.jsonl`) that a human or a deterministic rule promotes —
never directly as a silver row. (b) The model is **host Ollama**, reached from
a Beelink-only compose profile at `http://host.docker.internal:11434` with
`extra_hosts: ["host.docker.internal:host-gateway"]`, `format: <JSON schema>`,
`think: false`, explicit `options.num_ctx`, per-request `keep_alive`, a
preflight `GET /api/tags` (unreachable → write nothing, heartbeat `/fail`,
exit 2), and a 600 s timeout.

**Rationale.** A model upgrade makes replay non-reproducible, which destroys
the one property that lets a wrong quarter be repaired — so model output
cannot be silver. Ollama-on-host is the repo's stated convention
(`VILSECKKI-FINAL-ARCHITECTURE.md`: "Ollama runs as a systemd service on
Linux, outside Docker"; regwatch's compose: "Ollama is NOT included here");
there is zero precedent for a GPU container in either repo.

**Rejected.** llama.cpp in a container with device passthrough (the Gemini
notes). If it is ever wanted: the image is `ghcr.io/ggml-org/llama.cpp:server-vulkan`
(the `ggerganov` path 404s), Vulkan needs only `/dev/dri`, and `group_add:
[video, render]` breaks `docker compose up` because the image has no `render`
group `[HIGH, fact lane F3, live-tested]`. Instructor's `Mode.JSON_SCHEMA`
payload is real but llama-cpp-python's server would run it unconstrained
`[HIGH, F2]`.

## Q3 — Container topology

**Decision.** One image, one container per source (as built), with: one
healthchecks check **per source** (`LONGSERIES_HEARTBEAT_URL_<SOURCE>`), one
bronze root mounted by every service, a restart-safe first-poll gate, and —
to build — a host-level systemd timer that pings a "host alive" check with
`df -h` and `docker ps` as the body and `/fail` if free disk < 2 GB or any
`longseries-*` container is not running.

**Rationale.** A shared check let a dead source hide behind a live sibling
(found by the risk-first design, fixed in 6cd5fdf). Per-source containers
give a `docker ps` a tired human can read and isolate a publisher's failure.

**Rejected.** One scheduler container for all sources (one crash takes all
three down; one heartbeat by construction). Host cron per source (no
`restart: unless-stopped`; three crontabs to keep in sync across two hosts).

## Q4 — Alerting

**Decision.** healthchecks.io remains the only automatic path: every check
gets two channels in the healthchecks UI (email plus one push channel), the
Beelink pull timer's `/fail` is an independent dead-man from a second
machine, and every alert is already on disk in the capture manifest, so
`show` is the source of truth when the provider is down. regwatch's
`notify.py` is **not** wired in.

**Rationale.** The reader found regwatch has never run (no tests, an unused
`resend` dependency); its ladder is a shape worth copying only if a second
path is ever needed. A second code path is maintenance the owner does not
have. A weekly digest is deferred until there is a second edition to digest.

## Q5 — Gold layer

**Decision.** Files, not a server. `gold/` beside `silver/` holds
`vocab/availability.yaml` (rows of `(source_id, raw_value, polarity) → class`),
`crosswalk.csv` (human-reviewed, git-tracked), and the build output
`facts.parquet` + `facts.jsonl` + `transitions.csv` from one deterministic
`normalise` command. DuckDB is a query engine over the files, never a
`.duckdb` file that is the store. One fact row = `(canonical_id, source_id,
metric, value, valid_from=edition, valid_to, observed_at, capture_sha,
parser_version)`. The normaliser refuses to run when a manifest's `polarity`
has no row in the vocabulary, and a test asserts each source's mapping is
total. Delivery: bulk files first; an API only when a buyer asks for one.

**Rationale.** Three vocabularies and two polarities exist today (Amprion
two-valued state map; TransnetBW three-valued; 50Hertz lists where
connection is *not* possible). Nothing merges without an explicit, reviewed
mapping, and "explicit" means a file a human can diff.

## Q6 — Landing-page volatility

**Decision.** Disposition is decided on the visible-text hash
(`content_sha256`); the index row's `sha256` is always the hash of the bytes
received and those bytes are always kept (fixed in 6cd5fdf). A second,
DOM-level canonical hash with a denylist of volatile attributes
(`__VIEWSTATE`, `__EVENTVALIDATION`, CSRF tokens, `cdv=` cache-busters) is
deferred; text-only is sufficient for the three live sources today.

## Q7 — Build order

1. **Done (6cd5fdf):** DISCOVERY_EMPTY and STRUCTURE_MISSING alerts,
   per-source heartbeats, shared bronze root, restart-safe gate.
2. **Owner:** provision the VPS, enable backups, create six healthchecks
   checks (three sources, extract, pull, host), `docker compose up -d`.
   Then on the Beelink: the pull timer and the host-heartbeat timer (to be
   written as `ops/`).
3. **Next build:** gold v0 per Q5, seeded from the 10 Amprion and 52
   TransnetBW names with `status=proposed` in the crosswalk.
4. **Owner browser checks** (`docs/SOURCES.md`): TenneT's page and its
   ArcGIS app; 50Hertz's map data API; the archive probe.
5. **Deferred:** DOM canonicalisation; weekly digest; an API.

## Appendix — the extraction host, corrected (fact lane F1, `[HIGH]` unless marked)

None of this applies to collection. For the Ubuntu boot of the Beelink, when
a model is needed:

- **Kernel.** AMD's Strix Halo document requires Ubuntu 24.04 HWE
  `6.17.0-19.19~24.04.2` or later (24.04.5 HWE is 7.0), or 6.18.4+ on other
  distributions. The Gemini notes' "HWE 6.18.4+" conflated the two, and the
  "VGPR mismatch" rationale is invented — the fixes concern KFD queue and
  memory limits.
- **Memory.** `amdgpu.gttsize` alone is deprecated (the kernel says so).
  AMD's path: `pipx install amd-debug-tools && sudo amd-ttm --set <GB>`, or
  pair `amdgpu.gttsize=<MB>` with `ttm.pages_limit=<pages>`. Keep BIOS UMA
  small (0.5–2 GB) and raise the shared limit instead.
- **ROCm.** Core SDK 10.0.0 (2026-08-26) lists gfx1151 as supported with
  inbox drivers; 7.2 is no longer current. Validated PyTorch 2.11–2.13.
- **Backend.** Vulkan/RADV is the compatibility default; ROCm/HIP now wins
  prompt processing on gfx1151 by ~20–48% in community measurements, and
  extraction (long input, short JSON answer) is prompt-processing-bound
  `[MED for the extrapolation]`.
- **`HSA_OVERRIDE_GFX_VERSION=11.0.0` is outdated.** It forces gfx1100
  kernels; Ollama's docs list gfx1151 as natively supported and ROCm 7.2.2+
  has native kernels. Ollama 0.30.x+ on this APU needs `OLLAMA_VULKAN=1` and
  `OLLAMA_IGPU_ENABLE=1` instead. The repo's `CLAUDE.md` and the nightwork
  document carry the old flag; verify on the box before changing them:
  `uname -r; cat /sys/module/ttm/parameters/pages_limit; ollama --version`.
- **iGPU name.** Radeon 8060S (gfx1151), not "890M" (that is Strix Point).
- **Claude Code against local models.** Ollama ≥ 0.14 serves the Anthropic
  Messages API natively; `ollama launch claude` exists (≥ 0.15). The Gemini
  notes' LiteLLM proxy on port 11434 is redundant and collides with Ollama's
  own port (LiteLLM defaults to 4000) `[HIGH, F4]`.
- **Gemini's chassis tests.** Run for real: 6 pass, 1 fails (the polite-UA
  test patches `Client.get` for headers set on the constructor), and the
  pasted code did not compile without repair `[HIGH, F9]`.

## Judge disagreements

None recorded — the panel did not complete. Where this record departs from
the single completed design: none; it adopts that design's decisions and
marks what it could not corroborate.
