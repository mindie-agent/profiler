"""Join retained MC2 elapsed histograms, PMU fields and conditional service.

[Role] Present complete same-population MC2 measurements without another raw scan.
[Invariants] Pooled quantiles use full counters, never averages of group medians.
  PMU pipelines may overlap; elapsed minus AIV is not identified network wait.
[Timeouts & Locks] One saved source at a time, no workers or locks.
[Side-Effect Policy] Write a compact evidence table; no costs or source changes.
"""
import argparse
from collections import Counter
from decimal import Decimal
from math import ceil
from pathlib import Path

from replay_body_operator_families import identity, read, write


FIELDS = ("Duration(us)", "aiv_time(us)", "aiv_scalar_time(us)",
          "aiv_vec_time(us)", "aiv_mte2_time(us)", "aiv_mte3_time(us)", "Wait Time(us)")


def statistics(counter):
    n = sum(counter.values())
    if not n:
        return None
    pairs = sorted(counter.items())
    def at(position):
        seen = 0
        for value, count in pairs:
            seen += count
            if seen > position:
                return value
        raise ValueError("counter_position_outside_population")
    return {"count": n, "mean": float(sum(value*count for value, count in pairs)/n),
            "p50": float((at((n-1)//2)+at(n//2))/2), "p90": float(at(ceil(.9*n)-1)),
            "min": float(pairs[0][0]), "max": float(pairs[-1][0])}


def summarize(directory, references):
    cases = []
    for source in sorted(directory.glob("*-native-partitions.json")):
        actual = read(source)
        reference_path = references / (actual["source_case_id"] + "-references.json")
        prior = read(reference_path)
        if (actual["source_identity"] != prior["source_identity"]
                or actual["body_acceptance_identity"] != prior["body_acceptance_identity"]
                or actual["geometry"] != prior["geometry"]
                or actual["forward_count"] != prior["forward_count"]):
            raise ValueError("mc2_source_or_population_changed")
        rows = []
        for kind in ("MoeDistributeDispatchV3", "MoeDistributeCombineV3"):
            groups = [g for g in actual["partitions"] if g["native_operator_type"] == kind]
            cost, = [g for g in prior["groups"] if g["native_operator_type"] == kind]
            histogram = Counter()
            for group in groups:
                if group["native_abi"] != cost["native_abi"]:
                    raise ValueError("mc2_full_abi_partition_mismatch")
                histogram.update(dict(group["duration_ns_counter"]))
            if histogram != Counter(dict(cost["duration_ns_counter"])):
                raise ValueError("mc2_whole_histogram_changed")
            fields = {}
            for field in FIELDS:
                values, missing, invalid = Counter(), 0, 0
                for group in groups:
                    item = group["raw_pmu"]["fields"][field]
                    values.update({Decimal(value): n for value, n in item["numeric_value_counter"]})
                    missing += item["missing_or_na_count"]
                    invalid += item["invalid_numeric_count"]
                if sum(values.values()) + missing + invalid != sum(histogram.values()):
                    raise ValueError("pmu_field_population_not_conserved")
                fields[field] = {"statistics": statistics(values), "missing_count": missing,
                                 "invalid_count": invalid, "zero_count": values.get(Decimal(0), 0)}
            elapsed = fields["Duration(us)"]["statistics"]
            expected = statistics(Counter({Decimal(ns)/1000: n for ns, n in histogram.items()}))
            if elapsed != expected:
                raise ValueError("pmu_duration_and_observed_histogram_differ")
            dimensions = {}
            for name in ("Accelerator Core", "Block Num", "Mix Block Num", "OP State"):
                values = Counter()
                for group in groups:
                    values.update(dict(group["raw_pmu"]["dimensions"][name]))
                dimensions[name] = sorted(values.items())
            rows.append({"native_operator_type": kind, "calls": elapsed["count"],
                "native_abi": cost["native_abi"], "fields": fields, "dimensions": dimensions,
                "calls_per_forward": cost["calls_per_forward"],
                "predicted_conditional_service_us": cost["predicted_reference_us"],
                "elapsed_minus_aiv_mean_us": elapsed["mean"]-fields["aiv_time(us)"]["statistics"]["mean"],
                "observed_activity_ms_per_forward": cost["observed_activity_ms_per_forward"],
                "conditional_activity_residual_ms_per_forward": cost["reference_activity_error_ms_per_forward"],
                "strict_accuracy_implied": False, "additional_budget_allowed": False})
        cases.append({"source_case_id": actual["source_case_id"], "source_identity": actual["source_identity"],
            "partition_identity": identity(source), "reference_identity": identity(reference_path),
            "reference_runtime_commit": prior["runtime_source_commit"],
            "geometry": actual["geometry"], "forward_count": actual["forward_count"], "families": rows})
    result = {"schema_version": "mindie-mc2-pmu-summary/1", "status": "completed", "cases": cases,
        "sources": len(cases), "complete_forwards": sum(c["forward_count"] for c in cases),
        "raw_capture_reads": 0, "new_prediction_executions": 0,
        "interpretation": ["All PMU statistics pool complete retained per-field counters within one source and native ABI.",
            "AIV/pipeline times retain exporter semantics; overlapping pipelines are not additive service times.",
            "Elapsed minus AIV is a difference of population means, not a measured network-wait component.",
            "CSV Wait Time is a separate exporter metric, not a bound on in-kernel peer waiting.",
            "Active routed values, peer readiness and private dispatch are unobserved; conditional service is not bandwidth calibration."]}
    write(directory / "mc2-pmu-summary.json", result)
    lines = ["# Kimi MC2 retained PMU evidence", "", f"{result['sources']} sources / {result['complete_forwards']} complete Forwards. No new raw read or prediction.", "",
        "| Source | Native op | Calls | Elapsed Mean/P50 us | AIV Mean/P50 us | Scalar Mean/P50 us | MTE2 Mean us | CSV Wait Mean us | Conditional service us |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for case in cases:
        for row in case["families"]:
            f = row["fields"]
            pairs = [f"{f[k]['statistics']['mean']:.3f}/{f[k]['statistics']['p50']:.3f}"
                     for k in FIELDS[:3]]
            lines.append(f"| {case['source_case_id']} | {row['native_operator_type']} | {row['calls']} | "
                + " | ".join(pairs) + f" | {f['aiv_mte2_time(us)']['statistics']['mean']:.3f} | "
                f"{f['Wait Time(us)']['statistics']['mean']:.3f} | {row['predicted_conditional_service_us']:.3f} |")
    lines += ["", *["- " + item for item in result["interpretation"]], ""]
    (directory / "mc2-pmu-summary.md").write_text("\n".join(lines))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("references", type=Path)
    args = parser.parse_args()
    report = summarize(args.directory, args.references)
    print({k: report[k] for k in ("sources", "complete_forwards", "raw_capture_reads")})
