# GLM Decode：主体、分层与算子证据

新 Flash 使用独立 45 层 KDA/MLA 结构；历史 GLM78 DSA 另组展示。以下统计全部复用已验收提取，无新增原始 kernel 扫描或 Sim 预测。

| 模型组 / Case | 完整 Body | 几何桶 | Body P50 ms | Body activity mean ms |
|---|---:|---:|---:|---:|
| flash45_kda_mla / glm53flash-a3-tp16-c4-livepre | 73 | 4 | 29.444628 | 26.836990 |
| flash45_kda_mla / glm53flash-a3-tp16-c16-livepre | 108 | 13 | 35.461048 | 33.659187 |
| flash45_kda_mla / glm53flash-a3-tp16-c2 | 58 | 2 | 33.728684 | 32.461067 |
| flash45_kda_mla / glm53flash-a3-tp16-c4 | 61 | 4 | 39.742414 | 37.043835 |
| flash45_kda_mla / glm53flash-a5-tp8-c3 | 53 | 1 | 21.057180 | 20.805273 |
| flash45_kda_mla / glm53flash-a5-tp8-c96 | 27 | 1 | 57.572611 | 57.354872 |
| flash45_kda_mla / glm53flash-a5-tp8-c1 | 65 | 1 | 15.670472 | 15.421254 |
| glm78_dsa / a3_glm53_dc4k_b1 | 74 | 1 | 38.942772 | 历史版本未记录 |
| glm78_dsa / a3_glm53_dc4k_b2 | 70 | 1 | 40.934812 | 历史版本未记录 |
| glm78_dsa / a3_glm53_dc4k_b4 | 67 | 1 | 43.436892 | 历史版本未记录 |
| glm78_dsa / a3_glm53_dc4k_b8 | 61 | 1 | 47.148578 | 历史版本未记录 |
| glm78_dsa / a3_glm53_dc16k_b1 | 74 | 1 | 39.104879 | 历史版本未记录 |

每个几何桶的 Layer0、排除 Layer0 后的 attention×FFN 类型统计及源身份均见 JSON。跨桶的表格值仅描述数据，Sim 对账应逐桶进行。
算子层已保留新七源的原始 op_statistic 入口和整窗统计，其口径包括 prefill/辅助段；尚未在本摘要中生成 Body 内角色对账，因此没有把未关联的算子说成 Sim 漏算。

历史 A5 的 glm53-a5、glm53-tp8、glm-c2c8 三个目录都是 Flash45 BF16 服务压测。目录及四个原始 tar 均未发现 kernel_details/op_summary/trace/DB，只有客户端与服务指标；它们的 TPOT 保留为 serving 事实，Body 和 Layer 耗时保持空值。
