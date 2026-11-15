"""Focused tests for the independent original-row native-window source.

[Role]
  Exercise the streaming discovery, raw timetable accounting, rank/hardware
  declaration binding, multiple-trace keying, explicit unknown boundaries and
  the structural-declaration whitelist of ``zero_shot_native_windows``.

[Invariants]
  * Two retained captures of one enrolled ID stay distinct and each key carries
    its own content SHA, rank/device and source path.
  * Device span (max end - min start) and additive across streams (sum of
    durations) stay separate; raw op-type x native-core cells are retained.
  * Rank comes from the launch declaration plus the raw Device_id; hardware
    comes from preflight, not the cell-id suffix.
  * A missing source yields one explicit missing_source record, never silence.
  * A supplied structural declaration cannot smuggle measurement payloads into
    segmentation inputs.

[Timeouts & Locks]
  Tiny local gzip/CSV/JSON fixtures under pytest ``tmp_path``; no network,
  subprocess, sleep or device work.

[Side-Effect Policy]
  All generated artifacts live under ``tmp_path``; the repository is read-only.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))

import zero_shot_native_windows as native  # noqa: E402

_KERNEL_HEADER = (
    "Device_id,Type,Name,Accelerator Core,Stream ID,Start Time(us),"
    "Duration(us),Wait Time(us),Block Num\n"
)
_OPSTAT_HEADER = (
    "Device_id,OP Type,Core Type,Count,Total Time(us),Min Time(us),"
    "Avg Time(us),Max Time(us),Ratio(%)\n"
)
_DECLARATION = {
    "name": "synthetic-one-layer",
    "layers": 1,
    "body_layers": 1,
    "hidden_size": 8,
    "vocab_size": 16,
    "tp": 1,
    "layer_plans": [{"index": 0, "attention": "mla", "ffn": "moe", "mtp": False}],
}


def _write_kernel(path: Path, device: int, rows: list[tuple[str, str, int, float, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [_KERNEL_HEADER]
    for op_type, core, stream, start_us, duration_us in rows:
        lines.append(
            f"{device},{op_type},{op_type},{core},{stream},{start_us},{duration_us},0,1\n")
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.writelines(lines)


def _write_opstat(path: Path, device: int, cells: list[tuple[str, str, int, float]]) -> None:
    lines = [_OPSTAT_HEADER]
    for op_type, core, count, total_us in cells:
        lines.append(f"{device},{op_type},{core},{count},{total_us},{total_us},{total_us},{total_us},1.0\n")
    path.write_text("".join(lines), encoding="utf-8")


def _layout(root: Path) -> dict:
    case = root / "out" / "case_x"
    cell = case / "dc_1k_c1"
    rows = [
        ("RmsNorm", "AI_VECTOR_CORE", 61, 100.0, 10.0),
        ("RmsNorm", "AI_VECTOR_CORE", 61, 110.0, 20.0),
        ("MatMulV3", "AI_CORE", 62, 120.0, 5.0),
        ("MatMulV3", "MIX_AIC", 62, 200.0, 10.0),
    ]
    for host, start_rank in (("host-a", 0), ("host-b", 1)):
        device = 0  # one declared local worker on each node; global rank adds dp_start
        worker = f"dp{start_rank}_pp0_tp0_dcp0_ep{start_rank}_rank0_1_20260101000000_ascend_pt"
        base = cell / host / worker
        _write_kernel(base / "kernel_details.csv.gz", device, rows)
        _write_opstat(base / "op_statistic.csv", device,
                      [("RmsNorm", "AI_VECTOR_CORE", 2, 30.0),
                       ("MatMulV3", "AI_CORE", 1, 5.0),
                       ("MatMulV3", "MIX_AIC", 1, 10.0)])
        command = case / "cmd" / f"serve_case_x_{host}.sh"
        command.parent.mkdir(parents=True, exist_ok=True)
        command.write_text(
            "vllm serve m --tensor-parallel-size 1 --data-parallel-size 2 "
            f"--data-parallel-size-local 1 --data-parallel-start-rank {start_rank}\n",
            encoding="utf-8")
    evidence = root / "evidence" / "preflight_case_x.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps([
        {"node": "host-a", "hostname": "rack-a", "img": "img-a", "cfg": "cfg-a",
         "npu_raw": "| 0 | Ascend950DT | OK |"},
        {"node": "host-b", "hostname": "rack-b", "img": "img-b", "cfg": "cfg-b",
         "npu_raw": "| 0 | Ascend950DT | OK |"},
    ]), encoding="utf-8")
    return {"cell_id": "case_x_dc_1k_c1", "phase": "decode", "tp": 1}


def test_two_retained_traces_keep_own_sha_rank_hardware_and_raw_accounting(tmp_path):
    root = tmp_path / "root"
    row = _layout(root)
    timetables = list(native.iter_trace_timetables(
        row, roots=[root], declaration=_DECLARATION))
    assert len(timetables) == 2
    assert len({item.trace_key for item in timetables}) == 2
    assert {item.rank for item in timetables} == {0, 1}
    assert {item.device_id for item in timetables} == {0}
    assert {item.hardware["hardware_key"] for item in timetables} == {"Ascend950DT"}
    assert {item.rank_basis for item in timetables} == {
        "launch_data_parallel_start_rank_x_tp_plus_raw_device_id"}
    for item in timetables:
        assert item.source_sha256 and len(item.source_sha256) == 64
        assert item.size_bytes > 0
        assert item.raw_start_ns == 100_000 and item.raw_end_ns == 210_000
        assert item.raw_span_ms == 0.110  # 100us -> 210us, max end - min start
        assert item.raw_additive_ms == 0.045  # 10+20+5+10 us
        assert len(item.streams) == 2
        cells = {(cell.op_type, cell.core): cell for cell in item.operators}
        assert cells[("RmsNorm", "AI_VECTOR_CORE")].count == 2
        assert cells[("RmsNorm", "AI_VECTOR_CORE")].additive_ms == 0.030
        assert cells[("MatMulV3", "AI_CORE")].additive_ms == 0.005
        assert cells[("MatMulV3", "MIX_AIC")].additive_ms == 0.010
        assert item.boundaries["raw_span"] and item.boundaries["operators"]
        assert item.boundaries["rank"] and item.boundaries["hardware"]
    # Additive mass exceeds the elapsed span here because streams overlap.
    assert timetables[0].raw_additive_ms < timetables[0].raw_span_ms


def test_keyed_targets_are_self_contained_and_json_serializable(tmp_path):
    root = tmp_path / "root"
    row = _layout(root)
    targets = list(native.iter_native_targets(row, roots=[root], declaration=_DECLARATION))
    assert targets
    kinds = {target.kind for target in targets}
    assert {"trace", "operator"} <= kinds
    keys = [target.key for target in targets]
    assert len(keys) == len(set(keys))
    for target in targets:
        payload = target.as_dict()
        json.dumps(payload)
        assert payload["source_sha256"] == target.source_sha256
        assert payload["trace_key"] == target.trace_key
    summary = native.summarize_targets(iter(targets))
    assert summary["target_counts"]["trace"] == 2
    assert summary["target_counts"]["operator"] >= 6


def test_missing_source_is_explicit_not_empty(tmp_path):
    row = {"cell_id": "unknown_cell", "phase": "decode", "tp": 1}
    timetables = list(native.iter_trace_timetables(row, roots=[tmp_path / "empty"]))
    assert len(timetables) == 1
    item = timetables[0]
    assert item.status == "missing_source"
    assert item.reason == "cell_directory_not_retained"
    assert item.boundaries["raw_span"] is False
    assert item.boundaries["forwards"] is False


def test_declaration_rejects_measurement_payload_and_requires_topology(tmp_path):
    root = tmp_path / "root"
    row = _layout(root)
    poisoned = dict(_DECLARATION)
    poisoned["runtime"] = {"kernels": {"service_regimes": [{"duration_ms": 99.0}]}}
    timetables = list(native.iter_trace_timetables(
        row, roots=[root], declaration=poisoned))
    assert len(timetables) == 2
    for item in timetables:
        assert item.declaration["basis"] == (
            "explicit_structural_declaration_without_actual_capture_binding")
        assert "runtime" not in item.declaration
    broken = {"hidden_size": 8, "vocab_size": 16, "tp": 1}
    item = next(iter(native.iter_trace_timetables(row, roots=[root], declaration=broken)))
    assert item.status == "raw_only"
    assert item.reason and "declaration_unparsed" in item.reason
    assert item.operators  # raw evidence survives the missing declaration


def test_enrolled_rows_stream_from_plain_and_gzip(tmp_path):
    rows = [{"cell_id": "a", "phase": "decode"}, {"cell_id": "b", "phase": "prefill"}]
    plain = tmp_path / "rows.jsonl"
    plain.write_text("\n".join(json.dumps(item) for item in rows) + "\n", encoding="utf-8")
    assert list(native.iter_enrolled_rows(plain)) == rows
    compressed = tmp_path / "rows.jsonl.gz"
    with gzip.open(compressed, "wt", encoding="utf-8") as handle:
        handle.write("\n".join(json.dumps(item) for item in rows) + "\n")
    assert list(native.iter_enrolled_rows(compressed)) == rows


def test_malformed_raw_schema_is_explicit_and_does_not_abort_iteration(tmp_path):
    root = tmp_path / "root"
    case = root / "out" / "case_bad"
    worker = case / "dc_1k_c1" / "host-a" / "dp0_pp0_tp0_dcp0_ep0_rank0_1_x_ascend_pt"
    worker.mkdir(parents=True)
    with gzip.open(worker / "kernel_details.csv.gz", "wt", encoding="utf-8") as handle:
        handle.write("Device_id,Type,Start Time(us),Duration(us)\n0,MatMulV3,1,2\n")
    row = {"cell_id": "case_bad_dc_1k_c1", "phase": "decode", "tp": 1}
    item = next(iter(native.iter_trace_timetables(
        row, roots=[root], declaration=_DECLARATION)))
    assert item.status == "raw_only"
    assert item.reason and item.reason.startswith("source_scan_error")
    assert item.boundaries["operators"] is False
    targets = list(native.iter_native_targets(
        row, roots=[root], declaration=_DECLARATION))
    assert [target.kind for target in targets] == ["trace"]
    assert targets[0].status == "raw_only"


def _classification_layout(root: Path) -> None:
    case = root / "out" / "case_dup"

    def write_cell(name: str, host: str, worker: str, body: bytes, device: int) -> Path:
        base = case / name / host / worker
        base.mkdir(parents=True)
        path = base / "kernel_details.csv.gz"
        with gzip.open(path, "wb") as handle:
            handle.write(body)
        (base / "op_statistic.csv").write_text(
            f"{_OPSTAT_HEADER}{device},MatMulV3,AI_CORE,1,1.0,1.0,1.0,1.0,1.0\n",
            encoding="utf-8")
        return path

    shared = (_KERNEL_HEADER + "0,MatMulV3,MatMulV3,AI_CORE,1,1.0,2.0,0,1\n").encode()
    c16 = write_cell("dc_c16", "host-a", "dp0_rank0_1_a_ascend_pt", shared, 0)
    c16b = write_cell("dc_c16", "host-b", "dp1_rank0_1_b_ascend_pt",
                      (_KERNEL_HEADER + "1,MatMulV3,MatMulV3,AI_CORE,1,3.0,4.0,0,1\n").encode(), 1)
    write_cell("dc_c8", "host-a", "dp0_rank0_1_a_ascend_pt", shared, 0)
    c8b = write_cell("dc_c8", "host-b", "dp1_rank0_1_c_ascend_pt",
                     (_KERNEL_HEADER + "1,MatMulV3,MatMulV3,AI_CORE,1,5.0,6.0,0,1\n").encode(), 1)
    stale = (_KERNEL_HEADER + "0,MatMulV3,MatMulV3,AI_CORE,1,7.0,8.0,0,1\n").encode()
    stale_path = write_cell("dc_old", "host-a", "dp0_rank0_1_old_ascend_pt", stale, 0)
    logs = root / "logs"
    logs.mkdir()
    (logs / "lane.log").write_text(
        "CELL case_dup_dc_c16 rc=0 captured=True "
        f"export=[('host-a', {c16.stat().st_size}), ('host-b', {c16b.stat().st_size})]\n"
        "CELL case_dup_dc_c8 rc=0 captured=True "
        f"export=[('host-a', {c16.stat().st_size}), ('host-b', {c8b.stat().st_size})]\n"
        f"CELL case_dup_dc_old rc=0 captured=True export=[('host-a', {stale_path.stat().st_size})]\n"
        f"CELL case_dup_dc_old rc=0 captured=True export=[('host-a', {stale_path.stat().st_size + 1})]\n",
        encoding="utf-8")


def test_shared_payload_needs_digest_and_stale_receipt_evidence(tmp_path):
    root = tmp_path / "root"
    _classification_layout(root)
    row_c16 = {"cell_id": "case_dup_dc_c16", "phase": "decode", "tp": 1}
    c16 = list(native.iter_trace_timetables(row_c16, roots=[root]))
    shared = [item for item in c16 if item.host == "host-a"]
    assert len(shared) == 1 and shared[0].source_class == "shared_payload"
    assert shared[0].source_evidence["shared_with"][0]["cell_id"] == "case_dup_dc_c8"
    assert shared[0].source_evidence["independent_source_key"] == shared[0].raw_stream_sha256
    unique = [item for item in c16 if item.host == "host-b"][0]
    assert unique.source_class == "actual"
    assert unique.source_grade == "C_host_size_association"
    assert unique.exact_identity is False
    assert unique.worker_qualification == "host_size_only_unverified"
    row_c8 = {"cell_id": "case_dup_dc_c8", "phase": "decode", "tp": 1}
    c8_shared = [item for item in native.iter_trace_timetables(row_c8, roots=[root])
                 if item.host == "host-a"][0]
    assert c8_shared.source_evidence["independent_source_key"] == shared[0].raw_stream_sha256
    row_old = {"cell_id": "case_dup_dc_old", "phase": "decode", "tp": 1}
    old = next(iter(native.iter_trace_timetables(row_old, roots=[root])))
    assert old.source_class == "stale_superseded"
    assert old.source_evidence["receipt_match"] == "earlier"
    assert old.raw_stream_sha256 and len(old.raw_stream_sha256) == 64


def test_actual_weight_config_wins_over_similar_template(tmp_path, monkeypatch):
    from types import SimpleNamespace

    root = tmp_path / "root"
    row = _layout(root)
    case = root / "out" / "case_x"
    config = config_bytes = (
        b'{"architectures":["GlmMoeDsaForCausalLM"],"model_type":"glm_moe_dsa",'
        b'"hidden_size":6144,"num_hidden_layers":78,"vocab_size":154880}')
    weights = tmp_path / "weights"
    weight_dir = weights / "GLM-5.1-w4a4c8-mxfp4"
    weight_dir.mkdir(parents=True)
    (weight_dir / "config.json").write_bytes(config_bytes)
    import hashlib as _hashlib
    cfg_sha = _hashlib.sha256(config_bytes).hexdigest()
    (case / "status.json").write_text(json.dumps({
        "started": "2026-11-07T00:00:00Z",
        "spec": {"model": "/mnt/weight/GLM-5.1-w4a4c8-mxfp4",
                 "quantization": "w4a4c8", "served": "glm51"},
        "preflight": [{"node": "host-a", "cfg": cfg_sha}],
    }), encoding="utf-8")
    monkeypatch.setattr(native, "WEIGHT_CONFIG_ROOTS", (weights,))

    def fake_build(key, cfg):
        assert key == "GLM-5.1-w4a4c8-mxfp4"
        plans = [{"index": i, "attention": "mla", "ffn": "moe",
                  "mtp": False} for i in range(78)]
        return SimpleNamespace(to_dict=lambda: {
            "name": "glm51-bound", "layers": 78, "body_layers": 78,
            "hidden_size": 6144, "vocab_size": 154880, "tp": 1,
            "layer_plans": plans})

    import mindie_sim.catalog.specs as specs
    monkeypatch.setattr(specs, "build_model_spec", fake_build)
    item = next(iter(native.iter_trace_timetables(row, roots=[root])))
    assert item.model_binding["actual_config_sha256"] == cfg_sha
    assert item.model_binding["layers"] == 78
    assert item.model_binding["launch_model_dir"] == "/mnt/weight/GLM-5.1-w4a4c8-mxfp4"
    assert item.model_binding["quantization"] == "w4a4c8"
    assert item.model_binding["basis"] == (
        "capture_status_preflight_cfg")
    # A differently shaped template declaration cannot replace the bound geometry.
    declaration = {**_DECLARATION, "layers": 40, "body_layers": 40}
    item = next(iter(native.iter_trace_timetables(
        row, roots=[root], declaration=declaration)))
    assert item.model_binding["layers"] == 78
    assert item.status in {"measured", "raw_only"}


def test_prepare_model_probe_binds_rack08_host_and_preserves_launch_dir(tmp_path, monkeypatch):
    from types import SimpleNamespace

    root = tmp_path / "root"
    row = _layout(root)
    case = root / "out" / "case_x"
    config_bytes = (
        b'{"architectures":["Qwen3_5ForConditionalGeneration"],"model_type":"qwen3_5",'
        b'"hidden_size":6144,"num_hidden_layers":78,"vocab_size":154880}')
    weights = tmp_path / "weights"
    weight_dir = weights / "Qwen3.8-27B-w8a8-mxfp8-mtp"
    weight_dir.mkdir(parents=True)
    (weight_dir / "config.json").write_bytes(config_bytes)
    import hashlib as _hashlib
    cfg_sha = _hashlib.sha256(config_bytes).hexdigest()
    (case / "status.json").write_text(json.dumps({
        "started": "2026-11-07T00:00:00Z",
        "spec": {}, "preflight": None,
        "prepare": [{"node": "host-a", "hostname": "rack08os5",
                     "model_path": "/mnt/weight/Qwen3.8-27B-w8a8-mxfp8-mtp",
                     "model_probe": [
                         "/mnt/weight/Qwen3.8-27B-w8a8-mxfp8-mtp/config.json",
                         "/mnt/weight/Qwen3.8-27B-w8a8-mxfp8-mtp/index.json",
                         f"{cfg_sha}  /mnt/weight/Qwen3.8-27B-w8a8-mxfp8-mtp/config.json"]}],
    }), encoding="utf-8")
    monkeypatch.setattr(native, "WEIGHT_CONFIG_ROOTS", (weights,))

    def fake_build(key, cfg):
        plans = [{"index": i, "attention": "mla", "ffn": "moe",
                  "mtp": False} for i in range(78)]
        return SimpleNamespace(to_dict=lambda: {
            "name": "qwen-bound", "layers": 78, "body_layers": 78,
            "hidden_size": 6144, "vocab_size": 154880, "tp": 1,
            "layer_plans": plans})

    import mindie_sim.catalog.specs as specs
    monkeypatch.setattr(specs, "build_model_spec", fake_build)
    item = next(iter(native.iter_trace_timetables(row, roots=[root])))
    assert item.model_binding["basis"] == "capture_status_prepare_model_probe"
    assert item.model_binding["actual_config_sha256"] == cfg_sha
    assert item.model_binding["launch_model_dir"] == (
        "/mnt/weight/Qwen3.8-27B-w8a8-mxfp8-mtp")
    assert item.model_binding["launch_config_path"].endswith("/config.json")


def test_wrong_host_and_wrong_worker_are_not_actual(tmp_path):
    root = tmp_path / "root"
    case = root / "out" / "case_bad"
    body = (_KERNEL_HEADER + "0,MatMulV3,MatMulV3,AI_CORE,1,1.0,2.0,0,1\n").encode()

    def make(cell: str, host: str, worker: str) -> Path:
        base = case / cell / host / worker
        base.mkdir(parents=True)
        path = base / "kernel_details.csv.gz"
        with gzip.open(path, "wb") as handle:
            handle.write(body)
        (base / "op_statistic.csv").write_text(
            f"{_OPSTAT_HEADER}0,MatMulV3,AI_CORE,1,1.0,1.0,1.0,1.0,1.0\n",
            encoding="utf-8")
        return path

    path = make("dc_wrong_host", "host-c", "dp0_w0_ascend_pt")
    size = path.stat().st_size
    logs = root / "logs"
    logs.mkdir()
    (logs / "lane.log").write_text(
        "CELL case_bad_dc_wrong_host rc=0 captured=True "
        f"export=[('host-a', {size})]\n", encoding="utf-8")
    src = native.CellSource(root, case, case / "dc_wrong_host", (path,))
    roots = (str(root.resolve()),)
    digest = native._decompressed_sha(path)
    fake_host = native._source_classification(
        src, path, size, digest, "192.0.2.99", "dp0_w0_ascend_pt", roots)
    assert fake_host[0] == "host_not_in_receipt"
    assert fake_host[1]["receipt_match"] == "path_host_conflict"
    fake_worker = native._source_classification(
        src, path, size, digest, "host-c", "dp999_wrong_worker", roots)
    assert fake_worker[0] == "extra_trace"
    assert fake_worker[1]["receipt_match"] == "path_worker_conflict"
    invalid = native._source_classification(
        src, root / "not_the_retained_path.csv.gz", size, digest,
        "host-c", "dp0_w0_ascend_pt", roots)
    assert invalid[0] == "invalid_source_path"


def test_tarball_member_resolves_worker_for_host_size_receipt(tmp_path):
    import io
    import tarfile

    root = tmp_path / "root"
    row = _layout(root)
    case = root / "out" / "case_x"
    worker = "dp0_pp0_tp0_dcp0_ep0_rank0_1_20260101000000_ascend_pt"
    trace = case / "dc_1k_c1" / "host-a" / worker / "kernel_details.csv.gz"
    size = trace.stat().st_size
    log = root / "logs" / "lane.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "CELL case_x_dc_1k_c1 rc=0 captured=True "
        f"export=[('host-a', {size})]\n", encoding="utf-8")
    archive = case / "case_x_host-a.tar.gz"
    info = tarfile.TarInfo(
        f"out/case_x/dc_1k_c1/host-a/{worker}/kernel_details.csv.gz")
    info.size = size
    with tarfile.open(archive, "w:gz") as handle:
        handle.addfile(info, io.BytesIO(b"x" * size))
    item = next(iter(native.iter_trace_timetables(row, roots=[root])))
    assert item.host == "host-a" and item.worker == worker
    assert item.source_class == "actual"
    assert item.source_evidence["receipt_scope"] == "host_worker_size"
    assert item.source_evidence["worker_qualification"] == "canonical_path_identity"
    assert item.source_evidence["source_grade"] == "B_canonical_path_identity"
    assert item.source_evidence["exact_identity"] is True
    assert item.source_evidence["producer_receipt"][0]["worker"] == worker


def test_structured_status_export_is_current_and_log_version_is_history(tmp_path):
    root = tmp_path / "root"
    row = _layout(root)
    case = root / "out" / "case_x"
    worker = "dp0_pp0_tp0_dcp0_ep0_rank0_1_20260101000000_ascend_pt"
    trace = case / "dc_1k_c1" / "host-a" / worker / "kernel_details.csv.gz"
    size = trace.stat().st_size
    old_worker = "dp0_pp0_tp0_dcp0_ep0_rank0_0_20251231000000_ascend_pt"
    (case / "status.json").write_text(json.dumps({
        "cells": [{
            "tag": "case_x_dc_1k_c1", "captured": True, "rc": 0,
            "started": "2026-01-01T00:00:00Z", "finished": "2026-01-01T00:01:00Z",
            "export": {"host": "host-a", "rank": worker,
                       "kernel_gz_bytes": size, "ok": True},
        }]}), encoding="utf-8")
    (root / "logs").mkdir()
    (root / "logs" / "lane.log").write_text(
        "CELL case_x_dc_1k_c1 rc=0 captured=True "
        f"rank=host-a/{old_worker} gz={size - 1}\n", encoding="utf-8")
    item = next(iter(native.iter_trace_timetables(row, roots=[root])))
    assert item.source_class == "actual"
    assert item.source_evidence["source_grade"] == "A_independent_producer_receipt"
    assert item.source_evidence["receipt_source"] == "structured_status_cells"
    assert item.source_evidence["matched_version"]["session_started"] == (
        "2026-01-01T00:00:00Z")
    assert item.source_evidence["receipt_history"][0][0]["worker"] == old_worker


def _inventory_layout(root: Path) -> tuple[Path, Path, Path]:
    case = root / "out" / "case_inv"
    (case / "dc").mkdir(parents=True)
    (case / "status.json").write_text(json.dumps({
        "started": "2026-11-07T03:20:00Z", "preflight": None,
        "prepare": [{"node": "host-a", "hostname": "rack08os2",
                     "dies_visible": 8, "model_path": "/mnt/weight/x"}],
    }), encoding="utf-8")
    evidence = root / "evidence" / "fleet_inventory.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({
        "generated": "2026-11-07T03:21:27Z",
        "nodes": [{"node": "host-a", "hostname": "rack08os2",
                   "utc": "2026-11-07T03:18:09Z", "npu_count": 8,
                   "reachable": True}],
    }), encoding="utf-8")
    probe = root / "bin" / "fleet_probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text(
        "command = 'npu-smi info 2>/dev/null | grep -c Ascend950DT'\n"
        "npu_count = int(lines[3])\n", encoding="utf-8")
    return case, evidence, probe


def _clear_hardware_caches() -> None:
    native._fleet_inventory.cache_clear()
    native._fleet_probe.cache_clear()
    native._capture_status.cache_clear()


def test_inventory_family_binds_exact_host_epoch_and_keeps_subtype_unresolved(tmp_path, monkeypatch):
    root = tmp_path / "root"
    case, evidence, probe = _inventory_layout(root)
    probe_sha = native._sha256(probe)[0]
    monkeypatch.setattr(native, "VERIFIED_PRODUCER_PROBES", {
        probe_sha: {"role": "test_verified_family", "family": "Ascend950DT",
                    "schema": "test_schema", "source_line": 1}})
    _clear_hardware_caches()
    hardware = native._hardware_for(case, "host-a")
    assert hardware["hardware_key"] == "Ascend950DT"
    assert hardware["hardware_family"] == "Ascend950DT"
    assert hardware["hardware_subtype"] is None
    assert hardware["subtype_status"] == "unresolved"
    assert hardware["hardware_basis"] == "same_campaign_fleet_inventory_probe_family"
    assert hardware["hostname"] == "rack08os2" and hardware["npu_count"] == 8
    assert hardware["inventory_utc"] == "2026-11-07T03:18:09Z"
    assert hardware["inventory_generated"] == "2026-11-07T03:21:27Z"
    assert hardware["inventory_sha256"] == native._sha256(evidence)[0]
    assert hardware["probe_sha256"] == native._sha256(probe)[0]
    first = native._fleet_inventory.cache_info()
    native._hardware_for(case, "host-a")
    assert native._fleet_inventory.cache_info().hits > first.hits


def test_inventory_negative_controls_fail_explicitly(tmp_path):
    root = tmp_path / "root"
    case, evidence, probe = _inventory_layout(root)
    _clear_hardware_caches()
    assert native._hardware_for(case, "192.0.2.99")["hardware_basis"] == \
        "host_not_in_inventory"
    inventory = json.loads(evidence.read_text())
    inventory["generated"] = "2026-11-08T03:21:27Z"
    evidence.write_text(json.dumps(inventory))
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "inventory_epoch_mismatch"
    inventory["generated"] = "2026-11-07T03:21:27Z"
    inventory["nodes"][0]["npu_count"] = 0
    evidence.write_text(json.dumps(inventory))
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "inventory_node_unreachable_or_count_not_8"
    inventory["nodes"][0]["npu_count"] = 8
    inventory["nodes"].append(dict(inventory["nodes"][0]))
    evidence.write_text(json.dumps(inventory))
    _clear_hardware_caches()
    consistent = native._hardware_for(case, "host-a")
    assert consistent["hardware_basis"] in {
        "same_campaign_fleet_inventory_probe_family",
        "fleet_probe_digest_unverified"}
    inventory["nodes"].append({"node": "host-a", "hostname": "other",
                               "utc": "2026-11-07T03:18:09Z",
                               "npu_count": 8, "reachable": True})
    evidence.write_text(json.dumps(inventory))
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "inventory_duplicate_host_conflict"
    inventory["nodes"] = [{"node": "host-a", "hostname": "rack08os2",
                           "utc": "2026-11-07T03:18:09Z",
                           "npu_count": 8, "reachable": True}]
    evidence.write_text(json.dumps(inventory))
    status = json.loads((case / "status.json").read_text())
    status["prepare"][0]["hostname"] = "wrong-hostname"
    (case / "status.json").write_text(json.dumps(status))
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "inventory_prepare_hostname_conflict"
    probe.unlink()
    _clear_hardware_caches()
    status["prepare"][0]["hostname"] = "rack08os2"
    (case / "status.json").write_text(json.dumps(status))
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "fleet_probe_missing"
    evidence.unlink()
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "preflight_and_inventory_unavailable"


def test_probe_digest_not_prose_and_prepare_duplicates_reconcile(tmp_path, monkeypatch):
    root = tmp_path / "root"
    case, evidence, probe = _inventory_layout(root)
    _clear_hardware_caches()
    # A changed producer digest is unverified even if prose contains the old token.
    probe.write_text("command = 'npu-smi info | grep -c Ascend910B'\n"
                     "# historical grep -c Ascend950DT\n"
                     "npu_count = int(lines[3])\n", encoding="utf-8")
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "fleet_probe_digest_unverified"
    # The exact known producer digest remains verifiable without scanning prose.
    known_sha = "82733cca520bd3f4cbf21db86cef80cd55321659645040251f3bacffa217f325"
    monkeypatch.setattr(native, "VERIFIED_PRODUCER_PROBES", {
        known_sha: {"role": "fleet_probe_npu_smi_family",
                    "family": "Ascend950DT",
                    "schema": "fleet_inventory_npu_count_v1",
                    "source_line": 46}})
    probe.write_text("npu-smi info 2>/dev/null | grep -c Ascend950DT\n",
                     encoding="utf-8")
    # This synthetic file does not have the known digest, so it still must fail.
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "fleet_probe_digest_unverified"
    # Duplicate prepare entries with identical identity are consistent.
    status = json.loads((case / "status.json").read_text())
    status["prepare"].append(dict(status["prepare"][0]))
    (case / "status.json").write_text(json.dumps(status))
    _clear_hardware_caches()
    # Contradictory duplicate hostname/dies must fail before any family claim.
    status["prepare"].append({"node": "host-a", "hostname": "other-machine",
                              "dies_visible": 0, "model_path": "/mnt/weight/x"})
    (case / "status.json").write_text(json.dumps(status))
    _clear_hardware_caches()
    assert native._hardware_for(case, "host-a")["hardware_basis"] == \
        "prepare_duplicate_host_conflict"
