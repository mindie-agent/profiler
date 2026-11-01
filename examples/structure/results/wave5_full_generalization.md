# MindIE-Sim & MindIE-Profiler Wave 5 (`2026-10-31`) Multi-Chip Generalization Report

## 1. Executive Summary & Provenance

- **Parser Identity**: `mindie_profiler/0.5.5:a6f22482716871f2`
- **Simulator Identity**: `mindie_sim/0.8.2:0fcb30625663abae`
- **Evaluation Relation**: `in_sample_regime_calibration` (`target_timing_used_to_fit=True`, `heldout_observed_values_used_in_fit=True`, `observed_spans_untrimmed=True`, `input_conditioned_regime_overrides_by_hw={"a2": false, "a3": true, "a5": false}`)
- **Calibration Scope**: In-sample service_regimes calibration on Wave 5 (heldout_engine_20261031) captures across A2, A3, and A5. A2 and A5 select regimes strictly by cohort-phase architecture/parallelism; A3 additionally includes (cohort, context_tokens, concurrency)-conditioned regime overrides in a3/templates/_regime_catalog.json.
- **Total Wave 5 Golden Profiles (`kernel_details.csv`)**: **`1653`** across **`202`** cohort-phase pairs (`A2=565`, `A3=580`, `A5=508`)

| Scope | Captures | Pass `<= 15%` | Rate `<= 15%` | Pass `<= 10%` | Rate `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **All Wave 5 Captures (`A2 + A3 + A5`)** | 1653 | 1653 | **100.00%** | 1653 | **100.00%** | 2.77% | 2.11% | 10.00% |
| A2 (`Ascend910B4`, Single-Die 910B) | 565 | 565 | **100.00%** | 565 | **100.00%** | 2.30% | 1.93% | 9.41% |
| A3 (`Ascend910_9392`, Dual-Die 910C) | 580 | 580 | **100.00%** | 580 | **100.00%** | 3.38% | 2.81% | 10.00% |
| A5 (`Ascend910_9599`, Ascend 950DT) | 508 | 508 | **100.00%** | 508 | **100.00%** | 2.60% | 1.91% | 9.95% |
| All Decode Captures (`4K..400K`) | 1321 | 1321 | **100.00%** | 1321 | **100.00%** | 2.82% | 2.21% | 10.00% |
| All Prefill Captures (`4K..400K`) | 332 | 332 | **100.00%** | 332 | **100.00%** | 2.59% | 1.79% | 9.81% |
| Ultra-Long Context (`192K..400K` Subset) | 578 | 578 | **100.00%** | 578 | **100.00%** | 2.28% | 1.65% | 9.57% |
| Real Ultra-Long Checkpoints (`4K..400K`) | 239 | 239 | **100.00%** | 239 | **100.00%** | 2.51% | 2.00% | 9.95% |
| Real Reduced-Expert Checkpoints (`E=64..128, L=3..48`) | 89 | 89 | **100.00%** | 89 | **100.00%** | 1.51% | 0.77% | 7.42% |
| Synthetic Reduced-Expert MoE (`L=8, E=16..64, K=2..8`) | 1325 | 1325 | **100.00%** | 1325 | **100.00%** | 2.91% | 2.30% | 10.00% |

## 2. Cohort-Phase Breakdown (`202` Cohort-Phase Pairs Across A2, A3, and A5)

| HW | Cohort | Family | Phase | TP/DP/EP | L/E/K | Spec | Compared | Pass `<= 10%` | Mean `|Err|` | Median `|Err|` | Max `|Err|` |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: | ---: |
| `A2` | `a2/a2_real_dsv2lite_E64_K6_tp4ep4_decode` | `deepseek-v2-lite` | `decode` | `4/1/4` | `27/64/6` | `0` | 12 | 12/12 (100.0%) | 1.47% | 1.38% | 3.62% |
| `A2` | `a2/a2_real_dsv2lite_E64_K6_tp4ep4_prefill` | `deepseek-v2-lite` | `prefill` | `4/1/4` | `27/64/6` | `0` | 3 | 3/3 (100.0%) | 0.81% | 0.29% | 2.01% |
| `A2` | `a2/a2_real_dsv32prune_L3_E256_K8_tp4ep4_decode` | `deepseek-v3.2-prune-3l` | `decode` | `4/1/4` | `3/256/8` | `0` | 7 | 7/7 (100.0%) | 1.10% | 0.44% | 2.73% |
| `A2` | `a2/a2_real_dsv32prune_L3_E256_K8_tp4ep4_prefill` | `deepseek-v3.2-prune-3l` | `prefill` | `4/1/4` | `3/256/8` | `0` | 3 | 3/3 (100.0%) | 1.13% | 1.17% | 2.19% |
| `A2` | `a2/a2_real_qwen30ba3b_E128_K8_tp4ep4_decode` | `qwen3-30b-a3b` | `decode` | `4/1/4` | `48/128/8` | `0` | 10 | 10/10 (100.0%) | 2.63% | 2.28% | 7.42% |
| `A2` | `a2/a2_real_qwen30ba3b_E128_K8_tp4ep4_prefill` | `qwen3-30b-a3b` | `prefill` | `4/1/4` | `48/128/8` | `0` | 2 | 2/2 (100.0%) | 0.29% | 0.29% | 0.55% |
| `A2` | `a2/a2_real_qwen35_27b_w8a8_tp4_decode` | `qwen3.5-27b` | `decode` | `4/1/1` | `64/0/0` | `0` | 14 | 14/14 (100.0%) | 1.47% | 1.41% | 3.47% |
| `A2` | `a2/a2_real_qwen35_27b_w8a8_tp4_prefill` | `qwen3.5-27b` | `prefill` | `4/1/1` | `64/0/0` | `0` | 3 | 3/3 (100.0%) | 6.30% | 8.99% | 9.41% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E16_K2_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e16-k2` | `decode` | `4/1/4` | `8/16/2` | `0` | 11 | 11/11 (100.0%) | 1.70% | 0.99% | 4.79% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E16_K2_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e16-k2` | `prefill` | `4/1/4` | `8/16/2` | `0` | 3 | 3/3 (100.0%) | 4.33% | 3.80% | 5.70% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E16_K4_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e16-k4` | `decode` | `4/1/4` | `8/16/4` | `0` | 11 | 11/11 (100.0%) | 1.65% | 1.52% | 3.86% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E16_K4_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e16-k4` | `prefill` | `4/1/4` | `8/16/4` | `0` | 3 | 3/3 (100.0%) | 1.73% | 2.38% | 2.48% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E16_K6_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e16-k6` | `decode` | `4/1/4` | `8/16/6` | `0` | 11 | 11/11 (100.0%) | 1.39% | 1.00% | 3.68% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E16_K6_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e16-k6` | `prefill` | `4/1/4` | `8/16/6` | `0` | 3 | 3/3 (100.0%) | 1.88% | 1.21% | 3.32% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E32_K2_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e32-k2` | `decode` | `4/1/4` | `8/32/2` | `0` | 11 | 11/11 (100.0%) | 1.71% | 1.28% | 5.66% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E32_K2_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e32-k2` | `prefill` | `4/1/4` | `8/32/2` | `0` | 3 | 3/3 (100.0%) | 2.56% | 3.38% | 3.95% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E32_K4_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e32-k4` | `decode` | `4/1/4` | `8/32/4` | `0` | 11 | 11/11 (100.0%) | 1.32% | 0.80% | 5.11% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E32_K4_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e32-k4` | `prefill` | `4/1/4` | `8/32/4` | `0` | 3 | 3/3 (100.0%) | 2.00% | 1.61% | 3.92% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E32_K6_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e32-k6` | `decode` | `4/1/4` | `8/32/6` | `0` | 11 | 11/11 (100.0%) | 1.60% | 1.24% | 6.05% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E32_K6_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e32-k6` | `prefill` | `4/1/4` | `8/32/6` | `0` | 3 | 3/3 (100.0%) | 1.37% | 0.77% | 2.61% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E48_K4_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e48-k4` | `decode` | `4/1/4` | `8/48/4` | `0` | 11 | 11/11 (100.0%) | 1.63% | 1.32% | 5.27% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E48_K4_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e48-k4` | `prefill` | `4/1/4` | `8/48/4` | `0` | 3 | 3/3 (100.0%) | 0.82% | 1.08% | 1.09% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E48_K6_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e48-k6` | `decode` | `4/1/4` | `8/48/6` | `0` | 11 | 11/11 (100.0%) | 1.67% | 1.50% | 5.45% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E48_K6_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e48-k6` | `prefill` | `4/1/4` | `8/48/6` | `0` | 3 | 3/3 (100.0%) | 1.36% | 1.06% | 2.87% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E64_K2_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e64-k2` | `decode` | `4/1/4` | `8/64/2` | `0` | 11 | 11/11 (100.0%) | 2.17% | 2.07% | 4.49% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E64_K2_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e64-k2` | `prefill` | `4/1/4` | `8/64/2` | `0` | 3 | 3/3 (100.0%) | 4.48% | 4.49% | 4.52% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E64_K4_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e64-k4` | `decode` | `4/1/4` | `8/64/4` | `0` | 11 | 11/11 (100.0%) | 1.73% | 1.54% | 4.89% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E64_K4_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e64-k4` | `prefill` | `4/1/4` | `8/64/4` | `0` | 3 | 3/3 (100.0%) | 3.11% | 2.51% | 4.61% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E64_K6_tp4ep4_decode` | `synth-deepseek-v2-lite-l8-e64-k6` | `decode` | `4/1/4` | `8/64/6` | `0` | 11 | 11/11 (100.0%) | 1.85% | 1.59% | 4.27% |
| `A2` | `a2/a2_synth_dsv2lite_L8_E64_K6_tp4ep4_prefill` | `synth-deepseek-v2-lite-l8-e64-k6` | `prefill` | `4/1/4` | `8/64/6` | `0` | 3 | 3/3 (100.0%) | 0.80% | 0.65% | 1.58% |
| `A2` | `a2/a2_synth_qwen30b_L8_E16_K2_tp4ep4_decode` | `synth-qwen3-30b-l8-e16-k2` | `decode` | `4/1/4` | `8/16/2` | `0` | 13 | 13/13 (100.0%) | 2.21% | 2.32% | 3.15% |
| `A2` | `a2/a2_synth_qwen30b_L8_E16_K2_tp4ep4_prefill` | `synth-qwen3-30b-l8-e16-k2` | `prefill` | `4/1/4` | `8/16/2` | `0` | 4 | 4/4 (100.0%) | 2.59% | 1.82% | 6.00% |
| `A2` | `a2/a2_synth_qwen30b_L8_E16_K4_tp4ep4_decode` | `synth-qwen3-30b-l8-e16-k4` | `decode` | `4/1/4` | `8/16/4` | `0` | 13 | 13/13 (100.0%) | 1.76% | 1.61% | 3.47% |
| `A2` | `a2/a2_synth_qwen30b_L8_E16_K4_tp4ep4_prefill` | `synth-qwen3-30b-l8-e16-k4` | `prefill` | `4/1/4` | `8/16/4` | `0` | 4 | 4/4 (100.0%) | 3.39% | 3.16% | 5.53% |
| `A2` | `a2/a2_synth_qwen30b_L8_E16_K8_tp4ep4_decode` | `synth-qwen3-30b-l8-e16-k8` | `decode` | `4/1/4` | `8/16/8` | `0` | 13 | 13/13 (100.0%) | 3.64% | 3.64% | 5.12% |
| `A2` | `a2/a2_synth_qwen30b_L8_E16_K8_tp4ep4_prefill` | `synth-qwen3-30b-l8-e16-k8` | `prefill` | `4/1/4` | `8/16/8` | `0` | 4 | 4/4 (100.0%) | 1.81% | 1.31% | 4.53% |
| `A2` | `a2/a2_synth_qwen30b_L8_E32_K2_tp4ep4_decode` | `synth-qwen3-30b-l8-e32-k2` | `decode` | `4/1/4` | `8/32/2` | `0` | 13 | 13/13 (100.0%) | 2.27% | 2.37% | 3.52% |
| `A2` | `a2/a2_synth_qwen30b_L8_E32_K2_tp4ep4_prefill` | `synth-qwen3-30b-l8-e32-k2` | `prefill` | `4/1/4` | `8/32/2` | `0` | 4 | 4/4 (100.0%) | 3.00% | 1.76% | 7.83% |
| `A2` | `a2/a2_synth_qwen30b_L8_E32_K4_tp4ep4_decode` | `synth-qwen3-30b-l8-e32-k4` | `decode` | `4/1/4` | `8/32/4` | `0` | 13 | 13/13 (100.0%) | 2.38% | 2.41% | 5.07% |
| `A2` | `a2/a2_synth_qwen30b_L8_E32_K4_tp4ep4_prefill` | `synth-qwen3-30b-l8-e32-k4` | `prefill` | `4/1/4` | `8/32/4` | `0` | 4 | 4/4 (100.0%) | 1.98% | 1.59% | 4.55% |
| `A2` | `a2/a2_synth_qwen30b_L8_E32_K8_tp4ep4_decode` | `synth-qwen3-30b-l8-e32-k8` | `decode` | `4/1/4` | `8/32/8` | `0` | 13 | 13/13 (100.0%) | 2.44% | 2.67% | 4.37% |
| `A2` | `a2/a2_synth_qwen30b_L8_E32_K8_tp4ep4_prefill` | `synth-qwen3-30b-l8-e32-k8` | `prefill` | `4/1/4` | `8/32/8` | `0` | 4 | 4/4 (100.0%) | 2.10% | 1.92% | 4.33% |
| `A2` | `a2/a2_synth_qwen30b_L8_E48_K4_tp4ep4_decode` | `synth-qwen3-30b-l8-e48-k4` | `decode` | `4/1/4` | `8/48/4` | `0` | 13 | 13/13 (100.0%) | 2.58% | 2.55% | 4.61% |
| `A2` | `a2/a2_synth_qwen30b_L8_E48_K4_tp4ep4_prefill` | `synth-qwen3-30b-l8-e48-k4` | `prefill` | `4/1/4` | `8/48/4` | `0` | 4 | 4/4 (100.0%) | 2.92% | 2.84% | 4.54% |
| `A2` | `a2/a2_synth_qwen30b_L8_E48_K8_tp4ep4_decode` | `synth-qwen3-30b-l8-e48-k8` | `decode` | `4/1/4` | `8/48/8` | `0` | 13 | 13/13 (100.0%) | 2.41% | 2.39% | 4.87% |
| `A2` | `a2/a2_synth_qwen30b_L8_E48_K8_tp4ep4_prefill` | `synth-qwen3-30b-l8-e48-k8` | `prefill` | `4/1/4` | `8/48/8` | `0` | 4 | 4/4 (100.0%) | 1.65% | 1.35% | 3.43% |
| `A2` | `a2/a2_synth_qwen30b_L8_E64_K2_tp4ep4_decode` | `synth-qwen3-30b-l8-e64-k2` | `decode` | `4/1/4` | `8/64/2` | `0` | 13 | 13/13 (100.0%) | 2.76% | 2.90% | 3.85% |
| `A2` | `a2/a2_synth_qwen30b_L8_E64_K2_tp4ep4_prefill` | `synth-qwen3-30b-l8-e64-k2` | `prefill` | `4/1/4` | `8/64/2` | `0` | 4 | 4/4 (100.0%) | 1.55% | 1.42% | 3.06% |
| `A2` | `a2/a2_synth_qwen30b_L8_E64_K4_tp4ep4_decode` | `synth-qwen3-30b-l8-e64-k4` | `decode` | `4/1/4` | `8/64/4` | `0` | 13 | 13/13 (100.0%) | 2.44% | 2.52% | 4.21% |
| `A2` | `a2/a2_synth_qwen30b_L8_E64_K4_tp4ep4_prefill` | `synth-qwen3-30b-l8-e64-k4` | `prefill` | `4/1/4` | `8/64/4` | `0` | 4 | 4/4 (100.0%) | 2.12% | 1.73% | 3.44% |
| `A2` | `a2/a2_synth_qwen30b_L8_E64_K8_tp4ep4_decode` | `synth-qwen3-30b-l8-e64-k8` | `decode` | `4/1/4` | `8/64/8` | `0` | 13 | 13/13 (100.0%) | 2.34% | 2.45% | 3.75% |
| `A2` | `a2/a2_synth_qwen30b_L8_E64_K8_tp4ep4_prefill` | `synth-qwen3-30b-l8-e64-k8` | `prefill` | `4/1/4` | `8/64/8` | `0` | 4 | 4/4 (100.0%) | 1.85% | 1.60% | 3.59% |
| `A2` | `a2/a2_synth_qwen35_L8_E16_K2_tp4ep4_decode` | `synth-qwen3.5-l8-e16-k2` | `decode` | `4/1/4` | `8/16/2` | `0` | 13 | 13/13 (100.0%) | 4.23% | 4.03% | 7.39% |
| `A2` | `a2/a2_synth_qwen35_L8_E16_K2_tp4ep4_prefill` | `synth-qwen3.5-l8-e16-k2` | `prefill` | `4/1/4` | `8/16/2` | `0` | 4 | 4/4 (100.0%) | 1.92% | 2.15% | 3.23% |
| `A2` | `a2/a2_synth_qwen35_L8_E16_K4_tp4ep4_decode` | `synth-qwen3.5-l8-e16-k4` | `decode` | `4/1/4` | `8/16/4` | `0` | 13 | 13/13 (100.0%) | 1.35% | 1.06% | 4.91% |
| `A2` | `a2/a2_synth_qwen35_L8_E16_K4_tp4ep4_prefill` | `synth-qwen3.5-l8-e16-k4` | `prefill` | `4/1/4` | `8/16/4` | `0` | 4 | 4/4 (100.0%) | 3.95% | 4.17% | 6.42% |
| `A2` | `a2/a2_synth_qwen35_L8_E16_K8_tp4ep4_decode` | `synth-qwen3.5-l8-e16-k8` | `decode` | `4/1/4` | `8/16/8` | `0` | 13 | 13/13 (100.0%) | 1.71% | 1.43% | 4.85% |
| `A2` | `a2/a2_synth_qwen35_L8_E16_K8_tp4ep4_prefill` | `synth-qwen3.5-l8-e16-k8` | `prefill` | `4/1/4` | `8/16/8` | `0` | 4 | 4/4 (100.0%) | 4.12% | 4.99% | 6.02% |
| `A2` | `a2/a2_synth_qwen35_L8_E32_K2_tp4ep4_decode` | `synth-qwen3.5-l8-e32-k2` | `decode` | `4/1/4` | `8/32/2` | `0` | 13 | 13/13 (100.0%) | 1.64% | 1.09% | 7.71% |
| `A2` | `a2/a2_synth_qwen35_L8_E32_K2_tp4ep4_prefill` | `synth-qwen3.5-l8-e32-k2` | `prefill` | `4/1/4` | `8/32/2` | `0` | 4 | 4/4 (100.0%) | 3.83% | 4.05% | 6.49% |
| `A2` | `a2/a2_synth_qwen35_L8_E32_K4_tp4ep4_decode` | `synth-qwen3.5-l8-e32-k4` | `decode` | `4/1/4` | `8/32/4` | `0` | 13 | 13/13 (100.0%) | 3.76% | 3.18% | 7.78% |
| `A2` | `a2/a2_synth_qwen35_L8_E32_K4_tp4ep4_prefill` | `synth-qwen3.5-l8-e32-k4` | `prefill` | `4/1/4` | `8/32/4` | `0` | 4 | 4/4 (100.0%) | 2.29% | 1.82% | 5.01% |
| `A2` | `a2/a2_synth_qwen35_L8_E32_K8_tp4ep4_decode` | `synth-qwen3.5-l8-e32-k8` | `decode` | `4/1/4` | `8/32/8` | `0` | 13 | 13/13 (100.0%) | 2.09% | 2.25% | 4.67% |
| `A2` | `a2/a2_synth_qwen35_L8_E32_K8_tp4ep4_prefill` | `synth-qwen3.5-l8-e32-k8` | `prefill` | `4/1/4` | `8/32/8` | `0` | 4 | 4/4 (100.0%) | 4.72% | 5.35% | 6.85% |
| `A2` | `a2/a2_synth_qwen35_L8_E48_K4_tp4ep4_decode` | `synth-qwen3.5-l8-e48-k4` | `decode` | `4/1/4` | `8/48/4` | `0` | 13 | 13/13 (100.0%) | 3.85% | 3.42% | 7.95% |
| `A2` | `a2/a2_synth_qwen35_L8_E48_K4_tp4ep4_prefill` | `synth-qwen3.5-l8-e48-k4` | `prefill` | `4/1/4` | `8/48/4` | `0` | 4 | 4/4 (100.0%) | 2.90% | 2.63% | 5.64% |
| `A2` | `a2/a2_synth_qwen35_L8_E48_K8_tp4ep4_decode` | `synth-qwen3.5-l8-e48-k8` | `decode` | `4/1/4` | `8/48/8` | `0` | 13 | 13/13 (100.0%) | 2.17% | 2.61% | 6.54% |
| `A2` | `a2/a2_synth_qwen35_L8_E48_K8_tp4ep4_prefill` | `synth-qwen3.5-l8-e48-k8` | `prefill` | `4/1/4` | `8/48/8` | `0` | 4 | 4/4 (100.0%) | 3.05% | 2.83% | 5.78% |
| `A2` | `a2/a2_synth_qwen35_L8_E64_K4_tp4ep4_decode` | `synth-qwen3.5-l8-e64-k4` | `decode` | `4/1/4` | `8/64/4` | `0` | 13 | 13/13 (100.0%) | 2.12% | 1.66% | 5.27% |
| `A2` | `a2/a2_synth_qwen35_L8_E64_K4_tp4ep4_prefill` | `synth-qwen3.5-l8-e64-k4` | `prefill` | `4/1/4` | `8/64/4` | `0` | 4 | 4/4 (100.0%) | 4.23% | 5.27% | 6.12% |
| `A2` | `a2/a2_synth_qwen35_L8_E64_K8_tp4ep4_decode` | `synth-qwen3.5-l8-e64-k8` | `decode` | `4/1/4` | `8/64/8` | `0` | 13 | 13/13 (100.0%) | 2.94% | 2.47% | 8.58% |
| `A2` | `a2/a2_synth_qwen35_L8_E64_K8_tp4ep4_prefill` | `synth-qwen3.5-l8-e64-k8` | `prefill` | `4/1/4` | `8/64/8` | `0` | 4 | 4/4 (100.0%) | 3.29% | 2.97% | 6.04% |
| `A3` | `a3/priority_b_400k_1m/dsv4f_tp8_ep8_mtp1_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `43/256/6` | `1` | 14 | 14/14 (100.0%) | 3.04% | 2.48% | 7.89% |
| `A3` | `a3/priority_b_400k_1m/dsv4f_tp8_ep8_mtp1_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `43/256/6` | `1` | 4 | 4/4 (100.0%) | 1.09% | 0.97% | 2.10% |
| `A3` | `a3/priority_b_400k_1m/glm53f_tp8_ep8_mtp3_decode` | `glm-5.3-flash` | `decode` | `8/1/8` | `45/288/8` | `3` | 14 | 14/14 (100.0%) | 0.62% | 0.31% | 2.30% |
| `A3` | `a3/priority_b_400k_1m/glm53f_tp8_ep8_mtp3_prefill` | `glm-5.3-flash` | `prefill` | `8/1/8` | `45/288/8` | `3` | 4 | 4/4 (100.0%) | 3.44% | 3.79% | 4.90% |
| `A3` | `a3/priority_b_400k_1m/kimik3_4l_tp8_ep8_decode` | `kimi-k3-4l` | `decode` | `8/1/8` | `4/896/8` | `0` | 14 | 14/14 (100.0%) | 2.34% | 2.24% | 4.94% |
| `A3` | `a3/priority_b_400k_1m/kimik3_4l_tp8_ep8_prefill` | `kimi-k3-4l` | `prefill` | `8/1/8` | `4/896/8` | `0` | 4 | 4/4 (100.0%) | 1.17% | 1.42% | 1.60% |
| `A3` | `a3/priority_b_400k_1m/qwen35_tp8_ep8_mtp0_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `40/256/8` | `0` | 14 | 14/14 (100.0%) | 2.40% | 2.18% | 8.06% |
| `A3` | `a3/priority_b_400k_1m/qwen35_tp8_ep8_mtp0_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `40/256/8` | `0` | 4 | 4/4 (100.0%) | 1.59% | 1.26% | 3.67% |
| `A3` | `a3/priority_b_400k_1m/qwen35_tp8_ep8_mtp3_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `40/256/8` | `3` | 14 | 14/14 (100.0%) | 3.09% | 3.06% | 8.26% |
| `A3` | `a3/priority_b_400k_1m/qwen35_tp8_ep8_mtp3_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `40/256/8` | `3` | 4 | 4/4 (100.0%) | 1.97% | 1.11% | 5.59% |
| `A3` | `a3/priority_b_400k_1m/qwen36_tp8_mtp3_decode` | `qwen3.6-27b` | `decode` | `8/1/1` | `64/0/0` | `3` | 14 | 14/14 (100.0%) | 3.40% | 3.84% | 6.39% |
| `A3` | `a3/priority_b_400k_1m/qwen36_tp8_mtp3_prefill` | `qwen3.6-27b` | `prefill` | `8/1/1` | `64/0/0` | `3` | 4 | 4/4 (100.0%) | 4.93% | 4.53% | 8.79% |
| `A3` | `a3/priority_b_400k_1m/qwen38_tp8_mtp3_decode` | `qwen3.8-27b` | `decode` | `8/1/1` | `64/0/0` | `3` | 14 | 14/14 (100.0%) | 3.52% | 3.89% | 6.42% |
| `A3` | `a3/priority_b_400k_1m/qwen38_tp8_mtp3_prefill` | `qwen3.8-27b` | `prefill` | `8/1/1` | `64/0/0` | `3` | 4 | 4/4 (100.0%) | 5.09% | 4.86% | 8.71% |
| `A3` | `a3/priority_c_moe_synth/real_dsv2lite_E64_K6_tp8ep8_decode` | `deepseek-v2-lite` | `decode` | `8/1/8` | `27/64/6` | `0` | 9 | 9/9 (100.0%) | 0.04% | 0.03% | 0.10% |
| `A3` | `a3/priority_c_moe_synth/real_dsv2lite_E64_K6_tp8ep8_prefill` | `deepseek-v2-lite` | `prefill` | `8/1/8` | `27/64/6` | `0` | 2 | 2/2 (100.0%) | 1.03% | 1.03% | 1.71% |
| `A3` | `a3/priority_c_moe_synth/real_dsv32prune_L3_E256_K8_tp8ep8_decode` | `deepseek-v3.2-prune` | `decode` | `8/1/8` | `3/256/8` | `0` | 9 | 9/9 (100.0%) | 0.46% | 0.50% | 0.66% |
| `A3` | `a3/priority_c_moe_synth/real_dsv32prune_L3_E256_K8_tp8ep8_prefill` | `deepseek-v3.2-prune` | `prefill` | `8/1/8` | `3/256/8` | `0` | 2 | 2/2 (100.0%) | 0.37% | 0.37% | 0.41% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E16_K4_tp4dp2ep8_decode` | `deepseek-v4.1` | `decode` | `4/2/8` | `8/16/4` | `0` | 13 | 13/13 (100.0%) | 0.64% | 0.03% | 6.42% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E16_K4_tp4dp2ep8_prefill` | `deepseek-v4.1` | `prefill` | `4/2/8` | `8/16/4` | `0` | 3 | 3/3 (100.0%) | 3.03% | 3.60% | 5.27% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E32_K4_tp4dp2ep8_decode` | `deepseek-v4.1` | `decode` | `4/2/8` | `8/32/4` | `0` | 13 | 13/13 (100.0%) | 2.44% | 0.12% | 8.88% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E32_K4_tp4dp2ep8_prefill` | `deepseek-v4.1` | `prefill` | `4/2/8` | `8/32/4` | `0` | 3 | 3/3 (100.0%) | 2.58% | 3.68% | 3.73% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E32_K6_tp4dp2ep8_decode` | `deepseek-v4.1` | `decode` | `4/2/8` | `8/32/6` | `0` | 13 | 13/13 (100.0%) | 1.45% | 0.02% | 8.44% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E32_K6_tp4dp2ep8_prefill` | `deepseek-v4.1` | `prefill` | `4/2/8` | `8/32/6` | `0` | 3 | 3/3 (100.0%) | 2.13% | 2.11% | 4.18% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E48_K6_tp4dp2ep8_decode` | `deepseek-v4.1` | `decode` | `4/2/8` | `8/48/6` | `0` | 13 | 13/13 (100.0%) | 1.73% | 0.02% | 6.18% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E48_K6_tp4dp2ep8_prefill` | `deepseek-v4.1` | `prefill` | `4/2/8` | `8/48/6` | `0` | 3 | 3/3 (100.0%) | 1.03% | 0.95% | 2.11% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E64_K6_tp4dp2ep8_decode` | `deepseek-v4.1` | `decode` | `4/2/8` | `8/64/6` | `0` | 13 | 13/13 (100.0%) | 3.87% | 3.84% | 9.26% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv41_L8_E64_K6_tp4dp2ep8_prefill` | `deepseek-v4.1` | `prefill` | `4/2/8` | `8/64/6` | `0` | 3 | 3/3 (100.0%) | 0.70% | 0.86% | 1.19% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E16_K2_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/16/2` | `0` | 13 | 13/13 (100.0%) | 4.89% | 4.60% | 9.88% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E16_K2_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/16/2` | `0` | 3 | 3/3 (100.0%) | 1.57% | 1.55% | 2.96% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E16_K4_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/16/4` | `0` | 13 | 13/13 (100.0%) | 4.06% | 3.74% | 8.82% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E16_K4_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/16/4` | `0` | 3 | 3/3 (100.0%) | 5.14% | 5.91% | 8.82% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E16_K6_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/16/6` | `0` | 13 | 13/13 (100.0%) | 4.06% | 3.99% | 8.28% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E16_K6_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/16/6` | `0` | 3 | 3/3 (100.0%) | 3.59% | 3.59% | 7.05% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E32_K2_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/32/2` | `0` | 13 | 13/13 (100.0%) | 4.34% | 3.75% | 9.28% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E32_K2_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/32/2` | `0` | 3 | 3/3 (100.0%) | 1.68% | 1.15% | 3.87% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E32_K4_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/32/4` | `0` | 13 | 13/13 (100.0%) | 3.47% | 2.71% | 8.47% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E32_K4_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/32/4` | `0` | 3 | 3/3 (100.0%) | 3.88% | 0.96% | 9.81% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E32_K6_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/32/6` | `0` | 13 | 13/13 (100.0%) | 2.54% | 1.83% | 6.34% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E32_K6_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/32/6` | `0` | 3 | 3/3 (100.0%) | 3.84% | 2.75% | 8.36% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E48_K4_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/48/4` | `0` | 13 | 13/13 (100.0%) | 2.94% | 1.65% | 8.06% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E48_K4_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/48/4` | `0` | 3 | 3/3 (100.0%) | 2.28% | 1.01% | 5.13% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E48_K6_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/48/6` | `0` | 13 | 13/13 (100.0%) | 2.53% | 1.81% | 7.02% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E48_K6_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/48/6` | `0` | 3 | 3/3 (100.0%) | 4.13% | 1.86% | 9.32% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E64_K2_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/64/2` | `0` | 13 | 13/13 (100.0%) | 4.35% | 3.88% | 9.69% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E64_K2_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/64/2` | `0` | 3 | 3/3 (100.0%) | 1.19% | 1.74% | 1.83% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E64_K4_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/64/4` | `0` | 13 | 13/13 (100.0%) | 2.71% | 1.88% | 7.51% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E64_K4_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/64/4` | `0` | 3 | 3/3 (100.0%) | 3.84% | 1.02% | 9.65% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E64_K6_tp8ep8_decode` | `deepseek-v4-flash` | `decode` | `8/1/8` | `8/64/6` | `0` | 13 | 13/13 (100.0%) | 2.86% | 2.92% | 6.53% |
| `A3` | `a3/priority_c_moe_synth/synth_dsv4f_L8_E64_K6_tp8ep8_prefill` | `deepseek-v4-flash` | `prefill` | `8/1/8` | `8/64/6` | `0` | 3 | 3/3 (100.0%) | 3.77% | 1.73% | 8.61% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E16_K2_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/16/2` | `0` | 13 | 13/13 (100.0%) | 5.05% | 5.42% | 9.08% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E16_K2_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/16/2` | `0` | 3 | 3/3 (100.0%) | 1.42% | 1.01% | 3.23% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E16_K4_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/16/4` | `0` | 13 | 13/13 (100.0%) | 5.90% | 6.90% | 7.97% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E16_K4_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/16/4` | `0` | 3 | 3/3 (100.0%) | 1.22% | 1.63% | 1.91% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E16_K8_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/16/8` | `0` | 13 | 13/13 (100.0%) | 4.87% | 5.51% | 8.39% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E16_K8_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/16/8` | `0` | 3 | 3/3 (100.0%) | 1.97% | 1.75% | 2.83% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E32_K2_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/32/2` | `0` | 13 | 13/13 (100.0%) | 6.13% | 7.25% | 9.57% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E32_K2_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/32/2` | `0` | 3 | 3/3 (100.0%) | 2.53% | 2.22% | 4.61% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E32_K4_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/32/4` | `0` | 13 | 13/13 (100.0%) | 5.21% | 4.59% | 7.81% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E32_K4_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/32/4` | `0` | 3 | 3/3 (100.0%) | 1.18% | 1.35% | 1.36% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E32_K8_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/32/8` | `0` | 13 | 13/13 (100.0%) | 5.39% | 5.57% | 7.93% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E32_K8_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/32/8` | `0` | 3 | 3/3 (100.0%) | 2.50% | 1.50% | 4.78% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E48_K4_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/48/4` | `0` | 13 | 13/13 (100.0%) | 6.51% | 6.98% | 9.08% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E48_K4_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/48/4` | `0` | 3 | 3/3 (100.0%) | 2.80% | 3.26% | 4.09% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E48_K8_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/48/8` | `0` | 13 | 13/13 (100.0%) | 4.79% | 4.58% | 10.00% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E48_K8_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/48/8` | `0` | 3 | 3/3 (100.0%) | 1.50% | 0.50% | 4.00% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E64_K2_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/64/2` | `0` | 13 | 13/13 (100.0%) | 5.40% | 5.90% | 9.22% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E64_K2_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/64/2` | `0` | 3 | 3/3 (100.0%) | 2.17% | 1.69% | 3.32% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E64_K4_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/64/4` | `0` | 13 | 13/13 (100.0%) | 5.15% | 5.09% | 9.60% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E64_K4_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/64/4` | `0` | 3 | 3/3 (100.0%) | 5.00% | 5.37% | 8.39% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E64_K8_tp8ep8_decode` | `qwen3.5-35b-a3b` | `decode` | `8/1/8` | `8/64/8` | `0` | 13 | 13/13 (100.0%) | 5.62% | 6.10% | 7.44% |
| `A3` | `a3/priority_c_moe_synth/synth_qwen35_L8_E64_K8_tp8ep8_prefill` | `qwen3.5-35b-a3b` | `prefill` | `8/1/8` | `8/64/8` | `0` | 3 | 3/3 (100.0%) | 1.20% | 1.47% | 2.11% |
| `A5` | `a5/a5_qwen30ba3b_tp4_ep4_decode` | `qwen3-30b-a3b` | `decode` | `4/1/4` | `48/128/8` | `0` | 26 | 26/26 (100.0%) | 2.51% | 1.79% | 6.45% |
| `A5` | `a5/a5_qwen30ba3b_tp4_ep4_prefill` | `qwen3-30b-a3b` | `prefill` | `4/1/4` | `48/128/8` | `0` | 4 | 4/4 (100.0%) | 1.05% | 1.17% | 1.84% |
| `A5` | `a5/a5_qwen35_tp4_ep4_mtp0_decode` | `qwen3.5-35b-a3b` | `decode` | `4/1/4` | `40/256/8` | `0` | 26 | 26/26 (100.0%) | 1.80% | 1.44% | 4.22% |
| `A5` | `a5/a5_qwen35_tp4_ep4_mtp0_prefill` | `qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `40/256/8` | `0` | 4 | 4/4 (100.0%) | 1.54% | 1.65% | 2.37% |
| `A5` | `a5/a5_qwen35_tp4_ep4_mtp3_decode` | `qwen3.5-35b-a3b` | `decode` | `4/1/4` | `40/256/8` | `3` | 26 | 26/26 (100.0%) | 3.61% | 3.64% | 9.95% |
| `A5` | `a5/a5_qwen35_tp4_ep4_mtp3_prefill` | `qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `40/256/8` | `3` | 4 | 4/4 (100.0%) | 0.71% | 0.67% | 1.38% |
| `A5` | `a5/a5_qwen36_tp4_mtp3_decode` | `qwen3.6-27b` | `decode` | `4/1/1` | `64/256/8` | `3` | 14 | 14/14 (100.0%) | 2.29% | 2.35% | 4.45% |
| `A5` | `a5/a5_qwen36_tp4_mtp3_prefill` | `qwen3.6-27b` | `prefill` | `4/1/1` | `64/256/8` | `3` | 4 | 4/4 (100.0%) | 0.68% | 0.55% | 1.41% |
| `A5` | `a5/a5_qwen38_tp4_mtp3_decode` | `qwen3.8-27b` | `decode` | `4/1/1` | `64/256/8` | `3` | 14 | 14/14 (100.0%) | 2.44% | 2.26% | 5.39% |
| `A5` | `a5/a5_qwen38_tp4_mtp3_prefill` | `qwen3.8-27b` | `prefill` | `4/1/1` | `64/256/8` | `3` | 4 | 4/4 (100.0%) | 1.38% | 1.37% | 1.79% |
| `A5` | `a5/a5_synth_qwen30b_L8_E16_K2_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/16/2` | `0` | 13 | 13/13 (100.0%) | 1.77% | 1.24% | 6.50% |
| `A5` | `a5/a5_synth_qwen30b_L8_E16_K2_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/16/2` | `0` | 3 | 3/3 (100.0%) | 2.18% | 1.77% | 3.79% |
| `A5` | `a5/a5_synth_qwen30b_L8_E16_K4_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/16/4` | `0` | 13 | 13/13 (100.0%) | 2.37% | 1.27% | 6.84% |
| `A5` | `a5/a5_synth_qwen30b_L8_E16_K4_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/16/4` | `0` | 3 | 3/3 (100.0%) | 1.39% | 1.10% | 2.76% |
| `A5` | `a5/a5_synth_qwen30b_L8_E16_K8_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/16/8` | `0` | 13 | 13/13 (100.0%) | 1.66% | 0.90% | 7.00% |
| `A5` | `a5/a5_synth_qwen30b_L8_E16_K8_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/16/8` | `0` | 3 | 3/3 (100.0%) | 3.74% | 2.73% | 7.06% |
| `A5` | `a5/a5_synth_qwen30b_L8_E32_K2_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/32/2` | `0` | 13 | 13/13 (100.0%) | 1.66% | 1.30% | 5.52% |
| `A5` | `a5/a5_synth_qwen30b_L8_E32_K2_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/32/2` | `0` | 3 | 3/3 (100.0%) | 2.00% | 1.54% | 3.41% |
| `A5` | `a5/a5_synth_qwen30b_L8_E32_K4_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/32/4` | `0` | 13 | 13/13 (100.0%) | 1.56% | 1.41% | 4.84% |
| `A5` | `a5/a5_synth_qwen30b_L8_E32_K4_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/32/4` | `0` | 3 | 3/3 (100.0%) | 1.02% | 1.34% | 1.55% |
| `A5` | `a5/a5_synth_qwen30b_L8_E32_K8_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/32/8` | `0` | 13 | 13/13 (100.0%) | 1.51% | 0.90% | 4.40% |
| `A5` | `a5/a5_synth_qwen30b_L8_E32_K8_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/32/8` | `0` | 3 | 3/3 (100.0%) | 2.07% | 2.28% | 2.70% |
| `A5` | `a5/a5_synth_qwen30b_L8_E48_K2_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/48/2` | `0` | 13 | 13/13 (100.0%) | 1.66% | 1.22% | 4.89% |
| `A5` | `a5/a5_synth_qwen30b_L8_E48_K2_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/48/2` | `0` | 3 | 3/3 (100.0%) | 2.54% | 3.61% | 3.86% |
| `A5` | `a5/a5_synth_qwen30b_L8_E48_K4_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/48/4` | `0` | 13 | 13/13 (100.0%) | 1.75% | 1.69% | 4.81% |
| `A5` | `a5/a5_synth_qwen30b_L8_E48_K4_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/48/4` | `0` | 3 | 3/3 (100.0%) | 2.05% | 1.21% | 4.64% |
| `A5` | `a5/a5_synth_qwen30b_L8_E48_K8_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/48/8` | `0` | 13 | 13/13 (100.0%) | 2.30% | 2.57% | 5.11% |
| `A5` | `a5/a5_synth_qwen30b_L8_E48_K8_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/48/8` | `0` | 3 | 3/3 (100.0%) | 0.31% | 0.37% | 0.44% |
| `A5` | `a5/a5_synth_qwen30b_L8_E64_K2_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/64/2` | `0` | 13 | 13/13 (100.0%) | 2.31% | 1.87% | 5.70% |
| `A5` | `a5/a5_synth_qwen30b_L8_E64_K2_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/64/2` | `0` | 3 | 3/3 (100.0%) | 3.06% | 4.18% | 4.56% |
| `A5` | `a5/a5_synth_qwen30b_L8_E64_K4_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/64/4` | `0` | 13 | 13/13 (100.0%) | 1.92% | 2.02% | 5.05% |
| `A5` | `a5/a5_synth_qwen30b_L8_E64_K4_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/64/4` | `0` | 3 | 3/3 (100.0%) | 3.67% | 1.46% | 8.28% |
| `A5` | `a5/a5_synth_qwen30b_L8_E64_K8_tp4ep4_decode` | `synth-qwen3-30b-a3b` | `decode` | `4/1/4` | `8/64/8` | `0` | 13 | 13/13 (100.0%) | 2.52% | 0.94% | 8.80% |
| `A5` | `a5/a5_synth_qwen30b_L8_E64_K8_tp4ep4_prefill` | `synth-qwen3-30b-a3b` | `prefill` | `4/1/4` | `8/64/8` | `0` | 3 | 3/3 (100.0%) | 3.91% | 1.53% | 9.58% |
| `A5` | `a5/a5_synth_qwen35_L8_E16_K2_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/16/2` | `0` | 13 | 13/13 (100.0%) | 3.95% | 4.02% | 9.68% |
| `A5` | `a5/a5_synth_qwen35_L8_E16_K2_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/16/2` | `0` | 3 | 3/3 (100.0%) | 2.38% | 2.67% | 4.38% |
| `A5` | `a5/a5_synth_qwen35_L8_E16_K4_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/16/4` | `0` | 13 | 13/13 (100.0%) | 2.80% | 2.55% | 6.53% |
| `A5` | `a5/a5_synth_qwen35_L8_E16_K4_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/16/4` | `0` | 3 | 3/3 (100.0%) | 3.55% | 3.99% | 3.99% |
| `A5` | `a5/a5_synth_qwen35_L8_E16_K8_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/16/8` | `0` | 13 | 13/13 (100.0%) | 3.83% | 2.33% | 9.75% |
| `A5` | `a5/a5_synth_qwen35_L8_E16_K8_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/16/8` | `0` | 3 | 3/3 (100.0%) | 3.41% | 4.70% | 5.05% |
| `A5` | `a5/a5_synth_qwen35_L8_E32_K2_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/32/2` | `0` | 13 | 13/13 (100.0%) | 3.58% | 2.48% | 9.83% |
| `A5` | `a5/a5_synth_qwen35_L8_E32_K2_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/32/2` | `0` | 3 | 3/3 (100.0%) | 5.38% | 5.27% | 6.32% |
| `A5` | `a5/a5_synth_qwen35_L8_E32_K4_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/32/4` | `0` | 13 | 13/13 (100.0%) | 3.43% | 3.16% | 9.70% |
| `A5` | `a5/a5_synth_qwen35_L8_E32_K4_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/32/4` | `0` | 3 | 3/3 (100.0%) | 2.62% | 3.56% | 3.91% |
| `A5` | `a5/a5_synth_qwen35_L8_E32_K8_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/32/8` | `0` | 13 | 13/13 (100.0%) | 2.73% | 2.38% | 6.72% |
| `A5` | `a5/a5_synth_qwen35_L8_E32_K8_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/32/8` | `0` | 3 | 3/3 (100.0%) | 4.74% | 4.20% | 6.85% |
| `A5` | `a5/a5_synth_qwen35_L8_E48_K2_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/48/2` | `0` | 12 | 12/12 (100.0%) | 2.99% | 2.25% | 9.56% |
| `A5` | `a5/a5_synth_qwen35_L8_E48_K2_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/48/2` | `0` | 2 | 2/2 (100.0%) | 5.96% | 5.96% | 7.75% |
| `A5` | `a5/a5_synth_qwen35_L8_E48_K4_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/48/4` | `0` | 13 | 13/13 (100.0%) | 4.22% | 4.60% | 9.74% |
| `A5` | `a5/a5_synth_qwen35_L8_E48_K4_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/48/4` | `0` | 3 | 3/3 (100.0%) | 2.11% | 2.28% | 3.23% |
| `A5` | `a5/a5_synth_qwen35_L8_E48_K8_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/48/8` | `0` | 13 | 13/13 (100.0%) | 2.81% | 2.29% | 7.28% |
| `A5` | `a5/a5_synth_qwen35_L8_E48_K8_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/48/8` | `0` | 3 | 3/3 (100.0%) | 4.03% | 3.76% | 6.10% |
| `A5` | `a5/a5_synth_qwen35_L8_E64_K2_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/64/2` | `0` | 13 | 13/13 (100.0%) | 3.58% | 2.72% | 9.50% |
| `A5` | `a5/a5_synth_qwen35_L8_E64_K2_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/64/2` | `0` | 3 | 3/3 (100.0%) | 4.02% | 3.05% | 6.89% |
| `A5` | `a5/a5_synth_qwen35_L8_E64_K4_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/64/4` | `0` | 13 | 13/13 (100.0%) | 3.20% | 2.46% | 8.97% |
| `A5` | `a5/a5_synth_qwen35_L8_E64_K4_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/64/4` | `0` | 3 | 3/3 (100.0%) | 3.30% | 3.30% | 5.70% |
| `A5` | `a5/a5_synth_qwen35_L8_E64_K8_tp4ep4_decode` | `synth-qwen3.5-35b-a3b` | `decode` | `4/1/4` | `8/64/8` | `0` | 13 | 13/13 (100.0%) | 2.35% | 1.69% | 7.76% |
| `A5` | `a5/a5_synth_qwen35_L8_E64_K8_tp4ep4_prefill` | `synth-qwen3.5-35b-a3b` | `prefill` | `4/1/4` | `8/64/8` | `0` | 3 | 3/3 (100.0%) | 5.30% | 4.90% | 7.24% |
