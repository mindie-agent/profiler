"""BIND1 native-call tensor signature parsing and role-paired shape/dtype matching.

[Role]
  Parse captured semicolon-delimited tensor shape/dtype/format lanes and match
  them against ``mindie-sim`` ``BIND1`` ``typed`` declarations while preserving
  native input/output role slot ordering and per-role dtypes.

[Invariants]
  * Input and output lanes are paired index-by-index across shape, dtype, and
    format; unequal lane counts fail closed (``False``) and incomplete capture
    columns resolve to ``None`` rather than a guessed match.
  * Declared native roles preserve canonical ABI slot order (e.g. ``query`` ->
    ``key`` -> ``value``, ``input`` -> ``weight`` -> optional scales/bias) and
    role-specific dtypes; swapped operand slots return ``False``, and role sets
    without an established slot order resolve to ``None`` rather than ``True``.
  * Contiguous/ND layout declarations reject non-contiguous Ascend storage
    formats cleanly after case-normalization (including ``C1HWNCoC0``).

[Timeouts & Locks]
  Pure in-memory tuple/slot inspection per candidate binding; no I/O or locks.

[Side-Effect Policy]
  Pure functions; does not mutate caller bindings, events, or global state.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from .events import Event

_MISSING_TEXT = frozenset({"", "N/A", "NULL", "NONE", "UNDEFINED"})
_UNDEFINED_DTYPES = frozenset({"", "N/A", "NULL", "NONE", "UNDEFINED", "DT_UNDEFINED"})
_ATTENTION_AUX_DTYPES = frozenset(
    {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "bool"}
)
_DTYPE_TOKENS = {
    **dict.fromkeys(("BF16", "BFP16", "BFLOAT16", "DT_BF16", "DT_BFLOAT16"), "bf16"),
    **dict.fromkeys(("FP16", "HALF", "FLOAT16", "DT_FLOAT16", "DT_HALF"), "fp16"),
    **dict.fromkeys(("FP32", "FLOAT", "FLOAT32", "DT_FLOAT", "DT_FLOAT32"), "fp32"),
    **dict.fromkeys(("FP64", "DOUBLE", "FLOAT64", "DT_DOUBLE", "DT_FLOAT64"), "fp64"),
    **dict.fromkeys(("INT4", "DT_INT4"), "int4"),
    **dict.fromkeys(("INT8", "DT_INT8"), "int8"),
    **dict.fromkeys(("INT16", "DT_INT16"), "int16"),
    **dict.fromkeys(("INT32", "DT_INT32"), "int32"),
    **dict.fromkeys(("INT64", "DT_INT64"), "int64"),
    **dict.fromkeys(("UINT8", "DT_UINT8"), "uint8"),
    **dict.fromkeys(("UINT16", "DT_UINT16"), "uint16"),
    **dict.fromkeys(("UINT32", "DT_UINT32"), "uint32"),
    **dict.fromkeys(("UINT64", "DT_UINT64"), "uint64"),
    **dict.fromkeys(("BOOL", "DT_BOOL"), "bool"),
    **dict.fromkeys(("HIF8", "HIFLOAT8", "DT_HIFLOAT8"), "hif8"),
    **dict.fromkeys(("FP8_E4M3", "FP8_E4M3FN", "FLOAT8_E4M3FN", "DT_FLOAT8_E4M3FN"), "fp8_e4m3"),
    **dict.fromkeys(("FP8_E5M2", "FLOAT8_E5M2", "DT_FLOAT8_E5M2"), "fp8_e5m2"),
    **dict.fromkeys(("FP8_E8M0", "FLOAT8_E8M0", "DT_FLOAT8_E8M0"), "fp8_e8m0"),
    **dict.fromkeys(("MXFP4", "FLOAT4_E2M1", "DT_FLOAT4_E2M1"), "mxfp4"),
}
_NON_CONTIGUOUS_FORMATS = frozenset(
    {"FRACTAL_NZ", "FRACTAL_Z", "FRACTAL_Z_3D", "NC1HWC0", "NDC1HWC0", "C1HWNCOC0"}
)
_COARSE_SHAPE_KEYS = frozenset(
    {"local", "padded", "launch", "payload", "active_query", "nz_storage", "nz_logical_storage"}
)
_OUTPUT_SHAPE_KEYS = frozenset({"output", "out", "y", "outputs"})
_PRIMARY_INPUT_KEYS = ("input", "x", "lhs", "activation", "query", "q")
_TAIL_INPUT_ROLES = frozenset({"key_tail", "value_tail"})
_PARTIAL_CACHE_ROLES = frozenset({"cache_head", "rope_cache_head", "slot"})
_INPUT_ROLE_ORDER: dict[str, int] = {
    "input": 0,
    "x": 0,
    "lhs": 0,
    "activation": 0,
    "query": 0,
    "q": 0,
    "weight": 1,
    "rhs": 1,
    "w": 1,
    "key": 2,
    "k": 2,
    "key_tail": 2,
    "cache": 2,
    "value": 3,
    "v": 3,
    "value_tail": 3,
    "query_rope": 4,
    "rope_cache": 5,
    "residual": 6,
    "gamma": 7,
    "norm_weight": 7,
    "beta": 8,
    "norm_bias": 8,
    "gate": 9,
    "scale": 10,
    "weight_scale": 10,
    "bias": 11,
    "input_scale": 12,
    "activation_scale": 12,
    "group_list": 13,
    "indices": 14,
    "sparse_indices": 14,
}
_OUTPUT_ROLE_ORDER: dict[str, int] = {"output": 0, "out": 0, "y": 0}
_AUX_ONLY_ROLES = frozenset(
    {
        "group_list",
        "input_scale",
        "activation_scale",
        "scale",
        "weight_scale",
        "indices",
        "sparse_indices",
    }
)
_OPTIONAL_INPUT_KEYS = _AUX_ONLY_ROLES | frozenset({"bias", "residual"})
_ROLE_DTYPE_KEYS: dict[str, tuple[str, ...]] = {
    "input": ("input_dtype", "activation_dtype", "activation_format", "x_dtype", "lhs_dtype"),
    "x": ("x_dtype", "input_dtype", "activation_dtype", "activation_format"),
    "lhs": ("lhs_dtype", "input_dtype", "activation_dtype", "activation_format"),
    "activation": ("activation_dtype", "activation_format", "input_dtype"),
    "weight": ("weight_dtype", "weight_format", "rhs_dtype", "w_dtype"),
    "rhs": ("rhs_dtype", "weight_dtype", "weight_format"),
    "w": ("w_dtype", "weight_dtype", "weight_format"),
    "bias": ("bias_dtype",),
    "residual": ("residual_dtype", "input_dtype"),
    "gate": ("gate_dtype", "input_dtype"),
    "gamma": ("gamma_dtype", "norm_parameter_dtype", "parameter_dtype"),
    "beta": ("beta_dtype", "norm_parameter_dtype", "parameter_dtype"),
    "norm_weight": ("norm_weight_dtype", "norm_parameter_dtype", "parameter_dtype"),
    "norm_bias": ("norm_bias_dtype", "norm_parameter_dtype", "parameter_dtype"),
    "query": ("query_dtype",),
    "q": ("query_dtype",),
    "query_rope": ("query_rope_dtype", "query_dtype"),
    "key": ("key_dtype", "kv_dtype", "cache_dtype"),
    "k": ("key_dtype", "kv_dtype", "cache_dtype"),
    "key_tail": ("key_dtype", "kv_dtype", "cache_dtype"),
    "value": ("value_dtype", "kv_dtype", "cache_dtype"),
    "v": ("value_dtype", "kv_dtype", "cache_dtype"),
    "value_tail": ("value_dtype", "kv_dtype", "cache_dtype"),
    "cache": ("cache_dtype", "kv_dtype", "key_dtype"),
    "cache_head": ("cache_dtype", "kv_dtype", "key_dtype"),
    "rope_cache": ("rope_cache_dtype", "cache_dtype", "key_dtype"),
    "rope_cache_head": ("rope_cache_dtype", "cache_dtype", "key_dtype"),
    "group_list": ("group_list_dtype",),
    "input_scale": ("input_scale_dtype", "activation_scale_dtype", "activation_scale_format", "scale_dtype"),
    "activation_scale": ("activation_scale_dtype", "activation_scale_format", "input_scale_dtype", "scale_dtype"),
    "scale": ("scale_dtype", "weight_scale_dtype"),
    "weight_scale": ("weight_scale_dtype", "scale_dtype"),
    "indices": ("index_dtype",),
    "sparse_indices": ("index_dtype",),
}
_DECLARED_INPUT_DTYPE_ROLES: tuple[tuple[str, frozenset[str]], ...] = (
    ("weight_dtype", frozenset({"weight", "rhs", "w"})),
    ("weight_format", frozenset({"weight", "rhs", "w"})),
    ("rhs_dtype", frozenset({"weight", "rhs", "w"})),
    ("w_dtype", frozenset({"weight", "rhs", "w"})),
    ("key_dtype", frozenset({"key", "k", "key_tail"})),
    ("value_dtype", frozenset({"value", "v", "value_tail"})),
    (
        "cache_dtype",
        frozenset(
            {
                "key",
                "k",
                "key_tail",
                "value",
                "v",
                "value_tail",
                "cache",
                "cache_head",
                "rope_cache",
                "rope_cache_head",
            }
        ),
    ),
    ("kv_dtype", frozenset({"key", "k", "key_tail", "value", "v", "value_tail", "cache", "cache_head"})),
    ("bias_dtype", frozenset({"bias"})),
    ("norm_parameter_dtype", frozenset({"gamma", "beta", "norm_weight", "norm_bias"})),
    ("parameter_dtype", frozenset({"gamma", "beta", "norm_weight", "norm_bias"})),
    ("group_list_dtype", frozenset({"group_list"})),
    ("scale_dtype", frozenset({"scale", "weight_scale", "input_scale", "activation_scale"})),
    ("weight_scale_dtype", frozenset({"scale", "weight_scale"})),
    ("input_scale_dtype", frozenset({"input_scale", "activation_scale"})),
    ("activation_scale_dtype", frozenset({"input_scale", "activation_scale"})),
    ("activation_scale_format", frozenset({"input_scale", "activation_scale"})),
    ("index_dtype", frozenset({"indices", "sparse_indices"})),
)


def _norm_dtype(raw: Any) -> str | None:
    text = str(raw or "").strip().strip('"')
    upper = text.upper()
    if upper in _UNDEFINED_DTYPES:
        return None
    return _DTYPE_TOKENS.get(upper, text.lower().removeprefix("dt_"))


def parse_paired_lanes(
    shapes_text: str | None,
    dtypes_text: str | None,
    formats_text: str | None = None,
) -> tuple[str, tuple[tuple[int, ...], ...], tuple[str, ...], tuple[str, ...]]:
    """Parse semicolon-separated shape/dtype/format strings into aligned lanes."""
    s_whole = str(shapes_text or "").strip().strip('"')
    d_whole = str(dtypes_text or "").strip().strip('"')
    f_whole = str(formats_text or "").strip().strip('"')
    if s_whole.upper() in _MISSING_TEXT or d_whole.upper() in _MISSING_TEXT:
        return "missing", (), (), ()
    s_parts = s_whole.split(";")
    d_parts = d_whole.split(";")
    if len(s_parts) != len(d_parts):
        return "mismatch", (), (), ()
    has_formats = f_whole.upper() not in _MISSING_TEXT
    f_parts = f_whole.split(";") if has_formats else None
    if f_parts is not None and len(f_parts) != len(d_parts):
        return "mismatch", (), (), ()
    shapes: list[tuple[int, ...]] = []
    dtypes: list[str] = []
    formats: list[str] = []
    for idx, raw_d in enumerate(d_parts):
        s_cell = s_parts[idx].strip().strip('"')
        d_cell = raw_d.strip().strip('"')
        f_cell = f_parts[idx].strip().strip('"').upper() if f_parts is not None else ""
        if d_cell.upper() in _UNDEFINED_DTYPES:
            if s_cell.upper() in _MISSING_TEXT:
                continue
            return "missing", (), (), ()
        dt = _norm_dtype(d_cell)
        if dt is None or s_cell.upper() in {"N/A", "NULL", "NONE", "UNDEFINED"}:
            return "missing", (), (), ()
        if s_cell == "":
            dims: tuple[int, ...] = ()
        else:
            try:
                dims = tuple(int(value) for value in s_cell.split(",") if value.strip())
            except ValueError:
                return "missing", (), (), ()
            if not dims:
                return "missing", (), (), ()
        shapes.append(dims)
        dtypes.append(dt)
        if f_parts is not None:
            if f_cell in _MISSING_TEXT:
                return "missing", (), (), ()
            formats.append(f_cell)
    if not shapes:
        return "missing", (), (), ()
    return "ok", tuple(shapes), tuple(dtypes), tuple(formats)


def event_signature(
    event: Event,
) -> tuple[tuple[tuple[int, ...], ...], tuple[str, ...]] | None:
    """Parsed shape/dtype lanes of a captured event, or None when incomplete."""
    in_status, inputs, input_dtypes, _ = parse_paired_lanes(
        event.input_shapes, event.input_dtypes, event.input_formats
    )
    out_status, outputs, output_dtypes, _ = parse_paired_lanes(
        event.output_shapes, event.output_dtypes, event.output_formats
    )
    if in_status != "ok" or out_status != "ok":
        return None
    return (*inputs, *outputs), (*input_dtypes, *output_dtypes)


def _counter_leq(left: Counter[Any], right: Counter[Any]) -> bool:
    return all(left[key] <= right[key] for key in left)


def _as_shape_tuple(value: Any) -> tuple[int, ...] | None:
    if (
        isinstance(value, (list, tuple))
        and value
        and all(isinstance(v, int) and not isinstance(v, bool) for v in value)
    ):
        return tuple(value)
    return None


def _lookup_dtype(typed: Mapping[str, Any], attrs: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        raw = typed.get(key)
        if raw is None:
            raw = attrs.get(key)
        if (dt := _norm_dtype(raw)) is not None:
            return dt
    return None


def _parse_declared_shapes(
    shapes_field: Any,
) -> tuple[
    dict[str, tuple[int, ...]],
    dict[str, tuple[int, ...]],
    dict[str, tuple[int, ...]],
    tuple[tuple[int, ...], ...] | None,
    tuple[tuple[int, ...], ...] | None,
] | None:
    if not isinstance(shapes_field, Mapping) or not shapes_field:
        return None
    coarse: dict[str, tuple[int, ...]] = {}
    in_roles: dict[str, tuple[int, ...]] = {}
    out_roles: dict[str, tuple[int, ...]] = {}
    exp_in: tuple[tuple[int, ...], ...] | None = None
    exp_out: tuple[tuple[int, ...], ...] | None = None
    for raw_key, raw_val in shapes_field.items():
        key = str(raw_key).strip().lower()
        if key in {"inputs", "outputs"} and isinstance(raw_val, (list, tuple)):
            parsed_seq = [_as_shape_tuple(item) for item in raw_val]
            if parsed_seq and all(item is not None for item in parsed_seq):
                seq = tuple(item for item in parsed_seq if item is not None)
                if key == "inputs":
                    exp_in = seq
                else:
                    exp_out = seq
                continue
        if (shape := _as_shape_tuple(raw_val)) is None:
            continue
        if key in _COARSE_SHAPE_KEYS:
            coarse[key] = shape
        elif key in _OUTPUT_SHAPE_KEYS:
            out_roles[key] = shape
        else:
            in_roles[key] = shape
    return coarse, in_roles, out_roles, exp_in, exp_out


def _role_order_established(
    roles: Mapping[str, Any], order_map: Mapping[str, int]
) -> list[str] | None:
    if any(k not in order_map for k in roles):
        return None
    ranks = [order_map[k] for k in roles]
    if len(set(ranks)) != len(ranks):
        return None
    return sorted(roles, key=lambda k: order_map[k])


def _align_ordered_specs(
    obs_pairs: tuple[tuple[tuple[int, ...], str], ...],
    ordered_specs: tuple[tuple[tuple[int, ...], str | None, bool, bool], ...],
    *,
    ignore_dtype: bool = False,
) -> int:
    """Return 2 on exact ordered match, 1 on shape-matched untyped ambiguity, 0 on mismatch."""
    memo: dict[tuple[int, int], int] = {}

    def solve(oi: int, si: int) -> int:
        state = (oi, si)
        if state in memo:
            return memo[state]
        if oi == len(obs_pairs):
            res = 2 if all(spec[2] for spec in ordered_specs[si:]) else 0
            memo[state] = res
            return res
        if si == len(ordered_specs):
            memo[state] = 0
            return 0
        shape, exp_dt, is_opt, is_tail = ordered_specs[si]
        obs_shape, obs_dt = obs_pairs[oi]
        best = solve(oi, si + 1) if is_opt else 0
        shape_ok = (
            len(obs_shape) == len(shape) + 1 and obs_shape[1:] == shape
            if is_tail
            else obs_shape == shape
        )
        if shape_ok:
            if ignore_dtype or (exp_dt is not None and obs_dt == exp_dt):
                sub = solve(oi + 1, si + 1)
                if sub > best:
                    best = sub
            elif exp_dt is None:
                sub = solve(oi + 1, si + 1)
                if sub > 0:
                    best = max(best, 1)
        memo[state] = best
        return best

    return solve(0, 0)


def _match_input_dtypes(
    *,
    typed: Mapping[str, Any],
    attrs: Mapping[str, Any],
    input_roles: Mapping[str, tuple[int, ...]],
    explicit_inputs: tuple[tuple[int, ...], ...] | None,
    in_shapes: tuple[tuple[int, ...], ...],
    in_dtypes: tuple[str, ...],
    declared_dtype: str | None,
    primary_in_dt: str | None,
    is_attention_abi: bool,
) -> bool | None:
    explicit_in_dtypes = typed.get("input_dtypes")
    if isinstance(explicit_in_dtypes, (list, tuple)):
        normed_in = [_norm_dtype(raw) for raw in explicit_in_dtypes]
        if not normed_in or any(dt is None for dt in normed_in):
            return None
        return in_dtypes == tuple(dt for dt in normed_in if dt is not None)

    has_complete_roles = bool(input_roles) and (
        explicit_inputs is None or len(explicit_inputs) <= len(input_roles)
    )
    if not has_complete_roles:
        allowed_pos = {primary_in_dt} if primary_in_dt is not None else set()
        has_distinct_role_dt = False
        for attr_key, target_roles in _DECLARED_INPUT_DTYPE_ROLES:
            if (decl_dt := _lookup_dtype(typed, attrs, attr_key)) is None:
                continue
            allowed_pos.add(decl_dt)
            if decl_dt not in in_dtypes:
                if not (target_roles <= _OPTIONAL_INPUT_KEYS):
                    return False
                continue
            if decl_dt != primary_in_dt:
                has_distinct_role_dt = True
        if primary_in_dt is not None:
            checked_in = (
                tuple(
                    dt
                    for s, dt in zip(in_shapes, in_dtypes)
                    if dt not in (_ATTENTION_AUX_DTYPES - allowed_pos) and s != ()
                )
                if is_attention_abi
                else in_dtypes
            )
            if any(dt not in allowed_pos for dt in checked_in):
                return False
            if has_distinct_role_dt:
                return None
            if in_dtypes[0] != primary_in_dt or any(dt != primary_in_dt for dt in checked_in):
                return False
        elif has_distinct_role_dt:
            return None
        return True

    for attr_key, target_roles in _DECLARED_INPUT_DTYPE_ROLES:
        if (decl_dt := _lookup_dtype(typed, attrs, attr_key)) is None:
            continue
        if not (target_roles & input_roles.keys()):
            if decl_dt not in in_dtypes and not (target_roles <= _OPTIONAL_INPUT_KEYS):
                return False
            if decl_dt in in_dtypes and decl_dt != primary_in_dt:
                return None

    role_dtypes: dict[str, str | None] = {}
    for k in input_roles:
        spec_dt = _lookup_dtype(typed, attrs, *_ROLE_DTYPE_KEYS.get(k, (f"{k}_dtype",)))
        role_dtypes[k] = (
            spec_dt if spec_dt is not None else (None if k in _AUX_ONLY_ROLES else declared_dtype)
        )
    if primary_in_dt is None and all(v is None for v in role_dtypes.values()):
        return True
    for pkey in _PRIMARY_INPUT_KEYS:
        if pkey in input_roles and (p_dt := role_dtypes.get(pkey)) is not None:
            if in_dtypes[0] != p_dt:
                return False
            break
    declared_dt_set = {dt for dt in role_dtypes.values() if dt is not None}
    aux_skip = _ATTENTION_AUX_DTYPES - declared_dt_set
    obs_seq = tuple(
        (s, dt)
        for s, dt in zip(in_shapes, in_dtypes)
        if not (is_attention_abi and (dt in aux_skip or s == ()))
    )
    if input_roles.keys() & _PARTIAL_CACHE_ROLES:
        allowed_dt = {dt for dt in role_dtypes.values() if dt is not None}
        if primary_in_dt is not None:
            allowed_dt.add(primary_in_dt)
        if allowed_dt and any(dt not in allowed_dt for _, dt in obs_seq):
            return False
        return None
    ordered_keys = _role_order_established(input_roles, _INPUT_ROLE_ORDER)
    if ordered_keys is not None:
        ordered_specs = tuple(
            (input_roles[k], role_dtypes[k], k in _OPTIONAL_INPUT_KEYS, k in _TAIL_INPUT_ROLES)
            for k in ordered_keys
        )
        score = _align_ordered_specs(obs_seq, ordered_specs, ignore_dtype=False)
        return True if score == 2 else (None if score == 1 else False)

    if any(role_dtypes[k] is None for k in input_roles if k not in _OPTIONAL_INPUT_KEYS):
        return None
    obs_pairs = Counter(obs_seq)
    req_pairs = Counter(
        (shape, role_dtypes[k])
        for k, shape in input_roles.items()
        if k not in _OPTIONAL_INPUT_KEYS and role_dtypes[k] is not None
    )
    all_pairs = Counter(
        (shape, role_dtypes[k])
        for k, shape in input_roles.items()
        if role_dtypes[k] is not None
    )
    if not _counter_leq(req_pairs, obs_pairs):
        return False
    if not _counter_leq(obs_pairs, all_pairs):
        rem_shapes = Counter(
            s for (s, dt), cnt in (obs_pairs - all_pairs).items() for _ in range(cnt)
        )
        untyped_opt = Counter(shape for k, shape in input_roles.items() if role_dtypes[k] is None)
        return None if _counter_leq(rem_shapes, untyped_opt) else False
    return True if len(set(obs_seq)) <= 1 else None


def native_call_signature_match(binding: Mapping[str, Any], event: Event) -> bool | None:
    """True/False across role-matched input/output shapes, dtypes, and formats; None if unresolved."""
    in_status, in_shapes, in_dtypes, in_formats = parse_paired_lanes(
        event.input_shapes, event.input_dtypes, event.input_formats
    )
    out_status, out_shapes, out_dtypes, out_formats = parse_paired_lanes(
        event.output_shapes, event.output_dtypes, event.output_formats
    )
    if in_status == "mismatch" or out_status == "mismatch":
        return False
    if in_status != "ok" or out_status != "ok":
        return None

    typed = binding.get("typed") or {}
    attrs = typed.get("attrs") if isinstance(typed.get("attrs"), Mapping) else {}
    parsed_shapes = _parse_declared_shapes(typed.get("shapes"))
    if parsed_shapes is None:
        return False
    coarse_shapes, input_roles, output_roles, explicit_inputs, explicit_outputs = parsed_shapes
    family = str(binding.get("family") or "")
    is_attention_abi = family.lower() == "attention" or "query" in input_roles
    declared_dtype = _norm_dtype(typed.get("dtype"))
    primary_in_dt = (
        _lookup_dtype(typed, attrs, "input_dtype", "activation_dtype", "activation_format", "query_dtype")
        or declared_dtype
    )
    declared_out_dtype = _lookup_dtype(typed, attrs, "output_dtype", "output_format", "y_dtype")

    unresolved_order = False
    has_explicit_roles = bool(
        input_roles or output_roles or explicit_inputs is not None or explicit_outputs is not None
    )
    if not has_explicit_roles:
        if not coarse_shapes:
            return False
        coarse_set = set(coarse_shapes.values())
        if any(s not in coarse_set for s in (*in_shapes, *out_shapes)):
            return False
        if not (len(in_shapes) == 1 and len(out_shapes) == 1 and in_shapes[0] == out_shapes[0]):
            unresolved_order = True
    else:
        if explicit_outputs is not None:
            if out_shapes != explicit_outputs:
                return False
        elif output_roles:
            effective_out = out_shapes
            if is_attention_abi and len(out_shapes) > len(output_roles):
                if all(
                    out_shapes[i] == () and out_dtypes[i] in {"fp32", "bf16", "fp16"}
                    for i in range(len(output_roles), len(out_shapes))
                ):
                    effective_out = out_shapes[: len(output_roles)]
            ordered_out = _role_order_established(output_roles, _OUTPUT_ROLE_ORDER)
            if ordered_out is not None:
                if effective_out != tuple(output_roles[k] for k in ordered_out):
                    return False
            else:
                if Counter(effective_out) != Counter(output_roles.values()):
                    return False
                if len(set(effective_out)) > 1:
                    unresolved_order = True
        elif out_shapes:
            coarse_set = set(coarse_shapes.values())
            if not coarse_set:
                return None
            if any(s not in coarse_set for s in out_shapes):
                return False
            if len(out_shapes) > 1:
                unresolved_order = True

        if explicit_inputs is not None:
            if in_shapes != explicit_inputs:
                return False
        elif input_roles:
            for pkey in _PRIMARY_INPUT_KEYS:
                if pkey in input_roles and in_shapes:
                    if in_shapes[0] != input_roles[pkey]:
                        return False
                    break
            role_dt_vals = {
                dt
                for k in input_roles
                if (dt := _lookup_dtype(typed, attrs, *_ROLE_DTYPE_KEYS.get(k, (f"{k}_dtype",))))
                is not None
            }
            if declared_dtype is not None:
                role_dt_vals.add(declared_dtype)
            aux_skip = _ATTENTION_AUX_DTYPES - role_dt_vals
            obs_seq = tuple(
                (s, dt)
                for s, dt in zip(in_shapes, in_dtypes)
                if not (is_attention_abi and (dt in aux_skip or s == ()))
            )
            if input_roles.keys() & _PARTIAL_CACHE_ROLES:
                unresolved_order = True
            else:
                ordered_in = _role_order_established(input_roles, _INPUT_ROLE_ORDER)
                if ordered_in is not None:
                    shape_specs = tuple(
                        (
                            input_roles[k],
                            None,
                            k in _OPTIONAL_INPUT_KEYS,
                            k in _TAIL_INPUT_ROLES,
                        )
                        for k in ordered_in
                    )
                    if _align_ordered_specs(obs_seq, shape_specs, ignore_dtype=True) == 0:
                        return False
                else:
                    req_counts = Counter(
                        shape for k, shape in input_roles.items() if k not in _OPTIONAL_INPUT_KEYS
                    )
                    all_counts = Counter(input_roles.values())
                    obs_counts = Counter(s for s, _ in obs_seq)
                    if not (
                        _counter_leq(req_counts, obs_counts) and _counter_leq(obs_counts, all_counts)
                    ):
                        return False
                    if len(set(s for s, _ in obs_seq)) > 1:
                        unresolved_order = True
        elif in_shapes:
            coarse_set = set(coarse_shapes.values())
            if not coarse_set:
                return None
            if any(s not in coarse_set for s in in_shapes):
                return False
            if len(in_shapes) > 1:
                unresolved_order = True

    in_dt_verdict = _match_input_dtypes(
        typed=typed,
        attrs=attrs,
        input_roles=input_roles,
        explicit_inputs=explicit_inputs,
        in_shapes=in_shapes,
        in_dtypes=in_dtypes,
        declared_dtype=declared_dtype,
        primary_in_dt=primary_in_dt,
        is_attention_abi=is_attention_abi,
    )
    if in_dt_verdict is False:
        return False
    if in_dt_verdict is None:
        unresolved_order = True

    explicit_out_dtypes = typed.get("output_dtypes")
    if isinstance(explicit_out_dtypes, (list, tuple)):
        normed_out = [_norm_dtype(raw) for raw in explicit_out_dtypes]
        if not normed_out or any(dt is None for dt in normed_out):
            return None
        if out_dtypes != tuple(dt for dt in normed_out if dt is not None):
            return False
    else:
        target_out = declared_out_dtype or declared_dtype
        if target_out is not None:
            checked_out = (
                tuple(dt for s, dt in zip(out_shapes, out_dtypes) if s != ())
                if is_attention_abi
                else out_dtypes
            )
            if out_dtypes[0] != target_out or any(dt != target_out for dt in checked_out):
                return False

    if isinstance(typed.get("input_formats"), (list, tuple)):
        if not in_formats:
            return None
        if in_formats != tuple(str(x).strip().upper() for x in typed["input_formats"]):
            return False
    if isinstance(typed.get("output_formats"), (list, tuple)):
        if not out_formats:
            return None
        if out_formats != tuple(str(x).strip().upper() for x in typed["output_formats"]):
            return False
    layout = str(typed.get("layout") or "").strip().lower()
    if layout:
        if not in_formats or not out_formats:
            return None
        if layout in {"contiguous", "nd"}:
            if any(fmt in _NON_CONTIGUOUS_FORMATS for fmt in (*in_formats, *out_formats)):
                return False
        elif "fractal_nz" in layout and "FRACTAL_NZ" not in in_formats:
            return False
    return None if unresolved_order else True


__all__ = [
    "event_signature",
    "native_call_signature_match",
    "parse_paired_lanes",
]
