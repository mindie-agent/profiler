"""Standalone native-primitive workloads priced by the public SIM composition.

[Role]
  Map an explicitly declared standalone device workload (operation, tensor
  shapes/head grouping, dtype and timed repeat count) onto the same public
  ``mindie_sim`` primitive programs used by body prediction.  This is the
  integration point for the 29 ``operator_and_kernel_calibration_20261107``
  captures: eight FIA/GDN/conv1d native probe traces and twenty-one
  MoE-native probe traces.  A single native kernel is *not* expanded into a
  sixty-one layer model, a serving step or a synthetic forward population.

[Invariants]
  * The prediction path consumes only the source descriptor: declared tensor
    shapes, operation roles, dtypes, local head/rank split, hardware SKU and
    the retained profiling repeat count.  ``observed_ms``, ``predicted_ms``,
    ``structural_weights``, active HBM/cube demand, ``kernel_summary`` and any
    fitted duration are never read while pricing.
  * FIA/GDN/conv1d are composed with the established
    ``mindie_sim.prediction.call`` builders.  MoE roles are composed from
    ``vector_op`` / matrix / activation / grouped-row primitives on the same
    engine.  One engine invocation is one native call; the retained repeat
    count is carried as a protocol field, not multiplied into the per-call
    physical work.
  * An applicable workload that cannot be priced is returned with
    ``status="unsupported"`` and explicit ``missing_facts`` rather than an
    approximate or fitted number.  ``None`` is returned only when the row is
    not a standalone primitive workload at all.
  * Native duration observations are extracted by a separate function from
    the exact retained trace and are attached as ``native_observation`` with
    ``used_in_prediction=False``.  They never enter the pricing call.

[Timeouts & Locks]
  Bounded local JSON/CSV reads (the MoE point index is small), lazy SIM
  programs, no device access, locks or subprocesses.

[Side-Effect Policy]
  Read-only.  Returns new dictionaries and never mutates the capture row.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "mindie-profiler-fleet-primitive-workload/1"
DESCRIPTOR_SCHEMA = "mindie-profiler-primitive-workload-descriptor/1"
SUITE = "operator_and_kernel_calibration_20261107"
CALIBRATION_ROOT = Path(os.environ.get(
    "MINDIE_PRIMITIVE_CALIBRATION_ROOT",
    "/Volumes/data/mindie-sim-data/calibration-20261107",
))
ATTENTION_ROOT = CALIBRATION_ROOT / "a5" / "attention"
MOE_ROOT = CALIBRATION_ROOT / "a5" / "moe-native"
ATTENTION_REPRESENTATIVE = ATTENTION_ROOT / "raw" / "profiler" / "profiler_representative.json"
SKU = "Ascend950DT_9582"
HARDWARE_SOURCE = {
    "host": "rack08os8",
    "chip": "Ascend950DT",
    "container_image": (
        "vllm-ascend:nightly-ci-releases-v0.30.0-a5-cann9.2.0_20261022115200-20261024-r35"
    ),
    "npu_smi_driver": "26.2.0.b020",
    "torch_npu": "2.10.0.post7",
}

@dataclass(frozen=True)
class PrimitiveWorkload:
    """Narrow typed view of one declared standalone native workload."""

    kind: str
    phase: str | None
    repeats: int | None
    tensors: Mapping[str, Any]
    hardware: Mapping[str, Any]
    source: Mapping[str, Any]
    unsupported: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": DESCRIPTOR_SCHEMA,
            "kind": self.kind,
            "phase": self.phase,
            "repeats": self.repeats,
            "tensors": _canonical(self.tensors),
            "hardware": _canonical(self.hardware),
            "source": _canonical(self.source),
            "applicable": True,
            "unsupported": _canonical(self.unsupported),
        }


# Native MoE roles retained by the recorder.  Helper kernels (finite checks,
# negative controls, index gather) stay outside the native latency boundary.
MOE_NATIVE_ROLES = (
    "router_cast",
    "router_matmul",
    "gating",
    "gating_normalize_reduce",
    "gating_normalize_div",
    "finalize_prob_cast",
    "init_routing",
    "gmm_gate_up",
    "swiglu",
    "gmm_down",
    "finalize",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


def _capture_path(row: Mapping[str, Any]) -> Path | None:
    """Resolve the retained capture path from source provenance, if declared."""
    raw = str(row.get("capture_id") or "")
    marker = "calibration-20261107/a5/"
    if marker not in raw:
        return None
    return CALIBRATION_ROOT / "a5" / raw.split(marker, 1)[1]


def _is_primitive_row(row: Mapping[str, Any]) -> bool:
    return (row.get("suite") == SUITE
            and "calibration-20261107/a5/" in str(row.get("capture_id") or ""))


# ---------------------------------------------------------------------------
# Source descriptors
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _AttentionSource:
    path: Path
    sha256: str
    cases: dict[str, dict[str, Any]]
    profiled_iters: int
    device: int | None


@lru_cache(maxsize=2)
def _attention_source() -> _AttentionSource:
    data = ATTENTION_REPRESENTATIVE.read_bytes()
    payload = json.loads(data)
    if payload.get("kind") != "profiler_representative":
        raise ValueError("attention_source_requires_profiler_representative")
    cases = {case["case"]: case for case in payload["cases"]}
    profiled_iters = payload.get("profiled_iters")
    if type(profiled_iters) is not int or profiled_iters < 1:
        raise ValueError("attention_source_requires_positive_profiled_iters")
    device = payload.get("device")
    if type(device) is not int:
        device = None
    return _AttentionSource(
        ATTENTION_REPRESENTATIVE,
        hashlib.sha256(data).hexdigest(),
        cases,
        profiled_iters,
        device,
    )


@lru_cache(maxsize=2)
def _attention_native_sources() -> tuple[Path, str, dict[str, Any]]:
    path = ATTENTION_ROOT / "summary" / "native_sources.json"
    data = path.read_bytes()
    payload = json.loads(data)
    return path, hashlib.sha256(data).hexdigest(), dict(payload)


@lru_cache(maxsize=2)
def _attention_host_facts() -> dict[str, Any]:
    """Read the retained capture handoff; never infer a host from a tag."""
    path = ATTENTION_ROOT / "handoff.txt"
    text = path.read_text()
    match = re.search(r"^host:\s*(\S+)\s*\(([^)]*)\)", text, re.MULTILINE)
    if match is None:
        return {"handoff_path": str(path), "handoff_sha256": _sha256(path)}
    parts = [item.strip() for item in match.group(2).split(",")]
    return {
        "handoff_path": str(path),
        "handoff_sha256": _sha256(path),
        "host_ip": match.group(1),
        "host_name": parts[0] if parts else None,
        "chip": parts[1] if len(parts) > 1 else None,
    }


@lru_cache(maxsize=2)
def _moe_point_index() -> dict[int, tuple[Path, dict[str, Any], str]]:
    """Index retained MoE point descriptors by recorder pid (exact join key).

    The profiler directory embeds the recorder pid.  Joining on that declared
    pid plus the retained run identity is source provenance; it is not a
    capture-id prediction lookup.  All candidate point files are small.
    """
    index: dict[int, tuple[Path, dict[str, Any], str]] = {}
    for root in (MOE_ROOT / "raw" / "gate3", MOE_ROOT / "raw" / "wave2" / "points",
                 MOE_ROOT / "raw" / "dense"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.json"):
            try:
                payload = json.loads(path.read_bytes())
            except (OSError, ValueError):
                continue
            if not isinstance(payload, Mapping) or "pid" not in payload:
                continue
            pid = payload["pid"]
            if type(pid) is not int:
                continue
            index[pid] = (path, dict(payload), _sha256(path))
    return index


def _native_dispatch(capture_path: Path) -> dict[str, Any]:
    """Retained per-launch block dispatch from the raw kernel row, if present."""
    path = capture_path / "kernel_details.csv"
    if not path.is_file():
        return {"status": "missing_kernel_details_csv", "path": str(path)}
    try:
        rows = _read_kernel_rows(path)
    except OSError:
        return {"status": "unreadable_kernel_details_csv", "path": str(path)}
    if not rows:
        return {"status": "empty_kernel_details_csv", "path": str(path)}
    row = rows[0]
    try:
        block = int(str(row.get("Block Num", "")).strip())
        mix = int(str(row.get("Mix Block Num", "")).strip())
    except (TypeError, ValueError):
        return {"status": "dispatch_fields_absent", "path": str(path)}
    try:
        device_id = int(str(row.get("Device_id", "")).strip())
    except (TypeError, ValueError):
        device_id = None
    return {
        "status": "retained_raw_dispatch",
        "path": str(path),
        "sha256": _sha256(path),
        "block_num": block,
        "mix_block_num": mix,
        "row_count": len(rows),
        "primary_name": str(row.get("Name") or ""),
        "raw_device_id": device_id,
    }


def _capture_artifacts(capture_path: Path) -> dict[str, Any]:
    """List retained profiling artifacts; absent trace/db files stay explicit."""
    if not capture_path.is_dir():
        return {"status": "missing_capture_directory", "path": str(capture_path)}
    names = sorted(item.name for item in capture_path.iterdir() if item.is_file())
    return {
        "status": "retained_capture_directory",
        "path": str(capture_path),
        "files": names,
        "has_kernel_details_csv": "kernel_details.csv" in names,
        "has_analysis_db": "analysis.db" in names,
        "has_trace_view": "trace_view.json" in names,
        "has_op_summary": "op_statistics.csv" in names or "op_summary.csv" in names,
    }


def _attention_descriptor(row: Mapping[str, Any]) -> dict[str, Any] | None:
    path = _capture_path(row)
    if path is None:
        return None
    try:
        relative = path.relative_to(ATTENTION_ROOT / "raw" / "profiler")
    except ValueError:
        return None
    case_name = relative.parts[0]
    try:
        source = _attention_source()
    except (OSError, ValueError) as error:
        return {
            "schema": DESCRIPTOR_SCHEMA,
            "kind": "attention_native_unresolved",
            "phase": None,
            "repeats": None,
            "hardware": {"sku": SKU, "ranks_per_node": 8, **HARDWARE_SOURCE},
            "source": {"capture_path": str(path), "case": case_name,
                       "descriptor_path": str(ATTENTION_REPRESENTATIVE)},
            "applicable": True,
            "unsupported": {
                "reason": "missing_or_invalid_attention_source_descriptor",
                "error": f"{type(error).__name__}: {error}",
                "missing_facts": ["retained_profiler_representative_descriptor",
                                  "declared_repetition_count"],
            },
        }
    case = source.cases.get(case_name)
    if case is None:
        return {
            "schema": DESCRIPTOR_SCHEMA,
            "kind": "attention_native_unresolved",
            "phase": None,
            "repeats": None,
            "hardware": {"sku": SKU, "ranks_per_node": 8, **HARDWARE_SOURCE},
            "source": {"capture_path": str(path), "case": case_name,
                       "descriptor_path": str(source.path),
                       "descriptor_sha256": source.sha256},
            "applicable": True,
            "unsupported": {
                "reason": "case_absent_from_attention_source_descriptor",
                "missing_facts": ["declared_tensors_for_this_capture"],
            },
        }
    common = {
        "schema": DESCRIPTOR_SCHEMA,
        "kind": None,
        "phase": None,
        "repeats": 3,
        "hardware": {
            "sku": SKU,
            "ranks_per_node": 8,
            **HARDWARE_SOURCE,
        },
        "source": {
            "descriptor_path": str(source.path),
            "descriptor_sha256": source.sha256,
            "capture_path": str(path),
            "case": case_name,
            "recorder": "attention/scripts/profile_representative.py",
            "profiled_iters": 3,
        },
    }
    if case.get("status") != "ok":
        common.update({
            "kind": "unsupported_native_error",
            "applicable": True,
            "unsupported": {
                "reason": "source_native_call_rejected",
                "error": case.get("error"),
                "missing_facts": ["successful_native_invocation"],
            },
        })
        return common
    kind = case.get("kind")
    if kind == "fia":
        common.update({
            "kind": "fia_prefill" if case["q_len"] > 1 else "fia_decode",
            "phase": "prefill" if case["q_len"] > 1 else "decode",
            "tensors": {
                "q_len": int(case["q_len"]),
                "kv_len": int(case["kv_len"]),
                "query_heads": int(case["num_heads"]),
                "kv_heads": int(case["num_kv_heads"]),
                "head_dim": int(case["head_dim"]),
                "query_dtype": "bf16",
                "kv_dtype": "bf16",
                "causal": True,
                "window": 0,
                "input_layout": "TND",
                "sparse_mode": 3,
                "pre_tokens": 2147483647,
                "next_tokens": 0,
                "atten_mask": "torch.triu(diagonal=1); True=masked",
                "op_api": "torch_npu.npu_fused_infer_attention_score",
                "api_boundary": "one_warmup_then_profiled_calls",
                "device_dispatch": _native_dispatch(path),
                "tp": int(str(case.get("variant", "")).rsplit(".tp", 1)[-1])
                if ".tp" in str(case.get("variant", "")) else 1,
            },
        })
    elif kind == "gdn":
        common.update({
            "kind": "gdn_chunk_prefill",
            "phase": "prefill",
            "tensors": {
                "batch": 1,
                "tokens": int(case["tokens"]),
                "k_heads": int(case["num_k_heads"]),
                "v_heads": int(case["num_v_heads"]),
                "k_dim": int(case["k_dim"]),
                "v_dim": int(case["v_dim"]),
                "chunk": 64,
                "dtype": "bf16",
                "tp": int(str(case.get("variant", "")).rsplit(".tp", 1)[-1])
                if ".tp" in str(case.get("variant", "")) else 1,
            },
        })
    elif kind == "conv1d":
        common.update({
            "kind": "causal_conv1d",
            "phase": "prefill",
            "tensors": {
                "batch": 1,
                "tokens": int(case["tokens"]),
                "dim": int(case["dim"]),
                "kernel_width": int(case["kernel_width"]),
                "kernel": int(case["kernel_width"]),
                "input_dtype": "bf16",
                "activation": "silu",
                "bias": False,
                "initial_state": False,
                "tp": int(str(case.get("variant", "")).rsplit(".tp", 1)[-1])
                if ".tp" in str(case.get("variant", "")) else 1,
            },
        })
    else:
        return None
    common["applicable"] = True
    common["unsupported"] = None
    common["repeats"] = int(source.profiled_iters)
    try:
        native_path, native_sha, native = _attention_native_sources()
        common["source"].update({
            "native_sources_path": str(native_path),
            "native_sources_sha256": native_sha,
            "native_source_files": _canonical(native.get("sha256") or {}),
            "container": native.get("container"),
            "image": native.get("image"),
            "versions": _canonical(native.get("versions") or {}),
        })
    except (OSError, ValueError) as error:
        common["source"]["native_sources_error"] = f"{type(error).__name__}: {error}"
    common["source"].update(_attention_host_facts())
    raw_device = (common.get("tensors") or {}).get("device_dispatch", {}).get("raw_device_id")
    common["source"].update({
        "declared_device": source.device,
        "raw_kernel_device_id": raw_device,
        "profiling_artifacts": _capture_artifacts(path),
        "device_identity_status": (
            "unresolved_logical_vs_raw" if raw_device is not None
            and source.device is not None and raw_device != source.device
            else "declared_and_raw_agree" if raw_device is not None else
            "raw_device_id_absent"
        ),
    })
    common["source"].update({
        "binary_sha256": "eb1c788e39b7a02f0694450e917a3771c7e65d7d8fb9ea2e03f78c4a5313c456",
        "binary_path": "usr/local/Ascend/cann-9.2.0/aarch64-linux/lib64/libopapi.so",
        "binary_size_bytes": 49775024,
        "binary_role": "cann_opapi_library",
        "binary_identity_status": "image_layer_binary_hash_source_files_verified",
        "binary_identity_scope": (
            "current tag resolution 2026-11-11; the image source-layer member "
            "hashes equal the retained native_sources.json, but this is not a "
            "signed per-run receipt"
        ),
        "binary_image_layer_sha256": (
            "sha256:931e1ff5e88b88557168004d7497d3ae0d448b5ba84bbdfb68545970c702af40"
        ),
        "capture_dispatch_origin": "direct_torch_npu_op_api_probe",
        "capture_api_signature": (
            "torch_npu.npu_fused_infer_attention_score(query,key,value,"
            "atten_mask,actual_seq_lengths,actual_seq_lengths_kv,"
            "input_layout='TND',pre_tokens=INT_MAX,next_tokens=0,sparse_mode=3)"
        ),
        "model_dispatcher_source": {
            "path": "vllm_ascend/attention/attention_v1.py",
            "sha256": "bea4e410f797557e29cedbb495024147606e74b0e056d725194760ca69296eba",
        },
        "model_dispatcher_used_for_pricing": False,
        "cann_fia_kernel_sources": {
            "layer_sha256": "sha256:931e1ff5e88b88557168004d7497d3ae0d448b5ba84bbdfb68545970c702af40",
            "root": ("opp/built-in/op_impl/ai_core/tbe/impl/ops_transformer/"
                     "ascendc/fused_infer_attention_score/op_kernel/arch35"),
            "fia_arch35_template_tiling_key_enum.h":
                "48d2b245322504291a7606003afa12e0094bd171f5a908dcdcbad74a7687ba16",
            "fused_infer_attention_score_template_tiling_key.h":
                "2ef47d10a40eb1d5133d8c923fc3a67af4dd8da450a4b701b438e55df7164cc8",
            "fia_template_dispatcher.h":
                "dc1f808865d822ffa89ecd6e965e869d8211a3ff4768ed105b54a7ce73f86034",
            "flash_attention_noquant_block_cube_fused_infer.h":
                "b7129438fcebd051750af40427680a1b177bfff72669ea4f4455bba7547aac93",
            "flash_attention_noquant_block_vec_base_fused_infer.h":
                "304f50fbdc58574e5602d7aecc5698684d79e5aa4ca45b7d6ad4df20c31abc00",
            "matching_configs": {
                "D128_64x256": {
                    "config": 1,
                    "name": "S1Aligned64_S2Aligned256_DAligned128_DVAligned128",
                },
                "D128_128x128": {
                    "config": 3,
                    "name": "S1Aligned128_S2Aligned128_DAligned128_DVAligned128",
                },
                "D256_128x128": {
                    "config": 6,
                    "name": "S1Aligned128_S2Aligned128_DAligned256_DVAligned256",
                },
                "D256_64x256": {
                    "config": 18,
                    "name": "S1Aligned64_S2Aligned256_DAligned256_DVAligned256",
                },
            },
            "selector_blocks": {
                "1266-1280": {"configs": [1, 6], "isfd": "false,true",
                              "kv": "NO_PA,ENABLE_PA", "kvprefix": False,
                              "reconstruct": False, "tiling": "Simplified"},
                "1281-1294": {"configs": [1], "isfd": "false,true",
                              "kv": "NO_PA,PA_BBH,PA_BNBD,PA_NZ", "kvprefix": False,
                              "reconstruct": True, "tiling": "FIA"},
                "1308-1320": {"configs": [1, 6], "isfd": "false",
                              "kv": "NO_PA", "kvprefix": True,
                              "reconstruct": False, "tiling": "Simplified"},
                "1321-1334": {"configs": [2, 3, 5], "isfd": "true",
                              "kv": "NO_PA,ENABLE_PA", "kvprefix": False,
                              "reconstruct": False, "tiling": "Simplified"},
                "1335-1349": {"configs": [3, 5], "isfd": "true",
                              "kv": "NO_PA,PA_BBH,PA_BNBD,PA_NZ", "kvprefix": False,
                              "reconstruct": True, "tiling": "FIA"},
                "1350-1362": {"configs": [2, 3], "isfd": "false",
                              "kv": "NO_PA,ENABLE_PA", "kvprefix": False,
                              "reconstruct": False, "tiling": "Simplified"},
                "1363-1375": {"configs": [3], "isfd": "false",
                              "kv": "NO_PA,PA_BBH,PA_BNBD,PA_NZ", "kvprefix": False,
                              "reconstruct": True, "tiling": "FIA"},
                "1376-1386": {"configs": [3], "isfd": "false",
                              "kv": "NO_PA", "kvprefix": True,
                              "reconstruct": False, "tiling": "Simplified"},
                "1458-1469": {"configs": [18], "isfd": "false,true",
                              "kv": "NO_PA,ENABLE_PA", "kvprefix": False,
                              "reconstruct": False, "tiling": "Simplified",
                              "hasrope": "false,true"},
                "1470-1480": {"configs": [18], "isfd": "false",
                              "kv": "NO_PA", "kvprefix": True,
                              "reconstruct": False, "tiling": "Simplified"},
                "1497-1514": {"configs": [1, 3], "isfd": "false,true",
                              "kv": "NO_PA", "kvprefix": False,
                              "reconstruct": False, "tiling": "Simplified",
                              "note": "qkv_d_unequal"},
                "1527-1546": {"configs": [6, 18], "isfd": "false",
                              "kv": "NO_PA,ENABLE_PA", "kvprefix": False,
                              "s1outsplit": True, "reconstruct": False,
                              "tiling": "Simplified"},
                "1547-1559": {"configs": [1, 3], "isfd": "false",
                              "kv": "NO_PA,ENABLE_PA", "kvprefix": False,
                              "s1outsplit": True, "reconstruct": False,
                              "tiling": "Simplified"},
                "1560-1575": {"configs": [1, 3], "isfd": "false",
                              "kv": "NO_PA,PA_BBH,PA_BNBD,PA_NZ", "kvprefix": False,
                              "s1outsplit": True, "reconstruct": True, "tiling": "FIA"},
                "1576-1598": {"configs": [1, 3, 6, 18], "isfd": "false",
                              "kv": "NO_PA,ENABLE_PA", "kvprefix": False,
                              "s1outsplit": True, "reconstruct": False,
                              "tiling": "Simplified"},
            },
            "blanket_prefill_isfd_zero": False,
            "compile_time_fd": {
                "file": "fia_kernel_noquant_gqa.h",
                "line": 797,
                "text": "if constexpr (FLASH_DECODE)",
                "scope": "compile-time capability, not user q_len==1 guard",
            },
            "scope": "actual image layer headers; matching compile-time configs and "
                     "selector blocks are candidates, runtime selection not retained",
        },
    })
    return common


def _moe_declared_calls(point: Mapping[str, Any]) -> int | None:
    """Producer-declared repetition count, never a default."""
    trace = point.get("native_trace") or {}
    marker = trace.get("marker_count")
    if type(marker) is int and marker > 0:
        return marker
    counts = []
    for value in (trace.get("per_kernel_summary") or {}).values():
        if isinstance(value, Mapping) and type(value.get("n")) is int:
            counts.append(int(value["n"]))
    if counts and len(set(counts)) == 1 and counts[0] > 0:
        return counts[0]
    reps = [len(value.get("rep_durations_us") or ())
            for value in (trace.get("summary") or {}).values()
            if isinstance(value, Mapping)]
    reps = [value for value in reps if value > 0]
    if reps and len(set(reps)) == 1:
        return reps[0]
    return None


def _moe_descriptor(row: Mapping[str, Any]) -> dict[str, Any] | None:
    path = _capture_path(row)
    if path is None:
        return None
    try:
        relative = path.relative_to(MOE_ROOT / "raw" / "prof")
    except ValueError:
        return None
    profiler_name = relative.parts[0]
    pid_token = next((part for part in relative.parts if part.startswith("rack08os5_")), "")
    try:
        pid = int(pid_token.split("_")[1])
    except (IndexError, ValueError):
        pid = -1
    entry = _moe_point_index().get(pid)
    source = {
        "capture_path": str(path),
        "profiler": profiler_name,
        "recorder_pid": pid,
        "descriptor_path": None,
        "descriptor_sha256": None,
    }
    common = {
        "schema": DESCRIPTOR_SCHEMA,
        "kind": "moe_native_chain",
        "phase": "decode",
        "repeats": None,
        "hardware": {
            "sku": SKU,
            "ranks_per_node": 8,
            "num_devices": 1,
            "tp": 1,
            **HARDWARE_SOURCE,
        },
        "source": source,
        "applicable": True,
        "unsupported": None,
    }
    if entry is None:
        common.update({
            "kind": "moe_native_unresolved",
            "unsupported": {
                "reason": "missing_declared_tensor_descriptor",
                "missing_facts": [
                    "declared_E_K_bank_H_I_capacity_q",
                    "declared_local_expert_assignment_count",
                    "declared_native_role_binding",
                ],
            },
        })
        return common
    point_path, point, point_sha = entry
    source.update({"descriptor_path": str(point_path),
                   "descriptor_sha256": point_sha,
                   "point_schema": point.get("schema"),
                   "wave": point.get("wave"),
                   "run_id": point.get("run_id"),
                   "status": point.get("status"),
                   "tuple": _canonical(point.get("tuple")),
                   "manifest_sha256": point.get("manifest_sha256")})
    geometry = point.get("geometry")
    structural = point.get("structural")
    tuple_ = point.get("tuple")
    if not isinstance(geometry, Mapping) or not isinstance(structural, Mapping) \
            or not isinstance(tuple_, Mapping):
        common["unsupported"] = {
            "reason": "descriptor_outside_moe_native_call_chain",
            "missing_facts": ["declared_E_K_bank_H_I_capacity_q"],
        }
        return common
    calls = _moe_declared_calls(point)
    common["repeats"] = calls
    if calls is None:
        common["unsupported"] = {
            "reason": "missing_declared_repetition_count",
            "missing_facts": ["producer_declared_native_call_count"],
        }
    if point.get("status") != "valid":
        common["unsupported"] = {
            "reason": "source_point_status_not_valid",
            "source_status": point.get("status"),
            "errors": _canonical(point.get("errors", [])),
            "missing_facts": ["valid_native_binding"],
        }
    common["tensors"] = {
        "experts": int(geometry["E"]),
        "top_k": int(geometry["K"]),
        "local_bank": int(geometry["bank"]),
        "hidden": int(geometry["H"]),
        "intermediate": int(geometry["I"]),
        "capacity_rows": int(geometry["capacity"]),
        "tokens": int(tuple_["q"]),
        "dtype": str(tuple_["dtype"]),
        "distribution": str(tuple_.get("dist", "")),
        "local_assignment_rows": int(structural.get("local_assignments", 0)),
        "split": tuple_.get("split"),
    }
    return common


def primitive_workload_descriptor(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the declared standalone workload, or ``None`` when not one.

    ``None`` is reserved for rows that are not standalone native primitives
    (ordinary model captures, serving cells).  A primitive capture with a
    missing/invalid descriptor is an applicable-but-unpriceable workload and
    is returned with an explicit unsupported record.
    """
    if not isinstance(row, Mapping) or not _is_primitive_row(row):
        return None
    path = str(row.get("capture_id") or "")
    if "/a5/attention/raw/profiler/" in path:
        return _attention_descriptor(row)
    if "/a5/moe-native/raw/prof/" in path:
        return _moe_descriptor(row)
    return None


def is_primitive_workload(row: Mapping[str, Any]) -> bool:
    """Predicate for callers that route primitive rows before the model branch."""
    return primitive_workload_descriptor(row) is not None


def declared_primitive_workload(
    row: Mapping[str, Any],
) -> PrimitiveWorkload | None:
    """Typed declared workload for the normal caller contract.

    Returns ``None`` exactly when :func:`primitive_workload_descriptor` does.
    The tensors/operation/dtype/repeats/hardware/source fields are the only
    inputs consumed by the public SIM composition.
    """
    descriptor = primitive_workload_descriptor(row)
    if descriptor is None:
        return None
    return PrimitiveWorkload(
        kind=str(descriptor.get("kind")),
        phase=str(descriptor.get("phase")),
        repeats=(None if descriptor.get("repeats") is None
                 else int(descriptor["repeats"])),
        tensors=descriptor.get("tensors") or {},
        hardware=descriptor.get("hardware") or {},
        source=descriptor.get("source") or {},
        unsupported=descriptor.get("unsupported"),
    )


# ---------------------------------------------------------------------------
# Hardware case and public SIM composition
# ---------------------------------------------------------------------------


@lru_cache(maxsize=4)
def _hardware_case(ranks: int):
    from mindie_sim.backends.ascend import materialize
    from mindie_sim.prediction.structure import parse_case

    machine = materialize({"sku": SKU, "num_devices": int(ranks),
                           "ranks_per_node": 8})
    raw = {
        "machine": machine,
        "model": {
            "name": "standalone_primitive_workload",
            "layers": 1,
            "hidden_size": 512,
            "num_heads": 4,
            "num_kv_heads": 1,
            "head_dim": 256,
            "intermediate_size": 512,
            "vocab_size": 1000,
        },
        "workload": {"requests": [{"id": "primitive",
                                   "prompt_tokens": 1, "output_tokens": 1}]},
        "runtime": {"dp": 1, "tp": 1, "pp": 1, "ep": 1,
                    "max_num_batched_tokens": 16},
    }
    return parse_case(raw)


def _fia_op(descriptor: Mapping[str, Any]):
    from mindie_sim.schema.operators import OpSpec
    from mindie_sim.prediction import attention_decode, attention_prefill

    tensors = descriptor["tensors"]
    if tensors.get("input_layout") != "TND":
        raise ValueError("fia_capture_input_layout_requires_TND")
    if tensors.get("sparse_mode") != 3:
        raise ValueError("fia_capture_sparse_mode_requires_3")
    if tensors.get("pre_tokens") != 2147483647 or tensors.get("next_tokens") != 0:
        raise ValueError("fia_capture_attention_window_requires_pre_INT_MAX_next_0")
    if tensors.get("op_api") != "torch_npu.npu_fused_infer_attention_score":
        raise ValueError("fia_capture_api_requires_npu_fused_infer_attention_score")
    phase = descriptor["phase"]
    q_len, kv_len = tensors["q_len"], tensors["kv_len"]
    heads, kv_heads = tensors["query_heads"], tensors["kv_heads"]
    dim = tensors["head_dim"]
    context = kv_len - q_len
    if context < 0:
        raise ValueError("fia_kv_len_must_cover_query_rows")
    metadata = {
        "requests": ((q_len, context),),
        "query_heads": heads,
        "kv_heads": kv_heads,
        "head_dim": dim,
        "query_dtype": tensors["query_dtype"],
        "kv_dtype": tensors["kv_dtype"],
        "causal": True,
        "window": 0,
        "cp": 1,
    }
    pairs = (q_len * (context + 1) + q_len * (q_len - 1) // 2) if phase == "decode" \
        else (q_len * (context + q_len) - q_len * (q_len - 1) // 2)
    shape = (q_len, kv_len, heads, dim)
    if phase == "prefill":
        recipe, key, build = "flash_attention_prefill", "gqa_prefill", attention_prefill.build
    else:
        recipe, key, build = "flash_attention_decode", "gqa_decode", attention_decode.build
    op = OpSpec(
        "native_fia", "attention", phase, 0, 0, (), shape, shape, shape, shape,
        flops=4 * pairs * heads * dim,
        hbm_bytes=((q_len + kv_len) * heads * dim * 2
                   + kv_len * kv_heads * dim * 2),
        mte2_bytes=(q_len * heads * dim * 2 + kv_len * kv_heads * dim * 2),
        mte3_bytes=q_len * heads * dim * 2,
        vector_ops=5 * pairs * heads,
        recipe=recipe, dtype=tensors["query_dtype"],
        metadata=((key, metadata), ("native_operator", "FusedInferAttentionScore"),
                  ("capture_abi", {
                      "op_api": tensors.get("op_api"),
                      "input_layout": tensors.get("input_layout"),
                      "sparse_mode": tensors.get("sparse_mode"),
                      "pre_tokens": tensors.get("pre_tokens"),
                      "next_tokens": tensors.get("next_tokens"),
                      "atten_mask": tensors.get("atten_mask"),
                  }),
                  ("device_dispatch", tensors.get("device_dispatch"))),
    )
    return op, recipe, build


def _trace_stage_ms(events: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Read the bounded decode owner events; the planner compresses key tiles."""
    suffixes = {
        "q_load": ":program:q_load",
        "key_tile_pipeline": ":steady_pipeline",
        "final_store": ":program:final_store",
    }
    result: dict[str, float] = {}
    for event in events:
        task = str(event.get("task", ""))
        for name, suffix in suffixes.items():
            if task.endswith(suffix):
                result[name] = float(event.get("end_ms", 0.0)) - float(
                    event.get("start_ms", 0.0))
    return result


def _price_fia(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    from mindie_sim.prediction.call import call_costs
    from mindie_sim.prediction.mechanism import PlannedRecipe
    from mindie_sim.prediction.program import RecipeBook

    op, recipe_name, build = _fia_op(descriptor)
    case = _hardware_case(int(descriptor["tensors"].get("tp", 1)))
    if descriptor["phase"] == "prefill":
        # The staged GQA prefill program is the prediction boundary.  The
        # recipe compacts long periodic key-tile pipelines internally; no
        # aggregate work envelope or private fast path is used here.
        report = call_costs(case, (op,), recipes=RecipeBook(
            {recipe_name: PlannedRecipe(build)}), invocations=1)
        composition = {
            "program": "staged_gqa_prefill_pipeline",
            "work_source": "mindie_sim.prediction.attention_prefill.StagedGQAPrefill",
            "long_kv_execution": "recipe_bounded_periodic_pipeline",
        }
    else:
        report = call_costs(case, (op,), recipes=RecipeBook(
            {recipe_name: PlannedRecipe(build)}), invocations=1,
            trace_limit=200000)
        composition = {"program": "staged_gqa_decode_pipeline"}
    kernel = {
        "name": "FusedInferAttentionScore",
        "role": "fia",
        "shape": list(op.local_shape),
        "query_heads": descriptor["tensors"]["query_heads"],
        "kv_heads": descriptor["tensors"]["kv_heads"],
        "head_dim": descriptor["tensors"]["head_dim"],
        "dtype": op.dtype,
        "flops": op.flops,
        "hbm_bytes": op.hbm_bytes,
        "vector_ops": op.vector_ops,
        "duration_ms": report["duration_ms"],
        "stage_work": _fia_stage_work(op, descriptor),
        "engine_trace_stage_ms": (
            _trace_stage_ms(report.get("events") or ())
            if descriptor["phase"] == "decode" else None),
    }
    return {
        "status": "predicted",
        "model": "mindie_sim.public_primitive_composition/1",
        "composition": composition,
        "operators": [op.to_dict()],
        "kernels": [kernel],
        "coverage": {
            "declared_roles": ["FusedInferAttentionScore"],
            "basis": ("pinned_staged_gqa_prefill_pipeline_mechanism"
                      if descriptor["phase"] == "prefill"
                      else "pinned_staged_gqa_decode_pipeline_mechanism"),
            "native_implementation_identity": "not_established",
            "unmodeled": [],
        },
        "predicted_ms": report["duration_ms"],
        "predicted_total_ms": report["duration_ms"] * descriptor["repeats"],
        "resources": report["resources"],
        "execution": report["execution"],
        "protocol": report["protocol"],
        "assumptions": report["assumptions"],
    }


def _fia_stage_work(op, descriptor: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Decompose the declared FIA program into load / QK / PV / store stages.

    These are the declared work classes of the same physical recipe; the
    service column divides them by the declared hardware supply so that a
    reviewer can see the pipeline composition.  They are not a second
    latency model and the kernel duration remains the engine result.
    """
    from mindie_sim.prediction import attention_decode, attention_prefill

    tensors = descriptor["tensors"]
    q_len, kv_len = tensors["q_len"], tensors["kv_len"]
    heads, kv_heads = tensors["query_heads"], tensors["kv_heads"]
    dim = tensors["head_dim"]
    context = kv_len - q_len
    if descriptor["phase"] == "prefill":
        recipe_report = attention_prefill.StagedGQAPrefill().report(op)
        key_loads = int(recipe_report["key_tile_loads"])
        kv_bytes = int(recipe_report["kv_bytes"])
        physical = int(recipe_report["executed_rectangle_pairs"])
        logical = int(recipe_report["logical_pairs"])
        kv_work = kv_bytes
    else:
        recipe = attention_decode.StagedGQADecode()
        spec = recipe.spec(op)
        key_loads = sum(len(output.contributions) for output in spec.outputs)
        kv_bytes = sum(output.horizon * dim * spec.kv_bytes
                       for output in spec.outputs)
        pairs = attention_decode.causal_pairs(q_len, context)
        logical = pairs * heads
        physical = q_len * (context + q_len) * heads
        kv_work = 2 * kv_bytes
    query_bytes = q_len * heads * dim * 2
    output_bytes = q_len * heads * dim * 2
    flops = 4 * dim * physical
    vector = 7 * physical + q_len * (3 * dim + 10) * heads
    die = _hardware_case(int(descriptor["tensors"].get("tp", 1))).machine.dies[0]
    rates, peaks = dict(die.rates), dict(die.compute_peaks)
    hbm_rate = float(rates["hbm"])
    mte2_rate = float(rates.get("mte2_aic", hbm_rate))
    mte3_rate = float(rates.get("mte3", hbm_rate))
    vector_rate = float(rates["vector"])
    matrix_rate = float(peaks["bf16"])
    by_kind = {"hbm": hbm_rate, "mte2": mte2_rate, "mte3": mte3_rate,
               "vector": vector_rate, "matrix": matrix_rate}

    def service(kind, value):
        if kind not in by_kind:
            raise ValueError(f"unknown_fia_stage_resource:{kind}")
        return 1000.0 * value / by_kind[kind]

    stage_rows = [
        ("q_load", {"hbm": query_bytes, "mte2": query_bytes},
         {"bytes": query_bytes}),
        ("kv_load", {"hbm": kv_work, "mte2": kv_work},
         {"bytes": kv_work, "key_tile_loads": key_loads}),
        ("qk_pv", {"matrix": flops},
         {"flops": flops, "executed_pairs": physical,
          "logical_causal_pairs": logical}),
        ("softmax_online", {"vector": vector}, {"vector_ops": vector}),
        ("store", {"hbm": output_bytes, "mte3": output_bytes},
         {"bytes": output_bytes}),
    ]
    stages = []
    for name, work, operations in stage_rows:
        service_ms = max(service(kind, value) for kind, value in work.items())
        stages.append({
            "stage": name,
            "work": work,
            "operation_count": operations,
            "service_ms": service_ms,
            "service_basis": ("resource_lower_bound_diagnostic_not_used_for_"
                              "prediction"),
        })
    return stages


_GDN_NATIVE_NAMES = {
    "gdn_prepare_arch35_mix_aic_aiv_1_2":
        "aclnnChunkGatedDeltaRuleFwdPrepare_ChunkGatedDeltaRuleFwdPrepare",
    "chunk_fwd_h": "aclnnChunkGatedDeltaRuleFwd_ChunkFwdH_ChunkFwdH",
    "gdn_output_arch35_token_first":
        "aclnnChunkGatedDeltaRuleFwd_ChunkFwdO_ChunkFwdO",
}


def _price_gdn(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    from mindie_sim.prediction.call import call_costs
    from mindie_sim.prediction.call_gdn import make_call
    from mindie_sim.prediction.graph_analysis import graph_costs

    tensors = descriptor["tensors"]
    if descriptor["kind"] == "gdn_chunk_prefill":
        call = make_call("scan_prefill", {
            "batch": tensors["batch"], "tokens": tensors["tokens"],
            "k_heads": tensors["k_heads"], "v_heads": tensors["v_heads"],
            "k_dim": tensors["k_dim"], "v_dim": tensors["v_dim"],
            "chunk": tensors["chunk"], "phase": "prefill",
            "input_dtype": "bf16", "scale": tensors["k_dim"] ** -0.5,
            "chunk_size": tensors["chunk"], "a_log": None, "dt_bias": None,
        })
    else:
        call = make_call("conv_prefill", {
            "batch": tensors["batch"], "tokens": tensors["tokens"],
            "conv_width": tensors["dim"], "kernel": tensors["kernel"],
            "input_dtype": tensors["input_dtype"],
            "activation": "silu", "bias": bool(tensors.get("bias", False)),
            "initial_state": False,
        })
    case = _hardware_case(max(1, int(tensors.get("tp", 1))))
    report = call_costs(case, call.ops, recipes=call.recipes, invocations=1)
    isolated = graph_costs(case, call.ops, recipes=call.recipes, isolated=True)
    by_id = {row["op_id"]: row for row in isolated["timeline"]}
    kernels = []
    for op in call.ops:
        metadata = dict(op.metadata)
        boundary = op.source_boundary or "analytical"
        row = by_id.get(op.op_id, {})
        name = (metadata.get("native_kind")
                or _GDN_NATIVE_NAMES.get(op.recipe)
                or op.family)
        if descriptor["kind"] == "causal_conv1d":
            name = "CausalConv1d"
        kernels.append({
            "name": name,
            "role": op.family,
            "op_id": op.op_id,
            "recipe": op.recipe,
            "shape": list(op.local_shape),
            "dtype": op.dtype,
            "boundary": boundary,
            "flops": op.flops,
            "hbm_bytes": op.hbm_bytes,
            "vector_ops": op.vector_ops,
            "duration_ms": row.get("isolated_ms", 0.0),
            "operation_count": {
                "flops": op.flops,
                "hbm_bytes": op.hbm_bytes,
                "mte2_bytes": op.mte2_bytes,
                "mte3_bytes": op.mte3_bytes,
                "vector_ops": op.vector_ops,
            },
        })
    return {
        "status": "predicted",
        "model": "mindie_sim.public_primitive_composition/1",
        "operators": [op.to_dict() for op in call.ops],
        "kernels": kernels,
        "ledger": call.ledger,
        "limitations": list(call.limitations),
        "predicted_ms": report["duration_ms"],
        "predicted_total_ms": report["duration_ms"] * descriptor["repeats"],
        "resources": report["resources"],
        "execution": report["execution"],
        "protocol": report["protocol"],
        "assumptions": report["assumptions"],
    }


def _moe_expert_rows(descriptor: Mapping[str, Any]) -> tuple[int, ...]:
    tensors = descriptor["tensors"]
    bank = tensors["local_bank"]
    total = tensors["local_assignment_rows"]
    if bank < 1 or total < 0:
        raise ValueError("moe_native_chain_requires_nonnegative_declared_rows")
    base, extra = divmod(total, bank)
    return tuple(base + (1 if index < extra else 0) for index in range(bank))


def _price_moe(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    from mindie_sim.catalog.ops import vector_op
    from mindie_sim.prediction.call import call_costs
    from mindie_sim.prediction.calls_activation import (
        ActivationCallSpec, build_activation_call,
    )
    from mindie_sim.prediction.graph_analysis import graph_costs
    from mindie_sim.schema.operators import OpSpec

    tensors = descriptor["tensors"]
    experts, top_k, bank = tensors["experts"], tensors["top_k"], tensors["local_bank"]
    hidden, intermediate = tensors["hidden"], tensors["intermediate"]
    capacity, tokens = tensors["capacity_rows"], tensors["tokens"]
    dtype = tensors["dtype"]
    if dtype not in {"bf16", "bfloat16"}:
        return {"status": "unsupported", "unsupported": {
            "reason": "moe_native_chain_requires_bf16_activation",
            "missing_facts": ["bf16_router_abi", "bf16_grouped_weights"],
        }}
    expert_rows = _moe_expert_rows(descriptor)
    total_rows = sum(expert_rows)
    if not total_rows:
        return {"status": "unsupported", "unsupported": {
            "reason": "declared_zero_local_expert_rows",
            "missing_facts": ["positive_local_expert_assignment"],
        }}
    ops = []
    element_bytes = 2
    logits_ops = 5 + math.log2(max(1, top_k))

    def add(op):
        ops.append(op)
        return op.op_id

    # 1. FP32 router cast.
    router_cast = add(vector_op(
        op_id="router_cast", deps=(), stage=0, layer=0, requests=(),
        elements=tokens * hidden, ops_per_element=1, dtype="bf16",
        family="elementwise", phase="decode", recipe="moe_router_cast",
        shape=(tokens, hidden),
        read_bytes_override=tokens * hidden * 2,
        write_bytes_override=tokens * hidden * 4,
        metadata=(("native_role", "router_cast"),
                  ("native_kind", "aclnnInplaceCopy_CastAiCore_Cast"),
                  ("input_format", "bf16"), ("output_format", "fp32"))))

    # 2. FP32 router matmul on the matrix core.
    router_matmul = add(OpSpec(
        "router_matmul", "gemm", "decode", 0, 0, (),
        (tokens, experts), (tokens, experts, hidden), (tokens, experts),
        (tokens, experts), flops=2 * tokens * hidden * experts,
        hbm_bytes=(tokens * hidden * 4 + hidden * experts * 4 + tokens * experts * 4),
        mte2_bytes=(tokens * hidden * 4 + hidden * experts * 4),
        mte3_bytes=tokens * experts * 4, dtype="fp32", deps=(router_cast,),
        recipe="moe_router_matmul",
        metadata=(("program_kind", "matmul"), ("native_role", "router_matmul"),
                  ("native_kind", "aclnnMatmul_MatMulV3Common_MatMulV3"),
                  ("input_format", "fp32"), ("output_format", "fp32")),
    ))

    # 3. MoeGatingTopK.
    gating = add(vector_op(
        op_id="gating", deps=(router_matmul,), stage=0, layer=0, requests=(),
        elements=tokens * experts, ops_per_element=logits_ops, dtype="fp32",
        family="topk", phase="decode", recipe="moe_gating_topk",
        shape=(tokens, experts),
        read_bytes_override=tokens * experts * 4 + tokens * (8 + top_k * 4),
        write_bytes_override=tokens * top_k * 4 + tokens * top_k * 4 + tokens * experts * 4,
        returns=("weights", "ids", "extra"),
        metadata=(("native_role", "gating"),
                  ("native_kind", "aclnnMoeGatingTopK_MoeGatingTopK_MoeGatingTopK"),
                  ("topk_ids_dtype", "int32"),
                  ("router_weight_dtype", "fp32"), ("score_function", "softmax"),
                  ("renorm", True))))

    # 4. ReduceSum + Div normalization of the retained top-k probabilities.
    normalize_reduce = add(vector_op(
        op_id="gating_normalize_reduce", deps=(gating,), stage=0, layer=0,
        requests=(), elements=tokens * top_k, ops_per_element=1, dtype="fp32",
        family="elementwise", phase="decode", recipe="moe_gating_normalize_reduce",
        shape=(tokens, top_k),
        read_bytes_override=tokens * top_k * 4,
        write_bytes_override=tokens * 4,
        metadata=(("native_role", "gating_normalize_reduce"),
                  ("native_kind", "aclnnReduceSum_ReduceSumOpAiCore_ReduceSum"),)))
    normalize_div = add(vector_op(
        op_id="gating_normalize_div", deps=(gating, normalize_reduce),
        stage=0, layer=0, requests=(), elements=tokens * top_k,
        ops_per_element=1, dtype="fp32", family="elementwise", phase="decode",
        recipe="moe_gating_normalize_div", shape=(tokens, top_k),
        read_bytes_override=tokens * top_k * 4 + tokens * 4,
        write_bytes_override=tokens * top_k * 4,
        metadata=(("native_role", "gating_normalize_div"),
                  ("native_kind", "aclnnDiv_RealDivAiCore_RealDiv"),)))

    # 5. Cast the top-k probabilities to the activation dtype.
    prob_cast = add(vector_op(
        op_id="finalize_prob_cast", deps=(normalize_div,), stage=0, layer=0,
        requests=(), elements=tokens * top_k, ops_per_element=1, dtype="fp32",
        family="elementwise", phase="decode", recipe="moe_prob_cast",
        shape=(tokens, top_k),
        read_bytes_override=tokens * top_k * 4,
        write_bytes_override=tokens * top_k * 2,
        metadata=(("native_role", "finalize_prob_cast"),
                  ("native_kind", "aclnnInplaceCopy_CastAiCore_Cast"),
                  ("output_format", "bf16"))))

    # 6. MoeInitRoutingV3: expanded capacity allocation plus row indices.
    init_routing = add(vector_op(
        op_id="init_routing", deps=(router_cast, prob_cast), stage=0, layer=0,
        requests=(), elements=capacity, ops_per_element=1, dtype="bf16",
        family="routing", phase="decode", recipe="moe_init_routing",
        shape=(capacity, hidden),
        read_bytes_override=tokens * hidden * 2 + tokens * top_k * 2,
        write_bytes_override=(capacity * hidden * 2 + capacity * 4 + experts * 8
                              + capacity * 4),
        vector_ops_override=float(capacity + tokens * top_k),
        metadata=(("native_role", "init_routing"),
                  ("native_kind", "aclnnMoeInitRoutingV3_MoeInitRoutingV3_MoeInitRoutingV3"),
                  ("active_rows", capacity),
                  ("valid_rows", total_rows), ("expert_rows", list(expert_rows)))))

    # 7/9. Grouped expert gate-up and down GEMMs.
    def grouped(op_id, rows, n, k, deps, role):
        packed = bank * k * n * element_bytes
        return add(OpSpec(
            op_id, "grouped_gemm", "decode", 0, 0, (),
            (rows, n), (rows, n, k), (rows, n), (rows, n),
            flops=2 * rows * n * k,
            hbm_bytes=(rows * k * element_bytes + packed + rows * n * element_bytes),
            mte2_bytes=(rows * k * element_bytes + packed),
            mte3_bytes=rows * n * element_bytes, dtype="bf16", deps=deps,
            recipe=role,
            metadata=(("matrix_group_rows", expert_rows),
                      ("matrix_groups", bank),
                      ("packed_weight_bytes", packed),
                      ("native_role", "gmm_gate_up" if role == "grouped_gate_up"
                       else "gmm_down"),
                      ("native_kind", "aclnnGroupedMatmulV5_GroupedMatmul_GroupedMatmul"),
                      ("input_format", "bf16"),
                      ("weight_format", "bf16"), ("output_format", "bf16")),
        ))

    gate_up = grouped("gmm_gate_up", total_rows, 2 * intermediate, hidden,
                      (init_routing,), "grouped_gate_up")
    activation = build_activation_call(ActivationCallSpec(
        "swiglu_fused", capacity, intermediate, dtype="bf16", phase="decode"))
    swiglu_op = next(iter(activation.ops))
    from dataclasses import replace
    swiglu_op = replace(swiglu_op, op_id="swiglu", deps=(gate_up,),
                        metadata=tuple(activation.ops[0].metadata)
                        + (("native_role", "swiglu"), ("native_kind", "SwiGlu")))
    add(swiglu_op)
    down = grouped("gmm_down", total_rows, hidden, intermediate,
                   ("swiglu",), "grouped_down")
    finalize = add(vector_op(
        op_id="finalize", deps=(down, prob_cast), stage=0, layer=0, requests=(),
        elements=tokens * hidden, ops_per_element=1, dtype="bf16",
        family="elementwise", phase="decode", recipe="moe_finalize_routing",
        shape=(tokens, hidden),
        read_bytes_override=(total_rows * hidden * 2 + total_rows * 4
                             + tokens * top_k * 2),
        write_bytes_override=tokens * hidden * 2,
        vector_ops_override=float(tokens * hidden + total_rows),
        metadata=(("native_role", "finalize"),
                  ("native_kind", "aclnnMoeTokenUnpermute_MoeFinalizeRoutingV2_MoeFinalizeRoutingV2"),)))

    case = _hardware_case(1)
    report = call_costs(case, tuple(ops), recipes=activation.recipes,
                        invocations=1)
    isolated = graph_costs(case, tuple(ops), recipes=activation.recipes,
                           isolated=True)
    by_id = {row["op_id"]: row for row in isolated["timeline"]}
    kernels = []
    for op in ops:
        metadata = dict(op.metadata)
        row = by_id.get(op.op_id, {})
        kernels.append({
            "name": metadata.get("native_kind") or metadata.get("native_role", op.family),
            "role": metadata.get("native_role", op.family),
            "op_id": op.op_id,
            "recipe": op.recipe,
            "shape": list(op.local_shape),
            "dtype": op.dtype,
            "flops": op.flops,
            "hbm_bytes": op.hbm_bytes,
            "vector_ops": op.vector_ops,
            "duration_ms": row.get("isolated_ms", 0.0),
            "operation_count": {
                "flops": op.flops,
                "hbm_bytes": op.hbm_bytes,
                "mte2_bytes": op.mte2_bytes,
                "mte3_bytes": op.mte3_bytes,
                "vector_ops": op.vector_ops,
            },
        })
    return {
        "status": "predicted",
        "model": "mindie_sim.public_primitive_composition/1",
        "operators": [op.to_dict() for op in ops],
        "kernels": kernels,
        "ledger": {
            "declared_roles": list(MOE_NATIVE_ROLES),
            "expert_rows": list(expert_rows),
            "per_expert_rows_exact": tensors.get("distribution") == "balanced_exact",
            "per_expert_rows_basis": (
                "declared_balanced_distribution" if tensors.get("distribution")
                == "balanced_exact" else
                "equal_split_of_declared_total_and_local_bank"),
            "distribution": tensors.get("distribution"),
            "local_assignment_rows": total_rows,
            "capacity_rows": capacity,
        },
        "coverage": {
            "declared_roles": [kernel["role"] for kernel in kernels],
            "basis": {
                "gmm_gate_up": "declared_integer_expert_histogram_matrix_program",
                "gmm_down": "declared_integer_expert_histogram_matrix_program",
                "swiglu": "declared_gated_activation_expression_work",
                "router_cast": "declared_elementwise_cast_work",
                "router_matmul": "declared_fp32_matrix_work",
                "gating": "declared_topk_expression_work",
                "gating_normalize_reduce": "declared_reduction_work",
                "gating_normalize_div": "declared_elementwise_work",
                "finalize_prob_cast": "declared_elementwise_cast_work",
                "init_routing": "declared_expansion_and_index_work",
                "finalize": "declared_weighted_combination_work",
            },
            "native_implementation_identity": "not_established",
            "unmodeled": [],
            "assumptions": [
                "per_expert_rows_are_an_equal_split_of_the_declared_local_"
                "assignment_total; the retained point descriptor declares the "
                "total and local bank but not the per-expert array",
            ],
        },
        "predicted_ms": report["duration_ms"],
        "predicted_total_ms": report["duration_ms"] * descriptor["repeats"],
        "resources": report["resources"],
        "execution": report["execution"],
        "protocol": report["protocol"],
        "assumptions": report["assumptions"],
    }


# ---------------------------------------------------------------------------
# Independent native observations (never a pricing input)
# ---------------------------------------------------------------------------


def _read_kernel_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if len(ordered) % 2 else (
        ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) / 2


def _attention_observation(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    path = Path(descriptor["source"]["capture_path"])
    csv_path = path / "kernel_details.csv"
    if not csv_path.is_file():
        return {"status": "missing_artifact", "path": str(csv_path)}
    rows = _read_kernel_rows(csv_path)
    repeats = int(descriptor["repeats"])
    by_name: dict[str, list[float]] = {}
    for row in rows:
        try:
            value = float(str(row["Duration(us)"]).strip())
        except (KeyError, ValueError):
            continue
        by_name.setdefault(str(row.get("Name", "")), []).append(value)
    if not by_name:
        return {"status": "empty_artifact", "path": str(csv_path)}
    roles = []
    for name, values in sorted(by_name.items()):
        per_call = len(values) / repeats
        roles.append({
            "name": name,
            "rows": len(values),
            "per_call_invocations": per_call,
            "median_us": _median(values),
            "per_call_us": _median(values) * per_call,
            "source_path": str(csv_path),
            "source_sha256": _sha256(csv_path),
        })
    return {
        "status": "observed",
        "scope": "per_standalone_native_call",
        "boundary": "additive_device_kernel_duration",
        "repeats": repeats,
        "roles": roles,
        "per_call_ms": sum(role["per_call_us"] for role in roles) / 1000.0,
        "used_in_prediction": False,
    }


_MOE_NAME_ROLES = (
    ("router_matmul", "aclnnMatmul_MatMulV3"),
    ("gating", "aclnnMoeGatingTopK"),
    ("gating_normalize_reduce", "aclnnReduceSum"),
    ("gating_normalize_div", "aclnnDiv"),
    ("init_routing", "aclnnMoeInitRoutingV3"),
    ("swiglu", "SwiGlu"),
    ("finalize", "aclnnMoeTokenUnpermute"),
)


def _moe_observation(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    source_path = descriptor["source"].get("descriptor_path")
    if not source_path:
        return {"status": "missing_descriptor",
                "missing_facts": ["retained_point_descriptor"]}
    point = json.loads(Path(source_path).read_bytes())
    tensors = descriptor.get("tensors") or {}
    tokens, top_k = tensors.get("tokens", 0), tensors.get("top_k", 0)
    hidden, intermediate = tensors.get("hidden", 0), tensors.get("intermediate", 0)
    capacity = tensors.get("capacity_rows", tokens * top_k)
    native_trace = point.get("native_trace") or {}
    summary = native_trace.get("per_kernel_summary") or {}
    roles: dict[str, dict[str, Any]] = {}
    gmm: list[tuple[str, dict[str, Any]]] = []
    if summary:
        for key, value in summary.items():
            if not isinstance(value, Mapping):
                continue
            name = key.split(" | ", 1)[0]
            shape = key.split(" | ", 1)[1] if " | " in key else ""
            if "aclnnGroupedMatmulV5" in name:
                gmm.append((shape, dict(value)))
                continue
            matched = None
            for role, token in _MOE_NAME_ROLES:
                if token in name:
                    matched = role
                    break
            if matched is None and name.endswith("CastAiCore_Cast"):
                if f"-> {tokens},{top_k}" in shape:
                    matched = "finalize_prob_cast"
                elif f"-> {tokens},{hidden}" in shape:
                    matched = "router_cast"
            if matched is None:
                continue
            entry = roles.setdefault(matched, {
                "role": matched, "kernels": [], "median_us": 0.0,
                "source_path": source_path,
            })
            entry["kernels"].append({"key": key, **dict(value)})
            entry["median_us"] += float(value.get("median_us", 0.0))
        # The two grouped GEMMs are distinguishable by their output width.
        for shape, value in gmm:
            role = ("gmm_gate_up" if f"-> {capacity},{2 * intermediate}" in shape
                    else "gmm_down")
            entry = roles.setdefault(role, {
                "role": role, "kernels": [], "median_us": 0.0,
                "source_path": source_path,
            })
            entry["kernels"].append({"key": shape, **value})
            entry["median_us"] += float(value.get("median_us", 0.0))
    else:
        # Earlier gate3 points retain one summary entry per native role instead
        # of the final per-kernel summary.  Ambiguous multiplicities stay null.
        for role, value in (native_trace.get("summary") or {}).items():
            if not isinstance(value, Mapping) or value.get("median_us") is None:
                continue
            normalized = "gating_normalize" if role == "gating_normalize" else role
            entry = roles.setdefault(normalized, {
                "role": normalized, "kernels": [], "median_us": 0.0,
                "source_path": source_path,
                "ambiguous_multiplicity": bool(value.get("ambiguous_multiplicity")),
            })
            entry["kernels"].append({"key": role, **dict(value)})
            entry["median_us"] += float(value["median_us"])
    if not roles:
        return {"status": "missing_native_roles", "source_path": source_path,
                "used_in_prediction": False}
    missing = [role for role in MOE_NATIVE_ROLES if role not in roles]
    return {
        "status": "observed" if not missing else "partial",
        "scope": "per_standalone_native_call",
        "boundary": "additive_native_role_median",
        "roles": [roles[role] for role in MOE_NATIVE_ROLES if role in roles],
        "missing_roles": missing,
        "per_call_ms": sum(entry["median_us"] for entry in roles.values()) / 1000.0,
        "used_in_prediction": False,
    }


def primitive_native_observation(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Extract the retained per-native-call duration boundary, if present.

    The observation is read from the exact capture/point artifacts and is
    never consulted by :func:`predict_primitive_workload`.
    """
    descriptor = primitive_workload_descriptor(row)
    if descriptor is None:
        return None
    if "attention" in str(row.get("capture_id", "")):
        return _attention_observation(descriptor)
    return _moe_observation(descriptor)


# ---------------------------------------------------------------------------
# Raw native-call artifact identity (never a timing)
# ---------------------------------------------------------------------------


def native_call_artifact(descriptor: Mapping[str, Any]) -> Path | None:
    """The exact raw kernel CSV consumed by the native-call observer."""
    raw = (descriptor.get("source") or {}).get("capture_path")
    if not raw:
        return None
    candidate = Path(str(raw)) / "kernel_details.csv"
    return candidate if candidate.is_file() else None


@lru_cache(maxsize=64)
def _artifact_sha256(path_text: str) -> str:
    return _sha256(Path(path_text))


def _boundary_fields(row: Mapping[str, Any], descriptor: Mapping[str, Any]):
    capture_id = str(row.get("capture_id") or "")
    artifact = native_call_artifact(descriptor)
    source_sha256 = _artifact_sha256(str(artifact)) if artifact is not None else None
    calls = descriptor.get("repeats")
    return capture_id, source_sha256, calls


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def predict_primitive_workload(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """Price one standalone native primitive workload, or report unsupported.

    ``None`` means the row is not a standalone primitive workload at all.
    An applicable primitive with missing/unsupported physics returns a record
    with ``status`` in ``{"unsupported", "unsupported_physics"}`` and explicit
    ``missing_facts``; it is never silently mapped onto a model body.
    """
    descriptor = primitive_workload_descriptor(row)
    if descriptor is None:
        return None
    capture_id, source_sha256, declared_calls = _boundary_fields(row, descriptor)

    def _unsupported(payload):
        return {
            "schema": SCHEMA,
            "status": "unsupported",
            "kind": descriptor.get("kind"),
            "capture_id": capture_id,
            "prediction_boundary": "native_calls",
            "boundary_basis": "elapsed_native_call_span_ms",
            "source_sha256": source_sha256,
            "repeats": declared_calls,
            "boundary_samples": [],
            "descriptor": descriptor,
            "unsupported": payload,
            "predicted_ms": None,
        }

    if not descriptor.get("applicable", True) or descriptor.get("unsupported"):
        return _unsupported(descriptor.get("unsupported"))
    kind = descriptor["kind"]
    try:
        if kind in {"fia_prefill", "fia_decode"}:
            priced = _price_fia(descriptor)
        elif kind in {"gdn_chunk_prefill", "causal_conv1d"}:
            priced = _price_gdn(descriptor)
        elif kind == "moe_native_chain":
            priced = _price_moe(descriptor)
        else:
            priced = {"status": "unsupported", "unsupported": {
                "reason": "primitive_composition_not_established",
                "missing_facts": ["declared_public_composition_program"],
            }}
    except (ValueError, KeyError, TypeError) as error:
        priced = {
            "status": "unsupported",
            "unsupported": {
                "reason": "primitive_physical_program_not_supported",
                "error": f"{type(error).__name__}: {error}",
                "missing_facts": ["supported_source_tensor_contract"],
            },
        }
    if priced.get("status") != "predicted":
        return _unsupported(priced.get("unsupported"))
    if type(declared_calls) is not int or declared_calls < 1:
        return _unsupported({
            "reason": "missing_declared_repetition_count",
            "missing_facts": ["producer_declared_native_call_count"],
        })
    repeats = int(declared_calls)
    result = {
        "schema": SCHEMA,
        "status": "predicted",
        "kind": kind,
        "capture_id": capture_id,
        "prediction_boundary": "native_calls",
        "boundary_basis": "elapsed_native_call_span_ms",
        "source_sha256": source_sha256,
        "phase": descriptor["phase"],
        "descriptor": descriptor,
        "hardware": descriptor["hardware"],
        "tensors": descriptor["tensors"],
        "repeats": repeats,
        "boundary_samples": [
            {"key": f"{capture_id}:call{index}",
             "boundary_ms": priced["predicted_ms"]}
            for index in range(repeats)
        ],
        "boundary_reuse_basis": (
            "producer_declared_repeated_calls_with_same_declared_tensors_and_"
            "warm_state; one simulated cost is reused per declared repetition"
        ),
        "predicted_ms": priced["predicted_ms"],
        "predicted_total_ms": priced["predicted_ms"] * repeats,
        "model": priced["model"],
        "composition": priced.get("composition"),
        "program": {
            "operators": priced.get("operators", []),
            "kernels": priced.get("kernels", []),
            "ledger": priced.get("ledger"),
            "coverage": priced.get("coverage"),
        },
        "resources": priced.get("resources", []),
        "execution": priced.get("execution"),
        "protocol": priced.get("protocol"),
        "assumptions": priced.get("assumptions", []),
    }
    result["native_observation"] = primitive_native_observation(row)
    result["diagnostics"] = _diagnostics(result)
    observation = result["native_observation"] or {}
    per_call = observation.get("per_call_ms")
    repeat_total = (float(per_call) * repeats) if per_call is not None else None
    tensors = descriptor.get("tensors") or {}
    row_scope_usable = (
        descriptor["phase"] == "prefill"
        and (descriptor["kind"] == "fia_prefill"
             and tensors.get("q_len") == tensors.get("kv_len")))
    result["comparison_scopes"] = {
        "per_native_call": {
            "predicted_ms": result["predicted_ms"],
            "observed_ms": per_call,
            "basis": "one declared native call",
        },
        "profiled_repeat_total": {
            "predicted_ms": result["predicted_total_ms"],
            "observed_ms": repeat_total,
            "basis": (f"{repeats} retained profiled invocations; the attention "
                      "prefill row observed_ms is this additive boundary"),
        },
        "row_forward_population": {
            "usable": row_scope_usable,
            "basis": (
                "not used: the row divides a three-call kernel sum by 32 synthetic "
                "decode forwards" if not row_scope_usable else
                "attention prefill rows declare forward_steps=1; their observed_ms "
                "is the three retained calls and matches profiled_repeat_total"
            ),
        },
    }
    return result


def _diagnostics(result: Mapping[str, Any]) -> dict[str, Any]:
    """Pair the finished prediction with the independent native observation.

    This runs strictly after pricing.  It exists so a reviewer can see the
    error boundary without any measured duration entering the physical model.
    """
    observation = result.get("native_observation") or {}
    predicted = {kernel["role"]: float(kernel["duration_ms"])
                 for kernel in result["program"]["kernels"]}
    single_prediction = (next(iter(predicted.values()))
                         if len(predicted) == 1 else None)
    observed_rows = observation.get("roles") or []
    per_role = []
    observed_total = 0.0
    for row in observed_rows:
        role = row.get("role") or row.get("name") or "unknown"
        observed = float(row.get("median_us", 0.0)) / 1000.0
        observed_total += observed
        prediction = predicted.get(role)
        if prediction is None and len(observed_rows) == 1:
            prediction = single_prediction
        per_role.append({
            "role": role,
            "predicted_ms": prediction,
            "observed_ms": observed,
            "relative_error": (None if prediction is None or not observed
                               else prediction / observed - 1.0),
        })
    scope = observation.get("scope")
    observed_scope_ms = observation.get("per_call_ms")
    return {
        "scope": scope or "unavailable",
        "prediction_used_observation": False,
        "predicted_ms": result["predicted_ms"],
        "observed_ms": observed_scope_ms,
        "relative_error": (
            None if not observed_scope_ms else
            float(result["predicted_ms"]) / float(observed_scope_ms) - 1.0),
        "per_role": per_role,
        "observed_role_sum_ms": observed_total,
        "observed_missing_roles": observation.get("missing_roles", []),
        "boundary_note": (
            "The predicted call excludes the row-carried forward population; "
            "the observation is one standalone native call, not 32 forwards."
        ),
    }


__all__ = [
    "SCHEMA",
    "DESCRIPTOR_SCHEMA",
    "SUITE",
    "MOE_NATIVE_ROLES",
    "PrimitiveWorkload",
    "primitive_workload_descriptor",
    "is_primitive_workload",
    "declared_primitive_workload",
    "primitive_native_observation",
    "predict_primitive_workload",
]
