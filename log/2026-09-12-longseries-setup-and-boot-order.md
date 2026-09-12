# 2026-09-12 — longseries: the install as one command; Beelink boot-order runbook

**Branch:** `claude/longseries-chassis` → `main` · **Suite:** 173 → **188**.

## Why an installer after the panel said no

The 2026-09-09 design panel filed "an installer" under *do not build*; the
subtract designer's reason was "real; irrelevant at three sources and one
poll a day" — priced by how often it runs. The owner's constraint is
attention: the five-command install had not happened in the week since, and
the part needing a human was creating one healthchecks check per source and
pasting three URLs into `.env` under the right names. When the owner's time
is the scarce input and model time is cheap, a three-hour build that removes
twenty minutes of attention *and* the reason a series has not started is the
right trade. Recorded as a dated override in
`docs/DESIGN-OPTIONS-operator-experience.md`; the panel's text is untouched.

The critic's ruling that a preflight must never refuse to *collect* still
stands: `setup` never gates collection on the watchdog.

## What was built

- **`longseries setup`** (`src/longseries/setup.py`, `cmd_setup`), run as
  `docker compose run --rm setup` — a `setup` service in a compose profile,
  so `up` never starts it. In order: validate every YAML in `/sources`
  (nothing written if one is bad); write the `.longseries-root` marker into
  the mounted data root; create one healthchecks.io check per source through
  the Management API v3 (`POST /checks/`, `timeout` 86 400, `grace` 21 600,
  `channels: "*"`, `unique: ["name"]` so a re-run gets the existing check
  back with HTTP 200); write `.env`, keeping every existing line byte for
  byte and replacing only `.env.example` placeholders. The API key is read
  from that one shell and never written — `.env` is handed to every
  collector container. Without a key the slot is written empty and the
  summary says **UNMONITORED**. Files written inside the container are
  chowned to the owner of the mounted directory.
- **The data-root marker gate** (FAILURE-MODES #12, known gap #2 — closed).
  `poll` and `schedule` refuse to write into a root without the marker;
  in the loop it is a `ConfigError`, so the existing config-failure path
  pings `/fail` with the reason every interval and recovers on remount with
  no restart. Read commands need no marker. The failure model the deferral
  was waiting on: fail closed — a capture into the wrong directory is a
  capture that will be shadowed, not a capture.
- **`docs/BEELINK-BOOT-ORDER.md`** (repo root `docs/`): the Beelink lives in
  Ubuntu but every unattended restart lands in Windows. `efibootmgr -o`,
  the setup-menu fallback, GRUB's saved default, the two Windows-side guards
  (`bcdedit /set "{fwbootmgr}" displayorder … /addfirst`, fast startup off),
  BootNext for a deliberate one-off boot into Windows, and the two firmware
  settings a collector host needs (AC-loss power-on, USB not skipped by fast
  boot). Listed in `CLAUDE.md`.
- README install section: four lines, then what `setup` did for you.
  US-10 and US-11 in `docs/USER-STORIES.md` name every test.

## What was run

- `pytest`: **188/188** — 15 new (`tests/test_setup.py` ×12 with a fake
  healthchecks API over `httpx.MockTransport`; two schedule/poll gate tests;
  one CLI wiring test with no terminal and no key).
- `compose.yaml` parsed and the anchor merge checked with PyYAML. (This
  first pass said "no Docker in this sandbox" — wrong; see the section below.
  The claim had not been checked.)
- Healthchecks Management API field names checked against
  `healthchecks.io/docs/api/` on 2026-09-12: `X-Api-Key`, `timeout`,
  `grace`, `channels`, `unique`, `ping_url`.

## Owner steps now

```bash
git clone https://github.com/workflow-tools/beelink-bonus && cd beelink-bonus/longseries
sudo mkdir -p /srv/longseries && sudo chown "$USER" /srv/longseries
LONGSERIES_DATA=/srv/longseries HEALTHCHECKS_API_KEY=… docker compose run --rm setup
docker compose up -d --build
```

Then the boot-order runbook, once, so the next unattended restart comes back
in Ubuntu with the containers up.

## Steps that were skipped, then done — 2026-09-12, second pass

Asked whether Docker/Ubuntu best practice had been skipped in preprocessing or
processing: yes. The first pass tested the code and read the compose file. It
did not lint, lock, harden, build or run. All of it done in this pass:

**Preprocessing**
- `ruff` (F, E4/E7/E9, B, S, I; config now in `pyproject.toml`): 41 findings
  on the default set — 11 unused imports / import order auto-fixed, nine
  single-letter `l` names renamed, one dead assignment, two `zip()` calls now
  say `strict=False` (pairwise on purpose). Clean.
- `hadolint` on the Dockerfile: DL3013 (unpinned pip). Fixed by installing from
  `requirements.lock` / `requirements-extract.lock` (pip-compile, hashes) so
  two builds a year apart install the same bytes. Clean.
- `docker compose config` and `--profile setup config` with Compose v5.1.1
  (the CLI needs no daemon), plus 0 errors against the compose-spec JSON
  schema.
- Hardening: collectors run as the data root's owner (`setup` records
  `LONGSERIES_UID/GID` from the mounted directory — never guessed), with
  `cap_drop: ALL`, `no-new-privileges`, a read-only image filesystem, `/tmp`
  on tmpfs and a 1 GB memory cap; the image itself defaults to `USER 1000`
  and `PYTHONDONTWRITEBYTECODE`. `.env` is written 0600.
- The API key is now typed at `setup`'s prompt, not left in shell history.

**Processing**
- End to end over real sockets with the CLI installed from the locks into a
  fresh venv: a fake publisher that gzips everything and a fake healthchecks
  API — `setup` → `poll` (PDF stored decoded under its own sha256, success
  ping received) → `show` → second `poll` unchanged → an unmarked root
  refused → `repair` → `setup` again, idempotent.
- A Docker daemon *could* be started in the sandbox. Image built through the
  proxy with the Dockerfile's own `--secret id=ca` hook (211 MB, uid 1000,
  `/data` owned by 1000). Then, with an overlay compose file pointing at the
  fakes on the host: `docker compose run --rm setup` → `.env` 0600 and the
  marker both owned by 1000, one check created; `run --rm amprion poll` as
  1000 → clean run, every file in the data root owned by 1000, the User-Agent
  carrying the contact, the watchdog pinged; `show`; `up -d amprion` →
  `running=true user=1000:1000 readonly=true capdrop=[ALL] init=true
  mem=1 GiB`; `down`.
- **Found only by running it:** the first container `setup` died with
  `PermissionError` on `/data/.longseries-root`. Root without
  `CAP_DAC_OVERRIDE` cannot write into a directory owned by someone else —
  `cap_drop: ALL` had taken away the one thing root was there for. The
  one-off `setup` service now gets exactly `CHOWN` and `DAC_OVERRIDE` back.
  This would have been the owner's first-install experience.

Not done, and why: no image vulnerability scan (trivy/grype need a database
download; the base is `python:3.11-slim`, refreshed with
`docker compose build --pull`), and no test of the interactive prompts
(`getpass` under a real TTY) — the non-TTY path is what the tests and the
container run exercised; the prompt path is the owner's first install.
