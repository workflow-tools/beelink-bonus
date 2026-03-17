# Le Chat Pro — Data Factory Demand Intelligence

## Current State

The Data Factory's Le Chat role is already defined in `vilseckki-datafactory-app/LECHAT-PROJECT-DESCRIPTION.md`. This file extends that with a concrete workflow.

## Weekly Demand Intelligence Workflow

### Step 1: Open Le Chat Data Factory Project
Go to the VilseckKI Data Factory project in Le Chat.

### Step 2: Run Deep Research Queries
Ask Le Chat Deep Research to investigate:

**Query 1 — Marketplace Gaps:**
> "Search Datarade.ai and HuggingFace Datasets for synthetic data categories that are frequently searched but have few or no listings. Focus on German-language data, EU regulatory compliance data, healthcare dialogue data, and agricultural time-series. Report the top 10 gaps with estimated demand."

**Query 2 — Policy Signals:**
> "Search for recent announcements from the Bavarian AI Act Accelerator, Fraunhofer institutes, and appliedAI Institute about datasets they need or projects they're funding. Also check METI Japan's latest digitalization reports for agricultural data initiatives."

**Query 3 — Competitor Movement:**
> "What new synthetic data products have been listed on Datarade in the past 30 days? Focus on any that overlap with German B2B, healthcare, or agricultural domains."

### Step 3: Extract Actionable Leads
From the Deep Research results, identify:
- Dataset concepts worth generating
- Specific schemas/columns buyers are asking for
- Price points competitors are charging
- Gaps where no competition exists

### Step 4: Draft YAML Config Recommendations
Ask Le Chat to produce a structured recommendation:
> "Based on your research, propose 2-3 new dataset YAML configs for the VilseckKI Data Factory pipeline. For each, specify: dataset name, target buyer, table names, column types and distributions, LLM prompts for text columns, record count, and suggested Datarade price. Use the schema format from config_schema.py."

### Step 5: Hand Off to Claude Cowork
Take the Le Chat recommendations and bring them to Claude Cowork for:
- YAML config implementation
- Framework code extensions if needed
- Validation rule design

## Automation Path

Once the Agents API prototype (see `../agents-api/examples/demand-intel-agent.py`) is tested, this manual workflow should be automated to run weekly. The agent would:
1. Execute the research queries
2. Produce structured JSON output
3. Save to `vilseckki-datafactory-app/demand-signals/`
4. Claude Cowork processes the signals into YAML configs

## Tracking

Keep a running log of demand signals and their outcomes:

| Date | Signal | Source | Dataset Created? | Revenue? |
|------|--------|--------|-----------------|----------|
| — | — | — | — | — |
