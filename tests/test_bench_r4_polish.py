"""Regression tests for Round-4 Astra #9..#18 profiler bench polish fixes.

[Role]
  Verify all ten Round-4 Astra closure items (#9..#18) covering dual-die clock
  disambiguation without ``npu-smi info -m``, INT8 MC2 dispatch scale checks,
  FP8 P2P byte sizing, ABI-valid MC2 byte-only width selection, A2 INT8 MC2
  ``comm_alg`` forwarding, multi-query causal FIA masking, distinct per-token
  recurrent GDN state slots, native GDN sequence-length limit enforcement,
  ``cann_ops_transformer.mixed_quant_sparse_flash_mla`` 608-byte packed KV
  binding, and W4A8 output-dtype validation.

[Invariants]
  * Pure CPU in-memory execution with lightweight fake torch/NPU handles; zero
    live NPU contexts or external subprocesses.
  * Every item reproduces the exact Round-4 Astra counterexample geometry.

[Timeouts & Locks]
  Runs in < 1 s with no sleeps, locks, threads, or network calls.

[Side-Effect Policy]
  Allocates only in-memory Python test doubles; writes no files.
"""

from __future__ import annotations

import types
from typing import Any

import pytest

from mindie_profiler.bench import (
    BenchUnmodeledOperatorError,
    env_fingerprint,
    operators as ops,
    subgraph_runtime,
    timing,
)
from mindie_profiler.bench.operators_common import shape_evidence_problem
from mindie_profiler.events import ProfilerUsageError
from tests.test_bench_builder_silicon_fixes import (
    _DT_BF16,
    _DT_FP16,
    _DT_FP32,
    _DT_FP8_E4M3,
    _DT_INT8,
    _DT_INT32,
    _DT_UINT8,
    _StubTensor,
    _StubTorch,
    _make_context,
)


class _RowTensor(_StubTensor):
    """Stub tensor supporting 1D/2D dim-0 narrowing and deep value cloning."""

    def narrow(self, dim: int, start: int, length: int) -> "_RowTensor":
        assert dim == 0
        sliced = (
            [list(r) if isinstance(r, list) else r for r in self.values[start:start + length]]
            if isinstance(self.values, list)
            else self.values
        )
        return _RowTensor((length, *self.shape[1:]), dtype=self.dtype, device=self.device, values=sliced)

    def clone(self) -> "_RowTensor":
        if isinstance(self.values, list):
            copied = [list(r) if isinstance(r, list) else r for r in self.values]
        else:
            copied = self.values
        return _RowTensor(self.shape, dtype=self.dtype, device=self.device, values=copied)


def test_r4_09_clock_probe_rejects_ambiguous_multichip_without_mapping(monkeypatch) -> None:
    """#9: Never certify chip 0's 1650 MHz for target chip 1 at 800 MHz when info -m has no mapping."""
    dual_die_out = "\n".join([
        "NPU ID : 7",
        "Chip Count : 2",
        "Chip ID : 0",
        "Aicore Freq(MHZ) : 1650",
        "Aicore curFreq(MHZ) : 1650",
        "Chip ID : 1",
        "Aicore Freq(MHZ) : 1650",
        "Aicore curFreq(MHZ) : 800",
    ])
    monkeypatch.setattr(
        env_fingerprint, "_bounded_run",
        lambda cmd, *, cwd=None: None if tuple(cmd) == ("npu-smi", "info", "-m") else dual_die_out,
    )
    obs_mhz, obs_src = env_fingerprint.probe_observed_clock(
        physical_id=15, allow_npu_smi=True, device_properties={"clock_mhz": 1650.0},
    )
    assert obs_src == "device_properties_nominal_mhz"
    assert not env_fingerprint.is_live_clock_source(obs_src)
    assert env_fingerprint.probe_observed_clock(physical_id=15, allow_npu_smi=True) == (None, "unavailable")

    # Single unambiguous Chip ID block still certifies live curFreq without info -m.
    single_die_out = "\n".join([
        "NPU ID : 3",
        "Chip ID : 0",
        "Aicore Freq(MHZ) : 1650",
        "Aicore curFreq(MHZ) : 1620",
    ])
    monkeypatch.setattr(
        env_fingerprint, "_bounded_run",
        lambda cmd, *, cwd=None: None if tuple(cmd) == ("npu-smi", "info", "-m") else single_die_out,
    )
    assert env_fingerprint.probe_observed_clock(physical_id=3, allow_npu_smi=True) == (
        1620.0, "npu-smi_cur_freq_mhz"
    )


def test_r4_10_int8_mc2_dispatch_checks_active_dynamic_scales_and_keeps_data_edge() -> None:
    """#10: INT8 mc2_dispatch preserves expand_x as primary edge and checks dynamic_scales[:valid_rows]."""
    mc2_torch = _StubTorch()
    mc2_torch.allclose = lambda a, b, **_k: a.shape == b.shape and a.dtype == b.dtype and a.values == b.values
    mode = ["scale_1"]

    def _fake_dispatch_v2(**kw: Any) -> tuple[Any, ...]:
        tok, hid = kw["x"].shape
        active_x = [[64] * 4 for _ in range(tok)]
        tail_x = [[99 if mode[0] == "scale_1" else -99] * 4 for _ in range(tok)]
        expand_x = _RowTensor((tok * 2, hid), dtype=_DT_INT8, values=active_x + tail_x)
        active_scale = [2.0 if mode[0] == "scale_2" else 1.0 for _ in range(tok)]
        tail_scale = [77.0 if mode[0] == "scale_1" else -77.0 for _ in range(tok)]
        dyn_scales = _RowTensor((tok * 2,), dtype=_DT_FP32, values=active_scale + tail_scale)
        nums = _RowTensor((4,), dtype=_DT_INT32, values=[2, 2, 2, 2])
        ep_cnt = _RowTensor((4,), dtype=_DT_INT32, values=[2, 4, 6, 8])
        dummy = _RowTensor((tok,), dtype=_DT_INT32, values=[0] * tok)
        return (expand_x, dyn_scales, dummy, nums, ep_cnt, dummy, dummy)

    mc2_ctx = _make_context(mc2_torch, arch="A3", group_size=4)
    mc2_ctx["op_overrides"] = {"npu_moe_distribute_dispatch_v2": _fake_dispatch_v2}
    mc2_ex = subgraph_runtime.OperatorExecutor(mc2_torch, mc2_ctx)
    disp_node = {
        "node_id": "n_disp", "builder": "mc2_dispatch", "dtype": "int8",
        "group": "ep", "group_ranks": [0, 1, 2, 3],
        "shape": {"tokens": 8, "width": 4096, "e": 4, "top_k": 1, "group_size": 4},
    }
    gmm_node = {
        "node_id": "n_gmm", "builder": "grouped_matmul", "dtype": "int8",
        "shape": {"m": 8, "n": 256, "k": 4096, "e": 4},
    }
    mc2_ex.begin_case({"case_id": "c_mc2_int8_sub", "nodes": [disp_node, gmm_node]})
    ref = mc2_ex.launch(disp_node)
    assert isinstance(ref, tuple) and len(ref) == 4
    assert ref[0].shape == (8, 4096) and ref[0].dtype == _DT_INT8
    assert ref[1].shape == (8,) and ref[1].values == [1.0] * 8

    # Downstream grouped_matmul still binds expand_x (element 0) as its primary data edge.
    mc2_ex.launch(gmm_node, upstream=[ref])
    gmm_calls = [c for c in mc2_torch.calls if c[0] == "npu_grouped_matmul"]
    assert gmm_calls and gmm_calls[-1][1][0][0] is ref[0]

    # Tail-only changes in both expand_x and dynamic_scales still compare equal.
    mode[0] = "tail_only"
    tail_out = mc2_ex.launch(disp_node)
    assert subgraph_runtime._same_outputs(ref, tail_out, mc2_torch) is True

    # Identical code=64 & counts with active scales 1.0 vs 2.0 must NOT compare equal.
    mode[0] = "scale_2"
    diff_scale_out = mc2_ex.launch(disp_node)
    assert subgraph_runtime._same_outputs(ref, diff_scale_out, mc2_torch) is False


def test_r4_11_fp8_p2p_send_recv_uses_real_1_byte_element_width() -> None:
    """#11: On A5, dtype='fp8' bytes=65536 binds [512, 128] float8_e4m3fn (65,536 B) honestly."""
    torch = _StubTorch()
    ctx = _make_context(torch, arch="A5", group_size=2)
    ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {"builder": "p2p_send_recv", "dtype": "fp8", "shape": {"bytes": 65536, "group_size": 2}},
        ctx,
    )()
    _n, args, _kw = [c for c in torch.calls if c[0] == "npu_p2p_send_recv"][-1]
    buf = args[0]
    assert buf.shape == (512, 128)
    assert buf.dtype == _DT_FP8_E4M3
    assert buf.numel() * buf.dtype.nbytes == 65536
    assert ctx["_actual_shape"]["bytes"] == 65536
    assert ctx["_actual_shape"]["tokens"] == 512 and ctx["_actual_shape"]["width"] == 128


def test_r4_12_mc2_dispatch_byte_only_selects_abi_valid_width() -> None:
    """#12: Byte-only mc2_dispatch selects width inside [1024, 8192] ([1, 1280] for 2560 B BF16)."""
    torch = _StubTorch()
    ctx = _make_context(torch, arch="A5", group_size=2)
    ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {"builder": "mc2_dispatch", "dtype": "bf16", "shape": {"bytes": 2560, "group_size": 2}},
        ctx,
    )()
    _n, _a, kw = [c for c in torch.calls if c[0] == "npu_moe_distribute_dispatch_v2"][-1]
    assert kw["x"].shape == (1, 1280)
    assert kw["x"].numel() * kw["x"].dtype.nbytes == 2560
    assert ctx["_actual_shape"]["tokens"] == 1 and ctx["_actual_shape"]["width"] == 1280
    assert ctx["_actual_shape"]["bytes"] == 2560

    # Non-candidate aligned width inside [1024, 8192] (2304 B BF16 -> [1, 1152]) also resolves cleanly.
    torch.calls.clear()
    ctx2 = _make_context(torch, arch="A5", group_size=2)
    ops.build_operator_enqueue(
        torch,
        {"builder": "mc2_dispatch", "dtype": "bf16", "shape": {"bytes": 2304, "group_size": 2}},
        ctx2,
    )()
    _n, _a, kw2 = [c for c in torch.calls if c[0] == "npu_moe_distribute_dispatch_v2"][-1]
    assert kw2["x"].shape == (1, 1152)

    # Sub-1024 elements (1024 B BF16 = 512 elements) cannot form an ABI-valid [1024, 8192] width.
    with pytest.raises(ProfilerUsageError, match="bench_mc2_bytes_unrepresentable"):
        ops.build_operator_enqueue(
            torch,
            {"builder": "mc2_dispatch", "dtype": "bf16", "shape": {"bytes": 1024, "group_size": 2}},
            ctx,
        )


def test_r4_13_a2_int8_mc2_combine_forwards_comm_alg_to_setup_dispatch_and_combine() -> None:
    """#13: Forward comm_alg='hierarchy' to BOTH setup dispatch and combine on A2 INT8 EP16."""
    torch = _StubTorch()
    ctx = _make_context(torch, arch="A2", group_size=16)
    ctx["_actual_shape"] = {}
    ranks = list(range(16))
    ctx["groups"] = {
        "ep": ctx["groups"]["ep"],
        "ep:16": ctx["groups"]["ep"],
        f"ep@{','.join(str(r) for r in ranks)}": ctx["groups"]["ep"],
    }
    ops.build_operator_enqueue(
        torch,
        {
            "builder": "mc2_combine",
            "dtype": "int8",
            "comm_alg": "hierarchy",
            "group": "ep",
            "group_ranks": ranks,
            "shape": {"tokens": 8, "width": 4096, "e": 16, "group_size": 16},
        },
        ctx,
    )()
    setup_disp = [c for c in torch.calls if c[0] == "npu_moe_distribute_dispatch_v2"][-1][2]
    comb_kw = [c for c in torch.calls if c[0] == "npu_moe_distribute_combine_v2"][-1][2]
    assert setup_disp["comm_alg"] == "hierarchy"
    assert comb_kw["comm_alg"] == "hierarchy"
    assert comb_kw["comm_quant_mode"] == 2
    assert ctx["_actual_shape"]["comm_alg"] == "hierarchy"
    assert ctx["_actual_shape"]["comm_quant_mode"] == 2


def test_r4_14_multi_query_causal_incre_flash_attention_binds_right_aligned_mask() -> None:
    """#14: Multi-query causal incre_flash_attention binds right-aligned mask & sparse_mode=3 (14 pairs)."""
    torch = _StubTorch()
    triu_diagonals: list[int] = []

    class _TrackingTensor(_StubTensor):
        def triu_(self, *a: Any, **k: Any) -> "_TrackingTensor":
            triu_diagonals.append(int(k.get("diagonal", a[0] if a else 0)))
            return self

        def to(self, *args: Any, **kwargs: Any) -> "_TrackingTensor":
            base = super().to(*args, **kwargs)
            return _TrackingTensor(base.shape, dtype=base.dtype, device=base.device)

    orig_ones = torch.ones

    def _ones(*dims: int, dtype: Any = None, device: str = "npu:0") -> _StubTensor:
        t = orig_ones(*dims, dtype=dtype, device=device)
        return _TrackingTensor(t.shape, dtype=t.dtype, device=t.device)

    torch.ones = _ones
    ctx = _make_context(torch, arch="A5")
    ctx["_actual_shape"] = {}
    case = {
        "builder": "incre_flash_attention",
        "dtype": "bf16",
        "causal": True,
        "shape": {"tokens": 3, "sequences": 2, "heads": 4, "kv_heads": 1, "head_dim": 128, "kv_len": 10},
    }
    ops.build_operator_enqueue(torch, case, ctx)()
    _n, args, kw = [c for c in torch.calls if c[0] == "npu_fused_infer_attention_score"][-1]
    assert args[0].shape == (2, 2, 512)
    assert kw["actual_seq_lengths"] == [2, 1]
    assert kw["actual_seq_lengths_kv"] == [5, 5]
    assert kw["sparse_mode"] == 3
    assert kw["atten_mask"].shape == (2048, 2048)
    assert kw["atten_mask"].dtype == _DT_UINT8
    assert triu_diagonals == [1]
    assert ctx["_actual_shape"]["sparse_mode"] == 3
    assert ctx["_actual_shape"]["query_key_pairs"] == 14
    assert timing.estimate_working_set_bytes(case) >= 2048 * 2048


def test_r4_15_and_16_recurrent_gdn_distinct_slots_and_max_seq_len_8_guard() -> None:
    """#15 & #16: Distinct ssm_state_indices per token and native 1..8 sequence-length limit."""
    torch = _StubTorch()
    ctx = _make_context(torch, arch="A5")
    ctx["_actual_shape"] = {}

    # #15: Two 4-token chains get 8 distinct state slots [0..7] so recovery snapshots aren't overwritten.
    ops.build_operator_enqueue(
        torch,
        {
            "builder": "recurrent_gated_delta_rule",
            "dtype": "bf16",
            "shape": {"tokens": 8, "sequences": 2, "q_len": 4, "heads": 8, "head_dim": 128},
        },
        ctx,
    )()
    _n, r_args, r_kw = [c for c in torch.calls if c[0] == "npu_recurrent_gated_delta_rule"][-1]
    assert r_kw["actual_seq_lengths"].values == [4, 4]
    assert r_kw["ssm_state_indices"].values == [0, 1, 2, 3, 4, 5, 6, 7]
    assert len(set(r_kw["ssm_state_indices"].values)) == 8
    assert r_args[3].shape[0] == 8
    assert r_kw["num_accepted_tokens"].values == [1, 1]

    # #16a: Length 8 is allowed on native npu_recurrent_gated_delta_rule.
    torch.calls.clear()
    ops.build_operator_enqueue(
        torch,
        {
            "builder": "recurrent_gated_delta_rule",
            "dtype": "bf16",
            "shape": {"tokens": 8, "sequences": 1, "heads": 8, "head_dim": 128},
        },
        _make_context(torch, arch="A5"),
    )()
    assert [c for c in torch.calls if c[0] == "npu_recurrent_gated_delta_rule"][-1][2]["actual_seq_lengths"].values == [8]

    # #16b: Length 9 rejects cleanly before enqueueing when only native npu_recurrent_gated_delta_rule is installed.
    native_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def _native_only_gdn(*a: Any, **k: Any) -> Any:
        native_calls.append((a, k))
        return a[0]

    _native_only_gdn.__name__ = "npu_recurrent_gated_delta_rule"
    native_torch = _StubTorch()
    native_npu = types.SimpleNamespace(
        synchronize=lambda: None,
        npu_recurrent_gated_delta_rule=_native_only_gdn,
    )
    native_torch.npu = native_npu
    native_torch.ops = types.SimpleNamespace(npu=native_npu)
    no_fla_ctx = {
        "torch_npu": native_npu,
        "device": {"ordinal": 0},
        "soc_arch": "A5",
        "extra_modules": {"fla.ops.gated_delta_rule": None},
    }
    with pytest.raises(BenchUnmodeledOperatorError) as exc:
        ops.build_operator_enqueue(
            native_torch,
            {
                "builder": "recurrent_gated_delta_rule",
                "dtype": "bf16",
                "shape": {"tokens": 9, "sequences": 1, "heads": 8, "head_dim": 128},
            },
            no_fla_ctx,
        )
    assert "recurrent_gdn_seq_len_exceeds_native_limit:9>8" in exc.value.payload["reason"]
    assert native_calls == []

    # #16c: Indexed recurrent path also enforces the 1..8 limit when q_len=9 (without FLA).
    with pytest.raises(BenchUnmodeledOperatorError):
        ops.build_operator_enqueue(
            native_torch,
            {
                "builder": "recurrent_gated_delta_rule",
                "dtype": "bf16",
                "shape": {"tokens": 9, "sequences": 1, "q_len": 9, "state_len": 16, "heads": 8, "head_dim": 128},
            },
            no_fla_ctx,
        )
    assert native_calls == []

    # #16d: When uncapped fla.ops.gated_delta_rule.fused_recurrent_gated_delta_rule is installed,
    # length 9 routes cleanly to it instead of native npu_recurrent_gated_delta_rule,
    # whereas explicitly pinning op='npu_recurrent_gated_delta_rule' still rejects length 9.
    fla_calls: list[dict[str, Any]] = []

    def _fla_rec(**kw: Any) -> Any:
        fla_calls.append(kw)
        return kw["q"]

    fla_ctx = {
        "torch_npu": native_npu,
        "device": {"ordinal": 0},
        "soc_arch": "A5",
        "extra_modules": {
            "fla.ops.gated_delta_rule": types.SimpleNamespace(fused_recurrent_gated_delta_rule=_fla_rec)
        },
    }
    with pytest.raises(BenchUnmodeledOperatorError):
        ops.build_operator_enqueue(
            native_torch,
            {
                "builder": "recurrent_gated_delta_rule",
                "op": "npu_recurrent_gated_delta_rule",
                "dtype": "bf16",
                "shape": {"tokens": 9, "sequences": 1, "heads": 8, "head_dim": 128},
            },
            fla_ctx,
        )
    ops.build_operator_enqueue(
        native_torch,
        {
            "builder": "recurrent_gated_delta_rule",
            "dtype": "bf16",
            "shape": {"tokens": 9, "sequences": 1, "heads": 8, "head_dim": 128},
        },
        fla_ctx,
    )()
    assert native_calls == []
    assert len(fla_calls) == 1
    assert fla_calls[0]["cu_seqlens"].values == [0, 9]
    assert fla_calls[0]["ssm_state_indices"].values == [[0, 1, 2, 3, 4, 5, 6, 7, 8]]


def test_r4_17_mixed_quant_sparse_mla_resolves_cann_ops_transformer_and_608b_record() -> None:
    """#17: Resolve cann_ops_transformer.mixed_quant_sparse_flash_mla before npu_sparse_flash_mla & bind 608B KV."""
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _rec(tag: str):
        def _fn(*a: Any, **k: Any) -> Any:
            calls.append((tag, a, k))
            return a[0] if a else _StubTensor((1024,), dtype=_DT_INT32)
        _fn.__name__ = tag
        return _fn

    torch = _StubTorch()
    npu_ns = types.SimpleNamespace(synchronize=lambda: None)
    torch.npu = npu_ns
    torch.ops = types.SimpleNamespace(
        npu=npu_ns,
        _C_ascend=types.SimpleNamespace(npu_sparse_flash_mla=_rec("npu_sparse_flash_mla")),
        cann_ops_transformer=types.SimpleNamespace(
            mixed_quant_sparse_flash_mla=_rec("mixed_quant_sparse_flash_mla"),
            mixed_quant_sparse_flash_mla_metadata=_rec("mixed_quant_sparse_flash_mla_metadata"),
        ),
    )
    ctx: dict[str, Any] = {
        "torch_npu": npu_ns,
        "device": {"ordinal": 0},
        "soc_arch": "A3",
        "extra_modules": {},
        "_actual_shape": {},
    }
    shape = {
        "tokens": 8,
        "sequences": 4,
        "q_len": 2,
        "heads": 8,
        "kv_heads": 1,
        "head_dim": 448,
        "qk_rope_head_dim": 64,
        "kv_len": 1024,
    }
    ops.build_operator_enqueue(
        torch,
        {"builder": "mixed_quant_sparse_mla", "dtype": "bf16", "kv_dtype": "int8", "shape": shape},
        ctx,
    )()
    assert not [c for c in calls if c[0] == "npu_sparse_flash_mla"]
    assert [c for c in calls if c[0] == "mixed_quant_sparse_flash_mla_metadata"]
    _tag, mq_args, mq_kw = [c for c in calls if c[0] == "mixed_quant_sparse_flash_mla"][-1]
    assert mq_args[0].shape == (8, 8, 512) and mq_args[0].dtype == _DT_BF16
    assert mq_kw["ori_kv"].shape[-2:] == (1, 608)
    assert mq_kw["ori_kv"].dtype == _DT_INT8
    assert mq_kw["quant_mode"] == 1
    assert mq_kw["rope_head_dim"] == 64
    assert mq_kw["layout_q"] == "TND" and mq_kw["layout_kv"] == "PA_BBND"
    assert mq_kw["sinks"].shape == (8,) and mq_kw["sinks"].dtype == _DT_FP32
    assert ctx["_actual_shape"]["kv_dtype"] == "int8"
    assert ctx["_actual_shape"]["kv_bytes_per_token"] == 608
    assert ctx["_actual_shape"]["ori_kv_record_bytes"] == 608
    assert shape_evidence_problem(shape, ctx["_actual_shape"]) is None


def test_r4_18_w4a8_quant_matmul_validates_output_dtype_before_enqueueing() -> None:
    """#18: W4A8 quant_matmul rejects unsupported output_dtype='int8' and honors valid 'fp16'."""
    torch = _StubTorch()
    ctx = _make_context(torch, arch="A3")

    # Unsupported output_dtype='int8' on W4A8 must fail BEFORE any kernel call (quant_route & wq_route).
    for extra in ({"op": "npu_quant_matmul"}, {}):
        torch.calls.clear()
        with pytest.raises(ProfilerUsageError, match="bench_quant_matmul_output_dtype_unsupported"):
            ops.build_operator_enqueue(
                torch,
                {
                    "builder": "quant_matmul",
                    "dtype": "w4a8",
                    "output_dtype": "int8",
                    "shape": {"m": 16, "n": 64, "k": 128},
                    **extra,
                },
                ctx,
            )
        assert not [c for c in torch.calls if c[0] in {"npu_quant_matmul", "npu_weight_quant_batchmatmul"}]

    # Supported output_dtype='fp16' binds float16 output honestly on quant_route.
    torch.calls.clear()
    fp16_ctx = _make_context(torch, arch="A3")
    fp16_ctx["_actual_shape"] = {}
    ops.build_operator_enqueue(
        torch,
        {
            "builder": "quant_matmul",
            "op": "npu_quant_matmul",
            "dtype": "w4a8",
            "output_dtype": "fp16",
            "shape": {"m": 16, "n": 64, "k": 128},
        },
        fp16_ctx,
    )()
    _n, _a, q_kw = [c for c in torch.calls if c[0] == "npu_quant_matmul"][-1]
    assert q_kw["output_dtype"] == _DT_FP16
    assert fp16_ctx["_actual_shape"]["output_dtype"] == "fp16"
    assert fp16_ctx["_actual_shape"]["output_bytes"] == 2048
