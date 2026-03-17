# Mistral Vibe — Use Cases Alongside Claude Cowork

## Where Vibe Adds Value (Not Duplicating Claude)

### 1. Code Review Second Opinion
**Scenario:** Claude Cowork generates a complex component or refactors a module.
**Vibe role:** Open a terminal in the same project, ask Vibe to review the changes.
**Why this works:** Two different models catch different classes of bugs. Especially valuable for:
- Type safety issues in TypeScript
- Edge cases in async/offline-first code (Rebeka, FarAfield)
- Prompt contract validation (WritingPAD family)

### 2. Quick Terminal Tasks While Claude Cowork Is Running
**Scenario:** Claude Cowork is doing a long multi-file edit. You need a quick git operation, a grep across the codebase, or a one-off script.
**Vibe role:** Handle the quick task in a parallel terminal without interrupting Claude's context.
**Why this works:** Claude Cowork's context window is precious; don't burn it on `git log --oneline | head -20`.

### 3. Test Generation
**Scenario:** A module is written but untested.
**Vibe role:** Point Vibe at the module, ask it to generate Vitest/Jest tests.
**Why this works:** Test generation is relatively self-contained and doesn't need the full project context that Claude Cowork maintains.

### 4. Documentation Drafts
**Scenario:** You've built a feature but haven't documented it.
**Vibe role:** Generate JSDoc comments, README sections, or API documentation stubs.
**Why this works:** Documentation is formulaic enough that a coding agent handles it well.

### 5. Scaffolding New Market Configs
**Scenario:** Expanding Rebeka to a new country (e.g., Nepal NNC).
**Vibe role:** Given an existing market config (e.g., nigeria-nmcn), generate the skeleton for a new one.
**Why this works:** Pattern-following tasks are Vibe's sweet spot. Claude Cowork handles the substantive regulatory research.

### 6. Data Pipeline Scripts (Python)
**Scenario:** Writing one-off data processing scripts for Data Factory or dissertation experiments.
**Vibe role:** Generate pandas/polars scripts, R integration wrappers, validation checks.
**Why this works:** Your data science background means you can evaluate Python output quality quickly. Vibe's Devstral 2 model is strong on Python.

### 7. Cross-Checking Prompt Contracts
**Scenario:** Claude writes a prompt contract JSON for a new market.
**Vibe role:** Review the prompt contract for logical consistency, missing fields, or quality gate gaps.
**Why this works:** Adversarial review by a different model family is more likely to catch blind spots.

## Where Vibe Does NOT Add Value (Stay with Claude Cowork)

- **Multi-file architectural refactors** — Claude Cowork's long context is essential
- **Complex business logic decisions** — Cowork's careful reasoning is superior
- **Pattern library management** — Requires full project context across repos
- **Dissertation writing** — Long-form academic writing needs Claude's depth
- **Regulatory research** — Le Chat Deep Research or Claude, not Vibe
