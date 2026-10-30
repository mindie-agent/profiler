# Current profiling validation

One canonical case registry and one recorded Sim package. Selected costs are freshly replayed; unchanged cases retain verified evidence from this same Sim package. Calibration and held-out labels remain distinct; device Body latency is not client TPOT.


| Case | Complete target cycles | Cycle mean / P50 ms | Client token TPOT P50 ms | Serving status |
|---|---:|---:|---:|---|
| glm53flash-a3-tp16-c4-livepre | 46 | 39.847 / 39.684 | 14.697 | serving_prediction_failed |
| qwen35-35b-a5-tp4-c64-graph | 79 | 32.250 / 31.906 | 12.000 | serving_prediction_failed |
| qwen36-a5-tp2-c12 | 54 | 33.707 / 33.608 | 12.657 | serving_prediction_timeout |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 74 | 27.023 / 27.002 | 28.943 | serving_prediction_failed |
| a5_glm53flash_tp8_c64_p4k | 30 | 59.973 / 59.772 | 29.828 | serving_prediction_failed |
| a3_glm53flash_heldout_s1_c10_p4096 | — | — / — | 9.965 | completed |
| a3_glm53flash_heldout_s1_c12_p4096 | — | — / — | 10.749 | completed |
| a3_glm53flash_heldout_s1_c18_p4096 | — | — / — | 11.814 | completed |
| a3_glm53flash_heldout_s1_c24_p4096 | — | — / — | 13.144 | completed |
| a3_glm53flash_heldout_s1_c30_p4096 | — | — / — | 14.582 | completed |
| a3_glm53flash_heldout_s1_c6_p4096 | — | — / — | 8.966 | completed |
| a3_glm53flash_heldout_s2_p12288_c12 | — | — / — | 10.128 | completed |
| a3_glm53flash_heldout_s2_p16384_c12 | — | — / — | 10.319 | completed |
| a3_glm53flash_heldout_s2_p2048_c12 | — | — / — | 11.918 | completed |
| a3_glm53flash_heldout_s2_p32768_c12 | — | — / — | 9.432 | completed |
| a3_glm53flash_heldout_s2_p4096_c12 | — | — / — | 12.698 | completed |
| a3_glm53flash_heldout_s2_p8192_c12 | — | — / — | 9.975 | completed |
| a3_glm53flash_heldout_s3_hit_0pct_p8192 | — | — / — | 49.542 | completed |
| a3_glm53flash_heldout_s3_hit_50pct_p8192 | — | — / — | 24.781 | completed |
| a3_glm53flash_heldout_s3_hit_95pct_p8192 | — | — / — | 12.069 | completed |
| a3_glm53flash_heldout_s4_accept_counting | — | — / — | 9.263 | completed |
| a3_glm53flash_heldout_s4_accept_json | — | — / — | 7.280 | completed |
| a3_glm53flash_heldout_s4_accept_low | — | — / — | 15.191 | completed |
| a3_glm53flash_heldout_s4_accept_med | — | — / — | 7.153 | completed |
| a3_glm53flash_heldout_s5_prefill_p16384_c1 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p16384_c4 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p2048_c1 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p2048_c4 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p32768_c1 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p32768_c4 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p4096_c1 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p4096_c4 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p8192_c1 | — | — / — | — | completed |
| a3_glm53flash_heldout_s5_prefill_p8192_c4 | — | — / — | — | completed |
| a3_v41_heldout_pd_pipeline_c12_p16384 | — | — / — | 15.380 | completed |
| a3_v41_heldout_pd_pipeline_c12_p4096 | — | — / — | 17.193 | completed |
| a3_v41_heldout_pd_pipeline_c16_p16384 | — | — / — | 14.797 | completed |
| a3_v41_heldout_pd_pipeline_c16_p4096 | — | — / — | 16.852 | completed |
| a3_v41_heldout_pd_pipeline_c24_p16384 | — | — / — | 15.166 | completed |
| a3_v41_heldout_pd_pipeline_c24_p4096 | — | — / — | 17.452 | failed |
| a3_v41_heldout_pd_pipeline_c32_p16384 | — | — / — | 14.814 | completed |
| a3_v41_heldout_pd_pipeline_c32_p4096 | — | — / — | 18.925 | completed |
| a3_v41_heldout_pd_pipeline_c48_p16384 | — | — / — | 15.003 | completed |
| a3_v41_heldout_pd_pipeline_c48_p4096 | — | — / — | 18.784 | completed |
| a3_v41_heldout_pd_pipeline_c4_p16384 | — | — / — | 15.434 | completed |
| a3_v41_heldout_pd_pipeline_c4_p4096 | — | — / — | 14.670 | completed |
| a3_v41_heldout_pd_pipeline_c8_p16384 | — | — / — | 14.854 | completed |
| a3_v41_heldout_pd_pipeline_c8_p4096 | — | — / — | 14.052 | completed |
| a3_v41_heldout_pd_staged_c12_p16384 | — | — / — | 17.734 | completed |
| a3_v41_heldout_pd_staged_c12_p4096 | — | — / — | 15.340 | completed |
| a3_v41_heldout_pd_staged_c16_p16384 | — | — / — | 16.806 | completed |
| a3_v41_heldout_pd_staged_c16_p4096 | — | — / — | 16.986 | completed |
| a3_v41_heldout_pd_staged_c24_p16384 | — | — / — | 18.299 | completed |
| a3_v41_heldout_pd_staged_c24_p4096 | — | — / — | 19.123 | completed |
| a3_v41_heldout_pd_staged_c32_p16384 | — | — / — | 19.141 | completed |
| a3_v41_heldout_pd_staged_c32_p4096 | — | — / — | 19.741 | completed |
| a3_v41_heldout_pd_staged_c48_p16384 | — | — / — | 20.529 | completed |
| a3_v41_heldout_pd_staged_c48_p4096 | — | — / — | 20.265 | completed |
| a3_v41_heldout_pd_staged_c4_p16384 | — | — / — | 14.697 | completed |
| a3_v41_heldout_pd_staged_c4_p4096 | — | — / — | 14.682 | completed |
| a3_v41_heldout_pd_staged_c8_p16384 | — | — / — | 16.788 | completed |
| a3_v41_heldout_pd_staged_c8_p4096 | — | — / — | 14.871 | completed |
| a5_glm53flash_heldout_c12_p4k | 19 | 26.258 / 26.303 | 11.018 | serving_prediction_failed |
| a5_glm53flash_heldout_c24_p12k | 21 | 47.970 / 48.119 | 13.998 | serving_prediction_failed |
| a5_glm53flash_heldout_c48_p4k | 26 | 52.063 / 51.834 | 17.244 | serving_prediction_failed |
| a5_glm53flash_heldout_eager_c80_p4k | 6 | 339.879 / 340.000 | 85.974 | serving_prediction_failed |
| a5_kimi_k3_p32768_c1 | 62 | 33.952 / 32.817 | 32.769 | serving_prediction_failed |
| a3_kimi4_tp8_w4a8_c1 | 253 | 7.359 / 7.091 | 7.112 | completed |
| a3_kimi4_tp8_w4a8_c16 | 235 | 9.196 / 7.549 | 8.541 | serving_prediction_failed |
| a3_kimi4_tp8_w4a8_c32 | 220 | 8.801 / 7.826 | 9.708 | serving_prediction_failed |
| a3_kimi4_tp8_w4a8_c4 | 246 | 7.228 / 7.139 | 7.362 | serving_prediction_failed |
| a3_kimi4_tp8_w4a8_c64 | 196 | 11.619 / 10.585 | 14.028 | serving_prediction_failed |

Device target cycles, completion-token TPOT and client delivery have different boundaries. Uncovered cycle intervals are not assigned to Host scheduling without evidence.

| Case | Prediction / source failure |
|---|---|
| glm53flash-a3-tp16-c4-livepre | mindie_sim.schema.common.ModelingError: kda_source_recurrent_requires_decode_only_pcp1 |
| qwen35-35b-a5-tp4-c64-graph | mindie_sim.schema.common.ModelingError: arch35_dequant_requires_integral_rows_capacity_and_full_load_width |
| qwen36-a5-tp2-c12 | serving_prediction_timeout |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | mindie_sim.schema.common.ModelingError: hc_pre_arch35_requires_bf16_hc4_M1to256_Kmultiple128_two_aiv_per_aic |
| a5_glm53flash_tp8_c64_p4k | mindie_sim.schema.common.ModelingError: sparse_mla_metadata_requires_nope_bf16_paged_decode |
| a3_v41_heldout_pd_pipeline_c24_p4096 | ['ServerDisconnectedError: Server disconnected', 'ServerDisconnectedError: Server disconnected', 'ServerDisconnectedError: Server disconnected'] |
| a5_glm53flash_heldout_c12_p4k | mindie_sim.schema.common.ModelingError: sparse_mla_metadata_requires_nope_bf16_paged_decode |
| a5_glm53flash_heldout_c24_p12k | mindie_sim.schema.common.ModelingError: sparse_mla_metadata_requires_nope_bf16_paged_decode |
| a5_glm53flash_heldout_c48_p4k | mindie_sim.schema.common.ModelingError: sparse_mla_metadata_requires_nope_bf16_paged_decode |
| a5_glm53flash_heldout_eager_c80_p4k | mindie_sim.schema.common.ModelingError: sparse_mla_metadata_requires_nope_bf16_paged_decode |
| a5_kimi_k3_p32768_c1 | mindie_sim.schema.common.ModelingError: native_fusion_selected_roles_unmatched:situ_quant |
| a3_kimi4_tp8_w4a8_c16 | mindie_sim.schema.common.ModelingError: kda_source_recurrent_requires_decode_only_pcp1 |
| a3_kimi4_tp8_w4a8_c32 | mindie_sim.schema.common.ModelingError: kda_source_recurrent_requires_decode_only_pcp1 |
| a3_kimi4_tp8_w4a8_c4 | mindie_sim.schema.common.ModelingError: kda_source_recurrent_requires_decode_only_pcp1 |
| a3_kimi4_tp8_w4a8_c64 | mindie_sim.schema.common.ModelingError: kda_source_recurrent_requires_decode_only_pcp1 |

| Case | Client TTFT mean ms | Prefiller HTTP mean ms | Decoder TTFT mean ms | Token TPOT mean ms | Output tok/s |
|---|---:|---:|---:|---:|---:|
| a3_glm53flash_heldout_s1_c10_p4096 | 593.237 | — | — | 10.585 | 633.468 |
| a3_glm53flash_heldout_s1_c12_p4096 | 1050.990 | — | — | 11.573 | 590.645 |
| a3_glm53flash_heldout_s1_c18_p4096 | 1163.920 | — | — | 12.988 | 794.620 |
| a3_glm53flash_heldout_s1_c24_p4096 | 1320.120 | — | — | 13.751 | 969.108 |
| a3_glm53flash_heldout_s1_c30_p4096 | 1583.195 | — | — | 15.205 | 1055.338 |
| a3_glm53flash_heldout_s1_c6_p4096 | 416.922 | — | — | 9.003 | 481.683 |
| a3_glm53flash_heldout_s2_p12288_c12 | 1002.260 | — | — | 10.776 | 623.159 |
| a3_glm53flash_heldout_s2_p16384_c12 | 1124.597 | — | — | 11.579 | 569.254 |
| a3_glm53flash_heldout_s2_p2048_c12 | 446.891 | — | — | 12.505 | 720.246 |
| a3_glm53flash_heldout_s2_p32768_c12 | 1112.448 | — | — | 10.069 | 611.939 |
| a3_glm53flash_heldout_s2_p4096_c12 | 942.574 | — | — | 12.454 | 586.041 |
| a3_glm53flash_heldout_s2_p8192_c12 | 1212.068 | — | — | 11.537 | 545.834 |
| a3_glm53flash_heldout_s3_hit_0pct_p8192 | 8269.780 | — | — | 52.038 | 96.057 |
| a3_glm53flash_heldout_s3_hit_50pct_p8192 | 5260.354 | — | — | 29.619 | 158.971 |
| a3_glm53flash_heldout_s3_hit_95pct_p8192 | 1338.140 | — | — | 12.872 | 425.445 |
| a3_glm53flash_heldout_s4_accept_counting | 684.372 | — | — | 10.057 | 771.118 |
| a3_glm53flash_heldout_s4_accept_json | 631.349 | — | — | 8.018 | 923.123 |
| a3_glm53flash_heldout_s4_accept_low | 672.073 | — | — | 15.796 | 549.380 |
| a3_glm53flash_heldout_s4_accept_med | 732.074 | — | — | 7.538 | 904.457 |
| a3_glm53flash_heldout_s5_prefill_p16384_c1 | 2729.099 | — | — | — | 0.365 |
| a3_glm53flash_heldout_s5_prefill_p16384_c4 | 6950.875 | — | — | — | 0.442 |
| a3_glm53flash_heldout_s5_prefill_p2048_c1 | 685.956 | — | — | — | 1.455 |
| a3_glm53flash_heldout_s5_prefill_p2048_c4 | 1332.368 | — | — | — | 2.642 |
| a3_glm53flash_heldout_s5_prefill_p32768_c1 | 4922.888 | — | — | — | 0.202 |
| a3_glm53flash_heldout_s5_prefill_p32768_c4 | 12694.102 | — | — | — | 0.220 |
| a3_glm53flash_heldout_s5_prefill_p4096_c1 | 883.659 | — | — | — | 1.128 |
| a3_glm53flash_heldout_s5_prefill_p4096_c4 | 2206.948 | — | — | — | 1.538 |
| a3_glm53flash_heldout_s5_prefill_p8192_c1 | 1340.904 | — | — | — | 0.743 |
| a3_glm53flash_heldout_s5_prefill_p8192_c4 | 3545.694 | — | — | — | 0.870 |
| a3_v41_heldout_pd_pipeline_c12_p16384 | — | 5795.641 | 290.971 | 15.103 | 153.297 |
| a3_v41_heldout_pd_pipeline_c12_p4096 | — | 1441.662 | 269.017 | 17.201 | 325.126 |
| a3_v41_heldout_pd_pipeline_c16_p16384 | — | 7146.482 | 284.743 | 14.855 | 166.557 |
| a3_v41_heldout_pd_pipeline_c16_p4096 | — | 2085.127 | 313.622 | 17.056 | 382.291 |
| a3_v41_heldout_pd_pipeline_c24_p16384 | — | 9434.629 | 324.568 | 15.188 | 181.877 |
| a3_v41_heldout_pd_pipeline_c24_p4096 | — | 2835.733 | 304.665 | 17.319 | 387.039 |
| a3_v41_heldout_pd_pipeline_c32_p16384 | — | 11700.379 | 299.071 | 14.845 | 193.679 |
| a3_v41_heldout_pd_pipeline_c32_p4096 | — | 3201.924 | 336.531 | 18.793 | 552.479 |
| a3_v41_heldout_pd_pipeline_c48_p16384 | — | 16238.470 | 294.904 | 14.979 | 202.244 |
| a3_v41_heldout_pd_pipeline_c48_p4096 | — | 4237.844 | 357.432 | 18.521 | 645.871 |
| a3_v41_heldout_pd_pipeline_c4_p16384 | — | 3494.418 | 274.628 | 15.076 | 79.101 |
| a3_v41_heldout_pd_pipeline_c4_p4096 | — | 911.991 | 234.912 | 14.591 | 145.402 |
| a3_v41_heldout_pd_pipeline_c8_p16384 | — | 5137.335 | 295.261 | 15.101 | 107.006 |
| a3_v41_heldout_pd_pipeline_c8_p4096 | — | 1232.949 | 278.215 | 14.353 | 265.764 |
| a3_v41_heldout_pd_staged_c12_p16384 | — | 6012.185 | 337.879 | 17.710 | 131.027 |
| a3_v41_heldout_pd_staged_c12_p4096 | — | 1873.528 | 281.811 | 15.320 | 314.435 |
| a3_v41_heldout_pd_staged_c16_p16384 | — | 7022.877 | 374.226 | 16.844 | 156.221 |
| a3_v41_heldout_pd_staged_c16_p4096 | — | 2001.990 | 268.023 | 16.904 | 377.350 |
| a3_v41_heldout_pd_staged_c24_p16384 | — | 9483.998 | 418.653 | 18.427 | 167.925 |
| a3_v41_heldout_pd_staged_c24_p4096 | — | 2676.157 | 350.211 | 18.928 | 434.566 |
| a3_v41_heldout_pd_staged_c32_p16384 | — | 11562.557 | 478.856 | 19.182 | 168.353 |
| a3_v41_heldout_pd_staged_c32_p4096 | — | 3098.371 | 361.104 | 19.685 | 531.168 |
| a3_v41_heldout_pd_staged_c48_p16384 | — | 15504.492 | 436.961 | 20.590 | 202.860 |
| a3_v41_heldout_pd_staged_c48_p4096 | — | 4237.727 | 419.906 | 20.250 | 617.849 |
| a3_v41_heldout_pd_staged_c4_p16384 | — | 3622.761 | 349.003 | 14.863 | 79.443 |
| a3_v41_heldout_pd_staged_c4_p4096 | — | 864.520 | 211.657 | 14.694 | 158.189 |
| a3_v41_heldout_pd_staged_c8_p16384 | — | 5134.422 | 380.107 | 16.792 | 102.381 |
| a3_v41_heldout_pd_staged_c8_p4096 | — | 1334.158 | 218.409 | 14.835 | 250.510 |

Client-only and PD rows have no measured device Body. Prefiller HTTP, decoder first response and end-to-end request durations remain separate.

Summary: {"compared": 0, "passed": 0, "requested_sources": 119, "sources": 72, "status_counts": {"conditional_endpoint_comparison": 1, "failed": 15, "observed_only": 56}}

Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. Missing evidence and failed predictions remain visible and never count as a pass.
