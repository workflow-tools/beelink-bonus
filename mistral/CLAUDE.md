# Mistral Investigation — Claude Context Document

> **Purpose:** Context for any Claude Cowork session working in this directory.
> Read this first in every new session.
> Last updated: March 2026.

---

## What This Directory Is

This is an investigation workspace for evaluating and integrating Mistral AI's ecosystem into Ryan Hill's existing workflow. The primary workflow is managed through Claude Cowork attached to the local dev folder. Mistral is being evaluated as a complement, not a replacement.

## Owner Context

- **Company:** ML Upskill Agents UG (haftungsbeschrankt), Vilseck, Bayern
- **Subscription:** Le Chat Pro ($14.99/mo) — active
- **Hardware:** Beelink GTR9 Pro (AMD AI Max+ 395, 128GB LPDDR5X) for local model inference
- **Dev environment:** VS Code on MacBook Air; Beelink accessed via Tailscale
- **Background:** Data science / analytics (Python, R); vibe-coded micro-SaaS products; PhD student (CS, FAU)

## Active Projects (Priority Order)

1. **Dissertation + EHCP** — GRUND framework: synthetic document corpora with planted compliance flaws, multi-agent debate + Judge LLM, UK SEND system. The product IS the dissertation.
2. **Data Factory** — Synthetic dataset generation pipeline (vilseckki-datafactory-app). Le Chat already has a defined role as demand intelligence agent. See `../vilseckki-datafactory-app/LECHAT-PROJECT-DESCRIPTION.md`.
3. **Rebeka** — Clinical placement management platform incorporating ProPrecept. Multi-market, offline-first PWA.
4. **FarAfield** — Nurse migration sequencing app. Lower priority.

## Key Principle: Division of Labor

- **Claude Cowork** = primary development environment, architecture decisions, complex multi-file edits, long-context reasoning
- **Mistral Vibe** = coding cross-check, quick scaffolding, terminal-native tasks, code review second opinion
- **Le Chat Pro** = demand research, deep research reports, project-scoped context for ongoing monitoring
- **Mistral Agents API** = automation prototypes, MCP-based tool orchestration, pipeline triggers
- **Mistral Open-Source Models (Beelink)** = local inference for GRUND experiments, Data Factory text generation, privacy-first client work

## Related Files

| File | Location |
|------|----------|
| Beelink master context | `../CLAUDE.md` |
| Data Factory Le Chat brief | `../../vilseckki-datafactory-app/LECHAT-PROJECT-DESCRIPTION.md` |
| Pattern library index | `../../patterns/INDEX.md` |
| Patterns handoff | `../../patterns/HANDOFF.md` |
| Machine network | `../../patterns/reference/machines.md` |

## Session Log

Notes from investigation sessions go in the parent `../log/` directory with prefix `mistral-`.
