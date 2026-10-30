# Observed-rate calibration and cohort admission

There is no strict-admission rule that rejects a program merely because a resource rate, per-call/per-group parameter, or payload/low-M regime parameter was calibrated from observations. No new admission shim was added.

The audited paths are `mindie_profiler/structure_cohorts.py::_cohort`, `structure_mapping.py`, `mindie_sim/cohort_comparison.py::_check_cohort/_comparison` and `cohort_accuracy.py::accuracy_fields`. Their gates concern tensor contracts, physical work, placement, complete native boundaries and complete measured events. A refreshed case must regenerate its own graph/physical identity; calibration provenance does not change those gates.

The source-reference producer now explicitly reports `observed_service_calibration.allowed=true`. The legacy `communication_bandwidth_calibration_allowed=false` is narrowly scoped to identifying a **pure link rate from elapsed time without separating peer wait**. It does not forbid effective same-boundary collective service calibration. The fallback collective remains a reference because its observed native contract/program boundary is unverified, not because the source parameter was measured. Historical receipts and their audits are unchanged.

A real public-API regression uses the Qwen3.5 c128 FFN TensorMove cohort: **12,160 complete calls**, shape `[128,2048]` BF16, 524,288 bytes read and 524,288 bytes written per call. It fits the effective MTE3 service rate to this cohort's observed mean, then explicitly declares that rate before calling `compare_cohorts`:

- Observed mean: **3.499248601974 us**.
- Fitted effective rate: **149,828,737,433.598 bytes/s** for this isolated operator/payload regime.
- Public API result: **`compared`, accuracy pass**, prediction **3.499248601974 us**.
- Tensor contract, physical work and all observed counts/durations remain unchanged.

This is deliberately **in-sample**. It is neither a hardware-peak estimate nor evidence of generalization, and the fitted rate is not installed into a production whole-model case. Fit/evaluation source identities and the payload regime are explicit in the regression fixture. Held-out evaluation is an additional report dimension, not permission to calibrate.

The same tests prove that an incomplete native-program boundary stays `reference_only`, and that the 6,080 real GroupedMatmul calls with capacity 4,096 versus declared valid rows 1,024 do not gain strict eligibility from a calibrated resource rate. Observational evidence gaps are distinct from parameter provenance.

Validation on companion Sim `cc245da639ea693daecc3ea273965606659da13a`: `tests/test_calibration_evidence.py` plus existing source-reference tests, **9 passed**. All input comes from committed retained evidence; no raw capture scan, remote collection, model weights or device initialization occurred. Sim source was read only; its historical calibration wording is being corrected by the Sim owner separately.

Decode replay also preserves explicit `calibration_origin` and `calibration_evidence` from each manifest row, falling back to the Sim case's `runtime.metadata`. A manifest declaration takes precedence. Every geometry result carries the same declaration; missing values stay `not_declared` / `null`. Explicit `runtime.kernels.service_regimes` are retained in `calibration_evidence.declared_service_regimes`, including each rule's domain, response, `scale_with` and provenance. A regime declaration alone does not establish an in-sample or heldout evaluation relationship. This metadata does not change contract admission or measured spans.

The replay regression reuses the real Qwen3.5 c4 extraction (91 complete forwards, including the 84-call main geometry), verifies its source hash without parsing raw events, and tests absent, case-level, manifest-level and regime-only declarations. It preserves all measured geometry populations without running a prediction or rewriting historical receipts.

`glm-qwen-observed-service-inputs.json` supplies compact native observations for
six GLM/Qwen captures and 256 complete Forwards, with 190 identity, histogram
and population checks. It contains no Sim residuals. GLM routing keeps the
complete retained ABI; Qwen groups retain their complete active-contract
populations without pretending representative samples establish a full ABI.
The 90 GLM COMMUNICATION AllReduce envelopes per Forward remain separate from
AI_CPU control tasks and may parameterize the same collective service boundary.
