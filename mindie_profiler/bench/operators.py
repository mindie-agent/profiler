"""Canonical operator builders shared by the SKU suite and subgraph replay.

[Role]
  Turn a declared bench case (``builder``/``op``/``dtype``/``shape`` plus its
  contract fields) into a callable that enqueues the real NPU work: dtype
  resolution, quantized/grouped matmuls, TND/paged attention, absorbed MLA,
  state operators, memory/IO probes and HCCL collectives.

[Invariants]
  * Dispatch is by the declared ``builder`` or canonical ``op`` name, never by
    archetype, model id or case id.
  * ``bf16``/``fp16``/``int8`` never degrade to an implicit ``float32``;
    ``w4a8`` resolves to the integer weight dtype and packed 4-bit layouts.
  * ``FRACTAL_NZ`` requires ``npu_format_cast`` and fails closed when absent.
  * ``group_list_type == 0`` is preserved (it is a valid total-token split).
  * A named collective group that is absent is an error, never ``WORLD``;
    AllToAllV default splits conserve exactly ``sum(send) == elements``.
  * Absorbed MLA keeps one ``[tokens, 576]`` BF16 backing (``512`` latent +
    ``64`` rope = ``1152 B/token``) and slices views from it.
  * Unmapped catalog operators raise ``bench_builder_unavailable``.

[Timeouts & Locks]
  Builders allocate once, outside the timed window; no locks or threads.

[Side-Effect Policy]
  Allocates device memory through the caller-provided ``torch`` handle and
  returns closures; writes nothing.
"""

from __future__ import annotations

import importlib
import inspect
import math
from typing import Any, Callable, Mapping

from ..events import ProfilerUsageError

COLLECTIVE_OPS = ("all_reduce", "all_gather", "all_gather_into_tensor",
                  "reduce_scatter", "reduce_scatter_tensor", "all_to_all",
                  "all_to_all_single", "all_to_all_v", "send", "recv",
                  "npu_moe_distribute_dispatch_v2",
                  "npu_moe_distribute_combine_v2")
COLLECTIVE_ALIASES = {
    "all_reduce": "all_reduce", "all_gather": "all_gather_into_tensor",
    "all_gather_into_tensor": "all_gather_into_tensor",
    "reduce_scatter": "reduce_scatter_tensor",
    "reduce_scatter_tensor": "reduce_scatter_tensor",
    "all_to_all": "all_to_all_single", "all_to_all_single": "all_to_all_single",
    "all_to_all_v": "all_to_all_v", "send": "send", "recv": "recv",
    "mc2_dispatch": "mc2_dispatch", "mc2_combine": "mc2_combine",
    "npu_moe_distribute_dispatch_v2": "mc2_dispatch",
    "npu_moe_distribute_combine_v2": "mc2_combine"}
DTYPE_NAMES = {"bf16": "bfloat16", "bfloat16": "bfloat16", "fp16": "float16",
               "float16": "float16", "fp32": "float32", "float32": "float32",
               "int8": "int8", "int32": "int32", "int64": "int64",
               "uint8": "uint8", "w4a8": "int8", "int4": "int8"}
ELEMENT_BYTES = {"bf16": 2, "bfloat16": 2, "fp16": 2, "float16": 2, "fp32": 4,
                 "float32": 4, "int8": 1, "w4a8": 1, "int32": 4, "int64": 8,
                 "uint8": 1}
(RMS_NORM_EPSILON, ATTENTION_HEAD_DIM, MLA_LATENT_DIM, MLA_ROPE_DIM,
 CACHELINE_BYTES, SCALE_ROW_COUNT, GATHER_ROW_BYTES) = (1e-6, 128, 512, 64,
                                                        128, 5, 16)
(NZ_FORMAT_CODE, TOPK_GATING_DEFAULT, INT8_PACK_NUMERATOR) = (29, 8, 2)
FLOAT32, BFLOAT16, INT8 = "float32", "bfloat16", "int8"

def resolve_op(torch: Any, name: str) -> Any:
    """Resolve a packet from the torch-npu or CANN operator namespace."""
    ops = getattr(torch, "ops", None)
    for namespace in ("npu", "cann_ops_transformer"):
        container = getattr(ops, namespace, None) if ops is not None else None
        candidate = getattr(container, name, None) if container is not None else None
        if callable(candidate):
            return candidate
    direct = getattr(torch, name, None)
    return direct if callable(direct) else None

def torch_dtype(torch: Any, name: Any) -> Any:
    """Map canonical dtype names onto the installed torch aliases."""
    mapped = DTYPE_NAMES.get(str(name or "").strip().lower())
    return getattr(torch, mapped, None) if mapped is not None else None

def element_bytes(dtype: Any) -> int:
    return ELEMENT_BYTES.get(str(dtype or "").strip().lower(), 2)

def device_of(context: Mapping[str, Any]) -> str:
    return f"npu:{context['device']['ordinal']}"

def _shape(case: Mapping[str, Any]) -> Mapping[str, Any]:
    shape = case.get("shape")
    return shape if isinstance(shape, Mapping) else {}

def _int(shape: Mapping[str, Any], key: str, default: int = 1) -> int:
    try:
        return max(1, int(shape.get(key, default)))
    except (TypeError, ValueError):
        return default

def _dtype(torch: Any, case: Mapping[str, Any]) -> Any:
    resolved = torch_dtype(torch, case.get("dtype") or "bf16")
    if resolved is None:
        raise ProfilerUsageError(
            f"bench_dtype_unavailable: {case.get('dtype')!r} is not installed")
    return resolved

def _zeros(torch: Any, *shape: int, dtype: Any = None, device: str) -> Any:
    return torch.zeros(*shape, dtype=dtype, device=device)
def _ones(torch: Any, *shape: int, dtype: Any = None, device: str) -> Any:
    return torch.ones(*shape, dtype=dtype, device=device)
def _randn(torch: Any, *shape: int, dtype: Any = None, device: str) -> Any:
    return torch.randn(*shape, dtype=dtype, device=device)

def _accepts(op: Any, name: str) -> bool:
    """Check the installed schema/signature before sending an optional kwarg."""
    try:
        parameters = inspect.signature(op).parameters
    except (TypeError, ValueError):
        return True
    return name in parameters or any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values())

def _upstream(context: Mapping[str, Any], expected_elements: int) -> Any:
    """Use a producer output along a data edge only when its size matches."""
    inputs = context.get("_node_inputs") or ()
    if not inputs:
        return None
    value = inputs[0]
    numel = getattr(value, "numel", None)
    try:
        count = int(numel()) if callable(numel) else None
    except (TypeError, RuntimeError, ValueError):
        return None
    return value if count == expected_elements else None


def _ring_matrix(context: Mapping[str, Any], case: Mapping[str, Any],
                 rows: int, columns: int, dtype: Any, hot: bool) -> Any:
    """Rotate a fitting operand slice out of the cold ring, else ``None``."""
    ring = context.get("ring")
    if ring is None or not getattr(ring, "allocated", False):
        return None
    nbytes = int(rows) * int(columns) * element_bytes(case.get("dtype"))
    if nbytes <= 0 or nbytes > int(ring.plan["slot_stride_bytes"]):
        return None
    try:
        sliced, _receipt = ring.slice_bytes(nbytes, hot=hot, dtype=dtype)
    except ProfilerUsageError:
        return None
    viewer = getattr(sliced, "view", None)
    if not callable(viewer):
        return None
    try:
        return viewer(rows, columns)
    except (RuntimeError, TypeError, ValueError):
        return None

def _empty_event_pair(_torch, _case, _context):
    return lambda: None

def _empty_launch(_torch, case, context):
    kernel = str(_shape(case).get("kernel") or case.get("op") or "")
    launcher = (context.get("empty_launchers") or {}).get(kernel)
    if not callable(launcher):
        raise ProfilerUsageError(f"bench_empty_launch_unavailable: {kernel}")
    return launcher

def _vector_add(torch, case, context):
    shape, device = _shape(case), device_of(context)
    width, tokens = _int(shape, "width"), _int(shape, "tokens")
    dtype = _dtype(torch, case)
    left = (_upstream(context, tokens * width)
            or _ones(torch, tokens, width, dtype=dtype, device=device))
    right = _ones(torch, tokens, width, dtype=dtype, device=device)
    out = _zeros(torch, tokens, width, dtype=dtype, device=device)
    return lambda: torch.add(left, right, out=out)

def _norm(torch, case, context, *, add: bool):
    shape, device = _shape(case), device_of(context)
    width, tokens = _int(shape, "width"), _int(shape, "tokens")
    dtype = _dtype(torch, case)
    inputs = (_upstream(context, tokens * width)
              or _randn(torch, tokens, width, dtype=dtype, device=device))
    residual = _randn(torch, tokens, width, dtype=dtype, device=device) if add else None
    gamma = _ones(torch, width, dtype=dtype, device=device)
    op = resolve_op(torch, "npu_add_rms_norm" if add else "npu_rms_norm")
    if callable(op):
        return ((lambda: op(inputs, residual, gamma, RMS_NORM_EPSILON)) if add
                else (lambda: op(inputs, gamma, RMS_NORM_EPSILON)))
    def composite():
        value = torch.add(inputs, residual) if add else inputs
        mean = torch.mean(torch.mul(value, value), dim=-1, keepdim=True)
        return torch.mul(value, gamma) / torch.sqrt(mean + RMS_NORM_EPSILON)
    return composite

def _gated(torch, case, context, op_name: str, kind: str):
    shape, device = _shape(case), device_of(context)
    tokens, width = _int(shape, "tokens"), _int(shape, "width")
    dtype = _dtype(torch, case)
    inputs = _randn(torch, tokens, width * 2, dtype=dtype, device=device)
    op = resolve_op(torch, op_name)
    if callable(op):
        return lambda: op(inputs)
    def composite():
        gate, up = torch.chunk(inputs, 2, dim=-1)
        gate = gate * torch.sigmoid(gate * 1.702 if kind == "gelu" else gate)
        return gate * up
    return composite

def _moe_gating_topk(torch, case, context):
    shape, device = _shape(case), device_of(context)
    tokens = _int(shape, "tokens")
    experts = _int(shape, "experts", _int(shape, "e", TOPK_GATING_DEFAULT))
    top_k = _int(shape, "top_k", 1)
    dtype = _dtype(torch, case)
    logits = _randn(torch, tokens, experts, dtype=dtype, device=device)
    op = resolve_op(torch, "npu_moe_gating_top_k_softmax")
    if callable(op):
        return lambda: op(logits, top_k)

    def composite():
        return torch.topk(torch.softmax(logits, dim=-1), top_k, dim=-1)

    return composite

def _moe_init_routing(torch, case, context):
    shape, device = _shape(case), device_of(context)
    tokens = _int(shape, "tokens")
    experts = _int(shape, "experts", _int(shape, "e", TOPK_GATING_DEFAULT))
    top_k = _int(shape, "top_k", 1)
    width = _int(shape, "width", ATTENTION_HEAD_DIM)
    dtype = _dtype(torch, case)
    inputs = _randn(torch, tokens, width, dtype=dtype, device=device)
    ids = _zeros(torch, tokens, top_k, dtype=getattr(torch, "int32", None),
                 device=device)
    op = resolve_op(torch, "npu_moe_init_routing_v2")
    if callable(op):
        return lambda: op(inputs, ids, None, None, experts, 0, top_k)
    return lambda: torch.gather(inputs, 0, ids[:, :1].expand(tokens, 1))

def _quant_matmul(torch, case, context, hot: bool = False):
    shape, device = _shape(case), device_of(context)
    m, n, k = _int(shape, "m"), _int(shape, "n"), _int(shape, "k")
    layout = str(case.get("layout") or shape.get("layout") or "ND").upper()
    op = resolve_op(torch, "npu_quant_matmul")
    if op is None:
        raise ProfilerUsageError("bench_builder_unavailable: npu_quant_matmul")
    dtype, float32 = getattr(torch, INT8, None), getattr(torch, FLOAT32, None)
    left = _ones(torch, m, k, dtype=dtype, device=device)
    right = _ones(torch, k, n, dtype=dtype, device=device)
    if layout == "FRACTAL_NZ":
        cast = resolve_op(torch, "npu_format_cast")
        if not callable(cast):
            raise ProfilerUsageError("bench_builder_unavailable: npu_format_cast")
        right = cast(right, int(case.get("format_code") or NZ_FORMAT_CODE))
    pertoken = _ones(torch, m, dtype=float32, device=device)
    kwargs = {"scale": [_ones(torch, n, dtype=float32, device=device)],
              "output_dtype": getattr(torch, BFLOAT16, None)}
    if _accepts(op, "pertoken_scale"):
        kwargs["pertoken_scale"] = [pertoken]
    elif _accepts(op, "per_token_scale"):
        kwargs["per_token_scale"] = [pertoken]
    return lambda: op(left, right, **kwargs)

def _matmul(torch, case, context, hot: bool = False):
    shape, device = _shape(case), device_of(context)
    if str(case.get("dtype") or "bf16").lower() in {"int8", "w4a8"}:
        return _quant_matmul(torch, case, context)
    m, n, k = _int(shape, "m"), _int(shape, "n"), _int(shape, "k")
    layout = str(case.get("layout") or shape.get("layout") or "ND").upper()
    dtype = _dtype(torch, case)
    left = (_upstream(context, m * k)
            or _randn(torch, m, k, dtype=dtype, device=device))
    if case.get("cold_ring"):
        left = _ring_matrix(context, case, m, k, dtype, hot) or left
    if layout == "NK":
        right = _randn(torch, n, k, dtype=dtype, device=device).t()
    elif layout == "FRACTAL_NZ":
        cast = resolve_op(torch, "npu_format_cast")
        if not callable(cast):
            raise ProfilerUsageError("bench_builder_unavailable: npu_format_cast")
        right = cast(_randn(torch, k, n, dtype=dtype, device=device),
                     int(case.get("format_code") or NZ_FORMAT_CODE))
    else:
        right = _randn(torch, k, n, dtype=dtype, device=device)
    matmul = getattr(torch, "mm", None) or getattr(torch, "matmul", None)
    if not callable(matmul):
        raise ProfilerUsageError("bench_builder_unavailable: torch.mm")
    return lambda: matmul(left, right)

def _grouped_matmul(torch, case, context, hot: bool = False):
    shape, device = _shape(case), device_of(context)
    experts, k, n = _int(shape, "e"), _int(shape, "k"), _int(shape, "n")
    counts = [int(item) for item in (case.get("group_list") or [])]
    if not counts:
        counts = [_int(shape, "m")] + [0] * max(0, experts - 1)
    tokens = max(1, sum(counts))
    list_type = 0 if case.get("group_list_type") == 0 else int(
        case.get("group_list_type") or 1)
    op = resolve_op(torch, "npu_grouped_matmul")
    if op is None:
        raise ProfilerUsageError("bench_builder_unavailable: npu_grouped_matmul")
    kwargs = {"group_list": counts, "group_list_type": list_type,
              "split_item": 2, "group_type": 0}
    if str(case.get("dtype") or "bf16").lower() in {"int8", "w4a8"}:
        dtype = getattr(torch, INT8, None)
        inputs = _ones(torch, tokens, k, dtype=dtype, device=device)
        columns = (max(1, n // INT8_PACK_NUMERATOR)
                   if str(case.get("dtype")).lower() == "w4a8" else n)
        weights = _ones(torch, experts, k, columns, dtype=dtype, device=device)
        float32 = getattr(torch, FLOAT32, None)
        kwargs.update({"scale": [_ones(torch, n, dtype=float32, device=device)],
                       "per_token_scale": [_ones(torch, tokens, dtype=float32,
                                                 device=device)],
                       "output_dtype": getattr(torch, BFLOAT16, None)})
        return lambda: op([inputs], [weights], **kwargs)
    dtype = _dtype(torch, case)
    inputs = _randn(torch, tokens, k, dtype=dtype, device=device)
    weights = _randn(torch, experts, k, n, dtype=dtype, device=device)
    return lambda: op([inputs], [weights], **kwargs)

def _heads(shape: Mapping[str, Any]) -> tuple[int, int, int]:
    heads = _int(shape, "heads", _int(shape, "head_num"))
    kv_heads = _int(shape, "kv_heads", _int(shape, "num_key_value_heads", heads))
    return heads, kv_heads, _int(shape, "head_dim", ATTENTION_HEAD_DIM)

def _paged_kv(torch, shape, device, dtype, kv_heads, head_dim, kv_len):
    block_size = _int(shape, "block_size", 128)
    blocks = max(2, -(-kv_len // block_size))
    cache = _randn(torch, blocks, block_size, kv_heads, head_dim,
                   dtype=dtype, device=device)
    table = torch.tensor([list(range(1, blocks + 1))],
                         dtype=getattr(torch, "int32", None), device=device)
    return cache, table, block_size
def _attention(kind: str):
    """Build TND fusion, paged fused-infer or BSH incre-flash attention."""
    def build(torch, case, context):
        shape, device = _shape(case), device_of(context)
        dtype = _dtype(torch, case)
        heads, kv_heads, head_dim = _heads(shape)
        q_len = _int(shape, "seq_len", _int(shape, "q_len"))
        kv_len = _int(shape, "kv_len", q_len)
        scale = 1.0 / math.sqrt(head_dim)
        if kind == "fusion":
            op = resolve_op(torch, "npu_fusion_attention")
            if op is None:
                raise ProfilerUsageError(
                    "bench_builder_unavailable: npu_fusion_attention")
            query = _randn(torch, q_len, heads, head_dim, dtype=dtype,
                           device=device)
            key = _randn(torch, kv_len, kv_heads, head_dim, dtype=dtype,
                         device=device)
            value = _randn(torch, kv_len, kv_heads, head_dim, dtype=dtype,
                           device=device)
            return lambda: op(query=query, key=key, value=value, head_num=heads,
                              input_layout="TND", actual_seq_qlen=[q_len],
                              actual_seq_kvlen=[kv_len], scale=scale)
        if kind == "fused_infer":
            op = resolve_op(torch, "npu_fused_infer_attention_score")
            if op is None:
                raise ProfilerUsageError(
                    "bench_builder_unavailable: npu_fused_infer_attention_score")
            query = _randn(torch, q_len, heads, head_dim, dtype=dtype,
                           device=device)
            cache, table, block_size = _paged_kv(
                torch, shape, device, dtype, kv_heads, head_dim, kv_len)
            return lambda: op(query=query, key=cache, value=cache,
                              block_table=table, block_size=block_size,
                              num_heads=heads, num_key_value_heads=kv_heads,
                              input_layout="TND", actual_seq_lengths=[q_len],
                              actual_seq_lengths_kv=[kv_len], scale=scale)
        op = resolve_op(torch, "npu_incre_flash_attention")
        if op is None:
            raise ProfilerUsageError(
                "bench_builder_unavailable: npu_incre_flash_attention")
        batch = _int(shape, "batch", _int(shape, "sequences"))
        query = _randn(torch, batch, 1, heads * head_dim, dtype=dtype,
                       device=device)
        key = _randn(torch, batch, kv_len, kv_heads * head_dim, dtype=dtype,
                     device=device)
        value = _randn(torch, batch, kv_len, kv_heads * head_dim, dtype=dtype,
                       device=device)
        return lambda: op(query=query, key=key, value=value, num_heads=heads,
                          num_key_value_heads=kv_heads, input_layout="BSH",
                          actual_seq_lengths=[kv_len] * batch, scale_value=scale)
    return build
def _absorbed_mla(torch, case, context):
    shape, device = _shape(case), device_of(context)
    dtype = _dtype(torch, case)
    latent = _int(shape, "latent", MLA_LATENT_DIM)
    rope = _int(shape, "rope", MLA_ROPE_DIM)
    tokens, queries = _int(shape, "tokens"), _int(shape, "q_tokens", 1)
    backing = _zeros(torch, tokens, latent + rope, dtype=dtype, device=device)
    query_nope = _randn(torch, queries, latent, dtype=dtype, device=device)
    query_pe = _randn(torch, queries, rope, dtype=dtype, device=device)
    latent_view, rope_view = backing[:, :latent], backing[:, latent:]
    op = resolve_op(torch, "npu_fused_infer_attention_score")
    if callable(op):
        return lambda: op(query=query_nope, key=latent_view, value=rope_view,
                          num_heads=1, input_layout="TND",
                          actual_seq_lengths=[queries],
                          actual_seq_lengths_kv=[tokens])
    matmul = getattr(torch, "mm", None) or getattr(torch, "matmul", None)
    if not callable(matmul):
        raise ProfilerUsageError("bench_builder_unavailable: torch.mm")
    return lambda: matmul(query_nope, latent_view.t()) + matmul(query_pe, rope_view.t())
def _chunk_gated_delta_rule(torch, case, context):
    shape, device = _shape(case), device_of(context)
    op = resolve_op(torch, "npu_chunk_gated_delta_rule")
    if op is None:
        raise ProfilerUsageError(
            "bench_builder_unavailable: npu_chunk_gated_delta_rule")
    sequences, width = _int(shape, "sequences"), _int(shape, "head_dim")
    dtype = _dtype(torch, case)
    q, k, v = (_randn(torch, sequences, width, dtype=dtype, device=device)
               for _ in range(3))
    beta = _randn(torch, sequences, dtype=dtype, device=device)
    state = _zeros(torch, sequences, width, dtype=dtype, device=device)
    return lambda: op(q, k, v, beta=beta, initial_state=state,
                      actual_seq_lengths=[width] * sequences)
def _chunk_kda_fwd(torch, case, context):
    shape, device = _shape(case), device_of(context)
    op = resolve_op(torch, "chunk_kda_fwd")
    if op is None:
        raise ProfilerUsageError("bench_builder_unavailable: chunk_kda_fwd")
    sequences, width = _int(shape, "sequences"), _int(shape, "head_dim")
    dtype = _dtype(torch, case)
    q, k, v = (_randn(torch, sequences, width, dtype=dtype, device=device)
               for _ in range(3))
    return lambda: op(q, k, v)
def _causal_conv1d_update(torch, case, context):
    shape, device = _shape(case), device_of(context)
    width, state_len = _int(shape, "width"), _int(shape, "state_len", 3)
    dtype = _dtype(torch, case)
    inputs = _randn(torch, 1, width, dtype=dtype, device=device)
    state = _zeros(torch, 1, width, state_len, dtype=dtype, device=device)
    weight = _randn(torch, width, state_len, dtype=dtype, device=device)
    bias = _zeros(torch, width, dtype=dtype, device=device)
    concat = getattr(torch, "cat", None)
    def update():
        if callable(concat):
            shifted = concat((state[:, :, 1:], inputs.unsqueeze(-1)), dim=-1)
        else:  # pragma: no cover - minimal fake tensors only
            shifted = state.roll(-1, dims=-1)
            shifted[:, :, -1:].copy_(inputs.unsqueeze(-1))
        state.copy_(shifted)
        return (shifted * weight.unsqueeze(0)).sum(dim=-1) + bias
    return update
def _lightning_indexer(torch, case, context):
    shape, device = _shape(case), device_of(context)
    op = resolve_op(torch, "lightning_indexer")
    if op is None:
        raise ProfilerUsageError("bench_builder_unavailable: lightning_indexer")
    heads = _int(shape, "heads")
    head_dim = _int(shape, "head_dim", ATTENTION_HEAD_DIM)
    dtype = _dtype(torch, case)
    query = _randn(torch, heads, head_dim, dtype=dtype, device=device)
    key = _randn(torch, heads, head_dim, dtype=dtype, device=device)
    return lambda: op(query, key)
def _index_add(torch, case, context):
    shape, device = _shape(case), device_of(context)
    rows, tokens = _int(shape, "rows"), _int(shape, "tokens")
    cacheline = _int(shape, "cacheline_bytes", CACHELINE_BYTES)
    dtype = _dtype(torch, case)
    per_line = max(1, cacheline // element_bytes(case.get("dtype")))
    target = _zeros(torch, rows, per_line, dtype=dtype, device=device)
    source = _ones(torch, tokens, per_line, dtype=dtype, device=device)
    span = max(1, rows // per_line)
    if str(case.get("contention")) == "shared_cacheline":
        indices = [index % per_line for index in range(tokens)]
    else:
        indices = [(index % span) * per_line for index in range(tokens)]
    tensor = torch.tensor(indices, dtype=getattr(torch, "int32", None),
                          device=device)
    return lambda: target.index_add_(0, tensor, source)
def _strided_gather(torch, case, context):
    shape, device = _shape(case), device_of(context)
    length = _int(shape, "length")
    stride_bytes = _int(shape, "stride_bytes", CACHELINE_BYTES)
    row_bytes = _int(shape, "row_bytes", GATHER_ROW_BYTES)
    dtype = _dtype(torch, case)
    columns = max(1, row_bytes // element_bytes(case.get("dtype")))
    step = max(1, stride_bytes // max(1, row_bytes))
    stride = 1 if case.get("contiguous", step == 1) else step
    table = _randn(torch, length * stride, columns, dtype=dtype, device=device)
    tensor = torch.tensor([index * stride for index in range(length)],
                          dtype=getattr(torch, "int32", None), device=device)
    return lambda: table.index_select(0, tensor)
def _pinned_copy(torch, case, context):
    shape, device = _shape(case), device_of(context)
    size = _int(shape, "bytes")
    host = torch.empty(size, dtype=torch.uint8, pin_memory=True)
    target = torch.empty(size, dtype=torch.uint8, device=device)
    if str(shape.get("direction") or "h2d") == "h2d":
        return lambda: target.copy_(host, non_blocking=True)
    return lambda: host.copy_(target, non_blocking=True)
def _ple_slice(lookup: list[int], pattern: str, state: dict[str, int]) -> list[int]:
    if pattern != "rotating" or not lookup:
        return list(lookup)
    offset = state["offset"] % len(lookup)
    state["offset"] = offset + 1
    return lookup[offset:] + lookup[:offset]
def _ple_lookup(torch, case, context):
    shape, device = _shape(case), device_of(context)
    lookup = [int(item) for item in (case.get("lookup_ids") or [])] \
        or list(range(_int(shape, "tokens")))
    dtype_name = str(case.get("dtype") or "bf16").lower()
    row_bytes = _int(shape, "row_bytes", 0) or (
        320 if dtype_name == "bf16" else 180)
    codes = (160 if dtype_name == "int8"
             else max(1, row_bytes // element_bytes(dtype_name)))
    scales = SCALE_ROW_COUNT if dtype_name == "int8" else 0
    dtype = torch_dtype(torch, dtype_name)
    rows = max(lookup) + 1
    table = _zeros(torch, rows, codes, dtype=dtype, device=device)
    float32 = getattr(torch, FLOAT32, None)
    scale_table = (_zeros(torch, rows, scales, dtype=float32, device=device)
                   if scales else None)
    state, pattern = {"offset": 0}, str(case.get("reuse") or "repeated")
    int64 = getattr(torch, "int64", None)
    def ids_tensor():
        return torch.tensor(_ple_slice(lookup, pattern, state), dtype=int64,
                            device=device)
    path = str(case.get("path") or "uva_gather")
    host_slab = (torch.empty(rows, codes, dtype=dtype, pin_memory=True)
                 if path == "uva_gather" else None)
    if path == "pinned_h2d":
        host = torch.empty(len(lookup), codes, dtype=dtype, pin_memory=True)
        host_scales = (torch.empty(len(lookup), scales, dtype=float32,
                                   pin_memory=True) if scales else None)
        def pinned():
            tensor = ids_tensor()
            table.index_copy_(0, tensor, host[: tensor.numel() // codes])
            if scale_table is not None:
                scale_table.index_copy_(0, tensor,
                                        host_scales[: tensor.numel() // codes])
            return table.index_select(0, tensor)
        return pinned
    def gathered():
        tensor, source = ids_tensor(), host_slab if host_slab is not None else table
        if scale_table is None:
            return source.index_select(0, tensor)
        return (source.index_select(0, tensor),
                scale_table.index_select(0, tensor))
    return gathered
def _mte2_transfer(_torch, case, context):
    direction = str(case.get("op") or "mte2_aic")
    probe = (context.get("native_probes") or {}).get(direction)
    if not callable(probe):
        raise ProfilerUsageError(
            f"bench_native_probe_absent: {direction} needs an ABI-matched native "
            "probe; a tensor copy is not an isolated MTE2 transfer")
    return lambda: probe(int(_shape(case).get("bytes") or 0),
                         residency=str(case.get("residency") or "dram"),
                         owners=str(case.get("owners") or "one_owner"))
def _group_for(case: Mapping[str, Any], context: Mapping[str, Any]) -> Any:
    name = str(case.get("group") or "")
    groups = context.get("groups") or {}
    if not name:
        return groups.get("tp")
    if name not in groups:
        raise ProfilerUsageError(
            f"bench_collective_group_missing: named axis group {name!r} was not "
            "created for this rank; refusing to fall through to WORLD")
    return groups[name]
def _default_splits(elements: int, group_size: int) -> list[int]:
    quotient, remainder = divmod(int(elements), max(1, int(group_size)))
    return [quotient + (1 if index < remainder else 0)
            for index in range(group_size)]
def _bind_collective(torch: Any, case: Mapping[str, Any],
                     context: Mapping[str, Any], kind: str) -> Callable[[], Any]:
    """Bind one HCCL collective to its declared group and split matrices."""
    dist = context.get("dist") or importlib.import_module("torch.distributed")
    group = _group_for(case, context)
    shape = _shape(case)
    elements = max(1, int(case.get("nbytes") or shape.get("bytes") or 4096) // 4)
    device = device_of(context)
    float32 = getattr(torch, FLOAT32, None)
    buffer = _zeros(torch, elements, dtype=float32, device=device)
    group_size = max(1, int(case.get("group_size") or shape.get("group_size") or 1))
    if kind == "all_reduce":
        return lambda: dist.all_reduce(buffer, group=group)
    if kind == "all_gather_into_tensor":
        out = _zeros(torch, elements * group_size, dtype=float32, device=device)
        return lambda: dist.all_gather_into_tensor(out, buffer, group=group)
    if kind == "reduce_scatter_tensor":
        out = _zeros(torch, max(1, elements // group_size), dtype=float32,
                     device=device)
        return lambda: dist.reduce_scatter_tensor(out, buffer, group=group)
    if kind in {"all_to_all_single", "all_to_all_v"}:
        out = _zeros(torch, elements, dtype=float32, device=device)
        if kind == "all_to_all_single":
            return lambda: dist.all_to_all_single(out, buffer, group=group)
        send = [int(item) for item in (case.get("send_counts")
                                       or _default_splits(elements, group_size))]
        recv = [int(item) for item in (case.get("recv_counts") or send)]
        return lambda: dist.all_to_all_single(out, buffer,
                                              output_split_sizes=recv,
                                              input_split_sizes=send, group=group)
    if kind in {"send", "recv"}:
        peer = int(case.get("peer") or 0)
        if kind == "send":
            return lambda: dist.send(buffer, dst=peer, group=group)
        return lambda: dist.recv(buffer, src=peer, group=group)
    if kind in {"mc2_dispatch", "mc2_combine"}:
        name = ("npu_moe_distribute_dispatch_v2" if kind == "mc2_dispatch"
                else "npu_moe_distribute_combine_v2")
        op = resolve_op(torch, name)
        if op is None:
            raise ProfilerUsageError(f"bench_builder_unavailable: {name}")
        count = int(case.get("tokens") or shape.get("tokens") or 1)
        width = int(case.get("width") or shape.get("width") or ATTENTION_HEAD_DIM)
        inputs = _randn(torch, count, width, dtype=_dtype(torch, case),
                        device=device)
        return lambda: op(inputs, group=group)
    raise ProfilerUsageError(f"bench_collective_unsupported: {kind}")
def _send_recv(torch, case, context):
    direction = str(case.get("direction") or case.get("op") or "send")
    rank, pair = int(context.get("rank") or 0), case.get("pair")
    if direction not in {"send", "recv"}:
        direction = ("send" if isinstance(pair, (list, tuple)) and rank == pair[0]
                     else "recv")
    return _bind_collective(torch, case, context, direction)
def _unmapped_catalog_op(_torch, case, _context):
    raise ProfilerUsageError(
        f"bench_builder_unavailable: "
        f"{case.get('unsupported_reason') or case.get('op')}")
_norm_factory = lambda add: (lambda torch, case, context:
                              _norm(torch, case, context, add=add))
_gate_factory = lambda name, kind: (lambda torch, case, context:
                                    _gated(torch, case, context, name, kind))
_BUILDERS: dict[str, Callable[..., Callable[[], Any]]] = {
    "empty_event_pair": _empty_event_pair, "empty_launch": _empty_launch,
    "vector_add": _vector_add, "rms_norm": _norm_factory(False),
    "add_rms_norm": _norm_factory(True),
    "swiglu": _gate_factory("npu_swiglu", "silu"),
    "geglu": _gate_factory("npu_geglu", "gelu"),
    "moe_gating_topk": _moe_gating_topk, "moe_init_routing": _moe_init_routing,
    "matmul": _matmul, "quant_matmul": _quant_matmul,
    "grouped_matmul": _grouped_matmul,
    "fusion_attention": _attention("fusion"),
    "fused_infer_attention": _attention("fused_infer"),
    "incre_flash_attention": _attention("incre_flash"),
    "absorbed_mla": _absorbed_mla, "chunk_gated_delta_rule": _chunk_gated_delta_rule,
    "chunk_kda_fwd": _chunk_kda_fwd, "causal_conv1d_update": _causal_conv1d_update,
    "lightning_indexer": _lightning_indexer, "index_add": _index_add,
    "strided_gather": _strided_gather, "pinned_copy": _pinned_copy,
    "ple_lookup": _ple_lookup, "mte2_transfer": _mte2_transfer,
    "send_recv": _send_recv, "unmapped_catalog_op": _unmapped_catalog_op}
_OP_BUILDERS = {
    "empty_event_pair": "empty_event_pair", "empty_launch": "empty_launch",
    "vector_add": "vector_add", "cube_matmul": "matmul", "matmul": "matmul",
    "w8a8_matmul": "quant_matmul", "npu_quant_matmul": "quant_matmul",
    "quant_matmul": "quant_matmul", "npu_grouped_matmul": "grouped_matmul",
    "grouped_matmul": "grouped_matmul",
    "npu_fusion_attention": "fusion_attention",
    "npu_fused_infer_attention_score": "fused_infer_attention",
    "npu_incre_flash_attention": "incre_flash_attention",
    "absorbed_mla": "absorbed_mla",
    "npu_chunk_gated_delta_rule": "chunk_gated_delta_rule",
    "chunk_kda_fwd": "chunk_kda_fwd", "causal_conv1d_update": "causal_conv1d_update",
    "lightning_indexer": "lightning_indexer", "index_add_": "index_add",
    "index_add": "index_add", "gather": "strided_gather",
    "pinned_copy": "pinned_copy", "ple_lookup": "ple_lookup",
    "mte2_transfer": "mte2_transfer", "mte2_aic": "mte2_transfer",
    "mte2_aiv": "mte2_transfer", "rms_norm": "rms_norm",
    "npu_rms_norm": "rms_norm", "add_rms_norm": "add_rms_norm",
    "npu_add_rms_norm": "add_rms_norm", "swiglu": "swiglu",
    "npu_swiglu": "swiglu", "geglu": "geglu", "npu_geglu": "geglu",
    "moe_gating_topk": "moe_gating_topk",
    "npu_moe_gating_top_k_softmax": "moe_gating_topk",
    "moe_init_routing": "moe_init_routing",
    "npu_moe_init_routing_v2": "moe_init_routing", "send_recv": "send_recv"}
for _alias, _kind in COLLECTIVE_ALIASES.items():
    _BUILDERS[_alias] = (lambda torch, case, context, _kind=_kind:
                         _bind_collective(torch, case, context, _kind))
    _OP_BUILDERS[_alias] = _alias
OPERATOR_BUILDERS = _BUILDERS
RING_BUILDERS = frozenset({"matmul", "quant_matmul", "grouped_matmul"})
def resolve_builder(case: Mapping[str, Any]) -> str:
    """Return the canonical builder name for one declared case."""
    declared = str(case.get("builder") or "").strip()
    return (declared if declared in _BUILDERS else
            _OP_BUILDERS.get(declared) or
            _OP_BUILDERS.get(str(case.get("op") or "").strip(), declared))
def build_operator_enqueue(torch: Any, case: Mapping[str, Any],
                           context: Mapping[str, Any], *,
                           hot: bool = False) -> Callable[[], Any]:
    """Resolve one operator builder from the declared binding (never a case id)."""
    builder = resolve_builder(case)
    factory = _BUILDERS.get(builder)
    if factory is None:
        raise ProfilerUsageError(f"bench_builder_unknown: {builder!r}")
    if builder in RING_BUILDERS:
        return factory(torch, case, context, hot=hot)
    return factory(torch, case, context)
def supports_cold_ring(case: Mapping[str, Any]) -> bool:
    return resolve_builder(case) in RING_BUILDERS
__all__ = ["COLLECTIVE_ALIASES", "COLLECTIVE_OPS", "DTYPE_NAMES", "ELEMENT_BYTES", "OPERATOR_BUILDERS", "RING_BUILDERS", "build_operator_enqueue", "device_of", "element_bytes", "resolve_builder", "resolve_op", "supports_cold_ring", "torch_dtype"]
