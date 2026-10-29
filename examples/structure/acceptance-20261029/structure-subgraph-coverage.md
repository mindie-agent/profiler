# Historical A3/A5 structure and subgraph coverage

This is an offline replay of existing captures on 2026-10-29, not a new live
collection. Eight distinct full retained capture files contain 668,835 kernel
rows. Nine declarations are replayed because the same mixed Kimi capture is
compared with both a prefill declaration and a decode declaration. Those two
replays are not additional collected evidence.

The implementation can now compare one measured kernel with a declared
multi-operator subgraph. GLM A3 provides complete-capture acceptance for
`MlaPrologV3` and `LightningIndexer`: all 7,425 instances of these two types have
compatible subgraph candidates. They remain ambiguous across repeated layers;
none has a verified layer or invocation assignment.

The four evidence levels must remain separate:

1. A sim layer plan and operator DAG declare model structure.
2. A normalized native row records tensor descriptors from a capture.
3. Compatible contracts identify candidate nodes/subgraphs and properties shared
   by every candidate.
4. Host/module/explicit occurrence evidence is required to bind an individual
   layer and invocation. These eight capture inputs do not supply that evidence.

## Full-capture checks

| Capture and declaration | Complete rows | Target native events | Result |
| --- | ---: | --- | --- |
| GLM-5.3 A3 prefill, 4096 tokens, TP8 | 2,392 | MlaPrologV3 78; LightningIndexer 21 | All 99 have ambiguous subgraph candidates |
| GLM-5.3 A3 decode, 1 token, TP8 | 166,204 | MlaPrologV3 5,772; LightningIndexer 1,554 | All 7,326 have ambiguous subgraph candidates |
| DeepSeek V4 Flash A3 prefill, 4096 tokens, TP8 | 4,064 | QuantLightningIndexerV2 21; SparseAttnSharedkv 44 | Quantized Indexer contract gap; all 44 sparse attention events have candidates |
| DeepSeek V4 Pro A3 prefill, 1024-token chunks, TP16 | 24,271 | QuantLightningIndexerV2 120; SparseAttnSharedkv 248 | Quantized Indexer contract gap; 244 sparse attention candidates, 4 declaration mismatches |
| Qwen3.5 A3, 8192-token prefill declaration | 121,802 | FIA 737; cache store 737 | 11 FIA and 22 cache events have candidates; other phases/geometries remain visible |
| Qwen3.6 A3, 8192-token prefill declaration | 40,628 | FIA 323; cache store 323 | 17 FIA and 34 cache events have candidates |
| Qwen3.8 A5, 16384-token prefill declaration | 22,486 | FIA 228; cache store 228; GDN prepare/state/output 48 each | 17 FIA, 17 cache, and all 144 GDN native events have candidates |
| Kimi K3 A5 mixed window, 8192-token prefill declaration | 286,988 | Gated norm 5,451; MlaPrologV3 1,798 | 276 gated norm candidates; 5,175 gated norm rows lack descriptors; no selected MlaProlog boundary |
| Same Kimi file, 1-token decode with explicit MlaProlog implementation | Same 286,988 | MlaPrologV3 1,798 | Active descriptors parsed; BF16 declaration versus FP8 capture prevents a match |

The raw spelling of the DeepSeek operator is
`VllmAscendQuantLightningIndexerV2`. It is not an alias of BF16
`LightningIndexer`. The independent DeepSeek serving scripts select INT8 Indexer
KV. Flash has one complete native descriptor branch with output
`[4096, 1, 512]`; Pro has one with output `[1024, 1, 1024]`. Both contain 14
input slots and three output slots. Metadata kernels are counted separately
(Flash one, Pro four).

GLM MlaProlog has two distinct output branches. Prefill has 21 rows returning
Q-normalization output and 57 without it; decode has 1,554 and 4,218 respectively.
The declared full/shared Indexer schedule produces disjoint 21-layer and
57-layer candidate sets. The counts do not establish an ordered layer or decode
token identity.

## Structural coverage matrix

The declaration inventory exports 11 existing cases through the ordinary sim
frontend. A one-token metadata probe is used only to inspect supported structure
and contract families; it is not a new serving run. Counts and raw layer-plan
fields are retained in `structure-declaration-coverage.json`.

The frontend also retains each operator's actual `block` (`attention` or `ffn`)
and `role` (`body` or `residual`) at its construction boundary. Ordinary GEMMs,
mHC and attention-residual operators therefore remain visible under the correct
block even where a native matching contract is still missing. Expanded children
and joins inherit that declared scope. These are declared graph relationships,
not inferred event occurrences.

| Structure | Independent declaration | Native contract / measured candidate coverage | Remaining boundary |
| --- | --- | --- | --- |
| GQA | Qwen2.5 dense GQA; Qwen3.5/3.6/3.8 gated GQA | FIA active-Q/K/V/output and cache-store contracts; A3/A5 candidates above | Masks, sequence values, dispatch flags and repeated-layer occurrences are not resolved |
| MLA | GLM and Kimi latent MLA | GLM MlaProlog composite and sparse-attention candidates | Explicit source implementation selection is required; Kimi attention precision identity remains unresolved |
| DSA | GLM `mla_dsa`, full/shared Indexer schedule | Ordinary LightningIndexer score/top-k subgraph plus SparseFlashAttention | Quantized Indexer is a different ABI; shared candidate properties do not identify the producing layer |
| SWA | DeepSeek local window branches; Flash has two `swa_only` layers | Shared-KV sparse attention contracts include local-only candidates | A compressed layer also has a local branch; the whole layer must not be relabeled as pure SWA |
| CSA | V4 Flash/Pro `dsa_compressed_4`, window-compressed cache, Indexer enabled | Real quantized Indexer rows and shared-KV attention rows exist | Quantized Indexer and Compressor contracts are gaps; shared attention candidates alone do not prove the full CSA path |
| HCA | V4 Flash/Pro `dsa_compressed_128`, window-compressed cache, Indexer disabled | Compressor and sparse-attention kernels are present in complete captures | No Compressor contract; some sparse candidates span CSA/HCA, so HCA execution is not separately bound |
| KDA | Kimi 69 of 93 layers; GLM A5 hybrid 34 of 45 layers | Kimi active gated-norm rows: 276 candidates | ChunkKdaFwd 1,104 and RecurrentKda 5,175 remain contract gaps; no full-model GLM A5 kernel capture in the inspected inventory |
| GDN | Qwen3.5 30/40; Qwen3.6/3.8 48/64 layers | Native prepare/state/output contracts and recurrent/norm projections; A5 48 events per native chunk stage match | Mixed decode descriptors and implementation geometry are not all covered |
| MoE | GLM, DeepSeek, Kimi, Qwen3.5 routed/shared expert graphs | Individual matrix/activation contracts exist, and real grouped-MoE kernels are captured | GroupedMatmul, Situ quantization/routing and dispatch fusions are not a complete MoE contract or composite mapping |
| MLP | Qwen2.5/3.6/3.8 dense FFNs and GLM/Kimi dense layers | MatMul/SwiGLU contracts; e.g. GLM prefill three and decode 222 SwiGLU candidates | Constituent candidates do not establish one measured FFN boundary or its layer |
| Residual | Ordinary residual add and normalization DAGs | Some AddRmsNorm/Gemma native contracts exist | Source weight/bias conventions and separate add/fusion declarations still mismatch; no general residual composite acceptance |
| mHC | DeepSeek and GLM A5 hybrid hyper-connection DAGs | Real HcPre/HcPost: Flash 88/88; Pro 496/496 | Native contracts and measured composite candidates are absent |
| Attention residual | Kimi residual source accumulation, normalization, scores and mix | Real AttnResFwd: 14,768 events | Native contract/composite support is absent; a layer's `residual_kind` annotation is not an AttnResFwd match |

CSA/HCA terminology is checked against the Hugging Face Transformers
`deepseek_v4` documentation, Architecture section 2.3:
`https://huggingface.co/docs/transformers/model_doc/deepseek_v4`.
CSA combines low compression, overlapping compression and Lightning top-k
selection; HCA uses high compression without an Indexer and attends all pooled
entries. The labels above use architecture, cache policy and Indexer ownership
together with the compression ratio. V4.1 shared-compression ratios 1/2 remain
reported in their raw declared terms, rather than being assigned these labels
from a ratio alone.

All new A3/A5 reports have zero bound subgraphs, zero bound layers and zero
bound busy time. A `structural_groups` entry reports only properties common to
every compatible candidate. In particular, `ffn_kind=moe` or
`residual_kind=mhc` describes the candidate's originating layer and is not proof
that a measured kernel performs MoE or mHC.

The final serial replay processed 955,823 event-window occurrences across the
nine declarations in 126.891 seconds, with a whole-process peak RSS of
346,980,352 bytes (330.906 MiB). This includes the repeated Kimi declaration;
the distinct captured-row denominator remains 668,835. Each report's source
hash matches its previous body replay, and its graph hash is independently
re-exported. Three focused streaming-replay tests pass, including both GLM
output branches and the Kimi mixed-window precision mismatch.

After the final lowering-domain corrections, a fresh Python process
re-exported all nine declarations: every graph hash still matched its saved
report, so no capture rescan was needed. Every exported body node in these
declarations has a known attention/FFN block and body/residual role. The
validation JSON records the source hashes at this final check separately from
the scan-time hashes.

## Source and implementation boundaries

GLM MlaProlog comparisons explicitly select
`runtime.kernels.lowerings.mla_prolog=vllm_ascend_mla_prolog_v3`. The original case
file is unchanged. Each report preserves its base case hash, implementation
override and independent source declaration. The source requires an
unquantized absorbed KV projection and provides the MlaPrologV3 call boundary.
This establishes the selected declaration, not the capture's binary identity.
Invalid configurations now fail explicitly: a quantized prolog requires its
activation-quantization lowering, and its exposed quantized query-normalization
output must feed a compatible Indexer input declaration. Disabling the required
lowering or declaring a BF16 Indexer input for that quantized boundary is not
silently treated as a matching tensor contract.

Kimi has complete native FP8 descriptors, including its original rank-three
input and rank-four query outputs. Its independent case declares BF16 dense
attention and routed-expert-only MXFP4. The archived serving recipe/logs retain
Ascend quantization selection and MLAPO, but no per-module checkpoint
`quant_model_description.json` or equivalent weight headers. A local A5 runtime
source proves an activation quantization mechanism; it does not establish the
checkpoint's attention weight types. This is a declaration/capture
configuration-identity gap, not a CSV parser or tensor-shape omission. See
`kimi-mla-configuration-gap.json` for archive members, source revisions and
hashes.

An active comparison contract deliberately excludes fields such as cache
capacity, physical parameter packing, scale values and scalar dispatch flags.
The complete native descriptor and comparison scope remain available in
retained examples. Matching the active projection does not claim full binary
ABI equivalence.

## Artifacts and reproduction

- `subgraph-capture-branches.json`: full-window type frequencies, every distinct
  target descriptor branch, original source line, hardware and run evidence.
- `structure-declaration-coverage.json`: source hashes and exported structure,
  family and contract counts for 11 independent cases.
- `subgraph-a*.json`: nine new complete-window replay reports, including
  structural classifications and bounded representative body examples.
- `subgraph-replay-validation.json`: relevant module fingerprints before/after the
  serial batch, independent graph-hash recomputation, count checks, elapsed time
  and peak resident memory.
- `kimi-mla-configuration-gap.json`: independent precision evidence and the
  missing checkpoint configuration.

The existing `body-*.json`, A2 module replay and earlier fixture/full-capture
reports are retained unchanged. The reusable entry point remains
`examples/structure/replay_body_capture.py`. Its optional repeatable
`--lowering SELECTOR=IMPLEMENTATION` and `--lowering-source` arguments record an
explicit implementation declaration. `--capture`, `--case`, `--phase`,
`--tokens`, `--context` and `--sequences` reproduce the declaration stored in
each report. The companion sim source checkout must be on `PYTHONPATH`; no
device runtime, model weights or remote collection is required.

Final local maintained suites passed after the lowering-domain corrections:
profiler 450 passed and 26 skipped; sim 1,131 passed with live NPU tests excluded.
Whitespace and LF checks passed in all three affected repositories. These checks
and the historical replay do not establish a newly collected live run.
