# 2026-08-15 — Beelink × Upskill News indexing synergy (coordination session)

**Branch:** `claude/beelink-upskill-news-indexing-anq2li` (same branch in
beelink-bonus, patterns, upskill-news-app).

**Ask:** explore how the Beelink's "index/search processing" capacity and the
upskill-news IEC newsletter product interact; assess existing assets across the
portfolio; produce specific designs with specific to-do lists; explain the
"search index as an asset" concept; plan the Beelink setup (including making
Ubuntu the default boot instead of Windows).

**Method:** 13-agent exploration — 4 repo readers, 2 web researchers
(index-as-product economics; mid-2026 Strix Halo serving practice), 4 competing
designs (ship-the-product / index-factory / shared-substrate / passive-ladder),
3-judge panel (feasibility / revenue realism / ops-passivity). Also cloned and
surveyed the canonical `vilseckki-datafactory-app` for reusable production code.

**Verdict:** "Upskill Newsroom Server" backbone (22/30) + grafts from the
losing designs. Full decision record: `../BEELINK-UPSKILL-INDEXING-PLAN.md`.

**Artifacts produced this session:**
- `BEELINK-UPSKILL-INDEXING-PLAN.md` — master plan (this repo)
- `upskill-news-app/docs/BEELINK_FACTS_INDEX.md` — app-side integration contract
- `patterns/docs/research/BEELINK_INDEX_ASSET_RESEARCH.md` — sourced research
- `patterns/ideas/MICRO-SAAS-IDEAS.md` idea #110 + INDEX/DEV-LOG housekeeping
- `CLAUDE.md` corrections in this repo (HSA flag 11.0.0 → 11.5.1, MoE-centric
  speed table, resolved open questions, master-plan pointer)

**Key facts surfaced (do not lose):**
- The chip is gfx1151; the 11.0.0 HSA override was the wrong-chip spoof.
- MoE is the machine's sweet spot (~50 tok/s at 100B+ MoE); dense 70B ≈ 5 tok/s.
- The GTR9 Pro's Intel E610 NIC has a documented firmware deadlock under
  sustained GPU+network load — the headline 24/7 risk; Phase 0 gauntlet defined.
- Cloudflare Tunnel decrypts at its edge → Tailscale-only for confidential work
  (long-open question resolved).
- Nothing in the portfolio persists crawled data; the pipeline's HistoricalSource
  seam is empty — the Verified Facts Store fills exactly that hole.
- The index-as-product concept already existed in-portfolio (EU-AI-ACT corpus
  plan; patterns Stream 1); the AI-Act demand anchor passed unlaunched.
- Education vertical honesty: ~2,800 IECA members, <10 platform buyers —
  five-figure niche as a product; load-bearing as the product's accuracy moat.
- Data Factory repo survey: reuse health_check/auto_checker, ollama_models.py
  residency manager, blind_extractor verifier pattern, nightly-run.sh; the old
  BaseScraper abstraction was NOT carried forward; no embedding/vector code
  exists anywhere in the portfolio.

**Next actions:** Phase 0 hardware runbook (plan §6) — boot fix, NIC gauntlet,
benchmark gate, regwatch deployment; owner decisions listed in plan §9.
