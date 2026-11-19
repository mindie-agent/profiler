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
  * Zero ``inspect.signature`` calls exist in ``mindie_profiler/bench``.

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
from mindie_profiler.events import ProfilerUsageError

REPO_ROOT = Path(__file__).resolve().parents[1]
MIB = 1024 * 1024


class FakeTensor:
    _next_addr = 1_000_000

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
        self.dtype = int(dtype)
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
            elem_bytes = int(args[0])
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
        return self


class FakeBackend:
    """Explicit fake NPU + HCCL + fla backend recording kernel dispatches."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.format_casts: list[tuple[tuple[int, ...], int]] = []
        self.torch = self._make_torch()
        self.dist = self._make_dist()

    def _record(self, name: str):
        def kernel(*args: Any, **kwargs: Any) -> FakeTensor:
            self.calls.append((name, args, kwargs))
            first = next((a for a in args if isinstance(a, FakeTensor)), None)
            if first is None and args and isinstance(args[0], list) and args[0]:
                first = args[0][0]
            shape = first.shape if isinstance(first, FakeTensor) else (4, 16)
            dev = first.device if isinstance(first, FakeTensor) else "npu:0"
            return FakeTensor(shape, dtype=2, device=dev)

        return kernel

    def _make_torch(self) -> Any:
        t = types.SimpleNamespace()
        t.uint8, t.int8, t.bfloat16, t.float16 = 1, 1, 2, 2
        t.float32, t.int32, t.int64, t.bool = 4, 4, 8, 1

        def alloc(*dims: Any, dtype: Any = 2, device: str = "npu:0", pin_memory: bool = False) -> FakeTensor:
            if len(dims) == 1 and isinstance(dims[0], (list, tuple)):
                shape = tuple(int(x) for x in dims[0])
            else:
                shape = tuple(int(x) for x in dims)
            dev = "cpu" if pin_memory else str(device or "npu:0")
            return FakeTensor(shape, dtype=int(dtype or 2), device=dev, pinned=pin_memory)

        t.zeros = alloc
        t.ones = alloc
        t.randn = alloc
        t.empty = alloc
        t.tensor = lambda data, dtype=4, device="npu:0": FakeTensor(
            (max(1, len(data)),), dtype=int(dtype or 4), device=str(device)
        )

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
            "tensor_pad", "_npu_paged_attention", "npu_scatter_nd_update",
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
    for path in sorted((REPO_ROOT / "mindie_profiler" / "bench").rglob("*.py")):
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
    # Packed INT4 halves K dimension: (128 // 2, 64) = (64, 64) cast to FRACTAL_NZ (29)
    assert ((64, 64), 29) in backend.format_casts

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
    # k_nope and v_nope are sliced views of the exact same single c_kv backing buffer (512 + 64 = 576 BF16 = 1152 B/tok)
    assert args[1].addr == args[2].addr == kwargs["key_rope"].addr
    assert args[1].shape[-1] == 576

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
    prewarm_calls = len(backend.calls)
    assert prewarm_calls >= 1
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
