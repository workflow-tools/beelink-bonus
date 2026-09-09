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
from .heartbeat import Heartbeat, run_with_heartbeat
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
    print(json.dumps({k: (str(v) if k == "declared_cadence" else v) for k, v in c.__dict__.items()}, indent=2))
    return 0


def _ping_config_failure(source: str, err: Exception, transport=None) -> bool:
    """A config error is the one failure the per-source heartbeat cannot report from
    the config, because the config is what is broken. Fall back to the environment
    URL so the operator learns the reason within one interval instead of inferring
    it from a check that goes stale a day later. Never raises."""
    url = os.environ.get("LONGSERIES_HEARTBEAT_URL")
    if not url:
        return False
    try:
        Heartbeat(url, transport=transport).fail(f"config error in {source}: {err}")
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


def seconds_until_due(store: ContentAddressedStore, source_id: str, every_seconds: float, now: datetime) -> float:
    """How long to wait before the first poll after a (re)start. A container in a
    restart loop must not hammer the publisher: if the latest capture is younger
    than the interval, wait out the remainder."""
    d = store.source_dir(source_id) / "captures"
    if not d.exists():
        return 0.0
    names = sorted(p.name for p in d.iterdir() if p.is_dir())
    if not names:
        return 0.0
    try:
        last = datetime.strptime(names[-1], "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.0
    return max(0.0, every_seconds - (now - last).total_seconds())


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
        except ConfigError as e:
            pinged = _ping_config_failure(args.source, e, heartbeat_transport)
            print(f"[schedule] config error: {e}; watchdog {'notified' if pinged else 'NOT notified (no LONGSERIES_HEARTBEAT_URL)'}; retrying in {int(every)}s", file=sys.stderr)
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
        except Exception as e:  # a crash must not stop the schedule; the missing heartbeat has already fired
            print(f"[schedule] poll crashed: {e!r}; sleeping {int(every)}s", file=sys.stderr)
        sleeper(every)


def cmd_extract(args) -> int:
    from .extract.run import extract_source
    config = _load(args.source)
    counts = extract_source(ContentAddressedStore(Path(args.data)), config, replay=args.replay)
    print(json.dumps(counts, indent=2))
    return 3 if counts["failed"] else 0


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
    m = store.read_manifest(config.source_id, caps[-1])
    print(json.dumps({"captures": len(caps), "latest": caps[-1], "counts": m.get("counts"), "failed": m.get("failed"),
                      "alerts": m.get("alerts"), "landing_status": m.get("landing_status"),
                      "last_change_at": (store.last_change_at(config.source_id) or "never") and str(store.last_change_at(config.source_id))}, indent=2))
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
