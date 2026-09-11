"""CLI: the thing a container or a cron job actually runs.

    python -m longseries poll     sources/x.yaml --data /data
    python -m longseries schedule sources/x.yaml --data /data --every P1D
    python -m longseries show     sources/x.yaml --data /data
    python -m longseries validate sources/x.yaml
    python -m longseries extract  sources/x.yaml --data /data [--replay]     # bronze -> silver (needs .[extract])
    python -m longseries series   sources/x.yaml --data /data [--json]       # silver -> transitions

    python -m longseries repair   sources/x.yaml --data /data                # trim a torn trailing index line

Exit codes: 0 clean · 2 run failed (a P0 fired) · 3 run completed with P1 alerts.
Alerts go to stderr so a scheduler's log shows them without parsing JSON."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import sys
import time
from pathlib import Path

from .adapter import BaseAdapter
from .config import ConfigError, load_source_config, parse_cadence
from .heartbeat import Heartbeat, redact, run_with_heartbeat
from .store import ContentAddressedStore


def _load(path: str):
    """Load a source YAML. LONGSERIES_CONTACT and LONGSERIES_HEARTBEAT_URL in the
    environment override the file, so a real mailto: and a watchdog token never
    have to be committed."""
    c = load_source_config(path)
    if os.environ.get("LONGSERIES_CONTACT"):
        c.contact = os.environ["LONGSERIES_CONTACT"]
    if os.environ.get("LONGSERIES_HEARTBEAT_URL"):
        c.heartbeat_url = os.environ["LONGSERIES_HEARTBEAT_URL"]
    return c


def cmd_validate(args) -> int:
    c = _load(args.source)
    # The heartbeat URL is an unauthenticated capability (anyone holding it can forge
    # success pings and mute this source's dead-man's switch), and this output is
    # what an operator pastes into an issue when asking for help.
    shown = {k: (str(v) if k == "declared_cadence" else v) for k, v in c.__dict__.items()}
    if shown.get("heartbeat_url"):
        shown["heartbeat_url"] = f"set ({redact(shown['heartbeat_url'])})"
    print(json.dumps(shown, indent=2))
    return 0


def _ping_config_failure(source: str, err: Exception, transport=None, *, what: str = "config error") -> bool:
    """A config error — and any crash before the per-source Heartbeat exists — is the
    one failure that heartbeat cannot report, because the thing it would be built
    from is what is broken. Fall back to the environment URL so the operator learns
    the reason within one interval instead of inferring it from a check that goes
    stale a day later. Never raises."""
    url = os.environ.get("LONGSERIES_HEARTBEAT_URL")
    if not url:
        return False
    try:
        Heartbeat(url, transport=transport).fail(f"{what} in {source}: {err!r}")
        return True
    except Exception as e:  # never raise from the alert path — but say so, do not swallow silently
        print(f"[schedule] watchdog ping failed: {e!r}", file=sys.stderr)
        return False


def cmd_poll(args) -> int:
    config = _load(args.source)
    store = ContentAddressedStore(Path(args.data))
    adapter = BaseAdapter(config, store)
    heartbeat = Heartbeat(config.heartbeat_url) if config.heartbeat_url else None
    run = run_with_heartbeat(lambda: adapter.poll(), heartbeat)
    print(json.dumps({
        "capture_id": run.capture_id, "source_id": run.source_id, "failed": run.failed,
        "landing_status": run.landing_status, "counts": run.counts,
        "alerts": [a.as_dict() for a in run.alerts],
    }, indent=2))
    for a in run.alerts:
        print(f"ALERT {a.severity} {a.code}: {a.message}", file=sys.stderr)
    if run.failed:
        return 2
    return 3 if run.alerts else 0


def _capture_time(name: str) -> datetime | None:
    """Parse a capture directory name, tolerating the '.2' a same-second collision
    appends. Returns None for anything that is not one of ours."""
    try:
        return datetime.strptime(name.split(".")[0], "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def seconds_until_due(store: ContentAddressedStore, source_id: str, every_seconds: float, now: datetime) -> float:
    """How long to wait before the first poll after a (re)start. A container in a
    restart loop must not hammer the publisher: if the latest capture is younger
    than the interval, wait out the remainder.

    Two ways this gate used to switch itself off. It took sorted(names)[-1] and
    returned 0.0 when that would not parse — and any name beginning with a letter
    ('backup-before-rsync') sorts after every 2026-… timestamp, so one stray
    directory disabled the gate permanently. And it clamped only the lower bound,
    so one future-dated capture (a dead CMOS cell's BIOS default is 2099) slept the
    collector for 26,420 days, across restarts. Now: the newest name that actually
    parses and is not in the future decides, the wait is clamped to the interval at
    both ends, and 'no idea' waits rather than polls."""
    d = store.source_dir(source_id) / "captures"
    if not d.exists():
        return 0.0
    names = sorted(p.name for p in d.iterdir() if p.is_dir())
    if not names:
        return 0.0
    for name in reversed(names):
        last = _capture_time(name)
        if last is None or last > now:
            continue
        return min(every_seconds, max(0.0, every_seconds - (now - last).total_seconds()))
    # Captures exist but none of them can be believed: fail CLOSED. Polling now is
    # the behaviour a crash loop turns into a request flood at the publisher.
    print(f"[schedule] no usable capture timestamp in {d}; waiting a full interval", file=sys.stderr)
    return every_seconds


def cmd_schedule(args, *, sleeper=time.sleep, heartbeat_transport=None) -> int:
    """Poll on a fixed interval (default P1D). Polling more often than the
    declared cadence is cheap — the store writes zero bytes for unchanged files —
    and it bounds how late a change is noticed. Runs until stopped."""
    every = parse_cadence(args.every).total_seconds()
    gated = False
    while True:
        # Re-read the config every iteration. sources/ is a mounted volume, so an
        # edited YAML takes effect on the next poll with no restart — that is the
        # only repair channel a relocated operator has. It also means a bad edit
        # must not be fatal: a ConfigError here loops and retries rather than
        # exiting into a restart loop that never pings anything.
        try:
            config = _load(args.source)
        except Exception as e:  # NOT `except ConfigError`: ConfigError subclasses ValueError,
            # so the relation runs the wrong way and a plain ValueError (a malformed
            # int) or an OSError (a failed ./sources mount) escaped into a restart
            # loop that pinged nothing. Anything at all here loops and retries.
            pinged = _ping_config_failure(args.source, e, heartbeat_transport)
            print(f"[schedule] config error: {e!r}; watchdog {'notified' if pinged else 'NOT notified (no LONGSERIES_HEARTBEAT_URL)'}; retrying in {int(every)}s", file=sys.stderr)
            sleeper(every)
            continue
        if not gated:
            wait = seconds_until_due(ContentAddressedStore(Path(args.data)), config.source_id, every, datetime.now(timezone.utc))
            gated = True
            if wait > 0:
                print(f"[schedule] last capture is recent; first poll in {int(wait)}s", file=sys.stderr)
                sleeper(wait)
        try:
            rc = cmd_poll(args)
            print(f"[schedule] poll finished rc={rc}; sleeping {int(every)}s", file=sys.stderr)
        except Exception as e:
            # A crash must not stop the schedule — but it must not be silent either.
            # run_with_heartbeat only pings once a Heartbeat exists, and everything
            # that happens before that (building it, opening the store) used to be
            # swallowed here: three iterations, no ping, container Up. A duplicate
            # /fail costs nothing; a missing one costs the whole safety story.
            pinged = _ping_config_failure(args.source, e, heartbeat_transport, what="poll crashed")
            print(f"[schedule] poll crashed: {e!r}; watchdog {'notified' if pinged else 'NOT notified (no LONGSERIES_HEARTBEAT_URL)'}; sleeping {int(every)}s", file=sys.stderr)
        sleeper(every)


def cmd_extract(args) -> int:
    from .extract.run import extract_source
    config = _load(args.source)
    counts = extract_source(ContentAddressedStore(Path(args.data)), config, replay=args.replay)
    print(json.dumps(counts, indent=2))
    # no_parser_documents is not cosmetic: a document the extractor cannot route is a
    # frozen series that collection keeps looking healthy through.
    return 3 if (counts["failed"] or counts["no_parser_documents"]) else 0


def cmd_series(args) -> int:
    from .extract.run import load_silver
    from .extract.series import build_series, render_markdown
    config = _load(args.source)
    rows = load_silver(ContentAddressedStore(Path(args.data)), config.source_id)
    series = build_series(rows)
    if args.json:
        print(json.dumps({k: v for k, v in series.items() if k != "history"}, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(series, config.source_id))
    return 0


def cmd_repair(args) -> int:
    """Trim a torn TRAILING line from index.jsonl — the one damage a killed or
    out-of-space writer can leave. Anything else raises: a corrupt row in the
    middle of the file is a capture unaccounted for, never something to drop."""
    config = _load(args.source)
    removed = ContentAddressedStore(Path(args.data)).repair_index(config.source_id)
    print(json.dumps({"source_id": config.source_id, "bytes_removed": removed,
                      "repaired": bool(removed)}, indent=2))
    return 0


def cmd_show(args) -> int:
    config = _load(args.source)
    store = ContentAddressedStore(Path(args.data))
    caps = sorted(p.name for p in (store.source_dir(config.source_id) / "captures").glob("*")) if store.source_dir(config.source_id).exists() else []
    if not caps:
        print("no captures yet")
        return 0
    # A capture directory with no manifest is what a killed poll leaves (PID 1 has no
    # SIGTERM handler, so `docker stop` SIGKILLs it 10 s later). Reading caps[-1]
    # unconditionally made the one command an operator runs to check on a collector
    # the one that raises. Fall back to the newest complete capture and say so.
    incomplete = [c for c in caps if not (store.capture_dir(config.source_id, c) / "manifest.json").exists()]
    complete = [c for c in caps if c not in incomplete]
    if not complete:
        print(json.dumps({"captures": len(caps), "latest": None, "incomplete_captures": incomplete,
                          "note": "no capture has a manifest; every run so far was interrupted"}, indent=2))
        return 0
    m = store.read_manifest(config.source_id, complete[-1])
    last_change = store.last_change_at(config.source_id)
    print(json.dumps({"captures": len(caps), "latest": complete[-1], "incomplete_captures": incomplete,
                      "counts": m.get("counts"), "failed": m.get("failed"),
                      "alerts": m.get("alerts"), "landing_status": m.get("landing_status"),
                      "last_change_at": str(last_change) if last_change else "never"}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="longseries")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("poll", cmd_poll), ("schedule", cmd_schedule), ("show", cmd_show), ("validate", cmd_validate),
                     ("extract", cmd_extract), ("series", cmd_series), ("repair", cmd_repair)):
        sp = sub.add_parser(name)
        sp.add_argument("source")
        if name != "validate":
            sp.add_argument("--data", required=True)
        if name == "schedule":
            sp.add_argument("--every", default="P1D", help="poll interval, ISO-8601 duration or daily/weekly (default P1D)")
        if name == "extract":
            sp.add_argument("--replay", action="store_true", help="re-parse blobs that already have silver output")
        if name == "series":
            sp.add_argument("--json", action="store_true")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
