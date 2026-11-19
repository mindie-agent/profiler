"""Standalone five-domain SKU microbenchmark (zero ``mindie_sim`` dependency).

[Role]
  Register and execute the five S0 domains on ``DAV_2201`` A2/A3 silicon:
  inclusive completion minima, matrix/memory paths, grouped-MoE routing,
  attention/state operators and memory/IO gathers.  Case construction is pure
  and runs on a CPU-only host; execution binds one admitted ordinal and reuses
  the ``timing`` protocol.

[Invariants]
  * Only ``bf16``/``fp16``/``int8``/``w4a8`` are constructed.  A native FP8
    Cube request on A2/A3 is refused, never silently emulated.
  * ``group_list`` is always an integer list whose entries sum to ``M``;
    ``group_list_type=1`` (per-expert counts) is recorded beside it.
  * The held-out split is frozen from ``bench_profiles.json`` before timing.
  * ``host_fallback`` fails closed unless ``--allow-cpu-smoke`` is explicitly
    requested; missing kernels attach ``mindie-unmodeled-structure-hint/1``.
  * Published receipts carry no home path, host address, device node or digest.

[Timeouts & Locks]
  No locks.  Execution is single-process and bounded by the caller's container
  budget; each case owns its own allocation lifetime.

[Side-Effect Policy]
  Writes only the explicit ``--out`` JSON, ``--resume`` journal and
  ``--observations`` JSONL paths.
"""

from __future__ import annotations

import argparse, math, os, uuid
from typing import Any, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi import portable_receipt, resolve_allowed_phy_ids
from .profiles import profile_section
from .sku_microbench_runner import (
    BYTE_RATE_OPS, JsonlSink, MICROBENCH_SCHEMA, RECEIPT_SCHEMA,
    _emit_observations, _run_one, emit_sku_output, run_cases,
)
from .timing import (
    DEFAULT_SLOT_BYTES, admit_context, close_context,
    cold_ring_plan, make_blocker_unit_op, measurement_modes,
)
from .timing_ring import resolve_l2_bytes

CASE_SCHEMA = "mindie-bench-case/1"

_UNITS = profile_section("units")
_CFG = profile_section("sku_microbench")

DAV_2201 = "DAV_2201"
A2_SKUS = (
    "Ascend910B1", "Ascend910B2", "Ascend910B2C",
    "Ascend910B3", "Ascend910B4", "Ascend910B4-1",
)
A3_SKUS = (
    "Ascend910_9391", "Ascend910_9392", "Ascend910_9381",
    "Ascend910_9382", "Ascend910_9372", "Ascend910_9362",
)
SUPPORTED_SKUS = (DAV_2201, *A2_SKUS, *A3_SKUS)
SUPPORTED_DTYPES = ("bf16", "fp16", "int8", "w4a8")
FORBIDDEN_DTYPES = ("fp8", "fp8_e4m3", "fp8_e5m2", "mxfp8", "mxfp4", "hif8")

KIB = int(_UNITS["kib"])
MIB = int(_UNITS["mib"])
_JOURNAL_MODE = int(_CFG["journal_mode"])
_REASON_LIMIT = int(_CFG["max_reason_chars"])
_EXIT_ERR = int(_CFG["exit_error"])
_EXIT_UNAVAIL = int(_CFG["exit_torch_unavailable"])
_PRECYCLE_FACTOR = int(_CFG["precycle_trial_factor"])
_RUN_ID_HEX_CHARS = 2 * 2 * 2 + 2 * 2
_DOMAIN_IDS = tuple(int(item) for item in _CFG["domain_ids"])
_DOM_1, _DOM_2, _DOM_3, _DOM_4, _DOM_5 = _DOMAIN_IDS
DOMAIN_NAMES = {
    int(key): str(val) for key, val in _CFG["domain_names"].items()
}

HELDOUT_M = tuple(int(item) for item in _CFG["heldout_m"])
M_KNEE = tuple(
    sorted(
        {2 ** int(exp) for exp in _CFG["m_knee_exponents"]} | set(HELDOUT_M)
    )
)
_HELDOUT_BATCH = int(_CFG["heldout_batch"])
_HELDOUT_KV = int(_CFG["heldout_kv_len"])
_HELDOUT_KV_SET = frozenset(int(x) for x in _CFG["heldout_context_seq_lens"]) | {_HELDOUT_KV}
CONTEXT_SEQ_GRID = tuple(int(x) for x in _CFG["context_seq_grid"])
_LONG_CTX_THRESHOLD = int(_CFG["long_context_threshold"])
_LONG_PREFILL_CAP = int(_CFG["long_prefill_query_cap"])
_LONG_PREFILL_HEADS = int(_CFG["long_prefill_max_heads"])
_LINEAR_LOCAL_HEADS = int(_CFG["linear_attn_local_heads"])
_HELDOUT_ROUTING = (
    str(_CFG["heldout_routing_dist"]),
    float(_CFG["heldout_routing_zero"]),
)
_HELDOUT_FABRIC = frozenset(int(item) for item in _CFG["heldout_fabric_bytes"])
NARROW_N = tuple(int(item) for item in _CFG["narrow_n"])
MATRIX_DTYPES = ("bf16", "fp16", "int8", "w4a8")
GEMM_SHAPES = tuple(tuple(int(d) for d in row) for row in _CFG["gemm_shapes"])
_MKNEE_N = int(_CFG["mknee_n"])
_MKNEE_K = int(_CFG["mknee_k"])
NARROW_M = int(_CFG["narrow_m"])
_NARROW_K = int(_CFG["narrow_k"])
_NZ_CODE = int(_CFG["nz_format_code"])
_MTE2_BYTES = int(_CFG["mte2_transfer_bytes"])
ROUTING_ZERO_FRACTIONS = tuple(float(x) for x in _CFG["routing_zero_fractions"])
ROUTING_EXPERT_SHAPES = tuple(
    tuple(int(d) for d in row) for row in _CFG["routing_expert_shapes"]
)
ROUTING_TOKENS = tuple(int(x) for x in _CFG["routing_tokens"])
ZIPF_EXPONENT = float(_CFG["zipf_exponent"])
SPILL_EXPERT_BYTES = int(_CFG["spill_expert_bytes"])
SPILL_ACTIVE_RANGE = tuple(int(x) for x in _CFG["spill_active_range"])
_SPILL_EXPERTS = int(_CFG["spill_total_experts"])
_SPILL_K = int(_CFG["spill_k"])
_SPILL_N = int(_CFG["spill_n"])
_SPILL_COVERS = [int(x) for x in _CFG["spill_covers_mib"]]
ATTENTION_HEADS = int(_CFG["attention_heads"])
ATTENTION_KV_HEADS = int(_CFG["attention_kv_heads"])
ATTENTION_HEAD_DIM = int(_CFG["attention_head_dim"])
_ATTN_SEQ_LEN = int(_CFG["attention_seq_len"])
_ATTN_FLOPS_FACTOR = int(_CFG["attention_flops_factor"])
_PAGED_BLOCK = int(_CFG["paged_block_size"])
_PAGED_TABLE = [int(x) for x in _CFG["paged_block_table"]]
MLA_LATENT_DIM = int(_CFG["mla_latent_dim"])
MLA_ROPE_DIM = int(_CFG["mla_rope_dim"])
_MLA_TOKENS = int(_CFG["mla_tokens"])
MLA_KV_BYTES_PER_TOKEN = (MLA_LATENT_DIM + MLA_ROPE_DIM) * 2
_REC_SEQS = int(_CFG["recurrent_sequences"])
_CONV_WIDTH_FACTOR = int(_CFG["conv1d_width_factor"])
_CONV_STATE_LEN = int(_CFG["conv1d_state_len"])
CACHELINE_BYTES = int(_CFG["cacheline_bytes"])
_IDX_ADD_ROWS = int(_CFG["index_add_rows"])
INDEX_ADD_TOKENS = int(_CFG["index_add_tokens"])
_IDX_BYTES = int(_CFG["index_bytes"])
GATHER_LENGTHS = tuple(int(x) for x in _CFG["gather_lengths"])
PINNED_COPY_SIZES = tuple(int(x) for x in _CFG["pinned_copy_sizes"])
PLE_BF16_ROW_BYTES = int(_CFG["ple_bf16_row_bytes"])
PLE_INT8_ROW_BYTES = int(_CFG["ple_int8_row_bytes"])
PLE_OWNERSHIP_SHARDS = int(_CFG["ple_ownership_shards"])
PLE_ROW_SPAN = int(_CFG["ple_row_span"])
_PLE_LOOKUP_COUNT = int(_CFG["ple_lookup_count"])
_D1_VEC_BYTES = int(_CFG["d1_vector_bytes"])
_D1_CUBE_DIM = int(_CFG["d1_cube_dim"])
_D1_NORM_WIDTH = int(_CFG["d1_norm_width"])
_D1_W8A8_DIM = int(_CFG["d1_w8a8_dim"])

BYTE_RATE_OPS = frozenset({"gather", "mte2_aic", "mte2_aiv", "pinned_copy", "ple_lookup"})


def _heldout(*, matrix_m=None, batch=None, kv_len=None, routing=None, fabric=None) -> bool:
    """Freeze the held-out split: OR across every applicable axis."""
    if matrix_m is not None and matrix_m in HELDOUT_M:
        return True
    if batch == _HELDOUT_BATCH or (kv_len is not None and int(kv_len) in _HELDOUT_KV_SET):
        return True
    if routing == _HELDOUT_ROUTING:
        return True
    return bool(fabric is not None and fabric in _HELDOUT_FABRIC)


def uniform_counts(experts: int, tokens: int) -> list[int]:
    """Integer uniform histogram with an exact-sum remainder distribution."""
    _require(experts >= 1 and tokens >= 0, "bench_routing_shape_invalid")
    quotient, remainder = divmod(int(tokens), int(experts))
    return [quotient + (1 if idx < remainder else 0) for idx in range(experts)]


def zipf_counts(
    experts: int, tokens: int, exponent: float = ZIPF_EXPONENT
) -> list[int]:
    """Deterministic Zipf histogram with largest-remainder integer rounding."""
    _require(experts >= 1 and tokens >= 0, "bench_routing_shape_invalid")
    _require(exponent > 0, "bench_routing_exponent_invalid")
    weights = [1.0 / float(idx + 1) ** float(exponent) for idx in range(experts)]
    total = sum(weights)
    raw = [int(tokens) * weight / total for weight in weights]
    counts = [int(math.floor(val)) for val in raw]
    remainder = int(tokens) - sum(counts)
    order = sorted(
        range(experts), key=lambda idx: (-(raw[idx] - counts[idx]), idx)
    )
    for idx in order[: max(0, remainder)]:
        counts[idx] += 1
    return counts


def zero_experts(counts: Sequence[int], zero_fraction: float) -> list[int]:
    """Zero a deterministic tail cohort and redistribute its tokens."""
    _require(0.0 <= float(zero_fraction) < 1.0, "bench_routing_zero_fraction_invalid")
    values = [int(item) for item in counts]
    experts = len(values)
    zeros = int(round(float(zero_fraction) * experts))
    if zeros:
        active = list(range(experts - zeros))
        _require(bool(active), "bench_routing_zero_fraction_invalid")
        moved = sum(values[experts - zeros :])
        for idx in range(experts - zeros, experts):
            values[idx] = 0
        values = _redistribute(values, active, moved)
    return values


def _redistribute(values: list[int], active: Sequence[int], moved: int) -> list[int]:
    if moved <= 0:
        return values
    weights = [max(1, values[idx]) for idx in active]
    total = sum(weights)
    raw = [moved * weight / total for weight in weights]
    extra = [int(math.floor(val)) for val in raw]
    remainder = moved - sum(extra)
    order = sorted(
        range(len(active)), key=lambda pos: (-(raw[pos] - extra[pos]), pos)
    )
    for pos in order[: max(0, remainder)]:
        extra[pos] += 1
    for pos, idx in enumerate(active):
        values[idx] += extra[pos]
    return values


def group_list(counts: Sequence[int]) -> list[int]:
    """Validate and return the integer per-expert ``group_list`` (type 1)."""
    values = [int(item) for item in counts]
    _require(all(item >= 0 for item in values), "bench_group_list_negative")
    return values


def routing_distributions(experts: int, tokens: int) -> list[dict[str, Any]]:
    """Uniform and Zipf-1.2 histograms across every zero fraction."""
    families: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[int, ...]]] = set()
    for family, base in (
        ("uniform", uniform_counts(experts, tokens)),
        ("zipf_s1.2", zipf_counts(experts, tokens)),
    ):
        for fraction in ROUTING_ZERO_FRACTIONS:
            counts = zero_experts(base, fraction)
            _require(sum(counts) == tokens, "bench_group_list_sum_mismatch")
            signature = (family, tuple(counts))
            if signature in seen:
                continue
            seen.add(signature)
            families.append(
                {
                    "distribution": family,
                    "zero_fraction": fraction,
                    "active_experts": sum(1 for item in counts if item > 0),
                    "group_list": group_list(counts),
                    "total_tokens": int(tokens),
                }
            )
    return families


def bounded_row_remap(
    rows: Iterable[int], span: int = PLE_ROW_SPAN
) -> dict[str, Any]:
    """Injective dense remap of owned rows into a bounded registered slab."""
    unique = sorted({int(row) for row in rows})
    _require(span >= 1, "bench_ple_span_invalid")
    _require(len(unique) <= span, "bench_ple_span_too_small")
    mapping = {row: idx % span for idx, row in enumerate(unique)}
    _require(len(set(mapping.values())) == len(mapping), "bench_ple_remap_not_injective")
    return {
        "rows": unique,
        "span": int(span),
        "slots": mapping,
        "injective": True,
        "footprint_rows": len(mapping),
    }


def ple_cases(dtypes: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """BF16 320 B/row and INT8 180 B/row bounded UVA/H2D lookups."""
    cases: list[dict[str, Any]] = []
    requested = set(dtypes) if dtypes else set(SUPPORTED_DTYPES)
    for dtype, row_bytes in (("bf16", PLE_BF16_ROW_BYTES), ("int8", PLE_INT8_ROW_BYTES)):
        if dtype not in requested:
            continue
        ids = [idx * PLE_OWNERSHIP_SHARDS + 1 for idx in range(_PLE_LOOKUP_COUNT)]
        remap = bounded_row_remap(ids)
        for pattern in ("repeated", "rotating"):
            for path in ("uva_gather", "pinned_h2d"):
                cases.append(
                    _case(
                        _DOM_5,
                        f"d5.ple.{dtype}.{pattern}.{path}",
                        op="ple_lookup",
                        dtype=dtype,
                        builder="ple_lookup",
                        shape={
                            "tokens": len(ids),
                            "row_bytes": row_bytes,
                            "width": row_bytes // _element_bytes(dtype),
                            "ownership_shards": PLE_OWNERSHIP_SHARDS,
                        },
                        work_bytes=len(ids) * row_bytes,
                        extra={
                            "lookup_ids": ids,
                            "slot_map": remap["slots"],
                            "remap_span": remap["span"],
                            "remap_injective": True,
                            "reuse": pattern,
                            "path": path,
                        },
                        split=_heldout(),
                    )
                )
    return cases


def _case(
    domain: int,
    case_id: str,
    *,
    op: str,
    dtype: str,
    builder: str,
    shape: Mapping[str, Any],
    work_bytes: int = 0,
    work_flops: int = 0,
    split: bool = False,
    extra: Mapping[str, Any] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": CASE_SCHEMA,
        "case_id": case_id,
        "domain": domain,
        "domain_name": DOMAIN_NAMES[domain],
        "family": DOMAIN_NAMES[domain],
        "op": op,
        "dtype": dtype,
        "builder": builder,
        "shape": dict(shape),
        "work_bytes": int(work_bytes),
        "work_flops": int(work_flops),
        "split": "heldout" if split else "train",
        "timing": {"startup_ms": 0.0, "inclusive_minimum": True},
        "notes": notes,
    }
    if extra:
        payload.update(dict(extra))
    return payload


def build_cases(
    *,
    domain: int | None = None,
    sku: str = DAV_2201,
    dtypes: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Register the five domains without importing torch."""
    if sku not in SUPPORTED_SKUS:
        raise ProfilerUsageError(
            f"bench_sku_unsupported: {sku!r} is not a bench SKU; "
            f"this suite measures {', '.join(SUPPORTED_SKUS)}"
        )
    requested = list(dtypes) if dtypes else list(SUPPORTED_DTYPES)
    if [item for item in requested if item in FORBIDDEN_DTYPES]:
        raise ProfilerUsageError(
            "bench_native_fp8_unsupported_on_dav_2201: native FP8 Cube is never "
            "constructed on A2/A3; use int8 or w4a8"
        )
    unknown = [item for item in requested if item not in SUPPORTED_DTYPES]
    if unknown:
        raise ProfilerUsageError(f"bench_dtype_unsupported: {unknown}")
    protocol = (
        "hccs_dma" if sku in A3_SKUS else "pcie_dma" if sku in A2_SKUS else "host_dma"
    )
    builders = {
        _DOM_1: _domain1,
        _DOM_2: _domain2,
        _DOM_3: _domain3,
        _DOM_4: _domain4,
        _DOM_5: lambda req: _domain5(req, transfer_protocol=protocol),
    }
    if domain is not None and domain not in builders:
        raise ProfilerUsageError(f"bench_domain_unknown: {domain}")
    selected = [domain] if domain is not None else sorted(builders)
    cases: list[dict[str, Any]] = []
    for idx in selected:
        cases.extend(builders[idx](requested))
    seen: set[str] = set()
    for item in cases:
        if item["case_id"] in seen:
            raise ProfilerUsageError(f"bench_case_id_duplicate: {item['case_id']}")
        seen.add(item["case_id"])
    return cases


def _domain1(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases = [
        _case(_DOM_1, "d1.empty.event_pair", op="empty_event_pair", dtype="none", builder="empty_event_pair", shape={}),
        _case(_DOM_1, "d1.empty.aic_launch", op="empty_aic", dtype="none", builder="empty_launch",
              shape={"kernel": "empty_aic"}, extra={"kernel_class": "AIC", "task_count": 1}),
        _case(_DOM_1, "d1.empty.aiv_launch", op="empty_aiv", dtype="none", builder="empty_launch",
              shape={"kernel": "empty_aiv"}, extra={"kernel_class": "AIV", "task_count": 1}),
        _case(_DOM_1, "d1.vector.bf16.1", op="vector_add", dtype="bf16", builder="vector_add",
              shape={"tokens": 1, "width": 1}, work_bytes=_D1_VEC_BYTES),
        _case(_DOM_1, f"d1.cube.bf16.1x{_D1_CUBE_DIM}x{_D1_CUBE_DIM}", op="cube_matmul", dtype="bf16",
              builder="matmul", shape={"m": 1, "n": _D1_CUBE_DIM, "k": _D1_CUBE_DIM},
              work_flops=2 * _D1_CUBE_DIM * _D1_CUBE_DIM),
        _case(_DOM_1, f"d1.norm.bf16.1x{_D1_NORM_WIDTH}", op="rms_norm", dtype="bf16", builder="rms_norm",
              shape={"tokens": 1, "width": _D1_NORM_WIDTH}, work_bytes=2 * (_D1_NORM_WIDTH * 2 + _D1_NORM_WIDTH * 2)),
        _case(_DOM_1, f"d1.w8a8.int8.1x{_D1_W8A8_DIM}x{_D1_W8A8_DIM}", op="w8a8_matmul", dtype="int8",
              builder="quant_matmul",
              shape={"m": 1, "n": _D1_W8A8_DIM, "k": _D1_W8A8_DIM, "per_column_scale": [_D1_W8A8_DIM], "per_token_scale": [1]},
              work_flops=2 * _D1_W8A8_DIM * _D1_W8A8_DIM,
              extra={"scale_mode": "per_column", "per_token_scale": True}),
    ]
    return [case for case in cases if case["dtype"] == "none" or case["dtype"] in dtypes]


def _domain2(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for dtype in dtypes:
        for m, n, k in GEMM_SHAPES:
            cases.append(_case(
                _DOM_2, f"d2.gemm.{dtype}.{m}x{n}x{k}", op="matmul", dtype=dtype, builder="matmul",
                shape={"m": m, "n": n, "k": k}, work_flops=2 * m * n * k,
                work_bytes=_gemm_bytes(dtype, m, n, k),
                split=_heldout(matrix_m=m if m in HELDOUT_M else None), extra={"layout": "KN"},
            ))
        for m in M_KNEE:
            cases.append(_case(
                _DOM_2, f"d2.mknee.{dtype}.{m}x{_MKNEE_N}x{_MKNEE_K}", op="matmul", dtype=dtype,
                builder="matmul", shape={"m": m, "n": _MKNEE_N, "k": _MKNEE_K},
                work_flops=2 * m * _MKNEE_N * _MKNEE_K,
                work_bytes=_gemm_bytes(dtype, m, _MKNEE_N, _MKNEE_K),
                split=_heldout(matrix_m=m), extra={"layout": "KN", "axis": "M"},
            ))
        for n in NARROW_N:
            cases.append(_case(
                _DOM_2, f"d2.splitk.{dtype}.{NARROW_M}x{n}x{_NARROW_K}", op="matmul", dtype=dtype,
                builder="matmul", shape={"m": NARROW_M, "n": n, "k": _NARROW_K},
                work_flops=2 * NARROW_M * n * _NARROW_K,
                work_bytes=_gemm_bytes(dtype, NARROW_M, n, _NARROW_K),
                extra={"layout": "KN", "axis": "N", "split_k": True},
            ))
            for layout in ("NK", "FRACTAL_NZ"):
                cases.append(_case(
                    _DOM_2, f"d2.layout.{dtype}.{layout.lower()}.{NARROW_M}x{n}", op="matmul",
                    dtype=dtype, builder="matmul", shape={"m": NARROW_M, "n": n, "k": _NARROW_K},
                    work_flops=2 * NARROW_M * n * _NARROW_K,
                    work_bytes=_gemm_bytes(dtype, NARROW_M, n, _NARROW_K),
                    extra={"layout": layout, "format_code": _NZ_CODE if layout == "FRACTAL_NZ" else None,
                           "prepared_outside_timing": layout == "FRACTAL_NZ"},
                ))
        for direction in ("mte2_aic", "mte2_aiv"):
            for residency in ("dram", "l2"):
                for owners in ("one_owner", "full_owner"):
                    cases.append(_case(
                        _DOM_2, f"d2.{direction}.{dtype}.{residency}.{owners}", op=direction,
                        dtype=dtype, builder="mte2_transfer",
                        shape={"bytes": _transfer_bytes(dtype, direction), "residency": residency, "owners": owners},
                        work_bytes=_transfer_bytes(dtype, direction),
                        extra={"residency": residency, "owners": owners, "consumed_result": True},
                    ))
    return cases


def _domain3(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for dtype in dtypes:
        for experts, k, n in ROUTING_EXPERT_SHAPES:
            for tokens in ROUTING_TOKENS:
                for family in routing_distributions(experts, tokens):
                    counts = family["group_list"]
                    zero_pct = int(family["zero_fraction"] * 100)
                    case_id = f"d3.gmm.{dtype}.e{experts}.k{k}.n{n}.m{tokens}.{family['distribution']}.z{zero_pct}"
                    cases.append(_case(
                        _DOM_3, case_id, op="npu_grouped_matmul", dtype=dtype, builder="grouped_matmul",
                        shape={"e": experts, "k": k, "n": n, "m": tokens}, work_flops=2 * tokens * n * k,
                        work_bytes=_gemm_bytes(dtype, tokens, n, k) + _extra_expert_bank_bytes(dtype, experts, k, n),
                        split=_heldout(routing=(family["distribution"], family["zero_fraction"])),
                        extra={"group_list": counts, "group_list_type": 1, "integer_group_list": True,
                               "zero_fraction": family["zero_fraction"], "active_experts": family["active_experts"],
                               "distribution": family["distribution"], "per_token_scale": True},
                    ))
    for active in SPILL_ACTIVE_RANGE:
        span = active * SPILL_EXPERT_BYTES
        group = group_list([1] * active + [0] * (_SPILL_EXPERTS - active))
        cases.append(_case(
            _DOM_3, f"d3.spill.e{_SPILL_EXPERTS}.active{active}.4mib", op="npu_grouped_matmul",
            dtype="bf16", builder="grouped_matmul",
            shape={"e": _SPILL_EXPERTS, "k": _SPILL_K, "n": _SPILL_N, "m": active, "expert_bytes": SPILL_EXPERT_BYTES},
            work_flops=2 * active * _SPILL_K * _SPILL_N, work_bytes=span,
            extra={"group_list": group, "group_list_type": 1, "integer_group_list": True,
                   "active_experts": active, "l2_span_bytes": span, "l2_span_mib": span // MIB,
                   "covers_mib": list(_SPILL_COVERS), "per_token_scale": True},
        ))
    return cases


def _domain4(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    common = {"heads": ATTENTION_HEADS, "kv_heads": ATTENTION_KV_HEADS, "head_dim": ATTENTION_HEAD_DIM}
    lin_h = _LINEAR_LOCAL_HEADS
    for dtype in dtypes:
        is_bf16 = dtype == "bf16"
        is_float = dtype in {"bf16", "fp16"}
        if not is_float:
            continue
        for seq_len in CONTEXT_SEQ_GRID:
            is_long = seq_len >= _LONG_CTX_THRESHOLD
            pf_tokens = min(seq_len, _LONG_PREFILL_CAP)
            pf_heads = _LONG_PREFILL_HEADS if is_long else ATTENTION_HEADS
            split_kv = _heldout(kv_len=seq_len)
            pages = -(-seq_len // _PAGED_BLOCK)
            pf_flops = _ATTN_FLOPS_FACTOR * pf_heads * pf_tokens * seq_len * ATTENTION_HEAD_DIM
            dec_flops = _ATTN_FLOPS_FACTOR * ATTENTION_HEADS * seq_len * ATTENTION_HEAD_DIM
            grid_specs: list[tuple[str, str, bool, dict[str, Any]]] = [
                ("fa", f"tnd.s{seq_len}", True, dict(
                    op="npu_fusion_attention", builder="fusion_attention", work_flops=pf_flops, split=split_kv,
                    shape={"heads": pf_heads, "kv_heads": ATTENTION_KV_HEADS, "head_dim": ATTENTION_HEAD_DIM,
                           "layout": "TND", "sequences": 1, "tokens": pf_tokens, "seq_len": seq_len},
                    extra={"phase": "prefill", "input_layout": "TND", "actual_seq_qlen": True, "causal": True})),
                ("fia", f"paged.s{seq_len}", True, dict(
                    op="npu_fused_infer_attention_score", builder="fused_infer_attention", work_flops=dec_flops, split=split_kv,
                    shape={**common, "layout": "TND", "block_size": _PAGED_BLOCK,
                           "block_table": [1, pages], "tokens": 1, "seq_len": seq_len},
                    extra={"phase": "decode", "input_layout": "TND", "block_size": _PAGED_BLOCK,
                           "actual_seq_lengths": True, "paged": True})),
                ("ifa", f"legacy.s{seq_len}", True, dict(
                    op="npu_incre_flash_attention", builder="incre_flash_attention", work_flops=dec_flops, split=split_kv,
                    shape={**common, "layout": "BSH", "block_size": _PAGED_BLOCK, "tokens": 1, "seq_len": seq_len},
                    extra={"phase": "decode", "scale_value": True, "block_table": True, "legacy_paged_binding": True})),
                ("mla", f"absorbed.s{seq_len}", is_bf16, dict(
                    op="absorbed_mla", builder="absorbed_mla", work_bytes=MLA_KV_BYTES_PER_TOKEN * seq_len, split=split_kv,
                    shape={"heads": ATTENTION_HEADS, "sequences": 1, "tokens": 1, "seq_len": seq_len,
                           "latent": MLA_LATENT_DIM, "rope": MLA_ROPE_DIM,
                           "kv_bytes_per_token": MLA_KV_BYTES_PER_TOKEN, "single_backing": True},
                    extra={"phase": "decode", "c_kv_bytes_per_token": MLA_KV_BYTES_PER_TOKEN,
                           "backing_buffers": 1, "absorbed": True, "latent_split": [MLA_LATENT_DIM, MLA_ROPE_DIM]})),
                ("indexer", f"lightning.s{seq_len}", True, dict(
                    op="lightning_indexer", builder="lightning_indexer", split=split_kv,
                    shape={"tokens": 1, "heads": ATTENTION_HEADS, "head_dim": ATTENTION_HEAD_DIM, "seq_len": seq_len},
                    extra={"phase": "decode", "metadata_separate": True, "provider_namespace": "cann_ops_transformer"})),
                ("sfa", f"tnd.s{seq_len}", True, dict(
                    op="npu_sparse_flash_attention", builder="sparse_flash_attention", split=split_kv,
                    shape={"heads": ATTENTION_HEADS, "kv_heads": ATTENTION_KV_HEADS, "head_dim": MLA_LATENT_DIM,
                           "qk_rope_head_dim": MLA_ROPE_DIM, "tokens": 1, "seq_len": seq_len},
                    extra={"phase": "decode", "layout_query": "TND", "layout_kv": "TND"})),
                ("dcp", f"tnd.s{seq_len}", True, dict(
                    op="npu_ring_attention_update", builder="dcp_lse_attention_merge", split=split_kv,
                    shape={"tokens": seq_len, "heads": lin_h, "kv_heads": ATTENTION_KV_HEADS,
                           "head_dim": ATTENTION_HEAD_DIM, "seq_len": seq_len},
                    extra={"phase": "prefill", "input_layout": "TND", "input_softmax_layout": "TND"})),
                ("gdn", f"chunk.s{seq_len}", is_bf16, dict(
                    op="npu_chunk_gated_delta_rule", builder="chunk_gated_delta_rule", split=split_kv,
                    shape={"tokens": seq_len, "heads": lin_h, "sequences": 1,
                           "head_dim": ATTENTION_HEAD_DIM, "seq_len": seq_len, "state_dtype": "bf16"},
                    extra={"phase": "prefill", "actual_seq_lengths": True, "initial_state_dtype": "bf16"})),
                ("kda", f"chunk.s{seq_len}", True, dict(
                    op="chunk_kda_fwd", builder="chunk_kda_fwd", split=split_kv,
                    shape={"tokens": seq_len, "heads": lin_h, "sequences": 1,
                           "head_dim": ATTENTION_HEAD_DIM, "seq_len": seq_len, "state_dtype": "bf16"},
                    extra={"phase": "prefill", "provider_chain": ["vllm_ascend", "fla_npu", "torch_npu"], "chunked": True})),
            ]
            for suffix, tag, allowed, payload in grid_specs:
                if allowed:
                    cases.append(_case(_DOM_4, f"d4.{suffix}.{dtype}.{tag}", dtype=dtype, **payload))
        decode_state_specs: list[tuple[str, str, bool, dict[str, Any]]] = [
            ("gdn", "recurrent", is_bf16, dict(
                op="npu_recurrent_gated_delta_rule", builder="recurrent_gated_delta_rule",
                shape={"tokens": _REC_SEQS, "sequences": _REC_SEQS, "heads": ATTENTION_HEADS,
                       "head_dim": ATTENTION_HEAD_DIM, "state_dtype": "bf16"},
                extra={"phase": "decode", "actual_seq_lengths": True, "ssm_state_indices": True})),
            ("kda", "recurrent", True, dict(
                op="fused_recurrent_kda", builder="fused_recurrent_kda",
                shape={"tokens": _REC_SEQS, "sequences": 1, "heads": ATTENTION_HEADS,
                       "head_dim": ATTENTION_HEAD_DIM, "state_dtype": "fp32"},
                extra={"phase": "decode", "provider_chain": ["vllm_ascend", "fla_npu", "torch_npu"]})),
            ("conv1d", "update", True, dict(
                op="causal_conv1d_update", builder="causal_conv1d_update",
                shape={"tokens": _REC_SEQS, "width": _CONV_WIDTH_FACTOR * ATTENTION_HEAD_DIM, "state_len": _CONV_STATE_LEN},
                extra={"phase": "decode", "fused_provider": "cann_or_vllm_ascend", "python_reference": False})),
        ]
        for suffix, tag, allowed, payload in decode_state_specs:
            if allowed:
                cases.append(_case(_DOM_4, f"d4.{suffix}.{dtype}.{tag}", dtype=dtype, **payload))
    return cases


def _domain5(
    dtypes: Sequence[str], *, transfer_protocol: str = "host_dma"
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for dtype in dtypes:
        cases.append(_case(
            _DOM_5, f"d5.index_add.{dtype}.shared_cacheline", op="index_add_", dtype=dtype,
            builder="index_add", shape={"rows": _IDX_ADD_ROWS, "tokens": INDEX_ADD_TOKENS, "cacheline_bytes": CACHELINE_BYTES},
            extra={"contention": "shared_cacheline", "indices_per_cacheline": CACHELINE_BYTES // _IDX_BYTES},
        ))
        cases.append(_case(
            _DOM_5, f"d5.index_add.{dtype}.disjoint_cacheline", op="index_add_", dtype=dtype,
            builder="index_add", shape={"rows": _IDX_ADD_ROWS, "tokens": INDEX_ADD_TOKENS, "cacheline_bytes": CACHELINE_BYTES},
            extra={"contention": "disjoint_cacheline", "indices_per_cacheline": 1},
        ))
        for length in GATHER_LENGTHS:
            cases.append(_case(
                _DOM_5, f"d5.gather.{dtype}.stride128.{length}", op="gather", dtype=dtype,
                builder="strided_gather", shape={"length": length, "stride_bytes": CACHELINE_BYTES},
                work_bytes=length * CACHELINE_BYTES,
                extra={"stride_bytes": CACHELINE_BYTES, "burst_amplification": True},
            ))
        for size in PINNED_COPY_SIZES:
            for direction in ("h2d", "d2h"):
                cases.append(_case(
                    _DOM_5, f"d5.host_io.{dtype}.{direction}.{size}", op="pinned_copy", dtype=dtype,
                    builder="pinned_copy",
                    shape={"bytes": size, "direction": direction, "pinned": True, "transfer_protocol": transfer_protocol},
                    work_bytes=size,
                    extra={"direction": direction, "pinned": True, "transfer_protocol": transfer_protocol},
                ))
    cases.extend(ple_cases(dtypes))
    return cases


def _gemm_bytes(dtype: str, m: int, n: int, k: int) -> int:
    if dtype == "w4a8":
        return int(m) * int(k) + int(k) * int(n) // 2 + int(m) * int(n) * _element_bytes("bf16")
    elem = _element_bytes(dtype)
    return (int(m) * int(k) + int(k) * int(n) + int(m) * int(n)) * elem


def _extra_expert_bank_bytes(dtype: str, experts: int, k: int, n: int) -> int:
    weight = int(k) * int(n) // 2 if dtype == "w4a8" else int(k) * int(n) * _element_bytes(dtype)
    return max(0, int(experts) - 1) * weight


def _element_bytes(dtype: str) -> int:
    return 1 if dtype in {"int8", "w4a8"} else 2


def _transfer_bytes(_dtype: str, _direction: str) -> int:
    return _MTE2_BYTES


def _attention_flops(heads: int, seq_len: int) -> int:
    return _ATTN_FLOPS_FACTOR * int(heads) * int(seq_len) * int(seq_len) * ATTENTION_HEAD_DIM


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProfilerUsageError(reason)


def _sku_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench sku", allow_abbrev=False,
        description="Run the five S0 SKU microbench domains on one admitted die.",
    )
    parser.add_argument("--sku", default=DAV_2201, help="bench SKU (default DAV_2201)")
    parser.add_argument("--domain", type=int, default=None, choices=_DOMAIN_IDS)
    parser.add_argument("--dtype", action="append", default=None)
    parser.add_argument("--allowed-phy-ids", default=None)
    parser.add_argument("--sparse-visible-devices", action="store_true")
    parser.add_argument("--l2-mib", type=float, default=None)
    parser.add_argument("--slot-bytes", type=int, default=DEFAULT_SLOT_BYTES)
    parser.add_argument("--allow-cpu-smoke", action="store_true")
    parser.add_argument("--resume", default=None)
    parser.add_argument("--observations", default=None)
    parser.add_argument("--out", "--output", dest="output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _sku_parser().parse_args(list(argv or ()))
    cases = build_cases(domain=args.domain, sku=args.sku, dtypes=args.dtype)
    if args.limit is not None:
        if args.limit < 0:
            raise ProfilerUsageError("bench_limit_invalid")
        cases = cases[: args.limit]
    if args.dry_run:
        emit_sku_output(
            portable_receipt(
                {
                    "schema": MICROBENCH_SCHEMA, "status": "dry_run",
                    "sku": args.sku, "case_count": len(cases), "cases": cases,
                },
                home=os.environ.get("HOME"),
            ),
            args.output,
        )
        return 0
    try:
        import torch
        import torch_npu  # noqa: F401
    except TimeoutError:
        raise
    except Exception as exc:
        emit_sku_output(
            {"schema": MICROBENCH_SCHEMA, "status": "torch_npu_unavailable", "reason": str(exc)[:_REASON_LIMIT]},
            args.output,
        )
        return _EXIT_UNAVAIL
    if args.l2_mib is not None:
        l2_bytes = int(args.l2_mib * MIB)
    elif not args.allow_cpu_smoke:
        l2_bytes = resolve_l2_bytes(None, sku=args.sku, torch_npu=torch_npu)
    else:
        l2_bytes = None
    plan = cold_ring_plan(l2_bytes, slot_bytes=args.slot_bytes) if l2_bytes is not None else None
    context = admit_context(
        torch=torch, torch_npu=torch_npu,
        allowed_phy_ids=resolve_allowed_phy_ids(args.allowed_phy_ids),
        l2_bytes=l2_bytes, slot_bytes=args.slot_bytes, allocate=plan is not None,
        sparse_visible_devices=bool(args.sparse_visible_devices),
        allow_cpu_smoke=bool(args.allow_cpu_smoke),
    )
    context["blocker_unit_op"] = make_blocker_unit_op(torch, context["device"]["ordinal"])
    context["run_id"] = f"{args.sku}-{uuid.uuid4().hex[:_RUN_ID_HEX_CHARS]}"
    try:
        result = run_cases(
            cases, context=context, resume=args.resume, observations=args.observations,
            sku=args.sku, home=os.environ.get("HOME"),
        )
        result.update(
            {
                "sku": args.sku, "ring_plan": plan,
                "context": {key: context[key] for key in ("device", "memory", "budget", "clock")},
            }
        )
        emit_sku_output(portable_receipt(result, home=os.environ.get("HOME")), args.output)
    finally:
        close_context(context)
    return 0 if result["status"] == "ok" else _EXIT_ERR


__all__ = [
    "CASE_SCHEMA", "DAV_2201", "DOMAIN_NAMES", "HELDOUT_M", "JsonlSink",
    "MICROBENCH_SCHEMA", "M_KNEE", "NARROW_N", "RECEIPT_SCHEMA",
    "ROUTING_ZERO_FRACTIONS", "SPILL_ACTIVE_RANGE", "SPILL_EXPERT_BYTES",
    "SUPPORTED_DTYPES", "SUPPORTED_SKUS", "bounded_row_remap", "build_cases",
    "group_list", "main", "measurement_modes", "ple_cases",
    "routing_distributions", "run_cases", "uniform_counts", "zero_experts",
    "zipf_counts",
]

if __name__ == "__main__":
    raise SystemExit(main())
