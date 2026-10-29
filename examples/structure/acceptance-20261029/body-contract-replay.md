# Attention, cache and fused body contracts

This follow-up replays eight complete retained CSV windows from existing A3/A5
model runs: **668,835 positive-duration events**. It starts no new device work.
The independent sim cases supply declarations; event order, duration and observed
shapes never populate those declarations.

The [source inventory](model-evidence-inventory.md) distinguishes full model
captures, primitive probes, serving-only metrics and unresolved hardware identity.
Full capture here means the complete retained file for one rank/window, not
every rank or an entire application's lifetime.

## Implemented comparison boundaries

| Observed operator | Shared sim declaration | Comparison boundary |
| --- | --- | --- |
| Dense `FusedInferAttentionScore` | Existing GQA attention nodes, fresh prefill with CP/PCP=1 | Q/K/V and primary output shapes/dtypes/formats; no masks, sequence values, scalar flags or paged assumptions |
| `ScatterPaKvCache` | Existing GQA cache-store nodes | Active K/V element counts/dtypes and slot count; no guessed head factorization, layout, capacity, block size or slot values |
| `ReshapeAndCacheNdKernel` | Native/active descriptor support | Preserves 3D K/V and index dtype; no implicit alias to Scatter |
| `SparseFlashAttention` | Existing indexed latent attention in GLM | Q/Q-rope/O plus K/V/rope cache head dimensions; no capacity, index contents or dispatch proof |
| `SparseAttnSharedkv` | Existing shared-KV attention in DeepSeek V4 | Q/O, cache head dimensions and compressed-cache presence; compression ratio remains outside comparison |
| `_layer_norm_fwd_1pass_kernel_npu` | Existing GDN output norm-gate | Ordered x/weight/gate and output/statistics descriptors; no inferred epsilon or gate flags |
| `layer_norm_gated_fwd_kernel` | Existing KDA output norm-gate in Kimi | Source-verified active rows and weight/primary-output descriptors; not the Qwen native ABI, auxiliary statistics unknown |
| `GemmaRmsNorm` | Qwen model-class normalization semantics | Preserves weight-offset semantics and native identity, not ordinary RMS |

Other verified native records include paged FIA, `MlaPrologV3`,
`LightningIndexer`, `KvRmsNormRopeCache`, `PagedCacheLoadNdKernel`,
`RINGMLAPrefillBF16Kernel`, `ScatterNdUpdateSk` and `AddRmsNormBias`.
Having a normalized native record does not imply a matching model node.
Empty shapes with a valid dtype/layout are preserved as recorded; without
operator-specific validation they do not establish that the actual tensor is scalar.

`observed_contract_scope` states what is compared. Active projections also
retain `observed_native_tensor_abi` in sampled mappings. Native type identity
remains part of every new comparison tuple. A bound occurrence only proves the
declared structural association within this scope, not numerical equivalence or
equality of all execution parameters.

## Complete-file results

The target column covers the attention/cache/fused types added in this follow-up,
not all operations belonging to a model body. Other matrix/GDN/quantization
candidates remain separately counted in each JSON report.

| Full retained capture | Events | Target-type events | Usable target contracts | Target events with structure candidates |
| --- | ---: | ---: | ---: | ---: |
| [A3 Qwen3.5](body-a3_qwen35.json), declared prefill chunk 8192 | 121,802 | 9,983 | 7,296 | 101 |
| [A3 Qwen3.6](body-a3_qwen36.json), declared prefill chunk 8192 | 40,628 | 4,233 | 3,190 | 167 |
| [A5 Qwen3.8](body-a5_qwen38.json), declared prefill 16384 | 22,486 | 1,260 | 504 | 82 |
| [A3 GLM53 prefill](body-a3_glm53_prefill.json), declared 4096 | 2,392 | 351 | 198 | 78 |
| [A3 GLM53 decode](body-a3_glm53_decode.json), declared active token 1 | 166,204 | 25,974 | 14,652 | 5,772 |
| [A3 DeepSeek V4 Flash](body-a3_v4f.json), declared prefill 4096 | 4,064 | 171 | 171 | 44 |
| [A3 DeepSeek V4 Pro](body-a3_v4pro.json), declared prefill chunk 1024 | 24,271 | 980 | 980 | 244 |
| [A5 Kimi K3](body-a5_kimi_k3.json), declared prefill chunk 8192 | 286,988 | 9,311 | 4,136 | 276 |
| Total | 668,835 | 52,263 | 31,127 | 6,764 |

All 6,764 target matches remain **ambiguous repeated-node candidates**. None is
automatically bound to a layer without occurrence evidence. The full sources
include mixed phases/chunks/branches; a single declared geometry is a comparison
hypothesis, not an automatic phase assignment. GLM decode has an independently
recorded capture gate, but no per-event token index or exact context value.

The final A5 Qwen3.8 whole-file result is 1,144 ambiguous, 37 candidate and
21,305 unmapped. Attention/cache/gated norm add 82 matched events. Separately,
the independent Qwen model declaration now preserves Gemma weight-shift
semantics: 10 ordinary `RmsNorm` and 54 `AddRmsNorm` matches from the former
generic declaration are no longer justified. They require the actual native
lowering/weight-transformation declaration. The net increase is therefore 18
candidate events, not 82; matching count is not the correctness objective.
The earlier [A5 report](a5-full-prefill-declaration.json) remains historical evidence
with its own graph ID, not the current result.

The original 38-row slice was also rerun against the current declaration:
[23 unmapped, 14 ambiguous, 1 candidate](a5-fixture-current-body-contracts.json).
The extra unmapped event is the former unique ordinary-RMS candidate, now
excluded by the model's Gemma semantics. The original 14 occurrence ambiguities
remain; no missing metadata was filled from neighboring events.

Each report includes source/case hashes, graph ID, complete operator status and
diagnostic counts, and up to 64 body examples selected by native type, comparison
family, candidate count and missing reason. Examples are remapped separately
and never added to full-window denominators. Final runs took 0.39-22.51 seconds,
with a maximum RSS of about 221 MiB. Raw events are streamed; interval accounting
is bounded by the explicit event cap, not constant-memory or unbounded history.

## Remaining evidence and implementation gaps

- Qwen split-QKV+norm+RoPE exports expose only one output while the referenced
  wrapper returns Q/K/V/gate. Q and gate can have the same shape. Those rows
  remain `capture_metadata_missing`, never a guessed fusion.
- Kimi norm-gate has 276 usable descriptors and 5,175 original N/A rows. The
  latter are missing in the original archive member, not lost by normalization.
- `MlaPrologV3` and `LightningIndexer` span multiple current semantic nodes.
  Their native descriptors are retained, but no full event is attached to an
  arbitrary child node. Explicit fusion boundaries are still needed.
- Kimi's actual unabsorbed prefill FIA has Q/K width 192 and V/O width 128.
  The existing generic sim MLA path absorbs into latent width 512. This requires
  a source-defined prefill lowering; relabeling the current node would be wrong.
- `AddRmsNormBias` is parsed, but native/fusion selection is not independently
  declared by the current cases. It is not aliased to ordinary or Gemma RMS.
- Four V4 Pro SharedKV events have no compressed-cache input. The current
  declaration has compressed-cache presence at those active dimensions; the
  mismatch is retained, without guessing their layers.
- No model module evidence was retained for these eight CSV windows. Kimi's
  Python trace belongs to the API process and has no model-module/device-flow
  evidence. The previous [A2 synchronized module replay](module-replay.json)
  remains the positive actual-binding proof, not an A3/A5 LLM layer claim.
- In the inspected A5 GLM/DeepSeek directories and nested archives, only serving
  metrics were found. Kimi A3 evidence is primitive-only. Catalog support is not
  counted as full model profiling acceptance for those combinations.

## Reproduction and regression

The shared CSV decoder now reads `.csv.gz` directly and prioritizes `OP Type`
over `Task Type`. Explicit filenames such as `pf4k_b1.csv.gz` also work in
inventory, without conflating separate captures as ranks.

From the profiler checkout with matching sim source available:

```bash
PYTHONPATH=.:../sim-rewrite-20261027 \
  ../sim-rewrite-20261027/.venv/bin/python examples/structure/replay_body_capture.py \
  --capture /Volumes/data/mindie-sim-data/a3/2026-10-23/glm53-attn/raw/kernels/pf4k_b1.csv.gz \
  --case ../sim-rewrite-20261027/examples/cases/glm53-a3-w4a8.json \
  --phase prefill --tokens 4096 --output /tmp/glm-body-replay.json
```

The script's phase describes the declaration; it does not label all observed
events. Each saved report records its exact case and declared execution for
other reproductions. Kimi uses a single streamed archive member:

```bash
tar -xOzf /Volumes/data/mindie-sim-data/a5/2026-10-23/kimi-k3-longctx/k3lc-os1.tgz \
  raw/prof-export/op_summary_20261023053244.csv \
  > /tmp/mindie-body-profiling-kimi-op-summary.csv
```

The expected member SHA256 is
`ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648`;
archive identity is recorded in the inventory and Kimi report. No full archive
extraction or whole-file JSON/CSV loading is used.

Real-row tests cover operator identity, local head dimensions, cache presence,
dtype/layout changes, missing fields, source-call boundaries and independent
sim declaration equality. Mapping controls verify repeated layers, explicitly
annotated occurrences, conflicting tensors/phases, streaming parity and
nonadditive timing. Controlled bindings are labeled test evidence.
Streamed module mapping additionally requires windows covering full event spans;
clipped windows must preload selected events before loading module evidence so
that an overlapping invocation outside the clipped window is not missed.

Final local verification with both development checkouts:

- Profiler maintained suite: **435 passed, 26 skipped**, 7.88 seconds.
- Sim maintained suite excluding `live_npu`: **1,064 passed**, 234.81 seconds.
- Current resource-service, structure and observation interfaces: **56 passed**,
  0.79 seconds, after the concurrent sim engine integration.
- `git diff --check` passed in all three repositories; affected text files use LF.

The first sim full run exposed an unrelated prepared-plan/context binding
regression during the parallel sim integration. That execution-context path was
corrected in the sim workstream; the original resource-service assertions pass
without weakening source binding. No engine fix or persistent test workaround
is owned by this profiling change.
