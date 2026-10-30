# Residual mechanism ledger

[Full ledger](residual-mechanism-ledger.json) and [per-case tables](residual-mechanism-ledger.md) pin the scoreboard at Git `9f105588a72d8cba10e74f19c828e142fe968eca` (SHA256 `bdc93c3577aeaf12f03b4a921c3e17b8be01c5d83d9f68921c6c9080e18caa72`). The >50 MiB scoreboard is streamed directly from Git. Existing linked receipts and complete actual/native histograms provide the measurements and costs; this task performs **zero raw scans and zero predictions**.

The population is **38 captures / 2,796 selected complete Body forwards**: A5 Kimi BF16 12, A5 V4.1 seven, nine failed A5 GLM Flash cases, three Qwen3.5 TP4 cases, three Qwen3.6 TP2 cases, and four A3 cases. These are source/geometry populations, not additional captures per recipe or reference arm.

## What the fixed baseline shows

| Population | Mechanism | Observed activity ms/F | Current covered source service ms/F | Coverage and interpretation |
|---|---|---:|---:|---|
| Kimi A5, 12 sources | MC2 dispatch + combine | 4.220–6.086 | 0.582–0.670 | All 113,712 native calls have conditional references. The large service/elapsed gap remains visible; peer synchronization or transport causality is not established. |
| Kimi A5, 12 sources | Grouped matmul | 3.493–6.279 | 3.848–4.045 | Complete conditional coverage. Signed differences change with geometry; small execution B does not prove valid expert group-list rows. |
| Kimi A5, 12 sources | HCCL | 4.213–5.113 | unavailable | 230,514 measured calls remain without an exact current source/geometry cost. No zero prediction or borrowed reference from another model. |
| V4.1 A5, seven sources | MC2 dispatch + combine | 1.188–2.361 | 0.277–0.462 | All 66,400 calls have conditional references. |
| V4.1 A5, seven sources | Grouped matmul | 2.488–14.937 | 1.616–12.961 | All 66,400 calls have conditional references; growth with execution geometry remains explicit. |
| GLM Flash A5, nine failed sources | Grouped / fused activation matmul | 2.352–13.728 | 1.247–11.747 | Complete 26,712-call coverage combines disjoint strict and conditional native types; it is not a whole-Body pass. |
| GLM Flash A5 | Copy + routing | 1.124–2.689 across nine sources | 0.144–0.227 for three sources only | Current exact costs exist for c16/c32/c64 p4k. The other six sources' 24,860 calls remain uncovered; the three-source cost range must not be compared to the full nine-source observed range. |
| GLM Flash A5, nine sources | HCCL | 1.974–3.839 | unavailable | 28,620 calls remain measured without matched service costs. |
| Qwen3.5 A5, three sources | MC2 / grouped+DequantSwigluQuant / HCCL | 1.157–3.372 / 2.530–6.470 / 2.536–4.987 | unavailable in this fixed baseline | 19,120 / 28,680 / 28,680 calls are retained. Later bf71 recipe results belong in a separate incremental arm. |

These ranges describe different case populations; they are not differences between unrelated extrema. The full per-case tables expose **all observed**, **covered observed**, and **covered predicted** milliseconds separately, with strict/reference/uncovered calls both in total and per Forward.

For Qwen3.6 TP2 c96, the Body prediction is 53.947109 ms against 63.853365 ms, a −15.5141% error. The **0.328251 ms** distance to the 15% threshold is a statistical acceptance distance. Its HCCL reference covers 128 calls/F and compares **10.200487 ms/F service** against **16.614379 ms/F activity**, a **−6.413892 ms/F** residual. These quantities have different boundaries; neither should be added to or subtracted from Body as a corrective budget.

The A3 selection explicitly includes the historical focus cases **V4Flash c4** and **Kimi4 c32**. The remaining two are the failed A3 cases nearest the ±15% relative band: **GLM W4A8 c8** and **Kimi4 c1**. The complete relative ranking and absolute millisecond distances are stored in JSON. A small four-layer absolute gap does not imply good relative accuracy.

V4Flash c4 and GLM W4A8 c8 do not have complete canonical operator tables in this fixed scoreboard. Their existing 66-source HCCL ledgers provide measured MC2/HCCL populations: respectively **2.661 / 3.138 ms/F** and **5.389 / 9.497 ms/F**. The controller-generation map proves the retained operator populations remain reusable. Missing copy/matrix populations stay `null`, not absent or zero.

## Accounting boundaries

- Complete canonical actual histograms own native-family denominators and real Mean/P50. Individual strict and reference components retain their runtime, source, receipt, physical program and population evidence.
- Strict calls take precedence. A partial strict/reference overlap without retained event-level cohort histograms is shown separately and is never added to covered calls or cost.
- Multiple references require nonoverlapping aligned layer sets or distinct members of the **same retained population partition**. Histogram remaining capacity alone does not prove disjoint occurrences. Exact duplicate role/layer histograms cannot increase coverage.
- Conditional references never enter strict accuracy statistics. Missing prediction is `null`; partial cost coverage never produces a full-family cost.
- Typed AI_CPU controller overlays are excluded from HCCL physical-service rows. HCOM elapsed can include protocol and peer waits; it is not measured link service. Fused MC2 programs remain atomic and are not decomposed into invented per-kernel timings.
- **All residuals are nonadditive activity differences. Neither the four clusters nor their source-program service differences constitute a causal Body wall-clock budget.**

Seven regression tests cover duplicate references, partial strict overlap, cross-receipt occurrence ambiguity, complete multi-component fallback, the fixed A3 selection, and actual-file MC2/grouped-matmul provenance. The producer validates **238 full family histograms** and peaks at **266.23 MiB**. Kimi and V4.1 source-role observation IDs resolve to the saved actual's `source_role_references`, with native type, complete layer set and histogram equality checked; integer native partition indices retain their original partition identity. Correcting this namespace changed no measurement, cost or coverage value. Every intermediate local metadata generation and current source identity remains independent of the fixed baseline narrative.

[Independent review](residual-mechanism-independent-review.json) passed **222,264 checks with zero failures**, including all 238 family histograms, 130 conditional-reference groups, 12 strict components, population-partition navigation and mutual exclusion, covered-cost arithmetic and recorded runtime identities. Its peak was **402.58 MiB**, with no raw scans or predictions. Both provenance corrections are retained in the review history.

Reproduce:

```sh
python examples/structure/residual_mechanism_ledger.py \
  --commit 9f105588a72d8cba10e74f19c828e142fe968eca \
  --output-dir examples/structure/acceptance-20261030-residual-mechanisms
```
