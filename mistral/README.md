# Mistral Investigation — Beelink Bonus

Exploring how Mistral's ecosystem can complement the Claude Cowork-powered workflow for ML Upskill Agents UG projects.

## Why Mistral?

1. **Coding strength** — Devstral 2 and Mistral Vibe 2.0 are competitive coding agents; a second opinion on code is valuable
2. **Open-source models** — Mistral Small 4 (119B MoE), Mistral Large 3 (675B MoE), Devstral Small 2 (24B) all run locally on the Beelink GTR9 Pro's 128GB unified memory
3. **Le Chat Pro subscription** — Already paid for; should be extracting maximum value
4. **Cross-checking** — Using Mistral to validate Claude's outputs (and vice versa) catches errors neither catches alone
5. **Agents API** — MCP-compatible agent orchestration that could automate research and data pipeline tasks
6. **EU alignment** — Mistral is French/EU; for VilseckKI's "Nichts verlasst Bayern" positioning, EU-based AI tooling strengthens the narrative

## Directory Structure

```
mistral/
├── README.md                  ← This file
├── CLAUDE.md                  ← Context doc for Claude sessions in this directory
├── vibe-coding/               ← Mistral Vibe 2.0 CLI coding agent investigation
│   ├── SETUP.md               ← Installation, API key config, VS Code integration
│   ├── USE-CASES.md           ← Where Vibe adds value alongside Claude Cowork
│   └── EXPERIMENTS.md         ← Log of actual Vibe usage experiments
├── agents-api/                ← Mistral Agents API investigation
│   ├── OVERVIEW.md            ← API capabilities, MCP support, handoffs
│   ├── AUTOMATION-IDEAS.md    ← Specific automation opportunities for our projects
│   └── examples/              ← Code examples and prototypes
├── le-chat-pro/               ← Le Chat Pro feature investigation
│   ├── FEATURES.md            ← Deep Research, Think mode, Projects, Vocal mode
│   ├── PROJECTS-SETUP.md      ← How to set up Le Chat Projects for each repo
│   └── DEMAND-INTEL.md        ← Data Factory demand intelligence agent (extends existing Le Chat role)
├── open-source-models/        ← Models runnable on Beelink GTR9 Pro
│   ├── MODEL-CATALOG.md       ← Current models, sizes, quantizations, expected performance
│   ├── BEELINK-FIT.md         ← Which models fit in 128GB, benchmarks to run
│   └── OLLAMA-CONFIGS.md      ← Modelfile configs for Ollama on the Beelink
├── workflows/                 ← Cross-cutting workflow automation designs
│   ├── CLAUDE-MISTRAL-DIVISION.md  ← Division of labor between Claude and Mistral
│   └── PROJECT-WORKFLOWS.md   ← Per-project Mistral integration plans
└── reference/                 ← Quick-reference material
    └── PRICING.md             ← Le Chat Pro limits, API pricing, free tier details
```

## Active Projects and Mistral Relevance

| Project | Primary Tool | Mistral Role |
|---------|-------------|--------------|
| Dissertation + EHCP | Claude Cowork | Local model inference (GRUND), cross-check analysis |
| Data Factory | Claude + Le Chat | Le Chat demand intelligence, Mistral models for generation |
| Rebeka | Claude Cowork | Vibe for code review, Agents API for test generation |
| FarAfield | Claude Cowork | Lower priority; Vibe for scaffolding when needed |

## Status

- [x] Directory structure created
- [ ] Vibe 2.0 installed and tested
- [ ] Le Chat Projects configured for each major repo
- [ ] Agents API prototyped for one workflow
- [ ] Beelink benchmarks for Mistral open-source models
- [ ] Division of labor doc finalized
