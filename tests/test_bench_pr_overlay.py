"""Tests for the ephemeral PR-overlay A/B harness.

[Role]
  Exercise diff parsing/classification, real temporary-git worktree planning,
  compiled-extension staging, per-arm cache isolation, ABBA scheduling, paired
  differences and failure containment without an NPU or network.
"""

from __future__ import annotations

import importlib.util
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = _REPO_ROOT / "mindie_profiler" / "bench" / "pr_overlay.py"
_GIT_ENV = {
    "GIT_AUTHOR_NAME": "Overlay Test",
    "GIT_AUTHOR_EMAIL": "overlay@example.invalid",
    "GIT_COMMITTER_NAME": "Overlay Test",
    "GIT_COMMITTER_EMAIL": "overlay@example.invalid",
}
_GIT_CONFIG = (
    "-c", "user.name=Overlay Test", "-c", "user.email=overlay@example.invalid",
    "-c", "commit.gpgsign=false",
)


def _load_module():
    try:
        from mindie_profiler.bench import pr_overlay

        return pr_overlay
    except Exception:
        spec = importlib.util.spec_from_file_location("_bench_pr_overlay", _MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


po = _load_module()


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(_GIT_ENV)
    proc = subprocess.run(
        ["git", *_GIT_CONFIG, "-C", str(repo), *args],
        capture_output=True, text=True, timeout=30, check=False, env=env,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout


def _make_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "a.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "a.py").write_text("value = 2\n", encoding="utf-8")
    (repo / "b.py").write_text("other = 3\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "candidate")
    return repo, base


def _fake_plan(tmp_path: Path) -> dict:
    base_tree, pr_tree = tmp_path / "overlay" / "base", tmp_path / "overlay" / "pr"
    base_tree.mkdir(parents=True)
    pr_tree.mkdir(parents=True)
    return {
        "schema": po.PLAN_SCHEMA,
        "overlay_id": "trial",
        "root": str(tmp_path / "overlay"),
        "arms": {
            "base": {"tree": str(base_tree), "pythonpath": str(base_tree)},
            "pr": {"tree": str(pr_tree), "pythonpath": str(pr_tree)},
        },
        "classification": {"verdict": "pure_python"},
    }


def test_parse_name_status_z_nul_and_newline_forms() -> None:
    nul = b"R100\x00old.py\x00new.py\x00M\x00a.py\x00"
    assert po.parse_name_status_z(nul) == [
        ("R100", "old.py", "new.py"),
        ("M", "a.py"),
    ]
    newline = "M\ta.py\nR087\told.py\tnew.py\nA\tdocs/readme.md\n"
    assert po.parse_name_status_z(newline) == [
        ("M", "a.py"),
        ("R087", "old.py", "new.py"),
        ("A", "docs/readme.md"),
    ]
    assert po.parse_name_status_z("") == []
    with pytest.raises(ValueError) as excinfo:
        po.parse_name_status_z(b"R100\x00only-old\x00")
    assert len(str(excinfo.value)) <= 200
    with pytest.raises(ValueError):
        po.parse_name_status_z("Z\tnot-a-status\n")


def test_classify_diff_pure_rename_native_and_empty() -> None:
    pure = po.classify_diff([
        ("M", "pkg/ops.py"),
        ("A", "tests/test_ops.py"),
        ("M", "docs/ops.md"),
    ])
    assert pure["schema"] == po.CLASSIFICATION_SCHEMA
    assert pure["verdict"] == "pure_python"
    assert pure["native_paths"] == []
    assert pure["requires_abi_matched_build"] is False
    assert {"pkg/ops.py", "tests/test_ops.py", "docs/ops.md"} <= set(pure["python_paths"])

    renamed = po.classify_diff([("R100", "pkg/old.py", "pkg/new.py")])
    assert renamed["verdict"] == "pure_python"
    assert renamed["renames"] == [{"from": "pkg/old.py", "to": "pkg/new.py"}]
    assert {"pkg/old.py", "pkg/new.py"} <= set(renamed["python_paths"])

    copied = po.classify_diff([("C75", "pkg/a.py", "pkg/b.py")])
    assert copied["verdict"] == "pure_python"
    assert {"pkg/a.py", "pkg/b.py"} <= set(copied["python_paths"])

    native = po.classify_diff([("M", "csrc/kernel.cpp")])
    assert native["verdict"] == "native_rebuild_required"
    assert native["native_paths"] == ["csrc/kernel.cpp"]
    assert native["requires_abi_matched_build"] is True
    assert any("csrc" in reason or "native" in reason for reason in native["reasons"])

    opp = po.classify_diff([
        ("M", "vllm_ascend/opp/op_metadata.json"),
        ("A", "vllm_ascend/opp/op_kernel.bin"),
    ])
    assert opp["verdict"] == "native_rebuild_required"
    assert set(opp["native_paths"]) == {
        "vllm_ascend/opp/op_metadata.json",
        "vllm_ascend/opp/op_kernel.bin",
    }

    deleted = po.classify_diff([("D", "csrc/removed.cpp")])
    assert deleted["verdict"] == "native_rebuild_required"
    assert deleted["deleted_paths"] == ["csrc/removed.cpp"]

    empty = po.classify_diff([])
    assert empty["verdict"] == "no_change"
    assert empty["python_paths"] == [] and empty["native_paths"] == []


def test_plan_overlay_real_repo_and_mismatch_cleanup(tmp_path: Path) -> None:
    repo, base = _make_repo(tmp_path)
    root = tmp_path / "overlay"
    plan = po.plan_overlay(repo, base, "HEAD", overlay_id="unit", overlay_root=root)
    try:
        assert plan["schema"] == po.PLAN_SCHEMA
        assert plan["base_rev"] == base
        assert plan["base_parent"] == base
        assert plan["candidate_rev"] == _git(repo, "rev-parse", "HEAD").strip()
        assert plan["overlay_id"] == "unit"
        assert plan["classification"]["verdict"] == "pure_python"
        assert {"a.py", "b.py"} <= set(plan["classification"]["python_paths"])
        for arm in ("base", "pr"):
            tree = plan["arms"][arm]["tree"]
            assert Path(tree).is_dir()
            assert plan["arms"][arm]["pythonpath"] == tree
            assert os.path.isabs(tree)
        assert len(plan["worktrees"]) == 2
        assert (Path(plan["arms"]["pr"]["tree"]) / "b.py").read_text() == "other = 3\n"
    finally:
        po.remove_overlay(plan)
    assert not root.exists()

    bad_root = tmp_path / "bad-overlay"
    with pytest.raises(ValueError) as excinfo:
        po.plan_overlay(repo, "HEAD", "HEAD", overlay_id="bad", overlay_root=bad_root)
    message = str(excinfo.value)
    assert "candidate" in message and "base" in message
    assert not bad_root.exists()
    assert not (Path(repo) / ".git" / "worktrees" / "bad").exists()


def test_stage_compiled_extensions_symlink_skip_escape_and_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    installed = tmp_path / "site-packages" / "vllm_ascend"
    (installed / "sub").mkdir(parents=True)
    (installed / "_C.abi3.so").write_bytes(b"root-extension")
    (installed / "sub" / "_C_ops.so").write_bytes(b"sub-extension")
    outside = tmp_path / "outside.so"
    outside.write_bytes(b"outside")
    os.symlink(outside, installed / "_C_evil.so")

    overlay = tmp_path / "overlay"
    overlay.mkdir()
    (overlay / "_C.abi3.so").write_bytes(b"keep-me")

    result = po.stage_compiled_extensions(overlay, installed)
    assert result["installed_package_dir"] == str(installed)
    assert "_C.abi3.so" in result["skipped_existing"]
    assert (overlay / "_C.abi3.so").read_bytes() == b"keep-me"
    assert "_C_evil.so" not in result["linked"]
    assert not os.path.lexists(overlay / "_C_evil.so")
    assert "_C_evil.so" in result["rejected_unsafe"]

    linked_sub = overlay / "sub" / "_C_ops.so"
    assert linked_sub.is_symlink()
    assert linked_sub.resolve() == (installed / "sub" / "_C_ops.so").resolve()
    assert not os.path.isabs(os.readlink(linked_sub))

    copy_overlay = tmp_path / "copy-overlay"

    def deny_symlink(*_args, **_kwargs):
        raise OSError("symlinks unavailable")

    monkeypatch.setattr(po.os, "symlink", deny_symlink)
    copied = po.stage_compiled_extensions(copy_overlay, installed)
    assert copied["mode"] == "copy"
    assert set(copied["linked"]) == {"_C.abi3.so", "sub/_C_ops.so"}
    assert all(mode == "copy" for mode in copied["modes"].values())
    destination = copy_overlay / "sub" / "_C_ops.so"
    assert destination.is_file() and not destination.is_symlink()
    assert destination.read_bytes() == b"sub-extension"


def test_cache_environment_is_absolute_isolated_and_not_home(tmp_path: Path) -> None:
    base_dir = tmp_path / "overlay"
    base_env = po.cache_environment("base", "ovl1", base_dir=base_dir)
    pr_env = po.cache_environment("pr", "ovl1", base_dir=base_dir)
    required = {
        "TRITON_CACHE_DIR", "TORCHINDUCTOR_CACHE_DIR", "VLLM_CACHE_ROOT",
        "VLLM_ASSETS_CACHE", "XDG_CACHE_HOME", "PYTHONPYCACHEPREFIX",
    }
    assert required <= set(base_env)
    home = str(Path.home())
    for env in (base_env, pr_env):
        for value in env.values():
            assert os.path.isabs(value)
            assert os.path.commonpath([value, str(base_dir)]) == str(base_dir)
            assert not value.startswith(home)
    for key in required:
        assert base_env[key] != pr_env[key]
        assert "/base/" in base_env[key] and "/pr/" in pr_env[key]

    default_env = po.cache_environment("base", "ovl2")
    overlay_root = po.OVERLAY_ROOT_TEMPLATE.format(overlay_id="ovl2")
    for value in default_env.values():
        assert os.path.commonpath([value, overlay_root]) == overlay_root
        assert not value.startswith(home)

    with pytest.raises(ValueError):
        po.cache_environment("base", "ovl1", base_dir=Path.home())


def test_abba_schedule_shapes_and_bounds() -> None:
    assert po.abba_schedule(1) == [("base", "pr")]
    assert po.abba_schedule(2) == [("base", "pr"), ("pr", "base")]
    assert po.abba_schedule(4) == [
        ("base", "pr"), ("pr", "base"), ("base", "pr"), ("pr", "base"),
    ]
    for invalid in (0, 65):
        with pytest.raises(ValueError):
            po.abba_schedule(invalid)


def test_run_paired_trials_abba_order_and_partial_failure(tmp_path: Path) -> None:
    plan = _fake_plan(tmp_path)
    seen: list[tuple[int, str]] = []

    def runner(**kwargs):
        seen.append((kwargs["sequence"], kwargs["arm"]))
        assert os.path.isabs(kwargs["tree"])
        assert os.path.isabs(kwargs["pythonpath"])
        assert kwargs["env"]["TRITON_CACHE_DIR"].endswith(f"/{kwargs['arm']}/triton")
        return {"duration_ms": 10.0 + kwargs["sequence"], "outputs_ok": True}

    result = po.run_paired_trials(plan, runner, trials=2)
    assert seen == [(0, "base"), (0, "pr"), (1, "pr"), (1, "base")]
    assert result["schema"] == po.TRIALS_SCHEMA
    assert result["status"] == "completed"
    assert result["environment_mode"] == "separate_contexts"
    assert len(result["records"]) == 4
    assert all(record["outputs_ok"] is True for record in result["records"])
    assert any("separate_contexts" in note for note in result["notes"])

    def failing(**kwargs):
        if kwargs["sequence"] == 1 and kwargs["arm"] == "base":
            raise RuntimeError("simulated arm crash")
        return {"duration_ms": 20.0}

    partial = po.run_paired_trials(plan, failing, trials=2)
    assert partial["status"] == "partial"
    assert len(partial["records"]) == 3
    assert any("simulated arm crash" in note for note in partial["notes"])
    assert partial["differences"]["pairs"][0]["status"] == "paired"
    assert partial["differences"]["pairs"][-1]["status"] == "unpaired"


def test_pair_differences_median_direction_and_unpaired() -> None:
    records = [
        {"trial": 1, "arm": "base", "duration_ms": 100.0, "sequence": 0},
        {"trial": 1, "arm": "pr", "duration_ms": 90.0, "sequence": 0},
        {"trial": 2, "arm": "base", "duration_ms": 100.0, "sequence": 1},
        {"trial": 2, "arm": "pr", "duration_ms": 110.0, "sequence": 1},
        {"trial": 3, "arm": "base", "duration_ms": 100.0, "sequence": 2},
    ]
    differences = po.pair_differences(records)
    assert len(differences["pairs"]) == 3
    assert differences["paired_median_delta_ms"] == pytest.approx(0.0)
    assert differences["paired_median_relative"] == pytest.approx(0.0)
    assert differences["direction_counts"] == {"faster": 1, "slower": 1, "equal": 0}
    unpaired = differences["pairs"][-1]
    assert unpaired["trial"] == 3
    assert unpaired["status"] == "unpaired"
    assert unpaired["reason"] == "missing pr arm"
    assert unpaired["pr_ms"] is None and unpaired["delta_ms"] is None
    assert differences["between_arm_distribution"]["base"]["count"] == 2

    warm = po.pair_differences(records, warmup=1)
    assert warm["paired_median_delta_ms"] == pytest.approx(10.0)
    assert 1 in warm["excluded_trials"]

    for bad_duration in (-1.0, math.nan, math.inf):
        with pytest.raises(ValueError):
            po.pair_differences(
                [{"trial": 1, "arm": "base", "duration_ms": bad_duration, "sequence": 0}]
            )


def test_remove_overlay_refuses_unowned_root(tmp_path: Path) -> None:
    home = Path.home()
    home.mkdir(parents=True, exist_ok=True)
    with pytest.raises(ValueError):
        po.remove_overlay({"root": str(home), "worktrees": []})
    assert home.exists()
    with pytest.raises(ValueError):
        po.remove_overlay("/")
    with pytest.raises(ValueError):
        po.remove_overlay({"root": str(tmp_path.parent / "outside-overlay"), "worktrees": []})


def test_remove_overlay_guard_rejects_escaping_worktree(tmp_path: Path) -> None:
    root = tmp_path / "overlay"
    root.mkdir()
    outsider = tmp_path / "outsider"
    outsider.mkdir()
    result = po.remove_overlay({
        "root": str(root),
        "worktrees": [{"arm": "base", "path": str(outsider), "rev": "deadbeef"}],
    })
    assert result["failed_worktrees"][0]["path"] == str(outsider)
    assert outsider.is_dir()
    assert not root.exists()


def test_plan_overlay_allows_a_multi_commit_pr_branch(tmp_path: Path) -> None:
    repo, base = _make_repo(tmp_path)
    (repo / "b.py").write_text("other = 4\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "second candidate commit")
    root = tmp_path / "overlay-multi"
    plan = po.plan_overlay(repo, base, "HEAD", overlay_id="multi",
                           overlay_root=root)
    try:
        assert plan["base_parent"] == base
        assert plan["candidate_parent"] != plan["candidate_rev"]
        assert plan["candidate_parent"] == _git(
            repo, "rev-parse", "HEAD^1").strip()
        assert plan["classification"]["verdict"] == "pure_python"
    finally:
        po.remove_overlay(plan)


def test_inert_directories_and_root_lint_configs_are_not_native() -> None:
    for path in ("benchmarks/tests/latency-tests.json", "typos.toml",
                 ".ruff.toml", "ruff.toml", "docs/guide.md"):
        kind, rule, inert = po._path_class(path)
        assert kind == "python", path
        assert rule is None, path
        assert inert is True, path
    kind, rule, inert = po._path_class("csrc/ops.cpp")
    assert kind == "native" and inert is False and rule


def test_triton_python_kernels_are_listed_but_stay_pure_python(tmp_path: Path) -> None:
    kernel = tmp_path / "vllm_ascend" / "ops" / "triton_ops.py"
    kernel.parent.mkdir(parents=True)
    kernel.write_text("import triton\n@triton.jit\ndef kernel():\n    pass\n",
                      encoding="utf-8")
    classification = po.classify_diff([("M", "vllm_ascend/ops/triton_ops.py")],
                                      repo=str(tmp_path))
    assert classification["verdict"] == "pure_python"
    assert classification["triton_paths"] == ["vllm_ascend/ops/triton_ops.py"]
    assert classification["requires_abi_matched_build"] is False


def test_nested_shared_libraries_are_staged(tmp_path: Path) -> None:
    installed = tmp_path / "site-packages" / "vllm_ascend"
    nested = installed / "third_party" / "engram"
    nested.mkdir(parents=True)
    (nested / "libengram_hixl.so").write_bytes(b"nested-library")
    overlay = tmp_path / "overlay-nested"
    result = po.stage_compiled_extensions(overlay, installed)
    assert result["linked"] == ["third_party/engram/libengram_hixl.so"]
    staged = overlay / "third_party" / "engram" / "libengram_hixl.so"
    assert staged.is_symlink()
    assert staged.resolve() == (nested / "libengram_hixl.so").resolve()


def test_wrong_output_arms_are_excluded_from_delta_reporting() -> None:
    records = [
        {"trial": 1, "arm": "base", "duration_ms": 100.0, "outputs_ok": False},
        {"trial": 1, "arm": "pr", "duration_ms": 50.0, "outputs_ok": True},
        {"trial": 2, "arm": "base", "duration_ms": 100.0, "outputs_ok": True},
        {"trial": 2, "arm": "pr", "duration_ms": 90.0, "outputs_ok": True},
    ]
    differences = po.pair_differences(records)
    excluded = differences["pairs"][0]
    assert excluded["status"] == "excluded_output_mismatch"
    assert excluded["delta_ms"] is None
    assert differences["direction_counts"] == {"faster": 1, "slower": 0, "equal": 0}
    assert differences["paired_median_delta_ms"] == pytest.approx(-10.0)
    assert differences["excluded_output_mismatch_count"] == 1


def test_subprocess_trial_runner_reports_exit_status(tmp_path: Path) -> None:
    runner = po.subprocess_trial_runner(
        "python3 -c \"print('ok')\"", timeout_s=30.0)
    outcome = runner(arm="base", tree=str(tmp_path),
                     pythonpath=str(tmp_path),
                     env={"TRITON_CACHE_DIR": str(tmp_path / "triton")},
                     sequence=0, trial=1)
    assert outcome["outputs_ok"] is True
    assert outcome["duration_ms"] >= 0.0


def test_build_and_dependency_declarations_are_never_pure_python() -> None:
    paths = (
        "CMakeLists.txt", "requirements.txt", "setup.cfg",
        "csrc/CMakeLists.txt", "requirements/npu.txt", "constraints/base.in",
    )
    for path in paths:
        kind, rule, inert = po._path_class(path)
        assert kind == "native", path
        assert rule and "declaration" in rule, path
        assert inert is False, path
    classification = po.classify_diff([
        ("M", "CMakeLists.txt"), ("M", "requirements.txt"), ("M", "setup.cfg"),
    ])
    assert classification["verdict"] == "native_rebuild_required"
    assert classification["requires_abi_matched_build"] is True
    assert set(classification["native_paths"]) == {
        "CMakeLists.txt", "requirements.txt", "setup.cfg"}
    assert po._path_class("tests/CMakeLists.txt") == ("python", None, True)
    assert po._path_class("docs/requirements.txt") == ("python", None, True)


def test_stage_compiled_extensions_targets_worktree_package(tmp_path: Path) -> None:
    installed = tmp_path / "site-packages" / "vllm_ascend"
    installed.mkdir(parents=True)
    (installed / "__init__.py").write_text("", encoding="utf-8")
    (installed / "_C.so").write_bytes(b"installed-extension")
    tree = tmp_path / "overlay" / "base"
    package = tree / "vllm_ascend"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")

    result = po.stage_compiled_extensions(tree, installed)
    staged = package / "_C.so"
    assert staged.is_symlink()
    assert staged.resolve() == (installed / "_C.so").resolve()
    assert not (tree / "_C.so").exists()
    assert result["linked"] == ["_C.so"]

    direct = tmp_path / "direct"
    direct.mkdir()
    (direct / "__init__.py").write_text("", encoding="utf-8")
    po.stage_compiled_extensions(direct, installed)
    assert (direct / "_C.so").is_symlink()

    bare = tmp_path / "bare-tree"
    bare.mkdir()
    po.stage_compiled_extensions(bare, installed)
    assert (bare / "_C.so").is_symlink()


def test_subprocess_trial_runner_prefers_device_timed_receipt(tmp_path: Path) -> None:
    code = ("import json, time; time.sleep(0.05); "
            "print(json.dumps({'duration_ms': 1.5, 'outputs_ok': True}))")
    runner = po.subprocess_trial_runner([sys.executable, "-c", code], timeout_s=30.0)
    outcome = runner(arm="base", tree=str(tmp_path), pythonpath=str(tmp_path),
                     env={}, sequence=0, trial=1)
    assert outcome["duration_ms"] == pytest.approx(1.5)
    assert outcome["wall_duration_ms"] > outcome["duration_ms"]
    assert outcome["returncode"] == 0
    assert outcome["outputs_ok"] is True

    failing = po.subprocess_trial_runner(
        [sys.executable, "-c",
         "import json; print(json.dumps({'minimum_ms': 2.0})); raise SystemExit(3)"],
        timeout_s=30.0)
    failed = failing(arm="pr", tree=str(tmp_path), pythonpath=str(tmp_path),
                     env={}, sequence=0, trial=1)
    assert failed["duration_ms"] == pytest.approx(2.0)
    assert failed["returncode"] == 3
    assert failed["outputs_ok"] is False

    mismatch = po.subprocess_trial_runner(
        [sys.executable, "-c",
         "import json; print(json.dumps({'duration_ms': 3.0, 'validated': False}))"],
        timeout_s=30.0)
    invalid = mismatch(arm="pr", tree=str(tmp_path), pythonpath=str(tmp_path),
                       env={}, sequence=0, trial=1)
    assert invalid["returncode"] == 0
    assert invalid["outputs_ok"] is False


def test_failed_trial_arms_report_failed_and_cli_exits_nonzero(tmp_path: Path) -> None:
    plan = _fake_plan(tmp_path)
    runner = po.subprocess_trial_runner("/usr/bin/false", timeout_s=30.0)
    result = po.run_paired_trials(plan, runner, trials=2)
    assert result["status"] == "failed"
    assert result["differences"]["eligible_pairs"] == 0
    assert len(result["records"]) == 4
    assert all(record["outputs_ok"] is False for record in result["records"])
    assert all(record["returncode"] != 0 for record in result["records"])

    repo, base = _make_repo(tmp_path)
    root = tmp_path / "overlay-cli"
    rc = po.main([
        "--repo", str(repo), "--base", base, "--candidate", "HEAD",
        "--overlay-id", "cli", "--overlay-root", str(root),
        "--trial-cmd", "/usr/bin/false", "--trials", "1", "--remove",
    ])
    assert rc == 1
    assert not root.exists()


def test_main_removes_overlay_on_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, base = _make_repo(tmp_path)
    root = tmp_path / "overlay-timeout"

    def timeout_runner(_command):
        def runner(**_kwargs):
            raise TimeoutError("simulated child timeout")
        return runner

    monkeypatch.setattr(po, "subprocess_trial_runner", timeout_runner)
    with pytest.raises(TimeoutError, match="simulated child timeout"):
        po.main([
            "--repo", str(repo), "--base", base, "--candidate", "HEAD",
            "--overlay-id", "timeout", "--overlay-root", str(root),
            "--trial-cmd", "true", "--trials", "1", "--remove",
        ])
    assert not root.exists()


def test_multiline_indented_json_receipt_preserves_false_verdict(tmp_path: Path) -> None:
    import sys as _sys

    repo, base = _make_repo(tmp_path)
    root = tmp_path / "overlay-multiline"
    plan = po.plan_overlay(
        repo, base, "HEAD", overlay_id="multiline", overlay_root=root
    )
    try:
        cmd = [
            _sys.executable,
            "-c",
            "import json; print('log line'); print(json.dumps({'outputs_ok': False, 'duration_ms': 0.002}, indent=2))",
        ]
        result = po.run_paired_trials(
            plan, po.subprocess_trial_runner(cmd), trials=1
        )
        assert result["status"] == "failed"
        assert result["differences"]["eligible_pairs"] == 0
        assert all(r["outputs_ok"] is False for r in result["records"])
        assert all(r["duration_ms"] == pytest.approx(0.002) for r in result["records"])
    finally:
        po.remove_overlay(plan)
