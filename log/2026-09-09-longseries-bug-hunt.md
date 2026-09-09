# 2026-09-09 — longseries: a bug hunt over the whole chassis, and a failure-mode catalogue

**Branch:** `claude/longseries-chassis` → `main` · **Suite:** 110 tests before, **168 after**.

Trigger: on 2026-09-08 a single bug was found and fixed — `_load()` called
`sys.exit(1)`, and the resulting `SystemExit` slipped past the schedule loop's
`except Exception`, so a bad source YAML exited the process into a
`restart: unless-stopped` loop that never pinged anything. That is a *class* of
bug, not an instance: an exception class, an exit path or a swallowed error
chosen too narrowly, defeating a safety mechanism. This session went looking
for its siblings across five lenses (store, config/startup, alerts/heartbeat,
extraction/domain answers, ops/container), reproduced every filed finding
before believing it, then fixed and documented.

## Numbers

- **32 findings filed**, five lenses. After merging five cross-lens duplicates:
  **26 distinct defects** — 18 CONFIRMED, 7 PARTIAL (real, but narrower or
  differently caused than filed), **1 REFUTED**, 0 unreproducible.
- **21 fixed** in seven commits on this branch. **5 deferred** in this repo,
  plus 4 belonging to a different repository.
- **Tests: 110 → 168.** Every fix went test-first: write the regression, watch
  it fail, fix, run the whole suite. Nothing touches the network
  (`httpx.MockTransport` and the `FakeSite` fixture throughout).

## The one that was refuted

**"The blob's directory entry is never fsynced, so a power cut can leave an
index row pointing at a blob that is not on disk."** `strace` over one `save()`
disproves the specific ordering: the `rename()` of the blob is issued *before*
the index row's `fsync()`, and on a journalling filesystem `fsync()` commits
the running transaction, which contains that rename. On ext4 (Docker's default
here) and XFS the row cannot become durable ahead of the blob. The finding had
itself conceded it was never demonstrated. Its second half — extraction's
`read_bytes()` sitting *outside* the `try` — was real and was kept and fixed
separately.

## What was fixed, by severity tier

**Silent data loss (the store is the entire asset).**
A torn trailing line in `index.jsonl` — what ENOSPC or a SIGKILL inside a
buffered flush leaves — used to poison the source *permanently*: `versions()`,
`last_change_at()` and the next `save()` all raised a bare `JSONDecodeError`,
so every future poll died at the landing page over years of undamaged rows.
Now the append rolls back to its pre-append byte size on any `BaseException`,
reads raise `IndexCorrupt` naming file and line, and `longseries repair` trims
a *trailing* partial line only — a corrupt row mid-file is a capture
unaccounted for and is never dropped silently. Blob scratch files were named
from the content hash, so two writers holding the same bytes shared one `.tmp`
and a killed one published a *prefix* under the full hash; unique per-writer
names plus `os.link` finalisation. Capture directories were keyed to the
second, so two runs in one second overwrote each other's `landing.html` and
`manifest.json` — the record of what a run saw and which alerts fired; the
directory is now claimed with `mkdir(exist_ok=False)`.

**Silent cessation (worse than a crash, because a crash is visible).**
The direct sibling of the fixed bug, one class further out: `ConfigError`
*subclasses* `ValueError`, so `except ConfigError` never caught the plain
`ValueError` that `int()`/`float()` raise. `min_payload_bytes: 50k`,
`stale_tolerance: '1,5'`, `expect_min_documents: three` and a **missing source
file** (a failed `./sources` mount) all escaped into the same silent restart
loop the 2026-09-08 fix was supposed to have closed. Separately, a crash
*between* loading the config and constructing the per-source `Heartbeat` was
swallowed by the loop's bare `except Exception` — three iterations, no ping,
`docker ps` showing **Up**. And httpx has no whole-request budget, so a server
dribbling bytes inside the read timeout held one `_get()` open for hundreds of
hours: `poll()` never returned, *nothing* pinged, and the live process kept
`restart:` from firing. All three closed; fetches are now streamed under a byte
ceiling and a monotonic deadline.

**False all-clear (the whole safety story rests on this).**
No rule anywhere keyed on `counts['failed']` — `run.failed` means the *landing*
page failed — so a run that lost two of five documents to 403 pinged **success**
and exited 0 while an edition was lost forever. Now `P1 DOCUMENT_UNREACHABLE`,
escalating to **`P0 DOCUMENT_WITHDRAWN`** when the index shows that URL was
captured successfully before: a retraction is the event this collector exists
to witness. The landing page's prose drift reset the *documents'* staleness
clock, so `STALE` and `ZERO_NEW_FILES` could never fire on the one source that
collects documents (460 simulated days, frozen PDFs, not one alert); staleness
is now role-scoped. The heartbeat ignored the watchdog's HTTP status entirely
— a 404/429/503 dropped the alert with no log line and no retry — and its
`except httpx.HTTPError` let `InvalidURL` escape and *replace the run's own
exception*, so an operator debugging a full disk was shown a URL parse error.

**Wrong domain answers.** `_via_tables` silently dropped rows it could not
read, and `build_series` then reported those substations as **DISAPPEARED** — a
footnote marker turning `380 kV` into `380 kV*` manufactured an absence the
publisher never stated. That path had *zero* test coverage. `load_silver`
merged parser versions, publishing a bug fix as a restatement the publisher
never made — and at v10, lexicographic ordering silently reverted the fix.

## Deferred, and why

- **The `.longseries-root` marker** (an unmounted data root is
  indistinguishable from a fresh install: everything re-captured as `new`, both
  staleness alarms gated off, watchdog green). The compose-side trigger is
  removed — `create_host_path: false` makes Docker refuse to invent an empty
  host directory — but the in-collector half needs an owner decision the
  finding does not settle: how does a collector know it has run *before*, when
  the state it would consult lives on the volume that is missing? **Highest-value
  un-taken fix in the chassis.**
- **Recording `final_url` and the redirect chain** on index rows. Additive
  schema change to the file that *is* the asset, and the alerting half
  (`allowed_hosts`) is a policy call: a TSO legitimately serving PDFs from a CDN
  would start failing every poll.
- **`longseries verify`** (full-store re-hash), **`robots.txt` through
  `save()`**, **spooling undeliverable alerts to disk** — each is new capability
  or a schema/policy decision rather than a remaining defect; the confirmed harm
  behind each is closed.
- **Four findings in `patterns/skills/vanishing-data-prospector/scripts/archive-probe.mjs`**
  — a host that 404s everything makes the probe print "This is real deletion"
  and exit 0; `warc/revisit` captures discarded (14% of the archive invisible on
  transnetbw.de, one URL back-dated ten years); soft-404s classified LIVE; and
  `findAsOfDates` truncating the year off every "Stand MM/YYYY" (2026 read as
  2020, in the tool whose job is keeping the publisher's clock separate from
  ours). Different repository, one shared CDX fixture, one pass.

## Written this session

- **`longseries/docs/FAILURE-MODES.md`** — the durable catalogue. 26 numbered
  failure modes in a table (publisher moved or walled, YAML hot-edited, disk
  full, killed mid-write, watchdog lapsed or rotated, replica pull stopped,
  parse returning zero or too few rows, clock skew and DST, host lost), each
  with what the operator sees, what the code does, what it does **not** do, and
  the workaround; marked **COVERED** (a named test proves it), **HANDLED** (code
  does it, nothing proves it) or **GAP**. Plus an airport-triage opener, a
  recovery procedure, and a ranked gap list. This is the document to read first.
- **`longseries/README.md`** — a "When something goes wrong" section linking to
  it, the three new alert codes in the alert table, and the test count corrected
  (90 → 168; the dated 2026-09-03 verification record left as history).
- **`longseries/docs/ADR-001-architecture.md`** — a dated note appended, not a
  rewrite: Q3's restart gate had two fail-open paths, Q4's "`show` is the source
  of truth" was false of `show` itself, Q6's visible-text hash had a scope
  consequence it did not draw, and Q1's replica and backups remain entirely
  unbuilt.

## Standing exposure

With no off-host replica and no verified provider backup actually running, the
store on one host is the only copy of the asset. Every other failure in this
document has a code-level mitigation. That one does not.
