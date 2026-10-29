# Compressor FP32 conditional replay

This is an offline replay of two retained A3 captures, using Python 3.13.12.
The compact source, graph, count and resource receipt is
[`compressor-normalization-evidence.json`](compressor-normalization-evidence.json).
No new device collection or model-weight loading was performed.

The additional declarations select FP32 compressor normalization from independent
`vllm-ascend` source revision
`90f72ef299d4252a3658e1cf1477f1a25d178cd4`. Its
`vllm_ascend/models/deepseek_v4/compressor.py:142` constructs RMSNorm with FP32
weights; the native call passes that parameter directly. The JSON records the
pinned blob hash and a second corroborating revision. This establishes a
conditional source implementation, not the historical capture binary identity.
The original reference and selected cases remain available. Existing selected
hyper-connection boundaries are preserved.

| Capture | Declared body geometry | Compressor events | Matched cohorts | Compared events | Reference events | Observed activity |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| V4Flash A3 | prefill, 4096 tokens, context 0 | 62 | 3 | 0 | 62 | 27.361114 ms |
| V4Pro A3 | prefill, 1024 tokens, context 0 | 364 | 3 | 0 | 364 | 77.516420 ms |
| Total | two independent captures | 426 | 6 | 0 | 426 | 104.877534 ms |

Each declaration has the three source-supported parameter branches:
compression ratio 4 / width 512, ratio 4 / width 128, and ratio 128 / width 512.
Flash has 21, 21 and 20 observed calls respectively; Pro has 120, 120 and 124.
These parameter contracts establish candidate groups, not occurrence-level layer
or step identities. In particular, the complete Pro capture is compared against
a caller-declared body geometry; its event counts do not establish its step
sequence or active contexts.

All 426 matched events remain `reference_only`. The current semantic compressor
reference has five phases. Native `SaveState` / `WriteToCacheState` in
`csrc/attention/compressor/op_kernel/arch32/compressor_block_vec_perf.h` writes
updated state to global memory, whereas the current reference does not
explicitly price that side effect. Its volume depends on sequence and block-table
values. Native workspace traffic and internal reuse are also not reconstructed.
Selecting a single launch with `preserve_workspaces` would not supply this
missing work, so no native compressor fusion is selected and no accuracy result
is assigned.

The unfused reference totals 75.238880 ms when multiplied by the observed call
counts. That value is a resource reference, not a native-kernel prediction or an
accuracy claim. Two complete scans took 5.946842 seconds with a peak resident set
of 145,276,928 bytes. Four focused tests passed in 5.83 seconds, covering unchanged
baseline declarations, real capture descriptors, the FP32 parameter-read change,
single-count event accounting, and reference-only comparison behavior.
