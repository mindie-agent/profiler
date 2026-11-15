"""Executable numeric/shape preconditions evaluated before ``ready``.

[Role]
  Check the actual allocated shapes, dtypes, captured values and bound scalar
  attributes for every ``kind`` declared in ``op_api_catalog.json``.  Each
  declared kind has an executable branch; an unknown kind fails closed instead
  of silently returning no problems.

[Invariants]
  * ``aclnnSwiGlu`` rejects an odd split dimension.
  * ``MoeGatingTopKSoftmax`` requires ``1 <= k <= num_experts`` and every
    output shape ``[..., k]``.
  * ``QuantLightningIndexer`` requires compatible quantized/BF16 Q-K dtypes and
    the declared layout's output rank/geometry.
  * ``ChunkGatedDeltaRule`` requires Dk == Dv == 128 and Nv % Nk == 0.
  * ``dst_type`` and ``routing_flags`` verify that the captured flag is the
    value forwarded in the call plan, and validate its type/range.
  * ``tensor_list_spans`` verifies that every declared list has an allocation
    and that declared span lengths match the actual items.
  * ``paged_attention`` validates post-substitution page ids and context
    lengths against the allocated KV cache geometry.
  * A violation is returned, never converted into ``ready``.

[Timeouts & Locks]
  Pure in-memory arithmetic proportional to the allocation list.

[Side-Effect Policy]
  No I/O, device access or torch import.
"""

from __future__ import annotations

import math
from functools import wraps
from typing import Any
from .repro_values import bounded_count, bounded_mapping, bounded_shape, validate_count_attributes, bounded_summary, diagnostic_value, validate_captured_values, validate_container_depth
from .op_abi_attributes import INT_RULES, FLOAT_RULES, STR_ENUMS, attr_issue
from .repro_metadata import _flatten_values, synthesize_metadata, validate_metadata_counts
from .events import ProfilerUsageError

SUPPORTED_PRECONDITION_KINDS = frozenset({
    "even_split_dim", "topk_geometry", "qli_geometry", "rms_norm", "chunk_gdn",
    "attention_geometry", "dst_type", "routing_flags", "tensor_list_spans",
    "paged_attention", "inplace_aliases", "causal_conv", "gdn_inplace",
})


def _shape(by_name: dict[str, Any], name: str) -> list[int] | None:
    spec = by_name.get(name)
    return None if spec is None else [int(value) for value in spec.get("shape") or []]


def _dtype(by_name: dict[str, Any], name: str) -> str | None:
    spec = by_name.get(name)
    return None if spec is None else spec.get("dtype")


def _values(by_name: dict[str, Any], name: str) -> list[Any] | None:
    spec = by_name.get(name)
    return None if spec is None else spec.get("values")


def _plan_keyword(plan: dict[str, Any], name: str) -> dict[str, Any] | None:
    return (plan.get("keyword") or {}).get(name)


def _forwarded(plan: dict[str, Any], name: str) -> Any:
    spec = _plan_keyword(plan, name)
    if spec is None or spec.get("value") is None:
        return None
    return spec["value"]


def _problem(kind: str, detail: str, **extra: Any) -> dict[str, Any]:
    return diagnostic_value({"code": "invalid_precondition", "rule": kind, "detail": detail, **extra})


def _input_problems(attrs, allocations, plan, signature, occurrence=None):
    """Validate direct callers and forwarded values before any handler arithmetic."""
    try:
        validate_container_depth((attrs, allocations, plan, signature))
        validate_count_attributes(attrs)
        kinds = {**dict.fromkeys(INT_RULES, "int"), **dict.fromkeys(FLOAT_RULES, "float"),
                 **dict.fromkeys(STR_ENUMS, "str"), "dim": "int", "axis": "int",
                 "dst_type": "int", "dst_type_max": "float", "quant_mode": "str",
                 "expert_tokens_count_or_cumsum_flag": "int",
                 "expert_tokens_num_flag": "bool", "expert_tokens_before_capacity_flag": "bool",
                 "inplace_final_state": "bool"}
        params = (signature or {}).get("params") or {}
        declared = {name: spec["kind"] for name, spec in params.items() if spec.get("kind")}
        # Callable parameter names can differ from their captured attribute names.
        for call_name, spec in (plan.get("keyword") or {}).items():
            if spec.get("kind") in {"attr", "array"} and call_name in declared:
                declared[spec.get("name", call_name)] = spec.get("capture_kind") or declared[call_name]
        kinds.update(declared)
        candidates = [(name, kinds.get(name), value) for name, value in attrs.items()]
        for call_name, spec in (plan.get("keyword") or {}).items():
            kind = (params.get(call_name) or {}).get("kind")
            name = spec.get("name", call_name)
            kind = kind or kinds.get(name)
            if "value" in spec:
                candidates.append((name, kind, spec["value"]))
        for name, kind, value in candidates:
            if value is None or kind in {None, "tensor", "tensor_list"}:
                continue
            if kind == "int" and isinstance(value, bool):
                issue = {"name": name, "value": bounded_summary(value), "detail": "bool is not int"}
            else:
                issue, _ = attr_issue(name, kind, value)
            if issue:
                return [_problem("attribute", bounded_summary(issue))]
        for spec in allocations:
            shape = spec.get("shape", [])
            bounded_shape(shape)
            dtype = spec.get("dtype")
            if dtype is not None and not isinstance(dtype, str):
                return [_problem("allocation", "invalid dtype " + bounded_summary(dtype))]
            values = spec.get("values")
            if values is None:
                continue
            if spec.get("role") in {"seq_lens", "block_table", "group_list", "index"}:
                if _flatten_values(values, integer_only=True) is None:
                    return [_problem("allocation", "invalid count/index values " + bounded_summary(values))]
            _, problems = validate_captured_values(shape, dtype, values)
            if problems:
                return [_problem("allocation", bounded_summary(problems))]
        validate_metadata_counts({"allocations": allocations, "attrs": attrs})
        if occurrence is not None and any(spec.get("role") in
                {"seq_lens", "group_list", "block_table", "index"} for spec in allocations):
            metadata = synthesize_metadata({**occurrence, "attrs": attrs, "allocations": allocations})
            if any(value is False for value in metadata["checks"].values()):
                return [_problem("metadata", bounded_summary(metadata["violations"]))]
    except ProfilerUsageError as exc:
        return [_problem("cardinality", str(exc))]
    return []


def _validated(handler):
    @wraps(handler)
    def checked(occurrence, attrs, allocations, by_name, plan, rules):
        problems = _input_problems(attrs, allocations or list(by_name.values()), plan,
                                   occurrence.get("signature"), occurrence)
        return problems or handler(occurrence, attrs, allocations, by_name, plan, rules)
    return checked


def _int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


@_validated
def _even_split_dim(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "even_split_dim"
    problems: list[dict[str, Any]] = []
    x_shape = _shape(by_name, "x")
    if not x_shape:
        problems.append(_problem(kind, "missing x shape"))
        return problems
    dim = attrs.get("dim") if attrs.get("dim") is not None else -1
    if not -len(x_shape) <= dim < len(x_shape):
        problems.append(_problem(kind, f"dim {dim} out of range {x_shape}"))
    elif int(x_shape[dim]) % 2:
        problems.append(_problem(kind, f"shape[{dim}]={x_shape[dim]} is odd",
                                 shape=x_shape, dim=dim))
    return problems


@_validated
def _topk_geometry(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "topk_geometry"
    problems: list[dict[str, Any]] = []
    x_shape = _shape(by_name, "x")
    k = attrs.get("k")
    if not x_shape or not isinstance(k, int) or isinstance(k, bool):
        return [_problem(kind, "missing x shape or k")]
    num_experts = int(x_shape[-1])
    if k < 1 or k > num_experts:
        problems.append(_problem(kind, f"k={k} not in [1, {num_experts}]"))
    for name in ("y", "expert_idx", "out"):
        out_shape = _shape(by_name, name)
        if out_shape is None or list(out_shape[:-1]) != list(x_shape[:-1]) \
                or (out_shape and out_shape[-1] != k):
            problems.append(_problem(kind,
                                     f"{name} shape {out_shape} != {x_shape[:-1]}+[k]"))
    return problems


@_validated
def _qli_geometry(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "qli_geometry"
    problems: list[dict[str, Any]] = []
    query, key, out = _shape(by_name, "query"), _shape(by_name, "key"), _shape(by_name, "out")
    qd, kd = _dtype(by_name, "query"), _dtype(by_name, "key")
    quantized = {"int8", "fp8_e4m3", "fp8_e5m2"}
    if qd is None or kd is None:
        problems.append(_problem(kind, "missing query/key dtype"))
    elif qd != kd:
        problems.append(_problem(kind, f"query dtype {qd} != key dtype {kd}"))
    elif qd not in quantized | {"bf16", "fp16"}:
        problems.append(_problem(kind, f"unsupported dtype {qd}"))
    layout = str((occurrence.get("padding") or {}).get("layout") or "TND")
    expected_rank = {"TND": 3, "BSND": 4}.get(layout)
    if expected_rank is not None:
        if not query or len(query) != expected_rank:
            problems.append(_problem(kind, f"query rank {query} != {expected_rank}"))
        if out is None or len(out) != expected_rank:
            problems.append(_problem(kind, f"out rank {out} != {expected_rank}"))
    out_dtype = _dtype(by_name, "out")
    if out_dtype is not None and out_dtype not in {"int32", "int64"}:
        problems.append(_problem(kind, f"out dtype {out_dtype} is not an index dtype"))
    if query and out:
        if out[0] != query[0]:
            problems.append(_problem(kind, f"out[0] {out[0]} != query[0] {query[0]}"))
        sparse = attrs.get("sparse_count")
        if isinstance(sparse, int) and sparse > 0 and out[-1] != sparse:
            problems.append(_problem(kind, f"out[-1] {out[-1]} != sparse_count {sparse}"))
    return problems


@_validated
def _rms_norm(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "rms_norm"
    epsilon = attrs.get("epsilon", 1e-6)
    try:
        number = float(epsilon)
    except (TypeError, ValueError, OverflowError):
        return [_problem(kind, f"epsilon {epsilon!r}")]
    if not math.isfinite(number) or number <= 0 or number > 1:
        return [_problem(kind, f"epsilon {number} not in (0, 1]")]
    return []


@_validated
def _chunk_gdn(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "chunk_gdn"
    problems: list[dict[str, Any]] = []
    q, k, v = _shape(by_name, "q"), _shape(by_name, "k"), _shape(by_name, "v")
    if not (q and k and v):
        return [_problem(kind, "q/k/v allocations are missing")]
    if q and k and v:
        if q[-1] != 128 or v[-1] != 128:
            problems.append(_problem(kind, f"Dk={q[-1]} Dv={v[-1]} must both be 128"))
        nk = q[-2] if len(q) >= 2 else 0
        nv = v[-2] if len(v) >= 2 else 0
        if not nk or nv % nk:
            problems.append(_problem(kind, f"Nv={nv} % Nk={nk} != 0"))
        seq = by_name.get("actual_seq_lengths")
        if seq and seq.get("values") is not None:
            total = sum(_flatten_values(seq["values"], integer_only=True))
            if total > q[0]:
                problems.append(_problem(kind, f"sum(lengths)={total} > T={q[0]}"))
    return problems


@_validated
def _attention_geometry(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "attention_geometry"
    problems: list[dict[str, Any]] = []
    heads = attrs.get("head_num", attrs.get("num_heads"))
    if heads is not None and (not isinstance(heads, int) or isinstance(heads, bool)
                              or heads < 1):
        problems.append(_problem(kind, f"head count {heads!r}"))
    kv_heads = attrs.get("num_key_value_heads", attrs.get("num_kv_heads"))
    if (isinstance(heads, int) and not isinstance(heads, bool)
            and isinstance(kv_heads, int) and not isinstance(kv_heads, bool)
            and not 0 < kv_heads <= heads):
        problems.append(_problem(kind, f"num_kv_heads={kv_heads} not in [1, {heads}]"))
    dtypes = {name: _dtype(by_name, name) for name in ("query", "key", "value")}
    present = {name: value for name, value in dtypes.items() if value is not None}
    if len(set(present.values())) > 1:
        problems.append(_problem(kind, f"query/key/value dtype mismatch: {present}"))
    layout = str(attrs.get("input_layout") or "")
    query = _shape(by_name, "query")
    if layout == "TND" and query and len(query) != 3:
        problems.append(_problem(kind, f"TND query rank {query} != 3"))
    if layout == "BSH" and query and len(query) != 3:
        problems.append(_problem(kind, f"BSH query rank {query} != 3"))
    if layout in {"BSND", "BNSD"} and query and len(query) != 4:
        problems.append(_problem(kind, f"{layout} query rank {query} != 4"))
    batch_axis = {"BSH": 0, "BSND": 0, "BNSD": 0, "SBH": 1}.get(layout)
    if batch_axis is not None:
        shapes = {name: _shape(by_name, name)
                  for name in ("query", "key", "value")}
        batches = {name: shape[batch_axis]
                   for name, shape in shapes.items()
                   if shape and batch_axis < len(shape)}
        if len(set(batches.values())) > 1:
            problems.append(_problem(
                kind, f"Q/K/V batch cardinality mismatch: {batches}"))
    if layout == "TND":
        q_vector = attrs.get("actual_seq_q_len")
        if q_vector is None:
            q_vector = attrs.get("actual_seq_lengths")
        kv_vector = attrs.get("actual_seq_kv_len")
        if kv_vector is None:
            kv_vector = attrs.get("actual_seq_lengths_kv")
        if (isinstance(q_vector, (list, tuple))
                and isinstance(kv_vector, (list, tuple))
                and len(q_vector) != len(kv_vector)):
            problems.append(_problem(
                kind, f"actual_seq Q/KV vector arity {len(q_vector)} != "
                      f"{len(kv_vector)}"))
    table = _shape(by_name, "block_table")
    if (table and query
            and ("key_cache" in by_name or "value_cache" in by_name)
            and table[0] != query[0]):
        problems.append(_problem(
            kind, f"paged query batch {query[0]} != block_table batch {table[0]}"))
    forwarded_heads = _forwarded(plan, "head_num")
    if heads is not None and forwarded_heads is not None and forwarded_heads != heads:
        problems.append(_problem(kind, f"head_num forwarded {forwarded_heads} != {heads}"))
    return problems


@_validated
def _dst_type(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "dst_type"
    problems: list[dict[str, Any]] = []
    dst = attrs.get("dst_type")
    if dst is not None:
        number = _int(dst)
        if number is None or number < 0:
            problems.append(_problem(kind, f"dst_type {dst!r} is not a non-negative int"))
        forwarded = _forwarded(plan, "dst_type")
        if forwarded is not None and forwarded != dst:
            problems.append(_problem(kind,
                                     f"dst_type forwarded {forwarded!r} != captured {dst!r}"))
    quant_mode = attrs.get("quant_mode")
    if quant_mode is not None and not isinstance(quant_mode, str):
        problems.append(_problem(kind, f"quant_mode {quant_mode!r} is not str"))
    if "quant_mode" in (plan.get("keyword") or {}) and quant_mode is not None:
        forwarded = _forwarded(plan, "quant_mode")
        if forwarded is not None and forwarded != quant_mode:
            problems.append(_problem(
                kind, f"quant_mode forwarded {forwarded!r} != captured {quant_mode!r}"))
    dst_max = attrs.get("dst_type_max")
    if dst_max is not None:
        try:
            number = float(dst_max)
        except (TypeError, ValueError, OverflowError):
            problems.append(_problem(kind, f"dst_type_max {dst_max!r} is not numeric"))
        else:
            if not math.isfinite(number):
                problems.append(_problem(kind, "dst_type_max is non-finite"))
    return problems


@_validated
def _routing_flags(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "routing_flags"
    problems: list[dict[str, Any]] = []
    count_type = attrs.get("expert_tokens_num_type",
                           attrs.get("expert_tokens_count_or_cumsum_flag"))
    if count_type is not None and count_type not in {0, 1}:
        problems.append(_problem(kind,
                                 f"expert_tokens_num_type {count_type!r} not in {{0, 1}}"))
    flag = attrs.get("expert_tokens_num_flag",
                     attrs.get("expert_tokens_before_capacity_flag"))
    if flag is not None and not isinstance(flag, bool):
        problems.append(_problem(kind, f"expert_tokens_num_flag {flag!r} is not bool"))
    expert_num = attrs.get("expert_num")
    if expert_num is not None and (not isinstance(expert_num, int)
                                   or isinstance(expert_num, bool) or expert_num < 1):
        problems.append(_problem(kind, f"expert_num {expert_num!r} is not positive int"))
    forwarded_type = _forwarded(plan, "expert_tokens_num_type")
    if (count_type is not None and forwarded_type is not None
            and forwarded_type != count_type):
        problems.append(_problem(
            kind, f"expert_tokens_num_type forwarded {forwarded_type!r} != {count_type!r}"))
    forwarded_flag = _forwarded(plan, "expert_tokens_num_flag")
    if flag is not None and forwarded_flag is not None and forwarded_flag != flag:
        problems.append(_problem(
            kind, f"expert_tokens_num_flag forwarded {forwarded_flag!r} != {flag!r}"))
    idx = _shape(by_name, "expert_idx")
    if idx is None:
        problems.append(_problem(kind, "expert_idx allocation is missing"))
    elif not idx or idx[0] <= 0:
        problems.append(_problem(kind, f"expert_idx shape {idx} is empty"))
    active = attrs.get("active_expert_range")
    forwarded = _forwarded(plan, "active_expert_range")
    for label, value in (("captured", active), ("forwarded", forwarded)):
        if value is None:
            continue
        if not isinstance(value, (list, tuple)) or len(value) not in {0, 2} \
                or any(isinstance(item, bool) or not isinstance(item, int)
                       for item in value):
            problems.append(_problem(
                kind, f"active_expert_range {label} {value!r} is not int[2]"))
            continue
        if any(item < 0 for item in value):
            problems.append(_problem(
                kind, f"active_expert_range {label} has a negative bound"))
        elif len(value) == 2 and value[0] >= value[1]:
            problems.append(_problem(
                kind, f"active_expert_range {label} {value} is not ordered"))
        elif len(value) == 2 and isinstance(expert_num, int) \
                and not isinstance(expert_num, bool) and value[1] > expert_num:
            problems.append(_problem(
                kind, f"active_expert_range {label} {value} > expert_num {expert_num}"))
    if active is not None and forwarded is not None and forwarded != active:
        problems.append(_problem(
            kind, f"active_expert_range forwarded {forwarded!r} != {active!r}"))
    return problems


@_validated
def _tensor_list_spans(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "tensor_list_spans"
    problems: list[dict[str, Any]] = []
    declared_lists: set[str] = set()
    span_lengths = attrs.get("tensor_list_lengths")
    span_lengths = span_lengths if isinstance(span_lengths, dict) else {}
    for name, spec in (plan.get("keyword") or {}).items():
        if spec.get("kind") != "tensor_list":
            continue
        declared_lists.add(name)
        count = len([item for item in allocations
                     if item.get("tensor_list") == name])
        if count < 1 and not spec.get("optional"):
            problems.append(_problem(kind, f"required tensor list {name} is empty"))
        expected = attrs.get(f"{name}_len", span_lengths.get(name))
        if expected is not None:
            expected_number = bounded_count(expected, "tensor list span", 0, 1024)
            if count != expected_number:
                problems.append(_problem(
                    kind, f"{name} span declared {expected_number} but has {count} items"))
    declared_lists.update(str(name) for name in plan.get("outputs") or ())
    declared_lists.update(str(name) for name in plan.get("mutable_aliases") or ())
    declared_lists.update(str(item["tensor_list"]) for item in allocations
                          if item.get("direction") == "output"
                          and item.get("tensor_list"))
    for item in allocations:
        list_name = item.get("tensor_list")
        if list_name and list_name not in declared_lists:
            problems.append(_problem(kind, f"undeclared tensor list {list_name}"))
    return problems


@_validated
def _paged_attention(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "paged_attention"
    problems: list[dict[str, Any]] = []
    caches = [by_name[name] for name in ("key_cache", "value_cache", "kv_cache")
              if by_name.get(name) is not None]
    table = by_name.get("block_table")
    context = by_name.get("context_lens")
    if not caches or table is None or context is None:
        return [_problem(kind, "kv cache/block_table/context_lens allocation missing")]
    cache_shapes = [[int(value) for value in cache.get("shape") or []]
                    for cache in caches]
    capacities = [shape[0] for shape in cache_shapes if shape]
    pages = min(capacities) if capacities else 0
    if any(shape[1:] != cache_shapes[0][1:] for shape in cache_shapes[1:]):
        problems.append(_problem(
            kind, f"kv cache shapes are incompatible: {cache_shapes}"))
    table_shape = [int(value) for value in table.get("shape") or []]
    cols = table_shape[1] if len(table_shape) > 1 else 0
    if not pages:
        problems.append(_problem(kind, "kv cache has no allocated pages"))
    if len(table_shape) != 2 or cols < 1:
        problems.append(_problem(kind, f"block_table shape {table_shape} is not [rows, cols]"))
    if len(cache_shapes[0]) < 2:
        problems.append(_problem(
            kind, f"kv cache shape {cache_shapes[0]} needs a page size"))
    if table.get("dtype") not in {"int32", "int64"}:
        problems.append(_problem(kind, f"block_table dtype {table.get('dtype')!r} is not int"))
    query = _shape(by_name, "query")
    out = _shape(by_name, "out")
    if query and out and list(query[:-1]) != list(out[:-1]):
        problems.append(_problem(kind, f"out shape {out} incompatible with query {query}"))
    context_shape = [int(value) for value in context.get("shape") or []]
    if context_shape and table_shape and context_shape[0] > table_shape[0]:
        problems.append(_problem(
            kind, f"context items {context_shape[0]} > table rows {table_shape[0]}"))
    return problems


@_validated
def _inplace_aliases(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "inplace_aliases"
    problems: list[dict[str, Any]] = []
    aliases = list(plan.get("mutable_aliases") or ())
    if not aliases:
        problems.append(_problem(kind, "no mutable aliases declared"))
    for alias in aliases:
        spec = by_name.get(alias)
        if spec is None:
            problems.append(_problem(kind, f"alias {alias} is not allocated"))
        elif spec.get("direction") != "input":
            problems.append(_problem(kind, f"alias {alias} is not an input"))
    flag = attrs.get("inplace_final_state")
    if flag is not None and not isinstance(flag, bool):
        problems.append(_problem(kind, f"inplace_final_state {flag!r} is not bool"))
    if aliases and "inplace_final_state" in attrs and attrs.get("inplace_final_state"):
        problems.append(_problem(kind, "inplace_final_state conflicts with tensor aliases"))
    return problems


@_validated
def _causal_conv(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "causal_conv"
    problems: list[dict[str, Any]] = []
    activation_name = None
    for name in ("activation", "x", "input"):
        if name in by_name:
            activation_name = name
            break
    if activation_name is None:
        return [_problem(kind, "activation allocation missing")]
    shape = _shape(by_name, activation_name) or []
    if len(shape) < 2:
        problems.append(_problem(kind, f"activation rank {shape} < 2"))
    pad_slot = attrs.get("pad_slot_id")
    if pad_slot is not None:
        number = _int(pad_slot)
        if number is None or number < 0 or (shape and number >= shape[-1]):
            problems.append(_problem(kind, f"pad_slot_id {pad_slot!r} outside activation"))
    if "pad_slot_id" in (plan.get("keyword") or {}) and pad_slot is None:
        problems.append(_problem(kind, "pad_slot_id is declared but not captured"))
    return problems


@_validated
def _gdn_inplace(occurrence, attrs, allocations, by_name, plan, rules):
    kind = "gdn_inplace"
    problems: list[dict[str, Any]] = []
    scale = attrs.get("scale")
    if scale is not None:
        try:
            number = float(scale)
        except (TypeError, ValueError, OverflowError):
            problems.append(_problem(kind, f"scale {scale!r} is not numeric"))
        else:
            if not math.isfinite(number) or number <= 0:
                problems.append(_problem(kind, f"scale {number} not finite positive"))
    flag = attrs.get("inplace_final_state")
    if flag is not None and not isinstance(flag, bool):
        problems.append(_problem(kind, f"inplace_final_state {flag!r} is not bool"))
    state = _shape(by_name, "initial_state")
    if state is None:
        problems.append(_problem(kind, "initial_state allocation missing"))
    elif len(state) != 4:
        problems.append(_problem(kind, f"initial_state rank {state} != 4"))
    return problems


_HANDLERS = {
    "even_split_dim": _even_split_dim,
    "topk_geometry": _topk_geometry,
    "qli_geometry": _qli_geometry,
    "rms_norm": _rms_norm,
    "chunk_gdn": _chunk_gdn,
    "attention_geometry": _attention_geometry,
    "dst_type": _dst_type,
    "routing_flags": _routing_flags,
    "tensor_list_spans": _tensor_list_spans,
    "paged_attention": _paged_attention,
    "inplace_aliases": _inplace_aliases,
    "causal_conv": _causal_conv,
    "gdn_inplace": _gdn_inplace,
}


def precondition_problems(occurrence: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate executable numeric/shape preconditions before ``ready``."""
    try:
        occurrence = bounded_mapping(occurrence, "occurrence")
    except ProfilerUsageError as exc:
        return [_problem("cardinality", str(exc))]
    problems = _input_problems(occurrence.get("attrs") or {}, occurrence.get("allocations") or [],
                              occurrence.get("call_plan") or {}, occurrence.get("signature"), occurrence)
    if problems:
        return problems
    rules = occurrence.get("preconditions")
    if not rules:
        return []
    if isinstance(rules, list):
        return [{"code": "unhandled_precondition", "rule": bounded_summary(item),
                 "detail": "declarative requirement is not executable"} for item in rules]
    if not isinstance(rules, dict):
        return [{"code": "unhandled_precondition", "rule": bounded_summary(rules)}]
    kind = rules.get("kind") or ""
    if not isinstance(kind, str):
        return [{"code": "unhandled_precondition", "rule": bounded_summary(kind)}]
    handler = _HANDLERS.get(kind)
    if handler is None:
        return [{"code": "unhandled_precondition", "rule": kind or None}]
    plan = occurrence.get("call_plan") or {}
    attrs = occurrence.get("attrs") or {}
    allocations = occurrence.get("allocations") or []
    by_name = {spec["name"]: spec for spec in allocations}
    return handler(occurrence, attrs, allocations, by_name, plan, rules)


__all__ = ["SUPPORTED_PRECONDITION_KINDS", "precondition_problems"]
