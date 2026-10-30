# V4.1 complete cohort replay after streaming structure identities

The final [whole-family report](body-operator-family-scoreboard.json) uses Sim 40e4300ea7ccc1123759f6201cc2d69e3aa77ad6 and the seven unchanged formal composed source cases. It retains all 830 selected Forward samples and 1,447,364 measured body events. No capture or Body boundary was rescanned.

All 98 physical program workers completed below the 512 MiB budget. The maximum worker RSS was 187.91 MiB. The 112 comparable cohorts all passed the absolute 15 us tolerance for calls whose observed mean is at most 50 us. They cover 420,810 calls, or 29.07% of the full observed event population. There are no heavy-call cohorts in this strict subset; 112/112 does not mean complete native coverage or whole-Body accuracy.

| Source | Forward samples | All measured calls | Strict calls | Passed / compared cohorts |
| --- | ---: | ---: | ---: | ---: |
| c128 / p2k | 73 | 127446 | 37011 | 16 / 16 |
| c16 / p2k | 129 | 224840 | 65403 | 16 / 16 |
| c32 / p2k | 105 | 183011 | 53235 | 16 / 16 |
| c4 / p2k | 151 | 263341 | 76557 | 16 / 16 |
| TPOT 10 ms / c8 | 145 | 252886 | 73515 | 16 / 16 |
| TPOT 30 ms / c64 | 75 | 130725 | 38025 | 16 / 16 |
| TPOT 5 ms / c1 | 152 | 265115 | 77064 | 16 / 16 |

The declared model remains forty layers and DP8. Comparison validates every candidate, including 320 candidates for a forty-layer symmetric group, before retaining only the targets needed for cost execution. The full canonical graph identity is preserved. This does not identify which measured occurrence belongs to a particular layer or DP replica.

Each source retains all original families. Attention and FFN HCPost cohorts have changed resource boundaries and are explicitly excluded from this aggregate strict rebinding: fourteen exclusions in total. Their conditional references, together with MC2/GMM/MQSMLA and other previously retained references, remain in the separate 5ec receipts. Those references are not silently repriced or relabeled as 40e results.

The same q_b worker that failed at 569.05 MiB under ec58 succeeded independently at 178.56 MiB in 7.94 seconds. Its exact prior command, runtime pins and result are in q_b-pilot.json and q_b-pilot-worker.json. The earlier failed evidence directory is preserved. The pilot is separate from the 98 whole-family program workers.

The seven source replay durations sum to 990.69 seconds; this is not campaign wall-clock time. At most two source workers ran concurrently. Completed same-generation cases were reused during aggregation without repeating their costs. Repository-relative and resolved paths are normalized to the same pinned file; SHA256 and size checks are unchanged. The 5,440-check independent review reports zero failures.

Reproduce with the fixed checkout first in PYTHONPATH:

    PYTHONPATH=/tmp/mindie-sim-cohort-wave6-20261029:/Users/maoxx241/code/profiler \
      /Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python \
      examples/structure/replay_v41_composed_strict.py \
      --native-report examples/structure/acceptance-20261030-v41-composed-native-5ec8843a/v41-composed-native-reference-scoreboard.json \
      --output-dir NEW_OUTPUT_DIRECTORY \
      --runtime-source-commit 40e4300ea7ccc1123759f6201cc2d69e3aa77ad6

This runner uses the original complete actual/mapping metadata and the reviewed composed declarations. It does not select only favorable roles or extrapolate incomplete histograms. Source, case, fresh mapping, comparison and per-source detail identities are retained in the report.
