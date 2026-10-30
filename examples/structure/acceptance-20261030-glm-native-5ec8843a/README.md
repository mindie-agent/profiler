# GLM native references on 5ec8843a

This is a new prediction arm using fixed Sim `5ec8843a7e1711d0333dd59f9aec4f19f4f40363` and the source-bound cases in `acceptance-20261030-runtime5ec8843a/decode-forward-glm-cases.json`. Original accepted Body windows, complete native ABI partitions and every duration histogram remain unchanged. No profiling stream was reread and no old prediction was reused.

The [18-source native report](glm-native-reference-scoreboard.md) preserves 713 selected Forwards, 45 groups and 41,096 calls: 18 accepted-state KDA populations plus the original nine A5 fused gate/up and sparse MLA populations. The 36 fresh program sets took 16.751 seconds, maximum child RSS 98.88 MiB. All 45 groups resolve as conditional references, adding zero strict cohorts.

The [packed528 report](packed528/glm-native-reference-scoreboard.md) separately prices the two fully retained A3 c32/c64 `KvQuantSparseFlashAttentionVllm` ABI groups: 96 Forwards and 1,056 calls, two fresh programs in 1.391 seconds, maximum child RSS 89.22 MiB. **These 96 Forwards are already included in the 713-source population**; only the additional operator groups/calls are complementary. No packed528 coverage is extrapolated to the other A3 sources. The c32/c64 observed Mean is 829.848/1,632.353 us, versus conditional Sim service 1,298.268/2,596.536 us.

The combined unique population is 18 sources / 713 Forwards, with 47 native groups and 42,152 calls. Source-dependent KV lengths, accepted values, routed rows, private dispatch and capture-binary equivalence retain their original explicit limitations. Activity/service residuals are not additive Body wall-time budgets.

Independent review passed 10,523 checks for the 45-group report and 802 for packed528, with zero failures, zero capture reads and zero repeated predictions. It checks the current 322-file runtime, source/Body/case pins, complete histograms, fresh physical work across every declared layer and weighted service arithmetic. The 45 original groups retain exactly the same predicted values as the prior 30d source-complete report despite being genuinely re-executed; the newer runtime alone is not claimed as an accuracy improvement.

`native-execution.json` and `packed528/native-execution.json` retain all exact commands, runtime/manifest identities and per-source child attempts. Both use the existing `replay_glm_source_complete.py --phase native`; the latter filters the source input list through `packed528-inputs.json`. The 358 canonical strict cohorts were not repriced in this focused native run.
