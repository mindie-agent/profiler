# Grouped source / PMU joint constraints

Each row retains its complete native ABI, integer call histogram, layer population and original Block/PMU scope. Capacity is not valid routed M. These are usable whole-call responses, not inferred descriptor prices. No new capture scan or prediction occurs in this join.

| Source | Role / attention | Capacity | Calls/F | Mean/P50 us | AIC MTE2 us | AIV scalar us | AIV MTE2 us |
|---|---|---:|---:|---:|---:|---:|---:|
| a3_glm53_w4a8_tp16_tpot30_c2 | expert_up_activation_quant / mla | 128 | 75 | 98.430/98.122 | 43.870 | 7.404 | 6.727 |
| a3_glm53_w4a8_tp16_tpot30_c2 | expert_down / mla | 128 | 75 | 56.918/56.381 | 27.158 | 8.982 | 3.881 |
| a3_glm53_w4a8_tp16_tpot50_c2 | expert_up_activation_quant / mla | 128 | 75 | 98.479/98.162 | 43.875 (3298/3300 numeric) | 7.406 (3298/3300 numeric) | 6.731 (3298/3300 numeric) |
| a3_glm53_w4a8_tp16_tpot50_c2 | expert_down / mla | 128 | 75 | 56.947/56.381 | 27.198 (3299/3300 numeric) | 9.005 (3299/3300 numeric) | 3.894 (3299/3300 numeric) |
| a3_glm53_w4a8_tp16_tpot88_c8 | expert_up_activation_quant / mla | 384 | 75 | 172.332/172.184 | 110.438 (3661/3675 numeric) | 8.670 (3661/3675 numeric) | 0.920 (3661/3675 numeric) |
| a3_glm53_w4a8_tp16_tpot88_c8 | expert_down / mla | 384 | 75 | 95.165/94.702 | 60.778 (3661/3675 numeric) | 11.691 (3661/3675 numeric) | 4.943 (3661/3675 numeric) |

A numeric-subset PMU mean is explicitly marked with its own denominator and is excluded from arithmetic against complete-call means. A3 count examples reuse the source schedule under the saved balanced-routing assumption, not observed group-list values. Source SetTensor submissions are not compiled DMA descriptors. A5 INT32 up is separate from the mixed BF16 dequant branch; the latter supports a geometric schedule only after actual routing and host tile selection are known. Neither BlockNum nor an all-owner count may divide an exporter aggregate into a per-core price. Signed PMU differences remain diagnostics.
