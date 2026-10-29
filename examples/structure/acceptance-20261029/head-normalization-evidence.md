# Head normalization and SiTU coverage

This is retained A3/A5 capture analysis and source-selected local simulation,
not a new live NPU run. The compact machine-readable evidence is
`head-normalization-evidence.json`.

## AddRmsNormBias and AddRmsNormDynamicQuant

The original GLM rows contain a real fourth beta tensor; Qwen rows contain an
explicit empty fourth slot. Profiler now retains both ABIs. It does not turn
missing beta into zeros or infer a model parameter from the tensor shape.

The independent checkpoint metadata was read on the actual capture host
192.168.13.165, at `/mnt/weight/GLM-5.3-W4A8-INT/quant_model_description.json`.
Its SHA-256 is `08ce843a3517323bc0e93de00ea90e673b83d5b5766c9bd432108ede0a703503`
and its size is 17,219,752 bytes. The 22 bias keys belong to indexer LayerNorms;
there are no input/post-attention RMSNorm bias keys. This does not mean the
RMSNorm native beta slot is absent: `AscendRMSNorm.__init__` uses a global
`any("norm.bias" in name for name in quant_description)` test and allocates a
zero beta for every instance when that test passes. Its residual forward
passes this beta regardless of `bias_loaded`. The no-residual path checks
`bias_loaded` separately. The full key list and exact source hash are in JSON.

The explicit `vllm_ascend_native_norm` operator-family selection reuses existing
`residual_norm` and `norm_quant` passes. `has_bias: true` adds the channel beta
read and per-element addition. AddRmsNormBias retains both normalized and
residual outputs and writes FP32 rstd. Quantized variants retain live residual
and scale outputs; unused native auxiliary stores are explicitly outside the
modeled active-output scope. Gemma's caller-side gamma+1 requires the explicit
`external_gamma_shift: true` choice and remains a separate weighted-vector
read/add/write operation. It is not hidden inside AddRmsNormBias.

The original base cases are not edited. A GLM source/checkpoint-conditional
scenario enables `activation_quantization`, `norm_quant`, `residual_norm`, then
selects `add_rmsnorm` and `add_rmsnorm_quant` with the family above and
`has_bias: true`. The historical container no longer exists; current metadata
and independent source do not attest the captured executable revision.

## Kimi RMSNorm MX quantization and SiTU

An existing semantic ordering error blocked valid norm/quant composition.
Kimi `_KimiRoutedOutputTransform` applies the latent norm after routed combine
and before the latent up projection. Sim had placed it after latent down,
before expert packing. The catalog now declares the output position, and the
builder preserves combine -> weighted norm -> up projection, including the
(rows, 3584) shape and gamma read. This correction changes Kimi's structure;
it is independent of profiling duration or tensor fitting.

The retained Kimi catalog still declares BF16 activations. Its base case cannot
be called a verified FP8 checkpoint. A separate caller-declared MX scenario
uses FP8 E4M3 matrices/activations, E8M0 block-32 scales and `norm_quant` to
exercise RmsNormDynamicMxQuant. Full native/checkpoint identity remains open.

SituMxQuant now compares its active BF16 input, FP8 output and E8M0 scale
shapes, dtypes and layouts. The independent Kimi configuration supplies
beta=4 and linear_beta=25; capture descriptors do not expose those scalars or
activate_left. This is a conditional tensor comparison, not numerical or
occurrence proof. Routed GroupedMatmulSituQuant remains a separate unresolved
native ABI and is not aliased to SwiGLU.

The explicit `situ_mx_quant_arch35_2a9bd1b0` resource profile reuses the common
native fusion DAG. Inspected source keeps the SiTU BF16 result in local memory
for quantization; only that intermediate write and read disappear. Input
reads, FP8 output and E8M0 scale writes, vector expression and quantization work
remain. No native tiling or capture-binary identity is claimed.

## Validation boundary

Tests compare retained GLM/Qwen/Kimi original CSV rows against independent
source declarations, check real read/write/vector demand, preserve the external
Gemma producer, verify the Kimi latent-norm dependencies, and execute the SiTU
resource DAG through the common graph-cost engine. They do not create module,
layer, or invocation identity. Full capture prevalence and mapping results
belong to the separately generated final replay reports.
