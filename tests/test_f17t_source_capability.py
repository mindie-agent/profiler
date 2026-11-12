"""Focused source-capability checks for the ordinary V4.1 packed cache binding."""
from __future__ import annotations
import copy
import json
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("mindie_sim")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402
import zero_shot_public_consumer as pc  # noqa: E402
import zero_shot_source_binding as sb  # noqa: E402
from mindie_sim.schema.model import ModelSpec  # noqa: E402
from mindie_sim.catalog.cache_format import cache_format  # noqa: E402
from mindie_sim.catalog.cache import index_row_bytes  # noqa: E402

JSONL = Path("/private/tmp/mindie-7337-20261111-1457/formal-qwen/native-model-phase-17-logical-rank-0115/original-cells.jsonl")


def _spec(cell_id: str):
    if not JSONL.is_file():
        pytest.skip("retained original cells unavailable")
    rows = [json.loads(line) for line in JSONL.read_text().splitlines() if line.strip()]
    return z.cell_from_dict(next(row for row in rows if row["cell_id"] == cell_id)).spec


@pytest.mark.parametrize("cell_id,requested", [
    ("dsv41_dp16tp1ep16_dc_1k_c2", None),
    ("dsv41_kvbf16_dc_1k_c2", "bfloat16"),
])
def test_real_ds_structured_packed_capability(cell_id, requested):
    spec = _spec(cell_id)
    raw = z._raw_case(spec)
    declaration = raw["runtime"]["metadata"]["source_cache_declaration"]
    assert declaration["basis"] == "source_packed_cache_capability_overrides_requested"
    assert declaration["requested_kv_cache_dtype"] == requested
    assert declaration["requested_override_applied"] is False
    assert declaration["regions"]["window"] == {"dtype": "fp8_e4m3", "group_size": 32, "scale_dtype": "bf16"}
    assert declaration["regions"]["compressed_kv"] == {"dtype": "fp4_e2m1", "group_size": 16, "scale_dtype": "bf16"}
    assert declaration["storage_layout"]["window"] == 544
    assert declaration["storage_layout"]["compressed_kv"] == 320
    case = z._public_case(spec)
    serving = pc._serving_case(spec)
    assert cache_format(case.model, "window").row_bytes(512) == 544
    assert cache_format(case.model, "compressed_kv").row_bytes(512) == 320
    assert cache_format(case.model, "index_k").row_bytes(128) == 68
    assert index_row_bytes(case.model, 128) == 68
    assert cache_format(serving.model, "index_k").row_bytes(128) == 68
    assert case.model.kv_dtype == "bf16"
    assert len(serving.workload.requests) == 2
    assert serving.workload.requests[0].prompt_tokens == 1024
    assert serving.workload.requests[0].output_tokens == 64


def test_lowering_without_capability_is_not_packed():
    spec = _spec("dsv41_kvbf16_dc_1k_c2")
    raw = copy.deepcopy(z._raw_case(spec))
    raw["runtime"]["metadata"].pop("native_attention"); raw["machine"] = {}
    result = sb._apply_source_cache_declaration(spec, raw, compatible=True, prior_model=raw["model"])
    declaration = result["runtime"]["metadata"]["source_cache_declaration"]
    assert declaration["basis"] == "requested_kv_cache_dtype_applied_without_packed_capability"
    assert declaration["requested_override_applied"] is True
    regions = result["model"]["metadata"]["cache_representations"]
    assert regions["window"]["dtype"] == "bf16" and regions["compressed_kv"]["dtype"] == "bf16"
    assert regions["index_k"] == {"dtype": "int8", "group_size": 128, "scale_dtype": "fp16"}
    assert cache_format(ModelSpec.from_mapping(result["model"]), "index_k").row_bytes(128) == 130
    assert "mqsmla_attention" not in result["runtime"]["kernels"]["lowerings"]


def _row(name, mechanism, ms, family, subgraph=""):
    return z.OperatorRow(name, "", mechanism, subgraph, ms, 1, (), "", "", 0, None,
                         native_occurrence={"family": family, "recipe": family,
                                            "source_role": "", "program": "", "layer": 0})


def test_moe_comparison_view_recurrent_vs_allreduce():
    base = z.OperatorRow("expert", "", "moe_grouped", "moe", 0.2, 1, (), "", "", 0, None,
                         native_occurrence={"family": "grouped_gemm", "recipe": "balanced",
                                            "source_role": "", "program": ""})
    dispatch = _row("dispatch", "collective", 0.5, "mc2_protocol", "moe")
    allreduce = _row("tp_allreduce", "collective", 0.7, "allreduce")
    recurrent = _row("recurrent_scan0", "gdn_kda", 0.3, "recurrent_scan", "attention")
    assert z._moe_comparison_subgraphs((base, dispatch, allreduce), {"moe": 0.7}, 1)["moe"] == pytest.approx(0.7)
    assert z._moe_comparison_subgraphs((base, dispatch, allreduce, recurrent), {"moe": 0.7}, 1, kda_layers=(0,))["moe"] == pytest.approx(1.4)


def test_nested_matrix_wrapper_native_kind_is_the_projection_contract():
    wrapped = {"family": "projection", "recipe": "latent_projection",
               "matrix_wrapper": {"native_kind": "GroupedMatmul"}}
    plain = {"family": "projection", "recipe": "latent_projection"}
    assert pc._public_mechanism(wrapped, "latent_down", {})[:3] == ("moe_grouped", "moe", "")
    assert pc._public_mechanism(plain, "latent_down", {})[0] == "unclassified"



def test_retained_k3_l2_moe_comparison_view():
    capture = JSONL.parent.parent / "three-public-routing-0421-k3-model" / "capture.json"
    if not capture.is_file():
        pytest.skip("retained K3 capture unavailable")
    cap = json.loads(capture.read_text())
    spec = _spec("k3_dp4tp8ep32_base_decode_1024_c2")
    from mindie_sim.prediction.operator_analysis import target_graphs
    graphs = target_graphs(z._public_case(spec), phase="decode", tokens=1,
                           context=spec.prompt_tokens, sequences=[1, 1, 0, 0], scope="body")
    meta = {}
    for op in graphs[0]:
        leaf = re.sub(r"^s\d+\.l\d+\.", "", op.op_id); metadata = dict(getattr(op, "metadata", ()) or ())
        meta[leaf] = {"family": op.family, "recipe": op.recipe, "op_id": op.op_id,
                      "fusion_role": metadata.get("fusion_role"), "native_kind": metadata.get("native_kind"),
                      "grouping_scope": metadata.get("grouping_scope"),
                      "routed_expert": metadata.get("routed_expert"),
                      "source_basis": metadata.get("source_basis"),
                      "native_implementation": metadata.get("native_implementation")}
    operators = {}
    for index, row in enumerate(cap["rows"]):
        item = dict(meta.get(row["name"]) or {"family": "unknown", "recipe": ""})
        item.update(elapsed_ms=row["duration_ms"], operator_events=row["count"],
                    stage=0, replica=0, phase="decode")
        operators[f"s0:s0.l0.{row['name']}#{index}"] = item
    out = pc._public_consume({"operators": operators, "step": {"start_ms": 0.0,
                              "device_end_ms": cap["decode_body_ms"], "end_ms": cap["decode_body_ms"]},
                              "duration_ms": cap["decode_body_ms"]}, (), layers=cap["layers"],
                             basis="expected_index_mod_dp")
    kda_layers = tuple(plan.index for plan in z._public_case(spec).model.layer_plans
                       if str(getattr(plan, "attention", "")).lower() == "kda")
    view = z._moe_comparison_subgraphs(out["rows"], out["subgraphs"], cap["layers"], kda_layers=kda_layers)
    assert sum(row.total_ms for row in out["rows"]) == pytest.approx(21.91259977509477)
    assert out["subgraphs"]["moe"] == pytest.approx(0.02799744296962737)
    assert view["moe"] == pytest.approx(0.07955967952876795)
    assert out["per_layer"]["collective"] == pytest.approx(0.07184718253300576)


def test_capability_survives_removed_prose_and_optional_pricing_lowering():
    spec = _spec("dsv41_dp16tp1ep16_dc_1k_c2")
    raw = copy.deepcopy(z._raw_case(spec))
    raw["runtime"]["metadata"].pop("native_attention", None)
    raw["runtime"]["kernels"]["lowerings"].pop("mqsmla_attention", None)
    result = sb._apply_source_cache_declaration(spec, raw, compatible=True, prior_model=raw["model"])
    regions = result["model"]["metadata"]["cache_representations"]
    assert regions["window"] == {"dtype": "fp8_e4m3", "group_size": 32, "scale_dtype": "bf16"}
    assert regions["index_k"]["packed_elements"] == 2
    assert result["runtime"]["metadata"]["source_cache_declaration"]["basis"] == "source_packed_cache_capability_overrides_requested"
    assert result["runtime"]["metadata"]["source_cache_declaration"]["selected_lowerings"] == []


def test_moe_comparison_no_grouped_and_non_kda_negative():
    tp = (_row("tp_ag", "collective", 0.5, "allgather"), _row("tp_rs", "collective", 0.5, "reduce_scatter"))
    assert z._moe_comparison_subgraphs(tp, {"moe": 1.0}, 1)["moe"] == pytest.approx(0.0)
    activation_zero = _row("act0", "activation", 0.0, "swiglu")
    assert z._moe_comparison_subgraphs(tp + (activation_zero,), {"moe": 1.0}, 1)["moe"] == pytest.approx(0.0)
    activation = _row("act", "activation", 0.3, "swiglu")
    assert z._moe_comparison_subgraphs(tp + (activation,), {"moe": 1.0}, 1)["moe"] == pytest.approx(0.3)
    grouped = _row("expert", "moe_grouped", 0.2, "grouped_gemm", "moe")
    allreduce = _row("tp_ar", "collective", 0.7, "allreduce")
    gdn = _row("gdn_recurrent", "gdn_kda", 0.4, "recurrent_gated_delta")
    dispatch = _row("dispatch", "collective", 0.2, "mc2_protocol", "moe")
    assert z._moe_comparison_subgraphs((dispatch, allreduce), {"moe": 1.0}, 1)["moe"] == pytest.approx(0.2)
    assert z._moe_comparison_subgraphs((grouped, allreduce, gdn, dispatch), {"moe": 1.0}, 1)["moe"] == pytest.approx(0.4)


def test_v41_capability_does_not_depend_on_weight_quant_format():
    spec = _spec("dsv41_dp16tp1ep16_dc_1k_c2")
    raw = copy.deepcopy(z._raw_case(spec))
    raw["model"]["hf_config"].pop("quantization_config", None)
    raw["model"]["name"] = "display-only-name"
    assert sb._packed_source_cache_capability(raw) is not None
    k3 = _spec("k3_dp4tp8ep32_base_decode_1024_c2")
    assert sb._packed_source_cache_capability(z._raw_case(k3)) is None


def test_qwen_real_prefix_gdn_is_not_kda():
    spec = _spec("qwen38_27b_dp4tp2_decode_1024_c2")
    case = z._public_case(spec)
    kda_layers = tuple(plan.index for plan in case.model.layer_plans
                       if str(getattr(plan, "attention", "")).lower() == "kda")
    assert kda_layers == ()
    from mindie_sim.prediction.operator_analysis import target_graphs
    graphs = target_graphs(case, phase="decode", tokens=1, context=spec.prompt_tokens,
                           sequences=1, scope="body")
    recurrent = next(op for op in graphs[0] if "recurrent_scan" in op.op_id)
    gdn = z.OperatorRow(recurrent.op_id, "", "gdn_kda", "attention", 0.4, 1, (), "", "", 0, None,
                        native_occurrence={"family": recurrent.family, "recipe": recurrent.recipe,
                                           "source_role": "", "program": "", "layer": 0})
    grouped = _row("expert", "moe_grouped", 0.2, "grouped_gemm", "moe")
    dispatch = _row("dispatch", "collective", 0.2, "mc2_protocol", "moe")
    allreduce = _row("tp_allreduce", "collective", 0.5, "allreduce")
    view = z._moe_comparison_subgraphs((grouped, dispatch, allreduce, gdn), {"moe": 1.0}, 1, kda_layers=kda_layers)
    assert view["moe"] == pytest.approx(0.4)
