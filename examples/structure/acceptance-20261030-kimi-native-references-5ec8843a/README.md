# Kimi retained native references, Sim 5ec8843a

The kimi-native-reference-scoreboard.json report reprices all twelve retained A5 populations using Sim 5ec8843a7e1711d0333dd59f9aec4f19f4f40363: 618 complete Forward samples, 408 groups, 344,226 observed calls and 372 freshly executed program sets. The maximum worker RSS is 196.02 MiB; elapsed reference work is 26.01 s. No raw capture was rescanned and no old prediction was substituted.

This is the same BF16 source case/geometry population used by the prior source-complete arm. MX32 dispatch is not enabled. Full retained ABI, layer subsets and duration histograms remain unchanged. The new runtime corrects paired MLA vector owners' actual-row halves and source C1/C1/C2 ordering. Only FIA predicted cost changes relative to the prior 30d source-complete receipt; the other native families retain equal service values.

Examples of conditional FIA service (us/call):

| Source | Previous prediction | 5ec prediction | Observed Mean |
| --- | ---: | ---: | ---: |
| c16 / p16k | 78.2555 | 145.4725 | 142.0950 |
| c32 / p4k | 40.0162 | 72.9743 | 74.7919 |
| c32 / p16k | 153.2655 | 289.0890 | 264.0911 |

Every row remains reference_only, with strict compared calls equal to zero. FIA retains its 31-input/2-output ABI and NBSD output view; context and sparse/state values remain declared conditions. MC2, AttnRes and other source boundaries retain their own limitations. Native activity residuals are not additive Body wall-time contributions.

The independent review checks 12,893 conditions with zero failures, including full populations, 72 AttnRes buckets, ABI, source/case/runtime identities and arithmetic. It runs no raw scan or cost execution.

The producing command uses compare_kimi_native_partitions.py with the retained acceptance-20261030-source-complete/decode-forward-kimi-cases.json, acceptance-20261030-kimi-logical96-operators/native-partitions, and additional acceptance-20261030-kimi-paged-fia-pmu partitions. Set the fixed 5ec checkout before the profiler directory in PYTHONPATH; each JSON case retains its exact input pins and execution receipt.
