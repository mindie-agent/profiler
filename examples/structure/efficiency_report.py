"""Whole-network 4D MFU/MBU/CV efficiency, 0.8x MBU fitting, and 30ms SLA scaling report.

[Role] Generate operator-level and whole-network Cube_MFU / Vec_MFU / MBU / Link_Util /
  CV_Overlap breakdowns, counterfactual 0.8x MBU target efficiency & Roofline regime
  fitting, and 2x HBM vs 2x Compute hardware scaling throughput comparisons under an
  explicit decode SLA (default <= 30 ms) across representative LLM cases.
[Invariants] Strictly uses mindie_sim.prediction.efficiency physical work volumes and
  graph execution timelines; never mutates input case files or fabricates mock weights.
[Timeouts & Locks] Pure in-memory analytical execution; typical multi-case report < 10s.
[Side-Effect Policy] Read-only over structure case files; writes JSON only when --json-out
  is explicitly passed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from mindie_sim.prediction.efficiency import (
    analyze_network_efficiency,
    fit_efficiency_targets,
    solve_hardware_sla_throughput,
)
from mindie_sim.prediction.structure import parse_case

CASES_DIR = Path(__file__).resolve().parent / "cases"

DEFAULT_CASES: tuple[tuple[str, str], ...] = (
    ("Kimi-K3 (W4A8, KDA + DeepSeekMoE, 4-Layer Fixture)", "a3-kimi4-tp16-longctx-source.json"),
    ("Qwen3.5-35B-TP4 (A3, Hybrid GDN + MoE)", "a3-qwen35-tp4-long-context-source.json"),
)


def _fmt_pct(val: float | None) -> str:
    if val is None:
        return "   -  "
    return f"{val * 100.0:5.1f}%"


def _fmt_tokens(tokens: int) -> str:
    if tokens >= 1024 and tokens % 1024 == 0:
        return f"{tokens // 1024}K"
    return f"{tokens}tok"


def _load_case(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"case_file_not_found:{path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return parse_case(raw)


def build_efficiency_report(
    case_entries: Sequence[tuple[str, Path]] | None = None,
    *,
    decode_contexts: Sequence[int] = (4096, 131072),
    prefill_tokens: int = 4096,
    sla_ms: float = 30.0,
    target_mbu: float = 0.80,
    target_cube_mfu: float = 0.75,
    target_vec_mfu: float = 0.65,
    sla_max_sequences_per_dp: int = 16,
) -> dict[str, Any]:
    """Run whole-network efficiency, 0.8x MBU target fitting, and SLA scaling across cases."""
    if not decode_contexts:
        raise ValueError("decode_contexts_must_not_be_empty")
    if case_entries is None:
        case_entries = [
            (label, CASES_DIR / filename)
            for label, filename in DEFAULT_CASES
        ]
    if not case_entries:
        raise ValueError("no_case_entries_configured")

    cases_report: list[dict[str, Any]] = []
    for label, path in case_entries:
        case = _load_case(path)
        decode_runs: list[dict[str, Any]] = []
        for ctx in decode_contexts:
            fit = fit_efficiency_targets(
                case,
                phase="decode",
                tokens=1,
                context=ctx,
                sequences=1,
                target_mbu=target_mbu,
                target_cube_mfu=target_cube_mfu,
                target_vec_mfu=target_vec_mfu,
                mode="clamp_to_target",
            )
            net = {k: v for k, v in fit["baseline_analysis"].items() if k != "operators"}
            sla = solve_hardware_sla_throughput(
                case,
                sla_ms=sla_ms,
                context=ctx,
                tokens_per_seq=1,
                max_sequences_per_dp=sla_max_sequences_per_dp,
                target_mbu=target_mbu,
                target_cube_mfu=target_cube_mfu,
                target_vec_mfu=target_vec_mfu,
                b1_analysis=fit["baseline_analysis"],
            )
            decode_runs.append(
                {
                    "context": int(ctx),
                    "network_efficiency": net,
                    "target_fitting": {
                        k: v
                        for k, v in fit.items()
                        if k != "baseline_analysis"
                    },
                    "sla_scaling": sla,
                }
            )

        prefill_fit = fit_efficiency_targets(
            case,
            phase="prefill",
            tokens=prefill_tokens,
            context=0,
            sequences=1,
            target_mbu=target_mbu,
            target_cube_mfu=target_cube_mfu,
            target_vec_mfu=target_vec_mfu,
            mode="clamp_to_target",
        )
        prefill_net = {
            k: v for k, v in prefill_fit["baseline_analysis"].items() if k != "operators"
        }
        cases_report.append(
            {
                "label": label,
                "case_file": path.name,
                "sku": case.machine.sku,
                "model_name": case.model.name,
                "parallel": {
                    "tp": int(case.runtime.parallel.tp),
                    "dp": int(case.runtime.parallel.dp),
                    "ep": int(case.runtime.parallel.ep),
                },
                "decode_runs": decode_runs,
                "prefill_run": {
                    "tokens": int(prefill_tokens),
                    "network_efficiency": prefill_net,
                    "target_fitting": {
                        k: v
                        for k, v in prefill_fit.items()
                        if k != "baseline_analysis"
                    },
                },
            }
        )

    return {
        "parameters": {
            "decode_contexts": list(decode_contexts),
            "prefill_tokens": int(prefill_tokens),
            "sla_ms": float(sla_ms),
            "target_mbu": float(target_mbu),
            "target_cube_mfu": float(target_cube_mfu),
            "target_vec_mfu": float(target_vec_mfu),
        },
        "cases": cases_report,
    }


def format_markdown_report(report: Mapping[str, Any]) -> str:
    """Format the multi-case efficiency & SLA report into clean Markdown tables."""
    lines: list[str] = []
    params = report["parameters"]
    sla_ms = params["sla_ms"]
    target_mbu = params["target_mbu"]

    lines.append("# Whole-Network 4D MFU/MBU/CV Efficiency & Hardware Scaling SLA Report")
    lines.append("")
    lines.append("## 1. Whole-Network 4D MFU / MBU / CV Summary (Decode & Prefill, B=1 per DP)")
    lines.append("")
    lines.append(
        "| Case | Phase / Ctx | Graph ms | OpSum ms | Cube MFU | Vec MFU | Net MBU | Link Util | Roofline Eff | CV Overlap | Mem% | Cube% | Vec% | Link% |"
    )
    lines.append(
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )

    for case_entry in report["cases"]:
        label = case_entry["label"]
        for dec in case_entry["decode_runs"]:
            ctx_k = f"Decode {_fmt_tokens(dec['context'])}"
            net = dec["network_efficiency"]
            bb = net["breakdown_by_bound"]
            lines.append(
                f"| {label} | {ctx_k} | {net['graph_duration_ms']:7.2f} | {net['operator_sum_ms']:7.2f} "
                f"| {_fmt_pct(net['network_cube_mfu'])} | {_fmt_pct(net['network_vec_mfu'])} "
                f"| {_fmt_pct(net['network_mbu'])} | {_fmt_pct(net['network_link_util'])} "
                f"| {_fmt_pct(net['network_roofline_efficiency'])} | {_fmt_pct(net['network_cv_overlap'])} "
                f"| {_fmt_pct(bb['memory_bound']['share_of_operator_sum'])} "
                f"| {_fmt_pct(bb['cube_bound']['share_of_operator_sum'])} "
                f"| {_fmt_pct(bb['vector_bound']['share_of_operator_sum'])} "
                f"| {_fmt_pct(bb['link_bound']['share_of_operator_sum'])} |"
            )
        pre = case_entry["prefill_run"]
        pnet = pre["network_efficiency"]
        pbb = pnet["breakdown_by_bound"]
        lines.append(
            f"| {label} | Prefill {_fmt_tokens(pre['tokens'])} | {pnet['graph_duration_ms']:7.2f} | {pnet['operator_sum_ms']:7.2f} "
            f"| {_fmt_pct(pnet['network_cube_mfu'])} | {_fmt_pct(pnet['network_vec_mfu'])} "
            f"| {_fmt_pct(pnet['network_mbu'])} | {_fmt_pct(pnet['network_link_util'])} "
            f"| {_fmt_pct(pnet['network_roofline_efficiency'])} | {_fmt_pct(pnet['network_cv_overlap'])} "
            f"| {_fmt_pct(pbb['memory_bound']['share_of_operator_sum'])} "
            f"| {_fmt_pct(pbb['cube_bound']['share_of_operator_sum'])} "
            f"| {_fmt_pct(pbb['vector_bound']['share_of_operator_sum'])} "
            f"| {_fmt_pct(pbb['link_bound']['share_of_operator_sum'])} |"
        )

    last_ctx_label = _fmt_tokens(int(params["decode_contexts"][-1]))
    lines.append("")
    lines.append(f"## 2. Operator Family Breakdown (Decode {last_ctx_label}, B=1 per DP)")
    lines.append("")
    lines.append(
        "| Case | Family | Duration ms | Share % | Cube MFU | Vec MFU | MBU | Link Util | Roofline Eff |"
    )
    lines.append(
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    for case_entry in report["cases"]:
        label = case_entry["label"]
        dec_last = case_entry["decode_runs"][-1]
        fam_list = dec_last["network_efficiency"]["breakdown_by_family"]
        for fdata in fam_list:
            fam_rec = f"{fdata['family']}/{fdata['recipe']}"
            lines.append(
                f"| {label} | `{fam_rec}` | {fdata['duration_ms']:7.3f} | {_fmt_pct(fdata['share_of_operator_sum'])} "
                f"| {_fmt_pct(fdata['cube_mfu'])} | {_fmt_pct(fdata['vec_mfu'])} "
                f"| {_fmt_pct(fdata['mbu'])} | {_fmt_pct(fdata['link_util'])} "
                f"| {_fmt_pct(fdata['roofline_efficiency'])} |"
            )

    lines.append("")
    lines.append(f"## 3. Counterfactual `{target_mbu:.2f}x MBU` Target Fitting & Top Bottlenecks")
    lines.append("")
    lines.append(
        "| Case | Phase / Ctx | Current ms | Target ms | Saved ms | Speedup | Curr Net MBU | Target Net MBU | Top Bottleneck Family (Gap ms, Actual -> Target MBU) |"
    )
    lines.append(
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |"
    )
    for case_entry in report["cases"]:
        label = case_entry["label"]
        for dec in case_entry["decode_runs"]:
            ctx_k = f"Decode {_fmt_tokens(dec['context'])}"
            tf = dec["target_fitting"]
            top = tf["top_bottlenecks"][0] if tf["top_bottlenecks"] else None
            top_str = (
                f"`{top['family']}/{top['recipe']}` (-{top['gap_ms']:.2f}ms, "
                f"{(top['actual_mbu'] or 0.0)*100:.1f}% -> {(top['target_mbu'] or 0.0)*100:.1f}%)"
                if top
                else "none"
            )
            lines.append(
                f"| {label} | {ctx_k} | {tf['current_step_duration_ms']:7.2f} "
                f"| {tf['target_step_duration_ms']:7.2f} | {tf['saved_ms']:6.2f} "
                f"| {tf['step_speedup']:5.2f}x | {_fmt_pct(tf['current_network_mbu'])} "
                f"| {_fmt_pct(tf['target_network_mbu'])} | {top_str} |"
            )

    sla_boundary = (
        report["cases"][0]["decode_runs"][0]["sla_scaling"].get("timing_boundary", "target_body_only")
        if report["cases"] and report["cases"][0]["decode_runs"]
        else "target_body_only"
    )
    lines.append("")
    lines.append(
        f"## 4. Counterfactual Hardware Scaling (`1x` vs `2x HBM` vs `2x Compute`) under Decode SLA <= {sla_ms:.0f} ms (Boundary: `{sla_boundary}`)"
    )
    lines.append("")
    lines.append(
        "| Case | Context | Scenario | B=1 ms | B_VRAM | B_SLA (DP) | B_Feas (DP) | Feas Total B | Feas Step ms | TPS_Feas (tok/s) | Feas Gain | TPS_SLA (tok/s) | SLA Gain | Net MBU | Cube MFU | Mem% / Comp% / Link% |"
    )
    lines.append(
        "| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |"
    )
    for case_entry in report["cases"]:
        label = case_entry["label"]
        for dec in case_entry["decode_runs"]:
            ctx_k = _fmt_tokens(dec["context"])
            sla = dec["sla_scaling"]
            for sc in sla["scenarios"]:
                bs = sc["bottleneck_shares"]
                comp_share = bs["cube_bound"] + bs["vector_bound"]
                shares_str = (
                    f"{bs['memory_bound']*100:4.0f}% / {comp_share*100:4.0f}% / {bs['link_bound']*100:4.0f}%"
                )
                lines.append(
                    f"| {label} | {ctx_k} | `{sc['scenario_id']}` | {sc['step_ms_at_b1']:6.2f} "
                    f"| {sc['b_vram_max']:6d} | {sc['b_sla']:6d} | {sc['b_feasible']:6d} "
                    f"| {sc['total_feasible_concurrency']:7d} | {sc['step_ms_feasible']:7.2f} "
                    f"| {sc['tps_feasible']:9.1f} | {sc['tps_feasible_gain_vs_baseline']:6.2f}x "
                    f"| {sc['tps_at_sla']:9.1f} | {sc['tps_gain_vs_baseline']:6.2f}x "
                    f"| {_fmt_pct(sc['network_mbu_at_sla'])} | {_fmt_pct(sc['network_cube_mfu_at_sla'])} | {shares_str} |"
                )

    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        help="Optional Label=path/to/case.json or path/to/case.json (repeatable).",
    )
    parser.add_argument(
        "--contexts",
        default="4096,131072",
        help="Comma-separated decode context lengths (default: 4096,131072).",
    )
    parser.add_argument(
        "--prefill-tokens",
        type=int,
        default=4096,
        help="Prefill token count for prefill efficiency breakdown (default: 4096).",
    )
    parser.add_argument(
        "--sla-ms",
        type=float,
        default=30.0,
        help="Decode step latency SLA in ms (default: 30.0).",
    )
    parser.add_argument(
        "--target-mbu",
        type=float,
        default=0.80,
        help="Target MBU ceiling for counterfactual fitting (default: 0.80).",
    )
    parser.add_argument(
        "--target-cube-mfu",
        type=float,
        default=0.75,
        help="Target Cube MFU ceiling for counterfactual fitting (default: 0.75).",
    )
    parser.add_argument(
        "--target-vec-mfu",
        type=float,
        default=0.65,
        help="Target Vector MFU ceiling for counterfactual fitting (default: 0.65).",
    )
    parser.add_argument(
        "--max-seq-per-dp",
        type=int,
        default=16,
        help="Upper bound on sequences per DP replica during SLA search (default: 16).",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write full structured JSON report.",
    )
    args = parser.parse_args(argv)

    case_entries: list[tuple[str, Path]] | None = None
    if args.cases:
        case_entries = []
        for item in args.cases:
            if "=" in item:
                lbl, raw_path = item.split("=", 1)
                case_entries.append((lbl.strip(), Path(raw_path.strip())))
            else:
                p = Path(item.strip())
                case_entries.append((p.stem, p))

    contexts = [int(x.strip()) for x in args.contexts.split(",") if x.strip()]
    report = build_efficiency_report(
        case_entries,
        decode_contexts=contexts,
        prefill_tokens=args.prefill_tokens,
        sla_ms=args.sla_ms,
        target_mbu=args.target_mbu,
        target_cube_mfu=args.target_cube_mfu,
        target_vec_mfu=args.target_vec_mfu,
        sla_max_sequences_per_dp=args.max_seq_per_dp,
    )
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(format_markdown_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
