# mindie-profiler 0.5.5

[English](profiler-0.5.5.en.md)

本版本围绕 `heldout_engine_20261031` 多代际引擎基准采集批次（涵盖 **A2 `Ascend910B4`**、**A3 `Ascend910_9392`** 与 **A5 `Ascend910_9599`** 共 **1,653 份** 实测 Profile，覆盖 `4K..400K` 超长上下文、裁剪专家真实模型及 `L=8, E in {16, 32, 48, 64}, K in {2, 4, 6, 8}` 合成 MoE 拓扑），完成了 Decode / Prefill 原生结构分段锚点扩展与样本内体制校准评估闭环：

- **Decode 与 Prefill 原生结构分段锚点扩展**：
  - `mindie_profiler/decode_segmentation.py`：在 `_NORMS` 中新增 `AddRmsNormQuant`（保留 `hidden_size` 尾维契约校验），原生支持 `Qwen3-30B-A3B` W8A8 及 `synth-qwen3-30b-a3b` 融合层间残差 `RMSNorm` + 静态量化算子的逐层切分。
  - `examples/structure/prefill.py`：在 `anchor()` 与 `_attention_query_rows()` 中新增 `SparseFlashAttention` 与 `SparseFlashMla`（`shape[0] > 16`）Prefill MLA 锚点识别，并新增 `_prefill_head()`（`Index` 尾 Token 选择头）与 `_dp_partner_align()`（校验逐层 MLA 注意力类型、FFN 输入 Norm、激活函数、`GroupedMatmul*`/`SwiGlu` 存在性及 `hidden_size` 输出契约的 DP-partner EP all-to-all Prefill Chunk 对齐），无需外部补丁即可原生解析 `DeepSeek-V3.2-Prune-3L` 与 `DeepSeek-V4.1` `tp4dp2ep8` Prefill 采集。
- **三代硬件 1,653 份采集的分段与样本内体制校准评估**：
  - `examples/structure/wave5_generalization_eval.py` 与 `examples/structure/results/wave5_full_generalization.{json,md}`：汇总 **A2**（`565/565 <= 10%`，平均误差 `2.30%`）、**A3**（`580/580 <= 10%`，平均误差 `3.38%`）与 **A5**（`508/508 <= 10%`，平均误差 `2.60%`）共 **202 个 Cohort-Phase**、**1,653 份** 实测采集的校准评估结果（整体平均绝对相对误差 `2.77%`，中位数 `2.11%`，最大 `10.00%`；其中 `192K..400K` 超长上下文 `578` 份平均误差 `2.28%`，`L=8` 合成少专家数 MoE `1,325` 份平均误差 `2.91%`）。
  - 报告显式标注 `in_sample_regime_calibration` 溯源边界（区分 A2/A5 的 Cohort-Phase 级模板与 A3 按 `(cohort, context_tokens, concurrency)` 条件化的 `service_regimes` 覆盖，不宣称零样本盲测泛化），保持观测区间零裁剪（`observed_spans_untrimmed=True`），强制核验跨芯片报告的 `parser_identity` 一致性，并从原始采集记录直接推导每个 Cohort 的真实 `TP/DP/EP` 拓扑。
