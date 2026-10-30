# GLM78 A3: typed native V2 caller increment

This arm starts from the immutable local-native joint-service baseline. It adds the explicit `arch22_v2_caller` lowering with per-token INT8 dispatch, retaining BF16 routers, native fused grouped up, shared FFN quantization, exact local padding/TP slicing, final AllGather/unpad, and the three local joint-service rules.

| Source | Real Body mean ms | Sim ms | Error | Body | Layers passed |
|---|---:|---:|---:|---|---:|
| tpot30 c2 | 57.639270 | 49.095646 | −14.822575% | PASS | 39/78 |
| tpot50 c2 | 57.817112 | 49.072212 | −15.125106% | **FAIL** | 31/78 |
| tpot88 c8 | 69.556298 | 66.841840 | −3.902534% | PASS | 78/78 |

The full source population remains 162 Forwards / 10 geometry buckets; 137 primary Forwards are compared and seven smaller buckets remain deferred. Three fresh workers completed in 16.58 seconds, maximum child RSS 121,634,816 bytes. No raw capture or device was read or executed. The preceding joint-only arm's 3/3 PASS is retained as history; it does not replace the failed latest c2 result.

The fresh graph has 75 DispatchV2 and 75 CombineV2 whole-kernel groups per Forward. All seven dispatch output tensor contracts match the retained ABI, with buffer capacities 128/384. Capacity is not an observed valid expert-row count. Dispatch INT8 payload plus FP32 dynamic scale feeds routed GMM directly: 75 redundant routed quantizers and separate route-pack/unpack recipes are removed. Shared DSQ 75/F, final AllGather 75/F, two c2 pad calls per MoE layer, BF16 router 75/F, dependencies and output scales remain intact. `dynamic_scales` and `expand_scales` remain distinct roles.

The complete native elapsed means apply once to each device-kernel group, including its transport phases. They are ordinary inclusive group floors, **not** local joint-native execution rules and not pure link-bandwidth measurements. The actual queries record 75/75 group responses and retain SFA/GMM joint invocations at 78/75/75.

The primary arm declares a logical peer window of 16, the EP size. No capture evidence identifies this window or fullmesh/basic/hierarchy tiling. A separately declared window-8 sensitivity preserves every measured response and source input. Its three fresh predictions are bit-identical to window 16, so the observed result does not identify peer concurrency. Window 16 was chosen as the primary logical lower-bound arm before this comparison; no best-error selection is performed.

Both arms use Sim `f6e68d5e326ccbc6aade4f62fffbd816b23da500`, package SHA `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`. Calibration remains `observed` / `in_sample`; no Body residual was used to assign any parameter.

Reproduce from the profiler repository with the fixed checkout at that commit:

```sh
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/build_glm78_native_v2_service_cases.py
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/replay_decode_forwards.py \
  --manifest examples/structure/acceptance-20261030-glm78-native-v2-service/decode-forward-glm78-native-v2-cases.json \
  --output examples/structure/acceptance-20261030-glm78-native-v2-service/decode-forward-glm78-native-v2-replay.json \
  --geometry-limit 1 --prediction-timeout 90 \
  --runtime-source-commit f6e68d5e326ccbc6aade4f62fffbd816b23da500
```

`prepare_glm78_native_v2_window_sensitivity.py` creates the independent window-8 inputs. Standard arithmetic reviews pass 999 checks per arm. The native result review passes 13,024 checks and the baseline compatibility review passes 224 checks, including all inherited BF16/source overlays and typed producer/consumer edges. Review success is distinct from accuracy PASS.
