"""Regression tests for real-silicon CANN 9.3.0 bench builder fixes (BUG-A..E).

[Role]
  Verify zero-offset contiguous materialization before ``npu_format_cast`` and
  ``npu_convert_weight_to_int4pack`` (BUG-A/C), 100% ``record_actual_shape``
  coverage across all registered builders and real campaign plan shapes (BUG-B),
  RNG-free ACLGraph closures plus CANN 9.3.0 ``fusion_attention``,
  ``moe_token_unpermute``, ``pool_key_indexer``, ``scatter_index_cache`` and
  ``causal_conv1d_update`` ABIs (BUG-D), and the 6-part MC2 dispatch/combine
  fixes (BUG-E).

[Invariants]
  * Pure CPU in-memory execution with fake torch/NPU handles; zero live NPU use.
  * Zero RNG calls inside any timed closure across ``operators*.py``.

[Timeouts & Locks]
  Runs in < 2 s with no sleeps, locks, threads, or network calls.

[Side-Effect Policy]
  Allocates only lightweight in-memory Python stubs; writes no files.
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
    campaign_runner,
    env_fingerprint,
    operators as ops,
    subgraph_runtime,
)
from mindie_profiler.bench.operators_common import (
    cast_weight_nz,
    materialize_contiguous_zero_offset,
    randn as common_randn,
    shape_evidence_problem,
    shape_of,
)
from mindie_profiler.events import ProfilerUsageError

REPO_ROOT = Path(__file__).resolve().parents[1]


class _Dtype:
    def __init__(self, name: str, nbytes: int, *, is_floating_point: bool = True) -> None:
        self.name = name
        self.nbytes = nbytes
        self.is_floating_point = is_floating_point

    def __str__(self) -> str:
        return f"torch.{self.name}"

    def __repr__(self) -> str:
        return f"torch.{self.name}"


class _StubTensor:
    def __init__(
        self,
        shape: tuple[int, ...],
        *,
        dtype: Any,
        device: str = "npu:0",
        offset: int = 0,
        contiguous: bool = True,
        values: Any = None,
    ) -> None:
        self.shape = tuple(int(x) for x in shape)
        self.dtype = dtype
        self.device = str(device)
        self._offset = int(offset)
        self._contiguous = bool(contiguous)
        self.values = values

    def numel(self) -> int:
        return max(1, math.prod(self.shape)) if self.shape else 1

    def size(self, dim: int | None = None) -> Any:
        return self.shape if dim is None else self.shape[dim]

    def dim(self) -> int:
        return len(self.shape)

    def storage_offset(self) -> int:
        return self._offset

    def is_contiguous(self) -> bool:
        return self._contiguous

    def contiguous(self) -> "_StubTensor":
        if self._contiguous:
            return self
        return _StubTensor(
            self.shape, dtype=self.dtype, device=self.device, offset=0, contiguous=True
        )

    def clone(self) -> "_StubTensor":
        return _StubTensor(
            self.shape, dtype=self.dtype, device=self.device, offset=0, contiguous=True,
            values=self.values,
        )

    def detach(self) -> "_StubTensor":
        return self

    def view(self, *dims: Any) -> "_StubTensor":
        target = dims[0] if len(dims) == 1 and isinstance(dims[0], (tuple, list)) else dims
        return _StubTensor(
            tuple(max(1, int(d)) for d in target), dtype=self.dtype, device=self.device,
            offset=self._offset, contiguous=self._contiguous, values=self.values,
        )

    def reshape(self, *dims: Any) -> "_StubTensor":
        return self.view(*dims)

    def transpose(self, a: int, b: int) -> "_StubTensor":
        dims = list(self.shape)
        if len(dims) > max(a, b):
            dims[a], dims[b] = dims[b], dims[a]
        return _StubTensor(
            tuple(dims), dtype=self.dtype, device=self.device,
            offset=self._offset, contiguous=False,
        )

    @property
    def T(self) -> "_StubTensor":
        return self.transpose(0, 1) if len(self.shape) >= 2 else self

    def to(self, *args: Any, **kwargs: Any) -> "_StubTensor":
        dt = kwargs.get("dtype", self.dtype)
        dev = kwargs.get("device", self.device)
        for arg in args:
            if isinstance(arg, _Dtype):
                dt = arg
            elif isinstance(arg, str):
                dev = arg
        return _StubTensor(self.shape, dtype=dt, device=dev, offset=0, contiguous=True)

    def float(self) -> "_StubTensor":
        return self.to(dtype=_DT_FP32)

    def int(self) -> "_StubTensor":
        return self.to(dtype=_DT_INT32)

    def long(self) -> "_StubTensor":
        return self.to(dtype=_DT_INT64)

    def bool(self) -> "_StubTensor":
        return self.to(dtype=_DT_BOOL)

    def unsqueeze(self, dim: int = -1) -> "_StubTensor":
        dims = list(self.shape)
        idx = len(dims) if dim == -1 else dim
        dims.insert(idx, 1)
        return _StubTensor(tuple(dims), dtype=self.dtype, device=self.device, values=self.values)

    def squeeze(self, *_a: Any) -> "_StubTensor":
        return self

    def expand(self, *_a: Any) -> "_StubTensor":
        return self

    def repeat(self, *_a: Any) -> "_StubTensor":
        return self

    def copy_(self, *_a: Any, **_k: Any) -> "_StubTensor":
        return self

    def fill_(self, *_a: Any, **_k: Any) -> "_StubTensor":
        return self

    def zero_(self) -> "_StubTensor":
        return self

    def triu_(self, *_a: Any, **_k: Any) -> "_StubTensor":
        return self

    def index_select(self, *_a: Any, **_k: Any) -> "_StubTensor":
        return self

    def index_add_(self, *_a: Any, **_k: Any) -> "_StubTensor":
        return self

    def pin_memory(self) -> "_StubTensor":
        return self

    def __getitem__(self, _idx: Any) -> "_StubTensor":
        return self

    def __mod__(self, mod: int) -> "_StubTensor":
        vals = [v % mod for v in self.values] if isinstance(self.values, list) else self.values
        return _StubTensor(self.shape, dtype=self.dtype, device=self.device, values=vals)

    def __add__(self, _o: Any) -> "_StubTensor":
        return self

    def __mul__(self, _o: Any) -> "_StubTensor":
        return self

    def __sub__(self, _o: Any) -> "_StubTensor":
        return self

    def __truediv__(self, _o: Any) -> "_StubTensor":
        return self

    def __len__(self) -> int:
        return self.shape[0] if self.shape else 0


_DT_BF16 = _Dtype("bfloat16", 2, is_floating_point=True)
_DT_FP16 = _Dtype("float16", 2, is_floating_point=True)
_DT_FP32 = _Dtype("float32", 4, is_floating_point=True)
_DT_FP8_E4M3 = _Dtype("float8_e4m3fn", 1, is_floating_point=True)
_DT_FP8_E5M2 = _Dtype("float8_e5m2", 1, is_floating_point=True)
_DT_FP8_E8M0 = _Dtype("float8_e8m0fnu", 1, is_floating_point=True)
_DT_FP4 = _Dtype("float4_e2m1fn_x2", 1, is_floating_point=True)
_DT_INT8 = _Dtype("int8", 1, is_floating_point=False)
_DT_UINT8 = _Dtype("uint8", 1, is_floating_point=False)
_DT_INT32 = _Dtype("int32", 4, is_floating_point=False)
_DT_INT64 = _Dtype("int64", 8, is_floating_point=False)
_DT_BOOL = _Dtype("bool", 1, is_floating_point=False)


class _RecordingOps:
    def __init__(self, calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]]) -> None:
        self._calls = calls

    def __getattr__(self, name: str) -> Any:
        def _fn(*args: Any, **kwargs: Any) -> Any:
            self._calls.append((name, args, kwargs))
            if "format_cast" in name:
                w = args[0]
                return _StubTensor(w.shape, dtype=w.dtype, device=w.device, offset=0, contiguous=True)
            if "int4pack" in name:
                w = args[0]
                return _StubTensor(
                    (*w.shape[:-1], max(1, w.shape[-1] // 8)), dtype=_DT_INT32, device=w.device,
                )
            if "dispatch" in name:
                tok = args[0].shape[0] if args else kwargs["x"].shape[0]
                hid = args[0].shape[-1] if args else kwargs["x"].shape[-1]
                t = _StubTensor((tok, hid), dtype=_DT_BF16)
                a_info = _StubTensor((tok,), dtype=_DT_INT32, values="real_assist_info")
                ep_cnt = _StubTensor((8,), dtype=_DT_INT32, values="real_ep_recv_counts")
                sc = _StubTensor((tok,), dtype=_DT_FP32, values="real_expand_scales")
                return (t, t, a_info, t, ep_cnt, t, sc)
            if "fusion_attention" in name:
                q = args[0]
                out = _StubTensor(q.shape, dtype=q.dtype, values="fa_primary_out")
                return (out, None, None, None, 0, 0, None)
            if any(k in name for k in ("rms_norm", "dynamic_quant", "moe_init_routing", "gating_top_k")):
                t = _StubTensor((8, 128), dtype=_DT_BF16)
                return (t, t, t, t)
            return _StubTensor((8, 128), dtype=_DT_BF16)

        _fn.__name__ = name
        return _fn


class _StubTorch:
    bfloat16 = _DT_BF16
    float16 = _DT_FP16
    float32 = _DT_FP32
    float8_e4m3fn = _DT_FP8_E4M3
    float8_e5m2 = _DT_FP8_E5M2
    float8_e8m0fnu = _DT_FP8_E8M0
    int8 = _DT_INT8
    uint8 = _DT_UINT8
    int32 = _DT_INT32
    int64 = _DT_INT64
    bool = _DT_BOOL

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.randn_dtypes: list[Any] = []
        rec = _RecordingOps(self.calls)
        self.npu = rec
        self.npu.is_available = lambda: True
        self.npu.Event = lambda *a, **k: types.SimpleNamespace(
            record=lambda: None, synchronize=lambda: None
        )
        self.npu.current_stream = lambda: types.SimpleNamespace(synchronize=lambda: None)
        self.npu.Stream = lambda *a, **k: types.SimpleNamespace(synchronize=lambda: None)
        self.npu.stream = lambda _s: types.SimpleNamespace(
            __enter__=lambda: None, __exit__=lambda *_a: None
        )
        self.nn = types.SimpleNamespace(functional=rec)
        self.linalg = rec
        self.ops = types.SimpleNamespace(npu=rec, ascend=rec, vllm_ascend=rec, _C=rec)
        self.distributed = types.SimpleNamespace(
            is_initialized=lambda: True,
            get_rank=lambda group=None: getattr(group, "rank", 0),
            get_world_size=lambda group=None: getattr(group, "size", 8),
            all_reduce=lambda *a, **k: self.calls.append(("all_reduce", a, k)),
            all_gather_into_tensor=lambda *a, **k: self.calls.append(("all_gather_into_tensor", a, k)),
            reduce_scatter_tensor=lambda *a, **k: self.calls.append(("reduce_scatter_tensor", a, k)),
            all_to_all_single=lambda *a, **k: self.calls.append(("all_to_all_single", a, k)),
            send=lambda *a, **k: self.calls.append(("send", a, k)),
            recv=lambda *a, **k: self.calls.append(("recv", a, k)),
            P2POp=lambda op, tensor, peer, group=None: (op, tensor, peer),
            batch_isend_irecv=lambda ops_list: [types.SimpleNamespace(wait=lambda: None)],
            ReduceOp=types.SimpleNamespace(SUM="SUM"),
        )
        self._rec = rec

    def device(self, name: str) -> tuple[str, str]:
        return ("torch.device", str(name))

    def _shape(self, args: tuple[Any, ...]) -> tuple[int, ...]:
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            return tuple(int(x) for x in args[0])
        return tuple(int(x) for x in args)

    def zeros(self, *dims: Any, dtype: Any = _DT_BF16, device: str = "npu:0", **_k: Any) -> _StubTensor:
        return _StubTensor(self._shape(dims), dtype=dtype or _DT_BF16, device=device)

    empty = zeros
    ones = zeros

    def randn(self, *dims: Any, dtype: Any = _DT_BF16, device: str = "npu:0", **_k: Any) -> _StubTensor:
        self.randn_dtypes.append(dtype)
        return _StubTensor(self._shape(dims), dtype=dtype or _DT_BF16, device=device)

    def full(self, shape: Any, _val: Any, dtype: Any = _DT_BF16, device: str = "npu:0", **_k: Any) -> _StubTensor:
        return _StubTensor(tuple(int(x) for x in shape), dtype=dtype or _DT_BF16, device=device)

    def arange(self, *args: Any, dtype: Any = _DT_INT32, device: str = "npu:0", **_k: Any) -> _StubTensor:
        start, stop = (0, int(args[0])) if len(args) == 1 else (int(args[0]), int(args[1]))
        vals = list(range(start, stop))
        return _StubTensor((max(1, len(vals)),), dtype=dtype or _DT_INT32, device=device, values=vals)

    def tensor(self, data: Any, dtype: Any = _DT_INT32, device: str = "npu:0", **_k: Any) -> _StubTensor:
        if isinstance(data, list) and data and isinstance(data[0], list):
            shape = (len(data), len(data[0]))
        elif isinstance(data, (list, tuple)):
            shape = (len(data),)
        else:
            shape = (1,)
        return _StubTensor(shape, dtype=dtype or _DT_INT32, device=device, values=data)

    def cat(self, ts: Any, *_a: Any, **_k: Any) -> Any:
        return ts[0]

    def stack(self, ts: Any, *_a: Any, **_k: Any) -> Any:
        return ts[0]

    def matmul(self, a: Any, _b: Any) -> Any:
        return a

    def __getattr__(self, name: str) -> Any:
        return getattr(self._rec, name)


class _GroupWithDeviceArg:
    def __init__(self, size: int = 8, rank: int = 0) -> None:
        self.size = size
        self.rank = rank
        self.backend_device_args: list[Any] = []

    def _get_backend(self, device: Any) -> Any:
        self.backend_device_args.append(device)
        return types.SimpleNamespace(get_hccl_comm_name=lambda r: f"hccl_dev_{r}")


def _make_context(torch: _StubTorch, *, arch: str = "A5", group_size: int = 8) -> dict[str, Any]:
    grp = _GroupWithDeviceArg(size=group_size, rank=0)
    sig = ",".join(str(r) for r in range(group_size))
    extra_ns = _RecordingOps(torch.calls)
    extra_ns.float4_e2m1fn_x2 = _DT_FP4
    extra_ns.float8_e8m0fnu = _DT_FP8_E8M0
    return {
        "torch_npu": extra_ns,
        "device": {"ordinal": 0},
        "soc_arch": arch,
        "arch": arch,
        "dist": torch.distributed,
        "dist_initialized": True,
        "rank": 0,
        "world_size": group_size,
        "group": grp,
        "groups": {
            "ep": grp, "tp": grp, "mc2": grp, "group": grp,
            f"ep:{group_size}": grp, f"ep@{sig}": grp, f"group@{sig}": grp,
        },
        "empty_launchers": {"empty_launch": lambda: None},
        "native_probes": {"mte2_transfer": lambda *_a, **_k: None, "mte2_aic": lambda *_a, **_k: None},
        "extra_modules": {
            "cann_ops_transformer": extra_ns,
            "fla_npu": extra_ns,
            "vllm_ascend.ops.triton.kda": extra_ns,
            "vllm_ascend.ops.triton.kda.kda": extra_ns,
            "vllm_ascend.ops.context_parallel": extra_ns,
            "vllm_ascend.ops.fused_moe": extra_ns,
            "vllm_ascend.ops": extra_ns,
            "vllm_ascend._C": extra_ns,
            "fla.ops.kda": extra_ns,
            "fla.ops.gated_delta_rule": extra_ns,
        },
    }


def test_bug_a_cast_weight_nz_materializes_nonzero_offset_and_noncontiguous() -> None:
    torch = _StubTorch()
    ctx = _make_context(torch)

    ring_slice = _StubTensor((128, 64), dtype=_DT_INT8, offset=4096, contiguous=True)
    cast_weight_nz(torch, ring_slice, ctx)
    cast_name, cast_args, _ = torch.calls[-1]
    assert cast_name == "npu_format_cast"
    assert cast_args[0] is not ring_slice
    assert cast_args[0].storage_offset() == 0
    assert cast_args[0].is_contiguous()

    transposed = _StubTensor((128, 64), dtype=_DT_FP8_E4M3, offset=0, contiguous=False)
    mat = materialize_contiguous_zero_offset(transposed)
    assert mat is not transposed
    assert mat.is_contiguous() and mat.storage_offset() == 0

    clean = _StubTensor((128, 64), dtype=_DT_BF16, offset=0, contiguous=True)
    assert materialize_contiguous_zero_offset(clean) is clean

    # quant_matmul honors explicit supported output_dtype and rejects unsupported ones
    torch.calls.clear()
    q_int8_ctx = {**ctx, "_actual_shape": {}}
    ops.build_operator_enqueue(
        torch,
        {"builder": "quant_matmul", "dtype": "int8", "output_dtype": "int8",
         "shape": {"m": 16, "n": 64, "k": 128}},
        q_int8_ctx,
    )()
    _n, mm_args, mm_kw = [c for c in torch.calls if c[0] == "npu_quant_matmul"][-1]
    assert mm_args[0].dtype == _DT_INT8 and mm_kw["output_dtype"] == _DT_INT8
    assert q_int8_ctx["_actual_shape"]["output_dtype"] == "int8"
    assert q_int8_ctx["_actual_shape"]["output_bytes"] == 1024

    torch.calls.clear()
    q_fp8_ctx = {**ctx, "_actual_shape": {}}
    ops.build_operator_enqueue(
        torch,
        {"builder": "quant_matmul", "dtype": "fp8_e4m3",
         "shape": {"m": 16, "n": 64, "k": 128}},
        q_fp8_ctx,
    )()
    _n, mm_args, mm_kw = [c for c in torch.calls if c[0] == "npu_quant_matmul"][-1]
    assert mm_args[0].dtype == _DT_FP8_E4M3 and mm_kw["output_dtype"] == _DT_BF16
    assert q_fp8_ctx["_actual_shape"]["output_dtype"] == "bf16"
    assert q_fp8_ctx["_actual_shape"]["output_bytes"] == 2048

    with pytest.raises(ProfilerUsageError, match="bench_quant_matmul_output_dtype_unsupported"):
        ops.build_operator_enqueue(
            torch,
            {"builder": "quant_matmul", "dtype": "fp8_e4m3", "output_dtype": "fp8_e4m3",
             "shape": {"m": 16, "n": 64, "k": 128}},
            ctx,
        )


def test_bug_b_every_registered_builder_and_plan_edge_shapes_record_actual_shape() -> None:
    torch = _StubTorch()
    missing: list[str] = []
    for name in sorted(ops.OPERATOR_BUILDERS):
        ctx = _make_context(torch)
        ex = subgraph_runtime.OperatorExecutor(torch, ctx)
        node = {
            "node_id": "n0", "builder": name, "op": name, "dtype": "bf16",
            "shape": {"tokens": 128, "width": 128, "m": 64, "n": 128, "k": 128, "bytes": 65536, "group_size": 8},
            "group_ranks": list(range(8)),
        }
        ex.begin_case({"case_id": f"case_{name}", "nodes": [node]})
        fn = ex.build(node)
        fn()
        actual = (ctx.get("_actual_shape") or {}).get("node_shapes", {}).get("n0")
        if not actual:
            missing.append(name)
    assert missing == [], f"builders missing actual_shape: {missing}"

    edge_cases = [
        {"builder": "ple_lookup", "dtype": "bf16", "shape": {"tokens": 8, "width": 256}},
        {"builder": "kda_triangular_solve", "dtype": "bf16", "shape": {"tokens": 8, "width": 64}},
        {"builder": "incre_flash_attention", "dtype": "bf16",
         "shape": {"tokens": 8, "sequences": 1, "q_len": 8, "heads": 16, "kv_heads": 2, "head_dim": 256, "kv_len": 8200, "is_prefill": 0}},
        {"builder": "incre_flash_attention", "dtype": "bf16",
         "shape": {"tokens": 16, "sequences": 16, "q_len": 1, "heads": 4, "kv_heads": 1, "head_dim": 256, "kv_len": 2097168, "is_prefill": 0}},
        {"builder": "fusion_attention", "dtype": "bf16",
         "shape": {"tokens": 8, "sequences": 1, "q_len": 8, "heads": 8, "kv_heads": 1, "head_dim": 192, "kv_len": 519, "is_prefill": 0}},
        {"builder": "fused_infer_attention", "dtype": "bf16",
         "shape": {"tokens": 1, "sequences": 16, "q_len": 1, "heads": 8, "kv_heads": 1, "head_dim": 512, "kv_len": 131073, "is_prefill": 0}},
        {"builder": "recurrent_gated_delta_rule", "dtype": "bf16",
         "shape": {"tokens": 8, "sequences": 1, "q_len": 8, "heads": 8, "head_dim": 128}},
    ]
    for case in edge_cases:
        ctx = _make_context(torch)
        ex = subgraph_runtime.OperatorExecutor(torch, ctx)
        node = {"node_id": "n0", **case}
        ex.begin_case({"case_id": f"edge_{case['builder']}", "nodes": [node]})
        ex.build(node)()
        actual = ctx["_actual_shape"]["node_shapes"]["n0"]
        assert shape_evidence_problem(shape_of(node), actual) is None, (case, actual)


def test_bug_c_mxfp4_and_w4a8_pass_int32_zero_offset_to_int4pack() -> None:
    torch = _StubTorch()
    ctx = _make_context(torch, arch="A5")
    for builder, shape in (
        ("grouped_matmul", {"m": 16, "n": 64, "k": 128, "e": 4}),
        ("quant_matmul", {"m": 16, "n": 64, "k": 128}),
    ):
        torch.calls.clear()
        case = {"builder": builder, "dtype": "w4a8", "shape": shape}
        ops.build_operator_enqueue(torch, case, ctx)()
        pack_calls = [c for c in torch.calls if c[0] == "npu_convert_weight_to_int4pack"]
        assert pack_calls, (builder, "w4a8")
        for _name, args, _kw in pack_calls:
            assert args[0].dtype == _DT_INT32
            assert args[0].storage_offset() == 0
            assert args[0].is_contiguous()

        # CANN 9.3.0 A5 MXFP4 uses native uint8 packed FP4 + float4_e2m1fn_x2 / float8_e8m0fnu in ND
        torch.calls.clear()
        mx_case = {"builder": builder, "dtype": "mxfp4", "shape": shape}
        ops.build_operator_enqueue(torch, mx_case, ctx)()
        assert not [c for c in torch.calls if c[0] == "npu_convert_weight_to_int4pack"]
        assert not [c for c in torch.calls if c[0] == "npu_format_cast"]
        if builder == "quant_matmul":
            _n, q_args, q_kw = [c for c in torch.calls if c[0] == "npu_quant_matmul"][-1]
            assert q_args[0].dtype == _DT_UINT8 and q_args[0].shape == (16, 64)
            assert q_args[1].dtype == _DT_UINT8 and q_args[1].shape == (64, 64)
            assert q_kw["x1_dtype"] == _DT_FP4 and q_kw["x2_dtype"] == _DT_FP4
            assert q_kw["scale_dtype"] == _DT_FP8_E8M0 and q_kw["pertoken_scale_dtype"] == _DT_FP8_E8M0
            assert q_kw["group_sizes"] == [1, 1, 32]
        else:
            _n, g_args, g_kw = [c for c in torch.calls if c[0] == "npu_grouped_matmul"][-1]
            assert g_args[0][0].dtype == _DT_UINT8 and g_args[0][0].shape == (16, 64)
            assert g_args[1][0].dtype == _DT_UINT8 and g_args[1][0].shape == (4, 64, 64)
            assert g_kw["x_dtype"] == _DT_FP4 and g_kw["weight_dtype"] == _DT_FP4
            assert g_kw["scale_dtype"] == _DT_FP8_E8M0 and g_kw["per_token_scale_dtype"] == _DT_FP8_E8M0


def test_bug_d_zero_rng_in_closures_and_cann_93_op_signatures() -> None:
    # 1. Static AST invariant: zero RNG calls inside nested closures across operators*.py
    rng_names = {"randn", "rand", "randint", "randperm", "bernoulli", "normal_", "uniform_"}
    hits: list[tuple[str, str, int, str]] = []
    for path in sorted((REPO_ROOT / "mindie_profiler" / "bench").glob("operators*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for child in ast.walk(fn_node):
                if child is fn_node or not isinstance(
                    child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
                ):
                    continue
                for sub in ast.walk(child):
                    if isinstance(sub, ast.Call):
                        attr = sub.func.attr if isinstance(sub.func, ast.Attribute) else (
                            sub.func.id if isinstance(sub.func, ast.Name) else ""
                        )
                        if attr in rng_names:
                            hits.append((path.name, fn_node.name, sub.lineno, attr))
    assert hits == [], f"RNG inside timed closure: {hits}"

    torch = _StubTorch()
    ctx = _make_context(torch, arch="A5")

    # 2. moe_token_unpermute passes unique permutation range(tokens * top_k)
    ops.build_operator_enqueue(
        torch,
        {"builder": "moe_token_unpermute", "dtype": "bf16",
         "shape": {"tokens": 4, "width": 16, "top_k": 2}},
        ctx,
    )()
    _n, unperm_args, _kw = [c for c in torch.calls if c[0] == "npu_moe_token_unpermute"][-1]
    assert unperm_args[1].values == list(range(8))

    # 3. fusion_attention disables dropout RNG and unwraps 7-tuple to primary tensor
    torch.calls.clear()
    fa_out = ops.build_operator_enqueue(
        torch,
        {"builder": "fusion_attention", "dtype": "bf16",
         "shape": {"tokens": 8, "sequences": 1, "q_len": 8, "heads": 8, "kv_heads": 1,
                   "head_dim": 192, "kv_len": 519, "is_prefill": 0}},
        ctx,
    )()
    _n, fa_args, fa_kw = [c for c in torch.calls if c[0] == "npu_fusion_attention"][-1]
    assert fa_kw["keep_prob"] == 1.0
    assert fa_kw["gen_mask_parallel"] is False
    assert fa_kw["actual_seq_qlen"] == [8]
    assert fa_kw["actual_seq_kvlen"] == [519]
    assert fa_args[1].shape == (519, 1, 192)
    assert isinstance(fa_out, _StubTensor) and fa_out.values == "fa_primary_out"

    # 4. pool_key_indexer matches CANN 9.3.0 4-tensor + kwargs schema (BF16, FP8, INT8)
    for dt_name, exp_qmode in (("bf16", None), ("fp8_e4m3", 0), ("int8", 2)):
        torch.calls.clear()
        ops.build_operator_enqueue(
            torch,
            {"builder": "pool_key_indexer", "dtype": dt_name,
             "shape": {"tokens": 8, "heads": 8, "head_dim": 64, "seq_len": 256, "topk": 64}},
            ctx,
        )()
        _n, pk_args, pk_kw = [
            c for c in torch.calls if c[0] in {"pool_key_indexer", "npu_pool_key_indexer"}
        ][-1]
        assert len(pk_args) == 4
        assert pk_kw["layout_q"] == "TND" and pk_kw["layout_k"] == "TND"
        assert pk_kw["topk"] == 64
        if exp_qmode is None:
            assert "quant_mode" not in pk_kw
        else:
            assert pk_kw["quant_mode"] == exp_qmode
            assert "q_descale" in pk_kw and "k_descale" in pk_kw

    # 5. scatter_index_cache uses (cache, indices[T, 1], updates) and int8 carrier for FP8/MXFP4
    for dt_name, exp_dt in (("bf16", _DT_BF16), ("fp8_e4m3", _DT_INT8), ("mxfp4", _DT_INT8)):
        torch.calls.clear()
        ops.build_operator_enqueue(
            torch,
            {"builder": "scatter_index_cache", "dtype": dt_name,
             "shape": {"tokens": 6, "width": 64, "seq_len": 32}},
            ctx,
        )()
        _n, sc_args, _kw = [c for c in torch.calls if c[0] == "npu_scatter_nd_update"][-1]
        assert len(sc_args) == 3
        assert sc_args[0].shape == (32, 64) and sc_args[0].dtype == exp_dt
        assert sc_args[1].shape == (6, 1) and sc_args[1].dtype == _DT_INT32
        assert sc_args[2].shape == (6, 64) and sc_args[2].dtype == exp_dt

    # 6. causal_conv1d_update with width=1 factors 3072 into aligned (1, 3072) for fused kernel
    torch.calls.clear()
    c1d_ctx = _make_context(torch, arch="A5")
    c1d_ctx["_actual_shape"] = {}
    c1d_ctx["op_overrides"] = {"causal_conv1d_update": getattr(torch.npu, "npu_fused_causal_conv1d")}
    ops.build_operator_enqueue(
        torch,
        {"builder": "causal_conv1d_update", "dtype": "bf16",
         "shape": {"tokens": 3072, "width": 1}},
        c1d_ctx,
    )()
    _n, c_args, c_kw = [c for c in torch.calls if c[0] == "npu_fused_causal_conv1d"][-1]
    assert c_args[0].shape == (1, 3072)
    assert c_args[1].shape[1] == 3072
    assert c_args[2].shape[-1] == 3072
    assert "query_start_loc" in c_kw and "cache_indices" in c_kw
    assert shape_evidence_problem({"tokens": 3072, "width": 1}, c1d_ctx["_actual_shape"]) is None

    # 7. _capture_and_time_graph resets captured NPUGraph in finally & campaign_runner preserves capture reason
    reset_called: list[bool] = []
    fake_graph = types.SimpleNamespace(reset=lambda: reset_called.append(True))
    fake_runtime = types.SimpleNamespace(
        synchronize=lambda: None,
        capture=lambda fn, _name: ((fake_graph, fn()), {"status": "captured"}),
        replay=lambda cap: cap[1],
    )
    fake_protocol = types.SimpleNamespace(run=lambda fn, **_kw: {"qualified": True, "p50_us": 1.0})
    fake_exec = types.SimpleNamespace(torch=torch, outputs={})
    _graph, _rcpt, agree, ok = subgraph_runtime._capture_and_time_graph(
        fake_exec, fake_runtime, fake_protocol, {"case_id": "c1"}, [{"node_id": "n0"}],
        lambda: [_StubTensor((4, 4), dtype=_DT_BF16)], {},
    )
    assert reset_called == [True] and agree and ok

    fail_runtime = types.SimpleNamespace(
        synchronize=lambda: None,
        capture=lambda _fn, _name: (None, {"status": "capture_failed", "reason": "rng_offset_mismatch"}),
        replay=lambda _cap: None,
    )
    cap_ctx = _make_context(torch, arch="A5")
    cap_exec = subgraph_runtime.OperatorExecutor(torch, cap_ctx)
    cap_case = {
        "acquisition_uid": "acq-capfail",
        "case_id": "k2-fa-capfail",
        "canonical_key_digest": "0" * 16,
        "kind": "operator",
        "phase": "decode",
        "capture_mode": "aclgraph",
        "residency": "hot_l2",
        "canonical_key": {"storage_offsets": {"input": 0}, "strides": {"input": [1]}},
        "nodes": [{
            "node_id": "n0", "kind": "operator", "builder": "fusion_attention",
            "op": "fusion_attention", "dtype": "bf16",
            "shape": {"tokens": 8, "sequences": 1, "q_len": 8, "heads": 8, "kv_heads": 1,
                      "head_dim": 192, "kv_len": 519, "is_prefill": 0},
        }],
    }
    blocked, _rows, outcome = campaign_runner._execute_measured_case(
        cap_case, executor=cap_exec, protocol=fake_protocol, runtime=fail_runtime,
        stage="s0_local", rank=0, world_size=1, campaign_id="camp-test",
        soc_arch="A5", clock_source="test", nominal_clock_mhz=1650.0,
        baseline_clock_mhz=1650.0, observed_clock_mhz=1650.0,
        l2_bytes=0, env_id="env-test", run_id="run-test",
    )
    assert outcome == "blocked"
    assert blocked["status"] == "failed"
    assert blocked["reason"] == "rng_offset_mismatch"


def test_bug_e_mc2_six_fixes_and_randn_integer_guard() -> None:
    torch = _StubTorch()
    # Guard randn against integer/bool/fp8/fp4 dtypes
    for non_std in (_DT_INT8, _DT_INT32, _DT_BOOL, _DT_FP8_E4M3, _DT_FP4):
        out = common_randn(torch, 4, 8, dtype=non_std, device="npu:0")
        assert out.dtype == non_std
    assert torch.randn_dtypes == []

    # MC2 dispatch with bytes-only shape + strides via OperatorExecutor.begin_case + FP8/INT8
    for dt_name, exp_y_dtype in (("int8", None), ("fp8_e4m3", _DT_FP8_E4M3)):
        torch.calls.clear()
        ctx = _make_context(torch, arch="A5", group_size=4)
        ex = subgraph_runtime.OperatorExecutor(torch, ctx)
        node = {
            "node_id": "n0", "builder": "mc2_dispatch", "dtype": dt_name,
            "group": "ep", "group_ranks": [0, 1, 2, 3],
            "shape": {"bytes": 40960, "group_size": 4},
        }
        case = {"case_id": "c_mc2_d", "canonical_key": {"strides": {"input": [5120, 1]}}, "nodes": [node]}
        ex.begin_case(case)
        ex.build(node)()
        actual = ctx["_actual_shape"]["node_shapes"]["n0"]
        assert shape_evidence_problem(shape_of(node), actual) is None
        assert actual["width"] == 5120 and actual["tokens"] == 8
        grp = ctx["group"]
        assert grp.backend_device_args == [("torch.device", "npu")]
        _n, _a, kw = [c for c in torch.calls if c[0] == "npu_moe_distribute_dispatch_v2"][-1]
        assert kw["x"].dtype == _DT_BF16
        assert kw["quant_mode"] == 2
        assert kw["moe_expert_num"] % 4 == 0 and kw["moe_expert_num"] >= 4
        assert kw["expert_shard_type"] == 0 and kw["shared_expert_rank_num"] == 0 and kw["global_bs"] == 0
        assert kw["group_ep"] == "hccl_dev_0"
        if exp_y_dtype is None:
            assert "y_dtype" not in kw
        else:
            assert kw["y_dtype"] == exp_y_dtype

    # MC2 combine runs 1 setup dispatch_v2 and wires outputs into combine_v2
    torch.calls.clear()
    ctx = _make_context(torch, arch="A3", group_size=8)
    ex = subgraph_runtime.OperatorExecutor(torch, ctx)
    node = {
        "node_id": "n0", "builder": "mc2_combine", "dtype": "bf16",
        "group": "ep", "group_ranks": list(range(8)),
        "shape": {"bytes": 65536, "group_size": 8},
    }
    ex.begin_case({"case_id": "c_mc2_c", "canonical_key": {"strides": {"input": [4096, 1]}}, "nodes": [node]})
    step = ex.build(node)
    dispatch_setup_calls = [c for c in torch.calls if c[0] == "npu_moe_distribute_dispatch_v2"]
    assert len(dispatch_setup_calls) == 1
    step()
    combine_calls = [c for c in torch.calls if c[0] == "npu_moe_distribute_combine_v2"]
    assert len(combine_calls) == 1
    _n, _a, ckw = combine_calls[0]
    assert ckw["assist_info_for_combine"].values == "real_assist_info"
    assert ckw["ep_send_counts"].values == "real_ep_recv_counts"
    assert ckw["expand_scales"].values == "real_expand_scales"
    assert ckw["group_ep"] == "hccl_dev_0"
    assert shape_evidence_problem(shape_of(node), ctx["_actual_shape"]["node_shapes"]["n0"]) is None

    # INT8 MC2 dispatch preserves expand_x as primary output [0] alongside (dynamic_scales, expert_token_nums, ep_recv_counts)
    d_ctx = _make_context(torch, arch="A3", group_size=4)
    d_ex = subgraph_runtime.OperatorExecutor(torch, d_ctx)
    d_node = {
        "node_id": "n0", "builder": "mc2_dispatch", "dtype": "int8",
        "group": "ep", "group_ranks": [0, 1, 2, 3],
        "shape": {"bytes": 16384, "group_size": 4},
    }
    d_ex.begin_case({"case_id": "c_mc2_det", "canonical_key": {"strides": {"input": [4096, 1]}}, "nodes": [d_node]})
    det_out = d_ex.build(d_node)()
    assert isinstance(det_out, tuple) and len(det_out) == 4
    assert det_out[0].shape == (4, 4096)
    assert det_out[3].values == "real_ep_recv_counts"


def test_a5_cann_93_abi_fixes_and_mc2_round_robin_expert_ids() -> None:
    torch = _StubTorch()
    ctx = _make_context(torch, arch="A5")

    # 1. grouped_matmul FP8 ND (float32 scale, zero NZ cast), FP8 FRACTAL_NZ (MXFP8 e8m0 + customize_dtype), MXFP4 k=1
    torch.calls.clear()
    ops.build_operator_enqueue(
        torch,
        {"builder": "grouped_matmul", "dtype": "fp8_e4m3", "layout": "ND",
         "shape": {"m": 16, "n": 128, "k": 64, "e": 4}},
        ctx,
    )()
    assert not [c for c in torch.calls if c[0] == "npu_format_cast"]
    _n, gnd_args, gnd_kw = [c for c in torch.calls if c[0] == "npu_grouped_matmul"][-1]
    assert gnd_args[1][0].shape == (4, 64, 128) and gnd_args[1][0].dtype == _DT_FP8_E4M3
    assert gnd_kw["scale"][0].dtype == _DT_FP32 and gnd_kw["output_dtype"] == _DT_BF16

    torch.calls.clear()
    ops.build_operator_enqueue(
        torch,
        {"builder": "grouped_matmul", "dtype": "fp8_e4m3", "layout": "FRACTAL_NZ",
         "shape": {"m": 16, "n": 128, "k": 128, "e": 4}},
        ctx,
    )()
    cast_calls = [c for c in torch.calls if c[0] == "npu_format_cast"]
    assert cast_calls and cast_calls[-1][2].get("customize_dtype") == _DT_FP8_E4M3
    _n, gnz_args, gnz_kw = [c for c in torch.calls if c[0] == "npu_grouped_matmul"][-1]
    assert gnz_kw["scale_dtype"] == _DT_FP8_E8M0 and gnz_kw["per_token_scale_dtype"] == _DT_FP8_E8M0

    torch.calls.clear()
    k1_ctx = {**ctx, "_actual_shape": {}}
    ops.build_operator_enqueue(
        torch,
        {"builder": "grouped_matmul", "dtype": "mxfp4", "layout": "ND",
         "shape": {"m": 4, "n": 128, "k": 1, "e": 8}},
        k1_ctx,
    )()
    _n, gk1_args, gk1_kw = [c for c in torch.calls if c[0] == "npu_grouped_matmul"][-1]
    assert gk1_args[0][0].shape == (4, 32) and gk1_args[1][0].shape == (8, 32, 128)
    assert shape_evidence_problem({"m": 4, "n": 128, "k": 1, "e": 8}, k1_ctx["_actual_shape"]) is None

    # 2. dynamic_quant feeds BF16 input for fp8_e4m3 & mxfp4 targets
    torch.calls.clear()
    ops.build_operator_enqueue(
        torch, {"builder": "dynamic_quant", "dtype": "fp8_e4m3", "shape": {"tokens": 8, "width": 128}}, ctx
    )()
    _n, dq_args, dq_kw = [c for c in torch.calls if c[0] == "npu_dynamic_quant"][-1]
    assert dq_args[0].dtype == _DT_BF16 and dq_kw["dst_type"] == _DT_FP8_E4M3

    torch.calls.clear()
    ops.build_operator_enqueue(
        torch, {"builder": "dynamic_quant", "dtype": "mxfp4", "shape": {"tokens": 8, "width": 128}}, ctx
    )()
    _n, mxq_args, mxq_kw = [c for c in torch.calls if c[0] == "npu_dynamic_mx_quant"][-1]
    assert mxq_args[0].dtype == _DT_BF16 and mxq_kw["dst_type"] == _DT_FP4 and mxq_kw["round_mode"] == "round"

    # 3. scatter_pa_kv_cache passes cache_mode="Norm"
    torch.calls.clear()
    ops.build_operator_enqueue(
        torch, {"builder": "scatter_pa_kv_cache", "dtype": "bf16", "shape": {"tokens": 8, "width": 256}}, ctx
    )()
    _n, _spa_args, spa_kw = [c for c in torch.calls if c[0] == "npu_scatter_pa_kv_cache"][-1]
    assert spa_kw == {"cache_mode": "Norm"}

    # 4. lightning_indexer bf16 matches query/weights dtype, fp8 uses v2 topk + quant_mode + metadata
    torch.calls.clear()
    ops.build_operator_enqueue(
        torch, {"builder": "lightning_indexer", "dtype": "bf16", "shape": {"tokens": 8, "width": 128}}, ctx
    )()
    _n, li_args, _li_kw = [c for c in torch.calls if c[0] == "npu_lightning_indexer"][-1]
    assert li_args[0].dtype == _DT_BF16 and li_args[2].dtype == _DT_BF16

    torch.calls.clear()
    ops.build_operator_enqueue(
        torch, {"builder": "lightning_indexer", "dtype": "fp8_e4m3", "shape": {"tokens": 8, "width": 256}}, ctx
    )()
    assert [c for c in torch.calls if c[0] == "npu_quant_lightning_indexer_v2_metadata"]
    _n, qli_args, qli_kw = [c for c in torch.calls if c[0] == "npu_quant_lightning_indexer_v2"][-1]
    assert qli_kw["topk"] == 8 and qli_kw["quant_mode"] == 1
    assert qli_kw["layout_q"] == "TND" and qli_kw["layout_k"] == "PA_BBND"
    assert "cu_seqlens_q" in qli_kw and "seqused_k" in qli_kw and "block_table" in qli_kw

    # 5. mixed_quant_sparse_mla uses ori_kv / ori_sparse_indices / metadata (no 'k' kwarg!)
    smla_calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _smla_rec(tag: str):
        def _f(*a: Any, **k: Any) -> Any:
            smla_calls.append((tag, a, k))
            return a[0] if a else _StubTensor((16,), dtype=_DT_INT32)
        _f.__name__ = tag
        return _f

    smla_torch = _StubTorch()
    smla_torch.npu = types.SimpleNamespace(synchronize=lambda: None)
    smla_torch.ops = types.SimpleNamespace(
        npu=smla_torch.npu,
        _C_ascend=types.SimpleNamespace(
            npu_sparse_flash_mla=_smla_rec("npu_sparse_flash_mla"),
            npu_sparse_flash_mla_metadata=_smla_rec("npu_sparse_flash_mla_metadata"),
        ),
        cann_ops_transformer=types.SimpleNamespace(),
    )
    smla_ctx: dict[str, Any] = {
        "torch_npu": smla_torch.npu,
        "device": {"ordinal": 0},
        "soc_arch": "A5",
        "_actual_shape": {},
        "extra_modules": {},
    }
    smla_shape = {"head_dim": 512, "heads": 8, "is_prefill": 0, "kv_heads": 1, "kv_len": 2048, "q_len": 1, "sequences": 16, "tokens": 16}
    ops.build_operator_enqueue(
        smla_torch, {"builder": "mixed_quant_sparse_mla", "dtype": "bf16", "shape": smla_shape}, smla_ctx
    )()
    assert [c for c in smla_calls if c[0] == "npu_sparse_flash_mla_metadata"]
    _n, sm_args, sm_kw = [c for c in smla_calls if c[0] == "npu_sparse_flash_mla"][-1]
    assert "k" not in sm_kw and "ori_kv" in sm_kw and "ori_sparse_indices" in sm_kw and "ori_block_table" in sm_kw
    assert sm_args[0].shape == (16, 8, 576)
    assert sm_kw["layout_q"] == "TND" and sm_kw["layout_kv"] == "PA_BBND"
    assert shape_evidence_problem(smla_shape, smla_ctx["_actual_shape"]) is None

    # 6. causal_conv1d_update (fla_npu ABI) & kv_compress_epilog width=1
    fla_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def _fla_conv_upd(*a: Any, **kw: Any) -> Any:
        fla_calls.append((a, kw))
        return a[0]

    _fla_conv_upd.__module__ = "fla_npu.ops.ascendc"
    fla_ctx = _make_context(torch, arch="A5")
    fla_ctx["op_overrides"] = {"causal_conv1d_update": _fla_conv_upd}
    ops.build_operator_enqueue(
        torch, {"builder": "causal_conv1d_update", "dtype": "bf16", "shape": {"tokens": 3072, "width": 1}}, fla_ctx
    )()
    fa_args, fa_kw = fla_calls[-1]
    assert fa_args[0].shape == (1, 3072) and fa_args[1].shape == (1, 4, 3072) and fa_args[2].shape == (4, 3072)
    assert fa_kw["activation"] == "silu" and fa_kw["max_query_len"] == 1 and "conv_state_indices" in fa_kw

    torch.calls.clear()
    kvc_ctx = {**ctx, "_actual_shape": {}}
    ops.build_operator_enqueue(
        torch, {"builder": "kv_compress_epilog", "dtype": "bf16", "shape": {"tokens": 512, "width": 1}}, kvc_ctx
    )()
    _n, kvc_args, _ = [c for c in torch.calls if c[0] == "npu_kv_compress_epilog"][-1]
    assert kvc_args[1].shape == (1, 512)
    assert shape_evidence_problem({"tokens": 512, "width": 1}, kvc_ctx["_actual_shape"]) is None

    # 7. Newly wired A5 Triton/CANN builders (rms_norm_gated, split_qkv_rmsnorm_rope, fused_gdn_gating,
    #    dcp_output_pack, ssm_state_gather, hc_pre_v2, mhc_stream_mix, engram_ngram_hash, indexer_topk, A5 layer_norm/rms_norm_quant)
    triton_calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _rec_fn(tag: str, mod: str):
        def _f(*a: Any, **k: Any) -> Any:
            triton_calls.append((tag, a, k))
            return a[0]
        _f.__name__ = tag
        _f.__module__ = mod
        return _f

    class _FakeTritonKernel:
        def __init__(self, tag: str) -> None:
            self.__name__ = tag
            self.tag = tag

        def __getitem__(self, grid: Any):
            def _launch(*a: Any, **k: Any) -> None:
                triton_calls.append((self.tag, (grid, *a), k))
            return _launch

        def __call__(self, *_a: Any, **_k: Any) -> None:
            raise RuntimeError("must launch with grid")

    bare_npu = types.SimpleNamespace(
        synchronize=lambda: None,
        npu_rms_norm_quant=_rec_fn("npu_rms_norm_quant", "torch_npu"),
        npu_fused_infer_attention_score=_rec_fn("npu_fused_infer_attention_score", "torch_npu"),
    )
    bare_torch = _StubTorch()
    bare_torch.npu = bare_npu
    bare_torch.ops = types.SimpleNamespace(
        npu=bare_npu,
        _C_ascend=types.SimpleNamespace(npu_hc_pre_v2=_rec_fn("npu_hc_pre_v2", "vllm_ascend")),
        cann_ops_transformer=types.SimpleNamespace(),
    )
    bare_torch.topk = _rec_fn("torch.topk", "torch")
    bare_torch.layer_norm = _rec_fn("torch.layer_norm", "torch")
    triton_ctx = {
        "torch_npu": bare_npu,
        "device": {"ordinal": 0},
        "soc_arch": "A5",
        "extra_modules": {
            "vllm_ascend.ops.triton.kda.kda": types.SimpleNamespace(
                rms_norm_gated=_rec_fn("rms_norm_gated", "vllm_ascend.ops.triton.kda.kda")
            ),
            "vllm_ascend.ops.triton.linearnorm.split_qkv_rmsnorm_rope": types.SimpleNamespace(
                split_qkv_rmsnorm_rope_impl=_rec_fn("split_qkv_rmsnorm_rope_impl", "vllm_ascend.ops.triton.linearnorm.split_qkv_rmsnorm_rope")
            ),
            "vllm_ascend.ops.triton.fused_gdn_gating": types.SimpleNamespace(
                fused_gdn_gating_patch=_rec_fn("fused_gdn_gating_patch", "vllm_ascend.ops.triton.fused_gdn_gating")
            ),
            "vllm_ascend.ops.triton.dcp.dcp_a2a": types.SimpleNamespace(
                pack_dcp_output_lse=_rec_fn("pack_dcp_output_lse", "vllm_ascend.ops.triton.dcp.dcp_a2a")
            ),
            "vllm_ascend.ops.triton.mamba.state_index": types.SimpleNamespace(
                gather_ssm_states=_rec_fn("gather_ssm_states", "vllm_ascend.ops.triton.mamba.state_index")
            ),
            "vllm_ascend.ops.triton.qwen4_exp.hc": types.SimpleNamespace(
                hc_gate_mix=_rec_fn("hc_gate_mix", "vllm_ascend.ops.triton.qwen4_exp.hc")
            ),
            "vllm_ascend.ops.triton.engram_hash": types.SimpleNamespace(
                _engram_req_index_kernel=_FakeTritonKernel("_engram_req_index_kernel"),
                _hash_ids_kernel=_FakeTritonKernel("_hash_ids_kernel"),
            ),
        },
    }
    for case in (
        {"builder": "indexer_topk", "dtype": "fp32", "shape": {"tokens": 32, "width": 1}},
        {"builder": "rms_norm_gated", "dtype": "bf16", "shape": {"tokens": 16, "width": 128}},
        {"builder": "split_qkv_rmsnorm_rope", "dtype": "bf16", "shape": {"tokens": 16, "width": 768}},
        {"builder": "fused_gdn_gating", "dtype": "bf16", "shape": {"tokens": 32, "width": 32}},
        {"builder": "dcp_output_pack", "dtype": "bf16", "shape": {"tokens": 16, "width": 512}},
        {"builder": "dcp_output_pack", "dtype": "bf16", "shape": {"tokens": 1, "width": 256}},
        {"builder": "ssm_state_gather", "dtype": "fp32", "shape": {"tokens": 8, "width": 256}},
        {"builder": "hc_pre", "dtype": "bf16", "shape": {"tokens": 20480, "width": 1}},
        {"builder": "mhc_stream_mix", "dtype": "bf16", "shape": {"tokens": 8, "width": 2560}},
        {"builder": "engram_ngram_hash", "dtype": "fp32", "shape": {"tokens": 64, "width": 24}},
        {"builder": "layer_norm", "dtype": "bf16", "shape": {"tokens": 16, "width": 256}},
        {"builder": "rms_norm_quant", "dtype": "bf16", "shape": {"tokens": 16, "width": 128}},
        {"builder": "incre_flash_attention", "dtype": "bf16", "shape": {"tokens": 8, "sequences": 8, "heads": 4, "kv_heads": 1, "head_dim": 128, "kv_len": 256}},
    ):
        run_ctx = {**triton_ctx, "_actual_shape": {}}
        ops.build_operator_enqueue(bare_torch, case, run_ctx)()
        assert shape_evidence_problem(case["shape"], run_ctx["_actual_shape"]) is None, (case, run_ctx["_actual_shape"])
    dispatched = {tag for tag, _a, _k in triton_calls}
    assert {
        "torch.topk", "rms_norm_gated", "split_qkv_rmsnorm_rope_impl", "fused_gdn_gating_patch",
        "pack_dcp_output_lse", "gather_ssm_states", "npu_hc_pre_v2", "hc_gate_mix",
        "_engram_req_index_kernel", "_hash_ids_kernel", "torch.layer_norm",
        "npu_rms_norm_quant", "npu_fused_infer_attention_score",
    } <= dispatched

    # 8. _mc2_expert_ids round-robin guarantees every rank sends & receives >= 1 token even at tokens=1, top_k=1
    from mindie_profiler.bench.operators_moe_comm import _mc2_expert_ids

    for tokens, ep_world, moe_experts in ((1, 8, 8), (2, 8, 16), (3, 4, 8)):
        recv_by_rank = [0] * ep_world
        epr = moe_experts // ep_world
        for r in range(ep_world):
            eids = _mc2_expert_ids(torch, tokens, 1, moe_experts, "npu:0", ep_rank=r, ep_world=ep_world)
            flat = [v for row in eids.values for v in row]
            assert len(flat) == tokens
            for eid in flat:
                recv_by_rank[eid // epr] += 1
        assert all(cnt == tokens for cnt in recv_by_rank), (tokens, ep_world, recv_by_rank)


def test_round3_astra_10_to_18_closure(monkeypatch) -> None:
    """Verify Round-3 Astra findings #10 through #18 with exact counterexample shapes."""
    # #10: Dual-die clock qualification reads curFreq (800 MHz), fails 1485 MHz bound, reports missing when absent.
    mapping_out = "\n".join([
        "NPU ID  Chip ID  Chip Logic ID  Chip Phy-ID  Chip Name",
        "7       0        14             14           Ascend910",
        "7       1        15             15           Ascend910",
    ])
    throttled_out = "\n".join([
        "NPU ID : 7", "Chip ID : 0", "Aicore Freq(MHZ) : 1500", "Aicore curFreq(MHZ) : 1500",
        "Chip ID : 1", "Aicore Freq(MHZ) : 1650", "Aicore curFreq(MHZ) : 800",
    ])
    monkeypatch.setattr(
        env_fingerprint, "_bounded_run",
        lambda cmd, *, cwd=None: mapping_out if tuple(cmd) == ("npu-smi", "info", "-m") else throttled_out,
    )
    obs_mhz, obs_src = env_fingerprint.probe_observed_clock(physical_id=15, allow_npu_smi=True)
    assert (obs_mhz, obs_src) == (800.0, "npu-smi_cur_freq_mhz")
    clock_ok, clock_reason = env_fingerprint.validate_clock_band(obs_mhz, nominal_clock_mhz=1650.0)
    assert not clock_ok and clock_reason == "clock_thermally_throttled:800.0<1485.0"
    no_cur_out = "\n".join([
        "NPU ID : 7", "Chip ID : 0", "Aicore Freq(MHZ) : 1500", "Aicore curFreq(MHZ) : 1500",
        "Chip ID : 1", "Aicore Freq(MHZ) : 1650",
    ])
    monkeypatch.setattr(
        env_fingerprint, "_bounded_run",
        lambda cmd, *, cwd=None: mapping_out if tuple(cmd) == ("npu-smi", "info", "-m") else no_cur_out,
    )
    assert env_fingerprint.probe_observed_clock(physical_id=15, allow_npu_smi=True) == (None, "unavailable")

    # #11: mc2_dispatch preserves expand_x on data edges to grouped_matmul AND checks active rows (skipping HBM tail).
    class _RowTensor(_StubTensor):
        def narrow(self, dim: int, start: int, length: int) -> "_RowTensor":
            assert dim == 0
            sliced_rows = [list(r) for r in self.values[start:start + length]]
            return _RowTensor((length, *self.shape[1:]), dtype=self.dtype, device=self.device, values=sliced_rows)

        def clone(self) -> "_RowTensor":
            copied = [list(r) for r in self.values] if isinstance(self.values, list) and self.values and isinstance(self.values[0], list) else (
                list(self.values) if isinstance(self.values, list) else self.values
            )
            return _RowTensor(self.shape, dtype=self.dtype, device=self.device, values=copied)

    mc2_torch = _StubTorch()
    mc2_torch.allclose = lambda a, b, **_k: a.shape == b.shape and a.dtype == b.dtype and a.values == b.values
    dispatch_mode = ["ref"]

    def _fake_dispatch_v2(**kw: Any) -> tuple[Any, ...]:
        tok, hid = kw["x"].shape
        active = [[1.0] * 4 for _ in range(tok)]
        if dispatch_mode[0] == "perturb_active":
            active[2][0] = 9.0
        tail_val = 999.0 if dispatch_mode[0] == "ref" else -777.0
        tail = [[tail_val] * 4 for _ in range(tok)]
        expand_x = _RowTensor((tok * 2, hid), dtype=_DT_BF16, values=active + tail)
        nums = _RowTensor((4,), dtype=_DT_INT32, values=[2, 2, 2, 2])
        ep_cnt = _RowTensor((4,), dtype=_DT_INT32, values=[2, 4, 6, 8])
        dummy = _RowTensor((tok,), dtype=_DT_INT32, values=[0] * tok)
        return (expand_x, dummy, dummy, nums, ep_cnt, dummy, dummy)

    mc2_ctx = _make_context(mc2_torch, arch="A3", group_size=4)
    mc2_ctx["op_overrides"] = {"npu_moe_distribute_dispatch_v2": _fake_dispatch_v2}
    mc2_ex = subgraph_runtime.OperatorExecutor(mc2_torch, mc2_ctx)
    disp_node = {
        "node_id": "n_disp", "builder": "mc2_dispatch", "dtype": "bf16",
        "group": "ep", "group_ranks": [0, 1, 2, 3],
        "shape": {"tokens": 8, "width": 4096, "e": 4, "top_k": 1, "group_size": 4},
    }
    gmm_node = {
        "node_id": "n_gmm", "builder": "grouped_matmul", "dtype": "bf16",
        "shape": {"m": 8, "n": 256, "k": 4096, "e": 4},
    }
    mc2_ex.begin_case({"case_id": "c_mc2_sub", "nodes": [disp_node, gmm_node]})
    ref_disp = mc2_ex.launch(disp_node)
    assert isinstance(ref_disp, tuple) and len(ref_disp) == 3
    assert ref_disp[0].shape == (8, 4096) and ref_disp[0].dtype == _DT_BF16
    mc2_ex.launch(gmm_node, upstream=[ref_disp])
    gmm_calls = [c for c in mc2_torch.calls if c[0] == "npu_grouped_matmul"]
    assert gmm_calls and gmm_calls[-1][1][0][0] is ref_disp[0]
    dispatch_mode[0] = "tail_only"
    tail_disp = mc2_ex.launch(disp_node)
    assert subgraph_runtime._same_outputs(ref_disp, tail_disp, mc2_torch) is True
    dispatch_mode[0] = "perturb_active"
    bad_disp = mc2_ex.launch(disp_node)
    assert subgraph_runtime._same_outputs(ref_disp, bad_disp, mc2_torch) is False

    # #12: Byte-only quantized_all_reduce, native p2p_send_recv, and mc2_dispatch match payload bytes or fail closed.
    torch = _StubTorch()
    for builder, op_name in (("quantized_all_reduce", "npu_quant_all_reduce"), ("p2p_send_recv", "npu_p2p_send_recv")):
        torch.calls.clear()
        b_ctx = _make_context(torch, arch="A5", group_size=2)
        b_ctx["_actual_shape"] = {}
        ops.build_operator_enqueue(
            torch,
            {"builder": builder, "dtype": "int8", "shape": {"bytes": 65536, "group_size": 2}},
            b_ctx,
        )()
        _n, b_args, _kw = [c for c in torch.calls if c[0] == op_name][-1]
        assert b_args[0].numel() * b_args[0].dtype.nbytes == 65536
        assert b_ctx["_actual_shape"]["bytes"] == 65536
        with pytest.raises(ProfilerUsageError, match="bench_collective_bytes_unrepresentable"):
            ops.build_operator_enqueue(
                torch, {"builder": builder, "dtype": "bf16", "shape": {"bytes": 3, "group_size": 2}}, b_ctx
            )

    torch.calls.clear()
    mc2_b_ctx = _make_context(torch, arch="A5", group_size=2)
    mc2_b_ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {"builder": "mc2_dispatch", "dtype": "bf16", "shape": {"bytes": 2048, "group_size": 2}},
        mc2_b_ctx,
    )()
    _n, _a, d_kw = [c for c in torch.calls if c[0] == "npu_moe_distribute_dispatch_v2"][-1]
    assert d_kw["x"].numel() * d_kw["x"].dtype.nbytes == 2048
    assert mc2_b_ctx["_actual_shape"]["bytes"] == 2048
    with pytest.raises(ProfilerUsageError, match="bench_mc2_bytes_unrepresentable"):
        ops.build_operator_enqueue(
            torch,
            {"builder": "mc2_dispatch", "dtype": "bf16",
             "strides": {"input": [4096, 1]}, "shape": {"bytes": 2048, "group_size": 2}},
            mc2_b_ctx,
        )

    # #13: INT8 mc2_combine binds comm_quant_mode=2 on v2, rejects legacy v1 / unsupported FP8 combine.
    torch.calls.clear()
    c_int8_ctx = _make_context(torch, arch="A3", group_size=4)
    c_int8_ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {"builder": "mc2_combine", "dtype": "int8", "group": "ep", "group_ranks": [0, 1, 2, 3],
         "shape": {"tokens": 8, "width": 4096, "group_size": 4}},
        c_int8_ctx,
    )()
    _n, _a, c_kw = [c for c in torch.calls if c[0] == "npu_moe_distribute_combine_v2"][-1]
    assert c_kw["comm_quant_mode"] == 2
    assert c_int8_ctx["_actual_shape"]["bytes"] == 32768
    assert c_int8_ctx["_actual_shape"]["comm_quant_mode"] == 2
    with pytest.raises(BenchUnmodeledOperatorError):
        ops.build_operator_enqueue(
            torch,
            {"builder": "mc2_combine", "dtype": "fp8_e4m3",
             "shape": {"tokens": 8, "width": 4096, "group_size": 4}},
            _make_context(torch, arch="A5", group_size=4),
        )
    v1_torch = _StubTorch()
    v1_npu = types.SimpleNamespace(
        synchronize=lambda: None,
        npu_moe_distribute_combine=lambda **k: k["expand_x"],
    )
    v1_npu.npu_moe_distribute_combine.__name__ = "npu_moe_distribute_combine"
    v1_torch.npu = v1_npu
    v1_torch.ops = types.SimpleNamespace(npu=v1_npu)
    with pytest.raises(BenchUnmodeledOperatorError):
        ops.build_operator_enqueue(
            v1_torch,
            {"builder": "mc2_combine", "dtype": "int8", "shape": {"tokens": 8, "width": 4096}},
            {"torch_npu": v1_npu, "device": {"ordinal": 0}, "soc_arch": "A3"},
        )

    # #14: incre_flash_attention uneven tokens (3 across 2 seqs) & fusion_attention causal batched pairs (2x2 -> 6).
    torch.calls.clear()
    ifa_ctx = _make_context(torch, arch="A5")
    ifa_ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {"builder": "incre_flash_attention", "dtype": "bf16",
         "shape": {"tokens": 3, "sequences": 2, "heads": 4, "kv_heads": 1, "head_dim": 128, "kv_len": 10}},
        ifa_ctx,
    )()
    _n, ifa_args, ifa_kw = [c for c in torch.calls if c[0] == "npu_fused_infer_attention_score"][-1]
    assert ifa_args[0].shape == (2, 2, 512)
    assert ifa_kw["actual_seq_lengths"] == [2, 1] and sum(ifa_kw["actual_seq_lengths"]) == 3
    assert ifa_kw["actual_seq_lengths_kv"] == [5, 5]
    assert ifa_ctx["_actual_shape"]["q_len"] == 2 and ifa_ctx["_actual_shape"]["actual_seq_lengths"] == [2, 1]

    torch.calls.clear()
    fa_ctx = _make_context(torch, arch="A5")
    fa_ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {"builder": "fusion_attention", "dtype": "bf16", "causal": True,
         "shape": {"tokens": 4, "sequences": 2, "heads": 4, "kv_heads": 1, "head_dim": 128, "seq_len": 4}},
        fa_ctx,
    )()
    _n, _fa_a, fa_kw = [c for c in torch.calls if c[0] == "npu_fusion_attention"][-1]
    assert fa_kw["actual_seq_qlen"] == [2, 4] and fa_kw["actual_seq_kvlen"] == [2, 4]
    assert fa_ctx["_actual_shape"]["query_key_pairs"] == 6

    # #15: recurrent_gated_delta_rule honors tokens=8, sequences=2, q_len=4 without state_len & rejects inconsistent shapes.
    torch.calls.clear()
    rec_ctx = _make_context(torch, arch="A5")
    rec_ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {"builder": "recurrent_gated_delta_rule", "dtype": "bf16",
         "shape": {"tokens": 8, "sequences": 2, "q_len": 4, "heads": 8, "head_dim": 128}},
        rec_ctx,
    )()
    _n, _r_args, r_kw = [c for c in torch.calls if c[0] == "npu_recurrent_gated_delta_rule"][-1]
    assert r_kw["actual_seq_lengths"].values == [4, 4]
    assert r_kw["ssm_state_indices"].values == [0, 1, 2, 3, 4, 5, 6, 7]
    assert r_kw["num_accepted_tokens"].values == [1, 1]
    assert shape_evidence_problem(
        {"tokens": 8, "sequences": 2, "q_len": 4, "heads": 8, "head_dim": 128}, rec_ctx["_actual_shape"]
    ) is None
    with pytest.raises(ProfilerUsageError, match="bench_recurrent_state_shape_invalid"):
        ops.build_operator_enqueue(
            torch,
            {"builder": "recurrent_gated_delta_rule", "dtype": "bf16",
             "shape": {"tokens": 8, "sequences": 3, "q_len": 4, "heads": 8, "head_dim": 128}},
            rec_ctx,
        )

    # #16: mixed_quant_sparse_mla rejects INT8 KV on BF16-only npu_sparse_flash_mla & certifies BF16 honestly.
    smla_torch = _StubTorch()
    smla_npu = types.SimpleNamespace(synchronize=lambda: None)
    smla_calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _smla_only(*a: Any, **k: Any) -> Any:
        smla_calls.append(("npu_sparse_flash_mla", a, k))
        return a[0]

    _smla_only.__name__ = "npu_sparse_flash_mla"
    smla_torch.npu = smla_npu
    smla_torch.ops = types.SimpleNamespace(
        npu=smla_npu,
        _C_ascend=types.SimpleNamespace(npu_sparse_flash_mla=_smla_only),
        cann_ops_transformer=types.SimpleNamespace(),
    )
    smla_base_ctx = {"torch_npu": smla_npu, "device": {"ordinal": 0}, "soc_arch": "A5", "extra_modules": {}}
    smla_shape = {"tokens": 8, "sequences": 4, "q_len": 2, "heads": 8, "kv_heads": 1, "head_dim": 512, "kv_len": 1024}
    with pytest.raises(BenchUnmodeledOperatorError):
        ops.build_operator_enqueue(
            smla_torch,
            {"builder": "mixed_quant_sparse_mla", "dtype": "bf16", "kv_dtype": "int8", "shape": smla_shape},
            {**smla_base_ctx, "_actual_shape": {}},
        )
    bf16_smla_ctx = {**smla_base_ctx, "_actual_shape": {}}
    ops.build_operator_enqueue(
        smla_torch,
        {"builder": "mixed_quant_sparse_mla", "dtype": "bf16", "shape": smla_shape},
        bf16_smla_ctx,
    )()
    assert bf16_smla_ctx["_actual_shape"]["kv_dtype"] == "bf16"
    assert bf16_smla_ctx["_actual_shape"]["kv_bytes_per_token"] == 1152
    assert "scale_dtype" not in bf16_smla_ctx["_actual_shape"]

    # #17: dynamic_quant binds explicit dst_type=hifloat8 when supported, rejects hif8 when unavailable.
    dq_torch = _StubTorch()
    dq_ctx = _make_context(dq_torch, arch="A5")
    with pytest.raises(BenchUnmodeledOperatorError) as hif_exc:
        ops.build_operator_enqueue(
            dq_torch, {"builder": "dynamic_quant", "dtype": "hif8", "shape": {"tokens": 8, "width": 128}}, dq_ctx
        )
    assert hif_exc.value.payload["reason"] == "missing_native_dtype:hifloat8"
    hif8_dt = _Dtype("hifloat8", 1, is_floating_point=True)
    dq_ctx["torch_npu"].hifloat8 = hif8_dt
    dq_torch.calls.clear()
    ops.build_operator_enqueue(
        dq_torch, {"builder": "dynamic_quant", "dtype": "hif8", "shape": {"tokens": 8, "width": 128}}, dq_ctx
    )()
    _n, hif_args, hif_kw = [c for c in dq_torch.calls if c[0] == "npu_dynamic_quant"][-1]
    assert hif_args[0].dtype == _DT_BF16 and hif_kw["dst_type"] == hif8_dt

    # #18: quant_matmul binds explicit int8 output_dtype (1024 B) and rejects unsupported output_dtype cleanly.
    qm_ctx = _make_context(torch, arch="A5")
    qm_ctx["_actual_shape"] = {}
    torch.calls.clear()
    ops.build_operator_enqueue(
        torch,
        {"builder": "quant_matmul", "dtype": "int8", "output_dtype": "int8",
         "shape": {"m": 16, "n": 64, "k": 128}},
        qm_ctx,
    )()
    _n, _qa, q_kw = [c for c in torch.calls if c[0] == "npu_quant_matmul"][-1]
    assert q_kw["output_dtype"] == _DT_INT8
    assert qm_ctx["_actual_shape"]["output_dtype"] == "int8"
    assert qm_ctx["_actual_shape"]["output_bytes"] == 1024
    with pytest.raises(ProfilerUsageError, match="bench_quant_matmul_output_dtype_unsupported"):
        ops.build_operator_enqueue(
            torch,
            {"builder": "quant_matmul", "dtype": "int8", "output_dtype": "fp32",
             "shape": {"m": 16, "n": 64, "k": 128}},
            qm_ctx,
        )


def test_add_rms_norm_quant_width_scales_and_executor_soc_arch() -> None:
    """Lock live A3/A5 CANN ABI for add_rms_norm_quant, A5/A3 rms_norm_quant, and soc_arch propagation."""
    from mindie_profiler.bench.subgraph_runtime import OperatorExecutor

    torch = _StubTorch()
    ctx = _make_context(torch, arch="A5")
    ctx["_actual_shape"] = {}
    torch.calls.clear()
    ops.build_operator_enqueue(
        torch,
        {"builder": "add_rms_norm_quant", "dtype": "bf16", "shape": {"tokens": 8, "width": 6144}},
        ctx,
    )()
    _name, args, _kw = [c for c in torch.calls if c[0] == "npu_add_rms_norm_quant"][-1]
    assert args[3].shape == (6144,) and args[3].dtype == _DT_FP32
    assert args[4].shape == (6144,) and args[4].dtype == _DT_INT32

    torch.calls.clear()
    ops.build_operator_enqueue(
        torch,
        {"builder": "rms_norm_quant", "dtype": "bf16", "shape": {"tokens": 8, "width": 512}},
        ctx,
    )()
    _name, r_args, _r_kw = [c for c in torch.calls if c[0] == "npu_rms_norm_quant"][-1]
    assert r_args[3].dtype == _DT_FP32 and r_args[4].dtype == _DT_INT32

    a3_calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
    a3_npu = types.SimpleNamespace(
        synchronize=lambda: None,
        npu_rms_norm_quant=lambda *a, **k: (a3_calls.append(("npu_rms_norm_quant", a, k)), a[0])[1],
    )
    a3_npu.npu_rms_norm_quant.__name__ = "npu_rms_norm_quant"
    a3_torch = _StubTorch()
    a3_torch.npu = a3_npu
    a3_torch.ops = types.SimpleNamespace(npu=a3_npu)
    ops.build_operator_enqueue(
        a3_torch,
        {"builder": "rms_norm_quant", "dtype": "bf16", "shape": {"tokens": 8, "width": 512}},
        {"torch_npu": a3_npu, "device": {"ordinal": 0}, "soc_arch": "A3"},
    )()
    assert a3_calls[-1][1][3].dtype == _DT_FP32 and a3_calls[-1][1][4].dtype == _DT_INT8

    bare_ctx: dict[str, Any] = {"torch_npu": torch.npu, "device": {"ordinal": 0}}
    ex = OperatorExecutor(torch, bare_ctx)
    ex.begin_case({"case_id": "k2-a5", "sku": "Ascend950DT_9582", "nodes": []})
    assert bare_ctx.get("soc_arch") == "A5"
    ex.begin_case({"case_id": "k2-a3", "canonical_key": {"soc_arch": "A3"}, "nodes": []})
    assert bare_ctx.get("soc_arch") == "A3"
    ex.begin_case({"case_id": "k2-unknown-fallback", "soc_arch": "unknown", "canonical_key": {"sku": "Ascend950DT_9582"}, "nodes": []})
    assert bare_ctx.get("soc_arch") == "A5"
    ex.begin_case({"case_id": "k2-preserve", "nodes": []})
    assert bare_ctx.get("soc_arch") == "A5"

