# Kimi complete native Body references

Runtime `18c423c7297fc3b3e92a5eb34f204df40a2a6cb6`; all rows are conditional references, outside strict accuracy.
Exact native histograms are retained. Heterogeneous AttnRes source flags use captured layer call counts; no per-layer measured P50 is invented.

| Case / native | Calls/F | Real Mean / P50 us | Sim mean reference us | Real activity / Sim service / residual ms/F |
| --- | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k / MlaPrologV3 | 24.000 | 34.559218 / 34.513000 | 41.880561 | 0.829421 / 1.005133 / +0.175712 |
| a5_kimi_tp8_e16_bf16_c16_p16k / AttnResFwd | 187.000 | 11.179086 / 10.967000 | 7.212270 | 2.090489 / 1.348694 / -0.741795 |
| a5_kimi_tp8_e16_bf16_c16_p16k / CausalConv1d | 69.000 | 8.340544 / 8.304000 | 1.312000 | 0.575498 / 0.090528 / -0.484970 |
| a5_kimi_tp8_e16_bf16_c16_p16k / RecurrentKda | 69.000 | 20.565432 / 20.553000 | 7.494090 | 1.419015 / 0.517092 / -0.901923 |
| a5_kimi_tp8_e16_bf16_c16_p16k / MoeDistributeDispatchV3 | 92.000 | 33.413446 / 33.421000 | 2.453089 | 3.074037 / 0.225684 / -2.848353 |
| a5_kimi_tp8_e16_bf16_c16_p16k / MoeDistributeCombineV3 | 92.000 | 14.690633 / 14.568500 | 4.266497 | 1.351538 / 0.392518 / -0.959020 |
| a5_kimi_tp8_e16_bf16_c16_p4k / MlaPrologV3 | 24.000 | 34.539941 / 34.478000 | 41.880561 | 0.828959 / 1.005133 / +0.176175 |
| a5_kimi_tp8_e16_bf16_c16_p4k / AttnResFwd | 187.000 | 11.191476 / 10.965000 | 7.212270 | 2.092806 / 1.348694 / -0.744112 |
| a5_kimi_tp8_e16_bf16_c16_p4k / CausalConv1d | 69.000 | 8.331837 / 8.289000 | 1.312000 | 0.574897 / 0.090528 / -0.484369 |
| a5_kimi_tp8_e16_bf16_c16_p4k / RecurrentKda | 69.000 | 20.482388 / 20.479000 | 7.494090 | 1.413285 / 0.517092 / -0.896193 |
| a5_kimi_tp8_e16_bf16_c16_p4k / MoeDistributeDispatchV3 | 92.000 | 33.414167 / 33.418000 | 2.453089 | 3.074103 / 0.225684 / -2.848419 |
| a5_kimi_tp8_e16_bf16_c16_p4k / MoeDistributeCombineV3 | 92.000 | 14.725576 / 14.598000 | 4.266497 | 1.354753 / 0.392518 / -0.962235 |
| a5_kimi_tp8_e16_bf16_c1_p16k / AttnResFwd | 187.000 | 10.976889 / 10.820000 | 7.212270 | 2.052678 / 1.348694 / -0.703984 |
| a5_kimi_tp8_e16_bf16_c1_p16k / RecurrentKda | 69.000 | 10.652683 / 10.695000 | 2.098301 | 0.735035 / 0.144783 / -0.590252 |
| a5_kimi_tp8_e16_bf16_c1_p16k / MoeDistributeCombineV3 | 92.000 | 14.549829 / 14.394000 | 3.989132 | 1.338584 / 0.367000 / -0.971584 |
| a5_kimi_tp8_e16_bf16_c1_p16k / MoeDistributeDispatchV3 | 92.000 | 31.319129 / 31.313500 | 2.315434 | 2.881360 / 0.213020 / -2.668340 |
| a5_kimi_tp8_e16_bf16_c1_p16k / MlaPrologV3 | — | — | — | kimi_mla_prolog_declared_projection_differs:q_a |
| a5_kimi_tp8_e16_bf16_c1_p16k / CausalConv1d | — | — | — | causal_conv_declared_active_elements_differ |
| a5_kimi_tp8_e16_bf16_c1_p4k / AttnResFwd | 187.000 | 10.974159 / 10.821000 | 7.212270 | 2.052168 / 1.348694 / -0.703473 |
| a5_kimi_tp8_e16_bf16_c1_p4k / RecurrentKda | 69.000 | 10.700630 / 10.738000 | 2.098301 | 0.738343 / 0.144783 / -0.593561 |
| a5_kimi_tp8_e16_bf16_c1_p4k / MoeDistributeCombineV3 | 92.000 | 14.543737 / 14.416000 | 3.989132 | 1.338024 / 0.367000 / -0.971024 |
| a5_kimi_tp8_e16_bf16_c1_p4k / MoeDistributeDispatchV3 | 92.000 | 31.334812 / 31.322500 | 2.315434 | 2.882803 / 0.213020 / -2.669783 |
| a5_kimi_tp8_e16_bf16_c1_p4k / MlaPrologV3 | — | — | — | kimi_mla_prolog_declared_projection_differs:q_a |
| a5_kimi_tp8_e16_bf16_c1_p4k / CausalConv1d | — | — | — | causal_conv_declared_active_elements_differ |
| a5_kimi_tp8_e16_bf16_c2_p16k / AttnResFwd | 187.000 | 10.994817 / 10.826500 | 7.212270 | 2.056031 / 1.348694 / -0.707336 |
| a5_kimi_tp8_e16_bf16_c2_p16k / RecurrentKda | 69.000 | 10.990423 / 11.044000 | 2.139920 | 0.758339 / 0.147654 / -0.610685 |
| a5_kimi_tp8_e16_bf16_c2_p16k / MoeDistributeDispatchV3 | 92.000 | 31.564932 / 31.543000 | 2.315434 | 2.903974 / 0.213020 / -2.690954 |
| a5_kimi_tp8_e16_bf16_c2_p16k / MoeDistributeCombineV3 | 92.000 | 34.585196 / 34.645000 | 3.989132 | 3.181838 / 0.367000 / -2.814838 |
| a5_kimi_tp8_e16_bf16_c2_p16k / MlaPrologV3 | — | — | — | kimi_mla_prolog_declared_projection_differs:q_a |
| a5_kimi_tp8_e16_bf16_c2_p16k / CausalConv1d | — | — | — | causal_conv_declared_active_elements_differ |
| a5_kimi_tp8_e16_bf16_c2_p4k / AttnResFwd | 187.000 | 10.998059 / 10.814000 | 7.212270 | 2.056637 / 1.348694 / -0.707943 |
| a5_kimi_tp8_e16_bf16_c2_p4k / RecurrentKda | 69.000 | 11.241109 / 11.293000 | 2.139920 | 0.775637 / 0.147654 / -0.627982 |
| a5_kimi_tp8_e16_bf16_c2_p4k / MoeDistributeDispatchV3 | 92.000 | 31.532299 / 31.513000 | 2.315434 | 2.900971 / 0.213020 / -2.687952 |
| a5_kimi_tp8_e16_bf16_c2_p4k / MoeDistributeCombineV3 | 92.000 | 34.496619 / 34.534000 | 3.989132 | 3.173689 / 0.367000 / -2.806689 |
| a5_kimi_tp8_e16_bf16_c2_p4k / MlaPrologV3 | — | — | — | kimi_mla_prolog_declared_projection_differs:q_a |
| a5_kimi_tp8_e16_bf16_c2_p4k / CausalConv1d | — | — | — | causal_conv_declared_active_elements_differ |
| a5_kimi_tp8_e16_bf16_c32_p16k / MlaPrologV3 | 24.000 | 41.668252 / 41.625500 | 45.920334 | 1.000038 / 1.102088 / +0.102050 |
| a5_kimi_tp8_e16_bf16_c32_p16k / AttnResFwd | 187.000 | 11.399930 / 11.175000 | 7.212270 | 2.131787 / 1.348694 / -0.783092 |
| a5_kimi_tp8_e16_bf16_c32_p16k / CausalConv1d | 69.000 | 10.981230 / 10.934000 | 1.312000 | 0.757705 / 0.090528 / -0.667177 |
| a5_kimi_tp8_e16_bf16_c32_p16k / RecurrentKda | 69.000 | 30.550759 / 30.527000 | 14.988181 | 2.108002 / 1.034184 / -1.073818 |
| a5_kimi_tp8_e16_bf16_c32_p16k / MoeDistributeDispatchV3 | 92.000 | 34.207435 / 34.204000 | 2.728399 | 3.147084 / 0.251013 / -2.896071 |
| a5_kimi_tp8_e16_bf16_c32_p16k / MoeDistributeCombineV3 | 92.000 | 14.614950 / 14.506000 | 4.540783 | 1.344575 / 0.417752 / -0.926823 |
| a5_kimi_tp8_e16_bf16_c32_p4k / MlaPrologV3 | 24.000 | 41.661072 / 41.627500 | 45.920334 | 0.999866 / 1.102088 / +0.102222 |
| a5_kimi_tp8_e16_bf16_c32_p4k / AttnResFwd | 187.000 | 11.402969 / 11.165500 | 7.212270 | 2.132355 / 1.348694 / -0.783661 |
| a5_kimi_tp8_e16_bf16_c32_p4k / CausalConv1d | 69.000 | 10.930286 / 10.894000 | 1.312000 | 0.754190 / 0.090528 / -0.663662 |
| a5_kimi_tp8_e16_bf16_c32_p4k / RecurrentKda | 69.000 | 30.461027 / 30.449000 | 14.988181 | 2.101811 / 1.034184 / -1.067626 |
| a5_kimi_tp8_e16_bf16_c32_p4k / MoeDistributeDispatchV3 | 92.000 | 34.197007 / 34.183000 | 2.728399 | 3.146125 / 0.251013 / -2.895112 |
| a5_kimi_tp8_e16_bf16_c32_p4k / MoeDistributeCombineV3 | 92.000 | 14.583577 / 14.442000 | 4.540783 | 1.341689 / 0.417752 / -0.923937 |
| a5_kimi_tp8_e16_bf16_c4_p16k / AttnResFwd | 187.000 | 11.008107 / 10.821000 | 7.212270 | 2.058516 / 1.348694 / -0.709822 |
| a5_kimi_tp8_e16_bf16_c4_p16k / RecurrentKda | 69.000 | 11.858005 / 11.850500 | 2.337296 | 0.818202 / 0.161273 / -0.656929 |
| a5_kimi_tp8_e16_bf16_c4_p16k / MoeDistributeDispatchV3 | 92.000 | 31.863740 / 31.859500 | 2.315434 | 2.931464 / 0.213020 / -2.718444 |
| a5_kimi_tp8_e16_bf16_c4_p16k / MoeDistributeCombineV3 | 92.000 | 14.337638 / 14.266000 | 3.989132 | 1.319063 / 0.367000 / -0.952062 |
| a5_kimi_tp8_e16_bf16_c4_p16k / MlaPrologV3 | — | — | — | kimi_mla_prolog_declared_projection_differs:q_a |
| a5_kimi_tp8_e16_bf16_c4_p16k / CausalConv1d | — | — | — | causal_conv_declared_active_elements_differ |
| a5_kimi_tp8_e16_bf16_c4_p4k / AttnResFwd | 187.000 | 11.009162 / 10.828000 | 7.212270 | 2.058713 / 1.348694 / -0.710019 |
| a5_kimi_tp8_e16_bf16_c4_p4k / RecurrentKda | 69.000 | 11.918537 / 11.906000 | 2.337296 | 0.822379 / 0.161273 / -0.661106 |
| a5_kimi_tp8_e16_bf16_c4_p4k / MoeDistributeDispatchV3 | 92.000 | 31.842258 / 31.813000 | 2.315434 | 2.929488 / 0.213020 / -2.716468 |
| a5_kimi_tp8_e16_bf16_c4_p4k / MoeDistributeCombineV3 | 92.000 | 14.447793 / 14.367000 | 3.989132 | 1.329197 / 0.367000 / -0.962197 |
| a5_kimi_tp8_e16_bf16_c4_p4k / MlaPrologV3 | — | — | — | kimi_mla_prolog_declared_projection_differs:q_a |
| a5_kimi_tp8_e16_bf16_c4_p4k / CausalConv1d | — | — | — | causal_conv_declared_active_elements_differ |
| a5_kimi_tp8_e16_bf16_c8_p16k / MlaPrologV3 | 24.000 | 33.425231 / 33.389000 | 39.860674 | 0.802206 / 0.956656 / +0.154451 |
| a5_kimi_tp8_e16_bf16_c8_p16k / AttnResFwd | 187.000 | 10.997209 / 10.763000 | 7.212270 | 2.056478 / 1.348694 / -0.707784 |
| a5_kimi_tp8_e16_bf16_c8_p16k / CausalConv1d | 69.000 | 7.057520 / 7.045000 | 1.312000 | 0.486969 / 0.090528 / -0.396441 |
| a5_kimi_tp8_e16_bf16_c8_p16k / RecurrentKda | 69.000 | 15.605497 / 15.587000 | 4.703742 | 1.076779 / 0.324558 / -0.752221 |
| a5_kimi_tp8_e16_bf16_c8_p16k / MoeDistributeCombineV3 | 92.000 | 14.490970 / 14.450000 | 3.989132 | 1.333169 / 0.367000 / -0.966169 |
| a5_kimi_tp8_e16_bf16_c8_p16k / MoeDistributeDispatchV3 | 92.000 | 32.982231 / 32.979000 | 2.315434 | 3.034365 / 0.213020 / -2.821345 |
| a5_kimi_tp8_e16_bf16_c8_p4k / MlaPrologV3 | 24.000 | 33.437050 / 33.376500 | 39.860674 | 0.802489 / 0.956656 / +0.154167 |
| a5_kimi_tp8_e16_bf16_c8_p4k / AttnResFwd | 187.000 | 10.977039 / 10.745000 | 7.212270 | 2.052706 / 1.348694 / -0.704012 |
| a5_kimi_tp8_e16_bf16_c8_p4k / CausalConv1d | 69.000 | 7.043321 / 7.031500 | 1.312000 | 0.485989 / 0.090528 / -0.395461 |
| a5_kimi_tp8_e16_bf16_c8_p4k / RecurrentKda | 69.000 | 15.498420 / 15.467000 | 4.703742 | 1.069391 / 0.324558 / -0.744833 |
| a5_kimi_tp8_e16_bf16_c8_p4k / MoeDistributeCombineV3 | 92.000 | 14.508293 / 14.450000 | 3.989132 | 1.334763 / 0.367000 / -0.967763 |
| a5_kimi_tp8_e16_bf16_c8_p4k / MoeDistributeDispatchV3 | 92.000 | 32.913490 / 32.904500 | 2.315434 | 3.028041 / 0.213020 / -2.815021 |

Source service residuals cannot be added to explain Body wall time. Full ABI, source/case/runtime identity, exact histograms and program multiplicities are retained in JSON.
