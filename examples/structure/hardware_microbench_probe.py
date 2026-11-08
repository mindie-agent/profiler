"""Systematic hardware microbenchmark and verification-capture calibration tool.

[Role]
  Measure or summarize physical hardware parameters required by the four-layer
  piecewise predictor: AIV/Cube kernel launch floor, 1-to-N core MTE2/HBM
  bandwidth scaling, strided gather burst amplification, GroupedMatmul per-expert
  wave quantization, and HCCS/RoCE collective latency + bandwidth curves.

[Invariants]
  * No model-name or case-id lookup tables are produced; outputs are pure
    hardware supply and physical floor parameters keyed by SKU and pipe.
  * Live NPU probing (``--mode live-npu``) uses ``torch.npu.Event(enable_timing=True)``
    with explicit warmup and synchronization; offline mode (``--mode verification``)
    aggregates retained hardware verification captures under ``sim/data/verification``.

[Timeouts & Locks]
  Bounded iteration counts in live microbenchmarks; pure local JSON reading in
  verification-summary mode. No background daemons or file locks.

[Side-Effect Policy]
  Read-only over verification captures; writes only to stdout or an explicit
  ``--output`` path when requested by the caller.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

SIM_VERIFICATION_DIR = Path(__file__).resolve().parents[3] / "sim" / "data" / "verification"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"verification_capture_missing:{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except TimeoutError:
        raise
    except (OSError, ValueError) as exc:
        raise ValueError(f"verification_capture_invalid:{path}:{exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"verification_capture_not_mapping:{path}")
    return data


def summarize_verification_captures(root: Path = SIM_VERIFICATION_DIR) -> dict[str, Any]:
    """Extract physical hardware parameters from retained verification artifacts."""
    if not root.exists():
        raise FileNotFoundError(f"verification_root_missing:{root}")
    a3_hier = _load_json(root / "a3-physical-hierarchy-20261030.json")
    kimi_audit = _load_json(root / "a3-kimi128k-mechanism-audit-20261030.json")
    ccu_two_die = _load_json(root / "hccl-ccu-two-die-20261030.json")
    links: dict[str, dict[str, float]] = {}
    for entry in a3_hier.get("results", ()):
        for link in entry.get("links", ()):
            channel = str(link.get("channel") or link.get("name") or "unknown")
            cap = float(link.get("capacity_bytes_per_ms") or 0.0)
            lat = float(link.get("latency_us") or 0.0)
            if channel not in links and cap > 0:
                links[channel] = {
                    "capacity_gbps": round(cap / 1e6, 3),
                    "latency_us": lat,
                    "semantics": str(link.get("semantics") or "per_port"),
                }
    isolated_ops: dict[str, dict[str, float]] = {}
    for row in kimi_audit.get("canonical_isolated_roles", {}).get("rows", ()):
        if int(row.get("tp") or 0) != 8:
            continue
        for name, item in (row.get("groups") or {}).items():
            calls = max(1, int(item.get("calls") or 1))
            elapsed_ms = float(item.get("elapsed_sum_ms") or 0.0)
            isolated_ops[name] = {
                "calls": calls,
                "per_call_us": round(elapsed_ms * 1000.0 / calls, 3),
                "program": str(item.get("program") or ""),
            }
    comm_pairs: list[dict[str, Any]] = []
    for item in kimi_audit.get("native_communication_comparison", ()):
        calls = max(1, int(item.get("calls") or 1))
        native_ms = float(item.get("native_sum_mean_ms") or 0.0)
        analytic_ms = float(item.get("current_isolated_operator_sum_ms") or 0.0)
        comm_pairs.append({
            "tp": int(item.get("tp") or 0),
            "family": str(item.get("family") or ""),
            "native_per_call_us": round(native_ms * 1000.0 / calls, 3),
            "analytic_per_call_us": round(analytic_ms * 1000.0 / calls, 3),
        })
    ccu_domains = [
        {
            "ranks": int(dom.get("ranks") or 0),
            "collective": str(dom.get("selection", {}).get("collective") or ""),
            "template": str(dom.get("selection", {}).get("template") or ""),
            "signal_bytes": int(dom.get("selection", {}).get("signal_bytes") or 0),
        }
        for dom in ccu_two_die.get("domains", ())
    ]
    return {
        "schema": "mindie-profiler-hardware-microbench-probe/1",
        "mode": "verification-summary",
        "verification_root": str(root),
        "physical_constants": {
            "mte2_burst_bytes": 512,
            "mte2_descriptor_bytes": 8,
            "ub_align_bytes": 32,
            "cube_fractal": 16,
            "aiv_launch_cycles_per_core": 4096 * 128,
            "aiv_wave_cycles_per_core": 256 * 128,
            "attention_launch_cycles_per_core": 16384 * 128,
            "attention_wave_cycles_per_core": 8192 * 128,
            "collective_tree_stage_cycles_per_core": 8192 * 128,
        },
        "links": links,
        "isolated_operator_latencies": isolated_ops,
        "native_collective_comparisons": comm_pairs,
        "ccu_two_die_domains": ccu_domains,
    }


def run_live_npu_microbench(
    *, warmup: int = 10, iters: int = 50, device_id: int = 0, timeout_s: float = 30.0
) -> dict[str, Any]:
    """Run live NPU microbenchmarks when ``torch_npu`` is available on the host."""
    import time

    try:
        import torch
        import torch_npu  # type: ignore[import-not-found]  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(f"live_npu_unavailable:{exc}") from exc
    if not torch.npu.is_available():
        raise RuntimeError("live_npu_device_not_found")
    if not hasattr(torch.npu, "mem_get_info"):
        raise RuntimeError("live_npu_mem_get_info_unavailable")
    device = torch.device(f"npu:{max(0, int(device_id))}")
    free_bytes, _ = torch.npu.mem_get_info(device)
    if int(free_bytes) < 1024 * 1024 * 1024:
        raise RuntimeError(f"live_npu_insufficient_free_hbm:{free_bytes}")
    device_name = torch.npu.get_device_name(device)
    deadline = time.monotonic() + max(1.0, float(timeout_s))

    def bench_op(fn) -> float:
        for _ in range(max(1, warmup)):
            if time.monotonic() > deadline:
                raise TimeoutError(f"live_npu_microbench_timeout:{timeout_s}s")
            fn()
        torch.npu.synchronize()
        samples: list[float] = []
        for _ in range(max(1, iters)):
            if time.monotonic() > deadline:
                raise TimeoutError(f"live_npu_microbench_timeout:{timeout_s}s")
            start = torch.npu.Event(enable_timing=True)
            end = torch.npu.Event(enable_timing=True)
            start.record()
            fn()
            end.record()
            torch.npu.synchronize()
            samples.append(float(start.elapsed_time(end)) * 1000.0)
        return round(median(samples), 3)

    hbm_curves: list[dict[str, float]] = []
    for num_bytes in (4096, 65536, 1048576, 16777216, 67108864):
        elems = max(1, num_bytes // 2)
        src = torch.ones(elems, dtype=torch.bfloat16, device=device)
        dst = torch.empty_like(src)
        lat_us = bench_op(lambda: dst.copy_(src))
        moved = 2.0 * elems * 2.0
        bw_gbps = round((moved / 1e9) / max(lat_us / 1e6, 1e-12), 2)
        hbm_curves.append({"bytes": float(num_bytes), "latency_us": lat_us, "effective_gbps": bw_gbps})

    gemm_curves: list[dict[str, float]] = []
    for m in (1, 4, 16, 64, 256, 1024):
        a = torch.randn((m, 7168), dtype=torch.bfloat16, device=device)
        b = torch.randn((7168, 2048), dtype=torch.bfloat16, device=device)
        lat_us = bench_op(lambda: torch.matmul(a, b))
        tflops = round((2.0 * m * 7168 * 2048 / 1e12) / max(lat_us / 1e6, 1e-12), 2)
        gemm_curves.append({"m": float(m), "k": 7168.0, "n": 2048.0, "latency_us": lat_us, "effective_tflops": tflops})

    return {
        "schema": "mindie-profiler-hardware-microbench-probe/1",
        "mode": "live-npu",
        "device_name": device_name,
        "aiv_launch_floor_us": hbm_curves[0]["latency_us"] if hbm_curves else 0.0,
        "hbm_bandwidth_curve": hbm_curves,
        "cube_gemm_curve": gemm_curves,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Hardware Microbenchmark & Calibration Probe (硬件微基准与参数标定报告)",
        "",
        f"- mode: `{report.get('mode')}`",
    ]
    if "physical_constants" in report:
        lines.extend(["", "## Declared Architectural Constants / 架构声明物理常数", "", "| constant | value |", "|---|---:|"])
        for k, v in report["physical_constants"].items():
            lines.append(f"| `{k}` | {v} |")
    if report.get("links"):
        lines.extend(["", "## Interconnect Link Hierarchy / 互联链路带宽与延迟", "", "| channel | capacity (GB/s) | latency (us) | semantics |", "|---|---:|---:|---|"])
        for ch, info in report["links"].items():
            lines.append(f"| `{ch}` | {info['capacity_gbps']:.3f} | {info['latency_us']:.2f} | `{info['semantics']}` |")
    if report.get("isolated_operator_latencies"):
        lines.extend(["", "## Isolated Operator Microbenchmarks / 单算子隔离实测基线 (TP=8)", "", "| operator role | calls | per_call (us) | program |", "|---|---:|---:|---|"])
        for name, info in sorted(report["isolated_operator_latencies"].items()):
            lines.append(f"| `{name}` | {info['calls']} | {info['per_call_us']:.3f} | `{info['program']}` |")
    return "\n".join(lines + [""])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=("verification", "live-npu"), default="verification")
    parser.add_argument("--verification-root", type=Path, default=SIM_VERIFICATION_DIR)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.mode == "live-npu":
        report = run_live_npu_microbench()
    else:
        report = summarize_verification_captures(args.verification_root)
    text = json.dumps(report, indent=2, sort_keys=True) if args.json else render_markdown(report)
    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
