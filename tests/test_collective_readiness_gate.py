"""Real A5 all_reduce train: rank-local connections, communicator ordinals."""
from pathlib import Path

import pytest

from mindie_profiler.collective_readiness import read_collective_readiness

ROOT = Path("/Volumes/data/mindie-sim-data/calibration-20261107/a5/hccl-native/"
            "profiles/gate/native.all_reduce.g2.h4096.t128.train")
pytestmark = pytest.mark.skipif(not ROOT.exists(), reason="local A5 gate corpus absent")


def test_gate_ordinals_are_communicator_sequence_not_connection():
    report = read_collective_readiness(ROOT)
    assert len(report["calls"]) == 20
    for rank in ("rank_0", "rank_1"):
        calls = [item for item in report["calls"] if item["rank_id"] == rank]
        assert [item["call_ordinal"] for item in calls] == list(range(10))
        assert all(item["operation"]["communicator"] == "group_name_0"
                   for item in calls)
    second = {item["rank_id"]: item for item in report["calls"]
              if item["call_ordinal"] == 1}
    assert second["rank_0"]["connection_id"] != second["rank_1"]["connection_id"]
    assert second["rank_0"]["operation"]["op_name"].endswith("_612_1_1")
    assert second["rank_1"]["operation"]["op_name"].endswith("_612_1_1")


def test_gate_binder_positive_and_wrong_group_ordinal_negative():
    pytest.importorskip("mindie_sim")
    from mindie_sim.prediction.collective_readiness import bind_pipeline_ready
    from mindie_sim.prediction.engine import Engine, Resource

    report = read_collective_readiness(ROOT)
    engine = Engine([Resource("wire", 1_000_000_000, "bytes")], trace_limit=8)
    ready = {0: engine.submit("r0"), 1: engine.submit("r1")}
    for ordinal in (1, 7):
        ctx = bind_pipeline_ready(
            report, ready, communicator="group_name_0", ordinal=ordinal,
            expected_collective="all_reduce", expected_bytes=1_048_576,
            expected_dtype="bf16", expected_group_size=2)
        assert sorted(ctx) == [0, 1]
    for kwargs in ({"communicator": "group_name_9", "ordinal": 1},
                   {"communicator": "group_name_0", "ordinal": 2}):
        with pytest.raises(Exception):
            bind_pipeline_ready(
                report, ready, expected_collective="all_reduce",
                expected_bytes=1_048_576, expected_dtype="bf16",
                expected_group_size=2, **kwargs)
