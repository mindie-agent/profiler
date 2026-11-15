"""Build the hermetic A5 golden fixture from read-only live captures.

[Role]
  Extract every valid measured operator point from the read-only A5 capture
  directory: all 160 attention rows, all 120 fabric collective rows, all 36 MC2
  dispatch/combine stage timings (18 rows x 2 stages, including skew and prefill),
  and all 112 modeled kernel rows out of the 140 raw rows (428 points).  The five
  layer-block points are kept separately in ``block_points`` so the 428 operator
  points stay exactly the requested set.  Record exact source
  SHA-256 digests, per-point ``source_file``/``source_row_index`` provenance,
  unique IDs, calibration-domain flags, the unmodeled-row list and the rejected
  padded-varlen ABI record.

[Invariants]
  * The source directory is opened read-only; only the local fixture (or an
    explicit ``--output``) is written.
  * Every point keeps its measured p50 and a stable unique ``id``.
  * Rows without a numeric p50 are skipped, never guessed; the refused
    padded-varlen row is preserved as an explicit negative ABI fixture.
  * MC2 and kernel selection is complete, not a first-N excerpt.
  * Re-running produces byte-identical output (sorted keys, fixed ordering).

[Timeouts & Locks]
  Bounded local file reads; no device, network or subprocess work.

[Side-Effect Policy]
  Writes only ``tests/fixtures/a5_op_goldens.json`` (or ``--output``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

CAPTURE_DIR = Path(os.environ.get(
    "A5_CAPTURE_DIR",
    "/Volumes/data/Codex/2026-11-12/kan-x/work/agy-closure/live_a5_captures/data"))
OUT = Path(__file__).resolve().with_name("a5_op_goldens.json")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mindie_profiler.op_abi_bridge import infer_request  # noqa: E402
from mindie_profiler.op_formula_annotator import (  # noqa: E402
    _norm_row, load_rows,
)

SOURCE_FILES = (
    "mha_gqa_mqa_and_padding_a5.json",
    "layer_kimi_decode.json",
    "fabric_a5_16npu.json",
    "mc2_megamoe_ep_sweep.json",
    "kimi_layer_profile/kernel_details.csv",
)


def _digest(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(CAPTURE_DIR)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "kind": "csv" if path.suffix.lower() == ".csv" else "json",
    }


def _p50(row: dict) -> float | None:
    value = row.get("p50_us")
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _point(**kwargs) -> dict:
    return kwargs


def _attention_points(data: dict) -> tuple[list[dict], list[dict]]:
    source = "mha_gqa_mqa_and_padding_a5.json"
    points: list[dict] = []
    rejected: list[dict] = []
    for index, row in enumerate(data["results"]["A"]):
        measured = _p50(row)
        if measured is None:
            continue
        points.append(_point(
            id=f"attn_A_r{index}_kv{row['kv_len']}_q{row['q_len']}",
            group="attention", operator="flash_attention",
            params={"q_len": row["q_len"], "kv_len": row["kv_len"],
                    "hq": row["hq"], "hkv": row["hkv"], "head_dim": 128,
                    "phase": "decode", "layout": "TND", "dtype": "bf16"},
            launch_mode="python_eager", steady_l2_warm=True,
            measured_us=measured, source_file=source, source_row_index=index,
            source_section="A", in_calibrated_ref_domain=True,
            note=f"M_eff={row.get('m_eff')} tiles={row.get('tiles')}"))
    for index, row in enumerate(data["results"]["B"]):
        measured = _p50(row)
        if measured is None:
            continue
        points.append(_point(
            id=f"attn_B_r{index}_{row['variant']}_kv{row['kv_len']}_q{row['q_len']}",
            group="attention", operator="flash_attention",
            params={"q_len": row["q_len"], "kv_len": row["kv_len"],
                    "hq": row["hq"], "hkv": row["hkv"], "head_dim": 128,
                    "phase": "decode", "layout": "TND", "dtype": "bf16"},
            launch_mode="python_eager", steady_l2_warm=True,
            measured_us=measured, source_file=source, source_row_index=index,
            source_section="B", in_calibrated_ref_domain=True,
            note=f"{row['variant']} groups={row.get('groups')}"))
    for index, row in enumerate(data["results"]["C"]):
        measured = _p50(row)
        if measured is None:
            continue
        params = {"q_len": row["T"], "kv_len": row["T"], "hq": row["hq"],
                  "hkv": row["hkv"], "head_dim": 128, "phase": "prefill",
                  "layout": "TND", "dtype": "bf16",
                  "causal": bool(row["causal"])}
        if row["causal"]:
            # attn_bench.py:131 allocates and passes a BOOL [2048, 2048] mask.
            params["attn_mask_shape"] = [2048, 2048]
            params["mask_dtype"] = "bool"
        points.append(_point(
            id=(f"attn_C_r{index}_{row['variant']}_T{row['T']}_"
                f"{'causal' if row['causal'] else 'dense'}"),
            group="attention", operator="flash_attention", params=params,
            launch_mode="python_eager", steady_l2_warm=True,
            measured_us=measured, source_file=source, source_row_index=index,
            source_section="C", in_calibrated_ref_domain=True,
            note=f"{row['variant']} prefill"))
    op_map = {
        "fused_infer_attention": (
            "flash_attention",
            lambda row: {"q_len": row["logical_m"], "kv_len": 4096, "hq": 64,
                         "hkv": 1, "head_dim": 128, "phase": "decode",
                         "layout": "TND", "dtype": "bf16"}),
        "npu_rms_norm": (
            "rms_norm",
            lambda row: {"rows": row["storage_m"], "hidden": 7168,
                         "dtype": "bf16"}),
        "npu_dynamic_quant": (
            "dynamic_quant",
            lambda row: {"rows": row["storage_m"], "hidden": 7168,
                         "dtype": "bf16"}),
        "matmul_HxH": (
            "matmul",
            lambda row: {"M": row["storage_m"], "N": 7168, "K": 7168,
                         "dtype": "bf16"}),
        "matmul_HxN_staircase": (
            "matmul",
            lambda row: {"M": row["m"], "N": 2048, "K": 7168, "dtype": "bf16"}),
    }
    for index, row in enumerate(data["results"]["D"]):
        measured = _p50(row)
        op = row.get("op")
        if measured is None:
            if op == "padded_varlen_contract":
                rejected.append({
                    "id": "reject_D_padded_varlen",
                    "source_file": source, "source_row_index": index,
                    "raw_record": dict(row),
                    "expected_status": "invalid_abi",
                    "expected_code": "rejected_capture_row",
                    "reason": "captured launch refused by the runtime",
                })
            continue
        if op not in op_map:
            continue
        operator, builder = op_map[op]
        tag = (f"m{row['m']}" if "m" in row
               else f"m{row.get('storage_m')}_{row.get('m_bucket')}")
        points.append(_point(
            id=f"attn_D_r{index}_{op}_{tag}",
            group="attention", operator=operator, params=builder(row),
            launch_mode="python_eager", steady_l2_warm=True,
            measured_us=measured, source_file=source, source_row_index=index,
            source_section="D", in_calibrated_ref_domain=True,
            note=f"storage_m={row.get('storage_m')} "
                 f"logical_m={row.get('logical_m')}"))
    return points, rejected


def _layer_points(data: dict) -> list[dict]:
    per_op = data["per_op"]
    hidden, heads, kv_heads, head_dim = 7168, 96, 1, 192
    inter, experts, topk, ep = 3072, 896, 16, 8
    points: list[dict] = []
    specs = (
        ("rms_norm", "rms_norm", {"rows": 32, "hidden": hidden, "dtype": "bf16"},
         "Kimi K3.1 decode T=32"),
        ("qkv_proj", "matmul",
         {"M": 32, "N": 18816, "K": hidden, "dtype": "bf16"},
         "QKV projection, BF16 weight"),
        ("gate_matmul", "matmul",
         {"M": 32, "N": 896, "K": hidden, "dtype": "bf16"},
         "router gate matmul"),
    )
    for name, operator, params, note in specs:
        measured = _p50(per_op[name])
        if measured is None:
            continue
        points.append(_point(
            id=f"layer_{name}", group="layer", operator=operator,
            params=params, launch_mode="python_eager", steady_l2_warm=True,
            measured_us=measured, source_file="layer_kimi_decode.json",
            source_row_index=0, in_calibrated_ref_domain=True, note=note))
    measured = _p50(per_op.get("attention_tnd", {}))
    if measured is not None:
        points.append(_point(
            id="layer_attention_tnd", group="layer", operator="composite_chain",
            params={"components": [
                {"operator": "matmul",
                 "params": {"M": 32, "N": 18816, "K": hidden, "dtype": "bf16"}},
                {"operator": "flash_attention",
                 "params": {"q_len": 32, "kv_len": 32, "hq": heads,
                            "hkv": kv_heads, "head_dim": head_dim,
                            "phase": "decode", "layout": "TND",
                            "dtype": "bf16", "actual_seq_lens_q": [32],
                            "actual_seq_lens_kv": [32]}},
                {"operator": "matmul",
                 "params": {"M": 32, "N": 7168, "K": heads * head_dim,
                            "dtype": "bf16"}},
            ]},
            launch_mode="python_eager", steady_l2_warm=True,
            measured_us=measured, source_file="layer_kimi_decode.json",
            source_row_index=0, in_calibrated_ref_domain=True,
            note="qkv + FIA + o_proj measured as one eager block"))
    measured = _p50(per_op.get("moe_block", {}))
    if measured is not None:
        common = {"tokens": 32, "hidden": hidden, "experts_total": experts,
                  "experts_local": experts // ep, "topk": topk, "ep": ep,
                  "dtype": "bf16"}
        points.append(_point(
            id="layer_moe_block", group="layer", operator="composite_chain",
            params={"components": [
                {"operator": "matmul",
                 "params": {"M": 32, "N": 896, "K": hidden, "dtype": "bf16"}},
                {"operator": "moe_distribute_dispatch", "params": dict(common)},
                {"operator": "grouped_matmul",
                 "params": {**common, "inter": inter, "mode": "up_gate"}},
                {"operator": "swiglu",
                 "params": {"rows": 64, "hidden": inter, "dtype": "bf16"}},
                {"operator": "grouped_matmul",
                 "params": {**common, "inter": inter, "mode": "down"}},
                {"operator": "moe_distribute_combine", "params": dict(common)},
            ]},
            launch_mode="python_eager", steady_l2_warm=True,
            measured_us=measured, source_file="layer_kimi_decode.json",
            source_row_index=0, in_calibrated_ref_domain=False,
            note="gate + dispatch + up/down grouped GEMM + combine"))
    return points


def _fabric_points(data: dict) -> list[dict]:
    op_map = {
        "all_reduce": "hccl_all_reduce", "all_gather": "hccl_all_gather",
        "reduce_scatter": "hccl_reduce_scatter",
        "all_to_all_single": "hccl_all_to_all",
    }
    points: list[dict] = []
    for index, row in enumerate(data["results"]):
        measured = _p50(row)
        op = row.get("op")
        if measured is None or op not in op_map:
            continue
        points.append(_point(
            id=f"fabric_r{index}_{op}_ws{row['world_size']}_{row['size_bytes']}",
            group="fabric", operator=op_map[op],
            params={"size_bytes": row["size_bytes"],
                    "world_size": row["world_size"],
                    "algorithm": "ring", "dtype": "bf16", "transport": "ub"},
            launch_mode="python_eager", steady_l2_warm=False,
            measured_us=measured, source_file="fabric_a5_16npu.json",
            source_row_index=index, in_calibrated_ref_domain=True,
            note=f"busbw={row.get('busbw_gbps')} GB/s "
                 f"transport={row.get('transport', 'ub_urma')}"))
    return points


def _mc2_points(data: dict) -> list[dict]:
    from mindie_sim.op_formulas.hardware import A5, mc2_fit_domain
    points: list[dict] = []
    for index, row in enumerate(data["results"]):
        ep = int(row["ep"])
        tokens = int(row["tokens_per_rank"])
        skew = float(row.get("eta_target") or 1.0)
        domain = mc2_fit_domain(tokens, skew, A5, "ub")
        common = {"tokens": tokens, "hidden": 7168, "experts_total": 64,
                  "experts_local": max(1, 64 // ep), "topk": 8, "ep": ep,
                  "dtype": "bf16", "use_measured_fit": True, "skew": skew,
                  "transport": "ub"}
        for stage, operator in (("dispatch", "moe_distribute_dispatch"),
                                ("combine", "moe_distribute_combine")):
            measured = row.get(f"{stage}_us")
            if measured is None:
                continue
            number = _p50({"p50_us": measured})
            if number is None:
                continue
            points.append(_point(
                id=f"mc2_r{index}_ep{ep}_t{tokens}_skew{skew}_{stage}",
                group="mc2", operator=operator, params=dict(common),
                launch_mode="python_eager", steady_l2_warm=False,
                measured_us=number,
                source_file="mc2_megamoe_ep_sweep.json",
                source_row_index=index,
                in_calibrated_ref_domain=(domain == "in_calibrated_ref_domain"),
                fit_domain_status=domain,
                note=f"expand_tokens={row.get('expand_tokens')} stage={stage} "
                     f"eta_rank={row.get('eta_rank')}"))
    return points


def _kernel_points() -> tuple[list[dict], list[dict]]:
    path = CAPTURE_DIR / "kimi_layer_profile" / "kernel_details.csv"
    rows = load_rows(path)
    points: list[dict] = []
    unmodeled: list[dict] = []
    for index, raw in enumerate(rows):
        normalized = _norm_row(raw)
        measured = _p50({"p50_us": normalized.get("duration_us")})
        if measured is None:
            unmodeled.append({"row_index": index, "name": normalized.get("name"),
                              "type": normalized.get("type"),
                              "code": "missing_duration"})
            continue
        try:
            operator, params, _flags = infer_request(normalized)
        except TimeoutError:
            raise
        except Exception as exc:  # noqa: BLE001 - fixture records the reason
            unmodeled.append({"row_index": index, "name": normalized.get("name"),
                              "type": normalized.get("type"),
                              "code": getattr(exc, "code", type(exc).__name__),
                              "reason": str(exc)[:160]})
            continue
        points.append(_point(
            id=f"kernel_r{index}_{operator}",
            group="kernel", operator=operator, params=params,
            launch_mode="aclgraph", steady_l2_warm=True, measured_us=measured,
            source_file="kimi_layer_profile/kernel_details.csv",
            source_row_index=index, in_calibrated_ref_domain=True,
            note=str(normalized.get("name"))[:80],
            raw_row={
                "name": normalized.get("name"),
                "type": normalized.get("type"),
                "duration_us": normalized.get("duration_us"),
                "input_shapes": normalized.get("input_shapes"),
                "input_data_types": normalized.get("input_data_types"),
                "input_formats": normalized.get("input_formats"),
                "output_shapes": normalized.get("output_shapes"),
                "output_data_types": normalized.get("output_data_types"),
                "output_formats": normalized.get("output_formats"),
            }))
    return points, unmodeled


def build() -> dict:
    manifest = [_digest(CAPTURE_DIR / name) for name in SOURCE_FILES]
    mha = json.loads((CAPTURE_DIR / "mha_gqa_mqa_and_padding_a5.json").read_text())
    attention, rejected = _attention_points(mha)
    layer = _layer_points(
        json.loads((CAPTURE_DIR / "layer_kimi_decode.json").read_text()))
    fabric = _fabric_points(
        json.loads((CAPTURE_DIR / "fabric_a5_16npu.json").read_text()))
    mc2 = _mc2_points(
        json.loads((CAPTURE_DIR / "mc2_megamoe_ep_sweep.json").read_text()))
    kernel, unmodeled = _kernel_points()
    points = attention + fabric + mc2 + kernel
    points.sort(key=lambda item: (item["group"], item["id"]))
    ids = [item["id"] for item in points]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate golden point ids")
    counts: dict[str, int] = {}
    for item in points:
        counts[item["group"]] = counts.get(item["group"], 0) + 1
    return {
        "schema": "a5-op-goldens/2",
        "device": "Ascend950DT",
        "sku": "Ascend950DT_9581",
        "capture_dir_readonly": "external A5 capture mount (read-only; not read by tests)",
        "source_files": manifest,
        "counts": {**counts, "total": len(points),
                   "block_points_separate": len(layer)},
        "attention_rows": len(attention),
        "fabric_rows": len(fabric),
        "mc2_rows": len(mc2) // 2,
        "mc2_stage_points": len(mc2),
        "kernel_rows": {"raw": len(kernel) + len(unmodeled),
                        "modeled": len(kernel), "unmodeled": len(unmodeled),
                        "unmodeled_rows": unmodeled},
        "rejected_points": rejected,
        "point_count": len(points),
        "points": points,
        "block_points": layer,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_a5_op_goldens")
    parser.add_argument("--output", default=str(OUT))
    args = parser.parse_args(argv)
    payload = build()
    target = Path(args.output)
    target.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(f"wrote {target} ({payload['point_count']} points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
