"""silver -> the series. Two clocks on every row: 'edition' (what the publisher
says the world was, from when) and 'observed_at' (when we captured it). The
product is mostly the differences between consecutive editions — and the
restatements, where one edition was observed twice with different content."""
from __future__ import annotations

from collections import defaultdict

TRACKED_FIELDS = ("state", "availability", "design", "earliest_year", "voltage_kv", "remarks",
                  "feed_in_mw", "load_mw", "qualifiers")


def build_series(rows: list[dict]) -> dict:
    """Group by entity; order by (edition, observed_at); emit per-entity history,
    transitions between consecutive editions, entities that appear/disappear,
    and restatements (same edition, different content)."""
    by_entity: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_entity[r["entity"]].append(r)
    editions = sorted({r["edition"] for r in rows})
    present: dict[str, set[str]] = {e: set() for e in editions}
    for r in rows:
        present[r["edition"]].add(r["entity"])

    transitions, restatements, history = [], [], {}
    for entity, ers in by_entity.items():
        ers.sort(key=lambda r: (r["edition"], r["observed_at"]))
        history[entity] = ers
        # restatements: same edition observed with different tracked content
        seen_in_edition: dict[str, dict] = {}
        for r in ers:
            prev = seen_in_edition.get(r["edition"])
            if prev is not None:
                diff = _diff(prev, r)
                if diff:
                    restatements.append({"entity": entity, "edition": r["edition"],
                                         "first_observed_at": prev["observed_at"], "then_observed_at": r["observed_at"],
                                         "changes": diff})
            seen_in_edition[r["edition"]] = r
        # transitions: latest observation per edition, compared to the previous edition's
        latest_per_edition = [seen_in_edition[e] for e in sorted(seen_in_edition)]
        for a, b in zip(latest_per_edition, latest_per_edition[1:]):
            diff = _diff(a, b)
            if diff:
                transitions.append({"entity": entity, "from_edition": a["edition"], "to_edition": b["edition"], "changes": diff})

    appeared, disappeared = [], []
    for e_prev, e_next in zip(editions, editions[1:]):
        for ent in sorted(present[e_next] - present[e_prev]):
            appeared.append({"entity": ent, "edition": e_next})
        for ent in sorted(present[e_prev] - present[e_next]):
            disappeared.append({"entity": ent, "last_edition": e_prev, "absent_from": e_next})

    return {"editions": editions, "entities": sorted(by_entity), "history": history,
            "transitions": transitions, "appeared": appeared, "disappeared": disappeared,
            "restatements": restatements}


def _diff(a: dict, b: dict) -> dict:
    return {f: {"from": a.get(f), "to": b.get(f)} for f in TRACKED_FIELDS if a.get(f) != b.get(f) and (f in a or f in b)}


def render_markdown(series: dict, source_id: str) -> str:
    out = [f"# {source_id} — series", "", f"Editions: {', '.join(series['editions']) or '(none)'}  ·  Entities: {len(series['entities'])}", ""]
    for title, key, fmt in (
        ("Transitions", "transitions", lambda t: f"- **{t['entity']}** {t['from_edition']} → {t['to_edition']}: " + "; ".join(f"{k} {v['from']!r}→{v['to']!r}" for k, v in t['changes'].items())),
        ("Appeared", "appeared", lambda t: f"- **{t['entity']}** first listed in {t['edition']}"),
        ("Disappeared", "disappeared", lambda t: f"- **{t['entity']}** last listed {t['last_edition']}, absent from {t['absent_from']}"),
        ("Restatements (same edition, different content)", "restatements", lambda t: f"- **{t['entity']}** edition {t['edition']}, observed {t['first_observed_at'][:10]} then {t['then_observed_at'][:10]}: " + "; ".join(f"{k} {v['from']!r}→{v['to']!r}" for k, v in t['changes'].items())),
    ):
        out += [f"## {title} ({len(series[key])})", ""] + ([fmt(t) for t in series[key]] or ["- none"]) + [""]
    out += ["## Latest state per entity", "", "| entity | edition | state | design | earliest_year | capacity / remarks |", "|---|---|---|---|---|---|"]
    for ent in series["entities"]:
        r = series["history"][ent][-1]
        extra = r.get("remarks") or " · ".join(x for x in (r.get("feed_in_mw") and f"Einspeisung {r['feed_in_mw']}", r.get("load_mw") and f"Last {r['load_mw']}", *(r.get("qualifiers") or [])) if x)
        out.append(f"| {ent} | {r['edition']} | {r.get('state') or r.get('availability','')} | {r.get('design','')} | {r.get('earliest_year','')} | {extra} |")
    return "\n".join(out) + "\n"
