"""US-10: the install is one command, and safe to run twice."""
from __future__ import annotations

import io
import json

import httpx

from longseries.setup import MARKER, env_name, read_env, run_setup

GOOD = """source_id: de-tso-{n}
publisher: {n} GmbH
landing_url: https://example.test/{n}/
declared_cadence: P1M
polarity: lists_state
contact: mailto:archive@example.test
"""


def _sources(tmp_path, names=("amprion", "50hertz")):
    d = tmp_path / "sources"
    d.mkdir(exist_ok=True)
    for n in names:
        (d / f"{n}.yaml").write_text(GOOD.format(n=n), encoding="utf-8")
    return d


class _API:
    """healthchecks.io Management API, as far as setup uses it."""

    def __init__(self, status=201):
        self.posts: list[httpx.Request] = []
        self.status = status

    def handler(self, request):
        self.posts.append(request)
        if self.status >= 400:
            return httpx.Response(self.status, json={"error": "nope"})
        body = json.loads(request.content)
        short = body["name"].split("/")[-1]
        return httpx.Response(self.status, json={"uuid": f"uuid-{short}", "name": body["name"],
                                                 "ping_url": f"https://hc-ping.com/{short}-0123456789abcdef"})

    @property
    def transport(self):
        return httpx.MockTransport(self.handler)


def _run(tmp_path, api=None, **overrides):
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    kw = dict(sources_dir=tmp_path / "sources", data_root=data, env_path=tmp_path / ".env",
              contact="mailto:me@example.test", api_key="k-secret", api_url="https://hc.test/api/v3/",
              host_data_path="/srv/longseries", transport=api.transport if api else None)
    kw.update(overrides)
    out = io.StringIO()
    rc = run_setup(out=out, **kw)
    return rc, out.getvalue()


def test_env_name_follows_the_compose_convention():
    assert env_name("amprion.yaml") == "LONGSERIES_HEARTBEAT_URL_AMPRION"
    assert env_name("sources/50hertz.yaml") == "LONGSERIES_HEARTBEAT_URL_50HERTZ"
    assert env_name("transnetbw.yaml") == "LONGSERIES_HEARTBEAT_URL_TRANSNETBW"
    assert env_name("my-source.v2.yaml") == "LONGSERIES_HEARTBEAT_URL_MY_SOURCE_V2"


def test_setup_creates_one_check_per_source_and_writes_env_and_marker(tmp_path):
    _sources(tmp_path)
    api = _API()
    rc, out = _run(tmp_path, api)
    assert rc == 0, out
    assert len(api.posts) == 2
    for req in api.posts:
        assert str(req.url) == "https://hc.test/api/v3/checks/"
        assert req.headers["x-api-key"] == "k-secret"
        body = json.loads(req.content)
        assert body["timeout"] == 86400 and body["grace"] == 6 * 3600, "README: period 1 day, grace 6 h"
        assert body["unique"] == ["name"], "re-running must find the check, not duplicate it"
        assert body["channels"] == "*", "a check with no integrations alerts nobody"
        assert body["name"].startswith("longseries/de-tso-")
    env = read_env(tmp_path / ".env")
    assert env["LONGSERIES_CONTACT"] == "mailto:me@example.test"
    assert env["LONGSERIES_DATA"] == "/srv/longseries"
    assert env["LONGSERIES_HEARTBEAT_URL_AMPRION"] == "https://hc-ping.com/de-tso-amprion-0123456789abcdef"
    assert env["LONGSERIES_HEARTBEAT_URL_50HERTZ"] == "https://hc-ping.com/de-tso-50hertz-0123456789abcdef"
    marker = json.loads((tmp_path / "data" / MARKER).read_text(encoding="utf-8"))
    assert marker["longseries_root"] is True and marker["host_path"] == "/srv/longseries"
    owner = (tmp_path / "data").stat()
    assert env["LONGSERIES_UID"] == str(owner.st_uid) and env["LONGSERIES_GID"] == str(owner.st_gid), \
        "compose runs the collectors as the data root's owner, read from the directory, never guessed"
    assert (tmp_path / ".env").stat().st_mode & 0o777 == 0o600, "ping URLs are capabilities: owner-only"
    assert "0123456789abcdef" not in out, "a ping URL is a capability; the summary shows a redacted form"
    assert "k-secret" not in out and "k-secret" not in (tmp_path / ".env").read_text(encoding="utf-8")


def test_setup_is_idempotent(tmp_path):
    _sources(tmp_path)
    api = _API()
    assert _run(tmp_path, api)[0] == 0
    env_before = (tmp_path / ".env").read_text(encoding="utf-8")
    marker_before = (tmp_path / "data" / MARKER).read_text(encoding="utf-8")
    rc, out = _run(tmp_path, api)
    assert rc == 0
    assert len(api.posts) == 2, "a source that already has a URL is not re-created"
    assert (tmp_path / ".env").read_text(encoding="utf-8") == env_before
    assert (tmp_path / "data" / MARKER).read_text(encoding="utf-8") == marker_before
    assert "kept" in out


def test_setup_keeps_an_existing_url_and_fills_only_the_missing_one(tmp_path):
    _sources(tmp_path)
    (tmp_path / ".env").write_text("# mine\nFOO=bar\nLONGSERIES_HEARTBEAT_URL_AMPRION=https://hc-ping.com/keep-me\n", encoding="utf-8")
    api = _API()
    rc, _ = _run(tmp_path, api)
    assert rc == 0 and len(api.posts) == 1
    assert json.loads(api.posts[0].content)["name"] == "longseries/de-tso-50hertz"
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert text.startswith("# mine\nFOO=bar\n"), "unrelated lines and comments survive byte for byte"
    env = read_env(tmp_path / ".env")
    assert env["LONGSERIES_HEARTBEAT_URL_AMPRION"] == "https://hc-ping.com/keep-me"
    assert env["LONGSERIES_HEARTBEAT_URL_50HERTZ"].startswith("https://hc-ping.com/de-tso-50hertz")


def test_setup_replaces_placeholders_copied_from_env_example(tmp_path):
    _sources(tmp_path, names=("amprion",))
    (tmp_path / ".env").write_text("LONGSERIES_CONTACT=mailto:you@example.com   # placeholder\n"
                                   "LONGSERIES_HEARTBEAT_URL_AMPRION=https://hc-ping.com/uuid-amprion\n", encoding="utf-8")
    api = _API()
    rc, _ = _run(tmp_path, api)
    assert rc == 0 and len(api.posts) == 1
    env = read_env(tmp_path / ".env")
    assert env["LONGSERIES_CONTACT"] == "mailto:me@example.test"
    assert env["LONGSERIES_HEARTBEAT_URL_AMPRION"].startswith("https://hc-ping.com/de-tso-amprion")


def test_setup_without_an_api_key_leaves_the_slot_empty_and_shouts(tmp_path):
    _sources(tmp_path, names=("amprion",))
    rc, out = _run(tmp_path, api=None, api_key=None)
    assert rc == 0, "no key is not an error; it is a loud gap"
    assert "UNMONITORED" in out and "NO watchdog" in out
    env = read_env(tmp_path / ".env")
    assert env["LONGSERIES_HEARTBEAT_URL_AMPRION"] == ""
    assert (tmp_path / "data" / MARKER).is_file()


def test_setup_refuses_an_invalid_source_and_writes_nothing(tmp_path):
    _sources(tmp_path, names=("amprion",))
    (tmp_path / "sources" / "broken.yaml").write_text("source_id: x\npublisher: y\n", encoding="utf-8")
    api = _API()
    rc, out = _run(tmp_path, api)
    assert rc == 1 and "broken.yaml" in out
    assert api.posts == []
    assert not (tmp_path / ".env").exists()
    assert not (tmp_path / "data" / MARKER).exists()


def test_setup_refuses_a_data_root_that_is_not_there(tmp_path):
    _sources(tmp_path, names=("amprion",))
    rc, out = _run(tmp_path, _API(), data_root=tmp_path / "nowhere")
    assert rc == 1 and "mounted" in out
    assert not (tmp_path / ".env").exists()


def test_setup_requires_a_contact(tmp_path):
    _sources(tmp_path, names=("amprion",))
    rc, out = _run(tmp_path, _API(), contact=None)
    assert rc == 1 and "LONGSERIES_CONTACT" in out


def test_setup_reports_an_api_failure_and_still_writes_the_rest(tmp_path):
    _sources(tmp_path, names=("amprion",))
    api = _API(status=401)
    rc, out = _run(tmp_path, api)
    assert rc == 1 and "401" in out and "FAILED" in out
    env = read_env(tmp_path / ".env")
    assert env["LONGSERIES_CONTACT"] == "mailto:me@example.test" and env["LONGSERIES_DATA"] == "/srv/longseries"
    assert env["LONGSERIES_HEARTBEAT_URL_AMPRION"] == ""


def test_an_existing_check_is_returned_not_duplicated(tmp_path):
    """The API answers 200 (not 201) when `unique` matched an existing check."""
    _sources(tmp_path, names=("amprion",))
    api = _API(status=200)
    rc, out = _run(tmp_path, api)
    assert rc == 0 and "existing" in out
    assert read_env(tmp_path / ".env")["LONGSERIES_HEARTBEAT_URL_AMPRION"].startswith("https://hc-ping.com/")


def test_read_env_reads_what_compose_reads(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# c\nA=1   # inline\nB=\"two words\"\nC='x'\n\nD=http://h/p#frag\n", encoding="utf-8")
    assert read_env(p) == {"A": "1", "B": "two words", "C": "x", "D": "http://h/p#frag"}
