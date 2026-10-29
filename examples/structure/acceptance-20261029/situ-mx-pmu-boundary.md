# SituMxQuant: Task Duration and exported AIV metrics

Review date: 2026-10-30. This is a definition and source-identity review. It does
not change the main score, rescan the capture, or recompute simulation costs.
The JSON companion records every official source path, immutable revision,
SHA256, relevant lines and retained-capture locator.

**Keep Task Duration mean 65.134110 us as the primary comparison.** The exported
`aiv_time` mean 3.824011 us describes a different boundary. Its exact historical
exporter algorithm is **unknown**; the retained CSV does not identify that code
version.

| Retained population | Value |
|---|---:|
| Input / output | BF16 `[1,1536]` / FP8 `[1,768]`, E8M0 `[1,12,2]` |
| Events | 6898 |
| Block Num / Mix Block Num / Stream | 3 / 0 / 0 |
| Task Duration mean / p50 | 65.134110 / 64.697 us |
| Exported aiv_time mean / p50 | 3.824011 / 3.520 us |
| Exported vector / scalar mean | 0.650913 / 1.874164 us |
| Exported MTE2 / MTE3 mean | 1.046363 / 0.413234 us |
| Task Wait Time | 0 for all 6898 events |

The population statistics come from the already completed descriptor audit
`/tmp/situ-mx-native-boundary-20261029.json`, whose SHA is retained in the JSON
companion. This review read that small artifact and the two unedited retained CSV
rows; it did not repeat its full-capture scan.

## What the official source establishes

All source references below are from Huawei's `Ascend/msprof`, pinned to
`a11606183257bb954de14a6b5a64c44f4112ac9c`. This is the inspected source revision,
not a claim that the October 23 capture used that revision.

- The exported-field documentation, `docs/en/user_guide/profile_data_file_references.md:394`,
  defines Task Duration to include device-task scheduling, accelerator execution
  and completion response. Line 395 defines Task Wait Time as the interval from
  the previous task's end to this task's start. Thus zero Task Wait Time does
  not establish zero scheduling or response time inside Task Duration.
- The same generic documentation at lines 406-408 describes `aiv_time` as a
  theoretical simultaneous, equal-duration Block execution and `total_cycles`
  as a sum across Blocks. The older calculator path
  `analysis/mscalculate/stars/ffts_pmu_calculator.py:380` calls
  `analysis/common_func/utils.py:175`: converted cycle time is divided by the
  task's Block count, then multiplied by `ceil(blocks / available_cores)`.
  When Blocks fit in one wave, this is a Block average, not division by all
  available device cores.
- The inspected Ascend 950 path differs. `analysis/csrc/application/database/db_constant.h:392`
  identifies chip 15 as Ascend950; `analysis/msconfig/data_calculator_config.py:90`
  routes chips 15/16/19 to `Chip6PmuCalculator`. In
  `analysis/mscalculate/stars/chip6_pmu_calculator.py:460`, a non-MIX AIV task's
  time is converted from that PMU record's `end_time - start_time` syscnt
  interval and rounded to two decimals. This branch does not divide by Block
  count or total device cores. Its MIX branch at line 438 uses the same syscnt
  interval for the primary core, while the secondary AIV branch can still use
  the cycle/Block calculation.
- `analysis/common_func/msvp_common.py:314` renames internal `aiv_total_time`
  to exported `aiv_time`. A name alone therefore does not distinguish those
  generation-dependent calculation paths.
- `analysis/mscalculate/calculate_ai_core_data.py:60` derives each pipe time
  independently from its counter ratio and the selected total time. These
  fields are not an exclusive decomposition of Task Duration. The retained
  prefill row demonstrates the distinction: vector + scalar + MTE2 + MTE3 is
  60.054 us while `aiv_time` is 50.690 us. Neither sum should replace the task
  duration.

## What remains unknown for this capture

The reported 3.824011 us is the arithmetic mean of 6898 exported `aiv_time`
values. Whether each historical value used the generic Block-average path or
the inspected 950 syscnt path is not established by this review. `AI_VECTOR_CORE`
and `Mix Block Num=0` are compatible with the current non-MIX path but do not
prove the historical collector/exporter version or binary.

The preserved CSV does not expose the raw PMU start/end syscnt values,
per-Block intervals, frequency inputs, or exact collector/exporter build used
for that export. The precise relationship between its PMU interval endpoints
and device-task endpoints consequently remains unproven. The large observed
gap cannot be assigned quantitatively to scheduling, response, stalls,
instrumentation overhead or another cause from these fields alone.

Do not multiply `aiv_time` by 3 or 64, add the pipe times, subtract PMU time from
Task Duration to fit a launch floor, or replace the primary 65.134110 us with
3.824011 us. PMU remains separate diagnostic evidence. No phase, step, layer,
core-work equivalence or historical source identity is inferred from timing.
