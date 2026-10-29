# Native Layout And SiTU Declaration Evidence

This is a source and retained-capture check, not a new NPU run. Original capture
rows remain in `tests/fixtures/fusion_contracts/` with source hashes and row
locators in its `provenance.json`.

## LayerNorm

GLM's indexer uses mean/variance LayerNorm with affine weight and bias. The
independent `vllm` revision `58d3918e3ea0a544ffedadad2ba84559e9c51d8f`,
`vllm/model_executor/layers/layernorm.py:310-325`, explicitly converts the input
to FP32, uses FP32 affine parameters, and converts the result to the input dtype.
Its SHA-256 is
`3460eba01758849027bb59b8592626406e33ab25b23d2def729bb0ec42afce67`.

The sim declaration now contains input conversion, FP32 LayerNorm, and output
conversion. The GLM prefill and decode fixtures have matching FP32
`LayerNormV3` x/gamma/beta/y descriptors, respectively 4096 and 1 rows of width
128. The retained native rows also contain mean and reciprocal-standard-deviation
outputs. Those fields remain in the normalized observation. They are excluded
from the active primary-output comparison and from the semantic y-only workload;
this declaration does not select a physical native implementation or claim that
its auxiliary stores have been priced.

## Transposed Batch Matrix

The native projection preserves batch, row, input-channel, output-channel and
operand precision. It accepts the two retained input-axis orders while preserving
the original descriptors in comparison scope. Physical strides, permutation
arguments and dispatch selection are outside the comparison. It is not converted
into an ordinary unbatched GEMM.

Independent source evidence:

- `vllm-ascend` revision `175ef4d49c2072f9233619636f0309f4f88b4e2c`,
  `vllm_ascend/attention/sfa_v1.py:917-948`, SHA-256
  `c4ea3f33ba6c71d9a9163dc397c12d92dba67aa26c292ab1ce52605b3c91ad42`:
  absorbed query and expanded value batch matrices.
- Revision `ae923905948f360f4b7ab06df52d0789a0c9316e`,
  `vllm_ascend/attention/dsa_v1.py:1530-1572`, SHA-256
  `3fb4e94672e6adb931cb2e2a164201000822fe89250fd3bfd3585ba397acf52e`:
  grouped output projection with transpose-view arguments.

These declarations add metadata to existing batched matrix work and do not
invent transpose copies. The selected GLM prolog implementation and the retained
Kimi BF16 value expansion match their native active descriptors. The unselected
GLM and the retained V4 quantized cases remain precision gaps against BF16 native
rows. Separate caller-declared BF16 scenarios validate the V4 geometry adapter;
they do not replace the retained cases.

## SiTU

The independent Kimi config declares `hidden_act=situ`, beta 4, and linear-beta
25. The source expression is in `vllm/model_executor/layers/activation.py:155-184`,
revision `58d3918e3ea0a544ffedadad2ba84559e9c51d8f`, SHA-256
`157cb7610fba4237350daf7ec3b58c34c7f3fb38de8ff7b9e55584a69ca475c3`:

```text
gate = beta * tanh(gate / beta) * sigmoid(gate)
up = linear_beta * tanh(up / linear_beta)
result = cast_to_input_dtype(gate * up)
```

Dense, shared-expert and routed-expert FFNs now retain this activation and its
FP32 expression. The analytical BF16 expression counts 12 scalar operations per
output element, including casts and one operation per transcendental expression;
it is not a claim about native instruction count. Input and output traffic remain
the gated activation's actual two-input, one-output volume.

The local `SituMxQuant` registration is in
`csrc/moe/situ_mx_quant/op_host/situ_mx_quant_def.cpp:20-64`, SHA-256
`c4c9e30dd13cf759fc036b188360cb022e167ac209eeb5f86a020256e7d07367`.
That file is staged as an addition on base revision
`175ef4d49c2072f9233619636f0309f4f88b4e2c`; it is not attributed to the base
commit or to the captured binary.

A SiTU plus MX-quantization group requires an explicitly declared BF16 input,
FP8 output and E8M0 scale. Its scope excludes unknown native scalar values and
quantization layout. The grouped matrix plus SiTU variant remains marked
`native_abi_unverified`, with no tensor contract or physical fusion claim.

The retained Kimi case currently declares BF16 activations and routed MXFP4
weights without activation-scale metadata. It therefore does not select either
quantized SiTU boundary. This is a declaration/configuration identity gap; the
observed FP8 rows are not used to change the case.

## Verification

The affected sim tests passed: 40 layout, activation, attention and structure
checks, plus 33 family-selection checks. Seven profiler tests passed using
original LayerNorm and batch-matrix fixture rows. Tests check preservation of
batch geometry, casts, work and traffic, precision mismatches, native membership,
and the distinction between the retained case and an explicit alternative
quantization scenario. No full capture was rescanned for these checks.
