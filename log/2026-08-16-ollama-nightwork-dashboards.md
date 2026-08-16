# 2026-08-16 — Ollama defaults, `ollama launch`, Nightwork dashboards

**Session type:** summarize-and-connect (remote, multi-repo branch
`claude/ollama-beelink-dashboard-n6elb6`).

**Deliverable:** `docs/OLLAMA-NIGHTWORK-DASHBOARDS.md` — full strategy doc.
Three web-research subagents (JP real estate, JP international schools outside
Tokyo, local-LLM AI research) + local pattern-connection pass.

**Key connections made:**

1. **RegWatch is the Nightwork skeleton.** The dashboards Ryan wants (school
   intelligence, Tohoku land/akiya, arXiv mining) are RegWatch products (YAML
   additions) plus a nightly big-model deep-read + static-dashboard layer.
2. **The school brainstorm is already concrete** —
   `../patterns/education/tokyu-international-school.md` (Eastern Hill,
   Hachinohe). Research scan validates its two core bets (Harrow Appi works;
   OCSI shows military-adjacency scale) and adds a strategic upgrade: pursue
   municipal 誘致 land instead of market-price purchase. Companion signal
   watch-list filed in the patterns repo alongside the project doc.
3. **Ollama defaults audit** found real gaps: silent 4k-context truncation
   (upskill-news `OllamaAdapter` sets no `num_ctx` — backlog item), 5-min
   keep_alive vs. multi-minute 122B loads, unused KV-cache quantization,
   unused JSON-schema outputs, localhost-only binding blocking Tailscale
   serving.
4. **`ollama launch`** (v0.15+) runs Claude Code/Codex/OpenCode/Droid/Pi
   harnesses against local models via Ollama's Anthropic-compatible API —
   free overnight agentic labor on the Beelink for narrow verifiable chores.
5. **qwen3.8:27b** (released this week: 27.3B, Q4_K_M 18GB, vision, thinking
   default-on) explains the MacBook Air 15-min-per-prompt report: 18GB weights
   on a 24GB machine swaps, thinking mode multiplies. Fix: serve from the
   Beelink over Tailscale (`OLLAMA_HOST`).
6. **Sleep-time Compute (arXiv 2504.13171)** is the citable name for the whole
   overnight-precompute strategy; FindTheFlaws (2503.22989) + process-data
   synthesis (2605.02395) closely parallel the Data Factory flaw-injection
   methodology — dissertation positioning material.

**Open-question movement (CLAUDE.md):** NPU status answered (not in mainline
Ollama/llama.cpp; AMD Lemonade is the credible path); tok/s benchmark question
elevated — published Strix Halo numbers conflict up to 6×, making a
first-party benchmark both necessary and a citable artifact.

**Next actions:** see §8 of the strategy doc (priority-ordered, budget-aware).
