"""Deterministic mapping from mindie-model-structure/1 graphs to measured events (structure_mapping_helpers).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting deterministic mapping from mindie-model-structure/1 graphs to measured events.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from pathlib import Path
from .accounting import merge_intervals
from .events import ProfilerUsageError

SCHEMA = "mindie-profile-structure-mapping/1"

MAX_METADATA_BYTES = 32 * 1024 * 1024

def _snapshot_structure_carrier(value, name="structure metadata", _depth=0):
    if _depth > 64:
        raise ProfilerUsageError(f"{name} exceeds container nesting limit")
    if isinstance(value, Mapping):
        try:
            _ = len(value)
            out = {}
            for key in value:
                if type(key) is not str:
                    raise ProfilerUsageError(f"{name} keys must be plain strings")
                out[key] = _snapshot_structure_carrier(value[key], name, _depth + 1)
            return out
        except TimeoutError:
            raise
        except ProfilerUsageError:
            raise
        except (TypeError, ValueError, OverflowError) as exc:
            raise ProfilerUsageError(f"invalid {name} mapping protocol") from exc
    if isinstance(value, (list, tuple)):
        try:
            _ = len(value)
            return [_snapshot_structure_carrier(item, name, _depth + 1) for item in value]
        except TimeoutError:
            raise
        except ProfilerUsageError:
            raise
        except (TypeError, ValueError, OverflowError) as exc:
            raise ProfilerUsageError(f"invalid {name} sequence protocol") from exc
    return value

def read_metadata(value, schema):
    if isinstance(value, (str, Path)):
        path = Path(value)
        if path.stat().st_size > MAX_METADATA_BYTES:
            raise ProfilerUsageError(f"{path}: structure metadata exceeds 32 MiB")
        try:
            with path.open(encoding="utf-8") as stream:
                value = json.load(stream)
        except (ValueError, UnicodeError) as exc:
            raise ProfilerUsageError(f"{path}: invalid structure metadata: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ProfilerUsageError(f"expected {schema} metadata")
    if type(value) is not dict:
        value = _snapshot_structure_carrier(value, "structure metadata")
    else:
        # Normalize any nested non-dict Mapping carriers while keeping fast path on plain dict/list.
        value = _snapshot_structure_carrier(value, "structure metadata")
    if value.get("schema_version") != schema:
        raise ProfilerUsageError(f"expected {schema} metadata")
    return value

def _freeze(value):
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze(item)) for key, item in value.items()))
    return value

def _union_ns(intervals):
    return sum(right - left for left, right in merge_intervals(intervals))

_DTYPE_TOKENS = {
    "DT_BF16": "bf16", "DT_FLOAT16": "fp16", "DT_FLOAT": "fp32",
    "DT_INT8": "int8", "DT_INT32": "int32", "DT_UINT8": "uint8",
    "DT_UINT32": "uint32", "DT_BOOL": "bool", "DT_DOUBLE": "fp64",
}

def _event_signature(event):
    """Parsed shape/dtype lanes of a captured/predicted event, or None.

    Used only to stop a declared native call from aliasing an event whose
    tensor signature disagrees.  It is not occurrence evidence.
    """
    def shapes(text):
        rows = []
        for part in (text or "").split(";"):
            part = part.strip()
            if not part:
                continue
            try:
                rows.append(tuple(int(value) for value in part.split(",") if value.strip()))
            except ValueError:
                return None
        return tuple(rows)

    def dtypes(text):
        rows = []
        for part in (text or "").split(";"):
            part = part.strip()
            if not part:
                continue
            rows.append(_DTYPE_TOKENS.get(part, part.lower().removeprefix("dt_")))
        return tuple(rows)

    inputs, outputs = shapes(event.input_shapes), shapes(event.output_shapes)
    input_dtypes, output_dtypes = dtypes(event.input_dtypes), dtypes(event.output_dtypes)
    if inputs is None or outputs is None or not (inputs or outputs):
        return None
    if not (input_dtypes or output_dtypes):
        return None
    return (*inputs, *outputs), (*input_dtypes, *output_dtypes)

def _event_raw_identity(event):
    """Signed raw task identity used for one HCCL call's rank-local aliases."""
    locator = event.locator or {}
    global_task = locator.get(
        "global_task_id", locator.get("globalTaskId", locator.get("task_global_id")))
    connection = locator.get("connection_id", locator.get("connectionId"))
    if global_task is None or connection is None:
        return None
    return (str(event.rank_id), str(global_task), str(event.stream_id),
            str(event.task_id), str(connection), str(event.device_id),
            str(event.start_ns), str(event.end_ns))

def _event_inputs(event):
    """First-input role descriptor: dtype/shape of the tensor actually consumed."""
    raw_shapes = [part.strip() for part in (event.input_shapes or "").split(";")
                  if part.strip()]
    raw_dtypes = [part.strip() for part in (event.input_dtypes or "").split(";")
                  if part.strip()]
    if not raw_shapes or not raw_dtypes:
        return None
    try:
        shape = tuple(int(value) for value in raw_shapes[0].split(",") if value.strip())
    except ValueError:
        return None
    dtype = _DTYPE_TOKENS.get(raw_dtypes[0],
                              raw_dtypes[0].lower().removeprefix("dt_"))
    return shape, dtype

def _native_call_signature_match(binding, event):
    """True/False when an event descriptor exists, None when unavailable."""
    signature = _event_signature(event)
    if signature is None:
        return None
    shapes, dtypes = signature
    typed = binding.get("typed") or {}
    declared_dtype = typed.get("dtype")
    declared_shapes = [
        tuple(value) for value in (typed.get("shapes") or {}).values()
        if isinstance(value, (list, tuple)) and value
    ]
    if declared_dtype is not None and declared_dtype not in dtypes:
        return False
    if not declared_shapes:
        return False
    inputs = _event_inputs(event)
    if inputs is not None:
        input_shape, input_dtype = inputs
        if declared_dtype is not None and input_dtype != declared_dtype:
            return False
        # The first consumed tensor role must itself be the declared geometry;
        # an unrelated tensor that happens to share a shape cannot alias it.
        return any(declared == input_shape for declared in declared_shapes)
    # No input role descriptor: only exact shapes may correspond.
    return any(declared == observed
               for declared in declared_shapes for observed in shapes)

def _seal_digest(payload):
    digest = sha256()
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    for chunk in encoder.iterencode(payload):
        digest.update(chunk.encode("utf-8"))
    return "sha256:" + digest.hexdigest()

def _verify_graph_id(structure):
    declared = structure.get("graph_id")
    # Current exports exclude derived native-call evidence from the structural
    # identity.  Older callers sealed every key except source/graph_id; accept
    # that documented historical seal too instead of rejecting a valid bundle.
    current = _seal_digest({key: value for key, value in structure.items()
                            if key not in {"graph_id", "source", "native_calls",
                                           "native_call_coverage"}})
    if declared == current:
        return current
    legacy = _seal_digest({key: value for key, value in structure.items()
                           if key not in {"graph_id", "source"}})
    if declared == legacy:
        return declared
    raise ProfilerUsageError(
        "structure graph_id does not match its contents; re-export the structure")

def _task_key(rank, task):
    def text(key):
        return "" if task.get(key) is None else str(task[key])

    return (
        str(rank), text("device_id"), text("stream_id"), text("task_id"),
        task.get("start_ns"), task.get("end_ns"), text("global_task_id"),
    )

def _event_key(event):
    return (
        event.rank_id, event.device_id, event.stream_id, event.task_id,
        event.start_ns, event.end_ns,
        "" if event.locator.get("task_global_id") is None else str(event.locator["task_global_id"]),
    )

def _shared_kv_candidates(row, contract, candidates, targets):
    """Refine active SharedKV contracts using its optional compressed indices.

    The native ABI names input[4] ``cmp_sparse_indices`` (torch_binding.cpp,
    npu_sparse_attn_sharedkv_npu); dsa_v1.py supplies it for indexed compressed
    attention. Its presence and TND shape establish an index interface, not a
    compression ratio, context value, layer or captured implementation version.
    """
    if (row.kind != "SparseAttnSharedkv" or contract is None
            or contract[0] != "sparse_attention_active" or not candidates):
        return candidates, None
    from .native_tensor_abi import native_tensor_contract

    native = native_tensor_contract(row)
    if native is None or len(native[2]) != 14:
        return candidates, None
    inputs = native[2]
    indices = inputs[4]
    empty = ((), None, None)
    if inputs[3] != empty:
        return candidates, None
    if indices == empty:
        present, topk = False, None
    else:
        shape, dtype, layout = indices
        if (len(shape) != 3 or dtype != "int32" or layout != "ND"
                or shape[:2] != (inputs[0][0][0], inputs[1][0][-2])
                or shape[2] <= 0 or inputs[2] == empty):
            return candidates, None
        present, topk = True, shape[2]
    kept, unknown = [], 0
    for key in candidates:
        target = targets[key]
        metadata = target.get("operator", {}).get("metadata", {})
        geometry = metadata.get("indexed_attention_geometry", {})
        declared_indexed = target.get("structure", {}).get("indexer")
        declared_topk = geometry.get("topk")
        if (not isinstance(declared_indexed, bool)
                or declared_indexed and not isinstance(declared_topk, int)
                or declared_indexed is False and declared_topk not in (None, 0)):
            kept.append(key)
            unknown += 1
        elif declared_indexed == present and (not present or declared_topk == topk):
            kept.append(key)
    return kept, {
        "basis": "observed_optional_index_descriptor",
        "native_operator_type": row.kind,
        "input_slot": 4, "input_name": "cmp_sparse_indices",
        "observed_descriptor": indices,
        "compared": ["compressed_index_presence", "index_token_and_head_axes",
                     "index_topk_dimension", "index_dtype_and_format"],
        "candidate_count_before": len(candidates),
        "candidate_count_after": len(kept),
        "unknown_declaration_candidates_retained": unknown,
        "occurrence_binding_implied": False,
        "not_inferred": ["compression_ratio", "context", "phase", "layer", "step",
                         "index_values", "capture_binary_identity"],
    }
