# MindIE-Sim Full-Fleet DSH Capture Parsing & Zero-Shot Generalization Report

## 1. Executive Summary & Fleet Inventory

- **DSH `2026-10-30` Total `kernel_details.csv` Captures**: `743`
  - **Registered in `cases.json` (`body` scope)**: `178`
  - **Excluded Pure Decode-Eager Captures**: `4`
  - **Unregistered Held-Out Captures Evaluated**: `561` across `41` cohorts
- **Total Evaluated Body Captures (Registered + Held-Out)**: `856` (`856` compared)

| Evaluation Scope | Compared | Pass `<= 15%` | Rate `<= 15%` | Pass `<= 10%` | Rate `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Registered Decode Body (`cases.json`) | 280 | 280 | **100.00%** | 253 | **90.36%** | 4.40% | 3.36% | 14.58% |
| Registered Prefill Body (`cases.json`) | 15 | 15 | **100.00%** | 15 | **100.00%** | 4.01% | 4.07% | 8.42% |
| Held-Out Unregistered (Excl. Uncalibrated `v41` `dspark0`) | 517 | 505 | **97.68%** | 438 | **84.72%** | 5.87% | 5.09% | 49.98% |
| Held-Out Unregistered (All Compared, All Populations) | 561 | 546 | **97.33%** | 468 | **83.42%** | 5.99% | 5.10% | 49.98% |
| Held-Out Unregistered (Primary Population) | 561 | 547 | **97.50%** | 466 | **83.07%** | 6.08% | 5.17% | 49.98% |
| **Full Fleet Combined** | 856 | 841 | **98.25%** | 736 | **85.98%** | 5.44% | 4.60% | 49.98% |

## 2. Held-Out Cohort Breakdown

| Cohort | Family | Phase | TP/DP/EP | Spec | Cross-TP | Template | Captures | Compared | Pass `<=15%` | Pass `<=10%` | Mean `|Err|` | Median `|Err|` |
| :--- | :--- | :--- | :--- | ---: | :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `a3/dsv41_wave23_ablation_20261030/tp2dp8_ep16_dspark0_decode` | `deepseek-v4.1` | `decode` | `2/8/16` | 0 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 9/12 (75.0%) | 7/12 (58.3%) | 9.92% | 9.34% |
| `a3/dsv41_wave23_ablation_20261030/tp2dp8_ep16_dspark7_decode` | `deepseek-v4.1` | `decode` | `2/8/16` | 7 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.47% | 4.32% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark0_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 0 | No | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 7/12 (58.3%) | 8.19% | 8.33% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark0_skew` | `deepseek-v4.1` | `decode` | `4/4/16` | 0 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 4/8 (50.0%) | 9.04% | 10.15% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark3_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 3 | No | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 11/12 (91.7%) | 4.56% | 4.77% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark7_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 7 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 7/8 (87.5%) | 5.73% | 6.09% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark7_mb4096_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 7 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 4.50% | 4.37% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark7_skew` | `deepseek-v4.1` | `decode` | `4/4/16` | 7 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 5.85% | 4.81% |
| `a3/dsv41_wave23_ablation_20261030/tp8dp2_ep16_dspark0_decode` | `deepseek-v4.1` | `decode` | `8/2/16` | 0 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.02% | 3.67% |
| `a3/dsv41_wave23_ablation_20261030/tp8dp2_ep16_dspark3_decode` | `deepseek-v4.1` | `decode` | `8/2/16` | 3 | Yes | `a3-v41-tp4dp4-128k-source.json` | 10 | 10 | 10/10 (100.0%) | 8/10 (80.0%) | 7.24% | 7.82% |
| `a3/dsv41_wave23_ablation_20261030/tp8dp2_ep16_dspark7_decode` | `deepseek-v4.1` | `decode` | `8/2/16` | 7 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 11/12 (91.7%) | 10/12 (83.3%) | 6.27% | 5.34% |
| `a3/glm5_3_flash_w8a8_static_kernel_off_c10_p4481_20261030/glm5_3_flash_static_kernel` | `glm-5.3-flash` | `decode` | `16/1/16` | - | No | `decode-a3_glm53flash_static_on_c10_p131201.json` | 1 | 1 | 0/1 (0.0%) | 0/1 (0.0%) | 16.17% | 16.17% |
| `a3/glm5_3_flash_w8a8_static_kernel_on_c10_p4481_20261030/glm5_3_flash_static_kernel` | `glm-5.3-flash` | `decode` | `16/1/16` | - | No | `decode-a3_glm53flash_static_on_c10_p131201.json` | 1 | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 0.75% | 0.75% |
| `a3/kimi_k3_w4a8_4layer_tp16_ep16_heldout_20261030/prefill` | `kimi-k3-4l` | `prefill` | `16/1/16` | - | No | `a3-kimi4-tp16-longctx-source.json` | 6 | 6 | 6/6 (100.0%) | 5/6 (83.3%) | 5.94% | 5.00% |
| `a3/kimi_k3_w4a8_4layer_tp8_ep8_heldout_20261030/prefill` | `kimi-k3-4l` | `prefill` | `8/1/8` | - | No | `a3-kimi4-tp8-longctx-source.json` | 6 | 6 | 6/6 (100.0%) | 4/6 (66.7%) | 6.85% | 6.52% |
| `a3/qwen36_27b_tp2_128k_20261030/decode` | `qwen3.6-27b` | `decode` | `2/1/1` | - | No | `a3-qwen36-tp2-long-context-source.json` | 2 | 2 | 2/2 (100.0%) | 2/2 (100.0%) | 0.80% | 0.80% |
| `a3/qwen36_27b_tp4_128k_20261030/decode` | `qwen3.6-27b` | `decode` | `4/1/1` | - | No | `a3-qwen36-tp4-long-context-source.json` | 19 | 19 | 19/19 (100.0%) | 19/19 (100.0%) | 3.25% | 3.16% |
| `a3/qwen38_27b_tp2_128k_20261030/decode` | `qwen3.8-27b` | `decode` | `2/1/1` | - | No | `a3-qwen38-tp2-long-context-source.json` | 17 | 17 | 17/17 (100.0%) | 17/17 (100.0%) | 1.80% | 1.89% |
| `a3/qwen38_27b_tp4_128k_20261030/decode` | `qwen3.8-27b` | `decode` | `4/1/1` | - | No | `a3-qwen38-tp4-long-context-source.json` | 6 | 6 | 6/6 (100.0%) | 6/6 (100.0%) | 3.16% | 2.52% |
| `a3/wave23_dsv4f_tp8_ablation_20261030/dsv4f_tp8_mtp0_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | 0 | No | `decode-v4flash-a3-tp8-c4.json` | 12 | 12 | 11/12 (91.7%) | 11/12 (91.7%) | 7.35% | 4.49% |
| `a3/wave23_dsv4f_tp8_ablation_20261030/dsv4f_tp8_mtp1_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | 1 | No | `decode-v4flash-a3-tp8-c4.json` | 17 | 17 | 16/17 (94.1%) | 12/17 (70.6%) | 11.16% | 8.62% |
| `a3/wave23_dsv4f_tp8_ablation_20261030/dsv4f_tp8_mtp1_mb2048_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | 1 | No | `decode-v4flash-a3-tp8-c4.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 8.04% | 8.04% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp16_mtp3_decode` | `qwen3.5-35b-a3b` | `decode` | `16/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 18 | 18 | 12/18 (66.7%) | 9/18 (50.0%) | 9.97% | 10.00% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp0_mb8192_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 0 | Yes | `a3-qwen35-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 17/18 (94.4%) | 7.55% | 7.96% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp1_mb8192_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 1 | Yes | `a3-qwen35-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 16/18 (88.9%) | 7.72% | 8.35% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp3_mb2048_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 12 | 12 | 12/12 (100.0%) | 11/12 (91.7%) | 5.74% | 5.31% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp3_mb4096_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 12 | 12 | 12/12 (100.0%) | 11/12 (91.7%) | 5.52% | 5.05% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp3_mb8192_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 20 | 20 | 20/20 (100.0%) | 15/20 (75.0%) | 7.19% | 6.30% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp0_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 0 | Yes | `a3-qwen36-tp4-long-context-source.json` | 18 | 18 | 17/18 (94.4%) | 15/18 (83.3%) | 6.29% | 5.38% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp1_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 1 | Yes | `a3-qwen36-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 15/18 (83.3%) | 5.55% | 4.67% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp3_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen36-tp4-long-context-source.json` | 21 | 21 | 21/21 (100.0%) | 15/21 (71.4%) | 5.90% | 5.34% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp3_mb2048_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen36-tp4-long-context-source.json` | 10 | 10 | 10/10 (100.0%) | 9/10 (90.0%) | 3.38% | 2.46% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8dp2_mtp3_decode` | `qwen3.6-27b` | `decode` | `8/2/1` | 3 | Yes | `a3-qwen36-tp4-long-context-source.json` | 16 | 16 | 16/16 (100.0%) | 14/16 (87.5%) | 4.62% | 4.36% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp0_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 0 | Yes | `a3-qwen38-tp4-long-context-source.json` | 18 | 18 | 17/18 (94.4%) | 14/18 (77.8%) | 6.43% | 5.68% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp1_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 1 | Yes | `a3-qwen38-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 15/18 (83.3%) | 5.61% | 4.70% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp3_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen38-tp4-long-context-source.json` | 21 | 21 | 21/21 (100.0%) | 17/21 (81.0%) | 5.86% | 5.24% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8dp2_mtp3_decode` | `qwen3.8-27b` | `decode` | `8/2/1` | 3 | Yes | `a3-qwen38-tp4-long-context-source.json` | 16 | 16 | 16/16 (100.0%) | 14/16 (87.5%) | 5.04% | 4.09% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp0_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 0 | No | `longctx-a5-qwen36-tp8-source-model.json` | 21 | 21 | 21/21 (100.0%) | 17/21 (81.0%) | 5.62% | 5.12% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp3_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 3 | No | `longctx-a5-qwen36-tp8-source-model.json` | 28 | 28 | 28/28 (100.0%) | 23/28 (82.1%) | 5.57% | 4.59% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp0_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 0 | No | `longctx-a5-qwen36-tp8-source-model.json` | 21 | 21 | 21/21 (100.0%) | 17/21 (81.0%) | 5.20% | 4.39% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp3_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 3 | No | `longctx-a5-qwen36-tp8-source-model.json` | 28 | 28 | 28/28 (100.0%) | 25/28 (89.3%) | 4.75% | 3.55% |
