# Honesty tags — carrying genuine gaps, never inventing facts

The dominant, well-documented failure mode of LLM diagram generation is **fact
fabrication** — inventing SLAs, vendors, regions, instance counts, latency
figures (diagramskill.md, "Fact fabrication/confabulation"). This family
forbids it structurally.

## The rule

**Do not invent facts.** No SLA numbers, vendor names, region names, cloud
provider logos, product logos, instance counts, or latency figures beyond the
label text supplied in the IR. Where a fact is unknown, the IR carries an
explicit honesty tag, rendered **verbatim and visibly** — never silently
defaulted.

## The tags

| Tag | Means |
|---|---|
| `SLA: UNKNOWN (pending)` | No SLA is on file. Name the probe that would resolve it in a companion register. |
| `PROVISIONAL` | The element exists but its contract/tier/vendor is unverified. |
| `PROPOSED ADR NNNN` | Drafted but not separately accepted. Drops when the ADR is accepted. |

## How they render

- Honesty tags are **text** written into the node/edge label in the IR. They
  are verbatim-checked by the linter like any other label.
- Colour (the orange `evidence-gap` family) may *reinforce* a tag but never
  *replaces* it — the word must be present so the meaning survives grayscale.
- **Pending-ness is a text tag, never a line style.** Do not use a dashed line
  to imply "proposed" — dashed means async only (see
  [line-semantics.md](line-semantics.md)).

## The enforcement backbone: the IR forbids invention

The IR schema (see [ir-schema.md](ir-schema.md)) has **no fillable numeric
fields** the model can populate. Unknowns must be an explicit tag. The IR also
carries a `forbidden_facts` list of regex patterns (vendor/region/SLA markers);
the linter (`forbidden-facts` check) fails the SVG if any appears. If the spec
is ambiguous on a required field, **stop and ask** rather than defaulting.
