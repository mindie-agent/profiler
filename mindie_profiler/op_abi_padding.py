"""Layout- and overload-qualified padding/work accounting for captured operators.

[Role]
  Resolve one declared padding contract against the captured layout, sequence
  metadata, group-list encoding and physical capacity, and return bucket /
  logical / effective / charged counts with explicit violations.  Also provide
  the deterministic metadata synthesizer used by the reproducer.

[Invariants]
  * Layout is never guessed from a bare shape: BSH/BSND/BNSD use axis 0 as the
    batch axis and a sequence axis; TND uses axis 0 as tokens and cumsum.
  * ``effective_tokens == 0`` is real; ``None`` means "derive it", never the
    bucket through truthiness.
  * TND tail equality is device-qualified (arch22 ``== T``, generic ``<= T``).
  * Group lists validate per encoding (monotone cumsum, exact counts, sparse
    pairs); invalid metadata raises violations and is never clamped.
  * Leading-zero cumulative vectors are recognized and emitted where declared.

[Timeouts & Locks]
  Pure in-memory arithmetic; no I/O, locks or device access.

[Side-Effect Policy]
  No I/O and no mutation of supplied records.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .op_abi_numeric import _num, _strict_tokens, numeric_list
from .op_abi_padding_rules import (
    synthesize_group_list,
    synthesize_offsets,
    validate_group_list,
    validate_sequence_lengths,
)
from .repro_values import bounded_sequence

TND_LAYOUTS = frozenset({"TND", "TND_NZ"})
BATCHED_LAYOUTS = frozenset({"BSH", "BSND", "BNSD", "BSND_NZ"})


def _layout(entry: Mapping[str, Any], attrs: Mapping[str, Any]) -> tuple[str | None, str]:
    spec = entry.get("padding_semantics") or {}
    key = spec.get("layout_attr")
    if key:
        value = attrs.get(key)
        if value is None:
            for alias in (f"{key}s", f"{key}_query", "layout"):
                if attrs.get(alias) is not None:
                    value = attrs[alias]
                    break
        if value is not None:
            return str(value).strip(), "attr"
    layouts = spec.get("layouts") or {}
    if len(layouts) == 1:
        return next(iter(layouts)), "sole_declared_layout"
    default = spec.get("default_layout")
    return (str(default).strip(), "declared_default") if default else (None, "absent")


def _decode_layout(name: str | None) -> str | None:
    if not name:
        return None
    text = str(name).strip().upper()
    for prefix in ("PA_", "BSA_"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith("_NZ"):
        text = text[:-3]
    return text


def _axis_shape(record: Mapping[str, Any] | None) -> list[int] | None:
    if not record or record.get("present") is False:
        return None
    if record.get("items"):
        return _axis_shape(record["items"][0])
    if record.get("state") in {"absent", "omitted", "missing", "invalid"}:
        return None
    shape = record.get("shape")
    return [int(value) for value in shape] if shape is not None else None


def _first_input(entry: Mapping[str, Any], inputs: Sequence[Mapping[str, Any]]) -> dict | None:
    preferred = entry.get("tokens_from")
    for record in inputs:
        if preferred and record.get("name") == preferred and record.get("present"):
            return record
    for record in inputs:
        if record.get("present") and _axis_shape(record) is not None:
            return record
    return None


def _sequence_values(name: str | None, attrs: Mapping[str, Any],
                     inputs: Sequence[Mapping[str, Any]]) -> list[float] | None:
    if not name:
        return None
    values = numeric_list(attrs.get(name))
    if values is not None:
        return values
    for record in inputs:
        if record.get("name") == name and record.get("values") is not None:
            return numeric_list(record.get("values"))
    return None


def _tail_rule(rule: Mapping[str, Any], device: str | None) -> tuple[str, str]:
    by_arch = rule.get("tail_rule_by_arch") or {}
    device_key = (device or "generic").lower()
    device_key = "arch22" if device_key in {"arch22", "a2", "a3", "910b", "910_93"} else "generic"
    if device_key in by_arch:
        return str(by_arch[device_key]), device_key
    return str(rule.get("tail_rule") or "le_bucket"), device_key


def _group_type(entry: Mapping[str, Any], attrs: Mapping[str, Any]) -> str:
    spec = entry.get("padding_semantics") or {}
    key = spec.get("group_list_type_arg")
    if key and attrs.get(key) is not None:
        return str(attrs[key])
    return str(spec.get("default_group_type", "0"))


def _extent_of(name: str | None, inputs: Sequence[Mapping[str, Any]],
               axes: Sequence[int] | None = None) -> int | None:
    if not name:
        return None
    for record in inputs:
        if record.get("name") != name:
            continue
        shape = _axis_shape(record)
        if not shape:
            return None
        selected = list(axes) if axes else [0]
        value = 1
        for axis in selected:
            if axis >= len(shape):
                return None
            value *= max(0, int(shape[axis]))
        return value
    return None


def _kv_extent(entry: Mapping[str, Any], inputs: Sequence[Mapping[str, Any]],
               layout: str | None = None) -> int | None:
    spec = entry.get("padding_semantics") or {}
    candidates = spec.get("kv_extent_from") or (
        "key", "key_cache", "kv_cache", "value", "value_cache")
    by_layout = spec.get("kv_extent_axes_by_layout") or {}
    axes = by_layout.get(str(layout or "")) or spec.get("kv_extent_axes")
    for name in candidates:
        for record in inputs:
            if record.get("name") != name:
                continue
            selected = list(axes) if axes else (
                [0, 1] if record.get("role") == "kv_cache" else [0])
            extent = _extent_of(name, [record], selected)
            if extent is not None:
                return extent
    return None


def _kv_record(entry: Mapping[str, Any],
               inputs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    candidates = (entry.get("padding_semantics") or {}).get("kv_extent_from") or (
        "key", "key_cache", "kv_cache", "value", "value_cache")
    for name in candidates:
        for record in inputs:
            if record.get("name") == name and record.get("present"):
                return record
    return None


def _kv_tensor_specs(entry: Mapping[str, Any],
                     inputs: Sequence[Mapping[str, Any]], layout: str | None,
                     rule: Mapping[str, Any] | None
                     ) -> list[dict[str, Any]]:
    """Every bound KV tensor and the sequence extent it physically provides."""
    spec = entry.get("padding_semantics") or {}
    candidates = spec.get("kv_extent_from") or (
        "key", "key_cache", "kv_cache", "value", "value_cache")
    by_layout = spec.get("kv_extent_axes_by_layout") or {}
    axes = by_layout.get(str(layout or "")) or spec.get("kv_extent_axes")
    seq_axis = (rule or {}).get("seq_axis")
    batch_axis = (rule or {}).get("batch_axis")
    out: list[dict[str, Any]] = []
    for name in candidates:
        for record in inputs:
            if record.get("name") != name or record.get("present") is False:
                continue
            shape = _axis_shape(record)
            if not shape:
                continue
            cache = record.get("role") == "kv_cache" or str(name).endswith("cache")
            if cache:
                extent = _extent_of(name, [record],
                                    list(axes) if axes else [0, 1])
            elif seq_axis is not None and seq_axis < len(shape):
                extent = int(shape[seq_axis])
            elif str(layout or "") in TND_LAYOUTS:
                extent = int(shape[0])
            else:
                extent = _extent_of(name, [record],
                                    list(axes) if axes else [0])
            out.append({
                "name": str(name), "shape": shape, "extent": extent,
                "non_paged": not cache,
                "batch": (int(shape[batch_axis])
                          if batch_axis is not None and batch_axis < len(shape)
                          else None),
            })
    return out


def _sequence_charge(entry, attrs, inputs, layout_rule, bucket, mode, device,
                     kv_extent=None, q_extent=None, physical_bucket=None,
                     q_batch=None, kv_batch=None, kv_specs=None):
    """Return (logical, source, violations) for a sequence-filtered operator."""
    spec = entry.get("padding_semantics") or {}
    violations: list[dict[str, Any]] = []
    explicit = attrs.get("effective_tokens")
    if explicit is None:
        explicit = attrs.get("logical_tokens")
    q_name = spec.get("query_arg")
    kv_name = spec.get("kv_arg")
    q_values = _sequence_values(q_name, attrs, inputs)
    kv_values = _sequence_values(kv_name, attrs, inputs)
    encoding = (layout_rule or {}).get("seq_encoding") or spec.get("sequence_mode") or "cumsum"
    leading_zero = bool((layout_rule or {}).get("leading_zero")
                        or spec.get("leading_zero"))
    charge_limit = (physical_bucket if physical_bucket is not None else bucket)
    seq_extent = (q_extent if q_extent is not None else charge_limit)
    per_sequence = bool((layout_rule or {}).get("per_batch")
                        and (layout_rule or {}).get("seq_axis") is not None)
    q_checked = None
    if q_values is not None:
        q_checked = validate_sequence_lengths(
            q_values, encoding=encoding, extent=seq_extent,
            leading_zero=leading_zero, per_sequence=per_sequence,
            label="sequence_q")
        violations.extend(q_checked["violations"])
        if q_batch is not None and len(q_checked["values"] or ()) != int(q_batch):
            violations.append({
                "code": "sequence_q_batch_arity",
                "detail": f"{len(q_checked['values'] or ())} lengths != batch {q_batch}"})
        total = q_checked["total"]
        tail_rule, device_key = _tail_rule(layout_rule or {}, device)
        if (mode == "masked_varlen" and layout_rule
                and layout_rule.get("token_axis") == 0):
            if total > charge_limit:
                violations.append({"code": "sequence_tail_exceeds_bucket",
                                   "detail": f"{total} > {charge_limit}"})
            elif (tail_rule == "eq_bucket" and total != charge_limit
                  and "sequence_q_missing_leading_zero" not in
                  {item["code"] for item in q_checked["violations"]}):
                violations.append({
                    "code": "sequence_tail_not_equal_bucket",
                    "detail": f"TND tail {total} != T {charge_limit}",
                    "qualification": f"{device_key}:eq_bucket"})
    kv_checked = None
    if kv_values is not None and kv_name:
        pa_mode = bool(attrs.get("block_table") is not None or any(
            record.get("name") == "block_table" and record.get("present")
            for record in inputs))
        kv_mode_spec = (layout_rule or {}).get("kv_mode") or {}
        kv_encoding = (kv_mode_spec.get("PA" if pa_mode else "non_PA")
                       if kv_mode_spec else None)
        kv_encoding = (kv_encoding or (layout_rule or {}).get("seq_encoding")
                       or spec.get("kv_encoding") or "cumsum")
        targets = kv_specs or [{"name": kv_name, "extent": kv_extent}]
        checked_targets = []
        for target in targets:
            checked = validate_sequence_lengths(
                kv_values, encoding=kv_encoding, extent=target.get("extent"),
                leading_zero=bool(kv_encoding == "cumsum" and leading_zero),
                per_sequence=per_sequence, label="sequence_kv")
            for violation in checked["violations"]:
                violations.append({**violation, "tensor": target["name"]})
            checked_targets.append(checked)
        kv_checked = checked_targets[0] if checked_targets else None
        if kv_batch is not None and kv_checked is not None \
                and len(kv_checked["values"] or ()) != int(kv_batch):
            violations.append({
                "code": "sequence_kv_batch_arity",
                "detail": f"{len(kv_checked['values'] or ())} lengths != batch {kv_batch}"})
        if (q_values is not None and (layout_rule or {}).get("token_axis") == 0
                and len(numeric_list(q_values) or ())
                != len(numeric_list(kv_values) or ())):
            violations.append({
                "code": "sequence_qkv_vector_arity",
                "detail": (f"{len(numeric_list(q_values) or ())} Q lengths != "
                           f"{len(numeric_list(kv_values) or ())} KV lengths")})
    group_routed, group_source = None, None
    if mode == "grouped_prefix":
        group_name = spec.get("group_list_arg")
        values = _sequence_values(group_name, attrs, inputs)
        if values is not None:
            checked = validate_group_list(values, _group_type(entry, attrs),
                                             charge_limit)
            violations.extend(checked["violations"])
            group_routed, group_source = checked["routed_tokens"], f"group:{group_name}"
        else:
            expert_values = _sequence_values("expert_ids", attrs, inputs)
            if expert_values is not None:
                routed = len(expert_values)
                if any(value < 0 for value in expert_values):
                    violations.append({"code": "expert_ids_negative",
                                       "detail": str(expert_values[:8])})
                if routed > charge_limit:
                    violations.append({"code": "routed_rows_exceed_bucket",
                                       "detail": f"{routed} > {charge_limit}"})
                group_routed, group_source = routed, "expert_ids"
    if explicit is not None:
        value = _strict_tokens(explicit)
        if value is None:
            violations.append({"code": "effective_tokens_invalid", "detail": repr(explicit)})
        else:
            if value > bucket:
                violations.append({"code": "effective_tokens_exceeds_bucket",
                                   "detail": f"{value} > {bucket}"})
            return min(value, bucket), "explicit", violations
    if q_values is not None:
        routed = min(max(0, int(q_checked["total"])), bucket)
        return routed, f"filter:{q_name}", violations
    if kv_values is not None and kv_name:
        return min(max(0, int(kv_checked["total"])), bucket), f"filter:{kv_name}", violations
    if group_routed is not None:
        return min(max(0, int(group_routed)), bucket), group_source, violations
    return bucket, "unfiltered", violations


def _padding_tax(paid: int, logical: int) -> float | None:
    try:
        number = 100.0 * (paid / logical) if logical else 0.0
    except OverflowError:
        return None
    return round(number, 4) if math.isfinite(number) else None


def compute_padding(entry: Mapping[str, Any], inputs: Sequence[Mapping[str, Any]],
                    attrs: Mapping[str, Any], *, device: str | None = None) -> dict[str, Any]:
    """Resolve layout, validate metadata and return the token/work contract."""
    entry, inputs, attrs = bounded_sequence([entry, inputs, attrs], "padding inputs")
    spec = dict(entry.get("padding_semantics") or {})
    mode = str(spec.get("mode") or "full_padded_tensor")
    layout_name, layout_source = _layout(entry, attrs)
    layout = _decode_layout(layout_name)
    layouts = spec.get("layouts") or {}
    rule = (layouts.get(layout) if layout in layouts else
            layouts.get(layout_name) if layout_name in layouts else None)
    violations: list[dict[str, Any]] = []
    primary = _first_input(entry, inputs)
    shape = _axis_shape(primary)
    bucket = 0
    if shape is None:
        violations.append({"code": "primary_shape_missing",
                           "detail": entry.get("tokens_from")})
    elif mode != "full_padded_tensor" and layout is None and layouts:
        violations.append({"code": "layout_missing",
                           "detail": f"declared layouts: {sorted(layouts)}"})
    elif layouts and layout is not None and rule is None:
        violations.append({"code": "layout_not_declared",
                           "detail": f"{layout!r} not in {sorted(layouts)}"})
    elif rule:
        token_axis = rule.get("token_axis")
        batch_axis = rule.get("batch_axis")
        seq_axis = rule.get("seq_axis")
        if token_axis is not None:
            bucket = shape[token_axis] if len(shape) > token_axis else 0
        elif batch_axis is not None and seq_axis is not None:
            if len(shape) <= max(batch_axis, seq_axis):
                violations.append({"code": "shape_rank_too_small",
                                   "detail": f"{layout} needs axes {batch_axis},{seq_axis}"})
            else:
                bucket = int(shape[batch_axis]) * int(shape[seq_axis])
        else:
            bucket = shape[0] if shape else 0
        required_rank = rule.get("rank")
        if required_rank is not None and len(shape) != required_rank:
            violations.append({"code": "layout_rank_mismatch",
                               "detail": f"{layout} rank {len(shape)} != {required_rank}"})
    else:
        bucket = shape[0] if shape else 0
    bucket = max(0, int(bucket))
    allocation_bucket = bucket
    explicit_bucket = attrs.get("bucket_tokens")
    if explicit_bucket is not None:
        number = _num(explicit_bucket)
        if number is None or number < bucket:
            violations.append({"code": "bucket_tokens_below_allocation",
                               "detail": f"{explicit_bucket!r} < {bucket}"})
        else:
            bucket = int(number)

    kv_specs = _kv_tensor_specs(entry, inputs, layout or layout_name, rule or {})
    non_paged_kv = [item for item in kv_specs if item.get("non_paged")]
    kv_extent = (min(item["extent"] for item in non_paged_kv)
                 if non_paged_kv else _kv_extent(entry, inputs, layout))
    q_extent = allocation_bucket
    seq_axis = (rule or {}).get("seq_axis")
    rule_batch_axis = (rule or {}).get("batch_axis")
    per_batch = bool((rule or {}).get("per_batch"))
    q_batch = None
    if (per_batch and shape and rule_batch_axis is not None
            and rule_batch_axis < len(shape)):
        q_batch = max(0, int(shape[rule_batch_axis]))
    kv_batch = None
    if per_batch and non_paged_kv:
        kv_batch = non_paged_kv[0].get("batch")
    elif per_batch and seq_axis is not None:
        kv_shape = _axis_shape(_kv_record(entry, inputs))
        if kv_shape and rule_batch_axis is not None \
                and rule_batch_axis < len(kv_shape) and seq_axis < len(kv_shape):
            kv_batch = max(0, int(kv_shape[rule_batch_axis]))
            kv_extent = max(0, int(kv_shape[seq_axis]))
        else:
            kv_batch = q_batch
    elif per_batch and seq_axis is None:
        kv_batch = q_batch
    if per_batch and q_batch is not None:
        for item in non_paged_kv:
            if item.get("batch") is not None and item["batch"] != q_batch:
                violations.append({
                    "code": "qkv_batch_mismatch", "tensor": item["name"],
                    "detail": f"{item['name']} batch {item['batch']} != Q batch {q_batch}"})
        table = next((record for record in inputs
                      if record.get("name") == "block_table"
                      and record.get("present")), None)
        table_shape = _axis_shape(table)
        if table_shape and table_shape[0] != q_batch:
            violations.append({
                "code": "paged_query_block_table_batch",
                "detail": f"query batch {q_batch} != block_table batch {table_shape[0]}"})
    if len({item["extent"] for item in non_paged_kv}) > 1:
        violations.append({
            "code": "kv_sequence_extent_mismatch",
            "detail": {item["name"]: item["extent"] for item in non_paged_kv}})
    if per_batch and seq_axis is not None and shape and seq_axis < len(shape):
        q_extent = max(0, int(shape[seq_axis]))
    logical, token_source, sequence_violations = _sequence_charge(
        entry, attrs, inputs, rule or {}, bucket, mode, device,
        kv_extent=kv_extent, q_extent=q_extent,
        physical_bucket=allocation_bucket, q_batch=q_batch, kv_batch=kv_batch,
        kv_specs=kv_specs)
    violations.extend(sequence_violations)
    if mode == "full_padded_tensor" and token_source == "unfiltered":
        logical = bucket
        token_source = "full_bucket"
    charged = bucket if mode == "full_padded_tensor" else min(logical, bucket)
    if violations:
        charged = 0
    padded = max(0, bucket - logical)
    paid = max(0, charged - logical)
    qualification = {
        "layout": layout or layout_name, "layout_source": layout_source,
        "leading_zero": bool((rule or {}).get("leading_zero")
                             or spec.get("leading_zero")),
        "encoding": (rule or {}).get("seq_encoding") or spec.get("sequence_mode"),
        "device": device or "generic",
        "tail_rule": (_tail_rule(rule, device)[0] if rule else None),
        "per_batch": per_batch,
        "seq_extent": q_extent,
        "physical_bucket_tokens": allocation_bucket,
        "kv_mode": (rule or {}).get("kv_mode"),
        "pa": bool(attrs.get("block_table") is not None or any(
            record.get("name") == "block_table" and record.get("present")
            for record in inputs)),
    }
    kv_values = _sequence_values(spec.get("kv_arg"), attrs, inputs)
    if kv_values is not None and rule and rule.get("kv_mode"):
        expected = rule["kv_mode"].get("PA" if qualification["pa"] else "non_PA")
        observed = str(attrs.get("kv_lengths_encoding") or expected or "unknown")
        qualification["kv_observed"] = observed
        if expected and observed != expected:
            violations.append({"code": "kv_encoding_mismatch",
                               "detail": f"{observed} != {expected}"})
    return {
        "mode": mode, "layout": layout or layout_name,
        "bucket_tokens": bucket, "logical_tokens": logical,
        "effective_tokens": charged, "charged_tokens": charged,
        "padded_tokens": padded,
        "bucket_padding_tax_pct": _padding_tax(paid, logical),
        "token_source": token_source,
        "filters": list(spec.get("filters") or ()),
        "group_mode": (spec.get("group_types") or {}).get(_group_type(entry, attrs)),
        "group_list_type": _group_type(entry, attrs) if mode == "grouped_prefix" else None,
        "qualification": qualification,
        "kv_extent": kv_extent,
        "valid": not violations, "violations": violations,
    }


def operator_charge(entry: Mapping[str, Any], *, bucket: int,
                    logical: int | None = None,
                    attrs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Charge rows for a known bucket without re-parsing captured descriptors."""
    spec = entry.get("padding_semantics") or {}
    mode = str(spec.get("mode") or "full_padded_tensor")
    bucket = max(0, int(bucket))
    value = bucket if logical is None else max(0, int(logical))
    value = min(value, bucket)
    charged = bucket if mode == "full_padded_tensor" else value
    paid = max(0, charged - value)
    return {"mode": mode, "bucket_tokens": bucket, "logical_tokens": value,
            "charged_tokens": charged, "effective_tokens": charged,
            "padded_tokens": bucket - value,
            "bucket_padding_tax_pct": _padding_tax(paid, value)}


__all__ = [
    "BATCHED_LAYOUTS",
    "TND_LAYOUTS",
    "compute_padding",
    "numeric_list",
    "operator_charge",
    "synthesize_group_list",
    "synthesize_offsets",
    "validate_group_list",
    "validate_sequence_lengths",
]
