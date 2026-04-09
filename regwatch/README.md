# RegWatch

Self-hosted, LLM-triaged web change detection system. Monitors regulatory and policy URLs, classifies detected changes by urgency and domain impact using a local LLM (Ollama), and routes structured notifications to the right product.

Runs entirely on the Beelink GTR9 Pro. Zero cloud cost.

## Architecture

```
changedetection.io (polls URLs) → webhook → regwatch.py (Flask :5050)
  → Ollama triage (classifies diff) → notify (email / GitHub Issue / log)
  → product query API (GET /api/changes/{product})
```

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Ollama running locally with a model loaded (e.g., `ollama pull llama3.1:8b`)

### 1. Start changedetection.io

```bash
cd ~/regwatch
docker compose up -d
```

Web UI available at http://localhost:5000

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

```bash
export RESEND_API_KEY="re_..."          # For email notifications
export GITHUB_TOKEN="ghp_..."           # For GitHub Issue creation
export RESEND_FROM="regwatch@updates.mlupskill.com"
```

### 4. Run the orchestrator

```bash
python -m regwatch.app
```

Flask API available at http://localhost:5050

### 5. Configure webhook in changedetection.io

In the Web UI → Settings → Notifications:
- Webhook URL: `http://localhost:5050/webhook`

## Configuration

All configuration is YAML-driven (Rule 1: no code changes to add URLs or products).

| File | Purpose |
|------|---------|
| `domains.yaml` | Product registry — notification preferences + urgency routing |
| `watches/*.yaml` | Per-product URL watch lists with context metadata |
| `prompts/*_triage.yaml` | Per-product LLM triage prompt templates |

### Adding a new product

1. Add entry to `domains.yaml`
2. Create `watches/{product}.yaml`
3. Optionally create `prompts/{product}_triage.yaml`

No code changes needed.

## CLI

```bash
python -m regwatch.cli status                        # Show config health
python -m regwatch.cli test-triage <url> <diff_file>  # Test triage
python -m regwatch.cli digest --days=7                # Send weekly digest
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/changes/{product}?since=&urgency=` | Query change log |
| GET | `/api/status` | System health check |
| POST | `/api/triage/test` | Manual triage test |
| GET | `/health` | Simple health check |

## Design Rules

1. **Config-Driven** — YAML only, no code changes for new URLs/products
2. **Detection, Not Correction** — never modifies product content
3. **Product Isolation** — separate watches, logs, and API scope per product
4. **Idempotent Triage** — deduplicates by hash(url + diff + hour)
5. **Ollama Sharing** — queues behind Data Forge; regulatory changes aren't urgent
6. **No Silent Failures** — errors always produce a notification

## Resource Budget

~550MB RAM idle, negligible CPU, ~1GB disk/year. Invisible on a 128GB machine.
