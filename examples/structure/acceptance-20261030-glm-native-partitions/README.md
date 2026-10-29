# GLM Flash: retained complete native ABI populations

Nine existing A5 operator populations, 318 accepted Decode bodies and 27,666 selected events. Body endpoints and duration summaries remain unchanged. Every native-family duration histogram exactly matches its retained actual report.

| Source | Bodies | GMM Swiglu | Sparse MLA | Recurrent KDA |
|---|---:|---:|---:|---:|
| a5_glm53flash_tp8_c16_p4k | 30 | 1260 | 330 | 1020 |
| a5_glm53flash_tp8_c16_p8k | 32 | 1344 | 352 | 1088 |
| a5_glm53flash_tp8_c32_p4k | 31 | 1302 | 341 | 1054 |
| a5_glm53flash_tp8_c32_p8k | 35 | 1470 | 385 | 1190 |
| a5_glm53flash_tp8_c4_p8k | 11 | 462 | 121 | 374 |
| a5_glm53flash_tp8_c64_p4k | 31 | 1302 | 341 | 1054 |
| a5_glm53flash_tp8_c8_p4k | 30 | 1260 | 330 | 1020 |
| glm53flash-a5-tp8-c1 | 65 | 2730 | 715 | 2210 |
| glm53flash-a5-tp8-c3 | 53 | 2226 | 583 | 1802 |

Each source contains four complete ABI/topology partitions: GMM Swiglu in KDA-layer FFNs, GMM Swiglu in MLA-layer FFNs, the recurrent KDA anchor, and the sparse MLA anchor. All retain exact per-call duration histograms, layer/forward counts, full tensor shapes/dtypes/layouts and source locators. Example rows are supplementary; population coverage is established by the full partitions.

`GroupedMatmulSwigluQuantV2` buffer rows are capacity. They do not prove active routed rows, active experts or group-list values. `SparseFlashMla` index width 2,051 in the q=4 captures is retained verbatim; no unobserved valid top-k length is inferred. `RecurrentKda` flat tensor storage and state-pool capacity are also retained, not converted into fabricated active descriptors.

No new predictions are included in this evidence bundle. Strict contracts or conditional source-role costs must be derived independently by the comparer; references must remain outside strict accuracy denominators.

The initial c96 capture has Body evidence but no existing family actual in this input set, and is not included in these nine populations.

The parser ran once per source, with one additional content-hash read per source, and stopped after the last selected body head. Total elapsed 48.00 seconds; maximum source RSS 182.45 MiB. No remote collection or device work was performed.

Reproduction uses `collect_kimi_matrix_partitions.py` with repeatable `--native-type GroupedMatmulSwigluQuantV2 --native-type SparseFlashMla --native-type RecurrentKda`. Omitting these options preserves the original Kimi MatMulV3 CLI. Source/case/body input paths and hashes are in [native-partition-receipt.json](native-partition-receipt.json).
