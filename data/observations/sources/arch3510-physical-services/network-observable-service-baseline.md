# Conditional network service observations

The [network table](network-observable-service-baseline.json) retains **7 sources, 56 complete collective groups and 52,972 calls** from previously verified source-caller reports. It separates observed engine/native task/service from explicitly declared template, ranks, payload and topology. It contains no new cost or raw event parse.

| Hardware | Observed engine | Collective | Conditional template/ranks | Declared payload bytes |
|---|---|---|---|---|
| Ascend910_9362 | not directly identified | allgather | mesh / 8 | 57344 |
| Ascend910_9362 | not directly identified | reduce_scatter | mesh / 8 | 458752 |
| Ascend950DT_9582 | AIV | allgather | mesh / 4 | 16384, 262144, 524288 |
| Ascend950DT_9582 | AIV | allreduce | mesh_oneshot / 2 | 40960, 491520 |
| Ascend950DT_9582 | AIV | allreduce | mesh_twoshot / 2 | 3932160 |
| Ascend950DT_9582 | AIV | allreduce | mesh_twoshot / 4 | 65536, 1048576, 2097152 |

There are 20 groups in the source-declared 4–64 KiB band and 36 above it. Actual supported discrete small-payload points start at 16 KiB; **an exact 4 KiB measured payload and a measured UB_CLOS path are not present**. There is no fabricated interpolation through missing domains. A5 UB_MESH is a source-compatible topology condition, not a captured switch trace.

The table permits effective per-call or payload-regime service calibration. `declared_payload_bytes_per_observed_us` is expressly not independently measured pure-link bandwidth. A collective envelope, AIV device task and an unlinked AICPU controller are not summed to create another observation.

End-to-end elapsed does not uniquely decompose into switch-hop RTT, controller issue, notify polling, peer readiness and ingress queuing. The retained same-ABI Kimi c2 Combine slowdown and bounded V4.1 multi-rank phase-skew evidence are linked as constraints, without claiming causally measured incast. Receive packet arrival times and a measured peer payload matrix remain unavailable.

MC2 native/fused boundaries are listed separately in [the PMU baseline](mc2-observable-pmu-baseline.md); adding them to HCCL curves would mix different communication and compute scopes.

Reproduce: `python3 examples/structure/export_network_physical_services.py`. [Independent review](mc2-network-export-review.json) verifies the source pins, complete populations, measured/declared distinction and effective-service arithmetic.
