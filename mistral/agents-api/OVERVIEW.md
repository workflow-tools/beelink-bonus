# Mistral Agents API — Overview

## What It Is

The Mistral Agents API is a framework for building autonomous AI agents that can plan, use tools, execute code, and hand off tasks to other agents. It's Mistral's answer to OpenAI's Assistants API, but with MCP (Model Context Protocol) support baked in.

## Key Capabilities

### Built-in Tools (Connectors)
- **Code execution** — Sandboxed Python environment for calculations, data analysis, plotting
- **Web search** — Agents can search the web autonomously
- **Image generation** — FLUX1.1 Pro Ultra for visual content
- **Document library** — Access documents stored in Mistral Cloud

### MCP Integration
Agents can connect to any MCP-compatible server, which means:
- Database access (Supabase, PostgreSQL)
- GitHub operations (PRs, issues, code search)
- File system access
- Custom API integrations
- Any tool you'd use with Claude Code's MCP support

### Agent Handoffs
Multiple agents can collaborate on a single request:
- Agent A handles research
- Agent B handles code generation
- Agent C handles validation
- Orchestrator routes between them

### Conversations and Memory
Agents maintain conversation state across multiple turns. Useful for:
- Ongoing monitoring tasks
- Multi-step workflows that span sessions
- Stateful research assistants

## API Access

- **Free tier (Experiment plan):** Limited API calls, good for prototyping via Mistral Studio
- **Le Chat Pro:** Includes some API access (check current limits)
- **Pay-as-you-go:** Standard API pricing at console.mistral.ai

## SDK

```bash
pip install mistralai
```

```python
from mistralai import Mistral

client = Mistral(api_key="your-key")

# Create an agent
agent = client.beta.agents.create(
    model="mistral-medium-latest",
    name="data-factory-monitor",
    instructions="Monitor Datarade for synthetic data demand signals...",
    tools=[{"type": "web_search"}, {"type": "code_interpreter"}]
)
```

## Relevance to Our Stack

The Agents API is interesting because:
1. It's the only way to get autonomous, tool-using agents from Mistral (Le Chat is interactive only)
2. MCP support means it could plug into the same tool ecosystem as Claude Code
3. Code execution is sandboxed — safe for automation
4. Handoffs could enable a Mistral-based version of the GRUND multi-agent debate pattern

## Limitations to Investigate

- [ ] What are the actual rate limits on Le Chat Pro vs pay-as-you-go?
- [ ] How does agent memory persist? (Conversation-scoped or persistent?)
- [ ] Can agents be triggered on a schedule (cron-like)?
- [ ] How does the sandboxed Python compare to running code on the Beelink directly?
- [ ] What's the latency for multi-agent handoffs?
