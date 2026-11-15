"""Focused native/tensor recovery tests for ``modeling_inputs``.

These tests guard the first acceptance-input slice: a C7 hotspot or native call
is recovered at the operator/tensor level that is actually present, and is not
expanded into a guessed model or service case.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_PACKAGE = "_a5_source_bind_modeling_inputs"


def _load_modeling_inputs():
    """Load the module without importing the whole profiler package.

    The acceptance input path is a standalone module (no sim/provider import);
    keeping the test at that boundary also avoids unrelated concurrent edits to
    the package CLI surface.
    """
    package = types.ModuleType(_PACKAGE)
    package.__path__ = [str(ROOT / "mindie_profiler")]
    sys.modules[_PACKAGE] = package
    spec = importlib.util.spec_from_file_location(
        f"{_PACKAGE}.modeling_inputs", ROOT / "mindie_profiler" / "modeling_inputs.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mi = _load_modeling_inputs()


def _c7(*rows: dict) -> dict:
    return {
        "schema_version": "mindie-profile-summary/1",
        "hotspot_grouping": "variant",
        "top_hotspot_kernels": list(rows),
    }


def test_c7_hotspots_recover_ordered_slots_without_guessing_model_or_service() -> None:
    report = _c7(
        {
            "kernel_name": "aclnnInplaceFillScalar_FillAiCore_Fill",
            "input_shapes": '"1;"',
            "input_dtypes": "INT64;INT32",
            "input_formats": "ND;ND",
            "measured_device_ms_p50": 0.00162,
            "call_count": 1,
            "rank_id": "rank_0",
            "semantic_block": "Unclassified",
        }
    )
    bundle = mi.extract_modeling_inputs(report)
    assert bundle.metadata["source_kind"] == "c7_summary"
    assert bundle.metadata["source_schema"] == "mindie-profile-summary/1"
    assert bundle.metadata["native_scope"] == "operator_and_tensor_only"
    assert bundle.metadata["model_or_service_inferred"] is False
    observation = bundle.observations[0]
    assert observation.name == "aclnnInplaceFillScalar_FillAiCore_Fill"
    assert observation.native_operator is None
    assert observation.native_operator_source is None
    assert observation.native_identity_status == "missing_operator_type"
    assert observation.duration_ns == 1620
    assert observation.count == 1
    assert dict(observation.annotations)["duration_basis"] == "measured_device_ms_p50"
    # Two input slots are preserved; the first legacy shape is not invented
    # by taking the first slot.
    assert observation.shape is None
    assert [slot.shape for slot in observation.inputs] == [(1,), ()]
    assert [slot.dtype for slot in observation.inputs] == ["INT64", "INT32"]
    assert [slot.layout for slot in observation.inputs] == ["ND", "ND"]
    assert [slot.state for slot in observation.inputs] == ["descriptor", "scalar"]
    assert observation.native_abi is None
    assert dict(observation.annotations)["native_identity_gap"] == "missing_operator_type"
    payload = observation.as_dict()
    assert payload["native"]["display_name"] == "aclnnInplaceFillScalar_FillAiCore_Fill"
    assert payload["native"]["operator"] is None
    assert payload["native"]["identity_status"] == "missing_operator_type"
    assert "model" not in payload and "service" not in payload
    assert "model_case" not in json.dumps(payload)


def test_real_c7_does_not_promote_csv_name_to_native_type() -> None:
    try:
        from mindie_profiler import analyze_profile
    except ImportError:
        pytest.skip("profiler package import unavailable")
    csv_path = ROOT / "tests" / "fixtures" / "profiler_core" / "real_a3_wait_pmu" / "kernel_details.csv"
    if not csv_path.is_file():
        pytest.skip("retained real CSV unavailable")
    import csv as csv_module

    with csv_path.open(newline="") as stream:
        rows = list(csv_module.DictReader(stream))
    types = {row["Name"]: row["Type"] for row in rows}
    report = analyze_profile(csv_path.parent, full_range=True)
    observations = {item.name: item for item in mi.extract_modeling_inputs(report)}
    assert types["aclnnInplaceCopy_CastAiCore_Cast"] == "Cast"
    assert types["aclnnInplaceFillScalar_FillAiCore_Fill"] == "Fill"
    for name, source_type in (
        ("aclnnInplaceCopy_CastAiCore_Cast", "Cast"),
        ("aclnnInplaceFillScalar_FillAiCore_Fill", "Fill"),
    ):
        observation = observations[name]
        # The C7 hotspot contract carries Name but not Type; the display name is
        # never promoted to a typed native operator.
        assert observation.name == name
        assert source_type in {"Cast", "Fill"}
        assert observation.native_operator is None
        assert observation.native_identity_status == "missing_operator_type"
    fill = observations["aclnnInplaceFillScalar_FillAiCore_Fill"]
    assert fill.duration_ns == 1620
    assert [slot.shape for slot in fill.inputs] == [(1,), ()]


def test_c7_unavailable_tensor_metadata_stays_unknown_not_a_placeholder_shape() -> None:
    report = _c7(
        {
            "kernel_name": "AivKernel",
            "input_shapes": "N/A",
            "input_dtypes": "N/A",
            "input_formats": "N/A",
            "measured_device_ms_p50": 0.01,
            "call_count": 3,
            "rank_id": "rank_0",
            "semantic_block": "Comm",
        }
    )
    observation = mi.extract_modeling_inputs(report).observations[0]
    assert observation.shape is None and observation.dtype is None and observation.layout is None
    assert observation.inputs == ()
    assert observation.native_operator is None
    assert observation.native_identity_status == "missing_operator_type"
    assert observation.native_abi is None


def test_c7_single_scalar_shape_keeps_the_legacy_view() -> None:
    report = _c7(
        {
            "kernel_name": "aclnnInplaceCopy_CastAiCore_Cast",
            "input_shapes": '"1"',
            "input_dtypes": "INT64",
            "input_formats": "ND",
            "measured_device_ms_p50": 0.00156,
            "call_count": 1,
        }
    )
    observation = mi.extract_modeling_inputs(report).observations[0]
    assert observation.shape == (1,)
    assert observation.dtype == "int64"
    assert observation.layout == "ND"
    assert len(observation.inputs) == 1
    assert observation.inputs[0].state == "descriptor"
    assert observation.native_operator is None


def test_c7_display_name_and_typed_source_are_separate() -> None:
    report = _c7(
        {
            "kernel_name": "aclnnInplaceCopy_CastAiCore_Cast",
            "op_type": "Cast",
            "input_shapes": '"1"',
            "input_dtypes": "INT64",
            "input_formats": "ND",
            "output_shapes": '"1"',
            "output_dtypes": "INT64",
            "output_formats": "ND",
            "measured_device_ms_p50": 0.00156,
            "call_count": 1,
        }
    )
    observation = mi.extract_modeling_inputs(report).observations[0]
    assert observation.name == "aclnnInplaceCopy_CastAiCore_Cast"
    assert observation.native_operator == "Cast"
    assert observation.native_operator_source == "op_type"
    assert observation.native_identity_status == "typed"
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "complete"
    native = observation.as_dict()["native"]
    assert native["display_name"] == "aclnnInplaceCopy_CastAiCore_Cast"
    assert native["operator"] == "Cast"
    assert native["operator_source"] == "op_type"


def test_empty_shape_without_dtype_layout_is_incomplete_not_explicit_undefined() -> None:
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": "gap",
            "native_operator": "Op",
            "inputs": [{"shape": []}],
            "outputs": [{"shape": [1], "dtype": "bf16", "format": "ND"}],
        }
    )
    slot = observation.inputs[0]
    assert slot.state == "incomplete"
    assert slot.shape_present is True
    assert slot.dtype_present is False and slot.layout_present is False
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "incomplete"
    assert observation.native_abi["digest"] is None
    reasons = {item.get("reason") for item in observation.native_abi["issues"]}
    assert {"missing_dtype", "missing_layout"} <= reasons


def test_typed_empty_shape_is_a_scalar_not_undefined() -> None:
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": "scalar",
            "native_operator": "Op",
            "inputs": [{"shape": [], "dtype": "bf16", "format": "ND"}],
            "outputs": [{"shape": [1], "dtype": "bf16", "format": "ND"}],
        }
    )
    slot = observation.inputs[0]
    assert slot.state == "scalar"
    assert slot.dtype == "bf16" and slot.layout == "ND"
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "complete"
    assert observation.native_abi["verified"] is True
    assert observation.native_abi["digest"].startswith("sha256:")


def test_explicit_undefined_requires_present_dtype_and_layout_fields() -> None:
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": "undef",
            "native_operator": "Op",
            "inputs": [{"shape": [], "dtype": None, "format": None}],
            "outputs": [{"shape": [1], "dtype": "bf16", "format": "ND"}],
        }
    )
    slot = observation.inputs[0]
    assert slot.state == "explicit_undefined"
    assert slot.dtype_present is True and slot.layout_present is True
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "complete"
    assert observation.native_abi["digest"].startswith("sha256:")


def test_preset_digest_without_slots_is_not_verified() -> None:
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": "Op",
            "native_operator": "Op",
            "native_abi": {
                "schema": "mindie-native-tensor-abi/1",
                "status": "complete",
                "native_operator": "Op",
                "inputs": None,
                "outputs": None,
                "digest": "sha256:" + "a" * 64,
                "verified": True,
            },
        }
    )
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "conflict"
    assert observation.native_abi["verified"] is False
    assert observation.native_abi["digest"] is None
    assert any(
        item.get("reason") == "declared_digest_not_verified"
        for item in observation.native_abi["issues"]
    )


def test_missing_slot_presence_survives_json_roundtrip_and_type_upgrade(tmp_path: Path) -> None:
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": "gap",
            "inputs": [{"shape": []}],
            "outputs": [{"shape": [1], "dtype": "bf16", "format": "ND"}],
        }
    )
    assert observation.inputs[0].state == "incomplete"
    assert observation.native_abi is None
    bundle = mi.ModelingInputsBundle([observation])
    target = mi.write_modeling_inputs_bundle(bundle, tmp_path / "gap.json")
    payload = json.loads(target.read_text(encoding="utf-8"))
    slot = payload["observations"][0]["native"]["inputs"][0]
    assert slot["dtype"] is None and slot["layout"] is None
    assert slot["dtype_present"] is False and slot["layout_present"] is False
    round_trip = mi.extract_modeling_inputs(target)
    assert round_trip.observations[0].inputs[0].state == "incomplete"
    assert round_trip.observations[0].inputs[0].dtype_present is False
    # Adding a source-backed Type later must not fabricate the two missing
    # descriptor fields or a complete digest.
    payload["observations"][0]["native"]["operator"] = "LaterType"
    target.write_text(json.dumps(payload), encoding="utf-8")
    upgraded = mi.extract_modeling_inputs(target).observations[0]
    assert upgraded.native_operator == "LaterType"
    assert upgraded.inputs[0].state == "incomplete"
    assert upgraded.native_abi is not None
    assert upgraded.native_abi["status"] == "incomplete"
    assert upgraded.native_abi["digest"] is None
    assert {"missing_dtype", "missing_layout"} <= {
        item.get("reason") for item in upgraded.native_abi["issues"]
    }


def test_na_whole_fields_are_missing_not_explicit_undefined() -> None:
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": "na_gap",
            "native_operator": "Op",
            "input_shapes": "[]",
            "input_dtypes": "N/A",
            "input_formats": "N/A",
            "output_shapes": "[1]",
            "output_dtypes": "DT_BF16",
            "output_formats": "ND",
        }
    )
    slot = observation.inputs[0]
    assert slot.shape == () and slot.state == "incomplete"
    assert slot.dtype_present is False and slot.layout_present is False
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "incomplete"
    assert observation.native_abi["digest"] is None


def test_preset_abi_conflict_is_preserved_not_trusted() -> None:
    base = mi.OperatorObservation.from_mapping(
        {
            "name": "Op",
            "native_operator": "Op",
            "inputs": [{"shape": [384, 5120], "dtype": "bf16", "format": "ND"}],
            "outputs": [{"shape": [384, 5120], "dtype": "bf16", "format": "ND"}],
        }
    )
    assert base.native_abi is not None and base.native_abi["status"] == "complete"
    original_digest = base.native_abi["digest"]
    payload = base.as_dict()
    payload["native"]["inputs"][0]["shape"] = [384, 5121]
    conflicted = mi.OperatorObservation.from_mapping(payload)
    assert conflicted.native_abi is not None
    assert conflicted.native_abi["status"] == "conflict"
    assert conflicted.native_abi["verified"] is False
    assert conflicted.native_abi["digest"] is None
    assert conflicted.native_abi["provided"]["digest"] == original_digest
    assert any(
        item.get("reason") in {"abi_content_conflict", "declared_digest_mismatch"}
        for item in conflicted.native_abi["issues"]
    )
    operator_payload = base.as_dict()
    operator_payload["native"]["operator"] = "DifferentOp"
    operator_conflict = mi.OperatorObservation.from_mapping(operator_payload)
    assert operator_conflict.native_abi is not None
    assert operator_conflict.native_abi["status"] == "conflict"
    assert operator_conflict.native_abi["verified"] is False
    assert operator_conflict.native_abi["digest"] is None
    assert any(
        item.get("reason") in {"abi_content_conflict", "declared_digest_mismatch"}
        for item in operator_conflict.native_abi["issues"]
    )


def test_native_call_record_preserves_undefined_and_typed_slots() -> None:
    record = {
        "case_id": "qwen36-a5-tp2-c96",
        "cohort_id": "sha256:abc",
        "native_operator_type": "CausalConv1d",
        "raw_operator": {
            "type": "CausalConv1d",
            "name": "CausalConv1d",
            "device_id": "0",
            "stream_id": "6886",
            "task_id": "314531",
        },
        "raw_abi": {
            "input_shapes": "384,5120;4,5120;;2188,6,5120",
            "input_dtypes": "DT_BF16;DT_BF16;DT_UNDEFINED;DT_BF16",
            "input_formats": "ND;ND;NULL;ND",
            "output_shapes": "384,5120",
            "output_dtypes": "DT_BF16",
            "output_formats": "ND",
            "inputs": [
                {"shape": [384, 5120], "dtype": "bf16", "format": "ND"},
                {"shape": [4, 5120], "dtype": "bf16", "format": "ND"},
                {"shape": [], "dtype": None, "format": None},
                {"shape": [2188, 6, 5120], "dtype": "bf16", "format": "ND"},
            ],
            "outputs": [{"shape": [384, 5120], "dtype": "bf16", "format": "ND"}],
        },
    }
    bundle = mi.extract_modeling_inputs(record)
    observation = bundle.observations[0]
    assert bundle.metadata["source_kind"] == "native_observation"
    assert observation.name == "CausalConv1d"
    assert observation.native_operator == "CausalConv1d"
    assert len(observation.inputs) == 4 and len(observation.outputs) == 1
    assert observation.inputs[2].state == "explicit_undefined"
    assert observation.inputs[2].shape == () and observation.inputs[2].dtype is None
    assert observation.inputs[3].shape == (2188, 6, 5120)
    assert observation.shape is None  # four input slots are never collapsed to one
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "complete"
    assert observation.native_abi["digest"].startswith("sha256:")
    annotations = dict(observation.annotations)
    assert annotations["case_id"] == "qwen36-a5-tp2-c96"
    assert annotations["kernel_name"] == "CausalConv1d"
    assert observation.device_id == "0" and observation.stream_id == "6886"


def test_unknown_shape_is_not_silently_turned_into_a_scalar() -> None:
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": "typed_gap",
            "native_operator": "TypedGap",
            "input_shapes": [None, []],
            "input_dtypes": ["DT_BF16", "DT_UNDEFINED"],
            "input_formats": ["ND", "NULL"],
            "output_shapes": "4,8",
            "output_dtypes": "DT_BF16",
            "output_formats": "ND",
        }
    )
    assert [slot.state for slot in observation.inputs] == ["unknown", "explicit_undefined"]
    assert observation.inputs[0].shape is None
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "incomplete"
    assert observation.native_abi["digest"] is None
    assert {"slot": "inputs[0]", "reason": "unknown_tensor_dimensions"} in observation.native_abi["issues"]


def test_c7_report_file_path_is_read(tmp_path: Path) -> None:
    report = _c7(
        {
            "kernel_name": "aclnnFlashAttention",
            "input_shapes": "4,8",
            "input_dtypes": "DT_BF16",
            "input_formats": "ND",
            "measured_device_ms_p50": 0.01,
            "call_count": 2,
        }
    )
    path = tmp_path / "c7.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    bundle = mi.extract_modeling_inputs(path)
    assert bundle.source == str(path)
    assert bundle.metadata["source_kind"] == "c7_summary"
    assert len(bundle) == 1
    assert bundle.observations[0].shape == (4, 8)
    assert bundle.observations[0].duration_ns == 10_000


def test_bundle_round_trip_preserves_native_slots_and_abi(tmp_path: Path) -> None:
    bundle = mi.extract_modeling_inputs(
        {
            "raw_operator": {"type": "CausalConv1d", "name": "CausalConv1d"},
            "raw_abi": {
                "input_shapes": "384,5120;4,5120",
                "input_dtypes": "DT_BF16;DT_BF16",
                "input_formats": "ND;ND",
                "output_shapes": "384,5120",
                "output_dtypes": "DT_BF16",
                "output_formats": "ND",
            },
            "clock": {"duration_us": 2.5, "domain": "clock:test:us"},
            "step_state": {"op_state": "static"},
        }
    )
    target = mi.write_modeling_inputs_bundle(bundle, tmp_path / "modeling-inputs.json")
    round_trip = mi.extract_modeling_inputs(target)
    assert len(round_trip) == 1
    before, after = bundle.observations[0], round_trip.observations[0]
    assert after.native_operator == before.native_operator
    assert [slot.as_dict() for slot in after.inputs] == [slot.as_dict() for slot in before.inputs]
    assert after.native_abi == before.native_abi
    assert after.context == before.context
    assert after.duration_ns == 2_500 and before.duration_ns == 2_500
    assert dict(after.annotations)["duration_basis"] == "clock.duration_us"
    assert after.count == 1


def test_mapping_without_operator_or_tensor_identity_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty name"):
        mi.extract_modeling_inputs({"scope": "a prose-only report"})


_T03_NATIVE_FIRST_CALL = Path(
    os.environ.get(
        "MINDIE_T03_NATIVE_FIRST_CALL",
        "/Volumes/data/Codex/2026-11-12/kan-x/work/a5-implementation/jobs/"
        "A5-T03/out/native/native_first_call.json",
    )
)


@pytest.mark.skipif(not _T03_NATIVE_FIRST_CALL.is_file(), reason="T03 native handoff artifact unavailable")
def test_consumes_t03_real_native_first_call_handoff() -> None:
    bundle = mi.extract_modeling_inputs(_T03_NATIVE_FIRST_CALL)
    assert bundle.metadata["source_kind"] == "native_observation"
    observation = bundle.observations[0]
    assert observation.native_operator == "CausalConv1d"
    assert len(observation.inputs) == 12 and len(observation.outputs) == 1
    assert observation.inputs[2].state == "explicit_undefined"
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "complete"
    assert observation.native_abi["verified"] is True
    assert observation.native_abi["digest"].startswith("sha256:f06df4f7")
    assert observation.inputs[0].dtype == "bf16"
    # The native record's own clock-domain duration is recovered rather than
    # invented; the clock/window/state context stays attached.
    assert observation.duration_ns == 36_496
    assert dict(observation.annotations)["duration_basis"] == "clock.duration_us"
    assert observation.context is not None
    assert observation.context["clock"]["domain"].startswith("clock:")
    assert observation.context["step_state"]["op_state"] == "static"
    assert observation.context["ambiguities"]


@pytest.mark.skipif(not _T03_NATIVE_FIRST_CALL.is_file(), reason="T03 native handoff artifact unavailable")
def test_t03_real_bundle_roundtrip_keeps_shared_abi(tmp_path: Path) -> None:
    bundle = mi.extract_modeling_inputs(_T03_NATIVE_FIRST_CALL)
    target = mi.write_modeling_inputs_bundle(bundle, tmp_path / "t03.json")
    round_trip = mi.extract_modeling_inputs(target).observations[0]
    original = bundle.observations[0]
    assert round_trip.native_operator == "CausalConv1d"
    assert [slot.as_dict() for slot in round_trip.inputs] == [slot.as_dict() for slot in original.inputs]
    assert round_trip.inputs[2].state == "explicit_undefined"
    assert round_trip.native_abi is not None
    assert round_trip.native_abi["status"] == "complete"
    assert round_trip.native_abi["verified"] is True
    assert round_trip.native_abi["digest"].startswith("sha256:f06df4f7")


_T02_QUALIFIED_ABI = Path(
    os.environ.get(
        "MINDIE_T02_QUALIFIED_ABI",
        "/Volumes/data/Codex/2026-11-12/kan-x/work/a5-implementation/jobs/"
        "A5-T02/input/evidence/qualified_a5_abi.json",
    )
)


@pytest.mark.skipif(not _T02_QUALIFIED_ABI.is_file(), reason="T02 qualified ABI handoff artifact unavailable")
def test_consumes_t02_qualified_abi_collection_handoff() -> None:
    bundle = mi.extract_modeling_inputs(_T02_QUALIFIED_ABI)
    assert bundle.metadata["source_kind"] == "native_observation_collection"
    assert bundle.observations
    observation = bundle.observations[0]
    assert observation.native_operator == "FusedInferAttentionScore"
    assert len(observation.inputs) == 31 and len(observation.outputs) == 2
    assert observation.context is not None
    assert observation.context["hardware"] == "Ascend950DT_9582"
    assert observation.context["entry_key"] == "qwen36_tp4_h6/attention_prefill_D256"
    assert observation.context["model_label"] == "qwen36_tp4_h6"
    assert observation.context["source"]["sha256"] == (
        "22c6475d69d0871c91e3f64576f6b3b46755d8f389606cea7425e560a9ac4863"
    )
    assert observation.inputs[3].state == "explicit_undefined"


def _blank_t03_slot(record: dict, index: int = 2) -> dict:
    item = json.loads(json.dumps(record))
    raw = item["raw_abi"]
    raw["inputs"][index]["dtype"] = ""
    raw["inputs"][index]["format"] = ""
    raw["input_dtypes"] = ";".join(
        "" if pos == index else str(value)
        for pos, value in enumerate(raw["input_dtypes"].split(";"))
    )
    raw["input_formats"] = ";".join(
        "" if pos == index else str(value)
        for pos, value in enumerate(raw["input_formats"].split(";"))
    )
    return item


def _roundtrip_twice(observation, tmp_path: Path, name: str):
    bundle = mi.ModelingInputsBundle([observation])
    target = tmp_path / name
    for _ in range(2):
        mi.write_modeling_inputs_bundle(bundle, target)
        bundle = mi.extract_modeling_inputs(target)
    return bundle.observations[0]


@pytest.mark.skipif(not _T03_NATIVE_FIRST_CALL.is_file(), reason="T03 native handoff artifact unavailable")
def test_t03_blank_slot_mapping_roundtrip_keeps_gap(tmp_path: Path) -> None:
    record = _blank_t03_slot(json.loads(_T03_NATIVE_FIRST_CALL.read_text(encoding="utf-8")))
    observation = mi.OperatorObservation.from_mapping(record)
    assert len(observation.inputs) == 12 and len(observation.outputs) == 1
    assert observation.duration_ns == 36_496
    slot = observation.inputs[2]
    assert slot.state == "incomplete"
    assert slot.dtype == "" and slot.layout == ""
    assert slot.dtype_present is True and slot.layout_present is True
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "incomplete"
    assert observation.native_abi["verified"] is False
    assert observation.native_abi["digest"] is None
    after = _roundtrip_twice(observation, tmp_path, "t03-blank-mapping.json")
    assert len(after.inputs) == 12 and len(after.outputs) == 1
    assert after.duration_ns == 36_496
    assert after.inputs[2].state == "incomplete"
    assert after.inputs[2].dtype == "" and after.inputs[2].layout == ""
    assert after.inputs[2].dtype_present is True and after.inputs[2].layout_present is True
    assert after.native_abi is not None
    assert after.native_abi["status"] == "incomplete"
    assert after.native_abi["verified"] is False
    assert after.native_abi["digest"] is None


@pytest.mark.skipif(not _T03_NATIVE_FIRST_CALL.is_file(), reason="T03 native handoff artifact unavailable")
def test_t03_blank_slot_positional_roundtrip_keeps_gap(tmp_path: Path) -> None:
    item = _blank_t03_slot(json.loads(_T03_NATIVE_FIRST_CALL.read_text(encoding="utf-8")))
    raw = item["raw_abi"]
    positional = {
        "case_id": item.get("case_id"),
        "native_operator_type": item.get("native_operator_type"),
        "raw_operator": item.get("raw_operator"),
        "clock": item.get("clock"),
        "raw_abi": {
            key: raw[key] for key in
            ("input_shapes", "input_dtypes", "input_formats",
             "output_shapes", "output_dtypes", "output_formats")
        },
    }
    observation = mi.OperatorObservation.from_mapping(positional)
    assert len(observation.inputs) == 12 and len(observation.outputs) == 1
    assert observation.duration_ns == 36_496
    assert observation.inputs[2].state == "incomplete"
    assert observation.inputs[2].dtype == "" and observation.inputs[2].layout == ""
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "incomplete"
    assert observation.native_abi["verified"] is False
    assert observation.native_abi["digest"] is None
    after = _roundtrip_twice(observation, tmp_path, "t03-blank-positional.json")
    assert len(after.inputs) == 12 and len(after.outputs) == 1
    assert after.duration_ns == 36_496
    assert after.inputs[2].state == "incomplete"
    assert after.inputs[2].dtype == "" and after.inputs[2].layout == ""
    assert after.native_abi is not None
    assert after.native_abi["status"] == "incomplete"
    assert after.native_abi["verified"] is False
    assert after.native_abi["digest"] is None


_T16_REQUESTS = Path(
    os.environ.get(
        "MINDIE_T16_REQUESTS",
        "/Volumes/data/Codex/2026-11-12/kan-x/work/a5-implementation/jobs/"
        "A5-T16/example_requests.json",
    )
)


def test_whole_slot_absent_is_preserved_and_differs_from_undefined(tmp_path: Path) -> None:
    from mindie_profiler.native_tensor_abi import native_abi_from_slots
    absent = mi.OperatorObservation.from_mapping(
        {
            "name": "Op", "native_operator": "Op",
            "inputs": [{"present": False, "shape": [], "dtype": None, "layout": None}],
            "outputs": [{"shape": [1], "dtype": "bf16", "layout": "ND"}],
        }
    )
    undefined = mi.OperatorObservation.from_mapping(
        {
            "name": "Op", "native_operator": "Op",
            "inputs": [{"present": True, "shape": [], "dtype": None, "layout": None}],
            "outputs": [{"shape": [1], "dtype": "bf16", "layout": "ND"}],
        }
    )
    assert absent.inputs[0].present is False
    assert absent.inputs[0].state == "absent"
    assert absent.as_dict()["native"]["inputs"][0]["present"] is False
    assert absent.native_abi is not None and undefined.native_abi is not None
    direct = native_abi_from_slots(
        "Op", [{"present": False}],
        [{"shape": [1], "dtype": "bf16", "layout": "ND"}],
    )
    assert absent.native_abi["digest"] == direct["digest"]
    assert absent.native_abi["digest"] != undefined.native_abi["digest"]
    after = _roundtrip_twice(absent, tmp_path, "whole-slot-absent.json")
    assert after.inputs[0].present is False
    assert after.inputs[0].state == "absent"
    assert after.native_abi == absent.native_abi
    canonical = mi.OperatorObservation.from_mapping(
        {"name": "Op", "native_operator": "Op", "native_abi": direct}
    )
    assert canonical.inputs[0].present is False
    assert canonical.inputs[0].state == "absent"
    assert canonical.native_abi == direct


@pytest.mark.skipif(not _T03_NATIVE_FIRST_CALL.is_file(), reason="T03 native handoff artifact unavailable")
def test_t03_whole_slot_absent_roundtrip_preserves_positions(tmp_path: Path) -> None:
    record = json.loads(_T03_NATIVE_FIRST_CALL.read_text(encoding="utf-8"))
    record["raw_abi"]["inputs"][2] = {
        "present": False, "shape": [], "dtype": None, "format": None,
    }
    observation = mi.OperatorObservation.from_mapping(record)
    assert len(observation.inputs) == 12 and len(observation.outputs) == 1
    assert observation.duration_ns == 36_496
    assert observation.inputs[2].present is False
    assert observation.inputs[2].state == "absent"
    after = _roundtrip_twice(observation, tmp_path, "t03-whole-absent.json")
    assert len(after.inputs) == 12 and len(after.outputs) == 1
    assert after.duration_ns == 36_496
    assert after.inputs[2].present is False
    assert after.inputs[2].state == "absent"
    assert after.native_abi == observation.native_abi


@pytest.mark.skipif(not _T16_REQUESTS.is_file(), reason="T16 native request handoff unavailable")
def test_t16_qbmm_real_abi_matches_shared_projection(tmp_path: Path) -> None:
    request = json.loads(_T16_REQUESTS.read_text(encoding="utf-8"))["requests"][0]
    abi = request["abi"]
    observation = mi.OperatorObservation.from_mapping(
        {
            "name": abi["native_operator"],
            "native_operator": abi["native_operator"],
            "inputs": abi["inputs"],
            "outputs": abi["outputs"],
            "native_abi": abi,
        }
    )
    assert observation.native_abi is not None
    assert observation.native_abi["status"] == "complete"
    assert observation.native_abi["verified"] is True
    assert observation.native_abi["digest"] == (
        "sha256:5af74a1166c21f2ab82c7ec1854449dae3cfafa144aecebec10a47a6c36e1866"
    )
    changed = json.loads(json.dumps(abi))
    changed["inputs"][0]["shape"][0] += 1
    conflicted = mi.OperatorObservation.from_mapping(
        {
            "name": changed["native_operator"],
            "native_operator": changed["native_operator"],
            "inputs": changed["inputs"],
            "outputs": changed["outputs"],
            "native_abi": abi,
        }
    )
    assert conflicted.native_abi is not None
    assert conflicted.native_abi["status"] == "conflict"
    assert conflicted.native_abi["verified"] is False
    assert conflicted.native_abi["digest"] is None
    assert conflicted.native_abi["provided"]["digest"] == abi["digest"]
    assert any(
        item.get("reason") in {"abi_content_conflict", "declared_digest_mismatch"}
        for item in conflicted.native_abi["issues"]
    )
    bundle = mi.ModelingInputsBundle([observation])
    target = mi.write_modeling_inputs_bundle(bundle, tmp_path / "qbmm.json")
    round_trip = mi.extract_modeling_inputs(target).observations[0]
    assert round_trip.native_abi is not None
    assert round_trip.native_abi["verified"] is True
    assert round_trip.native_abi["digest"] == (
        "sha256:5af74a1166c21f2ab82c7ec1854449dae3cfafa144aecebec10a47a6c36e1866"
    )


_T02_SELECTED_ROW = Path(
    os.environ.get(
        "MINDIE_T02_SELECTED_ROW",
        "/Volumes/data/Codex/2026-11-12/kan-x/work/a5-implementation/jobs/"
        "A5-T02/input/evidence/native_qbmm_row120.json",
    )
)


@pytest.mark.skipif(not _T02_SELECTED_ROW.is_file(), reason="T02 selected-row handoff artifact unavailable")
def test_consumes_t02_selected_row_without_operator_type() -> None:
    bundle = mi.extract_modeling_inputs(_T02_SELECTED_ROW)
    assert bundle.metadata["source_kind"] == "native_selected_row"
    observation = bundle.observations[0]
    assert observation.name == "kernel_row:120"
    assert observation.native_operator is None
    assert observation.native_identity_status == "missing_operator_type"
    assert observation.native_abi is None
    assert len(observation.inputs) == 4 and len(observation.outputs) == 1
    assert observation.duration_ns == 17_883
    assert dict(observation.annotations)["duration_basis"] == "duration_us"
    assert observation.stream_id == "7085"
    assert observation.task_id == "594704"
    annotations = dict(observation.annotations)
    assert annotations["csv_line"] == "120"
    assert annotations["source_csv_sha256"] == (
        "7e0e459dec657f249ebbf82da9a7ceccf904aa3eff2e161cd8e312d1b04e6d2d"
    )
    assert annotations["source_csv_path"].endswith("kernel_details.csv")
    assert observation.context is not None
    assert observation.context["source_csv"]["sha256"] == annotations["source_csv_sha256"]
    assert observation.context["source_window"]["profile_window_s"] == pytest.approx(1.8065)
    payload = observation.as_dict()
    assert "model" not in payload and "service" not in payload
