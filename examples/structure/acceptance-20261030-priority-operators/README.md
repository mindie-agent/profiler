# Priority body operator replay

This directory retains the d9118c6e Sim baseline for the Kimi 63 complete body forwards and the first GLM Flash geometry probes. Raw captures were streamed locally; no new hardware workload was launched.

`body-operator-family-scoreboard.json` currently covers Kimi's default declaration and the independent current-checkpoint conditional declaration. Both use the same 63 captured forwards. The checkpoint metadata is a conditional configuration reference; historical capture binary identity and simultaneous activity of all four DP replicas are not established.

The `-canonical` variant corrects semantic role normalization: `subgraph:s0.lN.shared.situ_quant` denotes one repeated role, rather than a different role in every layer. It combines exact saved integer duration histograms and validates the combined tensor contracts, physical work and DP placement with the shared cohort implementation. It performs no additional capture scan. The original artifacts are retained. Busy union cannot be recovered from duration histograms and is explicitly unknown in merged cohorts; activity sums, means and medians remain exact.

Kimi's conditional declaration required one additional source scan because the first default-declaration extraction did not retain every event's joint contract and layer-role distribution. Its 502.1 MiB peak remained below the 512 MiB analysis budget. The canonical correction reread metadata only.

GLM files are diagnostic baseline mappings, not completed accuracy acceptance. They preserve execution geometry separately (q6/B1…B16 on A3; q4/B1 or B4 on the selected A5 cases). The native evidence file retains three complete-layer excerpts from a bounded stream prefix. A grouped-matrix operand with 256 storage rows does not prove 256 valid routed rows: the group-list values and dispatch valid-token counts remain unobserved. Kernel-activity contributions must not be equated with body wall-clock gaps or additional missing Sim work.
