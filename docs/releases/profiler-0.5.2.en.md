# mindie-profiler 0.5.2

This release adds Decode structure mapping and measured Body, layer and operator
comparisons while preserving the CLI help and diagnostics fixes from 0.5.1.

CSV/DB event normalization and native tensor contracts reuse Sim's declared
structure, fusion boundaries and physical work. Complete Decode bodies are
segmented from retained kernel captures, separating device activity, uncovered
intervals, outer model work and AICPU controller waits. Cohort comparisons retain
unresolved layer identity and use 15% relative tolerance for large calls or 15 us
absolute tolerance for calls at most 50 us.

The current source-corrected scoreboard passes 65 of 66 Body sources, including
in-sample observable service calibration. Qwen3.5-397B c48 remains a reported
-19.46% failure. Retrospective concurrency holdouts pass 144/150 operator domains
but only 2/6 whole bodies; this is not a claim of blind generalization. Prefill,
full Step/MTP/Host and client TPOT/TTFT validation remain separate ongoing work.

Published scoreboards are compact summaries with SHA256 pointers to external
complete evidence. Large replay data is excluded from Git tracking and wheels;
readable Markdown reports remain. Hardware evidence is offline replay of prior
A3/A5 captures, not a new live run. The standalone runtime retains zero required
third-party dependencies. Release benchmark attachments identify the exact clean
source revision and measured verification results.
