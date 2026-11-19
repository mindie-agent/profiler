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
  * The held-out split is frozen here, before any timing is acquired.
  * ``--resume`` appends one fsynced JSONL record per completed case and skips
    only ``(sku, case_id)`` records that already carry ``status == "ok"``; a
    torn tail is truncated to its last valid newline before appending.
  * ``--observations`` emits ``mindie-bench-observation/1`` repeat rows plus a
    ``case_complete`` marker per case.
  * Published receipts carry no home path, host address, device node or image
    digest locator.

[Timeouts & Locks]
  No locks.  Execution is single-process and bounded by the caller's container
  budget; each case owns its own allocation lifetime.

[Side-Effect Policy]
  Writes only the explicit ``--out`` JSON, ``--resume`` journal and
  ``--observations`` JSONL paths.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi import (
    capture_uri, portable_receipt, resolve_allowed_phy_ids, scrub_portable,
)
from .observations import (
    ObservationJournal, case_complete_row, observation_row,
)
from .operators import build_operator_enqueue, supports_cold_ring
from .timing import (
    DEFAULT_SLOT_BYTES, admit_context, calibrate_blocker, case_over_budget,
    close_context, cold_ring_plan, make_blocker_unit_op, measurement_modes,
)

MICROBENCH_SCHEMA = "mindie-bench-sku-microbench/1"
CASE_SCHEMA = "mindie-bench-case/1"
RECEIPT_SCHEMA = "mindie-bench-receipt/1"

DAV_2201 = "DAV_2201"
A2_SKUS = ("Ascend910B1", "Ascend910B2", "Ascend910B2C", "Ascend910B3", "Ascend910B4", "Ascend910B4-1")
A3_SKUS = ("Ascend910_9391", "Ascend910_9392", "Ascend910_9381", "Ascend910_9382", "Ascend910_9372", "Ascend910_9362")
SUPPORTED_SKUS = (DAV_2201, *A2_SKUS, *A3_SKUS)
SUPPORTED_DTYPES = ("bf16", "fp16", "int8", "w4a8")
FORBIDDEN_DTYPES = ("fp8", "fp8_e4m3", "fp8_e5m2", "mxfp8", "mxfp4", "hif8")
MIB = 1024 * 1024
KIB = 1024
_JOURNAL_MODE = 0o644

DOMAIN_NAMES = {
    1: "completion_minima", 2: "matrix_memory_paths",
    3: "grouped_moe_routing", 4: "attention_state", 5: "memory_io",
}

HELDOUT_M = (3, 12, 96, 384, 1536, 3072)
M_KNEE = tuple(sorted({2 ** exponent for exponent in range(0, 13)} | set(HELDOUT_M)))
NARROW_N = (64, 96, 128, 192, 256, 320, 384)
MATRIX_DTYPES = ("bf16", "fp16", "int8", "w4a8")
GEMM_SHAPES = ((4096, 4096, 4096), (4096, 18432, 7168), (32, 32, 7168))
NARROW_M = 1024
ROUTING_ZERO_FRACTIONS = (0.0, 0.25, 0.5, 0.75)
ROUTING_EXPERT_SHAPES = ((32, 7168, 4096), (64, 2048, 1024))
ROUTING_TOKENS = (32, 256, 4096, 16384)
ZIPF_EXPONENT = 1.2
SPILL_EXPERT_BYTES = 4 * MIB
SPILL_ACTIVE_RANGE = tuple(range(40, 51))
ATTENTION_HEADS = 8
ATTENTION_KV_HEADS = 1
ATTENTION_HEAD_DIM = 128
MLA_LATENT_DIM = 512
MLA_ROPE_DIM = 64
MLA_KV_BYTES_PER_TOKEN = (MLA_LATENT_DIM + MLA_ROPE_DIM) * 2
CACHELINE_BYTES = 128
PLE_BF16_ROW_BYTES = 320
PLE_INT8_ROW_BYTES = 180
PLE_OWNERSHIP_SHARDS = 8
PLE_ROW_SPAN = 262144
PINNED_COPY_SIZES = (4 * KIB, 1 * MIB, 16 * MIB)
GATHER_LENGTHS = (256, 4096)
INDEX_ADD_TOKENS = 4096
EMPTY_LAUNCHES = ("empty_aic", "empty_aiv")
BYTE_RATE_OPS = frozenset({"gather", "mte2_aic", "mte2_aiv", "pinned_copy",
                           "ple_lookup"})

def _heldout(*, matrix_m=None, batch=None, kv_len=None, routing=None,
             fabric=None) -> bool:
    """Freeze the held-out split: OR across every applicable axis."""
    if matrix_m is not None and matrix_m in HELDOUT_M:
        return True
    if batch == 16:
        return True
    if kv_len == 16384:
        return True
    if routing == ("zipf_s1.2", 0.5):
        return True
    if fabric is not None and fabric in (2 ** 15, 2 ** 19, 2 ** 23, 2 ** 27):
        return True
    return False

def uniform_counts(experts: int, tokens: int) -> list[int]:
    """Integer uniform histogram with an exact-sum remainder distribution."""
    _require(experts >= 1 and tokens >= 0, "bench_routing_shape_invalid")
    quotient, remainder = divmod(int(tokens), int(experts))
    return [quotient + (1 if index < remainder else 0) for index in range(experts)]

def zipf_counts(experts: int, tokens: int, exponent: float = ZIPF_EXPONENT) -> list[int]:
    """Deterministic Zipf histogram with largest-remainder integer rounding."""
    _require(experts >= 1 and tokens >= 0, "bench_routing_shape_invalid")
    _require(exponent > 0, "bench_routing_exponent_invalid")
    weights = [1.0 / float(index + 1) ** float(exponent) for index in range(experts)]
    total = sum(weights)
    raw = [int(tokens) * weight / total for weight in weights]
    counts = [int(math.floor(value)) for value in raw]
    remainder = int(tokens) - sum(counts)
    order = sorted(range(experts), key=lambda index: (-(raw[index] - counts[index]),
                                                     index))
    for index in order[:max(0, remainder)]:
        counts[index] += 1
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
        moved = sum(values[experts - zeros:])
        for index in range(experts - zeros, experts):
            values[index] = 0
        values = _redistribute(values, active, moved)
    return values

def _redistribute(values: list[int], active: Sequence[int], moved: int) -> list[int]:
    if moved <= 0:
        return values
    weights = [max(1, values[index]) for index in active]
    total = sum(weights)
    raw = [moved * weight / total for weight in weights]
    extra = [int(math.floor(value)) for value in raw]
    remainder = moved - sum(extra)
    order = sorted(range(len(active)),
                   key=lambda position: (-(raw[position] - extra[position]), position))
    for position in order[:max(0, remainder)]:
        extra[position] += 1
    for position, index in enumerate(active):
        values[index] += extra[position]
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
    for family, base in (("uniform", uniform_counts(experts, tokens)),
                         ("zipf_s1.2", zipf_counts(experts, tokens))):
        for fraction in ROUTING_ZERO_FRACTIONS:
            counts = zero_experts(base, fraction)
            _require(sum(counts) == tokens, "bench_group_list_sum_mismatch")
            signature = (family, tuple(counts))
            if signature in seen:
                continue  # tokens < experts: several fractions coincide.
            seen.add(signature)
            families.append({
                "distribution": family,
                "zero_fraction": fraction,
                "active_experts": sum(1 for item in counts if item > 0),
                "group_list": group_list(counts),
                "total_tokens": int(tokens),
            })
    return families

def bounded_row_remap(rows: Iterable[int], span: int = PLE_ROW_SPAN) -> dict[str, Any]:
    """Injective dense remap of owned rows into a bounded registered slab."""
    unique = sorted({int(row) for row in rows})
    _require(span >= 1, "bench_ple_span_invalid")
    _require(len(unique) <= span, "bench_ple_span_too_small")
    mapping = {row: index % span for index, row in enumerate(unique)}
    _require(len(set(mapping.values())) == len(mapping), "bench_ple_remap_not_injective")
    return {"rows": unique, "span": int(span), "slots": mapping,
            "injective": True, "footprint_rows": len(mapping)}

def ple_cases(dtypes: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """BF16 320 B/row and INT8 180 B/row bounded UVA/H2D lookups."""
    cases: list[dict[str, Any]] = []
    requested = set(dtypes) if dtypes else set(SUPPORTED_DTYPES)
    for dtype, row_bytes in (("bf16", PLE_BF16_ROW_BYTES), ("int8", PLE_INT8_ROW_BYTES)):
        if dtype not in requested:
            continue
        ids = [index * PLE_OWNERSHIP_SHARDS + 1 for index in range(256)]
        remap = bounded_row_remap(ids)
        for pattern in ("repeated", "rotating"):
            for path in ("uva_gather", "pinned_h2d"):
                case_id = f"d5.ple.{dtype}.{pattern}.{path}"
                cases.append(_case(
                    5, case_id, op="ple_lookup", dtype=dtype,
                    builder="ple_lookup",
                    shape={"tokens": len(ids), "row_bytes": row_bytes,
                           "width": row_bytes // _element_bytes(dtype),
                           "ownership_shards": PLE_OWNERSHIP_SHARDS},
                    work_bytes=len(ids) * row_bytes,
                    extra={"lookup_ids": ids,
                           "slot_map": remap["slots"],
                           "remap_span": remap["span"],
                           "remap_injective": True,
                           "reuse": pattern, "path": path},
                    split=_heldout()))
    return cases

def _case(domain: int, case_id: str, *, op: str, dtype: str, builder: str,
          shape: Mapping[str, Any], work_bytes: int = 0, work_flops: int = 0,
          split: bool = False, extra: Mapping[str, Any] | None = None,
          notes: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": CASE_SCHEMA, "case_id": case_id, "domain": domain,
        "domain_name": DOMAIN_NAMES[domain], "family": DOMAIN_NAMES[domain],
        "op": op, "dtype": dtype, "builder": builder, "shape": dict(shape),
        "work_bytes": int(work_bytes), "work_flops": int(work_flops),
        "split": "heldout" if split else "train",
        "timing": {"startup_ms": 0.0, "inclusive_minimum": True},
        "notes": notes,
    }
    if extra:
        payload.update(dict(extra))
    return payload

def build_cases(*, domain: int | None = None, sku: str = DAV_2201,
                dtypes: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Register the five domains without importing torch."""
    if sku not in SUPPORTED_SKUS:
        raise ProfilerUsageError(
            f"bench_sku_unsupported: {sku!r} is not a bench SKU; A5 silicon is "
            f"reclaimed and this suite measures {', '.join(SUPPORTED_SKUS)}")
    requested = list(dtypes) if dtypes else list(SUPPORTED_DTYPES)
    forbidden = [item for item in requested if item in FORBIDDEN_DTYPES]
    if forbidden:
        raise ProfilerUsageError(
            "bench_native_fp8_unsupported_on_dav_2201: native FP8 Cube is never "
            "constructed on A2/A3; use int8 or w4a8")
    unknown = [item for item in requested if item not in SUPPORTED_DTYPES]
    if unknown:
        raise ProfilerUsageError(f"bench_dtype_unsupported: {unknown}")
    protocol = ("hccs_dma" if sku in A3_SKUS else "pcie_dma" if sku in A2_SKUS else "host_dma")
    builders = {1: _domain1, 2: _domain2, 3: _domain3, 4: _domain4,
                5: lambda req: _domain5(req, transfer_protocol=protocol)}
    if domain is not None and domain not in builders:
        raise ProfilerUsageError(f"bench_domain_unknown: {domain}")
    selected = [domain] if domain is not None else sorted(builders)
    cases: list[dict[str, Any]] = []
    for index in selected: cases.extend(builders[index](requested))
    seen: set[str] = set()
    for item in cases:
        if item["case_id"] in seen:
            raise ProfilerUsageError(f"bench_case_id_duplicate: {item['case_id']}")
        seen.add(item["case_id"])
    return cases

def _domain1(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases = [
        _case(1, "d1.empty.event_pair", op="empty_event_pair", dtype="none",
              builder="empty_event_pair", shape={}),
        _case(1, "d1.empty.aic_launch", op="empty_aic", dtype="none",
              builder="empty_launch", shape={"kernel": "empty_aic"},
              extra={"kernel_class": "AIC", "task_count": 1}),
        _case(1, "d1.empty.aiv_launch", op="empty_aiv", dtype="none",
              builder="empty_launch", shape={"kernel": "empty_aiv"},
              extra={"kernel_class": "AIV", "task_count": 1}),
        _case(1, "d1.vector.bf16.1", op="vector_add", dtype="bf16",
              builder="vector_add", shape={"tokens": 1, "width": 1},
              work_bytes=6),
        _case(1, "d1.cube.bf16.1x16x16", op="cube_matmul", dtype="bf16",
              builder="matmul", shape={"m": 1, "n": 16, "k": 16},
              work_flops=2 * 1 * 16 * 16),
        _case(1, "d1.norm.bf16.1x128", op="rms_norm", dtype="bf16",
              builder="rms_norm", shape={"tokens": 1, "width": 128},
              work_bytes=2 * (128 * 2 + 128 * 2)),
        _case(1, "d1.w8a8.int8.1x128x128", op="w8a8_matmul", dtype="int8",
              builder="quant_matmul",
              shape={"m": 1, "n": 128, "k": 128,
                     "per_column_scale": [128], "per_token_scale": [1]},
              work_flops=2 * 1 * 128 * 128,
              extra={"scale_mode": "per_column", "per_token_scale": True}),
    ]
    return [case for case in cases
            if case["dtype"] == "none" or case["dtype"] in dtypes]

def _domain2(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for dtype in dtypes:
        for m, n, k in GEMM_SHAPES:
            cases.append(_case(
                2, f"d2.gemm.{dtype}.{m}x{n}x{k}", op="matmul", dtype=dtype,
                builder="matmul", shape={"m": m, "n": n, "k": k},
                work_flops=2 * m * n * k,
                work_bytes=_gemm_bytes(dtype, m, n, k),
                split=_heldout(matrix_m=m if m in HELDOUT_M else None),
                extra={"layout": "KN"}))
        for m in M_KNEE:
            cases.append(_case(
                2, f"d2.mknee.{dtype}.{m}x2048x7168", op="matmul", dtype=dtype,
                builder="matmul", shape={"m": m, "n": 2048, "k": 7168},
                work_flops=2 * m * 2048 * 7168,
                work_bytes=_gemm_bytes(dtype, m, 2048, 7168),
                split=_heldout(matrix_m=m), extra={"layout": "KN", "axis": "M"}))
        for n in NARROW_N:
            cases.append(_case(
                2, f"d2.splitk.{dtype}.{NARROW_M}x{n}x7168", op="matmul",
                dtype=dtype, builder="matmul",
                shape={"m": NARROW_M, "n": n, "k": 7168},
                work_flops=2 * NARROW_M * n * 7168,
                work_bytes=_gemm_bytes(dtype, NARROW_M, n, 7168),
                extra={"layout": "KN", "axis": "N", "split_k": True}))
            for layout in ("NK", "FRACTAL_NZ"):
                cases.append(_case(
                    2, f"d2.layout.{dtype}.{layout.lower()}.{NARROW_M}x{n}",
                    op="matmul", dtype=dtype, builder="matmul",
                    shape={"m": NARROW_M, "n": n, "k": 7168},
                    work_flops=2 * NARROW_M * n * 7168,
                    work_bytes=_gemm_bytes(dtype, NARROW_M, n, 7168),
                    extra={"layout": layout,
                           "format_code": 29 if layout == "FRACTAL_NZ" else None,
                           "prepared_outside_timing": layout == "FRACTAL_NZ"}))
        for direction in ("mte2_aic", "mte2_aiv"):
            for residency in ("dram", "l2"):
                for owners in ("one_owner", "full_owner"):
                    cases.append(_case(
                        2, f"d2.{direction}.{dtype}.{residency}.{owners}",
                        op=direction, dtype=dtype, builder="mte2_transfer",
                        shape={"bytes": _transfer_bytes(dtype, direction),
                               "residency": residency, "owners": owners},
                        work_bytes=_transfer_bytes(dtype, direction),
                        extra={"residency": residency, "owners": owners,
                               "consumed_result": True}))
    return cases

def _domain3(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for dtype in dtypes:
        for experts, k, n in ROUTING_EXPERT_SHAPES:
            for tokens in ROUTING_TOKENS:
                for family in routing_distributions(experts, tokens):
                    counts = family["group_list"]
                    case_id = (
                        f"d3.gmm.{dtype}.e{experts}.k{k}.n{n}.m{tokens}."
                        f"{family['distribution']}.z{int(family['zero_fraction'] * 100)}")
                    cases.append(_case(
                        3, case_id, op="npu_grouped_matmul", dtype=dtype,
                        builder="grouped_matmul",
                        shape={"e": experts, "k": k, "n": n, "m": tokens},
                        work_flops=2 * tokens * n * k,
                        work_bytes=_gemm_bytes(dtype, tokens, n, k)
                        + _extra_expert_bank_bytes(dtype, experts, k, n),
                        split=_heldout(
                            routing=(family["distribution"], family["zero_fraction"])),
                        extra={
                            "group_list": counts, "group_list_type": 1,
                            "integer_group_list": True,
                            "zero_fraction": family["zero_fraction"],
                            "active_experts": family["active_experts"],
                            "distribution": family["distribution"],
                            "per_token_scale": True,
                        }))
    for active in SPILL_ACTIVE_RANGE:
        span = active * SPILL_EXPERT_BYTES
        group = group_list([1] * active + [0] * (64 - active))
        cases.append(_case(
            3, f"d3.spill.e64.active{active}.4mib", op="npu_grouped_matmul",
            dtype="bf16", builder="grouped_matmul",
            shape={"e": 64, "k": 2048, "n": 1024, "m": active,
                   "expert_bytes": SPILL_EXPERT_BYTES},
            work_flops=2 * active * 2048 * 1024,
            work_bytes=span,
            extra={"group_list": group, "group_list_type": 1,
                   "integer_group_list": True, "active_experts": active,
                   "l2_span_bytes": span, "l2_span_mib": span // MIB,
                   "covers_mib": [160, 200], "per_token_scale": True}))
    return cases

def _domain4(dtypes: Sequence[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    common = {"heads": ATTENTION_HEADS, "kv_heads": ATTENTION_KV_HEADS,
              "head_dim": ATTENTION_HEAD_DIM}
    flops = _attention_flops(ATTENTION_HEADS, 2048)
    for dtype in dtypes:
        specs = [
            ("fa", "tnd", dict(op="npu_fusion_attention", builder="fusion_attention",
                shape={**common, "layout": "TND", "sequences": ATTENTION_HEADS,
                       "seq_len": 2048}, work_flops=flops,
                extra={"input_layout": "TND", "actual_seq_qlen": True, "causal": True})),
            ("fia", "paged", dict(op="npu_fused_infer_attention_score",
                builder="fused_infer_attention",
                shape={**common, "layout": "TND", "block_size": 128,
                       "block_table": [16, 16], "seq_len": 2048}, work_flops=flops,
                extra={"input_layout": "TND", "block_size": 128,
                       "actual_seq_lengths": True, "paged": True})),
            ("ifa", "legacy", dict(op="npu_incre_flash_attention",
                builder="incre_flash_attention",
                shape={**common, "layout": "TND", "block_size": 128}, work_flops=flops,
                extra={"scale_value": True, "block_table": True,
                       "legacy_paged_binding": True})),
            ("mla", "absorbed", dict(op="absorbed_mla", builder="absorbed_mla",
                shape={"latent": MLA_LATENT_DIM, "rope": MLA_ROPE_DIM,
                       "kv_bytes_per_token": MLA_KV_BYTES_PER_TOKEN,
                       "tokens": 512, "single_backing": True},
                work_bytes=MLA_KV_BYTES_PER_TOKEN * 512,
                extra={"c_kv_bytes_per_token": MLA_KV_BYTES_PER_TOKEN,
                       "backing_buffers": 1, "absorbed": True,
                       "latent_split": [512, 64]})),
            ("gdn", "chunk", dict(op="npu_chunk_gated_delta_rule",
                builder="chunk_gated_delta_rule",
                shape={"sequences": 8, "head_dim": 128, "state_dtype": "bf16"},
                extra={"actual_seq_lengths": True, "initial_state_dtype": "bf16"})),
            ("kda", "recurrent", dict(op="chunk_kda_fwd", builder="chunk_kda_fwd",
                shape={"sequences": 8, "head_dim": 128, "state_dtype": "bf16"},
                extra={"provider_chain": ["fla_npu", "torch_npu"], "chunked": True})),
            ("conv1d", "update", dict(op="causal_conv1d_update",
                builder="causal_conv1d_update",
                shape={"width": 4 * ATTENTION_HEAD_DIM, "state_len": 3},
                extra={"fused_provider": "unknown", "python_reference": True})),
            ("indexer", "lightning", dict(op="lightning_indexer",
                builder="lightning_indexer",
                shape={"heads": ATTENTION_HEADS, "head_dim": ATTENTION_HEAD_DIM},
                extra={"metadata_separate": True,
                       "provider_namespace": "cann_ops_transformer"})),
        ]
        for suffix, tag, payload in specs:
            cases.append(_case(4, f"d4.{suffix}.{dtype}.{tag}", dtype=dtype, **payload))
    return cases

def _domain5(dtypes: Sequence[str], *, transfer_protocol: str = "host_dma") -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for dtype in dtypes:
        cases.append(_case(5, f"d5.index_add.{dtype}.shared_cacheline", op="index_add_", dtype=dtype, builder="index_add",
            shape={"rows": 1024, "tokens": INDEX_ADD_TOKENS, "cacheline_bytes": CACHELINE_BYTES},
            extra={"contention": "shared_cacheline", "indices_per_cacheline": CACHELINE_BYTES // 4}))
        cases.append(_case(5, f"d5.index_add.{dtype}.disjoint_cacheline", op="index_add_", dtype=dtype, builder="index_add",
            shape={"rows": 1024, "tokens": INDEX_ADD_TOKENS, "cacheline_bytes": CACHELINE_BYTES},
            extra={"contention": "disjoint_cacheline", "indices_per_cacheline": 1}))
        for length in GATHER_LENGTHS:
            cases.append(_case(5, f"d5.gather.{dtype}.stride128.{length}", op="gather", dtype=dtype, builder="strided_gather",
                shape={"length": length, "stride_bytes": CACHELINE_BYTES}, work_bytes=length * CACHELINE_BYTES,
                extra={"stride_bytes": CACHELINE_BYTES, "burst_amplification": True}))
        for size in PINNED_COPY_SIZES:
            for direction in ("h2d", "d2h"):
                cases.append(_case(5, f"d5.host_io.{dtype}.{direction}.{size}", op="pinned_copy", dtype=dtype, builder="pinned_copy",
                    shape={"bytes": size, "direction": direction, "pinned": True, "transfer_protocol": transfer_protocol},
                    work_bytes=size, extra={"direction": direction, "pinned": True, "transfer_protocol": transfer_protocol}))
    cases.extend(ple_cases(dtypes))
    return cases

def _gemm_bytes(dtype: str, m: int, n: int, k: int) -> int:
    """Activation + weight + output bytes; ``w4a8`` packs weights two-per-byte."""
    if dtype == "w4a8":
        return (int(m) * int(k) + int(k) * int(n) // 2
                + int(m) * int(n) * _element_bytes("bf16"))
    element = _element_bytes(dtype)
    return (int(m) * int(k) * element + int(k) * int(n) * element
            + int(m) * int(n) * element)

def _extra_expert_bank_bytes(dtype: str, experts: int, k: int, n: int) -> int:
    """Add the remaining per-expert banks; ``_gemm_bytes`` already holds one."""
    weight = (int(k) * int(n) // 2 if dtype == "w4a8"
              else int(k) * int(n) * _element_bytes(dtype))
    return max(0, int(experts) - 1) * weight

def _element_bytes(dtype: str) -> int:
    if dtype in {"bf16", "fp16"}:
        return 2
    if dtype == "int8":
        return 1
    if dtype == "w4a8":
        return 1  # Packed 4-bit weights: one byte per two elements is refined
        # by the builder; the per-element byte keeps the envelope conservative.
    return 2

def _transfer_bytes(dtype: str, direction: str) -> int:
    """One isolated GM->L1 (AIC) or GM->UB (AIV) transfer window."""
    return 256 * KIB

def _attention_flops(heads: int, seq_len: int) -> int:
    return 4 * int(heads) * int(seq_len) * int(seq_len) * ATTENTION_HEAD_DIM

def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProfilerUsageError(reason)

class JsonlSink:
    """Append-only, fsynced JSONL trial log with torn-tail repair."""
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.repair()

    def repair(self) -> int:
        """Truncate an unterminated/invalid tail before any append."""
        return ObservationJournal(self.path).repair()
    def _records(self):
        self.repair()
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, Mapping):
                    yield dict(record)
    def completed_case_keys(self) -> set[tuple[Any, str]]:
        keys: set[tuple[Any, str]] = set()
        for record in self._records():
            if record.get("status") != "ok":
                continue
            case_id = record.get("case_id")
            if isinstance(case_id, str) and case_id:
                keys.add((record.get("sku"), case_id))
        return keys
    def completed_case_ids(self) -> set[str]:
        return {case_id for _sku, case_id in self.completed_case_keys()}
    def append(self, record: Mapping[str, Any]) -> None:
        if self.path.exists() and self.path.stat().st_size:
            with self.path.open("rb") as handle:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    self.repair()
        line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, _JOURNAL_MODE)
        try:
            payload = line.encode("utf-8")
            written = os.write(descriptor, payload)
            if written != len(payload):
                raise ProfilerUsageError("bench_resume_short_write")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

def _timing_repeats(timing: Mapping[str, Any]):
    modes = timing.get("modes") if isinstance(timing.get("modes"), Mapping) else {}
    for mode, summary in modes.items():
        for trial in (summary or {}).get("trials") or ():
            for index, value in enumerate(trial.get("repeats_us") or ()):
                yield str(mode), int(trial.get("trial") or 0), index, float(value)

def _emit_observations(journal: Any, case: Mapping[str, Any],
                       record: Mapping[str, Any], sku: Any, run_id: str) -> None:
    if journal is None or record.get("status") != "ok":
        return
    timing = record.get("timing")
    if not isinstance(timing, Mapping):
        return
    flops = int(case.get("work_flops") or 0)
    byte_rate = case.get("work_bytes") if case.get("op") in BYTE_RATE_OPS else None
    knee = ({"work": flops, "resource": "cube", "work_unit": "flops", "active_units": 1}
            if flops > 0 and str(case.get("case_id") or "").startswith("d2.mknee.") else {})
    for mode, trial, repeat_index, repeat_us in _timing_repeats(timing):
        journal.append(observation_row(
            plan_id=sku, case=case, run_id=f"{run_id}.{mode}.t{trial}",
            split=str(case.get("split") or "train"),
            boundary=str(case.get("boundary") or "device_kernel"),
            timing_mode=mode, residency=str(case.get("residency") or "device"),
            trial=trial, repeat_index=repeat_index, rank=None,
            duration_ms=repeat_us / 1000.0,
            source=f"capture://bench-sku/{case.get('case_id')}/{mode}."
                   f"{trial}.{repeat_index}",
            validated=bool(record.get("validated", True)),
            qualified=bool(record.get("qualified", True)),
            level="operator", phase=case.get("phase"),
            execution={"mode": mode, "protocol": timing.get("protocol")},
            work_bytes=byte_rate, **knee))
    journal.append(case_complete_row(
        plan_id=sku, case_id=case.get("case_id"), run_id=run_id, sku=sku,
        status="ok", split=str(case.get("split") or "train"),
        summary={"domain": case.get("domain"), "op": case.get("op")}))

def run_cases(cases: Sequence[Mapping[str, Any]], *, context: Mapping[str, Any],
              resume: str | Path | None = None,
              observations: str | Path | None = None,
              sku: str | None = None,
              home: str | None = None) -> dict[str, Any]:
    """Execute admitted cases and append one portable receipt per case."""
    sink = JsonlSink(resume) if resume else None
    completed = sink.completed_case_keys() if sink else set()
    journal = ObservationJournal(observations) if observations else None
    protocol = context["protocol"]
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    recovered = 0
    run_id = str(context.get("run_id") or sku or "bench-sku")
    for case in cases:
        key = (sku, str(case["case_id"]))
        if key in completed:
            skipped.append(str(case["case_id"]))
            recovered += 1
            continue
        record = _run_one(case, context=context, protocol=protocol, home=home, sku=sku)
        records.append(record)
        if sink is not None:
            sink.append(record)
        _emit_observations(journal, case, record, sku, run_id)
    return {"schema": MICROBENCH_SCHEMA,
            "status": "ok" if all(item["status"] == "ok" for item in records)
            else "partial",
            "case_count": len(cases), "executed_case_count": len(records),
            "skipped_case_count": len(skipped), "skipped_case_ids": skipped,
            "recovered_records": recovered,
            "recovered_case_ids": list(skipped),
            "records": records}

def _run_one(case: Mapping[str, Any], *, context: Mapping[str, Any],
             protocol: Any, home: str | None,
             sku: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA, "sku": sku, "case_id": str(case["case_id"]),
        "domain": case["domain"], "op": case["op"], "dtype": case["dtype"],
        "split": case["split"], "status": "ok",
        "source_uri": capture_uri("bench-sku", str(case["case_id"])),
    }
    if case_over_budget(case, context.get("budget")):
        record.update({"status": "over_budget",
                       "reason": "case working set exceeds the S0 cap"})
        return scrub_portable(record, home=home)
    try:
        torch = context["torch"]
        enqueue = build_operator_enqueue(torch, case, context)
        ring = context.get("ring")
        cold = bool(ring is not None and getattr(ring, "allocated", False)
                    and supports_cold_ring(case))
        hot_enqueue, run_kwargs = None, {}
        if cold:
            effective = dict(case, cold_ring=True)
            enqueue = build_operator_enqueue(torch, effective, context)
            hot_enqueue = build_operator_enqueue(torch, effective, context, hot=True)
            precycle = getattr(ring, "precycle", None)
            if callable(precycle):
                precycle(int(getattr(protocol, "repeats", 0)) * 3)
            run_kwargs.update({"cold_ring": ring, "hot_enqueue": hot_enqueue})
        blocker, blocker_receipt = None, None
        unit_op = context.get("blocker_unit_op")
        if callable(unit_op):
            calibrated = calibrate_blocker(context["runtime"], unit_op)
            blocker_receipt = calibrated.receipt()
            if calibrated.repeats:
                blocker = _blocker_prefix(unit_op, calibrated.repeats)
        timing = protocol.run(
            enqueue, case_id=str(case["case_id"]),
            kind=("collective" if case["op"] in {"all_reduce", "all_gather"} else "operator"),
            nbytes=int(case.get("work_bytes") or 0), blocker=blocker,
            blocker_receipt=blocker_receipt, **run_kwargs)
        record.update({"timing": timing, "minimum_ms": timing["minimum_ms"],
                       "startup_ms": 0.0,
                       "validated": True,
                       "qualified": bool(timing.get("qualified", True)),
                       "work_bytes": int(case.get("work_bytes") or 0),
                       "work_flops": int(case.get("work_flops") or 0),
                       "group_list": case.get("group_list"),
                       "group_list_type": case.get("group_list_type")})
    except TimeoutError:
        raise
    except Exception as exc:
        status = ("unsupported_binding" if isinstance(exc, ProfilerUsageError)
                  else "failed")
        record.update({"status": status, "reason": str(exc)[:400]})
    return scrub_portable(record, home=home)
def _blocker_prefix(unit_op: Callable[[], Any], repeats: int) -> Callable[[], Any]:
    def arm():
        for _ in range(int(repeats)):
            unit_op()
    return arm
def _sku_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler bench sku", allow_abbrev=False,
        description="Run the five S0 SKU microbench domains on one admitted die.")
    parser.add_argument("--sku", default=DAV_2201, help="bench SKU (default DAV_2201)")
    parser.add_argument("--domain", type=int, default=None, choices=(1, 2, 3, 4, 5),
                        help="single domain; default runs all five")
    parser.add_argument("--dtype", action="append", default=None,
                        help="restrict dtypes (bf16/fp16/int8/w4a8; repeatable)")
    parser.add_argument("--allowed-phy-ids", default=None,
                        help="physical die allowlist, e.g. '12..15' or '0,1,4,5'")
    parser.add_argument("--sparse-visible-devices", action="store_true",
                        help="LOCAL_RANK carries an explicit sparse physical id")
    parser.add_argument("--l2-mib", type=float, default=None,
                        help="measured L2 per die in MiB (required for cold rings)")
    parser.add_argument("--slot-bytes", type=int, default=DEFAULT_SLOT_BYTES,
                        help="cold-ring slot size in bytes (default 8 MiB)")
    parser.add_argument("--resume", default=None, help="append-only JSONL trial log")
    parser.add_argument("--observations", default=None,
                        help="append mindie-bench-observation/1 rows here")
    parser.add_argument("--out", "--output", dest="output", default=None,
                        help="write the campaign JSON here; otherwise print to stdout")
    parser.add_argument("--dry-run", action="store_true",
                        help="emit the frozen case registry without touching a device")
    parser.add_argument("--limit", type=int, default=None,
                        help="execute at most N cases (bounded smoke run)")
    return parser
def main(argv: Sequence[str] | None = None) -> int:
    args = _sku_parser().parse_args(list(argv or ()))
    cases = build_cases(domain=args.domain, sku=args.sku, dtypes=args.dtype)
    if args.limit is not None:
        if args.limit < 0:
            raise ProfilerUsageError("bench_limit_invalid")
        cases = cases[: args.limit]
    if args.dry_run:
        _emit(portable_receipt({
            "schema": MICROBENCH_SCHEMA, "status": "dry_run", "sku": args.sku,
            "case_count": len(cases), "cases": cases,
        }, home=os.environ.get("HOME")), args.output)
        return 0
    try:
        import torch
        import torch_npu  # noqa: F401
    except TimeoutError:
        raise
    except Exception as exc:
        _emit({"schema": MICROBENCH_SCHEMA, "status": "torch_npu_unavailable",
               "reason": str(exc)[:400]}, args.output)
        return 3
    l2_bytes = None if args.l2_mib is None else int(args.l2_mib * MIB)
    plan = (cold_ring_plan(l2_bytes, slot_bytes=args.slot_bytes)
            if l2_bytes is not None else None)
    context = admit_context(
        torch=torch, torch_npu=torch_npu,
        allowed_phy_ids=resolve_allowed_phy_ids(args.allowed_phy_ids),
        l2_bytes=l2_bytes, slot_bytes=args.slot_bytes, allocate=plan is not None,
        sparse_visible_devices=bool(args.sparse_visible_devices))
    context["blocker_unit_op"] = make_blocker_unit_op(
        torch, context["device"]["ordinal"])
    context["run_id"] = f"{args.sku}-{os.getpid()}"
    try:
        result = run_cases(cases, context=context, resume=args.resume,
                           observations=args.observations, sku=args.sku,
                           home=os.environ.get("HOME"))
        result.update({"sku": args.sku, "ring_plan": plan,
                       "context": {key: context[key] for key in
                                   ("device", "memory", "budget", "clock")}})
        _emit(portable_receipt(result, home=os.environ.get("HOME")), args.output)
    finally:
        close_context(context)
    return 0 if result["status"] == "ok" else 2
def _emit(payload: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
        print(json.dumps({"output": str(target), "status": payload.get("status")},
                         sort_keys=True))
        return
    import sys
    sys.stdout.write(text)
__all__ = ["CASE_SCHEMA", "DAV_2201", "DOMAIN_NAMES", "HELDOUT_M", "JsonlSink",
           "MICROBENCH_SCHEMA", "M_KNEE", "NARROW_N", "RECEIPT_SCHEMA",
           "ROUTING_ZERO_FRACTIONS", "SPILL_ACTIVE_RANGE", "SPILL_EXPERT_BYTES",
           "SUPPORTED_DTYPES", "SUPPORTED_SKUS", "bounded_row_remap",
           "build_cases", "group_list", "main", "measurement_modes", "ple_cases",
           "routing_distributions", "run_cases", "uniform_counts", "zero_experts",
           "zipf_counts"]
if __name__ == "__main__":
    raise SystemExit(main())
