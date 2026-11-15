"""Focused shared C-before-B scoped replay integration.

[Role] Exercise one genuine mixed A3 capture's full and tail chunks through the
  per-geometry scoped caller, A5 truncated-prefill offsets, archive-only recipe
  replacement, strict scope plans, bounded/stale extraction evidence and final
  prediction identity.
[Invariants] Every geometry keeps its own declaration; no geometry is promoted
  to the capture. Observations and explicit contexts are never rewritten.
[Timeouts & Locks] Real minimized line fixtures and finite local payloads; no
  devices, network, sleeps or locks.
[Side-Effect Policy] Writes only under tmp_path; fixture files stay read-only.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SIM_SOURCE = os.environ.get("MINDIE_SIM_SOURCE")
if SIM_SOURCE:
    sys.path.insert(0, SIM_SOURCE)
sys.path.insert(0, str(ROOT / "examples" / "structure"))

import scoped_native_replay as replay  # noqa: E402
from scoped_native_replay import (  # noqa: E402
    ReleasedScopedReplay,
    load_verified_extraction,
    prediction_identity,
    prepare_scoped_replay,
    read_prediction_cache,
    resolve_context_offset,
    validate_scope_plan,
)
from capture_policy import import_capture_policy  # noqa: E402
from dsh_scoped_prefill import score_prefill_capture  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "scoped_structure"
A3_CSV = FIXTURES / "a3_qwen35_tp8_prefill_full_tail_decode_mixed.csv"
A3_OBS = FIXTURES / "a3_qwen35_tp8_prefill_full_tail_decode_mixed.observation.json"
A5_4K_CSV = FIXTURES / "a5_qwen30b_e16k4_prefill_4k.csv"
A5_4K_OBS = FIXTURES / "a5_qwen30b_e16k4_prefill_4k.observation.json"
A5_64K_CSV = FIXTURES / "a5_qwen30b_e16k4_prefill_64k.csv"
A5_64K_OBS = FIXTURES / "a5_qwen30b_e16k4_prefill_64k.observation.json"
B_FIXTURE = (ROOT / "tests" / "fixtures" / "native_observations"
             / "a3_qwen35_prefill_400k_native.json")


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


@pytest.fixture
def restored_sys_path():
    saved = list(sys.path)
    yield
    sys.path[:] = saved


def load_json(path):
    return json.loads(Path(path).read_text())


def a3_raw():
    return load_json(FIXTURES / "a3_case.json")


def a5_raw():
    return load_json(FIXTURES / "a5_case.json")


def b_raw():
    return deepcopy(load_json(B_FIXTURE)["raw_case"])


def prepared_a3(raw, **options):
    return prepare_scoped_replay(
        raw, capture_path=A3_CSV, observation=A3_OBS,
        extract_missing=False, **options)


def test_mixed_a3_capture_keeps_full_and_tail_declarations_separate():
    raw = a3_raw()
    original = deepcopy(raw)
    observation = load_json(A3_OBS)
    prepared = prepared_a3(raw)
    try:
        full, full_provenance = prepared.apply(
            raw, phase="prefill", tokens=8064, context=0, sequences=1)
        tail, tail_provenance = prepared.apply(
            raw, phase="prefill", tokens=256, context=399744, sequences=1)
    finally:
        prepared.release()
    assert raw == original
    assert full_provenance["scope_status"] == "applied"
    assert tail_provenance["scope_status"] == "applied"
    assert (full["runtime"]["kernels"]["moe_token_partition"]
            ["gather_output_materialization"]) == "per_rank_copy"
    assert (tail["runtime"]["kernels"]["moe_token_partition"]
            ["gather_output_materialization"]) == "view"
    full_id = prediction_identity(
        full, phase="prefill", tokens=8064, context=0, sequences=1,
        sim_identity="sim", native_identity="native")
    tail_id = prediction_identity(
        tail, phase="prefill", tokens=256, context=399744, sequences=1,
        sim_identity="sim", native_identity="native")
    assert full_id != tail_id
    assert full_provenance["geometry"]["tokens"] == 8064
    assert tail_provenance["geometry"]["context"] == 399744
    assert observation == load_json(A3_OBS)
    assert len(observation["forwards"]) == 3


def test_c_applied_then_b_is_called_on_the_same_geometry():
    raw = a3_raw()
    prepared = prepared_a3(raw)
    try:
        result, provenance = prepared.apply(
            raw, phase="prefill", tokens=8064, context=0)
    finally:
        prepared.release()
    assert provenance["scope_status"] == "applied"
    assert provenance["native_status"] == "not_applicable"
    assert provenance["status"] == "applied_scope_only"
    assert result["runtime"]["kernels"]["moe_token_partition"]["kind"] == (
        "vllm_ascend_alltoall_tp_slice")


def test_a5_context_offset_uses_requested_context_minus_sumquery():
    observation = load_json(A5_64K_OBS)
    without_context = deepcopy(observation)
    for forward in without_context["forwards"]:
        forward.pop("context", None)
        forward.pop("context_tokens", None)
    raw = a5_raw()
    prepared = prepare_scoped_replay(
        raw, capture_path=A5_64K_CSV, observation=without_context,
        requested_context=81920, extract_missing=False)
    try:
        assert prepared.context_offset == 16384
        assert prepared.context_offset_basis == (
            "requested_context_minus_sumquery")
        contexts = [row["context"] for row in prepared.geometries()
                    if row["phase"] == "prefill"]
        assert contexts[:2] == [16384, 24576]
        result, provenance = prepared.apply(
            raw, phase="prefill", tokens=8192, context=16384)
    finally:
        prepared.release()
    assert without_context == {
        **observation, "forwards": [
            {key: value for key, value in forward.items()
             if key not in {"context", "context_tokens"}}
            for forward in observation["forwards"]]}
    if provenance["scope_reason"] == "sim_local_expert_reduce_recipe_unavailable":
        pytest.skip("installed Sim has no local_expert_reduce recipe")
    assert provenance["scope_status"] == "applied"
    assert result["runtime"]["moe_recipe"] == "local_expert_reduce"


def test_a5_explicit_observed_contexts_are_never_shifted():
    observation = load_json(A5_64K_OBS)
    raw = a5_raw()
    prepared = prepare_scoped_replay(
        raw, capture_path=A5_64K_CSV, observation=observation,
        requested_context=81920, extract_missing=False)
    try:
        assert prepared.context_offset == 0
        assert prepared.context_offset_basis == (
            "explicit_observed_context_present")
        contexts = [row["context"] for row in prepared.geometries()
                    if row["phase"] == "prefill"]
        assert contexts[:2] == [0, 8192]
    finally:
        prepared.release()


def test_foreign_recipe_preserved_and_archive_replacement_is_explicit():
    raw = a5_raw()
    raw["runtime"]["moe_recipe"] = "alltoall"
    original = deepcopy(raw)
    prepared = prepare_scoped_replay(
        raw, capture_path=A5_4K_CSV, observation=A5_4K_OBS,
        extract_missing=False)
    try:
        kept, conflict = prepared.apply(
            raw, phase="prefill", tokens=4096, context=0)
        assert kept == original
        assert conflict["scope_status"] == "conflict"
        assert conflict["reason"] == "scope_evidence_conflict_or_unsupported"
        rejected, rejected_provenance = prepared.apply(
            raw, phase="prefill", tokens=4096, context=0,
            replace_recipe=True)
        assert rejected == original
        assert rejected_provenance["scope_status"] == "conflict"
        replaced, replaced_provenance = prepared.apply(
            raw, phase="prefill", tokens=4096, context=0,
            replace_recipe=True, archive_template=True)
    finally:
        prepared.release()
    if replaced_provenance["scope_reason"] == (
            "sim_local_expert_reduce_recipe_unavailable"):
        pytest.skip("installed Sim has no local_expert_reduce recipe")
    assert replaced_provenance["scope_status"] == "applied"
    assert replaced["runtime"]["moe_recipe"] == "local_expert_reduce"


def test_preparation_runs_once_per_capture_across_geometries(monkeypatch):
    calls = []
    actual = replay.prepare_scoped_capture

    def counted(*args, **kwargs):
        calls.append(1)
        return actual(*args, **kwargs)

    monkeypatch.setattr(replay, "prepare_scoped_capture", counted)
    prepared = prepared_a3(a3_raw())
    try:
        prepared.apply(a3_raw(), phase="prefill", tokens=8064, context=0)
        prepared.apply(a3_raw(), phase="prefill", tokens=256,
                       context=399744)
        prepared.apply(a3_raw(), phase="prefill", tokens=8064, context=0)
    finally:
        prepared.release()
    assert len(calls) == 1


def test_released_prepared_state_cannot_price_again():
    prepared = prepared_a3(a3_raw())
    prepared.apply(a3_raw(), phase="prefill", tokens=8064, context=0)
    prepared.release()
    with pytest.raises(ReleasedScopedReplay):
        prepared.apply(a3_raw(), phase="prefill", tokens=8064, context=0)
    with pytest.raises(ReleasedScopedReplay):
        prepared.geometries()


def test_missing_scope_is_distinct_from_stale_and_malformed_evidence(tmp_path):
    raw = a5_raw()
    missing = prepare_scoped_replay(
        raw, capture_path=tmp_path / "absent.csv", observation=None,
        extract_missing=False)
    missing_result, missing_provenance = missing.apply(
        raw, phase="prefill", tokens=4096, context=0)
    missing.release()
    assert missing_result == raw
    assert missing_provenance["scope_status"] == "not_provided"
    assert missing_provenance["status"] == "unbound"

    observation = load_json(A5_4K_OBS)
    observation["source_identity"] = {
        "path": str(A5_4K_CSV), "size_bytes": A5_4K_CSV.stat().st_size}
    extraction = tmp_path / "extraction.json"
    extraction.write_text(json.dumps({
        "cache_version": "v1", "parser_identity": "p1", "cache_key": "k1",
        "observed": observation}))
    stale = prepare_scoped_replay(
        raw, capture_path=A5_4K_CSV, extraction_path=extraction,
        expected_extraction={"cache_version": "v1",
                             "parser_identity": "other",
                             "cache_key": "k1"},
        extract_missing=False)
    stale_result, stale_provenance = stale.apply(
        raw, phase="prefill", tokens=4096, context=0)
    stale.release()
    assert stale_result == raw
    assert stale_provenance["scope_status"] == "unsupported"
    assert stale_provenance["scope_reason"].startswith(
        "scope_evidence_stale")

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{")
    with pytest.raises(json.JSONDecodeError):
        prepare_scoped_replay(
            raw, capture_path=A5_4K_CSV, extraction_path=malformed,
            extract_missing=False)


def test_extraction_source_size_mismatch_propagates(tmp_path):
    observation = load_json(A5_4K_OBS)
    observation["source_identity"] = {
        "path": str(A5_4K_CSV), "size_bytes": A5_4K_CSV.stat().st_size + 1}
    extraction = tmp_path / "extraction.json"
    extraction.write_text(json.dumps({
        "cache_version": "v1", "parser_identity": "p1", "cache_key": "k1",
        "observed": observation}))
    with pytest.raises(ValueError, match="extraction_source_size_mismatch"):
        prepare_scoped_replay(
            a5_raw(), capture_path=A5_4K_CSV, extraction_path=extraction,
            expected_extraction={"cache_version": "v1",
                                 "parser_identity": "p1",
                                 "cache_key": "k1"},
            extract_missing=False)


def test_bounded_extraction_read_and_projection(tmp_path):
    observation = load_json(A3_OBS)
    observation["source_identity"] = {
        "path": str(A3_CSV), "size_bytes": A3_CSV.stat().st_size}
    extraction = tmp_path / "extraction.json"
    extraction.write_text(json.dumps({
        "cache_version": "v1", "parser_identity": "p1", "cache_key": "k1",
        "observed": observation, "bulk": "x" * 1000}))
    loaded, evidence = load_verified_extraction(
        extraction, capture_path=A3_CSV,
        expected={"cache_version": "v1", "parser_identity": "p1",
                  "cache_key": "k1"})
    assert evidence["status"] == "current"
    assert "bulk" not in loaded
    assert len(loaded["forwards"]) == 3
    assert all("layers" in forward for forward in loaded["forwards"])
    with pytest.raises(ValueError, match="full_extraction_exceeds_bounded_read"):
        load_verified_extraction(extraction, max_bytes=10)
    stale, stale_evidence = load_verified_extraction(
        extraction, capture_path=A3_CSV,
        expected={"cache_version": "v1", "parser_identity": "different",
                  "cache_key": "k1"})
    assert stale is None
    assert stale_evidence["status"] == "stale"


def test_scope_plan_must_match_every_observed_geometry():
    geometries = [{"tokens": 8064, "context": 0},
                  {"tokens": 256, "context": 399744}]
    signatures = [{"tokens": 8064, "context": 0, "key": "a"},
                  {"tokens": 256, "context": 399744, "key": "b"}]
    assert validate_scope_plan(None, geometries=geometries,
                               forward_count=2) is None
    assert validate_scope_plan(
        {"signatures": signatures}, geometries=geometries,
        forward_count=2) == signatures
    with pytest.raises(ValueError, match="scoped_plan_geometry_count_mismatch"):
        validate_scope_plan(
            {"signatures": signatures[:1]}, geometries=geometries,
            forward_count=2)
    with pytest.raises(ValueError, match="scoped_plan_geometry_mismatch"):
        validate_scope_plan(
            {"signatures": [signatures[0],
                            {**signatures[1], "context": 8064}]},
            geometries=geometries, forward_count=2)


def test_dsh_prefill_scoring_uses_explicit_contexts_and_strict_plan():
    observed = {"body_span_sum_ms": 1000.0, "forwards": [
        {"query_rows": 8064, "context": 0, "body": {"span_ms": 900.0}},
        {"query_rows": 256, "context": 399744,
         "body": {"span_ms": 100.0}}]}
    traits = {"phase": "prefill", "context_tokens": 400000,
              "cohort": "a3/test", "hw": "a3",
              "family": "qwen3.5-35b-a3b", "tp": 8, "dp": 1, "ep": 8,
              "spec_tokens": 0}
    signatures = [{"tokens": 8064, "context": 0, "key": "full"},
                  {"tokens": 256, "context": 399744, "key": "tail"}]
    provenance = [{"geometry": {"tokens": 8064, "context": 0},
                   "status": "applied"},
                  {"geometry": {"tokens": 256, "context": 399744},
                   "status": "unbound"}]
    pred_cache = {("full", "prefill", 8064, 0, 1):
                  {"body_forward_span_ms": 900.0},
                  ("tail", "prefill", 256, 399744, 1):
                  {"body_forward_span_ms": 100.0}}
    result = score_prefill_capture(
        A3_CSV, traits, "template", False,
        {"observed": observed, "meta": {}}, pred_cache, "legacy",
        scope_plan={"signatures": signatures, "provenance": provenance})
    assert result["status"] == "compared"
    assert result["observed_ms"] == 1000.0
    assert result["predicted_ms"] == 1000.0
    assert result["relative_error"] == 0.0
    with pytest.raises(ValueError, match="scoped_plan_geometry_count_mismatch"):
        score_prefill_capture(
            A3_CSV, traits, "template", False,
            {"observed": observed, "meta": {}}, pred_cache, "legacy",
            scope_plan={"signatures": signatures[:1],
                        "provenance": provenance[:1]})


def test_final_prediction_identity_depends_on_raw_geometry_and_runtime():
    raw = a3_raw()

    def identity(value=raw, *, sim="sim", native="native", tokens=8064,
                 context=0):
        return prediction_identity(
            value, phase="prefill", tokens=tokens, context=context,
            sequences=1, sim_identity=sim, native_identity=native)

    baseline = identity()
    assert baseline == identity()
    assert baseline != identity(sim="other")
    assert baseline != identity(native="other")
    assert baseline != identity(tokens=256, context=399744)
    changed = deepcopy(raw)
    changed["runtime"]["moe_recipe"] = "tp_join_reduce"
    assert baseline != identity(changed)


def test_observation_evidence_is_json_projected_without_bulk_copy():
    observation = load_json(A3_OBS)
    projected = replay._project_extraction({"observed": observation})
    assert projected["forwards"][0]["layers"]
    assert "bulk" not in projected


def test_wave5_driver_prices_full_and_tail_from_one_prepared_capture(
        tmp_path, monkeypatch):
    import evaluation_io
    import wave5_generalization_eval as wave5

    observation = load_json(A3_OBS)
    prefill_forwards = [deepcopy(forward)
                        for forward in observation["forwards"]
                        if forward.get("phase") == "prefill"]
    observation["source_identity"] = {
        "path": str(A3_CSV), "size_bytes": A3_CSV.stat().st_size}
    cache_key = "genuine-mixed-a3"
    (tmp_path / f"{cache_key}.json").write_text(json.dumps({
        "cache_version": "v1", "parser_identity": "p1",
        "cache_key": cache_key, "observed": observation}))
    slim = {
        "cache_version": "v1", "parser_identity": "p1",
        "cache_key": cache_key,
        "observed": {
            "body_span_sum_ms": sum(
                (float(row["body"]["end_ns"])
                 - float(row["body"]["start_ns"])) / 1e6
                for row in prefill_forwards),
            "forwards": [
                {"query_rows": row["query_rows"],
                 "context": row["context"],
                 "body": {"span_ms": (
                     float(row["body"]["end_ns"])
                     - float(row["body"]["start_ns"])) / 1e6}}
                for row in prefill_forwards]},
    }

    class FakeModule:
        __name__ = "fake_eval_a3_wave5"
        CACHE_ROOT = tmp_path
        PARSER_IDENTITY = "p1"

        @staticmethod
        def extract_or_load(capture_path, traits, template, seg_opts):
            return slim

        @staticmethod
        def predict_body(template, *, phase, tokens, context, sequences=1):
            return {"status": "modeled", "body_forward_span_ms": 1.0}

        @staticmethod
        def _atomic_write_json(path, payload):
            evaluation_io.atomic_write_json(path, payload)

    module = FakeModule()
    actual_import = wave5.importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == "eval_a3_wave5":
            return module
        return actual_import(name, *args, **kwargs)

    monkeypatch.setattr(wave5.importlib, "import_module", fake_import)
    traits = {"phase": "prefill", "context_tokens": 400000,
              "capture_path": str(A3_CSV)}
    path, payload = wave5._scoped_prefill_capture_worker((
        "a3", str(A3_CSV), traits, "template", a3_raw(), {}, False))
    assert path == str(A3_CSV)
    assert payload["status"] == "scoped"
    assert [row["geometry"]["tokens"] for row in payload["provenance"]] == [
        8064, 256]
    assert [row["declaration"]["moe_token_partition"]
            ["gather_output_materialization"]
            for row in payload["provenance"]] == ["per_rank_copy", "view"]
    assert len({row["key"] for row in payload["signatures"]}) == 2


def test_wave5_scoped_evaluate_short_circuits_only_the_prepared_capture():
    import wave5_generalization_eval as wave5

    class FakeModule:
        def __init__(self):
            self._scoped_results = {
                str(A3_CSV.resolve()): {"status": "precomputed",
                                        "path": str(A3_CSV)}}
            self.delegated = []

        def _unadapted_evaluate_heldout_capture(self, *args):
            self.delegated.append(args)
            return {"status": "fallback"}

    module = FakeModule()
    scoped = wave5._scoped_evaluate(
        module, A3_CSV, {"phase": "prefill"}, "tpl", {}, False, None,
        {}, "sig")
    assert scoped == {"status": "precomputed", "path": str(A3_CSV)}
    fallback = wave5._scoped_evaluate(
        module, A3_CSV.with_name("other.csv"), {"phase": "prefill"}, "tpl",
        {}, False, None, {}, "sig")
    assert fallback == {"status": "fallback"}
    assert len(module.delegated) == 1


def test_wave5_a5_scoped_evaluate_uses_the_same_prepared_capture():
    import wave5_generalization_eval as wave5

    class FakeModule:
        def __init__(self):
            self._scoped_results = {
                str(A5_4K_CSV.resolve()): {"status": "precomputed-a5"}}
            self.delegated = []

        def _unadapted_evaluate_capture(self, *args):
            self.delegated.append(args)
            return {"status": "fallback"}

    module = FakeModule()
    assert wave5._scoped_evaluate_capture(
        module, A5_4K_CSV, {"phase": "prefill"}, "tpl", {},
        {}, {}, "sig") == {"status": "precomputed-a5"}
    assert wave5._scoped_evaluate_capture(
        module, A5_4K_CSV.with_name("other.csv"), {"phase": "prefill"},
        "tpl", {}, {}, {}, "sig") == {"status": "fallback"}
    assert len(module.delegated) == 1


def test_real_a3_balanced_template_applies_caller_and_native_together():
    raw = b_raw()
    observation = load_json(A3_OBS)
    prepared = prepare_scoped_replay(
        raw, capture_path=A3_CSV, observation=observation,
        extract_missing=False)
    try:
        full, full_provenance = prepared.apply(
            raw, phase="prefill", tokens=8064, context=0)
        tail, tail_provenance = prepared.apply(
            raw, phase="prefill", tokens=256, context=399744)
    finally:
        prepared.release()
    assert full_provenance["scope_status"] == "applied"
    assert full_provenance["native_status"] == "applied"
    assert full_provenance["status"] == "applied"
    assert full_provenance["native"]["imported_rule_count"] == 4
    assert (full["runtime"]["kernels"]["moe_token_partition"]
            ["gather_output_materialization"]) == "per_rank_copy"
    assert tail_provenance["scope_status"] == "applied"
    assert (tail["runtime"]["kernels"]["moe_token_partition"]
            ["gather_output_materialization"]) == "view"


def test_real_a5_archive_template_replacement_applies(
        restored_sys_path, tmp_path):
    import wave5_generalization_eval as wave5

    archive = Path("/Volumes/data/mindie-sim-data/acceptance-archives-20261030"
                   "/wave5-eval")
    capture = Path("/Volumes/data/mindie-sim-data/a5/heldout_engine_20261031"
                   "/a5_synth_qwen30b_L8_E16_K4_tp4ep4_prefill_4k_c1"
                   "/kernel_details.csv")
    if not capture.is_file() or not (archive / "a5" / "eval_a5_wave5.py").is_file():
        pytest.skip("local A5 archive is not installed")
    module, _ = wave5._configure_chip(
        "a5", archive, tmp_path / "a5-cache", wave5.SIM_IDENTITY)
    traits = module.parse_capture_traits(capture)
    template, _policy = import_capture_policy(
        module._unadapted_resolve_template(traits)[1], capture_path=capture)
    prepared = prepare_scoped_replay(
        template, capture_path=A5_4K_CSV, observation=load_json(A5_4K_OBS),
        archive_template=True, extract_missing=False)
    try:
        result, provenance = prepared.apply(
            template, phase="prefill", tokens=4096, context=0,
            replace_recipe=True, archive_template=True)
    finally:
        prepared.release()
    if provenance["scope_reason"] == "sim_local_expert_reduce_recipe_unavailable":
        pytest.skip("installed Sim has no local_expert_reduce recipe")
    assert provenance["scope_status"] == "applied"
    assert provenance["scope"]["sim"]["reason"] == "generated_graph_matched"
    assert result["runtime"]["moe_recipe"] == "local_expert_reduce"


def test_balanced_grouped_mapping_is_exact_and_dimensions_still_rejected():
    from types import SimpleNamespace
    from capture_scoped_contracts import _op_summary

    def op(recipe, shape):
        return SimpleNamespace(
            layer=0, recipe=recipe, local_shape=shape, dtype="bf16",
            metadata={"matrix_weight_bank_groups": 32})

    summary = _op_summary([
        op("balanced_grouped_gate_up", (1008, 1024, 2048)),
        op("balanced_grouped_down", (1008, 2048, 512)),
        op("balanced_grouped_other", (1, 1, 1)),
    ])
    assert {row["recipe"] for row in summary[0]["grouped"]} == {
        "grouped_gate_up", "grouped_down"}
    raw = b_raw()
    mutated = deepcopy(raw)
    mutated["model"]["moe_intermediate_size"] = 1024
    prepared = prepare_scoped_replay(
        mutated, capture_path=A3_CSV, observation=load_json(A3_OBS),
        extract_missing=False)
    try:
        result, provenance = prepared.apply(
            mutated, phase="prefill", tokens=8064, context=0)
    finally:
        prepared.release()
    assert result == mutated
    assert provenance["scope_status"] != "applied"
    assert provenance["scope_reason"]


def test_prediction_cache_never_accepts_missing_or_foreign_identity(tmp_path):
    key = "a" * 64
    path = tmp_path / f"pred_{key}.json"
    path.write_text(json.dumps({"status": "modeled", "body_forward_span_ms": 1.0}), encoding="utf-8")
    assert read_prediction_cache(key, tmp_path) is None
    path.write_text(json.dumps({"status": "modeled", "prediction_identity": "b" * 64,
                                "body_forward_span_ms": 1.0}), encoding="utf-8")
    assert read_prediction_cache(key, tmp_path) is None
    path.write_text(json.dumps({"status": "modeled", "prediction_identity": key,
                                "body_forward_span_ms": 1.0}), encoding="utf-8")
    cached = read_prediction_cache(key, tmp_path)
    assert cached is not None and cached["body_forward_span_ms"] == 1.0


def test_dsh_materialize_scoped_jobs_schedules_offsets_and_signature_keys(tmp_path):
    from dsh_scoped_prefill import materialize_scoped_jobs

    observed = {"body_span_sum_ms": 1000.0, "forwards": [
        {"query_rows": 8064, "context": 0, "body": {"span_ms": 900.0}},
        {"query_rows": 256, "context": 399744,
         "body": {"span_ms": 100.0}}]}
    extraction = {
        "cache_version": "v1", "parser_identity": "p1", "cache_key": "k1",
        "full_cache_path": str(tmp_path / "full.json"),
        "observed": observed, "meta": {}}
    traits = {"phase": "prefill", "context_tokens": 400000,
              "cohort": "a3/test", "hw": "a3",
              "family": "qwen3.5-35b-a3b", "tp": 8, "dp": 1, "ep": 8,
              "spec_tokens": 0}
    signatures = [{"tokens": 8064, "context": 0, "key": "full-key"},
                  {"tokens": 256, "context": 399744, "key": "tail-key"}]
    for key in ("full-key", "tail-key"):
        (tmp_path / f"pred_{key}.json").write_text(json.dumps({
            "status": "modeled", "prediction_identity": key,
            "body_forward_span_ms": 500.0}))
    seen = []

    def run_pool(fn, items, workers):
        seen.extend(items)
        return {items[0].path: {
            "signatures": signatures,
            "context_offset": 0,
            "geometries": [{"tokens": 8064, "context": 0},
                           {"tokens": 256, "context": 399744}],
            "provenance": [
                {"geometry": {"tokens": 8064, "context": 0},
                 "status": "applied"},
                {"geometry": {"tokens": 256, "context": 399744},
                 "status": "applied"}]}}

    unscoped, results, pred_cache = materialize_scoped_jobs(
        heldout_tasks=[(A3_CSV, traits, "tpl", a3_raw(), {}, False,
                        "tplsig")],
        extractions={str(A3_CSV): extraction}, workers=1,
        sim_identity="sim", native_identity="native",
        cache_root=tmp_path, run_pool=run_pool)
    assert unscoped == {}
    assert len(seen) == 1 and len(seen[0].geometries) == 2
    assert str(A3_CSV) in results
    assert set(pred_cache) == {
        ("full-key", "prefill", 8064, 0, 1),
        ("tail-key", "prefill", 256, 399744, 1)}


def _genuine_a3_slim():
    observation = load_json(A3_OBS)
    prefill = [forward for forward in observation["forwards"]
               if forward.get("phase") == "prefill"]
    spans = [(float(row["body"]["end_ns"])
              - float(row["body"]["start_ns"])) / 1e6 for row in prefill]
    return {
        "body_span_sum_ms": sum(spans),
        "forwards": [
            {"query_rows": row["query_rows"], "context": row["context"],
             "body": {"span_ms": span}}
            for row, span in zip(prefill, spans)]}, spans


def test_wave5_materializer_scores_full_and_tail_with_original_timings(
        tmp_path, monkeypatch):
    import evaluation_io
    import wave5_generalization_eval as wave5

    slim_observed, spans = _genuine_a3_slim()
    observation = load_json(A3_OBS)
    observation["source_identity"] = {
        "path": str(A3_CSV), "size_bytes": A3_CSV.stat().st_size}
    cache_key = "a3-scored"
    (tmp_path / f"{cache_key}.json").write_text(json.dumps({
        "cache_version": "v1", "parser_identity": "p1",
        "cache_key": cache_key, "observed": observation}))
    slim = {"cache_version": "v1", "parser_identity": "p1",
            "cache_key": cache_key, "observed": slim_observed}
    traits = {"phase": "prefill", "context_tokens": 400000,
              "cohort": "a3/test", "hw": "a3",
              "family": "qwen3.5-35b-a3b", "tp": 8, "dp": 1, "ep": 8,
              "spec_tokens": 0, "capture_path": str(A3_CSV)}

    class FakeModule:
        __name__ = "fake_eval_a3_wave5"
        CACHE_ROOT = tmp_path
        PARSER_IDENTITY = "p1"
        _capture_policy_imports = {}
        _scoped_results = {}
        _scoped_capture_imports = {}

        @staticmethod
        def extract_or_load(capture_path, traits_arg, template, seg_opts):
            return slim

        @staticmethod
        def parse_capture_traits(path):
            return traits

        @staticmethod
        def _unadapted_resolve_template(traits_arg):
            return "template", a3_raw(), {}, False

        @staticmethod
        def predict_body(template, *, phase, tokens, context, sequences=1):
            return {"status": "modeled", "body_forward_span_ms": 1.0}

        @staticmethod
        def _atomic_write_json(path, payload):
            evaluation_io.atomic_write_json(path, payload)

        @staticmethod
        def _run_bounded_pool(fn, items, workers, **kwargs):
            result = {}
            for item in items:
                key, value = fn(item)
                result[key] = value
            return result

    module = FakeModule()
    actual_import = wave5.importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == "eval_a3_wave5":
            return module
        return actual_import(name, *args, **kwargs)

    monkeypatch.setattr(wave5.importlib, "import_module", fake_import)
    monkeypatch.setattr(wave5, "_capture_paths",
                        lambda hw, module_arg: [A3_CSV.resolve()])
    captured = []
    actual_scorer = wave5.score_prefill_capture

    def capture_scorer(*args, **kwargs):
        captured.append(args[4]["observed"])
        return actual_scorer(*args, **kwargs)

    monkeypatch.setattr(wave5, "score_prefill_capture", capture_scorer)
    wave5._materialize_scoped_prefill(module, "a3", 1)
    assert len(captured) == 1
    assert captured[0]["body_span_sum_ms"] == slim_observed["body_span_sum_ms"]
    assert [row["body"]["span_ms"] for row in captured[0]["forwards"]] == spans
    assert [row["context"] for row in captured[0]["forwards"]] == [0, 399744]
    path = str(A3_CSV.resolve())
    result = module._scoped_results[path]
    assert result["forward_count"] == 2
    assert result["observed_ms"] == round(sum(spans), 4)
    assert result["scoped_native_replay"]["capture_replaced"] is True
    declarations = [
        row["declaration"]["moe_token_partition"]
        ["gather_output_materialization"]
        for row in result["scoped_native_replay"]["geometries"]]
    assert declarations == ["per_rank_copy", "view"]
    assert module._scoped_capture_imports[path]["capture_replaced"] is True


def test_wave5_materializer_carries_a5_inferred_offset_into_score_plan(
        tmp_path, monkeypatch):
    import evaluation_io
    import wave5_generalization_eval as wave5

    full_observation = load_json(A5_64K_OBS)
    for forward in full_observation["forwards"]:
        forward.pop("context", None)
        forward.pop("context_tokens", None)
    full_observation["source_identity"] = {
        "path": str(A5_64K_CSV), "size_bytes": A5_64K_CSV.stat().st_size}
    cache_key = "a5-offset"
    (tmp_path / f"{cache_key}.json").write_text(json.dumps({
        "cache_version": "v1", "parser_identity": "p1",
        "cache_key": cache_key, "observed": full_observation}))
    full_rows = full_observation["forwards"]
    spans = [(float(row["body"]["end_ns"])
              - float(row["body"]["start_ns"])) / 1e6 for row in full_rows]
    slim_observed = {
        "body_span_sum_ms": sum(spans),
        "forwards": [
            {"query_rows": row["query_rows"],
             "body": {"span_ms": span}}
            for row, span in zip(full_rows, spans)]}
    slim = {"cache_version": "v1", "parser_identity": "p1",
            "cache_key": cache_key, "observed": slim_observed}
    traits = {"phase": "prefill", "context_tokens": 81920,
              "cohort": "a5/test", "hw": "a5",
              "family": "qwen3-30b-a3b", "tp": 4, "dp": 1, "ep": 4,
              "spec_tokens": 0, "capture_path": str(A5_64K_CSV)}

    class FakeModule:
        __name__ = "fake_eval_a5_wave5"
        CACHE_ROOT = tmp_path
        PARSER_IDENTITY = "p1"
        _capture_policy_imports = {}
        _scoped_results = {}
        _scoped_capture_imports = {}

        @staticmethod
        def extract_or_load(capture_path, traits_arg, template, seg_opts):
            return slim

        @staticmethod
        def parse_capture_traits(path):
            return traits

        @staticmethod
        def _unadapted_resolve_template(traits_arg):
            return "template", a5_raw(), {}, False

        @staticmethod
        def predict_body(template, *, phase, tokens, context, sequences=1):
            return {"status": "modeled", "body_forward_span_ms": 1.0}

        @staticmethod
        def _atomic_write_json(path, payload):
            evaluation_io.atomic_write_json(path, payload)

        @staticmethod
        def _run_bounded_pool(fn, items, workers, **kwargs):
            result = {}
            for item in items:
                key, value = fn(item)
                result[key] = value
            return result

    module = FakeModule()
    actual_import = wave5.importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == "eval_a5_wave5":
            return module
        return actual_import(name, *args, **kwargs)

    monkeypatch.setattr(wave5.importlib, "import_module", fake_import)
    monkeypatch.setattr(wave5, "_capture_paths",
                        lambda hw, module_arg: [A5_64K_CSV.resolve()])
    wave5._materialize_scoped_prefill(module, "a5", 1)
    path = str(A5_64K_CSV.resolve())
    record = module._scoped_capture_imports[path]
    recipe_missing = "sim_local_expert_reduce_recipe_unavailable" in (
        record.get("scope_reasons") or [])
    if not record.get("capture_replaced"):
        if recipe_missing:
            pytest.skip("installed Sim has no local_expert_reduce recipe")
        raise AssertionError(record)
    result = module._scoped_results[path]
    assert result["forward_count"] == 8
    assert result["observed_ms"] == round(sum(spans), 4)
    contexts = [row["geometry"]["context"]
                for row in result["scoped_native_replay"]["geometries"]]
    assert contexts == [16384 + 8192 * index for index in range(8)]


def test_wave5_explicit_authoritative_context_mismatch_fails_before_pricing(
        tmp_path, monkeypatch):
    import wave5_generalization_eval as wave5

    slim_observed, _spans = _genuine_a3_slim()
    slim_observed["forwards"][1]["context"] = 123456
    observation = load_json(A3_OBS)
    observation["source_identity"] = {
        "path": str(A3_CSV), "size_bytes": A3_CSV.stat().st_size}
    cache_key = "a3-conflict"
    (tmp_path / f"{cache_key}.json").write_text(json.dumps({
        "cache_version": "v1", "parser_identity": "p1",
        "cache_key": cache_key, "observed": observation}))
    slim = {"cache_version": "v1", "parser_identity": "p1",
            "cache_key": cache_key, "observed": slim_observed}

    class FakeModule:
        __name__ = "fake_eval_a3_wave5"
        CACHE_ROOT = tmp_path
        PARSER_IDENTITY = "p1"

        @staticmethod
        def extract_or_load(capture_path, traits_arg, template, seg_opts):
            return slim

        @staticmethod
        def predict_body(*args, **kwargs):
            raise AssertionError("priced_before_explicit_context_check")

        @staticmethod
        def _atomic_write_json(*args, **kwargs):
            raise AssertionError("cached_before_explicit_context_check")

    module = FakeModule()
    actual_import = wave5.importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == "eval_a3_wave5":
            return module
        return actual_import(name, *args, **kwargs)

    monkeypatch.setattr(wave5.importlib, "import_module", fake_import)
    with pytest.raises(ValueError, match="wave5_scoped_explicit_context_mismatch"):
        wave5._scoped_prefill_capture_worker((
            "a3", str(A3_CSV),
            {"phase": "prefill", "context_tokens": 400000},
            "template", a3_raw(), {}, False))
    assert not list(tmp_path.glob("pred_*.json"))
