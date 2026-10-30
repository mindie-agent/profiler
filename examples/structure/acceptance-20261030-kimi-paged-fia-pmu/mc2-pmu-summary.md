# Kimi MC2 retained PMU evidence

12 sources / 618 complete Forwards. No new raw read or prediction.

| Source | Native op | Calls | Elapsed Mean/P50 us | AIV Mean/P50 us | Scalar Mean/P50 us | MTE2 Mean us | CSV Wait Mean us | Conditional service us |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| a5_kimi_tp8_e16_bf16_c16_p16k | MoeDistributeDispatchV3 | 4324 | 33.413/33.421 | 15.280/15.250 | 3.718/3.690 | 1.689 | 0.000 | 2.453 |
| a5_kimi_tp8_e16_bf16_c16_p16k | MoeDistributeCombineV3 | 4324 | 14.691/14.569 | 14.426/14.300 | 7.210/7.163 | 3.610 | 0.087 | 4.266 |
| a5_kimi_tp8_e16_bf16_c16_p4k | MoeDistributeDispatchV3 | 4508 | 33.414/33.418 | 15.259/15.240 | 3.720/3.695 | 1.689 | 0.000 | 2.453 |
| a5_kimi_tp8_e16_bf16_c16_p4k | MoeDistributeCombineV3 | 4508 | 14.726/14.598 | 14.461/14.330 | 7.242/7.189 | 3.620 | 0.088 | 4.266 |
| a5_kimi_tp8_e16_bf16_c1_p16k | MoeDistributeDispatchV3 | 5428 | 31.319/31.314 | 15.201/15.180 | 3.741/3.722 | 1.579 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c1_p16k | MoeDistributeCombineV3 | 5428 | 14.550/14.394 | 14.278/14.120 | 7.535/7.472 | 3.273 | 0.087 | 3.989 |
| a5_kimi_tp8_e16_bf16_c1_p4k | MoeDistributeDispatchV3 | 5428 | 31.335/31.323 | 15.210/15.190 | 3.734/3.714 | 1.579 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c1_p4k | MoeDistributeCombineV3 | 5428 | 14.544/14.416 | 14.271/14.145 | 7.545/7.494 | 3.279 | 0.086 | 3.989 |
| a5_kimi_tp8_e16_bf16_c2_p16k | MoeDistributeDispatchV3 | 4968 | 31.565/31.543 | 15.151/15.090 | 3.685/3.666 | 1.572 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c2_p16k | MoeDistributeCombineV3 | 4968 | 34.585/34.645 | 34.319/34.380 | 17.972/17.977 | 8.358 | 0.087 | 3.989 |
| a5_kimi_tp8_e16_bf16_c2_p4k | MoeDistributeDispatchV3 | 5060 | 31.532/31.513 | 15.132/15.080 | 3.676/3.658 | 1.573 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c2_p4k | MoeDistributeCombineV3 | 5060 | 34.497/34.534 | 34.230/34.270 | 17.920/17.939 | 8.343 | 0.086 | 3.989 |
| a5_kimi_tp8_e16_bf16_c32_p16k | MoeDistributeDispatchV3 | 3772 | 34.207/34.204 | 14.700/14.520 | 3.883/3.864 | 1.866 | 0.000 | 2.728 |
| a5_kimi_tp8_e16_bf16_c32_p16k | MoeDistributeCombineV3 | 3772 | 14.615/14.506 | 14.349/14.240 | 6.809/6.766 | 3.934 | 0.086 | 4.541 |
| a5_kimi_tp8_e16_bf16_c32_p4k | MoeDistributeDispatchV3 | 4232 | 34.197/34.183 | 14.690/14.520 | 3.882/3.866 | 1.858 | 0.000 | 2.728 |
| a5_kimi_tp8_e16_bf16_c32_p4k | MoeDistributeCombineV3 | 4232 | 14.584/14.442 | 14.317/14.180 | 6.807/6.749 | 3.930 | 0.084 | 4.541 |
| a5_kimi_tp8_e16_bf16_c4_p16k | MoeDistributeDispatchV3 | 4784 | 31.864/31.860 | 14.937/14.920 | 3.652/3.631 | 1.551 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c4_p16k | MoeDistributeCombineV3 | 4784 | 14.338/14.266 | 14.066/13.990 | 7.369/7.332 | 3.290 | 0.087 | 3.989 |
| a5_kimi_tp8_e16_bf16_c4_p4k | MoeDistributeDispatchV3 | 4876 | 31.842/31.813 | 14.924/14.910 | 3.651/3.632 | 1.550 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c4_p4k | MoeDistributeCombineV3 | 4876 | 14.448/14.367 | 14.177/14.100 | 7.409/7.370 | 3.315 | 0.087 | 3.989 |
| a5_kimi_tp8_e16_bf16_c8_p16k | MoeDistributeDispatchV3 | 4692 | 32.982/32.979 | 15.196/15.160 | 3.694/3.675 | 1.627 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c8_p16k | MoeDistributeCombineV3 | 4692 | 14.491/14.450 | 14.222/14.180 | 7.388/7.366 | 3.327 | 0.086 | 3.989 |
| a5_kimi_tp8_e16_bf16_c8_p4k | MoeDistributeDispatchV3 | 4784 | 32.913/32.904 | 15.125/15.100 | 3.700/3.679 | 1.622 | 0.000 | 2.315 |
| a5_kimi_tp8_e16_bf16_c8_p4k | MoeDistributeCombineV3 | 4784 | 14.508/14.450 | 14.239/14.180 | 7.379/7.359 | 3.337 | 0.087 | 3.989 |

- All PMU statistics pool complete retained per-field counters within one source and native ABI.
- AIV/pipeline times retain exporter semantics; overlapping pipelines are not additive service times.
- Elapsed minus AIV is a difference of population means, not a measured network-wait component.
- CSV Wait Time is a separate exporter metric, not a bound on in-kernel peer waiting.
- Active routed values, peer readiness and private dispatch are unobserved; conditional service is not bandwidth calibration.
