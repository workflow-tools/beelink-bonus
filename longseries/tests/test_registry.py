"""The option register must stay honest against the source configs."""
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
SOURCES = ROOT / "sources"
REQUIRED = {"id", "title", "status", "decision", "verdict", "verdict_date", "dossiers",
            "collector", "stations", "future_question", "premium", "wedge", "kill_criteria",
            "review_date", "route", "owner_checks", "history"}
STATUSES = {"option", "product", "parked", "killed"}


def entries():
    files = sorted(REGISTRY.glob("*.yaml"))
    assert files, "registry/ has no entries"
    return [(f, yaml.safe_load(f.read_text(encoding="utf-8"))) for f in files]


def source_ids():
    return {yaml.safe_load(f.read_text(encoding="utf-8"))["source_id"] for f in SOURCES.glob("*.yaml")}


def test_required_fields_and_status():
    for f, e in entries():
        missing = REQUIRED - set(e)
        assert not missing, f"{f.name}: missing {sorted(missing)}"
        assert e["status"] in STATUSES, f"{f.name}: status {e['status']!r}"
        assert e["decision"] in {"collect", "productize"}, f"{f.name}: decision"


def test_options_have_kill_criteria_and_a_future_review_date():
    for f, e in entries():
        if e["status"] != "option":
            continue
        assert e["kill_criteria"], f"{f.name}: an option without kill criteria is a wish"
        assert date.fromisoformat(str(e["review_date"])) > date.fromisoformat(str(e["verdict_date"])), f"{f.name}: review_date"


def test_built_collectors_name_real_sources():
    ids = source_ids()
    for f, e in entries():
        c = e["collector"]
        if c.get("built"):
            assert c.get("sources"), f"{f.name}: built collector lists no sources"
            unknown = set(c["sources"]) - ids
            assert not unknown, f"{f.name}: sources not under sources/: {sorted(unknown)}"
        else:
            assert not c.get("sources"), f"{f.name}: not built but lists sources"
            assert c.get("how_to_build"), f"{f.name}: not built and no how_to_build"


def test_history_is_dated_and_ends_in_current_status():
    for f, e in entries():
        h = e["history"]
        assert h and all("date" in x and "status" in x for x in h), f"{f.name}: history rows need date and status"
        assert h[-1]["status"] == e["status"], f"{f.name}: last history status != status"
