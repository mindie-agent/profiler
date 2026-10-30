# GLM78 A3: complete local-native joint service

This arm changes only SFA and grouped up/down from analytic/lower-bound execution to an explicitly declared native service queue. The complete integer timing histograms supply each inclusive native-call mean. The two c2 sources share exactly the same full ABI, Block 20 / Mix 40 and physical domain, so their histograms are pooled before calculating the parameter. No Body residual enters the parameters.

| Source | Real Body mean ms | Sim ms | Error | Body | Layers passed |
|---|---:|---:|---:|---|---:|
| tpot30 c2 | 57.639270 | 49.285701 | −14.492842% | PASS | 42/78 |
| tpot50 c2 | 57.817112 | 49.291155 | −14.746424% | PASS | 35/78 |
| tpot88 c8 | 69.556298 | 67.838121 | −2.470196% | PASS | 78/78 |

The unchanged controller-corrected capture population contains 162 complete Forwards in 10 geometry buckets. The three primary buckets contain 137 Forwards; seven smaller buckets remain explicitly deferred. Three fresh workers completed in 11.43 seconds total, with a maximum child RSS of 115,179,520 bytes. No capture was scanned and no device workload was launched.

Each Forward actually executes 78 SFA, 75 grouped up and 75 grouped down joint services. `parameters.joint_native_services` retains these invocation counts and the unexecuted `analytical_reference_work`. The declared `joint_native_a3` queue uses `busy_ns`, one resource unit, and a reference rate of 1e9. It does not identify HBM bandwidth, L2 hit rate, or exclusive per-pipeline occupancy. Native startup/tail are included once in the full-call response.

All other response rules, dependencies, geometry, and source-caller declarations are retained. This arm does **not** enable the new native MC2 V2 caller. Existing generic MC2 transport, routing assumptions, and unknown expert group-list values remain visible; Body PASS does not imply complete native-contract coverage or every layer passing. Calibration is `observed` / `in_sample`, and is not a held-out accuracy result.

Sim source commit: `f6e68d5e326ccbc6aade4f62fffbd816b23da500`. The selected 288-file package SHA is `9f88dac92812c58accec2c6416daa0ea181bd7e5d27b43d9046d1e843b7bfe10`.

From the profiler repository, using the fixed checkout at that commit:

```sh
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/build_glm78_joint_service_cases.py
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/replay_decode_forwards.py \
  --manifest examples/structure/acceptance-20261030-glm78-joint-service/decode-forward-glm78-joint-service-cases.json \
  --output examples/structure/acceptance-20261030-glm78-joint-service/decode-forward-glm78-joint-service-replay.json \
  --geometry-limit 1 --prediction-timeout 90 \
  --runtime-source-commit f6e68d5e326ccbc6aade4f62fffbd816b23da500
```

The preceding caller-complete arm remains immutable in `acceptance-20261030-service-qwen-a3/`; its three failed accuracy results are not replaced or hidden. Standard saved-source arithmetic review passed 999 checks. The separate parameter audit checks complete populations, source/domain pooling, rule hits and retained analytic-reference work.
