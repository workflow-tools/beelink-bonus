# UK EHCP Tribunal Scraping — Insights & Instructions

## Why This Matters for Your Dissertation

Your PhD research on automating the indie developer pipeline from idea to marketable SaaS needs realistic test data. If your dissertation involves generating synthetic EHCP (Education, Health and Care Plan) documents — complete with the authentic flaws that trigger tribunal appeals — then mining published tribunal decisions is the same "court records as intelligence source" pattern that powers the Japan/Germany real estate scrapers.

The flaw taxonomy you extract becomes both dissertation data and a potential product (feeding into IEP Advocate, idea #12 in the pipeline).

---

## The EHCP Document Structure

An EHC Plan has 9 sections. Sections B, E, F, and I are appealable to the SEND Tribunal:

| Section | Content | Appealable |
|---------|---------|-----------|
| **A** | Child/young person views, interests, aspirations | No |
| **B** | Special educational needs (SEN) | Yes |
| **C** | Health care needs relating to SEN | No |
| **D** | Social care needs relating to SEN/disability | No |
| **E** | Outcomes sought | Yes |
| **F** | Special educational provision to meet SEN | Yes |
| **G** | Health care provision | No |
| **H** | Social care provision | No |
| **I** | Education placement (school/setting) | Yes |

The "Golden Thread" principle: every need in Section B must have a corresponding, specified, quantified provision in Section F, linked to a measurable outcome in Section E, deliverable at the placement in Section I. When this thread breaks, tribunals get involved.

---

## What Goes Wrong (The Flaw Taxonomy You're Mining For)

These are the categories of errors that lead to ~10,500 tribunal appeals annually. Councils lose the vast majority of these appeals, indicating pervasive drafting deficiencies:

### Section B (Needs) Flaws
- Vague or generic descriptions of needs ("has difficulty with reading")
- Incomplete identification — missing entire areas of difficulty
- Failure to specify nature, severity, or impact
- Needs described in terms of provision rather than the child's difficulties
- Contradictions between professional assessments and what's recorded

### Section F (Provision) Flaws — THE most common appeal ground
- Insufficient specification: "access to" instead of "3 hours per week of"
- Insufficient quantification: "regular input" instead of "45 minutes, 3x weekly"
- Vague language: "opportunities for," "as needed," "where appropriate"
- Missing detail on who delivers (qualifications, training requirements)
- No clarity on group size (1:1 vs. small group vs. whole class)
- Provision not linked to specific needs in Section B
- Non-enforceable wording (aspirational rather than mandatory)

### Section E (Outcomes) Flaws
- Unmeasurable outcomes ("will improve reading")
- Outcomes that describe provision rather than goals
- Missing timescales for achievement
- Not aligned with identified needs

### Section I (Placement) Flaws
- Named school cannot meet identified needs
- Inadequate provision available at the specified setting
- Mismatch between Sections B/F and what the placement offers

### Structural/Process Flaws
- Failure to consult required professionals during assessment
- Not incorporating parental views into Section A
- Annual reviews not reflected in updated plan
- Transition planning missing for post-16/post-18

---

## Data Sources for Scraping

### Tier 1: Published Upper Tribunal Decisions (best for scraping)

**The National Archives — Find Case Law**
- URL: https://caselaw.nationalarchives.gov.uk/
- Coverage: Judgments and tribunal decisions from April 2022 onwards
- Includes: Health, Education and Social Care Chamber decisions
- Format: HTML pages with structured metadata
- Scraping feasibility: HIGH — public government site, structured HTML

**BAILII (British and Irish Legal Information Institute)**
- URL: https://www.bailii.org/
- Coverage: Historic tribunal decisions (pre-April 2022)
- Includes: Upper Tribunal SEND/EHCP decisions
- Format: HTML with some structure
- Scraping feasibility: HIGH — established legal information institute, designed for access
- Database listing: https://www.bailii.org/databases.html

**Courts and Tribunals Judiciary**
- URL: https://www.judiciary.uk/judgments/tribunal-decisions/
- Coverage: Selected significant tribunal decisions
- Scraping feasibility: MEDIUM — less structured than BAILII

**Wales SEND Tribunal (bonus)**
- URL: https://specialeducationalneedstribunal.gov.wales/
- Publishes decisions by school year in PDF format
- Scraping feasibility: HIGH for Welsh cases specifically

### Tier 2: First-tier Tribunal Decisions (harder to access)

First-tier SEND Tribunal decisions are NOT routinely published online. They constitute ~90% of all EHCP tribunal cases but are not in searchable databases. Options:

- **FOI requests** to HM Courts & Tribunals Service — labour-intensive but legally valid
- **Partnership with advocacy organisations** (IPSEA, SEN Legal, Contact) who compile cases
- **Published case studies** from SEND advocacy websites

### Tier 3: Supplementary Intelligence (no scraping needed)

These provide the "what goes wrong" intelligence without needing tribunal decisions:

- **IPSEA guides**: https://www.ipsea.org.uk/ — detailed analysis of common EHCP failures
- **SEN Legal resources**: https://www.senlegal.co.uk/ — practitioner insights
- **Local Government & Social Care Ombudsman reports**: published investigations into LA SEND failures
- **Ofsted/CQC SEND area inspections**: published reports identifying systemic weaknesses
- **Council for Disabled Children**: https://councilfordisabledchildren.org.uk/

---

## Scraping Architecture

### Phase 1: Upper Tribunal Decisions (immediate)

Build a scraper for caselaw.nationalarchives.gov.uk targeting the Health, Education and Social Care Chamber. Search for EHCP/SEND-related keywords.

**Suggested search terms:**
- "education health care plan"
- "EHC plan" OR "EHCP"
- "special educational needs" AND "provision"
- "Section F" AND "specify" OR "quantify"
- "Section I" AND "placement"
- "annual review" AND "SEND"
- "SEND tribunal" AND "appeal"
- "working document" (common term for draft EHCPs under dispute)

**Expected structure on National Archives:**
- Case title, neutral citation, court/tribunal, date
- Full text of the decision in HTML
- Structured metadata (judge, parties anonymised, legislation cited)

**Extraction targets (same pattern as Japan/Germany scrapers):**
1. **Document type references** — which real documents are cited (the EHCP itself, professional reports, LA decision letters, annual review minutes)
2. **Flaw patterns** — what the tribunal found wrong (vague provision, missing quantification, unlinked needs/provision, procedural failures)
3. **Section-specific errors** — which EHCP section the flaw appears in (B, E, F, I)
4. **Remedy patterns** — what the tribunal ordered the LA to fix

### Phase 2: BAILII Historic Decisions

Scrape BAILII for pre-2022 Upper Tribunal SEND decisions to expand the corpus. BAILII has a well-known HTML structure used by legal researchers.

### Phase 3: Supplementary Sources

Parse IPSEA/SEN Legal guidance documents for structured flaw descriptions. These aren't tribunal decisions but provide expert-curated flaw taxonomies that complement the scraped data.

---

## Flaw Pattern Extraction — Regex Patterns for EHCP Text

```python
EHCP_FLAW_PATTERNS = [
    # Specification/quantification failures (Section F)
    (r"fail(?:ed|s|ure)?\s+to\s+(?:specify|quantify)", "insufficient_specification"),
    (r"(?:not|insufficiently)\s+(?:specified|quantified)", "insufficient_specification"),
    (r"(?:vague|unclear|imprecise)\s+(?:provision|wording|language)", "vague_provision"),
    (r"(?:access to|opportunities for|as (?:needed|appropriate))", "non_specific_language"),

    # Needs-provision mismatch
    (r"(?:no|without)\s+(?:corresponding|matching)\s+provision", "unlinked_need"),
    (r"(?:need|needs)\s+(?:not|inadequately)\s+(?:addressed|met|reflected)", "unmet_need"),
    (r"(?:provision|support)\s+(?:does not|fails to)\s+(?:address|meet|reflect)", "provision_mismatch"),

    # Outcomes issues (Section E)
    (r"(?:outcome|outcomes)\s+(?:not|are not)\s+(?:measurable|specific|achievable)", "unmeasurable_outcome"),
    (r"(?:no|without)\s+(?:clear|specific)\s+(?:outcome|target)", "missing_outcome"),

    # Procedural failures
    (r"fail(?:ed|ure)?\s+to\s+(?:consult|consider|have regard)", "procedural_failure"),
    (r"(?:not|did not)\s+(?:consult|seek|obtain)\s+(?:advice|assessment|report)", "missing_consultation"),
    (r"annual\s+review\s+(?:not|was not)\s+(?:conducted|carried out|completed)", "annual_review_failure"),

    # Placement issues (Section I)
    (r"(?:school|setting|placement)\s+(?:cannot|unable to|does not)\s+meet", "placement_mismatch"),
    (r"(?:inadequate|insufficient)\s+(?:provision|support)\s+at\s+(?:the|named)", "placement_inadequate"),

    # Assessment failures
    (r"(?:assessment|evaluation)\s+(?:not|was not)\s+(?:carried out|completed|adequate)", "assessment_failure"),
    (r"(?:professional|specialist)\s+(?:advice|assessment)\s+(?:not|was not)\s+(?:sought|obtained)", "missing_professional_input"),
]
```

---

## Expected Yield & Limitations

**Scale comparison with Japan/Germany:**

| Metric | Japan (courts.go.jp) | Germany (dejure.org) | UK EHCP (Upper Tribunal) |
|--------|---------------------|---------------------|--------------------------|
| Total accessible decisions | 2,000+ per query | 7,000+ per BGB section | ~300/year Upper Tribunal |
| Scraping infrastructure | GET requests, clean HTML | Paginated lists, redirect links | National Archives HTML |
| Full text availability | PDFs (need extraction) | Via openjur.de/BGH links | Inline HTML (easier) |
| API access | None | OLDP REST API (251K) | Limited GOV.UK API |
| Primary limitation | PDF text extraction | Cookie consent handling | Small published corpus |

**The UK corpus is smaller but the flaw intelligence is richer per decision.** Upper Tribunal SEND decisions are detailed, often 20-50 pages, with section-by-section analysis of what the LA got wrong. A single decision might identify 5-10 distinct flaw patterns.

**Practical estimate:** 200-500 published Upper Tribunal EHCP decisions accessible between BAILII and the National Archives. With 5-10 flaw patterns per decision, that's 1,000-5,000 flaw instances for taxonomy building — sufficient for a dissertation-quality dataset.

---

## Dissertation Integration

This scraping work directly supports your dissertation in several ways:

1. **Methodology demonstration:** "I built a pipeline that extracts domain intelligence from public legal records and translates it into synthetic data generation parameters" — this IS the indie developer automation thesis in action

2. **Data generation:** The flaw taxonomy enables generating realistic synthetic EHCPs with authentic errors at real-world frequencies, giving you a training/evaluation dataset for whatever ML system you're building

3. **Validation:** If your synthetic EHCPs with court-derived flaws are indistinguishable from real EHCPs to domain experts (SEN professionals), that validates the entire pipeline methodology

4. **Publication angle:** "Court-Derived Flaw Taxonomies for Domain-Aware Synthetic Document Generation" is a publishable contribution independent of the broader dissertation

5. **Cross-pollination with IEP Advocate:** The EHCP flaw taxonomy feeds directly into the compliance checking engine, creating a feedback loop between research and product

---

## Next Steps

1. **Explore the National Archives site via Chrome** — map the HTML structure for EHCP-related Upper Tribunal decisions the same way we mapped courts.go.jp and dejure.org
2. **Build a `uk_tribunals.py` scraper** following the same architecture as `japan_courts.py` and `germany_courts.py`
3. **Extract flaw taxonomy** from published decisions
4. **Cross-reference with IPSEA/SEN Legal guidance** to fill gaps where First-tier decisions aren't published
5. **Generate synthetic EHCPs** using the flaw taxonomy to drive the synth-factory error injection system
