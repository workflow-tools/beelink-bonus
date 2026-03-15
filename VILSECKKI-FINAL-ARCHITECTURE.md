# VilseckKI — Final Architecture & MVP Timeline

> **Status:** Architecture finalized, ready to build
> **Date:** March 11, 2026
> **Consolidated from:** Claude analysis + Gemini "Festung Franken" architecture + owner decisions

---

## The "Festung Franken" Architecture

Three physically separated modules. Zero US dependencies in the data path.

```
┌─────────────────────────────────────────────────────────┐
│  MODULE 1: THE GATEWAY (Hetzner Cloud, NBG1 Nürnberg)  │
│                                                         │
│  Caddy ─── auto-TLS, routing ──────────────────────┐    │
│    │                                                │    │
│    ├── vilseckki.de/*          → Next.js frontend   │    │
│    ├── vilseckki.de/supabase/* → Kong → Supabase    │    │
│    └── vilseckki.de/api/rag/*  → Tailscale tunnel ──┼──┐ │
│                                                     │  │ │
│  Self-Hosted Supabase (Docker Compose)              │  │ │
│  ├── GoTrue (auth)                                  │  │ │
│  ├── PostgreSQL (metadata, chat history, tenants)   │  │ │
│  ├── PostgREST (auto-generated REST API)            │  │ │
│  ├── Kong (API gateway)                             │  │ │
│  ├── Supabase Storage (original documents, RLS)     │  │ │
│  └── Studio (admin dashboard)                       │  │ │
│                                                     │  │ │
│  VPS: Hetzner CPX31 (4 vCPU, 8GB RAM, ~€8.90/mo)   │  │ │
└─────────────────────────────────────────────────────┘  │
                                                         │
┌─────────────────────────────────────────────────────┐  │
│  MODULE 2: THE SECURE BRIDGE (Tailscale)            │  │
│                                                     │  │
│  Encrypted WireGuard mesh VPN                       │  │
│  Hetzner ←→ Beelink on specific ports only          │  │
│  Beelink has ZERO public ports                      │  │
│  Free tier, zero firewall config                    │  │
└─────────────────────────────────────────────────────┘  │
                                                         │
┌─────────────────────────────────────────────────────┐  │
│  MODULE 3: THE BRAIN (Beelink GTR9 Pro, Vilseck)   │←─┘
│                                                     │
│  FastAPI (Python)                                   │
│  ├── /upload    → receive doc → chunk → embed       │
│  ├── /query     → retrieve → generate → respond     │
│  └── /status    → health check                      │
│                                                     │
│  Qdrant (Docker, per-tenant collections)            │
│  Ollama (GPU-accelerated, 128GB unified memory)     │
│                                                     │
│  Hardware: AMD AI Max+ 395, 128GB LPDDR5X           │
│  OS: Windows (pilot) → Ubuntu Server (production)   │
│  Power: ~65W TDP, ~€14/mo electricity               │
└─────────────────────────────────────────────────────┘
```

---

## Key Architecture Decisions (Resolved)

### Where do original documents live?

**Decision: Supabase Storage on Hetzner (with RLS isolation).**

Gemini suggested documents go to the Beelink and stay there. I initially leaned the same way. But after the Supabase Storage analysis, the Hetzner path is better for two reasons:

1. **Resilience.** If the Beelink reboots or loses power, client documents aren't lost. They're on Hetzner's Nürnberg data center with proper storage redundancy. The Beelink only holds derived data (vector embeddings in Qdrant) which can be regenerated from the originals.

2. **Backup story.** When the Notarin asks "what happens if your computer breaks?", the answer is "your documents are on Hetzner's servers in Nürnberg with automated backups. My computer only does the AI processing." This is a more reassuring answer than "everything is on one mini-PC in my apartment."

**The flow:** Client uploads via Next.js → Supabase Storage (Hetzner, RLS-isolated per tenant) → FastAPI on Beelink pulls the file, chunks it, embeds it, stores vectors in Qdrant. The Beelink is stateless and replaceable. If you add a second Beelink later, both pull from the same Supabase.

**The pitch still works:** "Ihre Dokumente liegen auf deutschen Servern bei Hetzner in Nürnberg — ein deutsches Unternehmen, 60 km von hier. Die KI-Verarbeitung läuft auf meinem eigenen Server hier in Vilseck. Nichts verlässt Bayern. Keine US-Firmen involviert."

### Why FastAPI (Python) on the Beelink instead of TypeScript?

**Decision: Python wins here, even though the frontend is TypeScript.**

The RAG pipeline needs: PDF text extraction (PyPDF2/pdfplumber), text chunking (LangChain's RecursiveCharacterTextSplitter), embedding calls (Ollama Python client), Qdrant vector operations (qdrant-client), and orchestration (LangChain or llama-index). The Python ecosystem for all of this is 2-3 years ahead of TypeScript equivalents. LangChain's Python version has 10x the community, examples, and debugging resources compared to LangChain.js.

You maintain two languages: TypeScript (Next.js frontend on Hetzner) and Python (FastAPI backend on Beelink). They communicate via a clean REST API over Tailscale. This is a standard polyglot microservices pattern, not a maintenance burden — they're separated by a network boundary anyway.

### Auth stack?

**Decision: Self-hosted Supabase (GoTrue).**

Since we're already self-hosting Supabase for Storage, database, and admin tooling, running a SEPARATE auth library (Better Auth) alongside Supabase would be redundant complexity. GoTrue gives us auth + JWT claims for RLS + Supabase Studio user management. One platform, one set of conventions.

### Billing?

**Decision: Wise Business invoicing (Phase 1).**

SEPA Überweisung. Monthly PDF Rechnung. No Stripe, no Creem, no MoR. This is how German B2B works. Revisit when client count exceeds 10-15.

---

## Hetzner VPS Structure

```
/opt/vilseckki/
├── supabase/                     # Cloned from github.com/supabase/supabase
│   └── docker/
│       ├── docker-compose.yml    # Official Supabase stack (trimmed)
│       └── .env                  # Keys, secrets, feature flags
├── app/
│   ├── docker-compose.yml        # Next.js + Caddy
│   ├── Caddyfile                 # Route: frontend / supabase / beelink
│   └── nextjs-frontend/          # Your Next.js repo (or pulled from GitHub)
│       ├── Dockerfile
│       ├── src/
│       └── package.json
└── scripts/
    ├── backup.sh                 # Automated Supabase DB + Storage backup
    ├── health-check.sh           # Ping Supabase, Next.js, Beelink tunnel
    └── update-supabase.sh        # Safe Supabase version update procedure
```

### Caddyfile

```
vilseckki.de {
    # Supabase API (auth, database, storage) via Kong gateway
    handle_path /supabase/* {
        reverse_proxy kong:8000
    }

    # RAG pipeline requests → Beelink via Tailscale
    handle_path /api/rag/* {
        reverse_proxy 100.x.y.z:8000  # Beelink Tailscale IP + FastAPI port
    }

    # Everything else → Next.js frontend
    handle {
        reverse_proxy frontend:3000
    }
}
```

### Docker Compose (App Layer)

```yaml
services:
  frontend:
    build:
      context: ./nextjs-frontend
      dockerfile: Dockerfile
    container_name: vilseckki-frontend
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_SUPABASE_URL=https://vilseckki.de/supabase
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    networks:
      - supabase_default

  caddy:
    image: caddy:2-alpine
    container_name: caddy-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - supabase_default

volumes:
  caddy_data:
  caddy_config:

networks:
  supabase_default:
    external: true
```

### Supabase Trimming (Save ~1-1.5GB RAM)

In the Supabase `docker-compose.yml`, comment out or remove:
- `imgproxy` (image transformation — not needed, you're handling PDFs not images)
- `edge-runtime` (Deno edge functions — not needed, your logic is in Next.js and FastAPI)
- `logflare` / `analytics` (optional — nice to have but not essential for MVP)
- `supabase-vector` (if using Qdrant on Beelink for vectors instead of pgvector)

In the Supabase `.env`:
```
ENABLE_IMAGE_TRANSFORMATION=false
```

This should bring idle RAM usage from ~3-4GB down to ~2-2.5GB, leaving comfortable headroom for Next.js and Caddy on the CPX31 (8GB total).

---

## Beelink Structure

```
C:\VilseckKI\                     # Windows (pilot phase)
├── ollama\                        # Ollama models + config
├── qdrant\                        # Qdrant Docker volume
├── fastapi-rag\                   # Python RAG pipeline
│   ├── main.py                    # FastAPI app
│   ├── rag_pipeline.py            # Chunking, embedding, retrieval logic
│   ├── requirements.txt           # langchain, qdrant-client, pdfplumber, etc.
│   └── .env                       # Ollama URL, Qdrant URL, auth secrets
└── scripts\
    ├── start-all.bat              # Starts Ollama, Qdrant, FastAPI
    └── health-check.bat           # Verify all services running
```

When moving to Ubuntu Server (production phase):
```
/opt/vilseckki/
├── docker-compose.yml             # Qdrant + FastAPI containers
├── fastapi-rag/                   # Same Python code
├── scripts/
│   ├── start.sh
│   └── health-check.sh
└── data/
    └── qdrant-storage/            # Qdrant persistent volume
```

Ollama runs as a systemd service on Linux, outside Docker, for direct GPU access.

---

## MVP Timeline: Two Parallel Tracks

### The Honest Answer

**Technical MVP: 10-14 focused working days.**
**Legal readiness: 1-2 weeks in parallel.**
**Calendar time to Notarin pilot: 3-4 weeks** (accounting for evenings/weekends schedule, with Cowork + Codestral acceleration).

### Critical Path

```
WEEK 1 ──────────────────────────────────────────────
│
├── LEGAL TRACK (non-blocking, runs in parallel)
│   ├── Day 1-2: Run the 6 legal research prompts
│   ├── Day 3-4: Review answers, identify blockers
│   ├── Day 5: Talk to Notarin ("what would you need?")
│   └── Day 5-7: Draft AVV + Dienstleistungsvertrag
│
├── TECH TRACK 1: Beelink (blocking — everything depends on this)
│   ├── Day 1: Install Ollama on Windows
│   │   └── Set HSA_OVERRIDE_GFX_VERSION=11.0.0
│   │   └── Pull models: llama3.1:70b-q4, mistral:7b, nomic-embed-text
│   │   └── BENCHMARK: actual tok/s on YOUR hardware
│   │   └── If GPU not detected → troubleshoot ROCm before anything else
│   ├── Day 2: Docker Desktop → Qdrant container
│   │   └── Test: create collection, insert vectors, query
│   ├── Day 2-3: FastAPI RAG skeleton
│   │   └── /upload endpoint: receive PDF → pdfplumber extract → chunk → embed → store in Qdrant
│   │   └── /query endpoint: embed query → Qdrant search → Ollama generate → return
│   │   └── Tenant ID parameter on both endpoints
│   └── Day 3: Install Tailscale on Beelink, verify connectivity
│
│   *** GATE CHECK: Can you upload a PDF and ask a question about it? ***
│   *** If yes → proceed. If no → fix before touching Hetzner. ***

WEEK 2 ──────────────────────────────────────────────
│
├── TECH TRACK 2: Hetzner VPS
│   ├── Day 4: Provision CPX31, install Docker + Tailscale
│   │   └── Verify: curl from Hetzner to Beelink Tailscale IP
│   ├── Day 4-5: Clone Supabase repo, configure .env, trim services
│   │   └── docker compose up -d
│   │   └── Verify Studio accessible (localhost:3000 or internal port)
│   │   └── Create first org/tenant in Studio
│   ├── Day 5: Caddy + routing
│   │   └── Caddyfile with three routes (supabase, rag, frontend)
│   │   └── Test: /supabase/auth/v1/health responds
│   │   └── Test: /api/rag/status reaches Beelink FastAPI
│   └── Day 5-6: Supabase Storage setup
│       └── Create 'documents' bucket
│       └── Write RLS policy: tenant_id isolation
│       └── Test: upload file via Supabase client, verify isolation
│
├── TECH TRACK 3: Next.js Frontend
│   ├── Day 6-7: Scaffold Next.js app
│   │   └── Supabase auth (login/signup pages)
│   │   └── Document upload page (Supabase Storage client)
│   │   └── Chat interface (sends query to /api/rag/query)
│   │   └── Basic tenant dashboard (list uploaded docs)
│   ├── Day 8: Wire upload → Beelink processing
│   │   └── On upload: Supabase Storage stores original
│   │   └── Webhook or polling: FastAPI pulls new file, processes it
│   │   └── Status indicator: "processing" → "ready to query"
│   └── Day 9: Dockerize, deploy to Hetzner app layer
│       └── docker compose up -d (frontend + caddy)

WEEK 3 ──────────────────────────────────────────────
│
├── INTEGRATION & HARDENING
│   ├── Day 10: End-to-end testing
│   │   └── Create test tenant → upload PDF → wait for processing → ask question → verify answer
│   │   └── Create second tenant → verify ZERO data leakage
│   │   └── Test from phone / different network
│   ├── Day 11: Error handling + monitoring
│   │   └── Health check scripts (Hetzner → Beelink alive?)
│   │   └── Beelink auto-restart on crash (systemd or Windows Task Scheduler)
│   │   └── Basic logging
│   └── Day 12: Landing page on vilseckki.de
│       └── German language, privacy messaging
│       └── Contact form or email link
│       └── Impressum + Datenschutzerklärung
│
├── LEGAL TRACK RESOLUTION
│   ├── Finalize AVV template
│   ├── Finalize Dienstleistungsvertrag
│   ├── Confirm Unternehmensgegenstand with Notarin
│   └── Get IT-Haftpflicht quote

WEEK 4 ──────────────────────────────────────────────
│
├── NOTARIN PILOT LAUNCH
│   ├── Day 13: Create her tenant in Supabase Studio
│   ├── Day 13: Walk her through the UI (in English)
│   ├── Day 13-14: Watch her use it, take notes
│   └── Ongoing: 4-6 week free pilot
│       └── Weekly check-in: "What's working? What's missing?"
│       └── Her feedback shapes v2
│
└── POST-PILOT (Week 8-9)
    ├── Convert pilot to paid (€149/month Rechnung via Wise)
    ├── Ask for referrals
    └── Register vilseckki.de (if not already)
```

### What Could Compress This?

**If the Beelink GPU just works** (ROCm detects the 890M cleanly, Ollama serves at expected speeds), you save 1-2 days of troubleshooting. This is the biggest variable.

**If you skip the custom Next.js frontend for the pilot** and just give the Notarin Open WebUI (which has its own auth and document upload), you could skip Week 2's frontend work entirely and have a working pilot in ~8-10 days. Less polished, but functional. Build the proper frontend after you've validated demand.

**Cowork + Codestral** for the FastAPI pipeline and Next.js frontend could realistically cut coding time by 40-50%. The boilerplate (Supabase client setup, FastAPI endpoint scaffolding, Next.js auth pages) is exactly what AI coding assistants are best at.

### What Cannot Be Compressed?

**The legal track.** § 203 StGB is criminal law. You cannot shortcut the AVV and Verpflichtungserklärung. If the research prompts surface a blocker (e.g., you need specific insurance before handling Berufsgeheimnisträger data), that blocks the pilot regardless of how fast the code is ready.

**The Beelink GPU verification.** If ROCm doesn't work cleanly on the 890M under Windows, you may need to go straight to Ubuntu Server, which adds 1-2 days. This is Day 1, not Day 14 — don't build everything else assuming the GPU works.

---

## Fastest Possible MVP (The Shortcut)

If you want a working demo in the Notarin's hands THIS MONTH:

1. **Skip the custom frontend.** Use Open WebUI on the Beelink (it has auth, document upload, and chat built in). Give her access via Tailscale directly.
2. **Skip Hetzner + Supabase for now.** The Beelink IS the entire stack for the pilot.
3. **Skip the landing page.** You have one client. She doesn't need a website.

```
Timeline for shortcut MVP:
Day 1: Ollama + Open WebUI + Tailscale on Beelink
Day 2: Benchmark, test document upload + RAG in Open WebUI
Day 3: Legal research prompts (run in Claude/Gemini)
Day 4-5: AVV + Dienstleistungsvertrag draft
Day 6-7: Notarin meeting → pilot begins

Total: 1 week.
```

Then build the "Festung Franken" architecture (Hetzner + Supabase + custom frontend) over the following 2-3 weeks WHILE the Notarin is using the rough version. Her feedback tells you what to prioritize in the real build.

**This is the same lean pattern you used for WritingPAD.** Validate first, productize second.

---

## Cost Summary

| Item | Monthly Cost |
|------|-------------|
| Hetzner CPX31 (8GB, Nürnberg) | ~€8.90 |
| vilseckki.de domain | ~€0.50 (annual / 12) |
| Beelink electricity (~65W, 24/7) | ~€14.00 |
| Tailscale | €0 (free tier) |
| IT-Recht-Kanzlei (shared with other products) | ~€9.90 (already paying) |
| Wise Business account | €0 (no monthly fee) |
| **Total monthly operating cost** | **~€33.30** |

**Break-even: 1 client at any tier.**

---

## Data Sovereignty Summary

When the Notarin asks "where is my data?":

| Data Type | Location | Operator | US Dependency |
|-----------|----------|----------|---------------|
| Login credentials | Hetzner VPS, Nürnberg | Hetzner Online GmbH (German) | None |
| Account metadata | Hetzner VPS, Nürnberg | Hetzner Online GmbH (German) | None |
| Original documents | Hetzner VPS, Nürnberg | Hetzner Online GmbH (German) | None |
| Document embeddings | Beelink, Vilseck | Your hardware | None |
| AI inference | Beelink, Vilseck | Your hardware | None |
| Chat history | Hetzner VPS, Nürnberg | Hetzner Online GmbH (German) | None |
| Payments | SEPA Überweisung | Wise (EU-licensed) | None |
| DNS | German registrar | INWX / Hetzner DNS | None |

**"Nichts verlässt Bayern."**

---

## Open Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| ROCm doesn't work on 890M under Windows | Blocks everything | Test Day 1. Fall back to Ubuntu Server. |
| § 203 StGB research surfaces a blocker | Delays pilot | Run legal prompts BEFORE writing code. |
| Supabase self-hosted is unstable | Service outages | Keep the trimmed stack minimal. Have docker restart policies. |
| Beelink power/internet outage | Service interruption | UPS (~€50). Tailscale auto-reconnects. Hetzner holds documents. |
| Notarin doesn't find it useful | No business validation | That's why it's a free pilot. Pivot before investing more. |

---

## Files in This Repo

| File | Purpose | Status |
|------|---------|--------|
| `CLAUDE.md` | Claude context for any session | Current |
| `VILSECKKI-FINAL-ARCHITECTURE.md` | **This file** — the build plan | Current |
| `VILSECKKI-IMPLEMENTATION-PLAN.md` | Earlier planning (legal prompts, payment analysis) | Reference — legal prompts still authoritative |
| `AUTH-AND-BACKEND-COMPARISON.md` | Better Auth vs Supabase analysis | Reference — decision made (Supabase) |
| `BEELINK-PASSIVE-REVENUE-STRATEGY.md` | Market analysis, pricing, GTM | Reference — pricing/market still authoritative |
| `log/2026-03-11-initial-strategy-session.md` | Session notes | Archive |
