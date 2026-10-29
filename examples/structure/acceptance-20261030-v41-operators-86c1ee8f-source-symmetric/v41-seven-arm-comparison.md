# V4.1 A5 seven-source operator comparison

Runtime `86c1ee8f`; zero raw rereads. Baseline and source-symmetric are separate conditions on the same observations.

| Arm | Complete forwards | Strict passed / compared | Strict calls | Conditional references | Excluded references |
|---|---:|---:|---:|---:|---:|
| Baseline | 830 | 126 / 126 | 487210 | 49 | 14 |
| Source-symmetric conditional | 830 | 112 / 112 | 420810 | 14 | 49 |

All strict compared cohorts in both arms are in the <=50us / absolute-error <=15us tier. No >50us strict cohort is scored in this population.

GroupedMatmul uses complete retained native ABI partitions and independently rebuilt FFN declarations for all 40 aligned layers. These rows do not enter strict accuracy.

| Capture | Role | Calls | Capacity / declared valid rows | Observed mean / P50 us | Baseline us | Source us | Baseline residual ms/F | Source residual ms/F |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| c4_p2k | expert_up | 6040 | 48 / 6 | 38.809 / 38.660 | 22.384 | 55.882 | -0.657 | +0.683 |
| c4_p2k | expert_down | 6040 | 48 / 6 | 23.604 / 23.476 | 11.813 | 26.130 | -0.472 | +0.101 |
| tpot10ms_c8 | expert_up | 5800 | 48 / 6 | 38.541 / 38.378 | 22.384 | 55.882 | -0.646 | +0.694 |
| tpot10ms_c8 | expert_down | 5800 | 48 / 6 | 23.656 / 23.572 | 11.813 | 26.130 | -0.474 | +0.099 |
| tpot5ms_c1 | expert_up | 6080 | 48 / 6 | 38.592 / 38.458 | 22.384 | 55.882 | -0.648 | +0.692 |
| tpot5ms_c1 | expert_down | 6080 | 48 / 6 | 23.639 / 23.543 | 11.813 | 26.130 | -0.473 | +0.100 |
| c16_p2k | expert_up | 5160 | 96 / 12 | 68.076 / 67.778 | 44.746 | 111.759 | -0.933 | +1.747 |
| c16_p2k | expert_down | 5160 | 96 / 12 | 37.439 / 37.167 | 22.163 | 52.256 | -0.611 | +0.593 |
| c32_p2k | expert_up | 4200 | 192 / 24 | 127.406 / 126.789 | 86.330 | 223.514 | -1.643 | +3.844 |
| c32_p2k | expert_down | 4200 | 192 / 24 | 65.238 / 64.668 | 44.275 | 104.508 | -0.838 | +1.571 |
| tpot30ms_c64 | expert_up | 3000 | 384 / 48 | 242.599 / 241.331 | 172.568 | 447.025 | -2.801 | +8.177 |
| tpot30ms_c64 | expert_down | 3000 | 384 / 48 | 119.854 / 118.821 | 88.541 | 209.013 | -1.253 | +3.566 |
| c128_p2k | expert_up | 2920 | 768 / 96 | 250.141 / 248.818 | 174.004 | 447.785 | -3.045 | +7.906 |
| c128_p2k | expert_down | 2920 | 768 / 96 | 123.273 / 122.228 | 89.337 | 210.048 | -1.357 | +3.471 |

Valid route rows and expert histogram remain unknown. Per-forward residual is predicted service minus measured kernel activity; communication/overlap prevents interpreting its sum as a body wall-time explanation.

Source HC changes two existing aggregate resource boundaries, so those old strict partitions remain excluded. N/A MQSMLA and changed HC/Dispatch/Combine references need a separate explicit source-correspondence rebind; they are not silently assigned zero cost.

Independent join: 98 checks; all seven observed identities, geometry and GMM histogram statistics match between arms.
