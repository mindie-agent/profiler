"""Contract regressions for MCP schemas, CLI exit codes, SQL guards, and timeouts.

[Role]
  Verifies public request/response contracts across MCP descriptors, reproducer
  raw-row binding and seed forwarding, fabric script emission exit codes, SQLite
  function authorization and string-ID metadata, cross-field configuration
  validation, and caller-owned ``TimeoutError`` propagation.

[Invariants]
  * Every published MCP ``inputSchema`` matches executable parameters with
    ``additionalProperties=False`` and stays within the 250-token budget.
  * Every broad ``Exception`` / ``OSError`` catch in ``mindie_profiler`` is
    immediately preceded by a bare ``TimeoutError`` re-raise, while socket
    timeout reconciliation in ``collect`` remains intact.
  * ``open_readonly`` / ``run_sql`` block denied SQLite functions before
    execution and report complete resolved column names.

[Timeouts & Locks]
  Tier 0/1 local tests (< 10 s total); subprocesses use explicit short timeouts.

[Side-Effect Policy]
  Writes only under ``tmp_path`` with isolated environment directories.
"""

from __future__ import annotations

import ast
import ctypes
import http.client
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
from unittest.mock import patch

import pytest

from mindie_profiler import (
    aclgraph_mcp,
    cann_abi,
    collect,
    fabric_probe,
    inventory,
    kernel_inventory,
    native_capture,
    native_capture_shm,
    op_api_registry,
    profiler_configs,
    public,
    repro_mcp,
    repro_op,
)
analyze_mod = importlib.import_module("mindie_profiler.analyze")
from mindie_profiler.events import ProfilerQueryError, ProfilerUsageError
from mindie_profiler.sql import _authorizer, open_readonly, run_sql
from temp_workspaces import make_temp_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = REPO_ROOT / "mindie_profiler"


def _compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _paged_attention_raw_row() -> dict[str, object]:
    return {
        "op_type": "aclnnPagedAttention",
        "cann_version": "8.0",
        "input_shapes": ["[16,8,128]", "[256,16,8,128]", "[256,16,8,128]", "[16,16]", "[16]"],
        "input_names": ["query", "key_cache", "value_cache", "block_table", "context_lens"],
        "input_dtypes": ["BF16", "BF16", "BF16", "INT32", "INT32"],
        "input_formats": ["ND"] * 5,
        "output_shapes": ["[16,8,128]"],
        "output_names": ["out"],
        "output_dtypes": ["BF16"],
        "output_formats": ["ND"],
        "attrs": {"num_kv_heads": 8, "num_heads": 8, "scale_value": 0.088, "kv_len": 2048},
    }


def test_aclgraph_and_all_mcp_descriptors_publish_exact_bounded_input_schemas() -> None:
    all_groups = (
        aclgraph_mcp.TOOL_SPECS,
        op_api_registry.MCP_TOOL_SPECS,
        repro_mcp.MCP_TOOL_SPECS,
    )
    try:
        import tiktoken

        encoders = [tiktoken.get_encoding("cl100k_base"), tiktoken.get_encoding("o200k_base")]
    except (ImportError, OSError):
        encoders = []
    for specs in all_groups:
        for spec in specs:
            assert "inputSchema" in spec and "input" not in spec
            schema = spec["inputSchema"]
            assert schema["type"] == "object"
            assert schema["additionalProperties"] is False
            serialized = _compact(spec)
            for enc in encoders:
                assert len(enc.encode(serialized, disallowed_special=())) <= 250

    for spec in aclgraph_mcp.TOOL_SPECS:
        fn = getattr(aclgraph_mcp, spec["name"])
        assert set(spec["inputSchema"]["properties"]) == set(inspect.signature(fn).parameters)

    valid_calls = [
        (
            "aclgraph_diagnose",
            {
                "region": {
                    "name": "r0",
                    "branch_a": {"op": "a", "stream_id": 0, "start_us": 0, "end_us": 10},
                    "branch_b": {"op": "b", "stream_id": 1, "start_us": 5, "end_us": 15},
                }
            },
        ),
        ("aclgraph_sq_budget", {"captured_batch_sizes": 4, "subgraphs_per_step": 8, "active_streams_per_graph": 4}),
        ("aclgraph_superkernel", {"static_decode": True, "capturable_ops": True, "dynamic_tiling_host_sync": False}),
        ("aclgraph_launch_floor", {"mode": "full", "superkernel": True}),
    ]
    for tool_name, payload in valid_calls:
        out = aclgraph_mcp.call_tool(tool_name, payload)
        assert out["ok"] == 1
        assert len(_compact(out).encode("utf-8")) <= 250

    bad = aclgraph_mcp.call_tool("aclgraph_launch_floor", {"mode": "full", "unexpected_kw": 1})
    assert bad["ok"] == 0 and bad["err"] == "EARGS"


def test_repro_mcp_binds_raw_occurrence_and_forwards_seed_and_cann_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    short_dir = str(make_temp_workspace("mpc_", base="/tmp"))
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", short_dir)
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    raw = _paged_attention_raw_row()
    out_dir = tmp_path / "repro"
    try:
        res_a = repro_mcp.call_mcp_tool(
            "repro_op",
            {"occurrence": raw, "cann_version": "8.0", "seed": 123, "output_dir": str(out_dir)},
        )
        res_b = repro_mcp.call_mcp_tool(
            "repro_op",
            {"occurrence": raw, "cann_version": "8.0", "seed": 456, "output_dir": str(out_dir)},
        )
        assert res_a["status"] == "ready" and res_b["status"] == "ready"
        assert res_a["artifact_id"] != res_b["artifact_id"]

        script_path = Path(res_a["artifact_path"])
        compile(script_path.read_text(encoding="utf-8"), str(script_path), "exec")
        cp = subprocess.run(
            [sys.executable, "-B", str(script_path), "--dry-run"],
            text=True,
            capture_output=True,
            timeout=15,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        dry = json.loads(cp.stdout)
        assert dry["status"] == "dry_run"
        assert dry["seed"] == 123

        intercepted: list[dict[str, object]] = []

        def _stub(bound_occ: dict[str, object], **kwargs: object) -> dict[str, object]:
            intercepted.append({"occurrence": bound_occ, "kwargs": kwargs})
            raise ProfilerUsageError("intercepted")

        with patch.object(repro_op, "generate_single_op_reproducer", side_effect=_stub):
            blocked = repro_mcp.call_mcp_tool(
                "repro_op",
                {"occurrence": {"op_type": "aclnnPagedAttention"}, "seed": 123, "cann_version": "9.0"},
            )
        assert blocked["status"] == "blocked"
        assert len(intercepted) == 1
        forwarded_occ = intercepted[0]["occurrence"]
        forwarded_kw = intercepted[0]["kwargs"]
        assert isinstance(forwarded_occ, dict) and forwarded_occ["cann_version"] == "9.0"
        assert isinstance(forwarded_kw, dict) and forwarded_kw["seed"] == 123 and forwarded_kw["cann_version"] == "9.0"
    finally:
        shutil.rmtree(short_dir, ignore_errors=True)


def test_fabric_probe_script_emission_reports_ok_and_exits_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script_out = tmp_path / "fabric_probe.py"
    plan_out = tmp_path / "fabric_plan.json"
    rc = fabric_probe.main(
        [
            "--world-size",
            "2",
            "--ranks-per-node",
            "2",
            "--duration-s",
            "20",
            "--plan",
            str(plan_out),
            "--script",
            str(script_out),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["status"] == "ok"
    assert payload["syntax_ok"] is True
    compile(script_out.read_text(encoding="utf-8"), str(script_out), "exec")


def test_sql_authorizer_blocks_denied_functions_and_preserves_resolved_column_names(tmp_path: Path) -> None:
    db = tmp_path / "profile.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE STRING_IDS (id INTEGER, value TEXT)")
    con.execute("INSERT INTO STRING_IDS VALUES (1, 'operator')")
    con.commit()
    con.close()

    resolved = run_sql(db, "SELECT 1 AS name")
    assert resolved["string_ids"]["resolved_columns"] == ["name_resolved"]
    assert list(resolved["rows"][0]) == ["name", "name_resolved"]
    assert resolved["rows"][0]["name_resolved"] == "operator"

    with pytest.raises(ProfilerQueryError):
        run_sql(db, "SELECT sqlite_compileoption_used('THREADSAFE') AS compiled")

    ro = open_readonly(db)
    invocations: list[tuple[object, ...]] = []
    ro.create_function("writefile", 2, lambda *args: invocations.append(args) or 1)
    ro.set_authorizer(_authorizer)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            ro.execute("SELECT writefile('never-created', 'payload')").fetchone()
    finally:
        ro.close()
    assert invocations == []


def test_profiler_configs_reject_inverted_cross_field_ranges_and_percentages() -> None:
    invalid_cases = [
        (profiler_configs.StructuralInferenceConfig, {"min_layer_candidates": 121, "max_layer_candidates": 20}),
        (profiler_configs.StructuralInferenceConfig, {"candidate_step_upper_bound": 600, "max_candidate_steps": 512}),
        (profiler_configs.FusionRuleConfig, {"default_savings_ratio": 0.9, "min_savings_ratio": 0.4, "max_savings_ratio": 0.8}),
        (profiler_configs.FusionRuleConfig, {"default_savings_ratio": 0.1, "min_savings_ratio": 0.4, "max_savings_ratio": 0.8}),
        (profiler_configs.ACLGraphLaunchConfig, {"overlap_serial_pct": 101.0}),
        (profiler_configs.CorrelationConfig, {"min_query_timeout_us": 500_000, "query_timeout_us": 100_000}),
        (profiler_configs.AdvisorConfig, {"cast_storm_share_ratio": 0.5, "cast_high_severity_ratio": 0.2}),
    ]
    for cls, kwargs in invalid_cases:
        with pytest.raises(ValueError):
            cls(**kwargs)


def test_caller_timeout_identity_propagates_across_boundaries_and_all_broad_handlers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = TimeoutError("caller_deadline_identity")

    csv_file = tmp_path / "timeout.csv"
    csv_file.write_text("name\nvalue\n", encoding="utf-8")
    with patch.object(inventory, "probe_csv", side_effect=sentinel):
        with pytest.raises(TimeoutError) as exc_info:
            inventory._csv_file_fact(csv_file)
        assert exc_info.value is sentinel

    with patch.object(public, "compare_profiles", side_effect=sentinel), patch.object(public, "_json_object", return_value={}):
        with pytest.raises(TimeoutError) as exc_info:
            public.main(["compare", "--baseline", "a", "--candidate", "b"])
        assert exc_info.value is sentinel

    status_dir = tmp_path / "cap"
    status_dir.mkdir()
    (status_dir / "status.json").write_text("{}", encoding="utf-8")
    with patch.object(Path, "read_text", side_effect=sentinel):
        with pytest.raises(TimeoutError) as exc_info:
            analyze_mod._capture_deployment_image(status_dir)
        assert exc_info.value is sentinel

    with patch.object(http.client.HTTPConnection, "connect", side_effect=sentinel):
        with pytest.raises(TimeoutError) as exc_info:
            collect.post_profile_action(
                "http://127.0.0.1:9999",
                "start_profile",
                execution_id="exec-0",
                timeout=1.0,
            )
        assert exc_info.value is sentinel

    with (
        patch.object(http.client.HTTPConnection, "connect", return_value=None),
        patch.object(http.client.HTTPConnection, "request", return_value=None),
        patch.object(http.client.HTTPConnection, "getresponse", side_effect=socket.timeout("timed out")),
    ):
        reconciled = collect.post_profile_action(
            "http://127.0.0.1:9999",
            "start_profile",
            execution_id="exec-0",
            timeout=1.0,
        )
    assert reconciled["error"]["code"] == "request_timeout"
    assert reconciled["external_effect"] == "unknown"

    shm_session = native_capture_shm.CaptureShmSession(tmp_path / "t0.shm", create=True, unlink_on_close=False)
    try:
        with patch.object(Path, "unlink", side_effect=sentinel):
            with pytest.raises(TimeoutError) as exc_info:
                shm_session.close(unlink=True)
            assert exc_info.value is sentinel
    finally:
        shm_session.path.unlink(missing_ok=True)

    monkeypatch.setenv("MINDIE_CAPTURE_SHM_PATH", str(tmp_path / "dummy.shm"))
    monkeypatch.setattr(native_capture_shm, "_STEP_FN_RESOLVED", False)
    monkeypatch.setattr(native_capture_shm, "_STEP_FN", None)
    with patch.object(ctypes, "CDLL", side_effect=sentinel):
        with pytest.raises(TimeoutError) as exc_info:
            native_capture_shm.mark_capture_step()
        assert exc_info.value is sentinel

    class _FakeProc:
        pid = 999999

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            raise sentinel

        def wait(self, timeout: float | None = None) -> int:
            return 0

    if os.name == "nt":
        with pytest.raises(TimeoutError) as exc_info:
            native_capture._terminate_process_group(_FakeProc(), None, grace_s=0.5)  # type: ignore[arg-type]
        assert exc_info.value is sentinel
    else:
        with patch("os.getpgid", return_value=999999), patch("os.killpg", side_effect=sentinel):
            with pytest.raises(TimeoutError) as exc_info:
                native_capture._terminate_process_group(_FakeProc(), os.getpgid(999999), grace_s=0.5)  # type: ignore[arg-type]
            assert exc_info.value is sentinel

    inv_db = tmp_path / "kernels.sqlite"
    con = kernel_inventory._connect(inv_db)
    try:
        with patch.object(kernel_inventory, "csv_rows", side_effect=sentinel):
            with pytest.raises(TimeoutError) as exc_info:
                kernel_inventory.ingest_source(con, csv_file, "", io.StringIO("name\n"), {}, timeout_s=5.0)
            assert exc_info.value is sentinel
        status_row = con.execute("SELECT status FROM sources").fetchone()
        assert status_row is not None and status_row[0] == "failed"
    finally:
        con.close()

    def _caught_names(node: ast.expr | None) -> set[str]:
        if isinstance(node, ast.Name):
            return {node.id}
        if isinstance(node, ast.Attribute):
            return {node.attr}
        if isinstance(node, ast.Tuple):
            return set().union(*(_caught_names(item) for item in node.elts))
        return set()

    for py_path in sorted(PKG_ROOT.rglob("*.py")):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                continue
            for idx, handler in enumerate(node.handlers):
                if not _caught_names(handler.type).intersection({"Exception", "OSError"}):
                    continue
                assert idx > 0, f"{py_path.name}:{handler.lineno} unguarded broad handler"
                prev = node.handlers[idx - 1]
                assert _caught_names(prev.type) == {"TimeoutError"}, f"{py_path.name}:{handler.lineno} missing adjacent TimeoutError guard"
                assert any(isinstance(stmt, ast.Raise) and stmt.exc is None for stmt in prev.body)
