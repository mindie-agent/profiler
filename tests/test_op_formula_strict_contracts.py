"""Strict validation, lossless aggregation and provable token-bound contracts.

[Role]
  Prove F11 (pre-coercion scalar validation, structured CLI failures, strict JSON
  containers), F12 (lossless full-batch aggregation with prioritized samples and
  intact protocol identifiers) and F13 (a provably conservative BPE upper bound
  on the complete MCP envelope).

[Invariants]
  * Booleans, fractional floats, NaN, infinities and strings are rejected for
    every integer/float parameter before any coercion.
  * Malformed JSON/CSV containers exit 2 with zero Python tracebacks.
  * A 120-row batch reports ``total_rows=120`` and ``violation_count=112``.
  * Protocol enum/schema strings are never truncated.
  * The complete MCP envelope satisfies every real tokenizer bound available
    offline; at minimum the project's own upper bound is <= 250.

[Timeouts & Locks]
  Pure in-memory work plus a few short CLI subprocesses.

[Side-Effect Policy]
  Temporary files only through ``tmp_path``.
"""

from __future__ import annotations

import json
import random
import string
import subprocess
import sys
from pathlib import Path

import pytest

from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.op_formula_annotator import (
    MCP_TOOL_SPECS, call_mcp_tool, load_rows,
)
from mindie_profiler.token_budget import (
    bounded_envelope, estimate_tokens, upper_bound_text, upper_bound_tokens,
)
from mindie_sim.op_formulas import FormulaValidationError, evaluate_operator
from mindie_sim.op_formulas.primitives import (
    strict_bool, strict_finite_float, strict_int, strict_int_list, strict_tol,
)

ROOT = Path(__file__).resolve().parents[1]


def _clean_rows(count: int, measured: float = 31.645) -> list[dict]:
    return [{"operator": "matmul",
             "params": {"M": 32, "N": 896, "K": 7168},
             "measured_us": measured} for _ in range(count)]


def test_strict_scalar_validators_reject_before_coercion():
    for bad in (True, False, 1.75, "12", [1], {"a": 1}, None):
        with pytest.raises(FormulaValidationError):
            strict_int(bad, "value")
    assert strict_int(3, "value") == 3
    with pytest.raises(FormulaValidationError):
        strict_int(0, "value", minimum=1)
    with pytest.raises(FormulaValidationError):
        strict_bool(1, "flag")
    assert strict_bool(True, "flag") is True
    for bad in (True, float("nan"), float("inf"), float("-inf"), "1.0", complex(1)):
        with pytest.raises(FormulaValidationError):
            strict_finite_float(bad, "value")
    assert strict_finite_float(1, "value") == 1.0
    for bad in (-0.01, 1.0, float("nan"), True):
        with pytest.raises(FormulaValidationError):
            strict_tol(bad)
    assert strict_tol(0.0) == 0.0
    with pytest.raises(FormulaValidationError):
        strict_int_list([1, 2.5], "values")
    with pytest.raises(FormulaValidationError):
        strict_int_list([1, True], "values")


@pytest.mark.parametrize("field,value", [
    ("M", True), ("M", 1.75), ("M", "32"), ("N", float("nan")),
    ("K", float("inf")), ("M", None),
])
def test_operator_parameters_reject_invalid_scalars(field, value):
    params = {"M": 32, "N": 896, "K": 7168}
    params[field] = value
    with pytest.raises(FormulaValidationError):
        evaluate_operator("matmul", params)


@pytest.mark.parametrize("operator,params", [
    ("flash_attention", {"q_len": 1, "kv_len": 8, "hq": True, "hkv": 1,
                         "head_dim": 8}),
    ("rms_norm", {"rows": 2, "hidden": 8, "gamma": 1}),
    ("moe_gating_topk_softmax", {"tokens": 2, "experts": 8, "hidden": 8,
                                 "topk": True}),
    ("moe_distribute_dispatch", {"tokens": 2, "hidden": 8, "experts_total": 8,
                                 "experts_local": 1, "topk": 2, "ep": 1.5}),
    ("hccl_all_reduce", {"size_bytes": 8, "world_size": True}),
    ("embedding", {"tokens": 2, "hidden": 8, "vocab": 16, "tp": 1.5}),
])
def test_boolean_and_fractional_parameters_are_rejected(operator, params):
    with pytest.raises(FormulaValidationError):
        evaluate_operator(operator, params)


def test_measured_and_tolerance_validation():
    for bad in (float("nan"), float("inf"), -1.0, True):
        with pytest.raises(FormulaValidationError):
            evaluate_operator("matmul", {"M": 2, "N": 2, "K": 2},
                              measured_us=bad)
    for bad in (float("nan"), 1.0, -0.5):
        receipt = call_mcp_tool("evaluate_op_formula",
                                {"operator": "matmul",
                                 "params": {"M": 2, "N": 2, "K": 2},
                                 "tol": bad})
        assert receipt["status"] in {"invalid_request", "unmodeled"}
    bad_measured = call_mcp_tool(
        "evaluate_op_formula", {"operator": "matmul",
                                "params": {"M": 2, "N": 2, "K": 2},
                                "measured_us": float("nan")})
    assert bad_measured["status"] in {"invalid_request", "unmodeled"}
    assert "NaN" not in json.dumps(bad_measured, allow_nan=False)


def test_cli_rejects_malformed_arguments_with_exit_two(tmp_path, capsys):
    from mindie_profiler.__main__ import main as cli_main

    def run(*args: str, subproc: bool = False):
        if subproc:
            res = subprocess.run(
                [sys.executable, "-m", "mindie_profiler", "op-formula", *args],
                cwd=ROOT, capture_output=True, text=True, timeout=60)
            return res.returncode, res.stdout, res.stderr
        rc = cli_main(["op-formula", *args])
        io = capsys.readouterr()
        return rc, io.out, io.err

    base = ["--operator", "matmul", "--params", '{"M":2,"N":2,"K":2}']
    for idx, extra in enumerate((["--measured-us", "nan"], ["--measured-us", "-1"],
                                 ["--tol", "nan"])):
        rc, out, err = run(*base, *extra, subproc=(idx == 0))
        assert rc == 2, (extra, out, err)
        assert "Traceback" not in err
    for bad_params in ("[]", "123"):
        rc, _, err = run("--operator", "matmul", "--params", bad_params)
        assert rc == 2
        assert "Traceback" not in err
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps({"garbage": 1}), encoding="utf-8")
    assert run("--rows", str(rows))[0] == 2
    rows.write_text(json.dumps([{"name": "x"}, [1, 2]]), encoding="utf-8")
    assert run("--rows", str(rows))[0] == 2
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert run("--rows", str(broken))[0] == 2


def test_strict_json_profile_containers(tmp_path):
    for key in ("rows", "ops", "kernels", "events", "records"):
        path = tmp_path / f"{key}.json"
        path.write_text(json.dumps({key: _clean_rows(1)}), encoding="utf-8")
        assert len(load_rows(path)) == 1
    for payload in ({"garbage": 1}, [1, 2], {"rows": [1]}, {"rows": "x"}):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ProfilerUsageError):
            load_rows(path)
    single = tmp_path / "single.json"
    single.write_text(json.dumps(_clean_rows(1)[0]), encoding="utf-8")
    with pytest.raises(ProfilerUsageError):
        load_rows(single)


def test_csv_container_rejects_extra_columns_and_bad_encoding(tmp_path):
    good = tmp_path / "good.csv"
    good.write_text("Name,Duration(us)\nmatmul,12.5\n", encoding="utf-8")
    assert len(load_rows(good)) == 1
    extra = tmp_path / "extra.csv"
    extra.write_text("Name,Duration(us)\nmatmul,12.5,oops\n", encoding="utf-8")
    with pytest.raises(ProfilerUsageError):
        load_rows(extra)
    missing = tmp_path / "missing.csv"
    missing.write_text("Name\nmatmul\n", encoding="utf-8")
    with pytest.raises(ProfilerUsageError):
        load_rows(missing)
    quoted = tmp_path / "quoted.csv"
    quoted.write_text('Name,Duration(us),Note\nmatmul,12.5,"line1\nline2"\n',
                      encoding="utf-8")
    assert len(load_rows(quoted)) == 1


def test_full_batch_aggregation_is_lossless_and_prioritizes_violations():
    rows = _clean_rows(8) + [{"operator": "matmul",
                              "params": {"M": 1024, "N": 1024, "K": 1024},
                              "measured_us": 0.01} for _ in range(112)]
    envelope = call_mcp_tool("annotate_profile_formulas",
                             {"rows": rows, "launch_mode": "python_eager"})
    assert envelope["total_rows"] == 120
    assert envelope["modeled_rows"] == 120
    assert envelope["violation_count"] == 112
    assert envelope["status"] == "violations_detected"
    assert "async_overlap_shadowed" in envelope["root_cause_codes"]
    assert envelope["schema"] == "mindie-op-formula-mcp/1"
    assert envelope["sample_rows_returned"] >= 1
    assert envelope["sample_rows"][0]["status"] == "bound_violation"
    assert envelope["rows_omitted"] == 120 - envelope["sample_rows_returned"]
    serialized = json.dumps(envelope, separators=(",", ":"), sort_keys=True)
    assert upper_bound_tokens(envelope) <= 250
    assert envelope["receipt"]["token_estimate"] <= 250
    assert envelope["receipt"]["within_budget"] is True
    assert estimate_tokens(envelope) <= 250


def test_partial_violation_batch_keeps_honest_status():
    rows = _clean_rows(3) + [
        {"operator": "matmul",
         "params": {"M": 1024, "N": 1024, "K": 1024},
         "measured_us": 0.01}]
    envelope = call_mcp_tool("annotate_profile_formulas",
                             {"rows": rows, "launch_mode": "python_eager"})
    assert envelope["total_rows"] == 4
    assert envelope["violation_count"] == 1
    assert envelope["status"] == "violations_detected"
    assert envelope["rows_omitted"] == 3
    assert envelope["sample_rows"][0]["measured_us"] == 0.01


def test_protocol_identifiers_are_never_truncated():
    for status in ("violations_detected", "invalid_input"):
        payload = {"schema": "mindie-op-formula-mcp/1", "status": status,
                   "reason": "async_overlap_shadowed"}
        envelope = bounded_envelope(payload, limit=250)
        assert envelope["schema"] == "mindie-op-formula-mcp/1"
        assert envelope["status"] == status
        assert envelope["reason"] == "async_overlap_shadowed"


def test_giant_and_random_operator_names_stay_within_budget():
    names = ["matmul_" + "Z" * 20000, "RmsNorm_" + "q" * 4000,
             "aclnn" + "".join(random.Random(7).choice(
                 string.ascii_letters + string.digits) for _ in range(500))]
    for name in names:
        receipt = call_mcp_tool(
            "evaluate_op_formula",
            {"operator": name, "params": {"M": 32, "N": 1024, "K": 1024},
             "measured_us": 0.01})
        serialized = json.dumps(receipt, separators=(",", ":"), sort_keys=True)
        assert len(serialized) <= 900
        assert upper_bound_tokens(receipt) <= 250
        assert receipt["receipt"]["within_budget"] is True
        if "canonical_op" in receipt:
            assert len(receipt["canonical_op"]) <= 24
        else:
            assert receipt["status"] in {"unmodeled", "invalid_request"}
        assert "ZZZZ" not in serialized and "qqqq" not in serialized


def test_upper_bound_is_conservative_on_adversarial_strings():
    for text in ("Z" * 20000, "q" * 4096, "7" * 1024,
                 "".join(random.Random(3).choice(string.printable)
                         for _ in range(2000)),
                 "violations_detected", "unfiltered_padding_shape_bound"):
        assert upper_bound_text(text) >= 1
        assert upper_bound_text(text) <= len(text.encode("utf-8")) + 8
    try:
        import tiktoken  # type: ignore
    except ImportError:
        pytest.skip("tiktoken is not installed offline")
    encodings = []
    for name in ("o200k_base", "cl100k_base"):
        try:
            encodings.append(tiktoken.get_encoding(name))
        except TimeoutError:
            raise
        except Exception:  # pragma: no cover - offline cache miss
            pytest.skip("tokenizer vocabulary is not available offline")
    cases = ["Z" * 20000, "matmul_" + "Z" * 20000, "q" * 4096, "7" * 1024]
    rng = random.Random(11)
    for _ in range(300):
        length = rng.randint(1, 160)
        alphabet = rng.choice([string.ascii_lowercase, string.ascii_uppercase,
                               string.digits, string.ascii_letters + string.digits,
                               string.printable])
        cases.append("".join(rng.choice(alphabet) for _ in range(length)))
    for case in cases:
        bound = upper_bound_text(case)
        for encoder in encodings:
            assert bound >= len(encoder.encode(case)), case[:40]
    envelope = call_mcp_tool("annotate_profile_formulas",
                             {"rows": _clean_rows(4),
                              "launch_mode": "python_eager"})
    text = json.dumps(envelope, separators=(",", ":"), sort_keys=True)
    for encoder in encodings:
        assert len(encoder.encode(text)) <= 250


def test_mcp_tool_specs_remain_two():
    assert len(MCP_TOOL_SPECS) == 2
    names = {item["name"] for item in MCP_TOOL_SPECS}
    assert names == {"evaluate_op_formula", "annotate_profile_formulas"}


def test_formula_test_discovery_is_covered_by_scoped_hygiene():
    import ast
    tree = ast.parse((ROOT / "tests/test_op_formulas_r4_closure.py").read_text())
    scoped = next(ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "SCOPED"
                          for t in node.targets))
    discovered = {str(p.relative_to(ROOT))
                  for p in (ROOT / "tests").glob("test_op_formula*.py")}
    assert discovered <= set(scoped), discovered - set(scoped)


def test_r5_10_catalog_sequence_and_fixture_timeouts_propagate():
    import importlib.util
    from unittest.mock import patch
    import mindie_profiler.op_abi_slots as slots
    import mindie_profiler.op_abi_geometry_common as common
    with patch('mindie_profiler.op_api_registry.catalog_entry', side_effect=TimeoutError('catalog')):
        with pytest.raises(TimeoutError):
            slots._resolve_entry('aclnnRmsNorm')
    with patch.object(common, 'decode_sequence_lengths', side_effect=TimeoutError('sequence')):
        with pytest.raises(TimeoutError):
            common._lengths([2], encoding='lengths', total=2, expected=1, label='test')
    spec = importlib.util.spec_from_file_location('r5_builder', ROOT / 'tests/fixtures/build_a5_op_goldens.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    from contextlib import ExitStack
    with ExitStack() as stack:
        if not builder.CAPTURE_DIR.exists():
            stack.enter_context(
                patch.object(builder, 'load_rows', return_value=[{'Name': 'Matmul', 'Duration(us)': '10.0'}])
            )
        stack.enter_context(patch.object(builder, 'infer_request', side_effect=TimeoutError('fixture')))
        with pytest.raises(TimeoutError):
            builder._kernel_points()
