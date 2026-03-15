# 2026-03-11 — Initial Strategy Session

## What Happened
- Read full project inventory, Rebeka ARCHITECTURE.md, EHCP self-challenge doc, and business site content
- Created CLAUDE.md with comprehensive project context
- Analyzed three revenue strategies from brainstorming prompt against owner's constraints
- Assessed local market (Nürnberg-Bayreuth-Weiden-Amberg corridor) opportunities

## Key Observations

### Portfolio is deep but bandwidth is the bottleneck
- 17+ app directories, 3 live/code-complete products, 5+ in pre-MVP
- WritingPAD family has a proven architecture pattern that ports well
- EHCP Audit is the highest-value new product (zero competition, dissertation alignment)
- Beelink strategy must NOT compete with existing product development time

### The Beelink's best role is as infrastructure for existing products FIRST
- EHCP Audit already needs local inference (GRUND framework cloud/local comparison)
- "Assessment Wizard Private Cloud" is a natural premium tier
- Fine-tuning nursing domain models improves ALL products in the family

### For passive income beyond existing products
- RAG-as-a-Service for local Mittelstand is the best fit
- German "Datensouveränität" angle is genuinely compelling in Oberpfalz
- One-time setup with monthly retainer is the right commercial model
- Target: 3-5 local clients at €300-500/month = €900-2,500/month passive

### Dissertation alignment is strong
- The automation pipeline (intake → preprocess → fine-tune → package → deliver) IS the dissertation topic
- Instrumenting and publishing on this pipeline = PhD research and revenue in the same work
- Seed 4 (solo developer automation stack) maps directly to this

## Decisions Made
- Created CLAUDE.md as the canonical context doc for this repo
- Created log/ directory for session tracking
- Did NOT create .clinerules yet (agreed with owner — not an app in development yet)

## Session 2 Updates (March 11, continued)

### Decisions Made
- Domain: vilseckki.de (hyper-local trust play, available)
- First client: Notarin (existing relationship, speaks English, handles maximally-confidential docs)
- PhD deprioritized relative to Beelink revenue — PhD is prestige/HSP points, Beelink is income NOW
- No fine-tuning until 10+ paying clients and real failure data

### Key Concern Raised
Owner asked the right question: "What actual value am I offering if my system can just do whatever for whoever using tiny local models?"
- This needs an honest answer — see CLAUDE.md value proposition section
- The value is NOT "better AI than Claude/GPT-4" — it's privacy guarantee + data residency + local trust
- For RAG specifically, model quality matters less because retrieval does the heavy lifting
- The Notarin pilot will answer this empirically

### #QuitGPT Context
- 2.5M users joined boycott after OpenAI Pentagon deal (Feb 28, 2026)
- Anthropic explicitly refused the same deal — positioned as ethical alternative
- German businesses especially sensitive to US military/surveillance angle
- Timing is ideal for "your data stays in Vilseck" messaging

## Next Steps (Owner to Decide)
- [ ] Register vilseckki.de
- [ ] Benchmark the actual Beelink hardware (install Ollama, run tok/s tests)
- [ ] Talk to the Notarin about a pilot
- [ ] Weekend 1: Ollama + Open WebUI + Tailscale setup
- [ ] Weekend 2: Landing page + Stripe link
