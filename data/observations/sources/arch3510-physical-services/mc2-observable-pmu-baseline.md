# MC2 scalar / DMA / wait observations

The [baseline](mc2-observable-pmu-baseline.json) projects the previously accepted 66-capture communication ledgers. It includes **46 sources, 710 native groups, 327,288 calls**. No CSV was reparsed and no device or Sim cost was run. Each row links the exact source/body SHA and retained group path; different execution geometries, layer kinds, first/steady layers and fused boundaries remain separate.

| Hardware | Native boundary | Calls |
|---|---|---:|
| Ascend910_9362 | DispatchFFNCombine | 15360 |
| Ascend910_9362 | MoeDistributeCombineV2 | 48672 |
| Ascend910_9362 | MoeDistributeDispatchV2 | 48672 |
| Ascend950DT_9582 | MoeDistributeCombineV3 | 107292 |
| Ascend950DT_9582 | MoeDistributeDispatchV3 | 107292 |

The PMU table preserves scalar, vector, MTE, cycle and task-wait statistics together with numeric, missing and zero denominators. AIC/AIV scalar-wait columns are absent in this population. Most ordinary PMU fields contain 327,200 numeric calls and 88 unavailable calls; the per-field table reports exact coverage instead of filling missing values with zero. Older retained schema omits duration/wait PMU projection for some groups, while complete native duration histograms remain available.

These values are usable same-boundary service observations. They do not independently price scalar UB/GM reads, scalar spin loops or SyncAll. Block Num is launch geometry rather than a measured count of active owners. Marginal per-field histograms do not preserve event-wise pipeline overlap, so subtracting the maximum pipeline value from wall time is not a measured synchronization component. `Wait Time(us)` is retained task-wait metadata and is not relabeled as scalar or network wait.

The next source-price join needs the exact instruction-count/owner program identity for each group and independent variation that separates issue, memory and polling. Counted source instructions alone plus whole-call elapsed do not identify all those rates. No new rate is written to Sim by this export.

Export: 2.214s, 176.92 MiB. [Independent review](mc2-network-export-review.json): 73,003 field/population checks, zero failures, 193.45 MiB, zero raw reads/cost.

Reproduce from profiler: `python3 examples/structure/export_mc2_physical_services.py` and `python3 examples/structure/review_physical_service_exports.py`.
