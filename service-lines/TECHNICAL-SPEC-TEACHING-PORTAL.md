# Technical Specification — The Teaching Portal

> **Review status: GATED — do not build.** Reviewed 2026-08-17. The reviewer verified every
> file path, export, and migration helper named here against `/home/user/upskill-news-app` and
> found no invented names; the reuse thesis is sound. It is gated because **no buyer exists** —
> see [`README.md`](README.md). Three defects corrected inline (the history-moderation bypass,
> the zero-retention overclaim on the cloud path, the `safety_events` pseudonymity claim) and
> one left open (the `admin` -> `operator` rename breaks `private.is_admin()`). What is worth
> doing now is §11 Q1 and Q2 plus the `OllamaAdapter` `num_ctx` fix.

**Status:** buildable specification, not a proposal. **Date:** 18 August 2026.
**Reference codebase:** `/home/user/upskill-news-app` (Next.js 16, Clerk, Supabase, verification-first pipeline).
**Sibling documents:** `docs/OLLAMA-NIGHTWORK-DASHBOARDS.md` (Ollama defaults audit), `docs/CLASSROOM-BUILD-LAB.md` (§4 portal architecture, §5 capacity arithmetic).

---

## Verdict

**Do not build a new application. Fork `upskill-news-app`, rename two roles, add three tables and four route handlers.** Roughly 70% of this specification already exists as working, unit-tested code in that repo: the role-gated network boundary (`proxy.ts`), the pure gate rules (`lib/auth-config.ts`), the fail-closed server-identity seam (`lib/auth-server.ts` + `lib/api-server.ts`), the four-provider model failover chain (`lib/pipeline/adapters/llm.ts`), and a complete append-only-audit RLS pattern in `supabase/migrations/`. What genuinely does not exist is: a quota counter with real queueing, a moderation stage, a roster/cohort model, and an `OllamaAdapter` that sets `num_ctx`, `keep_alive` and `format`.

The single highest-risk technical unknown is **not** the portal. It is whether a 27B open-weights model can drive a multi-file agentic coding loop well enough that a participant finishes a working app. §11 gives an afternoon-length test for that. Run it before Phase 3.

The single most likely operational failure is **queue-shaped, not capacity-shaped**: a gateway's per-key parallel limit returns HTTP 429 instead of queueing, participants (or their tooling) retry, and the retries amplify the load that caused the 429. §8 specifies the queue that prevents this. Build it in Phase 2, not later.

---

## 1. What this is and what it is not

This is a **single-tenant multi-cohort inference gateway with a teaching UI**: participants sign in to a browser tab, type into a chat or a build assistant, and their request is authenticated, quota-checked, moderated, routed to a model, moderated again, and returned — with the prompt and completion held only in process memory for the life of the request. It is the shared substrate under every service line that involves other people using models: a paid live cohort, an FMWR/SKIESUnlimited youth class, a B2B in-house workshop where exercises run against a client's own material, or a personal family deployment. It is **not** a chat product, not a general-purpose LLM proxy for arbitrary tenants, not a course platform (no lessons, no grading, no completion tracking — deliberately, see §2 R-13), not a data-retention system, and not something that will ever hold a participant's source documents. It stores who is allowed in, how much they have used, and that a safety rule fired — nothing else.

---

## 2. Requirements

### 2.1 Functional

| # | Requirement |
|---|---|
| F-1 | An operator creates a cohort, adds participants by email, and the participant receives a sign-in link. No self-registration, ever. |
| F-2 | A participant signs in and reaches exactly one surface: their cohort's workspace. No admin routes, no other cohort, no model endpoint, no key. |
| F-3 | Every model request carries a verified identity resolved server-side; the client cannot assert its own role, cohort, or quota. |
| F-4 | Each request is checked against a per-participant quota (requests and tokens, per rolling window) before any model call is made. |
| F-5 | Each request passes a deterministic filter, then an ML classifier, on the way in; the completion passes both on the way out. |
| F-6 | The router selects a backend (local → cloud → refuse) and **discloses the selected backend to the participant in the response**. |
| F-7 | An operator sees, per cohort: participants, quota consumption, safety-event counts by category, and backend health. One page. |
| F-8 | An operator can suspend a participant or a whole cohort in one action, effective on the next request. |
| F-9 | A safety event records participant, cohort, timestamp, category, stage (input/output), and the action taken — and **no prompt or completion text of any kind**. |
| F-10 | Session transcripts live in the participant's browser (`sessionStorage`) and are lost on tab close. There is no server-side history and no "resume conversation". |

### 2.2 Non-functional

| # | Requirement | Derived from |
|---|---|---|
| N-1 | **Zero prompt-content retention *by this system*.** No prompt or completion text is written to disk, to a database, to a log line, or to a third-party observability service, on any code path including error paths. Logs carry ids, token counts, latencies, statuses — never text. **Carve-out, stated plainly:** this holds absolutely on the local path. When a request falls back to a cloud provider (routing step 3), that provider retains the text under its own abuse-monitoring terms, so the guarantee becomes "nothing is retained by us." Any B2B pitch that says "your material does not leave the room" is therefore **only honest with cloud fallback disabled**, which must be a per-deployment switch, not a default. Disclose the active brain to the user. |
| N-2 | **Minor-safe by configuration, not by hope.** A cohort carries an `audience` of `adult` or `minor`. In `minor` cohorts moderation cannot be disabled, cloud fallback is refused rather than silently used, and the system prompt is pinned to the strict profile. The code path must make the unsafe combination unrepresentable, not merely discouraged. | Some deployments (CYS/SKIES youth, homeschool co-ops) involve minors; others (paid adult cohorts, B2B) do not. |
| N-3 | **Zero client install.** Chrome on a managed Chromebook, no extension, no CLI, no Docker, no local port. Everything is HTTPS to one origin. Progressive enhancement only. | Managed-device constraint. |
| N-4 | **Graceful degradation.** Beelink unreachable must produce a working, disclosed, degraded experience — not an error page. Failure ladder: local model → cloud model (adult cohorts only, disclosed) → read-only mode with a clear banner. A session must never hard-fail. | The Beelink is a single consumer mini-PC on a residential line. |
| N-5 | **Minutes-per-day operations.** No component may require daily attention. Cohorts are created in bulk; quotas reset on a schedule; alerts are exception-only and go to one channel. If it needs a daily check, it is not shipped. | Documented 15–25 min/day budget. |
| N-6 | **Fail closed everywhere.** Missing configuration produces a refusal, never a permissive default. This is already the codebase's posture: `boundaryInactiveOutcome()` returns 503 rather than degrading (`lib/api-server.ts`), and `buildMisconfiguredProxy()` in `proxy.ts` redirects every gated route to `/login` rather than falling back to the spoofable cookie gate. Keep it. | Existing convention; also the only defensible posture with minors. |
| N-7 | **No inbound ports on the residential line.** All Beelink connectivity is outbound-initiated (Tailscale). Nothing listens on a public IP at the house. | German residential ISP terms generally prohibit server operation; also the correct security posture regardless. |
| N-8 | **Accessibility.** WCAG 2.2 AA, verified by the existing harness. `scripts/a11y-audit.mjs` already runs axe-core over every route (`npm run a11y`). Extend the route list; do not write a new auditor. | Any federal-agency deployment would require Section 508 conformance evidence; and it is cheap here because the harness exists. |
| N-9 | **Data minimisation as a schema property.** The absence of content columns must be visible in the DDL, so that "we do not store prompts" is verifiable by reading `supabase/migrations/` rather than by trusting application code. | Makes the privacy claim auditable by a buyer's counsel in five minutes. |

### 2.3 Explicit non-requirements

R-13: **No learning-success monitoring in the platform.** No grading, no assessed exercises, no completion certificates, no progress tracking. This is a deliberate product decision with a legal edge: §1 FernUSG requires *both* spatial separation *and* monitoring of learning success (`Überwachung des Lernerfolgs`) before a paid offering is regulated distance learning. Building assessment into the portal manufactures the second element for every deployment that uses it. If a specific engagement needs assessment, it happens outside the portal, in a form counsel has reviewed for that engagement. *(Legal framing only — this is not legal advice, and the BGH's threshold for what counts as monitoring is low. See the constraints dossier.)*

R-14: No multi-tenancy beyond cohorts. One operator, one deployment, many cohorts. Selling the portal itself to other operators is a different product with a different security model.

R-15: No file upload in Phase 1–3. Participants paste text. File upload introduces virus scanning, size limits, storage, and a retention question the whole design exists to avoid.

---

## 3. Architecture

```
  PARTICIPANT                    PORTAL  (Next.js 16, one origin)                    BACKENDS
  ┌──────────────┐   HTTPS   ┌──────────────────────────────────────────┐
  │ Chromebook   │──────────▶│ proxy.ts                                 │
  │ browser tab  │           │   isClerkServerConfigured ? clerk : cookie│
  │ no install   │           │   dashboardRedirectPath()  ← HTML gate    │
  │ sessionStorage│          │   apiAccessDeniedStatus()  ← JSON gate    │
  └──────────────┘           └────────────────┬─────────────────────────┘
        ▲                                     │  (defense in depth only)
        │                    ┌────────────────▼─────────────────────────┐
        │                    │ app/api/inference/route.ts               │
        │                    │  1 getServerIdentity()      401/403       │
        │                    │  2 resolveAppUserId()       403           │
        │                    │  3 cohort + audience load   403/423       │
        │                    │  4 consumeQuota()           429 + Retry-After
        │                    │  5 moderateInput()          422           │
        │                    │  6 enqueue() ── bounded FIFO ── 503       │
        │                    │  7 routeAndGenerate() ───────────────────┼──▶ Beelink
        │                    │  8 moderateOutput()         422           │    (Tailscale,
        │                    │  9 recordUsage() / recordSafetyEvent()    │     outbound only)
        │                    │     ids + counts only, NEVER text         │       │ fail
        │                    └────────────────┬─────────────────────────┘       ▼
        │                                     │                            cloud provider
        └─────────── response + x-model-route ┘                            (adult cohorts,
                                                                            disclosed)
                     ┌─────────────────────────────────┐                        │ fail
                     │ Supabase (or Postgres)          │                        ▼
                     │  cohorts · participants ·       │                    read-only mode
                     │  quota_counters · safety_events │                    (banner, no calls)
                     │  RLS on, revoked from anon      │
                     │  NO content columns anywhere    │
                     └─────────────────────────────────┘
```

### Layer 1 — Network boundary

**Reuse `proxy.ts` unchanged in structure.** It already selects its branch once at module load (`isClerkServerConfigured ? buildClerkProxy() : isClerkConfigured ? buildMisconfiguredProxy() : cookieProxy`), and the half-configured state fails closed rather than pairing real sign-in UI with the unsigned `userRole` cookie. That is exactly the posture a portal for minors needs.

Two edits:

1. In `lib/auth-config.ts`, `dashboardRedirectPath()` gains a `/workspace` rule and the `/dashboard/iec` rule is renamed. Keep the function pure and node-tested — it is the only place the gate rules live, and both proxy branches share it.
2. `apiAccessDeniedStatus()` gains `/api/inference` (any signed-in non-guest) and `/api/operator/**` (operator only). Note the existing normalisation: an unknown role string parses to `guest` via `parseUserRole()` and gets 401; a known-but-wrong role gets 403. Preserve that distinction.

Do **not** move authorisation into the proxy. The existing comment is correct and load-bearing: the proxy gate is defense in depth, and every handler re-verifies via `getServerIdentity()`.

### Layer 2 — Identity

**Reuse `lib/auth-server.ts` verbatim.** `getServerIdentity()` returns `ServerIdentity | null`, importing `@clerk/nextjs/server` dynamically and only when configured, so a zero-env deployment never loads Clerk. `identityFromClerkAuth()` is the pure, node-testable core. `getClerkSessionToken()` supplies the bearer token for RLS-scoped queries.

The role vocabulary changes: `UserRole` in `lib/types.ts` becomes `'guest' | 'participant' | 'instructor' | 'operator'`. Keep `parseUserRole()` and its "unknown parses to guest" contract — several security properties depend on it.

Keep the fail-closed default in `roleFromClerkMetadata()`: a signed-in user with no recognised role claim reads as the *least-privileged authenticated role*, not as an operator.

### Layer 3 — Handler plumbing

**Reuse `lib/api-server.ts` wholesale.** It already provides every primitive the portal needs:

```ts
isServerBoundaryActive          // Clerk-configured AND Supabase-configured
ApiOutcome { status, body }     // handlers return data, not Responses
ApiDeps { identity, db }        // injected deps → unit-testable with a mocked client
apiJson(outcome)                // ApiOutcome → Response
identityDeniedOutcome(id, roles)// 401 absent / 403 wrong role
resolveAppUserId(db, clerkId)   // Clerk sub → public.users.id, null when unprovisioned
unprovisionedOutcome()          // 403 for a valid session with no users row
boundaryInactiveOutcome()       // 503 for demo/half-configured deployments
readJsonBody(request)           // null on malformed/non-object bodies
logServerError(context, cause)  // server-side detail; response bodies stay generic
```

`logServerError()` deserves emphasis: the existing rule is that raw PostgREST errors leak table, column and constraint names to authenticated callers, so specifics go to the server log and the caller gets a generic message. Under N-1 this rule tightens — the server log must not carry prompt text either.

The route-handler files stay thin wrappers, matching the existing convention exactly (`app/api/admin/release-gate/release/route.ts` is four lines delegating to `handleGateActionRequest`; `app/api/corrections/route.ts` delegates to `handleCorrectionRequest`; `app/api/admin/deliveries/send/route.ts` delegates to `handleSendDeliveryRequest`). New domain logic goes in `lib/inference-server.ts`, `lib/quota-server.ts`, `lib/moderation-server.ts`, `lib/roster-server.ts`.

### Layer 4 — Data

**Reuse the migration patterns in `supabase/migrations/`, not the tables.** What transfers:

- The `private` schema helper seam: `private.clerk_user_id()` reads `request.jwt.claims` directly (works on Supabase *and* plain Postgres), `private.app_user_id()` and `private.app_role()` are `security definer` and return `NULL` when unmapped, `private.is_admin()` gates operator policies.
- `private.raise_append_only()` as a `before update or delete` trigger — the enforcement mechanism for the safety-event log.
- `private.set_updated_at()`.
- The default-deny grant posture: `alter table ... enable row level security; revoke all on table ... from anon;` then explicit grants to `authenticated` / `service_role`.
- Text primary keys, so fixtures and localStorage ids migrate id-stably.
- The `seq bigint generated always as identity` tie-breaker used in `consent_audit` — needed anywhere "latest row wins" must be deterministic within a single timestamp.

Two clients, from `lib/supabase-server.ts`: `createUserScopedServerClient(token)` (anon key + the caller's Clerk token, RLS enforced) is the default; `createServiceRoleServerClient()` (bypasses RLS) is reserved for the roster writer, exactly as `users-role-server.ts` reserves it today for the `users.role` writer. Both use the `NO_COOKIES` / `NO_SESSION_AUTH` options — Clerk owns identity, no Supabase Auth session exists.

### Layer 5 — Model access

**Reuse `lib/pipeline/adapters/llm.ts` as the base, extend it.** It already gives you the failover chain the portal needs: `OllamaAdapter` → `OpenAICompatAdapter` → `AnthropicAdapter` → `MockLLMAdapter`, selected by `createLLMAdapter()` with `UPSKILL_OFFLINE=1` overriding everything. The security hygiene is already right and must be preserved: `assertSafeApiKey()` rejects control characters in keys before Undici can echo them into an error, `redirect: 'error'` prevents a misconfigured base URL from forwarding `x-api-key` to an arbitrary host, `parseJsonBody()` avoids V8's `SyntaxError` embedding a body snippet, and error messages carry provider + status only.

What is missing and must be added is documented in `docs/OLLAMA-NIGHTWORK-DASHBOARDS.md` §1, gap 1 — see §6 below.

The layering decision: `createLLMAdapter()` stays a *provider factory*. The *routing policy* (which provider, under what conditions, with what disclosure) is a new module `lib/model-router.ts` that composes adapters. Do not fold routing into the factory; the factory's precedence rules are unit-tested and doing double duty would make both harder to reason about.

### Layer 6 — Presentation

Reuse the shells and primitives: `AppSidebar`, `RoleGate`, `StatusBadge`, and `components/ui/*`. The participant workspace is one route with a composer, a transcript pane backed by `sessionStorage`, a persistent backend-disclosure badge, and a quota meter. The operator console is one route with a cohort table and a safety-event summary.

---

## 4. Data model

Everything the portal stores. The schema is deliberately small and the omissions are the point.

```sql
-- 2026xxxx_portal_identity.sql
-- Reuses the private.* helper seam from
-- supabase/migrations/20260714100000_identity_and_rls_helpers.sql verbatim:
-- clerk_user_id(), app_user_id(), app_role(), is_admin(),
-- raise_append_only(), set_updated_at().

-- ---------------------------------------------------------------------------
-- cohorts — the unit of policy. audience is load-bearing (N-2).
-- ---------------------------------------------------------------------------
create table public.cohorts (
  id                text primary key default gen_random_uuid()::text
                      check (length(id) > 0),
  name              text not null check (length(trim(name)) > 0),
  -- 'minor' forces strict moderation, forbids cloud fallback, pins the
  -- strict system-prompt profile. Enforced in app code AND by the
  -- cohort_no_cloud_for_minors check below.
  audience          text not null check (audience in ('adult', 'minor')),
  -- Operator kill switch (F-8). Effective on the next request; no session
  -- teardown is attempted.
  status            text not null default 'active'
                      check (status in ('active', 'suspended', 'ended')),
  -- Routing policy, resolved per request in lib/model-router.ts.
  allow_cloud_fallback  boolean not null default false,
  model_profile     text not null default 'default'
                      check (model_profile in ('default', 'strict', 'agentic')),
  -- Quota defaults inherited by participants at enrolment.
  default_requests_per_day  integer not null default 120 check (default_requests_per_day > 0),
  default_tokens_per_day    integer not null default 400000 check (default_tokens_per_day > 0),
  starts_on         date,
  ends_on           date,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  -- A minor cohort can never be configured to reach a cloud provider.
  constraint cohort_no_cloud_for_minors
    check (audience <> 'minor' or allow_cloud_fallback = false)
);

create trigger cohorts_set_updated_at
  before update on public.cohorts
  for each row execute function private.set_updated_at();

-- ---------------------------------------------------------------------------
-- participants — the roster. One row per person per cohort.
-- Deliberately thin: no address, no age, no guardian record, no notes.
-- ---------------------------------------------------------------------------
create table public.participants (
  id              text primary key default gen_random_uuid()::text
                    check (length(id) > 0),
  cohort_id       text not null references public.cohorts (id) on delete restrict,
  -- FK to the identity mapping table carried over from
  -- 20260714100000_identity_and_rls_helpers.sql. NULL until first sign-in
  -- (the operator enrols by email before a Clerk identity exists).
  user_id         text references public.users (id),
  -- Enrolment address. The ONLY personal datum the portal holds.
  email           text not null check (position('@' in email) > 1),
  display_name    text,
  status          text not null default 'invited'
                    check (status in ('invited', 'active', 'suspended', 'removed')),
  -- Per-participant overrides; NULL inherits the cohort default.
  requests_per_day  integer check (requests_per_day > 0),
  tokens_per_day    integer check (tokens_per_day > 0),
  enrolled_at     timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (cohort_id, email)
);

create index participants_cohort_idx on public.participants (cohort_id, status);
create index participants_user_idx   on public.participants (user_id);

create trigger participants_set_updated_at
  before update on public.participants
  for each row execute function private.set_updated_at();

-- ---------------------------------------------------------------------------
-- quota_counters — one row per participant per UTC window. Mutable by
-- design (this is a counter, not an audit record).
--
-- Reset is implicit: a new window_start yields a new row. There is no cron
-- job and nothing to sweep (N-5). Old rows are the usage history; prune
-- with a single DELETE when it ever matters.
-- ---------------------------------------------------------------------------
create table public.quota_counters (
  participant_id  text not null references public.participants (id) on delete cascade,
  -- Start of the UTC day (or hour, for burst windows). Compound PK makes the
  -- upsert idempotent and lock-free under concurrency.
  window_start    timestamptz not null,
  window_kind     text not null check (window_kind in ('day', 'hour')),
  requests_used   integer not null default 0 check (requests_used >= 0),
  tokens_used     bigint  not null default 0 check (tokens_used  >= 0),
  updated_at      timestamptz not null default now(),
  primary key (participant_id, window_kind, window_start)
);

-- ---------------------------------------------------------------------------
-- safety_events — APPEND-ONLY, CONTENT-FREE, and IDENTIFIED (not pseudonymous).
-- CORRECTION AFTER REVIEW: an earlier draft labelled this table "pseudonymous". It is not.
-- participant_id is a direct FK to participants, which holds an email, so one join yields
-- "this named person tripped self_harm at 14:32". A self_harm category is an inference about
-- mental health and is arguably Art. 9 special-category data. Combined with the append-only
-- trigger and ON DELETE RESTRICT, the row can never be deleted and the participant can never
-- be erased -- i.e. no Art. 17 path. BEFORE this table is created for any EU cohort it needs:
-- a defined retention period with automatic purge, an erasure path, a documented lawful basis,
-- and an Art. 9 analysis. For a minor cohort in the EU this is the most serious open defect in
-- this specification.
--
-- This table is the compliance artefact. It proves a moderation stage exists
-- and fired, and it proves — by the absence of any text column — that no
-- prompt or completion was retained (N-1, N-9).
--
-- Deliberately absent, and these omissions are the specification:
--   * no prompt text, no completion text, no excerpt, no "matched span"
--   * no hash of the content (a hash of a short prompt is reversible by
--     dictionary attack and would defeat the whole claim)
--   * no IP address, no user agent, no device identifier
--   * no free-text operator note field (it would become a content column
--     by convention within a month)
-- What an operator gets is a COUNT BY CATEGORY. That is enough to decide
-- whether to speak to someone, and it is all the portal will ever provide.
-- ---------------------------------------------------------------------------
create table public.safety_events (
  id              uuid primary key default gen_random_uuid(),
  participant_id  text not null references public.participants (id) on delete restrict,
  cohort_id       text not null references public.cohorts (id) on delete restrict,
  occurred_at     timestamptz not null default now(),
  -- Monotonic tie-breaker, same pattern as consent_audit.seq in
  -- 20260714100400_consent_audit_and_ops.sql: uuid PKs do not sort by
  -- insertion, so ordering within one instant needs this.
  seq             bigint generated always as identity,
  stage           text not null check (stage in ('input', 'output')),
  -- Which layer fired. 'deterministic' = the wordlist/pattern filter,
  -- 'classifier' = the guard model (see §7).
  detector        text not null check (detector in ('deterministic', 'classifier')),
  category        text not null check (category in (
                    'self_harm', 'sexual_minors', 'violence', 'harassment',
                    'illegal', 'pii_shape', 'prompt_injection', 'other')),
  action          text not null check (action in ('blocked', 'flagged', 'redacted')),
  -- Classifier confidence, when the detector produced one. No text.
  score           numeric(4,3) check (score is null or (score >= 0 and score <= 1))
);

create index safety_events_cohort_idx
  on public.safety_events (cohort_id, occurred_at, seq);
create index safety_events_participant_idx
  on public.safety_events (participant_id, occurred_at, seq);

create trigger safety_events_append_only
  before update or delete on public.safety_events
  for each row execute function private.raise_append_only();
```

### RLS posture

Identical in shape to the existing migrations: enable RLS on every table, revoke from `anon`, grant narrowly, then write explicit policies. Default deny.

```sql
alter table public.cohorts        enable row level security;
alter table public.participants   enable row level security;
alter table public.quota_counters enable row level security;
alter table public.safety_events  enable row level security;

revoke all on table public.cohorts        from anon, authenticated;
revoke all on table public.participants   from anon, authenticated;
revoke all on table public.quota_counters from anon, authenticated;
revoke all on table public.safety_events  from anon, authenticated;

grant select                 on table public.cohorts        to authenticated;
grant select                 on table public.participants   to authenticated;
grant select                 on table public.quota_counters to authenticated;
grant select, insert         on table public.safety_events  to authenticated;
grant select, insert, update on table public.cohorts, public.participants,
                                public.quota_counters, public.safety_events
                             to service_role;

-- Helper: is the caller a participant of this cohort? Mirrors the
-- private.owns_client() / private.is_client_self() pattern from
-- 20260714100100_clients_and_generations.sql.
create or replace function private.in_cohort(target_cohort_id text)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.participants p
    where p.cohort_id = target_cohort_id
      and p.user_id   = private.app_user_id()
      and p.status    = 'active'
  );
$$;

revoke all on function private.in_cohort(text) from public;
grant execute on function private.in_cohort(text) to authenticated, service_role;

-- A participant sees their own cohort's name/status and nothing else.
create policy cohorts_select_own
  on public.cohorts for select to authenticated
  using ((select private.in_cohort(id)));

create policy cohorts_select_operator
  on public.cohorts for select to authenticated
  using ((select private.is_admin()));

-- A participant sees their OWN participant row. Not their classmates'.
create policy participants_select_self
  on public.participants for select to authenticated
  using (user_id = (select private.app_user_id()));

create policy participants_select_operator
  on public.participants for select to authenticated
  using ((select private.is_admin()));

-- A participant reads their own quota (the meter in the UI). Writes go
-- through the service-role path only — a participant must never be able to
-- decrement their own counter.
create policy quota_select_self
  on public.quota_counters for select to authenticated
  using (participant_id in (
    select p.id from public.participants p
    where p.user_id = (select private.app_user_id())
  ));

-- Safety events: operator-read only. A participant cannot enumerate what
-- tripped, which would otherwise be a filter-probing oracle.
create policy safety_events_select_operator
  on public.safety_events for select to authenticated
  using ((select private.is_admin()));
```

**Note there is no `conversations` table, no `messages` table, no `prompts` table, and no `completions` table.** That is not an omission to be filled in a later iteration. Adding one inverts the product's only defensible claim.

---

## 5. API surface

Conventions inherited from the repo: route files are thin wrappers; domain logic returns `ApiOutcome` and is rendered by `apiJson()`; identity is verified inside the handler via `getServerIdentity()` regardless of what the proxy did; all handlers answer **503** when `isServerBoundaryActive` is false.

### `POST /api/inference`

**Auth:** any active participant, instructor, or operator with an active cohort membership.

```ts
// Request
interface InferenceRequest {
  cohortId: string;
  /** The user turn. Never persisted. */
  input: string;
  /** Prior turns, supplied by the CLIENT from sessionStorage. The server
   *  holds no history — this is what makes N-1 achievable rather than
   *  aspirational. Bounded server-side (see 413). */
  history?: Array<{ role: 'user' | 'assistant'; content: string }>;
  /** Requested capability tier. The router may downgrade and will say so. */
  tier?: 'chat' | 'build';
}

// Response 200
interface InferenceResponse {
  output: string;
  /** F-6 disclosure. Rendered as a persistent badge, not a tooltip. */
  route: {
    backend: 'local' | 'cloud' | 'mock';
    /** e.g. 'qwen3.8:27b' — the participant is told what answered them. */
    model: string;
    /** Present when the router did not honour the requested tier. */
    downgradedFrom?: 'build';
    /** Human-readable, shown verbatim in the UI. */
    notice?: string;
  };
  usage: {
    promptTokens: number;
    completionTokens: number;
    requestsRemaining: number;
    tokensRemaining: number;
    windowResetsAt: string; // ISO
  };
}
```

| Status | Meaning | Body |
|---|---|---|
| 200 | Generated | `InferenceResponse` |
| 400 | Malformed body (`readJsonBody()` returned null, missing `cohortId`/`input`) | `{ error }` |
| 401 | No verified identity — `unauthenticatedOutcome()` | `{ error }` |
| 403 | Not a participant of that cohort, or no `users` row — `unprovisionedOutcome()` | `{ error }` |
| 413 | `history` or `input` exceeds the context budget | `{ error, maxTokens }` |
| 422 | Moderation blocked the request or the completion | `{ error, stage, category }` — **no echo of the offending text** |
| 423 | Cohort or participant `status` is `suspended`/`ended` | `{ error }` |
| 429 | Quota exhausted | `{ error, windowResetsAt }` + `Retry-After` header |
| 503 | Server boundary inactive, **or** all backends unreachable and the cohort forbids fallback, **or** the queue is full | `{ error, retryAfterSeconds }` + `Retry-After` |
| 504 | Backend accepted but exceeded the request deadline | `{ error }` |

Two distinctions that matter and are easy to get wrong:

- **429 is quota, 503 is congestion.** They demand different client behaviour: 429 means stop until `windowResetsAt`; 503 means the same request may succeed shortly. Conflating them is what turns a busy minute into a retry storm (§8).
- **422 never echoes content.** The response says a category fired. It does not quote the trigger, because quoting it both leaks the filter's internals and re-introduces the content into a log the moment anyone tees the response.

### `GET /api/inference/health`

**Auth:** any signed-in user. Cheap, cached ~10s.

```ts
interface HealthResponse {
  backends: Array<{
    name: 'local' | 'cloud';
    reachable: boolean;
    /** ms, from the last probe. */
    latencyMs?: number;
    /** Model ids reported resident by `ollama ps`, when local. */
    loaded?: string[];
  }>;
  degraded: boolean;
  notice?: string;
}
```

Drives the banner in N-4. The probe is a `GET {OLLAMA_BASE_URL}/api/tags` with the existing `httpTimeoutSignal()` from `lib/pipeline/http-timeout.ts` — a real request, not a TCP connect, because a reachable Ollama with no model loaded is a different failure than an unreachable host.

### `GET /api/participant/quota`

**Auth:** the participant themself. Returns the same `usage` block as `InferenceResponse` without making a model call, so the meter can refresh on focus.

### `POST /api/operator/cohorts`

**Auth:** operator only. Service-role path (mirrors `handleUsersRoleRequest` in `lib/users-role-server.ts`, the only existing service-role writer). Creates a cohort; body is the mutable subset of the `cohorts` row. Rejects `audience: 'minor'` with `allow_cloud_fallback: true` at 400 before the database check fires, so the error is legible.

### `POST /api/operator/roster`

**Auth:** operator only. Service-role. Bulk enrol: `{ cohortId, emails: string[] }`. Idempotent on `(cohort_id, email)`. Returns per-email `created | already_enrolled | invalid`. This is the one call that has to be pleasant to use, because it is the only thing the operator does routinely (N-5).

### `POST /api/operator/participants/status`

**Auth:** operator only. Service-role. `{ participantId | cohortId, status }`. The kill switch (F-8). Takes effect on the next request; no attempt is made to terminate an in-flight generation.

### `GET /api/operator/overview`

**Auth:** operator only. One call backing the whole console (F-7): per-cohort participant counts by status, today's quota consumption, safety-event counts grouped by `(category, action)`, and backend health. No per-event detail is returned beyond the grouped counts — the console cannot drill into an individual event, because there is nothing to drill into.

---

## 6. Model routing

### Policy

Routing is a pure function of cohort configuration and backend health. Put it in `lib/model-router.ts` and unit-test it with a fake health oracle; do not entangle it with `createLLMAdapter()`.

```ts
export type Backend = 'local' | 'cloud' | 'mock';
export type Tier = 'chat' | 'build';

export interface RouteDecision {
  backend: Backend;
  model: string;
  downgradedFrom?: Tier;
  notice?: string;
  /** Ollama/llama.cpp options for this hop (see below). */
  options: LocalModelOptions;
}

export function decideRoute(input: {
  tier: Tier;
  audience: 'adult' | 'minor';
  allowCloudFallback: boolean;
  localReachable: boolean;
  localLoaded: string[];
  cloudConfigured: boolean;
}): RouteDecision | null;   // null ⇒ refuse (handler answers 503)
```

Ladder, in order:

1. **Local, requested tier.** `tier: 'build'` → the 27B; `tier: 'chat'` → the 8B. Always preferred: zero marginal cost, no third-party processor, no cross-border transfer.
2. **Local, downgraded tier.** If the 27B is not resident but the 8B is, serve `chat` and set `downgradedFrom: 'build'` with a notice. A degraded answer beats an error (N-4).
3. **Cloud.** Only if `allowCloudFallback` **and** `audience === 'adult'` **and** a cloud provider is configured. The schema's `cohort_no_cloud_for_minors` constraint means this branch is unreachable for minor cohorts even if the code were wrong — that redundancy is deliberate.
4. **Refuse.** Return null. The handler answers 503 with `retryAfterSeconds`, the UI shows the read-only banner. **Never silently fall back to `MockLLMAdapter` in production.** The mock exists so tests and local dev never hard-fail; serving its output to a paying participant as if it were a model would be a lie. Gate it behind `UPSKILL_OFFLINE=1`, which `createLLMAdapter()` already treats as overriding everything.

### Disclosure

Not optional and not buried. Three surfaces:

- `route.backend` and `route.model` in every response body.
- An `x-model-route: local|cloud|mock` response header, so a curl in a smoke test can assert it.
- A persistent badge in the composer UI — "answering locally (qwen3.8:27b)" / "answering via cloud (disclosed)" — not a toast that disappears.

For a B2B engagement the whole pitch is that material stays on the box. A participant must be able to see, at a glance and at any moment, whether that is currently true.

### Required Ollama options

`docs/OLLAMA-NIGHTWORK-DASHBOARDS.md` §1 audits Ollama's defaults and names the exact gap in this codebase: the `OllamaAdapter` request body in `lib/pipeline/adapters/llm.ts` sends only `temperature` and `num_predict` — no `num_ctx`, no `keep_alive`, no `format`. With a default context of 4,096 tokens, **prompts are silently truncated with no error**. For a chat turn carrying client-supplied history that is a correctness bug, not a tuning issue: the model simply never sees the head of the conversation, and nothing in the response indicates it.

Extend `OllamaAdapterOptions` and the request body:

```ts
export interface LocalModelOptions {
  /** REQUIRED. Never inherit the 4096 default. */
  numCtx: number;
  /** '-1' pins the model resident; '30m' for interactive windows.
   *  A 27B load costs minutes — unloading between turns is fatal to UX. */
  keepAlive: string;
  /** Cap runaway generations. */
  numPredict: number;
  temperature: number;
  /** JSON Schema for constrained output. Used by moderation and by any
   *  structured extraction; unset for prose. */
  format?: object;
  /** Reasoning models default to thinking ON. For moderation and bulk
   *  triage that is thousands of wasted hidden tokens per call. */
  think?: boolean;
}
```

Serving posture, per the same document's recommended systemd block:

```ini
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=11.0.0"
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_CONTEXT_LENGTH=32768"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_NUM_PARALLEL=2"
```

`OLLAMA_MAX_LOADED_MODELS=2` is what makes the two-model design possible: a build model and a small guard/chat model both resident. `OLLAMA_KV_CACHE_TYPE=q8_0` roughly halves KV-cache memory, which is what buys the context length back. `OLLAMA_HOST=0.0.0.0` binds beyond loopback — acceptable **only** because Tailscale ACLs are the firewall and no inbound port is open on the residential line (N-7).

Note `HSA_OVERRIDE_GFX_VERSION=11.0.0` is the value currently in the repo's `CLAUDE.md`; that file also records an unverified note that community guidance for gfx1151 suggests `11.5.1`. Test both on this unit (§12).

### llama.cpp equivalents

If `llama-server` replaces Ollama (worth considering for the build tier, where slot control and prefix caching matter):

| Concern | Flag |
|---|---|
| Context per slot | `-c 32768` — note this is divided across `--parallel` slots |
| Concurrency | `-np 4` |
| KV cache quantisation | `--cache-type-k q8_0 --cache-type-v q8_0` |
| Flash attention | `-fa` (prerequisite for KV quantisation) |
| GPU offload | `-ngl 999` |
| Structured output | `--json-schema` per request, or a GBNF grammar |
| Prefix cache reuse | slot reuse is automatic per slot; there is **no routing by identity** |

That last row is the trap. `docs/CLASSROOM-BUILD-LAB.md` §5 works the arithmetic: prefill is compute-bound and does not amortise across a batch, with order-of-magnitude ceilings around **800 prompt-tokens/sec for an 8B, 400 for a 14B, 200 for a 27B**, and a measured **266 for Qwen3.5-122B-A10B**. Thirty participants pasting a 6,000-token file every three minutes is roughly **1,000 prompt-tokens/sec of demand** — over the 27B's ceiling by 5×. Prefix caching turns a warm follow-up into a ~300-token delta instead of a cold 6,000, but only if the next turn lands on the slot still holding that participant's state, and **session-affinity routing is custom middleware, not configuration**. With ~10 slots against 30 people, only a third of the class can be warm.

**Design consequence, stated plainly: cap a synchronous cohort at 8–12 participants.** That is not a soft target; it is the number the hardware supports. Sell the small cohort as the product.

---

## 7. Moderation

### Position in the request path

Between quota and the queue on the way in (step 5 of the handler in §3), and between generation and the response on the way out (step 8). Input moderation runs *after* the quota check so that a blocked request still costs the participant a request — otherwise probing the filter is free and unlimited.

### What runs

**Layer 1 — deterministic filter.** Compiled patterns, no model, sub-millisecond, always on, cannot be disabled in any cohort. It covers the categories where a false negative is unacceptable and a regex is genuinely sufficient: explicit self-harm phrasing, sexual content involving minors, and PII *shapes* (email, phone, national-ID formats) which are flagged rather than blocked — participants paste their own email constantly and blocking would be useless. Also detects the obvious prompt-injection preambles ("ignore previous instructions", "you are now"). This layer exists because a classifier can be slow, wrong, or down, and there must be a floor that fires regardless.

**Layer 2 — ML classifier.** A small guard model (Llama Guard-class, ~8B, Q4) called with `format` set to a JSON schema, `think: false`, `num_predict` capped at ~64, and a short `num_ctx`. It returns `{ flagged, category, score }`. It catches what patterns cannot: intent, context, obfuscation.

Both layers run on input. On output, layer 1 runs always; layer 2 runs always in `minor` cohorts and is sampled in `adult` cohorts (see the cost discussion below).

### What happens on a hit

| Detector | Category | Action | Participant sees |
|---|---|---|---|
| Deterministic | `sexual_minors`, `self_harm` | `blocked` | 422 with a category-specific message and, for self-harm, a signposting line with a helpline. No model call is made. |
| Deterministic | `pii_shape` | `flagged` | Nothing. The request proceeds. The event is recorded. |
| Deterministic | `prompt_injection` | `flagged` | Nothing. Recorded; the system prompt is server-side anyway (`docs/CLASSROOM-BUILD-LAB.md` §4). |
| Classifier | any, `score ≥ block threshold` | `blocked` | 422, generic category message. |
| Classifier | any, `flag threshold ≤ score < block` | `flagged` | Nothing. Recorded. |
| Output stage | any block | `blocked` | 422; the completion is discarded and never rendered. The tokens still count against quota — they were generated. |

Every hit writes one `safety_events` row: ids, timestamp, stage, detector, category, action, score. No text. The operator console shows counts by category; there is no drill-down, because there is nothing stored to drill into. If an operator needs to know what someone actually typed, the answer is that the portal cannot tell them and was built that way on purpose.

Thresholds live in code, not in the database. An operator with a slider will eventually turn it down.

### The honest performance cost

Moderation is not free, and on this specific machine it is less free than it looks.

**A guard model on the CPU is not free on a unified-memory machine.** The Strix Halo's 128GB LPDDR5X is shared between CPU and GPU — they draw from the same memory controller and the same bandwidth budget. Running the guard on CPU cores to "keep the GPU free" does not sidestep the bottleneck; LLM inference is memory-bandwidth-bound, so a CPU-side guard competes directly with GPU decode for the resource that is actually scarce. It converts a GPU-scheduling problem into a bandwidth-contention problem and makes the main generation slower while the guard itself runs badly. Do not do it.

The right approach is to keep the guard resident on the GPU as the second of two loaded models (`OLLAMA_MAX_LOADED_MODELS=2`) and pay the prefill cost explicitly:

- Guard prefill at roughly 800 prompt-tokens/sec for an 8B (`docs/CLASSROOM-BUILD-LAB.md` §5). A 600-token turn plus a short guard preamble ≈ **0.8–1.0s**. Decode is ~20 tokens of JSON, negligible.
- Input plus output moderation ≈ **1.5–2.0s added per turn**, before the main model has generated anything.
- On a 12-person cohort where the main model is already near its prefill ceiling, that guard traffic is *additional prefill on the same GPU*. Budget it as roughly a 15–25% reduction in effective cohort capacity.

Mitigations, in order of value:

1. **Moderate the new user turn on input — and do not trust client-supplied history.** An earlier draft said "History was already moderated when it was new" and used that to skip re-checking it. **That is false and it is a bypass:** history arrives in the request body from the browser, so a participant can fabricate or edit it from a console. Either the server holds conversation state (preferred, and it costs nothing since no content is persisted beyond the request), or every turn sent to the model is moderated regardless of which role claims to have authored it. Until one of those is true, every minor-safety claim in N-2 is defeatable from a browser console.
2. **Sample output moderation in adult cohorts.** Layer 1 always; layer 2 on the first N turns of a session plus a random sample thereafter, and always after any prior flag for that participant in that session. In `minor` cohorts, no sampling.
3. **Run input moderation concurrently with queue admission**, not before it — the guard call and the wait for a main-model slot overlap.
4. **Cache deterministic-filter compilation at module load.** Obvious, and easy to get wrong in a serverless environment where the module reloads.

State it in the sales conversation too: moderation costs about two seconds a turn and about a fifth of cohort capacity. That is the price of running a portal minors can use, and it is worth paying.

---

## 8. Quota and abuse control

### Limits

Three windows, all enforced in `lib/quota-server.ts` before any model call:

| Limit | Default | Rationale |
|---|---|---|
| Requests per day | 120 | Generous for a 3-hour session; catches a runaway loop within minutes. |
| Tokens per day | 400,000 | The real cost control. A participant pasting whole files hits this well before the request count. |
| Requests per hour | 40 | Burst containment — the daily limit alone lets one person consume everything in ten minutes. |

Per-participant overrides (`participants.requests_per_day`, `participants.tokens_per_day`) inherit from the cohort when NULL.

### Accounting

Two-phase, because token counts are unknown until the response arrives:

1. **Before the call:** atomically increment `requests_used` for the day and hour windows. Reject with 429 if the post-increment value exceeds the limit. Use `insert ... on conflict (participant_id, window_kind, window_start) do update set requests_used = quota_counters.requests_used + 1 returning *` — one statement, no read-modify-write race, no advisory lock.
2. **After the call:** increment `tokens_used` by the actual usage. A request that pushes a participant over the token limit is *completed and then counted*; the next request is refused. Overshooting by one request is acceptable; refusing to serve a request whose cost you cannot yet know is not.

If the model call throws, the request increment stands. Failed requests consume quota, or a failing loop is free.

### The 429-amplification trap

**A gateway's per-key parallel limit typically returns HTTP 429 rather than queueing.** This is the failure mode to design against explicitly, and it is why quota and congestion must be different status codes.

The pathology: the backend saturates, the gateway or proxy refuses concurrent requests above N with 429, the client sees 429 and retries, retries arrive while the backend is still saturated and are refused again, and the retry traffic itself becomes the load keeping the system saturated. Naive client-side retry logic — including the retry built into most SDKs and into `fetch` wrappers people copy from blog posts — turns a transient two-second queue into a sustained outage. It is worse in a classroom, where thirty people hit "send" within the same ten seconds because the instructor just said "try it now".

The fix is **real queueing in the route handler**, not a smarter retry:

```ts
// lib/inference-queue.ts — module-scoped, single process.
export interface QueueOptions {
  /** Concurrent in-flight model calls. Match OLLAMA_NUM_PARALLEL. */
  maxConcurrent: number;
  /** Requests allowed to WAIT. Beyond this, refuse immediately. */
  maxQueued: number;
  /** How long a request may wait before being refused. */
  maxWaitMs: number;
}

/**
 * Admit a request into the model-call slot pool, or refuse.
 *
 * Returns a release() the caller MUST invoke in a finally block.
 * Refusal is `null` — the handler answers 503 with Retry-After, which
 * is semantically "come back", distinct from 429's "you are out of budget".
 *
 * Bounded on BOTH depth and wait: an unbounded queue converts a capacity
 * problem into a latency problem and then into a timeout problem, which
 * looks to the participant exactly like the 429 storm it replaced.
 */
export async function admit(o: QueueOptions): Promise<(() => void) | null>;
```

Rules that make this work:

- **`Retry-After` on every 429 and 503.** Both are honoured by well-behaved clients and are the only instruction the server can give.
- **The portal's own client never auto-retries a 429.** It shows the quota state and the reset time. Only 503 is retried, once, with jitter.
- **`maxConcurrent` matches the backend's real parallelism** (`OLLAMA_NUM_PARALLEL`, or `-np` on `llama-server`). Setting it higher just moves the queue somewhere it cannot be measured.
- **Queue depth is visible** in `/api/inference/health` so a saturated moment is diagnosable after the fact without any logging of content.

Caveat, honestly: this queue is per-process. On a single-instance deployment (topology A or B, §9) that is the whole system. On a horizontally scaled cloud deployment it is per-instance and the effective concurrency is `instances × maxConcurrent`. If topology C ever scales beyond one instance, the queue must move to a shared coordinator, and that is a real piece of work — a good reason to pin the cloud deployment to one instance for as long as possible.

### Other abuse controls

- **Input size cap** (413) before tokenisation, on raw bytes. Rejecting a 10MB paste should not require tokenising 10MB.
- **History cap.** `history` is client-supplied and therefore hostile. Truncate to the newest N turns fitting a token budget, server-side, and count the truncated total against the context budget — never trust a client-declared length.
- **No streaming in Phase 1–3.** Streaming complicates output moderation (you would be shipping unmoderated tokens and retracting them) and complicates queue accounting. Add it only after output moderation is proven, and then only with a buffer-and-flush strategy.

---

## 9. Deployment topologies

### (A) All-local — portal and model both on the Beelink

Next.js runs on the Beelink; Postgres runs on the Beelink; participants reach it over the LAN or over Tailscale.

**Fits:** a home or co-op cohort, a family deployment, a school-sited lab on an isolated segment.

| | |
|---|---|
| **For** | Nothing leaves the building. No hosting bill. No cross-border transfer question at all. Trivially fast — no WAN hop between portal and model. The strongest possible version of the privacy claim. |
| **Against** | Participants must be on the LAN or on your tailnet, which means "in the building" or "on a device you have configured" — a Chromebook you do not administer cannot join a tailnet. Single point of failure with no redundancy: one PSU, one disk, one residential line. You are the on-call engineer. No TLS-terminating CDN, so certificate handling is yours. |
| **Verdict** | The right answer for youth classes and family use, and the only topology that fully honours N-7 with zero caveats. |

### (B) Portal in the cloud, Beelink as a private backend

Next.js on Vercel or a small VPS; Postgres on Supabase; the model reached over Tailscale, outbound-initiated from the portal host to the Beelink.

**Fits:** a paid adult cohort with participants at home; a B2B workshop where the client's people join from their own network.

| | |
|---|---|
| **For** | Participants need only a browser and a link — no network configuration, works from a managed Chromebook anywhere (N-3). Real TLS, real uptime for the *portal*, so a Beelink outage degrades to cloud fallback (adult cohorts) or a read-only banner rather than a dead URL. Still no inbound port at the house (N-7). |
| **Against** | Two moving parts and a tunnel between them. Prompts transit the portal host, so the "nothing leaves the room" claim weakens to "nothing is retained anywhere and inference happens on our hardware" — true, but a longer sentence. If the portal is serverless, module-scoped state (the §8 queue, health cache) is per-instance; pin to one instance. Tailscale becomes a production dependency. |
| **Verdict** | **The default. Recommend this one.** It is the only topology that serves a remote paid cohort without asking participants to configure anything, and the failover story is genuinely graceful. |

### (C) Cloud-only, no Beelink

Portal in the cloud, model from a cloud provider via `OpenAICompatAdapter` or `AnthropicAdapter`.

**Fits:** a B2B pilot before the hardware story matters; any adult engagement where a client's own compliance posture already assumes a cloud vendor; the disaster-recovery configuration.

| | |
|---|---|
| **For** | Nothing to operate. Scales past any cohort size. Better models than the Beelink can run. Configuration-only: `LLM_PROVIDER=anthropic` plus a key, and `createLLMAdapter()` already handles it. |
| **Against** | Per-token cost, so quota moves from being a fairness mechanism to being a budget mechanism, and the numbers in §8 need re-deriving against a price. The privacy differentiator is gone entirely. Forbidden for `minor` cohorts by the `cohort_no_cloud_for_minors` constraint. |
| **Verdict** | Keep it configured and tested as the fallback leg — that is what makes N-4 real. Do not lead with it; it is the version of this product with no moat. |

**Runner-up to (B):** all-local (A) with Tailscale Funnel for remote participants. Rejected because it puts availability of the whole product on a residential line, and because Funnel's egress path is a third-party dependency that undercuts the very claim topology A exists to make.

---

## 10. Build sequence

Sized in evenings (≈2 hours each), not weeks. Every phase ends with something that works.

### Phase 1 — One cohort, end to end (3 evenings)

The least possible code that lets a real person use a real model through a real gate.

| Evening | Work |
|---|---|
| 1 | Fork `upskill-news-app`. Rename `UserRole` members in `lib/types.ts`. Update `dashboardRedirectPath()` and `apiAccessDeniedStatus()` in `lib/auth-config.ts` and their existing tests. Delete the IEC/edition routes and components. Verify `npm run build`, `npm run lint`, `npm run test` still pass. |
| 2 | `app/api/inference/route.ts` as a thin wrapper over a new `lib/inference-server.ts`, following the `handleGateActionRequest` shape exactly: `getServerIdentity()` → `identityDeniedOutcome()` → `readJsonBody()` → `createLLMAdapter()` → `apiJson()`. Extend `OllamaAdapter` with `numCtx` / `keepAlive` / `format` (the gap named in `docs/OLLAMA-NIGHTWORK-DASHBOARDS.md` §1). |
| 3 | The participant workspace: composer, `sessionStorage` transcript, backend-disclosure badge. `/api/inference/health` and the degradation banner. |

**Phase 1 has no database.** The roster is a hard-coded array of Clerk user ids in an environment variable; quota is in-memory per process. That is genuinely enough for one cohort of eight adults, and it defers the entire Supabase provisioning decision — which is still open in the source repo — by three weeks. Ship this, teach a session, then decide what the database needs to be.

### Phase 2 — Safety and fairness (3 evenings)

| Evening | Work |
|---|---|
| 4 | `lib/quota-server.ts`: three windows, in-memory. `lib/inference-queue.ts`: `admit()` with bounded depth and wait. 429 vs 503 with `Retry-After`, and a client that retries 503 only. |
| 5 | `lib/moderation-server.ts` layer 1 (deterministic). Wire input and output stages. 422 semantics with no content echo. |
| 6 | Layer 2 (guard model) with `format` + `think: false`. Measure the added latency on the real box and record the number. Decide the adult-cohort sampling rate from what you measure, not from this document. |

After Phase 2 the portal is safe enough for a minor cohort, still with no database.

### Phase 3 — Persistence and the operator console (3 evenings)

| Evening | Work |
|---|---|
| 7 | Apply the §4 migrations. Reuse `private.*` helpers verbatim. Add `tests/portal-migrations.test.ts` modelled on the existing `tests/supabase-migrations.test.ts`, asserting the posture: RLS enabled on every table, revoked from `anon`, append-only trigger present on `safety_events`, and — the one that matters — **no text column on `safety_events` other than the enumerated ones**. |
| 8 | `lib/roster-server.ts` + `/api/operator/cohorts`, `/api/operator/roster`, `/api/operator/participants/status`. Service-role path, mirroring `lib/users-role-server.ts`. Move quota to `quota_counters`. |
| 9 | `/api/operator/overview` and the console page. Extend `scripts/a11y-audit.mjs`'s route list; run `npm run a11y`. |

### Phase 4 — Whatever the first real cohort proved necessary (2–4 evenings)

Do not plan this now. Candidates in likely order: streaming with buffered output moderation, file paste-and-summarise, session-affinity routing for the build tier, per-cohort system prompts.

**Total to a portal that can run a paid adult cohort or a supervised youth class: nine evenings.** Phase 1 alone is three, and is independently useful.

---

## 11. Open technical questions

**Q1 (load-bearing). Can a 27B open-weights model reliably drive a multi-file agentic coding loop?**

Everything downstream depends on this. If yes, the participant deliverable is a real installable app and the portal is the differentiator. If no, the deliverable shrinks to single-file exercises, the "build your own app" promise is not honest, and the whole offer needs restating.

The failure mode is specific and is not about code quality on any single file: agentic loops fail on *state* — remembering which files exist, applying an edit to the right file, not re-creating a module it wrote twenty minutes ago, and recovering from a tool call that returned an error instead of looping on it.

**How to test it in an afternoon (about 3 hours):**

1. *(20 min)* Pull `qwen3.8:27b` on the Beelink. Set `OLLAMA_CONTEXT_LENGTH=32768`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_KEEP_ALIVE=-1`. Confirm with `ollama ps` what context the loaded model actually got — the requested value is not always the granted one.
2. *(10 min)* Point an existing agent harness at it rather than writing one. `ollama launch claude` (v0.15+) runs the Claude Code harness against a local model with no env-var setup; alternatively set `OLLAMA_HOST` to the Beelink's tailnet address from the Mac.
3. *(90 min)* Run three fixed tasks, each from an empty directory, each timed, with **no** human correction mid-run:
   - **T1 (scaffold):** "Create a static to-do PWA: `index.html`, `app.js`, `style.css`, `manifest.json`, `sw.js`. It must install and work offline." Five files, no dependencies, one cross-file contract (the service worker must cache the exact filenames it created).
   - **T2 (cross-file edit):** on T1's output — "Add a due date to each item, persist it, and show overdue items in red." Requires coordinated edits to three files it wrote itself.
   - **T3 (error recovery):** introduce a deliberate syntax error in `app.js`, then "the app is broken, fix it." Tests whether it reads the actual error or hallucinates a plausible different one.
4. *(30 min)* Score, strictly: does the artefact **run** (binary), how many turns, how many human interventions were needed to prevent a doom-loop, and — the diagnostic that predicts everything else — did it ever edit a file it had not previously read in that session?
5. *(30 min)* Run the identical three tasks against a frontier cloud model. You need the gap, not the absolute.

**Decision rule, set before running:** if T1 and T2 both produce a running artefact within 15 turns and fewer than 2 interventions, the build tier is viable on local hardware. If T1 passes but T2 does not, the honest product is guided single-file exercises with the model as an assistant rather than an agent. If T1 fails, the build tier requires cloud, which means adult cohorts only and a per-token cost line.

**Q2. What is the measured concurrent capacity of *this* Beelink?** The §6 prefill figures are order-of-magnitude, calibrated from a single measured anchor. Twelve simulated participants issuing a 6,000-token paste every three minutes for twenty minutes, measuring p50/p95 time-to-first-token, gives the real cohort cap. Until that number exists, every capacity statement in this document is an estimate.

**Q3. Does `HSA_OVERRIDE_GFX_VERSION=11.0.0` or `11.5.1` perform better on gfx1151?** Recorded as unverified in the source repo's `CLAUDE.md`. Two benchmark runs settle it.

**Q4. Is the guard model's added latency acceptable at cohort scale?** §7 budgets 1.5–2.0s per turn from an 8B prefill estimate. Measure it under concurrent load, not at idle — that is where contention shows.

**Q5. Is Ollama or `llama-server` the right server for the build tier?** Ollama is easier and has `format` and model management; `llama-server` gives explicit slot control and prefix-cache behaviour, which matters more as sessions get long. Answer after Q1 and Q2.

**Q6. Does a Chromebook under enterprise management reach a Tailscale-connected origin?** Topology B assumes it does not need to (the *portal* is public; only the portal reaches the tailnet). Verify on an actual managed device before promising remote access, because managed-device network policy is the constraint most likely to surprise you.

**Q7. Where does the queue live if topology C ever scales past one instance?** §8's queue is module-scoped and per-process. This is fine today and a real piece of work the day it is not.

---

## What to verify before acting

| Claim | Method | Cost |
|---|---|---|
| A 27B can drive an agentic loop | The T1/T2/T3 protocol in Q1, with the decision rule fixed in advance | one afternoon |
| Cohort capacity is 8–12, not 30 | Twelve simulated participants, 6,000-token pastes every 3 min for 20 min, record p50/p95 TTFT | 1 evening |
| Ollama actually granted the context you asked for | `ollama ps` after load — compare against `OLLAMA_CONTEXT_LENGTH`; the request is a hint, not a guarantee | 5 min |
| The correct gfx override for gfx1151 | Benchmark identical prompts under `11.0.0` and `11.5.1` | 30 min |
| Guard latency at load | Instrument the moderation call; measure at idle and at 8 concurrent | 1 evening |
| No prompt text reaches storage | `grep -rn "prompt\|input\|content" supabase/migrations/` over the new files should return only column *names* in `check` constraints, never a text column; plus a test asserting no unexpected text column on `safety_events` | 20 min |
| Nothing listens inbound at the house | `nmap` the residential WAN IP from outside; expect no open ports | 10 min |
| Managed Chromebook reaches the portal | Borrow one; load the origin; sign in | 1 hour |
| The 429/503 distinction actually holds | Drive 3× `maxConcurrent` concurrent requests; assert 503 + `Retry-After` for congestion and 429 only for exhausted quota | 30 min |
| The existing suite still passes after the fork | `npm run build && npm run lint && npm run test` (672 tests, 54 files as of the source repo) | 10 min |

---

## Sources

**Codebase (primary — every module named in this spec was read):**

- [`proxy.ts`](/home/user/upskill-news-app/proxy.ts) — network boundary, three-branch selection, fail-closed misconfigured branch
- [`lib/auth-config.ts`](/home/user/upskill-news-app/lib/auth-config.ts) — `dashboardRedirectPath`, `apiAccessDeniedStatus`, `roleFromClerkSessionClaims`, env gates
- [`lib/auth-server.ts`](/home/user/upskill-news-app/lib/auth-server.ts) — `getServerIdentity`, `identityFromClerkAuth`, `getClerkSessionToken`
- [`lib/api-server.ts`](/home/user/upskill-news-app/lib/api-server.ts) — `ApiOutcome`, `ApiDeps`, `identityDeniedOutcome`, `resolveAppUserId`, `boundaryInactiveOutcome`, `logServerError`
- [`lib/supabase-server.ts`](/home/user/upskill-news-app/lib/supabase-server.ts) — `createUserScopedServerClient`, `createServiceRoleServerClient`
- [`lib/types.ts`](/home/user/upskill-news-app/lib/types.ts) — `UserRole`, `parseUserRole`
- [`lib/pipeline/adapters/llm.ts`](/home/user/upskill-news-app/lib/pipeline/adapters/llm.ts) — `createLLMAdapter` precedence, `OllamaAdapter`, `assertSafeApiKey`, `redirect: 'error'`, `parseJsonBody`
- [`lib/pipeline/http-timeout.ts`](/home/user/upskill-news-app/lib/pipeline/http-timeout.ts) — `httpTimeoutSignal`
- [`lib/release-gate-server.ts`](/home/user/upskill-news-app/lib/release-gate-server.ts) — the handler shape this spec copies (audit-first ordering, conditional update, 409 on concurrency)
- Route wrappers: [`app/api/admin/release-gate/release/route.ts`](/home/user/upskill-news-app/app/api/admin/release-gate/release/route.ts), [`app/api/corrections/route.ts`](/home/user/upskill-news-app/app/api/corrections/route.ts), [`app/api/admin/deliveries/send/route.ts`](/home/user/upskill-news-app/app/api/admin/deliveries/send/route.ts)
- Migrations: [`20260714100000_identity_and_rls_helpers.sql`](/home/user/upskill-news-app/supabase/migrations/20260714100000_identity_and_rls_helpers.sql) (`private.clerk_user_id`, `app_user_id`, `app_role`, `is_admin`, `raise_append_only`, `set_updated_at`), [`20260714100100_clients_and_generations.sql`](/home/user/upskill-news-app/supabase/migrations/20260714100100_clients_and_generations.sql) (`owns_client`, `is_client_self`), [`20260714100400_consent_audit_and_ops.sql`](/home/user/upskill-news-app/supabase/migrations/20260714100400_consent_audit_and_ops.sql) (append-only log, `seq` tie-breaker, grant posture)

**Sibling documents:**

- [`docs/OLLAMA-NIGHTWORK-DASHBOARDS.md`](/home/user/beelink-bonus/docs/OLLAMA-NIGHTWORK-DASHBOARDS.md) §1 — Ollama defaults audit; the systemd override block; the named gap in `lib/pipeline/adapters/llm.ts` (no `num_ctx`, no `keep_alive`, no `format`)
- [`docs/CLASSROOM-BUILD-LAB.md`](/home/user/beelink-bonus/docs/CLASSROOM-BUILD-LAB.md) §4 (portal architecture, "students never see a model endpoint") and §5 (prefill ceilings, session-affinity routing, the 8060S/gfx1151 correction)
- [`/home/user/beelink-bonus/CLAUDE.md`](/home/user/beelink-bonus/CLAUDE.md) — hardware table, `HSA_OVERRIDE_GFX_VERSION` note (11.0.0 vs unverified 11.5.1)

**External:**

- [Ollama API reference](https://github.com/ollama/ollama/blob/main/docs/api.md) — `options.num_ctx`, `keep_alive`, `format`, `think`
- [llama.cpp `llama-server`](https://github.com/ggml-org/llama.cpp/tree/master/tools/server) — `-c`, `-np`, `--cache-type-k/v`, `-fa`, `--json-schema`
- [Clerk `clerkMiddleware()`](https://clerk.com/docs/references/nextjs/clerk-middleware) — session verification in the Next.js boundary
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security) — the default-deny posture the migrations implement
- [Next.js `proxy.ts`](https://nextjs.org/docs/app/api-reference/file-conventions/proxy) — the Next 16 replacement for `middleware.ts`
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) — the AA target `npm run a11y` audits against
