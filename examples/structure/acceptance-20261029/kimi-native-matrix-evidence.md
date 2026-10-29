# Kimi native matrix and SiTU contract evidence

This records the 2026-10-29 contract extension against retained A5 capture rows.
It is a historical-source replay, not a new hardware run. Complete tensor or
semantic boundaries, declared physical programs and scored timing comparisons
remain distinct.

## Source rows and independent declarations

The additional [fixture](../../../tests/fixtures/fusion_contracts/kimi_matrix_branches.csv)
retains original CSV lines 53, 136, 163, 164, 165, 167, 174, 238 and 240 without
cell changes. Its [provenance](../../../tests/fixtures/fusion_contracts/kimi_matrix_branches.provenance.json)
records the archive, member, full-source and fixture hashes. It is also registered
in the shared fusion fixture registry under `a5_kimi_k3`; another fixture from
that same capture does not add an independent capture.

| Native interface | Verified descriptor branch | Contract boundary |
| --- | --- | --- |
| `GroupedMatmulSituQuant` | Five inputs/two outputs; stacked MXFP4 `FRACTAL_NZ_C0_16` weights; FP8 E4M3 input/output and paired E8M0 scales. Original lines 163/238 have 28 experts, K=3584, output width=3072, M=2875/3286. | Expert-bank count, channels and precision. Actual routed M, group-list values, beta, linear-beta and dispatch are excluded from equality. |
| `GroupedMatmul` MXFP4 down | Original lines 165/240 retain weight `[28,96,224,16,32]`, E8M0 microscales in `antiquant_scale`, input K=3072 and output N=3584. | Grouped matrix contract retains bank count and captured M. It does not substitute expected routing moments for captured rows. |
| `SituMxQuant` | Original line 164 retains BF16 `[8192,1536]` to FP8 `[8192,768]` and E8M0 `[8192,12,2]`. | Existing SiTU/quant contract; independent activation parameters remain declared conditions. |
| `QuantBatchMatmulV4` | Original line 167 retains FP8 `[8192,768]`, packed FP4 weight and both scale tensors, producing BF16 `[8192,7168]`. | Existing strict V4 matrix projection; packed scale and weight axes are validated before projection. |
| `GroupedMatmul` single bank | Original lines 53/136/174 contain an explicit one-element group-list tensor and one weight bank. | Remains `grouped_matrix`, including bank=1. It is not silently converted into a dense matrix contract. |

The GroupedMatmulSituQuant independent implementation is the small retained
`gmmsituquant-latest-0916/gmmsituquant-latest-overlay.zip` delivery, based on
vllm-ascend `75f52c1d7df8df8548d854a01b64935727a70e88`. The op definition
`csrc/moe/grouped_matmul_situ_quant/op_host/grouped_matmul_situ_quant_def.cpp:9`
declares the native slots; `grouped_matmul_situ_quant_torch_adpt.h:148` validates
the stacked MX A8W4 interface and calls the native operation at line 181.
The fixture provenance contains archive/member hashes. This establishes
independent source semantics, not the identity of the historical binary.

The MXFP4 down scale slot is independently explained by
`/Users/maoxx241/code/vllm-ascend/vllm_ascend/device/device_op.py:1369`:
the `W4A8MXFP` branch clears ordinary scale and passes weight microscales through
`antiquant_scale`; the grouped call retains the caller's group list. The file
hash and revision are in the same fixture provenance.

The current-checkpoint conditional case is
`/Users/maoxx241/code/sim-rewrite-20261027/examples/cases/kimi-k3-a5-current-checkpoint-conditional.json`.
Its category precision declarations come from independently read current
checkpoint metadata, not profiler tensor dtypes. The historical config hash
matches, but the historical capture did not preserve the quant-description hash.
The case therefore remains explicitly conditional on the current checkpoint.

## Physical-cost limits

The source-backed grouped boundary contains gate/up GEMM, SiTU and its output
quantization; routing, input quantization, down GEMM and combine remain external.
Selecting that native boundary produces one physical launch while preserving
the declared member work and workspaces.

Current generic MXFP4 programs charge packed weight payload and scale traffic,
then use BF16 matrix service with assumed fused dequantization. They do not yet
provide native FP8/FP4 matrix service or an explicit operand-conversion and
microscale execution program. Both standalone MXFP4 matrices and the grouped
SiTU boundary expose `prediction_coverage.kind=partial_program`, reason
`mxfp4_native_execution_unmodeled`. A matching tensor cohort can have a positive
reference cost, but the comparison consumer emits `reference_only` and no timing
error score. Complete semantic coverage does not remove this physical gap.

Actual per-expert row values also remain unobserved. The GroupedMatmulSituQuant
channel-domain contract can match both retained routed-M branches while pricing
the independently declared expected routing workload. That does not establish
equal observed FLOPs, active weight reads, expert histograms or layer instances.

## Single-bank GMM remains a configuration gap

The retained independent linear wrapper
`/Users/maoxx241/code/vllm-ascend/vllm_ascend/quantization/methods/w8a8_mxfp8.py:105`
calls `npu_quant_matmul`; bounded inspection of the local Kimi and v4.1
wrappers did not locate a linear GMM call constructing `group_list=[M]`.
The file is at revision `175ef4d49c2072f9233619636f0309f4f88b4e2c`, SHA-256
`5b9ab8ce4b7bcf86681ea8cb7b54aff667d8b11d5cdc0842b062c7f3e3ade9ae`.
This negative search result is not proof that no historical implementation
exists; it means no such source selection is currently justified.

The independent CANN GMM API documentation is stricter than a shape-only alias:
`/Users/maoxx241/code/refs/ops-transformer/gmm/grouped_matmul/docs/aclnnGroupedMatmulV5.md:321`
allows cumulative group rows no greater than allocated input M, and line 338
retains that rule for a single tensor/weight bank. Line 616 says rows outside
the group-list range are not updated. The local documentation revision is
`a3925fd49cd256ad478d2faf983bf2961b8ae2c8`, file SHA-256
`ec3f5187b80a5cbd0d47ee48e314e7ffb12e5dee9654fc2bc840f76db938569d`.

Consequently bank=1 and equal allocated input/output M cannot prove dense work
over all rows. A matching historical wrapper or independently selected runtime
implementation with explicit group-list semantics is still required. Neither
capture duration nor an observed dtype supplies that missing declaration.

## Focused verification

The affected profiler matrix/fusion tests and sim matrix/SiTU tests passed:
63 tests in 14.99 seconds using the sim environment's CPython 3.13.12. The
retained-row integration test generates an independent one-block declaration,
selects the grouped native launch, maps original GroupedMatmulSituQuant and V4
events, and confirms positive reference costs with no error scores. No NPU work
or complete raw-capture rescan was performed for this contract extension.

## Complete replay audit: four Kimi declarations

The subsequent 2026-10-29 complete replay audit checked the four
`fusion-cohort-a5_kimi_k3*-reference` artifact sets in this directory. These
are four independent declarations applied to **one historical capture**, not
four captures or a new hardware run. Each contains 286,988 positive-duration
events with the same source hash, size and bounds:

- Source SHA-256:
  `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648`.
- CSV size: 110,031,770 bytes.
- Capture bounds: `[1792733126717667087, 1792733133630354040]` ns.

| Declaration suffix | All scored events | All reference-only events |
| --- | ---: | ---: |
| `a5_kimi_k3-reference` | 439 | 0 |
| `a5_kimi_k3_decode-reference` | 10,703 | 0 |
| `a5_kimi_k3_checkpoint-reference` | 2,023 | 8,002 |
| `a5_kimi_k3_decode_checkpoint-reference` | 43,469 | 22,859 |

The five requested head types have the following event counts. Each result
cell is `scored / reference-only`; zeroes do not imply a missing parser.
The denominator is the full capture for every declaration.

| Native type | Capture events | Base prefill | Base decode | Current-checkpoint prefill | Current-checkpoint decode |
| --- | ---: | ---: | ---: | ---: | ---: |
| `MatMulV3` | 21,819 | 163 / 0 | 8,838 / 0 | 163 / 0 | 8,838 / 0 |
| `GroupedMatmul` | 27,248 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| `GroupedMatmulSituQuant` | 7,266 | 0 / 0 | 0 / 0 | 0 / 7,266 | 0 / 7,266 |
| `SituMxQuant` | 7,266 | 0 / 0 | 0 / 0 | 368 / 0 | 6,898 / 0 |
| `QuantBatchMatmulV4` | 14,531 | 0 / 0 | 0 / 0 | 0 / 736 | 0 / 13,795 |

The current-checkpoint declarations produce cohorts for some branches of four
head types. `GroupedMatmul` remains unresolved for all 27,248 events.
Only `MatMulV3` and `SituMxQuant` have scored head-type events. V4 and grouped
SiTU cohorts retain `mxfp4_native_execution_unmodeled`, positive reference
costs and `comparison: null`. Matching those parameter domains does not
complete their physical programs.

All five types have an available observed contract for every retained event.
For current-checkpoint prefill, unmatched head-type counts are MatMulV3
21,656, SituMxQuant 6,898 and V4 13,795, besides all GroupedMatmul events.
For current-checkpoint decode they are MatMulV3 12,981, SituMxQuant 368 and
V4 736, besides all GroupedMatmul events. Decode MatMulV3 separates 6,083
geometry/scope mismatches from 6,898 dtype/quantization mismatches. These
are full-window comparisons against a declared phase, not evidence assigning
each captured event to a measured prefill/decode step.

For each artifact set, the audit verified recorded hashes and byte sizes for
case, mapping, comparison input, comparison and family reports; graph IDs
agree across summary, mapping, comparison and families. Family event counts
sum to 286,988. Per-family event/cohort/exclusion and scored/unscored equations
hold, and cohort statuses weighted by observed event count agree with family
scored/reference totals. Both current-checkpoint graph IDs also matched a
fresh export under CPython 3.13.12.

The same 7,266 grouped SiTU observations appear in both checkpoint declarations.
Do not add coverage across these tables or infer a deduplicated union from
aggregate reports. Layer occurrences remain ambiguous; unknown step counts
and symmetric DP folding do not multiply observed events. Activity sums
include overlapping events and are not end-to-end elapsed time.

## Remaining GroupedMatmul denominator

A single additional streaming pass over the complete CSV classified all
27,248 GroupedMatmul events into 367 exact contracts. Every row produced an
observed contract. Both checkpoint mappings report
`declared_geometry_or_scope_mismatch` and `no_tensor_candidates` for this
entire type; the following partition explains that aggregate diagnostic.

| Expert banks | K to N | Precision, input/weight/output | Events | Captured allocated M |
| --- | --- | --- | ---: | --- |
| 1 | 7168 to 4608 | FP8 E4M3 / FP8 E4M3 / BF16 | 5,451 | 1: 5,175 events; 8192: 276 events |
| 1 | 7168 to 3584 | FP8 E4M3 / FP8 E4M3 / BF16 | 7,266 | 1: 6,898 events; 1024: 368 events |
| 1 | 3584 to 7168 | FP8 E4M3 / FP8 E4M3 / BF16 | 7,265 | 1: 6,897 events; 1024: 368 events |
| 28 | 3072 to 3584 | FP8 E4M3 / MXFP4 / BF16 | 7,266 | 361 distinct values, 453 through 14819; M=512: 6,898 events; other values: 368 events |

The **19,982 single-bank events** lack an independently justified native
linear-GMM wrapper and group-list semantics. Representative original lines
53, 136 and 174 are retained in the fixture. Their descriptors include a
one-element INT64 group-list tensor, but no tensor values. The independent
wrapper and CANN evidence described earlier therefore still prohibit
flattening these into dense matrix contracts. Similar channel dimensions
alone do not establish the kernel's model role or full active row range.

The **7,266 28-bank MXFP4 down events** already agree with the checkpoint
declaration on bank count, K/N and operand/output precisions. Original lines
165 and 240 retain M=2875 and M=3286, respectively. The prefill declaration
instead has M=16384 and activation scales `[16384,48,2]`; decode has M=2
and scales `[2,48,2]`. None of the captured M values equal either declaration.
The independent probability-routing model uses 896 experts, top-k 16,
DP4 and EP32: 8192 declared tokens per DP replica give expected local rows
`8192 * 4 * 16 / 32 = 16384`; one decode token gives `1 * 4 * 16 / 32 = 2`.
This expectation is declared by `RoutingPolicy.local` and the case, not
measured from the capture.

The capture has no group-list values, per-expert histogram or active-versus-
padded row accounting. In particular M=512 describes the allocated tensor;
it does not prove 512 active routed rows. Resolving this branch requires an
independent runtime routing/padding declaration or retained routing values.
It is not a missing dtype or missing shape, and the observed tensor M must
not be used to backfill the model case. Even a justified geometry match would
retain the separate MXFP4 physical-program limitation.

The streaming classification took 8.44 seconds and peaked at 36,601,856 bytes
(about 34.9 MiB). The subsequent diagnostic experiment exported both full
graphs in the same process; its total peak reached 637,075,456 bytes
(about 607.6 MiB), exceeding the 512 MiB routine-analysis target. That
experiment is **not** a passing memory-budget acceptance. A single-graph
process lifecycle is required for subsequent export validation; this
resource correction does not justify changing graph geometry or comparison
results. This audit changed no runtime, case or raw capture.
