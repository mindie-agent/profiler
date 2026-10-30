# Complete-capture and accepted-Body HCCL evidence

66 independent local captures, all 5,250 previously accepted target bodies and 222 execution geometries are reconciled. The complete CSV pass parsed 12,706,254 events; capture signature inventory includes all phases and raw summary rows. Body groups reuse the exact accepted integer endpoints and deduplicate only identical device/type/start/end summary/device pairs. No Body was shortened and no new simulation or capture was performed.

All nine earlier A5 primary populations (495 Bodies) retain identical HCOM duration histograms. Their additional scan explicitly adds full-capture inventory and previously unselected accepted geometries; it does not replace the earlier successful receipts.

Validation: 574,988 complete-histogram, PMU, source-identity, geometry and endpoint checks; zero failures. A separate root-agent review checked 7,457 source-hash, full-histogram and population invariants with zero failures (no raw reread). Successful worker elapsed sum 611.93 s; maximum worker RSS 330.16 MiB, review 266.39 MiB. The full-capture scope has 67 scan attempts for 66 successful sources: one old Kimi scan completed parsing but failed while incorrectly inventorying its enclosing temporary directory. The preserved failed receipt and one retry identify the metadata-only correction. The other 65 successes were reused unchanged, with their own collector hashes.

`capture_inventory` is phase-unclassified and preserves original rows; it must not be added to `body_geometry_groups`. Controller, SDMA/Notify/CCU candidates and native fused communication programs are separate categories, not additive parts of HCOM elapsed. A source-level temporal region does not prove controller ownership.

24,806 `reduce_scatterAicpuKernel` rows are retained in the controller-alias overlay. The current tail policy recognizes the underscore-free spelling. This is a parser coverage finding, not permission to subtract these events or their durations from existing Body spans.

Files: `inputs.json` fixes 66 source identities and already exported Sim model topology; `execution-receipt.json` preserves retry history; `capture-body-hccl-summary.json` indexes all per-source evidence and all geometries; `associated-artifacts.json` inventories neighbouring trace/DB/communication/raw-profiler files and retained rank files. Each `*-capture-hccl.json` preserves full duration/PMU counters and bounded exact locators.

## Associated artifacts and linkage

Filesystem metadata was checked recursively within 62 capture roots. None contains a standalone timeline trace or profiler DB. Sixty sources retain step-trace exports; these are listed separately and are not assumed to identify individual model forwards. The old Kimi staged CSV is tied by exact member SHA to `k3lc-os1.tgz`. That archive contains a 524-byte communication-statistic CSV and a compressed PyTorch trace. The latter was streamed and contains 425,759 Python frames, 64 metadata events, one profiler range and two instant markers: no NPU Task/Stream/correlation fields, flow relations, or HCCL algorithm names. Its status is **existing_trace_but_no_device_correlation**, not missing trace. Communication statistics contain Count/Total/Min/Avg/Max/Ratio only, not measured payload bytes.

Rank-file counts below include the primary tp0 when a ranks directory exists. They inventory available local evidence; this pass does not claim clocks or peer/task associations across those ranks. All primary source files remain accounted for even when the rank-directory count is zero.

| Capture | Accepted Bodies | Geometries | Step export | Timeline/DB | Rank kernel files | Additional evidence |
|---|---:|---:|---|---|---:|---|
| glm53flash-a3-tp16-c4-livepre | 73 | 4 | yes | none retained standalone | 16 | — |
| glm53flash-a3-tp16-c16-livepre | 108 | 13 | yes | none retained standalone | 16 | — |
| glm53flash-a3-tp16-c2 | 58 | 2 | yes | none retained standalone | 16 | — |
| glm53flash-a3-tp16-c4 | 61 | 4 | yes | none retained standalone | 16 | — |
| glm53flash-a5-tp8-c3 | 53 | 1 | yes | none retained standalone | 0 | — |
| glm53flash-a5-tp8-c96 | 27 | 1 | yes | none retained standalone | 0 | — |
| glm53flash-a5-tp8-c1 | 65 | 1 | yes | none retained standalone | 0 | — |
| a3_glm53_dc4k_b1 | 74 | 1 | no | none retained standalone | 0 | — |
| a3_glm53_dc4k_b2 | 70 | 1 | no | none retained standalone | 0 | — |
| a3_glm53_dc4k_b4 | 67 | 1 | no | none retained standalone | 0 | — |
| a3_glm53_dc4k_b8 | 61 | 1 | no | none retained standalone | 0 | — |
| a3_glm53_dc16k_b1 | 74 | 1 | no | none retained standalone | 0 | — |
| a3_glm53_w4a8_tp16_tpot30_c2 | 48 | 2 | yes | none retained standalone | 16 | — |
| a3_glm53_w4a8_tp16_tpot50_c2 | 53 | 2 | yes | none retained standalone | 16 | — |
| a3_glm53_w4a8_tp16_tpot88_c8 | 61 | 6 | yes | none retained standalone | 16 | — |
| a5_glm53flash_tp8_c16_p4k | 43 | 8 | yes | none retained standalone | 0 | — |
| a5_glm53flash_tp8_c16_p8k | 42 | 8 | yes | none retained standalone | 0 | — |
| a5_glm53flash_tp8_c32_p4k | 37 | 5 | yes | none retained standalone | 0 | — |
| a5_glm53flash_tp8_c32_p8k | 36 | 2 | yes | none retained standalone | 0 | — |
| a5_glm53flash_tp8_c4_p8k | 23 | 3 | yes | none retained standalone | 0 | — |
| a5_glm53flash_tp8_c64_p4k | 31 | 1 | yes | none retained standalone | 0 | — |
| a5_glm53flash_tp8_c8_p4k | 38 | 5 | yes | none retained standalone | 0 | — |
| a3_glm53flash_tp16_aclgraph_c16 | 65 | 7 | yes | none retained standalone | 16 | — |
| a3_glm53flash_tp16_aclgraph_c32 | 65 | 8 | yes | none retained standalone | 16 | — |
| a3_glm53flash_tp16_aclgraph_c64 | 69 | 10 | yes | none retained standalone | 16 | — |
| a3_glm53flash_tp16_aclgraph_c8 | 62 | 5 | yes | none retained standalone | 16 | — |
| a5_kimi_tp8_e16_bf16_c16_p16k | 47 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c16_p4k | 49 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c1_p16k | 59 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c1_p4k | 59 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c2_p16k | 54 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c2_p4k | 55 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c32_p16k | 41 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c32_p4k | 46 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c4_p16k | 52 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c4_p4k | 53 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c8_p16k | 51 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_tp8_e16_bf16_c8_p4k | 52 | 1 | yes | none retained standalone | 0 | — |
| qwen35-35b-a5-tp4-c64-graph | 96 | 16 | yes | none retained standalone | 0 | — |
| qwen35-35b-a5-tp4-c128-graph | 99 | 21 | yes | none retained standalone | 0 | — |
| qwen35-35b-a5-tp4-c4-graph | 91 | 3 | yes | none retained standalone | 0 | — |
| qwen36-a5-tp2-c12 | 55 | 1 | yes | none retained standalone | 0 | — |
| qwen36-a5-tp2-c96 | 24 | 1 | yes | none retained standalone | 0 | — |
| qwen36-a5-tp2-c1 | 85 | 1 | yes | none retained standalone | 0 | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 152 | 1 | yes | none retained standalone | 0 | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 145 | 1 | yes | none retained standalone | 0 | — |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 75 | 1 | yes | none retained standalone | 0 | — |
| a5_v41_fp8_tp1_dp8_ep8_c16_p2k | 129 | 1 | yes | none retained standalone | 0 | — |
| a5_v41_fp8_tp1_dp8_ep8_c32_p2k | 105 | 1 | yes | none retained standalone | 0 | — |
| a5_v41_fp8_tp1_dp8_ep8_c4_p2k | 151 | 1 | yes | none retained standalone | 0 | — |
| a5_v41_fp8_tp1_dp8_ep8_c128_p2k | 73 | 1 | yes | none retained standalone | 0 | — |
| a5_kimi_k3_p32768_c1 | 63 | 1 | no | none retained standalone | 0 | same-source archive: Python trace + communication totals; no NPU linkage |
| v4flash-a3-tp8-c4 | 108 | 2 | yes | none retained standalone | 8 | — |
| v4flash-a3-tp8-c8 | 111 | 4 | yes | none retained standalone | 8 | — |
| qwen35-397b-a3-tp16-c48 | 23 | 1 | yes | none retained standalone | 0 | — |
| qwen35-397b-a3-tp16-c136 | 18 | 1 | yes | none retained standalone | 0 | — |
| a3_kimi4_tp8_w4a8_c1 | 254 | 1 | yes | none retained standalone | 8 | — |
| a3_kimi4_tp8_w4a8_c16 | 238 | 2 | yes | none retained standalone | 8 | — |
| a3_kimi4_tp8_w4a8_c32 | 229 | 6 | yes | none retained standalone | 8 | — |
| a3_kimi4_tp8_w4a8_c4 | 253 | 3 | yes | none retained standalone | 8 | — |
| a3_kimi4_tp8_w4a8_c64 | 207 | 7 | yes | none retained standalone | 8 | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c16 | 76 | 5 | yes | none retained standalone | 16 | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c32 | 77 | 7 | yes | none retained standalone | 16 | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4 | 78 | 2 | yes | none retained standalone | 16 | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c64 | 76 | 11 | yes | none retained standalone | 16 | — |
| a3_v41_w8a8_tp4_dp4_ep16_dspark7_c8 | 77 | 4 | yes | none retained standalone | 16 | — |

## Reproduce

Run the collector once per case with `--inputs inputs.json --case-id CASE --output-dir OUTPUT`; its model topology is already in the input manifest, so no physical-resource export or cost is performed. `review_capture_hccl.py OUTPUT` recomputes every saved numeric statistic and population without rescanning CSV. The independent source-template audit is maintained in `../acceptance-20261030-hccl-source/` and is a separate conditional interpretation.

Algorithm names, transport templates, wire bytes and peer waiting causes remain unconfirmed unless a capture field or verified relation establishes them. A preceding tensor-size candidate and a declared Sim recipe remain separate evidence; neither proves observed HCCL payload or a ring/mesh choice.

## DPU inventory scope

The historical 66-source filter did not explicitly select DPU-specific names or DPU-only cores outside `hcom_*`/`COMMUNICATION`; these results therefore do **not** prove DPU task absence. A separate metadata-only presence check (`dpu-presence-metadata.json`) inspected 374 retained operator/communication statistic files, 32,126 rows across 60 sources, plus the already preserved Kimi archive communication statistics, and found no DPU-named rows. The other sources lack these particular local summary files. This summary evidence does not close the event-filter coverage gap. Future collector code now includes DPU names and DPU cores; the saved 66-source event populations and their historical collector hashes remain unchanged. No primary CSV was rescanned for this check.
