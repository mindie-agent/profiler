# A3 Kimi TP8 AllGather / ReduceScatter conditional reference

This acceptance reuses one complete retained Body geometry from the existing 66-capture HCCL ledger. It does not read the raw CSV, collect hardware data, or change a previously accepted Body boundary.

- Source: `a3_kimi4_tp8_w4a8_c32`, TP8 / EP8, A3 `Ascend910_9362`, four target layers.
- Selected population: q=1, shape-derived execution B=32, **220 complete forwards**. The source has **229 forwards / 6 geometries**; the other nine forwards are outside this explicitly selected population.
- Original ledger groups, full duration histograms and controller rows remain byte-equivalent in the retained projection. Source, original Body, corrected Body generation and original case identities are linked there.
- The only case change is explicit `runtime.kernels.hccl` AllGather and ReduceScatter selectors: `AICPU_TS`, `mesh`, axis `tp`. Model, hardware, precision, parallel layout and execution geometry remain unchanged.
- Fixed Sim runtime: `40e4300ea7ccc1123759f6201cc2d69e3aa77ad6`; official source reference: `c2d6790464654ccf58aca39448de4b65fdc7b184`. This identifies the source program being evaluated, not the captured binary or an observed template selection.

## Measurement and declaration boundaries

The eligible measured rows are `COMMUNICATION` HCOM envelopes. Their actual device engine, selected algorithm, payload values and parent/child transport task links are unobserved. Typed `AI_CPU` controller tasks remain separately retained and add neither calls nor elapsed to this reference. An HCOM envelope can include protocol and peer waiting; its difference from source service cannot be interpreted as link bandwidth or attributed causally to Body wall time.

The **declared** BF16 payload for AllGather is 57,344 bytes = 4 local SP rows × hidden 7,168 × 2 bytes. ReduceScatter uses 458,752 bytes = 32 rows × 7,168 × 2 bytes. These come from the original Sim sequence-parallel structure. They are not captured payload arguments. Context 4,096 is an explicit conditional prompt reference and does not establish active KV length.

Each cost includes the entire selected local-phase / peer-exchange program once, including entry/exit dependencies. Identical programs across layers share a cost memo; the memo representative op ID is not an observed occurrence binding. No AIV template is assigned to these envelopes.

## Results

**11 conditional groups / 3,300 calls**, two freshly executed source program sets, **zero strict cohorts**. AllGather service is **4.446575 us/call**; ReduceScatter service is **5.354522 us/call**.

| Native / region / layers | Calls | Real Mean us | Real P50 us | Conditional service us |
|---|---:|---:|---:|---:|
| hcom_allGather_ / attention / 0 | 220 | 221.270014 | 202.216000 | 4.446575 |
| hcom_allGather_ / attention / 1,2 | 440 | 66.884673 | 31.939500 | 4.446575 |
| hcom_allGather_ / ffn / 1,2 | 440 | 26.833593 | 26.549500 | 4.446575 |
| hcom_allGather_ / ffn / 0 | 220 | 48.289300 | 21.860000 | 4.446575 |
| hcom_reduceScatter_ / ffn / 1,2 | 440 | 23.497430 | 23.719000 | 5.354522 |
| hcom_reduceScatter_ / attention / 1,2 | 440 | 20.910502 | 18.380000 | 5.354522 |
| hcom_reduceScatter_ / ffn / 0 | 220 | 41.500250 | 29.329500 | 5.354522 |
| hcom_reduceScatter_ / attention / 3 | 220 | 29.563386 | 29.349500 | 5.354522 |
| hcom_allGather_ / attention / 3 | 220 | 28.995514 | 28.939000 | 4.446575 |
| hcom_reduceScatter_ / attention / 0 | 220 | 25.296123 | 18.410000 | 5.354522 |
| hcom_reduceScatter_ / ffn / 3 | 220 | 22.145218 | 22.200000 | 5.354522 |

An additional **440 MLA FFN AllGather calls** are preserved as unresolved: that complete saved region contains two calls per layer/forward, while this adapter requires one uniquely declared collective per region. It neither splits the pooled histogram nor selects a convenient call. All 3,740 eligible HCOM calls are therefore accounted for as 3,300 referenced + 440 unresolved.

Execution: **0 raw reads**, **0 reused predictions**, 2 new program sets, maximum RSS **59.58 MiB**, measured worker elapsed **0.155 s**. Two real-population regression tests verify full-histogram preservation, controller exclusion, complete collective programs and rejection of an unobserved AIV engine. Independent review passed **664 checks**, with zero raw reads or cost evaluations; see [review](source-caller-independent-review.json).

Artifacts: [input manifest](inputs.json), [retained population](a3_kimi4_tp8_w4a8_c32-retained-hccl.json), [conditional case](a3_kimi4_tp8_w4a8_c32-aicpu-ts-mesh.case.json), [result](source-caller-reference-scoreboard.json), [table](source-caller-reference-scoreboard.md).

Reproduce with the fixed 40e runtime available on `PYTHONPATH`:

```sh
python examples/structure/compare_source_caller_references.py \
  --inputs examples/structure/acceptance-20261030-hccl-aicpu-ts-reference/inputs.json \
  --output-dir examples/structure/acceptance-20261030-hccl-aicpu-ts-reference \
  --runtime-source-commit 40e4300ea7ccc1123759f6201cc2d69e3aa77ad6
```
