# A3 retained network observations

`retained-a3-network-observations.json` preserves historical local measurements for the network modeling work. It contains **4 runs, 96 rank-specific payload/service points and 42 profiled collective envelopes** from 7 traces. It also links **25 TP8/TP16 model captures, 95 geometries, 2,510 complete Body forwards and 194,806 collective envelopes**. These populations are separate; the microbench runs are not additional model forwards.

Reproduce from the retained assets, without device work or cost prediction:

```bash
python3 examples/structure/export_arch22_network_observations.py
python3 examples/structure/fit_arch22_network_services.py
python3 -m pytest -q tests/test_arch22_network_observations.py
```

The exporter pins the input parents, traces and model ledgers. It reads one bounded JSON at a time; the recorded run used 183,517,184 bytes peak RSS. The model CSVs are not reread. Complete model histograms remain at their pinned ledger and exact JSON locator rather than being copied.

## Measured service curves

Successful captured `npu-smi` output identifies Phy-ID 4–5 as `SIO`, 4–6 as `HCCS_SW`, and the 4/5/6/7 submatrix as a mixture of those paths. The labels do not establish forwarding hop counts, every collective phase's route, or a general 8/16-device topology.

The following are rank 0 **unprofiled device-event batch duration / repetitions**, P50 in microseconds; each point has 25 samples. All ranks, means, P90 and single-call controls remain in the JSON. The two SIO runs are retained independently, including their difference at small payloads.

| Run | Ranks | 1 MiB | 4 MiB | 16 MiB | 64 MiB | 128 MiB |
|---|---:|---:|---:|---:|---:|---:|
| SIO c1, Phy-ID 4/5 | 2 | 103.064 | 109.095 | 168.938 | 618.057 | 1,243.055 |
| SIO c2, Phy-ID 4/5 | 2 | 137.339 | 132.591 | 172.250 | 625.673 | 1,257.420 |
| HCCS_SW, Phy-ID 4/6 | 2 | 117.933 | 124.268 | 194.283 | 698.580 | 1,371.490 |
| Mixed 4/5/6/7 | 4 | 113.451 | 169.011 | 201.088 | 581.055 | 1,088.560 |

These points are observable joint collective service within the retained protocol. A service curve may use them as in-sample observations with the rank, payload, repetition protocol and topology domain recorded. Dividing payload by time would yield effective collective throughput, not an independently identified physical link rate. No Body residual or target accuracy was used to produce them.

`retained-a3-joint-service-curves.json` fits `elapsed_us = joint_fixed_us + payload_bytes * us_per_byte` separately for each run, rank and collective. It contains 16 curves from 80 payload points; 16 single-payload controls are preserved as insufficient for a slope fit. Each domain has five distinct payloads, 1–128 MiB, with both mean and P50 fits. Dtype is checked against each captured rank's protocol. Signed intercepts, every residual, RMSE and maximum relative residual are reported unchanged. This is an in-sample joint response, not a unique switch-hop/notify decomposition or an 8/16-rank extrapolation.

Rank 0 mean fits illustrate the usable parameters and their limitations:

| Domain | Joint fixed us | Effective payload GB/s | RMSE us |
|---|---:|---:|---:|
| 2-rank SIO c1 AllReduce | 62.113 | 115.136 | 27.885 |
| 2-rank SIO c2 AllReduce | 87.378 | 115.334 | 33.774 |
| 2-rank HCCS_SW AllReduce | 81.383 | 104.845 | 18.461 |
| 4-rank mixed AllReduce | 108.654 | 137.975 | 19.750 |

The small-payload residuals remain visible: consumers should retain the measured knots when a single affine response is inadequate. The different effective rates include collective work and protocol effects; they are not physical link specifications.

## Phase evidence and limits

The instrumented traces report `RING-RING-NHR` and HCCL count/dtype for 4 MiB AllReduce. They contain ordered per-stream SDMA, notify, event and write-value tasks. All 6 exported envelopes per trace are preserved; the trace itself does not label which belong to warmup versus the three profiled calls named by the protocol.

Device tasks are associated by containment in the same trace's Communication envelope. A fabricated task-parent or host-stack relationship is never added. Crossing task counts are exposed. Phase activity sums may exceed envelope time because streams overlap; union is separate. For example, one retained SIO envelope is 969.34 us, contains 8 SDMA tasks totaling 56.10 us, and has overlapping notify waits totaling 969.20 us. Four notify-record SQEs report zero duration; that is recorded resolution, not proof of free instructions. These profiled intervals are **not** substituted for the unprofiled calibration points.

The 25 model sources provide measured whole-call service by complete source/geometry/attention/FFN/layer-population groups. TP8/TP16 are retained case declarations. Their physical card/die placement, algorithm, actual communication payload and child-phase association remain unknown. Adjacent tensor byte counters remain explicitly conditional and never become measured payload. AICPU controller wrappers are excluded from these collective service rows. Communication activity is not additive model Body latency.

Identified: whole collective elapsed service in an observed regime; historical two/four-rank path labels; trace task signatures and duration distributions. Not identified: per-switch-hop latency, a pure notify instruction price, exclusive cause of waits, or SIO/HCCS routing for each phase. Future decomposition can consume an explicit per-task route/correlation record when one exists; this evidence does not invent those values.
