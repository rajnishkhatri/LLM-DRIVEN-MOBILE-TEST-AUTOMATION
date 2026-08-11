"""kata CLI: the deterministic study instrument (spec sdd-roles-kata, item 6).

plan     expand a role registry + kata workload + reps into a byte-stable
         kata_plan (arms x instances x reps -> cells, per-role model/prompt
         bindings resolved at plan time). Clock-free, digest-stamped,
         all-or-nothing.
analyze  compute a byte-stable kata_verdict from a kata_plan + the frozen
         pre-registration + a kata_results observations file. This is where the
         §6 criteria + kill-rule live (kata_analyzer.evaluate). Fail-closed on
         stamp / digest / bijection / provenance / self-consistency violations.
report   re-project a kata_verdict into a Markdown scorecard. Never recomputes.

Exit taxonomy (spec F3, matching role-emit): argv-level misuse / input not
found / not-JSON exits 1 with usage on stderr and nothing written; every
render/validation-time failure (schema-invalid inputs, digest/stamp/bijection/
provenance/self-consistency violation, unresolved token) exits 2, also writing
nothing. Success exits 0. No exit code encodes "criteria met" — the verdict
content carries the booleans.

The literal token {args} in a registry invocation prompt renders verbatim here
(model resolution + prompt are plan-time bindings; {args} is substituted by the
deferred runner, not the plan).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from . import VALIDATOR_VERSION
from .kata_analyzer import PREREG_CONSTANTS, PREREG_DIGEST, evaluate
from .report import canonical_dumps

CATALOG_NAME = "sdd-roles"


class Usage(Exception):
    pass


class RenderFailure(Exception):
    pass


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_flags(args: list[str], spec: dict[str, bool]) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if not token.startswith("--") or token[2:] not in spec:
            raise Usage(f"unrecognized argument '{token}'")
        if i + 1 >= len(args):
            raise Usage(f"missing value for '{token}'")
        out[token[2:]] = args[i + 1]
        i += 2
    for name, required in spec.items():
        if required and name not in out:
            raise Usage(f"--{name} is required")
    return out


def _digest(obj) -> str:
    return hashlib.sha256(canonical_dumps(obj).encode("utf-8")).hexdigest()


def _load_and_validate(kernel: Path, path_flag: str, flags: dict, atype: str):
    """Read a JSON artifact, schema-validate it against its kernel schema.
    Not-found / not-JSON -> Usage (exit 1); schema-invalid -> RenderFailure
    (exit 2)."""
    path = Path(flags[path_flag])
    if not path.is_file():
        raise Usage(f"{path_flag} file not found: {flags[path_flag]}")
    try:
        data = _read_json(path)
    except (OSError, ValueError):
        raise Usage(f"{path_flag} file is not valid JSON")
    from .loader import SCHEMA_FILES

    try:
        import jsonschema

        jsonschema.validate(
            data, _read_json(kernel / "schemas" / SCHEMA_FILES[atype])
        )
    except Usage:
        raise
    except Exception:
        raise RenderFailure(f"{path_flag} fails {atype} schema validation")
    return data, path


def _prereg_constants(prereg: dict) -> dict:
    """The canonical constants block, in PREREG_CONSTANTS key order — the exact
    object PREREG_DIGEST is taken over (everything except the envelope +
    self-stamp fields)."""
    return {k: prereg[k] for k in PREREG_CONSTANTS}


def _assert_prereg_pinned(prereg: dict) -> None:
    """Digest-triangle check (ADR 0004), fail-closed. Recompute the digest from
    the prereg's OWN constants so a doctored constant with a stale-but-matching
    stored digest is still caught, and require agreement with the frozen code
    constants."""
    try:
        recomputed = hashlib.sha256(
            canonical_dumps(_prereg_constants(prereg)).encode("utf-8")
        ).hexdigest()
    except KeyError as exc:
        raise RenderFailure(f"pre-registration is missing constant {exc}")
    if recomputed != prereg.get("prereg_digest"):
        raise RenderFailure(
            "pre-registration prereg_digest does not match its own constants "
            "(a threshold was edited without re-pinning)"
        )
    if recomputed != PREREG_DIGEST:
        raise RenderFailure(
            "pre-registration digest mismatch against the frozen code constants"
        )


# ------------------------------------------------------------------- plan --


def render_plan(registry: dict, workload: dict, reps: int, default_model: str) -> dict:
    """Pure expansion of arms x instances x reps into a kata_plan. Model per
    role resolved from role.invocation.model, else default_model."""
    roles_by_id = {r["id"]: r for r in registry.get("roles", [])}
    arms = registry.get("arms", [])
    instances = workload.get("instances", [])
    if not arms:
        raise RenderFailure("registry declares no arms")
    if not instances:
        raise RenderFailure("workload declares no instances")

    gates: list[str] = []
    for r in registry.get("roles", []):
        for g in r.get("gates", []):
            if g not in gates:
                gates.append(g)
    gates.sort()

    def binding(role_id: str) -> dict:
        role = roles_by_id.get(role_id)
        if role is None:
            raise RenderFailure(f"arm references unknown role '{role_id}'")
        inv = role.get("invocation") or {}
        prompt = inv.get("prompt")
        if not prompt:
            raise RenderFailure(f"role '{role_id}' has no invocation.prompt")
        out = {
            "role": role_id,
            "model": inv.get("model") or default_model,
            "prompt": prompt,
        }
        if inv.get("agent"):
            out["agent"] = inv["agent"]
        return out

    cells = []
    for arm in arms:
        for inst in instances:
            for rep in range(reps):
                cells.append(
                    {
                        "cell_id": f"{arm['id']}/{inst['id']}/r{rep}",
                        "arm": arm["id"],
                        "instance": inst["id"],
                        "rep": rep,
                        "bindings": [binding(rid) for rid in arm["roles"]],
                    }
                )
    cells.sort(key=lambda c: (c["arm"], c["instance"], c["rep"]))

    registry_digest = _digest(registry)
    instances_out = [
        {
            "id": i["id"],
            "family": i["family"],
            "source_kata": i["source_kata"],
            "protected_tests": i["protected_tests"],
        }
        for i in instances
    ]
    stamp_src = (
        canonical_dumps(registry)
        + canonical_dumps(workload)
        + str(reps)
        + default_model
    )
    stamp = (
        f"{CATALOG_NAME} 1.4.0 "
        f"kata:{hashlib.sha256(stamp_src.encode('utf-8')).hexdigest()[:12]}"
    )
    plan = {
        "schema_version": "1.4.0",
        "artifact_type": "kata_plan",
        "stamp": stamp,
        "registry_digest": registry_digest,
        "prereg_digest": PREREG_DIGEST,
        "reps": reps,
        "arms": [a["id"] for a in arms],
        "instances": instances_out,
        "gates": gates,
        "cells": cells,
        "plan_digest": "",
    }
    plan["plan_digest"] = hashlib.sha256(
        canonical_dumps(cells).encode("utf-8")
    ).hexdigest()
    return plan


def plan(args: list[str]) -> int:
    flags = _parse_flags(
        args,
        {
            "kernel": True,
            "registry": True,
            "prereg": True,
            "workload": True,
            "reps": True,
            "default-model": False,
            "out": True,
        },
    )
    kernel = Path(flags["kernel"])
    registry, _ = _load_and_validate(kernel, "registry", flags, "role_registry")
    workload, _ = _load_and_validate(kernel, "workload", flags, "kata_workload")
    prereg, _ = _load_and_validate(kernel, "prereg", flags, "kata_preregistration")
    _assert_prereg_pinned(prereg)
    try:
        reps = int(flags["reps"])
    except ValueError:
        raise Usage("--reps must be an integer")
    if reps < 1:
        raise Usage("--reps must be >= 1")
    default_model = flags.get("default-model", "UNBOUND")
    built = render_plan(registry, workload, reps, default_model)
    Path(flags["out"]).write_text(canonical_dumps(built), encoding="utf-8")
    sys.stdout.write(f"planned: {len(built['cells'])} cells\n")
    return 0


# ---------------------------------------------------------------- analyze --


def _check_bijection(plan_cells: list[dict], observations: list[dict]) -> None:
    plan_ids = {c["cell_id"] for c in plan_cells}
    obs_ids = [o["cell_id"] for o in observations]
    obs_set = set(obs_ids)
    if len(obs_ids) != len(obs_set):
        dupes = sorted({i for i in obs_ids if obs_ids.count(i) > 1})
        raise RenderFailure(f"duplicate observation cell_id(s): {', '.join(dupes[:5])}")
    missing = sorted(plan_ids - obs_set)
    extra = sorted(obs_set - plan_ids)
    if missing:
        raise RenderFailure(f"observations missing plan cell(s): {', '.join(missing[:5])}")
    if extra:
        raise RenderFailure(f"observations name unknown cell(s): {', '.join(extra[:5])}")


def _check_self_consistency(observations: list[dict]) -> None:
    for o in observations:
        if o.get("provenance") != "tool_output":
            raise RenderFailure(
                f"{o['cell_id']}: provenance is not tool_output (anti-BMAD)"
            )
        gates = o.get("gates") or []
        all_final = all(g["final_pass"] for g in gates) if gates else False
        if o["final_all_gates_pass"] and not all_final:
            raise RenderFailure(
                f"{o['cell_id']}: final_all_gates_pass true but a gate final_pass is false"
            )


def _check_reps(plan_doc: dict, prereg: dict, accept_deviation: str | None) -> None:
    """F2 (ADR 0004): the plan's sample size must equal the registered `reps`,
    else the run is a declared deviation. Fail-closed — every other analyze check
    (bijection is over the plan's OWN cells, prereg_digest binds only the frozen
    constants) passes a silently-shrunk run, so without this a reps deviation
    slips through unremarked. The pre-registration stays frozen at its `reps`; a
    deviation is acknowledged at the invocation boundary, never by editing it."""
    plan_reps = plan_doc.get("reps")
    reg_reps = prereg.get("reps")
    if plan_reps == reg_reps:
        return
    if not accept_deviation:
        raise RenderFailure(
            f"plan reps {plan_reps} != pre-registered reps {reg_reps}: a "
            f"sample-size deviation must be declared with "
            f'--accept-deviation "<reason>" (ADR 0004; the pre-registration is '
            f"not edited). A smaller sample only makes a bar harder to clear."
        )
    sys.stderr.write(
        f"kata: DEVIATION ACCEPTED — plan reps {plan_reps} vs registered "
        f"{reg_reps}: {accept_deviation}\n"
    )


def analyze(args: list[str]) -> int:
    flags = _parse_flags(
        args,
        {"kernel": True, "plan": True, "prereg": True, "results": True,
         "out": True, "accept-deviation": False},
    )
    kernel = Path(flags["kernel"])
    plan_doc, _ = _load_and_validate(kernel, "plan", flags, "kata_plan")
    prereg, _ = _load_and_validate(kernel, "prereg", flags, "kata_preregistration")
    results, _ = _load_and_validate(kernel, "results", flags, "kata_results")

    _assert_prereg_pinned(prereg)
    _check_reps(plan_doc, prereg, flags.get("accept-deviation"))
    if results.get("prereg_digest") != PREREG_DIGEST:
        raise RenderFailure("results prereg_digest mismatch against frozen constants")
    if results.get("plan_stamp") != plan_doc.get("stamp"):
        raise RenderFailure("results plan_stamp does not match the plan's stamp")

    observations = results["observations"]
    _check_bijection(plan_doc["cells"], observations)
    _check_self_consistency(observations)

    body = evaluate(observations)
    verdict = {
        "schema_version": "1.4.0",
        "artifact_type": "kata_verdict",
        "plan_stamp": plan_doc["stamp"],
        "prereg_digest": PREREG_DIGEST,
        "input_digest": _digest(results),
        **body,
    }
    Path(flags["out"]).write_text(canonical_dumps(verdict), encoding="utf-8")
    sys.stdout.write(
        f"analyzed: winner {verdict['winner']} ({verdict['decision_reason']})\n"
    )
    return 0


# ------------------------------------------------------------------ report --


def _pct(v: int) -> str:
    """SCALE integer -> percent with 2 decimals, deterministic (no float)."""
    whole, frac = divmod(v, 100)
    return f"{whole}.{frac:02d}%"


def render_report(verdict: dict) -> str:
    lines = [
        "# Kata verdict scorecard",
        "",
        f"- winner: **{verdict['winner']}**",
        f"- decision: {verdict['decision_reason']}",
        f"- plan stamp: {verdict['plan_stamp']}",
        "",
        "## Arms",
        "",
        "| arm | decisional | k/n | rate | 95% interval | tokens | mutation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in verdict["arms"]:
        interval = f"[{_pct(s['wilson_lo10k'])}, {_pct(s['wilson_hi10k'])}]"
        lines.append(
            f"| {s['arm']} | {'yes' if s['decisional'] else 'ablation'} "
            f"| {s['k']}/{s['n']} | {_pct(s['rate10k'])} | {interval} "
            f"| {s['tokens_sum']} | {_pct(s['mutation_score_mean10k'])} |"
        )
    lines += ["", "## Criteria", "", "| id | passed | operands |", "| --- | --- | --- |"]
    for cr in verdict["criteria"]:
        ops = ", ".join(f"{o['name']}={o['value']}" for o in cr["operands"])
        lines.append(f"| {cr['id']} | {'yes' if cr['passed'] else 'no'} | {ops} |")
    lines += [
        "",
        "## Ablation (diagnostic only)",
        "",
        f"- C minus C-dbg: {_pct(verdict['ablation']['c_minus_cdbg_pp10k'])}",
        f"- intervals non-overlapping: "
        f"{'yes' if verdict['ablation']['intervals_nonoverlap'] else 'no'}",
        "",
        "## Decision flags",
        "",
        f"- C earns six roles: {'yes' if verdict['c_earns_six_roles'] else 'no'}",
        f"- B beats A: {'yes' if verdict['b_beats_a'] else 'no'}",
        f"- kill-rule triggered: {'yes' if verdict['kill_rule_triggered'] else 'no'}",
        f"- tamper-fail: {'yes' if verdict['tamper_fail'] else 'no'}",
        "",
    ]
    return "\n".join(lines)


def report(args: list[str]) -> int:
    flags = _parse_flags(args, {"kernel": True, "verdict": True, "out": True})
    kernel = Path(flags["kernel"])
    verdict, _ = _load_and_validate(kernel, "verdict", flags, "kata_verdict")
    Path(flags["out"]).write_text(render_report(verdict), encoding="utf-8")
    sys.stdout.write("reported\n")
    return 0


# ------------------------------------------------------------------- main --


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            raise Usage("subcommand required: plan | analyze | report")
        cmd, rest = args[0], args[1:]
        if cmd == "plan":
            return plan(rest)
        if cmd == "analyze":
            return analyze(rest)
        if cmd == "report":
            return report(rest)
        raise Usage(f"unknown subcommand '{cmd}'")
    except Usage as u:
        sys.stderr.write(f"kata: error: {u}\n")
        return 1
    except RenderFailure as r:
        sys.stderr.write(f"kata: failure: {r}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
