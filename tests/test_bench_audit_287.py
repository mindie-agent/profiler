"""Regression coverage for bench audits #287 and #301 using CPU-only device stand-ins."""

import json
from pathlib import Path

import pytest

from mindie_profiler.bench import bench_archetype_subgraphs as sub
from mindie_profiler.bench import bench_sku_microbench as sku
from mindie_profiler.bench import timing
from mindie_profiler.bench.operators import build_operator_enqueue
from mindie_profiler.events import ProfilerUsageError
from tests.test_bench_archetype_subgraphs import FakeJointRuntime, _case, _node, _plan
from tests.test_bench_operators import FakeBackend, FakeTensor
from tests.test_bench_sku_rc2 import TimingProtocol
from tests.test_bench_timing_protocol import FakeTorch


def _operator(node_id, builder, **shape):
    return {**_node(node_id, op=builder, builder=builder), "dtype": "bf16", "shape": shape}


@pytest.mark.parametrize(("builder", "requested", "actual"), [
    ("rms_norm", {"tokens": 32768, "width": 32768}, {"tokens": 256, "width": 128}),
    ("indexer_topk", {"tokens": 4, "width": 16, "top_k": 1024}, {"tokens": 4, "width": 16, "top_k": 16}),
    ("matmul", {"m": 0, "n": 8, "k": 16}, {"m": 1, "n": 8, "k": 16}),
])
def test_sku_receipts_report_resolved_dimensions_and_refuse_mismatched_timing(builder, requested, actual):
    backend = FakeBackend()
    context = {"torch": backend.torch, **backend.context()}
    case = {**_operator("node", builder, **requested), "case_id": builder, "domain": 1, "split": "train"}
    protocol = TimingProtocol()
    receipt = sku._run_one(case, context=context, protocol=protocol, home=None)
    assert receipt["requested_shape"] == requested
    assert {key: receipt["actual_shape"][key] for key in actual} == actual
    assert receipt["reason"] == "bench_requested_shape_mismatch"
    assert receipt["timing_invoked"] is False and protocol.calls == []
    build_operator_enqueue(backend.torch, case, context)()
    _, args, _ = backend.calls[-1]
    if builder == "matmul":
        assert args[0].shape == (actual["m"], actual["k"])
        assert args[2].shape == (actual["m"], actual["n"])
    else:
        assert args[0].shape == (actual["tokens"], actual["width"])
        if builder == "indexer_topk":
            assert args[1] == actual["top_k"]


def test_kv_compress_epilog_records_resolved_cache_dimensions_and_dtype():
    backend = FakeBackend()
    context = backend.context(_actual_shape={})
    case = {**_operator("node", "kv_compress_epilog", tokens=4, width=8, seq_len=2), "dtype": "fp16"}
    build_operator_enqueue(backend.torch, case, context)()
    _, (source, cache, indices), _ = backend.calls[-1]
    assert source.shape == cache.shape == (4, 8)
    assert source.dtype is cache.dtype is backend.torch.float16
    assert indices.shape == (4,) and indices.dtype is backend.torch.int32
    assert context["_actual_shape"] == {"tokens": 4, "width": 8, "seq_len": 4, "dtype": "fp16"}


def test_swiglu_records_resolved_dimensions_and_dtype():
    backend = FakeBackend()
    context = backend.context(_actual_shape={})
    case = {**_operator("node", "swiglu", tokens=4, width=8), "dtype": "fp16"}
    build_operator_enqueue(backend.torch, case, context)()
    _, (source,), _ = backend.calls[-1]
    assert source.shape == (4, 16) and source.dtype is backend.torch.float16
    assert context["_actual_shape"] == {"tokens": 4, "width": 8, "dtype": "fp16"}


@pytest.mark.parametrize(("dtype", "input_name", "weight_name"), [
    ("bf16", "bf16", "bf16"),
    ("int8", "int8", "int8"),
    ("w4a8", "int8", "int32"),
])
def test_grouped_matmul_records_dispatched_input_and_weight_dtypes(dtype, input_name, weight_name):
    backend = FakeBackend()
    context = backend.context(_actual_shape={})
    case = {**_operator("node", "grouped_matmul", m=4, n=8, k=16, e=2), "dtype": dtype}
    build_operator_enqueue(backend.torch, case, context)()
    _, ([source], weights), _ = backend.calls[-1]
    dtype_attr = {"bf16": "bfloat16", "int8": "int8", "int32": "int32"}
    assert source.dtype is getattr(backend.torch, dtype_attr[input_name])
    assert all(weight.dtype is getattr(backend.torch, dtype_attr[weight_name]) for weight in weights)
    assert context["_actual_shape"] == {
        "m": 4, "n": 8, "k": 16, "e": 2, "matrix_groups": 2,
        "dtype": input_name, "weight_dtype": weight_name,
    }


@pytest.mark.parametrize("include", [[], ["typo"], ["first", "typo"]])
def test_both_stages_reject_invalid_timed_node_selections(include):
    case = _case(nodes=[_node("first")], edges=[], boundary={"include": include})
    ordered = sub.topological_order(case)
    for cut in (sub.plan_timed_cut, sub._joint_split):
        with pytest.raises(ValueError, match="timed_window_empty|include_unknown"):
            cut(case, ordered)
    backend = FakeBackend()
    with pytest.raises(ValueError, match="timed_window_empty|include_unknown"):
        sub.run_plan(_plan([case]), protocol=TimingProtocol(),
                     executor=sub.OperatorExecutor(backend.torch, backend.context()))


def test_duplicate_node_ids_are_rejected_before_execution():
    case = _case(nodes=[_node("same"), _node("same")], edges=[])
    with pytest.raises(ValueError, match="duplicate_node_id"):
        sub.validate_plan(_plan([case]))


def test_all_gather_queries_the_selected_group_on_injected_dist():
    backend = FakeBackend()
    group = backend.dist.group
    sizes = []

    def world_size(selected):
        sizes.append(selected)
        return 4 if selected is group else 16

    backend.dist.get_world_size = world_size
    context = backend.context(_actual_shape={})
    build_operator_enqueue(backend.torch, {
        "op": "all_gather", "group": "tp", "nbytes": 4096, "dtype": "bf16",
    }, context)()
    _, (out, inp), kwargs = backend.calls[-1]
    assert sizes == [group] and kwargs["group"] is group
    assert inp.shape == (2048,) and out.shape == (8192,)
    assert context["_actual_shape"]["group_size"] == 4


@pytest.mark.parametrize(("l2_mib", "plan_qualified", "required_mib", "qualified"), [
    pytest.param(96, None, 288, False, id="insufficient-touched-bytes"),
    pytest.param(64, False, 192, False, id="unqualified-ring-plan"),
    pytest.param(64, True, 192, True, id="qualified-coverage"),
])
def test_all_reduce_cold_coverage_qualifies_receipt_and_all_samples(
    tmp_path, l2_mib, plan_qualified, required_mib, qualified,
):
    backend = FakeBackend()
    mib = timing.MIB
    plan = timing.cold_ring_plan(l2_mib * mib)
    if plan_qualified is not None:
        plan["qualified"] = plan_qualified
    ring = timing.ColdRing(backend.torch, plan, ordinal=0).allocate()
    clock = FakeTorch()
    all_reduce = backend.dist.all_reduce

    def timed_all_reduce(*args, **kwargs):
        clock.clock.ms += 0.1
        return all_reduce(*args, **kwargs)

    backend.dist.all_reduce = timed_all_reduce
    protocol = timing.MeasurementProtocol(timing.TorchTimingRuntime(clock), warmups=0, trials=2, repeats=2)
    context = backend.context(torch=backend.torch, protocol=protocol, ring=ring, budget={"cap_bytes": 500 * mib})
    case = {
        "case_id": "all_reduce.96mib", "domain": 3, "op": "all_reduce", "split": "train",
        "dtype": "bf16", "shape": {"bytes": 96 * mib}, "work_bytes": 96 * mib,
    }
    journal = tmp_path / "all-reduce.jsonl"
    result = sku.run_cases([case], context=context, observations=journal, sku=sku.DAV_2201)
    receipt = result["records"][0]
    assert receipt["status"] == "ok" and receipt["timing"]["qualified"] is True
    assert receipt["qualified"] is qualified
    assert receipt["cold_coverage"] == {
        "touched_bytes": 192 * mib, "required_bytes": required_mib * mib, "qualified": qualified,
    }
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    samples = [row for row in rows if row["record_type"] == "observation"]
    assert len(samples) == 4
    assert all(row["qualified"] is qualified for row in samples)
    assert rows[-1]["summary"]["qualified"] is qualified
    assert rows[-1]["summary"]["cold_coverage"] == receipt["cold_coverage"]


@pytest.mark.parametrize("stage", ["s0_local", "s1_joint"])
def test_subgraph_journal_keeps_every_node_shape_and_marks_the_unblocked_wall_span(tmp_path, stage):
    from tests.test_bench_timing_protocol import FakeTensor as ClockTensor

    torch = FakeTorch()
    torch.ones = lambda *shape, **_kwargs: ClockTensor(shape)
    calls = []

    def rms(x, *_args):
        torch.clock.ms += 0.01 if len(calls) % 2 == 0 else 0.11
        output = ClockTensor(x.shape)
        calls.append((x, output))
        return output, None

    executor = sub.OperatorExecutor(torch, {"op_overrides": {"rms_norm": rms}})
    protocol = timing.MeasurementProtocol(timing.TorchTimingRuntime(torch), warmups=0, trials=1, repeats=2)
    dims = {"tokens": 4, "width": 8}
    nodes = [_operator(node, "rms_norm", **dims) for node in ("first", "second")]
    case = {**_case(nodes=nodes, edges=[{"from": "first", "to": "second", "kind": "data"}]), "phase": "prefill"}
    journal = tmp_path / "gap.jsonl"
    result = sub.run_plan(_plan([case], stage=stage), runtime=FakeJointRuntime(),
                          protocol=protocol, executor=executor, observations=journal)
    record = result["records"][0]
    assert record["minimum_ms"] == pytest.approx(0.12)
    assert all(calls[i][1] is calls[i + 1][0] for i in range(0, len(calls), 2))
    expected = {"first": dims, "second": dims}
    assert record["node_shapes"] == expected and record["status"] == "unqualified"
    assert (record.get("timing") or record["eager"])["modes"]["eager"]["qualified"] is False
    first, second, done = [json.loads(line) for line in journal.read_text().splitlines()]
    for row in (first, second):
        assert row["node_shapes"] == expected
        assert row["boundary"] == row["identity"]["boundary"] == "host_submission_span"
        assert row["qualified"] is False
    assert done["summary"]["node_shapes"] == expected


@pytest.mark.parametrize(("captured", "wait_works"), [(True, False), (False, True), (False, False)])
def test_multi_op_protocol_qualifies_a_capture_or_a_verified_wait(captured, wait_works):
    torch = FakeTorch()
    runtime = timing.TorchTimingRuntime(torch)
    if not wait_works:
        runtime.wait_event = lambda *_args: False
    protocol = timing.MeasurementProtocol(runtime, warmups=0, trials=1, repeats=1)

    def enqueue():
        torch.clock.ms += 0.02

    kwargs = {} if captured else {
        "blocker": lambda: None, "blocker_receipt": {"calibrated": True, "estimated_ms": 2.5},
    }
    receipt = protocol.run(enqueue, case_id="two_ops", multi_op=True, captured=captured, **kwargs)
    assert receipt["qualified"] is (captured or wait_works)
    assert receipt["minimum_ms"] == pytest.approx(0.02)
    assert set(receipt["modes"]) == {"eager" if captured else "stream_saturated"}


def test_subgraph_requires_shape_evidence_for_each_timed_node(monkeypatch):
    from mindie_profiler.bench import subgraph_runtime

    backend = FakeBackend()
    real_builder = subgraph_runtime.build_operator_enqueue

    def build(torch, node, context, **kwargs):
        if node["node_id"] == "unknown":
            context = {**context, "_actual_shape": None}
        return real_builder(torch, node, context, **kwargs)

    monkeypatch.setattr(subgraph_runtime, "build_operator_enqueue", build)
    nodes = [_operator(name, "rms_norm", tokens=4, width=8) for name in ("known", "unknown")]
    record = sub.execute_local_case(sub.OperatorExecutor(backend.torch, backend.context()),
                                    _case(nodes=nodes, edges=[]), TimingProtocol(), execution_modes=["eager"])
    assert record["status"] == "unqualified" and record["qualified"] is False
    assert record["reason"] == "bench_subgraph_actual_shape_missing:unknown"
    assert set(record["node_shapes"]) == {"known"}


@pytest.mark.parametrize("builder", ["rms_norm", "add_rms_norm"])
@pytest.mark.parametrize("shape", [(32,), (2, 2, 8)])
def test_normalization_reuses_compatible_upstream_storage(builder, shape):
    backend = FakeBackend()
    executor = sub.OperatorExecutor(backend.torch, backend.context())
    source = FakeTensor(shape, dtype=backend.torch.bfloat16)
    executor.launch(_operator("consumer", builder, tokens=4, width=8), [source])
    _, args, _ = backend.calls[-1]
    assert args[0].shape == (4, 8) and args[0].addr == source.addr


@pytest.mark.parametrize(("builder", "kernel"), [
    ("l2_norm", "npu_l2_norm"),
    ("rms_norm_gated", "npu_rms_norm_gated"),
    ("add_rms_norm_quant", "npu_add_rms_norm_quant"),
    ("add_rms_norm_quant", "npu_add_rms_norm_dynamic_quant"),
    ("add_rms_norm", "npu_add_rms_norm"),
    ("rms_norm_quant", "npu_rms_norm_quant"),
    ("rms_norm_quant", "npu_rms_norm_dynamic_quant"),
])
def test_normalization_consumes_declared_rms_norm_output(builder, kernel, monkeypatch):
    backend = FakeBackend()
    source = FakeTensor((4, 8), dtype=backend.torch.bfloat16)
    if kernel == "npu_add_rms_norm_dynamic_quant":
        monkeypatch.setattr(backend.torch.npu, "npu_add_rms_norm_quant", None)
    context = backend.context(op_overrides={
        "npu_rms_norm": lambda *_args: (source, None),
        kernel: backend._record(kernel),
    })
    executor = sub.OperatorExecutor(backend.torch, context)
    case = _case(
        nodes=[_operator("producer", "rms_norm", tokens=4, width=8),
               _operator("consumer", builder, tokens=4, width=8)],
        edges=[{"from": "producer", "to": "consumer", "kind": "data"}],
    )
    sub.execute_local_case(executor, case, TimingProtocol(), execution_modes=["eager"])
    name, args, _ = backend.calls[-1]
    assert name == kernel
    assert args[0] is source


@pytest.mark.parametrize("upstream", [
    FakeTensor((8, 4)), FakeTensor((2, 4, 4)), FakeTensor((31,)), (), (None,), object(),
])
def test_add_rms_norm_rejects_incompatible_upstream_input(upstream):
    backend = FakeBackend()
    executor = sub.OperatorExecutor(backend.torch, backend.context())
    consumer = _operator("consumer", "add_rms_norm", tokens=4, width=8)
    with pytest.raises(ProfilerUsageError, match="bench_norm_input_shape_mismatch"):
        executor.launch(consumer, [upstream])
    assert backend.calls == []


@pytest.mark.parametrize(("builder", "kernel"), [
    ("add_rms_norm", "npu_add_rms_norm"),
    ("add_rms_norm_quant", "npu_add_rms_norm_quant"),
    ("add_rms_norm_quant", "npu_add_rms_norm_dynamic_quant"),
    ("rms_norm_gated", "npu_rms_norm_gated"),
])
def test_binary_normalization_binds_producers_in_data_edge_order(builder, kernel, monkeypatch):
    backend = FakeBackend()
    if kernel == "npu_add_rms_norm_dynamic_quant":
        monkeypatch.setattr(backend.torch.npu, "npu_add_rms_norm_quant", None)
        monkeypatch.setattr(backend.torch.npu, kernel, backend._record(kernel), raising=False)
    executor = sub.OperatorExecutor(backend.torch, backend.context())
    nodes = [
        _operator("a_residual", "rms_norm", tokens=4, width=8),
        _operator("b_input", "rms_norm", tokens=4, width=8),
        _operator("consumer", builder, tokens=4, width=8),
    ]
    case = _case(nodes=nodes, edges=[
        {"from": producer, "to": "consumer", "kind": "data"}
        for producer in ("b_input", "a_residual")
    ])
    sub.execute_local_case(executor, case, TimingProtocol(), execution_modes=["eager"])
    name, args, kwargs = backend.calls[-1]
    assert name == kernel
    assert args[0] is executor.outputs["b_input"]
    residual = kwargs["z"] if builder == "rms_norm_gated" else args[1]
    assert residual is executor.outputs["a_residual"]


def test_add_rms_norm_validates_residual_shape_and_rejects_extra_inputs():
    backend = FakeBackend()
    executor = sub.OperatorExecutor(backend.torch, backend.context())
    consumer = _operator("consumer", "add_rms_norm", tokens=4, width=8)
    x, compatible_residual = FakeTensor((4, 8)), FakeTensor((2, 2, 8))
    with pytest.raises(ProfilerUsageError, match="bench_norm_input_shape_mismatch"):
        executor.launch(consumer, [x, FakeTensor((8, 4))])
    with pytest.raises(ProfilerUsageError, match="bench_norm_input_count_mismatch"):
        executor.launch(consumer, [x, compatible_residual, x])
    assert backend.calls == []
    executor.launch(consumer, [x, (compatible_residual, None)])
    _, (_, residual, *_), _ = backend.calls[-1]
    assert residual.shape == (4, 8) and residual.addr == compatible_residual.addr


@pytest.mark.parametrize("width", [8, 4])
def test_rotary_embedding_uses_rms_norm_query_and_rejects_incompatible_width(width):
    backend = FakeBackend()
    outputs = []

    def rms_norm(x, *_args):
        output = FakeTensor(x.shape, dtype=x.dtype)
        outputs.append(output)
        return output, None

    executor = sub.OperatorExecutor(backend.torch, backend.context(op_overrides={"rms_norm": rms_norm}))
    nodes = [
        _operator("norm", "rms_norm", tokens=4, width=width),
        _operator("rope", "rotary_embedding", tokens=4, heads=2, head_dim=4),
    ]
    case = _case(nodes=nodes, edges=[{"from": "norm", "to": "rope", "kind": "data"}])
    if width == 4:
        with pytest.raises(ProfilerUsageError, match="bench_rotary_query_shape_mismatch"):
            sub.execute_local_case(executor, case, TimingProtocol(), execution_modes=["eager"])
        assert backend.calls == []
        return
    sub.execute_local_case(executor, case, TimingProtocol(), execution_modes=["eager"])
    assert len(backend.calls) == len(outputs)
    for (name, (query, _, _), _), output in zip(backend.calls, outputs):
        assert name == "npu_rotary_mul"
        assert query.shape == (1, 4, 2, 4) and query.addr == output.addr


@pytest.mark.parametrize("shape", [(1, 4, 2, 4), (4, 2, 4)])
def test_rotary_embedding_binds_compatible_query_through_cached_builder(shape):
    backend = FakeBackend()
    executor = sub.OperatorExecutor(backend.torch, backend.context())
    rotary = _operator("rope", "rotary_embedding", tokens=4, heads=2, head_dim=4)
    executor.launch(rotary)
    for _ in range(2):
        source = FakeTensor(shape)
        executor.launch(rotary, [source])
        _, (query, _, _), _ = backend.calls[-1]
        assert query.shape == (1, 4, 2, 4) and query.addr == source.addr
    with pytest.raises(ProfilerUsageError, match="bench_rotary_query_shape_mismatch"):
        executor.launch(rotary, [FakeTensor((8, 4))])
    assert len(backend.calls) == 3


@pytest.mark.parametrize("clone_oom", [False, True])
def test_graph_snapshot_never_aliases_mutated_replay_output(clone_oom):
    backend = FakeBackend()

    class Result:
        value = 1

        def detach(self):
            return self

        def clone(self):
            if clone_oom:
                raise RuntimeError("NPU out of memory cloning snapshot")
            snapshot = Result()
            snapshot.value = self.value
            return snapshot

    output = Result()
    backend.torch.allclose = lambda lhs, rhs, **_kwargs: lhs.value == rhs.value
    context = backend.context(op_overrides={"rms_norm": lambda *_args: output})

    class MutatingReplay(FakeJointRuntime):
        def replay(self, captured):
            output.value = 999
            return super().replay(captured)

    case = _case(nodes=[_operator("norm", "rms_norm", tokens=1, width=8)], edges=[])
    runtime = MutatingReplay()
    result = sub.execute_joint_case(sub.OperatorExecutor(backend.torch, context), case, TimingProtocol(),
                                    runtime, execution_modes=["aclgraph"])
    assert result["outputs_agree"] is False and result["qualified"] is False
    assert result["capture"]["status"] == ("snapshot_failed" if clone_oom else "captured")
    assert runtime.captures == (0 if clone_oom else 1)


def test_hot_resize_charge_includes_old_storage_kept_by_views():
    backend = FakeBackend()
    mib = timing.MIB
    ring = timing.ColdRing(backend.torch, timing.cold_ring_plan(96 * mib), ordinal=0).allocate()
    ledger = {"peak_bytes": ring.allocated_bytes}
    old, _ = ring.slice_hot(128 * mib, ledger=ledger, cap_bytes=513 * mib)
    with pytest.raises(ProfilerUsageError, match="hot control buffer exceeds S0 cap"):
        ring.slice_hot(188 * mib, ledger=ledger, cap_bytes=513 * mib)
    assert ring.allocated_bytes == 416 * mib and ledger["peak_bytes"] == 416 * mib
    new, _ = ring.slice_hot(188 * mib, ledger=ledger, cap_bytes=604 * mib)
    assert new.addr != old.addr and ledger["peak_bytes"] == 604 * mib


@pytest.mark.parametrize("tp", [8, 16])
def test_a3_dp2_template_has_routes_in_the_second_replica(tp, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "examples" / "structure"))
    from dsh_generalization_eval import parse_case, resolve_template
    from mindie_sim.prediction.collectives.topology import Topology

    _, template, _, _ = resolve_template({
        "hw": "a3", "family": "kimi-k3-4l", "tp": tp, "dp": 2, "ep": tp, "phase": "decode",
    })
    machine = template["machine"]
    assert machine["num_devices"] == tp * 2
    packages = [link for link in machine["links"] if link["channel"] == "d2d_intra_package"]
    assert [link["members"] for link in packages] == [[rank, rank + 1] for rank in range(0, tp * 2, 2)]
    assert all(link["capacity_bytes_per_ms"] == 448_000_000 for link in packages)
    case = parse_case(template)
    assert Topology(case.machine, case.runtime.parallel).route(tp, tp + 1) == ((f"d2d_intra_package:{tp}", tp, tp + 1),)
