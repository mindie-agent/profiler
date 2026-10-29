# High-concurrency full-layer spans grouped by attention structure

These are full Transformer layers, including dense FFN and actual communication. The GDN/GQA labels classify the declared attention structure, not the kernel cost.

| Case | TP | M / B / q | Attention structure | Layers | Layer occurrences | Mean ms/layer | Min layer mean ms | Max layer mean ms |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| a5_qwen36_highconc_c40 | 8 | 160 / 40 / 4 | gdn | 48 | 2592 | 0.333238 | 0.300046 | 1.547308 |
| a5_qwen36_highconc_c40 | 8 | 160 / 40 / 4 | gqa | 16 | 864 | 0.289689 | 0.288551 | 0.290606 |
| a5_qwen36_highconc_c128 | 8 | 512 / 128 / 4 | gdn | 48 | 1824 | 0.515500 | 0.496524 | 1.239153 |
| a5_qwen36_highconc_c128 | 8 | 512 / 128 / 4 | gqa | 16 | 608 | 0.488422 | 0.486149 | 0.493673 |
| a5_qwen36_highconc_c4 | 8 | 16 / 4 / 4 | gdn | 48 | 3504 | 0.215818 | 0.174680 | 2.030701 |
| a5_qwen36_highconc_c4 | 8 | 16 / 4 / 4 | gqa | 16 | 1168 | 0.183285 | 0.181104 | 0.193636 |
| a5_qwen38_highconc_c32 | 4 | 128 / 32 / 4 | gdn | 48 | 2304 | 0.381152 | 0.374087 | 0.401811 |
| a5_qwen38_highconc_c32 | 4 | 128 / 32 / 4 | gqa | 16 | 768 | 0.277580 | 0.272876 | 0.331568 |
| a5_qwen38_highconc_c128 | 4 | 512 / 128 / 4 | gdn | 48 | 1392 | 0.761777 | 0.758632 | 0.766355 |
| a5_qwen38_highconc_c128 | 4 | 512 / 128 / 4 | gqa | 16 | 464 | 0.566802 | 0.564475 | 0.568875 |
| a5_qwen38_highconc_c4 | 4 | 16 / 4 / 4 | gdn | 48 | 2160 | 0.207698 | 0.203935 | 0.219625 |
| a5_qwen38_highconc_c4 | 4 | 16 / 4 / 4 | gqa | 16 | 720 | 0.187527 | 0.180713 | 0.277209 |

M/B/q are executed tensor dimensions and may include graph padding; they are not asserted active request counts. Individual-layer distributions remain in the source JSON. Layer spans are nonadditive.
