# Provenance model (S7) and named-check routing

Every content-bearing HandoffContract site (`summary`, each `decisions[i]`,
each `completion_evidence[i]`) carries a `provenance` object:

```json
{
  "source": "role_authored | tool_output | environment_quoted",
  "derived_from": ["<fence-or-field id>", "..."],
  "fence_id": "<full sha256>",          // required when source = environment_quoted
  "tool": { "id", "version", "invocation_digest" }   // required when source = tool_output
}
```

- **environment_quoted** content travels **byte-verbatim** inside `fences[]`
  entries keyed by the **full sha256 of the fenced content bytes** (no
  truncated prefixes), with `source_uri` + `retrieved_at`. LLM paraphrase
  launders injection into trusted prose; verbatim fencing is the point.
- **Taint is sticky and monotonic through declared derivation**: a field whose
  `derived_from` names an environment fence must itself be `environment_quoted`
  (CHK-TAINT). Undeclared derivation is a D7/audit concern (item 3), not a
  validator claim.
- **tool_output** is valid only with a registered binding: tool id from the
  KernelConfig `gate_tool_allowlist`, plus `tool_version` and an invocation
  digest (CHK-TOOLBIND) — arbitrary shell output cannot launder environment
  content into a trusted class.

## Named-check routing (deliberate schema looseness)

Where the spec names a check for a failure mode, the schema deliberately leaves
that field optional so the failure surfaces under its **named** check id rather
than as a generic CHK-SCHEMA error:

| Failure | Surfaces as |
|---|---|
| provenance object absent at a site | CHK-PROV-PRESENT |
| fence id wrong/truncated; missing `source_uri`/`retrieved_at` | CHK-FENCE |
| tool binding missing/unregistered/incomplete | CHK-TOOLBIND |
| `threshold` absent/unnamed/value-drifted on a GateOutcome | CHK-THRESH |
| decision floors (empty set, missing rationale, alternatives floor) | CHK-DECISIONS (the schema's oneOf may double-report as CHK-SCHEMA; the named finding is always present) |

Structural inexpressibility stays schema-level: closed objects (no verdict
field on GateOutcome, no arm-membership on Role), `environment_quoted ⇒
fence_id`, the protected-set required keys (CHK-PROTECT is also check-reported).
