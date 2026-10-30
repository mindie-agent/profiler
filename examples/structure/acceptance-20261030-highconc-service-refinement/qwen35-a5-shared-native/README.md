# Q35 A5 shared-FFN precision and same-shape role correction

Three accepted Body populations are preserved: c4/c64/c128 have 84/79/76 selected forwards. One local retained-window pass per existing source produced complete native ABI, FFN ordinal, layer counts and integer duration histograms. It did not admit new Body windows. The scans read 601,360 CSV rows through the selected windows, retained 454,289 positive native events, took 26.551 seconds and peaked at 82,640,896 bytes. Native activity can overlap and is not Body wall time.

The BF16 matrix `[M,256,2048]` occurs twice per layer: FFN ordinal 1 precedes TopK (router); ordinal 2 follows routed expert combine/TP gather and precedes SwiGLU (shared gate-up). Ordinal 3 is the BF16 shared down `[M,2048,128]`. All three roles have exactly 40 calls per forward across all 40 layers. Full native descriptors and each source's own means are retained separately. The previous 80-call same-shape cohort is not divided using timing or assigned twice to the router.

The new source declaration changes only the shared-expert quantization category to BF16 operands, matching the retained descriptors. It removes the 80 source quantizers that previously preceded shared up/down and leaves routed INT8 experts unchanged. Three physical-role response rules each execute 40 times. Prior native response rules are preserved unchanged.

| Case | Real ms | Sim ms | Error | ≤15% | ≤8% |
|---|---:|---:|---:|---|---|
| c4 | 11.551367 | 9.900854 | −14.2885% | pass | fail |
| c64 | 21.956845 | 19.974997 | −9.0261% | pass | fail |
| c128 | 28.584774 | 26.049013 | −8.8710% | pass | fail |

All results use Sim `21c30821d87a757bace8cf6b2fffea2536db643e` and are explicitly in-sample. These precision/response changes do not promote the historical strict-contract scoreboard. No Body residual was used to choose service values.

Use `decode-forward-cases.json` and `decode-forward-replay.compact.json`. The format-only projection preserves the executed case hashes, all observations, predictions and query parameters. `format-projection.json` pins the oversized local original; it is omitted from Git. Repeated service declarations are references to the unchanged case files. Standard Body review: 693 checks, zero failures. Native parameter review: 257 checks, zero failures. Both are included. The builder and collector scripts are outside this directory in `examples/structure/`.
