# Qwen3.5 TP4 MC2 caller: three-case incremental replay

Only the requested c4/c64/c128 captures were re-evaluated. These Body receipts
use Sim `bf71bd7d8d0c676165886c84baa22e97d0f1a68f` and the complete caller cases
from `91aeb533`. No unrelated source was re-predicted and no NPU work was started.

| Concurrency | Complete primary forwards | Real Body mean ms | Sim Body ms | Error | Layer passes |
|---|---:|---:|---:|---:|---:|
| 4 | 84 | 11.551367 | 4.705846 | -59.26% | 0/40 |
| 64 | 79 | 21.956845 | 11.723498 | -46.61% | 0/40 |
| 128 | 76 | 28.584774 | 16.621713 | -41.85% | 0/40 |

All three predictions completed; none meets the 15% Body tolerance. The complete
extraction retains 286 forwards across 40 geometries. Only the three requested
primary populations (239 forwards) receive new predictions; the other 37
geometries are explicitly deferred, not execution failures.

The typed chain preserves full router/shared rows, TP-local selection, INT8
receiver payload and FP32 per-row scales, INT32 expert-up output, and
DequantSwigluQuant-owned scales consumed by expert-down. Each forward declares
40 AllGather and 80 AllReduce calls. At c128, 160 FFN post-gather copies are
separate from the 60 observed attention copies. The independent checks are in
[`../acceptance-20261030-qwen35-mc2-tp-independent/`](../acceptance-20261030-qwen35-mc2-tp-independent/).

The [full replay](decode-forward-qwen35-mc2-tp-replay.md) includes layer,
attention-structure, activity-union and layer-0 comparisons. The
[runtime delta](body-runtime-delta.md) uses identical observed populations;
it does not attribute a multi-change arm to one commit. c64/c128 predictions
increase by 0.782/1.777 ms, while c4 decreases by 0.662 ms.

Fresh operator references use a separately identified runtime with the native
TensorMove contract and fusion-origin export repairs. They are stored in
[`../acceptance-20261030-qwen35-source-complete/`](../acceptance-20261030-qwen35-source-complete/).
The Body receipts here remain immutable. Buffer capacity is not a measured
active routed-row count, and isolated operator activity is not additive Body
latency. The [residual ledger](../acceptance-20261030-residual-mechanisms/README.md)
retains its explicitly requested `9f10558` baseline.
