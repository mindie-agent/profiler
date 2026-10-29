# Heterogeneous sparse-attention cohort coverage

The P1 mapper now uses the recorded `SparseAttnSharedkv` compressed-index
interface to narrow its active tensor-contract candidates before testing their
physical equivalence. Replaying the two existing complete A3 captures recovers
41 V4Flash and 244 V4Pro events previously excluded as
`candidate_physical_work_differs`. No sim prediction, graph, case, raw capture or
formal full-family report was changed. This is an offline replay, not a new
device collection.

The compact machine-readable evidence is
[`heterogeneous-sparse-coverage.json`](heterogeneous-sparse-coverage.json).
It preserves original source hashes, fixture/source row numbers, graph IDs,
descriptor evidence, per-group errors and validation resources.

## Evidence and matching boundary

The native argument order names input slot 4 `cmp_sparse_indices`. Its explicit
undefined absence differs from a recorded INT32/ND tensor shaped
`[query_tokens, kv_heads, topk]`. The existing sim export independently supplies
`structure.indexer` and `operator.metadata.indexed_attention_geometry.topk`.
Matching these fields separates indexed and nonindexed compressed attention
while retaining the original active tensor contract and physical-work checks.

Source evidence is pinned to vllm-ascend revision
`175ef4d49c2072f9233619636f0309f4f88b4e2c`:

- `csrc/torch_binding.cpp`, HEAD lines 1099 and 1127, establishes native argument
  order. The working tree differs, so provenance records the HEAD blob hash.
- `vllm_ascend/attention/dsa_v1.py`, lines 1556-1590, supplies compressed cache
  and the optional compressed-index tensor in their respective branches.
- V4Flash original CSV lines 319 and 401 record indexed top-k 512 and explicit
  empty indices with the same active query/cache contract. V4Pro original lines
  337 and 141 record indexed top-k 1024 and explicit empty indices.

Each measured event enters at most one retained candidate-set cohort. Timing
does not choose a group. Missing or unsupported descriptors and unknown
declaration fields remain possible candidates; they do not silently select a
physical program. Contradictory explicit layer annotations are rejected.
No compression ratio, actual context, phase, layer, step or index values are
derived from this refinement. Group labels below describe the retained
independent declarations.

## Coverage and comparison

| Capture / operator | Raw events | Before cohort events | After cohort events | Remaining |
|---|---:|---:|---:|---|
| V4Flash SparseAttnSharedkv | 44 | 3 | 44 | None |
| V4Pro SparseAttnSharedkv | 248 | 0 | 244 | 4 descriptor mismatches |
| V4Flash Compressor | 62 | 0 | 0 | 62 norm-weight precision mismatches |
| V4Pro Compressor | 364 | 0 | 0 | 364 norm-weight precision mismatches |

The complete sources still contain 4,064 V4Flash and 24,271 V4Pro positive
events. The five sparse-attention cohorts pass the existing comparison
eligibility checks, but all five predictions remain outside the relative 15%
accuracy tolerance.

| Capture / declared group | Measured calls | Declared candidates | Observed us/call | Predicted us/call | Relative error |
|---|---:|---:|---:|---:|---:|
| V4Flash SWA, no compressed cache | 3 | 2 | 489.163 | 59.419 | -87.85% |
| V4Flash indexed compressed, top-k 512 | 21 | 21 | 3,738.519 | 1,406.401 | -62.38% |
| V4Flash nonindexed compressed | 20 | 20 | 946.030 | 59.870 | -93.67% |
| V4Pro nonindexed compressed | 124 | 31 | 259.851 | 14.886 | -94.27% |
| V4Pro indexed compressed, top-k 1024 | 120 | 30 | 1,180.346 | 126.921 | -89.25% |

These retain the comparison interpretation
`conditional_descriptive_comparison; no_occurrence_or_accuracy_certification`.
In particular, the V4Pro declaration uses context 0; this does not establish
the actual context of every event in its multi-chunk capture. Calls divided by
declared candidates are not independently verified step counts. All events
remain unbound to individual layers.

## Remaining gaps

**Four V4Pro sparse-attention events:** the recorded compressed-cache slot is
explicitly empty, while every one of the 61 declared body attention targets
uses compressed cache. The retained original example is CSV line 5983, with
query/output `[1024, 8, 512]`. The mapper preserves this mismatch. Neither event
order nor the count proves draft/MTP ownership.

**Compressor:** input slot 5 is `FLOAT` (FP32) in the retained A3 rows; the
independent sim declaration has BF16 norm weights. The APE parameter's leading
dimension already distinguishes ratios 4 and 128, and projection/norm widths
distinguish attention and index compressors. Candidate bucketing cannot repair
the remaining precision difference.

The clean local source
`vllm_ascend/models/deepseek_v4/compressor.py` at the pinned revision explicitly
selects FP32 norm weights only for A5 at lines 142-144 and passes
`self.norm.weight` directly at line 218. The historical A3 capture recipe uses
vllm-ascend `0.30.0rc2.dev200+g8fd0bc488`, image digest
`sha256:5bdd40411c1abda875996cb83cdd6c0ca1a5251240aa19755ae6aab539ce1bdc`.
Independent evidence from that runtime/checkpoint is needed before selecting
FP32 norm semantics. No dtype relaxation or observed-to-model backfill is made.

## Validation

26 focused tests pass in 9.44 seconds, including real empty/512/1024 index
interfaces, equal timestamps with distinct descriptors, incompatible explicit
annotations, unknown declarations, typed-empty slots, and preservation of the
Compressor precision gap.

The two full-source replays and focused sparse-cohort comparisons take
1.455 and 3.345 seconds. Peak process RSS is 146,128,896 bytes, below the
512 MiB analysis budget. Both freshly exported graph IDs exactly match the
formal baseline generated with sim `239f443c`. Evidence finalization records the
coordinated sim HEAD `ea0bae98509ebddbe87aa092941c97de3bee8008`; its exported
graph IDs remain equal to that baseline. Validation uses Python 3.13.12.
Temporary full mapping/comparison files are under `/tmp/P1-a3_v4f-*` and
`/tmp/P1-a3_v4pro-*`; this directory retains only the compact evidence.
