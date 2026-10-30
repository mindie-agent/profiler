# GLM source mechanisms: retained ABI applicability

This arm reuses complete accepted Decode populations. It does not change Body endpoints, infer layers from operator names, or treat activity sums as Body wall-clock contributions. Explicit source-program costs will be recorded separately from the earlier `c2261d63` generic references.

## A3 packed-cache sparse MLA

Two targeted passes reuse the previously accepted c32/c64 Forward windows and preserve each family's complete integer duration histogram exactly. They add no captures or new Body samples.

| Source | Geometry | Complete Forwards | Native calls | Real Mean / P50 us | Full ABI groups |
| --- | --- | ---: | ---: | ---: | ---: |
| a3_glm53flash_tp16_aclgraph_c32 | B32, q6 | 49 | 539 | 829.848284 / 829.977 | 1 |
| a3_glm53flash_tp16_aclgraph_c64 | B64, q6 | 47 | 517 | 1632.353474 / 1632.673 | 1 |

Both groups have `KvQuantSparseFlashAttentionVllm` query/output `[B*6,4,512]` BF16, K/V descriptors `[38820,128,1,528]` INT8, empty rope inputs, indices `[B*6,1,2051]`, and table `[B,1025]`. Query/cache length descriptors are both `[B]` INT32. All 11 aligned MLA layers are represented. The [partition receipt](native-partition-receipt.json) records 96 Forwards, 1,056 calls, 15.941 seconds and 194.77 MiB peak RSS; source/model/extraction identities remain in each complete partition artifact.

The applicable new program is explicitly `indexed_attention_packed_int8` with a declared scratch policy. Its 528-byte row assumes 512 INT8 payload values plus four FP32 scales, with aliased K/V reads. Descriptors establish the packed row width, but do not establish scale offsets/values, physical address aliasing, active sparse indices, valid sequence lengths, or private binary dispatch. The retained public arch22 implementation requires 672-byte rows and rope64; this capture must never be called an exact match to that kernel. The new program is an analytic rope0 adaptation and remains a conditional reference.

`glm_source_mechanism_references.py` verifies all retained input/output slots and matches the complete declared sequence set. If any aligned layer differs, or a sequence is absent, it rejects the entire original histogram. Tests use the actual c32 bucket and cover both a 672-byte ABI mismatch and a missing declared sequence.

## A5 MXFP8 grouped matrix

Priority source cases are `glm53flash-a5-tp8-c1`, `a5_glm53flash_tp8_c32_p4k`, and `a5_glm53flash_tp8_c64_p4k`. Their original declarations are under Sim `examples/cases/high-concurrency-20261030/{new17,glm-flash-ws9}/`; original full observations and mappings are retained in the existing profiler campaigns.

The explicit `ascend_mxfp8_grouped_nz` program currently covers grouped **expert_down**, FP8 operands with E8M0 scales and direct BF16 output. Its K=256 path can be compared by safely rebuilding the already-established expert_down cohorts against the new explicit declaration. The source uses integer per-expert row counts; forced-balanced rows are a declared scenario, since captured group-list values are unavailable.

It does not directly implement `GroupedMatmulSwigluQuantV2`, whose actual up-projection, activation and quantization output is FP8. The retained fused ABI has H4096/I256, 288 experts and packed NZ weights `[288,16,256,16,32]`; c1/c32/c64 output buffer capacities are respectively 32/1024/2048 routed rows. Capacity is not evidence of active routed rows. Existing [GLM9 native references](../acceptance-20261030-glm-native-references-c2261d63/README.md) keep the complete gate-up/activation/quantization program set and its condition explicit.

## Execution boundary

No source-mechanism predictions are claimed by this preparation receipt. New costs require an explicit, independently identified source-case variant and a fixed runtime. The native reference driver accepts `--case` while preserving `original_case_identity`; it checks that model, hardware and parallel declarations stay equal, then exports fresh contracts/work and actually executes the selected programs. `--source-mechanisms` enables the packed528 selector and requires the explicit analytic recipe. Existing strict cohort repricing uses `reprice_body_operator_families.py --role expert_down` with the new case, preserving original observations and safely rebuilding the declaration.

KDA remains separate: the retained native ABI has a nonempty accepted-token tensor. The current arch35 source adapter rejects that state-slot branch. Neither the accepted-token input nor flat active strides may be fabricated to force an implementation match.
