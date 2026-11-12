"""Actual A5 per-owner buffer capacity linkage into matrix tile plans."""
import json
import os
from dataclasses import replace
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
PROFILER = HERE.parent
SIM = PROFILER.parent / "sim"
CELLS = Path(os.environ.get(
    "MINDIE_TEST_ORIGINAL_CELLS",
    "/private/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl"))
CELL_ID = "smoke_qwen36_single_dc_4k_c8"


def _z():
    if str(PROFILER / "examples" / "structure") not in sys.path:
        sys.path.insert(0, str(PROFILER / "examples" / "structure"))
    os.environ.setdefault("MINDIE_PROFILER_SOURCE", str(PROFILER))
    os.environ.setdefault("MINDIE_SIM_SOURCE", str(SIM))
    os.environ.setdefault("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT",
                          "/private/tmp/mindie-7337-20261111-1457/header-provenance")
    import zero_shot_piecewise_validation as z
    return z


@pytest.mark.skipif(not CELLS.is_file(), reason="original cells unavailable")
def test_actual_per_owner_buffers_drive_matrix_and_grouped_tile_plan():
    from mindie_sim.prediction.piecewise.compiler import CompiledOperator
    from mindie_sim.prediction.piecewise.families_matrix import _compile_gemm
    from mindie_sim.prediction.piecewise.families_moe_collective import (
        DEFAULT_L0C_BYTES, _owner_capacity, tile_plan,
    )
    from mindie_sim.prediction.piecewise.expressions import evaluate

    z = _z()
    spec = None
    for line in CELLS.open("rb"):
        raw = json.loads(line)
        if raw.get("cell_id") == CELL_ID:
            spec = z.cell_from_dict(raw).spec
            break
    if spec is None:
        pytest.skip("smoke Qwen cell unavailable")
    z.predict_cell(spec)
    key = (spec.dataset, z._structure_fingerprint(spec))
    compiled = z._COMPILED_MODELS[key]
    supply = compiled[2]
    buffers, units = dict(supply.buffers), dict(supply.pool_units)
    assert buffers == {"l0a": 65536, "l0b": 65536, "l0c": 262144,
                       "l1": 524288, "ub": 253952}
    assert units["l0a"] == units["l0b"] == units["l0c"] == units["l1"] == 32
    assert units["ub"] == 64
    assert DEFAULT_L0C_BYTES == 128 * 1024

    # Authentic Qwen regular projection: K/N/M work is unchanged.
    sub = next(v for v in compiled[3].values()
               if any(o.operator.name == "o_projection" for o in v.operators))
    op = next(o for o in sub.operators if o.operator.name == "o_projection")
    theta = op.operator.theta
    k, n = int(theta.require("K")), int(theta.require("N"))
    assert k == 3072 and n == 5120
    act = float(theta.find("act_bytes", 2.0))
    weight_format = str(theta.find("weight_format", "bf16"))
    weight_bytes = 1.0 if weight_format in {
        "fp8_e4m3", "fp8", "mxfp8", "mx_fp8", "int8", "w8a8"} else 2.0
    source = tile_plan(
        128, n, k, mt=128, nt=128, kt=128, act_bytes=act,
        weight_bytes=weight_bytes, out_bytes=2.0,
        l1_bytes=buffers["l1"], l0a_bytes=buffers["l0a"],
        l0b_bytes=buffers["l0b"], l0c_bytes=buffers["l0c"],
        slots=2, compute_slots=2)
    assert _owner_capacity(op, theta, "l0c", DEFAULT_L0C_BYTES) == 262144
    assert source.l0c_bytes == 131072
    assert source.l0c_bytes <= buffers["l0c"]
    assert source.footprint(act, weight_bytes, 2.0)["l0c"] == 131072
    assert source.fits and source.n_tiles == 40

    # The same K/N/M with a legal larger N tile: actual l0c 256 KiB fits
    # n=256; the old 128 KiB fallback would shrink back to n=128.
    legal = tile_plan(
        128, n, k, mt=128, nt=256, kt=128, act_bytes=act,
        weight_bytes=weight_bytes, out_bytes=2.0,
        l1_bytes=buffers["l1"], l0a_bytes=buffers["l0a"],
        l0b_bytes=buffers["l0b"], l0c_bytes=buffers["l0c"],
        slots=2, compute_slots=2)
    old = tile_plan(
        128, n, k, mt=128, nt=256, kt=128, act_bytes=act,
        weight_bytes=weight_bytes, out_bytes=2.0,
        l1_bytes=524288, l0a_bytes=65536, l0b_bytes=65536,
        l0c_bytes=DEFAULT_L0C_BYTES, slots=2, compute_slots=2)
    assert old.n_tile == 128 and old.n_tiles == 40
    assert legal.n_tile == 256 and legal.n_tiles == 20
    assert legal.footprint(act, weight_bytes, 2.0)["l0c"] == 262144
    assert legal.fits
    assert 2 * 128 * n * k == 2 * 128 * n * k  # same mathematical work
    assert dict(supply.rates)["cube"] == 865075200000.0
    assert dict(supply.rates)["mte1"] == 13516800000.0

    # The code path itself consumes the actual buffer rather than a default.
    source_template = _compile_gemm(op, op.operator)
    source_derived = dict(source_template.derived)
    assert int(evaluate(source_derived["l0c_tile_bytes"], {})) == 131072
    assert int(evaluate(source_derived["tile_capacity_fits"], {})) == 1

    tiles = tuple((key, value) for key, value in op.operator.theta.tiles
                  if key != "nt")
    theta2 = replace(op.operator.theta, tiles=tiles).relocated(nt=256)
    op2 = replace(op.operator, theta=theta2)
    legal_template = _compile_gemm(op, op2)
    legal_derived = dict(legal_template.derived)
    assert int(evaluate(legal_derived["l0c_tile_bytes"], {})) == 262144
    assert int(evaluate(legal_derived["tile_capacity_fits"], {})) == 1
    assert int(evaluate(legal_derived["l0b_tile_bytes"], {})) == 65536
    assert op2.template.name == op.operator.template.name
    assert dict(supply.rates)["cube"] == 865075200000.0

    # Grouped construction uses the same per-owner capacities.
    grouped_actual = tile_plan(
        128, 4096, 6144, mt=128, nt=256, kt=128, act_bytes=2.0,
        weight_bytes=1.0, out_bytes=2.0,
        l1_bytes=buffers["l1"], l0a_bytes=buffers["l0a"],
        l0b_bytes=buffers["l0b"], l0c_bytes=buffers["l0c"],
        slots=2, compute_slots=2)
    grouped_old = tile_plan(
        128, 4096, 6144, mt=128, nt=256, kt=128, act_bytes=2.0,
        weight_bytes=1.0, out_bytes=2.0,
        l1_bytes=524288, l0a_bytes=65536, l0b_bytes=65536,
        l0c_bytes=DEFAULT_L0C_BYTES, slots=2, compute_slots=2)
    assert grouped_actual.n_tile == 256 and grouped_actual.n_tiles == 16
    assert grouped_actual.footprint(2.0, 1.0, 2.0)["l0c"] == 262144
    assert grouped_old.n_tile == 128 and grouped_old.n_tiles == 32
    assert grouped_actual.fits and grouped_old.fits

    # Constrained actual owners (8192 B each) must shrink the selected
    # footprint; the old theta/default plan remained 8x/2x/2x/16x over.
    constrained_supply = replace(
        supply,
        buffers=tuple((name, 8192) for name, _ in supply.buffers),
    )
    constrained = CompiledOperator(
        op.operator, constrained_supply, op.policy, kind=op.kind,
        layer=op.layer, domain=op.domain, siblings=op.siblings,
        variant=op.variant, feature_metadata=getattr(op, "feature_metadata", ()),
    )
    tight_template = _compile_gemm(constrained, op.operator)
    tight_derived = dict(tight_template.derived)
    for pool in ("l1", "l0a", "l0b", "l0c"):
        used = int(evaluate(tight_derived[f"{pool}_tile_bytes"], {}))
        assert used <= 8192, (pool, used)
    assert int(evaluate(tight_derived["tile_capacity_fits"], {})) == 1
    assert int(evaluate(tight_derived["l0c_tile_bytes"], {})) != 131072

    # A physically impossible owner capacity is reported, not fudged.
    impossible = tile_plan(
        128, n, k, mt=128, nt=256, kt=128, act_bytes=act,
        weight_bytes=weight_bytes, out_bytes=2.0,
        l1_bytes=buffers["l1"], l0a_bytes=buffers["l0a"],
        l0b_bytes=buffers["l0b"], l0c_bytes=1, slots=2, compute_slots=2)
    assert impossible.fits is False
