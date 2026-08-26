---
type: analysis
title: SDD Stage 1 — Brainstorm: host authored HTML as a static site with working links
description: >-
  Premise audit and six directions for publishing this workspace's
  self-contained HTML deliverables (prep guides, atlases, explainers) with
  a navigation strategy that keeps embedded relative links intact.
tags: [sdd, brainstorm, static-site, html, navigation]
---

# SDD Stage 1 — Brainstorm: Host authored HTML (multi-file, links, navigation)

**Stage:** SDD Stage 1 (brainstorm / ideation)
**Binding:** `.sdd/binding.toml` — constitution `.cursor/rules/architecture-principles.mdc`; spec/plan home `docs/sdd/`; `methodology_source = <none>` (skill body governs); `test_gate = <none>`; `check_gate` = skill-sync
**Status:** DIRECTION ACCEPTED 2026-08-26 — owner picked **D2**. Allowlist rider not chosen at this gate (clarify in `sdd-spec`). Advance → `sdd-spec`.
**Home:** `docs/research/html-site-hosting-brainstorm.md`

> Per `sdd-brainstorm`: restate the problem → premise audit against the working tree → ~6 directions → hypothesis validation for a lead → dependency map → **human gate**. No spec is written here.

---

## 0. Restated problem (not a solution)

This workspace already has **authored, mostly self-contained HTML** (study guides, atlases, explainers, research blogs). They are viewed locally via `atlas-docs` (`python3 -m http.server` on `docs/`) or `file://`. There is **no public host**.

The need is:

1. **Publish** more than one HTML file so a reader can open them in a browser without cloning the repo.
2. **Keep embedded links working** (HTML→HTML companions, HTML→SVG/assets, in-page `#` anchors).
3. **Give the reader a navigation strategy** to find and move between those files.

The previous session almost specified “one file + Vite/React/Tailwind/Vercel.” That was a **solution** for a smaller problem (host `docs/ccar-p-prep-guide-v2.html` alone). This brainstorm treats the **class** of the problem: a growing set of HTML documents whose contract is relative URLs, not a SPA.

---

## 1. Constitution / subtree backdrop

Touched folders: `docs/` (HTML + research mocks/SVGs), possibly a new `apps/` tree, `cases/coding-rules/junior-clean-architecture/` if that cluster is published.

**Constitution** (`.cursor/rules/architecture-principles.mdc`): this workspace has no numbered eight-invariant SDD constitution. Load-bearing here:

| Principle | Why it binds this change |
|---|---|
| **Single Responsibility** | Catalog (how you find a page) ≠ document (the page) ≠ host (how bytes are served). |
| **Open/Closed** | Adding a page should not require rewriting a shell or a router. |
| **Coupling** | Relative `href`/`src` *are* the integration contract between files. A JS router that inverts that coupling is a new abstraction. |
| **Trade-off analysis** | Every nav/host choice (preserve tree vs flatten, allowlist vs whole `docs/`) has a cost in 404s, duplication, or scope. |
| **Simplest style that works** | These files are already static documents. A static file server is the matching architectural style. |

**De-facto invariants on existing HTML specs** (must not be silently broken):

- Prep guide **FR-1** / atlas **FR-1**: one self-contained file, zero CDN, works from `file://` (`docs/sdd/specs/ccar-p-prep-guide.spec.md:63-66`, `docs/sdd/specs/platform-design-atlas.spec.md:50-52`).
- Prep guide **C4**: “repo file only” — no Artifact; local `atlas-docs` or `file://` (`ccar-p-prep-guide.spec.md:21`, `:179-181`). **Public hosting overrides C4.** That override belongs in the next spec, not as a silent side effect.
- Atlas **AC-1**: JS is progressive enhancement, never a content gate (`platform-design-atlas.spec.md:91-93`). A SPA wrapper that hides the document behind a router would violate this for any inlined page.

⚠️ **Ask-first at spec time** (new service and/or new abstraction → ADR): a Vercel (or GitHub Pages) project; any new npm dependency (Vite, React, Tailwind); a link-rewriting pipeline; an iframe shell.

`check_gate` (skill-sync) is untouched if we do not write skill surfaces.

---

## 2. Premise audit

| # | Premise | Status | Evidence |
|---|---|---|---|
| P1 | “We need Vite + React 19 + Tailwind + a hash router to host HTML.” | **REFUTED** | No `package.json`, no `apps/`, no `vercel.json` in this repo. The live local surface is already a static server: `.claude/launch.json:5-8` (`atlas-docs`, `-d docs`, port 8123). The HTML files do not import React. |
| P2 | “Every HTML file is self-contained (no extra assets).” | **REFUTED as universal; VERIFIED for the study-guide cluster** | **Self-contained:** prep guides and atlas (FR-1 above); o7 explainers have no `href` at all under `docs/architecture/explainers/`. **Not:** `cases/coding-rules/junior-clean-architecture/index.html:160` (`src="diagrams/….svg"`); `docs/research/o1-pipeline-blog.html:436` links to walkthrough HTML, `../mobile-test-automation-six-way-comparison.html`, `o1-diagrams/….svg`, and `mocks/o1-spine/README.md` (45 files under `docs/research/mocks/`). **CDN-dependent:** `docs/research/aws-ai-eval-iteration-1/aws-ai-eval-review.html:7-10` (Google Fonts + SheetJS CDN). |
| P3 | “There is no navigation today.” | **REFUTED for intra-page; VERIFIED for inter-page** | Intra-page: section ids (`docs/ccar-p-prep-guide-v2.html:360` `#front-matter`, `:411` `#d1`); atlas skip-link (`docs/claude-architect-m1-atlas.html:319`); o7 sticky chrome (`o7-pipeline-story-v2.html:174`); AML TOC (`docs/aml-sanctions-adjudication-design.html:97`). Inter-page catalog: **no** `docs/index.html`. Discovery is markdown logs (`docs/architecture/log.md:10-11`, `:98`) and OKF `docs/architecture/index.md` — which catalogs ADRs/worksheets, not HTML explainers. |
| P4 | “Embedded HTML→HTML links already exist and assume a shared directory tree.” | **VERIFIED** | Prep guide → atlas sibling: `docs/ccar-p-prep-guide-v2.html:2505` (`href="claude-architect-m1-atlas.html"`); same in v1 (`docs/ccar-p-prep-guide.html:2501`) and v3 (`docs/ccar-p-prep-guide-v3.html:2510`). Research cluster: `o1-pipeline-blog.html:436`, `o2-pipeline-blog.html:454`, `o3-pipeline-blog.html:493` — same-dir + `../` relatives. Copying one file out of tree **breaks** those hrefs. That is the defect class. |
| P5 | “There is no public production surface yet.” | **VERIFIED** | `atlas-docs` binds `127.0.0.1` only (`.claude/launch.json:7`). No Vercel/GitHub Pages config in-repo. Live prod surface for a future host **does not exist**; local `http://127.0.0.1:8123/` is the only proven serve. |
| P6 | “v2 is the current prep guide.” | **REFUTED as ‘current’; VERIFIED as a retained file** | v3 spec V4: v3 is current; v2 retained as provenance (`docs/sdd/specs/ccar-p-prep-guide-v3.spec.md:15`). Architecture log already points at v3 (`docs/architecture/log.md:10`). Hosting “v2 only” would publish a superseded file. |
| P7 | “GitHub blob view can replace an HTML host (evals-app CMS pattern).” | **REFUTED for this content type** | Evals-app used GitHub for **markdown**. GitHub’s blob UI shows HTML **source**, it does not run the quiz engine / SVG / theme JS. Interactive HTML needs an HTTP origin. |
| P8 | “A new app folder is required.” | **UNVERIFIABLE as necessity** | A Vercel/Pages project can root at `docs/` with no `apps/` copy. A copy-tree under `apps/` is a *packaging* choice, not a hosting requirement. Tagged on D1 vs D2. |
| P9 | “Public hosting is already allowed by existing specs.” | **REFUTED** | Prep-guide C4 explicitly deferred Artifact/public surfaces (`ccar-p-prep-guide.spec.md:179-181`). Publishing is a **spec override**, not an implementation detail. |

**Corrected framing (replaces the stale “one Vite app for one HTML file”):**

> Publish a **declared set** of HTML documents (and the relative assets they actually link to) over HTTP, with **native URLs that preserve today’s relative graph**, plus **one inter-page catalog**. Intra-page navigation already lives in each file. Do not introduce a SPA unless the catalog itself needs app state the documents do not have.

No live-site defect → **no D0**. The latent defect class is **link-closure**: shipping a file whose `href`/`src` is not also shipped.

**Corpus size (gated-on-data):** 21 HTML under `docs/` + 3 under `cases/coding-rules/junior-clean-architecture/` = **24 HTML files** (glob 2026-08-26). Not all 24 belong on a public origin.

---

## 3. Independent axes (do not conflate)

These are separate questions. Directions below *bundle* them; the gate can split them.

| Axis | Options | What it decides |
|---|---|---|
| **A. What is published** | Allowlist (study cluster) vs whole `docs/` vs include `cases/` | Scope / leak / 404 surface |
| **B. URL shape** | Preserve `docs/` tree vs flatten `/guides/<slug>/` with rewrite | Whether existing `href` keep working without a rewriter |
| **C. Inter-page catalog** | One authored `index.html` vs directory listing vs SPA catalog | How a reader *finds* a page |
| **D. Host** | Vercel static vs GitHub Pages vs none (keep `atlas-docs` only) | New service (Ask-first) |

Intra-page nav (sticky key, `#d1`, quiz engine) is **out of this change** — already implemented per file.

---

## 4. Candidate directions (~6)

Three high-probability (repo patterns named) + three exploratory.

### High-probability (follow existing patterns)

**D1 — Serve `docs/` as the site (atlas-docs in production).**
Point the static host at `docs/`. Add `docs/index.html` as the catalog (Vercel/Pages will not list directories). Relative `href`/`src` keep working because the tree is the URL space. *Follows:* `.claude/launch.json:5-8` `atlas-docs`. *Invariant:* Open/Closed — new HTML under `docs/` is live without a copy step. *Breaks if chosen:* **everything under `docs/` becomes public** (research mocks, unverified eval reviews, v1/v2 provenance, CDN-dependent eval HTML). Directory-style URLs for `mocks/*.md` work as downloads, not as GitHub-rendered markdown. ⚠️ new host service → ADR.

**D2 — Curated allowlist + preserve relative layout + one catalog + link-closure check.** **(recommended lead)**
A publish manifest names the files (and their relative dependencies). The host root is either a copy under `apps/html-site/` that **mirrors path layout** (`ccar-p-prep-guide-v3.html` beside `claude-architect-m1-atlas.html`) or a Vercel include-list with the same layout. Catalog is a small authored `index.html` (native `<a href>`). A check fails CI/local if a shipped HTML’s relative `href`/`src` is not also shipped. *Follows:* prep-guide FR-11 one-way companion link (`ccar-p-prep-guide.plan.md:171`); junior-clean-architecture relative SVGs (`index.html:160` + `README.md:15`); log-as-catalog but moved to HTML. *Invariant:* coupling stays in relative URLs; SRP — catalog is one file, documents stay untouched. *Breaks if chosen:* copy can drift from `docs/` unless the spec says “copy at publish” vs “canonical lives in the app.” Allowlist must be honest about clusters (study vs research vs cases).

**D3 — Demand-side: do not host. Keep `atlas-docs` + share the repo / zip.** **(the expensive app does not happen)**
Readers clone or download; `atlas-docs` already makes the relative graph work. *Follows:* prep-guide C4 “repo file only” (`ccar-p-prep-guide.spec.md:179-181`). *Invariant:* no new service, no C4 override. *Breaks if chosen:* **does not meet “host”** if the real goal is a URL you can send without git. Use this if the need was “open in browser locally,” already solved.

### Exploratory (different abstraction)

**D4 — React/hash catalog wrapping HTML (evals-app stack).**
Vite + React 19 catalog; viewer is `<iframe src=…>` or fetched HTML. Hash URLs `#/ccar-p`. *Follows:* the evals-app pattern from the prior chat (not in *this* repo). *Invariant stressed:* FR-1 / AC-1 (self-contained, no-JS readable) if content is inlined; iframe origin/path must still preserve relatives or links inside the iframe 404. ⚠️ new deps + SPA abstraction → ADR. *Breaks if chosen:* Tailwind/React do not style the documents (they bring their own CSS). Hash routing **does not** fix in-document `href="claude-architect-m1-atlas.html"` — those are navigation *inside* the iframe’s URL space. This stack solves a PDF catalog problem this repo does not have.

**D5 — Flatten URLs and rewrite links at publish (`/guides/ccar-p/`, `/guides/atlas/`).**
Class-level fix for “paths are the API”: a build rewrites `href`/`src` to the published slug map. *Invariant stressed:* the HTML-on-disk (FR-1 `file://`) and the hosted HTML **diverge** unless rewrite is reversible. ⚠️ new rewrite pipeline → ADR. *Breaks if chosen:* `file://` and `atlas-docs` no longer match production URLs; two graphs to maintain. Only worth it if you *refuse* to preserve directory layout.

**D6 — Injected chrome / iframe shell (shared header on every page).**
Build injects a nav bar or serves each page in a shell iframe. *Invariant stressed:* FR-1 (files must remain self-contained for `file://`); AC-1 (must work without JS). *Breaks if chosen:* every document’s CSS stacking (sticky keys at `top: 0`, e.g. `o7-pipeline-story-v2.html:174`) fights a second sticky chrome. Editing generated files is a content/host mix.

---

## 5. Leading direction — D2 hypotheses

**H1.** Native relative URLs work *because* the local prod-shaped surface already serves the tree that way.  
**Validation:** `.claude/launch.json:5-8`; companion `href` at `ccar-p-prep-guide-v2.html:2505`; research relatives at `o1-pipeline-blog.html:436`. **ACCEPTED** for any publish that **preserves layout**. **REJECTED** for a flat copy of one HTML without siblings.

**H2.** Leaving document HTML unmodified is safe *because* intra-page nav and quiz engines already live in-file, and FR-1/`file://` stay true.  
**Validation:** FR-1 `ccar-p-prep-guide.spec.md:63-66`; atlas AC-1 `platform-design-atlas.spec.md:91-93`; quiz engine is inline (`ccar-p-prep-guide-v2.html:2510-2514`). **ACCEPTED.** Catalog is an *additional* file, not a wrapper.

**H3.** The missing capability is **inter-page** discovery, not a router.  
**Validation:** no `docs/index.html` (glob); OKF index catalogs markdown architecture artifacts (`docs/architecture/index.md:1-14`), not HTML explainers. **ACCEPTED.** One static catalog is enough for ≤24 pages.

**H4.** A publish manifest + href-closure check prevents the *class* of 404 (shipped file → unpublished sibling), not just this week’s atlas link.  
**Validation:** the class is demonstrated by P4 (guide→atlas) and the research cluster (blog→mocks/SVGs). No such check exists today (no `package.json`, no site test). **ACCEPTED as a fitness function to specify** — it does not exist yet. Not “zero code.”

**H5.** “New app under `apps/`” is necessary.  
**Validation:** no `apps/` tree; `atlas-docs` already serves in place. **REJECTED as necessity.** It is a packaging option: copy-root vs `docs/` as host root (axis D vs D1). Spec should pick one; D2 works with either.

**H6.** Hosting v2 is hosting “the” prep guide.  
**Validation:** `ccar-p-prep-guide-v3.spec.md:15`; `docs/architecture/log.md:10`. **REJECTED.** Default allowlist current = **v3 + atlas**; v1/v2 only if the catalog labels them provenance.

**Feasibility:** “trivial / no build” is true **only** if the host roots at a tree (D1 or D2-preserve). It is false if D4/D5/D6. Calendar cost of D2 is allowlist honesty + one catalog + one check, not a frontend rewrite.

---

## 6. Dependency structure

```
do-regardless (any D except D3)
  ├─ Explicit C4/publication override in the next spec
  ├─ Decide allowlist (axis A) — study cluster vs +explainers vs +research vs +cases
  └─ Decide host product (axis D) — Vercel vs GitHub Pages  [Ask-first ADR]

capability (reader URL)  vs  operational (how we publish)
  — often conflated; the human pick is usually capability first

D2 sequenced:
  1. Allowlist + closure graph (what href/src each file needs)
  2. Layout-preserving publish root
  3. Catalog index.html
  4. Closure check
  Host wiring (4) can parallel 3 once the root exists.

D1 is a subset: skip copy, still need catalog + “everything in docs/ is public” acceptance.

D4/D5/D6 need D2’s closure graph first (they still must know the link set).

D3 is independent — reject hosting entirely; no ADR if no new service.
```

**Load-bearing cost** is not engineering time; it is the **publication decision** (what must not leak) and the **allowlist** (research blogs pull in `mocks/` + SVGs).

---

## 7. Suggested allowlist seeds (not a spec)

| Cluster | Files (illustrative) | Link closure |
|---|---|---|
| **Study (minimum)** | `docs/ccar-p-prep-guide-v3.html`, `docs/claude-architect-m1-atlas.html` | sibling `href` — ship both or rewrite the footer |
| **Explainers** | `docs/architecture/explainers/o7-pipeline-story-v2.html`, `o7-human-approval.html` | no HTML `href` found; isolated |
| **MTA research** | o1/o2/o3 blogs, walkthrough, six-way comparison | **must** include `docs/research/mocks/**` and `o1-diagrams/**/*.svg` or accept 404s |
| **AWS-AI eval HTML** | `docs/research/aws-ai-eval-iteration-*/**/*.html` | live CDN (fonts, SheetJS) — different trust model |
| **Cases** | `junior-clean-architecture/index-v3.html` + `diagrams/*.svg` | different tree (`cases/`), not under `docs/` |
| **Provenance** | ccar-p v1/v2 | only if catalog marks superseded |

---

## 8. Human gate

Pick **what to specify next** by id. Bare “yes” is not consent.

**Recommended:** **D2** (curated allowlist, preserve relative URLs, one `index.html` catalog, link-closure check). Host product (Vercel vs Pages) and exact allowlist are clarify questions in `sdd-spec`.

| Id | Track |
|---|---|
| **D1** | Publish all of `docs/` + catalog index |
| **D2** | Curated allowlist + preserve paths + catalog + closure check |
| **D3** | Do not host; keep `atlas-docs` only |
| **D4** | React/hash catalog (evals-app style) |
| **D5** | Flatten slugs + rewrite hrefs at publish |
| **D6** | Injected shared chrome / iframe shell |

Optional split (reply with ids, e.g. `D2` + `A-study`):

- **A-study** — only current prep guide + atlas  
- **A-study+explainers** — plus o7 HTML  
- **A-docs** — whole `docs/` (same as D1 scope)  
- **A-plus-cases** — also junior-clean-architecture  

Advance → **sdd-spec** with the chosen direction + the validated hypotheses above.

### Gate result (2026-08-26)

Owner reply: `d2`.

**Locked:** D2 — curated allowlist, preserve relative path layout, one catalog `index.html`, link-closure check. Documents stay unmodified; no React/Vite/hash router; no flatten+rewrite.

**Allowlist rider (2026-08-26):** owner locked published prep guide = **v3**
(`docs/ccar-p-prep-guide-v3.html`). Spec treat as **A-study**: v3 + atlas
(D2 closure; footer `href` unmodified). v1/v2 not published.

**Still open (first `sdd-spec` clarify):** host product (Vercel vs GitHub Pages).
