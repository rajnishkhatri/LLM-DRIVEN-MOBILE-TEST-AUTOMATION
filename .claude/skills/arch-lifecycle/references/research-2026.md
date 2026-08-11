# External research — agentic architecture workflows, 2025–2026

Deep-research run 2026-07-24 (105 agents; 23 sources fetched; 110 claims
extracted; 25 adversarially verified: 24 confirmed / 1 killed; synthesized
to 9 findings). Confidence labels are the verification pipeline's, not
vibes. This file records what the arch-* family adopted, adapted, or
rejected, and what remains unvalidated.

## Headline

The staged, human-gated micro-loop design has **no off-the-shelf equivalent
to copy** in the visible 2025–2026 landscape. Thoughtworks Haiven — the
most-cited GenAI architecture assistant — is by its own README "a sandbox to
lower the barrier to experiment," a single-container chat app with pluggable
knowledge packs (prompt libraries + domain-context folders) and one-shot
architecture prompts; no staged workflows, no approval gates
[high; github.com/tw-haiven/haiven]. Its knowledge-pack separation of
app-vs-domain context independently parallels our `.arch/binding.toml`
pattern — validation, not a source to borrow from.

## Adopted into the skills

1. **Progressive-disclosure budget** [high;
   platform.claude.com/docs/…/agent-skills/overview]: metadata always loaded
   (~100 tokens/skill), SKILL.md body <5k tokens on trigger, references/
   zero-cost until read. Audited 2026-07-24: all seven arch-* SKILL.md
   bodies are ~1.1–1.4k tokens. Note: the claim that the `description`
   field is the *sole* trigger mechanism was **refuted (0-3)** — treat
   description design as one discoverability lever, not the only one.
2. **ADR context window (arch-decide)** [medium — single peer-reviewed
   study, EASE 2026, arXiv 2604.03826]: context engineering dominates model
   scale for ADR generation quality; injecting the **last 3–5 accepted
   ADRs** achieves near-parity with full decision history (BERTScore F1
   0.8375 vs 0.8379). Adopted as arch-decide's default context recipe, with
   retrieval fallback for cross-cutting decisions. Caveat: fidelity was
   measured by similarity metrics, not downstream decision quality.

## Corrections applied to arch-risk

3. **Lens "independence" is largely illusory** [high; Apple ML preprint
   arXiv 2605.29800 + AWS RoPoLL arXiv 2606.30931, two independent
   primaries]: a 9-judge panel across 7 model families yields only ~2.2
   effective independent votes (Kish n_eff); inter-judge correlation
   0.45–0.53; varied prompts/temperature do nothing (n_eff 2.15–2.18) and
   chain-of-thought *increases* correlation (φ .391→.456). Correction:
   frame the phase-1 lenses as **coverage/decomposition** (each examines a
   different risk dimension), never as independent scorers; cap the panel
   at 3–5; claim no bias reduction from panel size. Transfer caveat: these
   results are from redundant classification/pairwise voting — lens-based
   coverage of *different* dimensions is exactly the design that escapes
   the redundancy critique.
4. **Never merge scores by mean** [medium; RoPoLL + Apple]: mean
   aggregation accumulates bias under mode collapse/sycophancy and N
   doesn't fix it; geometric median has a ½ breakdown point (at N=3 it's
   the plain median, tolerating one corrupted lens). Smarter aggregation
   can't repair correlated inputs (established methods close ≤11% of the
   Condorcet gap even with oracle labels). Correction: **median merge +
   surface per-lens disagreement raw** to the human arbiter.
5. **Deliberation only where lenses disagree** [high; NeurIPS 2025,
   openreview Vusd1Hw2D9]: multi-agent debate beats majority vote only on
   high-initial-disagreement items (77.75%→81.83% on LLMBar); on agreed
   items it adds cost, sometimes harm (counter-example in-paper: debate
   74.0% vs majority 81.8%). Correction: consensus discussion is
   **conditional** — divergent or single-lens cells only; agreed cells go
   straight to the human gate.
6. **Simulated deliberation doesn't genuinely converge** [low — single
   preprint, arXiv 2605.01986, N=3/cell; directionally corroborated by the
   conformity literature]: persona agents anchored (17/18 hung juries) —
   and the mirror failure, sycophantic premature consensus, is documented
   elsewhere. Correction: **log initial vs final lens positions** to detect
   both anchoring (no movement) and conformity cascade (instant collapse);
   human arbitration of the merge is vindicated, not optional.
7. **Panel composition** [medium; Cohere PoLL arXiv 2404.18796 read
   against finding 3]: disjoint-model-family panels mitigate
   *self-preference* specifically (a GPT-4 judge ranked a GPT-4 variant
   2 vs human-derived 4), not correlation generally (cross-family φ≈0.389).
   Cross-family lenses are worthwhile only if genuine vote redundancy is
   desired. **No permanent single scorer** across stages [medium; Wells
   Fargo jury-on-demand, arXiv 2512.01786]: the best judge on one
   task-metric can be among the worst on another.

## Explicitly NOT validated by this research (still book-sourced only)

- **Fitness-function generation by agents** (ArchUnit/PyTestArch/TSArch
  from ADRs or diagrams), LLM conformance/drift detection: **no claims
  survived verification.** arch-validate's governance wiring rests on
  Richards & Ford, not on verified agentic-tooling evidence.
- **Human-gate integrity countermeasures** (rubber-stamping, sycophancy at
  gates): no surviving verified claims. The no-auto-advance doctrine is
  plausible but empirically unbenchmarked — treat gate hygiene as an open
  design risk, not solved.
- **Landscape beyond Haiven** (cloud well-architected review agents,
  AI-ADR products): nothing survived verification; re-research when needed.

## Time sensitivity

The correlation/aggregation results are <3 months old (as of 2026-07-24)
and may be revised; the field moves monthly. Re-run the research before
treating the specific numbers (n_eff 2.2, γ̄ 0.45–0.53, Last_K 3–5) as
constants.
