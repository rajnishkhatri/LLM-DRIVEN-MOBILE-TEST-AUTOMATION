# Plan: Authored-HTML static site (html-site-hosting)

**Spec:** [`html-site-hosting.spec.md`](../specs/html-site-hosting.spec.md)
(SPEC-OK 2026-08-26, C1–C4 locked).
**Status:** PLAN-OK 2026-08-26 — F1–F3 ratified as drafted. Tasks:
[`html-site-hosting.tasks.md`](html-site-hosting.tasks.md).
**ADR:** [`0001-static-github-pages-origin-for-study-html.md`](../../architecture/adrs/application/html-site/0001-static-github-pages-origin-for-study-html.md)
(Accepted at PLAN-OK 2026-08-26).
**Change class:** small static publish tree + stdlib copy/closure check +
GitHub Actions Pages deploy. No new npm/runtime dependency. `check_gate`
(skill-sync) untouched. `test_gate` is `<none>` — the script’s own
`--selftest` covers AC-3/AC-4.

## A1 — simplest machinery statement

One app folder, one stdlib Python script, one TOML manifest, one authored
catalog, one GitHub Actions workflow that copies then uploads a generated
`dist/`. Rejected as over-machinery: Vite/React/Tailwind (new dep → ADR,
and D4 was declined), Vercel (C1 declined), committed HTML copies (C2
declined — second source of truth), serving `apps/html-site/` wholesale
(would put `publish.py` and the manifest on the public origin), href
rewriting (D5), an iframe shell (D6), pytest (repo `test_gate` is `<none>`;
a `--selftest` in the same file is enough).

## G1 — the two abstractions that survive A1

| Abstraction | What it buys | Simpler thing rejected |
|---|---|---|
| `manifest.toml` | Open/Closed: a later cluster is a data row, not a Python edit. Wrong row fails loud. | Hardcoded file list in `publish.py` — silent when the next author forgets to edit both the catalog and the script. |
| generated `dist/` | FR-1: the origin is exactly the three allowlisted files. Scripts never ship. | In-place gitignored siblings next to `publish.py` — one mistaken Pages “root = apps/html-site” leaks the toolchain. |

## Architecture

```
apps/html-site/
  index.html          # catalog (C4), committed, authored here
  manifest.toml       # allowlist: catalog + docs/ sources → publish names
  publish.py          # copy from docs/ → dist/, then closure + identity check
  dist/               # GENERATED, gitignored
    index.html
    ccar-p-prep-guide-v3.html
    claude-architect-m1-atlas.html
.github/workflows/html-site.yml   # on push to main: publish.py then Pages artifact
```

**SRP split (constitution):** catalog (how you find a page) ≠ document (the
page, untouched under `docs/`) ≠ host (Pages) ≠ check (fitness function).

**Coupling:** relative `href`/`src` stay the integration contract. v3 and the
atlas are siblings in `dist/` so `href="claude-architect-m1-atlas.html"`
resolves with zero rewrite (FR-2, AC-6).

**Style:** static file server. Matches the files. Pages is that server on a
public GitHub repo.

### Manifest v1 (literal)

```toml
# apps/html-site/manifest.toml — commit-time allowlist (FR-1).
catalog = "index.html"

[[document]]
source = "docs/ccar-p-prep-guide-v3.html"
publish_as = "ccar-p-prep-guide-v3.html"

[[document]]
source = "docs/claude-architect-m1-atlas.html"
publish_as = "claude-architect-m1-atlas.html"
```

`catalog` is copied from `apps/html-site/index.html` (no `docs/` canonical).
Each `[[document]]` is copied from repo-relative `source` to
`dist/<publish_as>`. Unknown paths are simply absent from `dist/` → origin
404 (AC-1). v1/v2 are not rows.

### `publish.py` (stdlib only: pathlib, shutil, tomllib, html.parser, argparse)

Python ≥3.11 (`tomllib`), same floor as skill-sync. No package, no deps.

```
python3 apps/html-site/publish.py              # wipe dist/, copy, check; exit 0/1/2
python3 apps/html-site/publish.py --check DIR  # closure check only (AC-3 fixture)
python3 apps/html-site/publish.py --selftest   # temp fixtures; AC-3 fail + AC-4 pass + AC-7
```

Exit: 0 green · 1 usage/config (bad/missing manifest, missing canonical) ·
2 check failure (dangling relative href/src, or published bytes ≠ canonical).

**Copy (FR-3, AC-7):** wipe `dist/`; copy catalog; for each document,
`Path.read_bytes`/`write_bytes` (byte-identical by construction); then
re-compare. A later editor who “fixes” a file in `dist/` is overwritten next
run; `dist/` is gitignored so that edit cannot land.

**Closure (FR-5, AC-3/AC-4):** for every `*.html` in the tree, parse
`href`/`src` with `html.parser`. Ignore fragment-only (`#…`), `http:`,
`https:`, `mailto:`, `data:`, `javascript:`. Strip fragments from the rest;
resolve relative to the HTML file’s directory; **fail** naming the missing
path if it is not a file in the tree. Intra-page `#d1` etc. are ignored
(FR-6).

**Local preview (FR-8):**

```
python3 apps/html-site/publish.py
python3 -m http.server 8124 --bind 127.0.0.1 -d apps/html-site/dist
```

`atlas-docs` (port 8123, `-d docs`) is unchanged.

### Catalog `index.html` (FR-4, AC-2, AC-5, C4)

Hand-authored, zero JS, system fonts, no CDN. Title **Study files**. One
line: unofficial CCAR-P prep guide (v3) and Claude Architect Module-1 atlas.
Two native `<a href>` to the sibling filenames. Footer: not Anthropic, not
the exam. Exact wording tunable at implement; the shape is locked.

### GitHub Pages (FR-9, ADR 0001)

`.github/workflows/html-site.yml`:

- trigger: `push` to `main` (repo default branch)
- `permissions: { contents: read, pages: write, id-token: write }`
- job: checkout → `python3 apps/html-site/publish.py` (must exit 0) →
  `actions/configure-pages` → `actions/upload-pages-artifact` with
  `path: apps/html-site/dist` → `actions/deploy-pages`
- concurrency group `pages`; do not cancel in-progress (avoid a half-deploy)

This is the **first real** `.github/workflows/` in this repo (other
`.github/` trees are sdd-roles corpus projections — do not touch those).

Expected origin after the Settings flip + a green run on `main`:
`https://rajnishkhatri.github.io/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/`
(project Pages default; no custom domain in this spec).

**Owner one-time (cannot be a committed file):** repo Settings → Pages →
Source = **GitHub Actions**. Until that flip, the workflow uploads and
deploy fails loud. Recorded as a task, not as hope.

## File touchpoints

| Op | File | Why |
|---|---|---|
| NEW | `apps/html-site/manifest.toml` | FR-1 allowlist |
| NEW | `apps/html-site/index.html` | FR-4 / C4 catalog |
| NEW | `apps/html-site/publish.py` | FR-3 copy + FR-5 closure + `--selftest` |
| NEW | `.github/workflows/html-site.yml` | FR-9 Pages deploy from `dist/` |
| EDIT | `.gitignore` | add `apps/html-site/dist/` |
| NEW | `docs/architecture/adrs/application/html-site/0001-static-github-pages-origin-for-study-html.md` | Ask-first ADR (already drafted, Proposed) |
| APPEND | `docs/architecture/log.md` | FR-7: public origin exists; C4 override for v3+atlas |
| EDIT | `docs/architecture/index.md` | one hand-grouped `html-site` pointer at the ADR |

**Not touched:** the two canonical HTML files; `docs/ccar-p-prep-guide.html`
/ `-v2.html`; `.claude/launch.json` `atlas-docs`; skill surfaces;
`tooling/sdd-roles/**/.github/**`.

## Constitution check

| Principle | How this plan holds it |
|---|---|
| Single Responsibility | catalog / documents / host / check are four files, four jobs |
| Open/Closed | new page = manifest row + catalog `<a>`; documents not rewritten |
| Coupling | relative URLs remain the seam; no router inverts them |
| Simplest style | static origin for static files |
| Trade-off | Pages + Actions vs Vercel vs D1 vs D3 — recorded in ADR 0001 |

No numbered eight-invariant constitution in this workspace; the binding
points at `.cursor/rules/architecture-principles.mdc`. Nothing here writes
a skill surface → AC-9 (`skill_sync.py check`) stays exit 0 by construction.

## Order (Stage-3 task seeds)

T1 manifest + `publish.py --selftest` red (AC-3 fixture fails naming the
atlas; AC-4 green fixture; missing canonical → exit 1) → T2 copy path
(AC-7 byte-identity; wipe+copy into `dist/`) → T3 catalog `index.html`
(AC-2/AC-5, C4 copy) → T4 `.gitignore` + local FR-8 serve note in the
script docstring → T5 workflow + ADR Compliance is that workflow → T6 log +
index pointer. T3 can parallel T1 once the sibling filenames are known.

## Risks / notes

- Live URL is **not** produced on this feature branch. It appears after
  merge to `main` plus the Settings flip. Local FR-8 is the implement-time
  proof; AC-1 on the public origin is confirmed after first deploy.
- GitHub Pages 404 body is GitHub’s, not ours. AC-1 accepts “file absent
  from the publish tree.”
- `html.parser` will not see URLs inside inline JS. The two canonicals’
  companion link is a plain `href` (verified at spec time,
  `docs/ccar-p-prep-guide-v3.html:2510`). Out of scope: inventing a JS-href
  crawler.
- Workflow actions are pinned by major tag at implement (`@v4` / `@v5`
  current); digest-pinning is a later hardening, not this spec.

## PLAN-OK forks (ratify as drafted, or amend)

| ID | Fork | Recommendation |
|----|------|----------------|
| F1 | ADR series home | **New** `application/html-site/` 0001. Not MTA 0018 (wrong quantum). |
| F2 | Generated tree | **`dist/`**, gitignored, only path the workflow uploads. |
| F3 | Pages trigger | **Actions on `main`**. Branch-from-folder is incompatible with C2. |

Gate: CLOSED 2026-08-26 — PLAN-OK; F1–F3 ratified as drafted; ADR 0001
Proposed → Accepted. Stage 3 tasks + Stage 4 analyze follow.
