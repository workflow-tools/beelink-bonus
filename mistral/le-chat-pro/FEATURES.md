# Le Chat Pro — Feature Investigation

## Subscription: $14.99/month (active)

## Features to Leverage

### 1. Deep Research
- Tool-augmented research agent that searches, reads, and synthesizes
- Produces structured research reports
- **Best for:** Market research, regulatory landscape analysis, competitive intelligence
- **Current use:** Ad-hoc via Le Chat web interface
- **Optimization:** Set up recurring Deep Research tasks for Data Factory demand intelligence

### 2. Think Mode (Magistral)
- Powered by Magistral reasoning model
- Step-by-step reasoning for complex problems
- **Best for:** Debugging logic, validating architectural decisions, cross-checking Claude's reasoning
- **Current use:** Not systematically used
- **Optimization:** Use for cross-checking GRUND framework design decisions

### 3. Projects (up to 1,000)
- Scoped context containers — each project gets its own instruction set and document library
- Up to 15GB document storage across all projects
- **Best for:** Giving Le Chat project-specific context without re-explaining every session
- **Current use:** Data Factory has LECHAT-PROJECT-DESCRIPTION.md ready to paste
- **Optimization:** Create projects for each major repo (see PROJECTS-SETUP.md)

### 4. Mistral Vibe (included)
- Terminal coding agent — see vibe-coding/ directory
- Daily usage limits apply on Pro plan

### 5. Vocal Mode (Voxtral)
- Low-latency voice input via Voxtral model
- **Potential use:** Voice-to-text for dissertation notes while walking/commuting
- **Potential use:** Dictating ideas while doing childcare (4 kids = lots of multitasking)
- **Worth testing:** How well does it handle English with German/Japanese terms mixed in?

### 6. Canvas
- Collaborative editing space within Le Chat
- **Potential use:** Drafting Data Factory YAML configs interactively
- **Potential use:** Iterating on GRUND framework diagrams

### 7. Image Generation
- FLUX1.1 Pro Ultra
- **Potential use:** Marketing visuals for VilseckKI landing page
- **Potential use:** Diagram generation for dissertation figures

## Limits to Verify

- [ ] Messages per day on Pro plan
- [ ] Deep Research reports per day
- [ ] Vibe usage limits
- [ ] Document storage per project vs total
- [ ] API access included with Pro (if any beyond Vibe)
