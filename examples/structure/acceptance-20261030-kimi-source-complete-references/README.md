# Kimi complete native source references

[`kimi-native-reference-scoreboard.json`](kimi-native-reference-scoreboard.json)
prices the existing complete native ABI/topology populations against Sim commit
`30dcea1e335778b3d6c6f9ba67cce3e84a5adbba` and the 12 source-complete cases.
The 618 accepted Body Forward instances and all original duration histograms
are unchanged. **408 conditional reference groups cover 344,226 calls, with no
unresolved groups and no added strict cohorts.** The 372 fresh source program
sets took 22.63 s; maximum worker RSS was 209.1 MiB. Raw profiling reads: zero.

| Native family | Calls |
| --- | ---: |
| RecurrentKda | 42,642 |
| CausalConv1d | 42,642 |
| AttnResFwd | 115,566 |
| MlaPrologV3 | 14,832 |
| FusedInferAttentionScore | 14,832 |
| MoeDistributeDispatchV3 | 56,856 |
| MoeDistributeCombineV3 | 56,856 |

The remaining underestimate ranking pools all 12 sources with their exact
618-Forward weights; it does not select the worst case or average per-case
medians. All three rows are conditional activity/service comparisons:

| Native family | Real activity ms/F | Source service ms/F | Real minus service ms/F |
| --- | ---: | ---: | ---: |
| MoeDistributeDispatchV3 | 2.985803 | 0.220336 | +2.765467 |
| MoeDistributeCombineV3 | 1.662590 | 0.379781 | +1.282808 |
| RecurrentKda | 1.110441 | 0.361095 | +0.749346 |

Next are AttnResFwd (+0.723141 ms/F) and FIA (+0.721339 ms/F). Prolog has the
opposite direction: source service exceeds measured activity by 0.141019 ms/F.
Unknown MC2 peer readiness and actual routed counts remain separate from
source protocol service; these differences do not establish a bandwidth
deficit and cannot be added as Body wall-time errors.

Compared with the previous source reference generation, all 30,876 previously
unresolved prolog/convolution calls now have a source-conditioned reference;
the additional complete FIA population contributes 14,832 calls. These are
coverage improvements, not strict accuracy passes.

FIA uses the full 31-input/2-output ABI and all 24 MLA layers. Captured queries
are BNSD and outputs are NBSD. Source contexts are 4104 or 16392, with explicit
CPU SplitCore/FD owner ranges. The CSV contains only the shape of the sequence
length array, so per-call KV length values and KV growth are unknown. Neither
the block-table width of 516 nor cache pool capacity establishes active KV
length. FIA therefore remains a conditional reference despite exact active
tensor contracts and prepared physical work.

The additional FIA evidence joins the original observation through explicit
actual ancestry, source identity, accepted Body identity, geometry and the
complete native histogram. Dispatch/Combine rows in that additional PMU pass
are not appended again. Each original native histogram is retained whole;
heterogeneous AttnRes program costs use exact captured layer counts without
inventing measured per-layer latency or P50.

Communication peer readiness, valid routed rows and expert count values remain
unknown. Prolog service is the declared decomposed semantic program set, not
proof of native fusion equivalence. The report's activity residuals compare
native elapsed activity with conditional source service; they cannot be added
to explain Body wall time or used as extra Body costs.

Reproduction uses `compare_kimi_native_partitions.py --manifest
examples/structure/acceptance-20261030-source-complete/decode-forward-kimi-cases.json
--partition-dir examples/structure/acceptance-20261030-kimi-logical96-operators/native-partitions
--additional-partition-dir examples/structure/acceptance-20261030-kimi-paged-fia-pmu
--output-dir <new-arm> --runtime-source-commit <pinned-commit>`, with the pinned
Sim checkout on `PYTHONPATH`.
