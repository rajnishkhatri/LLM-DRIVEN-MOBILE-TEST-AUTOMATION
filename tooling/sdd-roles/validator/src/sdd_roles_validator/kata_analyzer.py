"""The pre-registered analysis, frozen in code (spec sdd-roles-kata, S3/S4/S5).

This module is the immutable half of the digest triangle (ADR 0004): the §6
criteria and kill-rule live here as `PREREG_CONSTANTS`, and `PREREG_DIGEST` is
their sha256 taken at import. The `kata` selftest section asserts the committed
`kata-preregistration.json` canonical constants block byte-agrees with this
digest; every `kata_results` file the analyzer accepts must carry a matching
`prereg_digest`. A post-hoc threshold edit must therefore change this file AND
the committed artifact AND re-pin every results file — a loud, atomic amendment,
never a silent edit.

Everything is exact integer arithmetic (S4): scale S=10000, z frozen as
z**2 = 9604/2500 (z=1.96, C7), `math.isqrt` plus a perfect-square correction
the sole irrational op. Both Wilson bounds use the WIDENED half-width so the
interval never narrows versus the exact real interval — a floored lower bound
would narrow it and make a false C-win easier (the exact trap C-3 pins shut).

# do not refactor the wilson_interval / rate10k / evaluate expressions after
# the golden is cut — any algebraically-equal reorder that shifts an isqrt by 1
# flips every committed verdict golden. The byte-identical gate IS the guard.
"""

from __future__ import annotations

import hashlib
import math

from .report import canonical_dumps

# --- the frozen pre-registration (spec F1; §6 verbatim) --------------------

PREREG_CONSTANTS = {
    "arms": ["A", "B", "C", "C-dbg"],
    "reps": 5,
    "instance_count": 12,
    "primary_metric": "final_all_gates_pass",
    "interval_method": "wilson",
    "wilson_z_num": 9604,
    "wilson_z_den": 2500,
    "scale": 10000,
    "criteria": {
        "c_over_a_pp": 10,
        "c_over_a_intervals": "non-overlapping",
        "c_over_a_token_ratio_max": 3,
        "c_over_b_pp": 5,
        "b_over_a_pp": 5,
        "b_over_a_token_ratio_max": 2,
        "kill_a_within_c_pp": 5,
        "kill_a_token_num": 1,
        "kill_a_token_den": 2,
        "tamper_zero_tolerance": True,
    },
}

PREREG_DIGEST = hashlib.sha256(
    canonical_dumps(PREREG_CONSTANTS).encode("utf-8")
).hexdigest()

SCALE = PREREG_CONSTANTS["scale"]
Z2_NUM = PREREG_CONSTANTS["wilson_z_num"]
Z2_DEN = PREREG_CONSTANTS["wilson_z_den"]
_C = PREREG_CONSTANTS["criteria"]
PP_C_OVER_A = _C["c_over_a_pp"] * SCALE // 100          # 10pp -> 1000
PP_C_OVER_B = _C["c_over_b_pp"] * SCALE // 100          # 5pp  -> 500
PP_B_OVER_A = _C["b_over_a_pp"] * SCALE // 100          # 5pp  -> 500
PP_KILL = _C["kill_a_within_c_pp"] * SCALE // 100       # 5pp  -> 500

# The decisional arms (§6): C-dbg is a non-decisional ablation — it contributes
# ZERO operands to any criterion or the kill-rule.
DECISIONAL_ARMS = ("A", "B", "C")
ABLATION_ARM = "C-dbg"


# --- integer statistics (S4) ------------------------------------------------


def _ceil_sqrt(x: int) -> int:
    """Exact integer ceil of sqrt(x) for x >= 0: isqrt plus a perfect-square
    correction (isqrt alone floors)."""
    h = math.isqrt(x)
    return h if h * h == x else h + 1


def rate10k(k: int, n: int) -> int:
    """Point pass-rate as an integer on [0, SCALE], round-half-up. Display +
    point-margin deltas only — never inside an interval predicate (S4)."""
    if n <= 0:
        return 0
    return (k * SCALE + n // 2) // n


def wilson_interval(k: int, n: int) -> tuple[int, int]:
    """Wilson 95% score interval as integer bounds on [0, SCALE], BOTH widened
    (lower floored-down, upper ceiled-up) so the interval never narrows versus
    the exact real interval. z**2 = Z2_NUM/Z2_DEN (=1.96**2).

    Real center  = (k + z2/2) / (n + z2)
    Real halfw   = z * sqrt( k*(n-k)/n + z2/4 ) / (n + z2)

    Put over the common denominator D = n + z2 and the perfect-square
    denominator (2*n*Z2_DEN) so isqrt is exact. All terms are exact integers.
    """
    if n <= 0:
        return (0, SCALE)
    # Wilson, z2 = Z2_NUM/Z2_DEN. Put over the exact denominator
    #   D = n + z2 = (n*Z2_DEN + Z2_NUM) / Z2_DEN, so d_num = n*Z2_DEN + Z2_NUM.
    d_num = n * Z2_DEN + Z2_NUM
    # center = (k + z2/2)/D = (2*k*Z2_DEN + Z2_NUM) / (2*d_num)
    center_num = 2 * k * Z2_DEN + Z2_NUM
    center_den = 2 * d_num
    # half-width = z*sqrt(k*(n-k)/n + z2/4) / D. Squaring the numerator and
    # clearing fractions over the perfect-square denominator (2*n*Z2_DEN)**2:
    #   z2*(k*(n-k)/n + z2/4) = R / (2*n*Z2_DEN)**2,
    #   R = Z2_NUM * (4*n*k*(n-k)*Z2_DEN + n*n*Z2_NUM)
    # so the numerator-of-halfw (before /D) = sqrt(R)/(2*n*Z2_DEN), and dividing
    # by D = d_num/Z2_DEN gives halfw = sqrt(R) / (2*n*d_num).
    radicand = Z2_NUM * (4 * n * k * (n - k) * Z2_DEN + n * n * Z2_NUM)
    halfw_num = _ceil_sqrt(radicand)                # widened up
    halfw_den = 2 * n * d_num
    # Scale to [0, SCALE], widening: floor the lower bound, ceil the upper.
    #   lo = floor( (center - halfw) * SCALE ), hi = ceil( (center + halfw)*SCALE )
    # common denominator for center - halfw is center_den (== 2*d_num) and
    # halfw_den (== 2*n*d_num); halfw_den = n * center_den, so scale center up.
    lo_num = center_num * n * SCALE - halfw_num * SCALE
    hi_num = center_num * n * SCALE + halfw_num * SCALE
    den = halfw_den                                 # = n * center_den
    lo = lo_num // den                               # floor (widens down)
    hi = -((-hi_num) // den)                         # ceil (widens up)
    lo = max(0, min(SCALE, lo))
    hi = max(0, min(SCALE, hi))
    return (lo, hi)


# --- aggregation ------------------------------------------------------------


def _arm_aggregate(arm: str, rows: list[dict]) -> dict:
    n = len(rows)
    k = sum(1 for r in rows if r["final_all_gates_pass"])
    tokens_sum = sum(r["tokens"] for r in rows)
    lo, hi = wilson_interval(k, n)
    mut = [r["mutation_score"] for r in rows]
    crap_max = max((r["crap"]["max"] for r in rows), default=0)
    return {
        "arm": arm,
        "decisional": arm in DECISIONAL_ARMS,
        "k": k,
        "n": n,
        "rate10k": rate10k(k, n),
        "wilson_lo10k": lo,
        "wilson_hi10k": hi,
        "tokens_sum": tokens_sum,
        "tokens_mean": tokens_sum // n if n else 0,
        "mutation_score_mean10k": sum(mut) // n if n else 0,
        "crap_max": crap_max,
        "wall_clock_ms_sum": sum(r["wall_clock_ms"] for r in rows),
        "handoff_schema_failures": sum(r["handoff_schema_failures"] for r in rows),
        "tamper_events": sum(r["tamper_events"] for r in rows),
        "insufficient_data": n == 0,
    }


def _operand(name: str, value: int) -> dict:
    return {"name": name, "value": int(value)}


def evaluate(observations: list[dict]) -> dict:
    """Pure verdict computation over the results observations. Returns the
    kata_verdict body sans the plan_stamp/prereg_digest/input_digest envelope
    (the caller stamps those). All comparisons integer; C-dbg excluded from
    every decision operand (S5)."""
    by_arm: dict[str, list[dict]] = {}
    for r in observations:
        by_arm.setdefault(r["arm"], []).append(r)

    arm_stats = [
        _arm_aggregate(arm, by_arm.get(arm, []))
        for arm in PREREG_CONSTANTS["arms"]
    ]
    stat = {s["arm"]: s for s in arm_stats}

    a, b, c = stat.get("A"), stat.get("B"), stat.get("C")

    def _rate(s):
        return s["rate10k"] if s else 0

    def _tok(s):
        return s["tokens_sum"] if s else 0

    def _n(s):
        return s["n"] if s else 0

    # -- criteria (F2), each conjunct a self-describing operand ---------------
    # C_i is TWO conjuncts: (i-a) point margin >= 10pp, (i-b) strict non-overlap.
    c_i_a = _n(c) > 0 and _n(a) > 0 and (_rate(c) - _rate(a)) >= PP_C_OVER_A
    c_i_b = (
        _n(c) > 0
        and _n(a) > 0
        and c["wilson_lo10k"] > a["wilson_hi10k"]
    )
    c_ii = _n(a) > 0 and _tok(a) > 0 and _tok(c) <= _C["c_over_a_token_ratio_max"] * _tok(a)
    c_iii = _n(c) > 0 and _n(b) > 0 and (_rate(c) - _rate(b)) >= PP_C_OVER_B
    c_earns_six_roles = c_i_a and c_i_b and c_ii and c_iii

    # b_beats_a is TWO conjuncts: >= 5pp AND <= 2x tokens.
    b_pp = _n(b) > 0 and _n(a) > 0 and (_rate(b) - _rate(a)) >= PP_B_OVER_A
    b_tokens = (
        _n(a) > 0
        and _tok(a) > 0
        and _tok(b) <= _C["b_over_a_token_ratio_max"] * _tok(a)
    )
    b_beats_a = b_pp and b_tokens

    # kill: A >= C-5pp AND A tokens <= half C tokens (cross-multiplied).
    kill_pp = _n(a) > 0 and _n(c) > 0 and _rate(a) >= (_rate(c) - PP_KILL)
    kill_tokens = (
        _n(a) > 0
        and _n(c) > 0
        and _tok(a) * _C["kill_a_token_den"] <= _tok(c) * _C["kill_a_token_num"]
    )
    kill = kill_pp and kill_tokens

    tamper_fail = any(r["tamper_instance"] for r in observations) or any(
        r["tamper_events"] > 0 for r in observations
    )

    # -- precedence (S5): tamper -> kill -> C -> B -> default -----------------
    if tamper_fail:
        winner, reason = "none", "tamper-invalid"
    elif kill:
        winner, reason = "A", "gates-not-roles"
    elif c_earns_six_roles:
        winner, reason = "C", "six-roles-earned"
    elif b_beats_a:
        winner, reason = "B", "three-roles"
    else:
        winner, reason = "A", "default-solo"

    # -- ablation block (diagnostic only) ------------------------------------
    cdbg = stat.get(ABLATION_ARM)
    if c and cdbg and _n(c) > 0 and _n(cdbg) > 0:
        ablation = {
            "c_minus_cdbg_pp10k": _rate(c) - cdbg["rate10k"],
            "intervals_nonoverlap": (
                c["wilson_lo10k"] > cdbg["wilson_hi10k"]
                or cdbg["wilson_lo10k"] > c["wilson_hi10k"]
            ),
        }
    else:
        ablation = {"c_minus_cdbg_pp10k": 0, "intervals_nonoverlap": False}

    criteria = [
        {"id": "C_i_a", "passed": bool(c_i_a), "operands": [
            _operand("rate_c", _rate(c)), _operand("rate_a", _rate(a)),
            _operand("margin_required", PP_C_OVER_A)]},
        {"id": "C_i_b", "passed": bool(c_i_b), "operands": [
            _operand("wilson_lo_c", c["wilson_lo10k"] if c else 0),
            _operand("wilson_hi_a", a["wilson_hi10k"] if a else 0)]},
        {"id": "C_ii", "passed": bool(c_ii), "operands": [
            _operand("tokens_c", _tok(c)), _operand("tokens_a", _tok(a)),
            _operand("ratio_max", _C["c_over_a_token_ratio_max"])]},
        {"id": "C_iii", "passed": bool(c_iii), "operands": [
            _operand("rate_c", _rate(c)), _operand("rate_b", _rate(b)),
            _operand("margin_required", PP_C_OVER_B)]},
        {"id": "B_pp", "passed": bool(b_pp), "operands": [
            _operand("rate_b", _rate(b)), _operand("rate_a", _rate(a)),
            _operand("margin_required", PP_B_OVER_A)]},
        {"id": "B_tokens", "passed": bool(b_tokens), "operands": [
            _operand("tokens_b", _tok(b)), _operand("tokens_a", _tok(a)),
            _operand("ratio_max", _C["b_over_a_token_ratio_max"])]},
        {"id": "kill_pp", "passed": bool(kill_pp), "operands": [
            _operand("rate_a", _rate(a)), _operand("rate_c", _rate(c)),
            _operand("within_pp", PP_KILL)]},
        {"id": "kill_tokens", "passed": bool(kill_tokens), "operands": [
            _operand("tokens_a", _tok(a)), _operand("tokens_c", _tok(c)),
            _operand("token_num", _C["kill_a_token_num"]),
            _operand("token_den", _C["kill_a_token_den"])]},
    ]

    return {
        "wilson_z_num": Z2_NUM,
        "wilson_z_den": Z2_DEN,
        "scale": SCALE,
        "arms": arm_stats,
        "ablation": ablation,
        "criteria": criteria,
        "winner": winner,
        "decision_reason": reason,
        "c_earns_six_roles": bool(c_earns_six_roles),
        "b_beats_a": bool(b_beats_a),
        "kill_rule_triggered": bool(kill),
        "tamper_fail": bool(tamper_fail),
    }
