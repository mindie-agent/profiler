# Scalar / DMA / routing physical evidence

Six saved-capture passes preserve full native ABI, BlockNum, PMU numeric/missing populations and complete integer duration histograms inside already accepted Body windows. Every selected family exactly matches its previous retained population. The separately retained B16/32/64 directional copy audit is reused without another capture pass.

No hardware rate or Body prediction changes here. Pipeline times overlap; signed sum/max differences are not classified as barriers or launch. Exporter owner aggregation and compiled dispatch remain distinct from source counts.

| Source | Native / direction | Calls/F | Block | Duration Mean/P50 us | Scalar busy us | MTE2 busy us | MTE3 busy us |
|---|---|---:|---:|---:|---:|---:|---:|
| a5_glm53flash_tp8_c8_p4k | CausalConv1d / whole native | 34 | 64 | 8.920 / 8.912 | 4.919 | 2.026 | 1.443 |
| a5_glm53flash_tp8_c8_p4k | _copy_conv_state_kernel / gather | 34 | 64 | 6.403 / 6.394 | 2.634 | 2.992 | 1.684 |
| a5_glm53flash_tp8_c8_p4k | _copy_conv_state_kernel / scatter | 34 | 64 | 5.242 / 5.189 | 2.768 | 1.566 | 1.562 |
| a5_glm53flash_tp8_c8_p4k | MoeInitRoutingV3 / whole native | 42 | 64 | 21.641 / 21.509 | 4.522 | 1.092 | 0.643 |
| a5_glm53flash_tp8_c4_p8k | CausalConv1d / whole native | 34 | 64 | 8.331 / 8.139 | 4.924 | 2.052 | 1.378 |
| a5_glm53flash_tp8_c4_p8k | _copy_conv_state_kernel / gather | 34 | 64 | 4.896 / 4.769 | 1.965 | 1.533 | 0.937 |
| a5_glm53flash_tp8_c4_p8k | _copy_conv_state_kernel / scatter | 34 | 64 | 4.153 / 4.037 | 1.987 | 0.835 | 0.774 |
| a5_glm53flash_tp8_c4_p8k | MoeInitRoutingV3 / whole native | 42 | 64 | 21.821 / 21.538 | 4.423 | 1.083 | 0.892 |
| glm53flash-a5-tp8-c1 | CausalConv1d / whole native | 34 | 16 | 6.755 / 6.612 | 4.067 | 2.026 | 1.394 |
| glm53flash-a5-tp8-c1 | _copy_conv_state_kernel / gather | 34 | 64 | 3.810 / 3.686 | 1.595 | 0.546 | 0.271 |
| glm53flash-a5-tp8-c1 | _copy_conv_state_kernel / scatter | 34 | 64 | 3.559 / 3.479 | 1.561 | 0.278 | 0.222 |
| glm53flash-a5-tp8-c1 | MoeInitRoutingV3 / whole native | 42 | 64 | 20.796 / 20.692 | 3.897 | 1.040 | 1.013 |
| qwen35-35b-a5-tp4-c4-graph | CausalConv1d / whole native | 30 | 16 | 7.337 / 7.293 | 4.132 | 2.073 | 1.399 |
| qwen35-35b-a5-tp4-c4-graph | DequantSwigluQuant / whole native | 40 | 64 | 7.299 / 7.286 | 5.021 | 1.355 | 0.318 |
| qwen35-35b-a5-tp4-c64-graph | CausalConv1d / whole native | 30 | 64 | 10.995 / 11.030 | 4.922 | 2.794 | 1.707 |
| qwen35-35b-a5-tp4-c64-graph | DequantSwigluQuant / whole native | 40 | 64 | 54.031 / 54.304 | 30.525 | 18.848 | 11.458 |
| qwen35-35b-a5-tp4-c128-graph | CausalConv1d / whole native | 30 | 64 | 16.326 / 16.367 | 6.724 | 5.283 | 3.528 |
| qwen35-35b-a5-tp4-c128-graph | DequantSwigluQuant / whole native | 40 | 64 | 56.560 / 56.844 | 27.897 | 17.675 | 21.655 |

| Copy direction | Pipe | Effective slope ns/source-program | Intercept us | R² |
|---|---|---:|---:|---:|
| gather | aiv_scalar_time(us) | 181.161 | 1.113 | 0.9989 |
| gather | aiv_mte2_time(us) | 298.518 | 0.331 | 0.9998 |
| gather | aiv_mte3_time(us) | 139.955 | 0.572 | 0.9976 |
| scatter | aiv_scalar_time(us) | 136.334 | 1.922 | 0.9981 |
| scatter | aiv_mte2_time(us) | 133.207 | 0.751 | 0.9989 |
| scatter | aiv_mte3_time(us) | 134.413 | 0.642 | 0.9992 |

These six slopes are usable composite responses under the stated source schedule. Each point changes program count, metadata loads and bytes together: feature rank is one, so this dataset cannot split their independent prices. Negative intercepts or signed PMU remainders are retained, not clipped into a positive synchronization cost.

DSQ uses a conditional 64 group-index GetValue scan per block across all three domains; changing capacity changes other scalar work without changing this count. Routing keeps the owner-zero E288 serial load/add chain while sort/SIMT/gather/quantization work changes. Neither population identifies an isolated GetValue, sort opcode or atomic RMW latency.

All three GLM SparseFlashMlaMetadata populations are typed AI_CPU / Block0 with missing AIV/AIC counters. They stay model-body dependencies and are not represented as Vector service or discarded as tail control. Full Slice populations now have independent ABI buckets; offsets/index values remain unobserved.

Source hashes, complete counter populations, signed diagnostics, conditional counts and concrete missing contrasts are retained in scalar-dma-physical-constraints.json.
