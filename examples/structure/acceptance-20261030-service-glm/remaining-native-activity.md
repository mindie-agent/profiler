# Native activity outside the assigned service regimes

These measurements prioritize the next investigation. They do not establish missing Sim cost or an additive Body error budget. The current six service rules remain unchanged.

| Source | Native / role | Calls/F | Mean / P50 us | Activity ms/F | >50us/call |
|---|---|---:|---:|---:|---|
| a5_glm53flash_tp8_c16_p4k | GroupedMatmul / expert_down | 42.00 | 103.104 / 102.832 | 4.330352 | True |
| a5_glm53flash_tp8_c16_p4k | SparseFlashMla / unresolved | 11.00 | 86.586 / 86.495 | 0.952450 | True |
| a5_glm53flash_tp8_c16_p4k | _glm5_next_lightning_indexer_score_kernel / unresolved | 11.00 | 71.028 / 70.959 | 0.781306 | True |
| a5_glm53flash_tp8_c16_p4k | MatMulV3 / linear_qkvbfg_a | 34.00 | 22.750 / 22.715 | 0.773508 | False |
| a5_glm53flash_tp8_c16_p4k | Slice / unresolved | 224.00 | 3.046 / 2.909 | 0.682395 | False |
| a5_glm53flash_tp8_c16_p8k | GroupedMatmul / expert_down | 42.00 | 102.724 / 102.578 | 4.314396 | True |
| a5_glm53flash_tp8_c16_p8k | _glm5_next_lightning_indexer_score_kernel / unresolved | 11.00 | 126.802 / 126.864 | 1.394823 | True |
| a5_glm53flash_tp8_c16_p8k | SparseFlashMla / unresolved | 11.00 | 86.858 / 86.710 | 0.955436 | True |
| a5_glm53flash_tp8_c16_p8k | MatMulV3 / linear_qkvbfg_a | 34.00 | 22.732 / 22.767 | 0.772897 | False |
| a5_glm53flash_tp8_c16_p8k | Slice / unresolved | 224.00 | 3.042 / 2.916 | 0.681352 | False |
| a5_glm53flash_tp8_c8_p4k | GroupedMatmul / expert_down | 42.00 | 91.186 / 90.988 | 3.829819 | True |
| a5_glm53flash_tp8_c8_p4k | _glm5_next_lightning_indexer_score_kernel / unresolved | 11.00 | 69.982 / 69.982 | 0.769806 | True |
| a5_glm53flash_tp8_c8_p4k | MatMulV3 / linear_qkvbfg_a | 34.00 | 20.058 / 19.984 | 0.681975 | False |
| a5_glm53flash_tp8_c8_p4k | HcPre / ffn.hc_pre | 45.00 | 14.085 / 13.919 | 0.633840 | False |
| a5_glm53flash_tp8_c8_p4k | Slice / unresolved | 224.00 | 2.797 / 2.424 | 0.626465 | False |
| a5_glm53flash_tp8_c4_p8k | GroupedMatmul / expert_down | 42.00 | 51.435 / 51.334 | 2.160277 | True |
| a5_glm53flash_tp8_c4_p8k | MatMulV3 / linear_qkvbfg_a | 34.00 | 18.014 / 17.927 | 0.612472 | False |
| a5_glm53flash_tp8_c4_p8k | Slice / unresolved | 224.00 | 2.608 / 2.140 | 0.584188 | False |
| a5_glm53flash_tp8_c4_p8k | SparseFlashMla / unresolved | 11.00 | 52.802 / 52.896 | 0.580827 | True |
| a5_glm53flash_tp8_c4_p8k | HcPre / ffn.hc_pre | 45.00 | 11.933 / 11.783 | 0.536972 | False |
| glm53flash-a5-tp8-c3 | GroupedMatmul / expert_down | 42.00 | 51.524 / 51.382 | 2.164016 | True |
| glm53flash-a5-tp8-c3 | MatMulV3 / linear_qkvbfg_a | 34.00 | 17.826 / 17.762 | 0.606079 | False |
| glm53flash-a5-tp8-c3 | Slice / unresolved | 224.00 | 2.624 / 2.156 | 0.587852 | False |
| glm53flash-a5-tp8-c3 | SparseFlashMla / unresolved | 11.00 | 52.104 / 52.102 | 0.573141 | True |
| glm53flash-a5-tp8-c3 | HcPre / ffn.hc_pre | 45.00 | 11.905 / 11.728 | 0.535747 | False |
| glm53flash-a5-tp8-c1 | GroupedMatmul / expert_down | 42.00 | 22.482 / 22.473 | 0.944230 | False |
| glm53flash-a5-tp8-c1 | MatMulV3 / linear_qkvbfg_a | 34.00 | 16.983 / 16.915 | 0.577427 | False |
| glm53flash-a5-tp8-c1 | SparseFlashMla / unresolved | 11.00 | 51.517 / 51.481 | 0.566690 | True |
| glm53flash-a5-tp8-c1 | HcPre / ffn.hc_pre | 45.00 | 11.217 / 11.078 | 0.504749 | False |
| glm53flash-a5-tp8-c1 | HcPre / attention.hc_pre | 45.00 | 11.033 / 10.866 | 0.496488 | False |
