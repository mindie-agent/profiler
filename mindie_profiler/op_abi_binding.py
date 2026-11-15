"""Lossless positional binding of captured operator slots onto a pinned ABI.

[Role]
  Parse ordered ``input_*``/``output_*`` descriptors, match them to the exact
  catalog C/callable slot order (including declared tensor-list spans), validate
  descriptor/list-item state, scalar attributes and undefined-to-null policy,
  charge layout-qualified padding and publish three distinct digests.

[Invariants]
  * Empty positions are preserved.  A declared span with fewer descriptors than
    its length is a ``span_deficit``; extra descriptors are never appended.
  * ``absent``/``undefined``/``null``/``missing``/``invalid``/``scalar``/``tensor``
    are distinct.  Every tensor-list item gets the same present/shape/dtype/
    layout/policy checks as a scalar tensor slot.
  * Recipe-forwarded attributes (for example ``quant_mode``) are validated with
    the callable schema kind and included in ``call_abi_sha256``.
  * ``identity.status`` is ``complete`` only with schema, version and capture
    qualification; otherwise it is ``schema_bound``/``bound_unqualified``.
  * ``capture_shape_abi_sha256`` uses the raw slot order; ``call_abi_sha256``
    covers dtype, layout, strides, storage, null state and every forwarded attr.

[Timeouts & Locks]
  In-memory projection proportional to captured slots.

[Side-Effect Policy]
  No I/O, hardware access or simulation imports.
"""

from __future__ import annotations
from .repro_values import validate_json_integers, storage_record
from .repro_values import bounded_container_len, bounded_mapping, bounded_sequence, decode_bounded_json

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .native_tensor_abi import native_abi_from_slots
from .op_abi_attributes import bind_attrs as _bind_attrs
from .op_abi_attributes import recipe_forwarded_attr_specs
from .op_abi_descriptors import (
    _native_slots, _text, parse_shape, slot_descriptors,
)
from .op_abi_padding import compute_padding

BINDING_SCHEMA = "mindie-op-occurrence-binding/2"
_OP_KEYS = ("op_type", "kind", "operator", "api", "name")
_VERSION_KEYS = ("cann_version", "cann_release", "cann_build", "build_version")
_BLOCKING = {
    "required_slot_omitted", "required_slot_null", "unexpected_input_slots",
    "unexpected_output_slots", "surplus_slots", "descriptor_incomplete",
    "descriptor_invalid", "descriptor_not_a_mapping",
    "descriptor_column_mismatch", "dtype_unknown", "dtype_not_declared",
    "layout_not_declared", "required_attrs_absent", "padding_invalid",
    "missing_descriptor_field", "capture_abi_id_mismatch",
    "abi_signature_unpinned", "tensor_list_layout_unverified",
    "tensor_list_lengths_invalid", "span_deficit", "unknown_tensor_list_name",
    "invalid_attribute_type", "invalid_attribute_range",
    "invalid_attribute_value", "invalid_array_length", "invalid_array_range",
    "invalid_array_order", "undefined_policy_unspecified",
    "undefined_not_nullable", "tensor_list_item_invalid", "repro_unsupported",
}


def operator_name(row: Any) -> str:
    for key in _OP_KEYS:
        value = _text(_field(row, key))
        if value:
            return value
    return ""


def _field(row: Any, key: str) -> Any:
    if isinstance(row, Mapping):
        bounded_container_len(row)
        return row.get(key)
    return getattr(row, key, None)


def captured_version(row: Any) -> str | None:
    for key in _VERSION_KEYS:
        value = _text(_field(row, key))
        if value:
            return value
    return None


def row_attrs(row: Any) -> dict[str, Any]:
    for key in ("attrs", "attributes", "op_attrs", "attr"):
        value = _field(row, key)
        if isinstance(value, Mapping):
            return {str(name): val for name, val in bounded_mapping(value).items()}
        if isinstance(value, str) and value.strip().startswith("{"):
            try:
                parsed = decode_bounded_json(value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, Mapping):
                return {str(name): val for name, val in bounded_mapping(parsed).items()}
    return {}


def _declared_lengths(declared: Sequence[Mapping[str, Any]],
                      lengths: Mapping[str, Any] | None
                      ) -> tuple[dict[str, int], list[dict[str, Any]]]:
    if lengths is None:
        return {}, []
    lengths = bounded_mapping(lengths, "tensor list lengths")
    by_name = {spec["name"]: spec for spec in declared}
    resolved, issues = {}, []
    for name, value in lengths.items():
        key = str(name)
        spec = by_name.get(key)
        if spec is None:
            issues.append({"code": "unknown_tensor_list_name", "name": key})
            continue
        if spec.get("cat") != "tensor_list":
            issues.append({"code": "tensor_list_lengths_invalid", "name": key,
                           "detail": "length declared for a non-list slot"})
            continue
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1024:
            issues.append({"code": "tensor_list_lengths_invalid", "name": key,
                           "detail": "length must be an integer in [0, 1024]"})
            continue
        number = value
        resolved[key] = number
    return resolved, issues


def _assign(declared: Sequence[Mapping[str, Any]], slots: Sequence[Mapping[str, Any]],
            lengths: Mapping[str, int] | None = None,
            names: Sequence[str] | None = None
            ) -> tuple[list[tuple[Mapping[str, Any], list[Mapping[str, Any]]]],
                       list[Mapping[str, Any]], bool, list[dict[str, Any]]]:
    """Assign descriptors to declared contiguous spans in parameter order."""
    groups: list[list[Mapping[str, Any]]] = [[] for _ in declared]
    issues: list[dict[str, Any]] = []
    if names:
        by_name: dict[str, list[Mapping[str, Any]]] = {}
        for name, slot in zip(names, slots):
            by_name.setdefault(str(name), []).append(slot)
        used: set[int] = set()
        named_lengths = dict(lengths or {})
        for position, spec in enumerate(declared):
            candidates = by_name.get(spec["name"], [])
            if spec.get("cat") == "tensor_list":
                groups[position] = list(candidates)
                expected = named_lengths.get(spec["name"])
                if expected is not None and len(candidates) != int(expected):
                    code = ("span_deficit" if len(candidates) < int(expected)
                            else "tensor_list_lengths_invalid")
                    issues.append({"code": code, "name": spec["name"],
                                   "declared": int(expected),
                                   "captured": len(candidates)})
            else:
                groups[position] = list(candidates[:1])
                for surplus in candidates[1:]:
                    issues.append({"code": "surplus_slots",
                                   "name": spec["name"], "slot": surplus})
            used.update(id(slot) for slot in groups[position])
        extras = [slot for slot in slots if id(slot) not in used]
        return list(zip(declared, groups)), extras, False, issues
    lengths = dict(lengths or {})
    missing_required = [spec["name"] for spec in declared
                        if spec.get("cat") == "tensor_list"
                        and not spec.get("optional")
                        and spec["name"] not in lengths]
    index = 0
    for position, spec in enumerate(declared):
        is_list = spec.get("cat") == "tensor_list"
        if is_list and lengths:
            declared_count = max(0, int(lengths.get(spec["name"], 0)))
            available = max(0, len(slots) - index)
            if declared_count > available:
                issues.append({"code": "span_deficit", "name": spec["name"],
                               "declared": declared_count, "captured": available})
                count = available
            else:
                count = declared_count
        else:
            count = 1
        for _ in range(count):
            if index < len(slots):
                groups[position].append(slots[index])
                index += 1
    extras = list(slots[index:])
    unverified = bool(missing_required) or bool(
        extras and not lengths and any(
            spec.get("cat") == "tensor_list" for spec in declared))
    return list(zip(declared, groups)), extras, unverified, issues


def _slot_policy(spec: Mapping[str, Any]) -> bool | None:
    value = spec.get("undefined_means_null")
    return value if isinstance(value, bool) else None


def _tensor_list_item_issues(item: Mapping[str, Any], spec: Mapping[str, Any],
                             direction: str, slot: int, item_index: int,
                             policy: bool | None) -> list[dict[str, Any]]:
    """Apply the scalar tensor-slot state/dtype/layout contract to one item."""
    issues: list[dict[str, Any]] = []
    name = spec["name"]
    state = str(item.get("state") or "")
    declared_dtypes = list(spec.get("dtypes") or ())
    declared_layouts = list(spec.get("layouts") or ())
    context = {"direction": direction, "slot": slot, "name": name,
               "list_index": item_index}
    if not item.get("present") or state in {"absent", "undefined"}:
        issues.append({"code": "tensor_list_item_invalid", **context,
                       "reason": state or "absent"})
        if policy is True:
            issues.append({"code": "tensor_list_item_invalid", **context,
                           "reason": "undefined_means_null_has_no_list_null"})
        elif policy is None:
            issues.append({"code": "undefined_policy_unspecified", **context})
        else:
            issues.append({"code": "undefined_not_nullable", **context})
        return issues
    if state == "missing":
        issues.append({"code": "descriptor_incomplete", **context,
                       "fields": [field for field, flag in (
                           ("shape", item.get("shape_present")),
                           ("dtype", item.get("dtype_present")),
                           ("layout", item.get("layout_present"))) if not flag]})
        return issues
    if state == "invalid":
        issues.append({"code": "descriptor_invalid", **context,
                       "shape": item.get("shape")})
        return issues
    if state == "scalar":
        issues.append({"code": "tensor_list_item_invalid", **context,
                       "reason": "scalar_in_tensor_list"})
        return issues
    if not item.get("shape_present") or item.get("shape") is None:
        issues.append({"code": "descriptor_incomplete", **context,
                       "fields": ["shape"]})
    if not item.get("dtype_known") or item.get("dtype") is None:
        issues.append({"code": "dtype_unknown", **context,
                       "dtype_raw": item.get("dtype_raw")})
    elif declared_dtypes and item.get("dtype") not in declared_dtypes:
        issues.append({"code": "dtype_not_declared", **context,
                       "dtype": item.get("dtype"), "declared": declared_dtypes})
    if not item.get("layout_present") or not item.get("layout"):
        issues.append({"code": "descriptor_incomplete", **context,
                       "fields": ["layout"]})
    elif declared_layouts and item.get("layout") not in declared_layouts:
        issues.append({"code": "layout_not_declared", **context,
                       "layout": item.get("layout"), "declared": declared_layouts})
    return issues


def _bind_side(declared: Sequence[Mapping[str, Any]], parsed: Mapping[str, Any],
               direction: str, lengths: Mapping[str, int] | None = None,
               names: Sequence[str] | None = None
               ) -> tuple[list[dict[str, Any]], list[dict[str, Any]],
                          list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = list(parsed.get("issues") or ())
    pairs, extras, unverified, assignment_issues = _assign(
        declared, parsed.get("slots") or (), lengths, names)
    issues.extend(assignment_issues)
    if unverified:
        issues.append({"code": "tensor_list_layout_unverified", "direction": direction,
                       "detail": "provide input_tensor_list_lengths or input_names"})
    for index, (spec, assigned) in enumerate(pairs):
        base = {"position": index, "name": spec["name"], "role": spec.get("role"),
                "optional": bool(spec.get("optional")), "cat": spec.get("cat", "tensor")}
        declared_dtypes = list(spec.get("dtypes") or ())
        declared_layouts = list(spec.get("layouts") or ())
        policy = _slot_policy(spec)
        if spec.get("optional") and spec.get("cat") != "tensor_list" and policy is None:
            issues.append({"code": "undefined_policy_unspecified", "direction": direction,
                           "slot": index, "name": spec["name"]})
        if not assigned:
            records.append({**base, "present": False, "state": "omitted",
                            "shape": None, "usable": False,
                            "undefined_means_null": policy})
            if not spec.get("optional"):
                issues.append({"code": "required_slot_omitted", "direction": direction,
                               "slot": index, "name": spec["name"]})
            continue
        if spec.get("cat") == "tensor_list":
            items = [dict(item) for item in assigned]
            usable = all(item["usable"] for item in items)
            records.append({**base, "present": True, "state": "tensor_list",
                            "items": items, "shape": None,
                            "usable": usable,
                            "undefined_means_null": policy})
            for item_index, item in enumerate(items):
                item_issues = _tensor_list_item_issues(
                    item, spec, direction, index, item_index, policy)
                if item_issues:
                    item["usable"] = False
                    usable = False
                    issues.extend(item_issues)
            records[-1]["usable"] = usable
            continue
        slot = dict(assigned[0])
        record = {**base, **slot, "present": bool(slot.get("present")),
                  "undefined_means_null": policy}
        records.append(record)
        if (slot.get("dtype_raw") and not slot.get("dtype_known")
                and slot["state"] not in {"absent", "undefined"}):
            issues.append({"code": "dtype_unknown", "direction": direction,
                           "slot": index, "name": spec["name"],
                           "dtype_raw": slot.get("dtype_raw")})
        if slot["state"] in {"absent", "undefined"}:
            if spec.get("optional") and policy is True:
                record["state"] = "null"
                record["null_source"] = slot["state"]
                continue
            if spec.get("optional") and policy is False:
                issues.append({"code": "undefined_not_nullable", "direction": direction,
                               "slot": index, "name": spec["name"]})
            elif not spec.get("optional"):
                issues.append({"code": "required_slot_null", "direction": direction,
                               "slot": index, "name": spec["name"]})
        elif slot["state"] == "missing":
            issues.append({"code": "descriptor_incomplete", "direction": direction,
                           "slot": index, "name": spec["name"],
                           "fields": [field for field, flag in (
                               ("shape", slot.get("shape_present")),
                               ("dtype", slot.get("dtype_present")),
                               ("layout", slot.get("layout_present"))) if not flag]})
        elif slot["state"] == "invalid":
            issues.append({"code": "descriptor_invalid", "direction": direction,
                           "slot": index, "name": spec["name"],
                           "shape": slot.get("shape")})
        else:
            if not slot.get("dtype_known") and slot.get("dtype") is None:
                issues.append({"code": "dtype_unknown", "direction": direction,
                               "slot": index, "name": spec["name"],
                               "dtype_raw": slot.get("dtype_raw")})
            elif declared_dtypes and slot.get("dtype") not in declared_dtypes:
                issues.append({"code": "dtype_not_declared", "direction": direction,
                               "slot": index, "name": spec["name"],
                               "dtype": slot.get("dtype"), "declared": declared_dtypes})
            if declared_layouts and slot.get("layout") not in declared_layouts:
                issues.append({"code": "layout_not_declared", "direction": direction,
                               "slot": index, "name": spec["name"],
                               "layout": slot.get("layout"), "declared": declared_layouts})
    return records, issues, [dict(item) for item in extras]


def value_for(name: str, attrs: Mapping[str, Any],
              inputs: Sequence[Mapping[str, Any]]) -> Any:
    attrs, inputs = bounded_sequence([attrs, inputs], "attribute sources")
    if name in attrs and attrs[name] is not None:
        return attrs[name]
    aliases = {
        "actual_seq_lens_q": ("actual_seq_lengths_query", "actual_seq_qlen"),
        "actual_seq_lens_kv": ("actual_seq_lengths_kv", "actual_seq_kvlen"),
        "cu_seqlens": ("actual_seq_lens", "query_start_loc"),
        "query_start_loc": ("cu_seqlens",),
        "context_lens": ("context_lengths", "kv_lens"),
    }
    for alias in aliases.get(name, ()):
        if alias in attrs and attrs[alias] is not None:
            return attrs[alias]
    for record in inputs:
        if record["name"] == name and record.get("values") is not None:
            return record["values"]
    return None


def _raw_evidence(parsed: Mapping[str, Any]) -> dict[str, Any]:
    return {"present": parsed.get("present"), "slot_count": len(parsed.get("slots") or ()),
            "slots": parsed.get("slots") or (), "issues": parsed.get("issues") or ()}


def _canonical_identity(name: str, entry: Mapping[str, Any],
                        inputs: Sequence[Mapping[str, Any]],
                        outputs: Sequence[Mapping[str, Any]],
                        attrs: Sequence[Mapping[str, Any]]) -> str:
    def slot_record(record: Mapping[str, Any], direction: str) -> dict[str, Any]:
        items = record.get("items")
        base = {
            "direction": direction, "name": record.get("name"),
            "state": record.get("state"), "present": bool(record.get("present")),
            "optional": bool(record.get("optional")),
            "undefined_means_null": record.get("undefined_means_null"),
        }
        if items is not None:
            base["items"] = [slot_record(item, direction) for item in items]
            return base
        storage = storage_record(record)
        base.update({
            "shape": record.get("shape"), "dtype": record.get("dtype_raw"),
            "layout": record.get("layout_raw"),
            "strides": storage.get("strides", storage.get("stride")),
            "storage_offset": storage.get("storage_offset", storage.get("offset")),
            "storage_bytes": storage.get("storage_bytes"),
            "storage_id": storage.get("storage_id", storage.get("storage_object_id")),
        })
        return base

    payload = {
        "operator": name, "abi_id": entry.get("abi_id"),
        "inputs": [slot_record(record, "input") for record in inputs],
        "outputs": [slot_record(record, "output") for record in outputs],
        "attrs": [{"name": record["name"], "kind": record["kind"],
                   "present": record["present"],
                   "value": (record["value"] if record["value"] is not None
                             else record.get("raw_value")),
                   "raw_value": record.get("raw_value")}
                  for record in attrs],
    }
    validate_json_integers(payload)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           allow_nan=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def bind_resolved_occurrence(row: Any, match: Mapping[str, Any] | None, *,
                             cann_version: str | None = None,
                             device: str | None = None) -> dict[str, Any]:
    """Bind a capture row to a resolved catalog match or return ``unknown_abi``."""
    if isinstance(row, Mapping):
        row = bounded_mapping(row, "capture row")
    if match is not None:
        match = bounded_mapping(match, "catalog match")
    name = operator_name(row)
    inputs_parsed = slot_descriptors(row, "input")
    outputs_parsed = slot_descriptors(row, "output")
    captured_attrs = row_attrs(row)
    version = cann_version if cann_version is not None else captured_version(row)
    base = {
        "schema": BINDING_SCHEMA, "operator": name, "cann_version": version,
        "raw_input_slots": len(inputs_parsed.get("slots") or ()),
        "raw_output_slots": len(outputs_parsed.get("slots") or ()),
        "raw_evidence": {"inputs": _raw_evidence(inputs_parsed),
                         "outputs": _raw_evidence(outputs_parsed)},
    }
    if match is None or not (match.get("version_supported")
                             and match.get("abi_id_supported", True)):
        reason = (match or {}).get("unknown_reason")
        code = f"unknown_abi_{reason}" if reason else (
            "unknown_abi_missing_version" if match is not None and version is None
            else "unknown_abi_unverified_version" if match is not None
            else "unknown_abi_uncatalogued_name")
        return {**base, "status": "unknown_abi", "slot_status": "unknown_abi",
                "canonical": None, "catalog_match": None, "inputs": [], "outputs": [],
                "attr_slots": [], "attrs": captured_attrs, "padding": None,
                "effective_tokens": 0, "identity": None,
                "repro_status": "blocked", "repro_supported": False,
                "repro_block_reason": code,
                "qualification": {"version_qualified": bool(
                    (match or {}).get("version_qualified")),
                    "qualification_state": (match or {}).get(
                        "qualification_state", "unknown")},
                "issues": [{"code": code, "operator": name or None,
                            "requested_version": version,
                            "declared_versions": (match or {}).get("versions", []),
                            "raw_slots_preserved": True}]}
    entry = match["entry"]
    recipe = dict(entry.get("repro_recipe") or {})
    slot_specs = entry["c_abi_slots"].get("slot_specs") or {}
    declared_inputs = [dict(spec) for spec in slot_specs.get("inputs") or ()]
    declared_outputs = [dict(spec) for spec in slot_specs.get("outputs") or ()]

    def list_metadata(direction: str) -> tuple[dict[str, int] | None, list[str] | None]:
        raw = _field(row, f"{direction}_tensor_list_lengths")
        lengths = None
        if isinstance(raw, Mapping):
            lengths = {str(name): value for name, value in bounded_mapping(raw).items()}
        names = _field(row, f"{direction}_names")
        names = [str(name) for name in bounded_sequence(names, "names")] if isinstance(names, (list, tuple)) else None
        return lengths, names

    aliases = list(recipe.get("mutable_aliases") or ())
    if not declared_outputs and not outputs_parsed.get("present") and aliases:
        outputs_parsed = {"present": True, "slots": [], "issues": []}
    in_lengths, in_names = list_metadata("input")
    out_lengths, out_names = list_metadata("output")
    in_lengths, in_length_issues = _declared_lengths(declared_inputs, in_lengths)
    out_lengths, out_length_issues = _declared_lengths(declared_outputs, out_lengths)
    inputs, input_issues, extra_inputs = _bind_side(
        declared_inputs, inputs_parsed, "input", in_lengths, in_names)
    outputs, output_issues, extra_outputs = _bind_side(
        declared_outputs, outputs_parsed, "output", out_lengths, out_names)
    issues = [*in_length_issues, *out_length_issues, *input_issues, *output_issues]
    if extra_inputs:
        issues.append({"code": "surplus_slots", "direction": "input",
                       "count": len(extra_inputs), "slots": extra_inputs})
        issues.append({"code": "unexpected_input_slots", "direction": "input",
                       "count": len(extra_inputs), "slots": extra_inputs})
    if extra_outputs and not declared_outputs and len(extra_outputs) <= len(aliases):
        outputs = [{"position": index, "name": alias, "role": "activation",
                    "optional": False, "cat": "tensor", "state": "alias",
                    "present": True, "shape": None, "usable": True,
                    "aliased_input": alias, "storage": {}}
                   for index, alias in enumerate(aliases[:len(extra_outputs)])]
        extra_outputs = []
    if extra_outputs:
        issues.append({"code": "surplus_slots", "direction": "output",
                       "count": len(extra_outputs), "slots": extra_outputs})
        issues.append({"code": "unexpected_output_slots", "direction": "output",
                       "count": len(extra_outputs), "slots": extra_outputs})

    attr_specs = [dict(param, cat=param.get("cat", "int"),
                       required=bool(param.get("required",
                                               not param.get("optional", False))))
                  for param in entry["c_abi_slots"]["parameters"]
                  if param["name"] in set(entry["c_abi_slots"]["attr_slots"])]
    merged_specs = {spec["name"]: spec for spec in attr_specs}
    for spec in recipe_forwarded_attr_specs(recipe):
        # The C-storage kind wins for a name that is also a declared C attribute;
        # recipe-only arguments (for example DynamicQuant quant_mode) use the
        # callable schema kind and are validated with it.
        merged_specs.setdefault(spec["name"], spec)
    attr_specs = list(merged_specs.values())
    attr_slots, attr_issues = _bind_attrs(attr_specs, captured_attrs, inputs)
    issues.extend(attr_issues)
    attrs = dict(captured_attrs)
    attrs.update({record["name"]: record["value"] for record in attr_slots
                  if record["present"] and record["value"] is not None})
    recipe_attrs_known = {
        spec["attr"] for spec in (recipe.get("keyword") or {}).values()
        if isinstance(spec, dict) and spec.get("attr")}
    recipe_attr_required = {
        spec["attr"] for spec in (recipe.get("keyword") or {}).values()
        if isinstance(spec, dict) and spec.get("attr") and not spec.get("optional")}
    required_missing = [record["name"] for record in attr_slots
                        if record["required"] and not record["present"]
                        and (not recipe_attrs_known
                             or record["name"] in recipe_attr_required)]
    if required_missing:
        issues.append({"code": "required_attrs_absent", "names": required_missing})

    device = device or _text(attrs.get("device") or attrs.get("device_arch")
                             or attrs.get("soc") or attrs.get("arch")) or None
    padding = compute_padding(entry, inputs, attrs, device=device)
    if not padding["valid"]:
        issues.append({"code": "padding_invalid",
                       "violations": padding["violations"]})

    captured_abi = _text(_field(row, "abi_id") or _field(row, "capture_abi_id"))
    if captured_abi and captured_abi != entry.get("abi_id"):
        issues.append({"code": "capture_abi_id_mismatch",
                       "captured": captured_abi, "catalog": entry.get("abi_id")})
    signature_status = str(entry["c_abi_slots"].get("signature_status") or "pinned")
    if signature_status != "pinned":
        issues.append({"code": "abi_signature_unpinned",
                       "signature_status": signature_status,
                       "sources": [source.get("kind") for source in
                                   entry.get("sources") or ()]})

    raw_input_slots = inputs_parsed.get("slots") or ()
    raw_output_slots = list(outputs_parsed.get("slots") or ())
    if not raw_output_slots and aliases:
        alias_positions = [index for index, spec in enumerate(declared_inputs)
                           if spec["name"] in aliases]
        raw_output_slots = [raw_input_slots[index] for index in alias_positions
                            if index < len(raw_input_slots)]
    raw_shape_digest = native_abi_from_slots(
        name, _native_slots(raw_input_slots), _native_slots(raw_output_slots))
    named_inputs = _native_slots(inputs)
    named_outputs = _native_slots(outputs)
    if not outputs:
        named_outputs = _native_slots([slot for slot in inputs
                                       if slot["name"] in aliases])
    named_digest = native_abi_from_slots(name, named_inputs, named_outputs)
    call_digest = _canonical_identity(name, entry, inputs, outputs, attr_slots)
    blocking = any(issue["code"] in _BLOCKING for issue in issues)
    repro_supported = bool(recipe.get("supported") or recipe.get("repro_supported"))
    repro_status = str(recipe.get("status") or ("ready" if repro_supported
                                                else "blocked"))
    if repro_status != "ready" or not repro_supported:
        repro_supported = False
        repro_status = "blocked"
    explicit_span_violation = bool(
        (in_lengths or out_lengths) and (extra_inputs or extra_outputs))
    if explicit_span_violation:
        slot_status = "abi_mismatch"
    elif blocking or named_digest.get("status") != "complete":
        slot_status = "incomplete"
        if {issue["code"] for issue in issues} <= {"abi_signature_unpinned"}:
            slot_status = "blocked"
    else:
        slot_status = "bound"
    status = slot_status if slot_status != "bound" or repro_supported else "blocked"
    schema_pinned = bool(entry["c_abi_slots"].get("pinned"))
    version_qualified = bool(match.get("version_qualified"))
    capture_verified = bool(match.get("capture_verified"))
    identity = None
    if slot_status == "bound":
        if schema_pinned and version_qualified and capture_verified:
            identity_status = "complete"
        elif schema_pinned:
            identity_status = "schema_bound"
        else:
            identity_status = "bound_unqualified"
        identity = {
            "status": identity_status,
            "complete": identity_status == "complete",
            "catalog_abi_id": entry.get("abi_id"),
            "native_abi_sha256": raw_shape_digest.get("digest"),
            "capture_shape_abi_sha256": raw_shape_digest.get("digest"),
            "call_abi_sha256": call_digest,
            "named_shape_abi_sha256": named_digest.get("digest"),
            "source_sha256": [source.get("sha256") for source in
                              entry.get("sources") or ()],
            "match": match.get("match"),
            "qualification_state": match.get("qualification_state"),
            "schema_pinned": schema_pinned,
            "version_qualified": version_qualified,
            "capture_verified": capture_verified,
            "undefined_policy": {record["name"]: record.get("undefined_means_null")
                                 for record in inputs + outputs
                                 if record.get("optional")},
            "scalar_attrs": {record["name"]: record["value"]
                             for record in attr_slots if record["present"]},
        }
    span_deficits = [issue for issue in issues if issue.get("code") == "span_deficit"]
    by_name: dict[str, dict[str, Any]] = {}
    for direction, records in (("input", inputs), ("output", outputs)):
        for record in records:
            by_name[record["name"]] = {**record, "direction": direction}
    return {
        **base, "status": status, "slot_status": slot_status,
        "canonical": match["name"], "catalog_match": match.get("match"),
        "versions": match["versions"], "family": entry.get("family"),
        "surface": entry.get("surface"), "pipe": entry.get("pipe"),
        "abi_id": entry.get("abi_id"),
        "c_abi_slots": entry.get("c_abi_slots"),
        "flatten_adapter": entry.get("flatten_adapter"),
        "padding_semantics": dict(entry.get("padding_semantics") or {}),
        "inputs": inputs, "outputs": outputs, "attr_slots": attr_slots,
        "attrs": attrs, "by_name": by_name, "padding": padding,
        "effective_tokens": padding["effective_tokens"],
        "conservation": {
            "exact": not extra_inputs and not extra_outputs and not span_deficits,
            "captured_input_slots": len(inputs_parsed.get("slots") or ()),
            "captured_output_slots": len(outputs_parsed.get("slots") or ()),
            "declared_input_slots": len(declared_inputs),
            "declared_output_slots": len(declared_outputs),
            "consumed_input_slots": logging_consumed(inputs),
            "consumed_output_slots": logging_consumed(outputs),
            "span_deficit_count": len(span_deficits),
            "span_deficits": span_deficits,
            "unexpected_input_count": len(extra_inputs),
            "unexpected_output_count": len(extra_outputs),
            "surplus_input_slots": extra_inputs,
            "surplus_output_slots": extra_outputs,
        },
        "identity": identity, "native_abi": raw_shape_digest,
        "named_abi": named_digest, "call_abi_sha256": call_digest,
        "repro": recipe, "repro_supported": repro_supported,
        "repro_status": repro_status,
        "repro_block_reason": None if repro_supported else (
            recipe.get("unsupported_reason") or "recipe_not_ready"),
        "qualification": {
            "version_qualified": bool(match.get("version_qualified")),
            "qualification_state": match.get("qualification_state"),
            "schema_pinned": bool(entry["c_abi_slots"].get("pinned")),
            "capture_verified": bool(match.get("capture_verified")),
        },
        "issues": issues,
    }


def logging_consumed(records: Sequence[Mapping[str, Any]]) -> int:
    total = 0
    for record in bounded_sequence(records, "slots"):
        if record.get("state") == "tensor_list":
            total += len(record.get("items") or ())
        elif record.get("present"):
            total += 1
    return total


__all__ = [
    "BINDING_SCHEMA", "bind_resolved_occurrence", "captured_version", "operator_name",
    "parse_shape", "row_attrs", "slot_descriptors", "value_for",
]
