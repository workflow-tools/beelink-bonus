# Mistral Vibe 2.0 — Setup Guide

## What It Is

Mistral Vibe is a terminal-native coding agent powered by Devstral 2. It lives in your terminal (or VS Code's integrated terminal) and provides conversational code assistance with file read/write, grep, shell execution, and git awareness. Think of it as a lightweight Claude Code competitor that runs in your existing terminal workflow.

## Requirements

- Python 3.12+ (check: `python3 --version`)
- Le Chat Pro subscription (you have this)
- Mistral API key (generate at console.mistral.ai)

## Installation

```bash
# Option A: uv (preferred — faster)
uv tool install mistral-vibe

# Option B: pip
pip install mistral-vibe
```

## API Key Configuration

```bash
# Interactive setup (recommended for first time)
vibe --setup

# OR set environment variable
export MISTRAL_API_KEY="your-key-here"

# OR create ~/.vibe/.env manually
echo "MISTRAL_API_KEY=your-key-here" > ~/.vibe/.env
```

## VS Code Integration

Vibe runs inside VS Code's integrated terminal — no special extension needed:

1. Open VS Code integrated terminal (Ctrl+`)
2. Navigate to project directory
3. Run `vibe`
4. Vibe auto-scans project structure and git status

There is also a Mistral Code VS Code extension (search "Mistral" in VS Code extensions marketplace) for inline completions, but that is separate from Vibe.

## Vibe 2.0 Key Features

- **Custom subagents** — Build specialized agents for deploy scripts, PR reviews, test generation
- **Multi-choice clarifications** — Asks before acting when intent is ambiguous
- **Slash-command skills** — `/deploy`, `/lint`, `/docs` etc. for preconfigured workflows
- **Unified agent modes** — Combine tools, permissions, and behaviors into switchable modes

## Configuration Files

Vibe reads project context from:
- `.vibe/` directory in project root (optional)
- `AGENTS.md` or similar handoff docs
- Git status and file tree automatically

## Cost

Included with Le Chat Pro ($14.99/mo). API usage for Vibe through Le Chat Pro has daily limits — check current limits at mistral.ai/pricing.

## TODO

- [ ] Install Vibe on MacBook Air
- [ ] Generate API key at console.mistral.ai
- [ ] Run `vibe --setup`
- [ ] Test in one project directory (rebeka-app recommended — largest codebase)
- [ ] Evaluate whether to also install on Beelink for headless code tasks
