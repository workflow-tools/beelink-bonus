# 2026-09-11 — longseries: the 2026-09-09 bug hunt reviewed; one regression fixed

**Branch:** `claude/longseries-chassis` → `main` · **Suite:** 168 → **173**.

The 2026-09-09 hunt filed 32 findings and refuted only one — a verifier that
soft is a reason to read, not to count. This session read the eight commits
(`a16d280..af51f07`) line by line, re-ran everything, and fixed what it found
before letting the branch stand as `main`.

## What was run

- `pytest`: 168/168 before, **173/173** after (Python 3.11, httpx 0.28.1).
- Each of the five new regression tests was run against the *unfixed* source
  first (`git stash` of `src/`): all five fail there, all five pass after.
- `longseries validate` on the three shipped sources under the new `source_id`
  and `heartbeat_url` rules: all three pass.
- `docs/`: test counts corrected; catalogue row 27 and an extension of row 11
  added to `FAILURE-MODES.md`.

## Found and fixed

**1. Every compressed response raised `DecodingError` — a regression from
commit 747c4b8.** `_get` now streams so the size and wall-clock limits apply
while bytes arrive. `response.iter_bytes()` applies the content-encoding on
the way in, so the collected bytes are already plain — and the rewrite then
rebuilt an `httpx.Response` with the *original* headers, `content-encoding:
gzip` included, so httpx decoded the plain bytes a second time. httpx sends
`Accept-Encoding: gzip, deflate` by default and every TSO gzips its landing
page, so in production every poll would have ended as a failed run
(`P1 LANDING_UNREACHABLE`, `DecodingError: Error -3 while decompressing
data`) with nothing captured. The suite could not see it: a `MockTransport`
body is never compressed unless a test compresses one. No data was at risk —
the Beelink install has not happened yet — but the 09-09 `main` would have
failed on its first real poll. Fix: the rebuilt Response drops the three
wire-only headers (`content-encoding`, `content-length`, `transfer-encoding`);
the recorded `content-length` now matches the stored blob. Test:
`test_a_gzip_encoded_response_is_decoded_once_and_stored_plain`.

**2. A complete last index row missing only its newline glued the next row
onto it.** Reads coped (file iteration yields an unterminated last line);
`_append_index` did not — it wrote straight after it, producing one line
holding two JSON objects that no reader could parse, and `repair` would then
have trimmed *both* as one torn line, losing a valid capture record.
`_append_index` now terminates such a row before appending (the existing
rollback covers that byte too), and `repair_index` leaves a trailing line
that parses alone. Tests:
`test_a_complete_row_missing_only_its_newline_is_not_glued_to_the_next_append`,
`test_repair_leaves_a_complete_but_unterminated_last_row_alone`.

**3. `show` printed `"last_change_at": "None"`.** `(x or "never") and str(x)`
is the string `"None"` when x is None. Pre-dates the hunt. Test:
`test_show_says_never_when_nothing_has_changed_yet`.

**4. The HTML sniff counted `<!--` and `<head` as HTML signatures, and only
at byte 0.** A comment-first XML feed would have been a `P1
WRONG_CONTENT_TYPE` on every edition; a maintenance page opening with a
comment under the document's own content-type slipped past. Now
`<!doctype html` / `<html` anywhere in the first KB. Test:
`test_content_sniff_does_not_mistake_a_comment_first_xml_feed_for_html`.

## Read and deliberately left alone

For the operator-experience thread (`docs/DESIGN-OPTIONS-operator-experience.md`)
to weigh, not bugs:

- `DOCUMENT_WITHDRAWN` is P0 for *any* failure of a previously captured URL,
  a transport error after retries included. The landing path distinguishes
  vanished (404/410) from unreachable — "a routing problem is not a finding" —
  and the document path does not. The message carries the status, so the
  operator can tell; the severity may still be worth aligning.
- `_via_tables` (Amprion) raises on any row it cannot read under a recognised
  header, and `parse()` does not fall back to `_via_lines` when it raises, so
  one footnote-marked cell fails the whole edition rather than dropping a
  row. Fail-loud is the right default; whether real Amprion PDFs carry such
  rows can only be checked against real files once collection runs. The
  `if len(c) < 5` inside it is dead after the padding and is left as is.
- `cmd_schedule` pings `/fail` twice on a crash inside `run_with_heartbeat`
  (once there, once in the loop). Deliberate, documented, harmless.
- The hunt's other fixes read correctly and are covered by their 58 tests.
  Treat the hunt's *finding list* as claims and its *tests* as the record.

## Lesson

A fake transport that never compresses cannot exercise the one header every
real server sends. Any test double standing in for the wire must carry the
wire's encodings at least once — recorded in
`workflow-tools/patterns` → `skills/vanishing-data-prospector/references/collector-design.md`.

## Result

`claude/longseries-chassis` fast-forwarded onto `main` after the fixes. The
Beelink install (owner-side, still pending) starts from this `main`.
