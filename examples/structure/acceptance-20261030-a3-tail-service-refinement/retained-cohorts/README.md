# Seven A3 retained-population service replays

This arm reuses controller-corrected Forward windows, complete typed HCCL populations and available complete operator cohorts. Every newly mapped active contract is checked against fresh Sim nodes. The whole native histogram sets its arithmetic mean; the Body residual and old prediction never set a parameter. Existing service rules remain byte-for-byte unchanged.

| Source | Real mean ms | Sim ms | Error |
|---|---:|---:|---:|
| GLM dc16k b1 | 39.112085 | 33.636900 | −13.9987% |
| GLM dc4k b1 | 38.954827 | 33.636900 | −13.6515% |
| GLM dc4k b2 | 40.969878 | 35.482501 | −13.3937% |
| Kimi four-layer c32 | 6.713782 | 6.063596 | −9.6843% |
| Kimi four-layer c64 | 9.615404 | 8.639061 | −10.1539% |
| GLM Flash c2 | 34.118460 | 30.600588 | −10.3108% |
| V4Flash c4 | 32.485961 | 29.272304 | −9.8924% |

All seven pass the unchanged 15% Body criterion. Two meet the 10% refinement goal. Seven fresh workers use Sim `21c30821d87a757bace8cf6b2fffea2536db643e`; maximum child RSS is 103,137,280 bytes. The full source denominator is 820 Forwards / 20 geometry groups; 784 primary Forwards are compared, and 13 smaller groups remain deferred. There are no raw scans or device runs. The standard independent Body review passes 1,445 checks.

Kimi c32/c64, Flash c2 and V4Flash c4 add 15/17/18/10 physical response domains respectively. All 60 rules have exactly the declared invocation count in the actual Engine query receipt. Complete contract cohorts spanning several physical variants use the same observed population mean, with this pooling explicitly declared; separate variant timings are not invented. Collective responses include native protocol and peer wait. They do not identify pure link bandwidth, and rank-2/rank-4 network curves are not extrapolated to TP8/TP16.

The three old GLM cases receive **no new rules**. Their actual HCCL population is 156 AllReduce calls per Forward, while the source declaration expands to 78 attention reductions, 78 FFN reductions and 75 additional expert reductions. That 231-versus-156 difference remains a visible caller-contract gap. The fresh values are identical to the older values; this is a runtime revalidation, not claimed calibration progress. No complete Body-level native operator table exists for these three sources, so another source's operator population is not substituted.

Unsupported or ambiguous populations stay in `unassigned_populations`: changed HC resource boundaries, physical selectors admitting more than the observed cohort, or mismatched declared multiplicity. Those calls are never extrapolated from two examples. Existing all-rank symmetry, routing and source implementation assumptions remain attached to the Body comparisons.

Reproduce the preparation with `build_a3_tail_cohort_service_cases.py` and the prediction with:

```sh
PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:.:examples/structure \
  /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
  examples/structure/replay_decode_forwards.py \
  --manifest examples/structure/acceptance-20261030-a3-tail-service-refinement/retained-cohorts/decode-forward-retained-cohort-cases.json \
  --output examples/structure/acceptance-20261030-a3-tail-service-refinement/retained-cohorts/decode-forward-retained-cohort-replay.json \
  --geometry-limit 1 --prediction-timeout 90 \
  --runtime-source-commit 21c30821d87a757bace8cf6b2fffea2536db643e
```
