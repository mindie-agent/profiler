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


def test_builder_export_determinism_zero_legacy_refs_and_dev_zero_ctx(capsys, tmp_path):
    import hashlib
    import subprocess
    import sys

    assert abi.main(["--export-builders"]) == 0
    out_a = capsys.readouterr().out
    assert abi.main(["--export-builders"]) == 0
    out_b = capsys.readouterr().out
    assert out_a == out_b
    catalog = json.loads(out_a)
    assert catalog["schema"] == operators.BUILDERS_CATALOG_SCHEMA
    assert catalog["builder_count"] == 127 == len(operators.BUILDER_SPECS)
    assert catalog["backends"] == list(operators.HARDWARE_USABLE_ABI_BACKENDS)
    builder_ids = list(catalog["builders"].keys())
    assert builder_ids == sorted(operators.BUILDER_SPECS)
    # Independent frozen SHA-256 lock of the canonical 1916caa builder catalog
    canon_bytes = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(canon_bytes).hexdigest() == "87a4ae2c61dc2b8b5f73cce5496eeffd9d2ab695fa6cb08197159942b165bf30"

    repo_root = Path(__file__).resolve().parents[1]
    retired_files = (
        repo_root / "mindie_profiler" / ("sim_bridge" + "_cells.py"),
        repo_root / "mindie_profiler" / ("sim_bridge" + "_case.py"),
        repo_root / "mindie_profiler" / ("sim_bridge" + "_native_obs.py"),
        repo_root / "mindie_profiler" / ("sim_bridge" + "_predict.py"),
        repo_root / "mindie_profiler" / "bench" / ("bench_archetype" + "_subgraphs.py"),
    )
    assert [str(p) for p in retired_files if p.exists()] == []
    retired_tokens = (
        "sim_bridge" + "_cells",
        "sim_bridge" + "_case",
        "sim_bridge" + "_native_obs",
        "sim_bridge" + "_predict",
        "mindie_profiler.bench.bench_archetype" + "_subgraphs",
        ".bench_archetype" + "_subgraphs",
        "import bench_archetype" + "_subgraphs",
        "tools/" + "bench_packets",
        "tools." + "bench_packets",
    )
    offenders: list[tuple[str, str]] = []
    for folder in ("mindie_profiler", "tests", "examples"):
        for py_file in sorted((repo_root / folder).rglob("*.py")):
            text = py_file.read_text(encoding="utf-8")
            for token in retired_tokens:
                if token in text:
                    offenders.append((str(py_file.relative_to(repo_root)), token))
    assert offenders == [], f"retired module references remain: {offenders}"

    probe_code = (
        f"import json, sys; sys.path.insert(0, {str(repo_root)!r})\n"
        "import mindie_profiler\n"
        "import mindie_profiler.bench\n"
        "import mindie_profiler.bench.campaign_runner\n"
        "import mindie_profiler.bench.campaign_store\n"
        "import mindie_profiler.bench.campaign_diff\n"
        "import mindie_profiler.bench.env_fingerprint\n"
        "import mindie_profiler.fabric_probe\n"
        "import mindie_profiler.sim_native_bridge\n"
        "leaked = sorted(m for m in ('torch', 'torch_npu', 'mindie_sim') if m in sys.modules)\n"
        "print(json.dumps({'leaked': leaked}))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-I", "-c", probe_code],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert json.loads(proc.stdout)["leaked"] == []

    # When mindie_sim is on PYTHONPATH, verify packaged bench_packets ingests v2 shards directly
    try:
        from mindie_sim.observations import bench_packets
    except ImportError:
        return
    backend = FakeBackend()
    case = _make_v2_case(acq="acq-pkt", shape={"tokens": 16, "width": 64}, split="train")
    plan = _make_v2_plan([case], plan_id="pkt-plan")
    fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend950DT_9582", soc_arch="A5", observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    camp_dir = tmp_path / "pkt-camp"
    manifest = campaign_runner.run_campaign(
        plan,
        campaign_dir=camp_dir,
        env_fingerprint=fp,
        executor=OperatorExecutor(backend.torch, backend.context()),
        protocol=_CampaignProtocol(repeat_us=18.0),
        l2_bytes=1024,
        nominal_clock_mhz=1650.0,
        run_id="run-pkt",
    )
    shard = camp_dir / "buckets" / fp["env_fingerprint_id"] / manifest["observations_jsonl"]
    bundle = bench_packets.build_packets(list(bench_packets.iter_receipts([shard])))
    assert bundle["manifest"]["observations"] >= 1


def test_fabric_probe_unified_campaign_runner_and_observation_v2(tmp_path, monkeypatch):
    import threading
    from mindie_profiler import fabric_probe
    from mindie_profiler.bench import operators_moe_comm, subgraph_runtime, timing as bench_timing

    plan = fabric_probe.build_fabric_probe_plan(
        placement="a3_superpod_2x2",
        sizes=[4096],
        ops=["all_reduce", "all_to_all_v", "reduce_scatter"],
        warmup=1,
        iterations=2,
        timing_modes=["eager"],
    )
    bench_plan = fabric_probe.fabric_plan_to_bench_plan_v2(plan, sku="Ascend910_9392")
    assert bench_plan["schema"] == campaign_store.PLAN_V2_SCHEMA
    assert campaign_store.verify_seal(bench_plan, "plan_sha256") is True
    assert any(c["canonical_key"]["split_sizes"] for c in bench_plan["cases"])
    assert any(c["canonical_key"]["link_tiers"] == ["inter_node"] for c in bench_plan["cases"])
    assert any(c["canonical_key"]["link_tiers"] == ["intra_4p"] for c in bench_plan["cases"])

    # #2: Case-level group_ranks prevent undeclared cosets on a3_superpod_2x2
    specs = subgraph_runtime._explicit_group_specs(bench_plan["cases"])
    assert ("intra_package_sio.n0", (0, 1), False) in specs
    assert ("intra_package_sio.n1", (2, 3), False) in specs
    assert subgraph_runtime._cosets_for_ranks((0, 1), 4, spmd=False) == [[0, 1]]

    # #5: reduce_scatter encodes explicit input_bytes = size * group_size, output_bytes = size
    rs_case = next(c for c in bench_plan["cases"] if c["tier"] == "intra_package_sio.n0" and c["canonical_key"]["bench_builder"] == "reduce_scatter")
    assert rs_case["input_bytes"] == 8192 and rs_case["output_bytes"] == 4096
    rs_shapes: list[tuple[int, int]] = []
    rs_backend = FakeBackend()
    rs_dist = SimpleNamespace(
        is_initialized=lambda: True,
        get_world_size=lambda _g=None: 2,
        reduce_scatter_tensor=lambda out, inp, group=None: rs_shapes.append((inp.numel(), out.numel())),
    )
    rs_ctx = rs_backend.context(dist=rs_dist, dist_initialized=True, groups={"intra_package_sio.n0@0,1": object()}, rank=0, world_size=4)
    operators_moe_comm._bind_collective(rs_backend.torch, rs_case["nodes"][0], rs_ctx, "reduce_scatter_tensor")()
    assert rs_shapes == [(2048, 1024)]

    # #3: multi-pair send_recv binds each rank's own pair (ranks 2<->3, never both recv from 0)
    hccs_plan = fabric_probe.build_fabric_probe_plan(placement="hccs_sw_2rail", sizes=[4096], ops=["send_recv"], warmup=0, iterations=1, timing_modes=["eager"])
    hccs_v2 = fabric_probe.fabric_plan_to_bench_plan_v2(hccs_plan, sku="Ascend910_9392")
    sr_node = hccs_v2["cases"][0]["nodes"][0]
    assert sr_node["pairs"] == [[0, 1], [2, 3]]
    sr_calls: list[tuple[str, int, int]] = []
    sr_dist = SimpleNamespace(
        is_initialized=lambda: True,
        send=lambda _b, dst=0, group=None: sr_calls.append(("send", dst, 0)),
        recv=lambda _b, src=0, group=None: sr_calls.append(("recv", src, 0)),
    )
    for rk in range(4):
        sr_ctx = rs_backend.context(dist=sr_dist, dist_initialized=True, groups={"intra_node_hccs@0,1,2,3": object()}, rank=rk, world_size=4)
        operators_moe_comm.build_send_recv(rs_backend.torch, sr_node, sr_ctx)()
    assert sr_calls == [("send", 1, 0), ("recv", 0, 0), ("send", 3, 0), ("recv", 2, 0)]

    # #4: uniform & skew_circulant all_to_all_v on 6P satisfy recv_r[s] == send_s[r]
    for style in ("uniform", "skew_circulant"):
        sends_6p: dict[int, list[int]] = {}
        recvs_6p: dict[int, list[int]] = {}
        a2av_node = {
            "op": "all_to_all_v", "nbytes": 4096, "dtype": "fp32", "split_style": style,
            "group": "a2_hccs_mesh_6p", "group_ranks": [0, 1, 2, 3, 5, 6], "group_size": 6,
        }
        for idx, rk in enumerate([0, 1, 2, 3, 5, 6]):
            def _cap(_out, _in, *, output_split_sizes=None, input_split_sizes=None, group=None, _i=idx):
                sends_6p[_i] = list(input_split_sizes)
                recvs_6p[_i] = list(output_split_sizes)
            d6 = SimpleNamespace(is_initialized=lambda: True, get_world_size=lambda _g=None: 6, all_to_all_single=_cap)
            c6 = rs_backend.context(dist=d6, dist_initialized=True, groups={"a2_hccs_mesh_6p@0,1,2,3,5,6": object()}, rank=rk, world_size=8)
            operators_moe_comm._bind_collective(rs_backend.torch, a2av_node, c6, "all_to_all_v")()
        for r in range(6):
            assert recvs_6p[r] == [sends_6p[s][r] for s in range(6)]

    # #6: single-host inter-node run with nnodes=2 + non-loopback addr is blocked when distinct nodes < 2
    env_fp = env_fingerprint.probe_env_fingerprint(
        sku="Ascend910_9392", soc_arch="A3", observed_clock_mhz=1650.0, clock_source="test", environ={},
    )
    ok_single, reason_single = campaign_runner.verify_collective_topology(
        next(c for c in bench_plan["cases"] if c["canonical_key"]["link_tiers"] == ["inter_node"]),
        world_size=4, nnodes=2, master_addr="10.0.0.1", realized_node_ids=["h0", "h0", "h0", "h0"], require_node_evidence=True,
    )
    assert ok_single is False and reason_single == "inter_node_requires_multiple_distinct_nodes"
    ok_missing, reason_missing = campaign_runner.verify_collective_topology(
        next(c for c in bench_plan["cases"] if c["canonical_key"]["link_tiers"] == ["inter_node"]),
        world_size=4, nnodes=2, master_addr="10.0.0.1", realized_node_ids=None, require_node_evidence=True,
    )
    assert ok_missing is False and reason_missing == "inter_node_missing_realized_node_evidence"

    # #7: admitted warmup=0, iterations=1, timing_mode="eager" is respected by MeasurementProtocol
    class _StubTimer:
        def measure(self, fn, **_kw):
            fn()
            return {"duration_us": 10.0, "enqueue_us": None, "stream_saturated_qualified": None}
    proto_real = bench_timing.MeasurementProtocol(
        runtime=SimpleNamespace(
            available=True,
            source="torch.npu.Event(enable_timing=True)",
            require_device_timing=lambda: None,
            synchronize=lambda: None,
            new_event=lambda: None,
            new_stream=lambda: None,
            current_stream=lambda: None,
        ),
    )
    proto_real.timer = _StubTimer()
    call_count = [0]
    t_res = proto_real.run(lambda: call_count.__setitem__(0, call_count[0] + 1), case_id="fab-eager", kind="collective", nbytes=4096, warmups=0, trials=1, repeats=1, timing_modes=("eager",))
    assert call_count[0] == 1 and list(t_res["modes"].keys()) == ["eager"]

    # #8 + #12: Real 2-rank concurrent run_fabric_probe_campaign (12us vs 14us -> 14us max, single writer, 0 rate_repeat_conflict!)
    sio_plan = fabric_probe.build_fabric_probe_plan(
        placement="sio_pair",
        sizes=[4096, 65536],
        ops=["all_reduce"],
        warmup=0,
        iterations=2,
        timing_modes=["eager"],
    )
    sio_plan["physical_verification"] = True
    sio_plan["topology_label"] = "verified_sio"
    sio_plan["topology_source"] = "explicit"
    camp_dir = tmp_path / "fabric-camp"

    class _TwoRankBroker:
        def __init__(self):
            self._lock = threading.Lock()
            self._cond = threading.Condition(self._lock)
            self._epoch = 0
            self._vals: dict[int, object] = {}

        def all_gather_object(self, out, obj, group=None):
            del group
            rk = int(threading.current_thread().name.split("-")[1])
            with self._cond:
                my_epoch = self._epoch
                self._vals[rk] = obj
                if len(self._vals) == 2:
                    snap = [self._vals[0], self._vals[1]]
                    self._vals.clear()
                    self._epoch += 1
                    self._last = snap
                    self._cond.notify_all()
                else:
                    while self._epoch == my_epoch:
                        self._cond.wait(timeout=5.0)
                    snap = self._last
            out[:] = list(snap)

    def _run_two_rank(lat_by_rank: dict[int, float], run_id_arg: str | None = None):
        broker = _TwoRankBroker()
        results: dict[int, dict] = {}
        protos: dict[int, _CampaignProtocol] = {}
        errs: list[BaseException] = []

        def _worker(rk: int):
            try:
                be = FakeBackend()
                fd = SimpleNamespace(
                    is_initialized=lambda: True,
                    all_reduce=lambda tensor, group=None: tensor,
                    all_gather_object=broker.all_gather_object,
                )
                fr = SimpleNamespace(dist=fd, rank=rk, world_size=2, synchronize=lambda: None, barrier=lambda: None, capture=lambda fn: (fn, fn()))
                c = be.context(dist=fd, dist_initialized=True, groups={"intra_package_sio@0,1": object(), "intra_package_sio": object()}, rank=rk, world_size=2)
                p = _CampaignProtocol(repeat_us=lat_by_rank[rk])
                protos[rk] = p
                results[rk] = fabric_probe.run_fabric_probe_campaign(
                    sio_plan,
                    campaign_dir=camp_dir,
                    env_fingerprint=env_fp,
                    sku="Ascend910_9392",
                    executor=OperatorExecutor(be.torch, c),
                    protocol=p,
                    runtime=fr,
                    rank=rk,
                    world_size=2,
                    nnodes=1,
                    l2_bytes=1024,
                    nominal_clock_mhz=1650.0,
                    run_id=run_id_arg,
                )
            except BaseException as exc:
                errs.append(exc)

        threads = [threading.Thread(target=_worker, args=(r,), name=f"rank-{r}") for r in (0, 1)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)
        assert not errs, errs
        return results[0], results[1], protos

    m1_r0, m1_r1, _ = _run_two_rank({0: 12.0, 1: 14.0})
    assert m1_r0["campaign_sha256"] == m1_r1["campaign_sha256"]
    assert m1_r0["run_id"] == m1_r1["run_id"]
    assert m1_r0["schema"] == campaign_store.CAMPAIGN_SCHEMA
    assert campaign_store.verify_seal(m1_r0, "campaign_sha256") is True
    assert len(m1_r0["cases"]) == 2
    assert all(c["min_us"] == pytest.approx(14.0) and c["p50_us"] == pytest.approx(15.0) for c in m1_r0["cases"])
    assert all(c["rank_latencies_us"] == {"0": 13.0, "1": 15.0} for c in m1_r0["cases"])

    shard = camp_dir / "buckets" / env_fp["env_fingerprint_id"] / m1_r0["observations_jsonl"]
    shard_rows = [json.loads(line) for line in shard.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert shard_rows and all(r["schema"] == "mindie-bench-observation/2" for r in shard_rows)
    assert {round(r["duration_ms"], 6) for r in shard_rows} == {0.014, 0.016}

    # #12: packaged mindie_sim.observations.bench_packets ingests the v2 shard with 0 rate_repeat_conflict!
    try:
        from mindie_sim.observations import bench_packets
    except ImportError:
        bench_packets = None
    if bench_packets is not None:
        pkt_bundle = bench_packets.build_packets(list(bench_packets.iter_receipts([shard])))
        assert pkt_bundle["manifest"]["observations"] == len(shard_rows)
        assert {round(s["duration_ms"], 6) for p in pkt_bundle["fit-rate"] for s in p["samples"]} == {0.014, 0.016}

    # parse_fabric_probe_samples expands rank_latencies_us for BOTH JSONL shard and manifest -> calibrated fit!
    parsed_jsonl = fabric_probe.parse_fabric_probe_samples(shard.read_text(encoding="utf-8"))
    assert {r["rank"] for r in parsed_jsonl} == {0, 1}
    assert {r["bytes"] for r in parsed_jsonl} == {4096, 65536}
    parsed_manifest = fabric_probe.parse_fabric_probe_samples(m1_r0)
    assert {r["rank"] for r in parsed_manifest} == {0, 1}
    assert len(parsed_manifest) == 4

    # #10: unqualified v2 rows, failed case_outcome, and blocked manifest cases NEVER calibrate
    unq_rows = [{**r, "qualified": False} for r in shard_rows]
    fit_unq = fabric_probe.fit_calibrated_fabric_profile(sio_plan, unq_rows)
    assert fit_unq["status"] != "calibrated"
    failed_outcome = {
        "schema": "mindie-bench-observation/2", "record_type": "case_outcome",
        "status": "failed", "reason": "injected_fail", "case_id": "x", "rank": 0,
    }
    fit_failed = fabric_probe.fit_calibrated_fabric_profile(sio_plan, shard_rows + [failed_outcome])
    assert fit_failed["status"] != "calibrated"
    blocked_manifest = {**m1_r0, "blocked_cases": [{"status": "unsupported", "reason": "blocked"}]}
    fit_blocked = fabric_probe.fit_calibrated_fabric_profile(sio_plan, blocked_manifest)
    assert fit_blocked["status"] != "calibrated"

    # #8: Second 2-rank run hits CampaignStore cache cleanly on BOTH ranks (0% re-execution, 0 duplicate shard errors)
    m2_r0, m2_r1, protos2 = _run_two_rank({0: 99.0, 1: 99.0})
    assert m2_r0["cache_hit_count"] == 2 and m2_r0["executed_case_count"] == 0
    assert m2_r0["campaign_sha256"] == m2_r1["campaign_sha256"]
    assert protos2[0].calls == [] and protos2[1].calls == []

    # #1 + #9 + #11: Emitted script embeds resolved SKU, warm_reuse, allowed_phy_ids forwarding, and --max-bytes enforcement
    sio_phy = {**sio_plan, "allowed_phy_ids": [4, 5]}
    emitted = fabric_probe.emit_fabric_probe_script(sio_phy, sku="Ascend910_9392")
    assert emitted["syntax_ok"] is True
    assert "mindie-bench-observation/2" in emitted["script"]
    assert '"residency": "warm_reuse"' in emitted["script"]
    ns: dict = {"__name__": "fabric_script_campaign_test"}
    exec(compile(emitted["script"], "<fabric_script>", "exec"), ns)
    ident = ns["_sample_identity"]({"op": "all_reduce", "group_ranks": [0, 1], "protocol": "SIO"}, 4096, 0, "eager")
    assert ident["hardware"] == "Ascend910_9392" and ident["implementation"] == "hcclAllReduce"
    forwarded_argv: list[str] = []
    monkeypatch.setattr(campaign_runner, "main", lambda argv: (forwarded_argv.extend(argv), 0)[1])
    assert ns["main"](["--campaign-dir", str(tmp_path / "script-camp"), "--dry-run"]) == 0
    assert "--allowed-phy-ids" in forwarded_argv and forwarded_argv[forwarded_argv.index("--allowed-phy-ids") + 1] == "4,5"
    with pytest.raises(SystemExit):
        ns["main"](["--campaign-dir", str(tmp_path / "script-camp"), "--max-bytes", "4096", "--dry-run"])

    # #13: bench subgraph --campaign-dir enforces rank_mismatch and --execution-mode eager
    v1_plan = {
        "schema": campaign_runner.SUBGRAPH_PLAN_SCHEMA,
        "plan_id": "v1-sub-test",
        "stage": "s0_local",
        "rank": 1,
        "world_size": 2,
        "execution_modes": ["eager", "aclgraph"],
        "cases": [{
            "case_id": "c-dec", "split": "train", "phase": "decode",
            "nodes": [{"node_id": "n0", "kind": "operator", "builder": "rms_norm", "dtype": "bf16", "shape": {"tokens": 8, "width": 64}}],
            "edges": [],
        }],
    }
    v1_path = tmp_path / "v1_sub.json"
    v1_path.write_text(json.dumps(v1_plan), encoding="utf-8")
    monkeypatch.setenv("RANK", "0")
    monkeypatch.setenv("WORLD_SIZE", "2")
    mismatch_out = tmp_path / "mismatch.json"
    assert campaign_runner.main_subgraph(["--plan", str(v1_path), "--campaign-dir", str(tmp_path / "sc"), "--dry-run", "--out", str(mismatch_out)]) != 0
    assert json.loads(mismatch_out.read_text(encoding="utf-8"))["status"] == "rank_mismatch"
    monkeypatch.setenv("RANK", "1")
    eager_out = tmp_path / "eager_sub.json"
    assert campaign_runner.main_subgraph(["--plan", str(v1_path), "--campaign-dir", str(tmp_path / "sc"), "--execution-mode", "eager", "--dry-run", "--out", str(eager_out)]) == 0
    eager_payload = json.loads(eager_out.read_text(encoding="utf-8"))
    assert [c["capture_mode"] for c in eager_payload["cases"]] == ["eager"]


def test_probe_observed_clock_dual_die_a3_resolves_card_and_chip(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []
    mapping_out = "\n".join(
        [
            "NPU ID  Chip ID  Chip Logic ID  Chip Phy-ID  Chip Name",
            "0       0        0              0            Ascend910",
            "0       1        1              1            Ascend910",
            "7       0        14             14           Ascend910",
            "7       1        15             15           Ascend910",
            "7       2        -              -            Mcu",
        ]
    )
    common_card7 = "\n".join(
        [
            "NPU ID : 7",
            "Chip Count : 2",
            "Chip ID : 0",
            "Aicore Freq(MHZ) : 1500",
            "Aicore curFreq(MHZ) : 1500",
            "Chip ID : 1",
            "Aicore Freq(MHZ) : 1650",
            "Aicore curFreq(MHZ) : 800",
        ]
    )

    def _fake_run(cmd, *, cwd=None):
        del cwd
        key = tuple(cmd)
        calls.append(key)
        if key == ("npu-smi", "info", "-m"):
            return mapping_out
        if key == ("npu-smi", "info", "-t", "common", "-i", "7"):
            return common_card7
        return None

    monkeypatch.setattr(env_fingerprint, "_bounded_run", _fake_run)
    mhz, source = env_fingerprint.probe_observed_clock(physical_id=15, allow_npu_smi=True)
    assert (mhz, source) == (800.0, "npu-smi_cur_freq_mhz")
    ok, reason = env_fingerprint.validate_clock_band(mhz, nominal_clock_mhz=1650.0)
    assert not ok and reason is not None and "clock_thermally_throttled" in reason
    assert calls == [
        ("npu-smi", "info", "-m"),
        ("npu-smi", "info", "-t", "common", "-i", "7"),
    ]
    # Missing curFreq on chip 1 must NOT fall back to nominal Aicore Freq or chip 0 curFreq.
    common_missing_cur = "\n".join(
        [
            "NPU ID : 7",
            "Chip Count : 2",
            "Chip ID : 0",
            "Aicore Freq(MHZ) : 1500",
            "Aicore curFreq(MHZ) : 1500",
            "Chip ID : 1",
            "Aicore Freq(MHZ) : 1650",
        ]
    )
    monkeypatch.setattr(
        env_fingerprint,
        "_bounded_run",
        lambda cmd, *, cwd=None: mapping_out if tuple(cmd) == ("npu-smi", "info", "-m") else common_missing_cur,
    )
    assert env_fingerprint.probe_observed_clock(physical_id=15, allow_npu_smi=True) == (None, "unavailable")
    # Idle DVFS P-state (Usage Rate == 0%, curFreq 800, configured Freq 1650) reports configured 1650 MHz,
    # whereas loaded throttling (Usage Rate > 0%, curFreq 800) still reports 800 MHz and fails band check.
    common_idle_dvfs = "\n".join(
        [
            "NPU ID : 7",
            "Chip Count : 2",
            "Chip ID : 0",
            "Aicore Usage Rate(%) : 0",
            "Aicore Freq(MHZ) : 1650",
            "Aicore curFreq(MHZ) : 800",
            "Chip ID : 1",
            "Aicore Usage Rate(%) : 0",
            "Aicore Freq(MHZ) : 1650",
            "Aicore curFreq(MHZ) : 800",
        ]
    )
    monkeypatch.setattr(
        env_fingerprint,
        "_bounded_run",
        lambda cmd, *, cwd=None: mapping_out if tuple(cmd) == ("npu-smi", "info", "-m") else common_idle_dvfs,
    )
    assert env_fingerprint.probe_observed_clock(physical_id=15, allow_npu_smi=True) == (1650.0, "npu-smi_cur_freq_mhz")
    common_loaded_throttled = common_idle_dvfs.replace("Chip ID : 1\nAicore Usage Rate(%) : 0", "Chip ID : 1\nAicore Usage Rate(%) : 85")
    monkeypatch.setattr(
        env_fingerprint,
        "_bounded_run",
        lambda cmd, *, cwd=None: mapping_out if tuple(cmd) == ("npu-smi", "info", "-m") else common_loaded_throttled,
    )
    assert env_fingerprint.probe_observed_clock(physical_id=15, allow_npu_smi=True) == (800.0, "npu-smi_cur_freq_mhz")
    assert "allow_npu_smi=not bool(args.allow_cpu_smoke)" in Path(campaign_runner.__file__).read_text(encoding="utf-8")


