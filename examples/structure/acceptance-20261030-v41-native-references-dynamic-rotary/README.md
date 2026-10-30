# V4.1 dynamic + independent partial RoPE source reference

Seven existing rank-0 captures, 830 accepted complete 40-layer target Bodies, and all 182,600 retained native events (220 calls/Forward) are reused without raw reads. The fresh source case arm explicitly selects dynamic compressed-cache work and independent Q, KV and post-attention inverse partial rotations. It does not replace the previous 0b822d0e arm or create seven new capture populations.

- Runtime/input checkout: `5251d0d516d179d05831bd28e863d66df07e6f4f` (runtime 8ced).
- 84 fresh program sets and 84 conditional groups; no unresolved groups and no strict comparisons.
- 40.006 seconds, peak worker RSS 499.12 MiB, below the 512 MiB limit. Each source ran sequentially with the existing 180-second worker budget.
- Independent saved-evidence review: 2,928 checks, no failures. All source identities, complete histograms, layer memberships and Body populations equal the previous arm.
- Source Q, KV and inverse calls each retain 40 native calls/Forward. Their full BF16 active tensor, FP32 coefficient layout, partial slice and inverse/forward direction are checked independently. The former aggregate rotation is never duplicated across native calls.

The three new rotation references are each 1.312 us/call under the declared launch floor; captured mean times range from 2.62 to 6.68 us. These conditional service references are not an additional Body budget, a reconstructed per-layer measured latency, or proof of captured binary/scalar identity. Cache allocation and slot arrays do not establish active cache length, valid compressed writes or route counts. Existing index/cache references preserve those limitations.

`input-manifest.json` pins the seven new source cases and original complete ABI partitions. Per-source directories retain worker receipts, full runtime file identities, observations and source program membership. `v41-native-reference-scoreboard.json` uses `mindie-native-body-reference-batch/1` for the shared report importer; `v41-native-reference-independent-review.json` checks population and arithmetic without rerunning costs. Native per-program service/rate traces are not saved, so this review does not claim independent reconstruction of those resource costs.
