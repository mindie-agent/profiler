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

## Qwen additional complete gating populations

`decode-forward-qwen-gating-service-replay.json` adds the complete saved
gating48, Q/K L2 normalization96 and output normalization48 call populations
for the requested c12/c1 follow-up. The Q/K mean is explicitly pooled; its
two identical physical source shapes do not establish direction-specific
latency. All seven rules hit the expected counts once. The first three-case
receipt remains immutable.

| Case | Real mean ms | Sim ms | Error | 15% |
|---|---:|---:|---:|---|
| c12 | 24.225774 | 20.323928 | -16.106% | FAIL |
| c1 | 12.318284 | 9.511835 | -22.783% | FAIL |

The complete sources contain no `_copy_conv_state_kernel` family. Their
mixed Slice populations cannot prove a sole convolution-copy latency, so no
copy rule was invented. These additional native populations are source-call
service observations, not new strict ABI mappings or heldout validation.
Reproduce with `build_qwen_gating_service_cases.py` and the corresponding
gating manifest. The standard saved-Body audit passed 532 checks.

## GLM78 newly retained native evidence and grouped-call arm

Three targeted local streaming passes reuse the accepted controller-corrected
Body windows and exactly revalidate their integer endpoints. They preserve
137 primary Forwards, 332,998 positive events and 185 full native ABI
partitions. No new Forward or device capture is created. Total parsing time
was 23.15 seconds; peak RSS 72,089,600 bytes. AI_CPU controller intervals
remain in the evidence inventory but are not assigned service rules or
added to HCCL tasks.

The native evidence shows INT8 cache rows of **656 bytes with rope64** for
KvQuantSparseFlashAttention, 78 calls/Forward, and MlaPrologV3 with 57 ordinary
plus 21 quantized-query-output occurrences. The existing BF16-cache prolog
and D528/rope0 attention implementations cannot represent this boundary.
No per-sequence response duplicates the observed whole-batch time.

The explicit `ascend_w4a8_msd` resource fusion does support the 75 fused
gate/up+SwiGLU+quant calls, accompanied by 75 grouped-down calls. The separate
`decode-forward-glm78-grouped-service-replay.json` executes these complete
means on runtime `3b72ea2d`, retaining the 156 prior AllReduce responses.
Fused semantic member launches are removed by the existing Sim lowering.
Observed buffer capacities (128/384 rows) do not identify dynamic valid
expert-row counts; the prior symmetric integer-routing declaration remains
visible and is not validated by the service fit.

| Case | Real mean ms | Sim ms | Error | 15% |
|---|---:|---:|---:|---|
| tpot88 c8 | 69.556298 | 55.152565 | -20.708% | FAIL |
| tpot30 c2 | 57.639270 | 37.652901 | -34.675% | FAIL |
| tpot50 c2 | 57.817112 | 37.655092 | -34.872% | FAIL |

All four rules per source hit exactly 78/78/75/75 invocations. All 162
captured Forwards and ten geometry groups remain in the report, with seven
smaller groups deferred. Three fresh workers completed within 134.02 MiB;
the standard saved-Body audit passed 999 checks. Selection follows the new
declared mechanism, including the slightly worse c8 result; no best-error
selection is used. Reproduce the evidence with
`collect_glm78_retained_native.py --case-id CASE`, then build with
`build_glm78_grouped_service_cases.py` and replay its matching manifest.

## Qwen complete-cohort response arm

The subsequent `decode-forward-qwen-cohort-service-replay.json` uses the
retained complete active-contract cohorts for seven matrix domains, two
separately identified Slice domains, SwiGlu and cache store. All candidate
contracts are rechecked against the current declared operators. The physical
rule selects precisely that candidate population, without using a layer or
operator ID. Parameters are the original full-population means; unchanged
prior rules remain in place.

This corrects the earlier omission of the independently retained
`Slice → convolution_input_contiguous` cohort, 48 calls/Forward. The remaining
mixed Slice population is still unassigned. Source names alone neither create
this mapping nor distinguish individual layers.

| Case | Real mean ms | Sim ms | Error | 15% |
|---|---:|---:|---:|---|
| c12 | 24.225774 | 21.480134 | -11.334% | PASS |
| c1 | 12.318284 | 10.718852 | -12.984% | PASS |

All 18 physical rules match their expected invocations exactly once. Two new
workers reused all 140 measured Forwards without parsing raw captures, with
peak RSS 87,851,008 bytes. The standard Body review passed 532 checks and the
separate producer histogram/parameter/hit review passed 276. These remain
in-sample service observations; the complete active contract does not prove
the native tiling ABI. Existing rank and context assumptions remain explicit.
Reproduce with `build_qwen_cohort_service_cases.py`, followed by the matching
cohort manifest and output on runtime `3b72ea2d`. Earlier failed receipts are
retained. No parameter was assigned from the Body residual or chosen to land
at the 15% threshold.

## GLM78 D656 source program arm

`decode-forward-glm78-packed-source-replay.json` uses runtime `a961c114`
and the new explicit packed representation: 512 INT8 latent bytes, 64 BF16
rotary values and four FP32 scales, for 656 bytes per cache row. The existing
Sim expansion/fusion produces 78 complete prolog calls (57 ordinary and 21
quantized-query-output variants) and 78 whole-batch sparse attention calls.
The prior four AR/grouped service rules are preserved unchanged; **no new
prolog or sparse-attention empirical response is added** in this arm.

| Case | Real mean ms | Sim ms | Error | Body 15% | Layer pass |
|---|---:|---:|---:|---|---:|
| tpot88 c8 | 69.556298 | 77.592182 | +11.553% | PASS | 77/78 |
| tpot30 c2 | 57.639270 | 42.003352 | −27.127% | FAIL | 0/78 |
| tpot50 c2 | 57.817112 | 42.005543 | −27.348% | FAIL | 0/78 |

c8's captured and declared prolog have M48. The two c2 captures have M12,
while the unchanged graph-mode declaration produces M16 prolog work. That
active-contract discrepancy remains explicit in the cases, preflight and
comparison assumptions; it is not counted as an exact native binding or
hidden by assigning an M12 response to M16 work. Sparse attention retains
all B sequences in one call. Captured binary identity and per-step valid
context lengths remain unestablished; context4096 is the preserved input
condition. The raw captured populations are unchanged.

Three fresh workers took 5.61/4.82/4.85 seconds, at most 113,852,416 bytes RSS.
All four prior rules hit 78/78/75/75 calls. The standard Body/layer review
passed 999 checks, and the separate preserved-input/whole-call boundary
review passed 90 checks. All 162 complete forwards and ten geometries remain,
including seven deferred groups. Reproduce with
`build_glm78_packed_source_cases.py`, then replay the matching packed-source
manifest with `--geometry-limit 1` on the pinned runtime. No CSV reread or
new device work is required.


## GLM78 captured grid and complete native response arm

Runtime `672a595f` preserves the existing whole-model declarations but supplies
capture keys `[12]` for c2 and `[48]` for c8, using all retained prolog/query
shapes as the input evidence. The prior case omitted 12 from its explicit
capture grid, so selecting 16 was the declared GraphPolicy behavior, not a
runtime leak. The earlier M16 results remain immutable counterexamples.

`decode-forward-glm78-captured-grid-replay.json` first preserves the old four
response selectors byte-for-byte. c8 remains 77.592182 ms (+11.553%, PASS).
Both c2 predictions are 37.850900 ms (−34.331%/−34.533%, FAIL): their old M16
selectors correctly register **zero hits** under M12. This attempted input
change is retained rather than overwritten or counted as calibrated.

`decode-forward-glm78-native-service-replay.json` rebinds the same four
complete AR/grouped populations to fresh M12 physical axes, preserving every
observed mean. It additionally selects the existing INT32 shared gate/up
lowering and verifies both the native INT32 accumulator and DSQ output
contracts. Twelve new rules per source use the exact complete populations:
255 QBMM, 78 transpose-matmul, 75 DSQ, 81 dynamic quant, 21 layer norm and
three SwiGLU calls per Forward. Every one of the 16 rules hits its declared
population. No kernel name supplies a layer binding; the physical rule
contains shape/precision/recipe axes and no model or layer identifier.

| Case | Real mean ms | Sim ms | Error | Result |
|---|---:|---:|---:|---|
| tpot30 c2 | 57.639270 | 42.447117 | −26.357% | FAIL |
| tpot50 c2 | 57.817112 | 42.454402 | −26.571% | FAIL |

This is an in-sample observed-service assignment, using full integer duration
histograms and no Body residual. It remains a whole-call floor, so a larger
analytic program is not reduced. Native dynamic expert valid rows remain
unknown; buffer capacities are not treated as valid routing counts. Both
workers are fresh, with at most 111,919,104 bytes RSS. Standard Body/layer
checks passed 654/654; independent parameter/population checks passed 234/234.

Remaining source gaps are explicit: FFN and router Concat pad M12 to M16,
and 75 native AllGathers have no matching declared caller node. The native
router is BF16 operands with FP32 output while the existing declaration uses
FP32 operands. Generic norm-quant fusion would also combine 60 calls, whereas
the capture has only three fused dense-FFN calls; it cannot be enabled globally
as a substitute. Their activities are diagnostic populations, not addable
contributions to the Body wall span. No additional SFA/prolog empirical floor
has been assigned. Reproduce the grid arm with
`build_glm78_packed_source_cases.py --captured-grid`, then the native arm with
`build_glm78_native_service_cases.py`; both reuse the retained local evidence.
