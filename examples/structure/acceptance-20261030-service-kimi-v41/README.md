# A5 Kimi / V4.1 observable service replay

First accepted subset: [route-validated replay](decode-forward-route-validated-replay.json), **11/11 Body comparisons pass**, 1,013 retained complete forwards. These are in-sample comparisons: effective per-call service parameters and evaluation measurements share the same source capture. This result does not establish held-out generalization.

The active subset contains Kimi c16/c32 at both prompt contexts and all seven V4.1 sources. The subsequent Wave0 low-M arm below evaluates Kimi c1/c2/c4/c8 at both contexts with the known force-EPLB declared-work gap explicitly retained. Its new measurements are valid in-sample service comparisons, but do not establish source-policy closure. The input-only complete19 manifest is not a completed19 receipt.

## Parameters and boundary

`build_service_cases.py` reads only retained operator/cohort/native-reference observations. Every response is the complete matched population's weighted observed mean in microseconds; the source histograms/P50 remain in the retained observations. No prediction, body residual, or desired percentage error is a fitting input. A physically equivalent selector pools every retained bucket; in particular Kimi KDA keeps all 23 buckets, rather than its one representative node. The true 46-forward c32p4k population is 3,174 KDA calls; AttnRes has 8,602 calls and each MC2 direction has 4,232.

Rules select hardware, implementation/recipe, dtype, native kernel and exact physical local-shape coordinates. They do not select case IDs, operator IDs or layer numbers. The case/manifest fixes the evaluated attention context (Kimi 4,104/16,392; V4.1 2,048); no cross-context extrapolation is claimed. Dotted shape coordinates avoid the older whole-list/tuple matcher issue. Fresh structure serialization projects representative replica 0 only after binding the complete DP peer declaration; predictions still schedule the full declared cohort.

MC2 native response is applied once at the entry/exit boundary of its complete phase group. It is not added to every internal phase. The service is inclusive and a lower bound against the analytic program; it is not an added whole-body wait. HCCL service parameters retain same-boundary elapsed response including unseparated peer/protocol waiting; they are not pure-link bandwidth estimates or proof of a captured algorithm template. Conditional source-role and tensor-capacity/valid-row gaps remain explicit. Multi-program unfused MLA prolog references are omitted when they cannot be represented by one valid native boundary.

## Results

All cases used committed runtime `2f48346b` (276 package files, package fingerprint `e71d76a0e8fb32f59648503ffa653c55a08cf912e081941a4af9c62e61905a24`). No raw profiling event parse or new device collection occurred. The driver revalidated source hashes and reused the controller-corrected extraction.

| Source | Forwards | Real mean ms | Sim ms | Error | Worker seconds | Peak MiB | Prediction |
|---|---:|---:|---:|---:|---:|---:|---|
| a5_kimi_tp8_e16_bf16_c32_p4k | 46 | 40.018728 | 41.995725 | +4.94% | 14.84 | 145.25 | reused |
| a5_kimi_tp8_e16_bf16_c32_p16k | 41 | 44.666193 | 47.218681 | +5.71% | 33.07 | 144.69 | new |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 75 | 26.328226 | 24.811578 | -5.76% | 71.86 | 443.55 | reused |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 73 | 27.285973 | 25.539779 | -6.40% | 74.84 | 456.69 | reused |
| a5_kimi_tp8_e16_bf16_c16_p16k | 47 | 39.247386 | 40.763839 | +3.86% | 23.60 | 144.97 | new |
| a5_kimi_tp8_e16_bf16_c16_p4k | 49 | 36.985292 | 38.387860 | +3.79% | 12.95 | 145.17 | new |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | 129 | 14.929338 | 13.748800 | -7.91% | 83.83 | 441.62 | new |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | 105 | 18.624557 | 17.361229 | -6.78% | 60.65 | 428.20 | new |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | 151 | 13.238803 | 12.549524 | -5.21% | 46.47 | 434.08 | new |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 145 | 13.291562 | 12.155047 | -8.55% | 42.34 | 443.92 | new |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 152 | 13.134611 | 12.436061 | -5.32% | 43.68 | 436.88 | new |

The final queue took 349.46 seconds: eight new workers plus three exact case/runtime cache reuses. Worker peak was 456.69 MiB, with a 120-second per-prediction budget. The c128 and c64 V4.1 workers had already completed in 74.84 and 71.86 seconds and are reused with their original execution receipts. All 263 rules matched the expected full-DP invocation count; no declared rule was unmatched. V4.1 c8 retains its 82.349 ms measured outlier in the population.

[Independent retained-source review](route-validated-independent-review.json): **3,659 checks, zero failures**, 153.42 MiB. This independently reloads the original cohort/native/HCCL measurements and recomputes weighted means, input identities, invocation multiplicity, body statistics and pass arithmetic. `tests/test_observed_service_case_generation.py` adds two real-population checks for the 23 KDA buckets and one-response-per-MC2-group invariant.

## Execution history

- `decode-forward-priority-replay.json` is the completed exploratory four-source generation. Its Kimi KDA fitting population was incomplete and is superseded by the complete-population generation. Its two unchanged V4.1 case bytes remain valid cache inputs. Keep this historical report out of the current main scoreboard.
- `complete-replay.log` records an interrupted full19 attempt: the driver received SIGINT after c32p4k completed, while c32p16k was running, and exited 130. The owned child was verified exited; successful cache output was retained. This attempt did not produce a completed19 report.
- `decode-forward-route-validated-cases.json` and its matching replay are the formal safe11 generation. Kimi c32p4k reuses its exact completed result from the interrupted attempt. Other newly completed workers are recorded individually.
- `decode-forward-complete-cases.json` and `cases-complete-population/` retain prepared inputs for all19, including the eight deferred low-concurrency Kimi inputs. Those original prepared files were subsequently mounted into an independent current-runtime low-M arm with the routing limitation made explicit. A future source-policy correction must still regenerate physical work/domain rather than relabel this arm as source-closed.

## Reproduce

Run from the profiler repository with the declared Sim source on `PYTHONPATH`:

```sh
python examples/structure/acceptance-20261030-service-kimi-v41/build_service_cases.py
python examples/structure/replay_decode_forwards.py   --manifest examples/structure/acceptance-20261030-service-kimi-v41/decode-forward-route-validated-cases.json   --output examples/structure/acceptance-20261030-service-kimi-v41/decode-forward-route-validated-replay.json   --runtime-source-commit 2f48346b --prediction-timeout 120 --geometry-limit 1
python examples/structure/acceptance-20261030-service-kimi-v41/review_service_replay.py   --report examples/structure/acceptance-20261030-service-kimi-v41/decode-forward-route-validated-replay.json   --manifest examples/structure/acceptance-20261030-service-kimi-v41/decode-forward-route-validated-cases.json   --output examples/structure/acceptance-20261030-service-kimi-v41/route-validated-independent-review.json
```

The generator preserves original source IDs and pins every source/case/extraction identity. New arms use `variant_id`; they do not rename source populations or overwrite historical receipts.

## Wave0 low-M current-runtime arm

[Eight-source replay](decode-forward-low-m-3b72ea2d-replay.json) on `3b72ea2d`: **8/8 pass**, 435 complete forwards, 88.53 seconds and 147.77 MiB maximum worker RSS. All eight predictions are new executions. [Independent review](low-m-3b72ea2d-independent-review.json): 2,592 checks, zero failures, 145.86 MiB. No new raw parse, device capture or parameter fit occurred.

These cases reuse their own complete retained observation means; no high-c32 grouped rule is extrapolated. The generic declared expert rows remain `(4,4)` for rank0, while the source-compatible masked-cursor scenario produces `(1,0)`, `(2,0)`, `(3,1)`, `(5,3)` at c1/c2/c4/c8. The actual group-list values were not captured. `known_routing_work_gap` is carried by every case and result calibration/scenario metadata with `source_contract_closed=false`. Numerical pass does not close this known physical-work discrepancy.

| Source | Forwards | Real mean ms | Sim ms | Error |
|---|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c1_p16k | 59 | 30.823435 | 32.549560 | +5.60% |
| a5_kimi_tp8_e16_bf16_c1_p4k | 59 | 30.636854 | 32.359275 | +5.62% |
| a5_kimi_tp8_e16_bf16_c2_p16k | 54 | 33.875753 | 34.768187 | +2.63% |
| a5_kimi_tp8_e16_bf16_c2_p4k | 55 | 33.547630 | 34.418280 | +2.60% |
| a5_kimi_tp8_e16_bf16_c4_p16k | 52 | 34.816498 | 35.074433 | +0.74% |
| a5_kimi_tp8_e16_bf16_c4_p4k | 53 | 34.193709 | 34.461857 | +0.78% |
| a5_kimi_tp8_e16_bf16_c8_p16k | 51 | 35.964417 | 37.585296 | +4.51% |
| a5_kimi_tp8_e16_bf16_c8_p4k | 52 | 34.819213 | 36.421314 | +4.60% |
