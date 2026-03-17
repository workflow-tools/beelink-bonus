# Per-Project Mistral Integration Plans

## 1. Dissertation + EHCP (GRUND Framework)

### Mistral's Role
- **Local inference leg:** Mistral models on Beelink are one arm of the 2x2 factorial design
- **Literature monitoring:** Agents API or Le Chat Deep Research on weekly cadence
- **Cross-checking:** Use Think mode to validate GRUND methodology decisions

### Specific Actions
- [ ] Pull Mistral Small 4 and Mistral 14B on Beelink for GRUND experiments
- [ ] Create EHCP Reviewer Modelfile (see OLLAMA-CONFIGS.md)
- [ ] Set up Le Chat "Dissertation" project with GRUND context
- [ ] Prototype Agents API literature monitor (see AUTOMATION-IDEAS.md #2)
- [ ] Test Mistral Agents API handoffs as a GRUND multi-agent debate implementation

### Publishable Angle
Comparing Claude vs Mistral model families in the multi-agent debate framework is a natural extension of the GRUND evaluation. Document methodology carefully.

---

## 2. Data Factory (VilseckKI)

### Mistral's Role
- **Demand intelligence:** Le Chat Deep Research + eventual Agents API automation
- **Text generation:** Mistral 7B on Beelink for volume text augmentation (already planned)
- **Quality variety:** Using multiple model families for text gen reduces stylistic monoculture in datasets

### Specific Actions
- [ ] Configure Le Chat "Data Factory" project (instructions already written)
- [ ] Run first demand intelligence cycle (see DEMAND-INTEL.md workflow)
- [ ] Create datafactory-de Modelfile (see OLLAMA-CONFIGS.md)
- [ ] Test Mistral 7B vs llama3.1:70b for German text quality on Beelink
- [ ] Prototype demand-intel-agent.py (see examples/)

### Revenue Connection
Every demand signal that converts to a YAML config that generates a dataset that sells on Datarade is directly attributable to this workflow.

---

## 3. Rebeka

### Mistral's Role
- **Code review:** Vibe for TypeScript/Supabase code review alongside Claude
- **Market research:** Le Chat Deep Research for new country expansions
- **Test generation:** Vibe for generating Vitest test suites

### Specific Actions
- [ ] Install Vibe, test on rebeka-app codebase
- [ ] Set up Le Chat "Rebeka" project
- [ ] Use Vibe to generate test coverage for existing modules
- [ ] Use Le Chat Deep Research for next market expansion (Nepal NNC is #2 priority)

---

## 4. FarAfield

### Mistral's Role
- **Minimal:** Lower priority project
- **Scaffolding:** Vibe for quick file generation when needed
- **Market data:** Le Chat for nurse migration pathway research (PH→JP, etc.)

### Specific Actions
- [ ] Set up Le Chat "FarAfield" project (low priority)
- [ ] Use Vibe only for one-off scaffolding tasks

---

## 5. Beelink Infrastructure

### Mistral's Role
- **Health monitoring:** Agents API prototype for remote Beelink monitoring
- **Model management:** Le Chat for researching new model releases and compatibility
- **Optimization:** Le Chat Think mode for ROCm/Vulkan performance tuning research

### Specific Actions
- [ ] Prototype Beelink health monitor agent (see AUTOMATION-IDEAS.md #5)
- [ ] Set up Le Chat "Beelink Infrastructure" project
- [ ] Use Le Chat to track Ollama + ROCm compatibility updates for AMD AI Max+

---

## Implementation Priority

Start with the highest-value, lowest-effort integrations:

1. **Week 1:** Install Vibe on MacBook, configure Le Chat Projects (Data Factory + Dissertation)
2. **Week 2:** Run first demand intelligence cycle, start logging Vibe experiments
3. **Week 3:** Pull Mistral models on Beelink (requires Tailscale setup first), run benchmarks
4. **Week 4:** Prototype one Agents API automation (demand-intel-agent.py)
5. **Ongoing:** Log experiments, refine division of labor, expand to other projects
