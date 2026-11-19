"""Five-domain SKU microbench registry, routing laws, resume and portability.

[Role]
  Verify the pure case registry (all five domains, the frozen held-out split,
  the ``M`` knee, narrow-``N`` split-K and layout variants), the integer
  ``group_list`` laws, the ``40..50`` active ``4 MiB`` expert cache-spill
  sweep, attention/state geometry, the bounded injective PLE remap, the
  append-only ``--resume`` log and the sanitized ``capture://`` receipts.

[Invariants]
  * Native FP8 Cube is refused on A2/A3 and never constructed.
  * Every ``group_list`` is an integer list that conserves tokens.

[Timeouts & Locks]
  Pure in-memory work plus bounded file I/O under ``tmp_path``/``/tmp``.

[Side-Effect Policy]
  Writes only pytest ``tmp_path`` and registered short-lived temp workspaces.
"""

from __future__ import annotations

import json

import pytest

from mindie_profiler.bench import bench_sku_microbench as sku
from mindie_profiler.bench.observations import IDENTITY_FIELDS, observation_row
from mindie_profiler.events import ProfilerUsageError


def test_registry_covers_all_five_domains_with_unique_ids():
    cases = sku.build_cases()
    assert {case["domain"] for case in cases} == {1, 2, 3, 4, 5}
    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids))
    for case in cases:
        assert case["schema"] == sku.CASE_SCHEMA
        assert case["split"] in {"train", "heldout"}
        assert case["timing"]["startup_ms"] == 0.0
        assert case["timing"]["inclusive_minimum"] is True
        assert case["dtype"] in sku.SUPPORTED_DTYPES or case["domain"] == 1


def test_native_fp8_and_foreign_sku_are_refused():
    for dtype in ("fp8", "fp8_e4m3", "mxfp8", "mxfp4", "hif8"):
        with pytest.raises(ProfilerUsageError, match="bench_native_fp8_unsupported"):
            sku.build_cases(dtypes=[dtype])
    with pytest.raises(ProfilerUsageError, match="bench_sku_unsupported"):
        sku.build_cases(sku="DAV_3510")
    with pytest.raises(ProfilerUsageError, match="bench_dtype_unsupported"):
        sku.build_cases(dtypes=["fp32"])
    with pytest.raises(ProfilerUsageError, match="bench_domain_unknown"):
        sku.build_cases(domain=9)


def test_domain1_ops_are_the_inclusive_completion_minima():
    cases = sku.build_cases(domain=1)
    assert {case["op"] for case in cases} == {
        "empty_event_pair", "empty_aic", "empty_aiv", "vector_add",
        "cube_matmul", "rms_norm", "w8a8_matmul"}
    vector = next(case for case in cases if case["op"] == "vector_add")
    assert vector["shape"] == {"tokens": 1, "width": 1}
    cube = next(case for case in cases if case["op"] == "cube_matmul")
    assert cube["shape"] == {"m": 1, "n": 16, "k": 16}
    w8a8 = next(case for case in cases if case["op"] == "w8a8_matmul")
    assert w8a8["shape"]["per_column_scale"] == [128]
    assert w8a8["shape"]["per_token_scale"] == [1]


def test_domain2_m_knee_narrow_n_and_layouts():
    cases = sku.build_cases(domain=2, dtypes=["bf16", "fp16", "int8", "w4a8"])
    assert len([c for c in cases if c["case_id"].startswith("d2.gemm.")]) == 4 * 3
    knee = [c for c in cases if c["case_id"].startswith("d2.mknee.bf16")]
    m_values = sorted(case["shape"]["m"] for case in knee)
    assert set(2 ** exponent for exponent in range(13)) <= set(m_values)
    for held in sku.HELDOUT_M:
        assert held in m_values
        assert next(c for c in knee if c["shape"]["m"] == held)["split"] == "heldout"
    assert next(c for c in knee if c["shape"]["m"] == 8)["split"] == "train"
    narrow = [c for c in cases if c["case_id"].startswith("d2.splitk.bf16")]
    assert sorted(case["shape"]["n"] for case in narrow) == list(sku.NARROW_N)
    assert all(case["split_k"] is True for case in narrow)
    nz = [c for c in cases if c.get("layout") == "FRACTAL_NZ"]
    assert nz and all(case["format_code"] == 29 for case in nz)
    assert all(case["prepared_outside_timing"] is True for case in nz)
    mte2 = [c for c in cases if c["op"].startswith("mte2_")]
    assert {case["residency"] for case in mte2} == {"dram", "l2"}
    assert {case["owners"] for case in mte2} == {"one_owner", "full_owner"}
    assert all(case["consumed_result"] is True for case in mte2)
    assert all(item["dtype"] != "fp8" for item in cases)


def test_uniform_and_zipf_histograms_conserve_tokens():
    assert sku.uniform_counts(8, 10) == [2, 2, 1, 1, 1, 1, 1, 1]
    assert sum(sku.zipf_counts(32, 4096)) == 4096
    counts = sku.zipf_counts(16, 1024)
    assert counts == sorted(counts, reverse=True)
    assert len(sku.zipf_counts(16, 1024, exponent=1.2)) == 16
    fractions = {family["zero_fraction"] for family in sku.routing_distributions(32, 256)}
    assert fractions == {0.0, 0.25, 0.5, 0.75}
    for family in sku.routing_distributions(32, 256):
        assert all(isinstance(item, int) for item in family["group_list"])
        assert sum(family["group_list"]) == 256
        zeros = sum(1 for item in family["group_list"] if item == 0)
        assert zeros >= int(round(family["zero_fraction"] * 32))


def test_domain3_group_lists_are_integers_with_group_list_type_one():
    cases = sku.build_cases(domain=3)
    for case in cases:
        group = case["group_list"]
        assert isinstance(group, list) and group
        assert all(isinstance(item, int) and not isinstance(item, bool) for item in group)
        assert all(item >= 0 for item in group)
        assert sum(group) == case["shape"]["m"]
        assert case["group_list_type"] == 1
        assert case["integer_group_list"] is True
        assert case["per_token_scale"] is True
    assert {case["distribution"] for case in cases if "distribution" in case} == {
        "uniform", "zipf_s1.2"}


def test_cache_spill_sweep_spans_160_to_200_mib():
    spill = [case for case in sku.build_cases(domain=3)
             if case["case_id"].startswith("d3.spill.")]
    assert [case["active_experts"] for case in spill] == list(range(40, 51))
    assert spill[0]["l2_span_mib"] == 160
    assert spill[-1]["l2_span_mib"] == 200
    for case in spill:
        assert case["shape"]["expert_bytes"] == sku.SPILL_EXPERT_BYTES == 4 * sku.MIB
        assert case["shape"]["e"] == 64
        assert sum(case["group_list"]) == case["active_experts"]
        assert case["work_bytes"] == case["active_experts"] * sku.SPILL_EXPERT_BYTES
        assert case["covers_mib"] == [160, 200]


def test_domain4_absorbed_mla_uses_one_1152_byte_backing():
    cases = sku.build_cases(domain=4, dtypes=["bf16"])
    assert {case["op"] for case in cases} == {
        "npu_fusion_attention", "npu_fused_infer_attention_score",
        "npu_incre_flash_attention", "absorbed_mla",
        "npu_chunk_gated_delta_rule", "chunk_kda_fwd",
        "causal_conv1d_update", "lightning_indexer"}
    mla = next(case for case in cases if case["op"] == "absorbed_mla")
    assert mla["shape"]["kv_bytes_per_token"] == 1152 == sku.MLA_KV_BYTES_PER_TOKEN
    assert mla["c_kv_bytes_per_token"] == 1152
    assert mla["backing_buffers"] == 1
    assert mla["latent_split"] == [512, 64]
    fia = next(case for case in cases if case["op"] == "npu_fused_infer_attention_score")
    assert fia["block_size"] == 128 and fia["paged"] is True
    ifa = next(case for case in cases if case["op"] == "npu_incre_flash_attention")
    assert ifa["legacy_paged_binding"] is True


def test_domain5_rmw_gather_pcie_and_ple_rows():
    cases = sku.build_cases(domain=5, dtypes=["bf16", "int8"])
    contention = {case["contention"] for case in cases if case["op"] == "index_add_"}
    assert contention == {"shared_cacheline", "disjoint_cacheline"}
    shared = next(case for case in cases if case["contention"] == "shared_cacheline")
    assert shared["indices_per_cacheline"] == sku.CACHELINE_BYTES // 4
    gather = [case for case in cases if case["op"] == "gather"]
    assert all(case["stride_bytes"] == 128 for case in gather)
    copies = [case for case in cases if case["op"] == "pinned_copy"]
    assert {case["direction"] for case in copies} == {"h2d", "d2h"}
    assert all(case["pinned"] is True for case in copies)
    assert all(case["case_id"].startswith("d5.host_io.") and "pcie" not in case["case_id"] for case in copies)
    a2_copies = [c for c in sku.build_cases(domain=5, sku="Ascend910B4", dtypes=["bf16"]) if c["op"] == "pinned_copy"]
    a3_copies = [c for c in sku.build_cases(domain=5, sku="Ascend910_9362", dtypes=["bf16"]) if c["op"] == "pinned_copy"]
    assert all(c["transfer_protocol"] == "pcie_dma" for c in a2_copies)
    assert all(c["transfer_protocol"] == "hccs_dma" for c in a3_copies)
    ple = [case for case in cases if case["op"] == "ple_lookup"]
    rows = {case["dtype"]: case["shape"]["row_bytes"] for case in ple}
    assert rows == {"bf16": sku.PLE_BF16_ROW_BYTES, "int8": sku.PLE_INT8_ROW_BYTES}
    assert all(case["remap_injective"] is True for case in ple)
    assert {case["path"] for case in ple} == {"uva_gather", "pinned_h2d"}
    assert {case["reuse"] for case in ple} == {"repeated", "rotating"}


def test_bounded_row_remap_is_injective_and_bounded():
    remap = sku.bounded_row_remap([5, 5, 9, 1], span=8)
    assert remap["rows"] == [1, 5, 9]
    assert remap["injective"] is True
    assert sorted(remap["slots"].values()) == [0, 1, 2]
    with pytest.raises(ProfilerUsageError, match="bench_ple_span_too_small"):
        sku.bounded_row_remap(range(10), span=3)


class FakeProtocol:
    def __init__(self):
        self.calls = []

    def run(self, enqueue, *, case_id, kind, nbytes, blocker=None,
            blocker_receipt=None, stream=None):
        self.calls.append(case_id)
        enqueue()
        return {"schema": "mindie-bench-timing/1", "case_id": case_id,
                "minimum_ms": 0.001, "startup_ms": 0.0,
                "modes": {"eager": {"median_us": 1.0}}, "qualified": True}


def _record(**overrides):
    payload = {"schema": "mindie-bench-receipt/1", "case_id": "d1.empty.event_pair",
               "domain": 1, "op": "empty_event_pair", "dtype": "none",
               "split": "train", "status": "ok", "minimum_ms": 0.001,
               "work_bytes": 0, "work_flops": 0, "group_list": None,
               "group_list_type": None,
               "source_uri": "capture://bench-sku/d1.empty.event_pair"}
    payload.update(overrides)
    return payload


def test_jsonl_sink_is_append_only_and_ignores_a_torn_tail(tmp_path):
    path = tmp_path / "trials.jsonl"
    sink = sku.JsonlSink(path)
    sink.append(_record())
    sink.append(_record(case_id="d1.vector.bf16.1"))
    assert sink.completed_case_ids() == {"d1.empty.event_pair", "d1.vector.bf16.1"}
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"case_id": "torn"')
    assert sink.completed_case_ids() == {"d1.empty.event_pair", "d1.vector.bf16.1"}
    assert json.loads(path.read_text().splitlines()[0])["case_id"] == (
        "d1.empty.event_pair")


def test_run_cases_resumes_only_completed_records(tmp_path):
    resume = tmp_path / "trials.jsonl"
    sku.JsonlSink(resume).append(_record())
    case = next(case for case in sku.build_cases(domain=1)
                if case["case_id"] == "d1.empty.event_pair")
    protocol = FakeProtocol()
    context = {"protocol": protocol, "torch": object(),
               "device": {"ordinal": 0}}
    result = sku.run_cases([case], context=context, resume=resume)
    assert result["skipped_case_ids"] == ["d1.empty.event_pair"]
    assert result["executed_case_count"] == 0

    other = next(case for case in sku.build_cases(domain=1)
                 if case["case_id"] == "d1.empty.aic_launch")
    result = sku.run_cases([other], context=context, resume=resume)
    assert result["executed_case_count"] == 1
    assert result["records"][0]["source_uri"] == (
        "capture://bench-sku/d1.empty.aic_launch")
    assert json.loads(resume.read_text().splitlines()[-1])["case_id"] == (
        "d1.empty.aic_launch")


def test_receipts_never_contain_home_address_device_or_image_digest():
    protocol = FakeProtocol()
    context = {"protocol": protocol,
               "torch": type("T", (), {"npu": None})(),
               "device": {"ordinal": 0}}
    case = next(case for case in sku.build_cases(domain=1)
                if case["case_id"] == "d1.empty.event_pair")
    result = sku.run_cases([case], context=context, home="/home/someone")
    text = json.dumps(result["records"])
    assert "/home/someone" not in text
    assert "/dev/davinci" not in text
    assert "@sha256:" not in text


def test_unavailable_builder_is_reported_without_a_fabricated_duration():
    protocol = FakeProtocol()
    context = {"protocol": protocol,
               "torch": type("T", (), {})(),
               "device": {"ordinal": 0}}
    case = _case_for_builder("mte2_transfer")
    record = sku._run_one(case, context=context, protocol=protocol, home=None)
    assert record["status"] == "unsupported_binding"
    assert "bench_native_probe_absent" in record["reason"]
    assert "timing" not in record


def _case_for_builder(builder):
    return {"schema": sku.CASE_SCHEMA, "case_id": f"test.{builder}", "domain": 2,
            "op": "mte2_aic", "dtype": "bf16", "builder": builder,
            "shape": {"bytes": 4096}, "split": "train", "work_bytes": 4096,
            "work_flops": 0, "residency": "dram", "owners": "one_owner"}


def test_cli_dry_run_emits_the_frozen_registry_without_torch(capsys):
    assert sku.main(["--dry-run", "--domain", "2", "--dtype", "bf16"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry_run"
    assert payload["sku"] == sku.DAV_2201
    assert payload["case_count"] > 0
    assert all(case["domain"] == 2 for case in payload["cases"])
    assert all(case["dtype"] == "bf16" for case in payload["cases"])


def test_cli_dry_run_limit_and_portable_stdout(capsys):
    assert sku.main(["--dry-run", "--limit", "3"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["case_count"] == 3
    assert "/dev/davinci" not in json.dumps(payload)


def test_w4a8_weight_bytes_pack_two_elements_per_byte():
    m, n, k = 4096, 4096, 4096
    expected = m * k + k * n // 2 + m * n * 2
    assert sku._gemm_bytes("w4a8", m, n, k) == expected
    case = next(case for case in sku.build_cases(domain=2, dtypes=["w4a8"])
                if case["case_id"] == "d2.gemm.w4a8.4096x4096x4096")
    assert case["work_bytes"] == expected


def test_dtype_filters_apply_to_domain1_and_ple_cases():
    domain1 = sku.build_cases(domain=1, dtypes=["bf16"])
    assert {case["dtype"] for case in domain1} == {"none", "bf16"}
    ple = sku.ple_cases(["int8"])
    assert {case["dtype"] for case in ple} == {"int8"}
    assert all(case["shape"]["row_bytes"] == sku.PLE_INT8_ROW_BYTES for case in ple)


def test_jsonl_sink_repairs_a_torn_tail_before_appending(tmp_path):
    path = tmp_path / "trials.jsonl"
    sink = sku.JsonlSink(path)
    sink.append(_record())
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"case_id": "torn"')
    sink.append(_record(case_id="d1.vector.bf16.1"))
    lines = path.read_text().splitlines()
    assert [json.loads(line)["case_id"] for line in lines] == [
        "d1.empty.event_pair", "d1.vector.bf16.1"]
    assert sink.completed_case_keys() == {
        (None, "d1.empty.event_pair"), (None, "d1.vector.bf16.1")}


class ObservationProtocol:
    repeats = 2

    def __init__(self):
        self.calls = 0

    def run(self, enqueue, *, case_id, kind, nbytes, blocker=None,
            blocker_receipt=None, stream=None):
        self.calls += 1
        enqueue()
        return {"schema": "mindie-bench-timing/1", "case_id": case_id,
                "protocol": "warmups + trials x repeats device events",
                "minimum_ms": 0.0015, "qualified": True,
                "modes": {"eager": {"trials": [
                    {"trial": 0, "repeats_us": [1000.0, 2000.0],
                     "enqueue_us_samples": [1.0, 2.0]}]}}}


def test_observations_emit_repeat_rows_and_case_complete(tmp_path):
    journal = tmp_path / "observations.jsonl"
    case = next(case for case in sku.build_cases(domain=1)
                if case["case_id"] == "d1.empty.event_pair")
    protocol = ObservationProtocol()
    result = sku.run_cases(
        [case], context={"protocol": protocol, "torch": object(),
                         "device": {"ordinal": 0}},
        observations=journal, sku=sku.DAV_2201)
    assert result["executed_case_count"] == 1
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    assert [row["record_type"] for row in rows] == [
        "observation", "observation", "case_complete"]
    first = rows[0]
    assert first["schema"] == "mindie-bench-observation/1"
    assert first["case_id"] == "d1.empty.event_pair"
    assert first["split"] == case["split"]
    assert first["status"] == "ok" and first["validated"] is True
    assert first["qualified"] is True
    assert first["duration_ms"] == pytest.approx(1.0)
    assert first["source"].startswith("capture://bench-sku/")
    assert set(first["identity"]) == {
        "level", "boundary", "hardware", "implementation", "phase", "shape",
        "dtype", "layout", "execution"}
    assert set(first["key"]) == {
        "hardware", "implementation", "kernel", "dtype", "shape", "scope"}
    assert "work_bytes" not in first  # zero-byte cases omit the facet
    assert rows[0]["sample_id"] != rows[1]["sample_id"]
    assert rows[2]["status"] == "ok" and rows[2]["sku"] == sku.DAV_2201


class _Journal:
    def __init__(self):
        self.rows = []

    def append(self, record):
        self.rows.append(record)


def _timed_record():
    return {"status": "ok", "validated": True, "qualified": True,
            "timing": {"protocol": "device events",
                       "modes": {"eager": {"trials": [
                           {"trial": 0, "repeats_us": [1000.0]}]}}}}


def test_observation_row_applies_plan_identities_and_execution_mode():
    case = {"case_id": "d1.empty.event_pair", "split": "train"}
    accuracy = {field: field for field in IDENTITY_FIELDS}
    accuracy["execution"] = {"mode": "eager", "stage": "s0_local"}
    row = observation_row(
        plan_id="plan-1", case=case, run_id="run-1", split="train",
        boundary="device_kernel", timing_mode="aclgraph", residency="device",
        trial=0, repeat_index=1, rank=None, duration_ms=1.0,
        source="capture://bench/row", identity_override=accuracy,
        service_identity={"resource": "cube", "work_unit": "flops"})
    assert row["identity"]["hardware"] == "hardware"
    assert row["identity"]["execution"] == {"mode": "aclgraph",
                                            "stage": "s0_local"}
    assert row["service_identity"] == {"resource": "cube",
                                       "work_unit": "flops"}
    assert accuracy["execution"]["mode"] == "eager"
    partial = observation_row(
        plan_id="plan-1", case=case, run_id="run-1", split="train",
        boundary="device_kernel", timing_mode="eager", residency="device",
        trial=0, repeat_index=0, rank=None, duration_ms=1.0,
        source="capture://bench/row", identity_override={"level": "operator"})
    assert set(partial["identity"]) == set(IDENTITY_FIELDS)
    assert "service_identity" not in partial


def test_sku_observations_emit_work_bytes_only_on_byte_rate_ops():
    journal = _Journal()
    cases = sku.build_cases()
    gemm = next(case for case in cases
                if case["case_id"] == "d2.gemm.bf16.4096x4096x4096")
    sku._emit_observations(journal, gemm, _timed_record(), sku.DAV_2201, "run")
    assert "work_bytes" not in journal.rows[0]
    assert "work" not in journal.rows[0]
    for op in ("pinned_copy", "ple_lookup", "gather", "mte2_aic", "mte2_aiv"):
        case = next(item for item in cases if item["op"] == op)
        journal.rows.clear()
        sku._emit_observations(journal, case, _timed_record(), sku.DAV_2201,
                               "run")
        assert journal.rows[0]["work_bytes"] == case["work_bytes"] > 0


def test_mknee_observations_emit_cube_flops_facets_for_fit_service():
    journal = _Journal()
    knee = next(case for case in sku.build_cases(domain=2, dtypes=["bf16"])
                if case["case_id"].startswith("d2.mknee."))
    sku._emit_observations(journal, knee, _timed_record(), sku.DAV_2201, "run")
    row = journal.rows[0]
    assert row["work"] == knee["work_flops"] > 0
    assert (row["resource"], row["work_unit"], row["active_units"]) == (
        "cube", "flops", 1)
    assert "work_bytes" not in row
    assert row["identity"]["execution"] == {"mode": "eager",
                                            "protocol": "device events"}


def test_resume_recovers_completed_sku_case_keys(tmp_path):
    resume = tmp_path / "resume.jsonl"
    case = next(case for case in sku.build_cases(domain=1)
                if case["case_id"] == "d1.empty.event_pair")
    context = {"protocol": ObservationProtocol(), "torch": object(),
               "device": {"ordinal": 0}}
    first = sku.run_cases([case], context=context, resume=resume,
                          sku=sku.DAV_2201)
    assert first["recovered_records"] == 0
    second = sku.run_cases([case], context=context, resume=resume,
                           sku=sku.DAV_2201)
    assert second["recovered_records"] == 1
    assert second["skipped_case_ids"] == ["d1.empty.event_pair"]
    assert second["executed_case_count"] == 0


def test_over_budget_case_is_not_built():
    class Protocol:
        def run(self, *args, **kwargs):  # pragma: no cover - must not run
            raise AssertionError("over-budget case was executed")

    case = next(case for case in sku.build_cases(domain=2, dtypes=["bf16"])
                if case["case_id"] == "d2.gemm.bf16.4096x4096x4096")
    record = sku._run_one(case, context={"protocol": Protocol(),
                                         "torch": object(),
                                         "budget": {"cap_bytes": 1024}},
                          protocol=Protocol(), home=None, sku=sku.DAV_2201)
    assert record["status"] == "over_budget"
    assert "timing" not in record
