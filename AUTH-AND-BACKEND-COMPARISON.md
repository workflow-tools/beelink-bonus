# VilseckKI: Better Auth vs Self-Hosted Supabase

> **Decision context:** Choosing the auth + backend stack for VilseckKI, to be deployed on Hetzner VPS (Nürnberg). Must be zero US dependency in the data path. Must support multi-tenant document isolation for Berufsgeheimnisträger clients (Notare, Rechtsanwälte).

---

## The Real Question

This isn't just "which auth library?" — it's "how much backend infrastructure do you want to build vs. adopt?" VilseckKI needs four backend capabilities:

1. **Authentication** — user login, session management
2. **Tenant isolation** — each client's data strictly separated
3. **Document storage** — uploaded files (PDFs, contracts, etc.) stored securely per-tenant
4. **Metadata database** — user accounts, tenant config, usage tracking, billing state

Better Auth solves #1. You build #2–4 yourself.
Self-hosted Supabase solves all four out of the box.

---

## Option A: Better Auth + DIY Backend

### What You Get
- **Auth:** Better Auth library runs inside your Next.js process. Email/password, OAuth, 2FA, organization/multi-tenant plugin with RBAC (owner/admin/member roles + custom roles).
- **Database:** You set up PostgreSQL yourself on Hetzner. Better Auth stores auth tables there. You add your own tables for tenant metadata, usage, etc.
- **File storage:** You build your own. Likely: a `/uploads/{tenant_id}/` directory on the Beelink's filesystem, with an API endpoint to handle upload/download with auth checks.
- **Tenant isolation:** You implement this in your application code. Better Auth's organization plugin gives you tenant-aware auth (who belongs to which org), but the data isolation is your responsibility — either in application logic or Postgres RLS policies you write yourself.

### Architecture on Hetzner VPS

```
Hetzner VPS (Nürnberg, ~CX23 = €3.49–4.50/month)
├── Node.js (Next.js app)
│   ├── Better Auth (in-process)
│   ├── API routes (custom)
│   └── Drizzle or Prisma ORM
├── PostgreSQL 16 (apt install or Docker)
│   ├── better_auth_* tables (managed by library)
│   └── your tables (tenants, usage, billing)
└── Caddy (reverse proxy, auto-TLS)
```

### Advantages

**Minimal resource footprint.** A Next.js app + PostgreSQL on a CX23 (2 vCPU, 4GB RAM) is comfortable. Total Hetzner cost: ~€3.50–4.50/month. You're running two processes, not a dozen containers.

**Maximum simplicity.** One repo, one deployment, one process for the web app. Auth is a library import, not a service. Fewer things to break, fewer things to update, fewer things to monitor. For a solo dev running this alongside 17 other apps, simplicity is survival.

**Total control over the data model.** You design exactly the tables you need. No Supabase conventions to work around. If your tenant model is unusual (e.g., a Notarin who wants sub-workspaces per Mandant), you build exactly what you need.

**You already know this pattern.** Your WritingPAD/ProPrecept family uses Next.js + external services. Swapping Clerk for Better Auth is conceptually the same architecture — just self-hosted. The learning curve is the Better Auth API, not an entirely new platform.

**Fastest Path A deployment.** For the Open WebUI pilot (which has its own auth), you don't even need Better Auth yet. You add it when you build the custom frontend in Path B.

### Disadvantages

**You build the document storage pipeline yourself.** Upload endpoint, file validation, virus scanning (ClamAV?), per-tenant directory isolation, access control middleware, download endpoint with auth checks. This is maybe 2-3 days of work, but it's work you have to maintain.

**You write your own RLS or application-level isolation.** Better Auth's organization plugin tells you "this user belongs to tenant X." But enforcing "this user can ONLY see tenant X's data" across every query is your job. You can do this with Postgres RLS policies (which you'd write manually), or application-level middleware, or both. Either way, you're building and testing the isolation layer.

**No admin dashboard.** No Supabase Studio equivalent. If you need to inspect a client's data, debug a tenant issue, or check auth logs, you're writing SQL queries or building your own admin views.

**No realtime.** If you ever want live document collaboration or real-time status updates, you'd need to add something (Socket.io, SSE, etc.). Not needed for VilseckKI v1, but worth noting.

### Estimated Build Time for VilseckKI Backend

| Component | Time |
|-----------|------|
| Better Auth setup + Postgres schema | 0.5 day |
| Organization/tenant plugin config | 0.5 day |
| Document upload/download API | 1-2 days |
| Per-tenant storage isolation | 0.5 day |
| RLS policies or app-level isolation | 1 day |
| Testing tenant isolation thoroughly | 1 day |
| **Total** | **4-6 days** |

---

## Option B: Self-Hosted Supabase on Hetzner

### What You Get
- **Auth (GoTrue):** Email/password, OAuth, magic links, 2FA. Manages JWTs that embed user metadata. Mature — this is what Supabase Cloud runs for hundreds of thousands of projects.
- **Database (PostgreSQL):** Managed by the Supabase stack. Comes with pgvector extension (relevant for RAG if you ever move embeddings off the Beelink). Row Level Security is a first-class citizen — Supabase's entire security model is built on it.
- **File storage:** Supabase Storage is an S3-compatible storage layer backed by local filesystem (for self-hosted) or S3. Per-tenant isolation via storage policies tied to auth. Upload/download APIs included. You don't build this — it exists.
- **Realtime:** WebSocket subscriptions on database changes. Not needed for VilseckKI v1 but free to have.
- **Studio:** Admin dashboard for inspecting data, managing users, writing SQL queries, viewing auth logs. Runs locally. Extremely useful for debugging client issues.
- **Edge Functions (Deno):** Serverless functions. Optional — you can ignore this if your Next.js API routes handle everything.

### Architecture on Hetzner VPS

```
Hetzner VPS (Nürnberg, CX33 or higher = ~€7–12/month recommended)
├── Docker Compose (supabase/docker)
│   ├── supabase-db (PostgreSQL 15+)
│   ├── supabase-auth (GoTrue)
│   ├── supabase-rest (PostgREST)
│   ├── supabase-realtime
│   ├── supabase-storage
│   ├── supabase-studio (admin UI)
│   ├── supabase-meta (pg-meta)
│   ├── supabase-imgproxy (optional, image transforms)
│   ├── supabase-edge-runtime (optional, Deno functions)
│   ├── supabase-analytics (optional, Logflare)
│   └── supabase-vector (optional, pgvector)
├── Node.js (Next.js app, separate from Supabase stack)
└── Caddy (reverse proxy, auto-TLS)
```

### Advantages

**Tenant isolation is solved at the infrastructure level.** Supabase's entire philosophy is "put security in the database, not the application." You write RLS policies like:

```sql
CREATE POLICY "tenant_isolation" ON documents
  FOR ALL
  USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);
```

Every query, every API call, every storage request is automatically filtered by the authenticated user's tenant. You cannot accidentally leak data across tenants because Postgres itself enforces the boundary. For Berufsgeheimnisträger clients, this is a much stronger isolation guarantee than application-level checks.

**Document storage is built in.** Supabase Storage gives you:
- Upload/download APIs with auth-aware access control
- Storage policies (like RLS but for files): "users can only access files in their tenant's bucket"
- S3-compatible API (if you ever need to integrate with other tools)
- Local filesystem backend for self-hosted (no AWS dependency)
- Per-tenant file isolation without building anything custom

**Studio admin dashboard is invaluable for debugging.** When the Notarin says "I can't find my document," you open Studio, inspect her tenant's storage bucket and database rows, and solve the problem in 2 minutes instead of writing SQL queries in a terminal.

**You already need to learn Supabase.** You said so yourself. Rebeka (your SA placement management platform) is architected on Supabase with PostgreSQL + RLS. Learning Supabase now for VilseckKI means you're also investing in Rebeka's eventual build. Same skill, two products.

**pgvector is included.** If you ever decide to move the embedding/vector storage from Qdrant (on the Beelink) to the Hetzner VPS — maybe for reliability or to reduce Beelink load — pgvector is already there. You wouldn't need Qdrant at all. This simplifies the Beelink to just "runs Ollama" and nothing else.

**PostgREST gives you an instant API.** Define your tables, set RLS policies, and you have a full CRUD API without writing endpoint code. Your Next.js app calls the Supabase client library (which talks to PostgREST). This can cut backend development time significantly.

### Disadvantages

**Resource overhead.** The full Supabase Docker Compose stack runs 10-12 containers. Official recommendation is 4GB RAM minimum, 8GB recommended. A CX23 (4GB) is tight — you'd likely want a CX33 (8GB, ~€7.50/month before April price increase, ~€10/month after). This is still cheap, but it's 2-3x the cost of the Better Auth path.

You CAN trim the stack by removing services you don't need (Logflare/analytics, Edge Runtime, imgproxy, Realtime). A trimmed Supabase runs comfortably on 4GB. But you need to know what to remove and maintain the custom docker-compose.

**Operational complexity.** 10+ containers means more things that can fail. Docker networking issues, container restarts, version mismatches between Supabase components. You need to understand Docker Compose well enough to debug issues. Updates require pulling new images and hoping nothing breaks — Supabase self-hosted moves fast and breaking changes happen.

**Supabase self-hosted is community-supported, not officially supported.** From Supabase's own docs: self-hosting is available but Supabase Cloud is the recommended path for production. Bug reports for self-hosted get lower priority. The community GitHub discussions for self-hosted have a mix of success stories and pain reports.

**Two deployment targets to manage.** Your Next.js app is one deployment. The Supabase stack is another. They need to be coordinated. If Supabase's auth service goes down, your frontend is broken. If you update Next.js and it expects a newer Supabase client version that doesn't match your self-hosted version — you're debugging compatibility.

**Auth is GoTrue (Go), not TypeScript.** Better Auth runs in your Node.js process. GoTrue is a separate Go service. If you need to customize auth behavior (custom email templates, unusual login flows, special JWT claims for tenant isolation), you're configuring GoTrue's environment variables, not writing TypeScript. Less flexible, more opaque.

**The learning curve is the whole platform, not just auth.** Better Auth is one library with one API to learn. Supabase is a platform with auth, database APIs, storage APIs, RLS syntax, client libraries, Studio, and its own conventions. This is valuable knowledge (especially for Rebeka), but it's a bigger investment for VilseckKI specifically.

### Estimated Build Time for VilseckKI Backend

| Component | Time |
|-----------|------|
| Supabase Docker Compose setup + trimming | 1-2 days |
| Learning Supabase patterns (RLS, client library) | 2-3 days |
| Auth config (GoTrue, email/password) | 0.5 day |
| Database schema + RLS policies | 1 day |
| Storage buckets + storage policies | 0.5 day |
| Next.js integration with Supabase client | 1 day |
| Testing tenant isolation | 1 day |
| **Total** | **6-9 days** |

Slower initially, but you're building on a foundation that requires less custom code going forward.

---

## Head-to-Head Comparison

| Dimension | Better Auth + DIY | Self-Hosted Supabase |
|-----------|-------------------|---------------------|
| **Auth quality** | Excellent (TypeScript-native, in-process) | Excellent (GoTrue, battle-tested) |
| **Multi-tenant auth** | Organization plugin (RBAC, invites, roles) | JWT claims + RLS (database-enforced) |
| **Tenant data isolation** | You build it (app-level or manual RLS) | Built-in (RLS is the whole model) |
| **Document storage** | You build it (filesystem + API) | Built-in (Storage service + policies) |
| **Admin dashboard** | None (build your own or use pgAdmin) | Studio (web UI, very polished) |
| **Hetzner VPS cost** | ~€3.50–4.50/month (CX23, 4GB) | ~€7.50–10/month (CX33, 8GB) |
| **Resource usage** | Light (Node.js + Postgres) | Heavy (10-12 Docker containers) |
| **Setup time** | 4-6 days | 6-9 days |
| **Ongoing maintenance** | Lower (less moving parts) | Higher (Docker stack updates) |
| **Custom code needed** | More (storage, isolation, admin) | Less (use Supabase APIs) |
| **DSGVO story** | Clean (no external services) | Clean (all self-hosted in Nürnberg) |
| **§ 203 StGB story** | Clean (no third-party processor) | Clean (no third-party processor) |
| **Scales to Rebeka** | No (different architecture) | YES (Rebeka is built on Supabase) |
| **Learning investment** | Lower (one library) | Higher (whole platform) |
| **Solo dev sustainability** | Higher (less to break) | Lower (more to monitor) |
| **Recovery from failure** | Restart Node + Postgres | Debug which of 10+ containers broke |
| **pgvector (future RAG)** | Add separately if needed | Included |

---

## Recommendation

**There is no wrong answer here.** Both paths result in a fully EU-sovereign stack with proper tenant isolation. The choice depends on how you weigh two competing priorities:

### Choose Better Auth if:
- You want the fastest, simplest path to a working VilseckKI
- You value having fewer moving parts to maintain alongside 17 other apps
- You're comfortable building a document storage pipeline (it's not hard, just work)
- You want to keep the Hetzner costs minimal (~€3.50/month)
- You plan to learn Supabase later, specifically when you're ready to build Rebeka

### Choose Self-Hosted Supabase if:
- You want to learn Supabase NOW and have the investment pay off twice (VilseckKI + Rebeka)
- Database-level tenant isolation (RLS) matters to you for the § 203 StGB / Berufsgeheimnisträger argument — it's a stronger technical guarantee than application-level checks
- You don't want to build document storage, upload APIs, or admin tooling from scratch
- You're willing to spend 2-3 extra days on initial setup and ~€6/month more on Hetzner
- You can tolerate the Docker Compose operational overhead

### My lean:

If you told me "I want this running by end of March," I'd say **Better Auth**. If you told me "I want to invest in the right foundation for both VilseckKI and Rebeka," I'd say **Self-Hosted Supabase**. Given that you explicitly said you need to learn Supabase anyway, and given that Rebeka's 74,000-word technical design is already built on Supabase + RLS + Storage, I think the Supabase path is the higher-ROI choice — even though it's slower to start.

The Notarin doesn't care what your backend is. She cares that it works and her data is safe. Both paths deliver that.

---

---

## Appendix: Supabase Storage in the VilseckKI Architecture

### The Two-Stage Document Problem

VilseckKI has two distinct document handling stages:

**Stage 1 — Store the original securely.** Notarin uploads Kaufvertrag.pdf → store it, access-control it, make it downloadable/deletable. Only her tenant sees it.

**Stage 2 — Process for RAG.** Extract text → chunk → embed → store vectors → retrieve at query time. This is the AI pipeline.

Supabase Storage handles Stage 1. Stage 2 is custom pipeline code regardless of storage choice.

### What Supabase Storage Concretely Provides

1. **Database-enforced per-tenant file isolation.** Storage policies (RLS on `storage.objects`) mean Postgres blocks cross-tenant file access even if application code has a bug. For § 203 StGB compliance, this defense-in-depth is significant.

2. **Resumable uploads (TUS protocol).** Files up to 50GB, uploaded in 6MB chunks, survive network interruptions. Relevant for large legal documents over unreliable connections.

3. **S3-compatible API.** Document processing tools that expect S3 work against the self-hosted Storage endpoint. No AWS dependency.

4. **File metadata in Postgres.** Every file has a row in `storage.objects` with timestamps, size, MIME type. Queryable with SQL for billing ("total storage per tenant"), auditing, and administration.

5. **No custom upload/download code.** The Supabase client library handles multipart upload, auth token passing, and download URLs. Without it, you write 200-400 lines of security-critical file handling code.

### Three Architecture Variants

| Approach | Original Files | Vector Storage | Beelink Role |
|----------|---------------|----------------|--------------|
| Better Auth + DIY | Beelink filesystem | Qdrant on Beelink | Everything: storage + vectors + inference |
| Supabase + Qdrant | Supabase Storage (Hetzner) | Qdrant on Beelink | Vectors + inference only |
| Supabase + pgvector | Supabase Storage (Hetzner) | pgvector in Supabase Postgres | Inference ONLY |

**Variant 3 (Supabase + pgvector) is the most resilient.** The Beelink becomes a pure inference appliance. If it reboots, documents and embeddings are safe on Hetzner. If you add a second Beelink for capacity, both point at the same Supabase. The Beelink is stateless and replaceable.

**Trade-off:** Client documents live on Hetzner, not your physical hardware. The pitch shifts from "on my computer in my house" to "in a German data center in Nürnberg." Still DSGVO-clean, still no US dependency, but a subtly different trust story.

**Recommended variant for VilseckKI:** Supabase + Qdrant (middle option). Originals on Hetzner (backed up, Supabase-managed, RLS-isolated). RAG pipeline + Qdrant + Ollama on Beelink. Best balance of reliability, simplicity, and "your data stays local" messaging. Can migrate to pgvector later if Qdrant adds operational burden.

---

## Sources

- [Supabase Self-Hosting with Docker](https://supabase.com/docs/guides/self-hosting/docker)
- [Supabase Auth Self-Hosting Config](https://supabase.com/docs/guides/self-hosting/auth/config)
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Storage Self-Hosting Config](https://supabase.com/docs/guides/self-hosting/storage/config)
- [Supabase S3-Compatible Storage](https://supabase.com/docs/guides/storage/s3/compatibility)
- [Multi-Tenant RLS Deep Dive (LockIn)](https://dev.to/blackie360/-enforcing-row-level-security-in-supabase-a-deep-dive-into-lockins-multi-tenant-architecture-4hd2)
- [Self-Hosting Resource Discussion (GitHub)](https://github.com/orgs/supabase/discussions/26159)
- [Self-Hosting: What's Working Discussion (GitHub)](https://github.com/orgs/supabase/discussions/39820)
- [Better Auth Organization Plugin](https://better-auth.com/docs/plugins/organization)
- [Better Auth GitHub](https://github.com/better-auth/better-auth)
- [Building Multi-Tenant Apps with Better Auth (ZenStack)](https://zenstack.dev/blog/better-auth)
