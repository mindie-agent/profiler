# Observable service: Qwen3.6 TP2 and A3 cases

The first immutable replay contains Qwen3.6 TP2 c96, c12 and c1 on Sim
`2f48346b`. Each case uses the complete captured arithmetic mean for 48
CausalConv1d calls, 48 recurrent GDN calls and 128 HCCL calls per Forward.
Physical recipe, shape, state and collective payload/template fields select
the rules. The executed counters confirm all 224 calls matched exactly once.

| Case | Real mean ms | Sim ms | Error | 15% |
|---|---:|---:|---:|---|
| c96 | 63.853365 | 62.838292 | -1.590% | PASS |
| c12 | 24.225774 | 19.574902 | -19.198% | FAIL |
| c1 | 12.318284 | 9.006224 | -26.887% | FAIL |

These are **in-sample observable service parameters**. No Body residual,
target error, layer ID or model name determines a parameter. HCCL elapsed
includes protocol/peer wait and does not identify pure link bandwidth. The
public API applies an inclusive completion floor and preserves any larger
analytic work cost. Mixed TensorMove population is not assigned to one copy
role; other native mechanisms retain their existing declarations.

All 164 Forward samples and corrected layer populations are reused. Three
fresh workers completed; peak RSS 96,288,768 bytes. No capture parsing or
device workload was run. The existing replay driver rechecks capture hashes.
The saved checks cover 796 Body/layer arithmetic checks and 117 service,
source identity, full histogram and rule-count checks, all passing.

Reproduce from the profiler repository with the fixed 2f48346b checkout first
on `PYTHONPATH` and the Sim `.venv/bin/python`:

```sh
python examples/structure/build_qwen_a3_service_cases.py
python examples/structure/replay_decode_forwards.py \
  --manifest examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-qwen-service-cases.json \
  --output examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-qwen-service-replay.json \
  --geometry-limit 1 --prediction-timeout 90 --runtime-source-commit 2f48346b
```

## A3 complete-call responses

The separate `decode-forward-a3-service-replay.json` preserves all 1,209
Forward samples in 26 geometry groups. Eight primary groups (1,138 Forward
samples) execute fresh predictions; 18 smaller groups remain visibly deferred.

| Case | Real mean ms | Sim ms | Error | 15% |
|---|---:|---:|---:|---|
| Kimi4 c32 | 6.713782 | 5.972107 | -11.047% | PASS |
| Kimi4 c16 | 4.807080 | 4.173895 | -13.172% | PASS |
| Kimi4 c4 | 3.476353 | 3.195859 | -8.069% | PASS |
| Kimi4 c1 | 3.180250 | 3.237990 | +1.816% | PASS |
| GLM78 tpot88 c8 | 69.556298 | 55.528929 | -20.167% | FAIL |
| GLM78 tpot30 c2 | 57.639270 | 36.987368 | -35.830% | FAIL |
| GLM78 tpot50 c2 | 57.817112 | 36.987368 | -36.027% | FAIL |
| GLM Flash c4 | 29.761551 | 37.342291 | +25.472% | FAIL |

Kimi4 uses complete AG9/RS8/Conv3/KDA3/GMM-up3/GMM-down3 populations per
Forward. These are the A3 E896, EP8, top16, INT4/INT8 declarations, distinct
from the A5 E16 BF16 captures. Dynamic routed values remain unobserved; the
existing symmetric routing declaration is retained. Tensor buffer capacity
does not prove valid expert rows. Each selected physical rule hit its exact
declared call count.

GLM78 has complete retained HCCL statistics but no retained noncommunication
native family partition in this batch. Its 156 AllReduce means match, yet do
not alter Body latency because the analytic program already exceeds the
completion floor. The 75 observed AG calls have no corresponding declared
single-call boundary and remain unparameterized. MC2 envelopes are also not
assigned to transport-only programs while separate pack/unpack work remains.
GLM Flash retains the larger analytic costs, so the known overprediction is
not repaired by a nonnegative completion floor.

The standard saved-Body audit passed 1,338 checks. A separate agent verified
45,634 complete histogram, physical-selection, source-identity and executed
rule-count checks with no failures or new capture reads/costs. Eight workers
completed without resource failures; peak RSS was 135,921,664 bytes. Rebuild
this arm with `build_a3_observed_service_cases.py` and the same replay command,
using the A3 manifest/output filenames.
