# Paged FIA and recurrent GDN local coverage

Existing A3/A5 captures were streamed read-only once per capture. This acceptance adds explicit caller workloads; it does not infer phase, verify/draft identity, layer or step from a tensor shape. All new mapped events remain ambiguous, with zero bound events.

| Capture | Native type | Raw events | Baseline cohort events | New disjoint cohort events | Combined covered events | Remaining |
|---|---|---:|---:|---:|---:|---:|
| a3_qwen35 | FusedInferAttentionScore | 737 | 11 | 726 | 737 | 0 |
| a3_qwen35 | RecurrentGatedDeltaRule | 1950 | 0 | 1950 | 1950 | 0 |
| a3_qwen35 | ChunkGatedDeltaRuleFwd | 60 | 0 | 0 | 0 | 60 |
| a3_qwen36 | FusedInferAttentionScore | 323 | 17 | 306 | 323 | 0 |
| a3_qwen36 | RecurrentGatedDeltaRule | 720 | 0 | 720 | 720 | 0 |
| a3_qwen36 | ChunkGatedDeltaRuleFwd | 96 | 0 | 0 | 0 | 96 |
| a5_qwen38 | FusedInferAttentionScore | 228 | 17 | 211 | 228 | 0 |
| a5_qwen38 | RecurrentGatedDeltaRule | 528 | 0 | 528 | 528 | 0 |
| a5_qwen38 | ChunkGatedDeltaRuleFwd | 0 | 0 | 0 | 0 | 0 |

Baseline is the recorded default prefill declaration. New counts combine only different native tensor contracts; dense baseline and paged alternatives remain distinct. The final three-capture total is 1,288 FIA + 3,198 recurrent events with tensor cohorts, while 156 chunk events retain a declaration-boundary gap.

## Conditional per-call comparisons

Contexts below are caller assumptions. The reports completed pricing but do not establish captured context values. Accuracy policy: observed mean <=50 us uses absolute error <=15 us; larger calls use relative error <=15%.

| Capture | Phase / q / context | Native type | Calls | Instances | Observed mean us | P50 us | Predicted us | Signed diff us | Relative error | Accuracy |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| a3_qwen35 | decode / 2 / 8192 | RecurrentGatedDeltaRule | 1950 | 30 | 16.177 | 16.020 | 5.669 | -10.508 | -64.96% | pass |
| a3_qwen35 | decode / 2 / 8192 | FusedInferAttentionScore | 715 | 10 | 53.574 | 53.161 | 6.999 | -46.574 | -86.94% | fail |
| a3_qwen35 | prefill / 8192 / 0 | FusedInferAttentionScore | 11 | 10 | 2476.504 | 2478.569 | 508.463 | -1968.041 | -79.47% | fail |
| a3_qwen36 | decode / 1 / 8192 | FusedInferAttentionScore | 34 | 16 | 54.717 | 54.768 | 6.996 | -47.721 | -87.21% | fail |
| a3_qwen36 | decode / 4 / 8192 | RecurrentGatedDeltaRule | 720 | 48 | 25.715 | 25.639 | 12.006 | -13.709 | -53.31% | pass |
| a3_qwen36 | decode / 4 / 8192 | FusedInferAttentionScore | 255 | 16 | 58.192 | 58.199 | 7.014 | -51.178 | -87.95% | fail |
| a3_qwen36 | prefill / 8192 / 0 | FusedInferAttentionScore | 17 | 16 | 3678.352 | 3674.507 | 762.694 | -2915.659 | -79.27% | fail |
| a5_qwen38 | decode / 1 / 16384 | FusedInferAttentionScore | 24 | 16 | 135.013 | 134.959 | 16.784 | -118.229 | -87.57% | fail |
| a5_qwen38 | decode / 4 / 16384 | RecurrentGatedDeltaRule | 528 | 48 | 10.658 | 10.639 | 9.653 | -1.005 | -9.43% | pass |
| a5_qwen38 | decode / 4 / 16384 | FusedInferAttentionScore | 187 | 16 | 143.916 | 143.886 | 16.806 | -127.110 | -88.32% | fail |

New comparison statuses: {'compared': 10}; reference-only: 0; prediction failures: 0. Accuracy: {'passed': 3, 'failed': 7}. These are conditional comparisons, not evidence that the declared context or complete model execution matches the capture.

## Remaining boundary

ChunkGatedDeltaRuleFwd 156 A3 events now expose a validated legacy 9-input/4-output full native ABI, but generic sim TND/BF16-state chunk wrapper does not establish the captured BHTD/FP32-state native boundary. Its complete contract remains unmatched; no member costs or layer identities are invented.

The paged FIA contract excludes cache capacity and table/sequence values while retaining block size, packed row width and batch count. A separate rank-4 cache probe remains full native ABI; its storage is not flattened by assumption. Recurrent tests reject wrong key/output/state/gate/dtype metadata and unsupported declared FP16 operands.

## Evidence and budget

Runtime: isolated sim `d6eccd57` on base `239f443c`, with frontend `b355d9f6` cherry-picked as `a9a1efce`. Profiler contract edits are recorded by file SHA in the JSON. Main sim checkout and index were not changed.

| Capture | Source SHA-256 | Elapsed seconds | Peak MiB |
|---|---|---:|---:|
| a3_qwen35 | `2c2fb28ab36674f8eaef52042e1350a949a972225b4d4c5f52da1fe27fa58b53` | 4.432 | 83.86 |
| a3_qwen36 | `797260bd9ea48a7fb75831c397a6c0716be11233f4df953d299e5bdf99084d7f` | 2.636 | 74.70 |
| a5_qwen38 | `ec7fbcff6138d06fd7d0ed20497d8d4af2f78a179372db976090d4206a3d17ca` | 1.553 | 66.11 |

Focused tests: profiler 49 passed; isolated sim 74 passed. JSON retains source paths, full contracts/scopes, graph IDs, caller geometries, baseline artifact hashes and per-cohort metrics. Temporary detailed mappings/comparisons are `/tmp/P2-<capture>-<phase>-q<count>.*.json`.
