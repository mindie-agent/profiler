# V4.1 A5 native operator families inside complete Decode bodies

Six retained captures (client c1/c4/c8/c16/c32/c64) contribute **757 complete 40-layer body forwards**. Measured execution batches are 1/1/1/2/4/8. Sim runtime is `09811dad`; context 2048 is the independently profiled representative prompt, not the case workload placeholder 1. All six declarations parse as FP8 ordinary weights and FP4 routed experts, without an outer quantization override.

The strict scoreboard contains **108/108 passing cohorts, all in the <=50 us / absolute 15 us tier**. This does not establish accuracy for the heavy expert programs. There are separately **54 conditional source-role groups** for attention, expert matrices, HcPre, Dispatch and Combine. HcPost already has a strict tensor contract and is not counted again as a reference.

The independent review passes 4,842 arithmetic/identity/population checks, including the exact 39-layer steady call histograms. Capture extraction stayed below 418 MiB. `extraction-history.json` preserves the earlier placeholder-context diagnostic, the justified c1 reread and the interrupted partial c8 scan; those are not presented as one successful pass.

At B8/c64, expert up/down measured kernel activity totals 14.50 ms/forward versus 10.45 ms/forward for the declared program references. Their captured buffer capacities remain distinct from unknown valid routed rows, and Sim explicitly reports partial native FP4 execution coverage. At B1, Dispatch changes from 45.33 us mean / 33.64 us P50 (c1) to 29.45 / 16.84 us (c8), despite the same 15.36 us reference; elapsed communication cannot calibrate bandwidth without peer activity evidence. HcPre remains a partial base-program reference with an unresolved pre-mix branch.

These are per-kernel activity comparisons, not additive causal explanations of body wall-clock time. Every referenced program is existing model work; no reference grants extra budget.

Artifacts: `body-operator-family-scoreboard.json`, `body-operator-family-scoreboard.md`, `body-operator-family-independent-review.json`, `steady-layer-pooled.json`.
