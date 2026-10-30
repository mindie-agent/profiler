# Qwen3.5 TP4 MC2 typed caller acceptance

Existing c4/c64/c128 captures contain **239 accepted target Body forwards** (84/79/76). Only these three sources were revisited for complete GroupedMatmul, DequantSwigluQuant, Dispatch, TopK and TensorMove ABI buckets. Combine and HCCL reuse retained whole-population evidence; no remote collection, unrelated capture scan or Body re-segmentation was performed.

Operator runtime is **3b532649a613aa82589b95204dec3d84e916114b**. This includes the fused-origin export fix, TensorMove ABI and address-only `gathered_slice` signature correction. The separate [Body receipt](../acceptance-20261030-qwen35-mc2-tp-bf71bd7d/decode-forward-qwen35-mc2-tp-replay.json) remains on its executed `bf71bd7d` runtime; it is not relabeled.

| Population | Result |
| --- | --- |
| Strict cohorts | **37/37 passed:** 35/35 <=50 us absolute-15-us; 2/2 >50 us relative-15% |
| Strict events | **105,370 / 425,370** full Body events; 12+12+13 cohorts by source |
| Added FFN TensorMove | **12,160 calls = 76 × 160**, one same-work cohort across 40 layers × 4 copies; 3.499249 us Real mean / 3.442 us P50 vs 1.312 us Sim |
| Attention TensorMove | **9,300 calls** remain separate: c64 79×60 and c128 76×60; never reassigned to FFN |
| Native references | **33 groups / 57,360 calls**, 18 fresh program sets; all reference-only |
| HCCL references | **27 groups / 28,680 calls**, 9 fresh program sets; 40 AG + 80 AR per Forward |

The typed chain is checked on every one of the 40 layers: full-M router/shared FFN → local-M/TP TopK/Dispatch → received INT8 payload plus FP32 row scales → INT32 expert-up → DequantSwigluQuant-owned INT8 payload plus FP32 row scales → BF16 expert-down. No independent expert quantization or duplicate scale transport survives.

Observed routed buffers hold four times the case-declared valid rows. Group-list contents, active routed rows and peer readiness are not captured. Those GMM/DSQ/Dispatch/Combine programs therefore remain conditional references. TopK is additionally a **partial-work boundary**: its real third FP32 output is absent from the two-output declared work. HCCL references use explicit AIV mesh/mesh-twoshot programs; the measured engine does not prove the binary template.

| Source | Role | Calls/F | Real Mean / P50 us | Sim reference us | Signed activity residual ms/F |
| --- | --- | ---: | ---: | ---: | ---: |
| c4 | expert_up | 40 | 33.760525 / 33.860500 | 16.826368 | -0.677366 |
| c4 | expert_down | 40 | 22.188960 / 22.159000 | 8.798732 | -0.535609 |
| c4 | dispatch | 40 | 17.245965 / 16.954500 | 2.242899 | -0.600123 |
| c4 | expert_act | 40 | 7.299230 / 7.286000 | 6.699758 | -0.023979 |
| c4 | topk | 40 | 3.141281 / 3.130000 | 1.312000 | -0.073171 |
| c4 | expert_combine_native | 40 | 11.677635 / 11.374500 | 3.376874 | -0.332030 |
| c64 | expert_up | 40 | 60.442310 / 60.382500 | 34.340864 | -1.044058 |
| c64 | expert_act | 40 | 54.031062 / 54.304000 | 13.391758 | -1.625572 |
| c64 | expert_down | 40 | 42.252364 / 42.921000 | 18.916057 | -0.933452 |
| c64 | dispatch | 40 | 28.795800 / 29.043500 | 7.027383 | -0.870737 |
| c64 | topk | 40 | 6.696034 / 6.681000 | 1.312000 | -0.215361 |
| c64 | expert_combine_native | 40 | 27.371084 / 28.149000 | 8.216762 | -0.766173 |
| c128 | expert_up | 40 | 61.818739 / 61.902000 | 35.127296 | -1.067658 |
| c128 | expert_act | 40 | 56.560073 / 56.844500 | 13.391758 | -1.726733 |
| c128 | expert_down | 40 | 43.377041 / 44.727500 | 20.441243 | -0.917432 |
| c128 | dispatch | 40 | 41.178457 / 41.103500 | 12.047800 | -1.165226 |
| c128 | topk | 40 | 7.244563 / 7.225500 | 1.312000 | -0.237303 |
| c128 | expert_combine_native | 40 | 43.109088 / 43.058000 | 14.633523 | -1.139023 |

These signed activity residuals are **not additive Body wall-time explanations**. No reference group earns a strict pass. The strict FFN TensorMove buckets are absent from current native-reference `groups`; their original histograms remain only under `strict_superseded_partitions`. The complete canonical receipt replaces the source’s previous canonical generation; append the two external reference receipts once, without retaining older same-population embedded references as extra coverage.

Authoritative receipts:

- [Complete canonical cohorts](canonical-with-tensor-move/body-operator-family-scoreboard.json), [1,770-check independent review](canonical-with-tensor-move/body-operator-reprice-independent-review.json).
- [Native complete-ABI references](native-references/qwen35-native-reference-scoreboard.json) and [HCCL conditional references](hccl-references/source-caller-reference-scoreboard.json), [1,795-check independent review](qwen35-caller-results-independent-review.json).
- [Targeted scan receipt](native-partitions/native-partition-receipt.json): 69,260 calls / 42 buckets, 27.06 s, 139.53 MiB peak. One earlier fresh-case export failed before event parsing; a later summary hit a zero-count TensorMove bookkeeping difference. The three successful raw passes and exact histograms were retained; neither failure caused another raw scan.
- [Fresh canonical execution commands](canonical-3b532649/execution.json). TensorMove refresh reuses those same-runtime successful costs and runs only its new physical program. Native/HCCL pricing uses zero raw reads and peaks below 166 MiB.
- Six real-ABI tests in `tests/test_qwen35_caller_contracts.py` verify INT32/down-scale ABI, producer dependencies, complete Dispatch/DSQ outputs, partial TopK and strict 160-copy versus unscored 60-copy separation.

The native report’s `metadata_completion` records adding its required `reference_boundary` field and clarifying the rendered boundary description after execution. All cost values/histograms and their original executed runtime identity remain unchanged; this completion executed no pricing or raw reads.
