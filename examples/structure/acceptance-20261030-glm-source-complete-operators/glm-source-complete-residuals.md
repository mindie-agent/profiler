# GLM remaining service residuals

Runtime `30dcea1e335778b3d6c6f9ba67cce3e84a5adbba`; 18 sources, 713 retained Forward instances. Zero raw scans or new predictions in this summary.

## a3_glm53flash_tp16_aclgraph_c16

Strict 19/21; 50 Forward; B=16, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| direct, outside tolerance / QuantBatchMatmulV3 / shared.down | 42.000 | 20.758582 / 21.221000 | 5.000000 | 0.871860 / 0.210000 / -0.661860 |
| direct, outside tolerance / MatMulV2 / index_k | 22.000 | 11.361995 / 11.510000 | 35.374545 | 0.249964 / 0.778240 / +0.528276 |
| conditional subgraph / GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 241.813110 / 241.925000 | 309.212347 | 10.156151 / 12.986919 / +2.830768 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 79.840817 / 78.381000 | 40.360468 | 2.714588 / 1.372256 / -1.342332 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 39.825860 / 39.140500 | 61.206478 | 1.792164 / 2.754291 / +0.962128 |

## a3_glm53flash_tp16_aclgraph_c32

Strict 16/21; 49 Forward; B=32, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| direct, outside tolerance / QuantBatchMatmulV3 / shared.down | 42.000 | 28.640508 / 29.241000 | 5.000000 | 1.202901 / 0.210000 / -0.992901 |
| direct, outside tolerance / HcPost / attention.hc_post_group | 45.000 | 30.239390 / 29.960000 | 13.405091 | 1.360773 / 0.603229 / -0.757543 |
| direct, outside tolerance / MatMulV2 / index_k | 22.000 | 8.236203 / 8.220000 | 40.494545 | 0.181196 / 0.890880 / +0.709684 |
| conditional subgraph / GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 243.004965 / 243.004500 | 312.921712 | 10.206209 / 13.142712 / +2.936503 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 143.760685 / 143.613000 | 81.389830 | 4.887863 / 2.767254 / -2.120609 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 52.079518 / 51.581000 | 87.561105 | 2.343578 / 3.940250 / +1.596671 |

## a3_glm53flash_tp16_aclgraph_c64

Strict 12/21; 47 Forward; B=64, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| direct, outside tolerance / QuantBatchMatmulV3 / shared.down | 42.000 | 41.693854 / 43.221000 | 8.887816 | 1.751142 / 0.373288 / -1.377854 |
| direct, outside tolerance / MatMulV2 / linear_qkvbfg_a | 34.000 | 64.340868 / 64.531500 | 101.404548 | 2.187590 / 3.447755 / +1.260165 |
| direct, outside tolerance / HcPost / attention.hc_post_group | 45.000 | 51.747264 / 51.981000 | 26.810182 | 2.328627 / 1.206458 / -1.122169 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 245.540307 / 250.525000 | 144.290088 | 8.348370 / 4.905863 / -3.442507 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 66.201462 / 66.121000 | 140.274938 | 2.979066 / 6.312372 / +3.333306 |
| conditional subgraph / GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 245.404965 / 245.005000 | 320.328223 | 10.307009 / 13.453785 / +3.146777 |

## a3_glm53flash_tp16_aclgraph_c8

Strict 20/21; 47 Forward; B=8, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| direct, outside tolerance / MatMulV2 / index_k | 22.000 | 9.849673 / 9.960000 | 27.694545 | 0.216693 / 0.609280 / +0.392587 |
| conditional subgraph / GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 226.014961 / 225.564000 | 307.363773 | 9.492628 / 12.909278 / +3.416650 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 45.782579 / 45.221000 | 20.180234 | 1.556608 / 0.686128 / -0.870480 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 37.136530 / 36.921000 | 53.874366 | 1.671144 / 2.424346 / +0.753203 |

## glm53flash-a3-tp16-c16-livepre

Strict 20/21; 37 Forward; B=16, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| direct, outside tolerance / MatMulV2 / index_k | 22.000 | 7.501405 / 8.160000 | 35.374545 | 0.165031 / 0.778240 / +0.613209 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 33.367166 / 33.321000 | 170.607418 | 1.501522 / 7.677334 / +6.175811 |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 36.039351 / 36.780000 | 170.607418 | 1.621771 / 7.677334 / +6.055563 |
| conditional subgraph / GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 142.415490 / 142.163000 | 285.782843 | 5.981451 / 12.002879 / +6.021429 |

## glm53flash-a5-tp8-c1

Strict 19/19; 65 Forward; B=1, q=4, conditional context=4104.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 33.520268 / 33.438000 | 18.155890 | 1.039128 / 0.562833 / -0.476296 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 11.033061 / 10.866000 | 20.525515 | 0.496488 / 0.923648 / +0.427160 |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 11.216654 / 11.078000 | 20.525515 | 0.504749 / 0.923648 / +0.418899 |

## glm53flash-a5-tp8-c3

Strict 19/19; 53 Forward; B=4, q=4, conditional context=4104.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 98.658061 / 98.458000 | 72.457672 | 3.058400 / 2.246188 / -0.812212 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 11.752889 / 11.566000 | 27.198788 | 0.528880 / 1.223945 / +0.695065 |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 11.905497 / 11.728000 | 27.198788 | 0.535747 / 1.223945 / +0.688198 |

## a5_glm53flash_tp8_c16_p4k

Strict 19/19; 30 Forward; B=16, q=4, conditional context=4104.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 206.079138 / 205.812000 | 163.550332 | 6.388453 / 5.070060 / -1.318393 |
| conditional native / SparseFlashMla / indexed_attention_batch | 11.000 | 86.586355 / 86.494500 | 147.587072 | 0.952450 / 1.623458 / +0.671008 |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.000 | 206.644873 / 206.287000 | 163.550332 | 2.273094 / 1.799054 / -0.474040 |

## a5_glm53flash_tp8_c16_p8k

Strict 19/19; 32 Forward; B=16, q=4, conditional context=8200.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 205.998794 / 205.726500 | 163.550332 | 6.385963 / 5.070060 / -1.315902 |
| conditional native / SparseFlashMla / indexed_attention_batch | 11.000 | 86.857787 / 86.709500 | 147.587072 | 0.955436 / 1.623458 / +0.668022 |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.000 | 206.404088 / 206.335500 | 163.550332 | 2.270445 / 1.799054 / -0.471391 |

## a5_glm53flash_tp8_c32_p4k

Strict 19/19; 31 Forward; B=32, q=4, conditional context=4104.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / SparseFlashMla / indexed_attention_batch | 11.000 | 153.517238 / 153.209000 | 295.174144 | 1.688690 / 3.246916 / +1.558226 |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 207.720145 / 207.499000 | 165.203383 | 6.439324 / 5.121305 / -1.318020 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 43.986928 / 44.073000 | 27.496309 | 1.495556 / 0.934874 / -0.560681 |

## a5_glm53flash_tp8_c32_p8k

Strict 19/19; 35 Forward; B=32, q=4, conditional context=8200.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / SparseFlashMla / indexed_attention_batch | 11.000 | 153.329047 / 153.215000 | 295.174144 | 1.686620 / 3.246916 / +1.560296 |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 207.698392 / 207.331000 | 165.203383 | 6.438650 / 5.121305 / -1.317345 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 44.024733 / 44.062500 | 27.496309 | 1.496841 / 0.934874 / -0.561966 |

## a5_glm53flash_tp8_c4_p8k

Strict 19/19; 11 Forward; B=4, q=4, conditional context=8200.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 98.439079 / 98.184000 | 72.457672 | 3.051611 / 2.246188 / -0.805424 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 11.760531 / 11.581000 | 22.566303 | 0.529224 / 1.015484 / +0.486260 |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 11.932707 / 11.783000 | 22.566303 | 0.536972 / 1.015484 / +0.478512 |

## a5_glm53flash_tp8_c64_p4k

Strict 19/19; 31 Forward; B=64, q=4, conditional context=4104.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / SparseFlashMla / indexed_attention_batch | 11.000 | 288.254073 / 285.492000 | 590.348288 | 3.170795 / 6.493831 / +3.323036 |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 211.180266 / 210.918000 | 168.484143 | 6.546588 / 5.223008 / -1.323580 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 78.338271 / 78.285000 | 54.992617 | 2.663501 / 1.869749 / -0.793752 |

## a5_glm53flash_tp8_c8_p4k

Strict 19/19; 30 Forward; B=8, q=4, conditional context=4104.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 31.000 | 184.394300 / 183.975500 | 144.860048 | 5.716223 / 4.490661 / -1.225562 |
| conditional native / GroupedMatmulSwigluQuantV2 / grouped_gate_up_activation_quant | 11.000 | 185.149567 / 184.762500 | 144.860048 | 2.036645 / 1.593461 / -0.443185 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 13.619847 / 13.420500 | 22.566303 | 0.612893 / 1.015484 / +0.402591 |

## glm53flash-a3-tp16-c4-livepre

Strict 20/21; 46 Forward; B=4, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| direct, outside tolerance / MatMulV2 / index_k | 22.000 | 5.375942 / 5.560000 | 23.854545 | 0.118271 / 0.524800 / +0.406529 |
| conditional subgraph / GroupedMatmulSwigluQuant / grouped_gate_up_activation_quant | 42.000 | 78.892150 / 74.871500 | 154.407906 | 3.313470 / 6.485132 / +3.171662 |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 28.259251 / 28.261000 | 72.249091 | 1.271666 / 3.251209 / +1.979543 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 29.542351 / 29.220000 | 72.249091 | 1.329406 / 3.251209 / +1.921803 |

## glm53flash-a3-tp16-c2

Strict 21/21; 46 Forward; B=2, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 31.870573 / 31.241000 | 57.298182 | 1.434176 / 2.578418 / +1.144242 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 33.355411 / 33.221000 | 57.298182 | 1.500993 / 2.578418 / +1.077425 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 39.741958 / 39.261000 | 18.743769 | 1.351227 / 0.637288 / -0.713938 |

## glm53flash-a3-tp16-c4

Strict 21/21; 46 Forward; B=4, q=6, conditional context=4096.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 36.927639 / 36.361000 | 72.249091 | 1.661744 / 3.251209 / +1.589465 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 37.466675 / 37.161000 | 72.249091 | 1.686000 / 3.251209 / +1.565209 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 42.042336 / 40.921000 | 18.997965 | 1.429439 / 0.645931 / -0.783509 |

## glm53flash-a5-tp8-c96

Strict 17/19; 27 Forward; B=96, q=4, conditional context=4104.

| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| direct, outside tolerance / MatMulV3 / router | 42.000 | 42.303560 / 42.410000 | 159.681939 | 1.776750 / 6.706641 / +4.929892 |
| direct, outside tolerance / MatMulV3 / linear_qkvbfg_a | 34.000 | 33.611522 / 33.590500 | 49.345133 | 1.142792 / 1.677735 / +0.534943 |
| conditional subgraph / HcPre / ffn.hc_pre | 45.000 | 26.214426 / 26.045000 | 141.859084 | 1.179649 / 6.383659 / +5.204010 |
| conditional subgraph / HcPre / attention.hc_pre | 45.000 | 26.608493 / 26.398000 | 141.859084 | 1.197382 / 6.383659 / +5.186277 |
| conditional native / RecurrentKda / kda_recurrent | 34.000 | 113.835816 / 113.776500 | 82.488926 | 3.870418 / 2.804623 / -1.065794 |

## Interpretation

- Activity sums include overlapping streams and communication wait; residuals are not additive Body wall-time attribution.
- Native references preserve full ABI partitions and unknown dynamic values; none contributes to strict accuracy denominators.
- P50 belongs to each original cohort/partition; different layer groups are not averaged into one P50.
- Newly retained nine sources cover RecurrentKda only; the original nine A5 sources also retain fused-up and sparse attention.
