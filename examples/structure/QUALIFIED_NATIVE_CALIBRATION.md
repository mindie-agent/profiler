# Explicit Opt-In Qualified A2/A5 Native Calibration

`qualified_native_calibration.py` exposes two frozen, named operator calibration profiles as **explicit opt-in** simulation responses. Default `observed_native` replay and all archived profiles preserve their existing behavior; no model name, case ID, observed latency, or file path ever activates these profiles implicitly.

## Available Profiles

| Profile ID | Imported Native Operator Families | Status |
| --- | --- | --- |
| `a2-fia-dense` | A2 `FusedInferAttentionScore` (FIA) dense continuous-TND KV, W8A8 dense scale-only GEMM | `qualified/experimental` |
| `a5-attention` | A5 prefill attention (`D128` / `D256`), GDN `ChunkFwdH` | `qualified/experimental` |

- **`a2-fia-dense` train-only gating rule**: The A2 profile also records a frozen `fused_gdn_gating_kernel` response marked **train-only** (`0` heldout rows). It remains excluded unless `include_train_only=True` is passed explicitly and is never counted as a heldout-validated rule. Standard `mindie-sim` BF16 `delta_gates` operators are never relabeled as FP32 fused gating kernels; only an explicit caller-declared matching gating operator can select that rule.
- **`a5-attention` strict family scope**: The A5 profile imports only the three predeclared priority families listed above. `Cast`, `Transpose`, `Prepare`, `ChunkFwdO`, causal convolution, and `D256` decode remain analytical — no auxiliary operator role or decode phase is promoted automatically.

## Python API

`raw_case` below is the caller's original `mindie-sim` Case mapping; the adapter always returns a shallow/deep copy as needed and never mutates the caller's input dictionary.

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "examples/structure")
from native_observations import predict_body

abi = json.loads(Path("tests/fixtures/native_observations/qualified_a2_abi.json").read_text(encoding="utf-8"))
prediction = predict_body(
    raw_case,
    phase="prefill",
    tokens=2048,
    context=0,
    qualified=(("a2-fia-dense", abi["prefill"]),),
)
```

Selecting the A5 attention profile uses the same opt-in tuple convention:

```python
a5_abi = json.loads(Path("tests/fixtures/native_observations/qualified_a5_abi.json").read_text(encoding="utf-8"))
# `context` is the prior KV prefix; total native KV length = 8192 + 24576 = 32768.
prediction = predict_body(
    raw_case,
    phase="prefill",
    tokens=8192,
    context=24576,
    qualified=(("a5-attention", a5_abi["qwen35_tp4_h4"]),),
)
```

Because `ChunkFwdH` is a standalone public GDN callback, invoke it through the call builder and `graph_costs` directly (the adapter injects rules into a copied Case without mutating `raw_case`):

```python
import sys

sys.path.insert(0, "examples/structure")
from mindie_sim.prediction.operators.linear_attention.call_gdn import make_call
from mindie_sim.prediction.graph_analysis import graph_costs
from qualified_native_calibration import apply_qualified_native_observations

call = make_call(
    "scan_prefill",
    dict(batch=1, tokens=12288, k_heads=4, v_heads=8, k_dim=128, v_dim=128, chunk=64),
)
selected_case, provenance = apply_qualified_native_observations(
    raw_case,
    profile="a5-attention",
    phase="prefill",
    tokens=12288,
    context=0,
    native_abi=a5_abi["chunk_h8"],
    operators=call.ops,
    recipes=call.recipes,
)
report = graph_costs(selected_case, call.ops, recipes=call.recipes)
```

## Command-Line Entrypoint

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

The CLI prints the imported rule count alongside full provenance metadata (matched operator boundaries, verified ABI SHA256 digests, target service queue name, and frozen validation denominators). Pass `--include-train-only` explicitly if you want to inspect the train-only A2 gating rule.

## Contract & Failure Semantics

- **Full native slot ABI verification**: Callers supply the retained native ABI dictionary keyed by operator family. Before importing any rule, the adapter validates required input slots, explicitly absent optional/undefined slots, output slots, per-slot `dtype` / `layout` / `shape` invariants, geometry relationships, operator API, kernel name, hardware SKU, runtime stack, KV layout (`continuous TND`, dense, non-paged), and control flags. Missing outputs, unexpectedly active optional inputs, mismatched dtypes/layouts/shapes, or disagreements with caller-declared `attention_tensor_view` or `service_identity.implementation` raise typed `QualifiedCalibrationError` subclasses (`QualifiedCalibrationIOError`, `QualifiedProfileError`, `QualifiedAbiMismatch`) rather than silently falling back.
- **Explicit `not_applicable` outside the frozen physical domain**: Whenever hardware SKU, parallelism, runtime configuration, quantization, sequence count, or tensor shape falls outside a profile's frozen physical domain, the adapter returns a copy of `raw_case` unchanged alongside `status: "not_applicable"` and an explicit reason code so ordinary analytical prediction can proceed without masking out-of-domain misses.
- **Single replacement service queue (zero double-charging)**: Each profile registers a single service queue (`qualified_native_service` on A2; `native_local_service` on A5) only when the caller has not already declared a conflicting queue definition, installing a `JointNativeService` replacement on that queue while keeping analytical reference work isolated so timings are never double-counted.
- **Auditable runtime guard projection**: `metadata.native_abi.*` selectors are verified up front against the supplied ABI and stripped before runtime rule matching, while physical domain bounds, response coefficients, dtypes/layouts, and declared `gqa_*` / head geometry guards remain active at evaluation time (A2 FIA `kv_rows` and `prefix` coordinates bind to the declared local attention shape after ABI verification).

## Retained Heldout Denominators

- **A2 initial heldout (`123` admitted rows)**: `114` `JointNativeService` calls (`96` within `<= 10%`, `18` joint misses), `6` FIA analytical domain misses, and `3` unsupported GDR rows (`120` numerical rows total). Joint WAPE is `4.2732%` (`4.3461%` including the `6` analytical misses), which does **not** constitute a universal per-call pass. Fused GDN gating has `0` heldout rows and remains `train-only`.
- **A5 heldout (`87` total rows)**: All `8` predeclared priority domain points pass (`5` chunked attention + `3` `ChunkFwdH` at `T=12288`), while pure-prefill `q=1536` / `q=65536` and `ChunkFwdH` at `T=1536` / `T=49152` were predeclared out of domain. Across the full `87`-row denominator (`54` joint rows, `33` analytical fallback rows), `37/54` joint rows and `39/87` total rows fall within `<= 10%` (overall WAPE `61.0026%`). `D256` decode remains unpromoted (`6/6` heldout within `10%`, but `29/30` in-sample train with `11.312%` max error). No all-family, whole-prefill, whole-GDN, or end-to-end accuracy claim is made.

## Interaction with Prepared Capture Scopes & Cache Identity

- **Mutually exclusive with `scope=`**: Calling `predict_body(..., scope=..., qualified=...)` raises an explicit error rather than silently dropping `qualified`; ordinary `scope` replay without `qualified` is unaffected.
- **Automatic cache invalidation**: `native_observation_identity()` hashes `qualified_native_calibration.py` together with both frozen JSON profile files, so any code or coefficient change automatically invalidates prior cached predictions.
