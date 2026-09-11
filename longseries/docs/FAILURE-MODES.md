# longseries — failure modes, and what actually happens

What can go wrong with this collector, what the operator sees when it does,
what the code does about it today, what it does **not** do, and what to do by
hand. Written 2026-09-09 after a bug hunt over the whole chassis (26 distinct
defects reproduced, 21 fixed; suite 110 → 168 tests). Reviewed line by line on
2026-09-11: one regression the hunt itself introduced (#27) and three small
defects fixed, suite 173 — see `log/2026-09-11-longseries-review-of-the-bug-hunt.md`.
It is the first thing to read when a check goes red.

**Read the severity scale the way the store does.** The archive is the asset:
a rival starting in 2028 cannot obtain 2026 data at any price. So, in order:
silent data loss or corruption; silent cessation of collection; a false
all-clear; a wrong domain answer; everything else. A crash is *good news* by
comparison — it is visible.

Labels used throughout:

| Label | Means |
|---|---|
| **COVERED** | Handled in code **and** a named test in `tests/` fails if the handling is removed. |
| **HANDLED** | Handled in code, but nothing automated proves it (no Docker, no network, and no clock in this suite). |
| **GAP** | Nothing handles it. Stated plainly, including where a fix was deliberately deferred. |

---

## If a check just went red and you are in an airport

1. The healthchecks email/push carries the alert text in the body — that is
   the `/fail` ping. Read it first; it names the source and the alert code.
2. **No body, just "check is down"?** That is the dead-man's switch: no ping
   arrived for a day. The collector is dead, hung, or the host is gone. It is
   *not* a finding about the publisher.
3. From anywhere with a shell on the host:
   ```bash
   docker compose ps                                     # is it Up? Up ≠ working
   docker compose logs --tail=100 amprion                # config errors, crash lines, heartbeat failures
   docker compose run --rm amprion show /sources/amprion.yaml --data /data
   ```
   `show` prints the last complete capture's counts, alerts and
   `last_change_at`, and names any capture directory that has no manifest (an
   interrupted run). Every alert is on disk in the capture manifest, so `show`
   is the source of truth when healthchecks itself is down.
4. Nothing is urgent unless bytes are at risk. A day of missed polls on a P6M
   publisher costs nothing. **Do not** delete anything under `blobs/`,
   `index.jsonl` or `captures/` to "clean up" — that is the only irreversible
   move available to you.

---

## The catalogue

| # | Failure | What the operator sees | What the system does today | Label |
|---|---|---|---|---|
| 1 | Landing page 404/410 — section moved or withdrawn | `/fail` ping with `P0 LANDING_VANISHED`; exit 2 | Records the failed run and its manifest, alerts P0, keeps everything already stored | **COVERED** |
| 2 | Landing page reshaped, documents no longer linked | `/fail` with `P1 DISCOVERY_EMPTY` and/or `P1 STRUCTURE_MISSING`; exit 3 | Discovery is `<a href>`-only, so a redesign shows up the same day rather than after the 180-day cadence; `expect_landing_text` and `expect_min_documents` are set on all three sources | **COVERED** |
| 3 | Landing page moves behind a 301 to a new URL | *Nothing.* Green ping | `follow_redirects=True` fetches the new page; the index still records the requested URL and `http_status: 200` | **GAP** (H-5, deferred) |
| 4 | Publisher adds a login / hard bot wall (403, 401) | `/fail` with `P1 LANDING_UNREACHABLE` (landing) or `P1 DOCUMENT_UNREACHABLE` / `P0 DOCUMENT_WITHDRAWN` (documents); exit 2/3 | 403 is not retried; the failure is recorded per-URL, never silently dropped | **COVERED** |
| 5 | Publisher serves a 200 interstitial (Cloudflare, "Wartungsarbeiten") | `/fail` with `P1 PAYLOAD_TOO_SMALL`, `P1 WRONG_CONTENT_TYPE`, or `P1 STRUCTURE_MISSING` | Small bodies caught by `min_payload_bytes: 50000`; large HTML at a `.pdf` URL caught by content-type + magic-byte check; the bytes are **still stored** — a block page is the evidence of when access was denied | **COVERED** |
| 6 | Source YAML broken by a hot edit (bad syntax, bad value, unmounted `./sources`) | Log line `[schedule] config error: …; watchdog notified; retrying in 86400s`, plus a `/fail` ping carrying the reason | The loop catches **any** exception around `_load()` and pings via `LONGSERIES_HEARTBEAT_URL`; every coercion raises `ConfigError`; a bad `source_id` or `heartbeat_url` is rejected at load | **COVERED** |
| 7 | Source YAML edited to a *valid but different* `source_id` | *Nothing.* Green ping, everything re-captured as `new` | Nothing. A new `source_id` is a new empty tree by design | **GAP** |
| 8 | Disk full (ENOSPC) mid-poll | `/fail` ping carrying `crashed: OSError(28, …)`; the schedule sleeps and retries | The index append rolls back to its pre-append size, so no torn row survives; a half-written blob scratch file is unlinked; the exception reaches the watchdog | **COVERED** (rollback) / **HANDLED** (ping path) |
| 9 | Disk nearly full — no ENOSPC yet | *Nothing* | Nothing. No free-space check anywhere | **GAP** |
| 10 | Container killed mid-write (`docker stop`, OOM, power) | Next `show` names the capture as incomplete; the poll is simply redone | `init: true` gives PID 1 a signal handler; blobs are finalised with `os.link` under a per-writer scratch name; the index rolls back; capture directories are claimed with `mkdir(exist_ok=False)`; `show` falls back to the newest complete capture | **COVERED** (store + `show`) / **HANDLED** (`init: true`) |
| 11 | A torn trailing line already in `index.jsonl` | `IndexCorrupt: …/index.jsonl: line N is not valid JSON …` naming the file and line | Every read raises with a location instead of a bare `JSONDecodeError`; `longseries repair` trims a **trailing** partial line only. A complete last row missing only its newline is not damage: `repair` leaves it, and the next append terminates it instead of gluing the new row onto it | **COVERED** |
| 12 | Data root not mounted (bind mount points at nothing) | *Nothing.* Green ping, everything re-captured as `new`, forever | `create_host_path: false` makes Docker refuse to start rather than invent an empty host directory | **HANDLED** (compose is not exercised by the suite) — the in-collector half is a **GAP** |
| 13 | Watchdog URL rotated, check deleted, or account lapsed | `[heartbeat] ping hc-ping.com/8f3c1e2a… FAILED after 3 attempt(s): HTTP 404` on stderr — **and nothing else** | Non-2xx is detected, `/fail` is retried 3× on 408/429/5xx, and every failure is shouted to stderr | **COVERED** (detection) / **GAP** (nothing monitors the monitor) |
| 14 | No heartbeat configured at all | `[heartbeat] NO HEARTBEAT CONFIGURED — this source is UNMONITORED` on stderr at every run | Says so, loudly, then runs anyway | **COVERED** |
| 15 | Server dribbles bytes forever (no timeout ever fires) | `/fail` with the document recorded as failed, or `P1 LANDING_UNREACHABLE` | `_get` streams under a 256 MB ceiling and a 900 s whole-request deadline — httpx has no whole-request budget of its own | **COVERED** (documents + landing) |
| 16 | The same, on `robots.txt` | *Nothing. The poll hangs and no ping is ever sent* | Nothing: the robots fetch is a plain `client.get`, outside the bounded `_get` | **GAP** |
| 17 | Replica pull (VPS → Beelink) silently stops | *Nothing* | Nothing. `ops/` was never written; there is no pull timer, no pull heartbeat, no mirror freshness check | **GAP** |
| 18 | Restart loop hammering the publisher | Log line `last capture is recent; first poll in Ns` | `seconds_until_due` waits out the remainder of the interval, clamped at both ends, skipping future-dated and unparseable capture names, and waits a **full** interval when nothing can be believed | **COVERED** |
| 19 | Clock jumps forward (bad RTC, BIOS default 2099) | Log line, then a normal wait | Future-dated captures are skipped by the schedule gate | **COVERED** (schedule) / **GAP** (a future-dated `captured_at` still mutes the staleness alarms) |
| 20 | Clock jumps backward / DST | Nothing to see | Everything is UTC end to end: `capture_id`, `captured_at`, cadence arithmetic. DST cannot touch it | **COVERED** |
| 21 | A parse returns zero rows | `extract` exit 3, `<sha>.error.json` beside the silver rows | Both parsers raise `ParseError` when they find no rows or no edition; `_via_tables` raises rather than skipping a row it cannot read | **COVERED** |
| 22 | A parse returns *fewer* rows than last time (48 → 3) | *Nothing.* `extract` exits 0 | Nothing. There is no per-source expectation on silver row counts | **GAP** |
| 23 | A document loses its parser (renamed file, new convention) | `extract` exit 3 with `no_parser_documents > 0` | Counted separately from a landing page with no parser, which is normal | **COVERED** |
| 24 | A blob is missing or does not match its own name | `<sha>.error.json`, `counts.failed`, extraction continues | Read and re-hash happen inside the try; one bad blob no longer stops the whole source on every future run | **COVERED** |
| 25 | `extract` never runs at all | *Nothing* | Nothing. `extract` is not in `compose.yaml` and not on any watchdog | **GAP** |
| 26 | Collector host lost entirely | Every check for that host goes red within a day | Nothing automatic. See **Recovery** below | **GAP** |
| 27 | Publisher serves a compressed response (`content-encoding: gzip` — every TSO does) | Between 2026-09-09 and 2026-09-11 this would have been `/fail` with `P1 LANDING_UNREACHABLE` carrying `DecodingError`, on every poll, nothing captured; now nothing | `_get` streams the bytes httpx has already decoded and rebuilds the Response without the wire-only headers (`content-encoding`, `content-length`, `transfer-encoding`), so nothing is decoded twice; the recorded `content-length` is the blob's own. A `MockTransport` never compresses, which is how the streamed rewrite passed 168 tests | **COVERED** |

---

## The ones that need more than a table row

### Publisher page moved or reshaped (#1–#3)

Three shapes, three answers. A **404/410** is `P0 LANDING_VANISHED` — the one
alert that means *stop what you are doing*, because the section moved (a human
must find it) or the source is gone (the bytes you hold just became the only
copy). A **200 with nothing behind it** is `P1 DISCOVERY_EMPTY`; without that
alert a reshaped page would stay silent for the whole declared cadence, 180
days on `P6M`. A **200 with the wrong page behind it** is caught by
`expect_landing_text` (`"Schaltfeld"` on Amprion and 50Hertz, `"Umspannwerk"`
on TransnetBW) and by `expect_min_documents: 3` on Amprion.

**Does not do:** notice a 301 to a new home. `follow_redirects=True` quietly
takes the redirect, and the index row keeps recording the *requested* URL with
`http_status: 200`, so a document that migrated to a CDN or a new section is
attributed to the old URL with no trace of what answered. Recording
`final_url` and the redirect chain was deferred (H-5): it is an additive change
to the one file that is the whole asset, and the alerting half — an
`allowed_hosts` policy — would start failing every poll for a TSO that
legitimately serves PDFs from a CDN. That is an owner call, not a code call.

**Workaround:** when a publisher redesigns, re-characterise the source by hand
(fetch the page, confirm the filenames and the disclaimer), update
`sources/*.yaml`, and check the next capture's manifest with `show`. Never
construct a URL from a date to "fix" discovery: Amprion already runs two
filename conventions on one page, and a template-based collector returns zero
rows and reports success.

### Publisher adds a login or a bot wall (#4–#5)

A hard wall (401/403, or a Cloudflare challenge that returns a non-200) is a
failed fetch: `P1 LANDING_UNREACHABLE` for the page, and per-document
`P1 DOCUMENT_UNREACHABLE`, escalating to **`P0 DOCUMENT_WITHDRAWN`** when the
index shows that exact URL was captured successfully before. That escalation
matters more than any other alert in the system: a document that used to be
there and is now refused is the retraction this collector exists to witness,
and the bytes already in `blobs/` may be the only copy in the world.

A *soft* wall — a 200 serving an interstitial — is the dangerous one, because
it looks like a new edition. Two checks catch it: `min_payload_bytes: 50000`
(an 8 KB Akamai interstitial, a 2 KB CMS 404), and a content-type plus
magic-byte check against the URL's extension (a 60 KB styled maintenance page
served at a `.pdf` URL, which used to be recorded as a new edition and then as
*another* one when the real PDF returned — two transitions of a document that
never changed). The bytes are stored either way and the disposition carries
`content_problem`, so `P1 WRONG_CONTENT_TYPE` fires and the run pings `/fail`.

**Does not do:** solve a challenge, hold a session, or rotate anything. That is
deliberate. The User-Agent is honest and carries `LONGSERIES_CONTACT` so the
publisher can reach the owner; the poll is one page plus a handful of documents
a day, with a 1.5 s gap between fetches. If a publisher walls the section, the
right response is an email, not a workaround — and the archive up to that date
is intact and is the thing that just became valuable.

### Source YAML broken by a hot edit (#6–#7)

`sources/` is a read-only mounted volume and the config is re-read **every
iteration**, so an edited YAML takes effect on the next poll with no restart.
That is the only repair channel a relocated operator has, which is exactly why
a bad edit must not be fatal.

It used to be. `ConfigError` subclasses `ValueError`, so the subclass relation
runs the wrong way and `except ConfigError` never caught the plain `ValueError`
that `int()` and `float()` raise: `min_payload_bytes: 50k`,
`stale_tolerance: '1,5'`, `expect_min_documents: three` and a missing source
file (a failed `./sources` mount) all escaped the loop, exited the process, and
`restart: unless-stopped` looped forever **with no ping**. This is the same
mistake class as the `sys.exit(1)` bug fixed on 2026-09-08 — an exception class
chosen too narrowly defeating a safety net. Today every coercion goes through
`_coerce` and re-raises `ConfigError` naming the key, `read_text()`'s `OSError`
becomes a `ConfigError`, and the loop catches `Exception` and still pings.

**Does not do:** notice an edit that is *valid but wrong*. Change `source_id`
and the collector starts a fresh empty tree beside the real one, re-captures
everything as `new`, and pings green — the same failure shape as an unmounted
data root (#12), from a typo instead of a mount. Nothing compares the config to
the history on disk.

**Workaround:** after editing a source YAML, run
`docker compose run --rm <svc> validate /sources/<x>.yaml` (it redacts the
watchdog token) and then `show`, and check that `captures` did not reset to 1.

### Disk full, and the killed process (#8–#11)

These are the same family: a write that stops halfway. Three places could leave
damage, and all three are now closed.

- **The index.** A half-written row poisoned every later *read* and every later
  *write* of that source — `save()` reads the index first — so one torn line
  killed the collector permanently over years of undamaged rows still on disk.
  `_append_index` now records the file size first and truncates back to it on
  any `BaseException`. The failed capture is lost; the archive is not.
- **A blob.** The scratch file used to be named from the content hash, so two
  writers holding the same bytes shared one `.tmp`; one killed mid-write left a
  *prefix* there that the other published under the full hash — an index row
  disagreeing with disk, silently, forever. The scratch name is now unique per
  writer (pid + uuid4) and finalisation is `os.link`, so an existing blob is
  never overwritten and the loser of a race just writes nothing.
- **A capture directory.** Capture ids are precise to the second; two runs in
  one second shared a directory and the second overwrote the first's
  `landing.html` and `manifest.json` — the record of what that run saw and
  which alerts it fired. `poll()` now claims the directory with
  `mkdir(exist_ok=False)` and suffixes on collision.

`init: true` in `compose.yaml` fixes the trigger: PID 1 was `python` with no
SIGTERM handler and the kernel *discards* SIGTERM to PID 1, so every
`docker stop` stalled 10 s and then SIGKILLed, reliably, into whatever the poll
was doing.

**Does not do:** check free space before writing, verify existing blobs, or
repair anything but a torn *trailing* index line.
`longseries repair` refuses to drop a corrupt line anywhere else — a bad row in
the middle of the file is a capture unaccounted for, and dropping it silently
is the thing this whole document exists to prevent. A full-store
`longseries verify` (re-hash every blob against its filename) was deferred: the
corruption *source* is fixed, and extraction already turns a blob that does not
match its own name into a visible `<sha>.error.json` for every document that
has a parser.

**Workaround for a torn index:**
```bash
cp /data/<source_id>/index.jsonl /data/<source_id>/index.jsonl.bak   # always
docker compose run --rm amprion repair /sources/amprion.yaml --data /data
```
If `repair` raises `IndexCorrupt` instead, the damage is not a trailing line.
Stop. Read the named line by hand, work out which capture it belongs to, and
reconstruct it from that capture's `manifest.json` (which lists every URL, its
sha256 and its disposition) before touching anything.

**Workaround for free space:** the archive grows by roughly the size of one
edition per change — kilobytes to a few megabytes per source per cycle, plus
one landing snapshot per poll. It is small. Watch it anyway: `df -h` and
`du -sh $LONGSERIES_DATA` on the same schedule as anything else on the host.
The `df`-watching host timer specified in ADR-001 Q3 was never written.

### The unmounted data root (#12)

The worst-shaped failure in the system, because every signal points the wrong
way. Bind-mount the data root at a path that does not exist and Docker used to
create an empty directory for it: the collector then found no history, recorded
every document as `new`, and pinged **success** — three green checks a day
while the archive was invisible. Both staleness alarms are gated on there being
a history (`last_change_at is not None`), so neither can fire on a store with
none. Worse, captures written under the mountpoint are shadowed the moment the
real disk remounts.

`create_host_path: false` on the bind removes the trigger: Docker refuses to
start rather than invent the directory. Run `mkdir -p ./data`, or point
`LONGSERIES_DATA` at the real disk, before the first `up`.

**Does not do:** notice from inside the collector. The in-collector half — a
`{base}/.longseries-root` marker written on first use, and a P0 when it is
missing on a collector that has run before — was deferred because it needs an
owner decision the finding does not settle: how does a collector know it has
run before, when the only state it could consult lives on the volume that is
missing? The sketch's answer (raise a P0 and sleep-and-retry rather than exit)
changes the process's failure model, and neither half can be exercised by a
suite with no Docker and no network. **This remains the highest-value
un-taken fix in the chassis.**

**Workaround until then:** after any host reboot, disk swap or move, run `show`
on each source and check `captures` and `last_change_at` against what you
expect. A reset to `captures: 1` means the root is wrong.

### Watchdog account lapsed or its URL rotated (#13–#14)

The heartbeat used to ignore the watchdog's HTTP status entirely: a 404, 429 or
503 on a `/fail` POST returned normally and the alert was discarded with no log
line and no retry, against an `except httpx.HTTPError` that a non-2xx never
triggers. And `httpx.InvalidURL` — plus the bare `ValueError` from a bare host
or an unexpanded `${LONGSERIES_HEARTBEAT_URL_AMPRION}` — escaped that handler
entirely and *replaced the run's own exception*, so an operator debugging a
full disk was shown a URL parse error instead. Today `_send` inspects the
status, retries 408/429/5xx three times on the `/fail` path only (a lost
heartbeat is recoverable tomorrow; a lost alert is not), catches `Exception`
because the contract is log-and-swallow-always, and prints every failure to
stderr with the ping URL **redacted** to host plus an 8-character prefix. A
healthchecks ping URL is an unauthenticated capability: whoever holds it can
forge success pings and mute that source's dead-man's switch forever, and log
lines and `validate` output are exactly what an operator pastes into an issue.

**Does not do:** monitor the monitor. If the check UUID is wrong, deleted, or
the account lapses, every ping 404s, the warning goes to stderr, and nothing
else in the world notices. There is one saving asymmetry: a *rotated* URL means
the old check stops receiving pings and goes red on its own — you get an alert,
with the wrong reason. A *deleted* check gives you nothing at all. ADR-001 Q4
specifies an independent dead-man from a second machine (the Beelink pull
timer's own `/fail`); it was never built. Spooling undeliverable alerts to a
file in the data root was deferred — where it lives, when it is drained and how
it is rotated are owner decisions, and the data root is the asset, not a
scratch space.

**Workaround:** twice a year, open the healthchecks dashboard and confirm three
checks are green *and receiving pings* (the "last ping" column, not just the
status). Confirm the same when the account renews. `docker compose logs | grep
heartbeat` catches a rotated URL in one command.

### The replica pull silently stopping (#17)

ADR-001 Q1 decided: a cheap VPS is the canonical always-on collector, the
Beelink runs the same stack as an independent second replica when it is up, and
bronze moves VPS → Beelink by a pull-only
`rsync -az --ignore-existing` from a systemd timer into a separate mirror root
(`/srv/longseries-mirror/vps/`), never merged into the Beelink's own tree.

**None of it is built.** There is no `ops/` directory in this repo. There is no
pull timer, no pull heartbeat, no mirror-freshness check, and no test — because
there is nothing to test. If the pull is set up by hand and then stops (the
Beelink is on its Windows boot for a month, an SSH key expires, the timer is
masked by an upgrade), the mirror silently ages and *nothing says so*. The
canonical store on the VPS is unaffected — this is a redundancy failure, not a
data-loss failure — but the second copy that ADR-001 counts on quietly stops
existing, and the extraction host reads a stale mirror without knowing it.

**Workaround until `ops/` exists:** create a fourth healthchecks check for the
pull, and make the timer's `ExecStartPost` a `curl` of it. That single line
gives the mirror the same dead-man's switch the collectors have. Until then,
`ls -la /srv/longseries-mirror/vps/*/captures | tail` is the manual check, and
`rsync --delete` is never, under any circumstances, correct here.

### A parse that returns zero rows, or too few (#21–#25)

Both parsers already fail loudly on nothing: `ParseError("no rows found by
either path")`, `ParseError("no 'Stand <month> <year>' in document")`,
`ParseError("no tooltip blocks found — page structure changed?")`. And
`_via_tables` — which had zero test coverage and silently dropped rows it could
not read — now raises under a recognised header instead. That mattered because
`build_series` reported the dropped substations as **DISAPPEARED**: a footnote
marker turning `380 kV` into `380 kV*` manufactured an absence the publisher
never stated, in the exact field the product exists to report.

**Does not do:** notice a *drop*. Forty-eight TransnetBW substations becoming
three is a clean run with `parsed: 1`. The per-source expectation on silver row
counts has been open since 2026-09-03 and is still open.

**Does not do:** run at all, unless a human runs it. `extract` is not a compose
service and is not on any watchdog, so its exit code 3 — the signal for a
failed parse, a corrupt blob, or a document that lost its parser — is only seen
by whoever typed the command. Collection is safe (bronze is the asset and it
keeps filling), but the derived series can be frozen for months without a word.

**Workaround:** run `extract` and `series` on a cadence beside collection, and
read the counts:
```bash
python -m longseries extract sources/amprion.yaml --data $LONGSERIES_DATA
# parsed / skipped / no_parser / no_parser_documents / failed / rows  — watch `rows`
python -m longseries series sources/amprion.yaml --data $LONGSERIES_DATA
```
A row count that halves between editions is a parser problem until proven
otherwise. `--replay` re-parses stored bytes, which is the whole point of
keeping them: a wrong quarter is repairable, forever, as long as bronze is
intact.

### Clock skew and DST (#19–#20)

Everything is UTC end to end — `capture_id`, `captured_at`, cadence arithmetic
— and no local time is read anywhere, so DST cannot reach this system. Two
clocks are deliberately kept separate and must stay that way: `edition` (the
publisher's own "Stand") and `observed_at` (when we captured it). Conflating
them is how a collector reports a change that never happened.

Skew is the real risk, and it used to be severe: `seconds_until_due` clamped
only the lower bound, so one capture directory dated in the future — a dead
CMOS cell's BIOS default of 2099 — put the collector to sleep for 26,420 days,
and re-selected the same directory on every restart, so restarting did not fix
it. It also failed **open**: any directory name that would not parse
(`backup-before-rsync` sorts after every `2026-…` timestamp) made it return
`0.0`, silently disabling the restart-loop gate that keeps a crash-looping
container from hammering the publisher. Both are closed: the gate uses the
newest name that parses and is not in the future, clamps to the interval at
both ends, and waits a **full** interval when nothing can be believed.

**Does not do:** protect the alarms from a future-dated `captured_at`. If the
host clock runs ahead when rows are written and is then corrected, `age = now -
last_change_at` is negative, `age > cadence` is false, and `ZERO_NEW_FILES` and
`STALE` stay silent until real time catches up. A `P1 CLOCK_SKEW` alert was
sketched and not built.

**Workaround:** run NTP on the collector host. If a clock has already been
wrong, `grep captured_at /data/<source_id>/index.jsonl | tail` shows how far.
Do not edit those rows: the index is append-only and a wrong timestamp is a
true record of a wrong clock. Note the skew in the log and move on.

---

## Recovery: the collector host is gone

**Where the only copy of anything is.** Two things, and they are not equally
replaceable:

| Thing | Where | Replaceable? |
|---|---|---|
| The code | `github.com/workflow-tools/beelink-bonus`, branch `main` | Yes, entirely |
| Source characterisations, registry, docs | Same repo | Yes |
| `.env` — contact address, three healthchecks ping URLs | The host only, gitignored | Yes: re-create the checks, edit `.env` |
| **`$LONGSERIES_DATA` — blobs, index.jsonl, captures** | **The host, plus any replica or backup you made** | **No. Never. At any price.** |

Everything above bronze is rebuildable from bronze. Bronze is rebuildable from
nothing. A lost 2026 edition cannot be bought, re-fetched, or reconstructed —
the publisher keeps no archive, which is the entire reason this collector
exists.

**Procedure on a new host** (VPS or Beelink, Docker is the only requirement —
no GPU):

```bash
# 1. Code
git clone https://github.com/workflow-tools/beelink-bonus
cd beelink-bonus/longseries

# 2. Restore the store BEFORE starting anything. Into a real directory:
mkdir -p /srv/longseries
rsync -a <backup-or-replica>:/srv/longseries/ /srv/longseries/    # never --delete

# 3. Sanity-check what you restored, per source, before a collector touches it
ls /srv/longseries/*/blobs | head
wc -l /srv/longseries/de-tso-amprion-netzanschluss/index.jsonl
python -m longseries show sources/amprion.yaml --data /srv/longseries

# 4. Secrets. Re-use the SAME healthchecks checks if they still exist; the
#    dead-man's switch only means anything if the check has continuous history.
cp .env.example .env && $EDITOR .env      # LONGSERIES_CONTACT, three ping URLs,
                                          # LONGSERIES_DATA=/srv/longseries

# 5. Start. The restart gate will wait out the remainder of the interval from
#    the newest restored capture rather than polling immediately.
docker compose up -d --build
docker compose logs -f amprion
```

**If there is no backup and no replica**, the archive is gone and no amount of
work recovers it. Start collecting again the same day — the gap is permanent
but the series ahead of it is not — and record the gap explicitly in
`log/`. Do not silently restart into an empty root and let the new history
masquerade as continuous.

**So, the standing instruction:** back up `$LONGSERIES_DATA`. Provider
snapshots on the VPS, plus the ADR-001 Q1 pull to a second machine. Two
independent copies of a directory that grows by a few megabytes a cycle is the
cheapest insurance in this entire project, and it is the only failure in this
document that has no code-level mitigation at all.

---

## Known gaps, ranked

Honest list, worst first. Everything here is either unbuilt or deliberately
deferred, and every deferral names the reason.

1. **No off-host backup or replica is actually running** (#26, #17). ADR-001 Q1
   specifies both; neither exists as code in this repo. Owner action, not a
   code fix.
2. **A collector cannot tell an unmounted root from a fresh install** (#12).
   The compose-side trigger is removed; the in-collector marker is deferred
   pending an owner decision on the failure model.
3. **Nothing monitors the monitor** (#13). A deleted or lapsed healthchecks
   check silences a source permanently; only stderr says so.
4. **The `robots.txt` fetch is unbounded** (#16). It bypasses the streamed,
   deadline-guarded `_get`, so the H-4 hang — poll never returns, no ping ever
   sent, container Up — survives on that one request. Small window, same shape,
   not yet closed.
5. **`extract` is unscheduled and unwatched** (#25), and a silver row-count
   drop raises nothing (#22). The derived series can freeze for months while
   collection stays green.
6. **No free-space check** (#9). ENOSPC is handled cleanly; approaching ENOSPC
   is invisible.
7. **A future-dated `captured_at` mutes the staleness alarms** (#19). The
   schedule gate is protected; the alarms are not.
8. **Redirects are not recorded** (#3, H-5, deferred). `final_url` and the
   redirect chain are missing from every index row; an `allowed_hosts` policy
   is an owner call.
9. **`robots.txt` is not content-addressed.** It is written into the capture
   directory but never passed through `save()`, so it is the one payload with
   no index row and no dedup. Deferred: putting robots rows in the index
   interacts with the role-scoped staleness clock, and "which roles count as
   documents" is a design question.
10. **No `longseries verify`** (full-store re-hash). Deferred: the corruption
    source is fixed and extraction surfaces a mismatched blob for every
    document that has a parser.
11. **Undeliverable alerts are not spooled** (#13). Deferred: location,
    drain policy and rotation are owner decisions, and the data root is the
    asset.
12. **`compose.yaml` is not exercised by any test** — no Docker in the suite.
    `init: true`, `create_host_path: false` and the log ceiling are verified by
    reading, not by running.

---

## Related

- `docs/ADR-001-architecture.md` — why the topology is what it is, plus the
  2026-09-09 note recording which of its claims these fixes changed.
- `README.md` — install, alert table, what lands on disk.
- `docs/USER-STORIES.md` — every acceptance criterion names its test.
- `log/2026-09-09-longseries-bug-hunt.md` — the hunt this document came out of.
