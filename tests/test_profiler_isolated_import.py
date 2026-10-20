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
