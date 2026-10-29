"""Stream retained decode-attention and hyper-connection PMU evidence.

[Role] Preserve exact tensor populations, launch block counts and exported PMU.
[Invariants] Query width is a descriptor filter, not proof of decode/step identity.
  Block counts do not identify KV splits; overlapping PMU times are not additive.
[Timeouts & Locks] One bounded scan per source, fixed-size metric histograms and
  at most 256 descriptor groups; no locks, device calls or simulation.
[Side-Effect Policy] Reads captures and writes only requested evidence JSON/MD.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from hashlib import file_digest, sha256
import json
import math
from pathlib import Path
import resource
import sys
import time

from mindie_profiler.events import QueryStats
from mindie_profiler.normalized import row_from_event
from mindie_profiler.sources_csv import CsvSource, probe_csv


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "examples/structure/acceptance-20261029"
REQUESTS = {
    "a3_qwen35": {"FusedInferAttentionScore": (1, 2)},
    "a3_qwen36": {"FusedInferAttentionScore": (1, 4)},
    "a3_v4pro": {"HcPre": None, "HcPost": None},
}
DESCRIPTOR_FIELDS = (
    "input_shapes", "input_dtypes", "input_formats",
    "output_shapes", "output_dtypes", "output_formats",
)


def digest(path):
    with Path(path).open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def read(path):
    path = Path(path)
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError(f"metadata_exceeds_32_mib:{path}")
    return json.loads(path.read_text())


@dataclass
class Distribution:
    count: int = 0
    mean: float = 0.0
    squared_deviations: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    zero_count: int = 0
    histogram: Counter = field(default_factory=Counter)

    def add(self, value):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("nonfinite_normalized_metric")
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.squared_deviations += delta * (value - self.mean)
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)
        self.zero_count += int(value == 0)
        # Eight bins per power of two retain ~9% resolution without storing
        # one value per event. Extreme/negative values stay visible.
        bucket = ("negative" if value < 0 else "zero" if value == 0 else
                  max(-512, min(1024, math.floor(math.log2(value) * 8))))
        self.histogram[bucket] += 1

    def result(self, population):
        buckets = []
        def order(item):
            bucket = item[0]
            return (0 if bucket == "negative" else 1 if bucket == "zero" else 2,
                    bucket if isinstance(bucket, int) else 0)

        for bucket, count in sorted(self.histogram.items(), key=order):
            if isinstance(bucket, str):
                buckets.append({"kind": bucket, "count": count})
            else:
                buckets.append({
                    "lower_inclusive": 0 if bucket == -512 else 2 ** (bucket / 8),
                    "upper_exclusive": None if bucket == 1024 else 2 ** ((bucket + 1) / 8),
                    "count": count,
                })
        return {
            "present_count": self.count, "missing_count": population - self.count,
            "zero_count": self.zero_count, "min": self.minimum, "max": self.maximum,
            "mean": self.mean if self.count else None,
            "population_stddev": (
                math.sqrt(max(0.0, self.squared_deviations / self.count)) if self.count else None),
            "histogram": buckets,
        }


def descriptor(row):
    return {
        "native_operator_type": row.kind, "core": row.core, "op_state": row.state,
        **{name: getattr(row, name) for name in DESCRIPTOR_FIELDS},
    }


def _selected(row, requested):
    if row.kind not in requested:
        return False
    widths = requested[row.kind]
    if widths is None:
        return True
    # The retained FIA query is TND. Do not flatten another ABI into a query
    # width merely because its element count could fit a requested case.
    return bool(row.input_shapes and len(row.input_shapes[0]) == 3
                and row.input_shapes[0][0] in widths)


def analyze_capture(path, requested, *, expected_source=None, expected_positive_events=None,
                    max_rows=1_000_000, timeout_s=90):
    path = Path(path)
    started = time.perf_counter()
    stat = path.stat()
    actual_sha = digest(path)
    if expected_source is not None:
        if (actual_sha != expected_source["sha256"]
                or stat.st_size != expected_source["size_bytes"]):
            raise ValueError(f"capture_identity_mismatch:{path}")
    schema = probe_csv(path)
    stats = QueryStats("rank_0", "complete_capture_pmu_population", budget=max_rows)
    source = CsvSource(schema, rank_id="rank_0", rank_index=0)
    groups, operator_counts = {}, Counter()
    positive_events = 0
    for event in source.iter_events(
            max_rows=max_rows, timeout_s=timeout_s, stats=stats, strict=True):
        positive_events += 1
        operator_counts[event.op_type] += 1
        if event.op_type not in requested:
            continue
        row = row_from_event(event)
        if not _selected(row, requested):
            continue
        shape = descriptor(row)
        key = json.dumps(shape, sort_keys=True, separators=(",", ":"))
        if key not in groups:
            if len(groups) >= 256:
                raise ValueError("selected_descriptor_budget_256_exceeded")
            groups[key] = {
                "descriptor": shape, "event_count": 0, "duration": Distribution(),
                "pmu": {name: Distribution() for name in schema.pmu_columns},
                "pmu_status": Counter(), "blocks": {}, "source_rows": [],
                "first_source_row": row.line, "last_source_row": row.line,
                "streams": Counter(),
            }
        group = groups[key]
        group["event_count"] += 1
        group["duration"].add(row.duration_ns)
        group["pmu_status"][event.pmu_status] += 1
        group["last_source_row"] = row.line
        group["streams"][row.stream] += 1
        if len(group["source_rows"]) < 8:
            group["source_rows"].append(row.line)
        block = group["blocks"].setdefault(
            (row.blocks, event.mix_block_dim), Distribution())
        block.add(row.duration_ns)
        for name, value in event.pmu:
            group["pmu"][name].add(value)
    after = path.stat()
    if (stat.st_size, stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"capture_changed_during_scan:{path}")
    if expected_positive_events is not None and positive_events != expected_positive_events:
        raise ValueError(f"capture_positive_event_denominator_changed:{path}")
    results = []
    for key, group in sorted(groups.items()):
        count = group["event_count"]
        tensors = {name: value for name, value in group["descriptor"].items()
                   if name not in {"core", "op_state"}}
        tensor_key = json.dumps(tensors, sort_keys=True, separators=(",", ":"))
        results.append({
            "descriptor_id": "sha256:" + sha256(key.encode()).hexdigest(),
            "tensor_descriptor_id": "sha256:" + sha256(tensor_key.encode()).hexdigest(),
            "descriptor": group["descriptor"], "event_count": count,
            "source_rows": {
                "first": group["first_source_row"], "last": group["last_source_row"],
                "sample": group["source_rows"], "sample_limit": 8,
            },
            "stream_counts": dict(group["streams"]),
            "duration": {"unit": "ns", **group["duration"].result(count)},
            "block_configurations": [{
                "block_num": block[0], "mix_block_num": block[1],
                "event_count": values.count,
                "duration": {"unit": "ns", **values.result(values.count)},
            } for block, values in sorted(group["blocks"].items(), key=lambda item: str(item[0]))],
            "pmu_status_counts": dict(group["pmu_status"]),
            "pmu": {name: {
                "normalized_unit": schema.pmu_units[name],
                "source_column": schema.header[schema.pmu_columns[name]],
                "source_to_normalized_scale": schema.pmu_scales[name],
                **values.result(count),
            } for name, values in group["pmu"].items()},
        })
    populations = []
    for kind, widths in requested.items():
        for width in widths if widths is not None else (None,):
            selected = [group for group in results
                        if group["descriptor"]["native_operator_type"] == kind
                        and (width is None
                             or group["descriptor"]["input_shapes"][0][0] == width)]
            populations.append({
                "native_operator_type": kind, "query_rows": width,
                "event_count": sum(group["event_count"] for group in selected),
                "tensor_descriptor_count": len({group["tensor_descriptor_id"] for group in selected}),
                "execution_group_count": len(selected),
                "descriptor_ids": [group["descriptor_id"] for group in selected],
            })
    return {
        "source_identity": {"path": str(path.resolve()), "sha256": actual_sha,
                            "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns},
        "schema": {"header_sha256": schema.header_sha256, "columns": list(schema.header),
                   "block_column": schema.block_column, "mix_block_column": schema.mix_block_column,
                   "pmu_missing_columns": list(schema.pmu_missing)},
        "source_row_count": stats.rows_read, "positive_event_count": positive_events,
        "invalid_timing_rows": stats.bad_rows,
        "operator_counts": dict(sorted(operator_counts.items())),
        "requested_populations": populations, "groups": results,
        "elapsed_seconds": time.perf_counter() - started,
    }


def markdown(report):
    lines = [
        "# Retained Decode FIA and Hc PMU Evidence", "",
        "Full original CSV scans, using the shared profiler decoder. Query widths select "
        "descriptors; they do not prove phase, context, step, layer or native dispatch.", "",
        "Block Num and Mix Block Num remain observed launch fields. They are not a "
        "measurement of `kv_splits`. PMU time fields are converted from us to ns once; "
        "cycles, ratios and percent retain their exported units. PMU intervals may overlap "
        "and must not be added as elapsed kernel time.", "",
        "| Capture / type / query rows | Events | Tensor descriptors / state groups |",
        "| --- | ---: | ---: |",
    ]
    for capture in report["captures"]:
        for population in capture["requested_populations"]:
            lines.append(f"| {capture['capture_key']} / {population['native_operator_type']} / "
                         f"{population['query_rows']} | {population['event_count']} | "
                         f"{population['tensor_descriptor_count']} / "
                         f"{population['execution_group_count']} |")
    lines += ["", "| Capture / descriptor / state | Events | Block/Mix counts | Duration mean / min / max (us) |",
              "| --- | ---: | --- | --- |"]
    for capture in report["captures"]:
        for group in capture["groups"]:
            desc, duration = group["descriptor"], group["duration"]
            blocks = ", ".join(f"{row['block_num']}/{row['mix_block_num']}:{row['event_count']}"
                               for row in group["block_configurations"])
            label = (f"{capture['capture_key']} / {desc['native_operator_type']} / "
                     f"{group['descriptor_id'][7:19]} / {desc['op_state']}")
            times = " / ".join(f"{duration[name] / 1000:.6f}" for name in ("mean", "min", "max"))
            lines.append(f"| {label} | {group['event_count']} | {blocks} | {times} |")
    lines += [
        "", "| Descriptor | AIC total / MAC / MTE1 / MTE2 / scalar mean (us) | "
        "AIV total / vector / MTE2 / MTE3 / scalar mean (us) |",
        "| --- | --- | --- |",
    ]
    for capture in report["captures"]:
        for group in capture["groups"]:
            values = []
            for names in (
                ("aic_total_time", "aic_mac_time", "aic_mte1_time", "aic_mte2_time", "aic_scalar_time"),
                ("aiv_total_time", "aiv_vec_time", "aiv_mte2_time", "aiv_mte3_time", "aiv_scalar_time"),
            ):
                values.append(" / ".join(
                    f"{group['pmu'][name]['mean'] / 1000:.6f}"
                    if group["pmu"].get(name, {}).get("mean") is not None else "unavailable"
                    for name in names))
            lines.append(f"| {group['descriptor_id'][7:19]} | {values[0]} | {values[1]} |")
    lines += ["", "The JSON preserves every selected descriptor's six original tensor fields, "
              "all exported PMU distributions, missing/zero counts and source line samples. "
              "Tensor descriptor identity excludes core and OP State; execution groups retain "
              "those fields so dynamic/static exports are not silently conflated. "
              "Histograms use eight logarithmic bins per power of two; extrema and arithmetic "
              "means are streamed exactly up to floating-point arithmetic. No per-event values "
              "are retained, no simulation is executed, and no new NPU capture is collected.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--directory", type=Path, default=BASE)
    parser.add_argument("--output", type=Path, default=BASE / "decode-hc-pmu-evidence.json")
    args = parser.parse_args()
    started = time.perf_counter()
    captures = []
    for key, requested in REQUESTS.items():
        summary_path = args.directory / f"body-{key}.json"
        summary = read(summary_path)
        result = analyze_capture(
            summary["source_identity"]["path"], requested,
            expected_source=summary["source_identity"],
            expected_positive_events=summary["positive_event_count"])
        captures.append({
            "capture_key": key, "source_summary": {
                "file": str(summary_path), "sha256": digest(summary_path)}, **result})
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = int(peak if sys.platform == "darwin" else peak * 1024)
    report = {
        "schema_version": "mindie-retained-decode-hc-pmu-evidence/1",
        "status": "completed", "not_new_live_collection": True,
        "generator": {"file": str(Path(__file__).resolve()), "sha256": digest(__file__)},
        "raw_capture_count": len(captures),
        "unique_positive_events": sum(row["positive_event_count"] for row in captures),
        "captures": captures, "elapsed_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak, "memory_budget_bytes": 512 * 1024**2,
        "prediction_executions": 0,
        "interpretation": {
            "block_num_does_not_identify_kv_splits": True,
            "phase_context_step_layer_and_dispatch_not_observed": True,
            "pmu_columns_can_overlap_and_are_not_additive_wall_time": True,
            "units": "Time(us) normalized once to ns; cycles/ratio/percent unchanged",
            "histogram": "8 logarithmic bins per power of two; fixed bounds and explicit zero/negative bins",
        },
    }
    if peak > report["memory_budget_bytes"]:
        raise RuntimeError("pmu_evidence_memory_budget_exceeded")
    args.output.write_text(json.dumps(report, separators=(",", ":"), allow_nan=False) + "\n")
    args.output.with_suffix(".md").write_text(markdown(report))
    print(json.dumps({key: report[key] for key in (
        "status", "raw_capture_count", "unique_positive_events", "elapsed_seconds", "peak_rss_bytes")}))


if __name__ == "__main__":
    main()
