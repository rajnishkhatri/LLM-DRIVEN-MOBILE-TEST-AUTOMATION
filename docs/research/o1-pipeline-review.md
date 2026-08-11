# O1 Pipeline Walkthrough — Critical Review (2026-07-31)

**Reviewed artifact:** `docs/research/o1-pipeline-walkthrough.md` (887 lines; Part I spine walkthrough + Part II ASH-Capture proposal) and its rendered `o1-pipeline-walkthrough.html`.
**Baseline it was verified against:** `docs/sdd/specs/mobile-test-automation-spine.spec.md` (signed off 2026-07-27), `docs/sdd/plans/mobile-test-automation-spine.plan.md` (PLAN-OK 2026-07-28), `blueprint-revision-v2.md`, ADRs 0001–0013.
**Method:** 7-agent review (ground baseline → automation audit ∥ consistency ∥ ASH design ∥ security → adversarial verification → synthesis). All 28 findings below are **CONFIRMED** — each survived an adversarial verify pass against both the walkthrough and the baseline; misquoted or unsupported candidates were dropped.
**Requested by:** the user's ask — *"first check whether pipeline is fully automated with least human intervention; call out where human intervention is required; ask hard questions for improving and refining the pipeline."*
**Consumed by:** Replan R1 in `docs/sdd/plans/mobile-test-automation-spine.tasks.md` (routing of every finding to editorial fix / ADR decision / spike).

---

## 1. Automation verdict

**No — and the walkthrough conflates two different "automation" answers it never separates.**

**As approved (Phase 1 / spine baseline), the human is the orchestrator at every stage by design** (blueprint-revision-v2.md:41, :49). Per test on the happy path there are roughly **4–6 human touchpoints**: run the ingestion CLI, run hierarchy-tool against a live device for every screen (ASH-Capture is a same-day proposal, not built), invoke /generate-test, review + commit the generated Java, trigger CI — plus, for **every** conversion, a human evaluator validating the result against original intent (walkthrough §7). Add one touch per static-gate failure, per capture failure (escape hatch), per FLAKY/UNKNOWN verdict (owner unspecified anywhere), and per evaluator-FAIL iteration, which loops the whole conversion back to A0 with no stated bound.

**Two of these touchpoints are deliberate, load-bearing controls that should stay**: engineer review + commit (the commit *is* the audit pin, §5) and human evaluation/certification (CF9, spec.md:386 — judge advisory, certification an attributable individual decision). The rest is incidental Phase-1 labor that Phase 2 explicitly automates behind confidence gates and an HITL queue (blueprint:55–67) — but Phase 2 is gated on 50–100 human-certified conversions (blueprint:107–109), so the human cost is the price of admission, not a bug.

**Per release**: drift re-discovery is automated with human spillover through the escape hatch — claimed <10%, unmeasured, and the confirmed discovery-termination defect means ~20% of screens deterministically land there each release, exactly when demand peaks. **One-time**: ADR 0014, an ADR 0010 security-review queue entry (non-blocking but must drain before first production release), and the measurement spike.

**Net**: the compute stages are genuinely automated; authoring commit and certification are human-gated on purpose; and the walkthrough overstates automation by presenting end-state behavior (K-runs, auto-capture, ~90% graph replay) as current fact while never totaling its own recurring human costs.

---

## 2. Human-intervention map

| # | Human intervention | Frequency | Deliberate control vs incidental | Automatable? |
|---|---|---|---|---|
| 1 | Phase-1 orchestration: run ingestion CLI, run hierarchy-tool per screen, invoke /generate-test, trigger CI, feed ReplayReport to /diagnose-replay (§3, §6.1; blueprint:49) | Per test, multiple touches each — the dominant recurring cost | Incidental by explicit design ("The human is the orchestrator", blueprint:41) | Yes — that IS Phase 2 ("replaces the human driver with orchestration code. Nothing else moves", blueprint:55); the walkthrough never states which phase it describes, so this cost is invisible in the doc |
| 2 | Engineer reviews, adjusts, commits generated Java (§5:184–187) | Per IR version (every test, every regeneration — including regenerations after drift repair rewrites a manifest, a cascade the doc never mentions) | **Deliberate** — the commit is the audit pin; dropping review hollows out the doc's central auditability claim | Phase 2 replaces it with confidence gates + HITL for sub-threshold cases only (blueprint:63); not before the flywheel holds 50–100 certified conversions |
| 3 | Human evaluator validates EVERY conversion against original intent, PASS/FAIL (§7:281–287) | Per conversion, per iteration — FAIL loops to A0 with **no bound** | **Deliberate** — the CF9 shape (spec.md:386) and the source of the flywheel's labels | Partially: Phase-2 judge advises only after TPR/TNR >90% calibration against these very human labels; the certify decision must stay human |
| 4 | Escape-hatch manual navigation on capture failure (§11.8) | Claimed <10% of captures, unmeasured — the confirmed termination defect makes ~20% of screens per release deterministic escape-hatch cases | Incidental but structurally irreducible under the no-app-team-cooperation constraint (§11.11) | Partially (app-team title IDs, learned fingerprints — §11.11's own fallbacks); bucket must be measured before <10% is believable |
| 5 | Static-gate failure loop: engineer re-prompts Copilot until pass (§6.1:232) | Per failed generation, uncounted | Incidental — the gate is the control, the loop labor is not | Yes — ADR 0003's Phase-2 orchestrator (3 static repairs then HITL); walkthrough says "bounded retries" with no numbers |
| 6 | FLAKY/UNKNOWN triage + ENV_INFRA dead-letter/quarantine review (§6.2:245, §6.3:273–274) | Per non-STABLE verdict / per quarantine event | Quarantine review deliberate (M10a/M18/M21 no-silent-disable); FLAKY triage owner **unspecified — unowned gap** = ad-hoc human work | Quarantine review must stay human and attributable; flaky triage partially automatable under a CF6-governed K policy |
| 7 | Resolution of A2 ambiguityFlags (§2.2:100) | Per flagged step | Incidental gap — flags are emitted into the IR but nothing consumes them; ambiguity survives to the evaluator, the most expensive stage | A routing rule (flagged IR requires human sign-off before code gen) makes the cost early and explicit |
| 8 | Per-release graph-maintenance oversight; review of auto-committed graph versions, if anyone reviews them (§11.5, §13.3:790) | Per release (monthly) | Drift loop deliberately automated ("auditable-not-gated"); the silent **removal of human review from a spine-input artifact class** (committed_by='ash-capture') is an unrecorded control change | Already automated; open question is whether the dropped review control is an accepted decision |
| 9 | Exemplar / golden-set / object-repository curation (§7:289–301) | Per accepted conversion | Deliberate in effect — flywheel data quality is the whole Phase-2 bet | Write-back on CERTIFIED automatable; the accept/reject label is the evaluator's output and cannot be automated without destroying its meaning |
| 10 | Author ADR 0014, file + drain the ADR 0010 security-review entry, run the §12.4 measurement spike | One-time (queue must be empty at first production release, 0010:159–161) | Deliberate governance — the review is the ONLY check on the LLM-drives-device surface, and it is non-blocking and self-reviewed | No, and it should not be; the honest risk runs the other way — under-control of a sharp surface |

---

## 3. Findings (28, all CONFIRMED, ranked)

All findings below are CONFIRMED by verification against the walkthrough and the signed-off baseline. Duplicates across the three review dimensions are merged.

## Critical

**1. §8's main diagram puts CODE GENERATION (LLM) — plus Capture Hierarchy and Locator Resolution — inside the box captioned "THE SPINE … LLM output never touches it."** (§8:337–361 vs §1:25–33; spec.md:49–51, 342–344, 36–40) The doc's one-sentence idea is falsified by its own diagram, which is self-refuting on its face (an "(LLM)"-labeled stage inside an LLM-free box), and §1 and §8 each contradict the baseline in a *different* direction — the spec puts the hierarchy tool inside the spine (spec.md:63) and code gen outside. An auditor reading §8 concludes an LLM sits in the certified execution path — the exact accusation the architecture exists to refute.

**2. Device gate taught as K=3/K=5, silently un-deciding the signed-off K=1 spine baseline.** (§6.2:242, §8:372, mock runs:3 at :261 and mocks/o1-spine/ReplayReport.json:14, §12.2 A9:705 labels it "Unchanged"; spec.md:250–255, 347–348, CF6 at :383) Under CF6, changing K is a recorded decision, never just a commit — a walkthrough teaching K=3 as current fact is precisely the silent slide CF6 exists to prevent, and the mock ReplayReport (runs:3, flakiness verdict) is something the approved spine cannot emit.

**3. Zero screening anywhere: A0 is an unratified LLM stage consuming raw untrusted text, and Part II adds new class-2/3 LLM paths, with ADR 0009 / F3 never mentioned in 886 lines.** (§2.0:44–63, §11.4:542–544, §11.6:575; spec.md:62; 0009:87–92, :114, :122–123, :149–154) The spec builds three screening call sites into the spine and declares F3 "the whole guarantee"; the walkthrough shows none of them. Injection shaping NormalizedIntent propagates into IR, locators, and generated code; the discovery loop's screenshot/tree egress and deep-link "app docs" are new paths at a flip counter already at 2-of-3 — a genuinely new path *forces* the dedicated-component flip, and the doc doesn't even pose the question. A0 also exists only in this chat session (A13:709 mislabels it ALREADY PLANNED while §2.0 says "newly added this session").

**4. The discovery loop executes LLM-proposed actions live on an authenticated banking session, rebuilding the credential co-location ADR 0013 exists to remove.** (§11.4:524–557, §11.9:640, §12.2 A5:701; 0013:30–38, 97–103, 114–117) One worker calls the model (step 2) and taps the device (step 4) with app-session authority — "the gateway credential has no business in the execution context at all" is inverted by design. ADR 0013's scope is generated-code *execution*; A5's inheritance claim is aspiration, not analysis, and this surface has *fewer* in-path controls (no review, no commit, no capability gate) than the path 0013 hardened, guarded only by a denylist the doc itself calls "defense-in-depth only."

**5. Discovery cannot terminate successfully on legitimately changed screens — the success predicate compares against the stale stored signature.** (§11.4:549–553, §11.5:563–567) Discovery is invoked precisely when a screen changed; a changed screen can never hash to the old signature, so it deterministically exhausts the 15-action budget and dumps to the human escape hatch. At the doc's own ~20% screens-changed-per-release, the <10% escape-hatch claim collapses exactly when capture demand peaks. No re-keying mechanism (anchor-only match, fuzzy skeleton, human re-bind) exists. This is the first thing that breaks in production.

**6. Part II changes the spine contract while asserting it doesn't: NavigationManifest is declared "the spine's input," but no spine stage consumes manifests.** (§11:427–431, §11.3:497/:522, §12.3:713; spec.md:36–40, 487–495) The signed-off spine consumes committed test code plus exactly three schema contracts. A new spine-consumed artifact type is an sdd-replan event with schema-export, screening, and lineage obligations — none scoped. The claim only works because §0:18 quietly redraws the spine boundary.

**7. CERTIFIED is issued mechanically from two rule checks, with the human evaluator placed after the verdict — contradicting CF9, F7, and the spine non-goals.** (§6.3:264, 271–274; §8:380–388; spec.md:347–348, :386; style-decision.md:459) The baseline: certification gates don't exist in the spine at all, and when they do, certification is "an attributable individual decision" advised by the judge. As written, the doc teaches auditors that a machine certifies.

## Serious

**8. Deep-link probe launches LLM-proposed routes with no denylist applied to URLs or parameters.** (§11.6:570–586 vs §11.4:545) The denylist is scoped to discovery-loop *actions*; the probe launches every candidate route on an authenticated session, and the only check (landed-signature match) runs *after* execution. An `erica://transfer?...` proposal executes, and if it lands on the target it becomes the permanent VERIFIED cost-1 preferred edge. Widest LLM action space, narrowest filter.

**9. Part II logs into the app at capture time — contradicting §3's explicit "app creds are used only at replay time" — via stored Touch/Face-ID creds with automatic re-login on the 10-minute cap.** (§3:129–131 vs §11.4:529, :556–557, §13.4:851; 0013:14–17, 121–122) Both cannot be true, and the doc never acknowledges the change. Stored creds powering unbounded re-login are the shape of a long-lived credential in the most exposed worker, unreconciled with 0013's single-run session-token posture.

**10. ScreenGraph "joins the lineage chain" — but ADR 0012 has no cross-conversion chain for it to join.** (§13.3:792, §12.2 A6:702, §13.6:878; 0012:101–104, 158–159) ADR 0012's only chain construct is per-conversion; the global chain was explicitly rejected. A per-appVersion, cross-conversion artifact fits neither; `lineage_digest TEXT NOT NULL -- joins to ADR 0012 chain` is a dangling reference, so the graph's headline tamper-evidence claim does not actually exist until a chain scope is decided.

**11. ADR 0010 obligations mishandled: §13.6 ("no new security review surface") flatly contradicts §12.4 (queue entry required), the entry is unscoped, and "prod-grade data" may trip 0010:148's production-PII flip condition.** (§12.4:730–731 vs §13.6:880; 0010:146–161) If "prod-grade" means production-derived, ASH-Capture is the event that ends the non-blocking, dual-hatted review regime — the doc's entire environmental-safety argument hangs on an undefined adjective.

**12. Prompt-injection-to-action with persistence: on-screen content steers live taps, and LLM-discovered edges are recorded mid-loop (step 6, before target confirmation) then replayed forever as "NO LLM" paths, unreviewed.** (§11.4:542–551, §11.2:455 "auditable-not-gated") LLM provenance is laundered into a deterministic-looking cache; there is no review gate before graph commitment and no procedure to quarantine or remove a bad edge.

**13. The replay pipeline's classification stage — seven-class taxonomy, ENV_INFRA never-heal re-queue, M10a quarantine — is missing from the walkthrough entirely.** (§6:214–277, §8:364–381, mock has no classification field; spec.md:65, 265–269, 116–124; plan.md:83) The doc teaches "the classified, pinned, auditable verdict" pipeline without the classifier, and leaves quarantine and dead-letter flows invisible.

**14. Concurrent capture writers fork the version chain — no lock, no CAS, no uniqueness on prev_version_sha — while the post-release edge-flip storm maximizes concurrency.** (§13.3:786–793, §13.4:843; ADR 0006:72–78 single-writer precedent unapplied) Two parallel captures commit sibling versions; "latest" becomes ambiguous and re-verifications are silently dropped, exactly in release week.

**15. Cross-backend signature incomparability poisons the shared graph.** (§11.7:588–608; §13.3 nodes carry no backend field; spec.md:63) skeletonHash inputs (elementType, accessibilityId) differ across Perfecto, simulator, and adb backends, yet all three write into one graph — a locally discovered edge breaks Perfecto replay as phantom drift, undetectably. The flat `login(vaultRef)` also hides that biometric injection is impossible on some backends.

**16. Screen-signature stability and uniqueness are overclaimed for a load-bearing verification primitive.** (§11.1:437–453, :450; §13.3:800–801) Dynamic lists, A/B flags, personalization, and modals change the tuple set and thus the hash (false BROKEN churn on exactly the screens a bank has most of); templated detail screens with generic titles collide into one node; ANCHOR_LESS degenerates to skeleton-only identity where collision risk peaks — and the signature match is the *only* post-landing check on probed deep links.

**17. ADR 0007 is mischaracterized and ASH-Capture's invocation model is unspecified; ADR 0011 is cited as settled while still Proposed.** (§13.2:772–777, §13.6:877–881; 0007:55–63, :95; 0011:12–18; plan.md:7) "Route graph mutations through the existing outbox" inverts 0007's decision (provenance writes are synchronous, same-local-transaction; the outbox serves exactly two seams; "no third queue without a superseding ADR") — and a capture-request queue would be the forbidden third queue. Anchoring "via the ADR 0011 port" leans on a PROBE-PENDING decision. Unresolved dependencies dressed as settled reuse.

## Moderate

**18. "F1" used for the flywheel collides with F1, the release-blocking ArchUnit provider-seam rule.** (§2.0:57–58, §9:397; style-decision.md:453, 465–468) "F1 does NOT apply to A0" literally reads as waiving the provider-seam rule for the one LLM stage where it matters most.

**19. NavigationManifest: irRef null, duplicated login steps, a second "audit pin," and three unowned screen-name spaces joined by bare string equality.** (§11.3:497–522 vs §5:208–210; §2.2:97) Two committed sources of truth for the same flow with no drift detection, two competing audit pins with no hierarchy, and a silent name mismatch that captures the wrong screen while everything downstream trusts it.

**20. ASH-Capture auto-commits spine-input artifacts (committed_by='ash-capture'), silently dropping the review control that legitimizes "committed" everywhere else.** (§11.4:551, §13.3:790 vs §5:185–187; blueprint:49, :63) Removing human review from a spine-input artifact class is a control change that should be named and recorded, not inherited by vocabulary.

**21. Unmeasured coverage numbers (~90% / <10% / ~20%) presented as operating facts; §11.8's heading bakes "<10%" into the mechanism's name.** (§11.4:532, §11.5:563–564, §11.10, §12.4:728–729) All load-bearing for the automation claim, all pending the spike §12.4 itself demands — and mutually inconsistent with finding 5.

**22. No path exists for FLAKY/UNKNOWN verdicts, and the evaluator's FAIL→A0 loop is unbounded — the only unbounded loop in an architecture that brags about bounded loops.** (§6.2:245, §6.3:273–274, §7:286–287; 0003:50–54, spec.md:350) Every iteration re-spends the two most expensive resources: device minutes and the evaluator.

**23. Static-gate "bounded retries" has no bound, no owner, and presents Phase-2 orchestrator machinery as current behavior.** (§6.1:232, §8:367; 0003:50–54, spec.md:349, plan.md:58) The real budgets (3 static / 3 device, then HITL) exist — elsewhere, in a phase that isn't built.

**24. Graph mutation semantics are self-contradictory: in-place edge flips and mid-loop side-effect writes vs §13.3's no-mutation snapshot model; commit granularity undefined; provenance enums drift across sections; snapshot churn unpriced.** (§11.2:493–495, §11.4:550, §11.5, §13.3:817, 826–831; 0012:87–91) Under lazy re-verification, snapshot-per-change means roughly one full graph version per capture for a month — or in-place UPDATEs on tables the doc calls lineage-grade.

**25. Mock ReplayReport's pinning set is incomplete against the F6 contract it purports to teach** (three fields, no NOT_APPLICABLE convention, no runner digest — §6.3:259–267; spec.md:88–105, 329–339); **"LOCATOR RESOLUTION (deterministic)" lists VLM and LLM-guess sources two lines below the label** (§4:147–159, §8:352–355); **the human evaluator is drawn as a spine stage though "the spine has no HITL surface"** (§1:31–32, §8:384–388; spec.md:350).

**26. Escape-hatch recording and data handling unspecified: PII scope, retention, redaction of the human action stream; TYPE values have no schema home.** (§11.8:616–626, §11.3:506, §13.3:808–821; 0009:77–83; 0011 M39) Compounded by: **screenshots of prod-grade banking screens becoming routine model input** (growing ADR 0006's unowned model-egress residency exposure, 0006:126–141) and **retained graph JSON threatening ADR 0011's M39 timing bet** ("fails if spine evidence is later reclassified as retained"; per-conversion crypto-shred keys don't map to per-graph-version artifacts, 0011:169–178). "Prod-grade data" never engages M39/M40/redaction at all (§11.9:640; spec.md:207–211).

**27. The cost model ignores state destruction and device economics.** Dijkstra can splice cost-1 DEEP_LINK edges mid-path, destroying accumulated in-app state; "SCROLL=2 < TAP=2" is not an ordering, so path selection is nondeterministic (§11.2:491–492, §13.4:849). The month-start re-verification burst is an unbudgeted new consumer of the pinned Perfecto pool in release week — the doc never estimates one device-hour (§11.4:556–557, §11.5; blueprint:73). The two large recurring human costs (§5 review, §7 evaluation) are never totaled against the ">90% automated" framing.

## Minor

**28. Survivability overstated**: "the spine keeps working off existing manifests" decays within one release cadence when every edge flips UNVERIFIED — the real fallback is status-quo-ante manual capture (§11:429–431, §12.3:719–721). **Schema integrity gaps**: no composite FK from edges to nodes (dangling references representable — the exact partial-commit corruption findings 12/24 predict); edge_id/screen_id generation unspecified (§13.3:807–824). **committed_by is free text**, conflating human and service identity and unable to record the steering human behind escape-hatch commits (§13.3:790; spec.md:159–164 M37, CF9).

---

## 4. Hard questions (25)

## A. Boundary and consistency — which document is normative?

1. **Which pipeline does this walkthrough teach — the signed-off K=1 spine (spec.md:250–255) or the weeks-3–8 pipeline?** If K=3/5 is intended now, where is the CF6-required recorded decision, and why does an "O1 (Spine)" doc's mock show runs:3? *Decision: phase-label §6.2/§6.3/§8, or record the K change.*
2. **Fix §8 or fix §1 — which stages sit inside the spine?** The spec puts hierarchy capture inside (spec.md:63) and code gen outside (spec.md:342–344); both diagrams are wrong in different directions. Will you re-caption the box that currently says "LLM output never touches it" while containing an LLM stage? *Decision: adopt the spec's boundary in both diagrams.*
3. **Who issues CERTIFIED — the two rule checks in §6.3, or CF9's attributable human certifier?** Can the spine emit any certification verdict before the weeks-3–8 design exists? *Decision: rename the spine's output to a classification + gate outcome.*
4. **Is A0 an amendment to the spec's deterministic ingestion CLI (requiring sdd-replan) or a weeks-3–8 feature drawn as current?** And where does the ADR 0009 screening call sit relative to A0 — before its model egress, on NormalizedIntent, or both? *Decision: ratify or defer A0; fix A13's provenance label either way.*
5. **Is NavigationManifest a spine-consumed artifact — a contract change through the sign-off gate (spec.md:487–495) — or an authoring-arm input to the capture executor?** Whoever replays it is an unnamed executor with an undefined relationship to the gates. *Decision: name the consumer; demote or ratify the artifact.*

## B. ASH-Capture design mechanics

6. **How does discovery ever terminate on a legitimately changed screen when success is equality with the stale stored signature?** What re-keys node identity without a human? *Decision: design the re-keying mechanism before the measurement spike, or the spike measures a known-broken loop.*
7. **Are step-6 side-effect edges committed when a run aborts, crashes, or escape-hatches — under which graph_version_sha — and what removes a bad edge from the committed graph?* *Decision: define commit semantics and an edge quarantine procedure.*
8. **What serializes concurrent capture writers** — advisory lock, CAS on prev_version_sha, or a single-writer service per ADR 0006's precedent? *Decision: pick one before the first two parallel CI captures fork the chain.*
9. **Who owns the canonical screen-name space** across TestCaseIR.screenContext, graph screen_id, and display-text titleAnchor — and what is the defined behavior on rename or non-reconciliation: spurious discovery, hard error, or human queue? *Decision: name an owner and a validation rule; populate irRef.*
10. **What guarantees skeletonHash comparability across the three DeviceSession backends** — and if nothing, why do all three write into one graph with no backend field on signatures? *Decision: per-backend signatures, a backend column, or a single canonical capture backend.*
11. **Under the snapshot model, does each lazy edge re-verification mint a new full graph_version_sha** (~one snapshot per capture for a month), or which table absorbs the in-place UPDATE under which database grant? *Decision: define commit granularity; reconcile with 0012's INSERT/SELECT-only posture.*
12. **Does path search respect sessionPrecondition and the state-destruction of DEEP_LINK edges**, and what breaks the SCROLL=2/TAP=2 tie so replay paths are actually deterministic? *Decision: constrain deep links to first-hop-from-FRESH; fix the cost ordering.*

## C. Security and audit

13. **Which OS process holds the gateway credential and which holds the authenticated device session?** If one worker, say why that does not invert ADR 0013:114–117; if split, specify the proposer/executor boundary and the validated action queue between them. *Decision: the topology goes in ADR 0014, or A5's inheritance claim comes out.*
14. **Map every new LLM flow to an ADR 0009 call site** — A0's raw text intake, A0 egress, discovery screenshot/tree ingress and egress, deep-link "app docs," evaluator-FAIL error feedback — and rule whether any is the third additional path that forces the dedicated-component flip at 2-of-3. *Decision: this analysis is a precondition of the ADR 0014 draft, and someone other than the dual-hatted reviewer should rule on it.*
15. **Does the denylist apply to deep-link routes and their parameters before launch?** What concretely stops `erica://transfer?amount=...` from executing — and from becoming a VERIFIED cost-1 preferred edge when the transfer screen is itself the target? *Decision: route candidates through the validator plus an allowlisted route-prefix set.*
16. **What may a TYPE action type?** Where is the policy bounding LLM-chosen input text executed against an authenticated session — and where does a TYPE edge's value live, given the edge schema has no value column? *Decision: define a typed-input policy and schema home.*
17. **Define "prod-grade data": production-realistic synthetic, or production-derived?** If the latter: does ADR 0010:148's PII flip condition trigger (ending the non-blocking review regime), and which of M39 retention/crypto-shredding, M40 ephemeral volumes, and 0009 redaction apply to discovery screenshots, escape-hatch recordings, and model egress? *Decision: one adjective decides the entire control regime — define it.*
18. **Reconcile §3 with §11.4: does hierarchy capture authenticate into the app or not**, and how do stored Touch/Face-ID creds with automatic re-login satisfy ADR 0013's single-run token shape? *Decision: either capture gets its own credential decision or the §3 claim is retracted.*
19. **Which chain does lineage_digest join** — a new per-graph chain scope (an ADR 0012 amendment with its own anchoring cadence) or binding into per-conversion chains — and who computes it in the same transaction and verifies it per release? *Decision: an ADR, not a column comment.*
20. **Is removing engineer review from ASH-Capture's committed spine-input artifacts an accepted control change**, and will ADR 0014 state it explicitly instead of inheriting Part I's "reviewed and committed" credibility? Relatedly, will committed_by become a typed actor field recording the steering human on escape-hatch commits? *Decision: name the control change; fix the schema.*
21. **Is the capture-request path synchronous or a queue** — and if a queue, how does it clear ADR 0007:95's "no third queue without a superseding ADR"? In which process do graph + lineage writes join a local transaction per 0012:106–108? *Decision: specify the invocation model before "route through the existing outbox" appears in an ADR.*

## D. Automation economics

22. **What Phase-1 human-touch budget per test are you actually willing to pay** — count ingestion, capture run(s), generation invoke, review+commit, evaluation, expected failure-loop iterations — and at what measured escape-hatch and ANCHOR_LESS rates does ASH-Capture's business case fail? *Decision: set the threshold before the spike so the spike can falsify it.*
23. **Who owns FLAKY and UNKNOWN verdicts, what bounds the evaluator's FAIL→A0 loop, and who resolves A2's ambiguityFlags** before they reach the most expensive stage? Three unowned triage paths, three owners needed. *Decision: assign owners and bounds in the doc.*
24. **What is the fleet-level device-minute budget for the month-start burst** when every edge flips UNVERIFIED and concurrent captures re-verify overlapping prefixes — and does it contend with the release regression run on the same pinned pool the same week? *Decision: a device-hour estimate belongs in ADR 0014.*
25. **When drift repair rewrites a manifest a test's Java was generated against, is the Java regenerated and re-reviewed** — and is that recurring cost inside or outside the "<10%" framing? *Decision: define the regeneration cascade and count its review cost.*

---

## 5. Recommendations

## Fix in the doc now (editorial — no new decisions required)

1. **Redraw §8 and §1 to the spec's boundary**: hierarchy tool inside the spine, code generation and locator resolution in the authoring arm, human evaluator outside the spine box as the Phase-1 workflow wrapper; re-caption the spine box; add the missing classification stage between device gate and ReplayReport.
2. **Phase-label everything**: K=1 as the current spine baseline (K=3/5 explicitly weeks 3–8), repair-loop budgets as "3 static / 3 device then HITL — Phase-2 orchestrator," certification as weeks-3–8 and human-issued. Fix the mock ReplayReport: runs:1, classification field, complete pinning set with explicit NOT_APPLICABLE per F6.
3. **Rename "F1 (flywheel)" to "the data flywheel"** everywhere; note F1–F7 are reserved identifiers.
4. **Mark every coverage number (~90% / <10% / ~20%) as a target pending the §12.4 spike**; rename the §11.8 heading so "<10%" is not baked into the mechanism's name.
5. **Add ADR 0009 screening call-outs at every boundary** the doc teaches (ingestion, hierarchy capture, artifact pull, and each Part II egress); fix A13 (A0 is NEW, not ALREADY PLANNED); correct the ADR 0007 gloss (synchronous same-transaction provenance, two seams only); carry ADR 0011's Proposed/PROBE-PENDING status; resolve the §12.4-vs-§13.6 security-surface contradiction in §12.4's favor.
6. **Demote the NavigationManifest from "audit pin" to "capture provenance record"** (codeCommit stays the pin); populate irRef in the worked example.

## Needs an ADR or recorded decision

7. **A0's existence**: either an sdd-replan amendment to the deterministic ingestion CLI or an explicit weeks-3–8 deferral — it cannot remain an audit-facing diagram fact with no decision behind it.
8. **ADR 0014 must actually decide** (not inherit): the proposer/executor process split as an ADR-0013-successor shape; the 0009 call-site mapping and flip-counter ruling; denylist scope including deep-link routes/parameters and a TYPE-input policy; the capture credential model (stored creds vs single-run tokens, and the real bound on authenticated LLM-driving time); the definition of "prod-grade data" and whether 0010's PII flip triggers; the auto-commit control change; the screen-naming authority; write serialization; snapshot commit granularity; edge quarantine/removal.
9. **ADR 0012 amendment** defining a per-graph chain scope (or explicit per-conversion binding) before any tamper-evidence claim is made for the ScreenGraph.
10. **ADR 0007 superseding decision** if ASH-Capture needs an async invocation seam; otherwise state it runs synchronously in a named process whose writes join a local transaction.

## Measurement spike (before believing the design)

11. **Design the signature re-keying mechanism first** (finding 5) — otherwise the spike measures a deterministically broken discovery loop.
12. **Then run the §12.4 spike on a real release**, extended beyond ANCHOR_LESS and iOS deep-links to measure: actual escape-hatch rate given ~20% screen change, skeletonHash stability across dynamic screens and across backends, snapshot churn per month, device-hours for the month-start burst, and human touches per test — against the budget thresholds set in question D22, so the numbers can retire (or kill) the ~90/<10 claims rather than decorate them.
