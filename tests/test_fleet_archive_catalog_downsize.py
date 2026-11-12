"""Catalog downsize uses the canonical model, then declared depth and experts.

A template catalog_key is not a license to keep another architecture's hidden
size. Matching launch matrices materialize the catalog base. A disagreeing
width and a kernel with no matrix widths stay different refusals.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_STRUCTURE = ROOT / "examples" / "structure"
if str(_STRUCTURE) not in sys.path:
    sys.path.insert(0, str(_STRUCTURE))

import fleet_archive_case as archive  # noqa: E402
from fleet_operator_archive_engine import OrderedBodyEvaluator, _close_compiled_downsize  # noqa: E402
from test_fleet_archive_case import _sha, _write  # noqa: E402


def _kernel(rows: list[tuple[str, str, str]]) -> str:
    lines = ["Name,Input Shapes,Output Shapes"]
    for name, inputs, outputs in rows:
        lines.append(f'{name},"{inputs}","{outputs}"')
    return "\n".join(lines) + "\n"


def _matching_rows() -> list[tuple[str, str, str]]:
    return [
        ("aclnnMatmul", "8,2048;16,2048", "8,16"),
        ("aclnnMatmul", "8,1024;2048,1024", "8,2048"),
        ("aclnnMatmul", "8,128;2048,128", "8,2048"),
        ("aclnnMoeGatingTopK", "2,16", "2,2;2,2;2,16"),
        ("aclnnMoeTokenPermute", "2,2048;2,2", "4,2048;4;;"),
        ("aclnnGroupedMatmulWeightNz", "4,512;4,64,32,16,32;;4,2048;;;;4;4", "4,2048"),
    ]


def _layout(tmp_path: Path, rows: list[tuple[str, str, str]], *, hidden: int | None = None, experts: int = 16, top_k: int = 2, dequant_rows: int | None = None, graph_mode: str | None = None, kernel_text: str | None = None):
    cell = f"synth_qwen35_L8_E{experts}_K{top_k}_tp4ep4_prefill_4k_c1"
    source = tmp_path / "data" / "a5" / "heldout_engine_20261031" / cell / "kernel_details.csv"
    source.parent.mkdir(parents=True)
    source.write_text(kernel_text if kernel_text is not None else _kernel(rows), encoding="utf-8")
    cases = tmp_path / "cases"
    runtime = {"tp": 4, "dp": 1, "ep": 4, "pp": 1}
    if dequant_rows is not None:
        runtime["kernels"] = {"lowerings": {"grouped_int8_caller": {
            "implementation": "ascend_grouped_int32_dequant_swiglu",
            "options": {"dequant_program": "arch35_full_load", "input_capacity_rows": dequant_rows},
        }}}
    _write(cases / "catalog-qwen35.json", {
        "name": "catalog-template",
        "machine": {"backend": "ascend", "sku": "Ascend910B4", "num_devices": 4, "ranks_per_node": 4},
        "model": {"catalog_key": "qwen3.5-35b-a3b", "quantization": "w8a8_dynamic"},
        "runtime": runtime,
        "workload": {"num_requests": 1, "prompt_tokens": 8, "output_tokens": 1},
    })
    if graph_mode is not None:
        (source.parent / "cmd.sh").write_text(
            "vllm serve model --tensor-parallel-size 4 --data-parallel-size 1 "
            f"--compilation-config '{{\"cudagraph_mode\":\"{graph_mode}\"}}'\n",
            encoding="utf-8",
        )
    declaration = {"name": "qwen3.5-35b-a3b", "layers": 8, "tp": 4}
    if hidden is not None:
        declaration["hidden_size"] = hidden
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    _write(receipt, {
        "cache_version": "v-test", "parser_identity": "parser-test",
        "observed": {
            "phase": "prefill",
            "source_identity": {"path": str(source), "sha256": _sha(source), "size_bytes": source.stat().st_size},
            "model_declaration": declaration,
            "geometry_groups": [{
                "geometry": {"query_rows": 8, "sequences_per_replica": 1, "tokens_per_sequence": 8,
                             "context_tokens": None, "context_basis": "not_observed_from_cache_capacity"},
                "rank_id": "", "device_id": "4", "forward_ids": ["prefill:0"],
            }],
        },
    })
    cohort = "a5/synth_qwen35_prefill"
    record = {
        "path": str(source), "hw": "a2", "cohort": cohort, "cell": cell, "family": "synth-qwen3.5-35b-a3b",
        "phase": "prefill", "tp": 4, "dp": 1, "ep": 4, "num_layers": 8, "num_experts": experts,
        "top_k": top_k, "template": "catalog-qwen35.json",
    }
    results = tmp_path / "results"
    _write(results / "wave5_full_generalization.json", {
        "schema_version": "mindie-wave5-full-generalization/1",
        "sim_identity": "mindie_sim/test", "parser_identity": "mindie_profiler/test",
        "chip_report_identities": {"a2": {"schema_version": "chip", "sim_identity": "mindie_sim/test", "parser_identity": "mindie_profiler/test"}},
        "cohort_summaries": [{"cohort": cohort, "calibration_provenance": {"evaluation_relation": "in_sample_regime_calibration"}}],
        "cases": [record],
    })
    _write(results / "dsh_full_generalization.json", {"schema_version": "mindie-dsh-full-generalization/2", "heldout_cases": []})
    index = tmp_path / "receipts.tsv"
    index.write_text(f"source_path\treceipt\n{source}\t{receipt}\n", encoding="utf-8")
    archive.configure_archive_roots(
        data_roots=(tmp_path / "data",), results_dir=results, cases_dir=cases,
        archive_root=tmp_path / "missing-archive", receipt_index=index, cases_index=tmp_path / "no-cases.json",
    )
    return {
        "suite": "wave5_20261031",
        "capture_id": f"wave5:a2:{cohort}:{cell}",
        "phase": "prefill",
        "hardware_tier": "A2",
    }


def test_matching_matrices_materialize_catalog_base_before_declared_deltas(tmp_path: Path):
    row = _layout(tmp_path, _matching_rows())
    result = archive.resolve_archive_case(row)
    assert result["status"] == "resolved"
    model = result["case"]["model"]
    assert "catalog_key" not in model
    assert "model_catalog_key" not in model
    assert model["layers"] == 8
    assert model["hidden_size"] == 2048
    assert model["num_heads"] == 16
    assert model["head_dim"] == 256
    assert model["num_experts"] == 16
    assert model["top_k"] == 2
    assert model["moe_intermediate_size"] == 512
    assert len(model["layer_plans"]) == 8
    assert model["metadata"]["architectural_basis"] == "catalog_base_then_declared_downsize"
    assert model["metadata"]["catalog_key"] == "qwen3.5-35b-a3b"
    assert model["metadata"]["source_match"] == "launch_matrices"
    assert model["metadata"]["not_full_catalog_experts"] is True
    assert model["metadata"]["source_sku"] == result["case"]["machine"]["sku"]
    attentions = [plan["attention"] for plan in model["layer_plans"]]
    assert attentions.count("gqa") == 2
    assert attentions.count("gdn") == 6
    assert all(plan["num_experts"] == 16 and plan["top_k"] == 2 for plan in model["layer_plans"])
    payload = json.loads(json.dumps(result["case"]))
    payload["workload"] = {"num_requests": 1, "prompt_tokens": 8, "output_tokens": 1}
    from mindie_sim.prediction.structure import parse_case

    parsed = parse_case(payload)
    assert parsed.model.hidden_size == 2048
    assert parsed.model.layers == 8
    assert parsed.model.num_experts == 16
    assert _close_compiled_downsize(parsed, payload) == []


def test_matrix_hidden_disagreement_does_not_inherit_catalog_width(tmp_path: Path):
    rows = [
        ("aclnnMatmul", "8,4096;16,4096", "8,16"),
        ("aclnnMatmul", "8,1024;4096,1024", "8,4096"),
        ("aclnnMatmul", "8,128;4096,128", "8,4096"),
        ("aclnnMoeGatingTopK", "2,16", "2,2"),
        ("aclnnMoeTokenPermute", "2,4096;2,2", "4,4096"),
        ("aclnnGroupedMatmulWeightNz", "4,512;4,64;;4,4096", "4,4096"),
    ]
    result = archive.resolve_archive_case(_layout(tmp_path, rows))
    assert result["case"] is None
    assert any(item.startswith("catalog_width_disagrees_with_launch_matrices:hidden") for item in result["diagnostics"])
    assert "launch_matrix_widths_absent" not in result["diagnostics"]


def test_absent_matrices_do_not_inherit_catalog_widths(tmp_path: Path):
    result = archive.resolve_archive_case(_layout(tmp_path, [("Add", "8", "8")]))
    assert result["case"] is None
    assert "launch_matrix_widths_absent" in result["diagnostics"]
    assert not any("catalog_width_disagrees" in item for item in result["diagnostics"])


def test_declared_hidden_disagreement_is_not_overridden_by_matrices(tmp_path: Path):
    result = archive.resolve_archive_case(_layout(tmp_path, _matching_rows(), hidden=4096))
    assert result["case"] is None
    assert "hidden_size_disagrees:receipt=4096:catalog=2048" in result["diagnostics"]
    assert not any(item.startswith("catalog_width_disagrees_with_launch_matrices") for item in result["diagnostics"])


def test_gating_output_is_topk_when_permute_is_absent(tmp_path: Path):
    rows = [row for row in _matching_rows() if "Permute" not in row[0]]
    result = archive.resolve_archive_case(_layout(tmp_path, rows))
    model = result["case"]["model"]
    assert result["status"] == "resolved"
    assert model["top_k"] == 2
    assert model["num_experts"] == 16
    assert model["metadata"]["source_match"] == "launch_matrices"
    assert "launch_matrix_widths_absent" not in result["diagnostics"]


def test_routed_axis_must_match_the_declaration_not_the_catalog(tmp_path: Path):
    rows = _matching_rows()
    rows[3] = ("aclnnMoeGatingTopK", "2,256", "2,2;2,2;2,256")
    result = archive.resolve_archive_case(_layout(tmp_path, rows))
    assert result["case"] is None
    assert any(item.startswith("launch_routed_dims_disagree_with_declaration:experts:witness=256:declared=16") for item in result["diagnostics"])


def _caller(result: dict):
    return (
        ((result.get("case") or {}).get("runtime") or {}).get("kernels", {}).get("lowerings", {}).get("grouped_int8_caller")
    )


def _typed_line(stream: str, name: str, inputs: str, in_dtypes: str, outputs: str, out_dtypes: str, device: str = "4") -> str:
    return f'{device},{stream},{name},"{inputs}",{in_dtypes},"{outputs}",{out_dtypes}'


def _unfused_chain(stream: str, rows: int, *, hidden: int = 2048, intermediate: int = 512) -> list[str]:
    """INT8/INT8 gate returns BF16, then BF16 SwiGLU, DynamicQuantV2, BF16 down."""
    gate_n = intermediate * 2
    dtypes = "INT8;INT8;INT32;DT_BF16;FLOAT;FLOAT16;FLOAT16;INT64;FLOAT"
    return [
        _typed_line(stream, "aclnnGroupedMatmulWeightNz", f"{rows},{hidden};4,32;;;4,{gate_n};;;4;{rows}", dtypes, f"{rows},{gate_n}", "DT_BF16"),
        _typed_line(stream, "aclnnSwiGlu", f"{rows},{gate_n}", "DT_BF16", f"{rows},{intermediate}", "DT_BF16"),
        _typed_line(stream, "aclnnDynamicQuantV2", f"{rows},{intermediate}", "DT_BF16", f"{rows},{intermediate};{rows};{rows}", "INT8;FLOAT;FLOAT"),
        _typed_line(stream, "aclnnGroupedMatmulWeightNz", f"{rows},{intermediate};4,64;;;4,{hidden};;;4;{rows}", dtypes, f"{rows},{hidden}", "DT_BF16"),
    ]


def _typed_kernel(extra: list[str] | None = None) -> str:
    width = [
        _typed_line("1", "aclnnMatmul", "8,2048;16,2048", "DT_BF16;DT_BF16", "8,16", "DT_BF16"),
        _typed_line("1", "aclnnMatmul", "8,1024;2048,1024", "DT_BF16;DT_BF16", "8,2048", "DT_BF16"),
        _typed_line("1", "aclnnMatmul", "8,128;2048,128", "DT_BF16;DT_BF16", "8,2048", "DT_BF16"),
        _typed_line("1", "aclnnMoeGatingTopK", "2,16", "DT_BF16", "2,2;2,2;2,16", "DT_BF16;INT32;DT_BF16"),
        _typed_line("1", "aclnnMoeTokenPermute", "2,2048;2,2", "DT_BF16;INT32", "4,2048;4;;", "DT_BF16;INT32"),
        _typed_line("1", "aclnnGroupedMatmulWeightNz", "4,512;4,64;;;4,2048;;;4;4", "INT8;INT8;INT32;DT_BF16;FLOAT", "4,2048", "DT_BF16"),
    ]
    lines = ["Device_id,Stream ID,Name,Input Shapes,Input Data Types,Output Shapes,Output Data Types"]
    lines.extend(width)
    lines.extend(_unfused_chain("59", 4))
    lines.extend(_unfused_chain("59", 8))
    lines.extend(extra or [])
    return "\n".join(lines) + "\n"


def test_shape_only_kernel_does_not_rewrite_the_template_caller(tmp_path: Path):
    result = archive.resolve_archive_case(_layout(
        tmp_path, _matching_rows(), dequant_rows=128, graph_mode="FULL_DECODE_ONLY",
    ))
    assert result["status"] == "resolved", result["diagnostics"]
    caller = _caller(result)
    assert caller["implementation"] == "ascend_grouped_int32_dequant_swiglu"
    assert caller["options"]["input_capacity_rows"] == 128
    assert not any("valid_rows" in str(item) for item in result["diagnostics"])
    assert "typed_expert_chain" not in result["case"]["model"]["metadata"]


def test_witnessed_bf16_chain_binds_gemm_op_without_using_graph_mode_or_capacity(tmp_path: Path):
    result = archive.resolve_archive_case(_layout(
        tmp_path, _matching_rows(), dequant_rows=128, kernel_text=_typed_kernel(),
    ))
    assert result["status"] == "resolved", result["diagnostics"]
    assert _caller(result) is None
    chain = result["case"]["model"]["metadata"]["typed_expert_chain"]
    assert chain["bound_implementation"] == "gemm_op"
    assert chain["matrix_output_contract"] == "int32_cast_row_scale_column_scale_output_cast"
    assert chain["swiglu"] == "bf16"
    assert chain["activation_quant"] == "DynamicQuantV2"
    assert chain["down_returned_rows"] == [4, 8]
    assert chain["down_read_rows"] == [4, 8]
    assert "DT_BF16" in chain["down_scale_dtypes"]
    assert chain["int32_dequant_graph"] is False
    assert chain["gates"] == 2 and chain["downs"] == 2
    replaced = result["provenance"]["launch_replaced_template_fields"]
    assert any(item.get("reason") == "witnessed_unfused_int8_bf16_gmm_not_int32_dequant" for item in replaced)
    assert not any(item.get("policy") == "valid_rows" for item in replaced)
    assert any(str(item).startswith("typed_expert_chain:int8_bf16_w8_gmm_swiglu_dynamic_quant:down_rows=4,8") for item in result["diagnostics"])
    assert result["case"]["runtime"].get("graph_capture_mode") is None


def test_full_decode_only_alone_does_not_select_the_unfused_caller(tmp_path: Path):
    result = archive.resolve_archive_case(_layout(
        tmp_path, _matching_rows(), dequant_rows=128, graph_mode="FULL_DECODE_ONLY", kernel_text=_typed_kernel(),
    ))
    assert result["status"] == "resolved", result["diagnostics"]
    assert _caller(result) is None
    assert result["case"]["runtime"]["graph_capture_mode"] == "FULL_DECODE_ONLY"
    assert result["case"]["model"]["metadata"]["typed_expert_chain"]["down_returned_rows"] == [4, 8]


def test_returned_int32_dequant_graph_keeps_the_integer_caller(tmp_path: Path):
    extra = [
        _typed_line("59", "aclnnGroupedMatmulWeightNz", "4,2048;4,32", "INT8;INT8", "4,1024", "INT32"),
        _typed_line("59", "GroupedDequantSwiglu", "4,1024", "INT32", "4,512", "INT8"),
    ]
    result = archive.resolve_archive_case(_layout(
        tmp_path, _matching_rows(), dequant_rows=128, graph_mode="FULL_DECODE_ONLY",
        kernel_text=_typed_kernel(extra),
    ))
    assert result["status"] == "resolved", result["diagnostics"]
    caller = _caller(result)
    assert caller["options"]["input_capacity_rows"] == 128
    assert caller["options"]["dequant_program"] == "arch35_full_load"
    chain = result["case"]["model"]["metadata"]["typed_expert_chain"]
    assert chain["int32_dequant_graph"] is True
    assert chain["bound_implementation"] is None
    assert "typed_expert_chain:int32_dequant_graph_preserved" in result["diagnostics"]
    assert not any(item.get("policy") == "valid_rows" for item in result["provenance"]["launch_replaced_template_fields"])


def test_same_shape_on_another_stream_is_not_a_connection(tmp_path: Path):
    from fleet_archive_typed_deployment import bind_witnessed_expert_caller

    broken = ["Device_id,Stream ID,Name,Input Shapes,Input Data Types,Output Shapes,Output Data Types"]
    broken.extend(_unfused_chain("59", 4)[:1])
    broken.append(_typed_line("8", "aclnnSwiGlu", "4,1024", "DT_BF16", "4,512", "DT_BF16"))
    broken.extend(_unfused_chain("59", 4)[2:])
    source = tmp_path / "kernel_details.csv"
    source.write_text("\n".join(broken) + "\n", encoding="utf-8")
    runtime = {"kernels": {"lowerings": {"grouped_int8_caller": {
        "implementation": "ascend_grouped_int32_dequant_swiglu",
        "options": {"dequant_program": "arch35_full_load", "input_capacity_rows": 128},
    }}}}
    model = {"metadata": {}}
    replaced: list[dict] = []
    notes: list[str] = []
    bind_witnessed_expert_caller(runtime, model, source, replaced, notes)
    assert runtime["kernels"]["lowerings"]["grouped_int8_caller"]["options"]["input_capacity_rows"] == 128
    assert replaced == [] and notes == []
    assert "typed_expert_chain" not in model["metadata"]


def test_an_earlier_consumer_blocks_a_later_shape_match(tmp_path: Path):
    from fleet_archive_typed_deployment import bind_witnessed_expert_caller

    blocked = ["Device_id,Stream ID,Name,Input Shapes,Input Data Types,Output Shapes,Output Data Types"]
    blocked.extend(_unfused_chain("59", 4)[:1])
    blocked.append(_typed_line("59", "aclnnCast", "4,1024", "DT_BF16", "4,1024", "FP32"))
    blocked.extend(_unfused_chain("59", 4)[1:])
    source = tmp_path / "kernel_details.csv"
    source.write_text("\n".join(blocked) + "\n", encoding="utf-8")
    runtime = {"graph_capture_mode": "FULL_DECODE_ONLY", "kernels": {"lowerings": {"grouped_int8_caller": {
        "implementation": "ascend_grouped_int32_dequant_swiglu",
        "options": {"dequant_program": "arch35_full_load", "input_capacity_rows": 128},
    }}}}
    replaced: list[dict] = []
    notes: list[str] = []
    bind_witnessed_expert_caller(runtime, {"metadata": {}}, source, replaced, notes)
    assert runtime["kernels"]["lowerings"]["grouped_int8_caller"]["options"]["input_capacity_rows"] == 128
    assert notes == []


def test_compile_modeling_error_is_a_recorded_refusal(tmp_path: Path):
    evaluator = OrderedBodyEvaluator({
        "machine": {"backend": "ascend", "sku": "Ascend950PR_9579", "num_devices": 4},
        "model": {"layers": 8, "num_experts": 16, "top_k": 2},
        "runtime": {"tp": 4, "dp": 1, "ep": 4, "pp": 1},
        "workload": {"num_requests": 1, "prompt_tokens": 8, "output_tokens": 1},
    }, "prefill")
    rows = evaluator.evaluate_ordered([(8, 0, 1)])
    assert rows[0]["ok"] is False
    assert rows[0]["status"] == "model_rejected"
    assert any("hidden_size_required" in item for item in rows[0]["diagnostics"])


def test_identical_quartets_bind_their_own_source_indices(tmp_path: Path):
    from fleet_archive_typed_deployment import witness_typed_expert_chain

    lines = ["Device_id,Stream ID,Name,Input Shapes,Input Data Types,Output Shapes,Output Data Types"]
    lines.extend(_unfused_chain("59", 4))
    lines.extend(_unfused_chain("59", 4))
    source = tmp_path / "kernel_details.csv"
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    witness = witness_typed_expert_chain(source)
    assert [item["source_indices"] for item in witness["chains"]] == [[0, 1, 2, 3], [4, 5, 6, 7]]


def test_a_different_shape_cast_stays_inside_the_segment(tmp_path: Path):
    from fleet_archive_typed_deployment import bind_witnessed_expert_caller

    linked = ["Device_id,Stream ID,Name,Input Shapes,Input Data Types,Output Shapes,Output Data Types"]
    linked.extend(_unfused_chain("59", 4)[:1])
    linked.append(_typed_line("59", "aclnnCast", "7,8", "DT_BF16", "7,8", "FP32"))
    linked.extend(_unfused_chain("59", 4)[1:])
    source = tmp_path / "kernel_details.csv"
    source.write_text("\n".join(linked) + "\n", encoding="utf-8")
    runtime = {"kernels": {"lowerings": {"grouped_int8_caller": {
        "implementation": "ascend_grouped_int32_dequant_swiglu",
        "options": {"dequant_program": "arch35_full_load", "input_capacity_rows": 128},
    }}}}
    replaced: list[dict] = []
    notes: list[str] = []
    bind_witnessed_expert_caller(runtime, {"metadata": {}}, source, replaced, notes)
    assert "grouped_int8_caller" not in runtime["kernels"]["lowerings"]
    assert notes


def test_a_collective_between_the_gate_and_swiglu_breaks_the_segment(tmp_path: Path):
    from fleet_archive_typed_deployment import witness_typed_expert_chain

    broken = ["Device_id,Stream ID,Name,Input Shapes,Input Data Types,Output Shapes,Output Data Types"]
    broken.extend(_unfused_chain("59", 4)[:1])
    broken.append("4,N/A,hcom_alltoallv_AicpuKernel,N/A,N/A,N/A,N/A")
    broken.extend(_unfused_chain("59", 4)[1:])
    source = tmp_path / "kernel_details.csv"
    source.write_text("\n".join(broken) + "\n", encoding="utf-8")
    assert witness_typed_expert_chain(source)["chains"] == []


_PRIMARY_KERNEL = Path(
    "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261031/"
    "a5_synth_qwen35_L8_E16_K2_tp4ep4_prefill_4k_c1/kernel_details.csv"
)
_PRIMARY_SHA = "40e58861af47f2aa05f134175f35348613c31b899791c5dd7fae6c4b0a05b9e3"


def _csv_rows(path: Path):
    import csv
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def _write_rows(path: Path, fields, rows) -> None:
    import csv
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _quartet_indices(rows):
    found = []
    for index, row in enumerate(rows):
        if row["Type"] == "GroupedMatmul" and row["Output Shapes"].strip('"') == "1920,1024":
            chain = [cursor for cursor in range(index, min(index + 10, len(rows))) if rows[cursor]["Stream ID"] == row["Stream ID"]][:4]
            assert [rows[cursor]["Type"] for cursor in chain] == ["GroupedMatmul", "SwiGlu", "DynamicQuantV2", "GroupedMatmul"]
            found.append(chain)
    return found


def test_real_source_deletion_and_cross_layer_join_are_refused(tmp_path: Path):
    from fleet_archive_typed_deployment import witness_typed_expert_chain

    assert _sha(_PRIMARY_KERNEL) == _PRIMARY_SHA
    fields, rows = _csv_rows(_PRIMARY_KERNEL)
    quartets = _quartet_indices(rows)
    assert len(quartets) == 8
    assert [item + 2 for item in quartets[0]] == [137, 138, 139, 140]
    assert [item + 2 for item in quartets[1]] == [226, 227, 228, 229]
    full = witness_typed_expert_chain(_PRIMARY_KERNEL)
    assert len(full["chains"]) == 16
    assert sorted(item["read_rows"] for item in full["chains"]) == [128] * 8 + [1920] * 8
    assert [135, 136, 137, 138] in [item["source_indices"] for item in full["chains"]]
    assert [224, 225, 226, 227] in [item["source_indices"] for item in full["chains"]]
    deleted = tmp_path / "kernel_details.csv"
    _write_rows(deleted, fields, [row for index, row in enumerate(rows) if index != quartets[0][2]])
    removed = witness_typed_expert_chain(deleted)
    assert len(removed["chains"]) == 15
    assert removed["rows_seen"] == 1483
    first, second = quartets[0], quartets[1]
    partial = [
        row for index, row in enumerate(rows)
        if first[0] <= index <= second[3] and index not in {first[1], first[2], first[3], second[0]}
    ]
    _write_rows(deleted, fields, partial)
    assert witness_typed_expert_chain(deleted)["chains"] == []


def _route_line(name: str, inputs: str, outputs: str, stream: str = "59") -> str:
    return f'4,{stream},{name},"{inputs}","{outputs}"'


def _route_csv(*lines: str) -> str:
    return "Device_id,Stream ID,Name,Input Shapes,Output Shapes\n" + "\n".join(lines) + "\n"


def _float_runtime() -> dict:
    return {
        "tp": 4, "dp": 1, "ep": 4, "pp": 1,
        "kernels": {
            "moe_token_partition": {"kind": "vllm_ascend_mc2_tp_slice"},
            "native_moe_protocol": {"kind": "arch35_fullmesh"},
            "moe_transport": {"kind": "declared"},
        },
    }


def _replicated_lines(rows: int, topk: int) -> list[str]:
    packed = rows * topk
    return [
        _route_line("aclnnMatmul_MatMulV3", f"{rows},2048;16,2048", f"{rows},16"),
        _route_line("aclnnMoeGatingTopK", f"{rows},16", f"{rows},{topk};{rows},{topk};{rows},16"),
        _route_line("aclnnMoeInitRoutingV3", f"{rows},2048;{rows},{topk}", f"{packed},2048;{packed};4;{packed}"),
        _route_line("aclnnGroupedMatmulWeightNz", f"{packed},2048", f"{packed},1024"),
        _route_line("aclnnGroupedMatmulWeightNz", f"{packed},512", f"{packed},2048"),
        "4,N/A,hcom_allReduce_AicpuKernel,N/A,N/A",
        "4,N/A,hcom_allReduce_AicpuKernel,N/A,N/A",
    ]


def test_float_replicated_allreduce_uses_the_existing_recipe(tmp_path: Path):
    from fleet_archive_route_geometry import apply_witnessed_route

    source = tmp_path / "kernel_details.csv"
    source.write_text(_route_csv(*_replicated_lines(8, 2)), encoding="utf-8")
    runtime = _float_runtime()
    model = {"activation_dtype": "bf16", "num_experts": 16, "quantization": "none", "metadata": {}}
    replaced: list[dict] = []
    notes: list[str] = []
    apply_witnessed_route(runtime, model, source, [{"query_rows": 8, "device_id": "4", "forward_id": 0}], replaced, notes)
    assert runtime["moe_recipe"] == "local_expert_reduce"
    assert "moe_token_partition" not in runtime["kernels"]
    assert "native_moe_protocol" not in runtime["kernels"]
    assert "moe_transport" not in runtime["kernels"]
    assert replaced[0]["reason"] == "witnessed_replicated_allreduce"
    assert "route_geometry:grouped_gemm_m_remains_heaviest_bank" in notes
    assert model["metadata"]["route_geometry"]["populations"][0]["grouped_rows"] == 16


def test_local_and_ambiguous_route_evidence_does_not_rewrite(tmp_path: Path):
    from fleet_archive_route_geometry import apply_witnessed_route

    local = tmp_path / "local.csv"
    local.write_text(_route_csv(
        _route_line("aclnnMatmul_MatMulV3", "8,2048;16,2048", "8,16"),
        _route_line("aclnnMoeGatingTopK", "8,16", "8,2;8,2;8,16"),
        _route_line("aclnnGroupedMatmulWeightNz", "8,512", "8,2048"),
    ), encoding="utf-8")
    runtime = _float_runtime()
    notes: list[str] = []
    apply_witnessed_route(runtime, {"activation_dtype": "bf16", "metadata": {}}, local,
                          [{"query_rows": 8, "device_id": "4"}], [], notes)
    assert "moe_recipe" not in runtime
    assert runtime["kernels"]["moe_token_partition"]["kind"] == "vllm_ascend_mc2_tp_slice"
    assert notes == ["route_geometry:local_no_route_not_rewritten:declared_ep=4"]

    ambiguous = tmp_path / "ambiguous.csv"
    ambiguous.write_text(_route_csv(
        *_replicated_lines(8, 2),
        "4,N/A,hcom_alltoallv_,N/A,N/A",
        "4,N/A,hcom_allGather_,N/A,N/A",
    ), encoding="utf-8")
    runtime = _float_runtime()
    notes = []
    apply_witnessed_route(runtime, {"activation_dtype": "bf16", "metadata": {}}, ambiguous,
                          [{"query_rows": 8, "device_id": "4"}], [], notes)
    assert "moe_recipe" not in runtime
    assert notes == ["route_geometry_not_certified:alltoallv_with_replicated_token_rows"]

    missing = tmp_path / "missing.csv"
    missing.write_text(_route_csv("4,N/A,hcom_allReduce_,N/A,N/A"), encoding="utf-8")
    runtime = _float_runtime()
    notes = []
    apply_witnessed_route(runtime, {"activation_dtype": "bf16", "metadata": {}}, missing, [], [], notes)
    assert "moe_recipe" not in runtime
    assert notes == ["route_geometry_not_certified:collectives_without_routing"]


def test_quantized_replicated_witness_selects_the_full_allocation(tmp_path: Path):
    from fleet_archive_route_geometry import apply_witnessed_route

    source = tmp_path / "kernel_details.csv"
    source.write_text(_route_csv(*_replicated_lines(3840, 8), *_replicated_lines(256, 8)), encoding="utf-8")
    runtime = _float_runtime()
    model = {
        "activation_dtype": "bf16", "num_experts": 16, "quantization": "w8a8_dynamic",
        "quant": {"expert_weight_format": "int8", "weight_format": "int8", "native_format": "bf16",
                  "category_overrides": {"shared_expert": {"weight_format": "bf16"}}},
        "metadata": {},
    }
    notes: list[str] = []
    apply_witnessed_route(
        runtime, model, source,
        [{"query_rows": 3840, "device_id": "4", "forward_id": 0}, {"query_rows": 256, "device_id": "4", "forward_id": 1}],
        [], notes,
    )
    assert runtime["moe_recipe"] == "local_expert_reduce"
    assert "moe_token_partition" not in runtime["kernels"]
    assert "native_moe_protocol" not in runtime["kernels"]
    assert "moe_transport" not in runtime["kernels"]
    assert runtime["metadata"]["moe_grouped_gemm_rows"] == "full_eager_allocation"
    geometry = model["metadata"]["route_geometry"]
    assert geometry["algorithm"] == "replicated_allreduce"
    assert geometry["applied_moe_recipe"] == "local_expert_reduce"
    assert geometry["disproven_ep_divided_rows"] == [512, 7680]
    assert [item["grouped_rows"] for item in geometry["populations"]] == [30720, 2048]
    assert "route_geometry:grouped_gemm_m_is_full_eager_allocation" in notes
    assert [item["projection_rows"] for item in geometry["populations"]] == [3840, 256]


def test_a_source_without_the_projection_edge_does_not_rewrite(tmp_path: Path):
    from fleet_archive_route_geometry import apply_witnessed_route

    rows, topk = 8, 2
    packed = rows * topk
    source = tmp_path / "kernel_details.csv"
    source.write_text(_route_csv(
        _route_line("aclnnMoeGatingTopK", f"{rows},16", f"{rows},{topk};{rows},{topk};{rows},16"),
        _route_line("aclnnGroupedMatmulWeightNz", f"{packed},2048", f"{packed},1024"),
        "4,N/A,hcom_allReduce_AicpuKernel,N/A,N/A",
    ), encoding="utf-8")
    runtime = _float_runtime()
    notes: list[str] = []
    apply_witnessed_route(runtime, {"activation_dtype": "bf16", "num_experts": 16, "metadata": {}}, source,
                          [{"query_rows": rows, "device_id": "4"}], [], notes)
    assert "moe_recipe" not in runtime
    assert "native_moe_protocol" in runtime["kernels"]
    assert notes == ["route_geometry_not_certified:projection_edge_absent"]


_ROUTE_KERNELS = {
    "k2": (
        "a5_synth_qwen35_L8_E16_K2_tp4ep4_prefill_4k_c1",
        "40e58861af47f2aa05f134175f35348613c31b899791c5dd7fae6c4b0a05b9e3",
        "expert_alltoallv",
        [1920, 128],
        2,
    ),
    "k8": (
        "a5_synth_qwen35_L8_E16_K8_tp4ep4_prefill_4k_c1",
        "6a7ba62df2891dcec9d05498dae6e947c8fbc084eedc41cade6dd23f8ab7fff0",
        "replicated_allreduce",
        [30720, 2048],
        8,
    ),
    "e32": (
        "a5_synth_qwen35_L8_E32_K2_tp4ep4_prefill_4k_c1",
        "5b854684d59755bbb0eeca3f59d07ad3f166569d11d1a62ccf65b9fd15938ef9",
        "expert_alltoallv",
        [1920, 128],
        2,
    ),
}


def test_real_kernels_keep_alltoall_or_withhold_the_quantized_recipe():
    from fleet_archive_route_geometry import apply_witnessed_route

    root = Path("/Volumes/data/mindie-sim-data/a5/heldout_engine_20261031")
    frames = [
        {"query_rows": 3840, "device_id": "4", "forward_id": 0},
        {"query_rows": 256, "device_id": "4", "forward_id": 1},
    ]
    quant = {
        "activation_dtype": "bf16", "num_experts": 16, "quantization": "w8a8_dynamic",
        "quant": {"expert_weight_format": "int8", "weight_format": "int8", "native_format": "bf16",
                  "category_overrides": {"shared_expert": {"weight_format": "bf16"}}},
        "metadata": {},
    }
    for name, (cell, digest, algorithm, rows, topk) in _ROUTE_KERNELS.items():
        source = root / cell / "kernel_details.csv"
        assert _sha(source) == digest, name
        runtime = _float_runtime()
        model = json.loads(json.dumps(quant))
        if name == "e32":
            model["num_experts"] = 32
        notes: list[str] = []
        apply_witnessed_route(runtime, model, source, frames, [], notes)
        geometry = model["metadata"]["route_geometry"]
        assert geometry["algorithm"] == algorithm, name
        assert [item["grouped_rows"] for item in geometry["populations"]] == rows, name
        assert [item["projection_rows"] for item in geometry["populations"]] == [3840, 256], name
        assert [item["topk"] for item in geometry["populations"]] == [topk, topk], name
        assert [item["allreduce"] for item in geometry["populations"]] == [16, 16], name
        if algorithm == "expert_alltoallv":
            assert runtime["moe_recipe"] == "alltoall"
            assert "moe_token_partition" in runtime["kernels"]
            assert "native_moe_protocol" not in runtime["kernels"]
            assert runtime["kernels"]["moe_transport"] == {
                "kind": "separate_quantized_payload",
                "payload_dtype": "int8",
                "scale_dtype": "fp32",
                "scale_granularity": "row",
                "histogram_dtype": "int64",
            }
            assert "payload_row_bytes" not in runtime["kernels"]["moe_transport"]
            assert [item["gating_rows"] for item in geometry["populations"]] == [960, 64], name
            assert [item["alltoallv"] for item in geometry["populations"]] == [24, 24]
            assert [item["allgather"] for item in geometry["populations"]] == [16, 16]
            assert geometry["disproven_ep_divided_rows"] == []
        else:
            assert runtime["moe_recipe"] == "local_expert_reduce"
            assert "native_moe_protocol" not in runtime["kernels"]
            assert "moe_token_partition" not in runtime["kernels"]
            assert "moe_transport" not in runtime["kernels"]
            assert runtime["metadata"]["moe_grouped_gemm_rows"] == "full_eager_allocation"
            assert [item["gating_rows"] for item in geometry["populations"]] == [3840, 256], name
            assert geometry["disproven_ep_divided_rows"] == [512, 7680]
            assert [item["alltoallv"] for item in geometry["populations"]] == [0, 0]
            assert [item["allgather"] for item in geometry["populations"]] == [0, 0]


def test_closure_refuses_a_hidden_size_that_is_not_the_source_match(tmp_path: Path):
    row = _layout(tmp_path, _matching_rows())
    result = archive.resolve_archive_case(row)
    payload = json.loads(json.dumps(result["case"]))
    payload["workload"] = {"num_requests": 1, "prompt_tokens": 8, "output_tokens": 1}
    payload["model"]["metadata"]["source_hidden_size"] = 4096
    evaluator = OrderedBodyEvaluator(payload, "prefill")
    rows = evaluator.evaluate_ordered([(8, 0, 1), (4, 8, 1)])
    assert rows[0]["status"] == "model_rejected"
    assert any(item.startswith("dimensional_closure:hidden_size") for item in rows[0]["diagnostics"])
    assert evaluator.stats["engine_calls"] == 0
