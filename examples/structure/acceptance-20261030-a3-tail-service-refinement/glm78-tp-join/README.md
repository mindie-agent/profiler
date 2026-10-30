# Old GLM78 TP-only caller correction

The source-selected `tp_join_reduce` caller joins routed and shared token outputs before one TP reduction. Its conditions are TP8, EP=DP=CP=PCP=1, TP-sharded shared weights, and no nonlinear routed output transform. The source basis is vLLM Ascend `8fd0bc4885cb52e58791aaa8efacc571b9bd115d`, `fused_moe.py` lines 203–244/304–312/343–356 and `register_custom_ops.py` lines 123–156. Installed binary correspondence remains explicitly unproven.

The fresh declaration has 78 attention, three dense and 75 joined-MoE reductions, replacing 231 earlier reduction nodes with 156. This choice comes from source control flow; the observed event count only validates population completeness. Noncommunication FLOPs, vector work, HBM, MTE2 and MTE3 work remain exactly equal. Each source's complete 156-call-per-Forward native AllReduce population provides its own inclusive elapsed mean, preserving protocol/peer wait. No rank-2/rank-4 curve is transferred to TP8.

| Source | Native AR mean us | Sim Body ms | Error | Accuracy |
|---|---:|---:|---:|---|
| dc16k b1 | 23.492704 | 30.946071 | −20.8785% | FAIL |
| dc4k b1 | 25.139015 | 30.946071 | −20.5591% | FAIL |
| dc4k b2 | 25.435350 | 32.725844 | −20.1222% | FAIL |

These are completed executions with genuine accuracy failures, not execution failures. The source correction removes an erroneous cost contribution and exposes missing native services; the older PASS values are not selected instead. Three fresh workers use Sim `21c30821d87a757bace8cf6b2fffea2536db643e`, retaining all 218 Forwards in three geometry groups. No raw capture or device run was needed for this arm. The standard Body review passes 964 checks; the independent source/parameter review passes 142.

Reproduce with `build_glm78_tp_join_service_cases.py`, then the standard Decode replay using `decode-forward-tp-join-cases.json`. `tp-join-source-proof.json` records before/after physical work, reduction ownership, source conditions, complete observed histograms and actual per-domain response counts. Further native evidence is collected separately without changing this failed receipt.
