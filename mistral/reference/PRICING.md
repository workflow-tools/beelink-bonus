# Mistral Pricing Reference (March 2026)

## Le Chat Plans

| Plan | Price | Key Limits |
|------|-------|-----------|
| Free | $0 | Basic access, limited messages |
| Pro | $14.99/mo | Enhanced limits, Vibe included, Deep Research, 15GB docs, 1000 projects |
| Team | $25/user/mo | Centralized billing, admin controls |
| Enterprise | Custom | SSO, audit logs, dedicated support |

**You have:** Pro ($14.99/mo)

## API Pricing (console.mistral.ai)

| Plan | Price | Notes |
|------|-------|-------|
| Experiment | Free | Limited calls, good for prototyping in Mistral Studio |
| Pay-as-you-go | Per-token | Standard API pricing |

### Per-Token Rates (verify at mistral.ai/pricing — may have changed)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Mistral Large | ~$2-4 | ~$6-12 |
| Mistral Small | ~$0.1-0.2 | ~$0.3-0.6 |
| Devstral | ~$0.5-1 | ~$1-3 |
| Mistral Nemo | ~$0.15 | ~$0.15 |

*Note: Verify current prices. These are estimates based on last known pricing.*

## Vibe Usage (via Pro)

- Included with Le Chat Pro subscription
- Subject to daily usage limits (check current limits in app)
- Uses Devstral 2 model

## Local Models (Beelink)

- **Cost:** $0 per inference (electricity only: ~€14/month for 24/7 operation)
- **All Apache 2.0:** Free for commercial use
- **No rate limits:** Limited only by hardware speed

## Budget Recommendation

| Item | Monthly Cost | Purpose |
|------|-------------|---------|
| Le Chat Pro | $14.99 | Deep Research, Vibe, Projects |
| API (experiment) | $0 | Prototyping Agents API |
| API (PAYG, if needed) | €10-20 max | Demand intel agent, occasional API calls |
| Beelink electricity | ~€14 | Local model inference |
| **Total** | **~€40-50/mo** | |

This is reasonable given the potential revenue from Data Factory (target: €200-600/mo within 3-6 months) and the dissertation compute value.
