"""Ten-archetype subgraph runner: plan contract, cut collectives, S0/S1 arms.

[Role]
  Verify the exported plan contract, topological ordering, the rule that
  collectives are cut outside the timed window (and refused inside it),
  builder-based dispatch that ignores archetype labels, S0 local replay, S1
  eager-versus-captured replay with output agreement, and the dry-run CLI.

[Invariants]
  * No NPU is touched; runtimes, executors and protocols are explicit fakes.
  * A mismatched captured arm is reported ``unqualified``, never timed as a win.

[Timeouts & Locks]
  Pure in-memory work; no sleeps, threads or processes.

[Side-Effect Policy]
  Writes only pytest ``tmp_path`` plan/out files.
"""

from __future__ import annotations

import json
import types

import pytest

from mindie_profiler.bench import bench_archetype_subgraphs as sub
from mindie_profiler.bench.observations import ObservationJournal
from mindie_profiler.events import ProfilerUsageError


def _node(node_id, *, kind="operator", op="add", builder="empty_event_pair"):
    return {"schema": sub.NODE_SCHEMA, "node_id": node_id, "kind": kind,
            "op": op, "builder": builder, "binding": {"builder": builder}}


def _case(case_id="case-1", *, nodes=None, edges=None, boundary=None,
          archetype=None, stage_nodes=True):
    nodes = nodes or [_node("a"), _node("b")]
    edges = edges if edges is not None else [{"from": "a", "to": "b",
                                              "kind": "stream"}]
    return {"case_id": case_id, "kind": "subgraph", "phase": "decode",
            "nodes": nodes, "edges": edges, "archetype": archetype,
            "timed_boundary": boundary or {}, "split": "heldout",
            "parallel": {"tp": 8, "ep": 8, "sp": False, "mc2": True}}


def _plan(cases=None, *, stage="s0_local", modes=("eager", "aclgraph")):
    return {"schema": sub.PLAN_SCHEMA, "plan_id": "plan-1", "stage": stage,
            "rank": 0, "world_size": 8, "execution_modes": list(modes),
            "cases": cases or [_case()]}


def test_validate_plan_accepts_a_minimal_plan():
    plan = sub.validate_plan(_plan())
    assert plan["stage"] == "s0_local"
    assert plan["cases"][0]["case_id"] == "case-1"


@pytest.mark.parametrize("mutation,match", [
    ({"schema": "other"}, "bench_subgraph_plan_schema"),
    ({"stage": "s2"}, "bench_subgraph_stage_invalid"),
    ({"rank": 4096}, "bench_subgraph_rank_invalid"),
    ({"world_size": 0}, "bench_subgraph_world_invalid"),
    ({"execution_modes": ["lazy"]}, "bench_subgraph_execution_mode_invalid"),
    ({"cases": []}, "bench_subgraph_cases_missing"),
])
def test_validate_plan_rejects_bad_headers(mutation, match):
    plan = _plan()
    plan.update(mutation)
    with pytest.raises(ProfilerUsageError, match=match):
        sub.validate_plan(plan)


def test_validate_plan_rejects_bad_nodes_and_edges():
    node_case = _case(nodes=[_node("a", kind="kernel")])
    with pytest.raises(ProfilerUsageError, match="node_kind_invalid"):
        sub.validate_plan(_plan([node_case]))
    edge_case = _case(edges=[{"from": "a", "to": "b", "kind": "dma"}])
    with pytest.raises(ProfilerUsageError, match="edge_kind_invalid"):
        sub.validate_plan(_plan([edge_case]))
    unknown = _case(edges=[{"from": "a", "to": "zzz", "kind": "data"}])
    with pytest.raises(ProfilerUsageError, match="edge_unknown_node"):
        sub.topological_order(unknown)


def test_topological_order_and_cycle_detection():
    case = _case(
        nodes=[_node("c"), _node("a"), _node("b")],
        edges=[{"from": "a", "to": "b"}, {"from": "b", "to": "c"}])
    assert [node["node_id"] for node in sub.topological_order(case)] == ["a", "b", "c"]
    cyclic = _case(nodes=[_node("a"), _node("b")],
                   edges=[{"from": "a", "to": "b"}, {"from": "b", "to": "a"}])
    with pytest.raises(ProfilerUsageError, match="cycle"):
        sub.topological_order(cyclic)


def test_leading_and_trailing_collectives_are_cut_around_the_window():
    case = _case(nodes=[_node("head", kind="collective", op="all_reduce"),
                        _node("t1"), _node("t2"),
                        _node("tail", kind="collective", op="all_reduce")],
                 edges=[{"from": "head", "to": "t1"},
                        {"from": "t1", "to": "t2"},
                        {"from": "t2", "to": "tail"}])
    ordered = sub.topological_order(case)
    cut = sub.plan_timed_cut(case, ordered)
    assert [node["node_id"] for node in cut["pre"]] == ["head"]
    assert [node["node_id"] for node in cut["timed"]] == ["t1", "t2"]
    assert [node["node_id"] for node in cut["post"]] == ["tail"]
    pre, timed = sub.split_timed(case, ordered)
    assert [node["node_id"] for node in pre] == ["head"]
    assert [node["node_id"] for node in timed] == ["t1", "t2"]


def test_a_collective_between_timed_producers_is_refused():
    case = _case(nodes=[_node("x"), _node("comm", kind="collective", op="all_reduce"),
                        _node("y")],
                 edges=[{"from": "x", "to": "comm"}, {"from": "comm", "to": "y"}])
    with pytest.raises(ProfilerUsageError, match="bench_collective_splits_local_chain"):
        sub.plan_timed_cut(case, sub.topological_order(case))


def test_a_collective_inside_the_declared_window_is_refused():
    case = _case(nodes=[_node("comm", kind="collective", op="all_reduce"),
                        _node("t1")],
                 edges=[{"from": "comm", "to": "t1"}],
                 boundary={"include": ["comm"]})
    with pytest.raises(ProfilerUsageError, match="collective_inside_timed_window"):
        sub.split_timed(case, sub.topological_order(case))


def test_a_window_with_only_collectives_is_refused():
    case = _case(nodes=[_node("comm", kind="collective", op="all_reduce")], edges=[])
    with pytest.raises(ProfilerUsageError, match="timed_window_empty"):
        sub.split_timed(case, sub.topological_order(case))


def test_dispatch_uses_the_declared_builder_and_never_the_archetype():
    torch = types.SimpleNamespace()
    case = _node("n1", op="npu_fusion_attention", builder="empty_event_pair")
    enqueue = sub.build_operator_enqueue(torch, case, {})
    assert callable(enqueue)
    label_only = dict(case, case_id="dense_gqa_archetype", archetype="1 · Dense GQA")
    assert callable(sub.build_operator_enqueue(torch, label_only, {}))
    with pytest.raises(ProfilerUsageError, match="bench_builder_unknown"):
        sub.build_operator_enqueue(torch, _node("n2", builder="not_a_builder"), {})


class FakeExecutor:
    def __init__(self):
        self.launched: list[str] = []
        self.boundaries: list[str] = []
        self.context: dict = {}
        self.torch = types.SimpleNamespace(
            npu=types.SimpleNamespace(synchronize=lambda: None))

    def launch(self, node):
        self.launched.append(node["node_id"])
        return node["node_id"]

    def supply_boundary(self, node):
        self.boundaries.append(node["node_id"])
        return node["node_id"]


class FakeProtocol:
    def __init__(self, minimum_ms=0.002):
        self.calls: list[str] = []
        self.minimum_ms = minimum_ms

    def run(self, enqueue, *, case_id, kind="operator", nbytes=None):
        self.calls.append(case_id)
        enqueue()
        return {"case_id": case_id, "minimum_ms": self.minimum_ms,
                "startup_ms": 0.0, "modes": {"eager": {}}}


def test_execute_local_case_times_only_the_local_chain():
    case = _case(nodes=[_node("comm", kind="collective", op="all_reduce"),
                        _node("t1")],
                 edges=[{"from": "comm", "to": "t1"}])
    executor, protocol = FakeExecutor(), FakeProtocol()
    record = sub.execute_local_case(executor, case, protocol)
    assert record["status"] == "ok"
    assert record["cut_nodes"] == ["comm"]
    assert record["timed_nodes"] == ["t1"]
    assert executor.launched == ["t1"]
    assert executor.boundaries == ["comm"]
    assert record["single_rank_boundary_tensors"] is True
    assert protocol.calls == ["case-1"]
    assert record["startup_ms"] == 0.0
    assert record["split"] == "heldout"


class FakeJointRuntime:
    def __init__(self, match=True):
        self.match = match
        self.captures = 0
        self.replays = 0
        self.syncs = 0
        self.outputs = []

    def synchronize(self):
        self.syncs += 1

    def capture(self, call, case_id):
        self.captures += 1
        self.outputs = call()
        return (["graph"], {"status": "captured", "case_id": case_id})

    def replay(self, captured):
        self.replays += 1
        return self.outputs if self.match else ["wrong"]


def test_execute_joint_case_compares_eager_and_captured_outputs():
    case = _case(nodes=[_node("a"), _node("t1")],
                 edges=[{"from": "a", "to": "t1"}])
    executor, protocol = FakeExecutor(), FakeProtocol()
    runtime = FakeJointRuntime(match=True)
    record = sub.execute_joint_case(executor, case, protocol, runtime)
    assert record["outputs_agree"] is True
    assert record["qualified"] is True
    assert record["environment_mode"] == "separate_contexts"
    assert runtime.captures == 1 and runtime.replays == 2
    assert record["aclgraph"] is not None
    assert record["eager"]["minimum_ms"] == record["minimum_ms"]

    mismatched = sub.execute_joint_case(FakeExecutor(), _case("case-2"),
                                        FakeProtocol(), FakeJointRuntime(match=False))
    assert mismatched["outputs_agree"] is False
    assert mismatched["qualified"] is False


class FakeGraph:
    def __init__(self):
        self.replays = 0

    def replay(self):
        self.replays += 1


def test_torch_joint_runtime_captures_and_replays_a_graph():
    graph = FakeGraph()
    torch = types.SimpleNamespace(
        npu=types.SimpleNamespace(NPUGraph=lambda: graph,
                                  graph=lambda target: _GraphContext(target),
                                  synchronize=lambda: None))
    runtime = sub.TorchJointRuntime(torch)
    captured, receipt = runtime.capture(lambda: ["out"], "case")
    assert receipt["status"] == "captured"
    assert runtime.replay(captured) == ["out"]
    assert graph.replays == 1


class _GraphContext:
    def __init__(self, target):
        self.target = target

    def __enter__(self):
        return self.target

    def __exit__(self, *_exc):
        return False


def test_run_plan_dispatches_by_stage_and_keeps_failures_explicit():
    stage0 = sub.run_plan(_plan(stage="s0_local"), protocol=FakeProtocol(),
                          executor=FakeExecutor())
    assert stage0["status"] == "ok"
    assert stage0["records"][0]["status"] == "ok"
    stage1 = sub.run_plan(_plan(stage="s1_joint"), protocol=FakeProtocol(),
                          executor=FakeExecutor(), runtime=FakeJointRuntime())
    assert stage1["status"] == "ok"
    assert stage1["records"][0]["qualified"] is True
    broken_node = {**_node("n", builder="not_a_builder"),
                   "shape": {"tokens": 1, "heads": 8, "head_dim": 128, "seq_len": 4096, "top_k": 2049}}
    broken = _plan([_case(nodes=[broken_node])])
    result = sub.run_plan(broken, protocol=FakeProtocol(), executor=FakeExecutor())
    assert result["status"] == "partial"
    assert result["records"][0]["status"] == "unsupported_binding"
    assert result["records"][0]["actual_shape"]["top_k"] == 2049
    assert result["records"][0]["actual_shape"]["seq_len"] == 4096


def test_load_plan_reads_and_validates_a_file(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_plan()))
    assert sub.load_plan(path)["plan_id"] == "plan-1"
    path.write_text("{}")
    with pytest.raises(ProfilerUsageError, match="bench_subgraph_plan_schema"):
        sub.load_plan(path)
    path.write_text("[1, 2]")
    with pytest.raises(ProfilerUsageError, match="expected an object"):
        sub.load_plan(path)


def test_cli_dry_run_summarizes_the_plan_without_torch(tmp_path, capsys):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_plan()))
    assert sub.main(["--plan", str(path), "--dry-run"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry_run"
    assert payload["case_count"] == 1
    assert payload["cases"][0]["nodes"] == ["a", "b"]
    assert payload["cases"][0]["split"] == "heldout"


def test_cli_dry_run_writes_an_atomic_out_file(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_plan()))
    out = tmp_path / "sub.json"
    assert sub.main(["--plan", str(path), "--dry-run", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["status"] == "dry_run"
    assert not list(tmp_path.glob("*.tmp"))


class FakeDist:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.group = object()

    def all_reduce(self, tensor, group=None):
        self.calls.append(("all_reduce", {"group": group}))

    def all_gather_into_tensor(self, out, buffer, group=None):
        self.calls.append(("all_gather", {"group": group}))

    def reduce_scatter_tensor(self, out, buffer, group=None):
        self.calls.append(("reduce_scatter", {"group": group}))

    def all_to_all_single(self, out, buffer, **kwargs):
        self.calls.append(("all_to_all_single", kwargs))

    def send(self, buffer, dst=None, group=None):
        self.calls.append(("send", {"dst": dst, "group": group}))

    def recv(self, buffer, src=None, group=None):
        self.calls.append(("recv", {"src": src, "group": group}))


class FakeBuffer:
    def __init__(self):
        self.transfers = []

    def numel(self):
        return 1024


def _buffer_torch():
    def zeros(size, dtype=None, device=None):
        buffer = FakeBuffer()
        buffer.transfers.append(("zeros", size))
        return buffer

    torch = types.SimpleNamespace()
    torch.zeros = zeros
    torch.float32 = "float32"
    return torch


def test_collective_builders_use_the_declared_group_and_splits():
    torch, dist = _buffer_torch(), FakeDist()
    context = {"device": {"ordinal": 0}, "dist": dist, "groups": {"tp": dist.group}}
    sub.build_operator_enqueue(torch, {"op": "all_reduce", "group": "tp",
                                       "nbytes": 4096}, context)()
    assert dist.calls[-1] == ("all_reduce", {"group": dist.group})
    sub.build_operator_enqueue(torch, {"op": "all_to_all_v", "group": "tp",
                                       "group_size": 2, "nbytes": 4096,
                                       "send_counts": [600, 424],
                                       "recv_counts": [512, 512]}, context)()
    name, kwargs = dist.calls[-1]
    assert name == "all_to_all_single"
    assert kwargs["input_split_sizes"] == [600, 424]
    assert kwargs["output_split_sizes"] == [512, 512]
    sub.build_operator_enqueue(torch, {"op": "send", "group": "tp",
                                       "peer": 3}, context)()
    assert dist.calls[-1] == ("send", {"dst": 3, "group": dist.group})
    with pytest.raises(ProfilerUsageError, match="bench_collective_unsupported"):
        sub._bind_collective(torch, {"op": "barrier"}, context, "barrier")


def test_joint_runtime_creates_axis_groups_in_declared_order(monkeypatch):
    import sys

    calls: list[tuple] = []

    class Dist:
        def init_process_group(self, backend, rank=None, world_size=None, timeout=None):
            calls.append(("init", backend, rank, world_size, timeout is not None))

        def new_group(self, members):
            calls.append(("new_group", list(members)))
            return f"group-{len(calls)}"

        def destroy_process_group(self):
            calls.append(("destroy",))

    dist = Dist()
    module = types.ModuleType("torch.distributed")
    module.init_process_group = dist.init_process_group
    module.new_group = dist.new_group
    module.destroy_process_group = dist.destroy_process_group
    monkeypatch.setitem(sys.modules, "torch.distributed", module)
    runtime = sub.TorchJointRuntime(types.SimpleNamespace(), rank=0, world_size=8,
                                    parallel={"tp": 4, "ep": 2, "sp": False,
                                              "mc2": True})
    receipt = runtime.init_process_group()
    assert receipt["initialized"] is True
    assert receipt["groups"] == ["ep", "ep:2", "mc2", "mc2:4", "tp", "tp:4"]
    assert calls[0] == ("init", "hccl", 0, 8, True)
    assert [call[1] for call in calls[1:9]] == [
        [0, 1], [2, 3], [4, 5], [6, 7],
        [0, 1, 2, 3], [4, 5, 6, 7],
        [0, 1, 2, 3], [4, 5, 6, 7],
    ]
    assert runtime.groups["ep"] == "group-2"
    assert runtime.groups["mc2"] == "group-6"
    assert runtime.groups["tp"] == "group-8"
    runtime.close()
    assert calls[-1] == ("destroy",)
    single = sub.TorchJointRuntime(types.SimpleNamespace(), world_size=1)
    assert single.init_process_group()["initialized"] is False


def test_eight_rank_tp4_binds_the_contiguous_chunk_for_this_rank(monkeypatch):
    import sys

    calls: list[tuple] = []

    class Dist:
        def init_process_group(self, backend, rank=None, world_size=None, timeout=None):
            calls.append(("init", rank, world_size))

        def new_group(self, members):
            calls.append(("new_group", list(members)))
            return f"group-{len(calls)}"

        def destroy_process_group(self):
            calls.append(("destroy",))

    module = types.ModuleType("torch.distributed")
    dist = Dist()
    module.init_process_group = dist.init_process_group
    module.new_group = dist.new_group
    module.destroy_process_group = dist.destroy_process_group
    monkeypatch.setitem(sys.modules, "torch.distributed", module)
    runtime = sub.TorchJointRuntime(types.SimpleNamespace(), rank=5, world_size=8,
                                    parallel={"tp": 4})
    runtime.init_process_group()
    assert [call[1] for call in calls[1:]] == [[0, 1, 2, 3], [4, 5, 6, 7]]
    assert runtime.groups["tp"] == "group-3"
    runtime.close()


def test_subgroup_failure_destroys_the_process_group(monkeypatch):
    import sys

    calls: list[str] = []

    class Dist:
        def init_process_group(self, backend, rank=None, world_size=None, timeout=None):
            calls.append("init")

        def new_group(self, members):
            raise RuntimeError("hccl subgroup failure")

        def destroy_process_group(self):
            calls.append("destroy")

    module = types.ModuleType("torch.distributed")
    dist = Dist()
    module.init_process_group = dist.init_process_group
    module.new_group = dist.new_group
    module.destroy_process_group = dist.destroy_process_group
    monkeypatch.setitem(sys.modules, "torch.distributed", module)
    runtime = sub.TorchJointRuntime(types.SimpleNamespace(), rank=0, world_size=8,
                                    parallel={"tp": 4})
    with pytest.raises(RuntimeError, match="hccl subgroup failure"):
        runtime.init_process_group()
    assert calls == ["init", "destroy"]
    assert runtime.initialized is False


def test_case_declared_collective_groups_are_partitioned(monkeypatch):
    import sys

    calls: list[list[int]] = []

    class Dist:
        def init_process_group(self, backend, rank=None, world_size=None, timeout=None):
            calls.append([])

        def new_group(self, members):
            calls.append(list(members))
            return list(members)

        def destroy_process_group(self):
            calls.append([])

    module = types.ModuleType("torch.distributed")
    dist = Dist()
    module.init_process_group = dist.init_process_group
    module.new_group = dist.new_group
    module.destroy_process_group = dist.destroy_process_group
    monkeypatch.setitem(sys.modules, "torch.distributed", module)
    case = {
        "case_id": "joint", "parallel": {"tp": 8},
        "nodes": [
            {"node_id": "dp", "kind": "collective", "op": "all_reduce",
             "group": "dp", "group_size": 2},
            {"node_id": "die", "kind": "collective", "op": "all_reduce",
             "route": "intra_package_die"},
            {"node_id": "node", "kind": "collective", "op": "all_reduce",
             "route": "intra_node_hccs"},
        ],
    }
    runtime = sub.TorchJointRuntime(types.SimpleNamespace(), rank=0, world_size=8,
                                    cases=[case])
    runtime.init_process_group()
    assert runtime.groups["tp"] == [0, 1, 2, 3, 4, 5, 6, 7]
    assert runtime.groups["dp"] == [0, 1]
    assert runtime.groups["intra_package_die"] == [0, 1]
    assert runtime.groups["intra_node_hccs"] == [0, 1, 2, 3]
    assert [0, 1] in calls and [4, 5, 6, 7] in calls
    runtime.close()


def test_explicit_group_ranks_are_created_on_every_rank(monkeypatch):
    import sys

    created: list[list[int]] = []

    class Dist:
        def init_process_group(self, backend, rank=None, world_size=None, timeout=None):
            return None

        def new_group(self, members):
            created.append(list(members))
            return list(members)

        def destroy_process_group(self):
            return None

    module = types.ModuleType("torch.distributed")
    dist = Dist()
    module.init_process_group = dist.init_process_group
    module.new_group = dist.new_group
    module.destroy_process_group = dist.destroy_process_group
    monkeypatch.setitem(sys.modules, "torch.distributed", module)
    case = {
        "case_id": "joint", "group_ranks": [6, 2, 4],
        "nodes": [{"node_id": "a", "kind": "operator"}],
    }
    runtime = sub.TorchJointRuntime(types.SimpleNamespace(), rank=4, world_size=8,
                                    cases=[case])
    runtime.init_process_group()
    assert created == [[2, 4, 6]]
    assert runtime.groups["joint"] == [2, 4, 6]
    runtime.close()


def test_cli_rejects_a_plan_rank_that_disagrees_with_torchrun(tmp_path, capsys,
                                                              monkeypatch):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_plan()))
    monkeypatch.setenv("RANK", "1")
    monkeypatch.setenv("WORLD_SIZE", "8")
    assert sub.main(["--plan", str(path), "--dry-run"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "rank_mismatch"
    assert payload["plan"] == [0, 8]
    assert payload["environment"] == [1, 8]
    monkeypatch.setenv("RANK", "0")
    assert sub.main(["--plan", str(path), "--dry-run"]) == 0


def test_plan_limit_is_128_mib():
    assert sub.MAX_PLAN_BYTES == 128 * 1024 * 1024


def test_rank_neutral_plans_are_accepted_and_stage_override_runs_first(
        tmp_path, capsys, monkeypatch):
    path = tmp_path / "plan.json"
    plan = _plan(stage="s1_joint")
    plan["rank"] = None
    path.write_text(json.dumps(plan))
    monkeypatch.setenv("WORLD_SIZE", "4")
    monkeypatch.delenv("RANK", raising=False)
    assert sub.main(["--plan", str(path), "--dry-run"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "rank_mismatch"
    assert sub.main(["--plan", str(path), "--dry-run", "--stage", "s0_local"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry_run"
    assert payload["stage"] == "s0_local"


def test_s0_local_skips_joint_and_fabric_cases():
    fabric = _case("fabric-case", nodes=[_node("a")])
    fabric["kind"] = "fabric"
    joint = _case("joint-case", nodes=[_node("a")])
    joint["stage"] = "s1_joint"
    plan = _plan([_case("local"), joint, fabric])
    result = sub.run_plan(plan, protocol=FakeProtocol(), executor=FakeExecutor())
    statuses = {record["case_id"]: record["status"] for record in result["records"]}
    assert statuses == {"local": "ok", "joint-case": "skipped_stage",
                        "fabric-case": "skipped_stage"}
    assert result["status"] == "ok"


def test_joint_cases_keep_collectives_inside_the_timed_graph():
    case = _case(nodes=[_node("a"), _node("comm", kind="collective", op="all_reduce"),
                        _node("t1")],
                 edges=[{"from": "a", "to": "comm"}, {"from": "comm", "to": "t1"}])
    executor, protocol = FakeExecutor(), FakeProtocol()
    record = sub.execute_joint_case(executor, case, protocol, FakeJointRuntime())
    assert record["timed_nodes"] == ["a", "comm", "t1"]
    assert record["cut_nodes"] == []
    assert record["qualified"] is True
    assert executor.launched[:3] == ["a", "comm", "t1"]
    assert executor.launched.count("comm") == 3  # eager outputs, capture, eager timing


def test_aclgraph_unqualified_status_when_capture_is_unavailable():
    class NoGraphRuntime(FakeJointRuntime):
        def capture(self, call, case_id):
            return None, {"status": "unsupported_binding"}

    case = _case()
    record = sub.execute_joint_case(FakeExecutor(), case, FakeProtocol(),
                                    NoGraphRuntime())
    assert record["status"] == "unqualified"
    assert record["qualified"] is False
    assert record["aclgraph"] is None


def _plan_identities():
    return {
        "primitive_key": {
            "hardware": {"sku": "Ascend910B4", "architecture": "A2"},
            "implementation": "empty_event_pair",
            "kernel": "empty_event_pair", "dtype": "bf16",
            "shape": {"m": 1}, "scope": "device_kernel"},
        "accuracy_identity": {
            "level": "operator", "boundary": "device_kernel",
            "hardware": "Ascend910B4", "implementation": "empty_event_pair",
            "phase": "decode", "shape": {"m": 1}, "dtype": "bf16",
            "layout": "contiguous",
            "execution": {"mode": "eager", "stage": "s0_local"}},
        "service": {"resource": "hbm", "work_unit": "bytes", "work": 4096,
                    "active_units": 1, "boundary": "device_kernel",
                    "identity": {"hardware": {"key": "Ascend910B4"},
                                 "kernel": "empty_event_pair"}},
    }


def test_subgraph_observations_use_plan_identities_for_key_and_service(tmp_path):
    journal = ObservationJournal(tmp_path / "subgraph.jsonl")
    case = _case()
    case["identities"] = _plan_identities()
    record = {"status": "ok", "validated": True, "qualified": True,
              "timed_nodes": ["a", "b"],
              "timing": {"modes": {"aclgraph": {"trials": [
                  {"trial": 0, "repeats_us": [1000.0, 2000.0]}]}}}}
    sub._emit_case_observations(journal, _plan(), case, record, "run-1",
                                "s0_local")
    rows = [json.loads(line) for line in
            (tmp_path / "subgraph.jsonl").read_text().splitlines()]
    identities = case["identities"]
    assert rows[0]["key"] == identities["primitive_key"]
    assert rows[0]["service_identity"] == identities["service"]["identity"]
    assert rows[0]["identity"] == {
        **identities["accuracy_identity"],
        "execution": {"mode": "aclgraph", "stage": "s0_local"}}
    assert rows[0]["work"] == 4096 and rows[0]["resource"] == "hbm"
    assert rows[0]["active_units"] == 1


class TrialProtocol(FakeProtocol):
    def run(self, enqueue, *, case_id, kind="operator", nbytes=None):
        self.calls.append(case_id)
        enqueue()
        return {"case_id": case_id, "minimum_ms": 0.002, "startup_ms": 0.0,
                "modes": {"eager": {"trials": [
                    {"trial": 0, "repeats_us": [1000.0]}]}}}


def test_run_plan_coerces_observations_path_or_journal(tmp_path):
    path = tmp_path / "observations.jsonl"
    result = sub.run_plan(_plan(), protocol=TrialProtocol(),
                          executor=FakeExecutor(), observations=path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert result["status"] == "ok"
    assert [row["record_type"] for row in rows] == [
        "observation", "case_complete"]
    journal = ObservationJournal(tmp_path / "journal.jsonl")
    sub.run_plan(_plan(), protocol=TrialProtocol(), executor=FakeExecutor(),
                 observations=journal)
    assert journal.path.exists()


def test_subgraph_observations_emit_repeat_rows_and_case_complete(tmp_path):
    journal = ObservationJournal(tmp_path / "subgraph.jsonl")
    case = _case()
    record = {"status": "ok", "validated": True, "qualified": True,
              "timed_nodes": ["a", "b"],
              "timing": {"modes": {"eager": {"trials": [
                  {"trial": 0, "repeats_us": [1000.0, 2000.0]}]}}}}
    sub._emit_case_observations(journal, _plan(), case, record, "run-1",
                                "s0_local")
    rows = [json.loads(line) for line in
            (tmp_path / "subgraph.jsonl").read_text().splitlines()]
    assert [row["record_type"] for row in rows] == [
        "observation", "observation", "case_complete"]
    assert rows[0]["duration_ms"] == pytest.approx(1.0)
    assert rows[0]["source"].startswith("capture://bench-subgraph/")
    assert rows[0]["identity"]["execution"] == {"mode": "eager",
                                                "stage": "s0_local"}
    assert set(rows[0]["key"]) == {
        "hardware", "implementation", "kernel", "dtype", "shape", "scope"}


def test_operator_executor_reads_live_upstream_without_rebuild(monkeypatch):
    from mindie_profiler.bench import subgraph_runtime

    builds: list[str] = []

    def fake_build(torch, node, context, *, hot=False):
        builds.append(node["node_id"])
        live = context["_live_inputs"]
        return lambda: live["tensors"][0] if live["tensors"] else None

    monkeypatch.setattr(subgraph_runtime, "build_operator_enqueue", fake_build)
    executor = subgraph_runtime.OperatorExecutor(object(), {})
    node = {"node_id": "consumer", "kind": "operator", "builder": "empty_event_pair"}
    first, second = object(), object()
    assert executor.launch(node, [first]) is first
    assert executor.launch(node, [second]) is second
    assert executor.launch(node, [second]) is second
    assert builds == ["consumer"]


def test_boundary_nodes_pass_upstream_through_without_a_builder(monkeypatch):
    from mindie_profiler.bench import subgraph_runtime

    def fail_build(*args, **kwargs):
        raise AssertionError("a boundary node must not build an operator")

    monkeypatch.setattr(subgraph_runtime, "build_operator_enqueue", fail_build)
    executor = subgraph_runtime.OperatorExecutor(object(), {})
    marker = object()
    boundary = {"node_id": "edge", "kind": "boundary", "builder": "graph_boundary"}
    assert executor.launch(boundary, [marker]) is marker
    assert executor.outputs["edge"] is marker
    assert subgraph_runtime._cold_ring_capable(boundary) is False


def test_same_outputs_compares_tuples_and_never_agrees_on_all_none():
    torch = types.SimpleNamespace(
        allclose=lambda left, right, rtol=0.0, atol=0.0: left == right)
    assert sub._same_outputs((1, 2), (1, 2), torch) is True
    assert sub._same_outputs([1, 2], [1, 3], torch) is False
    assert sub._same_outputs((1, (2, 3)), (1, (2, 3)), torch) is True
    assert sub._same_outputs((1, 2), (1, 2, 3), torch) is False
    assert sub._same_outputs(None, None, torch) is None
    assert sub._same_outputs([None], [None], torch) is None
    assert sub._same_outputs(None, 1, torch) is False


def test_joint_split_posts_downstream_excluded_nodes():
    case = _case(
        nodes=[_node("head", kind="collective", op="all_reduce"), _node("t1"),
               _node("tail", kind="collective", op="all_reduce"), _node("after")],
        edges=[{"from": "head", "to": "t1", "kind": "data"},
               {"from": "t1", "to": "tail", "kind": "data"},
               {"from": "tail", "to": "after", "kind": "data"}],
        boundary={"include": ["t1"]})
    pre, timed, post = sub._joint_split(case, sub.topological_order(case))
    assert [node["node_id"] for node in pre] == ["head"]
    assert [node["node_id"] for node in timed] == ["t1"]
    assert [node["node_id"] for node in post] == ["tail", "after"]


class OrderingProtocol(FakeProtocol):
    def __init__(self, executor):
        super().__init__()
        self.executor = executor
        self.launched_at_timing = None

    def run(self, enqueue, *, case_id, kind="operator", nbytes=None):
        if self.launched_at_timing is None:
            self.launched_at_timing = list(self.executor.launched)
        return super().run(enqueue, case_id=case_id, kind=kind, nbytes=nbytes)


def test_execute_joint_case_launches_post_nodes_only_after_timing():
    case = _case(
        nodes=[_node("head", kind="collective", op="all_reduce"), _node("t1"),
               _node("tail", kind="collective", op="all_reduce"), _node("after")],
        edges=[{"from": "head", "to": "t1", "kind": "data"},
               {"from": "t1", "to": "tail", "kind": "data"},
               {"from": "tail", "to": "after", "kind": "data"}],
        boundary={"include": ["t1"]})
    executor = FakeExecutor()
    protocol = OrderingProtocol(executor)
    record = sub.execute_joint_case(executor, case, protocol, FakeJointRuntime())
    assert protocol.launched_at_timing == ["head", "t1"]
    assert executor.launched[-2:] == ["tail", "after"]
    assert record["pre_nodes"] == ["head"]
    assert record["post_nodes"] == ["tail", "after"]
    assert record["cut_nodes"] == ["head", "tail", "after"]
    assert record["timed_nodes"] == ["t1"]


def test_run_plan_records_a_generic_runtime_failure():
    class BoomExecutor(FakeExecutor):
        def launch(self, node):
            raise TypeError("dispatcher signature mismatch")

    result = sub.run_plan(_plan(), protocol=FakeProtocol(), executor=BoomExecutor())
    assert result["status"] == "partial"
    assert result["records"][0]["status"] == "failed"
    assert "dispatcher signature mismatch" in result["records"][0]["reason"]


def test_s1_cases_outside_the_participant_set_are_skipped():
    case = _case("participant")
    case["group_ranks"] = [2, 3]
    executor = FakeExecutor()
    executor.context = {"rank": 0}
    result = sub.run_plan(_plan([case], stage="s1_joint"), protocol=FakeProtocol(),
                          executor=executor, runtime=FakeJointRuntime())
    assert result["status"] == "ok"
    assert result["records"][0]["status"] == "skipped_non_participant"


def _qualified_timing():
    return {"timer_source": "torch.npu.Event(enable_timing=True)",
            "modes": {"eager": {"qualified": True, "trials": [
                {"trial": 0, "repeats_us": [1000.0]}]}}}


def test_s1_observations_emit_eager_and_aclgraph_arms(tmp_path):
    journal = ObservationJournal(tmp_path / "subgraph.jsonl")
    case = _case()
    case["identities"] = _plan_identities()
    record = {
        "status": "ok", "validated": True, "qualified": True,
        "outputs_agree": True, "timed_nodes": ["a", "b"],
        "eager": _qualified_timing(), "aclgraph": _qualified_timing(),
    }
    sub._emit_case_observations(journal, _plan(), case, record, "run-1",
                                "s1_joint", rank=3)
    rows = [json.loads(line) for line in
            (tmp_path / "subgraph.jsonl").read_text().splitlines()]
    observations = [row for row in rows if row["record_type"] == "observation"]
    assert len(observations) == 2
    assert {(row["identity"]["execution"]["graph"],
             row["identity"]["execution"]["mode"]) for row in observations} == {
        ("eager", "eager"), ("aclgraph", "eager")}
    assert all(row["identity"]["execution"]["stage"] == "s1_joint"
               for row in observations)
    assert all(row["rank"] == 3 for row in observations)
    assert all(row["qualified"] is True for row in observations)
    assert observations[0]["run_id"] != observations[1]["run_id"]
    assert observations[0]["sample_id"] != observations[1]["sample_id"]


def test_observation_boundary_always_matches_identity_boundary(tmp_path):
    journal = ObservationJournal(tmp_path / "subgraph.jsonl")
    case = _case()
    case["identities"] = _plan_identities()
    case["boundary"] = "resource_phase"
    record = {"status": "ok", "validated": True, "qualified": True,
              "timing": _qualified_timing()}
    sub._emit_case_observations(journal, _plan(), case, record, "run-1", "s0_local")
    rows = [json.loads(line) for line in journal.path.read_text().splitlines()]
    assert rows[0]["boundary"] == "device_kernel"
    assert rows[0]["boundary"] == rows[0]["identity"]["boundary"]

    plain = _case("plain")
    plain["timing"] = {"boundary": "resource_phase"}
    sub._emit_case_observations(journal, _plan(), plain, record, "run-2", "s0_local")
    rows = [json.loads(line) for line in journal.path.read_text().splitlines()]
    assert rows[-2]["boundary"] == "resource_phase"
    assert rows[-2]["boundary"] == rows[-2]["identity"]["boundary"]


BENCH_PACKETS_ENV = "MINDIE_BENCH_PACKETS"


def _bench_packets():
    import importlib.util
    import os
    from pathlib import Path

    pytest.importorskip("mindie_sim.prediction.primitives")
    root = Path(__file__).resolve().parents[1]
    candidates = [
        os.environ.get(BENCH_PACKETS_ENV),
        str(root.parent / "sim-a2-a3-unified" / "tools" / "bench_packets.py"),
        str(root.parent.parent / "sim" / "tools" / "bench_packets.py"),
        str(root.parent / "sim" / "tools" / "bench_packets.py"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("bench_packets", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    pytest.skip("bench_packets is unavailable in this workspace")


class SequenceProtocol(FakeProtocol):
    def __init__(self):
        super().__init__()
        self.index = 0

    def run(self, enqueue, *, case_id, kind="operator", nbytes=None):
        self.calls.append(case_id)
        enqueue()
        self.index += 1
        return {"case_id": case_id, "minimum_ms": 0.002, "startup_ms": 0.0,
                "timer_source": "torch.npu.Event(enable_timing=True)",
                "qualified": True,
                "modes": {"eager": {"qualified": True, "trials": [
                    {"trial": 0, "repeats_us": [1000.0 + self.index]}]}}}


def test_two_reruns_of_a_subgraph_plan_pass_without_packet_conflict(tmp_path):
    bench_packets = _bench_packets()
    path = tmp_path / "observations.jsonl"
    case = _case()
    case["split"] = "train"
    plan = _plan([case])
    results = [
        sub.run_plan(plan, protocol=SequenceProtocol(), executor=FakeExecutor(),
                     observations=path)
        for _ in range(2)
    ]
    assert results[0]["run_id"] != results[1]["run_id"]
    bundle = bench_packets.build_packets(list(bench_packets.iter_receipts([path])))
    assert bundle["manifest"]["observations"] == 2
    assert bundle["manifest"]["calibrate_samples"] == 2


def test_l2_resolution_prefers_cli_then_plan_then_sku_table():
    from mindie_profiler.bench.timing import MIB

    parser = sub._subgraph_parser()
    override = parser.parse_args(["--plan", "plan.json", "--l2-mib", "96"])
    assert sub._resolve_l2_bytes(override, {"sku": "Ascend910B4"}) == 96 * MIB
    plain = parser.parse_args(["--plan", "plan.json"])
    assert sub._resolve_l2_bytes(plain, {"l2_bytes": 123}) == 123
    assert sub._resolve_l2_bytes(plain, {"hardware_meta": {"l2_bytes": 456}}) == 456
    assert sub._resolve_l2_bytes(plain, {"sku": "Ascend910B4"}) == 100663296
    assert sub._resolve_l2_bytes(plain, {"hardware": "Ascend910_9362"}) == 201326592
    assert sub._resolve_l2_bytes(plain, {"sku": "unknown"}) is None


def test_typed_boundary_supply_uses_declared_dtype_and_shape():
    allocations: list[tuple] = []

    class BoundaryTorch:
        bfloat16 = "bf16"
        float32 = "float32"

        def zeros(self, *dims, dtype=None, device=None):
            allocations.append((dims, dtype, device))
            return ("tensor", dims)

    executor = sub.OperatorExecutor(BoundaryTorch(), {"device": {"ordinal": 0}})
    shaped = {"node_id": "b", "kind": "boundary", "dtype": "bf16",
              "shape": {"tokens": 8, "width": 16}}
    assert executor.supply_boundary(shaped) == ("tensor", (8, 16))
    assert allocations[0] == ((8, 16), "bf16", "npu:0")
    byte = {"node_id": "bytes", "kind": "boundary", "dtype": "fp32", "nbytes": 128}
    assert executor.supply_boundary(byte) == ("tensor", (32,))
    assert allocations[1] == ((32,), "float32", "npu:0")


def test_joint_split_rejects_a_non_convex_timed_cut():
    case = _case(
        nodes=[_node("a"), _node("b"), _node("c")],
        edges=[{"from": "a", "to": "b"}, {"from": "b", "to": "c"}],
        boundary={"include": ["a", "c"]})
    with pytest.raises(ProfilerUsageError, match="bench_subgraph_non_convex_cut:b"):
        sub._joint_split(case, sub.topological_order(case))


class _Leaf:
    def __init__(self, values):
        self.values = list(values)

    def detach(self):
        return _Leaf(self.values)

    def clone(self):
        return _Leaf(self.values)


def test_detach_recurses_into_tuples_and_lists():
    leaf = _Leaf([1])
    snapshot = sub._detach((leaf, [leaf]))
    leaf.values.append(2)
    assert snapshot[0] is not leaf and snapshot[0].values == [1]
    assert snapshot[1][0] is not leaf and snapshot[1][0].values == [1]


class _Shaped:
    def __init__(self, shape, dtype="bf16"):
        self.shape = tuple(shape)
        self.dtype = dtype


def test_same_outputs_rejects_shape_mismatch_and_allclose_errors():
    def boom(*_args, **_kwargs):
        raise RuntimeError("incomparable")

    torch = types.SimpleNamespace(allclose=boom)
    zeros = lambda size: _Shaped((size,))
    assert sub._same_outputs(
        (zeros(1), zeros(2)), (zeros(1), zeros(3)), torch) is False
    left = (_Shaped((1,)), _Shaped((2,)))
    right = (_Shaped((1,)), _Shaped((3,)))
    assert sub._same_outputs(left, right, torch) is False
    assert sub._same_outputs(_Shaped((1,)), _Shaped((2,)), torch) is False
    assert sub._same_outputs(_Shaped((1,), "bf16"), _Shaped((1,), "fp16"), torch) is False
    assert sub._same_outputs(_Shaped((1,)), _Shaped((1,)), torch) is False
    assert sub._same_outputs(None, None, torch) is None
    assert sub._same_outputs(None, _Shaped((1,)), torch) is False


def test_ep8_and_ep64_groups_resolve_by_declared_size_on_64_ranks(monkeypatch):
    import sys
    from mindie_profiler.bench.operators_moe_comm import _group_for

    created: list[list[int]] = []

    class Dist:
        def init_process_group(self, backend, rank=None, world_size=None, timeout=None):
            return None

        def new_group(self, members):
            created.append(list(members))
            return list(members)

        def destroy_process_group(self):
            return None

    module = types.ModuleType("torch.distributed")
    dist = Dist()
    module.init_process_group = dist.init_process_group
    module.new_group = dist.new_group
    module.destroy_process_group = dist.destroy_process_group
    monkeypatch.setitem(sys.modules, "torch.distributed", module)
    case = {"case_id": "joint", "parallel": {"ep": 64},
            "nodes": [{"node_id": "ep8", "kind": "collective",
                       "op": "all_reduce", "group": "ep", "group_size": 8}]}
    runtime = sub.TorchJointRuntime(types.SimpleNamespace(), rank=9, world_size=64,
                                    cases=[case])
    runtime.init_process_group()
    assert runtime.groups["ep:8"] == list(range(8, 16))
    assert runtime.groups["ep:64"] == list(range(64))
    assert runtime.groups["ep"] == list(range(8, 16))
    context = {"groups": runtime.groups}
    assert _group_for({"group": "ep", "group_size": 8}, context) == list(range(8, 16))
    assert _group_for({"group": "ep", "group_size": 64}, context) == list(range(64))
    runtime.close()


class RecordingProtocol(FakeProtocol):
    def __init__(self):
        super().__init__()
        self.kinds: list[tuple[str, int | None]] = []

    def run(self, enqueue, *, case_id, kind="operator", nbytes=None):
        self.kinds.append((kind, nbytes))
        return super().run(enqueue, case_id=case_id, kind=kind, nbytes=nbytes)


def test_execute_joint_case_passes_static_collective_modes():
    case = _case(
        nodes=[_node("a"), _node("comm", kind="collective", op="all_reduce")],
        edges=[], boundary={"include": ["a", "comm"]})
    case["work_bytes"] = 4096
    protocol = RecordingProtocol()
    record = sub.execute_joint_case(FakeExecutor(), case, protocol, FakeJointRuntime())
    assert record["qualified"] is True
    assert protocol.kinds == [("collective", 4096), ("collective", 4096)]


def test_execute_local_case_rejects_a_missing_data_upstream_producer():
    case = _case(
        nodes=[_node("a"), _node("b")],
        edges=[{"from": "a", "to": "b", "kind": "data"}],
        boundary={"include": ["b"]})
    torch = types.SimpleNamespace(
        npu=types.SimpleNamespace(synchronize=lambda: None))
    executor = sub.OperatorExecutor(torch, {"device": {"ordinal": 0}})
    with pytest.raises(ProfilerUsageError, match="bench_subgraph_missing_upstream:b"):
        sub.execute_local_case(executor, case, FakeProtocol())


def test_subgraph_calibrates_and_forwards_stream_blocker_for_small_s0_cases():
    from mindie_profiler.bench import timing as bench_timing
    from tests.test_bench_timing_protocol import FakeTensor, FakeTorch

    fake_torch = FakeTorch()
    fake_torch.zeros = lambda *shape, **_kw: FakeTensor(shape)
    fake_torch.ones = lambda *shape, **_kw: FakeTensor(shape)
    runtime = bench_timing.TorchTimingRuntime(fake_torch)
    protocol = bench_timing.MeasurementProtocol(runtime, warmups=1, trials=1, repeats=2)

    def unit_op():
        fake_torch.clock.ms += 0.05

    ctx: dict = {
        "torch": fake_torch,
        "runtime": runtime,
        "protocol": protocol,
        "device": {"ordinal": 0},
        "blocker_unit_op": unit_op,
        "op_overrides": {"rms_norm": lambda *_a, **_k: fake_torch.clock.__setattr__("ms", fake_torch.clock.ms + 0.01)},
    }
    executor = sub.OperatorExecutor(fake_torch, ctx)
    case = _case(
        nodes=[{**_node("n0", op="rms_norm"), "builder": "rms_norm", "dtype": "bf16", "shape": {"tokens": 1, "width": 8}}],
        edges=[],
        boundary={"include": ["n0"]},
    )
    res = sub.run_plan(_plan([case]), protocol=protocol, executor=executor)
    rec = res["records"][0]
    assert rec["status"] == "ok"
    assert rec["qualified"] is True
    assert rec["timing"]["stream_saturated_available"] is True
    assert rec["timing"]["modes"]["stream_saturated"]["qualified"] is True


def test_subgraph_full_decode_only_policy_runs_prefill_eager_and_decode_aclgraph(tmp_path):
    from mindie_profiler.bench import timing as bench_timing
    from tests.test_bench_timing_protocol import FakeTensor, FakeTorch

    fake_torch = FakeTorch()
    fake_torch.zeros = lambda *shape, **_kw: FakeTensor(shape)
    fake_torch.ones = lambda *shape, **_kw: FakeTensor(shape)
    fake_torch.allclose = lambda left, right, rtol=0.0, atol=0.0: type(left) is type(right) and getattr(left, "shape", getattr(left, "dims", None)) == getattr(right, "shape", getattr(right, "dims", None))
    graph = FakeGraph()
    fake_torch.npu.NPUGraph = lambda: graph
    fake_torch.npu.graph = lambda target: _GraphContext(target)
    runtime = bench_timing.TorchTimingRuntime(fake_torch)
    protocol = bench_timing.MeasurementProtocol(runtime, warmups=1, trials=1, repeats=2)

    def unit_op():
        fake_torch.clock.ms += 0.05

    def fake_rms(x, *_a, **_k):
        fake_torch.clock.ms += 0.01
        return x

    ctx: dict = {
        "torch": fake_torch, "runtime": runtime, "protocol": protocol,
        "device": {"ordinal": 0}, "blocker_unit_op": unit_op,
        "op_overrides": {"rms_norm": fake_rms},
    }
    executor = sub.OperatorExecutor(fake_torch, ctx)
    joint_rt = sub.TorchJointRuntime(fake_torch)

    prefill_case = {
        **_case("prefill-s0", nodes=[{**_node("p0", op="rms_norm"), "builder": "rms_norm", "dtype": "bf16", "shape": {"tokens": 512, "width": 8}}], edges=[], boundary={"include": ["p0"]}),
        "phase": "prefill",
    }
    decode_case = {
        **_case("decode-s0", nodes=[{**_node("d0", op="rms_norm"), "builder": "rms_norm", "dtype": "bf16", "shape": {"tokens": 1, "width": 8}}], edges=[], boundary={"include": ["d0"]}),
        "phase": "decode",
    }
    obs_path = tmp_path / "full_decode_only.jsonl"
    res = sub.run_plan(
        _plan([prefill_case, decode_case], stage="s0_local", modes=("eager", "aclgraph")),
        runtime=joint_rt, protocol=protocol, executor=executor, observations=obs_path,
    )
    assert res["status"] == "ok"
    pf_rec, dec_rec = res["records"]
    assert pf_rec["execution_modes"] == ["eager"]
    assert pf_rec["graph_policy"] == "FULL_DECODE_ONLY"
    assert "aclgraph" not in pf_rec
    assert dec_rec["execution_modes"] == ["eager", "aclgraph"]
    assert dec_rec["graph_policy"] == "FULL_DECODE_ONLY"
    assert dec_rec["outputs_agree"] is True
    assert dec_rec["aclgraph"]["modes"]["stream_saturated"]["qualified"] is True
    assert graph.replays > 0

    # S1 prefill also enforces FULL_DECODE_ONLY -> eager only (zero graph captures)
    s1_rt = FakeJointRuntime(match=True)
    s1_pf = sub.execute_joint_case(FakeExecutor(), {**_case("pf-s1"), "phase": "prefill"}, FakeProtocol(), s1_rt, execution_modes=["eager", "aclgraph"])
    assert s1_pf["execution_modes"] == ["eager"]
    assert s1_pf["aclgraph"] is None and s1_rt.captures == 0

    # Failed graph-only S0 run emits ZERO qualified rows (never a duplicate qualified base row)
    bad_rt = FakeJointRuntime(match=False)
    bad_obs = tmp_path / "failed_graph_only.jsonl"
    bad_res = sub.run_plan(
        _plan([decode_case], stage="s0_local", modes=("aclgraph",)),
        runtime=bad_rt, protocol=protocol, executor=executor, observations=bad_obs,
    )
    assert bad_res["status"] == "partial"
    assert bad_res["records"][0]["status"] == "unqualified"
    bad_rows = [json.loads(line) for line in bad_obs.read_text().splitlines() if '"observation"' in line]
    assert len(bad_rows) == 4 and all(r["qualified"] is False for r in bad_rows)


def test_non_contiguous_multi_axis_group_ranks_form_exact_hccs_sw_cosets(monkeypatch):
    import sys

    created: list[list[int]] = []
    dispatched: list[tuple[int, str, list[int]]] = []

    class Dist:
        def init_process_group(self, backend, rank=None, world_size=None, timeout=None):
            return None

        def is_initialized(self):
            return True

        def new_group(self, members):
            group = list(members)
            created.append(group)
            return group

        def destroy_process_group(self):
            return None

        def all_reduce(self, tensor, group=None):
            dispatched.append((current_rank[0], "all_reduce", list(group)))
            return tensor

    current_rank = [0]
    dist = Dist()
    module = types.ModuleType("torch.distributed")
    module.init_process_group = dist.init_process_group
    module.is_initialized = dist.is_initialized
    module.new_group = dist.new_group
    module.destroy_process_group = dist.destroy_process_group
    module.all_reduce = dist.all_reduce
    monkeypatch.setitem(sys.modules, "torch.distributed", module)

    dcp_node = {
        "node_id": "dcp0", "kind": "collective", "op": "all_reduce",
        "builder": "all_reduce", "dtype": "bf16", "nbytes": 4096,
        "group": "dcp", "group_size": 2, "group_ranks": [0, 2],
    }
    pcp_wide_node = {
        "node_id": "pcp4", "kind": "collective", "op": "all_reduce",
        "builder": "all_reduce", "dtype": "bf16", "nbytes": 4096,
        "group": "pcp", "group_size": 2, "group_ranks": [0, 4],
    }
    pcp_narrow_node = {
        "node_id": "pcp2", "kind": "collective", "op": "all_reduce",
        "builder": "all_reduce", "dtype": "bf16", "nbytes": 4096,
        "group": "pcp", "group_size": 2, "group_ranks": [0, 2],
    }
    roce_node = {
        "node_id": "roce0", "kind": "collective", "op": "all_reduce",
        "builder": "all_reduce", "dtype": "fp32", "nbytes": 4096,
        "group": "inter_node_roce", "group_size": 8,
        "group_ranks": [0, 1, 2, 3, 8, 9, 10, 11],
    }
    cases = [
        {"case_id": "sub-dcp", "parallel": {"tp": 2, "pcp": 2, "dcp": 2}, "nodes": [dcp_node]},
        {"case_id": "sub-pcp4", "parallel": {"tp": 4, "pcp": 2}, "nodes": [pcp_wide_node]},
        {"case_id": "sub-pcp2", "parallel": {"tp": 2, "pcp": 2}, "nodes": [pcp_narrow_node]},
        {"case_id": "fab-roce", "kind": "fabric", "group_ranks": [0, 1, 2, 3, 8, 9, 10, 11], "nodes": [roce_node]},
    ]

    from tests.test_bench_timing_protocol import FakeTensor, FakeTorch

    fake_torch = FakeTorch()
    fake_torch.zeros = lambda *shape, **_kw: FakeTensor(shape)
    fake_torch.ones = lambda *shape, **_kw: FakeTensor(shape)
    fake_torch.distributed = dist
    for rank, exp_dcp, exp_pcp4, exp_pcp2 in (
        (0, [0, 2], [0, 4], [0, 2]),
        (1, [1, 3], [1, 5], [1, 3]),
        (5, [5, 7], [1, 5], [5, 7]),
    ):
        created.clear()
        current_rank[0] = rank
        rt = sub.TorchJointRuntime(fake_torch, rank=rank, world_size=8, cases=cases)
        rt.init_process_group()
        # Non-contiguous cosets [0,2],[1,3],[4,6],[5,7] and [0,4],[1,5],[2,6],[3,7] are created;
        # out-of-world [0..3,8..11] is never truncated into a fake 4-rank intra-node group.
        for coset in ([0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]):
            assert coset in created
        assert [0, 1, 2, 3, 8, 9, 10, 11] not in created
        ctx = {
            "torch": fake_torch, "dist": dist, "groups": rt.groups,
            "dist_initialized": True, "rank": rank, "world_size": 8,
            "device": {"ordinal": 0}, "allow_cpu_smoke": True,
        }
        executor = sub.OperatorExecutor(fake_torch, ctx)
        executor.launch(dcp_node)
        executor.launch(pcp_wide_node)
        executor.launch(pcp_narrow_node)
        assert dispatched[-3:] == [
            (rank, "all_reduce", exp_dcp),
            (rank, "all_reduce", exp_pcp4),
            (rank, "all_reduce", exp_pcp2),
        ]
        with pytest.raises(sub.ProfilerUsageError, match="bench_collective_group_missing"):
            executor.launch(roce_node)
        rt.close()


def test_mixed_domains_and_work_bytes_forward_and_roundtrip_sim_packets(tmp_path):
    obs_path = tmp_path / "multi_domain_and_fabric.jsonl"
    journal = ObservationJournal(obs_path)
    plan = _plan()

    for idx, (work, wb, dur_us) in enumerate(((4096, 8192, 1200.0), (8192, 16384, 2100.0))):
        case = _case(f"mixed-sub-{idx}")
        case["split"] = "train"
        ident = _plan_identities()
        ident["service"].pop("identity", None)
        ident["service"]["work"] = work
        ident["service"]["mixed_domains"] = True
        ident["primitive_key"]["shape"] = {"m": idx + 1}
        ident["accuracy_identity"]["shape"] = {"m": idx + 1}
        case["identities"] = ident
        case["work_bytes"] = wb
        rec = {
            "status": "ok", "validated": True, "qualified": True,
            "timed_nodes": ["a", "b"], "outputs_agree": True,
            "timing": {"modes": {"aclgraph": {"qualified": True, "trials": [
                {"trial": 0, "repeats_us": [dur_us]}]}}},
        }
        sub._emit_case_observations(journal, plan, case, rec, f"run-m{idx}", "s0_local")

    for idx, (payload, dur_us) in enumerate(((4096, 500.0), (16384, 900.0))):
        fab = _case(
            f"fabric-hccs-{idx}",
            nodes=[{
                "node_id": "fab0", "kind": "collective", "op": "all_reduce",
                "builder": "all_reduce", "dtype": "fp32", "implementation": "all_reduce",
                "kernel": "all_reduce", "shape": {"bytes": payload, "group_size": 4},
            }],
            edges=[], boundary={"include": ["fab0"]},
        )
        fab.update({
            "split": "train",
            "kind": "fabric", "phase": "fabric", "route": "intra_node_hccs",
            "group_ranks": [0, 2, 4, 6], "work_bytes": payload, "fabric_bytes": payload,
            "identities": {
                "primitive_key": {
                    "hardware": {"sku": "Ascend910_9382", "architecture": "A3"},
                    "implementation": "all_reduce", "kernel": "all_reduce",
                    "dtype": "fp32", "shape": {"bytes": payload, "group_size": 4},
                    "scope": "device_kernel",
                },
                "accuracy_identity": {
                    "level": "operator", "boundary": "device_kernel",
                    "hardware": "Ascend910_9382", "phase": "fabric",
                    "implementation": "all_reduce",
                    "shape": {"bytes": payload, "group_size": 4},
                    "dtype": "fp32", "layout": "contiguous",
                    "execution": {"mode": "eager", "stage": "s1_joint"},
                },
                "service": {
                    "resource": "latency", "work_unit": "launches", "work": 1,
                    "active_units": 1, "boundary": "device_kernel",
                    "mixed_domains": False,
                },
            },
        })
        rec = {
            "status": "ok", "validated": True, "qualified": True,
            "timed_nodes": ["fab0"], "outputs_agree": None,
            "eager": {"modes": {"eager": {"qualified": True, "trials": [
                {"trial": 0, "repeats_us": [dur_us]}]}}},
        }
        sub._emit_case_observations(journal, plan, fab, rec, f"run-f{idx}", "s1_joint")

    rows = [json.loads(line) for line in obs_path.read_text().splitlines()]
    obs_rows = [r for r in rows if r["record_type"] == "observation"]
    done_rows = [r for r in rows if r["record_type"] == "case_complete"]
    mixed_obs = [r for r in obs_rows if r["case_id"].startswith("mixed-sub-")]
    fab_obs = [r for r in obs_rows if r["case_id"].startswith("fabric-hccs-")]

    assert all(r["mixed_domains"] is True for r in mixed_obs)
    assert [r["work_bytes"] for r in mixed_obs] == [8192, 16384]
    assert done_rows[0]["summary"]["mixed_domains"] is True
    assert done_rows[0]["summary"]["work_bytes"] == 8192
    assert all(r["mixed_domains"] is False and r["route"] == "intra_node_hccs" for r in fab_obs)
    assert [r["work_bytes"] for r in fab_obs] == [4096, 16384]

    try:
        from tools.bench_packets import build_packets, iter_receipts
    except ImportError:
        return
    bundle = build_packets(iter_receipts([obs_path]))
    # mixed_domains=True rows are excluded from fit-service, while rate & calibrate packets round-trip!
    assert bundle["fit-service"] == []
    assert len(bundle["fit-rate"]) == 2
    routes = {cond["route"] for cond in bundle["rate_conditions"]}
    assert "intra_node_hccs" in routes
    assert len(bundle["calibrate"]) == 4

