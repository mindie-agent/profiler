# 矩阵角色：从完整模型到局部契约

复用已有完整 Forward 的层窗口，仅读取两份 c4 CSV 的前缀；Sim 导出没有执行成本模型。
模型层身份来自完整 64 层序列的条件推断，不能宣称 Host/module 绑定。

| 模型 / 层 | CSV line | 实测类型 | M,N,K | 仅 tensor 候选数 | 拓扑条件后角色 |
|---|---:|---|---|---:|---|
| qwen3.6-27b / 0 | 98 | QuantBatchMatmulV3 | [16, 2048, 5120] | 2 | linear_qkvz |
| qwen3.6-27b / 0 | 99 | MatMulV3 | [16, 12, 5120] | 1 | linear_beta_alpha |
| qwen3.6-27b / 0 | 116 | MatMulV3 | [16, 5120, 768] | 1 | linear_output |
| qwen3.6-27b / 0 | 122 | QuantBatchMatmulV3 | [16, 4352, 5120] | 2 | dense_gate_up |
| qwen3.6-27b / 0 | 125 | QuantBatchMatmulV3 | [16, 5120, 2176] | 2 | dense_down |
| qwen3.6-27b / 3 | 194 | QuantBatchMatmulV3 | [16, 2048, 5120] | 2 | qkv_projection |
| qwen3.6-27b / 3 | 205 | QuantBatchMatmulV3 | [16, 5120, 768] | 1 | attention_output |
| qwen3.6-27b / 3 | 210 | QuantBatchMatmulV3 | [16, 4352, 5120] | 2 | dense_gate_up |
| qwen3.6-27b / 3 | 213 | QuantBatchMatmulV3 | [16, 5120, 2176] | 2 | dense_down |
| qwen3.8-27b / 0 | 98 | MatMulV3 | [16, 4096, 5120] | 1 | linear_qkvz |
| qwen3.8-27b / 0 | 99 | MatMulV3 | [16, 24, 5120] | 1 | linear_beta_alpha |
| qwen3.8-27b / 0 | 117 | MatMulV3 | [16, 5120, 1536] | 1 | linear_output |
| qwen3.8-27b / 0 | 121 | QuantBatchMatmulV3 | [16, 8704, 5120] | 2 | dense_gate_up |
| qwen3.8-27b / 0 | 124 | QuantBatchMatmulV3 | [16, 5120, 4352] | 2 | dense_down |
| qwen3.8-27b / 3 | 193 | QuantBatchMatmulV3 | [16, 3584, 5120] | 1 | qkv_projection |
| qwen3.8-27b / 3 | 209 | QuantBatchMatmulV3 | [16, 5120, 1536] | 1 | attention_output |
| qwen3.8-27b / 3 | 213 | QuantBatchMatmulV3 | [16, 8704, 5120] | 2 | dense_gate_up |
| qwen3.8-27b / 3 | 217 | QuantBatchMatmulV3 | [16, 5120, 4352] | 2 | dense_down |

Qwen3.6 的 GDN qkvz 与 GQA qkv 契约完全相同；FFN gate_up/down 在两类层中也重复。
因此先验证完整层计划，再在当前层的候选子图内对账。FFN 角色与所在层的 attention 类型分开保留；不把 GDN/GQA 层里的 FFN 计为 attention。
