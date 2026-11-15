"""Unit tests for standalone native-primitive workload integration boundaries."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
_STRUCTURE = ROOT / "examples" / "structure"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(_STRUCTURE) not in sys.path:
    sys.path.insert(0, str(_STRUCTURE))

from fleet_primitive_workloads import (  # noqa: E402
    SUITE,
    declared_primitive_workload,
    is_primitive_workload,
    predict_primitive_workload,
    primitive_native_observation,
    primitive_workload_descriptor,
)


def _plain_row() -> dict:
    return {
        "suite": "a5_multinode_full_coverage_20261108",
        "capture_id": "a5_multinode_20261108:case:cell",
        "observed_ms": 1.0,
        "geometry": {"structural_weights": [0.1, 0.2, 0.3, 0.4, 0.4, 0.5]},
    }


def test_non_primitive_rows_return_none_and_do_not_price() -> None:
    assert is_primitive_workload(_plain_row()) is False
    assert predict_primitive_workload(_plain_row()) is None
    assert primitive_workload_descriptor(_plain_row()) is None
    assert declared_primitive_workload(_plain_row()) is None
    assert primitive_native_observation(_plain_row()) is None


def test_primitive_suite_row_without_descriptor_returns_explicit_unsupported() -> None:
    row = {
        "suite": SUITE,
        "capture_id": f"{SUITE}:missing_descriptor_probe",
        "hardware_tier": "A5",
        "phase": "decode",
        "observed_ms": 99.0,
    }
    assert is_primitive_workload(row) is True
    result = predict_primitive_workload(row)
    assert result is not None
    assert result.get("predicted_step_ms") is None
    assert str(result.get("status", "")).startswith("unsupported") or result.get("status") in {
        "insufficient_evidence", "model_rejected",
    }
