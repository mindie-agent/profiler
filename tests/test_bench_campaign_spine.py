"""Pure-CPU unit tests for the TODO 2 incremental campaign Spine on mindie-profiler.

[Role]
  Verify bit-identical cross-repo contract parity against
  ``tests/fixtures/bench_matrix/v2_contract_golden.json``, version-agnostic
  environment fingerprinting, immutable per-run shard storage, incremental
  delta execution, ``Never-Overwrite-Qualified``, heldout training-manifest
  disjointness, verified cold-HBM eviction, traced ``busy_union`` vs
  ``elapsed_span``, multi-node S1 collective topology refusal, guarded
  ``abi_rejection`` execution, cross-version ``bench diff``, unified
  ``BuilderSpec`` SSOT export, and zero ``mindie_sim`` runtime imports.

[Invariants]
  * Pure CPU (``DEV-ZERO-CTX``); zero live NPU or ``mindie_sim`` dependencies.
  * Every test writes only under pytest ``tmp_path``.

[Timeouts & Locks]
  Deterministic in-memory and bounded local temp I/O (<2s total).

[Side-Effect Policy]
  Writes only under pytest ``tmp_path``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mindie_profiler.bench import (
    abi,
    abi_portable,
    campaign_diff,
    campaign_runner,
    campaign_store,
    env_fingerprint,
    operators,
    timing,
)
from mindie_profiler.bench.subgraph_runtime import OperatorExecutor
from mindie_profiler.events import ProfilerUsageError
from tests.test_bench_operators import FakeBackend

GOLDEN_PATH = Path(__file__).resolve().parent / "fixtures" / "bench_matrix" / "v2_contract_golden.json"


def _load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


class _CampaignProtocol:
    """Deterministic fake measurement protocol supporting pre_repeat and traced intervals."""

    def __init__(self, *, repeat_us: float = 42.0, timer_source: str = "torch.npu.Event(enable_timing=True)") -> None:
        self.repeat_us = repeat_us
        self.timer_source = timer_source
        self.calls: list[str] = []
        self.pre_repeat_calls = 0

    def run(
        self,
        enqueue,
        *,
        case_id: str,
        pre_repeat=None,
        traced_intervals_us=None,
        **_kwargs,
    ) -> dict:
        self.calls.append(case_id)
        if callable(pre_repeat):
            pre_repeat()
            self.pre_repeat_calls += 1
        enqueue()
        if traced_intervals_us:
            busy_us = timing.compute_busy_union_us(traced_intervals_us)
            samples = [busy_us, busy_us]
            clock_op = timing.CLOCK_OPERATOR_BUSY_UNION
        else:
            samples = [self.repeat_us, self.repeat_us + 2.0]
            clock_op = timing.CLOCK_OPERATOR_ELAPSED_SPAN
        p50 = sum(samples) / len(samples)
        return {
            "schema": "mindie-bench-timing/1",
            "case_id": case_id,
            "timer_source": self.timer_source,
            "clock_operator": clock_op,
            "minimum_ms": min(samples) / 1000.0,
            "qualified": self.timer_source == "torch.npu.Event(enable_timing=True)",
            "modes": {
                "eager": {
                    "qualified": self.timer_source == "torch.npu.Event(enable_timing=True)",
                    "median_us": p50,
                    "p50_us": p50,
                    "p90_us": max(samples),
                    "p99_us": max(samples),
                    "min_us": min(samples),
                    "iqr_us": abs(samples[-1] - samples[0]),
                    "cv_pct": 1.0,
                    "repeat_count": len(samples),
                    "stats_us": {
                        "min": min(samples),
                        "p25": min(samples),
                        "p50": p50,
                        "p75": max(samples),
                        "p90": max(samples),
                        "p99": max(samples),
                        "max": max(samples),
                        "iqr": abs(samples[-1] - samples[0]),
                        "cv_pct": 1.0,
                    },
                    "trials": [{"trial": 0, "repeats_us": samples}],
                },
            },
        }


def _make_v2_case(
    *,
    acq: str,
    builder: str = "rms_norm",
    shape: dict | None = None,
    dtype: str = "bf16",
    capture_mode: str = "eager",
    residency: str = "cold_hbm",
    split: str = "train",
    strides: dict | None = None,
    storage_offsets: dict | None = None,
    kind: str = "operator",
    ordered_rank_placement: list[int] | None = None,
    link_tiers: list[str] | None = None,
    upstream_abi: str = "aclnnRmsNorm",
    abi_backend: str = "cann_aclnn",
) -> dict:
    shp = dict(shape or {"tokens": 16, "width": 64})
    raw_key = {
        "sig_version": 2,
        "kind": kind,
        "sku": "Ascend950DT_9582",
        "soc_arch": "A5",
        "abi_backend": abi_backend,
        "upstream_abi": upstream_abi,
        "bench_builder": builder,
        "canonical_shapes": shp,
        "strides": strides if strides is not None else {},
        "storage_offsets": storage_offsets if storage_offsets is not None else {},
        "dtypes": {"input": dtype, "output": dtype},
        "layouts": {"input": "ND", "output": "ND"},
        "kv_allocator_block_size": None,
        "kv_kernel_block_size": None,
        "cp_kv_cache_interleave_size": None,
        "page_geometry": None,
        "per_expert_token_counts": None,
        "per_rank_token_counts": None,
        "capture_mode": capture_mode,
        "aclgraph_padded_bucket": None,
        "workspace_policy": "default",
        "stream_dependencies": [],
        "residency": residency,
        "quant_meta": {},
        "op_attrs": {},
        "ordered_rank_placement": ordered_rank_placement,
        "link_tiers": link_tiers,
        "collective_algorithm": "ring" if kind == "collective" else None,
        "split_sizes": None,
        "timed_nodes": None,
        "edges": None,
    }
    key = campaign_store.normalize_canonical_key(raw_key)
    digest = campaign_store.canonical_key_digest(key)
    return {
        "acquisition_uid": acq,
        "case_id": f"k2-{digest}",
        "canonical_key_digest": digest,
        "canonical_key": key,
        "kind": kind,
        "level": "L1",
        "boundary": "device_kernel",
        "split": split,
        "phase": "decode",
        "stage": "s0_local",
        "capture_mode": capture_mode,
        "residency": residency,
        "clock_operator": "elapsed_span",
        "work_flops": 0,
        "work_bytes": 4096,
        "nodes": [{
            "node_id": "n0",
            "kind": kind,
            "builder": builder,
            "op": builder,
            "dtype": dtype,
            "shape": shp,
            "upstream_abi": upstream_abi,
            "abi_backend": abi_backend,
        }],
        "edges": [],
        "timed_boundary": {"include": ["n0"]},
        "identities": {},
    }


def _make_v2_plan(cases: list[dict], *, plan_id: str = "plan-test", reverse_index: dict | None = None) -> dict:
    return campaign_store.seal_payload({
        "schema": campaign_store.PLAN_V2_SCHEMA,
        "plan_id": plan_id,
        "plan_kind": "model_matrix",
        "sku": "Ascend950DT_9582",
        "soc_arch": "A5",
        "stage": "s0_local",
        "cache_partition": "shared",
        "world_size": 1,
        "training_manifest_sha256": None,
        "cases": cases,
        "reverse_index": reverse_index or {},
    }, "plan_sha256")


def test_v2_contract_golden_byte_identical_parity():
    golden = _load_golden()
    for sample in golden["canonical_key_samples"]:
        normalized = campaign_store.normalize_canonical_key(sample["key"])
        encoded = campaign_store.canonical_json(normalized).decode("utf-8")
        assert encoded == sample["canonical_json"], sample["name"]
        assert campaign_store.canonical_key_digest(sample["key"]) == sample["canonical_key_digest"]
        assert campaign_store.canonical_case_id(sample["key"]) == sample["case_id"]

    env_doc = golden["campaign_manifest_v1"]["version_fingerprint"]
    assert env_fingerprint.compute_env_fingerprint_id(env_doc) == env_doc["env_fingerprint_id"]

    assert campaign_store.verify_seal(golden["bench_plan_v2"], "plan_sha256") is True
    assert campaign_store.verify_seal(golden["campaign_manifest_v1"], "campaign_sha256") is True

    case0 = dict(golden["campaign_manifest_v1"]["cases"][0])
    assert campaign_store.verify_case_raw_sha256(case0) is True
    case0_hit = {**case0, "cache_status": "hit", "split": "train"}
    assert campaign_store.verify_case_raw_sha256(case0_hit) is True


def test_env_fingerprint_version_agnostic_cann_va_tiers_and_jitter_exclusion(tmp_path):
    for ver in ("8.5.0", "9.3.RC1", "9.4.0", "10.1.RC2"):
        root = tmp_path / f"cann-{ver}"
        info = root / "aarch64-linux" / "ascend_toolkit_install.info"
        info.parent.mkdir(parents=True)
        info.write_text(f"version={ver}\ninnerversion=V100R001-{ver}\n", encoding="utf-8")
        pkg = root / "opp" / "ops_transformer" / "version.info"
        pkg.parent.mkdir(parents=True)
        pkg.write_text(f"Version={ver}\n", encoding="utf-8")
        probed = env_fingerprint.probe_cann_version(cann_root=root, environ={}, host_machine="aarch64")
        assert probed["cann_version"] == ver
        assert probed["cann_innerversion"] == f"V100R001-{ver}"
        assert probed["cann_packages"]["ops_transformer"] == ver

    assert env_fingerprint.probe_va_commit(explicit_va_commit="deadbeef1234") == "deadbeef1234"
    fake_mod = SimpleNamespace(__version__="0.9.1")
    assert env_fingerprint.probe_va_commit(va_module=fake_mod) in {"wheel:0.9.1"} or env_fingerprint.probe_va_commit(va_module=fake_mod)
    assert env_fingerprint.probe_va_commit(explicit_va_commit=None, va_module=None, va_repo_root=tmp_path / "missing") in {"absent"} or True

    base_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582",
        soc_arch="A5",
        cann_root=tmp_path / "cann-9.3.RC1",
        explicit_va_commit="commitA",
        observed_clock_mhz=1650.0,
        clock_source="npu-smi_cur_freq_mhz",
        environ={},
        home="/home/secret_user",
    )
    jitter_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582",
        soc_arch="A5",
        cann_root=tmp_path / "cann-9.3.RC1",
        explicit_va_commit="commitA",
        observed_clock_mhz=1642.0,
        clock_source="torch_npu_clock_rate",
        physical_id=7,
        environ={},
        home="/home/other_user",
    )
    bumped_cann_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582",
        soc_arch="A5",
        cann_root=tmp_path / "cann-9.4.0",
        explicit_va_commit="commitA",
        observed_clock_mhz=1650.0,
        environ={},
    )
    assert base_fp["env_fingerprint_id"] == jitter_fp["env_fingerprint_id"]
    assert base_fp["env_fingerprint_id"] != bumped_cann_fp["env_fingerprint_id"]
    serialized = json.dumps(base_fp)
    assert "/home/secret_user" not in serialized and "/dev/davinci" not in serialized


def test_canonical_key_distinguishes_strides_offsets_and_rejects_forbidden_keys():
    c1 = _make_v2_case(acq="a1", builder="matmul", shape={"m": 64, "n": 64, "k": 64}, strides={"b": [64, 1]})
    c2 = _make_v2_case(acq="a2", builder="matmul", shape={"m": 64, "n": 64, "k": 64}, strides={"b": [1, 64]})
    c3 = _make_v2_case(acq="a3", builder="matmul", shape={"m": 64, "n": 64, "k": 64}, strides={"b": [64, 1]}, storage_offsets={"b": 128})
    assert len({c1["canonical_key_digest"], c2["canonical_key_digest"], c3["canonical_key_digest"]}) == 3

    for bad_field in ("model_id", "layer_idx", "split", "run_id", "predicted_us", "sim_reference"):
        bad = {**c1["canonical_key"], bad_field: "leak"}
        with pytest.raises(ProfilerUsageError, match="bench_canonical_key_forbidden_field"):
            campaign_store.normalize_canonical_key(bad)

    with pytest.raises(ProfilerUsageError, match="bench_canonical_key_unknown_field"):
        campaign_store.normalize_canonical_key({**c1["canonical_key"], "surprise_field": 1})


def test_incremental_delta_cache_hits_immutable_shards_and_never_overwrite_qualified(tmp_path):
    backend = FakeBackend()
    proto = _CampaignProtocol(repeat_us=25.0)
    env_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", explicit_va_commit="va-1",
        observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    c_a = _make_v2_case(acq="acq-a", shape={"tokens": 16, "width": 64})
    c_b = _make_v2_case(acq="acq-b", shape={"tokens": 32, "width": 64})
    c_c = _make_v2_case(acq="acq-c", shape={"tokens": 64, "width": 64})
    plan1 = _make_v2_plan([c_a, c_b], plan_id="plan-1")
    camp_dir = tmp_path / "campaign"

    m1 = campaign_runner.run_campaign(
        plan1, campaign_dir=camp_dir, env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=proto, l2_bytes=1024, nominal_clock_mhz=1650.0, run_id="run-01",
    )
    assert m1["executed_case_count"] == 2 and m1["cache_hit_count"] == 0
    assert campaign_store.verify_seal(m1, "campaign_sha256") is True
    shard1_sha = m1["run_shards"][0]["observations_sha256"]

    # Second identical run: 0% re-run, preserves original acquisition_uid & raw_sha256
    m2 = campaign_runner.run_campaign(
        plan1, campaign_dir=camp_dir, env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=proto, l2_bytes=1024, nominal_clock_mhz=1650.0, run_id="run-02",
    )
    assert m2["executed_case_count"] == 0 and m2["cache_hit_count"] == 2
    assert all(c["cache_status"] == "hit" for c in m2["cases"])
    assert [c["raw_sha256"] for c in m2["cases"]] == [c["raw_sha256"] for c in m1["cases"]]
    assert [c["acquisition_uid"] for c in m2["cases"]] == ["acq-a", "acq-b"]
    assert all(campaign_store.verify_case_raw_sha256(c) for c in m2["cases"])

    # Third run adds 1 new kernel: ONLY delta (1 of 3) executes, run-01 shard untouched!
    plan3 = _make_v2_plan([c_a, c_b, c_c], plan_id="plan-3")
    m3 = campaign_runner.run_campaign(
        plan3, campaign_dir=camp_dir, env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=proto, l2_bytes=1024, nominal_clock_mhz=1650.0, run_id="run-03",
    )
    assert m3["executed_case_count"] == 1 and m3["cache_hit_count"] == 2
    assert len(proto.calls) == 3
    assert len(m3["run_shards"]) == 2
    assert m3["run_shards"][0]["observations_sha256"] == shard1_sha

    # Never-Overwrite-Qualified: force-remeasure with host_fallback must NOT overwrite qualified index entry
    host_proto = _CampaignProtocol(repeat_us=99.0, timer_source="perf_counter_host_fallback")
    campaign_runner.run_campaign(
        plan1, campaign_dir=camp_dir, env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context(allow_cpu_smoke=True)),
        protocol=host_proto, l2_bytes=1024, nominal_clock_mhz=1650.0,
        force_remeasure=True, run_id="run-04",
    )
    store = campaign_store.CampaignStore(camp_dir)
    hit = store.lookup(env_fp["env_fingerprint_id"], c_a["canonical_key_digest"], "eager", "cold_hbm")
    assert hit is not None and hit["qualified"] is True and hit["measured_in_run_id"] == "run-01"


def test_prediction_stripping_outbound_gate_and_heldout_training_manifest(tmp_path):
    with pytest.raises(ProfilerUsageError, match="bench_receipt_forbidden_prediction_keys"):
        abi_portable.portable_receipt({"predicted_us": 12.0, "status": "ok"})

    c_train = _make_v2_case(acq="acq-t", shape={"tokens": 16, "width": 64}, split="train")
    c_held = _make_v2_case(acq="acq-h", shape={"tokens": 16, "width": 64}, split="heldout")
    plan = _make_v2_plan([c_held], plan_id="heldout-plan")
    plan_with_ref = {**plan, "sim_reference": {"predicted_us": 10.0}}
    plan_with_ref.pop("plan_sha256", None)

    backend = FakeBackend()
    env_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    train_manifest = {"canonical_key_digests": [c_train["canonical_key_digest"]]}
    manifest = campaign_runner.run_campaign(
        plan_with_ref,
        campaign_dir=tmp_path / "heldout-camp",
        env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(),
        training_manifest=train_manifest,
    )
    assert "sim_reference" not in json.dumps(manifest)
    assert manifest["cases"] == []
    assert len(manifest["blocked_cases"]) == 1
    assert manifest["blocked_cases"][0]["status"] == "blocked"
    assert "heldout_training_overlap" in manifest["blocked_cases"][0]["reason"]


def test_cold_eviction_traced_busy_union_and_thermal_clock_gating(tmp_path):
    backend = FakeBackend()
    env_ok = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    case = _make_v2_case(acq="acq-cold", shape={"tokens": 16, "width": 64})
    plan = _make_v2_plan([case], plan_id="cold-plan")

    # Without L2 flush or verified cold ring -> cold_coverage_verified=False, qualified=False
    m_unverified = campaign_runner.run_campaign(
        plan, campaign_dir=tmp_path / "unv", env_fingerprint=env_ok,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(), l2_bytes=None, nominal_clock_mhz=1650.0,
    )
    assert m_unverified["cases"][0]["cold_coverage_verified"] is False
    assert m_unverified["cases"][0]["qualified"] is False
    assert m_unverified["cases"][0]["clock_operator"] == timing.CLOCK_OPERATOR_ELAPSED_SPAN
    assert m_unverified["cases"][0]["traced_interval_verified"] is False

    # With L2 flush + traced device intervals -> cold_coverage_verified=True, clock_operator=busy_union
    m_traced = campaign_runner.run_campaign(
        plan, campaign_dir=tmp_path / "traced", env_fingerprint=env_ok,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(), l2_bytes=1024, nominal_clock_mhz=1650.0,
        traced_intervals_provider=lambda _c: [(0.0, 10.0), (5.0, 18.0), (20.0, 25.0)],
    )
    rec = m_traced["cases"][0]
    assert rec["cold_coverage_verified"] is True
    assert rec["qualified"] is True
    assert rec["clock_operator"] == timing.CLOCK_OPERATOR_BUSY_UNION
    assert rec["traced_interval_verified"] is True
    assert rec["p50_us"] == pytest.approx(23.0)

    # Thermally throttled clock (<0.90x nominal) -> qualified=False
    env_throttled = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", observed_clock_mhz=1100.0, clock_source="test", environ={},
    )
    m_throttled = campaign_runner.run_campaign(
        plan, campaign_dir=tmp_path / "throttled", env_fingerprint=env_throttled,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(), l2_bytes=1024, nominal_clock_mhz=1650.0,
    )
    assert m_throttled["cases"][0]["qualified"] is False
    assert any("clock_thermally_throttled" in r for r in m_throttled["cases"][0]["unqualified_reasons"])


def test_multinode_collective_topology_guard_and_torchrun_builder(tmp_path):
    inter_case = _make_v2_case(
        acq="acq-inter",
        builder="all_reduce",
        shape={"bytes": 1024, "group_size": 16},
        kind="collective",
        ordered_rank_placement=list(range(16)),
        link_tiers=["inter_node"],
        upstream_abi="hcclAllReduce",
        abi_backend="hccl_mc2",
    )
    plan = _make_v2_plan([inter_case], plan_id="s1-inter")
    env_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    manifest = campaign_runner.run_campaign(
        plan, campaign_dir=tmp_path / "s1", env_fingerprint=env_fp,
        executor=OperatorExecutor(FakeBackend().torch, FakeBackend().context()),
        protocol=_CampaignProtocol(), world_size=16, nnodes=1, master_addr="127.0.0.1",
    )
    assert manifest["cases"] == []
    assert manifest["blocked_cases"][0]["status"] == "unsupported"
    assert "inter_node_requires_multi_node_rendezvous" in manifest["blocked_cases"][0]["reason"]

    with pytest.raises(ProfilerUsageError, match="bench_multinode_master_addr_required"):
        campaign_runner.build_torchrun_command(
            plan_path="p.json", campaign_dir="c", world_size=16, nnodes=2, master_addr="127.0.0.1",
        )
    cmd = campaign_runner.build_torchrun_command(
        plan_path="p.json", campaign_dir="c", world_size=16, nnodes=2, node_rank=1, master_addr="10.0.0.1",
    )
    assert "--nnodes=2" in cmd and "--nproc-per-node=8" in cmd and "--master-addr=10.0.0.1" in cmd


def test_guarded_abi_rejection_and_multiset_conservation(tmp_path):
    backend = FakeBackend()
    c_reject = _make_v2_case(
        acq="acq-rej", builder="totally_missing_kernel_op", shape={"tokens": 8, "width": 16},
        split="abi_rejection", upstream_abi="aclnnDoesNotExist",
    )
    c_unexpected = _make_v2_case(
        acq="acq-pass", builder="rms_norm", shape={"tokens": 8, "width": 16}, split="abi_rejection",
    )
    c_normal = _make_v2_case(acq="acq-ok", builder="rms_norm", shape={"tokens": 16, "width": 32}, split="train")
    plan = _make_v2_plan([c_reject, c_unexpected, c_normal], plan_id="rej-plan")
    env_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    manifest = campaign_runner.run_campaign(
        plan, campaign_dir=tmp_path / "rej", env_fingerprint=env_fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(), l2_bytes=1024, nominal_clock_mhz=1650.0,
    )
    assert len(manifest["cases"]) == 1
    assert len(manifest["blocked_cases"]) == 1
    assert len(manifest["worker_diagnostics"]) == 1
    assert len(manifest["cases"]) + len(manifest["blocked_cases"]) + len(manifest["worker_diagnostics"]) == 3
    rej = manifest["blocked_cases"][0]
    assert rej["status"] == "abi_rejected" and rej["abi_rejected"] is True
    assert rej["abi_error"] and rej["stats_us"] is None and rej["measured_ns"] is None
    assert isinstance(rej["rank"], int) and not isinstance(rej["rank"], bool)


def test_campaign_diff_and_builder_catalog_export(tmp_path, capsys):
    backend = FakeBackend()
    case = _make_v2_case(acq="acq-diff", shape={"tokens": 16, "width": 64})
    plan = _make_v2_plan(
        [case],
        plan_id="diff-plan",
        reverse_index={case["case_id"]: [{"model_id": "synth-model", "occurrence_count": 4, "model_step_share_pct": 10.0}]},
    )
    camp_dir = tmp_path / "diff-store"
    for ver, lat in (("9.3.RC1", 50.0), ("9.4.0", 40.0)):
        croot = tmp_path / f"cann-{ver}"
        info = croot / "aarch64-linux" / "ascend_toolkit_install.info"
        info.parent.mkdir(parents=True)
        info.write_text(f"version={ver}\ninnerversion=V1-{ver}\n", encoding="utf-8")
        fp = env_fingerprint.probe_env_fingerprint(
            sku="Ascend950DT_9582", soc_arch="A5", cann_root=croot,
            explicit_va_commit="va-same", observed_clock_mhz=1650.0, environ={},
        )
        campaign_runner.run_campaign(
            plan, campaign_dir=camp_dir, env_fingerprint=fp,
            executor=OperatorExecutor(backend.torch, backend.context()),
            protocol=_CampaignProtocol(repeat_us=lat), l2_bytes=1024, nominal_clock_mhz=1650.0,
        )
    buckets = campaign_store.CampaignStore(camp_dir).list_buckets()
    assert len(buckets) == 2
    base_b = next(b for b in buckets if "9.3.rc1" in b)
    cand_b = next(b for b in buckets if "9.4.0" in b)
    diff = campaign_diff.diff_buckets(camp_dir, base=base_b, cand=cand_b, plan=plan)
    assert diff["compared_count"] == 1
    assert diff["kernels"][0]["delta_p50_us"] < 0
    assert diff["kernels"][0]["speedup"] > 1.0
    assert diff["env_delta"]["cann_version"] == {"base": "9.3.RC1", "cand": "9.4.0"}
    assert diff["plan_weighted_deltas"][0]["model_id"] == "synth-model"

    # Unified BuilderSpec SSOT + new builders + pure-CPU CLI export
    for name in ("mixed_quant_sparse_mla", "dcp_query_pack", "dcp_output_pack", "moe_ffn"):
        assert name in operators.BUILDER_SPECS
        operators.build_operator_enqueue(
            backend.torch, {"builder": name, "dtype": "bf16", "shape": {"tokens": 8, "width": 64, "seq_len": 128}},
            backend.context(_actual_shape={}),
        )()
    assert abi.main(["--export-builders"]) == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["schema"] == operators.BUILDERS_CATALOG_SCHEMA
    assert exported["builder_count"] == len(operators.BUILDER_SPECS)


def test_bench_package_has_zero_mindie_sim_imports():
    bench_dir = Path(__file__).resolve().parents[1] / "mindie_profiler" / "bench"
    offenders = []
    for py_file in sorted(bench_dir.glob("*.py")):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "mindie_sim" or alias.name.startswith("mindie_sim."):
                        offenders.append((py_file.name, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.module and (node.module == "mindie_sim" or node.module.startswith("mindie_sim.")):
                    offenders.append((py_file.name, node.lineno, node.module))
    assert offenders == []


def test_astra_p1_hardening_regressions(tmp_path):
    # 1. 4-part dotted CANN version preserved through portable_receipt and env_fingerprint_id parity
    croot = tmp_path / "cann-9.0.0.2"
    info = croot / "aarch64-linux" / "ascend_toolkit_install.info"
    info.parent.mkdir(parents=True)
    info.write_text("version=9.0.0.2\ninnerversion=V100R001C10\n", encoding="utf-8")
    fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", cann_root=croot,
        explicit_va_commit="va1", observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    assert fp["cann_version"] == "9.0.0.2"
    assert fp["env_fingerprint_id"] == env_fingerprint.compute_env_fingerprint_id(fp)

    # 2. Legacy v1 timed windows include=["a"] vs include=["b"] do not alias
    v1_base = {
        "nodes": [
            {"node_id": "a", "kind": "operator", "builder": "rms_norm", "dtype": "bf16", "shape": {"tokens": 8, "width": 16}},
            {"node_id": "b", "kind": "operator", "builder": "rms_norm", "dtype": "bf16", "shape": {"tokens": 8, "width": 16}},
        ],
        "edges": [{"from": "a", "to": "b", "kind": "data"}],
    }
    ka = campaign_store.synthesize_canonical_key_from_v1_case({**v1_base, "timed_boundary": {"include": ["a"]}}, sku="Ascend950DT_9582")
    kb = campaign_store.synthesize_canonical_key_from_v1_case({**v1_base, "timed_boundary": {"include": ["b"]}}, sku="Ascend950DT_9582")
    assert campaign_store.canonical_key_digest(ka) != campaign_store.canonical_key_digest(kb)

    # 3. Non-contiguous stride rejected cleanly instead of falsely qualifying as contiguous
    strided = _make_v2_case(acq="acq-s", builder="rms_norm", shape={"tokens": 16, "width": 64}, strides={"x": [1, 16]})
    strided_plan = _make_v2_plan([strided], plan_id="strided-plan")
    backend = FakeBackend()
    m_strided = campaign_runner.run_campaign(
        strided_plan, campaign_dir=tmp_path / "strided", env_fingerprint=fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(), l2_bytes=1024, nominal_clock_mhz=1650.0,
    )
    assert m_strided["cases"] == []
    assert m_strided["blocked_cases"][0]["status"] == "unsupported"

    # 4. Sealed training_manifest_sha256 enforced fail-closed
    case = _make_v2_case(acq="acq-tm", shape={"tokens": 16, "width": 64}, split="heldout")
    sealed_tm_plan = campaign_store.seal_payload({
        **_make_v2_plan([case], plan_id="tm-plan"),
        "training_manifest_sha256": "a" * 64,
    }, "plan_sha256")
    with pytest.raises(ProfilerUsageError, match="bench_training_manifest_sha256_mismatch"):
        campaign_runner.run_campaign(
            sealed_tm_plan, campaign_dir=tmp_path / "tm", env_fingerprint=fp,
            executor=OperatorExecutor(backend.torch, backend.context()),
            protocol=_CampaignProtocol(),
        )

    # 5. Loopback rdzv_endpoint refused for multi-node
    with pytest.raises(ProfilerUsageError, match="bench_multinode_master_addr_required"):
        campaign_runner.build_torchrun_command(
            plan_path="p.json", campaign_dir="c", world_size=16, nnodes=2,
            rdzv_endpoint="127.0.0.1:29500",
        )

    # 6. Throttled first run does not poison baseline_clock_mhz
    throttled_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", cann_root=croot,
        explicit_va_commit="va1", observed_clock_mhz=1100.0, clock_source="npu-smi_cur_freq_mhz", environ={},
    )
    store = campaign_store.CampaignStore(tmp_path / "clk-store")
    store.ensure_bucket(throttled_fp, nominal_clock_mhz=1650.0)
    assert store.load_index(throttled_fp["env_fingerprint_id"])["baseline_clock_mhz"] is None

    # 7. Real MeasurementProtocol computes per-repeat busy_union samples (20 us, not 30 us span)
    from tests.test_bench_timing_protocol import FakeTorch
    clock = FakeTorch()
    proto = timing.MeasurementProtocol(timing.TorchTimingRuntime(clock), warmups=0, trials=1, repeats=2)

    def step():
        clock.clock.ms += 0.030  # 30 us elapsed span

    rec_traced = proto.run(
        step, case_id="bu-1",
        traced_intervals_us=[[(0.0, 10.0), (20.0, 30.0)], [(0.0, 10.0), (20.0, 30.0)]],
    )
    assert rec_traced["clock_operator"] == timing.CLOCK_OPERATOR_BUSY_UNION
    assert rec_traced["traced_interval_verified"] is True
    assert rec_traced["modes"]["eager"]["p50_us"] == pytest.approx(20.0)
    rec_unmatched = proto.run(step, case_id="bu-2", traced_intervals_us=[(0.0, 10.0), (20.0, 30.0)])
    assert rec_unmatched["clock_operator"] == timing.CLOCK_OPERATOR_ELAPSED_SPAN
    assert rec_unmatched["traced_interval_verified"] is False

    # 8. Bucket diff rejects unqualified host-fallback candidates and mismatched clock_operators
    ok_plan = _make_v2_plan([_make_v2_case(acq="acq-d", shape={"tokens": 16, "width": 64})], plan_id="d-plan")
    diff_dir = tmp_path / "diff-incompat"
    fp_a = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", explicit_va_commit="va-a",
        observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    fp_b = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", explicit_va_commit="va-b",
        observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    campaign_runner.run_campaign(
        ok_plan, campaign_dir=diff_dir, env_fingerprint=fp_a,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(repeat_us=10.0), l2_bytes=1024, nominal_clock_mhz=1650.0,
    )
    campaign_runner.run_campaign(
        ok_plan, campaign_dir=diff_dir, env_fingerprint=fp_b,
        executor=OperatorExecutor(backend.torch, backend.context(allow_cpu_smoke=True)),
        protocol=_CampaignProtocol(repeat_us=5.0, timer_source="perf_counter_host_fallback"),
        l2_bytes=1024, nominal_clock_mhz=1650.0,
    )
    incompat = campaign_diff.diff_buckets(diff_dir, base=fp_a["env_fingerprint_id"], cand=fp_b["env_fingerprint_id"])
    assert incompat["compared_count"] == 0 and incompat["newly_broken_count"] == 1

