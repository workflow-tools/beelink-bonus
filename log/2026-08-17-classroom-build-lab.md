# 2026-08-17 — Classroom Build Lab design study

**Session type:** exploration → design study (Opus, ultracode). Branch
`claude/ollama-beelink-dashboard-n6elb6`, restarted from main after PR #2 merged.

**Question:** could a class of high school students each build a personal app over four
weeks, using a permitted cloud LLM plus access to the Beelink — and how would that be
architected, for a teacher of any subject (FCS, English, social science, art, PE, CS)?

**Method:** 14-agent workflow — six research dimensions (compliance, capacity, workspace,
deployment, pedagogy, safety), each with an adversarial verifier, then synthesis, then a
hostile review pass. The review falsified several claims in the synthesis, including its
own header claim that everything had survived verification. A follow-up verification agent
checked four high-stakes claims against primary sources. Deliverable:
`docs/CLASSROOM-BUILD-LAB.md`.

**Three design decisions made mid-session that reshaped the architecture:**

1. **Self-built portal** rather than direct model access. This fixed two flaws the reviewer
   found in the workflow's own design: it had students running an agentic CLI on managed
   Chromebooks that cannot run one, and treated a system prompt as a control while students
   ran their own clients.
2. **Beelink sited at the school** on an isolated segment. Removes the tunnel provider as a
   plaintext US processor, the cross-border transfer, and the residential-IP traffic pattern
   that reads as exfiltration to a security team.
3. **No interaction logging.** Content retention zero; operational metadata only; safety
   classification stateless. Git history serves as the process record.

**Verified findings that changed conclusions:**

- **Anthropic's Usage Policy explicitly permits the portal pattern** — organizations may
  give minors access to products incorporating the API, subject to named requirements (age
  verification, content filtering, monitoring, AI disclosure, child-privacy compliance).
  This is the single most useful finding: a student cannot hold a Claude account, but a
  teacher can build an app that serves students.
- **The "UG as vendor" advice given earlier in the session was wrong for the federal case.**
  FAR 3.601(a) bars awarding to a business substantially owned by a Government employee;
  FAR 3.602's exception needs "a most compelling reason." Nuance: 18 U.S.C. § 208 imputes a
  *spouse's* interest, creating a recusal duty rather than a categorical bar — so the
  currently-real situation differs from the hypothetical.
- **EU AI Act Art. 5(1)(f) does not prohibit a text-based crisis classifier.** Art. 3(39)
  scopes it to biometric data, and Commission guidance states inferring emotions from
  written text is outside the prohibition. Separately, Annex III high-risk *deployer*
  obligations were postponed to 2 December 2027 by Regulation (EU) 2026/1744.
- **GitHub Classroom retires 28 August 2026** (11 days after this session), data deleted
  4 September. Do not build on it.
- **Hardware correction to this repo's CLAUDE.md:** the iGPU is a Radeon 8060S (gfx1151),
  40 CUs — not the 890M, which is the 16-CU Strix Point part. Table corrected.

**Errors the hostile review caught in the first synthesis** (all corrected in the doc):
electricity overstated ~45% from its own inputs; a gateway per-key parallel limit returns
429 rather than queueing, so the stated burst defense causes retry amplification; a
four-model memory budget summing to ~102 GB against a ~100 GB ceiling; a guard model
described as free on "idle CPU cores" when unified memory shares bandwidth; and a unit
sized for one section when a teaching load is 120–160 students.

**The untested assumption everything rests on:** whether a 27B open-weights model can
reliably drive a multi-file agentic coding loop. One afternoon settles it, and it is
verification item #1.

**Bottom line:** the unit is good and the revised architecture is sound; what remains is
jurisdictional. At a US federal school the self-built-system version stays hard (FERPA
direct control, ATO, and Section 508 conformance, which arrives before privacy does). At a
private/international school or an out-of-school cohort it works.
