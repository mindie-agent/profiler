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
