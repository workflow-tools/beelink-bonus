# Bavarian Grant Application Plan — VilseckKI UG

> **Purpose:** Eligibility assessment and step-by-step application plan for
> Bavarian funding programs, with creative-but-defensible strategies to maximize
> the Digitalbonus Bayern across BOTH funding tracks, plus Start?Zuschuss!
>
> **Entity:** ML Upskill Agents UG (haftungsbeschränkt), trading as VilseckKI
> **Founded:** ~August 2024
> **Employees:** 1 (sole founder)
> **Turnover:** <€10M (well under)
>
> Last updated: March 2026.

---

## The Big Unlock: Two Separate Digitalbonus Applications

Most people don't realize this: you can file **one application per Förderbereich**
during the entire program lifetime (July 2024 – December 2027). The two tracks are:

- **Förderbereich 2.1 — Digitalisierung** (your AI pipeline)
- **Förderbereich 2.2 — IT-Sicherheit** (securing the pipeline and client data)

You can get **Plus** on one track and **Standard** on the other. You cannot get
Plus on both.

| Track | Standard | Plus |
|-------|----------|------|
| 2.1 Digitalisierung | Up to €7,500 | Up to €30,000 |
| 2.2 IT-Sicherheit | Up to €7,500 | Up to €30,000 |

**Recommended combo:** Plus for Digitalisierung (€30K) + Standard for IT-Sicherheit (€7.5K) = **up to €37,500 from Digitalbonus alone.**

The reason: your AI pipeline is where the innovation story lives — that's your
strongest Plus pitch. IT-Sicherheit at Standard level still lets you fund
security hardware and services up to €7.5K.

---

## Track 1: Digitalisierung Plus (Up to €30,000)

This is your flagship application. The project: building and commercializing
the VilseckKI Data Factory — a config-driven synthetic dataset pipeline with
domain-adapted LLMs for EU AI Act compliance data.

### Project Title (Suggestion)

*"Entwicklung einer KI-gestützten Pipeline zur Generierung synthetischer
Trainingsdaten für die EU-AI-Act-konforme Modellvalidierung"*

### Why It Qualifies as "Besonderer Innovationsgehalt"

The Digitalbonus Plus requires you to demonstrate special innovation content.
Your pitch hits multiple criteria they explicitly list:

- Artificial intelligence — domain-adapted LLM with LoRA fine-tuning
- Intelligent data analysis — statistical validation with Evidently AI
- New business model enabled by digitalization — selling synthetic datasets
  on Datarade (Germany) and JDEX (Japan)
- EU AI Act compliance tooling — Article 10 training data documentation

### Creative Eligible Costs — Digitalisierung Track

Hardware is excluded here. But almost everything else about building and
launching the pipeline IS eligible:

**1. GPU Cloud Compute for Fine-Tuning (€6,000–€10,000)**
RunPod, Lambda Labs, or Vast.ai GPU rental for LoRA training runs. At ~€2–4/hr
for an A100, a serious fine-tuning campaign across multiple domain adapters
(German B2B, fisheries, agriculture, medical) adds up fast. Get written quotes.

**2. External Software Development (€8,000–€15,000)**
If you contract any developer work through the UG — pipeline features, web
dashboard, API endpoints, Datarade integration, JDEX onboarding portal. This
can include freelancer invoices or your own salary paid through the UG for
development work on the innovative project.

**3. AI / Data Compliance Consulting (€3,000–€6,000)**
Hire an external consultant to validate your Gebru-style datasheet methodology
against EU AI Act Article 10 requirements. This produces a compliance report
you can use in marketing AND satisfies the Bezirksregierung that you're doing
serious innovation work. Companies like Accenture, PwC, and smaller German
AI compliance boutiques offer this.

**4. Marketplace Integration and Go-To-Market (€2,000–€4,000)**
Datarade seller onboarding fees, JDEX registration, HuggingFace Pro account,
vilseckki.de domain + professional landing page development, marketing
materials. All qualify as digitalization measures introducing new digital
products/services.

**5. Specialized Software Licenses (€2,000–€4,000)**
Evidently AI (if you go beyond the open-source tier), SDV commercial license,
LLM API costs during development (Anthropic/OpenAI for benchmarking against
local models), monitoring/observability tools.

**6. Training and Certification (€1,000–€2,000)**
Coursework or certifications in AI/ML relevant to the project. Some
Bezirksregierungen accept this as part of an innovative digitalization project.

**7. Professional Translation Services (€500–€1,500)**
You're selling in German and Japanese markets. Professional translation of
datasheets, marketplace listings, terms of service, and marketing copy is a
legitimate project cost. Your German is functional but grant-funded professional
translation for client-facing materials is defensible.

### Sample Budget — Digitalisierung Plus

| Cost Item | Amount | Rationale |
|-----------|--------|-----------|
| GPU cloud compute (LoRA fine-tuning, 5 domain adapters) | €8,000 | RunPod A100 hours |
| Software development (pipeline features, dashboard, API) | €14,000 | Internal dev salary or contractor |
| EU AI Act compliance consulting | €4,000 | External consultant report |
| Marketplace integration (Datarade, JDEX, website) | €3,000 | Seller onboarding + vilseckki.de |
| Software licenses and API costs | €3,000 | Evidently, SDV, LLM APIs |
| Professional translation (DE/JA) | €1,000 | Datasheets + marketplace listings |
| Training / certification | €1,500 | Relevant AI coursework |
| **Total eligible costs** | **€34,500** | |
| **Grant at 50%** | **€17,250** | |

To hit the full €30K grant, you'd need €60K in eligible costs. The budget above
is conservative and defensible at ~€17K grant. You could scale it up with more
GPU compute, more consulting, or a larger development scope.

---

## Track 2: IT-Sicherheit Standard (Up to €7,500)

This is the track where **hardware IS explicitly eligible** — but only security
hardware. And here's the creative part: your entire VilseckKI value proposition
IS an IT security argument.

### Why Your Pipeline Is Genuinely an IT Security Project

This isn't a stretch. The core reason VilseckKI exists is:

- Data never leaves the local network (no cloud API calls for production inference)
- DSGVO compliance by architecture (synthetic data, no real PII)
- Client configs and generated datasets contain commercially sensitive information
- You're handling data for potential enterprise clients who require security guarantees

Securing this infrastructure is a legitimate IT security measure.

### Eligible Security Hardware — What You CAN Buy

Under Förderbereich 2.2, the following are explicitly listed as eligible:

**1. Hardware Firewall (€300–€800)**
A dedicated firewall appliance. Options:
- Protectli Vault (pfSense/OPNsense) — ~€300–500
- Ubiquiti UniFi Security Gateway — ~€150–300
- Netgate pfSense appliance — ~€400–800

This sits between your ISP router and your internal network, providing proper
stateful inspection, IDS/IPS, and logging. Essential for any operation handling
client data.

**2. NAS for Encrypted Backup — Datensicherungskomponente (€800–€1,500)**
This is explicitly listed: "Datensicherungs- und Netzwerksicherheitskomponenten."
A NAS configured as encrypted backup infrastructure qualifies:
- Synology DS224+ or DS423 with 2–4TB drives — ~€600–1,200
- Configured with: encrypted volumes, automated backup jobs for generated datasets,
  fine-tuning training data, client configs, and pipeline state
- Bonus: also backs up your development environment

The key: it must be part of a documented IT security concept, not just a generic
storage purchase. Frame it as "encrypted backup infrastructure for protecting
proprietary AI training data and client-specific dataset configurations."

**3. Network Security Components (€200–€600)**
Managed switch for VLAN segmentation:
- Production VLAN (Beelink — AI inference, no internet access)
- Development VLAN (MacBook — internet access, dev tools)
- IoT/guest isolation

A TP-Link or Ubiquiti managed switch is ~€100–300. This is textbook network
security infrastructure.

**4. UPS / Power Protection (€150–€300)**
An uninterruptible power supply for the server and NAS. Data loss prevention
is a security measure. A CyberPower or APC unit runs €150–300.

### Eligible Security Services and Software

**5. External IT Security Audit (€2,000–€3,000)**
Pay an IT security firm to audit your pipeline's data handling, network
architecture, encryption, and access controls. This produces documentation
you'll need for enterprise clients anyway. Companies like TÜV, DEKRA, or
smaller Bavarian IT security consultancies do this.

**6. DSGVO / Data Protection Consulting (€1,000–€2,000)**
Engage an external Datenschutzbeauftragter (data protection officer) to review
your data handling practices, write a Verarbeitungsverzeichnis (processing
register), and confirm your synthetic data methodology doesn't fall under
DSGVO personal data definitions. Essential paperwork.

**7. Encryption and Security Software (€500–€1,000)**
Full-disk encryption tools, certificate management, VPN infrastructure beyond
Tailscale (e.g., enterprise WireGuard with proper key rotation), secure backup
software licenses.

**8. Penetration Testing (€1,500–€2,500)**
External pen test of your network and pipeline. This is the gold standard
for demonstrating you take security seriously, and it's clearly an IT security
service.

### Sample Budget — IT-Sicherheit Standard

| Cost Item | Amount | Category |
|-----------|--------|----------|
| Hardware firewall (pfSense appliance) | €500 | Firewall — explicitly eligible |
| NAS + drives (encrypted backup) | €1,000 | Datensicherungskomponente — explicitly eligible |
| Managed switch (VLAN segmentation) | €250 | Netzwerksicherheitskomponente — explicitly eligible |
| UPS for server + NAS | €200 | Data loss prevention |
| External security audit | €2,500 | External IT security service |
| DSGVO consulting | €1,500 | External data protection service |
| Encryption / security software | €500 | IT security software |
| **Total eligible costs** | **€6,450** | |
| **Grant at 50%** | **€3,225** | |

To hit the full €7,500 Standard grant, you need €15,000 in eligible costs. You
could reach that by adding a pen test (€2K), more extensive security consulting,
or a beefier NAS setup. Even at the conservative €3.2K grant above, you're
getting security infrastructure that you actually need, paid for at half price.

---

## Combined Digitalbonus Strategy

| Track | Variant | Max Grant | Your Realistic Grant | Key Purchases |
|-------|---------|-----------|---------------------|---------------|
| 2.1 Digitalisierung | Plus | €30,000 | €15,000–€20,000 | GPU cloud, dev work, consulting, marketplace |
| 2.2 IT-Sicherheit | Standard | €7,500 | €3,000–€5,000 | Firewall, NAS, network gear, security audit |
| **Digitalbonus Total** | | **€37,500** | **€18,000–€25,000** | |

Add Start?Zuschuss! if you qualify:

| Program | Max Grant | Realistic | Key Purchases |
|---------|-----------|-----------|---------------|
| Digitalbonus (both tracks) | €37,500 | €18K–€25K | Software, services, security hardware |
| Start?Zuschuss! | €36,000 | €10K–€18K | Salary, rent, R&D hardware (Beelink #2), market intro |
| **Grand Total** | **€73,500** | **€28K–€43K** | |

---

## Start?Zuschuss! — Quick Reference

(Detailed in previous version; key updates here)

- **Round 21:** Closed January 9, 2026
- **Round 22:** Expected ~summer 2026, not yet announced
- **Your risk:** UG founded August 2024; 2-year window may expire before Round 22 deadline
- **Action:** Email StMWi NOW to confirm eligibility timing
- **Why it matters:** Start?Zuschuss! is the only realistic path to funding the Beelink hardware itself, since its R&D cost category is much broader

---

## What You Actually Walk Away With

If both Digitalbonus tracks are approved, here's what you get — all at 50% off:

**Physical infrastructure (IT-Sicherheit track):**
- A proper hardware firewall protecting your network
- A NAS with encrypted backup for all your datasets and training data
- Network segmentation (production inference isolated from dev)
- A UPS keeping everything alive during power blips
- A professional security audit report you can show to enterprise clients

**Development acceleration (Digitalisierung track):**
- Hundreds of GPU hours for fine-tuning domain adapters
- Professional EU AI Act compliance consulting + report
- Fully integrated marketplace presence on Datarade and JDEX
- Professional translations for your German and Japanese listings
- A compliance-documented pipeline that enterprise buyers trust

**None of this is make-work.** Every item on both lists is something you'd
either need to buy anyway or would meaningfully accelerate the business.
The grant just means you pay half.

---

## The "Fine-Tuned LLM" Pitch — Framing Notes

For grant applications, frame it accurately:

**German (for Digitalbonus application):**
*"Domänenspezifisch angepasstes Sprachmodell auf Basis offener Foundation-Modelle
(Llama 3.1, Mistral) mit eigenentwickelter Feinabstimmung (LoRA-Adapter) und
proprietären Trainingsdaten. Das Modell läuft vollständig lokal auf eigener
Hardware — kein Datentransfer an externe Cloud-Dienste."*

**What this says honestly:** Domain-adapted language model based on open
foundation models with self-developed fine-tuning and proprietary training data.
Runs entirely locally — no data transfer to external cloud services.

**Why it works:** The base model being open-weight is a feature, not a weakness.
It means no vendor lock-in, no per-token API costs, and full data sovereignty.
The proprietary part is your LoRA adapters, training data curation, validation
pipeline, and domain expertise. That's real innovation.

---

## Application Sequence — Step by Step

### Phase 1: Preparation (March–April 2026)

1. **Check ELSTER status** — if you don't have an ELSTER business account for
   your UG, register at elster.de immediately. Takes 2-3 weeks.
2. **Contact Regierung der Oberpfalz** — the Digitalbonus FAQ explicitly says
   "Wenn Sie planen, einen Digitalbonus Plus zu beantragen, bitten wir Sie,
   sich im Vorfeld an die für Sie zuständige Bezirksregierung zu wenden."
   Call them. Explain the AI pipeline project. Get their informal read on
   whether it qualifies as Plus.
3. **Email StMWi about Start?Zuschuss!** — confirm Round 22 timing and whether
   your August 2024 founding date still qualifies.
4. **Collect vendor quotes:**
   - RunPod/Lambda Labs: GPU cloud pricing for A100 hours
   - 2-3 IT security consulting firms: quotes for security audit
   - 1-2 DSGVO consultants: quotes for data protection review
   - Firewall, NAS, switch: product links with prices (Amazon.de is fine)

### Phase 2: Digitalbonus Submission (April–May 2026)

5. **Write the Digitalisierung Plus project description** (2-3 pages)
   - Current state: MVP pipeline exists, runs on local hardware
   - Innovation: domain-adapted LLM, EU AI Act compliance datasheets,
     dual-market (DE + JP) synthetic data marketplace
   - Timeline: 12 months
   - Budget: itemized with vendor quotes attached
6. **Write the IT-Sicherheit Standard project description** (1-2 pages)
   - Current state: pipeline handles sensitive client configs and generated
     datasets with no formal security infrastructure
   - Measure: implement network segmentation, encrypted backup, external
     security audit, DSGVO compliance review
   - Timeline: 6 months
   - Budget: itemized with product links and consulting quotes
7. **Submit both applications** via ELSTER — ideally early in the month
   (monthly contingent)

### Phase 3: Execution (After Eingangsbestätigung)

8. **Wait for entry confirmation** — do NOT purchase anything before this
9. **Execute IT-Sicherheit first** — buy firewall, NAS, switch; schedule
   security audit. This is faster and gives you infrastructure.
10. **Execute Digitalisierung in parallel** — begin GPU cloud fine-tuning
    runs, marketplace integration, consulting engagement.
11. **Keep all invoices** — every single one, including GPU cloud receipts

### Phase 4: Start?Zuschuss! (Summer 2026, If Eligible)

12. **Apply for Round 22** when announced — this is your hardware play
    (second Beelink, potentially) and salary funding
13. **Prepare a polished pitch** — the jury is competitive; your EU AI Act
    angle and international market approach need to shine

### Phase 5: Closeout

14. **Submit Verwendungsnachweis** for each Digitalbonus track after
    project completion — all invoices, proof of payment, brief report
15. **Receive grant payment** — the money comes AFTER you've spent and
    documented everything

---

## Key Risks — Updated

| Risk | Severity | Mitigation |
|------|----------|------------|
| Bezirksregierung rejects NAS as "standard hardware" | Medium | Frame it as Datensicherungskomponente in documented IT security concept, not as generic storage |
| Plus innovation threshold not met | Medium | Pre-consult with Regierung der Oberpfalz (they recommend this) |
| Start?Zuschuss! 2-year window expired | Medium-High | Email StMWi immediately to clarify |
| Verbot des vorzeitigen Maßnahmebeginns | High | Absolutely do not buy anything before Eingangsbestätigung |
| GPU cloud costs hard to quote upfront | Low | Get RunPod/Lambda pricing sheets; estimate hours conservatively |
| De-minimis ceiling | Low | All three grants combined (~€73K) well under €300K 3-year limit |
| Bezirksregierung reviewer unfamiliar with AI | Medium | Write in plain business German; avoid jargon; emphasize EU AI Act regulatory driver |

---

## Micro-SaaS Opportunity Note

This grant infrastructure directly supports your broader micro-SaaS strategy.
The compliance consulting reports, security audit documentation, and marketplace
presence you fund through Digitalbonus become reusable assets across multiple
products. The security infrastructure (firewall, NAS, network segmentation)
benefits not just the Data Factory but also the EHCP Audit, Assessment Wizard
private cloud, and any future VilseckKI RAG-as-a-Service clients. Think of the
grant-funded security stack as shared infrastructure for the entire UG.

---

## Sources

- [Digitalbonus Bayern — Förderprogramm](https://www.digitalbonus.bayern/foerderprogramm/)
- [Digitalbonus Bayern — Antragstellung](https://www.digitalbonus.bayern/antragstellung/)
- [Digitalbonus Bayern — Häufige Fragen](https://www.digitalbonus.bayern/haeufige-fragen/)
- [Digitalbonus Vollzugshinweise (PDF, V3, May 2025)](https://www.digitalbonus.bayern/fileadmin/user_upload/digitalbonus/dokumente/Vollzugshinweise_Digitalbonus.pdf)
- [Digitalbonus Förderrichtlinie (PDF)](https://www.digitalbonus.bayern/fileadmin/user_upload/digitalbonus/dokumente/F%C3%B6rderrichtlinie_Digitalbonus.pdf)
- [Start?Zuschuss! — StMWi](https://www.stmwi.bayern.de/wettbewerbe/startzuschuss/)
- [Förderdatenbank — Digitalbonus](https://www.foerderdatenbank.de/FDB/Content/DE/Foerderprogramm/Land/Bayern/digitalbonus.html)
- [IT-Sicherheit mit Digitalbonus — IIVP](https://iivp.de/foerdermittel-fuer-it-sicherheit/digitalbonus-bayern/)
- [IT-Sicherheit ISO 27001 mit Digitalbonus — Acato](https://acato.de/digitalbonus-bayern/)
