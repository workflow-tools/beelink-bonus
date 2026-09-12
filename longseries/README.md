# longseries — capture chassis for vanishing data

Polls a public web page on a schedule, follows the documents it links to,
and stores every byte it sees, content-addressed and never overwritten. Later,
an extraction tier turns those bytes into records. The reason it exists: some
bodies publish a figure, overwrite it next month, and keep no archive — the
series exists only if somebody was collecting. Each month that passes adds
history no later entrant can obtain.

**This is an archive with a scraper attached, not a scraper.** The scraper is
disposable; the archive is the asset and cannot be reconstructed later.

First series: Amprion's Schaltfeld map — which substations in its control area
have a free bay and connection capacity, green/red, with a supplementary
document. Published *"zur unverbindlichen Orientierung … ohne Gewähr …
Änderungen sind jederzeit möglich."*

## Where it runs — read this first

Collection needs **no GPU** and almost no CPU. It must keep running while the
owner's machines are in a shipping container, so the deployable unit is a
Docker Compose stack that runs identically on the Beelink, a €5 VPS, or a
laptop. The Beelink is for the *extraction* tier (local LLMs), which can lag
collection by days without harm.

Recommended: run collection on a VPS *and* on the Beelink (the store
deduplicates; two copies of the asset beat one), and rsync `bronze/` to
wherever extraction runs.

## Install (Beelink, VPS, anything with Docker)

The Beelink lives in Ubuntu 24.04. Docker Engine there is a system service, so
the collectors come back after an unattended reboot with nobody logged in —
provided the machine *boots* Ubuntu: `../docs/BEELINK-BOOT-ORDER.md` is the
firmware fix for a dual-boot box that otherwise restarts into Windows.
Collection needs no GPU; extraction that calls Ollama runs on the same boot,
where Ollama is a host systemd service (`docs/OLLAMA-NIGHTWORK-DASHBOARDS.md`).

Four lines. The data directory is the one thing you create by hand, because
only you know which disk is the asset; `setup` does everything else.

```bash
git clone https://github.com/workflow-tools/beelink-bonus && cd beelink-bonus/longseries
sudo mkdir -p /srv/longseries && sudo chown "$USER" /srv/longseries    # THE ASSET lives here — pick the real disk
LONGSERIES_DATA=/srv/longseries HEALTHCHECKS_API_KEY=… docker compose run --rm setup
docker compose up -d --build                                             # one container per source
```

`setup` runs inside the image (no Python on the host). It validates every YAML
in `sources/`, writes the `.longseries-root` marker into the data root, creates
one healthchecks.io check per source through the Management API (period 1 day,
grace 6 h, every integration your project already has attached) and writes
`.env` — contact, data root, one ping URL per source. It asks for the contact
address and the API key when they are not in the environment, keeps every
value already in `.env`, and is safe to run again: a check that exists is
returned, never duplicated. The API key comes from **Project settings → API
access** (read-write) on healthchecks.io, lives only in that one shell line,
and is never written to `.env`. Without a key, `setup` leaves the slot empty
and says **UNMONITORED** in capitals; fill it in later, or re-run with the key.

Then:

```bash
docker compose logs -f amprion            # first poll runs immediately
docker compose run --rm amprion show /sources/amprion.yaml --data /data
```

The `amprion` container polls once a day (`--every P1D`), sleeps, repeats.
Polling more often than the publisher's cadence is free — unchanged files
write zero bytes — and bounds how late a change is noticed. A collector
refuses to write into a data root without the marker — an empty mountpoint
looks exactly like a fresh install (failure mode #12) — and pings `/fail`
with the reason every interval until the disk is back.

One-off poll without the scheduler:

```bash
docker compose run --rm amprion poll /sources/amprion.yaml --data /data
```

Exit codes: `0` clean · `2` a P0 fired (landing page vanished) · `3` P1 alerts.

## Alerts — one external service does everything

Create a check at [healthchecks.io](https://healthchecks.io) (free tier is
fine): period **1 day**, grace **6 hours**. Put its ping URL in `.env`.

- Every run pings it. **No ping for a day = the collector is dead** and
  healthchecks emails/pushes you. That is the dead-man's switch; silence can
  never masquerade as success.
- A failed run, or any P0/P1 alert, pings `/fail` **with the alert text as
  the body**, so the same email tells you *what* is wrong.

| Alert | Severity | Meaning |
|---|---|---|
| `LANDING_VANISHED` | **P0** | Landing page 404/410. The section moved (needs a human) or the source is gone. |
| `LANDING_UNREACHABLE` | P1 | Could not fetch it (DNS, refused, timeout, persistent 5xx). A routing problem is *not* a finding — check the network before concluding anything. |
| `ZERO_NEW_FILES` | P1 | Nothing new or changed, and a change was due per the declared cadence. |
| `STALE` | P1 | Bytes identical for > 1.5× the declared cadence. Publisher broke, or you are eating a cache. |
| `PAYLOAD_TOO_SMALL` | P1 | A new/changed file is under `min_payload_bytes` — an error page served with a 200? |
| `WRONG_CONTENT_TYPE` | P1 | A 200 whose body is not what the URL promised (HTML at a `.pdf` URL). Stored anyway — a block page is evidence — but not a new edition. |
| `DOCUMENT_UNREACHABLE` | P1 | A linked document could not be fetched. That edition is not in the store. |
| `DOCUMENT_WITHDRAWN` | **P0** | A document we captured successfully before now fails. A retraction is the event this collector exists to witness. |

## When something goes wrong

**[`docs/FAILURE-MODES.md`](docs/FAILURE-MODES.md) is the first thing to read**
— especially if a check has gone red and you are not at your desk. It
catalogues every way this collector can fail (publisher moved, bot wall, bad
YAML edit, disk full, killed mid-write, watchdog lapsed, replica pull stopped,
clock skew, host lost entirely): what the operator actually sees, what the code
does today, what it does **not** do, and the workaround. Each entry is marked
COVERED (a test proves it), HANDLED (code does it, nothing proves it) or GAP
(nothing does it) — including the recovery procedure for a lost host and the
one thing that has no code-level mitigation at all: **back up
`$LONGSERIES_DATA`.**

Fast triage: `docker compose ps` → `docker compose logs --tail=100 <svc>` →
`docker compose run --rm <svc> show /sources/<x>.yaml --data /data`. Every
alert is on disk in the capture manifest, so `show` is the source of truth when
healthchecks itself is down. Nothing under `blobs/`, `index.jsonl` or
`captures/` is ever deleted to "clean up".

## What lands on disk

```
$LONGSERIES_DATA/de-tso-amprion-netzanschluss/
├── blobs/ab/abcdef…          raw bytes, verbatim, named by SHA-256, never rewritten
├── index.jsonl               one line per capture: url, sha, headers, status, timestamp, disposition
└── captures/2026-09-03T104407Z/
    ├── manifest.json         every URL seen this poll and its disposition; counts; alerts
    ├── landing.html          the page as rendered that day ("Stand:" dates, disclaimers)
    └── robots.txt            the terms that applied the day you collected
```

A changed file at the same URL keeps **both** versions — that pair is often the
product. Never delete anything under `blobs/`. Back the whole directory up.

For the landing page, "changed" means the **visible text** changed. Pages like
50Hertz's carry a fresh CSRF token and viewstate on every fetch; those are not
changes, and they do not mint a new blob. Each poll's raw HTML is still kept
verbatim under `captures/<id>/landing.html`.

## The register — decisions and dates, next to the code

`registry/` holds one YAML per series the owner has decided about: verdict,
which decision it is about (collect vs productize), the future buyer's
question, the option premium, the wedge, pre-committed kill criteria and a
review date. Schema in `registry/README.md`; `pytest` checks every built
collector names real `source_id`s. The Schaltfeld series is registered as an
**OPTION** (collect now, review 2026-11-30); two orbital sources are
registered but not yet collected, each with a no-code path to a source
config.

## Adding a series

1. Copy `sources/amprion.yaml`, fill it in. `polarity` is mandatory and never
   guessed — does the publisher list where a thing *is* possible, or where it
   is *not*? Getting that implicit inverts every answer silently.
2. `declared_cadence` must come with `declared_cadence_evidence`: the
   publisher's own words and where you read them. If they don't say, put
   `[LOW]` in the evidence and replace it by observation.
3. Add a service block in `compose.yaml` (copy the `amprion` one).
4. `docker compose up -d`. No code change.

Discovery is by scraping `<a href>` links from the landing page, filtered by
extension. There is deliberately no way to build a URL from a date: filename
conventions change (Amprion has two on one page), and a template-based
collector returns zero rows and reports success.

## Development

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest            # 188 tests; HTTP is faked with httpx.MockTransport, PDFs are generated in-test, nothing touches the network
```

Stories are in `docs/USER-STORIES.md`; every acceptance criterion names its
test. Tests were written before the implementation.

## Verification record (2026-09-03)

No CI. This is the record.

| Check | Result |
|---|---|
| `pytest` | 90/90 (168/168 after the 2026-09-09 bug hunt, 173/173 after the 2026-09-11 review of it, 188/188 with `setup` on 2026-09-12 — see `docs/FAILURE-MODES.md`) |
| Host poll ×2 against live Amprion | 3 new → 3 unchanged, 3 blobs, exit 0 |
| Container poll ×2 against live Amprion | same, from inside the image |
| Container with `--network=none` | clean failed run, exit 2, `P1 LANDING_UNREACHABLE`, manifest written, no traceback |
| Host poll ×2 against live TransnetBW | landing new → unchanged, exit 0 |
| Host poll ×2 against live 50Hertz | landing new → unchanged (viewstate/CSRF tokens differ every fetch; visible text identical) |
| `extract` on the captured Amprion blob | 10 rows, edition 2026-04, via pymupdf table detection |
| `extract` on the captured TransnetBW landing | 48 rows, edition 2026-05: 36 nicht / 8 mittelfristig / 4 langfristig verfügbar, 12 with MW bands |
| `docker build` | builds; behind a TLS-intercepting proxy use `--secret id=ca,src=…` |

## Extraction (Epic 2) — bronze → silver → series

Runs wherever the bronze store is (the Beelink, or the same VPS). Needs the
`extract` extra (pymupdf):

```bash
pip install -e ".[extract]"                 # or: docker build --build-arg EXTRAS='[extract]' -t longseries:extract .
python -m longseries extract sources/amprion.yaml    --data $LONGSERIES_DATA   # bronze -> silver, idempotent
python -m longseries extract sources/transnetbw.yaml --data $LONGSERIES_DATA
python -m longseries series  sources/amprion.yaml    --data $LONGSERIES_DATA   # transitions, appeared/disappeared, restatements
```

Parsers are pure functions of stored bytes, versioned, re-runnable with
`--replay`. Every silver row carries provenance back to the blob and the
parser version. Two clocks on every row: `edition` (the publisher's "Stand")
and `observed_at` (our capture). A failed parse writes `<sha>.error.json`.

| Source | Payload | Parser | What a row holds |
|---|---|---|---|
| Amprion | supplementary PDF (text table) | `amprion-supplementary` | substation, kV, municipality, n-0/n-1, earliest year, remarks; listed = available |
| TransnetBW | landing page HTML | `transnetbw-netzanschlusskarte` | substation, nicht/mittelfristig/langfristig verfügbar, kV, earliest year, design, feed-in/load MW bands, qualifiers |

No language model is involved yet. The map PDFs turned out to be unlabeled
vector dots — substation names live in the supplementary table, not on the
map — so the Beelink's job is cross-publisher normalisation (three-valued vs
two-valued availability, MW bands, differing "Stand" clocks), not vision.

## Not built yet

Gold-layer normalisation across publishers; 50Hertz (JS-rendered map, source
not yet located) and TenneT (browser challenge + robots.txt naming AI
crawlers — check from a browser before deciding). See `docs/USER-STORIES.md`.
