# Decode Body replay at Sim 5ec8843a

The five family manifests reuse all 66 source captures and unchanged case bytes from the previous `30dcea1e` source-complete campaign. No raw CSV was reread or new hardware workload started. The fixed checkout was `/Volumes/data-tmp/tmp/mindie-sim-cohort-wave6-20261029` at `5ec8843a7e1711d0333dd59f9aec4f19f4f40363`; the executable package SHA was `c8393b666a67919c06c6929112c49eeef8519c4a757e486c59d63938c8db79e9`.

All 66 primary geometries were attempted: **65 completed, 21 passed, one failed the memory budget**. All 5,250 accepted Body forwards and 222 observed geometries remain in the receipts; the other 156 geometries remain explicitly deferred. Successful predictions cover 4,599 primary forwards. The successful worker peak was 440.72 MiB. The failed old Kimi p32k attempt used 521.45 MiB in 33.79 seconds. Its diagnostic prediction of 28.56058 ms is retained but is excluded from Body and layer accuracy. The previous campaign had 22 passes; the reduction is a resource failure, not a newly failing numerical comparison.

| Family | Sources attempted | Completed | Body passes | Failed |
|---|---:|---:|---:|---:|
| GLM | 26 | 26 | 12 | 0 |
| Kimi TP8 p4k/p16k | 12 | 12 | 0 | 0 |
| Qwen A5 | 6 | 6 | 0 | 0 |
| V4.1 A5 existing declarations | 7 | 7 | 0 | 0 |
| Other retained priority sources | 15 | 14 | 9 | 1 |

[The runtime delta](body-runtime-delta.md) compares the same populations and explicitly includes the new failed attempt. Kimi c32 p16k increases by 3.2598 ms under the corrected MLA sequencing, reducing its error to −24.48%; this still fails the 15% Body criterion. GLM and Qwen do not gain passes merely by refreshing runtime identity.

The five independent reviews pass 15,601 population, endpoint and arithmetic checks. A passing review verifies the report's honesty; `remaining-independent-review.json` explicitly retains its input execution status as failed. The reviewer now permits a rejected diagnostic prediction to remain visible while requiring its scored prediction, error, pass flag and layer comparisons to be absent. A regression backed by this real memory failure also verifies that an incorrectly promoted pass is rejected.

`decode-forward-v41-composed-cases.json` records the seven explicit composed MX32/HC/prepared-matrix inputs separately. It is an input manifest, **not a completed Body replay**. The preceding Sim campaign already exposed excessive full-cost memory, and the c32 strict-cohort attempt at this runtime also exceeded 512 MiB. The successful projected native-reference campaign is recorded separately in `../acceptance-20261030-v41-composed-native-5ec8843a/`; it does not establish full-Body resource acceptance. These failures have been sent to the Sim owner for a cost-path memory repair before expanding that campaign.

Reproduction: run `replay_decode_forwards.py` with each family case manifest, `--geometry-limit 1 --prediction-timeout 90`, the exact runtime revision and a new runtime-specific prediction cache. Then run `review_decode_predictions.py` on each replay and `compare_body_runtime_arms.py` against the five previous source-complete reports. Per-family logs preserve execution progress and the nonzero return code for the failed campaign.
