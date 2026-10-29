# Kimi TP8 retained-capture geometry probe

Each row below describes only the first complete Decode candidate in the retained source. This is a bounded parser diagnostic, not full-capture acceptance or a body accuracy result. Existing Sim topology was reused only for its 93-layer attention sequence (69 KDA, 24 MLA); the old checkpoint precision, expert count and placement are not asserted for these new sources.

| Client case | Rows scanned | Head rows | KDA query rows | Paged MLA batch | First dense FFN execution rows | Current structural alignment |
|---|---:|---:|---|---:|---:|---|
| kimi_k3_tp8_high_conc_decode_c1_p4k_20261030 | 5181 | 1 | [1] | 1 | 8 | accepted |
| kimi_k3_tp8_high_conc_decode_c2_p4k_20261030 | 5626 | 2 | [2] | 2 | 8 | accepted |
| kimi_k3_tp8_high_conc_decode_c4_p4k_20261030 | 5626 | 4 | [4] | 4 | 8 | accepted |
| kimi_k3_tp8_high_conc_decode_c8_p4k_20261030 | 5433 | 8 | [8] | 8 | 8 | accepted |
| kimi_k3_tp8_high_conc_decode_c16_p4k_20261030 | 5433 | 16 | [16] | 16 | 16 | accepted |
| kimi_k3_tp8_high_conc_decode_c32_p4k_20261030 | 5435 | 32 | [32] | 32 | 32 | accepted |

The first candidates show no head-versus-body query-row conflict. Internal first-layer dense FFN rows are padded independently; they must not replace head/KDA/attention geometry for the entire Forward. The measured MLA uses 31-slot FusedInferAttentionScore with BF16 Q `[B,16,1,512]`, BF16 rotary Q `[B,16,1,64]`, and block table slot 14 `[B,516]`. Cache allocation dimensions do not establish active KV length.

For the c1 source, raw lines 47/62 are the first dense layer (gate-up N8448, down K4224), not the MoE shared expert. Raw lines 82/113 instead give MoE shared gate-up N1536 and down K768. Router line 78 outputs 16 logits; top-k line 81 outputs 8 choices. Expert GMM lines 84/111 have BF16 shapes `[16,3584] × [2,3584,6144]` and `[16,3072] × [2,3072,3584]`, alongside a separately observed hidden-to-latent projection. These are source-specific contracts requiring an independently declared new case.

Some exported views are opaque: for example c2 line 38 reports input `[6432]` and weight `[1536,128]` with output `[2,1536]`, and recurrent state outputs include large changing one-dimensional descriptors. The raw values remain unchanged; they are not silently converted into logical active tensor shapes.

The JSON records exact source hashes supplied by the independent retained-bundle inventory, core identity and raw row locators. Two bounded passes were used to improve per-kind tensor examples; no complete source scan or new device execution was performed.
