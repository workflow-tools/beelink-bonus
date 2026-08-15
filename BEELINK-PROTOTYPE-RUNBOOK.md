# Beelink Prototype Runbook

> **Date:** 2026-08-15 (evening update) · **Branch:** `claude/beelink-upskill-news-indexing-anq2li`
> **Executes:** Phases 0–2 of `BEELINK-UPSKILL-INDEXING-PLAN.md`, compressed into
> concrete action items with executor tags, aimed at one target: the **first
> shadow edition** (defined in §1). Where this doc and the master plan's fleet
> assumptions disagree, **this doc wins** — the fleet changed on 2026-08-15.
>
> **Fleet reality (owner-reported 2026-08-15):**
> - **beeteam** (Beelink GTR9 Pro) now runs **Ubuntu as primary OS** and has
>   **Claude Code installed on the box** — most setup/benchmark items below can
>   be executed by an on-box Claude Code session, not typed by hand.
> - The dev Mac is a **new MacBook Air (M5, 24GB RAM, 1TB)**. It has **no
>   Tailscale**; the old tailnet topology in `patterns/reference/machines.md`
>   is defunct (addendum filed there). Connectivity is rigged fresh in §2.
> - Cloud rig (Vercel + Supabase) is open — and deliberately **not needed for
>   the prototype at all** (§5).

**Executor tags:** `[YOU]` = physical/BIOS/accounts, only you can do it ·
`[CC@beeteam]` = a Claude Code session running on the Beelink ·
`[SESSION]` = any repo session (web, or Claude Code on the Mac) ·
`[MAC]` = on the MacBook Air.

---

## 1. The prototype, defined (so "done" is checkable)

**P1 — "first shadow edition":** all of the following true at once:

1. The facts store is live on beeteam with **real** College Scorecard rows for
   ~50 schools and real VA GI Bill status rows — crawled at least **twice**, so
   at least one diff has landed in `change_events`.
2. `runner generate --config demo-clients.yaml` produces editions for **3
   fictional personas**, grounded only in stored facts, QA-passing,
   release-gate-evaluated, written to an outbox as JSON **plus rendered HTML
   previews** (via the existing `newsletter/render.ts`) you can open in a
   browser.
3. Compose ran on the **local** model, using whichever serving binary the
   benchmark chose; the whole run fired **unattended from a systemd timer**
   with a healthchecks.io dead-man ping.
4. All vitest suites green; benchmark numbers recorded in
   `mistral/open-source-models/BEELINK-FIT.md` (ending its empty-log era).
5. **Zero cloud accounts involved.** No Clerk, no Supabase, no Resend, no
   GDPR surface — nothing was sent to anyone.

Everything else in the master plan (cloud edge, pilots, revenue) comes after
this exists.

## 2. Connectivity decision (the "rig it however we want" answer)

**Recommendation: re-establish Tailscale, on both machines, first.**
Free tier, ~10 minutes total, and the whole security architecture assumes it
(zero public ports on beeteam; `OLLAMA_BASE_URL` over the tailnet; survives
the certain relocation; the DSGVO story if Track B ever happens). LAN-only SSH
(`beelink.local`) works for a weekend at home but breaks the moment you
travel, and Cloudflare Tunnel stays rejected for anything confidential.

- [ ] `[YOU/MAC]` Install Tailscale on the Mac (App Store or
      `brew install --cask tailscale`), log in.
- [ ] `[CC@beeteam]` `curl -fsSL https://tailscale.com/install.sh | sh &&
      sudo tailscale up --ssh` — note the **new** MagicDNS name and IP (the old
      `beeteam.tail7.edc07.ts.net` / `100.79.207.105` are dead; do not reuse).
- [ ] `[SESSION]` Record the new names in `patterns/reference/machines.md`
      (replacing the 2026-08-15 stale-fleet addendum with measured facts).

Because Claude Code runs on beeteam, the Mac is optional for most of this
runbook — it's the dev cockpit (app dev, tests, reviewing HTML previews) and
the `iperf3` counterpart for the NIC soak.

## 3. Lane A — beeteam base (≈1 weekend; mostly `[CC@beeteam]`)

- [ ] **A1 Boot posture** `[CC@beeteam]` + `[YOU]` for any BIOS screen:
      confirm Ubuntu owns the boot order (`efibootmgr -v`). If Windows still
      wins or dual-boot remains: `sudo efibootmgr -o <ubuntu>,<windows>`;
      `GRUB_DEFAULT=saved` + `GRUB_SAVEDEFAULT=true`; install the oneshot
      `bootorder-assert.service`; boot Windows once to `powercfg /h off`.
- [ ] **A2 BIOS pass** `[YOU]`: Restore AC Power Loss = Power On (record the
      menu path in machines.md — undocumented for the GTR9 Pro); TDP cap
      ~85–100W; UMA minimum; IOMMU on; record BIOS + Intel E610 NVM versions,
      update to ≥1.08 / ≥1.30 if older.
- [ ] **A3 GPU memory** `[CC@beeteam]`: add
      `amdgpu.gttsize=131072 ttm.pages_limit=31457280` to
      `GRUB_CMDLINE_LINUX`, reboot, verify ~110GB GPU-addressable.
- [ ] **A4 LLM serving** `[CC@beeteam]`: Ollama systemd unit with
      `HSA_OVERRIDE_GFX_VERSION=11.5.1`, `OLLAMA_FLASH_ATTENTION=1`, never
      `OLLAMA_VULKAN=1`; `ollama list` — if `qwen3.5:122b` isn't there under
      Ubuntu, either copy the model blobs from the old Windows Ollama install
      (if that partition survives — saves a ~77GB download) or `ollama pull`
      overnight. Stand up `llama-server` (Vulkan) alongside for the bake-off.
- [ ] **A5 Benchmark gate** `[CC@beeteam]`: qwen3.5:122b decode+prefill on
      Ollama/ROCm **vs** llama-server/Vulkan; one 30B-A3B-class extractor
      candidate on real admissions-page extraction prompts (quality + speed —
      decides two-tier extraction); bge-m3 chunks/hour; idle/load watts.
      **Record in `mistral/open-source-models/BEELINK-FIT.md`, commit, push.**
      This closes the plan's serving-binary and batch-window questions.
- [ ] **A6 NIC soak** `[CC@beeteam]` + `[MAC]` as iperf3 server: 4h of
      concurrent generation + `iperf3` through the E610. Lock-up ⇒ USB 2.5GbE
      NIC (~€25 — `[YOU]` order one regardless) becomes primary. Re-run after
      any firmware update.
- [ ] **A7 Watchdogs & backup (prototype-grade)** `[CC@beeteam]`:
      healthchecks.io account (free) + ping hooks; Uptime Kuma container;
      restic to a local external disk for now (offsite Hetzner Storage Box is
      a pre-pilot upgrade, not a prototype blocker). `[YOU]`: smart plug.
- [ ] **A8 RegWatch** `[CC@beeteam]`: `docker compose up -d` in `regwatch/`,
      systemd wrapper, confirm `GET :5050/api/changes/upskill_news` returns
      triaged events from the existing watch list; point triage at the main
      LLM endpoint (no separate 8B model).

## 4. Lane B — Facts store + runner (≈2–3 weeks of evenings; `[SESSION]`, offline-testable)

All of this is ordinary repo work in `upskill-news-app` against fixtures — it
does not need the Beelink until the first on-box run, so it can proceed in
parallel with Lane A from any machine. Detailed contract:
`upskill-news-app/docs/BEELINK_FACTS_INDEX.md` §5.

- [ ] **B1** Migrations for the four tables (`fact_candidates`,
      `change_events`, `crawl_runs`, `schools` with `scorecard_id` + IPEDS
      `unitid`), append-only guard triggers.
- [ ] **B2** `FactsStoreSource` (Tier 2 DataSource) + tests.
- [ ] **B3** `VAGiBillSource` (Tier 1) + fixture tests, `meta.version` honored.
- [ ] **B4** Scorecard bulk puller. `[YOU]`: request `DATA_GOV_API_KEY`
      (2 minutes, free, instant).
- [ ] **B5** `server/runner/` CLI: `crawl` (SLA due-set → fetch → store →
      diff), `generate` (personas → pipeline → outbox JSON + **HTML previews**
      via `newsletter/render.ts`), `demo-clients.yaml` with 3 fictional
      personas. Postgres install on beeteam (`[CC@beeteam]`, one evening) when
      B1 is ready to apply.
- [ ] **B6** systemd units/timers checked into `server/runner/systemd/`
      (`Persistent=true`, `OnFailure=` ping), deployed by `[CC@beeteam]`.
- [ ] **B7** Generated school dataset → `lib/school-search.ts` wiring
      (closes the missing `scorecardId` mapping).
- [ ] **Deliberately post-prototype:** the admissions-page scraper/extractor
      (the fragile, liability-carrying part) and its 2-week accuracy soak.
      The prototype proves the loop on structured sources only.

## 5. Lane C — Mac cockpit (≈1 evening) & Lane D — cloud (deferred)

- [ ] `[MAC]` Clone the three repos; `npm install`; app runs fully offline in
      demo mode; use it + the outbox HTML previews to review shadow editions.
      24GB M5 is ample for app dev + tests (it will never serve models — that
      is beeteam's job).
- [ ] `[MAC]` VS Code Remote-SSH (or plain `ssh`) to beeteam over the tailnet;
      or just talk to the on-box Claude Code directly.
- **Cloud (Lane D): nothing until P1 exists.** When Phase 3 comes: your
  Claude account already carries **Vercel and Supabase connectors**, so
  provisioning can be Claude-assisted in-session; Stripe's connector exists
  but needs authorization in claude.ai settings before any session can use it
  (months away — payments are post-pilot).

## 6. Kickoff prompt for the on-box Claude Code session

Paste this into Claude Code on beeteam to start Lane A:

```
Read beelink-bonus/BEELINK-PROTOTYPE-RUNBOOK.md and BEELINK-UPSKILL-INDEXING-PLAN.md
(branch claude/beelink-upskill-news-indexing-anq2li). Execute Lane A items
A1–A5 on this machine: verify/fix boot order, apply the GTT kernel params,
set up the Ollama systemd unit with HSA_OVERRIDE_GFX_VERSION=11.5.1 (this chip
is gfx1151 — never 11.0.0, never OLLAMA_VULKAN=1), get qwen3.5:122b available,
stand up llama-server (Vulkan) alongside, and run the full benchmark gate.
Record all measurements in mistral/open-source-models/BEELINK-FIT.md with the
exact commands used, then commit and push to this branch. Flag anything that
needs BIOS access or a purchase — don't guess hardware state, measure it.
```

## 7. Sequencing at a glance

```
Lane A (beeteam base, 1 weekend)  ──┐
                                    ├─→ first on-box run ─→ timer-driven runs ─→ P1
Lane B (store+runner, 2–3 wks) ─────┘        (Postgres applied, runner deployed,
Lane C (Mac cockpit, 1 evening) ─ anytime     two crawls, three shadow editions)
Lane D (cloud) ─ deliberately after P1
```

Critical path = Lane B (the runner build). Lane A is a weekend and is fully
parallel. The first items to do **today**: Tailscale on both machines (§2),
order the USB NIC + smart plug, request `DATA_GOV_API_KEY`, and fire the §6
kickoff prompt on beeteam.
