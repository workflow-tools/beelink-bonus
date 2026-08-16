# Ollama Defaults, `ollama launch`, and the Nightwork Dashboard Strategy

> **Date:** 2026-08-16 · **Session type:** summarize-and-connect
> **Thesis:** The Beelink's edge over every other solo dev is not speed — it is
> *unattended throughput*. 128GB of unified memory running big models 8+ hours a
> night at ~€0.50 of electricity is compute most solo developers simply do not
> have. The way to cash that in is **Nightwork dashboards**: overnight batch
> reading + structured extraction + a morning publish, on top of the RegWatch
> skeleton that already exists in this repo.

---

## 1. Ollama Default Options We Have NOT Been Using

Ollama ships with defaults tuned for "chat on a laptop," not "24/7 batch server
with 128GB." Every one of these is a lever we have so far left at factory
setting.

| Option | Default | Why it matters for us | Set on the Beelink to |
|---|---|---|---|
| **Context length** (`num_ctx` / `OLLAMA_CONTEXT_LENGTH`) | 4,096 tokens (older docs say 2,048; newest builds pick from detected VRAM). **Prompts are silently truncated** — no error, the model just never sees the overflow. | This is the #1 footgun. Any long document fed to a default-config model gets its head chopped off silently. Agent harnesses (Claude Code via `ollama launch`) need ≥64k. | `OLLAMA_CONTEXT_LENGTH=32768` server-wide; per-request `num_ctx` for big jobs. Verify what a loaded model actually got with `ollama ps`. |
| **`keep_alive`** | **5 minutes**, then the model unloads | A 70B/122B load takes minutes. A nightly batch that calls the model every ~6 minutes pays the load cost *every call*. | `OLLAMA_KEEP_ALIVE=-1` during the batch window (or `keep_alive: -1` per request); let it unload during the day. |
| **KV cache quantization** (`OLLAMA_KV_CACHE_TYPE`) | `f16` | Long contexts on big models eat tens of GB of KV cache. `q8_0` halves that with negligible loss — on a unified-memory box that's the difference between 32k and 64k context fitting. | `OLLAMA_KV_CACHE_TYPE=q8_0` |
| **Flash attention** (`OLLAMA_FLASH_ATTENTION`) | Auto-enabled where supported since Oct 2025 | Prerequisite for KV-cache quantization; worth verifying it actually engages on ROCm/Vulkan for the 890M. | Check `journalctl -u ollama` at model load; force-enable if it isn't auto. |
| **`OLLAMA_HOST`** | Binds `127.0.0.1` only | The Mac can't reach the Beelink over Tailscale until this changes. This single line makes the Beelink the family inference server. | `OLLAMA_HOST=0.0.0.0` (Tailscale ACLs are the firewall). |
| **`OLLAMA_NUM_PARALLEL`** | 1 (recent builds) | Parallel slots multiply KV cache memory. For nightly batch: keep 1 (memory-bandwidth-bound anyway, per Data Factory runs). For serving RegWatch triage + a chat session simultaneously: 2 is affordable on a small model. | Leave 1 for the 70B+ window; 2–4 for the 8B triage model. |
| **`OLLAMA_MAX_LOADED_MODELS`** | 3× GPU count (implementation-dependent) | With 128GB we can deliberately pin **two** models: a big generator (e.g. `qwen3.5:122b`) + a small critic/triage model (8B), which is exactly the generate→verify shape the Data Factory and upskill-news pipelines use. | Explicitly set to 2–3 and test both stay resident. |
| **Structured outputs** (`format: <JSON schema>`) | Off — free-text | Every Nightwork extraction job wants schema-validated JSON, not regex-parsing prose. Ollama has supported JSON-schema-constrained output since late 2024; we use it nowhere. | Pass a JSON schema in the `format` field for every extraction call. |
| **Thinking mode** (`think: true/false`) | **On by default** for thinking models (incl. qwen3.8) | Thinking models burn thousands of hidden reasoning tokens per call. Good for hard extraction; terrible default for bulk triage. | Explicitly set `think: false` on triage/bulk calls; leave on for the hard nightly deep-reads. |
| **`num_predict`** | Model-dependent (often unlimited-until-stop) | Runaway generations waste the night. Batch jobs should cap it. | Set per job. |
| **`ollama launch`** (v0.15+) | n/a — new subsystem | Turns the Beelink into an *agent host*, not just a completion API: `ollama launch claude` runs the Claude Code harness against a local model with zero env-var setup. See §2. | Use for overnight agentic maintenance jobs (see §4). |

**Concrete gaps found in our own code:**

1. **`upskill-news-app/lib/pipeline/adapters/llm.ts:92-95`** — the Ollama
   adapter sends only `temperature` and `num_predict`. **No `num_ctx`, no
   `keep_alive`, no `format`.** In production posture (Qwen3.5-122B composing
   from a large fact table) the compose prompt will hit the silent-truncation
   default. Recommended (Iteration B backlog item): add `num_ctx`
   (env-configurable, e.g. `OLLAMA_NUM_CTX`), `keep_alive`, and optional
   JSON-schema `format` support to `OllamaAdapter`.
2. **`regwatch/`** — triage calls should pin `num_ctx` + `think: false` +
   `format` (JSON schema) explicitly rather than inherit server defaults.
3. **No systemd env block documented** for the Beelink's Ollama service. The
   recommended block:

   ```ini
   # /etc/systemd/system/ollama.service.d/override.conf
   [Service]
   Environment="HSA_OVERRIDE_GFX_VERSION=11.0.0"
   Environment="OLLAMA_HOST=0.0.0.0"
   Environment="OLLAMA_CONTEXT_LENGTH=32768"
   Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
   Environment="OLLAMA_KEEP_ALIVE=30m"
   Environment="OLLAMA_MAX_LOADED_MODELS=2"
   ```

   (Nightly cron exports `OLLAMA_KEEP_ALIVE=-1` for its window instead.)

---

## 2. `qwen3.8:27b` and "Ollama can launch Claude?" — Explained

### What the numbers on the library page mean

`qwen3.8:27b` (https://ollama.com/library/qwen3.8:27b) decodes as:

- **`qwen3.8`** — the model family/generation (Alibaba's Qwen line; 3.8 is the
  August 2026 generation, successor to the Qwen3.5 series our pipelines target).
- **`:27b`** — the *tag*: this variant has **27.3 billion parameters**. Tags on
  one library page are different sizes/quantizations of the same family.
- **Q4_K_M, 18GB** — the default quantization (weights compressed to ~4.5
  bits/param) and the resulting **file size ≈ RAM needed for weights alone**.
  Rule of thumb: Q4 file size ≈ params × 0.55–0.65 bytes; running RAM = weights
  + KV cache (grows with context) + overhead.
- **Vision projector, BF16, 931MB (461M params)** — it's a vision-language
  model; a separate small network encodes images into the LLM.
- **Thinking on by default** — it is a reasoning model: it generates a hidden
  chain-of-thought *before* the visible answer.
- **132.4K downloads / updated 2 days ago** — it shipped *this week* (mid-Aug
  2026). Popularity signal, not quality metric.

### Why "launch Claude with Qwen" is a real sentence

**Claude Code the harness ≠ Claude the model.** Claude Code is an agent loop
(read files, edit, run commands) that talks to *an* Anthropic-compatible API
endpoint. Ollama v0.15+ serves an Anthropic-compatible API, so:

```bash
ollama launch claude              # guided picker, zero config
# equivalent manual wiring:
ANTHROPIC_BASE_URL=http://localhost:11434 \
ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_API_KEY="" claude
```

…runs the Claude Code *harness* with **qwen3.8 (or any local/cloud Ollama
model) as its brain**. Same trick for Codex, OpenCode, Droid, and Pi
(`ollama launch pi`). Ollama's guidance: coding agents want **≥64k context**
and their local picks need **~23GB VRAM** — trivial for the Beelink, the whole
Mac for a MacBook Air.

What this means for us: **free, unmetered agentic labor on the Beelink.** A
harness like Claude Code or Pi driven by a local model is markedly less capable
than the hosted frontier models — but for *narrow, repeatable, verifiable*
nightly chores (re-run scrapers, fix a broken selector, regenerate a dashboard
page, retry failed extractions), a local 27B–122B agent that costs €0.00/token
and runs while we sleep is a new tool class. Cloud Claude designs the jobs;
local Qwen runs them nightly.

### The right home for qwen3.8:27b is the Beelink, not the Mac

On the Beelink, 27B Q4 (~18GB weights) leaves >100GB for KV cache — it can run
with 64k+ context, thinking on, vision enabled, and still co-load an 8B triage
model. Its vision capability is directly useful for Nightwork: **reading
Japanese real-estate listing photos, zoning maps, and municipal PDFs as
images.**

---

## 3. Why the MacBook Air Crawled (and the Fix)

Observed: `qwen3.8:27b` on the MacBook Air (M5, 24GB) took ~15 minutes to
answer one prompt. That is exactly what the numbers predict:

1. **Memory:** 18GB weights + ~1GB vision projector + KV cache + macOS +
   browser ≫ 24GB. macOS also caps GPU-wired memory below total RAM. The model
   spills to SSD swap; token generation drops from "reads like typing" to
   seconds-per-token.
2. **Thinking on by default:** before you see *anything*, the model generates
   potentially thousands of hidden reasoning tokens. At swap-crippled speeds,
   that alone is your 15 minutes of "pondering."

**Fixes, in order of leverage:**

| Fix | How |
|---|---|
| **Don't run it on the Mac at all** (best) | Serve from the Beelink over Tailscale: on Beelink `OLLAMA_HOST=0.0.0.0`; on Mac `export OLLAMA_HOST=http://<beelink-tailscale-ip>:11434` — every Ollama CLI/agent on the Mac now uses Beelink compute. Tailscale is already working (Data Factory setup). |
| Use a Mac-sized model | For 24GB: ~7–14B Q4 dense (e.g. the small qwen3.8 tags, `gpt-oss:20b` borderline). Leave 27B+ to the Beelink. |
| Turn thinking off | Interactive: `/set nothink`. API: `think: false`. |
| Reduce memory pressure | Close browsers/Electron apps before loading; check swap pressure in Activity Monitor while it runs. |

**Pi + qwen3.8 on the Mac specifically:** `ollama launch pi` and pick a model —
but pick a *small* one locally, or set the Mac's `OLLAMA_HOST` to the Beelink
first and Pi on the Mac will happily drive qwen3.8:27b *running in Vilseck*.
That's the correct division of labor for a 24GB laptop and a 128GB server.

---

## 4. The Nightwork Pattern (RegWatch Grows a Dashboard)

**What already exists in this repo:** `regwatch/` — changedetection.io polls
URLs → webhook → Flask → **Ollama triage** → email/GitHub-issue routing, all
YAML-config, all on the Beelink, zero cloud cost. Adding a product = adding
YAML (`domains.yaml`, `watches/*.yaml`, `prompts/*_triage.yaml`).

**What Nightwork adds:** RegWatch answers *"did something change?"* A Nightwork
dashboard answers *"what is the current state of the world I care about?"* —
by spending the night actually **reading**:

```
        DAY (reactive, cheap)                NIGHT (batch, heavy)
changedetection.io polls sources      cron 01:00 (lockfile, like Data Factory)
  → 8B triage: urgent? → email          → OLLAMA_KEEP_ALIVE=-1
                                        → fetch queue: new/changed pages, PDFs,
                                          listings, arXiv abstracts
                                        → BIG model deep-read (27B–122B,
                                          think:true, format:<JSON schema>)
                                        → upsert SQLite state DB (one per domain)
                                        → render static dashboard (HTML/MD)
                                          + morning digest email (Resend)
```

Design rules (all learned elsewhere in the portfolio — this is the
connect-the-patterns part):

- **Verification-first, confidence-tiered.** Reuse the upskill-news pipeline
  shape: gather → cross-verify → verified/stale/unverified tiers → compose.
  A dashboard that shows *confidence and freshness* per fact is the product
  moat, and it's the same architecture we already built and tested (672 tests).
- **CJK rules apply.** Everything in §5–§6 reads Japanese. Every extraction
  prompt and quality gate must follow the Data Factory CJK reference
  (`../vilseckki-datafactory-app/CLAUDE.md` PI-002): character counts not
  `.split()`, chars×1.0–1.5 token estimates, selective-NFKC zenkaku
  normalization, no `\b` regex. The proven CJK model there is
  `qwen2.5:72b`; qwen3.8:27b (vision) is the candidate successor —
  benchmark before switching.
- **Structured outputs everywhere.** JSON-schema `format` per job; schema drift
  detection is a solved problem in the Data Factory (and a PipeElf extraction
  candidate).
- **Cron with lockfile + time cap** — the Data Factory `cron/` harness already
  implements the 8-hour-cap nightly pattern; copy it, don't reinvent.
- **Publish as static HTML** — a dashboard that is just a rendered file needs
  no server, no auth, no maintenance; serve via Tailscale (private) and email
  the digest. Low-touch by construction.

**Why this is a moat (the token math):** an 8-hour nightly window at a
conservative 6 tok/s on a 70B-class dense model ≈ **~170k generated tokens** of
frontier-adjacent quality *per night, per model, at ~€0.50 electricity* — with
input-side reading (prompt processing is much faster than generation)
covering millions of characters of Japanese source text. MoE models
(Qwen3.5-122B-A10B class) push throughput several-fold higher at similar
quality. The same volume through a cloud API with big contexts re-sent nightly
is real money **and** ships private data (school-project competitive research,
land-purchase interest) to third parties. Solo devs without this hardware
either pay it, cap their ambitions, or don't run nightly at all. We just leave
the machine on.

---

## 5. Dashboard 1: Eastern Hill Intelligence (Japanese International Schools)

*(The school brainstorm is no longer abstract: see
`../patterns/education/tokyu-international-school.md` — a concrete
Hachinohe-Station bilingual MEXT school plan targeting Misawa DoD contractors,
updated 2026-08-12. This dashboard exists to keep that document alive and
correct without manual research hours.)*

<!-- FILLED FROM RESEARCH AGENT B -->

## 6. Dashboard 2: Tohoku Land & Akiya Watch (Japanese Real Estate)

<!-- FILLED FROM RESEARCH AGENT A -->

## 7. Dashboard 3: arXiv Research Miner (Dissertation Support)

<!-- FILLED FROM RESEARCH AGENT C -->

## 8. What To Do First

<!-- FILLED AFTER SECTIONS 5-7 -->

## Sources

<!-- CONSOLIDATED AT END -->
