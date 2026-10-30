# Kimi composed observable services

Two complete 93-layer Body predictions use the Sim-owned composed cases at
`3b72ea2d`, with the retained c32 p4k/p16k measurements. Both executions completed:

| Context | Forwards | Observed mean ms | Predicted ms | Error |
|---|---:|---:|---:|---:|
| p4k | 46 | 40.018728 | 36.968860 | -7.62% |
| p16k | 41 | 44.666193 | 42.155614 | -5.62% |

The nine declared response rules match their expected occurrences: AllGather
187, ReduceScatter 186, three matrix roles 92 each, MC2 dispatch/combine 92 each,
and grouped up/down 92 each. Every rule retains its measurement provenance and
physical domain. The p4k observations contributed calibration parameters; p16k
reuses them, but no preregistered held-out split is claimed.

`body-independent-review.json` checks 764 receipt and comparison invariants.
`rule-provenance-independent-review.json` independently checks 163 rules,
source identities, histograms and domain constraints. Both passed. These are
local predictions against existing captures, with no new device workloads.

The ordered main scoreboard selects these source declarations for c32. Per-layer
detail remains in `decode-forward-composed-replay.json`; Body accuracy does not
imply that every individual layer or operator meets its own tolerance.
