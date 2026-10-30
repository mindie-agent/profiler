# Bounded Body recovery and explicit V4.1 composition

Sim `ec58ce7921583967a50e803c78b962d90f8273b0` was used for eight incremental predictions over unchanged retained captures. Seven V4.1 inputs explicitly select the composed MX32 communication, prepared matrix and arch35 HC programs; the old Kimi p32k input is unchanged. All eight complete within the original 90-second / 512-MiB worker budget, with a maximum of 70.83 seconds / 436.94 MiB. No raw capture was reread. The four independent reviews pass 1,572 population and arithmetic checks.

| Case | Real Body mean ms | Sim Body ms | Error |
|---|---:|---:|---:|
| V4.1 c1 | 13.135 | 7.430 | −43.43% |
| V4.1 c4 | 13.239 | 7.430 | −43.88% |
| V4.1 c8 | 13.292 | 7.430 | −44.10% |
| V4.1 c16 | 14.929 | 9.078 | −39.19% |
| V4.1 c32 | 18.625 | 12.361 | −33.63% |
| V4.1 c64 | 26.328 | 18.933 | −28.09% |
| V4.1 c128 | 27.286 | 19.245 | −29.47% |
| Old Kimi p32k c1 | 32.555 | 28.561 | −12.27% |

The V4.1 resource issue is fixed for full-Body prediction, but all seven composed conditions still fail the 15% accuracy criterion. The latest explicit declarations are retained even though their errors are larger than the previous declarations; inputs are not selected by closeness to measurement. These seven sources contain 830 accepted complete Body forwards.

The Kimi retry contains 63 forwards. Its prediction is exactly the previous rejected diagnostic value, 28.560581581623204 ms, while worker memory drops from 521.45 to 414.88 MiB. It restores the completed PASS without changing measured spans. The previous failed attempt remains in `../acceptance-20261030-runtime5ec8843a/`.

[The delta table](body-runtime-delta.md) separates the previous and current inputs/runtimes. Together with the unaffected 58 completed `5ec8843a` primary predictions, all 66 latest primary sources have completed predictions and 22 pass. Their per-row runtime identities remain distinct.

The complete-structure strict-cohort worker is a separate memory path. Its c32 pilot still exceeds 512 MiB and is retained in `../acceptance-20261030-v41-composed-operators-ec58ce79/`; it is not promoted to strict accuracy or extrapolated to the other six sources. The existing 98 native-reference groups remain conditional results from their recorded `5ec8843a` runtime.

Reproduce with the two case manifests, `replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90 --runtime-source-commit ec58ce7921583967a50e803c78b962d90f8273b0`, and separate prediction caches. The three V4.1 output shards partition the seven source IDs, with no duplicate populations; the Kimi output is a separate failed-attempt retry. Logs and independent reviews accompany every output shard.
