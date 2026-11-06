# Scoped native-structure fixtures

Minimized line subsets of genuine device `kernel_details.csv` captures. Line
numbers are renumbered in the fixture CSV; every selected row, its timestamp,
duration and tensor descriptor are copied verbatim. No timing value is changed
and no synthetic row is present. The observation JSON carries the selected
forward/layer spans and the source hashes.

## A3 AllToAll TP-slice mixed trace

`a3_qwen35_tp8_prefill_full_tail_decode_mixed.csv`

- Prefill source: `/Volumes/data/mindie-sim-data/a3/heldout_engine_20261031/qwen35_tp8_ep8_mtp0_prefill_400k_c1/kernel_details.csv`
  sha256 `b12ddd923e90e94738cfa1ef7ef3881c5c2b719bae171d81e24995adce226ba4`
- Frozen extraction: `/Volumes/data/mindie-sim-data/acceptance-archives-20261030/wave5-eval/a3/extractions/438248a6cd996d46fed4aaeb13e2a0f37efaf8d137b3b7680685d8792d0d57b5.json`
  (forwards 0 and 50; bodies are original lines 89-3406 and 170878-173796)
- Decode source: `/Volumes/data/mindie-sim-data/a3/heldout_engine_20261031/qwen35_tp8_ep8_mtp0_decode_192k_c1/kernel_details.csv`
  sha256 `5d33988ccb23d87d955b387de99c82387970f7231345da8260f36afc2b4f4dcf`
  (first forward, first 40 MoE layers; `MoeDistributeDispatchV2` /
  `MoeDistributeCombineV2` caller, kept only to prove an unrelated phase does
  not block the selected prefill windows)
- Windows: `prefill:0` q8064/context0, `prefill:50` q256/context399744,
  `decode:0` q1/context192000.
- Selected row predicates: router `MatMulV3`, `MoeGatingTopK`,
  `MoeTokenPermute`, `DynamicQuant`, `MoeInitRoutingV3`,
  `GroupedMatmulSwigluQuant`, `GroupedMatmul`, `MoeTokenUnpermute`,
  `allgatherAicpuKernel`, named `hcom_alltoallv`/`hcom_allGather`, every
  `TensorMove`, and the decode MC2 callers.
- Fixture sha256 `9c6b4e57625980f84be6c1cd2de1d466b11b3497b75712cc512358b3a4f71fe6`;
  observation sha256 `6762821aeaf0f7da3b10eb539dd2485f77556f1673d577b25c1890637f9f6027`.

The full window repeats 8 `TensorMove` gather copies per layer, while the tail
window has none. The projection records that difference as `per_rank_copy` vs
`view`; it does not borrow the full window's row shape for the tail.

## A5 eager local-expert windows

`a5_qwen30b_e16k4_prefill_4k.csv` (q4096/context0, one forward) and
`a5_qwen30b_e16k4_prefill_64k.csv` (q8192/context0..57344, eight forwards).

- Source: `/Volumes/data/mindie-sim-data/a5/heldout_engine_20261031/a5_synth_qwen30b_L8_E16_K4_tp4ep4_prefill_4k_c1/kernel_details.csv`
  sha256 `bac97a21d4699c2619123453797ebcebd201eee0199fa4824c60330816ea6d84`
  and `.../a5_synth_qwen30b_L8_E16_K4_tp4ep4_prefill_64k_c1/kernel_details.csv`
  sha256 `2af0fb3423bded7378f701cbc6958d61915f122b30169b4e19456a7322c28016`
- Selected rows: `MatMulV3`, `MoeGatingTopK`, `MoeInitRoutingV3`, both
  `GroupedMatmul` calls, `SwiGlu`, `MoeFinalizeRoutingV2`, named
  `hcom_allReduce` before and after the routed chain.
- `4k` fixture sha256 `f28e083da7764f44368299fe14c9f3112d2b216c9212105d6657a9a7562ee3cc`,
  observation sha256 `689cf89ea478ef144e409c5bcd8b2afbc508b0a4684edad5c8fa996104ba8b11`.
- `64k` fixture sha256 `ef9ce43985151c526dc8f23d88bc1ad253d95cab7da13c644adb9f2ade3f5a5d`,
  observation sha256 `92bd733a462483727460bc7330dc2e896487f876c8d0a626f8835d4ea5bd3f26`.

The 64K window has eight identical-query forward spans distinguished only by
context. The resolver selects exactly one by requested context; other contexts
are unavailable rather than silently reusing the first row shape.

The A5 native grouped descriptor M is the allocated `q*top_k` buffer, not the
valid local-assignment count. The projection keeps that allocation separate
from the declared-policy local-bank valid rows and the unmasked SwiGlu
full-capacity rows; it does not require the Sim graph to copy the captured
buffer extent as matrix work. For `balanced` routing the local bank is the
forced integer ledger, so E48 q4096/K4 expects 4104 rows rather than the
uniform rank average 4096; the uniform average is retained only as an explicit
reference field. For the four historical 20261031 E48 captures, balanced
routing is inherited from the archived template contract; the generic
`routing_basis` label only says `declared_balanced_integer_ledger` and does not
infer that origin for other explicit raws. Those commands contain no force-EPLB
literal, so this is not a native force-EPLB observation.

`a3_case.json` / `a5_case.json` are minimal source-model declarations for
descriptor validation. They contain no capture path, hash or measured value.
