"""CLI: the thing a container or a cron job actually runs.

    python -m longseries poll     sources/x.yaml --data /data
    python -m longseries show     sources/x.yaml --data /data
    python -m longseries validate sources/x.yaml

Exit codes: 0 clean · 2 run failed (a P0 fired) · 3 run completed with P1 alerts.
Alerts go to stderr so a scheduler's log shows them without parsing JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapter import BaseAdapter
from .config import ConfigError, load_source_config
from .heartbeat import Heartbeat, run_with_heartbeat
from .store import ContentAddressedStore


def _load(path: str):
    try:
        return load_source_config(path)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args) -> int:
    c = _load(args.source)
    print(json.dumps({k: (str(v) if k == "declared_cadence" else v) for k, v in c.__dict__.items()}, indent=2))
    return 0


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
    for name, fn in (("poll", cmd_poll), ("show", cmd_show), ("validate", cmd_validate)):
        sp = sub.add_parser(name)
        sp.add_argument("source")
        if name != "validate":
            sp.add_argument("--data", required=True)
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
