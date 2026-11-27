"""A5 SKU registration, attention/KDA operator bindings, and HBM budget tests.

[Role]
  Exercise A5 SKU L2 sizing and CLI admission, compressed causal prefill mask
  and working-set checks, Triton/NPU chunk & recurrent KDA bindings, paged
  decode geometry, full un-clamped long-context shapes, and budget refusals
  through ``l0_presets``, ``build_operator_enqueue``, and ``campaign_runner``.

[Invariants]
  Only fake device kernels execute. Budget refusals never allocate or time.

[Timeouts & Locks]
  Tests perform bounded in-memory work and synchronous temporary writes.

[Side-Effect Policy]
  Writes only under pytest's temporary directories.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from mindie_profiler.__main__ import main
from mindie_profiler.bench import campaign_runner, env_fingerprint, l0_presets, timing
from mindie_profiler.bench.operators import build_operator_enqueue
from mindie_profiler.bench.subgraph_runtime import OperatorExecutor
from mindie_profiler.bench.timing_ring import resolve_l2_bytes
from mindie_profiler.events import ProfilerUsageError
from tests.test_bench_operators import FakeBackend

A5_SKUS = ("Ascend950DT_9581", "Ascend950DT_9582", "Ascend950PR_9579", "Ascend950PR_958b")


class TimingProtocol:
    repeats = 2

    def __init__(self):
        self.calls = []

    def run(self, enqueue, *, case_id, hot_enqueue=None, **kwargs):
        self.calls.append(case_id)
        enqueue()
        payload = {
            "minimum_ms": 0.001,
            "timer_source": "torch.npu.Event(enable_timing=True)",
            "modes": {
                "eager": {
                    "qualified": True,
                    "p50_us": 1.25,
                    "p90_us": 1.5,
                    "p99_us": 1.5,
                    "min_us": 1.0,
                    "iqr_us": 0.25,
                    "cv_pct": 1.0,
                    "trials": [{"trial": 0, "repeats_us": [1.0, 1.5]}],
                },
            },
        }
        if hot_enqueue is not None:
            hot_enqueue()
            payload["hot_control"] = {"repeats_us": [0.8, 0.9], "median_us": 0.85}
        return payload


def _a5_env(sku: str = A5_SKUS[0]) -> dict:
    return env_fingerprint.probe_env_fingerprint(
        sku=sku, soc_arch="A5", observed_clock_mhz=1650.0, clock_source="test",
    )


def _v1_plan(case: dict, *, sku: str = A5_SKUS[0]) -> dict:
    node = {
        "node_id": "n0",
        "kind": "operator",
        "builder": case["builder"],
        "op": case.get("op", case["builder"]),
        "dtype": case.get("dtype", "bf16"),
        "shape": dict(case["shape"]),
        **({k: case[k] for k in ("causal", "paged", "block_size") if k in case}),
    }
    return {
        "schema": "mindie-bench-subgraph-plan/1",
        "plan_id": "rc2-unit",
        "sku": sku,
        "execution_modes": ["eager"],
        "cases": [{
            **case,
            "nodes": [node],
            "edges": [],
            "timed_boundary": {"include": ["n0"]},
        }],
    }


@pytest.mark.parametrize("hardware", A5_SKUS)
def test_a5_sku_registered_end_to_end(hardware, capsys):
    assert hardware in l0_presets.A5_SKUS and hardware in l0_presets.SUPPORTED_SKUS
    assert resolve_l2_bytes(None, sku=hardware) == (112 if hardware == "Ascend950PR_958b" else 128) * timing.MIB
    argv = ["bench", "sku", "--sku", hardware, "--dry-run", "--domain", "5", "--dtype", "bf16"]
    assert main(argv) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "dry_run"
    assert output["sku"] == hardware
    assert output["case_count"] > 0


def test_causal_prefill_binds_compressed_mask_and_reports_triangular_pairs(tmp_path):
    shape = {"tokens": 768, "seq_len": 768, "heads": 8, "kv_heads": 2, "head_dim": 128}
    case = {
        "case_id": "causal.768", "builder": "fusion_attention", "op": "npu_fusion_attention",
        "dtype": "bf16", "split": "heldout", "phase": "prefill", "causal": True, "shape": shape,
    }
    qkv_bytes = 768 * (shape["heads"] + 2 * shape["kv_heads"]) * shape["head_dim"] * 2
    mask_bytes = 2048 ** 2
    assert timing.estimate_working_set_bytes(case) == qkv_bytes + mask_bytes

    backend, protocol = FakeBackend(), TimingProtocol()
    refused = campaign_runner.run_campaign(
        _v1_plan(case),
        campaign_dir=tmp_path / "refused",
        env_fingerprint=_a5_env(),
        executor=OperatorExecutor(backend.torch, backend.context(budget={"cap_bytes": qkv_bytes + mask_bytes - 1})),
        protocol=protocol,
    )
    assert refused["blocked_cases"][0]["status"] == "over_budget"
    assert protocol.calls == backend.calls == []

    executed = campaign_runner.run_campaign(
        _v1_plan(case),
        campaign_dir=tmp_path / "ok",
        env_fingerprint=_a5_env(),
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=protocol,
    )
    record = executed["cases"][0]
    assert record["status"] == "ok"
    _, (q, k, _, _), launch = backend.calls[-1]
    assert q.shape[0] * k.shape[0] == 589_824
    assert launch["actual_seq_qlen"] == launch["actual_seq_kvlen"] == [768]
    actual = record["actual_executed_shape"]
    assert actual["query_key_pairs"] == 295_296
    assert launch["sparse_mode"] == actual["sparse_mode"] == 2
    mask = launch["atten_mask"]
    assert mask.shape == (2048, 2048) and mask.nbytes == mask_bytes
    assert mask.device == q.device and mask.dtype is backend.torch.uint8
    assert mask.triangular_diagonal == 1


@pytest.mark.parametrize("provider", ("chunk_kda_fwd", "chunk_kda"))
@pytest.mark.parametrize("dtype", ("bf16", "fp16"))
def test_chunk_kda_calls_provider_with_fp32_initial_state(provider, dtype):
    case = {
        "builder": "chunk_kda_fwd", "op": "chunk_kda_fwd", "dtype": dtype,
        "shape": {"tokens": 768, "seq_len": 768, "heads": 2, "head_dim": 128, "state_dtype": "fp32"},
    }
    backend = FakeBackend()
    del backend.torch.npu.npu_chunk_kda_fwd

    def chunk_kda_fwd(q, k, v, g, beta, scale, initial_state, output_final_state,
                      cu_seqlens=None, prebuilt_meta=None):
        assert scale == pytest.approx(128 ** -0.5)
        assert output_final_state is False and cu_seqlens is None and prebuilt_meta is None
        backend.calls.append((provider, (q, k, v, g, beta, initial_state), {}))
        return v, None

    def chunk_kda(q, k, v, g, beta, scale=None, initial_state=None, output_final_state=False,
                  use_qk_l2norm_in_kernel=False, cu_seqlens=None, prebuilt_meta=None):
        assert use_qk_l2norm_in_kernel is False
        return chunk_kda_fwd(q, k, v, g, beta, scale, initial_state, output_final_state, cu_seqlens, prebuilt_meta)

    selected = {"chunk_kda_fwd": chunk_kda_fwd, "chunk_kda": chunk_kda}[provider]
    modules = {"vllm_ascend.ops.triton.kda": SimpleNamespace(**{provider: selected})}
    context = backend.context(extra_modules=modules, _actual_shape={})
    build_operator_enqueue(backend.torch, case, context)()
    _, operands, _ = backend.calls[-1]
    actual = context["_actual_shape"]
    assert actual["state_dtype"] == "fp32"
    assert operands[-1].dtype is backend.torch.float32
    beta_dtype = "fp32" if dtype == "fp16" else dtype
    for name, tensor, dtype_name in zip(
        ("q", "k", "v", "g", "beta", "state"),
        operands,
        (dtype, dtype, dtype, "fp32", beta_dtype, "fp32"),
        strict=True,
    ):
        assert actual[f"{name}_shape"] == list(tensor.shape)
        assert actual[f"{name}_dtype"] == dtype_name


@pytest.mark.parametrize("cap_bytes", (2_100_224, 5_639_167, 5_639_168))
def test_chunk_kda_checks_provider_peak_before_allocating(tmp_path, monkeypatch, cap_bytes):
    case = {
        "case_id": "kda.768", "builder": "chunk_kda_fwd", "op": "chunk_kda_fwd",
        "dtype": "bf16", "split": "heldout", "phase": "prefill",
        "shape": {"tokens": 768, "seq_len": 768, "heads": 2, "head_dim": 128, "state_dtype": "fp32"},
    }
    peak_bytes = 5_639_168
    assert timing.estimate_working_set_bytes(case) == peak_bytes
    backend, protocol = FakeBackend(), TimingProtocol()
    del backend.torch.npu.npu_chunk_kda_fwd
    modules = {"vllm_ascend.ops.triton.kda": SimpleNamespace(chunk_kda_fwd=backend._record("chunk_kda_fwd"))}
    context = backend.context(extra_modules=modules, budget={"cap_bytes": cap_bytes})

    if cap_bytes < peak_bytes:
        def unexpected_allocation(*args, **kwargs):
            pytest.fail("chunk KDA allocated before checking the provider peak")

        for name in ("randn", "zeros", "ones", "empty"):
            monkeypatch.setattr(backend.torch, name, unexpected_allocation)
        result = campaign_runner.run_campaign(
            _v1_plan(case),
            campaign_dir=tmp_path / "kda-refused",
            env_fingerprint=_a5_env(),
            executor=OperatorExecutor(backend.torch, context),
            protocol=protocol,
        )
        assert result["blocked_cases"][0]["status"] == "over_budget"
        assert protocol.calls == backend.calls == []
        with pytest.raises(ProfilerUsageError, match="bench_vram_budget_exceeded"):
            build_operator_enqueue(backend.torch, case, context)
    else:
        result = campaign_runner.run_campaign(
            _v1_plan(case),
            campaign_dir=tmp_path / "kda-ok",
            env_fingerprint=_a5_env(),
            executor=OperatorExecutor(backend.torch, context),
            protocol=protocol,
        )
        assert result["cases"][0]["status"] == "ok"
        assert len(backend.calls) == 1


@pytest.mark.parametrize("builder", ("fused_infer_attention", "absorbed_mla"))
@pytest.mark.parametrize(("batch", "q_len"), ((16, 1), (1, 8)))
def test_paged_decode_passes_batch_and_query_shape_to_kernel(builder, batch, q_len):
    case = {
        "builder": builder, "op": builder, "dtype": "bf16", "paged": True, "block_size": 128,
        "shape": {
            "tokens": batch * q_len, "sequences": batch, "q_len": q_len,
            "seq_len": 2048, "heads": 16, "kv_heads": 2, "head_dim": 128, "block_size": 128,
        },
    }
    backend = FakeBackend()
    context = backend.context(_actual_shape={})
    build_operator_enqueue(backend.torch, case, context)()
    _, args, launch = backend.calls[-1]
    assert args[0].shape[0] == batch * q_len
    assert launch["block_table"].shape == (batch, 16)
    assert launch["actual_seq_lengths"] == list(range(q_len, batch * q_len + 1, q_len))
    assert launch["actual_seq_lengths_kv"] == [2048] * batch
    assert context["_actual_shape"]["sequences"] == batch and context["_actual_shape"]["q_len"] == q_len


@pytest.mark.parametrize("builder", ("recurrent_gated_delta_rule", "fused_recurrent_kda"))
def test_recurrent_cases_execute_the_planned_batch_queries_and_state(builder):
    case = {
        "builder": builder, "op": builder, "dtype": "bf16",
        "shape": {
            "tokens": 64, "sequences": 16, "q_len": 4, "state_len": 512,
            "heads": 8, "head_dim": 128,
        },
    }
    backend = FakeBackend()
    context = backend.context(_actual_shape={})
    kda = builder == "fused_recurrent_kda"
    if kda:
        def indexed_kda(*args, **kwargs):
            backend.calls.append((builder, args, kwargs))
            return args[0]

        context["extra_modules"] = {"vllm_ascend.ops.triton.kda": SimpleNamespace(fused_recurrent_kda=indexed_kda)}
    build_operator_enqueue(backend.torch, case, context)()
    _, operands, launch = backend.calls[-1]
    if kda:
        assert launch["initial_state"].shape == (512, 8, 128, 128)
        assert launch["cu_seqlens"].shape == (17,)
        assert launch["ssm_state_indices"].shape == (16, 4)
        assert operands[0].shape == (1, 64, 8, 128)
    else:
        assert operands[3].shape == (512, 8, 128, 128)
        assert launch["actual_seq_lengths"].shape == (16,)
        assert launch["ssm_state_indices"].shape == (64,)
        assert operands[0].shape == (64, 8, 128)


def test_indexed_kda_refuses_before_allocating_at_original_byte_cap(tmp_path, monkeypatch):
    case = {
        "case_id": "indexed.kda", "builder": "fused_recurrent_kda", "op": "fused_recurrent_kda",
        "dtype": "bf16", "split": "train", "phase": "decode",
        "shape": {"tokens": 256, "sequences": 64, "q_len": 4, "state_len": 512, "heads": 8, "head_dim": 128},
    }
    assert timing.estimate_working_set_bytes(case) == 271_587_588
    backend, protocol = FakeBackend(), TimingProtocol()
    modules = {"vllm_ascend.ops.triton.kda": SimpleNamespace(fused_recurrent_kda=backend._record("indexed_kda"))}
    context = backend.context(extra_modules=modules, budget={"cap_bytes": 270_008_320})

    def unexpected_allocation(*args, **kwargs):
        pytest.fail("indexed KDA allocated before checking the combined footprint")

    for name in ("randn", "zeros", "ones", "tensor"):
        monkeypatch.setattr(backend.torch, name, unexpected_allocation)
    result = campaign_runner.run_campaign(
        _v1_plan(case),
        campaign_dir=tmp_path / "ikda-refused",
        env_fingerprint=_a5_env(),
        executor=OperatorExecutor(backend.torch, context),
        protocol=protocol,
    )
    assert result["blocked_cases"][0]["status"] == "over_budget"
    assert protocol.calls == backend.calls == []
    with pytest.raises(ProfilerUsageError, match="bench_vram_budget_exceeded"):
        build_operator_enqueue(backend.torch, case, context)


@pytest.mark.parametrize("builder", ("fusion_attention", "dcp_lse_attention_merge"))
def test_long_shapes_execute_full_dimensions_without_clamping(builder):
    case = {
        "builder": builder, "op": builder, "dtype": "bf16",
        "shape": {"tokens": 262144, "seq_len": 262144, "heads": 32, "kv_heads": 8, "head_dim": 128},
    }
    backend = FakeBackend()
    context = backend.context(budget={"cap_bytes": 8 * 1024 ** 3}, _actual_shape={})
    build_operator_enqueue(backend.torch, case, context)()
    assert context["_actual_shape"]["heads"] == 32
    assert backend.calls[-1][1][0].shape == (262144, 32, 128)


def test_failed_timing_invocation_records_blocked_status(tmp_path):
    case = {
        "case_id": "fail.timing", "builder": "rms_norm", "op": "rms_norm",
        "dtype": "bf16", "split": "train", "phase": "prefill",
        "shape": {"tokens": 16, "width": 64},
    }
    backend = FakeBackend()

    def fail_timing(enqueue, **_kwargs):
        enqueue()
        raise RuntimeError("timer failed after enqueue")

    result = campaign_runner.run_campaign(
        _v1_plan(case),
        campaign_dir=tmp_path / "fail-camp",
        env_fingerprint=_a5_env(),
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=SimpleNamespace(run=fail_timing),
    )
    assert result["blocked_cases"][0]["status"] == "failed"
    assert result["executed_case_count"] == 1
    assert len(backend.calls) == 1
