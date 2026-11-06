"""Validate complete retained native ABI slots for qualified responses.

[Role] Compare a caller-declared native ABI record and its explicit public-Engine
  tensor/service entities with the frozen complete slot contract before a
  qualified response rule is imported.
[Invariants] Required slots, absent optional slots, output slots and per-slot
  dtype/layout/shape relations come from the retained TRAIN native evidence.
  Missing or unexpectedly active slots, explicit conflicting dtypes/layouts or
  service identities are typed mismatches, never silent label replacement.
  Profile coefficients, domains and source rules are not changed here.
[Timeouts & Locks] Finite list comparison over one bounded ABI record; no I/O,
  locks, device work or dynamic registration.
[Side-Effect Policy] Pure validation; no caller mapping is mutated.
"""
from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json


class QualifiedCalibrationError(Exception):
    """A named profile or its declared input is visibly unusable."""


class QualifiedAbiMismatch(QualifiedCalibrationError):
    """The caller's actual native ABI does not agree with the frozen profile."""

    def __init__(self, code: str, **detail):
        self.code = code
        self.detail = detail
        suffix = ":" + json.dumps(detail, sort_keys=True) if detail else ""
        super().__init__(code + suffix)


_DTYPE_ALIASES = {
    "DT_BF16": "BF16", "BF16": "BF16", "TORCH.BFLOAT16": "BF16",
    "DT_FLOAT": "FLOAT", "FLOAT": "FLOAT", "FLOAT32": "FLOAT",
    "TORCH.FLOAT32": "FLOAT", "DT_INT8": "INT8", "INT8": "INT8",
    "DT_BOOL": "BOOL", "BOOL": "BOOL", "DT_INT64": "INT64", "INT64": "INT64",
    "DT_UNDEFINED": "UNDEFINED", "UNDEFINED": "UNDEFINED", "": "UNDEFINED",
    "NONE": "UNDEFINED",
}
_ABSENT_FORMATS = {"NULL", "UNDEFINED", ""}


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _dtype(value) -> str:
    return _DTYPE_ALIASES.get(str(value or "").upper(), str(value or "").upper())


def _format(value) -> str:
    text = str(value or "").upper()
    return "UNDEFINED" if text in _ABSENT_FORMATS else text


def _parse_shape(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]
    if isinstance(value, int):
        return [value]
    if not isinstance(value, str):
        raise QualifiedAbiMismatch("native_abi_shape_not_declared", value=repr(value))
    text = value.strip().strip('"')
    if not text:
        return []
    return [int(part) for part in text.split(",") if part.strip()]


def _shape_list(record, key):
    value = record.get(key)
    if isinstance(value, str):
        value = value.strip().strip('"').split(";")
    if not isinstance(value, (list, tuple)):
        raise QualifiedAbiMismatch("native_abi_shapes_not_declared:" + key)
    return [_parse_shape(item) for item in value]


def _slot_lists(record, kind):
    prefix = "input" if kind == "input" else "output"
    return (_shape_list(record, prefix + "_shapes"),
            list(record.get(prefix + "_dtypes") or ()),
            list(record.get(prefix + "_formats") or ()))


def _resolve(name, family, op):
    metadata = dict(op.metadata)
    shape = tuple(op.local_shape)
    if family in {"fused_attention", "attention_prefill_D128", "attention_prefill_D256"}:
        gqa = metadata.get("gqa_prefill") or metadata.get("gqa_decode") or {}
        if name == "q":
            return shape[0]
        if name == "hq":
            return shape[2]
        if name == "d":
            return shape[3]
        if name == "hkv":
            return int(dict(gqa).get("kv_heads", 1))
        if name == "kv_total":
            return shape[1]
        if name == "kv_native":
            return shape[1]
    if family == "dense_matmul":
        return {"m": shape[0], "n": shape[1], "k": shape[2]}.get(name)
    if family == "gdn_gating":
        return {"t": shape[0], "h": shape[1]}.get(name)
    if family == "ChunkFwdH":
        lengths = tuple(metadata.get("lengths", ()))
        tokens = sum(int(item) for item in lengths)
        heads = int(metadata.get("heads", shape[1]))
        chunks = int((metadata.get("chunks_per_sequence") or [tokens // 64])[0])
        return {
            "tokens": tokens, "heads": heads, "key_heads": int(metadata.get("key_heads", 1)),
            "d": 128, "chunks": chunks, "double_chunks": 2 * chunks,
            "heads_d2": heads * 128 * 128,
        }.get(name)
    return None


def _expected_shape(symbols, family, op):
    result = []
    for symbol in symbols:
        if isinstance(symbol, int):
            result.append(symbol)
            continue
        value = _resolve(symbol, family, op)
        if value is None:
            raise QualifiedAbiMismatch("native_abi_shape_symbol_unresolved", symbol=symbol)
        result.append(int(value))
    return result


def _validate_slot_set(contract, family, record, op, kind, source_rule_id):
    specs = contract.get(kind + "_slots_by_rule", {}).get(source_rule_id)
    if specs is None:
        specs = contract.get(kind + "_slots")
    if specs is None:
        return
    shapes, dtypes, formats = _slot_lists(record, kind)
    maximum = max(max(spec["indices"]) if "indices" in spec else spec["index"]
                  for spec in specs)
    expected_count = maximum + 1
    if len(shapes) < expected_count:
        raise QualifiedAbiMismatch("native_abi_slots_incomplete",
                                   kind=kind, declared=len(shapes), expected=expected_count)
    if len(shapes) > expected_count:
        raise QualifiedAbiMismatch("native_abi_unexpected_active_slots",
                                   kind=kind, declared=len(shapes), expected=expected_count)
    if len(dtypes) != expected_count or len(formats) != expected_count:
        raise QualifiedAbiMismatch("native_abi_slot_metadata_incomplete", kind=kind)
    for spec in specs:
        indices = spec["indices"] if "indices" in spec else [spec["index"]]
        for index in indices:
            shape = _parse_shape(shapes[index])
            actual_dtype, actual_format = _dtype(dtypes[index]), _format(formats[index])
            if spec.get("absent"):
                if (shape not in (None, [])
                        or actual_dtype != "UNDEFINED" or actual_format != "UNDEFINED"):
                    raise QualifiedAbiMismatch("native_abi_unexpected_optional_input",
                                               kind=kind, index=index,
                                               dtype=actual_dtype, format=actual_format)
                continue
            if spec.get("empty"):
                if shape not in (None, [], [0]):
                    raise QualifiedAbiMismatch("native_abi_output_shape_mismatch",
                                               kind=kind, index=index, declared=shape)
            else:
                expected = _expected_shape(spec["shape"], family, op)
                if shape != expected:
                    raise QualifiedAbiMismatch("native_abi_geometry_mismatch",
                                               kind=kind, index=index,
                                               declared=shape, expected=expected)
            if actual_dtype != _dtype(spec["dtype"]):
                raise QualifiedAbiMismatch("native_abi_input_contract_mismatch",
                                           kind=kind, index=index,
                                           declared=actual_dtype, expected=_dtype(spec["dtype"]))
            if actual_format != _format(spec["format"]):
                raise QualifiedAbiMismatch("native_abi_input_contract_mismatch",
                                           kind=kind, index=index,
                                           declared=actual_format, expected=_format(spec["format"]))


def _compare_fixed(expected, actual, path="abi"):
    if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
            raise QualifiedAbiMismatch("native_abi_field_type_mismatch", path=path)
        for key, value in expected.items():
            if key.startswith(("input_", "output_")):
                continue
            if key not in actual:
                raise QualifiedAbiMismatch("native_abi_field_missing", path=path + "." + key)
            _compare_fixed(value, actual[key], path + "." + key)
        return
    if isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)):
            raise QualifiedAbiMismatch("native_abi_field_type_mismatch", path=path)
        if list(actual[:len(expected)]) != list(expected):
            raise QualifiedAbiMismatch("native_abi_field_mismatch", path=path)
        return
    if expected == "unknown":
        if actual not in (None, "", "unknown"):
            raise QualifiedAbiMismatch("native_abi_identity_not_unknown", path=path)
        return
    if actual != expected:
        raise QualifiedAbiMismatch("native_abi_field_mismatch", path=path)


def _rule_geometry(rule, key):
    value = dict(rule.get("match", {})).get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise QualifiedAbiMismatch("native_abi_rule_geometry_not_integer", key=key)
    return value


def _check_geometry(contract, family, record, rule):
    expected = dict(contract.get("geometry", {}))
    actual = record.get("geometry")
    if not isinstance(actual, Mapping):
        raise QualifiedAbiMismatch("native_abi_geometry_not_declared", family=family)
    for key, value in expected.items():
        if isinstance(value, str) and value.startswith("rule_declared_"):
            if family == "ChunkFwdH":
                source = "metadata.heads" if key == "heads" else "metadata.key_heads"
            else:
                source = "metadata.gqa_prefill.query_heads" if key == "query_heads" else key
            wanted = _rule_geometry(rule, source)
        else:
            wanted = value
        if actual.get(key) != wanted:
            raise QualifiedAbiMismatch("native_abi_geometry_mismatch", family=family,
                                       axis=key, declared=actual.get(key), expected=wanted)


def _check_mask(contract, record, source_rule_id):
    expected = dict(contract.get("fixed", {}).get("control_flags", {})).get("mask")
    if expected is None:
        expected = dict(contract.get("mask_by_rule", {})).get(source_rule_id)
    actual = dict(record.get("control_flags") or {}).get("mask")
    if expected in {"none", "present"} and actual != expected:
        raise QualifiedAbiMismatch("native_abi_mask_mismatch",
                                   declared=actual, expected=expected)


def validate_native_abi(contract, family, record, op, rule, source_rule_id):
    """Validate one retained ABI record against its complete slot contract."""
    if not isinstance(record, Mapping):
        raise QualifiedAbiMismatch("actual_native_abi_not_declared", family=family)
    _compare_fixed(contract["fixed"], record, "abi." + family)
    _check_geometry(contract, family, record, rule)
    _validate_slot_set(contract, family, record, op, "input", source_rule_id)
    _validate_slot_set(contract, family, record, op, "output", source_rule_id)
    _check_mask(contract, record, source_rule_id)
    return {
        "family": family,
        "sha256": _digest(record),
        "api": record.get("api"),
        "kernel_name": record.get("kernel_name") or record.get("kernel_type"),
        "geometry": dict(record.get("geometry") or {}),
        "kv_view": dict(record.get("kv_view") or {}),
        "control_flags": dict(record.get("control_flags") or {}),
        "input_slots": len(_shape_list(record, "input_shapes")),
        "output_slots": len(_shape_list(record, "output_shapes")),
    }


def _check_view(view, contract, family, op):
    caller = dict(contract.get("caller_view") or {})
    if not caller or view is None:
        return
    if not isinstance(view, Mapping):
        raise QualifiedAbiMismatch("native_abi_caller_view_incompatible", family=family)
    for field in ("query_shape", "key_shape", "value_shape", "output_shape"):
        if field in view:
            declared = _parse_shape(view[field])
            expected = _expected_shape(caller[field], family, op)
            if declared != expected:
                raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                           family=family, field=field,
                                           declared=declared, expected=expected)
    for field in ("query_dtype", "key_dtype", "value_dtype", "output_dtype"):
        if field in view and _dtype(view[field]) != "BF16":
            raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                       family=family, field=field,
                                       declared=view[field], expected="bf16")
    if "logical_layout" in view and str(view["logical_layout"]).upper() not in {
            "TND", "CONTINUOUS_TND"}:
        raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                   family=family, field="logical_layout")
    if "kv_storage" in view and str(view["kv_storage"]).lower() not in {"dense", "contiguous"}:
        raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                   family=family, field="kv_storage")
    kind = str(view.get("kind") or "").lower()
    if (view.get("paged") is True or "paged" in kind or "segmented" in kind
            or view.get("kv_block_size") not in (None, 0)):
        raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                   family=family, field="paged")


def _check_implementation(implementation, contract, family):
    if implementation is None:
        return
    if not isinstance(implementation, Mapping):
        raise QualifiedAbiMismatch("native_abi_caller_service_identity_incompatible",
                                   family=family)
    storage = implementation.get("kv_storage")
    if storage is not None and str(storage).lower() not in {"dense", "contiguous"}:
        raise QualifiedAbiMismatch("native_abi_caller_service_identity_incompatible",
                                   family=family, field="kv_storage")
    if implementation.get("paged") is True:
        raise QualifiedAbiMismatch("native_abi_caller_service_identity_incompatible",
                                   family=family, field="paged")
    fixed = dict(contract.get("fixed", {}))
    for field in ("api", "kernel_name", "kernel_type"):
        if field in implementation and implementation[field] != fixed.get(field):
            raise QualifiedAbiMismatch("native_abi_caller_service_identity_incompatible",
                                       family=family, field=field)


def check_caller_native_entity(op, axes, family, contract):
    """Reconcile explicit caller tensor/service entities with the retained ABI."""
    if family not in {"fused_attention", "attention_prefill_D128", "attention_prefill_D256"}:
        return
    if family == "fused_attention" and op.layout not in {"contiguous", "ND"}:
        raise QualifiedAbiMismatch("native_abi_caller_layout_incompatible", family=family)
    metadata = dict(op.metadata)
    _check_view(metadata.get("attention_tensor_view"), contract, family, op)
    gqa = metadata.get("gqa_decode") or metadata.get("gqa_prefill") or {}
    gqa = dict(gqa) if isinstance(gqa, Mapping) else {}
    for field in ("query_dtype", "kv_dtype"):
        if field in gqa and _dtype(gqa[field]) != "BF16":
            raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                       family=family, field="metadata." + field)
    if gqa.get("paged") is True:
        raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                   family=family, field="metadata.paged")
    if gqa.get("attention_tensor_view") not in (None, "continuous_tnd"):
        raise QualifiedAbiMismatch("native_abi_caller_view_incompatible",
                                   family=family, field="metadata.attention_tensor_view")
    requests = tuple(dict(gqa).get("requests", ()))
    if requests and int(op.local_shape[1]) != int(op.local_shape[0]) + sum(
            int(request[1]) for request in requests):
        raise QualifiedAbiMismatch("native_abi_caller_sequence_partition_incompatible",
                                   family=family)
    identity = dict(axes.get("service_identity") or {})
    _check_implementation(identity.get("implementation"), contract, family)
    _check_implementation(axes.get("implementation"), contract, family)
    _check_implementation(metadata.get("implementation"), contract, family)
    nested = metadata.get("service_identity")
    if nested is not None:
        if not isinstance(nested, Mapping):
            raise QualifiedAbiMismatch("native_abi_caller_service_identity_incompatible",
                                       family=family)
        _check_implementation(nested.get("implementation"), contract, family)
