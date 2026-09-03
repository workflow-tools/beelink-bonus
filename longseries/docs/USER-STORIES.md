# Long-Series Chassis — User Stories (Epic 1: Capture)

Stories are the source of the tests in `tests/`. Each acceptance criterion
names the test that proves it. The rules behind them are the owner's
collector spec (`patterns/skills/vanishing-data-prospector/references/collector-design.md`)
and the falsification rules in that skill's `SKILL.md`. Where a story
exists because something went wrong once, the story says so.

Governing idea: **this is an archive with a scraper attached, not a scraper.**
The scraper is disposable. The archive must be correct on the first poll and
can never be reconstructed later.

---

## US-01 Content-addressed, never-overwrite raw store

As the archive engine,
I want every fetched payload stored by its SHA-256, unmodified, with the
source URL, HTTP headers and capture timestamp recorded beside it,
so that unchanged files write zero new bytes, a changed file at the same URL
keeps *both* versions, and any later fact can be traced to the exact bytes.

Acceptance:
- `test_store_new_payload_is_written_under_its_sha256`
- `test_store_identical_bytes_write_zero_new_bytes`
- `test_store_changed_bytes_at_same_url_keep_both_versions`
- `test_store_record_carries_url_headers_status_timestamp_and_discovered_on`
- `test_store_versions_lists_every_capture_of_a_url_in_order`
- `test_store_blobs_are_partitioned_by_hash_prefix` (ext4 inode hygiene)
- `test_store_never_rewrites_an_existing_blob_even_if_asked`

## US-02 Landing page and terms snapshotted every poll

As the archive engine,
I want the rendered landing-page HTML, `robots.txt` and (when found) the
terms page stored on every poll,
so that "Stand:" dates, prose qualifiers and re-use terms — which drift
independently of the payload — are reconstructible for the day of capture.

Why: a capacity figure that quietly gains the word *vorläufig* has changed
meaning without changing value. And the only legal question that will ever
be asked is "what did the terms say the day you collected?"

The landing page is also a **tracked payload** with versions, not only a
snapshot: TransnetBW publishes its per-substation availability list as page
text (🔴 nicht verfügbar / 🟢 mittelfristig verfügbar / langfristig
verfügbar, "Stand 05/2026") with no document to download. A source with an
empty `accept_extensions` is landing-only.

Acceptance:
- `test_run_snapshots_landing_html_every_poll_even_when_unchanged`
- `test_run_snapshots_robots_txt_every_poll`
- `test_run_manifest_records_landing_sha_and_robots_sha`
- `test_landing_page_is_tracked_as_a_payload`
- `test_landing_only_source_captures_nothing_but_the_landing_page`
- `test_source_config_accepts_empty_extensions_meaning_landing_only`

## US-03 Run manifest per poll

As the archive engine,
I want each poll to write one manifest listing every URL seen and its
disposition (new / unchanged / changed / failed),
so that "what did we see on 2026-08-25" is answerable as a *set*, not
reconstructed from per-file records.

Acceptance:
- `test_run_manifest_lists_every_discovered_url_with_a_disposition`
- `test_run_manifest_counts_match_dispositions`
- `test_failed_fetch_is_a_disposition_not_a_crash`

## US-04 Discovery by link scraping, never by URL construction

As the archive engine,
I want document URLs discovered by scraping links from the landing page,
so that a renamed file or a moved section is still captured.

Why: in one worked case the naming convention changed three times in ten
months and the landing page moved sections. A pattern-based collector would
have returned zero rows daily and reported success — the same error as a
self-constructed 404, running unattended forever.

Acceptance:
- `test_discover_finds_renamed_files_without_any_date_pattern`
- `test_discover_resolves_relative_links_to_absolute`
- `test_discover_ignores_mailto_javascript_and_fragment_links`
- `test_base_adapter_has_no_url_template_hook` (guardrail: the API offers no
  place to put a date pattern)

## US-05 Landing-page 404 is a P0

As the operator who will be mid-relocation when it happens,
I want a 404/410 on the landing page itself to raise a P0 alert and abort
the poll,
so that "the section moved" or "the source is gone" is known within a day,
not a quarter.

Acceptance:
- `test_landing_404_raises_landing_vanished`
- `test_landing_410_raises_landing_vanished`
- `test_landing_vanished_produces_p0_alert`

## US-05b Unreachable is not vanished

As the operator working from a container or a hotel network,
I want a landing page that cannot be fetched (connection refused, DNS,
timeout, persistent 5xx) recorded as a *failed run with a P1
`LANDING_UNREACHABLE`*, never as the P0 `LANDING_VANISHED`,
so that a routing problem is never written into the record as though the
source were gone.

Why: `web.archive.org` was blocked from an agent container and fine from a
laptop; that one difference nearly decided a whole project. The manifest is
still written, so the gap in the series is visible and explained.

Acceptance:
- `test_landing_unreachable_is_a_failed_run_with_p1_not_p0`
- `test_landing_persistent_5xx_is_a_failed_run_with_p1`

## US-06 Polite, identifiable, retrying fetches

As the archive engine,
I want every request to carry an honest User-Agent with contact details,
retry 429/5xx with exponential backoff a bounded number of times, and
never retry a 404,
so that the publisher can reach us, transient failures don't lose data, and
we never hammer a dead URL.

Why: the honest UA is the station-5 withdrawal-risk mitigation, not politeness
theatre.

Acceptance:
- `test_requests_carry_user_agent_with_contact`
- `test_transient_5xx_is_retried_with_backoff_then_succeeds`
- `test_429_is_retried`
- `test_retries_are_bounded_and_then_raise`
- `test_404_on_a_document_is_not_retried_and_is_recorded_as_failed`

## US-07 Fail loudly — alerts the operator can act on

As the operator,
I want alerts on: landing vanished (P0), zero new-or-changed files when
churn was expected (P1), a payload suspiciously small (P1), and content
byte-identical for longer than the declared cadence (P1 staleness),
so that silence never masquerades as success.

Why: a weekly source returning the same hash for six weeks is failing while
every naive check passes. Compare against the *declared* cadence from
station 3 of the screen.

Acceptance:
- `test_alert_zero_new_files_when_cadence_expected_change`
- `test_no_zero_new_alert_when_within_cadence_window`
- `test_alert_payload_too_small`
- `test_alert_stale_when_unchanged_longer_than_cadence_times_tolerance`
- `test_alerts_carry_severity_code_and_human_message`

## US-08 Heartbeat — positive proof of life

As the operator,
I want every run to ping a watchdog URL on completion — a success ping on
success, a failure ping on failure — so that a *missing* ping is
distinguishable from a quiet success.

Why: a collector that dies quietly produces no alerts at all, which looks
exactly like a collector that is working. The watchdog raising on a missing
ping is the dead-man's-switch; we just have to ping.

The fail ping carries the alert text as its body, so the watchdog's own
email/push is the entire alert path. One external service, two jobs.

Acceptance:
- `test_heartbeat_pings_success_url_after_successful_run`
- `test_heartbeat_pings_fail_url_when_run_raises`
- `test_heartbeat_pings_fail_with_alert_text_on_p1`
- `test_heartbeat_success_when_only_p2_alerts`
- `test_heartbeat_crash_ping_carries_the_exception`
- `test_heartbeat_failure_itself_does_not_mask_the_run_result`

## US-09 Sources are data, not code

As the operator,
I want each source declared in a YAML file (landing URL, declared cadence,
polarity, licence evidence, minimum payload bytes, contact),
so that adding a source is a file plus an adapter module, not a deploy.

Acceptance:
- `test_source_config_loads_required_fields`
- `test_source_config_rejects_missing_polarity` (polarity is never implicit)
- `test_source_config_parses_declared_cadence_to_timedelta`

---

## Out of scope for Epic 1 (tracked for Epic 2: Extraction)

- Replayable parsers over stored bytes (silver layer)
- Entity crosswalk, polarity normalisation, unit/timezone traps (gold layer)
- Bitemporal fact table with `observed_at` immutable
- Per-source expectation tests and parse-failure-rate alerts
- Ollama structured-output extraction via the host service
