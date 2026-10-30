# MC2 source counts and retained PMU constraints

Four domains, 16 native populations, 37,480 calls. No raw scans or Engine predictions.

| Case / population | Native | Calls | Scalar mean us | MTE2 mean us | MTE3 mean us | Source UB calls total / max owner |
|---|---|---:|---:|---:|---:|---:|
| a5_kimi_tp8_e16_bf16_c1_p4k / kda / steady_layers | dispatch | 4012 | 3.7369 | 1.5855 | 0.6137 | 167 / 72 |
| a5_kimi_tp8_e16_bf16_c1_p4k / kda / steady_layers | combine | 4012 | 7.5799 | 3.2935 | 0.4570 | 26 / 26 |
| a5_kimi_tp8_e16_bf16_c1_p4k / mla / steady_layers | dispatch | 1416 | 3.7266 | 1.5612 | 0.5889 | 167 / 72 |
| a5_kimi_tp8_e16_bf16_c1_p4k / mla / steady_layers | combine | 1416 | 7.4460 | 3.2377 | 0.4429 | 26 / 26 |
| a5_kimi_tp8_e16_bf16_c32_p4k / kda / steady_layers | dispatch | 3128 | 3.8902 | 1.8547 | 0.7098 | 287 / 72 |
| a5_kimi_tp8_e16_bf16_c32_p4k / kda / steady_layers | combine | 3128 | 6.7833 | 3.9029 | 0.6637 | 188 / 26 |
| a5_kimi_tp8_e16_bf16_c32_p4k / mla / steady_layers | dispatch | 1104 | 3.8574 | 1.8673 | 0.6975 | 287 / 72 |
| a5_kimi_tp8_e16_bf16_c32_p4k / mla / steady_layers | combine | 1104 | 6.8742 | 4.0072 | 0.6704 | 188 / 26 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / mla / steady_layers | dispatch | 5928 | 8.0027 | 14.3982 | 0.8698 | 1694 / 202 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / mla / layer0 | dispatch | 152 | 82.8755 | 272.3187 | 0.8753 | 1694 / 202 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / mla / steady_layers | combine | 5928 | 6.5702 | 2.0803 | 0.3078 | 41 / 26 |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 / mla / layer0 | combine | 152 | 6.4849 | 2.0972 | 0.3152 | 41 / 26 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / mla / steady_layers | dispatch | 2925 | 5.7582 | 4.6574 | 1.2955 | 1904 / 202 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / mla / steady_layers | combine | 2925 | 8.9485 | 5.1792 | 1.2435 | 328 / 26 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / mla / layer0 | dispatch | 75 | 9.6849 | 18.2508 | 1.3748 | 1904 / 202 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 / mla / layer0 | combine | 75 | 8.9512 | 5.0345 | 1.2596 | 328 / 26 |

- Each row preserves one native/ABI/Block/Mix/topology population; do not pool models or transport domains.
- Source calls are conditional source-program work, not established compiled ISA; native binary match is not established.
- Source totals and maximum per-owner counts are separate. Unknown exported PMU owner reduction forbids calling their ratio a scalar instruction price.
- Successful flag polling is enumerated; absent scalar-wait counters, failed polls, Notify/Wait, SyncAll and transaction amplification remain unknown.
- Task Wait Time is not scalar spin wait; elapsed minus maximum pipeline busy is not SyncAll latency.
- Packet/frame blocks are source protocol units, not measured network packets or hardware DMA descriptors.
- Joint response models may use observable population means within the same explicit domain; training/holdout is reported independently of admission.

The retained design has 8 distinct source programs, 8 columns and numerical rank 8. Algebraic rank does not establish independent prices because source families, precision, payload and owner schedules are confounded.

Runtime `c2b21f2023d096392ec7a4b7406df88d8611849a`; JSON keeps complete histograms, native descriptors where retained, layer counts, per-owner inventories, source ranges and exact input identities.

## Within-domain observed responses

Each domain has only two token/peer configurations (rank 2 for 8 candidate columns). The figures below are descriptive constraints, not isolated scalar or link prices. Native ABI changes remain attached to each point.

| Width / native / population | UB total ratio | UB max-owner ratio | Scalar high/low | MTE2 high/low | MTE3 high/low |
|---|---:|---:|---:|---:|---:|
| 3584 / MoeDistributeCombineV3 / kda / steady_layers | 7.2308 | 1.0000 | 0.8949 | 1.1850 | 1.4524 |
| 3584 / MoeDistributeDispatchV3 / kda / steady_layers | 1.7186 | 1.0000 | 1.0410 | 1.1698 | 1.1567 |
| 3584 / MoeDistributeCombineV3 / mla / steady_layers | 7.2308 | 1.0000 | 0.9232 | 1.2377 | 1.5139 |
| 3584 / MoeDistributeDispatchV3 / mla / steady_layers | 1.7186 | 1.0000 | 1.0351 | 1.1960 | 1.1845 |
| 5120 / MoeDistributeCombineV3 / mla / layer0 | 8.0000 | 1.0000 | 1.3803 | 2.4005 | 3.9959 |
| 5120 / MoeDistributeDispatchV3 / mla / layer0 | 1.1240 | 1.0000 | 0.1169 | 0.0670 | 1.5707 |
| 5120 / MoeDistributeCombineV3 / mla / steady_layers | 8.0000 | 1.0000 | 1.3620 | 2.4897 | 4.0403 |
| 5120 / MoeDistributeDispatchV3 / mla / steady_layers | 1.1240 | 1.0000 | 0.7195 | 0.3235 | 1.4894 |

Source UB totals rise in all eight comparisons while the maximum single-owner UB count stays fixed. Kimi Combine and V4.1 Dispatch scalar time falls in the larger-token population. These observations rule out treating all-owner UB calls divided by exported scalar busy time as one independently measured scalar rate. V4.1 Layer0 and steady populations retain the same source program but markedly different observed responses; they remain separate.

The copied source-operation details preserve historical field names such as `scalar_source_id_reads_unpriced` verbatim. Those names are provenance, not a statement that the current runtime does not charge the operation: the current `primitive_services` owner inventory is exported separately, and this report executes no cost model.

Qwen35 response parameters are outside this four-domain matrix. Current declarations and complete-population evidence are linked from `examples/structure/cases.json`; current operator scores are maintained in `examples/structure/results/operators.json`. FIA/GDN source-symbol applicability remains explicit and is separate from strict cohort admission.
