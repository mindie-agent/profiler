# Six Qwen A5 retained Body operator populations

Prepared explicit source-GDN-native inputs preserve the original model, precision, TP, and measured execution geometry. They select `arch35_fp32`, the independently measured scalar-store service, and the conditional cache-index source layout. The Sim case preparation is committed by the Sim owner as `c6d4bd63`.

Each of the six original CSVs was streamed once against the existing accepted complete-Body windows. The extractor checked every selected forward endpoint against its accepted source; heads, drafts, and duplicate communication summaries are excluded. All native families, including unresolved contracts, retain complete integer-nanosecond histograms.

| Capture | q / execution B | Selected / source forwards | Native Body events | Contract-eligible events |
|---|---:|---:|---:|---:|
| qwen35-35b-a5-tp4-c128-graph | 4 / 128 | 76 / 99 | 145160 | 29640 |
| qwen35-35b-a5-tp4-c4-graph | 4 / 4 | 84 / 91 | 141960 | 32760 |
| qwen35-35b-a5-tp4-c64-graph | 4 / 64 | 79 / 96 | 138250 | 30810 |
| qwen36-a5-tp2-c1 | 4 / 1 | 85 / 85 | 148240 | 48960 |
| qwen36-a5-tp2-c12 | 4 / 12 | 55 / 55 | 98560 | 31680 |
| qwen36-a5-tp2-c96 | 4 / 96 | 24 / 24 | 45312 | 13824 |

Total: 403 selected forwards from 450 complete source forwards; 717,482 native events, of which 187,674 currently have eligible contracts. Six sequential source scans took 93.202 s; peak worker RSS was 140.58 MiB. Structure extraction used the fixed `5251d0d5` runtime. No cost prediction or new device collection ran.

The independent JSON review passed 8,672 checks: accepted source/Body identity, selected and unselected forward counts, complete family/subgroup histograms and quantiles, mapping inclusion/exclusion conservation, and per-layer sample counts. Its scope does not re-read raw events or rederive Sim costs.

Qwen3.5 TP4 uses 4 key heads / 8 value heads and 2,048-wide convolution; Qwen3.6 TP2 uses 8 / 24 heads and 5,120-wide convolution. State is FP32 and active Q/K/V is BF16. TP2 still has 64 scalar-store owners per device. The gating kernel has no complete native tensor ABI in these captures; any upcoming comparison is a conditional source-program reference. Communication activity includes peer wait and is not a bandwidth calibration target.

`operator-reprice-inputs.json` provides the next fresh-structure/fresh-cost input list. This artifact contains measured populations only; it does not claim an accuracy result.

## Fresh source-complete runtime result

The `runtime30dcea1e/` arm prices fresh structure and programs at Sim `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`, preserving all 717,482 observed events. Strict cohorts pass 70/75 (micro 67/70; heavy 3/5), while the matching complete-Body predictions pass **0/6**. Six gating, six FIA and six FFN all-reduce references are conditional and stay outside strict accuracy. Three changed MoE-combine references remain explicitly excluded.

See [the per-source residual ledger](runtime30dcea1e/qwen-body-operator-residual-ledger.md) for the largest matched activity differences, unpaired families, total all-reduce activity, and layer0 versus steady communication distributions. Activity residuals are not a causal decomposition of Body wall time; unpaired work is not automatically missing from Sim. No raw sources were rescanned for the new costs or reviews.
