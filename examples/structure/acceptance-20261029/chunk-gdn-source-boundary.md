# A3 ChunkGDN: source boundary audit

The retained A3 implementation covers the entire chunk recurrence core in one
native launch. It is not a state-update-only kernel. This finding does **not**
resolve the 156 retained capture events into exact native matches: the capture
and the independently retained source expose different gate/output layouts,
and the generic sim group selects a different wrapper ABI.

This is a read-only source investigation on 2026-10-29. It performs no new
capture, full CSV scan, prediction, layer assignment, or accuracy acceptance.
The machine-readable evidence is
[chunk-gdn-source-boundary.json](chunk-gdn-source-boundary.json).

## Retained capture denominator

| Capture | Original CSV line | Events | Activity sum | Q/K | V |
| --- | ---: | ---: | ---: | --- | --- |
| A3 Qwen35 | 91 | 60 | 78.393143 ms | `[1,4,8192,128]` | `[1,8,8192,128]` |
| A3 Qwen36 | 87 | 96 | 164.081522 ms | `[1,4,8192,128]` | `[1,12,8192,128]` |
| Total | | **156** | **242.474665 ms** | | |

Counts and source hashes come from the existing
`tests/fixtures/mixed_step_body/provenance.json`; the two original descriptor
rows are already retained in that fixture directory. Both branches expose
FP32 beta, raw gate, initial/final state and cumsum; Q/K/V/A/output are BF16.
The input A-storage width is 64, and the metadata descriptors are INT64 `[2]`
and `[256]`. Their values are not recorded, so no sequence boundaries, chunk
indices, scalar flags, or layer identity are inferred from them.

## Source-supported computation

The independent source is
`flashserve/flash-linear-attention-npu` revision
`a4a795857868729fbdbb0118c1e06c8655a7b31b`
(retained wheel metadata: `26.9.1+deva4a7958`).
The aggregate kernel is:

```text
fla/ops/ascendc/gdn/chunk_gdn_fwd/chunk_gated_delta_rule_fwd/
  op_kernel/internal/arch22/chunk_gated_delta_rule_fwd_arch22.cpp
SHA256 b77606cadd208e42da7896cc2a5a7a5cde32e73da46108f58048333f78fe8d9c
18630 bytes
```

The local retained kernel was compared byte-for-byte against the official raw
file at that revision. The host and tiling files also match their retained
manifest hashes. This establishes source provenance, not the identity of the
binary used by the October 23 captures.

The L0 launcher has one `ADD_TO_LAUNCHER_LIST_AICORE` call
(`op_host/op_api/chunk_gated_delta_rule_fwd.cpp:67`). Its arch22 entry point
contains this sequence:

| Kernel source lines | Computation | Existing sim semantic operation |
| --- | --- | --- |
| 247-263 | Chunk-local FP32 gate cumsum, KKT and gated/beta epilogue | `chunk_products`, plus an explicit cumsum requirement |
| 265-340 | Triangular solve producing A | `triangular_solve` |
| 341-355 | Recompute W and U from K/V/beta/A/cumsum | `wy_transform` |
| 357-359 | Public cumsum export and H/final-state update | `recurrent_scan`, plus cumsum export |
| 361-377 | Output from Q/K/vNew/H/cumsum | `recurrent_output` |

The wrapper allocates the A-storage input at
`op_host/op_api/aclnn_chunk_gated_delta_rule_fwd.cpp:748`.
The kernel explicitly ignores it at line 389, `(void)a_storage`.
Its presence in the capture therefore does not demonstrate that a separate
upstream kernel has already produced A, nor justify charging an A-input read.
The solved A output is produced inside this native core.

Q/K/V projections, convolution, Q/K L2 normalization, gate activation
production, output norm/gating and output projection are outside this boundary.
The wrapper's input conversions and final output transpose/copy are also
separate from this one native launch.

## Why the current generic group is insufficient

The five existing semantic operations are in
`mindie_sim/prediction/recurrent.py:109`, `:113`, `:119`, `:125` and `:151`.
The `gdn_chunk` declaration at line 245 already groups this mathematical core,
but its source is the TND/BF16-state
`vllm_ascend/ops/gdn.py::_chunk_gated_delta_rule_fused` wrapper. That wrapper
casts state to BF16 and supplies per-sequence INT32 lengths. The retained
native capture instead has BHTD Q/K/V, FP32 state and cumulative/chunk INT64
metadata. Renaming or widening the default group would conflate these ABIs.

There is a second boundary difference even against the retained arch22 source:

| Descriptor | Capture | Retained native call |
| --- | --- | --- |
| Raw gate | `[B,T,H]` FP32 | `[B,H,T]` FP32 |
| Primary output | `[B,T,H,V]` BF16 | Allocated as `[B,H,T,V]` BF16 |

The host converts gate/beta before the native call at lines 599-612 and
transposes/copies the output after it at lines 782-795. The capture has no
strides or separate logical/storage-shape fields that establish whether this
is descriptor-view reporting or a different implementation version.
Flat auxiliary outputs alone are not a contradiction: the source explicitly
handles caller-owned storage descriptors. The unresolved gate/output
difference must remain visible rather than being flattened into exact ABI
equality.

## Resource requirements for a future selected implementation

One launch retains substantial GM intermediates. The arch22 tiler explicitly
allocates FP32 KKT scores and solve workspaces, BF16 pre-solve A, an internal
FP32 cumsum, W/U, BF16 H checkpoints and vNew. The kernel publishes and
consumes these GM buffers between stages. A generic fusion rule must not remove
all intermediate traffic.

The smallest truthful source-selected implementation must account for:

- Chunk cumsum computation, its internal GM write/read, and the public BTH
  cumsum export.
- FP32 KKT scores, pre-solve and solved A, solve precision conversions and the
  selected solve/layout-staging workspaces.
- W/U and H/vNew GM materialization and their consumers.
- FP32 initial/final state separately from BF16 intermediate H checkpoints.
- H/O scratch, matrix/vector phases, synchronization and one launch; wrapper
  conversions remain outside that launch.

For illustration, under a separately declared single 8192-token sequence,
the source W and U payloads are each 16 MiB for Qwen35 geometry and 24 MiB for
Qwen36 geometry. H checkpoints are 32/48 MiB, while initial/final FP32 state is
only 0.5/0.75 MiB. These are conditional allocation payloads, not measured HBM
traffic or a summed peak; the JSON preserves the formulas' numeric results and
their limitations.

A small next step can reuse the existing five semantic operations behind an
explicit arch22 source selector, expose the cumsum/output requirements, and
produce a **reference-only** active-geometry correspondence. It must retain
the source interpretation and layout uncertainty. Complete physical scoring
requires the source program's missing work/traffic and a compatible selected
boundary; this audit does not turn the existing 156 events into scored cohorts.
