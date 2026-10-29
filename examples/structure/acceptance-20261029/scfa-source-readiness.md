# A3 SCFA source readiness at 26f5adb4

This is a focused conditional replay of two retained complete captures, using
sim `26f5adb48dd418584cd18c79d6a63ca8ab42afd7` and Python 3.13.12.
The [machine-readable evidence](scfa-source-readiness.json) records source,
case, graph and temporary artifact hashes. It adds no new capture and leaves
the [earlier descriptor-partition evidence](heterogeneous-sparse-coverage.md)
unchanged.

The source-selected program now runs with the independently declared A3 copy
supplies. It compares **141 of 292 SparseAttnSharedkv events**: V4Flash's 21
indexed events and V4Pro's 120 indexed events. There are two compared cohorts,
zero reference-only events and zero occurrence-bound events. Both cohorts
fail the 15% relative tolerance; a successful replay is not an accuracy pass.

| Capture | All sparse calls | Selected calls | Declared targets | Observed mean us | Predicted us | Difference us | Relative error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V4Flash | 44 | 21 | 21 | 3738.519 | 7037.371 | +3298.852 | +88.24% |
| V4Pro | 248 | 120 | 30 | 1180.346 | 835.600 | -344.746 | -29.21% |

The partition uses the actual optional index descriptor: input slot 4 is
`[4096,1,512] INT32 ND` for V4Flash and `[1024,1,1024] INT32 ND` for V4Pro.
V4Flash's other 23 calls are 20 CFA and 3 SWA calls. V4Pro retains 124 CFA
calls and 4 events whose compressed-cache descriptor is empty. These are not
assigned to SCFA, and no event is counted in multiple selected buckets.
Thirty declared V4Pro targets and 120 calls do not establish four complete
steps, particular layer occurrences, or the context of any call.

## Independent source conditions

The helper committed as `44d250e` clones the existing Case and adds only
`lowerings.sharedkv_attention`:

```json
{
  "implementation": "vllm_ascend_sharedkv_scfa",
  "options": {
    "owner_schedule": "one_query_per_core",
    "selected_rows": "valid_prefix",
    "sinks_dtype": "fp32",
    "metadata_s2_split": false,
    "return_softmax_lse": false,
    "scratch_policy": "offchip"
  }
}
```

The source family cites vllm-ascend
`175ef4d49c2072f9233619636f0309f4f88b4e2c`. Its selection applies to contiguous,
single-sequence prefill with a compressed-index producer. It does not select
SWA, CFA, decode or multiple-sequence programs. The declarations retain
context 0 and query counts 4096/1024 respectively. Descriptor compatibility
does not prove those scalar conditions, index values, captured dispatch or
the native binary revision.

## Actual supplies and service

Both cases resolve the same nominal analytical rates. The original explicit
device overrides remain active, including MTE3 at 2.4 TB/s.

| Resource | Aggregate supply | Owners |
| --- | ---: | ---: |
| Shared HBM | 1.2 TB/s | one shared resource |
| MTE1 | 4.224 TB/s | 20 AIC |
| MTE2 AIC | 1.056 TB/s | 20 AIC |
| MTE2 AIV | 2.112 TB/s | 40 AIV |
| Fixpipe | 4.224 TB/s | 20 AIC |
| MTE3 | 2.4 TB/s | 40 AIV |
| Vector | 8.448 T operations/s | 40 AIV |

These are source/profile declarations, not measured peaks or values fitted
to the observed errors. The profile records asc-devkit revision
`56500ea0dc219380f50f4a17ce73ef5264f830fc`, instruction-document hashes and
read-only CANN platform-file hashes. AIV's per-owner read supply and generic
Fixpipe-to-GM supply remain explicit analytical assumptions. The configured
1650 MHz clock differs from the platform file's 1500 MHz; the chosen
instruction MTE1 rates also differ from that file. The evidence retains both
discrepancies.

| Source-work diagnostic | V4Flash | V4Pro |
| --- | ---: | ---: |
| HBM bytes per call | 8,417,286,400 | 981,664,000 |
| HBM lower bound, us | 7014.405 | 818.053 |
| Prediction above HBM bound, us | 22.965 | 17.547 |
| HBM bound / prediction | 99.67% | 97.90% |
| Useful compressed rows over all queries | 1,572,352 | 130,816 |

The actual Engine service agrees with recomputed source Work within 0.01
resource units; fixed-owner copy bounds also stay below the shared-HBM bound.
The difference is therefore not explained by a missing split-copy supply or
by launch overhead in this declaration. V4Flash reaches 512 selected rows
and uses both gather AIVs, while V4Pro at context 0 reaches at most 256 and
does not use the second gather path.

For V4Flash, the declared offchip HBM lower bound already exceeds the observed
mean. That is a reason to revisit the unverified scratch/cache/index/scalar
conditions, not a basis for tuning the HBM rate. V4Pro's context-0 scenario
is compared with the complete retained event population: **835.600 versus
1180.346 us is a conditional population residual, not a verified same-context
error**. The independent run uses a 4096-token prompt and a 1024-token batch
limit; contexts 0/1024/2048/3072 are therefore useful separate declaration
scenarios. The event descriptors and counts do not establish those contexts
for individual calls, and this replay does not assign them by order or
timing. Scalar index response, page-table control,
invalid-index probes, local initialization, cross-core flag latency, cache
eviction, inner matrix overlap and local-buffer capacity remain unmodeled.

### V4Pro context sensitivity

Four subsequent single-program probes keep query 1024, the original Case,
source options and hardware supplies fixed, and independently declare context:

| Declared prior context | Source prediction, us |
| ---: | ---: |
| 0 | 835.600 |
| 1024 | 1813.126 |
| 2048 | 2908.730 |
| 3072 | 3762.680 |

These are scenario results, not four new cohorts. They do not replace the
main context-0 result, allocate any of the 120 observed calls, or contribute
weighted scores to the campaign. The retained population mean of 1180.346 us
does not identify an event's context. Each probe used one source program with
ready external inputs, no host submission and no raw scan; it took
1.737-3.407 s and peaked at 48,349,184-48,742,400 bytes. The JSON retains
the source geometry, serviced HBM and artifact hash for each scenario.

## Exported work and execution work

At this revision, `structure.py` prepares a source recipe when a fusion-group
key is present. Directly selected SCFA nodes lack that key, so exported
`physical_work_per_instance` still contains the generic semantic envelope:
HBM 1,687,681,024 / 152,304,640 bytes for V4Flash/V4Pro. Prediction executes
the selected `PlannedRecipe` and services the larger source ledger shown
above. The exported envelope must not be presented as the source program's
resource demand. The selected recipe and geometry remain in the physical
signature; no mixed-program cohort error was demonstrated in these two
homogeneous target sets.

The focused runs took 10.780 s / 5.505 s and peaked at
93,732,864 / 115,933,184 bytes. A subsequent source-Work-only audit took
0.349 s and 53,870,592 bytes; it did not scan raw data or predict again.
All focused artifact hashes and the recorded source hashes were checked.
The accuracy policy adds no floor to the prediction. The model's declared
device completion minimum and independent host launch cost are separate
concepts.

The campaign-wide results are maintained in
[the full family report](cohort-full-family-replay.md),
[the ranked error report](fusion-cohort-replay-top-errors.md) and
[the large-call report](fusion-cohort-large-call-errors.md).
This focused receipt does not claim that a concurrently running full campaign
has completed.
