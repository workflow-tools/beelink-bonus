# VilseckKI — Implementation Plan & Legal Cross-Check

> **Status:** Pre-implementation planning
> **Date:** March 2026
> **Goal:** Fastest path to first paying client, then efficient 2-4 week SaaS build

---

## 1. Repo Structure Decision

**Create `vilseckki-app/` as a new repo.** Keep `beelink-bonus/` for hardware-specific docs and experiments.

```
vilseckki-app/                    # The SaaS product
├── CLAUDE.md                     # Claude context (copy relevant sections from beelink-bonus)
├── ARCHITECTURE.md               # System architecture
├── src/                          # Next.js app (when Path B begins)
│   ├── app/                      # App router
│   ├── components/
│   └── lib/
├── infrastructure/               # Beelink server setup scripts
│   ├── setup-ollama.ps1          # Windows Ollama setup (or .sh if Linux)
│   ├── setup-open-webui.ps1      # Docker-based Open WebUI
│   ├── setup-tailscale.ps1       # Tailscale client networking
│   ├── health-check.ps1          # Monitoring script
│   └── docker-compose.yml        # Open WebUI + Qdrant + supporting services
├── landing/                      # Static landing page (German)
│   └── index.html
├── legal/                        # AGB, AVV template, Datenschutzerklärung
│   ├── LEGAL-CHECKLIST.md
│   └── AVV-TEMPLATE.md
├── docs/
│   ├── SETUP-CHECKLIST.md
│   └── CLIENT-ONBOARDING.md
└── log/                          # Session notes (migrate from beelink-bonus)
```

**beelink-bonus/ stays** for hardware benchmarks, ROCm experiments, model testing. It's the lab. vilseckki-app/ is the business.

---

## 2. The Vercel Problem (This Matters)

You identified the right issue. Your entire pitch is "your data never leaves Germany." If your frontend runs on Vercel:

**The facts:**
- Vercel, Inc. is a US company headquartered in San Francisco
- Vercel does have a Frankfurt (eu-central-1) region
- BUT: Vercel is subject to the US CLOUD Act, which means US law enforcement can compel Vercel to hand over data stored on their servers, even in the EU
- Vercel's Edge Network routes requests globally — even with a Frankfurt region, DNS/TLS termination may touch US infrastructure
- For a normal SaaS (WritingPAD, ProPrecept), this is fine because you have legitimate transfer mechanisms (DPF, SCCs) and Vercel processes minimal data
- For VilseckKI, where the ENTIRE VALUE PROPOSITION is "data stays in Germany," Vercel undermines your credibility

**The solution: Host the frontend on a German provider.**

### Recommended: Hetzner Cloud

| Aspect | Detail |
|--------|--------|
| **Company** | Hetzner Online GmbH, Gunzenhausen, Germany |
| **Data centers** | Nürnberg (NBG1) and Falkenstein (FSN1) — both in Germany |
| **Pricing** | CX23: ~€3.49/month (going up ~30% in April 2026, so ~€4.50) |
| **DSGVO** | Fully German company, German data centers, not subject to US CLOUD Act |
| **Next.js** | Run as a Node.js server on the VPS, or use a static export behind Caddy/nginx |
| **Location angle** | Hetzner's Nürnberg data center is literally 60km from Vilseck. Your data doesn't even leave Franken. |

**Alternative: netcup GmbH** — Headquartered in Nürnberg, even cheaper, also fully German. Less polished than Hetzner but adequate.

**Alternative: IONOS (1&1)** — German, well-known to Mittelstand clients. More expensive but the name recognition helps with conservative buyers.

### Architecture with Hetzner (Zero US Dependencies)

```
Client browser
    ↓ HTTPS (TLS via Caddy, vilseckki.de)

Hetzner VPS (Nürnberg)              ← German company, German data center
├── Next.js frontend (Node.js)
├── Caddy (reverse proxy + auto-TLS)
├── Better Auth (auth library, in-process)
├── PostgreSQL (auth data, tenant metadata)
├── API routes
│   └── Payment: Wise Überweisung / Creem EU MoR at scale
│
    ↓ WireGuard / Tailscale tunnel (encrypted)

Beelink (your home in Vilseck)      ← Your hardware, your house
├── Ollama (inference, GPU-accelerated)
├── Qdrant (vector DB, per-tenant collections)
└── Document storage (encrypted, per-tenant)
```

**Full data sovereignty chain:**
- Domain registrar: German (INWX, netcup, or Hetzner)
- Frontend/Auth/Metadata: Hetzner VPS, Nürnberg
- Auth: Better Auth (open-source library, no external calls)
- Payments: Wise Überweisung (Phase 1) / Creem EU MoR (Phase 2)
- AI Inference: Beelink, Vilseck (your physical hardware)
- Documents + Vector DB: Beelink, Vilseck
- **US dependencies in core data path: ZERO**

**Key insight:** The Hetzner VPS handles the web-facing part (landing page, auth, billing dashboard). All document processing and AI inference happens on the Beelink. Client documents never touch Hetzner — they go directly to the Beelink via the encrypted tunnel. This means:
- No client documents on any third-party server, ever
- The Hetzner VPS is just a router/UI server
- If someone asks "where is my data?", the answer is "on a computer in Vilseck, Germany, in my possession"

### Authentication: No Clerk

Clerk is a US company (CLOUD Act) and contradicts the "no US services" positioning. Replaced with:

**Better Auth** (or Auth.js/NextAuth v5 as alternative) — open-source TypeScript auth library, runs inside the Next.js app, stores data in Postgres on the Hetzner VPS. No external service, no third-party data processor, no US dependency.

| Option | Type | Hosting | Pros | Cons |
|--------|------|---------|------|------|
| **Better Auth** (recommended) | Library | In-app + Postgres on Hetzner | Zero vendor lock-in, free, full-featured, no separate service | Newer than Auth.js, smaller community |
| Auth.js (NextAuth v5) | Library | In-app + Postgres on Hetzner | Mature (2M+ weekly downloads), well-documented | Less feature-rich OOTB |
| Hanko | Service | Self-host on Hetzner | German company (Kiel), passkey-first | Separate container to manage, passkeys may confuse Mittelstand clients |
| Supabase Auth (self-hosted) | Platform | Self-host on Hetzner | Auth + DB + storage in one | Overkill unless using full Supabase stack |

**For § 203 StGB compliance:** Library-based auth (Better Auth / Auth.js) is ideal because there is no third-party Auftragsverarbeiter for auth data. The Notarin's login credentials never leave the Hetzner Nürnberg data center.

---

## 3. Payment Processing — Three Options

### Option A: Direct Invoicing via Wise Business (RECOMMENDED FOR LAUNCH)

For B2B local clients (a Notarin paying €149/month), this is actually the most natural approach in Germany. German businesses EXPECT a Rechnung, not a Stripe checkout page.

**How it works:**
- Client signs a Dienstleistungsvertrag (service agreement)
- You send a monthly Rechnung via Wise Business (or sevDesk when you activate it)
- Client pays via Überweisung (bank transfer) — this is how 90% of German B2B transactions work
- You include 19% MwSt on the invoice
- Zero payment processing fees

**Pros:**
- Zero fees (no 2.9%, no 3.9%)
- Maximally "German" — no US payment processor involved at all
- Simple for 1-10 clients
- Wise Business handles multi-currency if needed later
- sevDesk integration for Buchhaltung when revenue flows

**Cons:**
- Manual invoicing (automate with sevDesk later)
- No automatic subscription management
- Client could miss a payment — need to follow up manually
- Doesn't scale past ~15-20 clients without tooling

**Verdict:** Use this for the Notarin pilot and first 5-10 clients. It's free, professional, and reinforces the "local business" trust signal.

### Option B: Creem (EU MoR — for when you scale)

**What Creem offers:**
- EU-based Merchant of Record (they are the legal seller)
- Handles VAT calculation and remittance across EU
- 3.9% + €0.40 per transaction
- SEPA payouts free for EU companies
- Subscription management, dunning, analytics built in

**When to switch to Creem:**
- When you have 10+ clients and manual invoicing becomes a burden
- When you expand beyond Germany (EU-wide, no per-country VAT headaches)
- When you want a self-service signup flow on the website

**Pros:**
- EU company — no US CLOUD Act concern
- MoR means they handle AGB/Widerrufsrecht complexity
- "No data leaves Europe" story stays intact

**Cons:**
- 3.9% + €0.40 is more expensive than Stripe (2.9% + €0.30)
- Newer company (launched Sept 2024) — less proven than Stripe/Paddle
- For B2B within Germany, you don't actually need MoR advantages (no cross-border VAT complexity)

### Option C: Stripe (keep for existing products, skip for VilseckKI)

Stripe works perfectly for WritingPAD, ProPrecept, etc. But for VilseckKI's "no US companies" positioning, having Stripe in the payment flow is a messaging contradiction. Save it for your other products.

### Recommendation

**Phase 1 (0-10 clients):** Wise Business invoicing. Direct Überweisung. Zero fees. Maximum trust.
**Phase 2 (10+ clients):** Evaluate Creem vs. adding sevDesk automated invoicing. If you're still mostly Germany B2B, sevDesk + Überweisung is probably still better. If you're expanding EU-wide, Creem.

---

## 4. Beelink Setup Checklist — Windows Considerations

The Beelink ships with Windows. You have three paths:

### Path 1: Keep Windows (Fastest to Start)

Ollama has a native Windows installer as of 2025. Docker Desktop runs on Windows via WSL2.

```
Setup sequence:
□ 1. Windows Update — get everything current
□ 2. Enable WSL2: wsl --install (for Docker)
□ 3. Install Docker Desktop for Windows
□ 4. Install Ollama for Windows (https://ollama.com/download/windows)
□ 5. Set environment variable: HSA_OVERRIDE_GFX_VERSION=11.0.0
       → System Properties → Environment Variables → System Variables → New
□ 6. Start Ollama, verify GPU detection:
       ollama run llama3.1:7b "Hello, test"
       → Check Task Manager → GPU tab to verify 890M is being used
□ 7. Pull production models:
       ollama pull llama3.1:70b-instruct-q4_K_M
       ollama pull mistral:7b-instruct-q4_K_M
       ollama pull nomic-embed-text
□ 8. Run benchmark: time the response to a complex prompt, note tok/s
□ 9. Docker: deploy Open WebUI
       docker run -d -p 3000:8080 \
         -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
         -v open-webui:/app/backend/data \
         --name open-webui \
         ghcr.io/open-webui/open-webui:main
□ 10. Install Tailscale for Windows (https://tailscale.com/download/windows)
□ 11. Configure Windows power settings: "Never sleep" on AC power
□ 12. Test from MacBook: connect via Tailscale IP to Open WebUI
□ 13. Set up Windows Task Scheduler for Ollama auto-start on boot
```

**Pros:** Fastest to get running. No OS reinstall.
**Cons:** WSL2 adds a layer. ROCm support on Windows is less mature than Linux. Docker Desktop licensing (free for personal/small business < $10M revenue — you're fine). Windows Updates may reboot the machine.

### Path 2: Dual Boot (Windows + Ubuntu Server)

Keep Windows for any personal use. Install Ubuntu Server 24.04 LTS on a second partition for the AI server role.

**Pros:** Best ROCm support (Linux is the primary ROCm target). More stable for 24/7 server operation. No Docker Desktop licensing questions.
**Cons:** Need to partition the drive. Boot management. Can't use both simultaneously.

### Path 3: Full Linux (Best for Production, Biggest Commitment)

Wipe Windows, install Ubuntu Server 24.04 LTS. The Beelink becomes a dedicated headless server.

**Pros:** Cleanest setup. Best performance. Most reliable for 24/7 operation. ROCm works best here.
**Cons:** Lose Windows. Irreversible without a full reinstall.

### Recommendation

**Start with Path 1 (Windows)** for the Notarin pilot. It gets you running this weekend. If you validate demand and decide to make this a serious product, migrate to Path 3 (Ubuntu Server) later. The models, configs, and Docker volumes are all portable.

---

## 5. Legal Cross-Check Research Prompts

These are research prompts you should run (in Claude, or via your own research) BEFORE taking money from anyone. The EthicalPivot lesson applies: validate the legal landscape before building.

### Prompt 1: AVV Requirements for Local AI Hosting

```
I operate ML Upskill Agents UG (haftungsbeschränkt) in Vilseck, Germany. I want
to offer a service called VilseckKI where I host AI inference on my own physical
hardware (a Beelink mini-PC in my home) and provide access to local businesses
(Rechtsanwälte, Notare, Steuerberater) via encrypted tunnel (Tailscale/WireGuard).

Clients upload documents to my hardware for RAG (retrieval-augmented generation)
and chat with a local LLM (Llama, Mistral, etc. via Ollama). No cloud APIs are
involved for inference. The frontend web application is hosted on Hetzner Cloud
(Nürnberg data center).

Legal questions:
1. Am I an Auftragsverarbeiter (Art. 28 DSGVO) for my clients' data? Do I need
   an AVV with each client?
2. If my clients are Rechtsanwälte or Notare, does their Berufsgeheimnis
   (§ 203 StGB) impose additional requirements on me as their IT service provider?
3. What specific clauses must the AVV contain for AI inference services?
   (Ref: the BayLDA and DSK guidance on KI and DSGVO)
4. Do I need a Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO) for this?
5. Is a Datenschutz-Folgenabschätzung (DSFA / DPIA, Art. 35 DSGVO) required
   for AI-based document processing?

Please cite specific DSGVO articles, German case law, and BayLDA guidance where
applicable. I need actionable answers, not general overviews.
```

### Prompt 2: EU AI Act Classification

```
I operate a service where clients upload documents and query them via a locally-
hosted LLM (open-source models like Llama 3.1 70B, Mistral 7B). The system
performs retrieval-augmented generation (RAG) — it finds relevant passages in
uploaded documents and generates natural-language answers.

Under the EU AI Act (Regulation 2024/1689), which entered into force in stages
from February 2025:

1. Is my RAG system classified as a "KI-System" under Art. 3(1)?
2. If yes, what risk category does it fall into? (Minimal / Limited / High /
   Unacceptable)
3. Specifically for legal document processing (Rechtsanwälte/Notare): Does
   Art. 6 Annex III point 8(a) (administration of justice) apply to a tool
   that searches documents but does NOT make legal decisions?
4. What transparency obligations (Art. 50) apply? Must I disclose to end-users
   that they are interacting with an AI system?
5. What are my obligations as a "deployer" (Betreiber) vs. "provider"
   (Anbieter) under the Act? I did not develop the base models — I deploy
   open-source models.
6. Is there a de minimis exemption for small providers (KMU/SME)?

Cite specific AI Act articles and recitals. Reference the German AI Act
implementation guidance (BMAS/BMWK) if available as of early 2026.
```

### Prompt 3: Haftung (Liability) for AI-Generated Outputs

```
I host a local AI system that German Rechtsanwälte and Notare use to query
their own documents. The system generates natural-language answers based on
document retrieval (RAG). It does NOT provide legal advice — it searches and
summarizes.

1. If the AI generates an incorrect summary and the lawyer relies on it in
   a legal proceeding, what is my liability as the service provider?
2. Does the new EU Product Liability Directive (2024/2853) apply to AI
   inference services? Am I a "manufacturer" of a "product" under this
   directive?
3. Does the AI Liability Directive proposal (COM/2022/496) — if adopted —
   change my exposure?
4. Should I carry Berufshaftpflichtversicherung (professional liability
   insurance) or IT-Haftpflicht? What coverage amounts are standard for
   IT-Dienstleister in Germany?
5. What disclaimers should the AGB and the UI include to limit liability?
   (e.g., "KI-generierte Zusammenfassungen ersetzen keine rechtliche
   Beratung" or similar)
6. Should the Dienstleistungsvertrag include a Haftungsbeschränkung
   (limitation of liability)? What is enforceable under German AGB-Recht
   (§§ 305-310 BGB)?

Cite German case law on IT service provider liability where available.
```

### Prompt 4: Gewerberechtliche Requirements

```
ML Upskill Agents UG (haftungsbeschränkt) is registered in Vilseck, Germany
(Amtsgericht Amberg, HRB 8114). The Unternehmensgegenstand in the
Handelsregister is: "Entwicklung und Betrieb von Softwareanwendungen sowie
datengestützte Beratungsleistungen."

I want to offer a new service: hosting local AI inference for businesses
under the trade name "VilseckKI."

1. Does "hosting AI inference for third parties" fall within the registered
   Unternehmensgegenstand, or do I need a Satzungsänderung (amendment to the
   articles of association) at the Notar and Handelsregister?
2. Do I need a separate Gewerbeanmeldung for the trade name "VilseckKI," or
   is it covered by the existing UG registration?
3. Are there any Genehmigungspflichten (licensing requirements) for operating
   an AI hosting service in Bavaria?
4. Do I need to register as a Telekommunikationsanbieter or
   Telemediendienst under the DDG (Digitale-Dienste-Gesetz)?
5. What are the Impressum requirements for vilseckki.de if it operates as a
   trade name of the UG?

Cite relevant German commercial law (HGB, GewO, DDG) and Bavarian
regulations.
```

### Prompt 5: § 203 StGB and IT Service Providers to Berufsgeheimnisträger

```
I want to provide IT services (local AI document processing) to German
Rechtsanwälte and Notare who are Berufsgeheimnisträger under § 203 StGB.

Since the 2017 reform (§ 203 Abs. 3 StGB), IT service providers ("sonstige
Mitwirkende") can receive confidential information if properly engaged.

1. What contractual framework do I need? Is the AVV sufficient, or do I
   need a separate Verpflichtungserklärung (confidentiality agreement)?
2. Must I be specifically "verpflichtet" (formally obligated) by the lawyer/
   Notar under § 203 Abs. 3 S. 2 StGB?
3. What technical and organizational measures (TOMs) does the
   Rechtsanwaltskammer or Bundesnotarkammer expect from IT service providers?
4. Can I use sub-processors (e.g., Hetzner for the frontend VPS, Clerk for
   auth) when serving Berufsgeheimnisträger, or does this violate § 203?
5. Are there specific BRAK (Bundesrechtsanwaltskammer) or BNotK guidelines
   on cloud/AI services for lawyers and Notare?
6. My Notarin is my first pilot client. What specific documents should I
   prepare before she starts uploading any client-related documents to my
   system?

This is critical — getting § 203 wrong is a criminal offense (Straftat),
not just a regulatory fine.
```

### Prompt 6: Insurance and Risk

```
I am operating an IT service (local AI hosting) for professional clients
in Germany, including Rechtsanwälte and Notare.

1. What types of insurance should I carry?
   - IT-Haftpflichtversicherung?
   - Berufshaftpflicht?
   - Cyber-Versicherung?
   - Vermögensschadenhaftpflicht?
2. What are typical coverage amounts and premiums for a UG in this space?
3. Does operating AI inference from residential premises (home office /
   Heimarbeitsplatz) affect insurance requirements or coverage?
4. Should the UG's Gesellschaftsvertrag be amended to cover this activity
   for Haftungsbeschränkung purposes?

Provide specific German insurer names and product types if possible.
```

---

## 6. Critical Legal Items to Resolve BEFORE Taking Money

Based on the research prompts above, these are the blockers:

| # | Item | Risk if Skipped | Effort |
|---|------|-----------------|--------|
| 1 | **AVV template** for clients | DSGVO violation, fines | Medium — template + legal review |
| 2 | **§ 203 StGB compliance** for Berufsgeheimnisträger clients | CRIMINAL liability | High — need proper Verpflichtungserklärung |
| 3 | **EU AI Act classification** | Potential transparency/compliance violations | Low — likely "limited risk" but must confirm |
| 4 | **Haftungsbeschränkung in AGB** | Unlimited liability for AI errors | Medium — IT-Recht-Kanzlei can likely generate |
| 5 | **Check Unternehmensgegenstand** | Handelsregister mismatch | Low — likely already covered, confirm with Notarin |
| 6 | **IT-Haftpflicht insurance** | Uninsured professional liability | Low — get a quote from Hiscox or similar |

### The Notarin Advantage

Here's the beautiful thing: your first client IS a Notarin. She can:
- Confirm whether the Unternehmensgegenstand covers this activity
- Execute a Satzungsänderung if needed (that's literally her job)
- Review the AVV template from a practitioner's perspective
- Tell you what § 203 compliance looks like from the Berufsgeheimnisträger's side
- Possibly refer you to a Rechtsanwalt colleague for the AGB review

Ask her. This is a conversation, not a legal engagement. "I want to make sure I'm setting this up correctly — what would you need from an IT service provider before you'd trust them with client documents?"

---

## 7. Summary: What to Do This Week

### Immediate (This Week)
1. Run the 6 legal research prompts above. Get answers before spending time on code.
2. Talk to the Notarin — frame it as "I'm exploring this, what would you need?"
3. Check the Unternehmensgegenstand in the Handelsregister (hrb-portal.de or Amtsgericht Amberg online)

### Weekend 1 (If Legal Is Clear)
4. Beelink: Install Ollama (Windows path), pull models, benchmark tok/s
5. Deploy Open WebUI via Docker
6. Install Tailscale, test access from MacBook
7. Give the Notarin access for a free pilot

### Weekend 2
8. Register vilseckki.de
9. Deploy landing page on Hetzner (static HTML to start, ~€3.49/month)
10. Prepare AVV template and Dienstleistungsvertrag
11. Set up Wise Business invoicing for first client

### Week 3-4 (If Pilot Validates)
12. Build proper Next.js app on Hetzner VPS
13. Integrate Clerk for auth
14. Set up per-tenant document isolation in Qdrant
15. German-language UI
16. AGB + Datenschutzerklärung via IT-Recht-Kanzlei

---

## Sources

- [Creem.io — EU MoR](https://www.creem.io/)
- [Creem vs Stripe comparison](https://www.creem.io/comparisons/stripe)
- [Creem supported countries](https://docs.creem.io/merchant-of-record/supported-countries)
- [Hetzner Cloud — Made in Germany](https://www.hetzner.com/cloud-made-in-germany)
- [Hetzner price adjustment April 2026](https://www.hetzner.com/pressroom/statement-price-adjustment/)
- [AVV für KI-Dienste (Plotdesk)](https://plotdesk.com/magazin/auftragsverarbeitungsvertrag-avv-ki-dienste)
- [DSGVO-konformes KI-Hosting Leitfaden (Coding9)](https://coding9.de/blog/dsgvo-konformes-ki-hosting-leitfaden)
- [KI und DSGVO für deutsche Unternehmen (Plotdesk)](https://plotdesk.com/magazin/dsgvo-konforme-ki-loesungen)
- [QuitGPT.org](https://quitgpt.org/)
- [Euronews: Cancel ChatGPT boycott](https://www.euronews.com/next/2026/03/02/cancel-chatgpt-ai-boycott-surges-after-openai-pentagon-military-deal)
