# Explicit qualified A2/A5 native calibration

`qualified_native_calibration.py` imports two frozen, named calibration profiles
as **explicit opt-in** responses. The default `observed_native` replay and every
archived profile keep their prior behavior. No model name, case ID, observed
duration or file path selects a response.

## Profiles

| profile | imported native families | status |
| --- | --- | --- |
| `a2-fia-dense` | A2 FIA dense continuous-TND KV, W8A8 dense scale-only | qualified/experimental |
| `a5-attention` | A5 prefill attention D128/D256, GDN `ChunkFwdH` | qualified/experimental |

The A2 profile also records the frozen `fused_gdn_gating_kernel` response as
**train-only**. It is excluded unless `include_train_only=True`, has zero heldout
rows, and never becomes a heldout-validated claim. Ordinary Sim's BF16
`delta_gates` op is not relabelled as the FP32 fused gating kernel; only a
caller-declared matching gating op can select that recorded rule.

The A5 profile imports exactly the three predeclared priority families. It does
not import Cast, Transpose, Prepare, ChunkFwdO, causal convolution, or D256
decode; those remain analytical. No minor role or decode promotion is automatic.

## Python API

`raw_case` below is the caller's retained raw Sim case; the adapter returns a
copied case and never mutates the caller's mapping.

```python
import json
import sys
sys.path.insert(0, "examples/structure")
from native_observations import predict_body

abi = json.loads(open("tests/fixtures/native_observations/qualified_a2_abi.json").read())
prediction = predict_body(
    raw_case, phase="prefill", tokens=2048, context=0,
    qualified=(("a2-fia-dense", abi["prefill"]),),
)
```

The A5 attention arm uses the same opt-in tuple:

```python
a5_abi = json.loads(open(
    "tests/fixtures/native_observations/qualified_a5_abi.json").read())
# context is the prior prefix; retained native total KV = 8192 + 24576 = 32768.
prediction = predict_body(
    raw_case, phase="prefill", tokens=8192, context=24576,
    qualified=(("a5-attention", a5_abi["qwen35_tp4_h4"]),),
)
```

`ChunkFwdH` is a complete public GDN callback, so use the existing call builder
and `graph_costs`; the rules are inserted into a copied case and never overwrite
the caller's raw:

```python
import sys
sys.path.insert(0, "examples/structure")
from mindie_sim.prediction.call_gdn import make_call
from mindie_sim.prediction.graph_analysis import graph_costs
from qualified_native_calibration import apply_qualified_native_observations

call = make_call("scan_prefill", dict(batch=1, tokens=12288, k_heads=4,
                                      v_heads=8, k_dim=128, v_dim=128, chunk=64))
selected, provenance = apply_qualified_native_observations(
    raw_case, profile="a5-attention", phase="prefill", tokens=12288, context=0,
    native_abi=a5_abi["chunk_h8"], operators=call.ops, recipes=call.recipes,
)
report = graph_costs(selected, call.ops, recipes=call.recipes)
```

## Runnable CLI

```bash
python examples/structure/qualified_native_calibration.py \
  --profile a2-fia-dense \
  --case tests/fixtures/native_observations/qualified_a2_case.json \
  --abi tests/fixtures/native_observations/qualified_a2_abi.json --abi-key prefill \
  --phase prefill --tokens 2048 --context 0

python examples/structure/qualified_native_calibration.py \
  --profile a5-attention \
  --case tests/fixtures/native_observations/qualified_a5_cases.json --case-key qwen35_tp4_h4 \
  --abi tests/fixtures/native_observations/qualified_a5_abi.json --abi-key qwen35_tp4_h4 \
  --phase prefill --tokens 8192 --context 24576
```

The command prints the imported-rule count and the full provenance, including
matched boundaries, actual ABI hashes, one queue, and the frozen denominators.
`--include-train-only` is the only way to expose the A2 gating record.

## Contract and failure semantics

- The caller supplies the actual retained ABI, keyed by profile family. The
  profile validates the complete retained native slot contract: required input
  slots, explicitly absent optional/undefined slots, output slots, per-slot
  dtype/layout/shape and geometry relations, plus API, kernel, hardware, known
  runtime, KV view (continuous TND, dense, non-paged) and control flags. Missing
  outputs, an unexpectedly active optional input, a bad output dtype/layout/
  shape, or a conflicting input layout are typed errors, not silent successes.
  Explicit caller `attention_tensor_view` shapes/dtypes/layouts and
  `service_identity.implementation` are reconciled with the same retained ABI
  before projection, so a caller paged or wrong-dtype entity is not overwritten
  by duplicated profile labels. A malformed profile or disagreeing ABI is a
  typed `QualifiedCalibrationError` (`QualifiedCalibrationIOError`,
  `QualifiedProfileError`, `QualifiedAbiMismatch`).
- A hardware, parallelism, runtime, quantization, sequence or shape state
  outside the frozen physical domain returns the caller's raw unchanged with
  `status: not_applicable` and a reason. Ordinary prediction remains available;
  no heldout or out-of-domain error is hidden.
- One declared queue (`qualified_native_service` for A2,
  `native_local_service` for A5) is written only when the caller has not
  declared a conflicting rate/owner/work unit. The imported rule is a
  `JointNativeService` replacement on that queue. Sim retains the analytical
  reference work separately, so the response is never added on top of the
  analytical schedule (no double charge).
- Projection is explicit and auditable: the analysis adapter's
  `metadata.native_abi.*` and related identity selectors are validated against
  the caller's actual ABI and removed from the ordinary-Sim runtime match.
  Physical domains, response coefficients, dtype/layout and declared
  `gqa_*`/head geometry remain in the runtime guards. A2 FIA `kv_rows`/`prefix`
  coordinates use the declared attention local shape after the exact ABI check.

## Truthful denominators

A2 first heldout: 114 JointNativeService calls, 96 within 10%, 18 Joint
failures; 6 FIA analytical domain misses and 3 GDR rows unsupported; 120
numerical rows and 123 admitted rows. Joint WAPE is 4.2732% (4.3461% including
the six analytical misses), but this is not a universal per-call pass. Gating
has zero heldout rows and stays train-only.

A5 heldout: 8 priority domain points pass (5 chunked attention + 3 ChunkFwdH
T12288); pure-prefill q1536/q65536 and H T1536/T49152 were predeclared outside.
The whole A5 denominator is 87 rows: 54 joint, 33 analytical fallback, 37/54
joint rows within 10%, 39/87 all rows, weighted absolute error 61.0026%. D256
decode remains unpromoted (6/6 heldout but TRAIN 29/30, max 11.312%). No
all-10-family, whole-prefill, whole-GDN or end-to-end accuracy claim follows.

## Prepared scope

`predict_body(..., scope=... , qualified=...)` is not a supported combination:
the qualified request is rejected visibly instead of being silently discarded.
Ordinary `scope` replay without `qualified` is unchanged.

## Cache identity

`native_observation_identity()` includes
`qualified_native_calibration.py` and both qualified JSON profiles. Changing any
of those semantics or data invalidates the retained prediction cache namespace.
