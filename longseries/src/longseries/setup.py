"""`longseries setup` — the install, as one command that runs inside the image.

    docker compose run --rm setup        # from longseries/, after creating the data root

What it does, in order — and nothing is written if step 1 fails:
  1. validates every YAML in the sources directory;
  2. marks the mounted data root with `.longseries-root`, so a collector can tell
     the asset's disk from an empty mountpoint (FAILURE-MODES #12);
  3. creates one healthchecks.io check per source through the Management API
     (period 1 day, grace 6 h, every integration the project already has attached)
     — or leaves the slot empty and says UNMONITORED when there is no API key;
  4. writes `.env` next to compose.yaml, keeping every value already there.

Safe to run twice: existing URLs are kept, the marker is kept, and the API is asked
with `unique: ["name"]`, so a check that already exists is returned, not duplicated.
The API key is read from the environment of this one run and never written anywhere:
`.env` is handed to every collector container, and the key can delete checks."""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .config import ConfigError, load_source_config
from .heartbeat import redact

MARKER = ".longseries-root"
DEFAULT_API_URL = "https://healthchecks.io/api/v3/"
PERIOD_SECONDS = 24 * 3600   # one poll a day
GRACE_SECONDS = 6 * 3600     # README: period 1 day, grace 6 h
CONTACT_KEY = "LONGSERIES_CONTACT"
DATA_KEY = "LONGSERIES_DATA"


class SetupError(Exception):
    pass


def env_name(yaml_path: str | Path) -> str:
    """amprion.yaml -> LONGSERIES_HEARTBEAT_URL_AMPRION. compose.yaml and .env.example
    key the watchdog on the FILE stem, not the source_id, so this must too."""
    stem = re.sub(r"[^A-Za-z0-9]+", "_", Path(yaml_path).stem).strip("_").upper()
    return f"LONGSERIES_HEARTBEAT_URL_{stem}"


def _is_placeholder(value: str) -> bool:
    """A value copied from .env.example is not a configuration."""
    return "uuid-" in value or "example.com" in value


def read_env(path: Path) -> dict[str, str]:
    """KEY=VALUE lines the way compose reads them: comments and blanks skipped, an
    inline ` # comment` after an unquoted value dropped, matching quotes stripped."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
            value = value[1:-1]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        out[key] = value
    return out


def write_env(path: Path, updates: dict[str, str]) -> None:
    """Rewrite the KEY= lines named in `updates` in place; keep every other line,
    comments included, byte for byte; append the keys that were not there."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    pending = dict(updates)
    out: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        key = stripped.partition("=")[0].strip() if "=" in stripped and not stripped.startswith("#") else None
        if key is not None and key in pending:
            out.append(f"{key}={pending.pop(key)}")
        else:
            out.append(raw)
    if pending:
        if out and out[-1].strip():
            out.append("")
        out.append(f"# written by `longseries setup` on {datetime.now(timezone.utc).date().isoformat()}")
        out.extend(f"{k}={v}" for k, v in pending.items())
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)   # ping URLs are capabilities; compose reads it as the owner
    _match_owner(path, path.parent)


def _match_owner(path: Path, like: Path) -> None:
    """Inside the container this runs as root; the host user must still own what was
    written. Best effort — on a Docker Desktop mount chown is a no-op anyway."""
    try:
        st = like.stat()
        os.chown(path, st.st_uid, st.st_gid)
    except (OSError, AttributeError):
        pass


def data_root_is_marked(root: str | Path) -> bool:
    return (Path(root) / MARKER).is_file()


def mark_data_root(root: Path, host_path: str | None) -> bool:
    """Create the marker if it is missing. Returns True when it was created now."""
    marker = root / MARKER
    if marker.exists():
        return False
    marker.write_text(json.dumps({
        "longseries_root": True,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "created_by": "longseries setup",
        "host_path": host_path,
        "note": "Collectors refuse to write into a data root without this file. Do not copy it to another directory.",
    }, indent=2) + "\n", encoding="utf-8")
    _match_owner(marker, root)
    return True


def create_check(client: httpx.Client, api_url: str, api_key: str, *, name: str, tags: str, desc: str) -> tuple[str, bool]:
    """POST /checks/ with `unique: ["name"]`: 201 = created, 200 = the existing check
    of that name. Returns (ping_url, created_now)."""
    r = client.post(api_url.rstrip("/") + "/checks/", headers={"X-Api-Key": api_key},
                    json={"name": name, "tags": tags, "desc": desc, "timeout": PERIOD_SECONDS,
                          "grace": GRACE_SECONDS, "channels": "*", "unique": ["name"]})
    if r.status_code not in (200, 201):
        raise SetupError(f"healthchecks API answered HTTP {r.status_code} for {name}: {r.text[:200]!r}")
    body = r.json()
    if not body.get("ping_url"):
        raise SetupError(f"healthchecks API returned no ping_url for {name}")
    return body["ping_url"], r.status_code == 201


@dataclass
class Slot:
    env: str
    source_id: str
    status: str      # kept | created | existing | unmonitored | failed
    detail: str = ""


def run_setup(*, sources_dir: Path, data_root: Path, env_path: Path, contact: str | None, api_key: str | None,
              api_url: str = DEFAULT_API_URL, host_data_path: str | None = None,
              transport: httpx.BaseTransport | None = None, out=None) -> int:
    out = out or sys.stdout

    def say(s: str = "") -> None:
        print(s, file=out)

    yamls = sorted(Path(sources_dir).glob("*.yaml"))
    if not yamls:
        say(f"setup: no *.yaml in {sources_dir}; nothing to install")
        return 1
    configs, bad = [], []
    for p in yamls:
        try:
            configs.append((p, load_source_config(p)))
        except ConfigError as e:
            bad.append(str(e))
    if bad:
        say("setup: refusing to write anything while a source YAML is invalid:")
        for b in bad:
            say(f"  - {b}")
        return 1

    root = Path(data_root)
    if not root.is_dir():
        say(f"setup: data root {root} is not a directory — is it mounted? Create it on the host first; "
            f"compose refuses to invent it (FAILURE-MODES #12).")
        return 1

    existing = read_env(Path(env_path))
    kept_contact = existing.get(CONTACT_KEY, "")
    if _is_placeholder(kept_contact):
        kept_contact = ""
    contact = (kept_contact or contact or "").strip()
    if not contact.startswith(("mailto:", "http://", "https://")):
        say(f"setup: {CONTACT_KEY} is required — a mailto: or https: address that goes into the User-Agent so a "
            f"publisher can reach you (station-5 withdrawal risk); got {contact!r}")
        return 1

    updates: dict[str, str] = {}
    if kept_contact != contact:
        updates[CONTACT_KEY] = contact
    if not existing.get(DATA_KEY):
        updates[DATA_KEY] = host_data_path or "./data"
    # compose runs every collector as `user: ${LONGSERIES_UID}:${LONGSERIES_GID}` — the owner
    # of the data root, read here from the mounted directory itself, so nothing in the
    # asset is ever written by root and no uid has to be guessed.
    owner = root.stat()
    if not existing.get("LONGSERIES_UID"):
        updates["LONGSERIES_UID"] = str(owner.st_uid)
    if not existing.get("LONGSERIES_GID"):
        updates["LONGSERIES_GID"] = str(owner.st_gid)
    created_marker = mark_data_root(root, existing.get(DATA_KEY) or host_data_path)

    slots: list[Slot] = []
    rc = 0
    with httpx.Client(transport=transport, timeout=30.0) as client:
        for p, cfg in configs:
            key = env_name(p)
            current = existing.get(key, "")
            if current and not _is_placeholder(current):
                slots.append(Slot(key, cfg.source_id, "kept", current))
                continue
            if not api_key:
                updates[key] = ""
                slots.append(Slot(key, cfg.source_id, "unmonitored",
                                  "no HEALTHCHECKS_API_KEY — create a check (period 1 day, grace 6 h) and fill this in, or re-run with the key"))
                continue
            try:
                url, new = create_check(client, api_url, api_key, name=f"longseries/{cfg.source_id}",
                                        tags=f"longseries {cfg.source_id}", desc=f"{cfg.publisher} — {cfg.landing_url}")
            except (SetupError, httpx.HTTPError, ValueError) as e:
                rc = 1
                updates[key] = ""
                slots.append(Slot(key, cfg.source_id, "failed", str(e)))
                continue
            updates[key] = url
            slots.append(Slot(key, cfg.source_id, "created" if new else "existing", url))

    write_env(Path(env_path), updates)

    say(f"setup: sources    {len(configs)} valid: " + ", ".join(cfg.source_id for _, cfg in configs))
    say(f"setup: data root  {root} — {MARKER} {'created' if created_marker else 'already there'}"
        + (f" (host path {existing.get(DATA_KEY) or host_data_path})" if (existing.get(DATA_KEY) or host_data_path) else "")
        + f"; collectors will run as uid {existing.get('LONGSERIES_UID') or owner.st_uid}"
          f":{existing.get('LONGSERIES_GID') or owner.st_gid}, its owner")
    say(f"setup: .env       {env_path} — {'updated' if updates else 'unchanged'}"
        + (f" ({', '.join(sorted(updates))})" if updates else ""))
    say("setup: watchdogs")
    width = max(len(s.env) for s in slots)
    for s in slots:
        if s.status in ("kept", "created", "existing"):
            say(f"  {s.env.ljust(width)}  {s.status:<11} {redact(s.detail)}   longseries/{s.source_id}")
        elif s.status == "unmonitored":
            say(f"  {s.env.ljust(width)}  UNMONITORED {s.detail}")
        else:
            say(f"  {s.env.ljust(width)}  FAILED      {s.detail}")
    unmonitored = [s for s in slots if s.status in ("unmonitored", "failed")]
    if unmonitored:
        say()
        say(f"setup: WARNING — {len(unmonitored)} source(s) have NO watchdog. Nothing will notice if they stop collecting. "
            f"Re-run `docker compose run --rm setup` with HEALTHCHECKS_API_KEY set, or paste ping URLs into {env_path}.")
    say()
    say("setup: next  ->  docker compose up -d --build")
    return rc
