# Junior Clean Architecture Blog (Silicon Sandwiches)

Self-contained mentoring post: Uncle Bob–style Clean Architecture (chapters 20+) told through the Silicon Sandwiches franchise-ordering kata.

## Open the post

No build step. From this directory:

```bash
open index.html
# or: python3 -m http.server 8080
# then visit http://localhost:8080/
```

Diagrams load via relative paths (`diagrams/*.svg`). Serving over `http://` avoids some browsers blocking local `file://` SVG loads; opening the file directly usually works too.

## Re-render diagrams

Requires [D2](https://d2lang.com/) on `PATH` (`d2 --version`).

```bash
cd diagrams
for f in ss-scream-vs-framework ss-clean-rings ss-dip-crossing \
         ss-humble-presenter ss-details-at-edge ss-services-fallacy \
         ss-package-by-component; do
  d2 "$f.d2" "$f.svg"
done
```

These are **hand-authored D2 → SVG**. They are not C4 IR and are not gated by `scripts/lint_diagram.py`.

## Layout

```
junior-clean-architecture/
  index.html
  README.md
  diagrams/
    ss-scream-vs-framework.{d2,svg}
    ss-clean-rings.{d2,svg}
    ss-dip-crossing.{d2,svg}
    ss-humble-presenter.{d2,svg}
    ss-details-at-edge.{d2,svg}
    ss-services-fallacy.{d2,svg}
    ss-package-by-component.{d2,svg}
```

## Self-audit

| Check | Status |
|---|---|
| Ch. 20 Business Rules — §2 owns Entity / UseCase / models | Yes (once) |
| Ch. 21 Screaming — §1 + `ss-scream-vs-framework` | Yes (once) |
| Ch. 22 Clean Architecture rings + DIP + DTOs — §3 + rings/DIP figures | Yes (once) |
| Ch. 19 Policy & Level — 2–3 sentences inside §3 (not a standalone section) | Yes |
| Ch. 23 Humble Objects — §4 + presenter figure | Yes (once) |
| Ch. 25 Layers & Boundaries — §5 owns multiplying streams | Yes (once) |
| Ch. 24 Partial Boundary — sidebar inside §5 only | Yes (once) |
| Ch. 26 Main — §6 code-focused | Yes (once) |
| Ch. 27 Services — §8 gluten-free surcharge + services figure | Yes (once) |
| Ch. 28 Test Boundary — §9 | Yes (once) |
| Ch. 29 Embedded — footnote only (`#ch29-footnote`) | Yes |
| Ch. 30 + 32 Details (DB + frameworks) — merged §7 + details figure | Yes (once each theme) |
| Ch. 34 Package by Component — §10 + packaging figure | Yes (once) |
| Cast naming consistent (Order, Offer, FranchiseShop, PlaceOrder, ResolveOffer, ports/adapters, Spring `@Configuration`) | Yes |
| No C4 IR / `lint_diagram.py` pipeline | Yes — raw D2 only |
| No loan / non-SS examples in diagrams | Yes — Silicon Sandwiches labels throughout |
