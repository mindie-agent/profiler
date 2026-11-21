"""RC-2 SKU planning and full-shape receipt regression tests.

[Role]
  Exercise CLI admission, held-out and cross-sample plans, and exact execution
  receipts through the SKU runner and operator bindings.

[Invariants]
  Only fake device kernels execute. Budget refusals never generate samples.

[Timeouts & Locks]
  Tests perform bounded in-memory work and synchronous temporary journal writes.

[Side-Effect Policy]
  Writes only under pytest's temporary directories.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from mindie_profiler.__main__ import main
from mindie_profiler.bench import bench_sku_microbench as sku
from mindie_profiler.bench import timing
from mindie_profiler.bench.operators import build_operator_enqueue
from mindie_profiler.bench.timing_ring import resolve_l2_bytes
from mindie_profiler.events import ProfilerUsageError
from test_bench_operators import FakeBackend


A5_SKUS = ("Ascend950DT_9581", "Ascend950DT_9582", "Ascend950PR_9579", "Ascend950PR_958b")
TRAIN = {512, 2048, 8192, 32768, 131072, 262144, 409600}
HELDOUT = {768, 2049, 4097, 24576, 98304, 200000, 350000, 400000}
PLAN_FIELDS = {
    "schema", "sku", "arch", "abi", "op", "dtype", "batch", "q_len", "kv_len",
    "heads", "kv_heads", "head_dim", "block_size", "topk", "tp", "ep", "pp",
    "pcp", "dcp", "timing_boundary", "split",
}


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
            "modes": {"eager": {"qualified": True, "trials": [
                {"trial": 0, "repeats_us": [1.0, 1.5]},
            ]}},
        }
        if hot_enqueue is not None:
            hot_enqueue()
            payload["hot_control"] = {"repeats_us": [0.8, 0.9]}
        return payload


@pytest.fixture
def domain4():
    return sku.build_cases(domain=4, sku=A5_SKUS[0], dtypes=["bf16"])


@pytest.mark.parametrize("hardware", A5_SKUS)
def test_a5_sku_registered_end_to_end(hardware, capsys):
    assert hardware in sku.A5_SKUS and hardware in sku.SUPPORTED_SKUS
    assert resolve_l2_bytes(None, sku=hardware) == 134217728
    argv = ["bench", "sku", "--sku", hardware, "--dry-run", "--domain", "5", "--dtype", "bf16"]
    assert main(argv) == 0
    output = json.loads(capsys.readouterr().out)
    cases = sku.build_cases(domain=5, sku=hardware, dtypes=["bf16"])
    assert output["cases"] == json.loads(json.dumps(cases))
    copies = [case for case in cases if case["op"] == "pinned_copy"]
    assert copies and all(case["transfer_protocol"] == "ub_dma" for case in copies)
    assert all(case["plan_key"]["sku"] == hardware and case["plan_key"]["arch"] == "A5" for case in cases)


def test_plan_keys_and_frozen_context_splits(domain4):
    cases = sku.build_cases(sku=A5_SKUS[0])
    for case in cases:
        key = case["plan_key"]
        assert PLAN_FIELDS <= key.keys()
        assert key["schema"] == "mindie-bench-plan-key/1"
        assert key["case_id"] == case["case_id"]
        for field in ("op", "dtype", "split"):
            assert key[field] == case[field]
    contexts = {"train": set(), "heldout": set()}
    for case in domain4:
        key = case["plan_key"]
        if key["kv_len"] is not None:
            contexts[key["split"]].add(key["kv_len"])
    assert contexts == {"train": TRAIN, "heldout": HELDOUT}
    assert 262144 in contexts["train"]
    assert 400000 in contexts["heldout"] and 409600 in contexts["train"]
    indexer = next(case for case in domain4 if case["op"] == "lightning_indexer"
                   and case["shape"]["seq_len"] == 2049)
    assert indexer["shape"]["top_k"] == indexer["plan_key"]["topk"] == 2048
    backend = FakeBackend()
    record = sku._run_one(indexer, context={"torch": backend.torch, **backend.context()},
                          protocol=TimingProtocol(), home=None)
    assert record["status"] == "ok"
    assert backend.calls[-1][2]["sparse_count"] == record["actual_shape"]["top_k"] == 2048


def test_context_cross_samples_and_parallel_plans(domain4):
    keys = [case["plan_key"] for case in domain4]
    for op in ("npu_fused_infer_attention_score", "absorbed_mla"):
        samples = {(key["batch"], key["q_len"], key["kv_len"])
                   for key in keys if key["op"] == op and key["world_size"] == 1}
        for context in (2048, 24576, 131072, 200000):
            assert {(batch, 1, context) for batch in (16, 64, 128)} <= samples
            assert {(1, q_len, context) for q_len in (2, 4, 8)} <= samples
    chunked = {(case["plan_key"]["q_len"], case["plan_key"]["kv_len"])
               for case in domain4 if case["builder"] == "fusion_attention" and case.get("chunked")}
    assert chunked == {(q_len, ctx) for q_len in (2048, 8192) for ctx in (131072, 200000)}
    for axis in ("pcp", "dcp"):
        plans = [key for key in keys if key["parallel_axis"] == axis]
        assert {key["world_size"] for key in plans} == {2, 4}
        assert {key["kv_len"] for key in plans} == {ctx for ctx in TRAIN | HELDOUT if ctx >= 131072}
        assert all(key[axis] == key["world_size"] for key in plans)
        assert all(key["rank_local_tokens"] == -(-key["kv_len"] // key["world_size"]) for key in plans)
    plan = next(case for case in domain4 if case.get("parallel_axis") == "pcp")
    protocol = TimingProtocol()
    run = sku.run_cases([plan], context={"protocol": protocol, "torch": object()})
    assert run["status"] == "ok" and run["records"][0]["status"] == "plan_only"
    assert run["executed_case_count"] == 0 and run["plan_only_case_count"] == 1
    assert protocol.calls == []


def test_causal_prefill_binds_compressed_mask_and_reports_triangular_pairs(domain4):
    case = next(c for c in domain4 if c.get("causal") and c["shape"]["seq_len"] == 768)
    backend, protocol = FakeBackend(), TimingProtocol()
    context = {"torch": backend.torch, "protocol": protocol, **backend.context()}
    shape = case["shape"]
    qkv_bytes = 768 * (shape["heads"] + 2 * shape["kv_heads"]) * shape["head_dim"] * 2
    mask_bytes = 2048 ** 2
    assert timing.estimate_working_set_bytes(case) == qkv_bytes + mask_bytes

    context["budget"] = {"cap_bytes": qkv_bytes + mask_bytes - 1}
    refused = sku.run_cases([case], context=context)
    assert refused["records"][0]["status"] == "over_budget"
    assert protocol.calls == backend.calls == []

    context.pop("budget")
    record = sku.run_cases([case], context=context)["records"][0]
    assert record["status"] == "ok"
    _, (q, k, _, _), launch = backend.calls[-1]
    assert q.shape[0] * k.shape[0] == 589_824
    assert launch["actual_seq_qlen"] == launch["actual_seq_kvlen"] == [768]
    actual = record["actual_shape"]
    assert actual["query_key_pairs"] == 295_296
    assert record["work_flops"] == case["work_flops"] == 4 * shape["heads"] * 295_296 * shape["head_dim"]
    assert launch["sparse_mode"] == actual["sparse_mode"] == 2
    mask = launch["atten_mask"]
    assert mask.shape == (2048, 2048) and mask.nbytes == mask_bytes
    assert mask.device == q.device and mask.dtype is backend.torch.uint8
    assert mask.triangular_diagonal == 1
    assert actual["atten_mask_shape"] == [2048, 2048]
    assert actual["atten_mask_bytes"] == mask_bytes and actual["atten_mask_dtype"] == "uint8"


@pytest.mark.parametrize("provider", ("chunk_kda_fwd", "chunk_kda"))
@pytest.mark.parametrize("dtype", ("bf16", "fp16"))
def test_chunk_kda_calls_provider_with_fp32_initial_state(provider, dtype):
    cases = sku.build_cases(domain=4, sku=A5_SKUS[0], dtypes=[dtype])
    case = next(c for c in cases if c["builder"] == "chunk_kda_fwd" and c["shape"]["seq_len"] == 768)
    backend, protocol = FakeBackend(), TimingProtocol()
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
    context = {"torch": backend.torch, **backend.context(), "extra_modules": modules}
    receipt = sku._run_one(case, context=context, protocol=protocol, home=None)
    assert receipt["status"] == "ok", receipt.get("reason")
    assert case["shape"]["state_dtype"] == receipt["actual_shape"]["state_dtype"] == "fp32"
    _, operands, _ = backend.calls[-1]
    actual = receipt["actual_shape"]
    beta_dtype = "fp32" if dtype == "fp16" else dtype
    dtypes = (dtype, dtype, dtype, "fp32", beta_dtype, "fp32")
    for name, tensor, dtype_name in zip(("q", "k", "v", "g", "beta", "state"), operands, dtypes, strict=True):
        assert actual[f"{name}_shape"] == list(tensor.shape)
        assert actual[f"{name}_dtype"] == dtype_name
    assert operands[-1].dtype is backend.torch.float32


@pytest.mark.parametrize("builder", ("fused_infer_attention", "absorbed_mla"))
@pytest.mark.parametrize(("batch", "q_len"), ((16, 1), (1, 8)))
def test_paged_decode_passes_batch_and_query_shape_to_kernel(domain4, builder, batch, q_len):
    case = next(c for c in domain4 if c["builder"] == builder and c["plan_key"]["kv_len"] == 2048
                and (c["plan_key"]["batch"], c["plan_key"]["q_len"]) == (batch, q_len))
    backend = FakeBackend()
    receipt = sku._run_one(case, context={"torch": backend.torch, **backend.context()},
                           protocol=TimingProtocol(), home=None)
    assert receipt["status"] == "ok"
    _, args, launch = backend.calls[-1]
    assert args[0].shape[0] == batch * q_len
    assert launch["block_table"].shape == (batch, 16)
    assert launch["actual_seq_lengths"] == list(range(q_len, batch * q_len + 1, q_len))
    assert launch["actual_seq_lengths_kv"] == [2048] * batch
    assert receipt["actual_shape"]["sequences"] == batch and receipt["actual_shape"]["q_len"] == q_len


@pytest.mark.parametrize("builder", ("recurrent_gated_delta_rule", "fused_recurrent_kda"))
def test_recurrent_cases_execute_the_planned_batch_queries_and_state(domain4, builder):
    cases = [case for case in domain4 if case["builder"] == builder and "state_len" in case["shape"]]
    assert {(key["state_len"], key["batch"], key["q_len"]) for key in (c["plan_key"] for c in cases)} == {
        (state, batch, q_len) for state in (512, 2048) for batch in (1, 16, 64) for q_len in (1, 2, 4)
    }
    case = next(c for c in cases if c["shape"]["sequences"] == 16 and c["shape"]["q_len"] == 4)
    backend = FakeBackend()
    context = {"torch": backend.torch, **backend.context()}
    kda = builder == "fused_recurrent_kda"
    if kda:
        def indexed_kda(*args, **kwargs):
            backend.calls.append((builder, args, kwargs))
            return args[0]

        context["extra_modules"] = {"vllm_ascend.ops.triton.kda": SimpleNamespace(fused_recurrent_kda=indexed_kda)}
    receipt = sku._run_one(case, context=context, protocol=TimingProtocol(), home=None)
    assert receipt["status"] == "ok"
    assert receipt["actual_shape"] == case["shape"]
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
        assert (4,) * 16 in backend.tensor_values


def test_indexed_kda_refuses_before_allocating_at_original_byte_cap(domain4, monkeypatch):
    case = next(c for c in domain4 if c["builder"] == "fused_recurrent_kda"
                and (c["shape"].get("sequences"), c["shape"].get("q_len"), c["shape"].get("state_len")) == (64, 4, 512))
    assert (case["shape"]["heads"], case["shape"]["head_dim"]) == (8, 128)
    assert timing.estimate_working_set_bytes(case) == 271_587_588
    backend, protocol = FakeBackend(), TimingProtocol()
    indexed_kda = backend._record("indexed_kda")
    modules = {"vllm_ascend.ops.triton.kda": SimpleNamespace(fused_recurrent_kda=indexed_kda)}
    context = {"torch": backend.torch, "protocol": protocol, "extra_modules": modules,
               **backend.context(budget={"cap_bytes": 270_008_320})}

    def unexpected_allocation(*args, **kwargs):
        pytest.fail("indexed KDA allocated before checking the combined footprint")

    for name in ("randn", "zeros", "ones", "tensor"):
        monkeypatch.setattr(backend.torch, name, unexpected_allocation)
    result = sku.run_cases([case], context=context)
    assert result["records"][0]["status"] == "over_budget"
    assert result["executed_case_count"] == 0 and result["over_budget_case_count"] == 1
    assert protocol.calls == backend.calls == []
    with pytest.raises(ProfilerUsageError, match="bench_vram_budget_exceeded"):
        build_operator_enqueue(backend.torch, case, context)


@pytest.mark.parametrize("builder", ("fusion_attention", "dcp_lse_attention_merge"))
def test_long_shapes_that_used_to_be_clamped_execute_full_dimensions(domain4, builder):
    template = next(c for c in domain4 if c["builder"] == builder and c["shape"].get("seq_len") == 262144)
    requested = {**template["shape"], "heads": 32}
    case = {**template, "case_id": f"test.full.{builder}", "shape": requested,
            "plan_key": {**template["plan_key"], "case_id": f"test.full.{builder}", "heads": 32}}
    backend = FakeBackend()
    context = {"torch": backend.torch, **backend.context(budget={"cap_bytes": 8 * 1024 ** 3})}
    receipt = sku._run_one(case, context=context, protocol=TimingProtocol(), home=None)
    assert receipt["status"] == "ok"
    assert receipt["actual_shape"]["heads"] == 32
    assert backend.calls[-1][1][0].shape == (262144, 32, 128)


@pytest.mark.parametrize("source", ("observations", "resume"))
@pytest.mark.parametrize("update_plan_key", (False, True))
def test_resume_reexecutes_same_case_id_with_different_heads(domain4, tmp_path, source, update_plan_key):
    case = next(c for c in domain4 if c.get("causal") and c["shape"]["seq_len"] == 768)
    larger = {**case, "shape": {**case["shape"], "heads": 32}}
    if update_plan_key:
        larger["plan_key"] = {**case["plan_key"], "heads": 32}
    backend, protocol = FakeBackend(), TimingProtocol()
    context = {"torch": backend.torch, "protocol": protocol, **backend.context()}
    path = tmp_path / "journal.jsonl"
    journals = {source: path, "sku": A5_SKUS[0]}
    first = sku.run_cases([case], context=context, **journals)
    if source == "observations":
        unfinished = json.loads(path.read_text().splitlines()[0])
        unfinished.update(plan_key=larger["plan_key"], requested_shape=larger["shape"], sample_id="unfinished")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(unfinished) + "\n")
    second = sku.run_cases([larger], context=context, **journals)
    assert first["records"][0]["actual_shape"]["heads"] == 8
    assert second["executed_case_count"] == 1 and second["recovered_records"] == 0
    assert second["records"][0]["actual_shape"]["heads"] == 32
    assert [args[0].shape[1] for _, args, _ in backend.calls] == [8, 32]
    assert len(protocol.calls) == 2
    assert sku.run_cases([case, larger], context=context, **journals)["skipped_case_count"] == 2
    if source == "observations":
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        observations = [row for row in rows if row["record_type"] == "observation"]
        assert len({row["sample_id"] for row in observations}) == len(observations) == 4
        resume = tmp_path / "recovered.jsonl"
        result = sku.run_cases([larger], context=context, resume=resume, **journals)
        assert result["executed_case_count"] == 0
        recovered = json.loads(resume.read_text())
        assert recovered["recovered"] is True and recovered["actual_shape"]["heads"] == 32


def test_failed_timing_invocation_counts_as_executed(domain4):
    case = next(c for c in domain4 if c.get("causal") and c["shape"]["seq_len"] == 768)
    backend = FakeBackend()

    def fail_timing(enqueue, **kwargs):
        enqueue()
        raise RuntimeError("timer failed after enqueue")

    context = {"torch": backend.torch, "protocol": SimpleNamespace(run=fail_timing), **backend.context()}
    result = sku.run_cases([case], context=context)
    assert result["records"][0]["status"] == "failed"
    assert result["executed_case_count"] == len(backend.calls) == 1
    assert result["over_budget_case_count"] == 0


def test_full_shape_budget_refusal_and_retry_keep_receipt_identity(domain4, tmp_path):
    case = next(c for c in domain4 if c["builder"] == "fusion_attention"
                and c["shape"].get("seq_len") == 409600 and "parallel_axis" not in c)
    requested = dict(case["shape"])
    assert requested["tokens"] == 409600
    backend = FakeBackend()
    protocol = TimingProtocol()
    ring_plan = timing.cold_ring_plan(resolve_l2_bytes(None, sku=A5_SKUS[0]))
    ring = timing.ColdRing(backend.torch, ring_plan, ordinal=0)
    ring.allocate()
    context = {"torch": backend.torch, "protocol": protocol, "ring": ring, **backend.context()}
    context["device"]["local_rank"] = 3
    journals = {"observations": tmp_path / "samples.jsonl", "resume": tmp_path / "receipts.jsonl"}
    context["budget"] = {"cap_bytes": 1}
    result = sku.run_cases([case], context=context, sku=A5_SKUS[0], **journals)
    refusal = result["records"][0]
    assert refusal["status"] == "over_budget" and refusal["requested_shape"] == requested
    assert result["executed_case_count"] == 0 and result["over_budget_case_count"] == 1
    assert protocol.calls == [] and backend.calls == []
    # One full slot fits here, while the builder's two cold slots exceed the cap.
    context["budget"]["cap_bytes"] = timing.estimate_working_set_bytes(case) + ring_plan["total_bytes"]
    refusal = sku.run_cases([case], context=context, sku=A5_SKUS[0], **journals)["records"][0]
    assert refusal["status"] == "over_budget" and refusal["requested_shape"] == requested
    assert refusal["case_id"] == case["case_id"] and refusal["plan_key"] == case["plan_key"]
    assert "actual_shape" not in refusal and "timing" not in refusal
    assert protocol.calls == [] and not journals["observations"].exists()

    context["budget"]["cap_bytes"] = 8 * 1024 ** 3
    executed = sku.run_cases([case], context=context, sku=A5_SKUS[0], **journals)["records"][0]
    assert executed["status"] == "ok"
    assert {key: executed["actual_shape"][key] for key in requested} == requested
    assert executed["actual_shape"]["q_len"] == 409600
    assert executed["participating_ranks"] == [3]
    assert executed["cold_ring_bytes"] == ring_plan["total_bytes"]
    assert executed["timing_events"]["samples_by_mode"] == {"eager": 2, "hot_control": 2}
    assert case["shape"] == executed["requested_shape"] == requested
    assert case["case_id"] == executed["case_id"] and case["plan_key"] == executed["plan_key"]
    for _, args, launch in backend.calls:
        assert args[0].shape == (409600, 8, 128)
        assert launch["actual_seq_qlen"] == [409600]
    assert [json.loads(line)["status"] for line in journals["resume"].read_text().splitlines()] == [
        "over_budget", "over_budget", "ok",
    ]
    assert [json.loads(line)["record_type"] for line in journals["observations"].read_text().splitlines()] == [
        "observation", "observation", "case_complete",
    ]
    journals["resume"].unlink()
    recovery = sku.run_cases([case], context=context, sku=A5_SKUS[0], **journals)
    assert recovery["executed_case_count"] == 0
    recovered = json.loads(journals["resume"].read_text())
    assert recovered["recovered"] is True
    for field in ("actual_shape", "participating_ranks", "cold_ring_bytes", "timing_events"):
        assert recovered[field] == executed[field]
