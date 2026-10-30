"""Retained source programs must not execute at invented segmentation geometry."""
from collections import Counter
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest


def test_qwen96_twoshot_keeps_normalized_layer_plan_without_physical_b1_graph(monkeypatch):
    sim = pytest.importorskip("mindie_sim")
    case_path = (Path(sim.__file__).resolve().parents[1] /
                 "examples/cases/high-concurrency-20261030/qwen-source-gdn-native/"
                 "qwen36-a5-tp2-c96-source-gdn-native.json")
    if not case_path.is_file():
        pytest.skip("requires the source-pinned high-concurrency Sim case")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "examples/structure"))
    replay = importlib.import_module("decode")
    original = json.loads(case_path.read_text())
    source = deepcopy(original)
    # This is the committed HCCL source alternative: its physical invocation
    # is B96/q4. The former metadata-only B1/q1 lowering rejects this template.
    source["runtime"]["kernels"]["hccl"] = {"allreduce": {
        "expansion": "AIV", "template": "mesh_twoshot", "block_limit": 63,
        "axes": ["tp"],
    }}
    before = deepcopy(source)
    config = replay._model_config(source)
    assert config == replay._model_config(original)
    assert Counter(plan["attention"] for plan in config["layer_plans"]) == {"gdn": 48, "gqa": 16}
    assert config["tp"] == 2
    assert source == before
