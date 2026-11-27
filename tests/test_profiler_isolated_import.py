"""Isolated-import and modeling-inputs bundle contract tests.

[Role]
  Prove that ``mindie_profiler``, its CLI shim, and ``modeling_inputs`` import
  under ``python -I`` without ``mindie_sim``, and pin bundle extraction/writes.

[Invariants]
  * The subprocess path contains only this repository; no site package or
    ``mindie_sim`` import is allowed to satisfy the import.
  * Extracted observations preserve names, shapes, dtypes and durations.

[Timeouts & Locks]
  Subprocess imports use a 10s timeout; no locks or sleeps.

[Side-Effect Policy]
  The subprocess only imports/prints.  Bundle writes target pytest ``tmp_path``.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from mindie_profiler import modeling_inputs as mi

REPO_ROOT = Path(__file__).resolve().parents[1]


def _isolated(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_isolated_python_import_of_package_cli_and_modeling_inputs():
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(REPO_ROOT)!r}); "
        "import mindie_profiler; "
        "import mindie_profiler.modeling_inputs as m; "
        "from mindie_profiler.cli import main; "
        "assert 'mindie_sim' not in sys.modules; "
        "assert m.SCHEMA_VERSION == 'mindie-modeling-inputs/1'; "
        "assert callable(main); "
        "print('ISOLATED_IMPORT_OK')"
    )
    proc = _isolated(code)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ISOLATED_IMPORT_OK"


def test_operator_family_classification_is_deterministic():
    assert mi.classify_operator_family("aclnnMatMul") == "matmul"
    assert mi.classify_operator_family("aclnnGroupedMatmul") == "matmul"
    assert mi.classify_operator_family("aclnnAdd") == "elementwise"
    assert mi.classify_operator_family("aclnnRmsNorm") == "rmsnorm"
    assert mi.classify_operator_family("HcomAllReduce") == "communication"
    assert mi.classify_operator_family("vendor::unknown_kernel") == "unknown"
    assert set(mi.OPERATOR_FAMILIES) >= {"matmul", "rmsnorm", "elementwise", "copy"}


def test_extract_and_write_modeling_inputs_bundle(tmp_path):
    source = [
        {"name": "aclnnMatMul", "input_shapes": '"2,4,8"', "input_dtypes": "DT_BF16",
         "input_formats": "ND", "duration_ns": 120, "rank": 0, "device_id": 0},
        {"operator_name": "aclnnRelu", "shape": [2, 4, 8], "dtype": "float16", "duration": 30},
    ]
    bundle = mi.extract_modeling_inputs(source)

    assert isinstance(bundle, mi.ModelingInputsBundle)
    assert bundle.schema_version == mi.SCHEMA_VERSION
    assert len(bundle) == 2
    assert bundle.observations[0].family == "matmul"
    assert bundle.observations[0].shape == (2, 4, 8)
    assert bundle.observations[0].dtype == "bfloat16"
    assert bundle.observations[0].duration_ns == 120
    assert bundle.observations[1].family == "elementwise"

    target = mi.write_modeling_inputs_bundle(bundle, tmp_path / "modeling-inputs.json")
    payload = json.loads(Path(target).read_text(encoding="utf-8"))
    assert payload["schema_version"] == mi.SCHEMA_VERSION
    assert payload["observation_count"] == 2
    assert [item["family"] for item in payload["observations"]] == ["matmul", "elementwise"]

    round_trip = mi.extract_modeling_inputs(tmp_path / "modeling-inputs.json")
    assert len(round_trip) == 2
    assert round_trip.observations[0].name == "aclnnMatMul"


def test_profiler_standalone_zero_mindie_sim_dependency_firewall():
    import ast
    import tomllib
    from mindie_profiler import body_moe_contracts

    assert callable(body_moe_contracts.moe_fusion_contract)
    assert callable(body_moe_contracts.moe_fusion_scope)

    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = list(pyproject.get("project", {}).get("dependencies", []))
    assert not any("mindie-sim" in d or "mindie_sim" in d for d in deps), deps

    forbidden_prefixes = (
        "mindie_sim.prediction",
        "mindie_sim.schema",
        "mindie_sim.backends",
        "mindie_sim.observed_contracts",
        "mindie_sim.subgraph_math",
        "mindie_sim.compose.inputs",
    )
    violations: list[str] = []
    for py_path in sorted((REPO_ROOT / "mindie_profiler").rglob("*.py")):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name == p or alias.name.startswith(p + ".") for p in forbidden_prefixes):
                        violations.append(f"{py_path.relative_to(REPO_ROOT)}:{node.lineno}:{alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module == p or node.module.startswith(p + ".") for p in forbidden_prefixes):
                    violations.append(f"{py_path.relative_to(REPO_ROOT)}:{node.lineno}:{node.module}")
    assert violations == [], f"Private mindie_sim imports forbidden: {violations}"

    code = (
        "import sys\n"
        "class _BlockSim:\n"
        "    def find_spec(self, fullname, path, target=None):\n"
        "        if fullname == 'mindie_sim' or fullname.startswith('mindie_sim.'):\n"
        "            raise ModuleNotFoundError(f'blocked:{fullname}', name=fullname)\n"
        "        return None\n"
        "sys.meta_path.insert(0, _BlockSim())\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
        "from mindie_profiler import hardware_presets, observed_contracts, native_abi_model\n"
        "from mindie_profiler.sim_modeling_provider import MindieSimModelingProvider\n"
        "from mindie_profiler.sim_structure_ingress import subgraph_efficiency_summary\n"
        "from mindie_profiler.cli_advisor import doctor_report\n"
        "import mindie_profiler.bench\n"
        "a5 = hardware_presets.resolve_hardware_preset('a5', dtype='fp8_e4m3')\n"
        "assert a5.peak_flops_per_s > 0 and a5.memory_bandwidth_bytes_per_s > 0\n"
        "peaks = hardware_presets.resolve_hardware_peaks('Ascend910_9362')\n"
        "assert peaks['hbm_peak_bytes_per_s'] == 1.6e12\n"
        "assert callable(observed_contracts.observed_contract)\n"
        "assert MindieSimModelingProvider().available() is True\n"
        "plan, err = native_abi_model.build_plan({\n"
        "    'api': {'namespace': 'aclnn', 'entry': 'aclnnMatmul'},\n"
        "    'tensors': {\n"
        "        'x1': {'shape': [2, 4], 'dtype': 'bf16', 'layout': 'ND', 'role': 'input'},\n"
        "        'x2': {'shape': [4, 8], 'dtype': 'bf16', 'layout': 'ND', 'role': 'weight'},\n"
        "        'out': {'shape': [2, 8], 'dtype': 'bf16', 'layout': 'ND', 'role': 'output'},\n"
        "    },\n"
        "})\n"
        "assert err is None and plan is not None and plan.ops[0].flops == 128.0\n"
        "summary = subgraph_efficiency_summary({'subgraphs': []}, {'windows': []})\n"
        "assert summary['schema'] == 'mindie-profiler-subgraph-efficiency/1'\n"
        "doc = doctor_report()\n"
        "assert isinstance(doc, dict) and doc['status'] == 'ok'\n"
        "assert doc['mindie_sim_bridge']['installed'] is False and doc['mindie_sim_bridge']['optional'] is True\n"
        "assert 'mindie_sim' not in sys.modules\n"
        "print('STANDALONE_FIREWALL_OK')\n"
    )
    proc = _isolated(code)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "STANDALONE_FIREWALL_OK"

