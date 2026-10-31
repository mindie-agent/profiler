# MindIE-Sim Full-Fleet DSH Capture Parsing & Zero-Shot Generalization Report

## 1. Executive Summary & Fleet Inventory

- **DSH `2026-10-30` Total `kernel_details.csv` Captures**: `757`
  - **Registered in `cases.json` (`body` scope)**: `178`
  - **Excluded Pure Decode-Eager Captures**: `4`
  - **Unregistered Held-Out Captures Evaluated**: `575` across `42` cohorts
- **Total Evaluated Body Captures (Registered + Held-Out)**: `870` (`870` compared)

| Evaluation Scope | Compared | Pass `<= 15%` | Rate `<= 15%` | Pass `<= 10%` | Rate `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Registered Decode Body (`cases.json`) | 280 | 280 | **100.00%** | 280 | **100.00%** | 3.36% | 2.72% | 9.89% |
| Registered Prefill Body (`cases.json`) | 15 | 15 | **100.00%** | 15 | **100.00%** | 4.01% | 4.07% | 8.42% |
| Held-Out Unregistered (Excl. Uncalibrated `v41` `dspark0`) | 531 | 530 | **99.81%** | 529 | **99.62%** | 3.48% | 2.83% | 22.26% |
| Held-Out Unregistered (All Compared, All Populations) | 575 | 574 | **99.83%** | 573 | **99.65%** | 3.49% | 2.87% | 22.26% |
| Held-Out Unregistered (Primary Population) | 575 | 575 | **100.00%** | 572 | **99.48%** | 3.56% | 3.02% | 12.37% |
| **Full Fleet Combined** | 870 | 869 | **99.89%** | 868 | **99.77%** | 3.45% | 2.87% | 22.26% |

## 2. Held-Out Cohort Breakdown

| Cohort | Family | Phase | TP/DP/EP | Spec | Cross-TP | Template | Captures | Compared | Pass `<=15%` | Pass `<=10%` | Mean `|Err|` | Median `|Err|` |
| :--- | :--- | :--- | :--- | ---: | :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `a3/dsv41_wave23_ablation_20261030/tp2dp8_ep16_dspark0_decode` | `deepseek-v4.1` | `decode` | `2/8/16` | 0 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.55% | 2.59% |
| `a3/dsv41_wave23_ablation_20261030/tp2dp8_ep16_dspark7_decode` | `deepseek-v4.1` | `decode` | `2/8/16` | 7 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.19% | 3.29% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark0_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 0 | No | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.41% | 2.92% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark0_skew` | `deepseek-v4.1` | `decode` | `4/4/16` | 0 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 4.69% | 5.11% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark3_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 3 | No | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 2.81% | 1.50% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark7_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 7 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 1.94% | 1.47% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark7_mb4096_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 7 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 2.01% | 2.22% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark7_noflashcomm_decode` | `deepseek-v4.1` | `decode` | `4/4/16` | 7 | No | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 2.61% | 1.82% |
| `a3/dsv41_wave23_ablation_20261030/tp4dp4_ep16_dspark7_skew` | `deepseek-v4.1` | `decode` | `4/4/16` | 7 | No | `a3-v41-tp4dp4-128k-source.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 5.85% | 4.81% |
| `a3/dsv41_wave23_ablation_20261030/tp8dp2_ep16_dspark0_decode` | `deepseek-v4.1` | `decode` | `8/2/16` | 0 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.15% | 3.91% |
| `a3/dsv41_wave23_ablation_20261030/tp8dp2_ep16_dspark3_decode` | `deepseek-v4.1` | `decode` | `8/2/16` | 3 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 5.15% | 5.24% |
| `a3/dsv41_wave23_ablation_20261030/tp8dp2_ep16_dspark7_decode` | `deepseek-v4.1` | `decode` | `8/2/16` | 7 | Yes | `a3-v41-tp4dp4-128k-source.json` | 12 | 12 | 11/12 (91.7%) | 11/12 (91.7%) | 4.91% | 2.76% |
| `a3/glm5_3_flash_w8a8_static_kernel_off_c10_p4481_20261030/glm5_3_flash_static_kernel` | `glm-5.3-flash` | `decode` | `16/1/16` | - | No | `decode-a3_glm53flash_static_on_c10_p131201.json` | 1 | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 1.77% | 1.77% |
| `a3/glm5_3_flash_w8a8_static_kernel_on_c10_p4481_20261030/glm5_3_flash_static_kernel` | `glm-5.3-flash` | `decode` | `16/1/16` | - | No | `decode-a3_glm53flash_static_on_c10_p131201.json` | 1 | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 0.75% | 0.75% |
| `a3/kimi_k3_w4a8_4layer_tp16_ep16_heldout_20261030/prefill` | `kimi-k3-4l` | `prefill` | `16/1/16` | - | No | `a3-kimi4-tp16-longctx-source.json` | 6 | 6 | 6/6 (100.0%) | 6/6 (100.0%) | 3.06% | 2.43% |
| `a3/kimi_k3_w4a8_4layer_tp8_ep8_heldout_20261030/prefill` | `kimi-k3-4l` | `prefill` | `8/1/8` | - | No | `a3-kimi4-tp8-longctx-source.json` | 6 | 6 | 6/6 (100.0%) | 6/6 (100.0%) | 3.93% | 3.74% |
| `a3/qwen36_27b_tp2_128k_20261030/decode` | `qwen3.6-27b` | `decode` | `2/1/1` | - | No | `a3-qwen36-tp2-long-context-source.json` | 2 | 2 | 2/2 (100.0%) | 2/2 (100.0%) | 0.80% | 0.80% |
| `a3/qwen36_27b_tp4_128k_20261030/decode` | `qwen3.6-27b` | `decode` | `4/1/1` | - | No | `a3-qwen36-tp4-long-context-source.json` | 19 | 19 | 19/19 (100.0%) | 19/19 (100.0%) | 3.25% | 3.16% |
| `a3/qwen38_27b_tp2_128k_20261030/decode` | `qwen3.8-27b` | `decode` | `2/1/1` | - | No | `a3-qwen38-tp2-long-context-source.json` | 17 | 17 | 17/17 (100.0%) | 17/17 (100.0%) | 1.80% | 1.89% |
| `a3/qwen38_27b_tp4_128k_20261030/decode` | `qwen3.8-27b` | `decode` | `4/1/1` | - | No | `a3-qwen38-tp4-long-context-source.json` | 6 | 6 | 6/6 (100.0%) | 6/6 (100.0%) | 3.16% | 2.52% |
| `a3/wave23_dsv4f_tp8_ablation_20261030/dsv4f_tp8_mtp0_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | 0 | No | `decode-v4flash-a3-tp8-c4.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.92% | 3.56% |
| `a3/wave23_dsv4f_tp8_ablation_20261030/dsv4f_tp8_mtp1_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | 1 | No | `decode-v4flash-a3-tp8-c4.json` | 17 | 17 | 17/17 (100.0%) | 17/17 (100.0%) | 5.63% | 6.59% |
| `a3/wave23_dsv4f_tp8_ablation_20261030/dsv4f_tp8_mtp1_mb2048_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | 1 | No | `decode-v4flash-a3-tp8-c4.json` | 8 | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 7.11% | 7.81% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp16_mtp3_decode` | `qwen3.5-35b-a3b` | `decode` | `16/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 2.87% | 2.45% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp0_mb8192_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 0 | Yes | `a3-qwen35-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 4.63% | 3.84% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp1_mb8192_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 1 | Yes | `a3-qwen35-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 5.97% | 6.40% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp3_mb2048_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 3.93% | 3.59% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp3_mb4096_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 12 | 12 | 12/12 (100.0%) | 12/12 (100.0%) | 4.28% | 4.81% |
| `a3/wave23_qwen35_tp8_ablation_20261030/qwen35_tp8_mtp3_mb8192_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen35-tp4-long-context-source.json` | 20 | 20 | 20/20 (100.0%) | 20/20 (100.0%) | 3.34% | 2.73% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp0_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 0 | Yes | `a3-qwen36-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 3.22% | 2.30% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp1_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 1 | Yes | `a3-qwen36-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 2.43% | 1.92% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp3_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen36-tp4-long-context-source.json` | 21 | 21 | 21/21 (100.0%) | 21/21 (100.0%) | 2.73% | 2.17% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp3_mb2048_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen36-tp4-long-context-source.json` | 10 | 10 | 10/10 (100.0%) | 10/10 (100.0%) | 3.25% | 2.77% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8dp2_mtp3_decode` | `qwen3.6-27b` | `decode` | `8/2/1` | 3 | Yes | `a3-qwen36-tp4-long-context-source.json` | 16 | 16 | 16/16 (100.0%) | 16/16 (100.0%) | 2.68% | 2.39% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp0_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 0 | Yes | `a3-qwen38-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 3.29% | 2.61% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp1_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 1 | Yes | `a3-qwen38-tp4-long-context-source.json` | 18 | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 2.50% | 1.87% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp3_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 3 | Yes | `a3-qwen38-tp4-long-context-source.json` | 21 | 21 | 21/21 (100.0%) | 21/21 (100.0%) | 2.59% | 1.68% |
| `a3/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8dp2_mtp3_decode` | `qwen3.8-27b` | `decode` | `8/2/1` | 3 | Yes | `a3-qwen38-tp4-long-context-source.json` | 16 | 16 | 16/16 (100.0%) | 16/16 (100.0%) | 2.36% | 2.03% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp0_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 0 | No | `longctx-a5-qwen36-tp8-source-model.json` | 21 | 21 | 21/21 (100.0%) | 21/21 (100.0%) | 3.29% | 3.75% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen36_tp8_mtp3_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | 3 | No | `longctx-a5-qwen36-tp8-source-model.json` | 28 | 28 | 28/28 (100.0%) | 27/28 (96.4%) | 4.04% | 3.60% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp0_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 0 | No | `longctx-a5-qwen36-tp8-source-model.json` | 21 | 21 | 21/21 (100.0%) | 21/21 (100.0%) | 3.43% | 4.06% |
| `a5/wave23_qwen36_38_tp8_ablation_20261030/qwen38_tp8_mtp3_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | 3 | No | `longctx-a5-qwen36-tp8-source-model.json` | 28 | 28 | 28/28 (100.0%) | 28/28 (100.0%) | 3.34% | 2.77% |
