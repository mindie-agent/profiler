# Joint collective service parameters

These bounded parameters use the [retained network populations](network-observable-service-baseline.json). They can parameterize the same observable collective boundary. Payload, topology and template remain explicit source conditions; the intercept is a joint fixed service and the slope is a joint effective service rate.

| Physical domain | Payload bytes | Fixed µs | Effective GB/s | Maximum payload-mean residual µs | Status |
|---|---|---:|---:|---:|---|
| Ascend950DT_9582 AIV allreduce mesh_oneshot R2 | 40960, 491520 | 7.835349 | 13.664910 | 0.000000 | bounded_two_point_secant |
| Ascend950DT_9582 AIV allreduce mesh_twoshot R4 | 65536, 1048576, 2097152 | 25.624948 | 97.488878 | 0.228060 | joint_linear_fit |
| Ascend950DT_9582 AIV allreduce mesh_twoshot R2 | 3932160 | — | — | — | single_payload_observation |
| Ascend950DT_9582 AIV allgather mesh R4 | 16384, 262144, 524288 | 11.324448 | 26.026929 | 2.674666 | joint_linear_fit |
| Ascend910_9362 AICPU_TS allgather mesh R8 | 57344 | — | — | — | single_payload_observation |
| Ascend910_9362 AICPU_TS reduce_scatter mesh R8 | 458752 | — | — | — | single_payload_observation |

Distinct payload means are pooled using complete event counts, then weighted equally in OLS. The JSON retains every original group residual and within-payload range. In particular, first/steady or role-specific peer readiness may differ substantially at the same payload; these differences are not attributed solely to network throughput.

All fits are in-sample and bounded to their stated payload domains. The two-point secant is an exact interpolation only, with no independent third-point validation or extrapolation. Negative intercepts/slopes, if present, remain visible rather than clipped.

Reproduce: `python3 examples/structure/fit_network_joint_services.py`. No raw scan, device collection or Sim cost is run.
