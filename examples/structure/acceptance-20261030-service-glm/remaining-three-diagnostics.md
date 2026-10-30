# Remaining three GLM cases: boundary and service evidence

No new cost or capture read. References below are current scheduled node intervals including waiting, not isolated kernel service. Component intervals and native activities are not additive Body-error allocations.

| Source | Native / role | Calls/F | Native Mean / P50 us | Native ms/F | Current reference |
|---|---|---:|---:|---:|---|
| a5_glm53flash_tp8_c8_p4k | HcPre / whole retained population | 90 | 13.853 / 13.681 | 1.246733 | 6 stages × 90 calls; projection alone scheduled 1.440567ms/F (not an atomic native comparison) |
| a5_glm53flash_tp8_c8_p4k | MatMulV3 / linear_qkvbfg_a | 34 | 20.058 / 19.984 | 0.681975 | scheduled 10.157us/call; 0.345355ms/F |
| a5_glm53flash_tp8_c8_p4k | Slice / whole retained population | 224 | 2.797 / 2.424 | 0.626465 | no_independent_recipe_correspondence_retained |
| a5_glm53flash_tp8_c8_p4k | SparseFlashMlaMetadata / whole retained population | 11 | 43.981 / 41.179 | 0.483788 | no_independent_recipe_correspondence_retained |
| a5_glm53flash_tp8_c4_p8k | HcPre / whole retained population | 90 | 11.847 / 11.668 | 1.066196 | 6 stages × 90 calls; projection alone scheduled 1.440567ms/F (not an atomic native comparison) |
| a5_glm53flash_tp8_c4_p8k | MatMulV3 / linear_qkvbfg_a | 34 | 18.014 / 17.927 | 0.612472 | scheduled 9.089us/call; 0.309040ms/F |
| a5_glm53flash_tp8_c4_p8k | Slice / whole retained population | 224 | 2.608 / 2.140 | 0.584188 | no_independent_recipe_correspondence_retained |
| a5_glm53flash_tp8_c4_p8k | SparseFlashMlaMetadata / whole retained population | 11 | 39.293 / 36.752 | 0.432221 | no_independent_recipe_correspondence_retained |
| glm53flash-a5-tp8-c1 | HcPre / whole retained population | 90 | 11.125 / 10.974 | 1.001237 | 6 stages × 90 calls; projection alone scheduled 1.256896ms/F (not an atomic native comparison) |
| glm53flash-a5-tp8-c1 | MatMulV3 / linear_qkvbfg_a | 34 | 16.983 / 16.915 | 0.577427 | scheduled 8.288us/call; 0.281804ms/F |
| glm53flash-a5-tp8-c1 | Slice / whole retained population | 224 | 2.151 / 1.935 | 0.481761 | no_independent_recipe_correspondence_retained |
| glm53flash-a5-tp8-c1 | SparseFlashMlaMetadata / whole retained population | 11 | 34.980 / 31.811 | 0.384785 | no_independent_recipe_correspondence_retained |

No extra regime is added by this diagnostic. Native ABI gaps and missing atomic boundaries remain visible; the listed recipes may already account for physical work.
