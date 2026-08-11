# Kata verdict scorecard

- winner: **C**
- decision: six-roles-earned
- plan stamp: sdd-roles 1.4.0 kata:a6f56755e9b0

## Arms

| arm | decisional | k/n | rate | 95% interval | tokens | mutation |
| --- | --- | --- | --- | --- | --- | --- |
| A | yes | 12/60 | 20.00% | [11.82%, 31.79%] | 600000 | 50.00% |
| B | yes | 36/60 | 60.00% | [47.36%, 71.44%] | 900000 | 70.00% |
| C | yes | 60/60 | 100.00% | [93.98%, 100.00%] | 1680000 | 90.00% |
| C-dbg | ablation | 48/60 | 80.00% | [68.21%, 88.18%] | 1560000 | 80.00% |

## Criteria

| id | passed | operands |
| --- | --- | --- |
| C_i_a | yes | rate_c=10000, rate_a=2000, margin_required=1000 |
| C_i_b | yes | wilson_lo_c=9398, wilson_hi_a=3179 |
| C_ii | yes | tokens_c=1680000, tokens_a=600000, ratio_max=3 |
| C_iii | yes | rate_c=10000, rate_b=6000, margin_required=500 |
| B_pp | yes | rate_b=6000, rate_a=2000, margin_required=500 |
| B_tokens | yes | tokens_b=900000, tokens_a=600000, ratio_max=2 |
| kill_pp | no | rate_a=2000, rate_c=10000, within_pp=500 |
| kill_tokens | yes | tokens_a=600000, tokens_c=1680000, token_num=1, token_den=2 |

## Ablation (diagnostic only)

- C minus C-dbg: 20.00%
- intervals non-overlapping: yes

## Decision flags

- C earns six roles: yes
- B beats A: yes
- kill-rule triggered: no
- tamper-fail: no
