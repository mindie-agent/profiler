# Native Fusion Coverage From Final Saved Cases

Historical retained captures; no new live collection. Final `.case.json` artifacts, artifact hashes and freshly exported graph IDs determine replay evidence.

8 unique captures contain 668,835 events and 148 native types. Declaration variants do not enlarge that denominator.

Fresh graph verification: 13 saved replay declarations, CPython 3.13.12, `/Users/maoxx241/code/sim-rewrite-20261027/.venv/bin/python`.

The 59 required model-body types contain 328,927 events: 47 types have declared boundaries, 45 have complete boundaries, 33 have comparable contracts, and 31 match at least one retained original fixture row. These are distinct evidence levels, not a count of bound layer occurrences.

Default declarations and source-selected variants remain separate. A Transformer block contains Attention and FFN; FFN may be MoE. Candidate geometry does not bind a layer occurrence.

| Native type | Events | Default boundary | Replay boundary | Replay contract | Fixture matches |
| --- | ---: | --- | --- | --- | ---: |
| `GroupedMatmul` | 35,979 | complete | complete_boundary_declared | comparable_declared_contract | 3/10 |
| `QuantBatchMatmulV3` | 27,406 | complete | complete_boundary_declared | comparable_declared_contract | 13/16 |
| `DynamicQuant` | 23,551 | complete | complete_boundary_declared | comparable_declared_contract | 11/12 |
| `DynamicMxQuant` | 23,459 | complete | complete_boundary_declared | comparable_declared_contract | 2/4 |
| `AddRmsNormBias` | 19,247 | not selected | complete_boundary_declared | comparable_declared_contract | 2/6 |
| `MoeGatingTopK` | 15,638 | complete | complete_boundary_declared | comparable_declared_contract | 3/6 |
| `AttnResFwd` | 14,768 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/2 |
| `QuantBatchMatmulV4` | 14,531 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/2 |
| `MoeInitRoutingV3` | 9,032 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/10 |
| `MoeTokenUnpermute` | 8,956 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/8 |
| `CausalConv1d` | 8,853 | complete | complete_boundary_declared | comparable_declared_contract | 1/8 |
| `TransposeBatchMatMul` | 7,940 | complete | complete_boundary_declared | comparable_declared_contract | 3/5 |
| `MlaPrologV3` | 7,648 | not selected | complete_boundary_declared | comparable_declared_contract | 4/5 |
| `GroupedMatmulSituQuant` | 7,266 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/2 |
| `SituMxQuant` | 7,266 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/2 |
| `RmsNormDynamicMxQuant` | 7,265 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/2 |
| `l2norm_fwd_kernel2` | 7,260 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/6 |
| `MoeDistributeDispatchV3` | 6,898 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/1 |
| `MoeDistributeCombineV3` | 6,897 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/1 |
| `DequantSwigluQuant` | 5,917 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/4 |
| `GroupedMatmulSwigluQuantV2` | 5,873 | complete | complete_boundary_declared | comparable_declared_contract | 4/4 |
| `SparseFlashAttention` | 5,850 | complete | complete_boundary_declared | comparable_declared_contract | 2/2 |
| `layer_norm_gated_fwd_kernel` | 5,451 | complete | complete_boundary_declared | comparable_declared_contract | 1/2 |
| `RecurrentKda` | 5,175 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/2 |
| `SwiGlu` | 4,982 | complete | complete_boundary_declared | comparable_declared_contract | 6/8 |
| `_layer_norm_fwd_1pass_kernel_npu` | 3,402 | complete | complete_boundary_declared | comparable_declared_contract | 3/6 |
| `fused_gdn_gating_kernel` | 3,402 | complete | complete_boundary_declared | comparable_declared_contract | 3/6 |
| `FusedInferAttentionScore` | 3,254 | complete | complete_boundary_declared | comparable_declared_contract | 3/8 |
| `RecurrentGatedDeltaRule` | 3,198 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/3 |
| `_triton_rope_siso` | 3,150 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/3 |
| `GroupedMatmulSwigluQuant` | 2,724 | complete | complete_boundary_declared | comparable_declared_contract | 4/4 |
| `RmsNorm` | 1,652 | complete | complete_boundary_declared | comparable_declared_contract | 4/10 |
| `LayerNormV3` | 1,575 | complete | complete_boundary_declared | comparable_declared_contract | 2/2 |
| `LightningIndexer` | 1,575 | complete | complete_boundary_declared | comparable_declared_contract | 2/2 |
| `ScatterPaKvCache` | 1,384 | complete | complete_boundary_declared | comparable_declared_contract | 6/8 |
| `split_qkv_rmsnorm_mrope_kernel` | 1,288 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/8 |
| `ChunkKdaFwd` | 1,104 | incomplete | incomplete_boundary_only | declared_boundary_without_comparable_contract | 0/1 |
| `InplacePartialRotaryMul` | 1,017 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/4 |
| `AddRmsNormDynamicMxQuant` | 960 | complete | complete_boundary_declared | comparable_declared_contract | 1/2 |
| `MoeFinalizeRoutingV2` | 736 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/2 |
| `AddRmsNorm` | 648 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/2 |
| `HcPost` | 584 | complete | complete_boundary_declared | comparable_declared_contract | 2/2 |
| `HcPre` | 584 | complete | complete_boundary_declared | comparable_declared_contract | 2/2 |
| `GemmaRmsNorm` | 438 | complete | complete_boundary_declared | comparable_declared_contract | 2/4 |
| `Compressor` | 426 | complete | complete_boundary_declared | comparable_declared_contract | 0/6 |
| `MatmulReduceScatterV2` | 372 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/1 |
| `MoeInitRoutingV2` | 368 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/1 |
| `MoeGatingTopKHash` | 292 | complete | complete_boundary_declared | comparable_declared_contract | 0/4 |
| `MoeTokenPermute` | 292 | complete | complete_boundary_declared | declared_boundary_without_comparable_contract | 0/2 |
| `RmsNormCast` | 292 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/2 |
| `SparseAttnSharedkv` | 292 | complete | complete_boundary_declared | comparable_declared_contract | 4/4 |
| `AddRmsNormDynamicQuant` | 225 | not selected | complete_boundary_declared | comparable_declared_contract | 2/2 |
| `ChunkGatedDeltaRuleFwd` | 156 | incomplete | incomplete_boundary_only | declared_boundary_without_comparable_contract | 0/2 |
| `VllmAscendQuantLightningIndexerV2` | 141 | complete | complete_boundary_declared | comparable_declared_contract | 2/2 |
| `AttentionUpdate` | 72 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/1 |
| `_copy_pcp_kv_cache_kernel` | 72 | not selected | not_declared_in_replay_cases | no_native_declaration_in_replay_cases | 0/2 |
| `ChunkFwdH` | 48 | complete | complete_boundary_declared | comparable_declared_contract | 1/1 |
| `ChunkFwdO` | 48 | complete | complete_boundary_declared | comparable_declared_contract | 1/1 |
| `ChunkGatedDeltaRuleFwdPrepare` | 48 | complete | complete_boundary_declared | comparable_declared_contract | 1/1 |

GLM native normalization uses the separately saved source/checkpoint-conditional choices; the catalog default is not retroactively changed. Kimi SiTU and RMS MX mechanisms can exist while the retained BF16 activation declaration does not select them. See `head-normalization-evidence.json` for the global bias predicate and precision limits.

12 required types have no native target in the saved replay declarations (27 capture/type pairs). This is not an unimplemented-mechanism count. QuantBatchMatmulV4, RMS MX and SiTU MX need the appropriate precision/activation declaration; recurrent GDN and AttentionUpdate require the corresponding phase or parallelism. GroupedMatmulSituQuant retains an exact-native-boundary source gap. Per-capture reasons and capability sources remain in the JSON.

ChunkKdaFwd and ChunkGatedDeltaRuleFwd incomplete native boundaries remain outside complete contract/resource coverage. Full JSON preserves all 148 types, raw missingness, source branches, per-declaration fixture matches and full-capture status/reason counts.

Fixture examples are deduplicated by original capture and source line. Full-replay counts stay per declaration and must not be summed as additional hardware evidence. No inclusive fused duration is divided among member nodes.
