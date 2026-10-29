# Kimi d911: expert collective setup dominates the positive program residual

The conditional DP4 × B1 model predicts 46.902 ms/body versus the retained 32.555 ms mean. Client concurrency one does not prove equal work on the other DP replicas.

| Boundary | Calls/forward | Measured activity ms/forward | Declared isolated service ms/forward | Of which setup | Signed activity residual |
| --- | ---: | ---: | ---: | ---: | ---: |
| MoeDistributeDispatchV3 / dispatch | 92 | 2.256722 | 14.264946 | 14.260000 | +12.008224 |
| MoeDistributeCombineV3 / combine | 92 | 1.347340 | 14.264946 | 14.260000 | +12.917606 |

The declared expert collective has `steps=31`, `setup_ms=0.155`, and 13,888 bytes per sending rank. Thus 31 × 5 µs of fixed setup dominates its 155.054 µs isolated duration. Across 92 MoE layers and dispatch plus combine, setup alone is 28.520 ms.

The next check is the native dispatch/combine protocol, startup rounds, overlap and active-peer assumptions. Do not fit link bandwidth to elapsed kernel times. These programs already exist in Sim and their costs must not be added again.

The source diagnostic prices representative KDA/MoE and MLA/MoE layers 1, 3, 89 and 91, then extends only exact physical-signature matches. It covers 2,483 of 4,636 declared rank-0 program occurrences. Its isolated service sums are not body wall time; the +24.926 ms communication activity residual is not an additive causal attribution of the +14.347 ms body difference.
