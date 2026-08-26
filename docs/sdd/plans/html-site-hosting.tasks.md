# Tasks: Authored-HTML static site (html-site-hosting)

**Status:** TASKS-OK 2026-08-26 — Stage-4 analyze accepted; no CRITICAL
findings. Advance → **sdd-implement**, T1.1 first.

**Spec:** [`html-site-hosting.spec.md`](../specs/html-site-hosting.spec.md)
(SPEC-OK) · **Plan:** [`html-site-hosting.plan.md`](html-site-hosting.plan.md)
(PLAN-OK 2026-08-26, F1–F3 ratified) · **ADR 0001** Accepted.
Legend: `[dep: …]` prerequisite · `[P]` may run in parallel · red-first on
the `--selftest` tasks.

---

| Id | Task (file-level) | Depends | ACs | Pass/fail |
|---|---|---|---|---|
| **T1.1** | Write `apps/html-site/manifest.toml` literal from the plan | — | FR-1 seed | `python3 -c "import tomllib,pathlib; tomllib.loads(pathlib.Path('apps/html-site/manifest.toml').read_text())"` succeeds; two `[[document]]` rows + `catalog` |
| **T1.2** | `publish.py`: `--selftest` skeleton with three sections (AC-3 fail tree = v3 HTML whose `href` names the atlas, atlas absent → exit 2 naming `claude-architect-m1-atlas.html`; AC-4 v1 tree green → exit 0; missing canonical → exit 1) — **run it: RED** | T1.1 | AC-3, AC-4 | selftest exits non-zero listing the failing sections; output pasted |
| **T1.3** | Implement wipe+copy into `dist/`, byte-identity compare, `html.parser` closure check, CLI (`publish.py` / `--check DIR` / `--selftest`); make T1.2 green | T1.2 | AC-3, AC-4, AC-7 | `--selftest` exit 0; after default run, `dist/*.html` bytes equal the two `docs/` canonicals; output pasted |
| **T2** [P] | Author `apps/html-site/index.html` (C4): title Study files; one-line unofficial v3 + atlas; two native `<a href>` to the sibling filenames; footer not Anthropic / not the exam; **zero** `<script>` | T1.1 | AC-2, AC-5 | grep: both target filenames as `href`; no `<script`; title contains `Study files` |
| **T3** | Append `apps/html-site/dist/` to root `.gitignore`; docstring on `publish.py` shows the FR-8 two-liner (`publish.py` then `http.server -d apps/html-site/dist`) | T1.3 | FR-8 | `gitignore` contains the path; docstring contains `http.server` |
| **T4** | Add `.github/workflows/html-site.yml` as planned (push to `main`, Pages permissions, `publish.py` must exit 0, upload `apps/html-site/dist` only). Do **not** touch `tooling/sdd-roles/**/.github/**` | T1.3, T2, T3 | FR-9, AC-1 (tree) | workflow file exists; `path: apps/html-site/dist`; no new file under the sdd-roles corpus `.github/` |
| **T5** | Run `python3 apps/html-site/publish.py` from repo root. Assert `dist/` contains **exactly** the three allowlist names and does **not** contain `ccar-p-prep-guide.html` or `ccar-p-prep-guide-v2.html`. Confirm v3’s companion `href` target exists as a sibling in `dist/` | T2, T1.3 | AC-1, AC-6, AC-7 | `ls dist` is the three names; `cmp` of the two documents vs `docs/` is silent; atlas path exists |
| **T6** [P] | Construction invariants: no `package.json` / Vite / React / Tailwind added for this site; `python3 tooling/skill-sync/skill_sync.py check` from repo root exit 0 | T4 | AC-8, AC-9 | `test ! -f package.json`; `test ! -f apps/html-site/package.json`; skill-sync exit 0 pasted |
| **T7** | Append FR-7 line to `docs/architecture/log.md` (public origin for v3+atlas; prep-guide C4 overridden for those two only). Hand-group a `html-site` pointer on `docs/architecture/index.md` to ADR 0001 | T5 | FR-7 | both files name the origin/ADR; v1/v2 still described as repo-only |
| **T8** | Owner one-time: GitHub Settings → Pages → Source = GitHub Actions. Not a committed file. Do this when merging to `main`; live URL is then `https://rajnishkhatri.github.io/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/` | T4, merge to `main` | FR-9 (ops) | Pages source is Actions; first workflow on `main` is green. **Not required to close implement on this branch.** |

[P] = parallelizable within its dependency level (T2 after T1.1; T6 after T4).

## EARS coverage (1:1)

| AC | Covered by |
|---|---|
| AC-1 unknown path 404 / absent | T5 (`dist/` exactly three names; v1/v2 absent) + T4 (workflow uploads only `dist/`) |
| AC-2 JS disabled, native links | T2 (no `<script`; native `<a href>`) |
| AC-3 closure fail names atlas | T1.2 → T1.3 (`--selftest` fail fixture) |
| AC-4 closure pass on v1 tree | T1.2 → T1.3 (`--selftest` green fixture) |
| AC-5 catalog → v3 not v1/v2 | T2 (`href` is `ccar-p-prep-guide-v3.html`) |
| AC-6 v3 companion footer loads atlas | T5 (sibling exists in `dist/` after copy) |
| AC-7 published bytes = canonicals | T1.3 + T5 (`cmp`) |
| AC-8 no package.json / Vite / React / Tailwind | T6 |
| AC-9 skill-sync check exit 0 | T6 |

Measurability: every AC is a command or a grep except T8 (dashboard), which
the spec already allows to be “file absent from the publish tree” for AC-1
and which the plan records as post-merge. No criterion flagged back to the
spec.

## Stage-4 analyze (2026-08-26)

- **Cross-artifact:** every AC has ≥1 owning task (table above — no
  zero-coverage criterion). C1 GitHub Pages ↔ T4/T8. C2 generate-from-docs
  ↔ T1.3 (no committed HTML copies). C4 catalog copy ↔ T2. ADR 0001
  Compliance = `publish.py` + the workflow. No task edits a canonical HTML
  file (FR-6). No CRITICAL findings.
- **Grounding (this session):**
  - `docs/ccar-p-prep-guide-v3.html` exists; companion `href` at line 2510
    is `claude-architect-m1-atlas.html`
  - `docs/claude-architect-m1-atlas.html` exists
  - `apps/` absent (T1.1 creates `apps/html-site/`) — no collision
  - no repo-root `.github/workflows/` (T4 creates the first real one;
    sdd-roles corpus `.github/` trees are out of touch)
  - no `package.json` anywhere in the workspace
  - `python3` = 3.13.5; `tomllib` importable (plan floor ≥3.11 holds)
  - `python3 tooling/skill-sync/skill_sync.py check` from repo root →
    exit 0 (6 families, 0 drifted, 0 shadow)
  - no new dependency declared; ADR 0001 is the Ask-first record
- **Baseline gates:** `check_gate` green (above). `test_gate` is `<none>` —
  skipped per binding. `--selftest` is this change’s executable law (same
  skip of Gherkin as skill-sync).
- **Constitution:** SRP/Open-Closed/coupling/simplest-style held in the
  plan’s constitution table. New series `application/html-site/` does not
  collide with MTA 0001–0017.

No CRITICAL findings. Advance → **sdd-implement**, T1.1 first.

## Two hard gates (per sdd-spec)

1. **SPEC-OK** — closed 2026-08-26 (C1–C4).
2. **PLAN-OK** — closed 2026-08-26 (F1–F3).
Tasks are drafted; Stage-4 analyze is above. **TASKS-OK** 2026-08-26.
