"""Contract tests for 1:1 bench operator builders, cold-ring rotation and fail-fast hints.

[Role]
  Verify the 101+ canonical 1:1 operator builders across the four domain modules
  (``operators_norm_quant``, ``operators_attention_mla``, ``operators_moe_comm``,
  ``operators_recurrent_mhc``), ``ColdRing`` narrowed typed views and per-repeat
  multi-slot rotation across inputs/weights/outputs, ``w4a8`` and
  ``FRACTAL_NZ=29`` routing, ``ple_lookup`` device safety, and fail-fast
  ``BenchUnmodeledOperatorError`` (``mindie-unmodeled-structure-hint/1``).

[Invariants]
  * No live NPU is touched; fake NPU tensors enforce strict device matching on
    ``index_select`` and track buffer addresses across repeats.
  * Zero ``inspect.signature`` calls exist anywhere under ``mindie_profiler``.

[Timeouts & Locks]
  Pure in-memory execution (< 2 s); no sleeps, threads or subprocesses.

[Side-Effect Policy]
  Allocates only lightweight Python fake tensors in memory.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path
import types
from typing import Any

import pytest

from mindie_profiler.bench import (
    BenchUnmodeledOperatorError,
    UNMODELED_HINT_SCHEMA,
    UnmodeledCapabilityError,
    operators as ops,
    timing,
)
from mindie_profiler.bench.operators_attention_mla import ATTENTION_MLA_BUILDERS
from mindie_profiler.bench.operators_moe_comm import MOE_COMM_BUILDERS
from mindie_profiler.bench.operators_norm_quant import NORM_QUANT_BUILDERS
from mindie_profiler.bench.operators_recurrent_mhc import RECURRENT_MHC_BUILDERS
from mindie_profiler.bench.timing_ring import resolve_l2_bytes
from mindie_profiler.events import ProfilerUsageError

REPO_ROOT = Path(__file__).resolve().parents[1]
MIB = 1024 * 1024


class FakeDtype(int):
    def __new__(cls, name: str, nbytes: int):
        dtype = super().__new__(cls, nbytes)
        dtype.name = name
        return dtype

    def __str__(self):
        return f"torch.{self.name}"


class FakeTensor:
    _next_addr = 1_000_000
    index_add_calls: list[tuple[Any, Any, Any]] = []

    def __init__(
        self,
        shape: tuple[int, ...],
        *,
        dtype: int = 2,
        device: str = "npu:0",
        addr: int | None = None,
        format_code: int = 2,
        pinned: bool = False,
    ) -> None:
        self.shape = tuple(int(d) for d in shape)
        self.dtype = dtype
        self.device = str(device)
        if addr is None:
            addr = FakeTensor._next_addr
            FakeTensor._next_addr += max(128, self.nbytes)
        self.addr = int(addr)
        self.format_code = int(format_code)
        self.pinned = bool(pinned)

    @property
    def nbytes(self) -> int:
        return max(1, math.prod(self.shape)) * max(1, self.dtype)

    def numel(self) -> int:
        return max(1, math.prod(self.shape))

    def narrow(self, dim: int, start: int, length: int) -> "FakeTensor":
        assert dim == 0 and len(self.shape) == 1
        assert 0 <= start and start + length <= self.shape[0]
        return FakeTensor(
            (length,),
            dtype=self.dtype,
            device=self.device,
            addr=self.addr + start * self.dtype,
            format_code=self.format_code,
        )

    def view(self, *args: int) -> "FakeTensor":
        if len(args) == 1 and isinstance(args[0], int) and len(self.shape) == 1:
            elem_bytes = args[0]
            if elem_bytes in {1, 2, 4, 8} and self.dtype == 1 and self.nbytes % elem_bytes == 0:
                return FakeTensor(
                    (self.nbytes // elem_bytes,),
                    dtype=elem_bytes,
                    device=self.device,
                    addr=self.addr,
                    format_code=self.format_code,
                )
        elems = math.prod(int(d) for d in args)
        assert elems * self.dtype == self.nbytes
        return FakeTensor(
            tuple(int(d) for d in args),
            dtype=self.dtype,
            device=self.device,
            addr=self.addr,
            format_code=self.format_code,
        )

    def t(self) -> "FakeTensor":
        assert len(self.shape) == 2
        return FakeTensor(
            (self.shape[1], self.shape[0]),
            dtype=self.dtype,
            device=self.device,
            addr=self.addr,
            format_code=self.format_code,
        )

    def __getitem__(self, item: Any) -> "FakeTensor":
        return FakeTensor(
            self.shape,
            dtype=self.dtype,
            device=self.device,
            addr=self.addr,
            format_code=self.format_code,
        )

    def fill_(self, _value: float) -> "FakeTensor":
        return self

    def zero_(self) -> "FakeTensor":
        return self

    def triu_(self, diagonal: int = 0) -> "FakeTensor":
        self.triangular_diagonal = diagonal
        return self

    def to(self, device: str) -> "FakeTensor":
        result = FakeTensor(self.shape, dtype=self.dtype, device=device)
        if hasattr(self, "triangular_diagonal"):
            result.triangular_diagonal = self.triangular_diagonal
        return result

    def pin_memory(self) -> "FakeTensor":
        assert self.device == "cpu"
        return FakeTensor(self.shape, dtype=self.dtype, device="cpu", addr=self.addr, pinned=True)

    def copy_(self, src: "FakeTensor", non_blocking: bool = False) -> "FakeTensor":
        assert isinstance(src, FakeTensor)
        _ = non_blocking
        return self

    def index_select(self, dim: int, index: "FakeTensor") -> "FakeTensor":
        assert dim == 0
        if self.device != index.device:
            raise RuntimeError(f"device mismatch: table on {self.device} vs index on {index.device}")
        return FakeTensor((index.shape[0], *self.shape[1:]), dtype=self.dtype, device=self.device)

    def index_add_(self, dim: int, index: "FakeTensor", src: "FakeTensor") -> "FakeTensor":
        assert dim == 0 and self.device == index.device == src.device
        FakeTensor.index_add_calls.append((self, index, src))
        return self


class FakeBackend:
    """Explicit fake NPU + HCCL + fla backend recording kernel dispatches."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.format_casts: list[tuple[tuple[int, ...], int]] = []
        self.tensor_values: list[tuple[int, ...]] = []
        self.torch = self._make_torch()
        self.dist = self._make_dist()

    def _record(self, name: str):
        def kernel(*args: Any, **kwargs: Any) -> FakeTensor | None:
            self.calls.append((name, args, kwargs))
            if name == "npu_kv_compress_epilog":
                return None
            first = next((a for a in args if isinstance(a, FakeTensor)), None)
            if first is None and args and isinstance(args[0], list) and args[0]:
                first = args[0][0]
            shape = first.shape if isinstance(first, FakeTensor) else (4, 16)
            dev = first.device if isinstance(first, FakeTensor) else "npu:0"
            return FakeTensor(shape, dtype=2, device=dev)

        return kernel

    def _make_torch(self) -> Any:
        t = types.SimpleNamespace()
        for name, nbytes in (("uint8", 1), ("int8", 1), ("bfloat16", 2), ("float16", 2),
                             ("float32", 4), ("int32", 4), ("int64", 8), ("bool", 1)):
            setattr(t, name, FakeDtype(name, nbytes))

        def alloc(*dims: Any, dtype: Any = 2, device: str = "npu:0", pin_memory: bool = False) -> FakeTensor:
            if len(dims) == 1 and isinstance(dims[0], (list, tuple)):
                shape = tuple(int(x) for x in dims[0])
            else:
                shape = tuple(int(x) for x in dims)
            dev = "cpu" if pin_memory else str(device or "npu:0")
            return FakeTensor(shape, dtype=dtype or 2, device=dev, pinned=pin_memory)

        t.zeros = alloc
        t.ones = alloc
        t.randn = alloc
        t.empty = alloc

        def make_tensor(data, dtype=4, device="npu:0") -> FakeTensor:
            nested = bool(data) and isinstance(data[0], (list, tuple))
            values = tuple(int(x) for row in data for x in row) if nested else tuple(
                int(x) for x in data)
            shape = (len(data), len(data[0])) if nested else (max(1, len(data)),)
            self.tensor_values.append(values)
            return FakeTensor(shape, dtype=dtype or 4, device=str(device))

        t.tensor = make_tensor

        def bin_op(name: str):
            def fn(a: FakeTensor, b: FakeTensor, out: FakeTensor | None = None) -> FakeTensor:
                target = out if out is not None else FakeTensor(a.shape, dtype=a.dtype, device=a.device)
                self.calls.append((name, (a, b, target), {}))
                return target

            return fn

        t.matmul = bin_op("matmul")
        t.mm = bin_op("mm")
        t.add = bin_op("add")
        t.mul = bin_op("mul")

        def index_select(src: FakeTensor, dim: int, idx: FakeTensor, out: FakeTensor | None = None) -> FakeTensor:
            res = src.index_select(dim, idx)
            target = out if out is not None else res
            self.calls.append(("index_select", (src, idx, target), {}))
            return target

        t.index_select = index_select
        t.nn = types.SimpleNamespace(
            functional=types.SimpleNamespace(
                layer_norm=self._record("layer_norm"),
                silu=self._record("silu"),
                gelu=self._record("gelu"),
                sigmoid=self._record("sigmoid"),
                softmax=self._record("softmax"),
                embedding=self._record("embedding"),
                pad=self._record("pad"),
            )
        )

        npu_ns = types.SimpleNamespace(synchronize=lambda: None)
        ascend_ns = types.SimpleNamespace()

        def format_cast(tensor: FakeTensor, code: int) -> FakeTensor:
            self.format_casts.append((tensor.shape, int(code)))
            return FakeTensor(
                tensor.shape, dtype=tensor.dtype, device=tensor.device,
                addr=tensor.addr, format_code=int(code),
            )

        npu_ns.npu_format_cast = format_cast
        for kernel_name in (
            "npu_rms_norm", "npu_add_rms_norm", "npu_gemma_rms_norm", "npu_layer_norm_eval",
            "npu_rms_norm_quant", "npu_add_rms_norm_quant", "npu_rms_norm_gated", "npu_l2_norm",
            "npu_dynamic_quant", "npu_swiglu", "npu_clipped_swiglu", "npu_swiglu_quant",
            "npu_dequant_swiglu_quant", "npu_situ", "npu_geglu", "npu_gelu", "npu_silu",
            "npu_sigmoid", "npu_softmax", "npu_fusion_attention",
            "npu_fused_infer_attention_score", "npu_incre_flash_attention",
            "npu_mla_prolog_v2", "npu_mla_prolog_v3", "npu_rotary_mul", "npu_topk_v2",
            "npu_quant_matmul", "npu_weight_quant_batchmatmul", "npu_grouped_matmul",
            "npu_grouped_matmul_swiglu_quant_v2", "npu_moe_gating_top_k_softmax",
            "npu_moe_gating_top_k_hash", "npu_moe_init_routing_v2", "npu_moe_token_permute",
            "npu_moe_token_unpermute", "npu_histogram_v2", "npu_moe_distribute_dispatch_v2",
            "npu_moe_distribute_combine_v2", "npu_moe_distribute_dispatch_v3",
            "npu_moe_distribute_combine_v3", "npu_megamoe", "npu_mm_reduce_scatter_base",
            "npu_all_gather_base_mm", "npu_quant_all_reduce", "npu_p2p_send_recv",
            "npu_muls_add", "npu_causal_conv1d", "npu_causal_conv1d_update",
            "npu_fused_gdn_gating", "npu_chunk_gated_delta_rule",
            "npu_chunk_gated_delta_rule_fwd_prepare", "npu_chunk_fwd_h", "npu_chunk_fwd_o",
            "npu_recurrent_gated_delta_rule", "npu_chunk_kda_fwd",
            "npu_chunk_kda_fwd_prepare", "npu_chunk_kda_fwd_finalize", "npu_solve_tril",
            "recompute_w_u_fwd", "npu_recurrent_kda", "ssm_state_gather",
            "ssm_state_scatter", "npu_hc_pre", "npu_hc_post", "hc_combine_norm",
            "npu_mhc_stream_mix", "npu_attn_res_fwd", "npu_embedding",
            "npu_engram_ngram_ids", "npu_rejection_sample", "npu_categorical_sampler",
            "tensor_pad", "_npu_paged_attention", "npu_scatter_pa_kv_cache", "npu_scatter_nd_update",
        ):
            setattr(npu_ns, kernel_name, self._record(kernel_name))

        for ascend_name in (
            "npu_dequant_situ_quant", "npu_sparse_flash_attention", "npu_sparse_flash_mla",
            "compressor_from_projected", "npu_lightning_indexer", "npu_pool_key_indexer",
            "npu_key_pool", "npu_indexer_quant_cache", "npu_kv_compress_epilog",
            "npu_generic_block_sparse_attention", "npu_ring_attention_update",
            "split_qkv_rmsnorm_rope",
        ):
            setattr(ascend_ns, ascend_name, self._record(ascend_name))

        t.npu = npu_ns
        t.ops = types.SimpleNamespace(
            npu=npu_ns,
            _C_ascend=ascend_ns,
            cann_ops_transformer=types.SimpleNamespace(),
        )
        return t

    def _make_dist(self) -> Any:
        dist = types.SimpleNamespace()
        dist.group = object()
        dist.is_initialized = lambda: True
        dist.get_world_size = lambda _g=None: 4
        dist.get_rank = lambda _g=None: 0
        dist.all_reduce = self._record("dist.all_reduce")
        dist.all_gather_into_tensor = self._record("dist.all_gather_into_tensor")
        dist.reduce_scatter_tensor = self._record("dist.reduce_scatter_tensor")
        dist.all_to_all_single = self._record("dist.all_to_all_single")
        dist.send = self._record("dist.send")
        dist.recv = self._record("dist.recv")
        dist.isend = "isend"
        dist.irecv = "irecv"
        dist.P2POp = lambda op, tensor, peer, group=None: (op, tensor, peer, group)
        dist.batch_isend_irecv = lambda p2p_ops: [types.SimpleNamespace(wait=lambda: None) for _ in p2p_ops]
        return dist

    def context(self, **extra: Any) -> dict[str, Any]:
        base = {
            "device": {"ordinal": 0},
            "torch_npu": self.torch.npu,
            "dist": self.dist,
            "groups": {"tp": self.dist.group},
        }
        base.update(extra)
        return base


def test_section_5_2_complete_101_builder_superset_is_registered():
    expected_norm = {
        "rms_norm", "add_rms_norm", "gemma_rms_norm", "layer_norm",
        "rms_norm_quant", "add_rms_norm_quant", "rms_norm_gated", "l2_norm",
        "dynamic_quant", "swiglu", "swiglu_oai", "swiglu_dynamic_quant",
        "dequant_swiglu_quant", "dequant_situ_quant", "situ_activation",
        "geglu", "gelu", "silu_mul", "sigmoid", "softmax",
    }
    expected_attn = {
        "fusion_attention", "fused_infer_attention", "incre_flash_attention",
        "absorbed_mla", "mla_prolog_v2", "mla_prolog_v3",
        "sparse_flash_attention", "mixed_quant_sparse_mla", "mla_kv_compressor",
        "lightning_indexer", "pool_key_indexer", "key_pool",
        "indexer_quant_cache", "kv_compress_epilog", "block_sparse_attention_c8",
        "dcp_lse_attention_merge", "scatter_pa_kv_cache", "scatter_index_cache",
        "rotary_embedding", "split_qkv_rmsnorm_rope", "indexer_topk",
    }
    expected_moe_comm = {
        "matmul", "quant_matmul", "grouped_matmul", "grouped_matmul_swiglu_quant",
        "moe_gating_topk", "moe_gating_topk_hash", "moe_init_routing",
        "moe_token_permute", "moe_token_unpermute", "histogram_v2",
        "mc2_dispatch", "mc2_combine", "mc2_dispatch_v3", "mc2_combine_v3",
        "megamoe_fused_mc2", "matmul_reduce_scatter", "all_gather_matmul",
        "all_reduce", "quantized_all_reduce", "all_gather", "reduce_scatter",
        "all_to_all_v", "p2p_send_recv", "muls_add",
    }
    expected_rec_mhc = {
        "causal_conv1d_fn", "causal_conv1d_update", "fused_gdn_gating",
        "chunk_gated_delta_rule", "chunk_gdn_fwd_prepare", "chunk_gdn_fwd_h",
        "chunk_gdn_fwd_o", "recurrent_gated_delta_rule",
        "recurrent_gdn_recover_ssm", "chunk_kda_fwd", "kda_chunk_products",
        "kda_chunk_output", "kda_triangular_solve", "kda_wy_transform",
        "fused_recurrent_kda", "ssm_state_gather", "ssm_state_scatter",
        "hc_pre", "hc_post", "hc_combine_norm", "mhc_stream_mix",
        "attn_res_prefix", "vocab_embedding", "ple_lookup", "engram_ngram_hash",
        "engram_uva_h2d", "gated_mul_add", "rejection_sampler",
        "categorical_sampler", "vector_add", "vector_mul_gate",
        "vector_pack_indices", "dtype_cast", "tensor_copy", "tensor_fill",
        "tensor_pad", "strided_gather",
    }
    assert expected_norm <= set(NORM_QUANT_BUILDERS)
    assert expected_attn <= set(ATTENTION_MLA_BUILDERS)
    assert expected_moe_comm <= set(MOE_COMM_BUILDERS)
    assert expected_rec_mhc <= set(RECURRENT_MHC_BUILDERS)
    all_102 = expected_norm | expected_attn | expected_moe_comm | expected_rec_mhc
    assert len(all_102) == 102
    assert all_102 <= set(ops.OPERATOR_BUILDERS)
    assert all_102 <= set(ops.CANONICAL_BUILDERS)


def test_every_canonical_builder_executes_against_fake_npu_backend():
    backend = FakeBackend()
    ctx = backend.context()
    for builder_name in sorted(ops.CANONICAL_BUILDERS):
        case = {
            "builder": builder_name,
            "dtype": "int8" if "quant_matmul" in builder_name else "bf16",
            "group": "tp",
            "group_size": 4,
            "nbytes": 4096,
            "shape": {
                "m": 16, "n": 32, "k": 64, "e": 4,
                "tokens": 8, "width": 128, "heads": 4, "kv_heads": 2,
                "head_dim": 128, "seq_len": 64, "top_k": 2,
            },
        }
        enqueue = ops.build_operator_enqueue(backend.torch, case, ctx)
        assert callable(enqueue), builder_name
        enqueue()


def test_zero_inspect_signature_across_bench_and_fabric_template():
    for path in sorted((REPO_ROOT / "mindie_profiler").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "signature":
                raise AssertionError(f"inspect.signature found in {path}")
    tmpl = (REPO_ROOT / "mindie_profiler" / "fabric_probe_script_template.py").read_text(encoding="utf-8")
    assert "inspect.signature" not in tmpl


def test_w4a8_routes_to_int4_weight_quant_and_casts_fractal_nz_29():
    backend = FakeBackend()
    ctx = backend.context()
    w4_case = {
        "builder": "quant_matmul",
        "dtype": "w4a8",
        "shape": {"m": 8, "n": 64, "k": 128},
    }
    fn = ops.build_operator_enqueue(backend.torch, w4_case, ctx)
    fn()
    dispatched = [name for name, _args, _kw in backend.calls]
    assert "npu_weight_quant_batchmatmul" in dispatched
    assert "npu_quant_matmul" not in dispatched
    # INT4 carrier packs eight nibbles per int32: (k, n // 8) = (128, 8) -> FRACTAL_NZ (29)
    assert ((128, 8), 29) in backend.format_casts
    _name, args, kwargs = backend.calls[-1]
    assert args[0].shape == (8, 128)
    assert args[1].shape == (128, 8)
    assert kwargs["antiquant_scale"].shape == (1, 64)
    assert kwargs["antiquant_offset"].shape == (1, 64)

    backend.calls.clear()
    backend.format_casts.clear()
    w8_case = {
        "builder": "quant_matmul",
        "dtype": "int8",
        "per_token_scale": True,
        "shape": {"m": 8, "n": 64, "k": 128},
    }
    ops.build_operator_enqueue(backend.torch, w8_case, ctx)()
    assert backend.calls[-1][0] == "npu_quant_matmul"
    assert ((128, 64), 29) in backend.format_casts


def test_absorbed_mla_uses_single_1152_byte_c_kv_and_ple_avoids_device_mismatch():
    backend = FakeBackend()
    ctx = backend.context()
    mla_case = {
        "builder": "absorbed_mla",
        "dtype": "bf16",
        "shape": {"tokens": 4, "heads": 16, "seq_len": 256, "block_size": 128},
    }
    ops.build_operator_enqueue(backend.torch, mla_case, ctx)()
    name, args, kwargs = backend.calls[-1]
    assert name == "npu_fused_infer_attention_score"
    # k_nope and v_nope share offset 0 and key_rope occupies the contiguous trailing plane of the single 1152 B/tok c_kv backing
    assert args[1].addr == args[2].addr
    assert kwargs["key_rope"].addr == args[1].addr + args[1].nbytes
    assert args[1].shape[-1] == 512 and kwargs["key_rope"].shape[-1] == 64

    for path in ("uva_gather", "pinned_h2d", "hbm"):
        ple_case = {
            "builder": "ple_lookup",
            "dtype": "bf16",
            "lookup_ids": [1, 9, 17, 25],
            "path": path,
            "shape": {"tokens": 4, "row_bytes": 320},
        }
        ops.build_operator_enqueue(backend.torch, ple_case, ctx)()

    uva_case = {"builder": "engram_uva_h2d", "dtype": "bf16", "local_shape": [1572864]}
    ops.build_operator_enqueue(backend.torch, uva_case, ctx)()


def test_cold_ring_rotates_inputs_weights_and_outputs_per_repeat():
    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(8 * MIB, slot_bytes=1 * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan)

    gemm_case = {
        "builder": "matmul",
        "dtype": "bf16",
        "cold_ring": True,
        "shape": {"m": 64, "n": 64, "k": 64},
    }
    cold_fn = ops.build_operator_enqueue(backend.torch, gemm_case, ctx)
    left_addrs, right_addrs, out_addrs = [], [], []
    backend.calls.clear()
    for _ in range(4):
        cold_fn()
        _name, (left, right, out), _kw = backend.calls[-1]
        left_addrs.append(left.addr)
        right_addrs.append(right.addr)
        out_addrs.append(out.addr)
    assert len(set(left_addrs)) == 4
    assert len(set(right_addrs)) == 4
    assert len(set(out_addrs)) == 4

    # Hot control reuses fixed slot 0 on every repeat
    hot_fn = ops.build_operator_enqueue(backend.torch, gemm_case, ctx, hot=True)
    backend.calls.clear()
    hot_addrs = []
    for _ in range(4):
        hot_fn()
        _name, (left, _right, _out), _kw = backend.calls[-1]
        hot_addrs.append(left.addr)
    assert len(set(hot_addrs)) == 1

    # Out-of-place norm builder rotates inputs & weights AND pre-warms output retention FIFO
    backend.calls.clear()
    norm_case = {
        "builder": "rms_norm",
        "dtype": "bf16",
        "cold_ring": True,
        "shape": {"tokens": 64, "width": 128},
    }
    norm_fn = ops.build_operator_enqueue(backend.torch, norm_case, ctx)
    assert backend.calls == []  # zero build-time warmups
    backend.calls.clear()
    norm_x_addrs, norm_w_addrs = [], []
    for _ in range(4):
        norm_fn()
        _name, (x_arg, w_arg, _eps), _kw = backend.calls[-1]
        norm_x_addrs.append(x_arg.addr)
        norm_w_addrs.append(w_arg.addr)
    assert len(set(norm_x_addrs)) == 4
    assert len(set(norm_w_addrs)) == 4


def test_fail_fast_unmodeled_operator_error_on_unknown_or_missing_kernels():
    backend = FakeBackend()
    ctx = backend.context()

    with pytest.raises(BenchUnmodeledOperatorError) as exc_info:
        ops.build_operator_enqueue(
            backend.torch,
            {"builder": "nonexistent_future_kernel", "model_id": "deepseek-v4", "layer_idx": 3},
            ctx,
        )
    err = exc_info.value
    assert isinstance(err, (ProfilerUsageError, RuntimeError, ValueError, UnmodeledCapabilityError))
    assert err.payload["schema"] == UNMODELED_HINT_SCHEMA
    assert err.payload["model_id"] == "deepseek-v4"
    assert err.payload["layer_idx"] == 3

    with pytest.raises(BenchUnmodeledOperatorError) as triple_exc:
        ops.resolve_builder_strict(
            "unknown_family", "unknown_recipe", "unknown_impl", ["bf16"], {},
            model_id="kimi-k3", layer_idx=7, local_shape=[4, 4096],
        )
    assert triple_exc.value.payload["schema"] == UNMODELED_HINT_SCHEMA
    assert triple_exc.value.payload["reason"] == "unmodeled_structure_triple"

    # Bare CPU torch without NPU surface and without allow_cpu_smoke MUST fail closed
    bare_torch = types.SimpleNamespace(
        bfloat16=2, zeros=lambda *s, **k: None, ones=lambda *s, **k: None, add=lambda a, b: None
    )
    with pytest.raises(BenchUnmodeledOperatorError) as surface_exc:
        ops.build_operator_enqueue(
            bare_torch,
            {"builder": "vector_add", "dtype": "bf16", "shape": {"tokens": 4, "width": 16}},
            {"device": {"ordinal": 0}},
        )
    assert surface_exc.value.payload["reason"] == "npu_runtime_surface_unavailable"

    # Missing fused kernels NEVER fall back to composite PyTorch ops
    empty_npu_torch = FakeBackend().torch
    empty_npu_torch.npu = types.SimpleNamespace(synchronize=lambda: None)
    empty_npu_torch.ops = types.SimpleNamespace(npu=empty_npu_torch.npu, _C_ascend=types.SimpleNamespace())
    for must_fail_builder in (
        "rms_norm", "add_rms_norm", "swiglu", "geglu", "moe_gating_topk",
        "moe_init_routing", "absorbed_mla", "causal_conv1d_update",
        "chunk_gated_delta_rule", "chunk_kda_fwd",
    ):
        with pytest.raises(BenchUnmodeledOperatorError) as k_exc:
            ops.build_operator_enqueue(
                empty_npu_torch,
                {"builder": must_fail_builder, "dtype": "bf16", "shape": {"tokens": 4, "width": 128, "heads": 4}},
                {"device": {"ordinal": 0}, "torch_npu": empty_npu_torch.npu},
            )
        assert k_exc.value.payload["schema"] == UNMODELED_HINT_SCHEMA
        assert k_exc.value.payload["builder"] == must_fail_builder


@pytest.mark.parametrize(
    "family,recipe,impl,dtypes,meta,expected_builder",
    [
        ("sp_matmul_collective", "sp_matmul_collective_pipeline", "", ["bf16"], {"sp_collective_kind": "all_gather"}, "all_gather_matmul"),
        ("sp_matmul_collective", "sp_matmul_collective_pipeline", "", ["bf16"], {}, "matmul_reduce_scatter"),
        ("mc2_protocol", "arch35_fullmesh_resource_phase", "MoeDistributeDispatchV3", ["bf16"], {}, "mc2_dispatch_v3"),
        ("alltoall", "expert_dispatch", "", ["bf16"], {"mc2_mode": 2}, "megamoe_fused_mc2"),
        ("allreduce", "ring_allreduce", "", ["int8"], {"quantized_all_reduce": True}, "quantized_all_reduce"),
        ("pp_p2p", "pipeline_send_recv", "", ["bf16"], {}, "p2p_send_recv"),
        ("add_rmsnorm_quant", "add_rmsnorm_quantize", "", ["bf16"], {}, "add_rms_norm_quant"),
        ("rmsnorm", "grouped_gemma_rmsnorm", "", ["bf16"], {}, "gemma_rms_norm"),
        ("swiglu", "grouped_swigluoai", "", ["bf16"], {}, "swiglu_oai"),
        ("quantize", "situ_quantize", "", ["int8"], {}, "dequant_situ_quant"),
        ("grouped_gemm", "balanced_grouped_gate_up", "", ["int8"], {"onchip_handoff_to": "down"}, "grouped_matmul_swiglu_quant"),
        ("attention", "sparse_flash_attention", "SparseFlashAttention", ["bf16"], {}, "sparse_flash_attention"),
        ("attention", "aclnn_mixed_quant_sparse_flash_mla", "aclnnMixedQuantSparseFlashMla", ["int8"], {}, "mixed_quant_sparse_mla"),
        ("attention_merge", "dcp_merge", "", ["bf16"], {}, "dcp_lse_attention_merge"),
        ("histogram", "expert_hist", "", ["int32"], {}, "histogram_v2"),
        ("topk", "moe_gating_topk", "aclnnMoeGatingTopKHash", ["fp32"], {}, "moe_gating_topk_hash"),
        ("rotary", "split_qkv_rmsnorm_mrope_fused", "", ["bf16"], {}, "split_qkv_rmsnorm_rope"),
        ("recurrent_scan", "vllm_ascend_recurrent_kda_arch35", "RecurrentKda", ["bf16"], {}, "fused_recurrent_kda"),
        ("recurrent_vector", "vllm_ascend_recurrent_gated_delta_rule_arch35_fp32_recover_ssm", "", ["bf16"], {}, "recurrent_gdn_recover_ssm"),
        ("mhc", "hc_pre_fused", "", ["bf16"], {}, "hc_pre"),
        ("mhc", "hc_post_fused", "", ["bf16"], {}, "hc_post"),
        ("mhc", "hc_combine_norm", "", ["bf16"], {}, "hc_combine_norm"),
        ("sampling", "top_p", "", ["fp32"], {}, "categorical_sampler"),
        ("elementwise", "moe_muls_add", "", ["bf16"], {}, "muls_add"),
        ("pad", "query_pad", "", ["bf16"], {}, "tensor_pad"),
    ],
)
def test_resolve_builder_strict_maps_1_to_1_to_registered_builders(
    family, recipe, impl, dtypes, meta, expected_builder
):
    builder_name, upstream_abi = ops.resolve_builder_strict(family, recipe, impl, dtypes, meta)
    assert builder_name == expected_builder
    assert builder_name in ops.OPERATOR_BUILDERS
    assert upstream_abi


def _assert_disjoint(operands):
    ranges = [(item.addr, item.addr + item.nbytes) for item in operands]
    for left in range(len(ranges)):
        for right in range(left + 1, len(ranges)):
            l0, l1 = ranges[left]
            r0, r1 = ranges[right]
            assert l1 <= r0 or r1 <= l0, (ranges, left, right)


@pytest.mark.parametrize("slot_mib", [8, 9])
@pytest.mark.parametrize(
    "builder,shape",
    [
        ("vector_add", {"tokens": 64, "width": 512}),
        ("matmul", {"m": 64, "n": 64, "k": 64}),
    ],
)
def test_cold_and_hot_ring_operands_never_alias(slot_mib, builder, shape):
    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(96 * MIB, slot_bytes=slot_mib * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan)
    case = {"builder": builder, "dtype": "bf16", "cold_ring": True, "shape": shape}
    cold_fn = ops.build_operator_enqueue(backend.torch, case, ctx)
    cold_left = []
    for _ in range(6):
        backend.calls.clear()
        cold_fn()
        operands = backend.calls[-1][1][:3]
        assert len(operands) == 3
        _assert_disjoint(operands)
        cold_left.append(operands[0].addr)
    assert len(set(cold_left)) == len(cold_left)

    hot_fn = ops.build_operator_enqueue(backend.torch, case, ctx, hot=True)
    hot_left = []
    for _ in range(6):
        backend.calls.clear()
        hot_fn()
        operands = backend.calls[-1][1][:3]
        assert len(operands) == 3
        _assert_disjoint(operands)
        hot_left.append(operands[0].addr)
    assert len(set(hot_left)) == 1


def test_grouped_matmul_hot_keeps_one_distinct_weight_per_expert():
    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(96 * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan)
    ctx["_actual_shape"] = {}
    case = {
        "builder": "grouped_matmul", "dtype": "bf16", "cold_ring": True,
        "shape": {"m": 8, "n": 32, "k": 16, "e": 4},
        "group_list": [2, 2, 2, 2],
    }
    ops.build_operator_enqueue(backend.torch, case, ctx, hot=True)()
    _name, args, _kwargs = backend.calls[-1]
    weights = args[1]
    assert len(weights) == 4
    assert len({item.addr for item in weights}) == 4
    assert ctx["_actual_shape"] == {
        "m": 8, "n": 32, "k": 16, "e": 4, "matrix_groups": 4,
        "dtype": "bf16", "weight_dtype": "bf16",
    }


@pytest.mark.parametrize(
    "case,positional,kwargs",
    [
        ({"builder": "rms_norm_quant", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8}}, 5, {"epsilon"}),
        ({"builder": "add_rms_norm_quant", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8}}, 5, {"epsilon"}),
        ({"builder": "mla_prolog_v2", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8, "heads": 2}}, 0,
         {"token_x", "weight_dq", "weight_uq_qr", "weight_uk", "weight_dkv_kr",
          "rmsnorm_gamma_cq", "rmsnorm_gamma_ckv", "rope_sin", "rope_cos",
          "cache_index", "kv_cache", "kr_cache",
          "rmsnorm_epsilon_cq", "rmsnorm_epsilon_ckv", "cache_mode"}),
        ({"builder": "mla_prolog_v3", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8, "heads": 2}}, 0,
         {"token_x", "weight_dq", "weight_uq_qr", "weight_uk", "weight_dkv_kr",
          "rmsnorm_gamma_cq", "rmsnorm_gamma_ckv", "rope_sin", "rope_cos",
          "cache_index", "kv_cache", "kr_cache",
          "rmsnorm_epsilon_cq", "rmsnorm_epsilon_ckv", "cache_mode"}),
        ({"builder": "lightning_indexer", "dtype": "bf16",
          "shape": {"tokens": 4, "heads": 2, "head_dim": 8, "seq_len": 16}}, 3,
         {"sparse_count"}),
        ({"builder": "sparse_flash_attention", "dtype": "bf16",
          "shape": {"tokens": 4, "heads": 2, "kv_heads": 1, "head_dim": 8,
                    "seq_len": 16}}, 5,
         {"layout_query", "layout_kv", "actual_seq_lengths_query", "actual_seq_lengths_kv"}),
        ({"builder": "dcp_lse_attention_merge", "dtype": "bf16",
          "shape": {"tokens": 4, "heads": 2, "head_dim": 8}}, 6, set()),
        ({"builder": "moe_init_routing", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8, "e": 4, "top_k": 2}}, 2,
         {"active_num", "expert_num", "quant_mode"}),
        ({"builder": "grouped_matmul_swiglu_quant", "dtype": "int8",
          "shape": {"m": 8, "n": 16, "k": 8, "e": 4}}, 4, {"group_list"}),
        ({"builder": "mc2_dispatch", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8, "e": 4, "top_k": 2}}, 0,
         {"expert_ids", "group_ep", "moe_expert_num"}),
        ({"builder": "mc2_combine", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8, "e": 4, "top_k": 2}}, 0,
         {"expand_x", "assist_info_for_combine", "ep_send_counts"}),
        ({"builder": "chunk_gated_delta_rule", "dtype": "bf16",
          "shape": {"tokens": 4, "heads": 2, "head_dim": 8}}, 3,
         {"g", "beta", "initial_state", "actual_seq_lengths", "scale"}),
        ({"builder": "recurrent_gated_delta_rule", "dtype": "bf16",
          "shape": {"tokens": 4, "heads": 2, "head_dim": 8}}, 4,
         {"g", "beta", "actual_seq_lengths"}),
        ({"builder": "hc_post", "dtype": "bf16",
          "shape": {"tokens": 4, "width": 8, "streams": 2}}, 4, set()),
    ],
)
def test_strict_dispatcher_schemas_for_previously_failing_builders(case, positional, kwargs):
    backend = FakeBackend()
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    _name, args, call_kwargs = backend.calls[-1]
    assert len(args) == positional
    assert kwargs <= set(call_kwargs)


def test_resolve_builder_honors_explicit_registered_builder_and_strict_sentinel_fallback():
    # [P-P0-1]: Exported node carrying explicit registered builder (e.g. grouped_matmul_swiglu_quant)
    # without serialized onchip_handoff_to metadata MUST NOT be downgraded back to grouped_matmul!
    assert ops.resolve_builder({
        "family": "grouped_gemm", "recipe": "grouped_matmul",
        "builder": "grouped_matmul_swiglu_quant",
    }) == "grouped_matmul_swiglu_quant"
    assert ops.resolve_builder({
        "family": "layernorm", "recipe": "hidden_norm", "builder": "unmapped_catalog_op",
    }) == "layer_norm"
    assert ops.resolve_builder({
        "family": "rmsnorm_quant", "recipe": "hidden_quant",
    }) == "rms_norm_quant"
    with pytest.raises(BenchUnmodeledOperatorError):
        ops.resolve_builder({
            "family": "mhc", "recipe": "hc_sinkhorn",
            "implementation": "HcSinkhorn", "builder": "unmapped_catalog_op",
        })
    with pytest.raises(BenchUnmodeledOperatorError):
        ops.resolve_builder({
            "family": "gemm", "recipe": "future", "implementation": "Imaginary",
            "dtypes": ["bf16"],
        })
    assert ops.resolve_builder({"family": "alltoall", "recipe": "all_to_all"}) == "all_to_all"
    assert ops.resolve_builder({
        "family": "attention", "recipe": "fused_infer_attention",
    }) == "fused_infer_attention"
    assert ops.resolve_builder({
        "family": "recurrent_scan", "recipe": "chunk_kda_fwd",
    }) == "fused_recurrent_kda"
    assert len(ops.CANONICAL_BUILDERS) == 103
    assert "graph_boundary" not in ops.CANONICAL_BUILDERS
    assert "all_to_all" in ops.OPERATOR_BUILDERS
    assert "graph_boundary" not in ops.RING_BUILDERS
    sentinel = object()
    boundary = ops.build_operator_enqueue(
        FakeBackend().torch,
        {"family": "barrier", "recipe": "pipeline"},
        {"_node_inputs": [sentinel]},
    )
    assert boundary() is sentinel


def test_resolve_l2_bytes_prefers_explicit_then_device_then_sku():
    assert resolve_l2_bytes(4096) == 4096
    props = types.SimpleNamespace(L2_cache_size=8192)
    torch_npu = types.SimpleNamespace(get_device_properties=lambda ordinal: props)
    assert resolve_l2_bytes(None, sku="DAV_2201", torch_npu=torch_npu) == 8192
    assert resolve_l2_bytes(None, sku="DAV_2201") == 96 * MIB
    assert resolve_l2_bytes(None, sku="unknown_sku") is None


def test_matmul_nk_layout_transposes_and_reads_dynamic_upstream_each_call():
    backend = FakeBackend()
    ctx = backend.context()
    case = {
        "builder": "matmul", "dtype": "bf16", "layout": "NK",
        "shape": {"m": 4, "n": 8, "k": 16},
    }
    ops.build_operator_enqueue(backend.torch, case, ctx)()
    _name, args, _kwargs = backend.calls[-1]
    assert args[0].shape == (4, 16)
    assert args[1].shape == (16, 8)

    upstream = FakeTensor((4, 16), dtype=2, device="npu:0")
    dynamic_ctx = backend.context(_node_inputs=[upstream])
    dynamic = ops.build_operator_enqueue(
        backend.torch, {**case, "layout": "KN"}, dynamic_ctx
    )
    dynamic()
    assert backend.calls[-1][1][0].addr == upstream.addr


def test_ple_rotating_vectors_and_index_add_contention_are_distinct(monkeypatch):
    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(96 * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan)
    ple = {
        "builder": "ple_lookup", "dtype": "bf16", "cold_ring": True,
        "lookup_ids": [1, 9, 17, 25], "slot_map": {"1": 0, "9": 1, "17": 2, "25": 3},
        "remap_span": 4, "path": "pinned_h2d",
        "shape": {"tokens": 4, "row_bytes": 320},
    }
    backend.tensor_values.clear()
    ops.build_operator_enqueue(backend.torch, {**ple, "reuse": "rotating"}, ctx)()
    rotating = list(backend.tensor_values)
    assert len(set(rotating)) > 1
    backend.tensor_values.clear()
    ops.build_operator_enqueue(backend.torch, {**ple, "reuse": "repeated"}, ctx)()
    assert len(set(backend.tensor_values)) == 1

    index_case = {
        "builder": "index_add", "dtype": "bf16", "indices_per_cacheline": 4,
        "shape": {"rows": 256, "tokens": 8, "width": 4},
    }
    from mindie_profiler.bench import operators_recurrent_mhc as recurrent
    zero_calls: list[tuple] = []
    real_zeros = recurrent.zeros
    monkeypatch.setattr(recurrent, "zeros", lambda t, *d, **k: (
        zero_calls.append((d, k.get("device"))), real_zeros(t, *d, **k))[1])
    FakeTensor.index_add_calls.clear()
    ops.build_operator_enqueue(
        backend.torch, {**index_case, "contention": "shared_cacheline"},
        backend.context())()
    shared_index = FakeTensor.index_add_calls[-1][1]
    assert shared_index.device == "npu:0"
    assert ((8,), "npu:0") in zero_calls  # all RMWs hit row 0
    FakeTensor.index_add_calls.clear()
    ops.build_operator_enqueue(
        backend.torch, {**index_case, "contention": "disjoint_cacheline"},
        backend.context())()
    disjoint = backend.tensor_values[-1]
    assert len(set(disjoint)) == len(disjoint)
    offsets = sorted(item * 4 * 2 for item in disjoint)
    assert min(right - left for left, right in zip(offsets, offsets[1:])) >= 128


def test_lightning_indexer_matches_cann_positional_and_npu_keyword_schemas():
    backend = FakeBackend()
    case = {"builder": "lightning_indexer", "dtype": "bf16",
            "shape": {"tokens": 4, "heads": 2, "head_dim": 8, "seq_len": 16}}
    ctx = {**backend.context(), "_actual_shape": {}}
    ops.build_operator_enqueue(backend.torch, case, ctx)()
    name, args, kwargs = backend.calls[-1]
    assert name == "npu_lightning_indexer"
    assert len(args) == 3 and kwargs["sparse_count"] == 16
    assert ctx["_actual_shape"]["query_dtype"] == ctx["_actual_shape"]["cache_dtype"] == "bf16"

    ops.build_operator_enqueue(backend.torch, {
        "builder": "lightning_indexer", "dtype": "bf16",
        "shape": {"tokens": 1, "heads": 8, "head_dim": 128, "seq_len": 409600},
    }, backend.context())()
    assert backend.calls[-1][2]["sparse_count"] == 2048

    # Explicit top_k / sparse_count above dsa_index_topk must be forwarded un-clamped for ABI rejection probes.
    for key, probe_val in (("top_k", 2049), ("sparse_count", 8193)):
        ctx = {**backend.context(), "_actual_shape": {}}
        ops.build_operator_enqueue(backend.torch, {
            "builder": "lightning_indexer", "dtype": "bf16",
            "shape": {"tokens": 1, "heads": 8, "head_dim": 128, "seq_len": 16384, key: probe_val},
        }, ctx)()
        assert backend.calls[-1][2]["sparse_count"] == probe_val
        assert ctx["_actual_shape"]["top_k"] == probe_val

    backend = FakeBackend()
    del backend.torch.ops._C_ascend.npu_lightning_indexer
    backend.torch.ops.cann_ops_transformer.lightning_indexer = (
        lambda *call_args, **call_kwargs: backend.calls.append(
            ("lightning_indexer", call_args, call_kwargs)) or call_args[0])
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    name, args, kwargs = backend.calls[-1]
    assert name == "lightning_indexer"
    assert len(args) == 4 and args[3] == 16 and kwargs == {}


@pytest.mark.parametrize(("shape_layout", "case_layout"), [
    ({"input_layout": "BNSD", "query_layout": "TND"}, "TND"),
    ({"query_layout": "BNSD"}, "TND"),
    ({}, "BNSD"),
])
def test_absorbed_mla_uses_bnsd_for_both_query_planes(shape_layout, case_layout):
    backend = FakeBackend()
    ctx = {**backend.context(), "_actual_shape": {}}
    case = {"builder": "absorbed_mla", "dtype": "bf16", "layout": case_layout,
            "shape": {"tokens": 5, "sequences": 2, "heads": 8, "seq_len": 256, **shape_layout}}
    ops.build_operator_enqueue(backend.torch, case, ctx)()
    _, args, kwargs = backend.calls[-1]
    assert args[0].shape == (2, 8, 3, 512)
    assert kwargs["query_rope"].shape == (2, 8, 3, 64)
    assert kwargs["actual_seq_lengths"] == [3, 2]
    assert kwargs["input_layout"] == "BNSD"
    assert ctx["_actual_shape"]["input_layout"] == ctx["_actual_shape"]["query_layout"] == "BNSD"


def test_sparse_flash_attention_passes_tnd_3d_indices_and_device_lengths():
    backend = FakeBackend()
    case = {"builder": "sparse_flash_attention", "dtype": "bf16",
            "shape": {"tokens": 4, "heads": 2, "kv_heads": 1, "head_dim": 8,
                      "seq_len": 16}}
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    _name, args, kwargs = backend.calls[-1]
    assert kwargs["layout_query"] == "TND" and kwargs["layout_kv"] == "TND"
    assert kwargs["attention_mode"] == 2
    assert args[3].shape == (4, 1, 2048) and args[3].dtype == 4
    assert args[4] == pytest.approx(8 ** -0.5)
    for field, value in (("actual_seq_lengths_query", 4),
                         ("actual_seq_lengths_kv", 16)):
        tensor = kwargs[field]
        assert isinstance(tensor, FakeTensor)
        assert tensor.dtype == 4 and tensor.device == "npu:0"
        assert tensor.shape == (1,) and (value,) in backend.tensor_values

    # seq_len = 512 < dsa_index_topk (2048): 512 valid [0..511] + 1536 trailing -1 sentinels
    backend.tensor_values.clear()
    ops.build_operator_enqueue(backend.torch, {
        "builder": "sparse_flash_attention", "dtype": "bf16",
        "shape": {"tokens": 1, "heads": 8, "kv_heads": 1, "head_dim": 512,
                  "qk_rope_head_dim": 64, "seq_len": 512},
    }, backend.context())()
    _name, s512_args, s512_kw = backend.calls[-1]
    assert s512_args[3].shape == (1, 1, 2048)
    idx_512 = backend.tensor_values[0]
    assert len(idx_512) == 2048
    assert idx_512[:512] == tuple(range(512))
    assert idx_512[512:] == (-1,) * (2048 - 512)
    assert s512_kw["query_rope"].shape == (1, 8, 64)
    assert s512_kw["key_rope"].shape == (512, 1, 64)

    # seq_len = 409600 >= dsa_index_topk (2048): 2048 distinct strided indices across [0..409599], zero -1s
    backend.tensor_values.clear()
    ops.build_operator_enqueue(backend.torch, {
        "builder": "sparse_flash_attention", "dtype": "bf16",
        "shape": {"tokens": 1, "heads": 8, "kv_heads": 1, "head_dim": 512,
                  "qk_rope_head_dim": 64, "seq_len": 409600},
    }, backend.context())()
    _name, s400k_args, _s400k_kw = backend.calls[-1]
    assert s400k_args[3].shape == (1, 1, 2048)
    idx_400k = backend.tensor_values[0]
    assert len(idx_400k) == 2048
    assert -1 not in idx_400k
    assert len(set(idx_400k)) == 2048
    assert idx_400k[0] == 0 and idx_400k[1] == 200 and idx_400k[-1] == 2047 * 200


def test_gated_delta_actual_seq_lengths_are_device_int32_tensors():
    backend = FakeBackend()
    chunk_case = {"builder": "chunk_gated_delta_rule", "dtype": "bf16",
                  "shape": {"tokens": 4, "heads": 2, "head_dim": 8}}
    ops.build_operator_enqueue(backend.torch, chunk_case, backend.context())()
    lengths = backend.calls[-1][2]["actual_seq_lengths"]
    assert isinstance(lengths, FakeTensor)
    assert lengths.dtype == 4 and lengths.device == "npu:0" and lengths.shape == (1,)
    assert (4,) in backend.tensor_values

    for builder in ("recurrent_gated_delta_rule", "recurrent_gdn_recover_ssm"):
        backend.tensor_values.clear()
        case = {"builder": builder, "dtype": "bf16",
                "shape": {"tokens": 4, "heads": 2, "head_dim": 8}}
        ops.build_operator_enqueue(backend.torch, case, backend.context())()
        _name, args, kw = backend.calls[-1]
        rec_lengths, state_idx = kw["actual_seq_lengths"], kw["ssm_state_indices"]
        assert isinstance(rec_lengths, FakeTensor) and rec_lengths.dtype == 4 and rec_lengths.shape == (4,)
        assert isinstance(state_idx, FakeTensor) and state_idx.dtype == 4 and state_idx.shape == (4,)
        assert args[3].shape == (4, 2, 8, 8)
        assert (1, 1, 1, 1) in backend.tensor_values
        assert (0, 1, 2, 3) in backend.tensor_values


def test_w4a8_int4_pack_runs_once_on_the_unpacked_weight():
    backend = FakeBackend()
    packed_shapes: list[tuple[int, ...]] = []

    def pack(item):
        packed_shapes.append(item.shape)
        return FakeTensor((item.shape[0], item.shape[1] // 8), dtype=item.dtype,
                          device=item.device, addr=item.addr)

    ctx = backend.context(extra_ops={"npu_convert_weight_to_int4pack": pack})
    case = {"builder": "quant_matmul", "dtype": "w4a8",
            "shape": {"m": 8, "n": 64, "k": 128}}
    ops.build_operator_enqueue(backend.torch, case, ctx)()
    assert packed_shapes == [(128, 64)]
    assert backend.calls[-1][1][1].shape == (128, 8)

    backend = FakeBackend()
    packed_shapes.clear()
    ctx = backend.context(extra_ops={"npu_convert_weight_to_int4pack": pack})
    nk_case = {**case, "layout": "NK"}
    ops.build_operator_enqueue(backend.torch, nk_case, ctx)()
    assert packed_shapes == [(128, 64)]
    assert backend.calls[-1][1][1].shape == (128, 8)


def test_int8_quant_matmul_nk_layout_transposes_without_nz_cast():
    backend = FakeBackend()
    case = {"builder": "quant_matmul", "dtype": "int8", "layout": "NK",
            "shape": {"m": 8, "n": 64, "k": 128}}
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    _name, args, _kwargs = backend.calls[-1]
    assert args[1].shape == (128, 64)
    assert backend.format_casts == []


def test_dynamic_rms_norm_quant_uses_two_positional_args():
    backend = FakeBackend()
    backend.torch.npu.npu_rms_norm_dynamic_quant = backend._record(
        "npu_rms_norm_dynamic_quant")
    case = {"builder": "rms_norm_quant", "dtype": "bf16",
            "shape": {"tokens": 4, "width": 8}}
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    name, args, kwargs = backend.calls[-1]
    assert name == "npu_rms_norm_dynamic_quant"
    assert len(args) == 2 and set(kwargs) == {"epsilon"}


def test_paged_fia_block_table_has_distinct_sequential_pages():
    backend = FakeBackend()
    case = {"builder": "fused_infer_attention", "dtype": "bf16", "paged": True,
            "shape": {"tokens": 4, "heads": 2, "kv_heads": 1, "head_dim": 8,
                      "seq_len": 256, "block_size": 16}}
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    block_table = backend.calls[-1][2]["block_table"]
    assert block_table.shape == (1, 16)
    assert backend.tensor_values[-1] == tuple(range(16))


def test_incre_flash_attention_prefers_native_and_falls_back_to_scale():
    backend = FakeBackend()
    case = {"builder": "incre_flash_attention", "dtype": "bf16",
            "shape": {"tokens": 4, "heads": 2, "kv_heads": 1, "head_dim": 8,
                      "seq_len": 16}}
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    assert backend.calls[-1][0] == "npu_incre_flash_attention"

    backend = FakeBackend()
    del backend.torch.npu.npu_incre_flash_attention
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    name, _args, kwargs = backend.calls[-1]
    assert name == "npu_fused_infer_attention_score"
    assert kwargs["scale"] == pytest.approx(8 ** -0.5)
    assert "scale_value" not in kwargs


def test_uva_gather_executes_a_device_index_select_in_the_timed_window():
    backend = FakeBackend()
    case = {"builder": "ple_lookup", "dtype": "bf16", "path": "uva_gather",
            "lookup_ids": [1, 2, 3, 4], "shape": {"tokens": 4, "row_bytes": 64}}
    ops.build_operator_enqueue(backend.torch, case, backend.context())()
    selects = [call for call in backend.calls if call[0] == "index_select"]
    assert selects
    _name, (_src, index, _target), _kwargs = selects[-1]
    assert index.device == "npu:0"


def test_tiny_cold_ring_case_reports_honest_touched_coverage():
    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(96 * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan)
    case = {"builder": "matmul", "dtype": "bf16", "cold_ring": True,
            "shape": {"m": 64, "n": 64, "k": 64}}
    ops.OPERATOR_BUILDERS["matmul"](backend.torch, case, ctx)()
    coverage = ctx["_cold_coverage"]
    assert coverage["qualified"] is False
    assert coverage["touched_bytes"] == 36 * 64 * 64 * 3 * 2
    assert coverage["required_bytes"] == ring.plan["required_bytes"]


def test_unified_byte_ledger_rejects_ring_fallbacks_and_hot_over_cap():
    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(96 * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan,
                          budget={"cap_bytes": 900 * MIB})
    ctx["_byte_ledger"] = {"peak_bytes": ring.allocated_bytes}
    case = {"builder": "matmul", "dtype": "bf16", "cold_ring": True,
            "shape": {"m": 16, "n": 8192, "k": 16384}}
    cold = ops.build_operator_enqueue(backend.torch, case, ctx)
    cold()
    assert ctx["_byte_ledger"]["peak_bytes"] == (
        ring.allocated_bytes + 2 * (16 * 16384 + 16384 * 8192 + 16 * 8192) * 2)
    with pytest.raises(ProfilerUsageError, match="bench_vram_budget_exceeded"):
        ops.build_operator_enqueue(backend.torch, case, ctx, hot=True)


def test_cold_ring_cached_builder_consumes_updated_live_upstream():
    from mindie_profiler.bench.subgraph_runtime import OperatorExecutor

    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(96 * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan)
    executor = OperatorExecutor(backend.torch, ctx)
    node = {"node_id": "n1", "kind": "operator", "builder": "matmul",
            "dtype": "bf16", "cold_ring": True,
            "shape": {"m": 4, "n": 8, "k": 16}}
    first = FakeTensor((4, 16), dtype=2, device="npu:0")
    second = FakeTensor((4, 16), dtype=2, device="npu:0")
    executor.launch(node, [first])
    assert backend.calls[-1][1][0].addr == first.addr
    executor.launch(node, [second])
    assert backend.calls[-1][1][0].addr == second.addr
    assert len(executor.built) == 1


def test_case_wide_hot_arena_advances_across_nodes():
    from mindie_profiler.bench.subgraph_runtime import OperatorExecutor

    backend = FakeBackend()
    ring = timing.ColdRing(
        backend.torch, timing.cold_ring_plan(96 * MIB), ordinal=0
    ).allocate()
    ctx = backend.context(ring=ring, ring_plan=ring.plan)
    executor = OperatorExecutor(backend.torch, ctx)
    node = {"node_id": "n1", "kind": "operator", "builder": "matmul",
            "dtype": "bf16", "cold_ring": True,
            "shape": {"m": 4, "n": 8, "k": 16}}
    executor.launch(node, hot=True)
    first_out = backend.calls[-1][1][2]
    executor.launch({**node, "node_id": "n2"}, hot=True)
    second_out = backend.calls[-1][1][2]
    assert second_out.addr != first_out.addr
    assert ctx["_hot_arena"]["sub_offset"] > 0


def test_mc2_builder_uses_group_rank_world_and_hccl_comm_name():
    backend = FakeBackend()

    class CommBackend:
        def get_hccl_comm_name(self, rank):
            return f"hccl-{rank}"

    class Group:
        def _get_backend(self):
            return CommBackend()

    class Dist:
        def get_rank(self, group):
            assert isinstance(group, Group)
            return 9

        def get_world_size(self, group):
            assert isinstance(group, Group)
            return 64

    group, dist = Group(), Dist()
    ctx = backend.context(groups={"ep": group}, dist=dist)
    case = {"builder": "mc2_dispatch", "dtype": "bf16",
            "shape": {"tokens": 4, "width": 8, "e": 4, "top_k": 2}}
    ops.build_operator_enqueue(backend.torch, case, ctx)()
    _name, _args, kwargs = backend.calls[-1]
    assert kwargs["ep_rank_id"] == 9
    assert kwargs["ep_world_size"] == 64
    assert kwargs["group_ep"] == "hccl-9"


def test_wrap_ring_step_has_zero_build_time_execution():
    from mindie_profiler.bench.operators_common import wrap_ring_step

    calls: list[int] = []
    step = wrap_ring_step(4, lambda slot: calls.append(slot), retain_outputs=True)
    assert calls == []
    step()
    step()
    assert calls == [0, 1]


class _DtypeTag(int):
    def __new__(cls, byte_width: int, tag: str) -> "_DtypeTag":
        obj = super().__new__(cls, byte_width)
        obj.tag = tag
        return obj

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _DtypeTag):
            return self.tag == other.tag
        return super().__eq__(other)

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((int(self), self.tag))


def test_cann_93_operator_builder_abi_contracts():
    # [P-P0-1]: Exported INT8 grouped_matmul with output_dtype="int8" recovers BF16 scale+output (or FP32+FP16)
    backend = FakeBackend()
    backend.torch.bfloat16 = _DtypeTag(2, "bfloat16")
    backend.torch.float16 = _DtypeTag(2, "float16")
    backend.torch.float32 = _DtypeTag(4, "float32")
    backend.torch.int32 = _DtypeTag(4, "int32")
    backend.torch.int64 = _DtypeTag(8, "int64")
    backend.torch.int8 = _DtypeTag(1, "int8")
    orig_alloc = backend.torch.zeros
    backend.torch.zeros = backend.torch.ones = backend.torch.randn = backend.torch.empty = (
        lambda *dims, dtype=backend.torch.bfloat16, device="npu:0", pin_memory=False: FakeTensor(
            tuple(int(x) for x in (dims[0] if len(dims) == 1 and isinstance(dims[0], (list, tuple)) else dims)),
            dtype=dtype, device="cpu" if pin_memory else str(device or "npu:0"), pinned=pin_memory,
        )
    )
    _ = orig_alloc
    ctx = backend.context()
    gmm_int8 = {
        "builder": "grouped_matmul", "dtype": "int8", "output_dtype": "int8",
        "shape": {"m": 8, "n": 32, "k": 16, "e": 4}, "group_list": [2, 2, 2, 2],
    }
    ops.build_operator_enqueue(backend.torch, gmm_int8, ctx)()
    _name, _args, kw = backend.calls[-1]
    assert kw["output_dtype"] == backend.torch.bfloat16
    assert kw["output_dtype"] != backend.torch.float16
    assert len(kw["scale"]) == 4 and all(t.dtype == backend.torch.bfloat16 for t in kw["scale"])
    assert len(kw["per_token_scale"]) == 1 and kw["per_token_scale"][0].dtype == backend.torch.float32

    ops.build_operator_enqueue(backend.torch, {**gmm_int8, "output_dtype": "fp16"}, ctx)()
    _name, _args, kw_fp16 = backend.calls[-1]
    assert kw_fp16["output_dtype"] == backend.torch.float16
    assert all(t.dtype == backend.torch.float32 for t in kw_fp16["scale"])

    # E=1 grouped_matmul passes rank-3 [1, K, N] weight and [1, N] scale
    ops.build_operator_enqueue(backend.torch, {
        "builder": "grouped_matmul", "dtype": "int8", "output_dtype": "int8",
        "shape": {"m": 8, "n": 32, "k": 16, "e": 1}, "group_list": [8],
    }, ctx)()
    _name, e1_args, e1_kw = backend.calls[-1]
    assert e1_args[1][0].shape == (1, 16, 32)
    assert e1_kw["scale"][0].shape == (1, 32)

    # [P-P0-1b]: grouped_matmul_swiglu_quant preserves exported routing counts -> cumulative endpoints
    backend.tensor_values.clear()
    swiglu_q = {
        "builder": "grouped_matmul_swiglu_quant", "dtype": "int8",
        "shape": {"m": 12, "n": 32, "k": 16, "e": 48},
        "group_list": [1] * 12 + [0] * 36, "group_list_type": 1,
    }
    ops.build_operator_enqueue(backend.torch, swiglu_q, ctx)()
    expected_cum = tuple(list(range(1, 13)) + [12] * 36)
    assert expected_cum in backend.tensor_values

    # Paged FIA TND uses BnNBsD (blocks, kv_heads, block_size, head_dim)
    ops.build_operator_enqueue(backend.torch, {
        "builder": "fused_infer_attention", "dtype": "bf16", "paged": True,
        "shape": {"tokens": 1, "heads": 8, "kv_heads": 1, "head_dim": 128, "seq_len": 256, "block_size": 128},
    }, ctx)()
    assert backend.calls[-1][1][1].shape == (2, 1, 128, 128)

    # [P-P0-3a]: absorbed_mla allocates disjoint pages across requests (8 * 17 = 136) and contiguous planes
    backend.tensor_values.clear()
    mla_case = {
        "builder": "absorbed_mla", "dtype": "bf16",
        "shape": {"tokens": 8, "heads": 8, "seq_len": 2049, "block_size": 128},
    }
    ops.build_operator_enqueue(backend.torch, mla_case, ctx)()
    _name, mla_args, mla_kw = backend.calls[-1]
    assert mla_args[1].shape == (8 * 17, 128, 512)
    assert mla_kw["key_rope"].shape == (8 * 17, 128, 64)
    assert mla_kw["block_table"].shape == (8, 17)
    assert len(set(backend.tensor_values[-1])) == 136
    assert mla_kw["actual_seq_lengths"] == list(range(1, 9))
    assert mla_kw["actual_seq_lengths_kv"] == [2049] * 8

    # DeepSeek prefill MLA inherits parent _case_meta phase="prefill" -> 1 sequence, [1, 1] block_table
    pf_ctx = {**ctx, "_case_meta": {"phase": "prefill"}}
    ops.build_operator_enqueue(backend.torch, {
        "builder": "absorbed_mla", "dtype": "bf16",
        "shape": {"tokens": 128, "heads": 8, "seq_len": 128, "block_size": 128},
    }, pf_ctx)()
    assert backend.calls[-1][2]["block_table"].shape == (1, 1)
    assert backend.calls[-1][2]["actual_seq_lengths"] == [128]

    # [P-P0-3b]: recurrent_gated_delta_rule honors FP32 recipe state, ssm_state_indices & BlockNum >= T
    rec_case = {
        "builder": "recurrent_gated_delta_rule", "dtype": "bf16",
        "implementation": "ascend_recurrent_gdn_arch22_fp32",
        "shape": {"tokens": 8, "heads": 2, "head_dim": 64},
    }
    ops.build_operator_enqueue(backend.torch, rec_case, ctx)()
    _name, rec_args, rec_kw = backend.calls[-1]
    assert rec_args[3].shape == (8, 2, 64, 64) and rec_args[3].dtype == backend.torch.float32
    assert rec_kw["ssm_state_indices"].shape == (8,)
    assert rec_kw["actual_seq_lengths"].shape == (8,)
    assert rec_kw["scale"] == pytest.approx(0.125)

    # [P-P0-3c]: dcp_lse_attention_merge honors width=512, input_softmax_layout="TND", actual_seq_qlen=[0, T]
    backend.tensor_values.clear()
    dcp_case = {
        "builder": "dcp_lse_attention_merge", "dtype": "bf16",
        "shape": {"tokens": 8, "heads": 1, "width": 512},
    }
    ops.build_operator_enqueue(backend.torch, dcp_case, ctx)()
    _name, dcp_args, dcp_kw = backend.calls[-1]
    assert dcp_args[0].shape == (8, 1, 512)
    assert dcp_kw["input_layout"] == "TND" and dcp_kw["input_softmax_layout"] == "TND"
    assert (0, 8) in backend.tensor_values

    # [P-P0-3d]: fused_recurrent_kda sets initial_state+inplace_final_state=False on vllm_ascend ONLY
    kda_calls: list[tuple[Any, dict[str, Any]]] = []
    triton_kda_mod = types.SimpleNamespace(
        fused_recurrent_kda=lambda *a, **k: (kda_calls.append((a, k)), a[0])[1]
    )
    no_npu_kda = backend.context()
    delattr(no_npu_kda["torch_npu"], "npu_recurrent_kda")
    no_npu_kda["extra_modules"] = {"vllm_ascend.ops.triton.kda": triton_kda_mod}
    kda_case = {
        "builder": "fused_recurrent_kda", "dtype": "bf16",
        "shape": {"tokens": 4, "heads": 2, "head_dim": 64},
    }
    ops.build_operator_enqueue(backend.torch, kda_case, no_npu_kda)()
    assert kda_calls[0][1]["initial_state"].shape == (1, 2, 64, 64)
    assert kda_calls[0][1]["inplace_final_state"] is False

    fla_calls: list[dict[str, Any]] = []
    fla_mod = types.SimpleNamespace(
        fused_recurrent_kda=lambda *a, **k: (fla_calls.append(k), a[0])[1]
    )
    fla_ctx = backend.context()
    fla_ctx["extra_modules"] = {"fla.ops.kda": fla_mod}
    ops.build_operator_enqueue(backend.torch, kda_case, fla_ctx)()
    assert fla_calls[0] == {}

    # Long-context 400K (409,600) builders stay strictly under 8 GiB S0 VRAM cap
    cap_8gib = 8 * 1024 ** 3
    for long_case in (
        {"builder": "absorbed_mla", "dtype": "bf16", "cold_ring": True,
         "shape": {"tokens": 1, "sequences": 1, "heads": 8, "seq_len": 409600}},
        {"builder": "fusion_attention", "dtype": "bf16", "cold_ring": True, "phase": "prefill",
         "shape": {"tokens": 409600, "heads": 32, "kv_heads": 1, "head_dim": 128, "seq_len": 409600}},
        {"builder": "chunk_gated_delta_rule", "dtype": "bf16", "cold_ring": True,
         "shape": {"tokens": 409600, "heads": 2, "head_dim": 128}},
    ):
        long_ctx = backend.context(budget={"cap_bytes": cap_8gib})
        long_ctx["_byte_ledger"] = {"peak_bytes": 0}
        ops.build_operator_enqueue(backend.torch, long_case, long_ctx)()
        assert long_ctx["_byte_ledger"]["peak_bytes"] <= cap_8gib


def test_r7_dcp_partial_chaining_collective_dtype_and_per_node_shapes():
    """Verify #279: DCP partial_count chaining, collective dtype sizing, and per-node shapes."""
    from mindie_profiler.bench.subgraph_runtime import OperatorExecutor

    # 1. dcp_lse_attention_merge allocates partial_count distinct partials and chains (out, max, sum)
    backend = FakeBackend()
    merge_calls: list[tuple[Any, ...]] = []

    def fake_ring_update(acc_o, acc_m, acc_s, cur_o, cur_m, cur_s, **_kw):
        merge_calls.append((acc_o, acc_m, acc_s, cur_o, cur_m, cur_s))
        return (
            types.SimpleNamespace(tag=f"out_{len(merge_calls)}", addr=acc_o.addr + cur_o.addr),
            types.SimpleNamespace(tag=f"max_{len(merge_calls)}"),
            types.SimpleNamespace(tag=f"sum_{len(merge_calls)}"),
        )

    backend.torch.ops.npu.npu_ring_attention_update = fake_ring_update
    dcp_ctx = backend.context()
    dcp_ctx["_actual_shape"] = {}
    dcp_fn = ops.build_operator_enqueue(
        backend.torch,
        {"builder": "dcp_lse_attention_merge", "dtype": "fp32",
         "shape": {"tokens": 4, "heads": 2, "head_dim": 64, "partial_count": 4}},
        dcp_ctx,
    )
    dcp_fn()
    assert len(merge_calls) == 3
    assert len({call[3].addr for call in merge_calls} | {merge_calls[0][0].addr}) == 4
    assert merge_calls[1][0].tag == "out_1" and merge_calls[1][1].tag == "max_1"
    assert merge_calls[2][0].tag == "out_2" and merge_calls[2][2].tag == "sum_2"
    assert dcp_ctx["_actual_shape"]["partial_count"] == 4
    assert dcp_ctx["_actual_shape"]["dtype"] == "fp32"

    # 2. Collective honors bf16 element size (4096 B -> 2048 bf16 elements, not 1024 fp32)
    coll_backend = FakeBackend()
    coll_ctx = coll_backend.context()
    coll_ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        coll_backend.torch,
        {"builder": "all_reduce", "dtype": "bf16", "nbytes": 4096, "group_size": 2},
        coll_ctx,
    )()
    _cname, (buf,), _ckw = coll_backend.calls[-1]
    assert buf.shape == (2048,) and buf.dtype == coll_backend.torch.bfloat16
    assert coll_ctx["_actual_shape"]["dtype"] == "bf16"
    assert coll_ctx["_actual_shape"]["elements"] == 2048

    # 3. Subgraph OperatorExecutor records per-node node_shapes without overwriting earlier GEMMs
    sub_backend = FakeBackend()
    sub_ctx = sub_backend.context()
    sub_ctx["_actual_shape"] = {}
    ex = OperatorExecutor(sub_backend.torch, sub_ctx)
    ex.launch({"node_id": "s0.l0.q_proj", "builder": "matmul", "dtype": "bf16",
               "shape": {"m": 16, "n": 64, "k": 128}})
    ex.launch({"node_id": "s0.l0.v_expand", "builder": "grouped_matmul", "dtype": "bf16",
               "shape": {"m": 16, "n": 128, "k": 128, "e": 4}})
    node_shapes = sub_ctx["_actual_shape"]["node_shapes"]
    assert node_shapes["s0.l0.q_proj"]["n"] == 64
    assert node_shapes["s0.l0.v_expand"]["n"] == 128 and node_shapes["s0.l0.v_expand"]["matrix_groups"] == 4
