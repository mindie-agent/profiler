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

from mindie_profiler.bench import campaign_runner, operators as ops, subgraph_runtime
from mindie_profiler.bench.operators_common import (
    cast_weight_nz,
    materialize_contiguous_zero_offset,
    randn as common_randn,
    shape_evidence_problem,
    shape_of,
)

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

    # quant_matmul on A5 FP8 and INT8 sanitizes output_dtype to bf16
    for dt_name, expected_in in (("int8", _DT_INT8), ("fp8_e4m3", _DT_FP8_E4M3)):
        torch.calls.clear()
        case = {
            "builder": "quant_matmul", "dtype": dt_name, "output_dtype": dt_name,
            "shape": {"m": 16, "n": 64, "k": 128},
        }
        ops.build_operator_enqueue(torch, case, ctx)()
        mm_calls = [c for c in torch.calls if c[0] == "npu_quant_matmul"]
        assert mm_calls
        _n, mm_args, mm_kw = mm_calls[-1]
        assert mm_args[0].dtype == expected_in
        assert mm_kw["output_dtype"] == _DT_BF16


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
        for dt_name in ("mxfp4", "w4a8"):
            torch.calls.clear()
            case = {"builder": builder, "dtype": dt_name, "shape": shape}
            ops.build_operator_enqueue(torch, case, ctx)()
            pack_calls = [c for c in torch.calls if c[0] == "npu_convert_weight_to_int4pack"]
            assert pack_calls, (builder, dt_name)
            for _name, args, _kw in pack_calls:
                assert args[0].dtype == _DT_INT32
                assert args[0].storage_offset() == 0
                assert args[0].is_contiguous()


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
