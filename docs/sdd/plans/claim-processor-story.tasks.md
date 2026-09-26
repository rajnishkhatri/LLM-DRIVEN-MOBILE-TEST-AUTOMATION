# Tasks: Insurance Claim Processor Explainer — "The Workflow the Model Never Controls"

**Spec:** `docs/sdd/specs/claim-processor-story.spec.md` (SPEC-OK
2026-09-23) · **Plan:** `docs/sdd/plans/claim-processor-story.plan.md`
(PLAN-OK 2026-09-23) · **Status:** **IMPLEMENTED (2026-09-23)** — owner approved the tasks gate
and all fifteen tasks T0–T14 ran green in one `sdd-implement` session.
Deliverable at `docs/architecture/explainers/insurance-claim-processor-story.html`
(164.4 KB); verifier `verify_claim_processor_story.py` green (153
checks, exit 0), red-first honored (first run failed on the missing
Part-IX envelope beat and one verbatim table cell; both fixed), and all
10 injected mutation probes caught (one verifier tightening: the AC-9
card-id set is now pinned, after the rename mutation initially slipped
through the count-only check). T8 flip-test rehearsal: F1–F9 read as a
complete mechanism story figures-only; one grammar fix applied (F8
connector curves rerouted under the labels, clipped texts fixed) and F6
gained its amber "model's draft, paused" band rather than a whitelist
entry. Browser pass over HTTP (`.claude/launch.json` explainers-static):
UTF-8 + CSS1Compat, no body h-scroll at 375 px or 300 px, both themes
verified (dark emulation unavailable for `file://`, so themes were
checked served), zero `<script>` tags (AC-1 by construction).
`check_gate` exit 0 after the `docs/architecture/log.md` registration;
private Artifact published (claude.ai/artifact/UC3Ryu3Kxe9UWrYncvPueQ,
repo file canonical). Owner converge checklist: AC-15 figures-only flip
test + AC-16 hybrid-rule read. Next: Stage-7 review (`code-review`,
fresh thread).
Prior gate record: TASKS-OK (2026-09-23) — Stage-4 analyze GREEN.

**Stage-7 review + fix record (2026-09-23):** `/code-review` (high, 8
angles) + the owner's four screenshot comments (r1–r4) produced 10
findings, all fixed in the same session: F3 pins retargeted to match
the caption (Extract/Validate/Record teal, Understand/Validate slate,
the two helpers amber) with pin-head dots for direction, its legend
split to two lines, Validate box widened; F4's guardrail redrawn as a
band both model arrows cross ("screens in + out" — confirmed against
`claim_processor/invoker.py`: one `guardrailConfig` on Converse screens
input and output); F5's human-review text refit and the drain label
moved below the curves; F8's six connector curves replaced with an
orthogonal left-gutter bus that never crosses label text; F10/F13/F9
overrun lines trimmed or shifted; `.claude/launch.json` regression
reverted (atlas-docs restored, `--bind 127.0.0.1` on both servers).
**Scope addition (owner-requested):** new **F14 "The whole machine, as
deployed"** end-to-end state-machine figure in Part VIII (console
graph redrawn in the two-lane grammar: smoke-#1 path numbered ①–⑦,
dashed not-yet-exercised states, slate HITL chain pinned to finding
F2); the decision map renumbered **F15**; AC-10 now reads F1–F15. The
verifier gained the missing check class — **AC-8b**, an approximate
per-`<text>` overflow lint against each figure's viewBox — which ran
red-first (caught one real F9 overrun beyond the 6 known ones) and is
green at **640 checks, exit 0** (179.3 KB ≤ 350 KB cap). Browser
re-pass over HTTP: F3/F4/F5/F8/F10/F14 screenshots clean.

**Stage-4 analyze record (2026-09-23):**
- **Grounding:** all 18 referenced artifacts exist on disk (source
  table, precedent files, constitution, log surface); `adrs/` holds all
  15 ADR files. No non-existent file/API referenced. No new dependency
  (stdlib + hand-authored HTML only) — no ADR trigger.
- **Baseline:** `check_gate` (skill-sync) exit 0, 7 families clean;
  `test_gate = <none>` per binding.
- **Constitution:** framing doc (trade-off analysis, quality
  attributes) — satisfied by construction: every decision card carries
  a trade-off table; no invariant conflicts for a docs-only change.
- **Cross-artifact:** figure count (14), card ids (10), part count
  (9), single-lane exceptions (F2/F3/F12/F13), deliverable + verifier
  paths, and converge steps agree across spec ↔ plan ↔ tasks.
- **Finding A1 (resolved):** figure ids F1–F14 collide with deploy
  finding ids F1–F11. Resolution written into spec FR-6: on-page
  finding references always read "finding Fn", never bare; the
  verifier keys figures on `data-fig`, never text.
Markers: `[deps: …]` must-finish-first · `[par]` parallelizable with
siblings.

**Checklist ("unit tests for English"):** every AC is measurable —
AC-2/4/5/6/7/8/10/11/12 and the static halves of AC-9/14 by the stdlib
verifier (T12); AC-1/3 + the theme halves of AC-12/14 by browser check
(T13); AC-9/13 by targeted read (T13/T14); AC-15/16 human-judged at the
converge gate by design (spec C3 — the machine proxies are AC-7's
in-SVG title + step-number + label checks). Vague words made concrete:
"labeled" (AC-4) = a visible `<text>` node in the same `<g>` as the
`<use>`; "flagged tunable" (AC-5) = the frozen value list below;
"not live" (AC-5) = the frozen census below; "figures in order"
(AC-10) = `data-fig="F1…F14"` in ascending document order. No
unmeasurable criteria remain.

## Frozen inputs (authoring-time constants — verifier data)

**Unverified-value list (AC-5a):** contextual grounding threshold
`~0.70` (design §4 + ledger Stage 2 both flag re-verify) · `$10,000`
payout threshold (design §1a: "defaults — tune per domain").

**Live/not-live census (AC-5b), from `build/DEPLOY-LEDGER.md` +
`build/DEPLOY-WALKTHROUGH.md` §Remaining work, frozen 2026-09-23:**
- **LIVE on account 324177727513 / us-east-1 (deployed + smoke-proven
  2026-09-22):** S3 bucket (3 prefixes, SSE-KMS, versioned) · Bedrock
  guardrail `claim-processor-guardrail` (PII mask + prompt-attack) ·
  AppConfig app/env/profile + linear-bake strategy (data-plane read
  verified) · 3 IAM roles (step-lambda, remediation, sfn-exec) · 6
  Lambdas (breaker-probe, understand-extract, degraded-extract,
  validate, retrieve-summarize, record) · state machine
  `claim-processor` (13 states, Standard, StartAt BreakerProbe) ·
  auto-approve smoke #1 SUCCEEDED (~12 s, grounded, config snapshot
  live).
- **BUILT BUT NOT DEPLOYED / NOT EXERCISED (status chip):** HITL
  await-review + expire-review handlers (finding F2 open — token never
  persisted; flagged smokes parked) · alarms + SNS + remediation Lambda
  (Stages 6–7 pending; F10/F11 open) · breaker-open → DegradedExtract
  path (deployed in ASL but smoke pending) · ensemble (flag-gated,
  default off) · contextual-grounding check (F5: inert — no
  `guardContent` sent).
- **DESIGNED / PRODUCTION-PROMOTE ONLY (status chip):** Bedrock KB on
  S3 Vectors (ADR 0007 fast-follow) · Textract/BDA understanding
  promote (ADR 0006) · Cedar / Verified Permissions (future tool) ·
  A2I / UI review surface · SFN log delivery (F8: off by design, PII).

**Findings one-liners for F13 (C1 depth):** F1 no Lambda bootstrap
(fixed) · F2 HITL token never persisted (open) · F3 placeholder
account/app ids (handled via deploy-out rendering) · F4 guardrail IAM
matched name not ID (fixed) · F5 grounding check inert (documented) ·
F6 Lambda roles lacked log permissions (fixed) · F7 `Comment` key =
malformed IAM policy (fixed + grammar test) · F8 SFN log delivery
grants/PII (documented, logging off) · F9 non-ASL top-level key (fixed
+ test) · F10 remediation Lambda not implemented (open) · F11
remediation role can write but not read config (open). Text-explainer
beats: F1, F2, F3 only (the deploy-blockers).

## Task list

- **T0 — Design-skill load + style anchor.** Load `artifact-design` +
  `artifact-diagramming`; re-read the reference's token block, sticky
  legend, envelope-beat, decision-card, and footer patterns
  (`docs/architecture/explainers/aws-ai-architect-story.html`).
  Pass: both skills loaded in-session before any HTML is written.
- **T1 — Content map derivation.** [deps: T0] From the spec source
  table, derive `<scratchpad>/claim-story-content-map.json`: per-Part
  claim outlines (each claim: source path + section, lane owner,
  unverified/status marking per the frozen lists), the 14 figures'
  data (in-SVG title sentence verbatim from the plan inventory, icon
  list, steps yes/no, figcaption citation), per-Part text-explainer
  beats (spec structure table), envelope-beat text ×9, 10 cards'
  trade-off data + default-lines + ADR ids, scorecard rows, footer
  status-line text from the census.
  Pass: sanity script — 14 figures with titles/citations; 9 parts each
  with ≥1 figure + beat text; 10 cards with ADR ids; every citation
  path exists on disk; census items each assigned ≥1 landing spot.
- **T2 — Chassis + icon library.** [deps: T1] Skeleton at
  `docs/architecture/explainers/insurance-claim-processor-story.html`:
  shell + tokens (reference palette + `.status` chip style; three-block
  theming; explicit body background), `<defs>` symbol library (14
  symbols per the plan), masthead + seam statement + byline, sticky
  legend (lanes + unverified + status chips), icon key strip, empty
  `.part` shells I–IX, card/scorecard/footer shells.
  Pass: opens from `file://`; both themes sane; zero external URLs; no
  body h-scroll at 375 px; legend is the only sticky element; every
  symbol renders once in the key strip with a label.
- **T3 — F4 hero + Part III (grammar anchor).** [deps: T2] The
  pipeline hero figure (S3 → SFN → Lambdas → Bedrock+Guardrail → S3,
  two lanes, steps ①–⑦, icons via `<use>` + labels, in-SVG title) and
  Part III prose (minimal per plan — this Part is the flip-test
  anchor). **Named grammar anchor: lane band geometry, icon plate
  size, step-number style, title placement for T4–T10.**
  Pass: AC-4/7/8 verifier probes green on this figure; figcaption
  cites `design/solution-design.md` §1 + §7; envelope beat closes the
  Part.
- **T4 — Parts I + II.** [deps: T3] [par] Part I: F1 (two doors), F2
  (agent vs workflow, enumerated single-lane exception, crossed
  rejected side), losing-alternatives beat, three-walls beat. Part II:
  F3 (characteristics → components map, single-lane exception),
  tension-pairs beat.
  Pass: anchor grammar held; F2/F3 carry no lane washes on neutral
  chips; citations to design §1, capability brief, worksheets,
  components doc resolve.
- **T5 — Part IV (the human gate).** [deps: T3] [par] F5 (four gates →
  one human), F6 (token wait, 7-day timer, status chip on the not-live
  wait path), reviewer-contract + single-use-token beats.
  Pass: anchor grammar; F6 carries the `.status` chip per census;
  cites design §1a + ADR 0005.
- **T6 — Part V (safety + IAM).** [deps: T3] [par] F7 (two nets), F8
  (three keys matrix), two-ARN-trap + Cedar-waits beats.
  Pass: anchor grammar; cites design §4/§5 + ADRs 0008/0009.
- **T7 — Part VI (grounding).** [deps: T3] [par] F9 (cite-or-flag,
  fail-closed), retrieve-vs-RAG-API + no-memory + S3-Vectors-promote
  beats (promote carries status chip).
  Pass: anchor grammar; unverified marker on the ~0.70 threshold
  everywhere it appears; cites design §2 + ADR 0007 + eval-report
  RAG-integrity finding.
- **T8 — Mid-build flip-test rehearsal.** [deps: T4, T5, T6, T7]
  Figures-only scroll of F1–F9 (browser, both themes): does the
  mechanism read without prose? Fix grammar drift now; record one line
  of outcome in this file.
  Pass: rehearsal performed; any fixes applied before T9 starts.
- **T9 — Part VII (resilience) + Part VIII (proof + deploy).**
  [deps: T8] Part VII: F10 (seven-layer stack; status chips on
  alarms/remediation + ensemble layers), F11 (breaker-open path;
  status chip), integrity-invariant + decisions-age beats (0012/0013
  reversals). Part VIII: F12 (proof pyramid), F13 (deploy timeline
  with the 11 finding one-liners pinned per the frozen list; F1/F2/F3
  text-explainer beats), remaining-work beat.
  Pass: anchor grammar; census chips exactly per the frozen list;
  finding ids verbatim; cites design §8, ADRs 0010–0015, resilience
  clinic, README gate flag, walkthrough + ledger.
- **T10 — Part IX: decision map + cards.** [deps: T8] F14 (ten dots on
  the two-lane map) + ten `#d-*` cards (host, hitl, guardrail, iam,
  rag, docunderstand, config, breaker, ensemble, degrade): question,
  trade-off table in `overflow-x` wrapper, `.default-line`, ADR id,
  anchors both ways; supersession lines on d-host, d-breaker,
  d-ensemble.
  Pass: all ten present; anchors resolve both directions; ADR ids
  match `adrs/index.md`.
- **T11 — Scorecard + footer.** [deps: T9, T10] Scorecard rows wired
  to card anchors + sources (status/unverified chips per occurrence);
  footer About (source-artifact links), Honesty note (both chip
  semantics), the census-derived live-status line dated 2026-09-23,
  provenance + as-of.
  Pass: every scorecard row's anchor resolves; footer status line
  matches the frozen census.
- **T12 — Verifier.** [deps: T11] Write
  `docs/architecture/explainers/verify_claim_processor_story.py`
  (stdlib-only) implementing the plan's harness (AC-2, 4, 5-keyed +
  census, 6-shingle, 7, 8 + exception whitelist F2/F3/F12/F13, 9-static,
  10, 11, 12, 14-static); run to **exit 0**.
  Pass: verifier green on the deliverable; deliberately broken probes
  (one per check class, temporarily injected) each fail — then
  restored.
- **T13 — Browser passes.** [deps: T12] Serve over
  `python3 -m http.server`; check AC-1 (no required JS), AC-3 (375 px
  + 300 px scrollWidth probe), AC-12 (dark mode; icon strip legible
  both themes), AC-14 (`characterSet`/`compatMode`); targeted read
  AC-9/13.
  Pass: all observed green; screenshots of F4 in both themes captured
  for the converge record.
- **T14 — Registration + converge handoff.** [deps: T13] Append the
  newest-first `docs/architecture/log.md` entry (file, design lineage,
  SDD provenance); re-run `check_gate` (skill-sync) → exit 0; publish
  the private claude.ai Artifact (FR-12, repo file canonical); hand the
  owner the converge checklist: AC-15 figures-only flip test, AC-16
  hybrid-rule read.
  Pass: log entry present; check_gate exit 0; Artifact link delivered;
  owner checklist issued.

## AC ↔ task map

| AC | Owned by |
|---|---|
| AC-1, 3 | T2 (build-time), T13 (proof) |
| AC-2 | T2, T12 |
| AC-4 | T2/T3 (build), T12 (proof) |
| AC-5 | T5/T7/T9/T11 (build, frozen lists), T12 (proof) |
| AC-6 | T12 |
| AC-7, 8 | T3–T10 (build), T12 (proof) |
| AC-9 | T10 (build), T12 static + T13 read |
| AC-10 | T3–T10 (build), T12 (proof) |
| AC-11 | T1 (map), T12 (proof) |
| AC-12 | T2 (tokens), T12 (size/tokens), T13 (dark) |
| AC-13 | T2/T11 (build), T13/T14 (proof) |
| AC-14 | T2 (shell), T12 static, T13 (served) |
| AC-15, 16 | T8 (rehearsal), owner at converge (T14 handoff) |
