# Division of Labor — Claude Cowork vs Mistral Ecosystem

## Principle

Claude Cowork is the primary development environment. Mistral augments it in specific roles where either (a) a second opinion adds value, (b) Mistral has a competitive feature, or (c) automation reduces manual work.

## Role Matrix

| Task | Primary | Secondary | Notes |
|------|---------|-----------|-------|
| **Architecture decisions** | Claude Cowork | — | Long context + careful reasoning = Claude |
| **Multi-file refactors** | Claude Cowork | — | Context window management is critical |
| **Pattern library management** | Claude Cowork | — | Cross-repo awareness needed |
| **Dissertation writing** | Claude Cowork | — | Long-form academic depth |
| **Regulatory research** | Claude Cowork | Le Chat Deep Research | Cross-check findings between both |
| **Code generation (new features)** | Claude Cowork | Vibe (review) | Claude writes, Vibe reviews |
| **Code review** | Claude Cowork | Vibe | Two-model review catches more bugs |
| **Test generation** | Vibe | Claude Cowork | Tests are self-contained; good Vibe task |
| **Quick terminal tasks** | Vibe | — | Don't burn Claude's context on grep/git |
| **Market research** | Le Chat Deep Research | Claude Cowork | Le Chat for initial research, Claude for synthesis |
| **Demand intelligence** | Le Chat / Agents API | Claude (YAML impl) | Le Chat researches, Claude implements |
| **Data Factory text gen** | Beelink (Ollama) | — | Local models, overnight cron |
| **GRUND experiments** | Claude API + Beelink | Mistral API + Beelink | Both model families in factorial design |
| **Scaffolding new markets** | Vibe | Claude Cowork | Vibe for skeleton, Claude for substance |
| **Documentation** | Vibe | Claude Cowork | Formulaic; good Vibe task |
| **German business research** | Le Chat | — | EU-based model may have better German context |
| **Beelink infrastructure** | Le Chat / Agents API | — | Health monitoring, model management |

## Workflow Patterns

### Pattern 1: Write → Cross-Check
1. Claude Cowork generates code/content
2. Copy relevant output to Vibe terminal
3. Ask Vibe: "Review this for [type safety / edge cases / compliance]"
4. Merge feedback in Claude Cowork

### Pattern 2: Research → Implement
1. Le Chat Deep Research produces findings
2. Bring structured findings to Claude Cowork
3. Claude implements (YAML configs, code, docs)

### Pattern 3: Parallel Development
1. Claude Cowork handles the main task
2. Vibe handles an independent subtask in parallel
3. Both outputs merged manually

### Pattern 4: Automated Pipeline
1. Agents API agent runs on schedule (or trigger)
2. Outputs structured data (JSON, YAML draft)
3. Claude Cowork processes output into production artifacts

## Cost Awareness

| Tool | Cost | Limit |
|------|------|-------|
| Claude Cowork | Included in Claude subscription | Session-based |
| Le Chat Pro | $14.99/mo | Daily message limits |
| Vibe (via Pro) | Included | Daily usage limits |
| Mistral API (PAYG) | Per-token | Budget: decide max €/month |
| Beelink (Ollama) | ~€14/mo electricity | Unlimited (hardware owned) |

## Anti-Patterns (Don't Do This)

- Don't use Vibe for tasks requiring full project context (that's Claude's strength)
- Don't use Le Chat for implementation (it can't edit your files)
- Don't duplicate the same task in both Claude and Mistral "just to compare" except during evaluation phase
- Don't use the Agents API for tasks that are faster to do manually (overhead isn't worth it for one-offs)
