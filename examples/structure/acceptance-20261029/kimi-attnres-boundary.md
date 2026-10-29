# Kimi AttnResFwd: source boundary and remaining evidence

The retained campaign image establishes the **same-name six-input,
three-output AttnResFwd interface**. The current gap is the complete source
program, active views and per-call scalar arguments. It is no longer an
unidentified four-slot interface. Profiler still returns no tensor candidate
for this type: the four recorded descriptors cannot select one physical
program or a layer.

This review reuses the prior full-capture descriptor count, verifies the four
retained rows and source hashes, and reads only the matching image's source
files. It does not rescan the raw capture, start a container, initialize an NPU,
read model weights, export a sim graph or run a prediction.

## Source identity

- Capture CSV SHA256:
  `ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648`.
- Retained image:
  `sha256:883670fcc91cbd75a7070b00501be0ecd81a266b81366a21bf02139d8e6a33e1`,
  tag `kimik3-pool-snapshot:20261017-node21`.
- [Caller/interface bundle](../../../tests/fixtures/kimi_grouped_attnres/source_image_883670fc/provenance.json)
  records the same-image Python, registration and torch-adapter hashes.
- [Kernel acquisition](../../../tests/fixtures/kimi_grouped_attnres/source_image_883670fc/kernel-provenance.json)
  records seven additional files, 117,162 bytes, from the effective image
  overlay. Upper-layer order, whiteouts, opaque directories and symlinks were
  checked before reading. Remote job: `job-20261029T142103Z-339d3416`.
- These establish the retained image's source implementation. They do not
  establish which compiled library or tiling key each captured call loaded.

## Actual recorded descriptors

All tensors are BF16. The captured bank format is NCL; the other formats are
ND. Shapes below are the original one-dimensional recorded extents, not
reconstructed logical prefix/bank views.

| First CSV line | Events | Input extents, in slot order | Output extents | Activity sum, us |
|---|---:|---|---|---:|
| 47 | 4 | 58720256;58720256;7168;7168;58720256;7168 | 7340032;58720256;7340032 | 110.623 |
| 78 | 744 | 7340032;58720256;7168;7168;7340032;7168 | 7340032;7340032;7340032 | 97511.831 |
| 30505 | 75 | 57344;57344;7168;7168;57344;7168 | 7168;57344;7168 | 310.114 |
| 30520 | 13945 | 7168;57344;7168;7168;7168;7168 | 7168;7168;7168 | 147655.751 |
| Total | 14768 | Four descriptors | | 245588.319 |

The source allocates `hidden_states = empty_like(prefix)`, so the fresh main
output supports a conditional local-row interpretation of 1024 or 1 at
H=7168. It does not recover the aliased prefix's active view or the bank's
valid history. No phase, layer or step is assigned from these extents.
The [JSON evidence](kimi-attnres-boundary.json) preserves native descriptors,
counts, diagnostics, source hashes and unresolved fields.

## Complete semantic interface for sim

Reuse the existing operation builders, dependency graph and complete-group
resource transformation, with a source-selected residual point:

```text
attn_res_point(
    context, prefix_id, addend_id_or_none, bank_ids,
    valid_blocks, write_slot_or_none, output_norm_or_none,
    mix, materialize, tokens_local, block_token_stride, optimize_prefill
) -> ops, hidden_id, raw_prefix_id, materialized_id, updated_bank_ids
```

The caller defines three main boundaries in retained `kimi_k3.py`:

1. `prepare_attn_residual`, lines 742-766: optional previous MLP add with BF16
   rounding, optional bank write, learned residual mixture, then input RMSNorm.
   Valid history is `ceil(layer_index / block_size)`. A block boundary stores
   the raw prefix and then clears the live prefix before attention, lines
   782-784.
2. FFN preparation, lines 796-809: optional attention residual add, mixture
   over `prev_valid_blocks + is_block_write_layer`, then post-attention
   RMSNorm. The block-write layer has no old live prefix to add.
3. Final output, lines 1102-1111: optional last MLP add and final mixture;
   no output RMSNorm is supplied. Standalone decoder calls have a separate
   add-only branch (`mix=False`, valid history zero), lines 817-827.

The initial embedding bank write, deferred MLP output and raw-prefix aliases
must remain explicit. Absorbing the add into the next point must remove the
old standalone residual add. Sequence-parallel sharding and transport are
part of the source program (lines 1019-1052, 786-794 and 1116-1131), not a
metadata-only division of the global token count.

The reviewed sim `AttentionResidual.before` currently describes only the
six-member learned mixture (`mindie_sim/prediction/blocks.py:137`), while
`Frontend.body` appends end-of-block residual sources and immediately adds
MLP outputs (`prediction/frontend.py:56`). Extending that group's member list
alone would not reproduce the retained image's prefix/bank state or final
boundary. This review does not change those defaults.

## Source-defined resource requirements

The retained `op_kernel/attn_res_fwd_apt.cpp:35` declares `AIV_ONLY`. Projection
and residual-norm weights are BF16 storage, loaded and multiplied into FP32
vector score weights (`arch35/attn_res_fwd_resident.h:176`). RMS, dot reduction,
softmax and weighted accumulation are vector operations. The old semantic
score GEMM cannot be priced as a native Cube GEMM for this implementation.

Let T be local rows, H hidden width and N valid bank rows. When mixing with
N>0, the resident path reads `2*T*N*H` useful bank bytes and retains rows in UB;
the reload path reads `4*T*N*H` useful bank bytes across its score and weighted
passes. Tiling selects between these using actual UB capacity and buffer
geometry (`op_host/attn_res_fwd_tiling.cpp:115`, `:210`).
`mix=False` or N=0 skips score/softmax/history reads.

Preserve prefix reads, optional addend reads and raw-prefix writes, bank
writes, main output writes, and optional materialized output writes. The
mixture is rounded to BF16 before optional output RMSNorm. Output-norm gamma
is normally read per token, but the explicit prefill-cache branch can retain
it per core when UB permits (`tiling.cpp:227`). These paths are directly
visible in `arch35/attn_res_fwd_reload.h:299`, `:322`, `:373`, and `:434`.

The entry ignores user workspace; host tiling reserves 16 MiB of system
workspace (`attn_res_fwd_apt.cpp:36`, `tiling.cpp:247`). This is not an
FP32 intermediate traffic allocation. Local score/mix/normalization buffers
can be modeled as on-chip only for this source-selected implementation;
external prefix, bank and materialized writes must not be removed.

## Contract and aggregation boundary

`attn_res_fwd_common.h:45-56` fills an absent addend with `prefix` and an absent
output-norm tensor with `norm`. The corresponding scalar flags disable their
work. All six nonempty tensor slots therefore cannot prove add or output-norm
presence. `valid_blocks`, bank stride, write slot, materialization and tiling
selection also remain absent from the capture.

A future parameter/output-extent projection can identify candidate complete
source groups. It cannot distinguish all valid-history/flag work buckets.
If one descriptor matches different physical work, retain
`candidate_physical_work_differs`; do not pick one subset by duration or layer
frequency. Complete-invocation multiset comparison would require independent
invocation bounds and multiplicity.

The diagnostic now distinguishes retained source-interface evidence from
unknown per-event implementation/tiling. AttnRes still has no contract and
adds zero bound events. Focused verification:
`tests/test_kimi_grouped_attnres_contracts.py` and
`tests/test_body_fusion_contracts.py`: **27 passed in 0.14s**.
