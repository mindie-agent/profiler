# Complete observed native services: A3 livepre

Both primary Body populations pass on Sim `f6e68d5e326ccbc6aade4f62fffbd816b23da500`.
This is in-sample calibration of complete native calls, not held-out validation
or an independently identified HBM/cache/instruction rate.

| Case | Forwards | Real mean ms | Sim ms | Error |
|---|---:|---:|---:|---:|
| c4 | 46 | 29.761551 | 29.545482 | -0.7260% |
| c16 | 37 | 41.069081 | 40.882155 | -0.4551% |

The same five source roles are declared in both cases: 90 HCPre, 90 HCPost,
42 fused grouped gate-up/activation/quantization, 42 grouped down and 11 sparse
attention calls. Every response is the mean of its complete retained integer
duration histogram. Both overestimated GMM/attention and underestimated HC are
calibrated; Body residuals and the passing threshold do not set any parameter.
Complete timing populations are established. Full-population native ABI,
compiled identity, group-list values and internal occupancy remain explicit
source conditions for these two captures.

One declared local service queue is shared by these five native domains. Sim
retains input/dependency ordering and queue contention. The replaced analytical
traffic/FLOPs remain reference work; their cold resource schedule does not run
alongside the observed whole call. This does not assign a measured L2 hit rate.
The c4 down completion floor is replaced by the joint rule; all existing
communication, convolution and recurrence declarations remain unchanged.

The two fresh predictions took 5.20 seconds in total; the largest worker used
80.06 MiB. They reuse 83 primary Forwards from 181 retained complete Forwards
across 17 geometries. Fifteen secondary populations stay deferred. No new
capture or kernel parsing ran. The original analytical/native-source replay
remains beside this directory, including the c16 failure.

Independent reviews verify 455 Body/layer/population checks and 231 parameter,
multiplicity and source-boundary checks, with zero failures. Compact predictions
save executed response/hit counts and analytical reference work; the review's
busy-ns quantity is derived from these values, not an exported Engine counter.
