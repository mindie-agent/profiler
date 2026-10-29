# Complete family and physical-cohort replay

The final 2026-10-29 replay reuses **eight complete A3/A5 captures, 668,835
positive-duration events and 148 native types**. Eleven phase/configuration
declarations produce fifteen variants. Kimi's four declarations reuse one
capture; their event totals are not independent hardware evidence. No new NPU
workload was launched.

There is no `COMPARE_TYPES` allowlist. Every valid tensor/physical-work cohort
enters `compare_cohorts`; all native types remain visible in the complete family
tables. Each distinct physical program has its own 120-second budget.

## Complete replay results

| Capture / declaration variant | Cohort events | Scored events | Reference events | Compared / reference cohorts |
| --- | ---: | ---: | ---: | ---: |
| a3_glm53_prefill / source_declared_unfused_reference | 1,076 | 752 | 324 | 16 / 6 |
| a3_glm53_prefill / selected_native_fusion | 1,076 | 1,001 | 75 | 21 / 1 |
| a3_glm53_decode / source_declared_unfused_reference | 79,624 | 55,648 | 23,976 | 16 / 6 |
| a3_glm53_decode / selected_native_fusion | 79,624 | 74,074 | 5,550 | 21 / 1 |
| a3_qwen35 / case_default | 3,442 | 762 | 2,680 | 14 / 1 |
| a3_qwen36 / case_default | 1,330 | 1,330 | 0 | 15 / 0 |
| a3_v4f / case_default | 772 | 619 | 153 | 15 / 3 |
| a3_v4f / selected_native_fusion | 772 | 707 | 65 | 16 / 2 |
| a3_v4pro / case_default | 4,336 | 3,472 | 864 | 14 / 3 |
| a3_v4pro / selected_native_fusion | 4,336 | 3,968 | 368 | 15 / 2 |
| a5_kimi_k3 / case_default | 439 | 439 | 0 | 3 / 0 |
| a5_kimi_k3_decode / source_declared_unfused_reference | 10,703 | 10,703 | 0 | 5 / 0 |
| a5_kimi_k3_checkpoint / current_checkpoint_conditional | 10,025 | 2,023 | 8,002 | 9 / 3 |
| a5_kimi_k3_decode_checkpoint / current_checkpoint_conditional | 66,328 | 43,469 | 22,859 | 8 / 4 |
| a5_qwen38 / case_default | 989 | 989 | 0 | 22 / 0 |

All **210 compared cohorts and 32 reference cohorts** completed without failed
programs. These counts include repeated declarations. Thirty-eight native types
produce cohorts, thirty-four have scored comparisons, and ten have references;
the latter sets overlap. All event occurrences remain unbound: cohort
reconciliation does not invent a layer, replica or step identity.

The [Top family/subgraph table](fusion-cohort-replay-top-errors.md) separates
scored and reference events, full activity denominators and remaining reasons.
Its [JSON index](fusion-cohort-replay-families.json) links all fifteen complete
family tables. Activity sums include overlapping events and are not model
wall-clock time. The [independent review](fusion-cohort-independent-review.json)
checks 33,245 artifact/identity/arithmetic conditions. That review does not
rescan raw P50 or interval unions; it checks consistency across saved artifacts.

The [refreshed inventory](fusion-coverage-inventory.md) uses exact saved cases
and fresh graph identities. Of 59 required model-body types, 51 have a declared
native boundary, 49 have a complete boundary, 37 have a comparable contract,
and 35 match a retained original fixture row. These evidence levels do not
establish captured layer occurrences. Fixture registration contains 798 unique
original records; overlapping retained Kimi source lines are deduplicated.

## Kimi: zero cohort fixed, remaining boundaries visible

Unbound semantic recipe names now resolve to the actual selected physical
program. Explicit implementation bindings, real resource work and dependencies
remain distinct. Source MSD metadata also normalizes only known member
occurrence IDs; it retains member order, recipe, family and shape.

A complete symmetric DP candidate set can produce single-device statistics while
keeping `replica=null`, every candidate ID and the possible replicas. The
per-device declaration count is used for multiplicity; observed totals are not
multiplied by DP4. No rank-to-replica or layer occurrence is inferred.

The old decode rejection of **8,771 physical-signature events and 1,932 placement
events** is gone. The baseline decode declaration now scores 10,703 events,
including 8,838 MatMulV3 events. The checkpoint variants retain independent
current-checkpoint precision metadata; only the config hash is known to match
the historical campaign. The historical quant-description hash and dispatch
identity remain unavailable.

| Native head | Baseline prefill scored / reference | Baseline decode scored / reference | Checkpoint prefill scored / reference | Checkpoint decode scored / reference |
| --- | ---: | ---: | ---: | ---: |
| MatMulV3 | 163 / 0 | 8,838 / 0 | 163 / 0 | 8,838 / 0 |
| GroupedMatmul | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| GroupedMatmulSituQuant | 0 / 0 | 0 / 0 | 0 / 7,266 | 0 / 7,266 |
| SituMxQuant | 0 / 0 | 0 / 0 | 368 / 0 | 6,898 / 0 |
| QuantBatchMatmulV4 | 0 / 0 | 0 / 0 | 0 / 736 | 0 / 13,795 |

GroupedSiTU and V4 retain positive reference costs, but their incomplete native
MXFP4 conversion/scale/matrix program does not receive a full-kernel error score.
The same 7,266 GroupedSiTU events in two phase declarations must not be counted
twice as additional coverage.

All 27,248 remaining GroupedMatmul events have parseable contracts. One complete
streaming audit separates **19,982 single-bank events** whose group-list semantics
are not established by an independent dense wrapper, and **7,266 28-bank expert
down events** whose captured allocation M differs from declared routed work.
Group-list values and effective rows are not captured. Tensor allocation and
padding cannot substitute for an independently declared runtime workload.
See [Kimi source and branch evidence](kimi-native-matrix-evidence.md).

## HC and GLM conditional errors

HcPre reuses the same L1 X panel for source projection and Gram work, removing
the erroneous independent full-X HBM reduction. Real cast/partial/output traffic
and launch/dependency boundaries remain. HcPost includes its source conversions
and dependent phases. No L2 residency is inferred from a workspace fitting.

| Selected HC program | Old error | Final error | Final predicted mean ms | Measured mean ms |
| --- | ---: | ---: | ---: | ---: |
| V4F HcPre | +114.51% | +67.20% | 0.721545 | 0.431534 |
| V4Pro HcPre | +111.88% | +64.99% | 0.316457 | 0.191803 |
| V4F HcPost | -39.78% | -28.93% | 0.297336 | 0.418375 |
| V4Pro HcPost | -45.49% | -35.80% | 0.129751 | 0.202098 |

The GLM selected case uses source MSD gate/up and down programs, balanced integer
routing and independently declared nominal INT4 supply. Norm-bias, MLA/indexer
and `steady_matmul` choices are explicit. These are conditional declarations,
not proof of the captured expert histogram, cache placement or native dispatch.
Generic single-launch fusion now inherits incomplete member costs; only a
complete selected source program removes its implemented epilogue gaps.

| GLM selected family | Prefill scored events / error | Decode scored events / error |
| --- | ---: | ---: |
| GroupedMatmulSwigluQuantV2 | 75 / -3.57% | 5,550 / -87.78% |
| GroupedMatmul down | 75 / +54.59% | 5,550 / -88.37% |
| MlaPrologV3 | 78 / -64.56% | 5,772 / -55.32% |
| AddRmsNormBias | 153 / -32.30% | 11,322 / -98.45% |
| AddRmsNormDynamicQuant | 3 / -44.69% | 222 / -98.81% |

Only the prefill MSD gate/up result is within 15%. Old up/down entries were
references without a score, so this is new comparison coverage, not a proved
accuracy improvement over an old score. Norm-bias predictions are unchanged;
MLA/W8 differences also include the newly selected matrix program. GLM sparse
attention still has -53.63%/-97.81% prefill/decode error, and A5 Qwen3.8 V3
matrix cohorts have +75.47% error. This is not full-model accuracy acceptance.

## Verification and reproduction

[Final batch validation](fusion-cohort-validation.json) reports `completed`,
unchanged runtime hashes, unchanged capture identities, no failed programs,
and **626.158 seconds** elapsed. Eleven serial raw scans keep
Kimi phase/configuration variants separate. Peak mapping RSS is
**467,206,144 bytes (445.56 MiB)**;
peak comparison RSS is **469,614,592 bytes
(447.86 MiB)**. Both pass the 512 MiB budget.

The earlier 549.05 MiB checkpoint mapping attempt failed its budget gate.
Streaming canonical graph hashing removes the complete JSON/UTF8 temporary
copies; graph IDs and full mapping content remain identical. The final result
above is a fresh complete replay after that repair, not the failed receipt.

[Maintained-suite verification](cohort-verification.json) records the same
runtime-source identity: profiler **527 passed, 26 skipped (24.83s)**;
sim **1,444 passed (224.80s)**. Skipped live tests and historical replay do not
constitute a newly executed hardware workload. All fresh graph checks and tests
use **CPython 3.13.12** from the sim environment.

```bash
PYTHONPATH=/path/to/sim-rewrite:/path/to/profiler /path/to/sim-rewrite/.venv/bin/python \
  examples/structure/replay_fusion_cohorts.py --run
```

`--compare-existing --run` reuses saved mappings and cases but still requires the
same graph identity. Changed declarations require remapping. Inventory refresh
uses `examples/structure/refresh_fusion_inventory.py` and does not rescan raw
captures.

A separate inventory refresh verifies 24 graphs (15 replay variants and nine
default declarations) in fresh serial workers. Maximum worker RSS is
441.44 MiB and parent RSS is 57.70 MiB, both within budget. This replaces the
earlier 629.08 MiB single-process refresh; all graph IDs and coverage results
remain identical. Inventory refresh does not rerun the raw captures.

A pre-existing cross-version routing sensitivity remains separate: for V4 Pro's
uniform 384-expert/top-6/EP16/1,024-token declaration, `RoutingPolicy.local`
produces `384.00000000000045` on CPython 3.11.13 and
`383.99999999999653` on 3.13.12; downstream `ceil` yields 385 versus 384 rows.
This replay attests the stated 3.13.12 environment, not cross-version graph
identity. No capture or declaration was altered to hide that difference.
