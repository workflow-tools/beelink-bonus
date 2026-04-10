# RegWatch — BugBot Review Rules

RegWatch is a self-hosted, LLM-triaged web change detection system.
Python 3.11+ / Flask / YAML-driven configuration / Ollama for LLM triage.

## Architecture Context

- `regwatch/app.py` — Flask webhook receiver + API mount
- `regwatch/config.py` — YAML config loader (domains.yaml, watches/*.yaml, prompts/*.yaml)
- `regwatch/triage.py` — Ollama LLM triage calls + JSON response parsing
- `regwatch/notify.py` — Email (Resend) + GitHub Issue creation
- `regwatch/log.py` — JSONL append-only change logs + deduplication
- `regwatch/api.py` — Flask blueprint for product query API
- `regwatch/digest.py` — Weekly digest compiler
- `regwatch/cli.py` — CLI entry point for manual operations

## Critical Review Rules

### No Silent Failures (Rule 6 — blocking)
Flag as a **blocking bug** any code path where:
- A webhook is received but no log entry or notification is produced
- An `except` block catches an error without logging it or sending a fallback notification
- A notification channel failure is not followed by a fallback attempt

### Config-Driven Enforcement (Rule 1 — blocking)
Flag as a **blocking bug** any Python code that:
- Hardcodes a URL that should come from `watches/*.yaml`
- Hardcodes a product name, corridor code, or urgency level that should come from YAML config
- Requires a code change to add a new watched URL or product

### Detection, Not Correction (Rule 2 — blocking)
Flag as a **blocking bug** any code that:
- Modifies external product files, pathway JSONs, or any content outside the RegWatch directory
- Sends automated content patches to any downstream system

### Type Safety (warning)
Flag any public function that is missing type hints on parameters or return value.

### Docstring Coverage (warning)
Flag any public function or module that is missing a docstring.

### Error Specificity (warning)
Flag bare `except:` or overly broad `except Exception:` unless it is in a
top-level handler (webhook endpoint or CLI entry point) with explicit logging.

### YAML Schema Consistency (warning)
If a PR adds or renames a key in any YAML config file, check that:
- The corresponding `config.py` loader handles it
- The BUGBOT.md and README.md are updated in the same PR

### Test Coverage (suggestion)
If a PR modifies `triage.py`, `notify.py`, or `log.py`, suggest adding or
updating tests in `tests/` for the changed behaviour.

## Dependencies

Runtime deps are intentionally minimal: flask, requests, pyyaml, resend.
Flag any new dependency addition for review — it needs justification.
