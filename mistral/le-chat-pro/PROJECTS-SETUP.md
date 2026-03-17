# Le Chat Pro — Projects Setup Guide

## Strategy

Create one Le Chat Project per major initiative. Each project gets a tailored instruction set (paste from existing CLAUDE.md / LECHAT files) and relevant documents uploaded.

## Projects to Create

### 1. VilseckKI Data Factory (PRIORITY — already has instructions)
**Instructions:** Paste from `vilseckki-datafactory-app/LECHAT-PROJECT-DESCRIPTION.md`
**Documents to upload:**
- `configs/mittelstand-b2b.yaml` (example config)
- `generators/config_schema.py` (Pydantic schema)
- `SYNTHETIC-DATA-FACTORY-PLAN.md`
- `BEELINK-PASSIVE-REVENUE-STRATEGY.md`

**Le Chat role:** Demand intelligence agent (research, propose YAML configs)

### 2. Dissertation / GRUND / EHCP
**Instructions:** Write a brief covering:
- GRUND framework purpose (synthetic corpus + planted flaws + multi-agent debate + Judge LLM)
- UK SEND / EHCP context
- Current dissertation stage
- What you want Le Chat to help with (literature search, methodology cross-check)

**Documents to upload:**
- EHCP architecture docs from `ehcpaudit-app/`
- Any dissertation chapter drafts

**Le Chat role:** Literature monitor, methodology cross-checker

### 3. Rebeka Platform
**Instructions:** Brief covering:
- Multi-market clinical placement management
- Offline-first PWA architecture
- Current markets and expansion pipeline

**Documents to upload:**
- `rebeka-app/ARCHITECTURE.md`
- Key market configs

**Le Chat role:** Market research for new country expansions, competitor tracking

### 4. ML Upskill Agents UG (Business)
**Instructions:** Brief covering:
- German UG structure, Vilseck location
- Product portfolio overview
- VilseckKI brand and local market positioning
- Tax and compliance context

**Documents to upload:**
- German SaaS compliance stack pattern
- Business strategy docs from beelink-bonus/business-docs/

**Le Chat role:** German business/legal research, grant application research, tax optimization ideas

### 5. Beelink Infrastructure
**Instructions:** Brief covering:
- Hardware specs (AMD AI Max+ 395, 128GB)
- Ollama setup, ROCm configuration
- Current and planned services

**Documents to upload:**
- `beelink-bonus/CLAUDE.md`
- `beelink-bonus/SPECS.md`

**Le Chat role:** Hardware optimization research, model compatibility checks

## Setup Steps

For each project:
1. Go to Le Chat (chat.mistral.ai)
2. Click "Projects" in sidebar
3. Create new project with the name above
4. Paste instructions into the project description field
5. Upload listed documents
6. Pin the project for quick access

## Maintenance

Review and update project instructions monthly. When Claude Cowork updates a CLAUDE.md, propagate relevant changes to the corresponding Le Chat project.
