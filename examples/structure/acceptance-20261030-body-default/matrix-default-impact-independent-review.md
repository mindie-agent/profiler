# Body matrix default: independent impact review

This changes the physical cost recipe, not only host CPU performance. Input bytes and captured populations are unchanged.

| Source group | Affected sources | Unique inputs |
|---|---:|---:|
| qwen | 8 | 8 |
| glm | 12 | 8 |
| v4 | 2 | 2 |

Affected source list:

- `qwen35-35b-a5-tp4-c64-graph` — `fcd7c235d50c`
- `qwen35-35b-a5-tp4-c128-graph` — `5458702a9701`
- `qwen35-35b-a5-tp4-c4-graph` — `0e0a5575f51d`
- `qwen36-a5-tp2-c12` — `bb70ee96cbef`
- `qwen36-a5-tp2-c96` — `06d1ae9e123d`
- `qwen36-a5-tp2-c1` — `0ca0c5e95381`
- `qwen35-397b-a3-tp16-c48` — `c2316dff86e2`
- `qwen35-397b-a3-tp16-c136` — `43df26924059`
- `a3_glm53_dc4k_b2` — `4671d3c85fc1`
- `a3_glm53_dc4k_b4` — `4671d3c85fc1`
- `a3_glm53_dc16k_b1` — `4671d3c85fc1`
- `a3_glm53_dc4k_b1` — `4671d3c85fc1`
- `a3_glm53_dc4k_b8` — `4671d3c85fc1`
- `glm53flash-a3-tp16-c16-livepre` — `c9b8825860b9`
- `glm53flash-a5-tp8-c1` — `b2cd9f2efa1e`
- `glm53flash-a5-tp8-c3` — `619bd71493a5`
- `glm53flash-a3-tp16-c4-livepre` — `2ea5a162e821`
- `glm53flash-a3-tp16-c2` — `6e7eeb903615`
- `glm53flash-a3-tp16-c4` — `aef0573da26c`
- `glm53flash-a5-tp8-c96` — `2f49a5ebab8b`
- `v4flash-a3-tp8-c4` — `a20b7c039fda`
- `v4flash-a3-tp8-c8` — `ab010289f828`

Current operator receipts requiring fresh structure and cost:

| Source | Native family | Role | Prior program | Cohorts | Calls |
|---|---|---|---|---:|---:|
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | index_k | TiledMatmul(128,128) | 1 | 814 |
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | index_q | TiledMatmul(128,128) | 1 | 407 |
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | linear_decay_b|linear_gate_b | TiledMatmul(128,128) | 1 | 2516 |
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | linear_output | TiledMatmul(128,128) | 1 | 1258 |
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | linear_qkvbfg_a | TiledMatmul(128,128) | 1 | 1258 |
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | output | TiledMatmul(128,128) | 1 | 407 |
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | q_b | TiledMatmul(128,128) | 1 | 407 |
| glm53flash-a3-tp16-c16-livepre | MatMulV2 | qkv_a | TiledMatmul(128,128) | 1 | 407 |
| glm53flash-a3-tp16-c16-livepre | QuantBatchMatmulV3 | down | TiledMatmul(128,128) | 1 | 111 |
| glm53flash-a3-tp16-c16-livepre | QuantBatchMatmulV3 | gate_up | TiledMatmul(128,128) | 1 | 111 |
| glm53flash-a3-tp16-c16-livepre | QuantBatchMatmulV3 | shared.down | TiledMatmul(128,128) | 1 | 1554 |
| glm53flash-a5-tp8-c3 | GroupedMatmul | expert_down | MappedMatmul via balanced_grouped_down | 1 | 2226 |
| glm53flash-a5-tp8-c3 | MatMulV3 | index_q | TiledMatmul(128,128) | 1 | 583 |
| glm53flash-a5-tp8-c3 | MatMulV3 | linear_output | TiledMatmul(128,128) | 1 | 1802 |
| glm53flash-a5-tp8-c3 | MatMulV3 | linear_qkvbfg_a | TiledMatmul(128,128) | 1 | 1802 |
| glm53flash-a5-tp8-c3 | MatMulV3 | router | TiledMatmul(128,128) | 1 | 2226 |
| glm53flash-a5-tp8-c3 | QuantBatchMatmulV3 | down | TiledMatmul(128,128) | 1 | 159 |
| glm53flash-a5-tp8-c3 | QuantBatchMatmulV3 | gate_up | TiledMatmul(128,128) | 1 | 159 |
| glm53flash-a5-tp8-c3 | QuantBatchMatmulV3 | shared.down | TiledMatmul(128,128) | 1 | 2226 |
| glm53flash-a5-tp8-c3 | QuantBatchMatmulV3 | shared.gate_up | TiledMatmul(128,128) | 1 | 2226 |
| glm53flash-a5-tp8-c1 | GroupedMatmul | expert_down | MappedMatmul via balanced_grouped_down | 1 | 2730 |
| glm53flash-a5-tp8-c1 | MatMulV3 | index_q | TiledMatmul(128,128) | 1 | 715 |
| glm53flash-a5-tp8-c1 | MatMulV3 | linear_output | TiledMatmul(128,128) | 1 | 2210 |
| glm53flash-a5-tp8-c1 | MatMulV3 | linear_qkvbfg_a | TiledMatmul(128,128) | 1 | 2210 |
| glm53flash-a5-tp8-c1 | MatMulV3 | router | TiledMatmul(128,128) | 1 | 2730 |
| glm53flash-a5-tp8-c1 | QuantBatchMatmulV3 | down | TiledMatmul(128,128) | 1 | 195 |
| glm53flash-a5-tp8-c1 | QuantBatchMatmulV3 | gate_up | TiledMatmul(128,128) | 1 | 195 |
| glm53flash-a5-tp8-c1 | QuantBatchMatmulV3 | shared.down | TiledMatmul(128,128) | 1 | 2730 |
| glm53flash-a5-tp8-c1 | QuantBatchMatmulV3 | shared.gate_up | TiledMatmul(128,128) | 1 | 2730 |

Refresh `glm-low-concurrency-86c1ee8f` (A5 c1/c3) and `glm-a3-livepre-86c1ee8f` (A3 c16). The other 19 affected body sources have no current main-table operator receipt to refresh. Keep historical receipts intact. Reprice the full retained cases so any matrix-dependent source calls are rechecked; do not carry incompatible cohorts into the new denominator.

612 read-only checks passed; no raw reads, no cost calls, no fixed checkout reads. 12 later-changed, explicitly configured Kimi inputs were verified against their exact 0e2d Git bytes; all 22 affected source inputs still match current main bytes.
