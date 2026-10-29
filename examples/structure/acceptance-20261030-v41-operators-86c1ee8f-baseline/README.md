# V4.1 A5 baseline: fresh runtime, retained measurements

This arm preserves the six prior source cases and measured body-window histograms. The seventh A5 c128 case is recorded separately in `../acceptance-20261030-v41-c128-operators-86c1ee8f-baseline/`. All costs were recomputed using fixed Sim `86c1ee8f18b9b997eacb315476e2461b99b59fb1`; no raw CSV was scanned and no older cost result was reused.

`--frozen-native-rebind` revalidates each complete GroupedMatmul native ABI bucket against all 40 aligned FFN layers. The new declaration supplies the physical work. The observed buffer capacity, full duration histogram and unknown valid route rows remain unchanged. These are conditional references and never enter the strict accuracy denominator. Changed native Dispatch/Combine programs remain explicitly excluded pending a separate source-correspondence rebind.

Reproduce each case with `examples/structure/reprice_body_operator_families.py --actual <retained.actual.json> --use-source-case-path --output-dir <new-output> --variant runtime86-baseline --runtime-source-commit 86c1ee8f18b9b997eacb315476e2461b99b59fb1 --runtime-validation-status maintained --frozen-native-rebind`, with the fixed Sim checkout and profiler in `PYTHONPATH`. The global scoreboard records all exact source, case, mapping, comparison and runtime identities.

The independent reviewer is `examples/structure/review_repriced_body_operators.py <output-directory>`. It verifies source hashes, full observed histogram statistics, strict cohort math, reference partitions and visible failures without running cost or reading raw captures.

The source-specific MXA8W4 / mixed-packed MQSMLA / HC arm is kept in `../acceptance-20261030-v41-operators-86c1ee8f-source-symmetric/`. It is a separate `[B]*8` DP condition. The two arms must not be pooled into one accuracy denominator or selected by whichever predicts a lower error.
