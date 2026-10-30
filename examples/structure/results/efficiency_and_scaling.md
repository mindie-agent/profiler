# Whole-Network 4D MFU/MBU/CV Efficiency & Hardware Scaling SLA Report

## 1. Whole-Network 4D MFU / MBU / CV Summary (Decode & Prefill, B=1 per DP)

| Case | Phase / Ctx | Graph ms | OpSum ms | Cube MFU | Vec MFU | Net MBU | Link Util | Roofline Eff | CV Overlap | Mem% | Cube% | Vec% | Link% |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | Decode 4K |    4.18 |    4.21 |   0.3% |   0.2% |  25.5% |  16.8% |  25.5% |    -   |  36.3% |   0.0% |   3.2% |  50.6% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | Decode 128K |    4.39 |    4.42 |   0.6% |   0.2% |  28.1% |  16.0% |  28.1% |    -   |  39.3% |   0.0% |   3.0% |  48.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | Prefill 4K |   60.37 |   62.17 |  10.1% |   6.6% |  16.7% | 297.8% | 297.8% | 100.0% |  16.3% |  20.8% |  54.0% |   8.9% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | Decode 4K |   14.44 |   14.44 |   0.1% |   0.3% |  11.0% |   0.6% |  11.0% |    -   |  29.5% |   0.0% |   0.0% |   8.4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | Decode 128K |   15.65 |   15.65 |   0.2% |   0.4% |  17.1% |   0.5% |  17.1% |    -   |  35.0% |   0.0% |   0.0% |   7.7% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | Prefill 4K |  124.45 |  124.45 |  14.7% |  16.6% |  47.2% |  66.0% |  66.0% | 100.0% |  52.4% |  37.5% |   0.9% |   9.2% |

## 2. Operator Family Breakdown (Decode 128K, B=1 per DP)

| Case | Family | Duration ms | Share % | Cube MFU | Vec MFU | MBU | Link Util | Roofline Eff |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `alltoallv/hccl_source_peer_exchange` |   1.902 |  43.1% |   0.0% |   0.0% |   0.0% |  31.4% |  31.4% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `grouped_gemm/balanced_grouped_gate_up` |   0.527 |  11.9% |   0.7% |   0.0% |  83.9% |   0.0% |  83.9% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `grouped_gemm/balanced_grouped_down` |   0.267 |   6.0% |   0.7% |   0.0% |  82.8% |   0.0% |  82.8% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `attention/ascend_paged_mla_decode_arch22` |   0.229 |   5.2% |   7.4% |   1.9% |  73.7% |   0.0% |  73.7% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `projection/latent_projection` |   0.185 |   4.2% |   0.3% |   0.0% |  69.6% |   0.0% |  69.6% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `situ/grouped_situ` |   0.134 |   3.0% |   0.0% |   0.6% |   0.5% |   0.0% |   0.6% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `alltoall/expert_dispatch` |   0.114 |   2.6% |   0.0% |   0.0% |   0.0% |  46.2% |  46.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `alltoall/expert_combine` |   0.114 |   2.6% |   0.0% |   0.0% |   0.0% |  46.2% |  46.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/linear_bfg` |   0.106 |   2.4% |   0.2% |   0.0% |  52.4% |   0.0% |  52.4% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `router/router` |   0.106 |   2.4% |   0.1% |   0.0% |  30.5% |   0.0% |  30.5% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gate_up_projection/dense_gate_up` |   0.097 |   2.2% |   2.9% |   0.2% |  40.9% |   0.0% |  40.9% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `quantize/dynamic_quantize` |   0.062 |   1.4% |   0.0% |   2.7% |   3.6% |   0.0% |   3.6% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/linear_qkv` |   0.053 |   1.2% |   0.3% |   0.0% |  78.3% |   0.0% |  78.3% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `recurrent_scan/vllm_ascend_recurrent_kda_arch22` |   0.041 |   0.9% |   0.0% |   3.4% |   4.8% |   0.0% |   4.8% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/attention_residual_scores` |   0.040 |   0.9% |   0.0% |   0.0% |   1.0% |   0.0% |   1.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `rmsnorm/rmsnorm` |   0.040 |   0.9% |   0.0% |   0.7% |   2.2% |   0.0% |   2.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/linear_output` |   0.035 |   0.8% |   0.3% |   0.0% |  78.3% |   0.0% |  78.3% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/output_gate` |   0.035 |   0.8% |   0.1% |   0.0% |  26.1% |   0.0% |  26.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `down_projection/dense_down` |   0.033 |   0.7% |   4.2% |   2.6% |  62.5% |   0.0% |  62.5% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `elementwise/short_convolution` |   0.029 |   0.7% |   0.0% |   0.1% |   0.2% |   0.0% |   0.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `cast/residual_values_fp32` |   0.020 |   0.5% |   0.0% |   0.1% |   1.4% |   0.0% |   1.4% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `softmax/attention_residual_softmax` |   0.020 |   0.5% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `elementwise/attention_residual_mix` |   0.020 |   0.5% |   0.0% |   0.3% |   1.9% |   0.0% |   1.9% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `cast/attention_residual_output_cast` |   0.020 |   0.5% |   0.0% |   0.1% |   1.4% |   0.0% |   1.4% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `elementwise/residual_add` |   0.020 |   0.5% |   0.0% |   0.1% |   1.4% |   0.0% |   1.4% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/q_a` |   0.018 |   0.4% |   0.2% |   0.0% |  52.2% |   0.0% |  52.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/kv_a` |   0.018 |   0.4% |   0.1% |   0.0% |  19.6% |   0.0% |  19.6% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/output` |   0.012 |   0.3% |   0.3% |   0.0% |  78.3% |   0.0% |  78.3% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `hccl_local/hccl_aicpu_source_phase` |   0.011 |   0.2% |   0.0% |   0.0% | 100.0% |   0.0% | 100.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `pad/sequence_parallel_reduce_scatter_pad` |   0.010 |   0.2% |   0.0% |   2.0% |   8.1% |   0.0% |   8.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `situ/situ` |   0.010 |   0.2% |   0.0% |   3.0% |   2.6% |   0.0% |   3.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `tensor_copy/linear_beta_cast` |   0.007 |   0.2% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `sigmoid/linear_beta_sigmoid` |   0.007 |   0.2% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `elementwise/linear_output_norm_gate` |   0.007 |   0.2% |   0.0% |   0.1% |   0.2% |   0.0% |   0.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `topk/router_topk` |   0.007 |   0.2% |   0.0% |   0.2% |   0.1% |   0.0% |   0.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `routing/route_pack` |   0.007 |   0.2% |   0.0% |   0.0% |   4.1% |   0.0% |   4.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `routing/route_unpack` |   0.007 |   0.2% |   0.0% |   2.2% |   4.1% |   0.0% |   4.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `rmsnorm/latent_norm` |   0.007 |   0.2% |   0.0% |   0.3% |   0.7% |   0.0% |   0.7% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `elementwise/expert_add` |   0.007 |   0.2% |   0.0% |   0.1% |   1.4% |   0.0% |   1.4% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/q_b` |   0.005 |   0.1% |   0.1% |   0.0% |  29.7% |   0.0% |  29.7% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/q_absorb` |   0.005 |   0.1% |   0.1% |   0.0% |  13.2% |   0.0% |  13.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `gemm/v_expand` |   0.005 |   0.1% |   0.1% |   0.0% |  13.2% |   0.0% |  13.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `pad/sequence_parallel_right_pad` |   0.003 |   0.1% |   0.0% |   2.0% |   8.1% |   0.0% |   8.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `rmsnorm/q_norm` |   0.003 |   0.1% |   0.0% |   0.1% |   0.2% |   0.0% |   0.2% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `rmsnorm/kv_norm` |   0.003 |   0.1% |   0.0% |   0.0% |   0.1% |   0.0% |   0.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `elementwise/rotary` |   0.003 |   0.1% |   0.0% |   0.1% |   0.1% |   0.0% |   0.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `cache_store/kv_store` |   0.003 |   0.1% |   0.0% |   0.0% |   0.1% |   0.0% |   0.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `elementwise/gated_output` |   0.003 |   0.1% |   0.0% |   0.1% |   0.1% |   0.0% |   0.1% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `copy/paged_mla_query_pad_nope` |   0.000 |   0.0% |   0.0% |   0.0% | 100.0% |   0.0% | 100.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `copy/paged_mla_query_pad_rope` |   0.000 |   0.0% |   0.0% |   0.0% | 100.0% |   0.0% | 100.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `hccl_boundary/hccl_entry` |   0.000 |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | `hccl_boundary/hccl_exit` |   0.000 |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `grouped_gemm/balanced_grouped_gate_up` |   2.118 |  13.5% |   0.1% |   0.0% |  26.6% |   0.0% |  26.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `grouped_gemm/balanced_grouped_down` |   1.925 |  12.3% |   0.1% |   0.3% |  15.7% |   0.0% |  15.7% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `routing/route_pack` |   1.920 |  12.3% |   0.0% |   0.0% |   0.3% |   0.0% |   0.3% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `attention/flash_attention_decode` |   1.326 |   8.5% |   1.5% |   2.5% |  84.5% |   0.0% |  84.5% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `router/router` |   0.827 |   5.3% |   0.3% |   0.0% |   8.6% |   0.0% |   8.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `elementwise/expert_add` |   0.641 |   4.1% |   0.0% |   0.0% |   0.3% |   0.0% |   0.3% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `topk/router_topk` |   0.629 |   4.0% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `gemm/linear_qkvz` |   0.625 |   4.0% |   0.9% |   0.0% |  50.5% |   0.0% |  50.5% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `allreduce/moe_output_reduce` |   0.605 |   3.9% |   0.0% |   0.0% |   0.0% |   6.6% |   6.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `allreduce/linear_reduce` |   0.454 |   2.9% |   0.0% |   0.0% |   0.0% |   6.6% |   6.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `gate_up_projection/dense_gate_up` |   0.417 |   2.7% |   0.1% |   0.0% |   8.5% |   0.0% |   8.5% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `down_projection/dense_down` |   0.331 |   2.1% |   0.1% |   0.0% |   5.5% |   0.0% |   5.5% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `elementwise/shared_gate_apply` |   0.322 |   2.1% |   0.0% |   0.1% |   0.3% |   0.0% |   0.3% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `gemm/linear_output` |   0.311 |   2.0% |   0.6% |   0.0% |  33.9% |   0.0% |  33.9% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `router/shared_gate` |   0.258 |   1.7% |   0.0% |   0.0% |   0.3% |   0.0% |   0.3% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `rmsnorm/rmsnorm` |   0.258 |   1.6% |   0.0% |   0.6% |   1.0% |   0.0% |   1.0% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `quantize/dynamic_quantize` |   0.225 |   1.4% |   0.0% |   2.4% |   3.2% |   0.0% |   3.2% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `elementwise/residual_add` |   0.200 |   1.3% |   0.0% |   0.2% |   1.6% |   0.0% |   1.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `qkv_projection/qkv_projection` |   0.166 |   1.1% |   0.5% |   0.1% |  26.5% |   0.0% |  26.5% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `allreduce/catalog_tp_allreduce` |   0.151 |   1.0% |   0.0% |   0.0% |   0.0% |   6.6% |   6.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `gemm/linear_beta_alpha` |   0.150 |   1.0% |   0.0% |   0.0% |   1.4% |   0.0% |   1.4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `elementwise/linear_output_norm_gate` |   0.145 |   0.9% |   0.0% |   0.4% |   0.4% |   0.0% |   0.4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `rotary/rotary` |   0.134 |   0.9% |   0.0% |   0.1% |   0.1% |   0.0% |   0.1% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `recurrent_vector/decode_recurrent_scan` |   0.122 |   0.8% |   0.0% |  10.7% |  21.7% |   0.0% |  21.7% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `output_projection/attention_output` |   0.104 |   0.7% |   0.6% |   0.0% |  33.9% |   0.0% |  33.9% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `cast/router_input_cast` |   0.100 |   0.6% |   0.0% |   0.2% |   1.6% |   0.0% |   1.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `swiglu/grouped_swiglu` |   0.100 |   0.6% |   0.0% |   0.3% |   0.8% |   0.0% |   0.8% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `routing/route_unpack` |   0.100 |   0.6% |   0.0% |   2.5% |   4.9% |   0.0% |   4.9% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `swiglu/swiglu` |   0.100 |   0.6% |   0.0% |   0.0% |   0.1% |   0.0% |   0.1% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `rmsnorm/qk_norm` |   0.088 |   0.6% |   0.0% |   0.1% |   0.2% |   0.0% |   0.2% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `short_convolution/ascend_causal_conv1d_update` |   0.075 |   0.5% |   0.0% |   0.9% |   1.6% |   0.0% |   1.6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `tensor_copy/beta_contiguous` |   0.075 |   0.5% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `tensor_copy/alpha_contiguous` |   0.075 |   0.5% |   0.0% |   0.0% |   0.0% |   0.0% |   0.0% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `tensor_fill/core_output_zero` |   0.075 |   0.5% |   0.0% |   0.1% |   0.3% |   0.0% |   0.3% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `tensor_copy/qkv_concatenate` |   0.075 |   0.5% |   0.0% |   0.0% |   0.3% |   0.0% |   0.3% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `gdn_gating/ascend_gdn_decode_gating` |   0.075 |   0.5% |   0.0% |   5.1% |   0.1% |   0.0% |   5.1% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `elementwise/decode_q_l2norm` |   0.075 |   0.5% |   0.0% |   0.0% |   0.1% |   0.0% |   0.1% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `elementwise/decode_k_l2norm` |   0.075 |   0.5% |   0.0% |   0.0% |   0.1% |   0.0% |   0.1% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `tensor_copy/core_output_copy` |   0.075 |   0.5% |   0.0% |   0.0% |   0.1% |   0.0% |   0.1% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `tensor_copy/z_norm_materialize` |   0.075 |   0.5% |   0.0% |   0.0% |   0.5% |   0.0% |   0.5% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `elementwise/attention_gate` |   0.029 |   0.2% |   0.0% |   0.3% |   0.5% |   0.0% |   0.5% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `cache_store/kv_store` |   0.025 |   0.2% |   0.0% |   0.0% |   0.1% |   0.0% |   0.1% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | `tensor_copy/qkv_split_materialize` |   0.000 |   0.0% |   0.0% |   0.0% | 100.0% |   0.0% | 100.0% |

## 3. Counterfactual `0.80x MBU` Target Fitting & Top Bottlenecks

| Case | Phase / Ctx | Current ms | Target ms | Saved ms | Speedup | Curr Net MBU | Target Net MBU | Top Bottleneck Family (Gap ms, Actual -> Target MBU) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | Decode 4K |    4.18 |    3.83 |   0.35 |  1.09x |  25.5% |  27.8% | `situ/grouped_situ` (-0.11ms, 0.5% -> 3.2%) |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | Decode 128K |    4.39 |    4.04 |   0.35 |  1.09x |  28.1% |  30.5% | `situ/grouped_situ` (-0.11ms, 0.5% -> 3.2%) |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | Decode 4K |   14.44 |   13.16 |   1.27 |  1.10x |  11.0% |  12.1% | `router/router` (-0.63ms, 8.6% -> 35.6%) |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | Decode 128K |   15.65 |   14.44 |   1.22 |  1.08x |  17.1% |  18.5% | `router/router` (-0.63ms, 8.6% -> 35.6%) |

## 4. Counterfactual Hardware Scaling (`1x` vs `2x HBM` vs `2x Compute`) under Decode SLA <= 30 ms (Boundary: `target_body_only`)

| Case | Context | Scenario | B=1 ms | B_VRAM | B_SLA (DP) | B_Feas (DP) | Feas Total B | Feas Step ms | TPS_Feas (tok/s) | Feas Gain | TPS_SLA (tok/s) | SLA Gain | Net MBU | Cube MFU | Mem% / Comp% / Link% |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 4K | `baseline` |   4.18 |     64 |     16 |     16 |      16 |    4.36 |    3667.5 |   1.00x |    3667.5 |   1.00x |  27.1% |   0.7% |   40% /    3% /   49% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 4K | `2x_hbm` |   3.45 |     64 |     16 |     16 |      16 |    3.57 |    4477.2 |   1.22x |    4477.2 |   1.22x |  16.5% |   0.9% |   23% /    7% /   59% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 4K | `2x_compute` |   4.17 |     64 |     16 |     16 |      16 |    4.35 |    3679.6 |   1.00x |    3679.6 |   1.00x |  27.2% |   0.3% |   43% /    0% /   49% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 4K | `2x_cube_only` |   4.17 |     64 |     16 |     16 |      16 |    4.35 |    3678.8 |   1.00x |    3678.8 |   1.00x |  27.2% |   0.3% |   40% /    3% /   49% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 4K | `2x_hbm_2x_compute` |   3.43 |     64 |     16 |     16 |      16 |    3.55 |    4506.6 |   1.23x |    4506.6 |   1.23x |  16.7% |   0.4% |   25% /    4% /   60% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 4K | `target_0.8x_mbu` |   3.83 |     64 |     16 |     16 |      16 |    3.96 |    4043.4 |   1.10x |    4043.4 |   1.10x |  29.9% |   0.8% |   40% /    3% /   49% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 128K | `baseline` |   4.39 |     64 |     16 |     16 |      16 |    7.67 |    2086.8 |   1.00x |    2086.8 |   1.00x |  49.7% |   3.8% |   66% /    2% /   28% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 128K | `2x_hbm` |   3.57 |     64 |     16 |     16 |      16 |    5.50 |    2910.0 |   1.39x |    2910.0 |   1.39x |  34.7% |   5.3% |   50% /    4% /   39% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 128K | `2x_compute` |   4.37 |     64 |     16 |     16 |      16 |    7.60 |    2106.5 |   1.01x |    2106.5 |   1.01x |  50.2% |   1.9% |   67% /    0% /   28% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 128K | `2x_cube_only` |   4.37 |     64 |     16 |     16 |      16 |    7.60 |    2106.2 |   1.01x |    2106.2 |   1.01x |  50.2% |   1.9% |   65% /    2% /   28% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 128K | `2x_hbm_2x_compute` |   3.54 |     64 |     16 |     16 |      16 |    5.20 |    3075.3 |   1.47x |    3075.3 |   1.47x |  36.7% |   2.8% |   49% /    3% /   41% |
| Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture) | 128K | `target_0.8x_mbu` |   4.04 |     64 |     16 |     16 |      16 |    7.25 |    2208.4 |   1.06x |    2208.4 |   1.06x |  52.6% |   4.0% |   66% /    2% /   28% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 4K | `baseline` |  14.44 |     96 |     16 |     16 |      16 |   19.43 |     823.5 |   1.00x |     823.5 |   1.00x |  27.0% |   0.4% |   51% /    0% /    6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 4K | `2x_hbm` |  13.43 |     96 |     16 |     16 |      16 |   18.03 |     887.6 |   1.08x |     887.6 |   1.08x |  14.5% |   0.4% |   22% /    0% /    7% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 4K | `2x_compute` |  14.39 |     96 |     16 |     16 |      16 |   19.41 |     824.4 |   1.00x |     824.4 |   1.00x |  27.0% |   0.2% |   51% /    0% /    6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 4K | `2x_cube_only` |  14.42 |     96 |     16 |     16 |      16 |   19.41 |     824.4 |   1.00x |     824.4 |   1.00x |  27.0% |   0.2% |   51% /    0% /    6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 4K | `2x_hbm_2x_compute` |  13.40 |     96 |     16 |     16 |      16 |   18.00 |     888.7 |   1.08x |     888.7 |   1.08x |  14.6% |   0.2% |   22% /    0% /    7% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 4K | `target_0.8x_mbu` |  13.16 |     96 |     16 |     16 |      16 |   17.43 |     917.7 |   1.11x |     917.7 |   1.11x |  30.1% |   0.4% |   51% /    0% /    6% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 128K | `baseline` |  15.65 |     37 |      9 |      9 |       9 |   29.27 |     307.5 |   1.00x |     307.5 |   1.00x |  46.6% |   0.8% |   68% /    0% /    4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 128K | `2x_hbm` |  14.05 |     37 |     16 |     16 |      16 |   28.11 |     569.1 |   1.85x |     569.1 |   1.85x |  40.2% |   1.4% |   50% /    0% /    4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 128K | `2x_compute` |  15.60 |     37 |      9 |      9 |       9 |   29.17 |     308.6 |   1.00x |     308.6 |   1.00x |  46.8% |   0.4% |   68% /    0% /    4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 128K | `2x_cube_only` |  15.63 |     37 |      9 |      9 |       9 |   29.17 |     308.6 |   1.00x |     308.6 |   1.00x |  46.8% |   0.4% |   68% /    0% /    4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 128K | `2x_hbm_2x_compute` |  14.01 |     37 |     16 |     16 |      16 |   27.94 |     572.7 |   1.86x |     572.7 |   1.86x |  40.4% |   0.7% |   50% /    0% /    4% |
| Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE) | 128K | `target_0.8x_mbu` |  14.44 |     37 |     10 |     10 |      10 |   28.99 |     345.0 |   1.12x |     345.0 |   1.12x |  51.0% |   0.9% |   69% /    0% /    4% |
