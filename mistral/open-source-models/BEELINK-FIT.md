# Mistral Models — Beelink GTR9 Pro Fit Analysis

## Hardware Reminder
- **GPU:** Radeon 890M (40 RDNA 3.5 CUs, accesses full 128GB unified memory)
- **RAM:** 128GB LPDDR5X (shared CPU/GPU)
- **Critical flag:** `export HSA_OVERRIDE_GFX_VERSION=11.0.0`
- **Inference stack:** Ollama + ROCm (or Vulkan fallback)

## Benchmarks to Run

After Tailscale is set up and Ollama is running:

```bash
# For each model, record:
# 1. Pull time
# 2. VRAM usage (rocm-smi)
# 3. Tokens/second (prompt eval + generation)
# 4. Quality on a standard task

# Test script (run for each model):
MODEL="mistral:7b"
echo "=== Benchmarking $MODEL ==="
ollama pull $MODEL

# Warm up
ollama run $MODEL "Hello, respond with one word." --verbose

# Benchmark: German text generation (Data Factory relevant)
time ollama run $MODEL "Generate a realistic German business invoice description for a Handwerksbetrieb in Bavaria. Include company name (GmbH), service description, and amount. Output in German." --verbose

# Benchmark: Code generation
time ollama run $MODEL "Write a Python function that validates a German PLZ (postal code) and returns the associated Bundesland." --verbose

# Benchmark: EHCP-style analysis (dissertation relevant)
time ollama run $MODEL "Review this EHCP provision: 'The child will receive some speech therapy sessions.' Identify compliance issues with the SEND Code of Practice requirement for specific, measurable provisions." --verbose

# Check VRAM
rocm-smi
```

## Fit Assessment Table

| Model | Size (Q4) | Fits? | Concurrent With | Primary Use Case | Priority |
|-------|-----------|-------|-----------------|------------------|----------|
| mistral:7b | ~4.5GB | Yes | Anything | Data Factory volume text | 1 |
| devstral-small | ~14GB | Yes | 70B models | Code review, test gen | 2 |
| mistral:14b | ~8GB | Yes | 70B models | Balanced general | 3 |
| mistral-small (119B MoE) | ~70GB | Yes (solo) | Maybe 7B | Flagship local | 4 |
| mistral:8b | ~5GB | Yes | Anything | Fast general tasks | 5 |
| mistral:3b | ~2GB | Yes | Anything | Edge/batch tasks | 6 |

## GRUND Dissertation Relevance

The 2x2 factorial design needs:
- **Cloud models:** Claude API, Mistral API
- **Local models:** Ollama on Beelink

Mistral models that should be tested as GRUND participants:
1. **Mistral Small 4** — strong enough to be a credible "local" option in the experiment
2. **Mistral 14B** — mid-range comparison point
3. **Mistral 7B** — lightweight comparison point

Compare against llama3.1:70b (already planned) to measure model family effects.

## Results Log

| Model | Date | Pull Time | VRAM | Prompt Tok/s | Gen Tok/s | Notes |
|-------|------|-----------|------|-------------|-----------|-------|
| — | — | — | — | — | — | (fill after benchmarking) |
