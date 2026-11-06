"""Focused tests for phase/geometry-scoped native caller projection.

[Role] Exercise the prepared one-capture API, A3 AllToAll transport binding,
  A5 eager capacity/valid-row separation, conflict preservation and negative
  controls on genuine minimized fixture lines.
[Invariants] Positive fixtures are verbatim line subsets of real captures;
  negative controls mutate only a temporary copy. No measurement value selects
  a caller.
[Side-Effect Policy] Temporary homes, mutated CSVs and observation copies live
  under tmp_path; the fixture tree stays read-only.
"""
from copy import deepcopy
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "scoped_structure"
SIM_SOURCE = os.environ.get("MINDIE_SIM_SOURCE")
if SIM_SOURCE:
    sys.path.insert(0, SIM_SOURCE)
sys.path.insert(0, str(ROOT / "examples" / "structure"))

import capture_scoped_evidence as evidence  # noqa: E402
import capture_scoped_structure as scoped  # noqa: E402
from capture_scoped_contracts import (  # noqa: E402
    ALLTOALL_KIND,
    ALLTOALL_TRANSPORT,
    LOCAL_EXPERT_RECIPE,
)
from capture_scoped_structure import (  # noqa: E402
    apply_scoped_structure,
    prepare_scoped_capture,
)


A3_CSV = FIXTURES / "a3_qwen35_tp8_prefill_full_tail_decode_mixed.csv"
A3_OBS = FIXTURES / "a3_qwen35_tp8_prefill_full_tail_decode_mixed.observation.json"
A5_4K_CSV = FIXTURES / "a5_qwen30b_e16k4_prefill_4k.csv"
A5_4K_OBS = FIXTURES / "a5_qwen30b_e16k4_prefill_4k.observation.json"
A5_64K_CSV = FIXTURES / "a5_qwen30b_e16k4_prefill_64k.csv"
A5_64K_OBS = FIXTURES / "a5_qwen30b_e16k4_prefill_64k.observation.json"


@pytest.fixture(autouse=True)
def isolated_roots(tmp_path, monkeypatch):
    home = tmp_path / "home"
    mindie = tmp_path / "mindie"
    home.mkdir()
    mindie.mkdir()
    for name, value in (("HOME", home), ("MINDIE_HOME", mindie),
                        ("MINDIE_ROOT", mindie),
                        ("MINDIE_PROFILER_HOME", mindie)):
        monkeypatch.setenv(name, str(value))
    yield


def load_json(path):
    return json.loads(Path(path).read_text())


def a3_raw(**runtime):
    raw = load_json(FIXTURES / "a3_case.json")
    raw["runtime"].update(runtime)
    return raw


def a5_raw(**runtime):
    raw = load_json(FIXTURES / "a5_case.json")
    raw["runtime"].update(runtime)
    return raw


def call(raw, *, csv_path, observation, phase, tokens, context, sequences=1,
         replace_recipe=False, archive_template=False, context_offset=0):
    return apply_scoped_structure(
        raw, capture_path=csv_path, observation=observation, phase=phase,
        tokens=tokens, context=context, sequences=sequences,
        replace_recipe=replace_recipe, archive_template=archive_template,
        context_offset=context_offset)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mutated_csv(tmp_path, source, mutate, name):
    rows = list(csv.reader(Path(source).open(newline="")))
    if not mutate(rows):
        raise AssertionError("mutation did not match a fixture row")
    target = tmp_path / name
    with target.open("w", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    return target


def mutated_observation(tmp_path, source, mutate, name):
    document = deepcopy(load_json(source))
    mutate(document)
    target = tmp_path / name
    target.write_text(json.dumps(document))
    return target


def observation_for_csv(tmp_path, source, csv_path, name):
    document = deepcopy(load_json(source))
    document["source_identity"] = {
        "path": str(csv_path), "sha256": sha256(csv_path),
        "size_bytes": Path(csv_path).stat().st_size,
    }
    target = tmp_path / name
    target.write_text(json.dumps(document))
    return target


def sim_recipe_available():
    try:
        from mindie_sim.prediction.feedforward import MOE_RECIPES
    except Exception:
        return False
    return LOCAL_EXPERT_RECIPE in MOE_RECIPES


def test_prepared_capture_scans_once_for_multiple_geometries(monkeypatch):
    identities = []
    scans = []
    original_identity = evidence._file_identity
    original_scan = evidence.kernel_rows

    def counting_identity(path):
        identities.append(str(path))
        return original_identity(path)

    def counting_scan(*args, **kwargs):
        scans.append(1)
        return original_scan(*args, **kwargs)

    monkeypatch.setattr(evidence, "_file_identity", counting_identity)
    monkeypatch.setattr(evidence, "kernel_rows", counting_scan)
    raw = a3_raw()
    prepared = prepare_scoped_capture(A3_CSV, A3_OBS, raw=raw)
    assert len(identities) == 2  # before and after one scan
    assert len(scans) == 1
    first, first_prov = prepared.apply(raw, phase="prefill", tokens=8064,
                                       context=0)
    second, second_prov = prepared.apply(raw, phase="prefill", tokens=256,
                                         context=399744)
    assert first_prov["status"] == "applied"
    assert second_prov["status"] == "applied"
    assert len(identities) == 2 and len(scans) == 1
    assert first_prov["source"]["sha256"] == sha256(A3_CSV)
    assert first_prov["source_after_scan"]["sha256"] == first_prov["source"]["sha256"]
    assert first_prov["scan"]["windows"] == 3
    assert first != second


def test_a3_full_window_binds_partition_and_transport_atomically():
    raw = a3_raw()
    original = deepcopy(raw)
    new, provenance = call(raw, csv_path=A3_CSV, observation=A3_OBS,
                           phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "applied", provenance
    declaration = provenance["declaration"]
    assert declaration["moe_token_partition"] == {
        "kind": ALLTOALL_KIND, "padding": "none",
        "gather_output_materialization": "per_rank_copy",
    }
    assert declaration["moe_transport"] == ALLTOALL_TRANSPORT
    assert new["runtime"]["kernels"]["moe_token_partition"] == declaration["moe_token_partition"]
    assert new["runtime"]["kernels"]["moe_transport"] == declaration["moe_transport"]
    assert raw == original
    analysis = provenance["analysis"]
    assert len(analysis["layers"]) == 40
    assert analysis["allocation"]["native_gmm_rows_min"] == 2648
    assert analysis["allocation"]["native_gmm_rows_max"] == 14693
    assert analysis["allocation"]["expected_local_valid_rows"] == 8064
    assert analysis["allocation"]["gmm_rows_compared_to_generated"] is False
    assert analysis["transport"]["histogram_allgathers_per_layer"] == 1
    assert analysis["transport"]["scale_exchanges_per_layer"] == 1
    assert analysis["transport"]["payload_exchanges_per_layer"] == 1
    assert analysis["transport"]["return_exchanges_per_layer"] == 1
    assert analysis["transport"]["finalize_gathers_per_layer"] == 1
    assert analysis["layers"][0]["auxiliary_histogram_gathers"] == 1
    assert analysis["layers"][0]["native_gmm_rows"] != analysis["allocation"]["expected_local_valid_rows"]
    assert analysis["layers"][0]["gather_copies"] == 8
    assert provenance["sim"]["supported"] is True
    assert provenance["sim"]["mismatches"] == []
    facts = provenance["sim"]["generated"][0]["facts"]
    recipes = [fact["recipe"] for fact in facts]
    assert "moe_expert_count_histogram" in recipes
    assert "expert_scale_dispatch" in recipes
    assert "expert_quantized_dispatch" in recipes
    assert "expert_combine" in recipes
    assert recipes.count("tensor_copy") == 8
    gate = next(fact for fact in facts if fact["recipe"] == "grouped_gate_up")
    assert gate["local_shape"][:2] == (8064, 2 * 512)
    assert provenance["timing_values_used"] is False
    assert provenance["semantic_equivalence"] is False
    assert provenance["exact_native_kernel_match"] is False
    text = json.dumps(new, sort_keys=True)
    assert str(FIXTURES) not in text and "sha256" not in text
    assert "native_gmm_rows" not in text and "first_csv_line" not in text


def test_a3_tail_window_keeps_tail_geometry_and_view_materialization():
    new, provenance = call(a3_raw(), csv_path=A3_CSV, observation=A3_OBS,
                           phase="prefill", tokens=256, context=399744)
    assert provenance["status"] == "applied"
    analysis = provenance["analysis"]
    assert analysis["declaration"]["moe_token_partition"]["gather_output_materialization"] == "view"
    assert analysis["allocation"]["full_rows"] == 256
    assert analysis["allocation"]["local_rows"] == 32
    assert analysis["allocation"]["native_gmm_rows_max"] == 456
    assert analysis["allocation"]["expected_local_valid_rows"] == 256
    assert all(layer["gather_copies"] == 0 for layer in analysis["layers"])
    assert all(layer["auxiliary_histogram_gathers"] == 0
               for layer in analysis["layers"])
    assert provenance["sim"]["supported"] is True
    assert new["runtime"]["kernels"]["moe_token_partition"]["gather_output_materialization"] == "view"


def test_a3_mixed_decode_rows_do_not_block_prefill():
    raw = a3_raw()
    new, provenance = call(raw, csv_path=A3_CSV, observation=A3_OBS,
                           phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "applied"
    decode, decode_prov = call(raw, csv_path=A3_CSV, observation=A3_OBS,
                               phase="decode", tokens=1, context=192000)
    assert decode_prov["status"] == "unbound"
    assert decode_prov["reason"] == "existing_mc2_path_outside_scoped_adapter"
    assert decode == raw
    again, again_prov = call(raw, csv_path=A3_CSV, observation=A3_OBS,
                             phase="prefill", tokens=8064, context=0)
    assert again_prov["status"] == "applied" and again == new


def test_a3_existing_partition_and_transport_conflicts_are_preserved():
    raw = a3_raw()
    raw["runtime"]["kernels"]["moe_token_partition"] = {
        "kind": "vllm_ascend_mc2_tp_slice"}
    original = deepcopy(raw)
    new, provenance = call(raw, csv_path=A3_CSV, observation=A3_OBS,
                           phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "conflict"
    assert new == original

    raw = a3_raw()
    raw["runtime"]["kernels"]["moe_transport"] = {
        "kind": "separate_quantized_payload", "dispatch_dtype": "int8",
        "payload_dtype": "int8", "scale_dtype": "fp32",
        "scale_granularity": "row", "histogram_dtype": "int64",
    }
    original = deepcopy(raw)
    new, provenance = call(raw, csv_path=A3_CSV, observation=A3_OBS,
                           phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "conflict"
    assert provenance["caller"]["conflicts"][0]["field"] == "runtime.kernels.moe_transport.histogram_dtype"
    assert new == original

    raw = a3_raw()
    raw["runtime"]["kernels"]["moe_token_partition"] = {"kind": ALLTOALL_KIND}
    raw["runtime"]["kernels"]["moe_transport"] = {"dispatch_dtype": "int8"}
    new, provenance = call(raw, csv_path=A3_CSV, observation=A3_OBS,
                           phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "applied"
    assert provenance["caller"]["action"] == "completed"
    assert new["runtime"]["kernels"]["moe_token_partition"]["padding"] == "none"
    assert new["runtime"]["kernels"]["moe_transport"]["histogram_dtype"] == "int32"


def test_a3_format_dtype_row_and_order_negatives(tmp_path):
    def bad_format(rows):
        for row in rows:
            if row[5] == "MoeTokenPermute":
                row[19] = row[19].replace("ND;ND", "ND;NCHW", 1)
                return True
        return False

    def bad_dtype(rows):
        for row in rows:
            if row[5] == "DynamicQuant" and "INT8" in row[18]:
                row[18] = row[18].replace("INT8", "FLOAT16", 1)
                return True
        return False

    def bad_row(rows):
        for row in rows:
            if row[5] == "MoeInitRoutingV3":
                row[17] = row[17].replace("5430,2048", "5431,2048", 1)
                return True
        return False

    def bad_order(rows):
        topk = next(i for i, row in enumerate(rows) if row[5] == "MoeGatingTopK")
        permute = next(i for i, row in enumerate(rows) if row[5] == "MoeTokenPermute")
        topk_start, permute_start = rows[topk][8], rows[permute][8]
        rows[topk], rows[permute] = rows[permute], rows[topk]
        rows[topk][8], rows[permute][8] = topk_start, permute_start
        return True

    for mutate, name in ((bad_format, "format.csv"), (bad_dtype, "dtype.csv"),
                         (bad_row, "row.csv"), (bad_order, "order.csv")):
        target = mutated_csv(tmp_path, A3_CSV, mutate, name)
        observation = observation_for_csv(tmp_path, A3_OBS, target, name + ".json")
        new, provenance = call(a3_raw(), csv_path=target, observation=observation,
                               phase="prefill", tokens=8064, context=0)
        assert provenance["status"] == "unbound", (name, provenance)
        assert new == a3_raw()


def test_a5_explicit_balanced_raw_uses_generic_basis_without_archive_origin():
    if not sim_recipe_available():
        pytest.skip("Track A local_expert_reduce is not installed in this interpreter")
    raw = a5_raw(routing={"policy": "balanced"})
    new, provenance = call(
        raw, csv_path=A5_4K_CSV, observation=A5_4K_OBS,
        phase="prefill", tokens=4096, context=0, archive_template=False)
    assert provenance["status"] == "applied", provenance
    allocation = provenance["analysis"]["allocation"]
    assert allocation["expected_local_valid_rows"] == 4096
    assert allocation["uniform_rank_average_rows"] == 4096
    assert allocation["routing_basis"] == (
        "declared_balanced_integer_ledger; not_native_force_eplb")
    assert "archived_template" not in allocation["routing_basis"]
    assert new["runtime"]["moe_recipe"] == LOCAL_EXPERT_RECIPE
    assert new["runtime"]["routing"] == {"policy": "balanced"}


def test_a5_capacity_and_expected_valid_rows_are_separate():
    new, provenance = call(a5_raw(), csv_path=A5_4K_CSV,
                           observation=A5_4K_OBS, phase="prefill",
                           tokens=4096, context=0)
    analysis = provenance["analysis"]
    assert analysis["allocation"]["init_routing_allocation_rows"] == 16384
    assert analysis["allocation"]["native_gmm_rows"] == 16384
    assert analysis["allocation"]["expected_local_valid_rows"] == 4096
    assert analysis["allocation"]["gmm_rows_compared_to_generated"] is False
    assert analysis["allocation"]["valid_routed_rows"] == "unobserved"
    assert analysis["layers"][0]["gmm_row_axis_role"] == "allocated_capacity_including_unselected_slots"
    if not sim_recipe_available():
        assert provenance["status"] == "unbound"
        assert provenance["reason"] == "sim_local_expert_reduce_recipe_unavailable"
        assert new == a5_raw()
        pytest.skip("Track A local_expert_reduce is not installed in this interpreter")
    assert provenance["status"] == "applied", provenance
    assert provenance["sim"]["supported"] is True
    assert provenance["sim"]["mismatches"] == []
    facts = provenance["sim"]["generated"][0]["facts"]
    gate = next(fact for fact in facts if fact["recipe"] == "grouped_gate_up")
    down = next(fact for fact in facts if fact["recipe"] == "grouped_down")
    swiglu = next(fact for fact in facts if fact["recipe"] == "grouped_swiglu")
    assert gate["local_shape"] == (4096, 1536, 2048)
    assert down["local_shape"] == (4096, 2048, 768)
    assert swiglu["local_shape"] == (16384, 768)
    assert any(fact["recipe"] == "moe_output_reduce" for fact in facts)
    assert new["runtime"]["moe_recipe"] == LOCAL_EXPERT_RECIPE


def test_a5_64k_context_selects_one_forward_and_real_graph_contract():
    prepared = prepare_scoped_capture(A5_64K_CSV, A5_64K_OBS, raw=a5_raw())
    for context in (0, 16384, 32768, 57344):
        new, provenance = prepared.apply(
            a5_raw(), phase="prefill", tokens=8192, context=context)
        assert provenance["analysis"]["ok"] is True
        assert provenance["analysis"]["forward_id"] == f"prefill:{context // 8192}"
        assert provenance["analysis"]["allocation"]["init_routing_allocation_rows"] == 32768
        assert provenance["analysis"]["allocation"]["expected_local_valid_rows"] == 8192
        if sim_recipe_available():
            assert provenance["status"] == "applied", provenance
            facts = provenance["sim"]["generated"][0]["facts"]
            shapes = {fact["recipe"]: fact["local_shape"] for fact in facts}
            assert shapes["grouped_gate_up"] == (8192, 1536, 2048)
            assert shapes["grouped_swiglu"] == (32768, 768)
            assert shapes["grouped_down"] == (8192, 2048, 768)
    new, provenance = prepared.apply(a5_raw(), phase="prefill", tokens=8192,
                                     context=12345)
    assert provenance["status"] == "unbound"
    assert provenance["reason"] == "requested_geometry_not_in_prepared_capture"
    assert new == a5_raw()


def test_a5_context_offset_for_truncated_prefill_observation(tmp_path):
    offset = 100000
    def drop_context(document):
        document["forwards"][0].pop("context", None)
        document["forwards"][0].pop("context_tokens", None)
    observation = mutated_observation(tmp_path, A5_4K_OBS, drop_context,
                                      "offset.json")
    prepared = prepare_scoped_capture(
        A5_4K_CSV, observation, raw=a5_raw(), context_offset=offset)
    assert prepared.geometries()[0]["context"] == offset
    new, provenance = prepared.apply(a5_raw(), phase="prefill", tokens=4096,
                                     context=offset)
    assert provenance["analysis"]["ok"] is True
    assert provenance["analysis"]["allocation"]["query_rows"] == 4096
    if not sim_recipe_available():
        assert provenance["status"] == "unbound"


def test_a5_recipe_conflicts_and_archive_template_replacement():
    raw = a5_raw(moe_recipe="alltoall")
    original = deepcopy(raw)
    new, provenance = call(raw, csv_path=A5_4K_CSV, observation=A5_4K_OBS,
                           phase="prefill", tokens=4096, context=0)
    assert provenance["status"] == "conflict"
    assert new == original
    new, provenance = call(raw, csv_path=A5_4K_CSV, observation=A5_4K_OBS,
                           phase="prefill", tokens=4096, context=0,
                           replace_recipe=True)
    assert provenance["status"] == "conflict"
    assert provenance["caller"]["conflicts"][0]["reason"] == "recipe_replacement_requires_archive_template"
    new, provenance = call(raw, csv_path=A5_4K_CSV, observation=A5_4K_OBS,
                           phase="prefill", tokens=4096, context=0,
                           replace_recipe=True, archive_template=True)
    assert provenance["caller"]["action"] == "replaced"
    assert provenance["caller"]["preserved"][0]["basis"] == "archive_template_adaptation"
    if sim_recipe_available():
        assert provenance["status"] == "applied"
        assert new["runtime"]["moe_recipe"] == LOCAL_EXPERT_RECIPE
    else:
        assert provenance["status"] == "unbound"


def test_a5_dtype_row_and_order_negatives(tmp_path):
    def bad_dtype(rows):
        for row in rows:
            if row[5] == "SwiGlu":
                row[18] = row[18].replace("DT_BF16", "FLOAT16", 1)
                return True
        return False

    def bad_row(rows):
        for row in rows:
            if row[5] == "MoeFinalizeRoutingV2":
                row[17] = row[17].replace("4096,2048", "4095,2048", 1)
                return True
        return False

    def bad_order(rows):
        routing = next(i for i, row in enumerate(rows) if row[5] == "MoeInitRoutingV3")
        gate = next(i for i, row in enumerate(rows) if row[5] == "GroupedMatmul")
        routing_start, gate_start = rows[routing][8], rows[gate][8]
        rows[routing], rows[gate] = rows[gate], rows[routing]
        rows[routing][8], rows[gate][8] = routing_start, gate_start
        return True

    for mutate, name in ((bad_dtype, "a5_dtype.csv"),
                         (bad_row, "a5_row.csv"),
                         (bad_order, "a5_order.csv")):
        target = mutated_csv(tmp_path, A5_4K_CSV, mutate, name)
        observation = observation_for_csv(tmp_path, A5_4K_OBS, target,
                                          name + ".json")
        new, provenance = call(a5_raw(), csv_path=target, observation=observation,
                               phase="prefill", tokens=4096, context=0)
        assert provenance["status"] == "unbound", (name, provenance)
        assert new == a5_raw()



def test_prepared_capture_does_not_reject_more_than_sixteen_historical_windows():
    document = deepcopy(load_json(A5_4K_OBS))
    base = document["forwards"][0]
    body = base["body"]
    span = body["end_ns"] - body["start_ns"]
    for index in range(20):
        shift = span + (index + 1) * 1_000_000
        layers = [dict(layer) for layer in base["layers"]]
        for layer in layers:
            layer["start_ns"] += shift
            layer["end_ns"] += shift
        document["forwards"].append({
            "forward_id": "extra:" + str(index),
            "phase": "prefill", "query_rows": base["query_rows"],
            "tokens_per_sequence": base["query_rows"], "sequences": 1,
            "context": 1_000_000 + index * base["query_rows"],
            "body": {"start_ns": body["start_ns"] + shift,
                     "end_ns": body["end_ns"] + shift,
                     "first_csv_line": body["first_csv_line"],
                     "last_csv_line": body["last_csv_line"]},
            "layers": layers,
        })
    prepared = prepare_scoped_capture(A5_4K_CSV, document, raw=a5_raw())
    assert len(prepared.geometries()) == 21
    new, provenance = prepared.apply(a5_raw(), phase="prefill", tokens=4096,
                                     context=0)
    assert provenance["analysis"]["ok"] is True
    assert provenance["status"] in {"applied", "unbound"}


def repeated_a3_trace(tmp_path, *, repeats=8, break_repeat=None):
    """Duplicate the genuine A3 full window at one geometry with shifted times."""
    rows = list(csv.reader(A3_CSV.open(newline="")))
    header, body_rows = rows[0], rows[1:]
    observation = load_json(A3_OBS)
    forward = observation["forwards"][0]
    body_first = forward["body"]["first_csv_line"]
    body_last = forward["body"]["last_csv_line"]
    duration = forward["body"]["end_ns"] - forward["body"]["start_ns"]
    output, line_maps, forwards = [], [], []
    for repeat in range(repeats):
        shift = repeat * (duration + 1_000_000)
        mapping = {}
        for line in range(body_first, body_last + 1):
            row = deepcopy(body_rows[line - 2])
            start_ns = int(float(row[8].strip()) * 1000) + shift
            row[8] = f"{start_ns / 1000:.3f}\t"
            if (repeat == break_repeat and row[5] == "TensorMove"
                    and row[14].strip('"') == "1008,2048"):
                row[4], row[5] = "unknown_copy", "unknown"
            mapping[line] = len(output) + 2
            output.append(row)
        line_maps.append(mapping)
        layers = []
        for layer in forward["layers"]:
            lines = [mapping[line] for line in range(
                layer["first_csv_line"], layer["last_csv_line"] + 1)
                if line in mapping]
            layers.append({
                "layer_id": layer["layer_id"],
                "start_ns": layer["start_ns"] + shift,
                "end_ns": layer["end_ns"] + shift,
                "first_csv_line": min(lines), "last_csv_line": max(lines),
            })
        forwards.append({
            "forward_id": f"repeat:{repeat}", "phase": "prefill",
            "query_rows": forward["query_rows"],
            "tokens_per_sequence": forward["query_rows"],
            "sequences": 1, "context": 0,
            "body": {"start_ns": forward["body"]["start_ns"] + shift,
                     "end_ns": forward["body"]["end_ns"] + shift,
                     "first_csv_line": min(l["first_csv_line"] for l in layers),
                     "last_csv_line": max(l["last_csv_line"] for l in layers)},
            "layers": layers,
        })
    target = tmp_path / "repeated_a3.csv"
    with target.open("w", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows([header, *output])
    document = {"schema_version": "mindie-scoped-structure-window/1",
                "forwards": forwards,
                "source_identity": {"path": str(target),
                                    "sha256": sha256(target),
                                    "size_bytes": target.stat().st_size}}
    observation_path = tmp_path / "repeated_a3.observation.json"
    observation_path.write_text(json.dumps(document))
    return target, observation_path


def test_repeated_geometry_is_bounded_and_conflicts_are_permanent(tmp_path):
    target, observation = repeated_a3_trace(tmp_path, repeats=8)
    prepared = prepare_scoped_capture(target, observation, raw=a3_raw())
    geometry = prepared.geometries()[0]
    assert geometry["status"] == "ok"
    assert geometry["window_count"] == 8
    assert prepared.scan["peak_active_windows"] == 1
    assert prepared.scan["peak_live_evidence"] <= 1
    assert prepared.scan["retained_evidence"] == 0
    assert prepared.scan["geometry_contracts"] == 1
    contract = prepared.contracts[( "prefill", 8064, 1, 0, 8064)]
    assert len(contract["analysis"]["layers"]) == 40
    assert len(contract["witnesses"]) <= 4
    assert len(contract["witnesses"]) < contract["window_count"]
    new, provenance = prepared.apply(a3_raw(), phase="prefill", tokens=8064,
                                     context=0)
    assert provenance["status"] == "applied"
    assert provenance["selection"]["window_count"] == 8
    assert len(provenance["selection"]["witnesses"]) <= 4
    assert len(provenance["selection"]["witnesses"]) < 8
    assert "repeat:" in json.dumps(provenance["selection"]["witnesses"])
    assert "repeat:7" not in json.dumps(provenance["selection"]["witnesses"])

    target, observation = repeated_a3_trace(
        tmp_path, repeats=8, break_repeat=3)
    prepared = prepare_scoped_capture(target, observation, raw=a3_raw())
    geometry = prepared.geometries()[0]
    assert geometry["status"] == "unbound"
    assert geometry["reason"] == "repeated_window_contract_conflict"
    assert geometry["window_count"] == 8
    contract = prepared.contracts[("prefill", 8064, 1, 0, 8064)]
    assert contract["first_conflict"]["reason"] == "repeated_window_contract_conflict"
    assert len(contract["witnesses"]) <= 4
    original = a3_raw()
    new, provenance = prepared.apply(original, phase="prefill", tokens=8064,
                                     context=0)
    assert provenance["status"] == "unbound"
    assert provenance["reason"] == "repeated_window_contract_conflict"
    assert provenance["first_conflict"]["reason"] == "repeated_window_contract_conflict"
    assert new == original


def test_a3_extra_router_shaped_variant_is_unbound(tmp_path):
    def incompatible_router(rows):
        for row in rows:
            if (row[5] == "MatMulV3" and "1536,2048" in row[14]
                    and row[17].strip('"') == "8064,1536"):
                row[14] = row[14].replace("1536,2048", "256,2048", 1)
                row[17] = '"8064,256"'
                row[18] = "DT_BF16"
                return True
        return False

    def duplicate_valid_router(rows):
        for row in rows:
            if (row[5] == "MatMulV3" and "1536,2048" in row[14]
                    and row[17].strip('"') == "8064,1536"):
                row[14] = row[14].replace("1536,2048", "256,2048", 1)
                row[17] = '"8064,256"'
                row[18] = "FLOAT"
                return True
        return False

    for mutate, name in ((incompatible_router, "router_dtype.csv"),
                         (duplicate_valid_router, "router_duplicate.csv")):
        target = mutated_csv(tmp_path, A3_CSV, mutate, name)
        observation = observation_for_csv(tmp_path, A3_OBS, target,
                                          name + ".json")
        new, provenance = call(a3_raw(), csv_path=target,
                               observation=observation, phase="prefill",
                               tokens=8064, context=0)
        assert provenance["status"] == "unbound", (name, provenance)
        assert new == a3_raw()


def _prior_windows(document, *, count, overlapping):
    base = document["forwards"][0]
    first = base["body"]["start_ns"]
    for index in range(count):
        if overlapping:
            start = first + 100_000
            end = first + 200_000
        else:
            start = first - 10_000_000 + index * 1000
            end = start + 400
        step = max(5, (end - start) // 40)
        layers = []
        for layer_id in range(40):
            layer_start = start + layer_id * step
            layers.append({"layer_id": layer_id, "start_ns": layer_start,
                           "end_ns": min(end, layer_start + step)})
        document["forwards"].append({
            "forward_id": "prior:" + str(index),
            "phase": "prefill", "query_rows": 8064,
            "tokens_per_sequence": 8064, "sequences": 1,
            "context": 1_000_000 + index,
            "body": {"start_ns": layers[0]["start_ns"],
                     "end_ns": layers[-1]["end_ns"]},
            "layers": layers,
        })
    return document


def test_expired_windows_are_processed_without_preallocation():
    document = deepcopy(load_json(A3_OBS))
    _prior_windows(document, count=100, overlapping=False)
    prepared = prepare_scoped_capture(A3_CSV, document, raw=a3_raw())
    assert prepared.scan["peak_live_evidence"] <= 1
    assert prepared.scan["peak_active_windows"] == 1
    assert prepared.scan["retained_evidence"] == 0
    assert prepared.scan["geometry_contracts"] == 103
    new, provenance = prepared.apply(a3_raw(), phase="prefill", tokens=8064,
                                     context=0)
    assert provenance["status"] == "applied"


def test_more_than_sixteen_genuinely_overlapping_windows_is_rejected():
    document = deepcopy(load_json(A3_OBS))
    _prior_windows(document, count=20, overlapping=True)
    with pytest.raises(ValueError, match="active_window_limit"):
        prepare_scoped_capture(A3_CSV, document, raw=a3_raw(),
                               max_active_windows=16)

def test_missing_malformed_and_hash_mismatch_are_not_success(tmp_path):
    raw = a3_raw()
    missing, provenance = call(raw, csv_path=tmp_path / "absent.csv",
                               observation=A3_OBS, phase="prefill",
                               tokens=8064, context=0)
    assert provenance["status"] == "not_provided" and missing == raw
    missing, provenance = call(raw, csv_path=A3_CSV,
                               observation=tmp_path / "absent.json",
                               phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "not_provided" and missing == raw
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json")
    missing, provenance = call(raw, csv_path=A3_CSV, observation=bad,
                               phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "unsupported"
    assert provenance["reason"] == "scoped_observation_malformed"
    assert missing == raw

    def corrupt(document):
        document["source_identity"]["sha256"] = "0" * 64

    observation = mutated_observation(tmp_path, A3_OBS, corrupt, "hash.json")
    new, provenance = call(raw, csv_path=A3_CSV, observation=observation,
                           phase="prefill", tokens=8064, context=0)
    assert provenance["status"] == "unsupported"
    assert provenance["reason"] == "capture_source_hash_mismatch"
    assert new == raw


def test_missing_phase_is_not_invented_as_prefill():
    document = deepcopy(load_json(A5_4K_OBS))
    document["forwards"][0].pop("phase")
    prepared = prepare_scoped_capture(A5_4K_CSV, document, raw=a5_raw())
    assert all(item["phase"] is None for item in prepared.geometries())
    new, provenance = prepared.apply(a5_raw(), phase="prefill", tokens=4096,
                                     context=0)
    assert provenance["status"] == "unbound"
    assert provenance["reason"] == "requested_geometry_not_in_prepared_capture"
    assert new == a5_raw()


def test_scan_errors_propagate(monkeypatch):
    def timeout(*args, **kwargs):
        raise TimeoutError("bounded scan exceeded")

    monkeypatch.setattr(evidence, "kernel_rows", timeout)
    with pytest.raises(TimeoutError):
        call(a3_raw(), csv_path=A3_CSV, observation=A3_OBS,
             phase="prefill", tokens=8064, context=0)

    def parser_error(*args, **kwargs):
        raise RuntimeError("csv parser failed")

    monkeypatch.setattr(evidence, "kernel_rows", parser_error)
    with pytest.raises(RuntimeError, match="csv parser failed"):
        call(a3_raw(), csv_path=A3_CSV, observation=A3_OBS,
             phase="prefill", tokens=8064, context=0)
