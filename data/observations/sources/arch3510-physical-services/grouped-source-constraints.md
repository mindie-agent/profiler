# Grouped source / PMU joint constraints

Each row retains its complete native ABI, integer call histogram, layer population and original Block/PMU scope. Capacity is not valid routed M. These are usable whole-call responses, not inferred descriptor prices. No new capture scan or prediction occurs in this join.

| Source | Role / attention | Capacity | Calls/F | Mean/P50 us | AIC MTE2 us | AIV scalar us | AIV MTE2 us |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c4-graph | expert_up / gdn | 128 | 30 | 33.644/33.767 | 20.013 | 0.000 | 0.000 |
| qwen35-35b-a5-tp4-c4-graph | expert_down / gdn | 128 | 30 | 22.158/22.096 | 13.381 | 12.094 | 2.610 |
| qwen35-35b-a5-tp4-c4-graph | expert_up / gqa | 128 | 10 | 34.111/34.264 | 20.531 | 0.000 | 0.000 |
| qwen35-35b-a5-tp4-c4-graph | expert_down / gqa | 128 | 10 | 22.282/22.270 | 13.411 | 11.616 | 2.616 |
| qwen35-35b-a5-tp4-c64-graph | expert_up / gdn | 2048 | 30 | 60.682/60.593 | 42.285 | 0.000 | 0.000 |
| qwen35-35b-a5-tp4-c64-graph | expert_down / gdn | 2048 | 30 | 43.713/43.629 | 37.213 | 19.958 | 13.345 |
| qwen35-35b-a5-tp4-c64-graph | expert_up / gqa | 2048 | 10 | 59.724/59.681 | 41.096 | 0.000 | 0.000 |
| qwen35-35b-a5-tp4-c64-graph | expert_down / gqa | 2048 | 10 | 37.871/37.804 | 30.344 | 19.393 | 9.794 |
| qwen35-35b-a5-tp4-c128-graph | expert_up / gdn | 4096 | 30 | 62.328/62.295 | 43.909 | 0.000 | 0.000 |
| qwen35-35b-a5-tp4-c128-graph | expert_down / gdn | 4096 | 30 | 45.415/45.242 | 38.760 | 20.566 | 13.396 |
| qwen35-35b-a5-tp4-c128-graph | expert_up / gqa | 4096 | 10 | 60.290/60.176 | 41.806 | 0.000 | 0.000 |
| qwen35-35b-a5-tp4-c128-graph | expert_down / gqa | 4096 | 10 | 37.262/37.190 | 29.721 | 19.515 | 9.444 |

A numeric-subset PMU mean is explicitly marked with its own denominator and is excluded from arithmetic against complete-call means. A3 count examples reuse the source schedule under the saved balanced-routing assumption, not observed group-list values. Source SetTensor submissions are not compiled DMA descriptors. A5 INT32 up is separate from the mixed BF16 dequant branch; the latter supports a geometric schedule only after actual routing and host tile selection are known. Neither BlockNum nor an all-owner count may divide an exporter aggregate into a per-core price. Signed PMU differences remain diagnostics.
