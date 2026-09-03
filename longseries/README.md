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

```bash
git clone https://github.com/workflow-tools/beelink-bonus
cd beelink-bonus/longseries
cp .env.example .env && $EDITOR .env      # contact, heartbeat URL, data dir
docker compose up -d --build              # starts one container per source
docker compose logs -f amprion            # first poll runs immediately
docker compose run --rm amprion show /sources/amprion.yaml --data /data
```

That's it. The `amprion` container polls once a day (`--every P1D`), sleeps,
repeats. Polling more often than the publisher's cadence is free — unchanged
files write zero bytes — and bounds how late a change is noticed.

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
pytest            # 64 tests; HTTP is faked with httpx.MockTransport, nothing touches the network
```

Stories are in `docs/USER-STORIES.md`; every acceptance criterion names its
test. Tests were written before the implementation.

## Verification record (2026-09-03)

No CI. This is the record.

| Check | Result |
|---|---|
| `pytest` | 64/64 |
| Host poll ×2 against live Amprion | 3 new → 3 unchanged, 3 blobs, exit 0 |
| Container poll ×2 against live Amprion | same, from inside the image |
| Container with `--network=none` | clean failed run, exit 2, `P1 LANDING_UNREACHABLE`, manifest written, no traceback |
| `docker build` | builds; behind a TLS-intercepting proxy use `--secret id=ca,src=…` |

## Not built yet

The extraction tier (Epic 2): replayable parsers over `blobs/`, entity
crosswalk, polarity normalisation, a bitemporal fact table, and the Ollama
structured-output call for the map PDF. See `docs/USER-STORIES.md` → "Out of
scope for Epic 1". Collection is running; extraction can wait — the bytes
cannot.
