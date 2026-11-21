"""Round-1 P0/P1 review closure for the retained A5 clean-core physics core.

Each test pins one exact finding from the Round-1 review: removed SLA symbols,
timeout propagation, descriptor/lowering gaps, source-binding honesty, batched
GEMM geometry, directional transfer bytes, exact ABI agreement, cell workload
conversion, evidence path normalization and pinned-source resolution.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from mindie_profiler import native_abi_model as abi
from mindie_profiler.native_abi_model import _gemm_geometry, build_plan
from mindie_profiler.sim_bridge_predict import _binding_state, _canonical_result

ROOT = Path(__file__).resolve().parents[1]
STRUCT = ROOT / "examples" / "structure"


def _tensor(shape, dtype, role):
    return {"shape": list(shape), "dtype": dtype, "layout": "ND", "role": role}


def _invocation(x1, x2, out, *, attrs=None, version=None, entry="aclnnMatmul"):
    return {
        "api": {"namespace": "aclnn", "entry": entry, "aclnn_symbol": entry},
        "version": dict(version or {}),
        "tensors": {"x1": _tensor(x1, "bf16", "input"),
                    "x2": _tensor(x2, "bf16", "weight"),
                    "out": _tensor(out, "bf16", "output")},
        "attrs": dict(attrs or {}),
    }


def _plan(x1, x2, out, *, attrs=None, version=None):
    pytest.importorskip("mindie_sim")
    plan, gap = build_plan(_invocation(x1, x2, out, attrs=attrs, version=version))
    assert gap is None, gap
    return plan


# --------------------------------------------------------------- finding 1
def test_efficiency_report_uses_the_retained_sla_sizing_symbol():
    source = (STRUCT / "efficiency_report.py").read_text(encoding="utf-8")
    assert "solve_hardware_sla_throughput" not in source
    assert "sweep_topology_grid" not in source
    assert "fit_efficiency_targets" not in source
    assert "solve_sla_sizing" in source

    pytest.importorskip("mindie_sim")
    sys.path.insert(0, str(STRUCT))
    try:
        module = importlib.import_module("efficiency_report")
        assert callable(module.analyze_network_efficiency)
        assert callable(module.solve_sla_sizing)
    finally:
        sys.path.remove(str(STRUCT))
        sys.modules.pop("efficiency_report", None)


# --------------------------------------------------------------- finding 2
def test_load_json_propagates_a_deadline(monkeypatch):
    sys.path.insert(0, str(STRUCT))
    try:
        module = importlib.import_module("zero_shot_source_binding")
    finally:
        sys.path.remove(str(STRUCT))
        sys.modules.pop("zero_shot_source_binding", None)

    def _deadline(self, *args, **kwargs):
        raise TimeoutError("deadline exceeded")

    monkeypatch.setattr(Path, "read_text", _deadline)
    with pytest.raises(TimeoutError):
        module._load_json("unused.json")


# --------------------------------------------------------------- finding 3
@pytest.mark.parametrize("tensor", [
    {"dtype": "bf16", "role": "weight"},
    {"shape": [4, 8], "dtype": "not_a_dtype", "role": "weight"},
])
def test_incomplete_tensor_descriptors_never_become_zero_work(tensor):
    pytest.importorskip("mindie_sim")
    invocation = _invocation([2, 4], [4, 8], [2, 8])
    invocation["tensors"]["x2"] = tensor
    plan, reason = build_plan(invocation)
    assert plan is None
    assert reason.startswith("t12_invocation_unavailable:tensor_descriptor_incomplete:")


def test_missing_descriptor_does_not_construct_an_opspec(monkeypatch):
    pytest.importorskip("mindie_sim")
    invocation = _invocation([2, 4], [4, 8], [2, 8])
    invocation["tensors"]["x1"] = {"role": "input", "dtype": "bf16", "layout": "ND"}

    def _forbidden(**_kwargs):
        pytest.fail("OpSpec constructed for an incomplete descriptor")

    monkeypatch.setattr(abi, "_op_spec", _forbidden)
    plan, reason = build_plan(invocation)
    assert plan is None
    assert reason.endswith("tensor_descriptor_incomplete:inputs:x1")


def test_incomplete_gemm_geometry_is_an_explicit_gap():
    pytest.importorskip("mindie_sim")
    plan, reason = build_plan(_invocation([2, 4], [4, 9], [2, 8]))
    assert plan is None
    assert reason == "t12_invocation_unavailable:gemm_geometry_incomplete"


# --------------------------------------------------------------- finding 4
def test_version_label_is_never_a_source_binding():
    plan = _plan([2, 4], [4, 8], [2, 8], version={
        "source": "caller-label",
        "image_id": "sha256:9e869e8148467296f56d1001b0dac4fea893c841ac7d0a03d4e824a233c2ffea",
    })
    assert _binding_state(plan) == (False, None)
    payload = _canonical_result(plan, None, duration=None, execute=False).to_dict()
    assert payload["binding_bound"] is False
    assert payload["binding"]["typed"]["source"] is None
    assert payload["invocation"]["version"] == {
        "source": "caller-label",
        "image_id": "sha256:9e869e8148467296f56d1001b0dac4fea893c841ac7d0a03d4e824a233c2ffea",
    }
    assert "attributable_source_reference_unresolved" in payload["binding"]["unresolved"]


# --------------------------------------------------------------- finding 5
def test_batched_gemm_keeps_every_leading_dimension():
    tensors = {
        "x1": _tensor([2, 4, 8], "bf16", "input"),
        "x2": _tensor([2, 8, 16], "bf16", "weight"),
        "out": _tensor([2, 4, 16], "bf16", "output"),
    }
    assert _gemm_geometry(tensors, {}) == (8, 8, 16)  # 2*4*8*16 = 1024 MACs
    assert 2 * 4 * 8 * 16 == 1024


def test_gemm_broadcasts_leading_batches_and_applies_transposes():
    broadcast = {
        "x1": _tensor([2, 1, 4, 8], "bf16", "input"),
        "x2": _tensor([1, 3, 8, 16], "bf16", "weight"),
        "out": _tensor([2, 3, 4, 16], "bf16", "output"),
    }
    assert _gemm_geometry(broadcast, {}) == (24, 8, 16)

    transposed = {
        "x1": _tensor([2, 8, 4], "bf16", "input"),
        "x2": _tensor([2, 16, 8], "bf16", "weight"),
        "out": _tensor([2, 4, 16], "bf16", "output"),
    }
    attrs = {"transpose_x1": True, "transpose_x2": True}
    assert _gemm_geometry(transposed, attrs) == (8, 8, 16)


def test_weight_scale_name_does_not_shadow_the_matrix_operand():
    tensors = {
        "x1": _tensor([2, 4, 8], "bf16", "input"),
        "x2": _tensor([2, 8, 16], "bf16", "weight"),
        "weight_scale": _tensor([64, 16, 2], "bf16", "scale"),
        "out": _tensor([2, 4, 16], "bf16", "output"),
    }
    assert _gemm_geometry(tensors, {}) == (8, 8, 16)


# --------------------------------------------------------------- finding 6
@pytest.mark.parametrize("dtype,width", [
    ("int8", 1), ("fp8_e4m3", 1), ("bf16", 2),
])
def test_matrix_flops_and_transfer_bytes_use_the_real_operand_format(dtype, width):
    plan = _plan_with_dtype(dtype)
    op = plan.ops[0]
    macs = 1 * 4 * 8
    assert op.matrix_flops == ((dtype, 2.0 * macs),)
    assert op.flops == sum(value for _, value in op.matrix_flops)
    assert op.mte2_bytes == float(4 * width + 4 * 8 * width)
    assert op.mte3_bytes == float(1 * 8 * 2)


def _plan_with_dtype(dtype):
    pytest.importorskip("mindie_sim")
    invocation = {
        "api": {"namespace": "aclnn", "entry": "aclnnMatmul",
                "aclnn_symbol": "aclnnMatmul"},
        "version": {},
        "tensors": {"x1": _tensor([1, 4], dtype, "input"),
                    "x2": _tensor([4, 8], dtype, "weight"),
                    "out": _tensor([1, 8], "bf16", "output")},
        "attrs": {},
    }
    plan, gap = build_plan(invocation)
    assert gap is None, gap
    return plan


def test_packed_widths_round_up_per_slot():
    assert abi._slot_bytes({"shape": [3], "dtype": "uint4"}) == 2   # ceil(1.5)
    assert abi._slot_bytes({"shape": [3], "dtype": "int4"}) == 2
    assert abi._slot_bytes({"shape": [3], "dtype": "fp4_e2m1"}) == 2
    assert abi._slot_bytes({"shape": [3], "dtype": "uint1"}) == 1   # ceil(0.375)
    assert abi._slot_bytes({"shape": [2], "dtype": "uint1"}) == 1   # ceil(0.25)


def test_unresolved_compute_format_is_a_gap_not_bf16():
    pytest.importorskip("mindie_sim")
    plan, reason = build_plan(_plan_input("uint4"))
    assert plan is None
    assert reason == "t12_invocation_unavailable:gemm_compute_dtype_unresolved"


def _plan_input(dtype):
    return {
        "api": {"namespace": "aclnn", "entry": "aclnnMatmul",
                "aclnn_symbol": "aclnnMatmul"},
        "version": {},
        "tensors": {"x1": _tensor([1, 4], dtype, "input"),
                    "x2": _tensor([4, 8], dtype, "weight"),
                    "out": _tensor([1, 8], "bf16", "output")},
        "attrs": {},
    }


# --------------------------------------------------------------- finding 7
def test_non_matrix_entries_stay_explicit_lowering_gaps():
    pytest.importorskip("mindie_sim")
    invocation = {
        "api": {"namespace": "aclnn", "entry": "aclnnAddRmsNorm",
                "aclnn_symbol": "aclnnAddRmsNorm"},
        "version": {},
        "tensors": {
            "x1": _tensor([2, 4], "bf16", "input"),
            "x2": _tensor([2, 4], "bf16", "input"),
            "gamma": _tensor([4], "bf16", "weight"),
            "y": _tensor([2, 4], "bf16", "output"),
            "rstd": _tensor([2, 1], "fp32", "output"),
            "x_out": _tensor([2, 4], "bf16", "output"),
        },
        "attrs": {},
    }
    plan, reason = build_plan(invocation)
    assert plan is None
    assert reason == ("t12_invocation_unavailable:canonical_lowering_missing:"
                      "aclnnAddRmsNorm")


def test_attention_geometry_gets_no_invented_vector_work():
    pytest.importorskip("mindie_sim")
    from mindie_profiler.op_api_registry import catalog_operator

    name = "aclnnFusedInferAttentionScoreV3"
    report = catalog_operator(name)
    assert report is not None
    specs = report["entry"]["c_abi_slots"]["slot_specs"]
    tensors = {}
    for direction in ("inputs", "outputs"):
        role = "output" if direction == "outputs" else "input"
        for spec in specs[direction]:
            tensors[str(spec["name"])] = _tensor([16, 8, 128], "bf16", role)
    plan, reason = build_plan({
        "api": {"namespace": "aclnn", "entry": name, "aclnn_symbol": name},
        "version": {}, "tensors": tensors, "attrs": {},
    })
    assert plan is None
    assert reason == (
        "t12_invocation_unavailable:canonical_lowering_missing:" + name)


# --------------------------------------------------------------- finding 8
def _request_for(plan, *, request_abi):
    return {
        "request_id": "req:abi",
        "t12_invocation": {
            "api": dict(plan.api), "version": dict(plan.version),
            "tensors": {name: dict(tensor) for name, tensor in plan.tensors.items()},
            "attrs": dict(plan.attrs), "conditions": dict(plan.conditions),
        },
        "abi": request_abi,
    }


def _actual_abi(plan):
    from mindie_profiler.native_tensor_abi import native_abi_from_slots
    inputs, outputs = plan.abi_slots()
    return native_abi_from_slots(plan.operator, inputs, outputs)


def test_equal_element_counts_do_not_certify_a_different_abi():
    pytest.importorskip("mindie_sim")
    from mindie_profiler.sim_bridge import predict_native_requests

    plan = _plan([2, 4, 8], [2, 8, 16], [2, 4, 16])
    actual = _actual_abi(plan)
    exact = predict_native_requests(
        [_request_for(plan, request_abi=dict(actual))],
        hardware="Ascend950DT_9582", phase="decode")["predictions"][0]
    assert exact["status"] == "modeled"
    assert exact["eligibility"]["capture_pairing"] is True
    assert exact["abi"]["digest"] == actual["digest"]

    from mindie_profiler.native_tensor_abi import native_abi_from_slots
    substituted = native_abi_from_slots(
        plan.operator,
        [
            {"shape": [8, 2, 4], "dtype": "bf16", "layout": "ND"},
            {"shape": [8, 4, 8], "dtype": "bf16", "layout": "ND"},
        ],
        [{"shape": [8, 2, 8], "dtype": "bf16", "layout": "ND"}],
    )
    assert substituted["verified"] is True
    assert substituted["digest"] != actual["digest"]
    mismatch = predict_native_requests(
        [_request_for(plan, request_abi=substituted)],
        hardware="Ascend950DT_9582", phase="decode")["predictions"][0]
    assert mismatch["status"] == "modeled"
    assert mismatch["eligibility"]["capture_pairing"] is False
    assert mismatch["abi"]["digest"] == actual["digest"]


# --------------------------------------------------------------- finding 9
def test_raw_case_for_cell_applies_workload_and_parallel_axes(tmp_path):
    from mindie_profiler.sim_bridge_cells import CellSpec, raw_case_for_cell

    template = {
        "runtime": {"parallel": {"tp": 8, "dp": 1, "ep": 1, "pp": 1},
                    "max_num_seqs": 1},
        "workload": {"num_requests": 1, "prompt_tokens": 8, "output_tokens": 1},
    }
    case = tmp_path / "template.json"
    case.write_text(json.dumps(template), encoding="utf-8")
    spec = CellSpec(model_case=case, concurrency=16, prompt_tokens=65536,
                    max_tokens=8, tp=2, dp=4, ep=8, pp=1,
                    graph_buckets=(1, 2, 4))
    raw = raw_case_for_cell(spec)
    assert raw["runtime"]["parallel"] == {"tp": 2, "dp": 4, "ep": 8, "pp": 1}
    assert raw["runtime"]["graph_buckets"] == [1, 2, 4]
    assert raw["workload"] == {
        "num_requests": 16, "prompt_tokens": 65536, "output_tokens": 8,
        "arrival_interval_ms": 0, "synthetic": True,
    }


# --------------------------------------------------------------- finding 10
def test_tracked_evidence_has_no_developer_local_path():
    forbidden = ("/" + "Volumes/", "/" + "Users/")
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "data/observations"], cwd=ROOT,
        capture_output=True, text=True)
    if tracked.returncode != 0:
        pytest.skip("git checkout unavailable")
    for name in filter(None, tracked.stdout.split("\0")):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in forbidden), path

    document = json.loads((
        ROOT / "data/observations/sources/arch22-physical-services"
        / "grouped-source-constraints.json").read_text(encoding="utf-8"))
    identity = document["producer_identity"]
    assert identity["repository"] == "mindie-agent/profiler"
    assert identity["relative_path"] == "examples/structure/summarize_grouped_micro_services.py"
    assert identity["source_sha256"] == identity["sha256"]
    assert "path" not in identity
    source = document["records"][0]["source_identity"]
    assert source["path"].startswith("capture://mindie-sim-data/")
    assert document["path_normalization"]["schema"] == "mindie-path-normalization/1"


def test_repository_has_no_tracked_developer_paths():
    pattern = "|".join(("/" + "Volumes/", "/" + "Users/"))
    result = subprocess.run(
        ["git", "grep", "-l", "-E", pattern], cwd=ROOT,
        capture_output=True, text=True)
    if result.returncode not in (0, 1):
        pytest.skip("git checkout unavailable")
    assert result.stdout.strip() == ""


# --------------------------------------------------------------- finding 11
def test_pinned_source_path_requires_an_enrolled_checkout(tmp_path, monkeypatch):
    import test_op_abi_repro as repro

    source = {"repo": "vllm-ascend", "rel_path": "csrc/example.h",
              "path": "repository://vllm-ascend/csrc/example.h"}
    (tmp_path / "csrc").mkdir()
    pinned = tmp_path / "csrc" / "example.h"
    pinned.write_text("// pinned\n", encoding="utf-8")

    monkeypatch.setenv("MINDIE_ABI_SOURCE_ROOTS",
                       json.dumps({"vllm-ascend": str(tmp_path)}))
    assert repro._pinned_source_path(source) == pinned

    source_missing = {**source, "rel_path": "csrc/absent.h"}
    with pytest.raises(AssertionError, match="pinned source missing"):
        repro._pinned_source_path(source_missing)

    monkeypatch.setenv("MINDIE_ABI_SOURCE_ROOTS", "{}")
    with pytest.raises(pytest.skip.Exception):
        repro._pinned_source_path(source)


# ------------------------------------------------------------ Round-2 P1 #1
def _structure_module(monkeypatch, name):
    monkeypatch.syspath_prepend(str(STRUCT))
    return importlib.import_module(name)


def test_localize_evidence_resolves_capture_and_repository_uris(
        monkeypatch, tmp_path):
    capture = tmp_path / "captures"
    workstreams = tmp_path / "workstreams"
    monkeypatch.setenv("MINDIE_SIM_DATA_ROOT", str(capture))
    monkeypatch.setenv("MINDIE_WORKSTREAM_ROOT", str(workstreams))
    evidence_roots = _structure_module(monkeypatch, "evidence_roots")

    capture_uri = "capture://mindie-sim-data/a3/heldout/kernel_details.csv"
    capture_path = capture / "a3" / "heldout" / "kernel_details.csv"
    repository_uri = (
        "repository://mindie-agent/profiler/examples/structure/cases.json")
    repository_path = STRUCT / "cases.json"
    workstream_uri = "repository://mindie-agent/.workstreams/runs/run.json"
    workstream_path = workstreams / "runs" / "run.json"

    assert evidence_roots.localize_evidence(capture_uri) == str(
        capture_path.resolve())
    assert evidence_roots.localize_evidence(
        "capture:/mindie-sim-data/a3/heldout/kernel_details.csv") == str(
            capture_path.resolve())
    assert evidence_roots.localize_evidence(repository_uri) == str(
        repository_path.resolve())
    assert evidence_roots.localize_evidence(workstream_uri) == str(
        workstream_path.resolve())
    assert evidence_roots.localize_evidence("relative/case.json") == (
        "relative/case.json")
    assert evidence_roots.localize_evidence(42) == 42

    localized = evidence_roots.localize_evidence(
        {"sources": [capture_uri], "pins": (repository_uri,)})
    assert localized == {
        "sources": [str(capture_path.resolve())],
        "pins": (str(repository_path.resolve()),),
    }
    override = evidence_roots.localize_evidence(
        capture_uri, capture_base=tmp_path / "override")
    assert override == str(
        (tmp_path / "override/a3/heldout/kernel_details.csv").resolve())


def test_localize_evidence_restores_registered_dsh_classification(
        monkeypatch, tmp_path):
    pytest.importorskip("mindie_sim")
    capture = tmp_path / "captures"
    monkeypatch.setenv("MINDIE_SIM_DATA_ROOT", str(capture))
    evidence_roots = _structure_module(monkeypatch, "evidence_roots")
    dsh = _structure_module(monkeypatch, "dsh_generalization_eval")

    cases = evidence_roots.localize_evidence(
        json.loads((STRUCT / "cases.json").read_text()))["cases"]
    reg_by_path = {
        Path(case["source"]["path"]).resolve(): case
        for case in cases
        if case.get("source", {}).get("path")
        and case.get("supported_scopes") != ["engine"]
    }
    for case_id in (
        "decode:a3_glm53flash_heldout_c12_p4k",
        "decode:a5_glm53flash_heldout_c12_p4k",
    ):
        case = next(item for item in cases if item["id"] == case_id)
        source = Path(case["source"]["path"]).resolve()
        assert source.is_relative_to(capture.resolve())
        assert dsh.inventory_capture(source, reg_by_path) == (
            "registered", None)


# ------------------------------------------------------------ Round-2 P1 #2
def test_raw_case_re_raises_the_original_timeout(monkeypatch, tmp_path):
    consumer = _structure_module(monkeypatch, "zero_shot_public_consumer")
    cells = importlib.import_module("mindie_profiler.sim_bridge_cells")
    case = tmp_path / "case.json"
    case.write_text("{}", encoding="utf-8")
    spec = SimpleNamespace(model_case=case)
    deadline = TimeoutError("deadline exceeded")

    def _deadline(_spec):
        raise deadline

    monkeypatch.setattr(cells, "raw_case_for_cell", _deadline)
    with pytest.raises(TimeoutError) as caught:
        consumer._raw_case(spec)
    assert caught.value is deadline

    def _invalid(_spec):
        raise ValueError("invalid template")

    monkeypatch.setattr(cells, "raw_case_for_cell", _invalid)
    assert consumer._raw_case(spec) == {}
