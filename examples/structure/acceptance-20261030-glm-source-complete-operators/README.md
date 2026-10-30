# GLM Flash complete-source replay

The same 18 retained Flash sources and primary Forward geometry were replayed against Sim `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba` (runtime `9902629b`). Ten A5 sources use reviewed `glm-source-complete/` cases; eight A3 sources use `glm-source-accepted-26/`. All original observations and conditional operator contexts are preserved. The eight other full-GLM sources are outside this operator campaign; their Body cases retain their original architecture and cache declarations.

The [complete-family scoreboard](body-operator-family-scoreboard.md) includes 713 selected Forwards and 376,073 strictly compared calls: **337/358 cohorts pass**, comprising **328/345 cohorts with measured Mean ≤50 us** under the 15 us absolute-error rule and **9/13 larger cohorts** under the 15% rule. These are cohort counts, not independent layers or captures. All source-family populations, including unscored events, remain present. The 344 fresh program executions took 231.212 seconds, maximum child RSS 109.67 MiB. No raw capture was reread during repricing and no previous prediction was reused.

The [native-reference table](glm-native-reference-scoreboard.md) preserves 45 whole ABI partitions and 41,096 calls, separately from strict accuracy:

- Accepted-state KDA: all 18 sources, 24,242 calls; eleven inputs/three outputs, every retained KDA layer checked. Symbolic accepted counts choose the initial state slot; all current queries execute. Actual accepted values, slots, active views and the in-kernel sigmoid flag remain unknown.
- Fused MXFP8 gate/up/SwiGLU/quant: the original nine A5 sources, 13,356 calls, exactly 42 per Forward. Full six-input/two-output ABI validates three semantic members; the source-complete declaration prices only the one selected fusion resource. Down projection stays external. Group-list values, actual routed rows, private binary and L1 K remain conditional.
- SparseFlashMla: the original nine A5 sources, 3,498 calls. Full-batch reference preserves dynamic sparse-length and private-dispatch uncertainty.

The 36 fresh native program sets took 13.186 seconds, maximum child RSS 128.02 MiB. All 45 groups resolved as conditional references, adding **zero strict cohorts**. A5 c96 and the eight A3 additions have KDA partitions only; missing fused-up or sparse families are not extrapolated. Original per-group Mean/P50 values and layer sets remain intact.

Independent review passed 16,374 checks for the complete-family receipts, 5,769 checks for the native references and 5,330 checks for the residual ledger, with no failures. These audits check retained populations, parsed declarations, fresh physical work, conditional source boundaries and arithmetic without rereading capture streams or rerunning costs. The residual audit also keeps the 54 pre-existing unfused-subgraph references separate from 45 full-native references and 358 direct cohorts. The fused-resource selector has three real-capture regressions, including an explicit failure when obsolete semantic members are absent from the fresh resource graph.

[Per-source remaining residuals](glm-source-complete-residuals.md) rank failing direct cohorts and conditional native references separately. For example, c32/c64 fused-up source service is 165.20/168.48 us versus roughly 208/211 us; SparseFlashMla remains overpredicted by 1.558/3.323 ms per Forward. The first is a conditional source correspondence and the second retains sparse-length assumptions. Neither residual can be added directly to explain Body wall time: device activities overlap and may contain communication wait.

Reproduction uses the fixed source checkout before the profiler package, the existing real observations, and the source-complete Body manifest:

```sh
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:/Users/maoxx241/code/profiler \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/replay_glm_source_complete.py \
  --inputs examples/structure/acceptance-20261030-glm-source-accepted-26/operator-reprice-inputs.json \
  --body-manifest examples/structure/acceptance-20261030-source-complete/decode-forward-glm-cases.json \
  --native-dir examples/structure/acceptance-20261030-glm-native-partitions \
  --native-dir examples/structure/acceptance-20261030-glm-source-accepted-26/additional-native-partitions \
  --output-dir /tmp/glm-source-complete-replay \
  --runtime-source-commit 30dcea1e335778b3d6c6f9ba67cce3e84a5adbba \
  --phase families
```

Run again with `--phase native` after the family phase, then run `summarize_glm_source_complete.py` on that output directory. Each phase uses one source subprocess at a time. Retained input identities, fresh resource work, executable runtime hashes, per-program attempts and original population histograms remain in the referenced receipts. The fixed checkout must resolve to the recorded commit; a newer checkout is a distinct prediction arm.
