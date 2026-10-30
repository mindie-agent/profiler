# Complete same-contract population pooling

Several individually retained quantization/normalization cohorts have the same physical selector. Assigning one subpopulation's mean to that whole selector would be incorrect. This increment first proves that their target populations are disjoint, their active contracts are equal, and their complete integer histograms together cover every selected invocation. It then pools the whole population and assigns one mean once per call. No partial histogram is extrapolated.

| Source | Added complete populations per Forward | Sim Body ms | Error |
|---|---|---:|---:|
| Kimi four-layer c32 | DynamicQuant 8 | 6.096790 | −9.1899% |
| Kimi four-layer c64 | DynamicQuant 8 | 8.699366 | −9.5268% |
| GLM Flash c2 | RmsNorm 90, DynamicQuant 45 | 31.017872 | −9.0877% |

All three meet the 10% refinement goal and the unchanged 15% acceptance criterion. Every preceding rule is unchanged. Four new rules record actual Engine hits 8/8/90/45, exactly matching the complete populations. Three fresh workers use `21c30821d87a757bace8cf6b2fffea2536db643e`, with 462 primary Forwards compared and 494 full-source Forwards retained across 15 geometry groups. No raw capture or device is read. Standard Body review: 300 checks; independent parameter review: 110 checks, both without failures.

`build_a3_pooled_contract_services.py` reproduces the independent inputs. `pooled-contract-populations.json` preserves the disjoint target sets, constituent cohort counts, exact contracts, full pooled histograms and source identities. Calibration remains in-sample observed service, and no Body residual or target threshold determines a response value. Physical-role timings inside a pool are not independently identified.
