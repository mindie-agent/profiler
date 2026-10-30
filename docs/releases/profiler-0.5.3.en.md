# mindie-profiler 0.5.3

Paired with `mindie-sim 0.8.1`, this release delivers full A3/A5 Decode (280 cases) and Prefill (15 cases) long/short-context convergence, the full-fleet DSH held-out generalization evaluator (561 unregistered captures), and the whole-network 4D MFU/MBU/CV efficiency, 0.80x MBU target fitting, and 30ms SLA hardware scaling report generator.

- **Registered Decode & Prefill Convergence**:
  - `examples/structure/results/decode.md`: 280/280 (100.0%) pass <= 15%, 253/280 (90.4%) <= 10%, mean |error| = 4.40% (median 3.36%), with 100% of the 187 new 64K/96K/128K long-context cases within 10%.
  - `examples/structure/results/prefill.md`: 15/15 (100.0%) comparable Prefill Body cases pass <= 8.42% (mean |error| = 4.01%).
- **Full-Fleet DSH Parsing & Zero-Shot Generalization (`examples/structure/dsh_generalization_eval.py`)**:
  - Recognizes pre-AllGather terminal norm mHC stream collapse in `mindie_profiler/decode_segmentation.py`.
  - Across all 856 evaluated Body captures, **841/856 (98.25%) pass <= 15%** and **736/856 (85.98%) <= 10%** (mean |error| = 5.44%, median = 4.60%); across the 561 unregistered held-out captures, **546/561 (97.33%) pass <= 15%** (mean |error| = 5.99%, median = 5.10%).
- **Whole-Network 4D Efficiency, 0.80x MBU Target Fitting & 30ms SLA Hardware Scaling Report (`examples/structure/efficiency_report.py`)**:
  - Reports operator-family and network-level `Cube_MFU`, `Vec_MFU`, `MBU`, `Link_Util`, and `CV_Overlap`, counterfactual 0.80x MBU target fitting, and `1x` vs `2x HBM` vs `2x Compute` SLA-constrained maximum throughput.
