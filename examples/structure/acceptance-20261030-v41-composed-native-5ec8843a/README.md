# V4.1 composed source references, Sim 5ec8843a

The final entry is [v41-complete-reference-scoreboard.json](v41-complete-reference-scoreboard.json), with the same-name Markdown table. It contains seven retained captures, 830 complete Forward samples, 98 reference groups and 398,400 observed calls. Strict compared calls remain zero. No raw capture was rescanned.

This arm uses the parent-reviewed v41-composed-arch35-conditional source cases from Sim 5ec8843a7e1711d0333dd59f9aec4f19f4f40363. The model, physical geometry, forty layers and eight DP peers are retained. Explicit selections enable MX32 dispatch, BF16 combine, arch35 HCPre/HCPost and prepared MX32 q_b/wo_a/wo_b with AIC Fixpipe output. Routed GroupedMatmul remains its declared source program; it is not silently relabeled as the prepared projection recipe. Kimi BF16 and GLM inputs are not assigned this MX32 protocol.

The report joins two immutable cost receipts:

| Receipt | Groups | Calls | New program sets | Peak worker MiB |
| --- | ---: | ---: | ---: | ---: |
| v41-composed-native-reference-scoreboard.json | 70 | 265,600 | 63 | 143.83 |
| normalized-cohorts/v41-normalized-reference-scoreboard.json | 28 | 132,800 | 21 | 148.33 |
| Final disjoint join | 98 | 398,400 | 0 additional | 148.33 antecedent maximum |

Both receipts cover the same 830 Forward samples; the join counts those samples once. Complete histograms are preserved. The first receipt covers MC2 dispatch/combine, attention/FFN HCPre, grouped expert up/down, wo_a and the three MQSMLA ratio populations. The second adds attention/FFN HCPost, q_b and wo_b.

Evidence boundaries remain visible:

- MC2, GMM and wo_a retain full observed ABI buckets. Routing counts and group-list values remain unknown; buffer capacity is not a valid-token count.
- HCPre retains its full observed five-input/four-output ABI, while the selected public source prices three outputs. The extra [B,4] output is an explicit partial source correspondence.
- MQSMLA retains the complete source-symbol populations and layer subsets for ratios 0/1/2. This capture did not retain a full tensor ABI; the report does not invent one.
- HCPost/q_b/wo_b retain complete normalized contracts and histograms whose counts/activity exactly equal their original cohorts. These are not new full native ABI captures.
- Every selected layer has homogeneous fresh physical work. Replica 0 is only the serialization representative after full DP traffic binding; eight symmetric peers are a declared condition, not an observed per-rank binding.
- The declared_programs field may name another layer/region's physical representative when an identical program-set key shares one executed cost. Each group's own representative_target_ids, layer set and work remain authoritative. The memoized program name is not a Host occurrence.
- Native activity and predicted service overlap; their residuals must not be summed to explain Body wall time. Other previously retained rotary/cache reference populations remain separate and are not relabeled as newly priced here.

The attempted c32 strict comparison in strict-focused-c32 remains a visible failed attempt: q_b/wo_b comparison exceeded 512 MiB (597.53 MiB), and HCPost changed resource boundary. No strict result from that attempt is counted. The subsequent conditional path keeps full peer traffic but serializes only the needed replica/targets; it does not increase the memory budget.

Reproduction uses the fixed checkout first on PYTHONPATH:

    PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:/Users/maoxx241/code/profiler \
      /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
      examples/structure/replay_v41_composed_sources.py \
      --inputs examples/structure/acceptance-20261030-v41-native-references-30dcea1e/input-manifest.json \
      --case-dir /tmp/mindie-sim-cohort-wave6-20261029/examples/cases/high-concurrency-20261030/v41-composed-arch35-conditional \
      --output-dir examples/structure/acceptance-20261030-v41-composed-native-5ec8843a \
      --runtime-source-commit 5ec8843a7e1711d0333dd59f9aec4f19f4f40363

Then run compare_v41_composed_cohorts.py with --native-report pointing to the 70-group report, --output-dir pointing to normalized-cohorts and the same --runtime-source-commit. Finally run join_v41_composed_references.py with --native-report and --normalized-report pointing to those immutable receipts, and --output pointing to a new final report. The join performs no prediction. All source, declaration and execution identities are retained in JSON.
