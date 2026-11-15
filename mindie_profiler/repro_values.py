"""Captured-value validation and allocation projection for one-op reproducers.

[Role]
  Turn a bound occurrence's input/output records into exact allocation specs
  while enforcing the strict ``len(flat_values) == prod(shape)`` captured-value
  contract, dtype-compatible numeric leaves and element-level presence for
  tensor-list items.

[Invariants]
  * A captured value vector is installed only when its recursively flattened
    length equals the allocated numel and every leaf is representable in the
    exact destination dtype; otherwise the occurrence is blocked before ``ready``.
  * Absent, missing, invalid or scalar tensor-list members are never allocated.
  * Nested captured values have no privilege; fidelity labels derive from specs.

[Timeouts & Locks]
  Pure in-memory work proportional to the captured element count.

[Side-Effect Policy]
  No I/O, device access or torch import.
"""

from __future__ import annotations

from .events import ProfilerUsageError

import math
import json
from pathlib import Path
from typing import Any, Mapping

_METADATA_ROLES = {"seq_lens", "block_table", "group_list", "index"}
_FLOAT_DTYPES = {
    "bfloat16", "float16", "float32", "float64", "float8_e4m3fn",
    "float8_e5m2", "fp16", "fp32", "fp64", "bf16", "fp8_e4m3",
    "fp8_e4m3fn", "fp8_e5m2",
}
_INT_DTYPES = {
    "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32",
    "uint64", "uint1", "fp8_e8m0",
}
_BOOL_DTYPES = {"bool"}
_INT_RANGES = {
    "uint1": (0, 1),
    "int8": (-128, 127), "uint8": (0, 255),
    "int16": (-32768, 32767), "uint16": (0, 65535),
    "int32": (-(1 << 31), (1 << 31) - 1),
    "uint32": (0, (1 << 32) - 1),
    "int64": (-(1 << 63), (1 << 63) - 1),
    "uint64": (0, (1 << 64) - 1),
    "fp8_e8m0": (0, 255),
}
_FLOAT_MAX = {
    "float16": 65504.0, "fp16": 65504.0,
    "bfloat16": 3.3895313892515355e38, "bf16": 3.3895313892515355e38,
    "float32": 3.4028234663852886e38, "fp32": 3.4028234663852886e38,
    "float64": float.fromhex("0x1.fffffffffffffp+1023"), "fp64":
        float.fromhex("0x1.fffffffffffffp+1023"),
    "float8_e4m3fn": 448.0, "fp8_e4m3": 448.0, "fp8_e4m3fn": 448.0,
    "float8_e5m2": 57344.0, "fp8_e5m2": 57344.0,
}


def bounded_count(value, name, low=0, high=1_000_000):
    """Integer-only resource budget, checked before range/allocation/conversion.

    Defaults cap host metadata and loops at one million items. Callers use
    smaller topology limits or explicit byte/element limits; never clamp input.
    Diagnostics omit the value so even a 5001-digit integer is safe to reject.
    """
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ProfilerUsageError(f"{name} must be an integer in [{low}, {high}]")
    return value


def bounded_container_len(value, maximum=1_000_000):
    """Check declared size before accessing members, preserving caller timeouts."""
    try:
        length = len(value)
    except TimeoutError:
        raise
    except (OverflowError, TypeError, ValueError) as exc:
        raise ProfilerUsageError("container length is not a bounded integer") from exc
    if length > maximum:
        raise ProfilerUsageError(f"container exceeds {maximum} members")
    return length


def _bounded_members(value, budget, maximum=1_000_000, *, string_keys=False,
                     defer_lookup=False):
    """Charge each yielded entry, including repeated references, before descent."""
    bounded_container_len(value, maximum)
    limit = bounded_container_len.__defaults__[0]
    mapping = isinstance(value, Mapping)
    lookup = mapping and type(value) is not dict
    try:
        if not mapping:
            for count, item in enumerate(value, 1):
                budget[0] += 1
                if count > maximum:
                    raise ProfilerUsageError(f"container exceeds {maximum} members")
                if budget[0] > limit:
                    raise ProfilerUsageError("container traversal exceeds one million members")
                yield None, item
            return
        if not lookup:
            for count, (key, item) in enumerate(value.items(), 1):
                if string_keys and type(key) is not str:
                    raise ProfilerUsageError("mapping keys must be plain strings")
                budget[0] += 1
                if count > maximum:
                    raise ProfilerUsageError(f"container exceeds {maximum} members")
                if budget[0] > limit:
                    raise ProfilerUsageError("container traversal exceeds one million members")
                yield key, item
            return
        for count, key in enumerate(value, 1):
            if string_keys and type(key) is not str:
                raise ProfilerUsageError("mapping keys must be plain strings")
            budget[0] += 1
            if count > maximum:
                raise ProfilerUsageError(f"container exceeds {maximum} members")
            if budget[0] > limit:
                raise ProfilerUsageError("container traversal exceeds one million members")
            item = None
            if not defer_lookup:
                if not string_keys and type(key) is not str:
                    for _ in _container_nodes(key, _budget=budget, _leaves=False):
                        pass
                item = value[key]
            yield key, item
    except TimeoutError:
        raise
    except TypeError as exc:
        raise ProfilerUsageError("invalid container member protocol") from exc


def bounded_sequence(value, name, high=1_000_000):
    """Snapshot an array with bounded declared size, depth and total members."""
    if not isinstance(value, (list, tuple)):
        raise ProfilerUsageError(f"{name} must be an array with at most {high} items")
    bounded_container_len(value, high)
    return _copy_container(value, 0, [0], False, high)


def bounded_mapping(value, name="mapping", high=1_000_000):
    """Snapshot an object, rejecting non-string keys before lookup or hashing."""
    if not isinstance(value, Mapping):
        raise ProfilerUsageError(f"{name} must be an object")
    bounded_container_len(value, high)
    return _copy_container(value, 0, [0], False, high)


def bounded_shape(shape, high=268_435_456):
    """At most 32 dimensions and 2**28 tensor elements; metadata uses 10**6."""
    total = 1
    for dim in bounded_sequence(shape, "shape", 32):
        total *= bounded_count(dim, "shape dimension", 0, high)
        bounded_count(total, "shape elements", 0, high)
    return total


def bounded_summary(value, depth=0, _budget=None):
    """Bound diagnostics before decimal rendering or recursive container repr."""
    if type(value) is int and value.bit_length() > 4096:
        return f"<int with {value.bit_length()} bits>"
    if type(value) in (str, bytes):
        return repr(value[:96])
    if isinstance(value, (list, tuple, Mapping)):
        if _budget is None:
            _budget = [0]
        try:
            length = bounded_container_len(value)
        except ProfilerUsageError:
            return "<container exceeds size limit>"
        if depth >= 2:
            return f"<{type(value).__name__} length {length}>"
        mapping, parts = isinstance(value, Mapping), []
        try:
            for key, item in _bounded_members(value, _budget):
                parts.append((bounded_summary(key, depth + 1) + ": " if mapping else "")
                             + bounded_summary(item, depth + 1, _budget))
                if len(parts) == 4:
                    break
        except ProfilerUsageError:
            return "<container exceeds size limit>"
        return ("{" if mapping else "[") + ", ".join(parts) + (
            ", ..." if length > 4 or length < len(parts) else "") + ("}" if mapping else "]")
    if value is None or type(value) in (int, float, bool):
        return repr(value)[:120]
    return f"<{type(value).__name__}>"


def diagnostic_value(value, depth=0, _budget=None):
    """Project diagnostic fields without retaining unsafe numeric/container leaves."""
    if _budget is None:
        _budget = [0]
    if value is None or type(value) is bool:
        return value
    if type(value) is str and len(value) <= 160:
        return value
    if type(value) is int and abs(value) <= (1 << 62):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, (Mapping, list, tuple)) and depth < 4:
        try:
            bounded_container_len(value, 32)
        except ProfilerUsageError:
            return bounded_summary(value)
        result = {} if isinstance(value, Mapping) else []
        try:
            for key, item in _bounded_members(value, _budget, 32):
                if isinstance(result, dict):
                    key = key if type(key) is str and len(key) <= 160 else bounded_summary(key)
                    result[key] = diagnostic_value(item, depth + 1, _budget)
                else:
                    result.append(diagnostic_value(item, depth + 1, _budget))
        except ProfilerUsageError:
            return "<container exceeds diagnostic limit>"
        return result
    return bounded_summary(value)


def _container_nodes(value, maximum=64, _budget=None, _leaves=True):
    """Walk at most one million entries without deduplicating shared subtrees."""
    budget = [0] if _budget is None else _budget
    limit = bounded_container_len.__defaults__[0]
    containers = (list, tuple, dict, set, frozenset, Mapping)
    scalars = (type(None), int, str, float, bool)

    def children(container):
        if not isinstance(container, Mapping):
            bounded_container_len(container)
            try:
                for count, item in enumerate(container, 1):
                    budget[0] += 1
                    if count > limit:
                        raise ProfilerUsageError(f"container exceeds {limit} members")
                    if budget[0] > limit:
                        raise ProfilerUsageError("container traversal exceeds one million members")
                    if type(item) not in scalars or (_leaves and type(item) is int):
                        yield item
            except TimeoutError:
                raise
            except TypeError as exc:
                raise ProfilerUsageError("invalid container member protocol") from exc
            return
        bounded_container_len(container)
        lookup = type(container) is not dict
        try:
            if not lookup:
                for count, (key, item) in enumerate(container.items(), 1):
                    budget[0] += 1
                    if count > limit:
                        raise ProfilerUsageError(f"container exceeds {limit} members")
                    if budget[0] > limit:
                        raise ProfilerUsageError("container traversal exceeds one million members")
                    if type(key) not in scalars or (_leaves and type(key) is int):
                        yield key
                    if type(item) not in scalars or (_leaves and type(item) is int):
                        yield item
                return
            for count, key in enumerate(container, 1):
                budget[0] += 1
                if count > limit:
                    raise ProfilerUsageError(f"container exceeds {limit} members")
                if budget[0] > limit:
                    raise ProfilerUsageError("container traversal exceeds one million members")
                # Resuming after the key's entire subtree is checked permits lookup.
                if type(key) not in scalars or (_leaves and type(key) is int):
                    yield key
                item = container[key]
                if type(item) not in scalars or (_leaves and type(item) is int):
                    yield item
        except TimeoutError:
            raise
        except TypeError as exc:
            raise ProfilerUsageError("invalid container member protocol") from exc

    stack = [(iter((value,)), 0)]
    while stack:
        iterator, depth = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            continue
        if _leaves:
            yield item
        if type(item) in scalars or not isinstance(item, containers):
            continue
        if depth >= maximum:
            raise ProfilerUsageError("input container nesting exceeds 64 levels")
        if type(item) in (list, tuple):
            length = bounded_container_len(item)
            if all(type(x) in scalars or not isinstance(x, containers) for x in item):
                if not _leaves:
                    budget[0] += length
                    if budget[0] > limit:
                        raise ProfilerUsageError("container traversal exceeds one million members")
                    continue
                if budget[0] + length <= limit:
                    for x in item:
                        if isinstance(x, int):
                            yield x
                    budget[0] += length
                    continue
        stack.append((children(item), depth + 1))


def validate_container_depth(value, maximum=64):
    """Bound declared sizes, nesting and cumulative visits, including DAGs."""
    for _ in _container_nodes(value, maximum, _leaves=False):
        pass


def decode_bounded_json(text):
    """Check nesting before the decoder consumes Python's recursion budget."""
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > 64:
                raise ProfilerUsageError("JSON nesting exceeds 64 levels")
        elif char in "]}":
            depth -= 1
    try:
        return json.loads(text)
    except RecursionError as exc:
        raise ProfilerUsageError("JSON nesting exceeds the decoding limit") from exc


def binding_issues(binding):
    """Missing diagnostics are empty; declared diagnostics must be an array."""
    issues = binding.get("issues")
    return () if issues is None else bounded_sequence(issues, "issues")


def load_cli_json(path):
    """Translate malformed, too-deep or oversized-decimal JSON at ingress."""
    try:
        return decode_bounded_json(Path(path).read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ProfilerUsageError("invalid JSON input: " + bounded_summary(str(exc))) from exc


def validate_json_integers(value):
    """Reject unbounded integer leaves before provenance serialization."""
    for item in _container_nodes(value):
        if isinstance(item, int) and item.bit_length() > 4096:
            raise ProfilerUsageError("provenance integer exceeds the bounded serialization limit")


def validate_count_attributes(attrs):
    """Validate declared extents, list spans and index arrays without coercion."""
    attrs = bounded_mapping(attrs, "attributes")
    limits = {"batch_size": (0, 65536), "num_seqs": (0, 65536),
              "head_num": (1, 1 << 20), "num_heads": (1, 1 << 20),
              "num_query_heads": (1, 1 << 20), "k": (1, 1 << 20),
              "expert_num": (1, 1 << 24), "num_experts": (1, 1 << 24),
              "block_size": (1, 1 << 24), "pre_tokens": (0, 1 << 62),
              "next_tokens": (0, 1 << 62), "pre_tockens": (0, 1 << 62),
              "next_tockens": (0, 1 << 62), "pad_slot_id": (0, 268_435_456),
              "null_block_id": (0, 268_435_456), "offset": (0, 268_435_456)}
    arrays = {"active_expert_range", "prefix", "actual_shared_prefix_len"}
    extents = {"bucket_tokens", "effective_tokens", "physical_bucket_tokens",
               "seq_extent", "shared_prefix_pages", "expert_capacity"}
    for name, value in attrs.items():
        if value is None:
            continue
        if name == "tensor_list_lengths":
            if not isinstance(value, dict):
                raise ProfilerUsageError("tensor_list_lengths must be an object")
            for length in value.values():
                bounded_count(length, "tensor list span", 0, 1024)
        elif name in arrays or name.startswith("actual_seq"):
            for item in bounded_sequence(value, "count/index array", 65536):
                bounded_count(item, "count/index element", 0, 268_435_456)
        elif (name in limits or name in extents or name.startswith("num_")
              or name.endswith(("_len", "_count", "_size", "_num", "_index"))):
            low, high = limits.get(name, (0, 268_435_456))
            bounded_count(value, name, low, high)


def validate_binding_counts(binding):
    """Check caller counts before any binding diagnostic or provenance hash."""
    binding = bounded_mapping(binding, "binding")
    validate_count_attributes(binding.get("attrs") or {})
    for field in ("inputs", "outputs"):
        for record in bounded_sequence(binding.get(field, ()), field, 1024):
            storage_record(record)
            key = str(record.get("name")) + "_len"
            if record.get("cat") == "tensor_list" and key in (binding.get("attrs") or {}):
                bounded_count(binding["attrs"][key], key, 0, 1024)
            items = record.get("items", ()) if record.get("cat") == "tensor_list" else [record]
            for item in bounded_sequence(items, "tensor list", 1024):
                storage_record(item)
                if item.get("shape") is not None:
                    bounded_shape(item["shape"])
def repro_count_options(warmup, iters, flush_mb, l2_bytes):
    """At most 10**6 iterations, 4096 MiB flush storage, and 2**40 L2 bytes."""
    bounded_count(warmup, "warmup")
    bounded_count(iters, "iters", 5)
    bounded_count(flush_mb, "flush_mb", 0, 4096)
    if l2_bytes is not None:
        bounded_count(l2_bytes, "l2_bytes", 0, 1 << 40)


def jsonable(value: Any) -> Any:
    if isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (list, tuple)):
        try:
            value = bounded_sequence(value, "attribute array", 65536)
        except ProfilerUsageError:
            return None
        out = []
        for item in value:
            converted = jsonable(item)
            if converted is None and item is not None:
                return None
            out.append(converted)
        return out
    return None


def flatten_values(value: Any) -> list[Any] | None:
    """Recursively flatten a captured value, rejecting malformed leaves."""
    if isinstance(value, bool):
        return [value]
    if isinstance(value, (int, float)):
        return [value]
    if isinstance(value, (list, tuple)):
        out: list[Any] = []
        for item in bounded_sequence(value, "captured values"):
            nested = flatten_values(item)
            if nested is None:
                return None
            bounded_count(len(out) + len(nested), "flattened captured values")
            out.extend(nested)
        return out
    return None


def _dtype_name(dtype: Any) -> str:
    name = str(dtype or "").lower().strip()
    return name[3:] if name.startswith("dt_") else name


def _dtype_family(dtype: Any) -> str:
    name = _dtype_name(dtype)
    if name in _BOOL_DTYPES:
        return "bool"
    if name in _INT_DTYPES:
        return "int"
    if name in _FLOAT_DTYPES:
        return "float"
    return "unknown"


def _value_repr(value: Any) -> str:
    return bounded_summary(value)[:120]


def validate_captured_values(shape: list[int], dtype: Any, values: Any
                             ) -> tuple[list[Any] | None, list[dict[str, Any]]]:
    """Validate a captured value against the exact allocated geometry."""
    problems: list[dict[str, Any]] = []
    validate_container_depth(values)
    bounded_shape(shape)
    expected = 1
    for dim in shape or [1]:
        expected *= int(dim)
    flat = flatten_values(values)
    if flat is None:
        return None, [{"code": "captured_value_invalid", "values": _value_repr(values)}]
    if len(flat) != expected:
        return None, [{"code": "captured_value_numel_mismatch",
                       "shape": list(shape), "expected": expected,
                       "captured": len(flat)}]
    family = _dtype_family(dtype)
    name = _dtype_name(dtype)
    if family == "unknown":
        return None, [{"code": f"unsupported_value_dtype:{name or '<none>'}",
                       "dtype": dtype,
                       "detail": "no explicit value/encoding contract"}]
    for index, item in enumerate(flat):
        mismatch = {"code": "captured_value_type_mismatch", "index": index,
                    "dtype": dtype, "value": _value_repr(item)}
        if family == "bool":
            if not isinstance(item, bool):
                problems.append(mismatch)
            continue
        if isinstance(item, bool):
            problems.append(mismatch)
            continue
        if family == "int":
            if not isinstance(item, int):
                problems.append(mismatch)
                continue
            low, high = _INT_RANGES.get(name, (-(1 << 63), (1 << 64) - 1))
            if not low <= item <= high:
                problems.append({"code": "captured_value_out_of_range",
                                 "index": index, "dtype": dtype,
                                 "value": _value_repr(item)})
            continue
        if family == "float":
            limit = _FLOAT_MAX.get(name)
            # Compare integers exactly before conversion, including float64's
            # rounding boundary. Validation need not convert accepted integers.
            if isinstance(item, int):
                if limit is not None and abs(item) > limit:
                    problems.append({"code": "captured_value_out_of_range",
                                     "index": index, "dtype": dtype,
                                     "value": _value_repr(item), "max_finite": limit})
                continue
            if not isinstance(item, float) or not math.isfinite(item):
                problems.append({"code": "captured_value_non_finite",
                                 "index": index, "value": _value_repr(item)})
                continue
            if limit is not None and abs(item) > limit:
                problems.append({"code": "captured_value_out_of_range",
                                 "index": index, "dtype": dtype,
                                 "value": repr(item), "max_finite": limit})
            continue
        if not isinstance(item, (int, float)):
            problems.append(mismatch)
    return (None if problems else flat), problems


def _copy_container(value, depth, budget, literal, maximum=1_000_000):
    """Copy containers with one cumulative budget; optionally require JSON leaves."""
    fast = (type(None), bool, str)
    scalars = (type(None), int, str, float, bool)
    val_type = type(value)
    if val_type in fast:
        return value
    if val_type is int:
        if not literal or value.bit_length() <= 4096:
            return value
        raise ProfilerUsageError("literal integer exceeds the bounded serialization limit")
    if val_type is float:
        if not literal or math.isfinite(value):
            return value
        raise ProfilerUsageError("literal numbers must be finite")
    if isinstance(value, (list, tuple, dict, Mapping)):
        if depth >= 64:
            raise ProfilerUsageError("literal container nesting exceeds 64 levels")
        if val_type in (list, tuple):
            length = bounded_container_len(value, maximum)
            limit = bounded_container_len.__defaults__[0]
            if budget[0] + length <= limit and (
                not literal and all(type(x) in scalars or not isinstance(x, (list, tuple, dict, Mapping)) for x in value)
                or literal and all(type(x) in fast for x in value)
            ):
                budget[0] += length
                return list(value)
        if val_type is dict:
            bounded_container_len(value, maximum)
            limit, result = bounded_container_len.__defaults__[0], {}
            for key, item in value.items():
                if type(key) is not str:
                    raise ProfilerUsageError("mapping keys must be plain strings")
                budget[0] += 1
                if budget[0] > limit:
                    raise ProfilerUsageError("container traversal exceeds one million members")
                result[key] = item if type(item) in fast else _copy_container(item, depth + 1, budget, literal)
            return result
        if isinstance(value, Mapping):
            bounded_container_len(value, maximum)
            limit, result = bounded_container_len.__defaults__[0], {}
            try:
                for count, key in enumerate(value, 1):
                    if type(key) is not str:
                        raise ProfilerUsageError("mapping keys must be plain strings")
                    budget[0] += 1
                    if count > maximum or budget[0] > limit:
                        raise ProfilerUsageError(f"container exceeds {maximum} members" if count > maximum else "container traversal exceeds one million members")
                    item = value[key]
                    result[key] = item if type(item) in fast else _copy_container(item, depth + 1, budget, literal)
            except TimeoutError:
                raise
            except TypeError as exc:
                raise ProfilerUsageError("invalid container member protocol") from exc
            return result
        bounded_container_len(value, maximum)
        limit, seq_out = bounded_container_len.__defaults__[0], []
        for count, item in enumerate(value, 1):
            budget[0] += 1
            if count > maximum or budget[0] > limit:
                raise ProfilerUsageError(f"container exceeds {maximum} members" if count > maximum else "container traversal exceeds one million members")
            seq_out.append(item if type(item) in fast else _copy_container(item, depth + 1, budget, literal))
        return seq_out
    if not literal:
        return value
    raise ProfilerUsageError("literal value must be a JSON primitive, object or array")


def literal_value(value, depth=0):
    """Copy exact JSON leaves and string keys into standalone built-in literals."""
    return _copy_container(value, depth, [0], True)


def storage_mapping(value):
    """Absent storage is empty; all members use the literal_value JSON domain."""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProfilerUsageError("storage must be an object")
    value = literal_value(value)
    for key in ("storage_id", "storage_object_id"):
        if isinstance(value.get(key), bool):
            raise ProfilerUsageError("storage ID must not be a boolean")
    for key in ("storage_offset", "offset", "storage_bytes"):
        if value.get(key) is not None:
            bounded_count(value[key], key, 0, 1 << 40)
    for key in ("stride", "strides"):
        if value.get(key) is not None:
            for stride in bounded_sequence(value[key], key, 32):
                bounded_count(stride, "stride", 0, 1 << 40)
    return value


def storage_record(item: dict[str, Any]) -> dict[str, Any]:
    """Validate nested and direct descriptors, even shadowed direct members."""
    item = bounded_mapping(item, "storage descriptor")
    keys = {"stride", "strides", "storage_offset", "storage_bytes", "storage_id",
            "offset", "storage_object_id"}
    merged = storage_mapping({key: item[key] for key in keys if key in item})
    declared = storage_mapping(item.get("storage"))
    merged.update({key: value for key, value in declared.items() if key in keys})
    return merged


def slot_allocations(binding: dict[str, Any]
                     ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validate_binding_counts(binding)
    allocations: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    for direction, field in (("input", "inputs"), ("output", "outputs")):
        for record in bounded_sequence(binding.get(field, ()), field, 1024):
            if not record.get("present") or record.get("state") == "alias":
                continue
            items = (record.get("items")
                     if record.get("cat") == "tensor_list" else [record])
            for list_index, item in enumerate(bounded_sequence(items, "tensor list", 1024)):
                context = {"name": record.get("name"), "direction": direction}
                if record.get("cat") == "tensor_list":
                    context["list_index"] = list_index
                if not item.get("present") or item.get("state") in {
                        "absent", "undefined", "missing", "invalid", "scalar"}:
                    problems.append({"code": "allocation_absent_tensor", **context,
                                     "state": item.get("state")})
                    continue
                shape = item.get("shape")
                dtype = item.get("dtype")
                layout = item.get("layout")
                if shape is None or dtype is None:
                    problems.append({"code": "allocation_geometry_unknown", **context})
                    continue
                if not layout or not isinstance(layout, str):
                    problems.append({"code": "allocation_layout_unknown", **context,
                                     "layout": layout})
                    continue
                bounded_shape(shape)
                values = None
                raw_values = item.get("values")
                if raw_values is not None:
                    values, value_problems = validate_captured_values(
                        list(shape), dtype, raw_values)
                    if value_problems:
                        problems.extend({**problem, **context}
                                        for problem in value_problems)
                        continue
                allocation = {
                    "name": record["name"], "direction": direction,
                    "list_index": (len([entry for entry in allocations
                                        if entry.get("name") == record["name"]])
                                   if record.get("cat") == "tensor_list" else None),
                    "role": record.get("role"), "shape": [int(dim) for dim in shape],
                    "dtype": dtype, "layout": layout,
                    "state": item.get("state"),
                    "values": values,
                    "present": True,
                    "storage": storage_record(item),
                }
                if record.get("cat") == "tensor_list":
                    allocation["tensor_list"] = record["name"]
                allocations.append(allocation)
    return allocations, problems


def fidelity(allocations: list[dict[str, Any]]) -> str:
    """Honest fidelity label for the input tensor values actually installed."""
    inputs = [spec for spec in allocations
              if spec.get("direction") == "input" and spec.get("state") != "alias"]
    if inputs and all(spec.get("values") is not None for spec in inputs):
        return "value_captured"
    captured = [spec for spec in inputs if spec.get("values") is not None]
    if any(spec.get("role") not in _METADATA_ROLES for spec in captured):
        return "shape_and_values_captured"
    if captured:
        return "metadata_captured_activations_synthetic"
    return "descriptor_synthetic"


__all__ = [
    "fidelity", "flatten_values", "jsonable", "slot_allocations",
    "storage_record", "validate_captured_values",
]
