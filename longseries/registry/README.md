# registry/ — the option register

One YAML per series the owner has *decided* about, whether or not a collector
exists for it yet. This is the `vanishing-data-prospector` skill's station-6
register, kept next to the chassis it governs, because an unregistered
collector is a leak and an unregistered option is a wish.

The screen itself (six stations, evidence, tags) lives in a dated dossier in
the `patterns` repo; the entry here carries the *decisions* and the *dates*,
and links to the dossier for the evidence. Never copy source documents here.

## Fields

| Field | Meaning |
|---|---|
| `id`, `title` | Stable identifier and a human name |
| `status` | `option` (collect now, product later) · `product` (buyers now, being sold) · `parked` (blocked on an owner check) · `killed` |
| `decision` | Which decision the verdict is about: `collect` or `productize` — the skill treats them as different bets |
| `verdict`, `verdict_date`, `screened_with` | The dossier's verdict, when, and the skill version (repo@commit) |
| `dossiers` | Links to the dated dossier(s) holding the evidence |
| `collector.built` | Whether a chassis source config exists; `collector.sources` must then name real `source_id`s under `sources/` (a test enforces it) |
| `collector.not_built` | Publishers in scope with no collector yet, and why |
| `stations` | One line per station with result and tag; the dossier has the detail |
| `future_question` | The question the future buyer will ask, in their words — the reason the past is worth keeping |
| `buyers_now`, `buyers_later` | Named organisations / evidenced buyer types, with tags |
| `premium` | What the option costs: setup hours and euros per month, as numbers |
| `wedge` | The day-one artefact offered to people near the future buyer |
| `kill_criteria` | Pre-committed; any one fires a re-screen, not a debate |
| `review_date` | When stations 1, 2b and 5 are re-run (an hour's work). Options are reviewed, not remembered |
| `route`, `ceiling` | few-large · many-small · portfolio · validation-only, with the ceiling arithmetic and its tag |
| `owner_checks` | What only a browser or the owner can settle |

## Rules

- Every `option` has non-empty `kill_criteria` and a `review_date` after `verdict_date`.
- `collector.sources` entries must match a `source_id` in `sources/*.yaml`; `pytest` checks it.
- A status change is a new dated line under `history`, never an edit of the old one.
- The programme-level rule from the skill applies across all entries: one paying
  customer on some series within the owner's horizon, or the whole thing is a
  well-run hobby — legitimate, as long as it is named.
