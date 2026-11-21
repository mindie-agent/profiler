"""Declarative context, batch and state plans for SKU microbench Domain 4.

[Role]
  Expand the attention and recurrent grids with explicit per-sequence query
  lengths and rank-local context-parallel planning data.

[Invariants]
  Train and held-out contexts are disjoint. Full-query, chunked-query and
  context-parallel cases each have their own case ID and declared geometry.

[Timeouts & Locks]
  Pure case construction; no timers or locks.

[Side-Effect Policy]
  Reads the packaged bench profile. No device imports, allocation or writes.
"""

from __future__ import annotations

from itertools import product
from typing import Any, Callable, Sequence

from .operators_common import FA_CAUSAL_SPARSE_MODE, attention_flops, causal_attention_pairs
from .profiles import profile_section

_CFG = profile_section("sku_microbench")
_OP_CFG = profile_section("operators")
_ELEMENT_BYTES = profile_section("timing")["element_bytes"]
_DOMAIN = next(int(key) for key, name in _CFG["domain_names"].items() if name == "attention_state")
CONTEXT_SEQ_GRID = tuple(_CFG["context_seq_grid"])
HELDOUT_CONTEXT_SEQ_LENS = tuple(_CFG["heldout_context_seq_lens"])
ATTENTION_HEADS = int(_CFG["attention_heads"])
ATTENTION_KV_HEADS = int(_CFG["attention_kv_heads"])
ATTENTION_HEAD_DIM = int(_CFG["attention_head_dim"])
MLA_LATENT_DIM = int(_CFG["mla_latent_dim"])
MLA_ROPE_DIM = int(_CFG["mla_rope_dim"])
MLA_KV_BYTES_PER_TOKEN = (MLA_LATENT_DIM + MLA_ROPE_DIM) * int(_ELEMENT_BYTES["bf16"])
_MLA_HEAD_SHAPE = {"latent": MLA_LATENT_DIM, "rope": MLA_ROPE_DIM}
_PAGED_BLOCK = int(_CFG["paged_block_size"])
_LINEAR_LOCAL_HEADS = int(_CFG["linear_attn_local_heads"])
_REC_SEQS = int(_CFG["recurrent_sequences"])
_CONV_WIDTH_FACTOR = int(_CFG["conv1d_width_factor"])
_CONV_STATE_LEN = int(_CFG["conv1d_state_len"])
_ATTN_SHAPE = {"heads": ATTENTION_HEADS, "kv_heads": ATTENTION_KV_HEADS, "head_dim": ATTENTION_HEAD_DIM}
_DSA_TOPK = int(_OP_CFG["dsa_index_topk"])
_CASE_FACTORY = Callable[..., dict[str, Any]]


def domain4_cases(dtypes: Sequence[str], make_case: _CASE_FACTORY) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    lin_h = _LINEAR_LOCAL_HEADS
    for dtype in dtypes:
        is_bf16 = dtype == "bf16"
        if dtype not in {"bf16", "fp16"}:
            continue
        for seq_len in (*CONTEXT_SEQ_GRID, *HELDOUT_CONTEXT_SEQ_LENS):
            split_kv = seq_len in HELDOUT_CONTEXT_SEQ_LENS
            # Keep resumed RC-1 results out of the revised full-shape grid.
            split_tag = "heldout" if split_kv else "train"
            pages = -(-seq_len // _PAGED_BLOCK)
            pf_pairs = causal_attention_pairs(seq_len, seq_len)
            pf_flops = attention_flops(pf_pairs, ATTENTION_HEADS, ATTENTION_HEAD_DIM)
            dec_flops = attention_flops(seq_len, ATTENTION_HEADS, ATTENTION_HEAD_DIM)
            grid_specs: list[tuple[str, str, bool, dict[str, Any]]] = [
                ("fa", f"tnd.s{seq_len}", True, dict(
                    op="npu_fusion_attention", builder="fusion_attention", work_flops=pf_flops, split=split_kv,
                    shape={**_ATTN_SHAPE, "layout": "TND", "sequences": 1, "tokens": seq_len,
                           "seq_len": seq_len, "sparse_mode": FA_CAUSAL_SPARSE_MODE},
                    extra={"phase": "prefill", "input_layout": "TND", "actual_seq_qlen": True, "causal": True})),
                ("fia", f"paged.s{seq_len}", True, dict(
                    op="npu_fused_infer_attention_score", builder="fused_infer_attention", work_flops=dec_flops, split=split_kv,
                    shape={**_ATTN_SHAPE, "layout": "TND", "block_size": _PAGED_BLOCK,
                           "block_table": [1, pages], "tokens": 1, "seq_len": seq_len},
                    extra={"phase": "decode", "input_layout": "TND", "block_size": _PAGED_BLOCK,
                           "actual_seq_lengths": True, "paged": True})),
                ("ifa", f"legacy.s{seq_len}", True, dict(
                    op="npu_incre_flash_attention", builder="incre_flash_attention", work_flops=dec_flops, split=split_kv,
                    shape={**_ATTN_SHAPE, "layout": "BSH", "block_size": _PAGED_BLOCK, "tokens": 1, "seq_len": seq_len},
                    extra={"phase": "decode", "scale_value": True, "block_table": True, "legacy_paged_binding": True})),
                ("mla", f"absorbed.s{seq_len}", is_bf16, dict(
                    op="absorbed_mla", builder="absorbed_mla", work_bytes=MLA_KV_BYTES_PER_TOKEN * seq_len, split=split_kv,
                    shape={"heads": ATTENTION_HEADS, "sequences": 1, "tokens": 1, "seq_len": seq_len,
                           **_MLA_HEAD_SHAPE, "kv_heads": 1, "head_dim": MLA_LATENT_DIM, "block_size": _PAGED_BLOCK,
                           "kv_bytes_per_token": MLA_KV_BYTES_PER_TOKEN, "single_backing": True},
                    extra={"phase": "decode", "c_kv_bytes_per_token": MLA_KV_BYTES_PER_TOKEN,
                           "backing_buffers": 1, "absorbed": True, "latent_split": [MLA_LATENT_DIM, MLA_ROPE_DIM]})),
                ("indexer", f"lightning.s{seq_len}", True, dict(
                    op="lightning_indexer", builder="lightning_indexer", split=split_kv,
                    shape={"tokens": 1, "heads": ATTENTION_HEADS, "kv_heads": 1,
                           "head_dim": ATTENTION_HEAD_DIM, "seq_len": seq_len, "top_k": min(seq_len, _DSA_TOPK)},
                    extra={"phase": "decode", "metadata_separate": True, "provider_namespace": "cann_ops_transformer"})),
                ("sfa", f"tnd.s{seq_len}", True, dict(
                    op="npu_sparse_flash_attention", builder="sparse_flash_attention", split=split_kv,
                    shape={"heads": ATTENTION_HEADS, "kv_heads": ATTENTION_KV_HEADS, "head_dim": MLA_LATENT_DIM,
                           "qk_rope_head_dim": MLA_ROPE_DIM, "tokens": 1, "seq_len": seq_len, "top_k": _DSA_TOPK},
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
                           "head_dim": ATTENTION_HEAD_DIM, "seq_len": seq_len, "state_dtype": "fp32"},
                    extra={"phase": "prefill", "provider_chain": ["vllm_ascend", "fla_npu", "torch_npu"], "chunked": True})),
            ]
            for suffix, tag, allowed, payload in grid_specs:
                if allowed:
                    cases.append(make_case(_DOMAIN, f"d4.{suffix}.{dtype}.{tag}.{split_tag}", dtype=dtype, **payload))
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
                cases.append(make_case(_DOMAIN, f"d4.{suffix}.{dtype}.{tag}", dtype=dtype, **payload))
        cases.extend(_cross_samples(dtype, make_case))
    return cases


def _paged_decode_samples(
    dtype: str, make_case: _CASE_FACTORY, seq_len: int, batch: int, q_len: int,
) -> list[dict[str, Any]]:
    tokens = batch * q_len
    pages = -(-seq_len // _PAGED_BLOCK)
    shape = {
        **_ATTN_SHAPE, "layout": "TND", "sequences": batch, "q_len": q_len,
        "tokens": tokens, "seq_len": seq_len, "block_size": _PAGED_BLOCK,
        "block_table": [batch, pages],
    }
    tag = f"b{batch}.q{q_len}.s{seq_len}"
    split = seq_len in HELDOUT_CONTEXT_SEQ_LENS
    eb = int(_ELEMENT_BYTES[dtype])
    kv_slots = batch * pages * _PAGED_BLOCK
    fia_elements = (tokens * ATTENTION_HEADS + 2 * kv_slots * ATTENTION_KV_HEADS) * ATTENTION_HEAD_DIM
    decode = {"phase": "decode", "mtp": q_len > 1, "paged": True}
    cases = [make_case(
        _DOMAIN, f"d4.fia.{dtype}.paged.{tag}", dtype=dtype,
        op="npu_fused_infer_attention_score", builder="fused_infer_attention", shape=shape, split=split,
        estimated_bytes=fia_elements * eb,
        work_flops=attention_flops(tokens * seq_len, ATTENTION_HEADS, ATTENTION_HEAD_DIM),
        extra={**decode, "input_layout": "TND", "actual_seq_lengths": True},
    )]
    if dtype == "bf16":
        cases.append(make_case(
            _DOMAIN, f"d4.mla.{dtype}.absorbed.{tag}", dtype=dtype,
            op="absorbed_mla", builder="absorbed_mla", split=split,
            shape={**shape, **_MLA_HEAD_SHAPE, "head_dim": MLA_LATENT_DIM,
                   "kv_bytes_per_token": MLA_KV_BYTES_PER_TOKEN, "single_backing": True},
            estimated_bytes=(tokens * ATTENTION_HEADS + kv_slots) * MLA_KV_BYTES_PER_TOKEN,
            work_bytes=batch * seq_len * MLA_KV_BYTES_PER_TOKEN,
            extra={**decode, "absorbed": True, "backing_buffers": 1},
        ))
    return cases


def _cross_samples(dtype: str, make_case: _CASE_FACTORY) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    decode_shapes = [(batch, 1) for batch in _CFG["cross_batches"]]
    decode_shapes.extend((1, q_len) for q_len in _CFG["mtp_query_lens"])
    for seq_len, (batch, q_len) in product(_CFG["cross_context_seq_lens"], decode_shapes):
        cases.extend(_paged_decode_samples(dtype, make_case, seq_len, batch, q_len))
    for seq_len, q_len in product(_CFG["chunked_prefill_context_seq_lens"], _CFG["chunked_prefill_lens"]):
        cases.append(make_case(
            _DOMAIN, f"d4.fa.{dtype}.chunk.q{q_len}.s{seq_len}", dtype=dtype,
            op="npu_fusion_attention", builder="fusion_attention",
            shape={**_ATTN_SHAPE, "layout": "TND", "sequences": 1, "q_len": q_len,
                   "tokens": q_len, "seq_len": seq_len},
            work_flops=attention_flops(q_len * seq_len, ATTENTION_HEADS, ATTENTION_HEAD_DIM),
            split=seq_len in HELDOUT_CONTEXT_SEQ_LENS,
            extra={"phase": "prefill", "chunked": True, "input_layout": "TND", "actual_seq_qlen": True},
        ))
    if dtype == "bf16":
        cases.extend(_recurrent_samples(dtype, make_case))
    cases.extend(_context_parallel_plans(dtype, make_case))
    return cases


def _recurrent_samples(dtype: str, make_case: _CASE_FACTORY) -> list[dict[str, Any]]:
    cases = []
    for state_len, batch, q_len in product(
        _CFG["recurrent_state_lens"], _CFG["recurrent_batches"], _CFG["recurrent_q_lens"],
    ):
        shape = {"tokens": batch * q_len, "sequences": batch, "q_len": q_len,
                 "state_len": state_len, "heads": ATTENTION_HEADS, "head_dim": ATTENTION_HEAD_DIM}
        tag = f"b{batch}.q{q_len}.state{state_len}"
        cases.append(make_case(
            _DOMAIN, f"d4.gdn.{dtype}.recurrent.{tag}", dtype=dtype,
            op="npu_recurrent_gated_delta_rule", builder="recurrent_gated_delta_rule",
            shape={**shape, "state_dtype": "bf16"},
            extra={"phase": "decode", "actual_seq_lengths": True, "ssm_state_indices": True},
        ))
        cases.append(make_case(
            _DOMAIN, f"d4.kda.{dtype}.recurrent.{tag}", dtype=dtype,
            op="fused_recurrent_kda", builder="fused_recurrent_kda",
            shape={**shape, "state_dtype": "fp32"},
            extra={"phase": "decode", "provider_chain": ["vllm_ascend"]},
        ))
    return cases


def _context_parallel_plans(dtype: str, make_case: _CASE_FACTORY) -> list[dict[str, Any]]:
    cases = []
    contexts = (
        seq_len for seq_len in (*CONTEXT_SEQ_GRID, *HELDOUT_CONTEXT_SEQ_LENS)
        if seq_len >= _CFG["multi_rank_pcp_dcp_min_ctx"]
    )
    for seq_len, world in product(contexts, _CFG["multi_rank_world_sizes"]):
        for axis in ("pcp", "dcp"):
            prefill = axis == "pcp"
            tokens = seq_len if prefill else 1
            cases.append(make_case(
                _DOMAIN, f"d4.{axis}.{dtype}.w{world}.s{seq_len}", dtype=dtype,
                op="npu_fusion_attention" if prefill else "npu_fused_infer_attention_score",
                builder="fusion_attention" if prefill else "fused_infer_attention",
                shape={**_ATTN_SHAPE, "layout": "TND", "tokens": tokens, "seq_len": seq_len},
                split=seq_len in HELDOUT_CONTEXT_SEQ_LENS,
                extra={"phase": "prefill" if prefill else "decode", "parallel_axis": axis,
                       "world_size": world, "rank_local_tokens": -(-seq_len // world)},
            ))
    return cases
