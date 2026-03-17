# Mistral Open-Source Models — Catalog (March 2026)

## Models Available for Local Inference

All models below are Apache 2.0 licensed (free for commercial use).

### Mistral Small 4 (NEW — March 2026)
- **Parameters:** 119B (Mixture of Experts)
- **Type:** General-purpose, multimodal (text + image)
- **Performance:** Matches/surpasses GPT-OSS 120B, 40% lower latency than Mistral Small 3
- **VRAM estimate:** ~65-80GB at Q4_K_M (fits in Beelink's 128GB)
- **Ollama:** `ollama pull mistral-small:latest` (check for availability)
- **Best for:** General tasks where you want a strong local model
- **Our use:** Data Factory text generation, VilseckKI RAG-as-a-Service

### Mistral Large 3
- **Parameters:** 675B total / 41B active (Sparse MoE)
- **Type:** General-purpose frontier model
- **Performance:** #2 on LMArena for OSS non-reasoning models
- **VRAM estimate:** At Q4_K_M, likely ~40-50GB for active parameters (MoE may need more for full weight loading — needs testing)
- **Ollama:** Check availability; may need custom Modelfile
- **Best for:** Complex reasoning, multi-step tasks
- **Our use:** GRUND Judge LLM candidate, high-quality German text generation

### Devstral 2
- **Parameters:** Not publicly stated (likely 20-30B range based on Devstral Small 2)
- **Type:** Code-specialized
- **Powers:** Mistral Vibe 2.0
- **Best for:** Code generation, code review, debugging
- **Our use:** Automated code review via API, PR review agent

### Devstral Small 2
- **Parameters:** 24B
- **Type:** Code-specialized (compact)
- **Performance:** Beats Qwen 3 Coder Flash (30B) at coding tasks
- **VRAM estimate:** ~14GB at Q4_K_M
- **Ollama:** `ollama pull devstral-small:latest`
- **Best for:** Fast code generation, lightweight coding tasks
- **Our use:** Quick code generation on Beelink, test generation

### Mistral 3 Family (December 2025)
- **14B:** ~8GB at Q4_K_M — fast general-purpose
- **8B:** ~5GB at Q4_K_M — very fast, good for volume tasks
- **3B:** ~2GB at Q4_K_M — edge deployment, extremely fast
- **Best for:** Volume work, concurrent tasks, low-latency inference
- **Our use:** Data Factory text augmentation (volume jobs), embeddings

### Mistral 7B (Original)
- **Parameters:** 7B
- **Already in use:** Referenced in Data Factory pipeline for volume jobs
- **VRAM:** ~4.5GB at Q4_K_M
- **Our use:** Already planned for Data Factory volume text generation

## Beelink Memory Budget (128GB Total)

```
Available for models:  ~100-110GB (OS + overhead takes ~18-28GB)

Concurrent model loading scenarios:
┌─────────────────────────────────┬──────────┐
│ Scenario                        │ VRAM Used │
├─────────────────────────────────┼──────────┤
│ Mistral Small 4 (Q4) alone      │ ~70GB    │
│ Mistral Large 3 (Q4) alone      │ ~45GB*   │
│ Large 3 + Devstral Small 2      │ ~59GB    │
│ Large 3 + Mistral 7B            │ ~50GB    │
│ Mistral 14B + 8B + 7B           │ ~17GB    │
│ llama3.1:70b + Mistral 7B       │ ~45GB    │
└─────────────────────────────────┴──────────┘
* MoE weight loading behavior needs benchmarking
```

## Priority Models to Pull

1. `mistral:7b` — already planned, volume text gen
2. `devstral-small` — code review and test gen
3. `mistral:14b` (Mistral 3 14B) — balanced general-purpose
4. `mistral-small` (Small 4, 119B MoE) — flagship local model (once confirmed in Ollama)
