# 2026-09-05 — option register added; chassis merged to main

- `longseries/registry/` created: schema (`README.md`) and three entries —
  `schaltfeld.yaml` (OPTION, review 2026-11-30, eleven kill criteria),
  `spacex-rideshare-manifest.yaml` and `starlink-availability-status.yaml`
  (OPTION, not yet collected, no-code build path). `tests/test_registry.py`
  checks required fields, kill criteria and review dates on options, and that
  built collectors name real `source_id`s. `pytest`: **105/105**.
- `docs/SOURCES.md`: addendum with the § 17c bill facts, Art. 50(4a), the
  withdrawal-in-reverse watch list and BK6-25-287.
- `claude/longseries-chassis` fast-forwarded onto `main` at the owner's
  request (the Beelink installs from `main`).
- Evidence and tags: `workflow-tools/patterns`, dossiers of 2026-09-04 and
  2026-09-05, and `skills/vanishing-data-prospector` v2.
