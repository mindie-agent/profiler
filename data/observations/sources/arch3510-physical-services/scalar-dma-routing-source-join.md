# Routing source-operation / PMU join

This increment reuses the existing six-source scalar/DMA ledger; only its three same-domain GLM MoeInitRoutingV3 populations need the new source-operation export. Copy fits and DSQ observations remain unchanged. No raw scan, prediction, or rate change occurs.

| Source | Calls/F | Assignments / active owners | Native Mean/P50 us | Vector / Scalar / MTE2 / MTE3 busy us |
|---|---:|---:|---:|---:|
| glm53flash-a5-tp8-c1 | 42 | 32 / 32 | 20.796/20.692 | 1.500/3.897/1.040/1.013 |
| a5_glm53flash_tp8_c4_p8k | 42 | 128 / 64 | 21.821/21.538 | 3.069/4.423/1.083/0.892 |
| a5_glm53flash_tp8_c8_p4k | 42 | 256 / 64 | 21.641/21.509 | 3.412/4.522/1.092/0.643 |

The 13 source-count features have exact rank 3 on three independent capture domains. Sort/Concat/Extract blocks co-vary with assignments; owner-zero E288 loops are constant; atomic payload co-varies with active owners. A saturated three-point fit would have zero validation degrees of freedom. Repeated calls improve each measured mean but add no independent physical design point.

VBitSort32 and VMrgSort4V2 are registered resource names; the actual source export deliberately retains one whole Sort macro and leaves SDK/compiled opcode expansion unknown. Logical SIMT INT32 accesses are not warp instructions or DCache misses. SetAtomicAdd plus a DataCopyPad payload is not a measured number of RMW transactions. Do not divide aggregate PMU fields by all-owner counts.

The usable result is the complete per-domain native response plus source-count joint constraints. Separate rates need orthogonal E/assignment/owner/bytes contrasts and compiled/owner-specific observations. Signed differences between overlapping pipes remain diagnostics, not automatically synchronization or unmodeled latency.
