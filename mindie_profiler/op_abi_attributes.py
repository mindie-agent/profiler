"""Type/range validation for every attribute that can reach a call plan.

[Role]
  Own the scalar/array attribute rules shared by captured C-ABI attributes and
  recipe-forwarded wrapper arguments (``quant_mode``, ``dst_type`` and friends),
  so a value that changes the invoked call is both validated and hashed.

[Invariants]
  * ``int`` rejects ``bool`` (except the two declared MoE flag aliases), all floats and values outside the declared range.
  * ``str`` rejects every non-string, so ``quant_mode=7`` is
    ``invalid_attribute_type`` even when the catalog carries the parameter only
    in the recipe keyword list.
  * Enum attributes are checked against the canonical string set; unknown
    values are blocking, never silently forwarded.
  * Fixed-length callable arrays (for example ``int[2] active_expert_range``)
    enforce declared allowed lengths, bounds and ordering before ``ready``.
  * A recipe attribute spec with no signature kind falls back to the catalog
    kind and remains validated.

[Timeouts & Locks]
  Pure in-memory work proportional to the attribute count.

[Side-Effect Policy]
  No I/O, device access or catalog imports.
"""

from __future__ import annotations

import math
from .repro_values import bounded_summary, bounded_mapping, bounded_sequence, validate_count_attributes
from .events import ProfilerUsageError
from collections.abc import Mapping, Sequence
from typing import Any

ATTR_ALIASES = {
    "head_num": ("num_heads", "num_query_heads"),
    "num_key_value_heads": ("num_kv_heads",),
    "scale_value": ("scale", "softmax_scale"),
    "keep_prob": ("keep_probability",),
    "pre_tokens": ("pre_tockens",),
    "next_tokens": ("next_tockens",),
    "actual_seq_q_len": ("actual_seq_lengths_q", "actual_seq_qlen", "actual_seq_lengths_query"),
    "actual_seq_kv_len": ("actual_seq_lengths_kv", "actual_seq_kvlen"),
    "actual_seq_lengths": ("actual_seq_lengths_q", "actual_seq_qlen"),
    "actual_seq_lengths_kv": ("actual_seq_lengths_kv", "actual_seq_kvlen"),
    "expert_tokens_count_or_cumsum_flag": ("expert_tokens_num_type",),
    "expert_tokens_before_capacity_flag": ("expert_tokens_num_flag",),
    "block_size": ("block_size",),
    "cache_mode": ("cache_mode",),
}
INT_RULES: dict[str, tuple[float, float]] = {
    "head_num": (1, 1 << 20), "num_heads": (1, 1 << 20),
    "num_key_value_heads": (0, 1 << 20), "expert_num": (1, 1 << 24),
    "num_experts": (1, 1 << 24), "k": (1, 1 << 20),
    "block_size": (1, 1 << 24), "sparse_mode": (0, 255),
    "inner_precise": (0, 255), "split_item": (0, 255),
    "group_type": (0, 255), "group_list_type": (0, 2),
    "expert_tokens_num_type": (0, 1), "pre_tokens": (0, 1 << 62),
    "next_tokens": (0, 1 << 62), "pre_tockens": (0, 1 << 62),
    "next_tockens": (0, 1 << 62), "dim": (-64, 64),
    "layout": (0, 64), "rotary_mode": (0, 64),
}
FLOAT_RULES: dict[str, tuple[float, float]] = {
    "scale_value": (0.0, 1e6), "scale": (0.0, 1e6),
    "keep_prob": (0.0, 1.0), "epsilon": (0.0, 1.0),
    "rmsnorm_epsilon_cq": (0.0, 1.0), "rmsnorm_epsilon_ckv": (0.0, 1.0),
    "softmax_scale": (0.0, 1e6),
}
STR_ENUMS = {
    "input_layout": {"TND", "BSH", "BSND", "BNSD", "BSND_NZ", "TND_NZ"},
    "layout_query": {"TND", "BSND", "BSH"},
    "layout_key": {"TND", "BSND", "BSH", "PA_BSND"},
    "cache_mode": {"PA_BSND", "PA_BNSD", "BSND"},
    "rotary_mode": {"half", "interleave", "quarter"},
}
ARRAY_LENGTH_RULES = {
    "active_expert_range": {"fixed_length": 2, "fixed_lengths": [2],
                            "allowed_lengths": [0, 2], "ordered": True,
                            "minimum": 0},
}
TENSOR_KINDS = frozenset({"tensor", "tensor_list"})
SCALAR_KINDS = frozenset({"int", "float", "str", "bool", "boolean"})


def validate_binding_attributes(binding):
    """Recheck supplied bindings, including unused declared scalar slots."""
    binding = bounded_mapping(binding, "binding")
    attrs = binding.get("attrs") or {}
    validate_count_attributes(attrs)
    specs = {spec["name"]: spec for spec in binding.get("attr_slots") or ()}
    for spec in recipe_forwarded_attr_specs(binding.get("repro") or {}):
        specs.setdefault(spec["name"], spec)
    for spec in specs.values():
        name = spec["name"]
        kind = spec.get("kind") or spec.get("cat") or "int"
        values = [attrs[name]] if name in attrs else []
        if kind in {"int", "int_array", "int_list"}:
            values.extend(spec[key] for key in ("value", "raw_value") if spec.get(key) is not None)
        for value in values:
            issue, _ = attr_issue(name, kind, value, spec)
            if issue:
                raise ProfilerUsageError(f"repro-op attribute invalid: {bounded_summary(issue)}")


def attr_issue(name: str, kind: str, value: Any,
               spec: Mapping[str, Any] | None = None
               ) -> tuple[dict[str, Any] | None, Any]:
    """Validate one scalar attribute and return an issue plus normalized value."""
    spec = bounded_mapping(spec, "attribute specification") if spec is not None else None
    if kind == "int":
        if isinstance(value, (str, bytes)):
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": f"expected int, got {bounded_summary(value)}"}, None
        if isinstance(value, bool):
            if name in {"expert_tokens_count_or_cumsum_flag",
                        "expert_tokens_num_type"}:
                return None, int(value)
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": "bool is not int", "value": bounded_summary(value)}, None
        if not isinstance(value, int):
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": f"expected int, got {bounded_summary(value)}"}, None
        number = value
        low, high = INT_RULES.get(name, (-(1 << 62), 1 << 62))
        if not low <= number <= high:
            return {"code": "invalid_attribute_range", "name": name,
                    "detail": f"{bounded_summary(number)} not in [{low}, {high}]"}, None
        try:
            validate_count_attributes({name: number})
        except ProfilerUsageError as exc:
            return {"code": "invalid_attribute_range", "name": name, "detail": str(exc)}, None
        return None, number
    if kind == "float":
        if isinstance(value, (str, bytes)):
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": f"expected float, got {bounded_summary(value)}"}, None
        if isinstance(value, bool):
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": "bool is not float"}, None
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": f"expected float, got {bounded_summary(value)}"}, None
        if not math.isfinite(number):
            return {"code": "invalid_attribute_range", "name": name,
                    "detail": "non-finite"}, None
        low, high = FLOAT_RULES.get(name, (-1e12, 1e12))
        if not low <= number <= high:
            return {"code": "invalid_attribute_range", "name": name,
                    "detail": f"{bounded_summary(number)} not in [{low}, {high}]"}, None
        return None, number
    if kind in {"bool", "boolean"}:
        if isinstance(value, bool):
            return None, value
        if isinstance(value, int) and value in (0, 1):
            return None, bool(value)
        return {"code": "invalid_attribute_type", "name": name,
                "detail": f"expected bool, got {bounded_summary(value)}"}, None
    if kind in {"int_array", "float_array", "array", "int_list", "str_list"}:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": f"expected array, got {bounded_summary(value)}"}, None
        try:
            items = bounded_sequence(value, "attribute array", 65536)
        except ProfilerUsageError:
            return {"code": "invalid_array_length", "name": name}, None
        if kind in {"int_array", "int_list"}:
            if any(isinstance(item, bool) or not isinstance(item, int)
                   for item in items):
                return {"code": "invalid_attribute_type", "name": name,
                        "detail": f"non-int array element in {bounded_summary(items)}"}, None
            if any(not 0 <= item <= 268_435_456 for item in items):
                return {"code": "invalid_array_range", "name": name,
                        "detail": bounded_summary(items)}, None
        metadata = dict(ARRAY_LENGTH_RULES.get(name) or {})
        metadata.update(spec or {})
        allowed = metadata.get("allowed_lengths")
        fixed = metadata.get("fixed_length")
        if fixed is None and metadata.get("fixed_lengths"):
            fixed = metadata["fixed_lengths"][0]
        if allowed is not None and len(items) not in allowed:
            return {"code": "invalid_array_length", "name": name,
                    "detail": f"length {len(items)} not in {allowed}"}, None
        if fixed is not None and items and len(items) != int(fixed):
            return {"code": "invalid_array_length", "name": name,
                    "detail": f"length {len(items)} != {fixed}"}, None
        minimum = metadata.get("minimum")
        if minimum is not None and any(item < int(minimum) for item in items):
            return {"code": "invalid_array_range", "name": name,
                    "detail": f"element below {minimum}: {bounded_summary(items)}"}, None
        if metadata.get("ordered") and any(
                right < left for left, right in zip(items, items[1:])):
            return {"code": "invalid_array_order", "name": name,
                    "detail": f"not non-decreasing: {bounded_summary(items)}"}, None
        return None, items
    if kind == "str":
        if not isinstance(value, str):
            return {"code": "invalid_attribute_type", "name": name,
                    "detail": f"expected str, got {bounded_summary(value)}"}, None
    text = str(value)
    enum = STR_ENUMS.get(name)
    if enum is not None and text not in enum:
        return {"code": "invalid_attribute_value", "name": name,
                "detail": f"{text!r} not in {sorted(enum)}"}, None
    return None, text


def bind_attrs(declared: Sequence[Mapping[str, Any]],
               captured: Mapping[str, Any],
               inputs: Sequence[Mapping[str, Any]]
               ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve, normalize and validate declared attributes against a capture."""
    declared, captured, inputs = bounded_sequence([declared, captured, inputs], "attribute sources")
    by_name = {record["name"]: record for record in inputs if record.get("present")}
    records, issues = [], []
    for spec in declared:
        name = spec["name"]
        value, source = None, "absent"
        if name in captured:
            value, source = captured[name], "captured_attr"
        else:
            for alias in ATTR_ALIASES.get(name, ()):
                if alias in captured:
                    value, source = captured[alias], f"captured_alias:{alias}"
                    break
        if value is None and name in by_name and by_name[name].get("values") is not None:
            value, source = by_name[name]["values"], "positional_values"
        if (isinstance(value, int) and not isinstance(value, bool)
                and name == "rotary_mode"):
            value = {1: "half", 2: "interleave",
                     3: "quarter"}.get(value, value)
        present = source != "absent" and value is not None
        kind = str(spec.get("kind") or spec.get("cat") or "int")
        normalized = value
        if present:
            issue, normalized = attr_issue(name, kind, value, spec)
            if issue is not None:
                issues.append(issue)
        records.append({"name": name, "kind": kind,
                        "required": bool(spec.get("required")),
                        "present": present, "value": normalized,
                        "raw_value": value, "source": source,
                        "cat": spec.get("cat")})
    return records, issues


def _parameter_kind(recipe: Mapping[str, Any], call_name: str,
                    spec: Mapping[str, Any]) -> str:
    params = (recipe.get("signature") or {}).get("params") or {}
    declared = (params.get(call_name) or {}).get("kind")
    if declared:
        return str(declared)
    return "int_array" if "array" in spec else "int"


def recipe_forwarded_attr_specs(recipe: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return every recipe attr/array that becomes a call-plan value.

    The returned ``kind`` is the callable schema kind, not the C storage kind,
    so a string wrapper parameter is validated as a string even if the catalog
    stores the same name as an integer scalar.
    """
    recipe = bounded_mapping(recipe, "recipe")
    specs: list[dict[str, Any]] = []
    signature = recipe.get("signature") or {}
    params = signature.get("params") or {}
    for call_name, raw in (recipe.get("keyword") or {}).items():
        if not isinstance(raw, Mapping):
            continue
        attr_name = raw.get("attr") or raw.get("array")
        if not attr_name:
            continue
        parameter = params.get(call_name) or {}
        required = not bool(raw.get("optional", not parameter.get("required", False)))
        spec = {"name": str(attr_name), "call_name": str(call_name),
                "kind": _parameter_kind(recipe, str(call_name), raw),
                "required": required, "cat": "attr"}
        for key in ("fixed_length", "fixed_lengths", "allowed_lengths",
                    "ordered", "minimum"):
            if key in raw:
                spec[key] = raw[key]
            elif key in parameter:
                spec[key] = parameter[key]
        specs.append(spec)
    for call_name in recipe.get("positional") or ():
        parameter = params.get(str(call_name)) or {}
        kind = str(parameter.get("kind") or "")
        if kind in {"int", "float", "str", "bool", "int_array", "float_array"}:
            specs.append({"name": str(call_name), "call_name": str(call_name),
                          "kind": kind, "required": bool(parameter.get("required")),
                          "cat": "attr"})
    return specs


__all__ = [
    "ARRAY_LENGTH_RULES", "ATTR_ALIASES", "FLOAT_RULES", "INT_RULES", "SCALAR_KINDS", "STR_ENUMS",
    "TENSOR_KINDS", "attr_issue", "bind_attrs", "recipe_forwarded_attr_specs",
]
