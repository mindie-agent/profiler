"""Ephemeral PR-overlay A/B harness for a serving checkout such as vllm-ascend.

[Role]
  Materialise detached ``base``/``pr`` worktrees, classify the diff, stage
  installed compiled extensions, isolate per-arm caches, and run ABBA trials.

[Invariants]
  * Only ``.py``/``.pyi`` and documented inert resources are overlayable; native
    C/C++/AscendC/OPP/CMake or build/dependency edits require an ABI-matched
    rebuild.  Installed ``_C*.so`` modules are symlinked so a regular package
    directory cannot hide them.
  * Subprocesses are bounded (``check=False``, truncated stderr); ``TimeoutError`` is never swallowed.
  * Writes stay under the overlay root; cleanup refuses unowned paths.
  * Base/PR import in separate processes (``environment_mode="separate_contexts"``).

[Timeouts & Locks]
  Git commands use ``GIT_TIMEOUT_SECONDS`` (60 s).  No locks.

[Side-Effect Policy]
  Creates/removes only ``<overlay_root>/base`` and ``<overlay_root>/pr``.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from statistics import median
from typing import Any, Iterable, Mapping, Sequence
OVERLAY_ROOT_TEMPLATE = "/tmp/mindie_pr_overlay_{overlay_id}"
CLASSIFICATION_SCHEMA = "mindie-pr-overlay-classification/1"
PLAN_SCHEMA = "mindie-pr-overlay-plan/1"
TRIALS_SCHEMA = "mindie-pr-overlay-trials/1"
CLEANUP_SCHEMA = "mindie-pr-overlay-cleanup/1"
GIT_TIMEOUT_SECONDS = 60.0
MAX_TRIALS = 64
MAX_STDERR_CHARS = 400
MAX_MESSAGE_CHARS = MAX_STDERR_CHARS // 2
_DIR_MODE = stat.S_IRWXU
_MAX_TRITON_SCAN_CHARS = 1_000_000
_ARMS = ("base", "pr")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_STATUS_RE = re.compile(r"^[ACDMRTUXB][0-9]{0,3}$")
_INERT_SUFFIXES = frozenset({
    ".md", ".markdown", ".rst", ".txt", ".ini", ".cfg", ".yaml", ".yml",
    ".png", ".jpg", ".jpeg", ".gif", ".svg",
})
_INERT_DIRS = frozenset({"tests", "docs", "benchmarks"})
_ROOT_LINT_CONFIGS = frozenset({"typos.toml", ".ruff.toml", "ruff.toml"})
_PYTHON_SUFFIXES = frozenset({".py", ".pyi"})
_NATIVE_SUFFIXES = frozenset({
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".cu", ".cmake",
    ".mk", ".ascendc", ".json", ".bin", ".so", ".a", ".o", ".whl", ".toml",
})
_NATIVE_SEGMENTS = frozenset({"csrc", "op_host", "op_kernel", "opp", "cmake", "third_party"})
_BUILD_NAMES = frozenset({
    "setup.py", "setup.cfg", "pyproject.toml", "cmakelists.txt", "makefile",
    "gnumakefile", "manifest.in",
})
_CACHE_LAYOUT = {
    "TRITON_CACHE_DIR": "triton",
    "TORCHINDUCTOR_CACHE_DIR": "torchinductor",
    "TORCH_EXTENSIONS_DIR": "torch-extensions",
    "VLLM_CACHE_ROOT": "vllm",
    "VLLM_ASSETS_CACHE": "vllm-assets",
    "XDG_CACHE_HOME": "xdg",
    "PYTHONPYCACHEPREFIX": "pycache",
}
def _bounded(text: object, limit: int) -> str:
    value = str(text).replace("\x00", " ").strip()
    return value if len(value) <= limit else value[: max(0, limit - len("..."))] + "..."
def _is_within(path: str | os.PathLike[str], root: str | os.PathLike[str]) -> bool:
    try:
        left, right = os.path.abspath(path), os.path.abspath(root)
        return os.path.commonpath([left, right]) == right
    except (TypeError, ValueError):
        return False
def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.match(value):
        raise ValueError(f"{label} must be a safe non-empty token, got {value!r}")
    return value
def _git(repo: str | os.PathLike[str], args: Sequence[str], *, context: str) -> bytes:
    """Run one bounded git command without a shell."""
    try:
        proc = subprocess.run(
            ["git", "-C", os.fspath(repo), *args],
            capture_output=True, timeout=GIT_TIMEOUT_SECONDS, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"{context} exceeded the {GIT_TIMEOUT_SECONDS:.0f}s git timeout") from exc
    except TimeoutError:
        raise
    except OSError as exc:
        raise RuntimeError(f"{context} could not run git: {_bounded(exc, MAX_STDERR_CHARS)}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"{context} failed with exit {proc.returncode}: "
                           f"{_bounded(proc.stderr.decode('utf-8', 'surrogateescape'), MAX_STDERR_CHARS)}")
    return proc.stdout
def _resolved_commit(repo: str, revision: str, *, context: str) -> str:
    sha = _git(repo, ["rev-parse", "--verify", f"{revision}^{{commit}}"],
               context=context).decode("utf-8", errors="surrogateescape").strip()
    if not sha:
        raise RuntimeError(f"{context}: git returned an empty commit id for {revision!r}")
    return sha
def _triton_source(path: str, repo: str | None) -> bool:
    """Detect Triton kernel Python sources by repo content or path hint."""
    lowered = path.lower()
    if "triton" in lowered:
        return True
    if not repo or not lowered.endswith((".py", ".pyi")):
        return False
    candidate = os.path.join(repo, path)
    try:
        with open(candidate, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read(_MAX_TRITON_SCAN_CHARS)
    except TimeoutError:
        raise
    except OSError:
        return False
    return "triton" + ".jit" in text or "triton" + ".autotune" in text
def _path_class(path: str, repo: str | None = None) -> tuple[str, str | None, bool]:
    """Return ``(kind, native_rule, inert)`` for one changed path."""
    parts = [part for part in path.replace("\\", "/").split("/") if part not in ("", ".")]
    if not parts:
        return "native", "empty path", False
    name, parents = parts[-1].lower(), [part.lower() for part in parts[:-1]]
    if (any(part in _INERT_DIRS for part in parents)
            or (not parents and name in _ROOT_LINT_CONFIGS)
            or os.path.splitext(name)[1] in _INERT_SUFFIXES):
        return "python", None, True
    if _triton_source(path, repo):
        return "python", "triton_kernel", False
    rule = None
    if name in _BUILD_NAMES:
        rule = f"build/dependency declaration {parts[-1]}"
    elif name.startswith(("requirements", "constraints")) and name.endswith((".txt", ".in")):
        rule = f"dependency declaration {parts[-1]}"
    elif any(part in {"requirements", "constraints"} for part in parents) and name.endswith(
        (".txt", ".in")
    ):
        rule = f"dependency declaration {parts[-1]}"
    elif os.path.splitext(name)[1] in _NATIVE_SUFFIXES:
        rule = f"native/build suffix {os.path.splitext(name)[1]}"
    else:
        for parent in parents:
            if parent in _NATIVE_SEGMENTS:
                rule = f"native source directory {parent}/"
                break
    if rule is not None:
        return "native", rule, False
    suffix = os.path.splitext(name)[1]
    inert = any(part in _INERT_DIRS for part in parents) or suffix in _INERT_SUFFIXES
    if suffix in _PYTHON_SUFFIXES or inert:
        return "python", None, inert
    return "native", "unclassified path conservatively requires a rebuild", False
def _coerce_entry(entry: object) -> tuple[str, str, str | None]:
    if isinstance(entry, str) or not isinstance(entry, (tuple, list)) or not (
        0 <= len(entry) - 2 <= 1
    ):
        raise ValueError(f"diff entry must be a 2/3-tuple, got {entry!r}")
    status, path_a = entry[0], entry[1]
    path_b = entry[2] if len(entry) - 2 else None
    if not isinstance(status, str) or not _STATUS_RE.match(status.upper()):
        raise ValueError(f"invalid git name-status value {status!r}")
    status = status.upper()
    if not isinstance(path_a, str) or not path_a:
        raise ValueError(f"diff entry has no path: {entry!r}")
    if path_b is not None and (not isinstance(path_b, str) or not path_b):
        raise ValueError(f"diff rename/copy has no destination path: {entry!r}")
    if (path_b is None) == (status[0] in {"R", "C"}):
        raise ValueError(f"{status} entry has the wrong number of paths: {entry!r}")
    return status, path_a, path_b
def parse_name_status_z(payload: bytes | str) -> list[tuple[str, ...]]:
    """Parse NUL-delimited or newline/tab ``git diff --name-status`` output."""
    if isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="surrogateescape")
    elif isinstance(payload, str):
        text = payload
    else:
        raise ValueError(_bounded(
            f"name-status payload must be bytes or str, got {type(payload).__name__}",
            MAX_MESSAGE_CHARS,
        ))
    try:
        if "\x00" in text:
            tokens = [token.rstrip("\r\n") for token in text.split("\x00") if token]
        else:
            tokens = []
            for line in text.splitlines():
                if not line.strip():
                    continue
                if "\t" in line:
                    fields = [field for field in line.split("\t") if field]
                else:
                    head = line.split(None, 1)
                    if head[0].upper()[:1] in {"R", "C"} and len(head) - 1:
                        fields = [head[0], *head[1].split(None, 1)]
                    else:
                        fields = head
                tokens.extend(fields)
        return _records_from_tokens(tokens)
    except ValueError as exc:
        raise ValueError(_bounded(f"malformed name-status payload: {exc}", MAX_MESSAGE_CHARS)) from exc
def _records_from_tokens(tokens: Sequence[str]) -> list[tuple[str, ...]]:
    records: list[tuple[str, ...]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index].strip()
        if not status:
            index += 1
            continue
        if not _STATUS_RE.match(status.upper()):
            raise ValueError(f"invalid status {status!r} at token {index}")
        status = status.upper()
        arity = 2 if status[0] in {"R", "C"} else 1
        if index + arity >= len(tokens):
            raise ValueError(f"status {status!r} at token {index} is missing {arity} path(s)")
        paths = list(tokens[index + 1: index + 1 + arity])
        if any(not path for path in paths):
            raise ValueError(f"status {status!r} at token {index} has an empty path")
        records.append((status, *paths))
        index += 1 + arity
    return records
def classify_diff(entries: Iterable[object] | None,
                  repo: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Classify a git name-status diff as source-overlayable or rebuild-required."""
    raw_entries = [] if entries is None else list(entries)
    repo_abs = os.path.abspath(os.fspath(repo)) if repo is not None else None
    python_paths: set[str] = set()
    native_paths: set[str] = set()
    triton_paths: set[str] = set()
    deleted_paths: set[str] = set()
    renames: list[dict[str, str]] = []
    reasons: list[str] = []
    inert_seen = False
    for entry in raw_entries:
        status, path_a, path_b = _coerce_entry(entry)
        kind = status[0]
        if kind in {"R", "C"}:
            if kind == "R":
                renames.append({"from": path_a, "to": path_b})
                reasons.append(f"rename {path_a} -> {path_b}: both sides classified")
            else:
                reasons.append(f"copy {path_a} -> {path_b}: both sides classified")
            for side, path in (("source", path_a), ("destination", path_b)):
                path_kind, rule, inert = _path_class(path, repo_abs)
                if rule == "triton_kernel":
                    triton_paths.add(path)
                if path_kind == "native":
                    native_paths.add(path)
                    reasons.append(f"{status} {side} {path}: {rule}")
                else:
                    python_paths.add(path)
                    inert_seen = inert_seen or inert
        elif kind == "D":
            deleted_paths.add(path_a)
            path_kind, rule, inert = _path_class(path_a, repo_abs)
            if path_kind == "native":
                native_paths.add(path_a)
                reasons.append(f"deleted native/build path {path_a}: {rule}")
            else:
                inert_seen = inert_seen or inert
                reasons.append(f"deleted ABI-neutral path {path_a}")
        else:
            path_kind, rule, inert = _path_class(path_a, repo_abs)
            if rule == "triton_kernel":
                triton_paths.add(path_a)
            if path_kind == "native":
                native_paths.add(path_a)
                reasons.append(f"{status} {path_a}: {rule}")
            else:
                python_paths.add(path_a)
                inert_seen = inert_seen or inert
    if not raw_entries:
        verdict = "no_change"
        reasons = ["empty diff: no overlay or rebuild is required"]
    elif native_paths:
        verdict = "native_rebuild_required"
        reasons.append(
            "compiled C/C++/AscendC/OPP or build/dependency inputs changed; "
            "a source-only overlay cannot preserve the installed ABI"
        )
    else:
        verdict = "pure_python"
        reasons.append(
            "only Python-hosted (.py/.pyi) or documented inert resources changed; "
            "source overlay is ABI-compatible"
        )
    if triton_paths:
        reasons.append(
            "Triton kernel Python sources overlay as source with an isolated "
            "TRITON_CACHE_DIR")
    if inert_seen:
        reasons.append("inert tests/docs/benchmarks paths are ABI-neutral and retained in python_paths")
    return {
        "schema": CLASSIFICATION_SCHEMA, "verdict": verdict,
        "python_paths": sorted(python_paths), "native_paths": sorted(native_paths),
        "triton_paths": sorted(triton_paths),
        "deleted_paths": sorted(deleted_paths), "renames": renames,
        "reasons": list(dict.fromkeys(reasons)),
        "requires_abi_matched_build": bool(native_paths),
    }
def _cleanup_partial(root: str, repo: str, worktrees: Sequence[str]) -> None:
    for path in reversed(list(worktrees)):
        try:
            _git(repo, ["worktree", "remove", "--force", path], context="worktree cleanup")
        except TimeoutError:
            raise
        except (RuntimeError, OSError):
            pass
    if os.path.lexists(root):
        try:
            shutil.rmtree(root)
        except TimeoutError:
            raise
        except OSError:
            pass
def plan_overlay(
    repo: str | os.PathLike[str], base_rev: str, candidate_rev: str, *,
    overlay_id: str, overlay_root: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Validate revisions, materialise detached worktrees, and classify the diff."""
    overlay_id = _token(overlay_id, "overlay_id")
    repo_abs = os.path.abspath(os.fspath(repo))
    if not os.path.isdir(repo_abs):
        raise ValueError(f"repository does not exist or is not a directory: {repo_abs}")
    base_sha = _resolved_commit(repo_abs, base_rev, context="resolve base revision")
    candidate_sha = _resolved_commit(repo_abs, candidate_rev, context="resolve candidate revision")
    if base_sha == candidate_sha:
        raise ValueError(
            f"candidate {candidate_rev!r} ({candidate_sha}) equals base "
            f"{base_rev!r}; an overlay needs a distinct candidate revision")
    try:
        _git(repo_abs, ["merge-base", "--is-ancestor", base_sha, candidate_sha],
             context="verify base is an ancestor of candidate")
    except RuntimeError as exc:
        raise ValueError(
            f"base {base_rev!r} ({base_sha}) is not an ancestor of candidate "
            f"{candidate_rev!r} ({candidate_sha}): {_bounded(exc, MAX_STDERR_CHARS)}"
        ) from exc
    try:
        parent_sha = _resolved_commit(repo_abs, f"{candidate_rev}^1",
                                      context="resolve candidate parent")
    except RuntimeError as exc:
        raise ValueError(
            f"candidate {candidate_rev!r} ({candidate_sha}) has no parent commit: "
            f"{_bounded(exc, MAX_STDERR_CHARS)}") from exc
    root = os.path.abspath(
        OVERLAY_ROOT_TEMPLATE.format(overlay_id=overlay_id) if overlay_root is None
        else os.fspath(overlay_root)
    )
    if os.path.lexists(root):
        raise RuntimeError(f"overlay root already exists and is not owned by this call: {root}")
    parent_dir = os.path.dirname(root)
    if not os.path.isdir(parent_dir):
        raise RuntimeError(f"overlay root parent does not exist: {parent_dir}")
    os.mkdir(root, mode=_DIR_MODE)
    base_tree, pr_tree = os.path.join(root, "base"), os.path.join(root, "pr")
    created: list[str] = []
    try:
        for tree, sha in ((base_tree, base_sha), (pr_tree, candidate_sha)):
            _git(repo_abs, ["worktree", "add", "--detach", tree, sha],
                 context=f"create {os.path.basename(tree)} worktree")
            created.append(tree)
        diff_payload = _git(
            repo_abs,
            ["diff", "--name-status", "-z", "-M", "--ignore-submodules=none", base_sha, candidate_sha],
            context="diff base against candidate",
        )
        classification = classify_diff(parse_name_status_z(diff_payload), repo_abs)
    except BaseException:
        _cleanup_partial(root, repo_abs, created)
        raise
    base_arm = {"tree": base_tree, "pythonpath": base_tree}
    pr_arm = {"tree": pr_tree, "pythonpath": pr_tree}
    return {
        "schema": PLAN_SCHEMA, "overlay_id": overlay_id, "root": root, "repo": repo_abs,
        "base_rev": base_sha, "candidate_rev": candidate_sha,
        "base_parent": base_sha, "candidate_parent": parent_sha,
        "arms": {"base": base_arm, "pr": pr_arm}, "classification": classification,
        "worktrees": [{"arm": "base", "path": base_tree, "rev": base_sha},
                      {"arm": "pr", "path": pr_tree, "rev": candidate_sha}],
    }
def _extension_sources(installed_abs: str, patterns: Sequence[str] = (
        "*.so", "*.pyd", "*.dylib")) -> list[tuple[str, str]]:
    """Walk the whole installed tree so nested shared libraries are staged too."""
    found: dict[str, str] = {}
    for directory, dirs, names in os.walk(installed_abs, followlinks=False):
        dirs[:] = sorted(name for name in dirs
                         if not os.path.islink(os.path.join(directory, name)))
        for name in sorted(names):
            if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
                candidate = os.path.join(directory, name)
                if os.path.isfile(candidate) or os.path.islink(candidate):
                    rel = os.path.relpath(candidate, installed_abs).replace(os.sep, "/")
                    found[rel] = candidate
    return sorted(found.items())
def _link_extension(destination: str, source_real: str) -> str:
    parent = os.path.dirname(destination)
    os.makedirs(parent, mode=_DIR_MODE, exist_ok=True)
    target = os.path.relpath(source_real, os.path.realpath(parent))
    try:
        os.symlink(target, destination)
        return "symlink"
    except TimeoutError:
        raise
    except OSError:
        if os.path.lexists(destination):
            return "existing"
    shutil.copy2(source_real, destination)
    return "copy"
def stage_compiled_extensions(
    overlay_tree: str | os.PathLike[str], installed_package_dir: str | os.PathLike[str],
    patterns: Sequence[str] = ("*.so", "*.pyd", "*.dylib"),
) -> dict[str, Any]:
    """Symlink installed compiled extensions into an overlay package tree."""
    overlay_abs = os.path.abspath(os.fspath(overlay_tree))
    installed_abs = os.path.abspath(os.fspath(installed_package_dir))
    if not os.path.isdir(installed_abs):
        raise ValueError(f"installed package directory does not exist: {installed_abs}")
    if os.path.lexists(overlay_abs) and not os.path.isdir(overlay_abs):
        raise ValueError(f"overlay tree exists but is not a directory: {overlay_abs}")
    os.makedirs(overlay_abs, mode=_DIR_MODE, exist_ok=True)
    patterns = (patterns,) if isinstance(patterns, str) else tuple(str(p) for p in patterns)
    if not patterns:
        raise ValueError("at least one extension glob pattern is required")
    linked: list[str] = []
    skipped_existing: list[str] = []
    missing: list[str] = []
    rejected_unsafe: list[str] = []
    modes: dict[str, str] = {}
    used_copy = False
    installed_real, overlay_real = os.path.realpath(installed_abs), os.path.realpath(overlay_abs)
    for rel, source in _extension_sources(installed_abs, patterns):
        destination = os.path.join(overlay_abs, *rel.split("/"))
        if not _is_within(destination, overlay_abs):
            rejected_unsafe.append(rel)
            missing.append(rel)
            continue
        if os.path.lexists(destination):
            skipped_existing.append(rel)
            continue
        try:
            source_real = os.path.realpath(source, strict=True)
        except TimeoutError:
            raise
        except (OSError, RuntimeError):
            missing.append(rel)
            continue
        if not _is_within(source_real, installed_real) or not _is_within(
            os.path.realpath(destination), overlay_real
        ):
            rejected_unsafe.append(rel)
            missing.append(rel)
            continue
        try:
            mode = _link_extension(destination, source_real)
        except TimeoutError:
            raise
        except OSError as exc:
            missing.append(rel)
            modes[rel] = f"error:{_bounded(exc, MAX_MESSAGE_CHARS)}"
            continue
        if mode == "existing":
            skipped_existing.append(rel)
            continue
        linked.append(rel)
        modes[rel] = mode
        used_copy = used_copy or mode == "copy"
    return {
        "linked": linked, "skipped_existing": skipped_existing, "missing": missing,
        "rejected_unsafe": rejected_unsafe, "modes": modes,
        "mode": "copy" if used_copy else "symlink",
        "installed_package_dir": installed_abs,
    }
def _home_path() -> str:
    return os.path.abspath(os.path.expanduser("~"))
def cache_environment(
    arm: str, overlay_id: str, *, base_dir: str | os.PathLike[str] | None = None,
) -> dict[str, str]:
    """Return an isolated cache environment for one arm of one overlay.
    The overlay id appears exactly once: the default ``OVERLAY_ROOT_TEMPLATE``
    already embeds it, while an explicit ``base_dir`` is a parent and receives
    ``<overlay_id>/<arm>``.  No inherited environment is returned.
    """
    arm, overlay_id, home = _token(arm, "arm"), _token(overlay_id, "overlay_id"), _home_path()
    if base_dir is None:
        arm_root = os.path.join(OVERLAY_ROOT_TEMPLATE.format(overlay_id=overlay_id), arm)
    else:
        base_abs = os.path.abspath(os.fspath(base_dir))
        if base_abs in {os.path.abspath(os.sep), home}:
            raise ValueError("base_dir must be a scratch/overlay root, not the filesystem root or $HOME")
        arm_root = os.path.join(base_abs, overlay_id, arm)
    arm_root = os.path.abspath(arm_root)
    if _is_within(arm_root, home):
        raise ValueError("cache paths must not live under $HOME; use an overlay root")
    return {key: os.path.join(arm_root, directory) for key, directory in _CACHE_LAYOUT.items()}
def abba_schedule(trials: int) -> list[tuple[str, str]]:
    """Return alternating ABBA arm orders for ``trials`` sequences."""
    if isinstance(trials, bool) or not isinstance(trials, int):
        raise ValueError(f"trials must be an integer, got {trials!r}")
    if trials < 1:
        raise ValueError("trials must be at least 1")
    if trials > MAX_TRIALS:
        raise ValueError(f"trials must be at most {MAX_TRIALS}")
    return [("base", "pr") if index % 2 == 0 else ("pr", "base") for index in range(trials)]
def _distribution(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "median_ms": None, "min_ms": None, "max_ms": None}
    return {"count": len(values), "median_ms": float(median(values)),
            "min_ms": min(values), "max_ms": max(values)}
def pair_differences(trials: Sequence[Mapping[str, Any]], *, warmup: int = 0) -> dict[str, Any]:
    """Pair base/pr durations per trial and report signed PR-minus-base deltas."""
    if isinstance(warmup, bool) or not isinstance(warmup, int) or warmup < 0:
        raise ValueError("warmup must be a non-negative integer")
    grouped: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for raw in trials:
        if not isinstance(raw, Mapping):
            raise ValueError(f"trial record must be a mapping, got {type(raw).__name__}")
        trial, arm, duration = raw.get("trial"), raw.get("arm"), raw.get("duration_ms")
        if isinstance(trial, bool) or not isinstance(trial, int):
            raise ValueError(f"trial record needs an integer trial, got {trial!r}")
        if arm not in _ARMS:
            raise ValueError(f"trial record arm must be one of {_ARMS}, got {arm!r}")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError(f"duration_ms must be numeric, got {duration!r}")
        value = float(duration)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"duration_ms must be finite/non-negative, got {duration!r}")
        sequence = raw.get("sequence")
        if sequence is not None and (isinstance(sequence, bool) or not isinstance(sequence, int)):
            raise ValueError(f"sequence must be an integer or None, got {sequence!r}")
        grouped.setdefault(trial, {"base": [], "pr": []})[arm].append(
            {"duration_ms": value, "sequence": sequence,
             "outputs_ok": raw.get("outputs_ok")}
        )
    trial_numbers = sorted(grouped)
    skipped = set(trial_numbers[:warmup])
    pairs: list[dict[str, Any]] = []
    deltas: list[float] = []
    relatives: list[float] = []
    base_values: list[float] = []
    pr_values: list[float] = []
    excluded: list[dict[str, Any]] = []
    counts = {"faster": 0, "slower": 0, "equal": 0}
    for trial in trial_numbers:
        if trial in skipped:
            continue
        base_records, pr_records = grouped[trial]["base"], grouped[trial]["pr"]
        sequence = next((record["sequence"] for record in base_records + pr_records
                         if record["sequence"] is not None), trial)
        if len(base_records) == 1 and len(pr_records) == 1:
            base_ms, pr_ms = base_records[0]["duration_ms"], pr_records[0]["duration_ms"]
            if (base_records[0].get("outputs_ok") is False
                    or pr_records[0].get("outputs_ok") is False):
                pair = {"trial": trial, "sequence": sequence,
                        "status": "excluded_output_mismatch",
                        "base_ms": base_ms, "pr_ms": pr_ms, "delta_ms": None,
                        "relative": None, "direction": None,
                        "outputs_ok": False}
                pairs.append(pair)
                excluded.append(pair)
                continue
            delta = pr_ms - base_ms
            relative = delta / base_ms if base_ms != 0 else None
            direction = "faster" if delta < 0 else "slower" if delta > 0 else "equal"
            counts[direction] += 1
            deltas.append(delta)
            if relative is not None:
                relatives.append(relative)
            base_values.append(base_ms)
            pr_values.append(pr_ms)
            pairs.append({
                "trial": trial, "sequence": sequence, "status": "paired",
                "base_ms": base_ms, "pr_ms": pr_ms, "delta_ms": delta, "relative": relative, "direction": direction,
            })
        else:
            flags = (("missing base arm", not base_records), ("missing pr arm", not pr_records), ("duplicate base arm records", len(base_records) > 1), ("duplicate pr arm records", len(pr_records) > 1))
            reasons = [label for label, present in flags if present]
            pairs.append({ "trial": trial, "sequence": sequence, "status": "unpaired", "reason": "; ".join(reasons), "base_ms": base_records[0]["duration_ms"] if len(base_records) == 1 else None, "pr_ms": pr_records[0]["duration_ms"] if len(pr_records) == 1 else None, "base_records": len(base_records), "pr_records": len(pr_records), "delta_ms": None, "relative": None, "direction": None,
            })
    return { "pairs": pairs, "unpaired": [pair for pair in pairs if pair["status"] == "unpaired"], "excluded": excluded, "excluded_output_mismatch_count": len(excluded), "paired_median_delta_ms": float(median(deltas)) if deltas else None, "paired_median_relative": float(median(relatives)) if relatives else None, "direction_counts": counts, "between_arm_distribution": { "base": _distribution(base_values), "pr": _distribution(pr_values), "delta_ms": _distribution(deltas),
        }, "warmup": warmup, "excluded_trials": sorted(skipped),
    }
def run_paired_trials( plan: Mapping[str, Any], trial_runner: Any, *, trials: int = 2,
) -> dict[str, Any]:
    """Run an ABBA schedule, stopping at the first arm failure.
    ``trial_runner(arm=, tree=, pythonpath=, env=, sequence=, trial=)`` returns
    ``duration_ms`` and optionally ``outputs_ok``.  Each arm runs in its own
    process context, so ``environment_mode`` is ``"separate_contexts"``.
    """
    if not isinstance(plan, Mapping):
        raise ValueError("plan must be a mapping")
    raw_arms = plan.get("arms")
    if not isinstance(raw_arms, Mapping):
        raise ValueError("plan must contain an 'arms' mapping")
    arms = {}
    for arm in _ARMS:
        payload = raw_arms.get(arm)
        if not isinstance(payload, Mapping):
            raise ValueError(f"plan is missing the {arm!r} arm")
        tree = payload.get("tree")
        pythonpath = payload.get("pythonpath", tree)
        if (not isinstance(tree, str) or not os.path.isabs(tree)
                or not isinstance(pythonpath, str) or not os.path.isabs(pythonpath)):
            raise ValueError(f"plan arm {arm!r} needs absolute tree/pythonpath values")
        arms[arm] = {"tree": tree, "pythonpath": pythonpath}
    overlay_id = _token(plan.get("overlay_id") or "overlay", "overlay_id")
    schedule = abba_schedule(trials)
    classification = plan.get("classification")
    if isinstance(classification, Mapping) and classification.get("verdict") == "native_rebuild_required":
        raise ValueError("plan classification is 'native_rebuild_required'; source overlay "
                         "cannot preserve the installed compiled extensions")
    base_dir = plan.get("root")
    if base_dir is not None and not isinstance(base_dir, (str, os.PathLike)):
        raise ValueError("plan root must be a path")
    notes = ["environment_mode=separate_contexts: base and pr package revisions run in "
             "isolated processes with per-arm Triton/vLLM/extension caches"]
    records: list[dict[str, Any]] = []
    failure = ""
    for sequence, order in enumerate(schedule):
        trial_number = sequence + 1
        for arm in order:
            env = cache_environment(arm, overlay_id, base_dir=base_dir)
            try:
                outcome = trial_runner( arm=arm, tree=arms[arm]["tree"], pythonpath=arms[arm]["pythonpath"], env=env, sequence=sequence, trial=trial_number, )
            except TimeoutError:
                raise
            except Exception as exc:
                failure = (f"trial {trial_number} sequence {sequence} arm {arm} failed: "
                           f"{type(exc).__name__}: {_bounded(exc, MAX_STDERR_CHARS)}")
                break
            if not isinstance(outcome, Mapping):
                failure = (f"trial {trial_number} sequence {sequence} arm {arm} returned "
                           f"{type(outcome).__name__}, not a mapping")
                break
            duration = outcome.get("duration_ms")
            if (isinstance(duration, bool) or not isinstance(duration, (int, float))
                    or not math.isfinite(float(duration)) or float(duration) < 0):
                failure = (f"trial {trial_number} sequence {sequence} arm {arm} returned "
                           f"an invalid duration_ms={duration!r}")
                break
            record = {"trial": trial_number, "arm": arm, "duration_ms": float(duration), "sequence": sequence}
            if "outputs_ok" in outcome:
                record["outputs_ok"] = outcome["outputs_ok"]
            records.append(record)
        if failure:
            break
    if failure:
        notes.append(failure)
    if not records:
        notes.append("no arm completed; differences are empty and unpaired")
    return { "schema": TRIALS_SCHEMA, "status": "partial" if failure else "completed", "records": records, "differences": pair_differences(records), "environment_mode": "separate_contexts", "notes": notes, }
def subprocess_trial_runner(command: str, *, timeout_s: float = GIT_TIMEOUT_SECONDS):
    """Run one ABBA arm in its own process with the per-arm cache environment."""
    argv = (command if isinstance(command, (list, tuple))
            else [part for part in shlex.split(str(command)) if part])
    if not argv:
        raise ValueError("trial command must be non-empty")
    def runner(*, arm: str, tree: str, pythonpath: str, env: Mapping[str, str], sequence: int, trial: int) -> dict[str, Any]:
        child_env = {**os.environ, **dict(env), "PYTHONPATH": pythonpath}
        started = time.perf_counter()
        try:
            proc = subprocess.run( list(argv), cwd=tree, env=child_env, capture_output=True, timeout=timeout_s, check=False)
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError( f"trial {trial} arm {arm} exceeded the {timeout_s:.0f}s limit") from exc
        duration_ms = (time.perf_counter() - started) * 1000.0
        return {"duration_ms": duration_ms, "outputs_ok": proc.returncode == 0, "stderr": _bounded(proc.stderr.decode("utf-8", "surrogateescape"), MAX_STDERR_CHARS)}
    return runner
def _is_safe_removal_root(root: str) -> bool:
    """Guard cleanup to /tmp overlay roots and pytest/temp test workspaces."""
    if not root or not os.path.isabs(root):
        return False
    root_abs, root_real = os.path.abspath(root), os.path.realpath(root)
    if root_abs == os.path.abspath(os.sep):
        return False
    home = _home_path()
    if _is_within(root_abs, home) or root_abs == os.path.abspath(os.getcwd()):
        return False
    temp_roots = { os.path.abspath(tempfile.gettempdir()), os.path.realpath(tempfile.gettempdir()), os.path.abspath("/tmp"), os.path.realpath("/tmp"), os.path.abspath("/private/tmp"), os.path.realpath("/private/tmp"), }
    for candidate in (root_abs, root_real):
        parts = candidate.replace("\\", "/").split("/")
        if (any(part.startswith("test_") for part in parts)
                and any(part.startswith(("pytest-of-", "pytest-")) for part in parts)):
            return True
        under_temp = any(candidate != temp_root and _is_within(candidate, temp_root)
                         for temp_root in temp_roots)
        if not under_temp:
            continue
        if os.path.basename(candidate).startswith("mindie_pr_overlay_"):
            return True
        if (os.path.isdir(os.path.join(candidate, "base"))
                and os.path.isdir(os.path.join(candidate, "pr"))):
            return True
    return False
def remove_overlay(plan: Mapping[str, Any] | str | os.PathLike[str]) -> dict[str, Any]:
    """Remove worktrees via ``git worktree remove --force`` and then the root."""
    if isinstance(plan, Mapping):
        raw_root, worktrees, repo = plan.get("root"), plan.get("worktrees") or [], plan.get("repo")
    else:
        raw_root, worktrees, repo = plan, [], None
    if not isinstance(raw_root, (str, os.PathLike)):
        raise ValueError("plan must expose an absolute root")
    root = os.path.abspath(os.fspath(raw_root))
    allowed_root = _is_safe_removal_root(root)
    if not allowed_root:
        raise ValueError(f"refusing to remove overlay root outside the temp overlay area: {root}")
    if os.path.islink(root):
        raise ValueError(f"refusing to remove a symlinked overlay root: {root}")
    if not isinstance(worktrees, (list, tuple)):
        raise ValueError("plan worktrees must be a list")
    removed: list[str] = []
    failed: list[dict[str, str]] = []
    for entry in worktrees:
        if not isinstance(entry, Mapping):
            failed.append({"path": repr(entry), "error": "malformed worktree record"})
            continue
        path = entry.get("path")
        if not isinstance(path, (str, os.PathLike)):
            failed.append({"path": repr(path), "error": "worktree has no path"})
            continue
        worktree = os.path.abspath(os.fspath(path))
        if not _is_within(worktree, root):
            failed.append({"path": worktree, "error": "worktree escapes overlay root"})
            continue
        if not os.path.lexists(worktree):
            continue
        git_repo = os.fspath(repo) if isinstance(repo, (str, os.PathLike)) else worktree
        try:
            _git(git_repo, ["worktree", "remove", "--force", worktree], context=f"remove {os.path.basename(worktree)} worktree")
            removed.append(worktree)
        except TimeoutError:
            raise
        except RuntimeError as exc:
            failed.append({"path": worktree, "error": _bounded(exc, MAX_STDERR_CHARS)})
    if os.path.lexists(root):
        if not allowed_root:
            raise ValueError(f"refusing to remove overlay root: {root}")
        try:
            shutil.rmtree(root)
        except TimeoutError:
            raise
        except OSError as exc:
            raise RuntimeError( f"could not remove overlay root {root}: {_bounded(exc, MAX_STDERR_CHARS)}"
            ) from exc
    return { "schema": CLEANUP_SCHEMA, "root": root, "removed_worktrees": removed, "failed_worktrees": failed, "root_removed": not os.path.lexists(root), }
def main(argv: Sequence[str] | None = None) -> int:
    """Materialise a PR-overlay plan and emit it as JSON (``bench pr-ab``)."""
    parser = argparse.ArgumentParser(prog="mindie-profiler bench pr-ab", description="Create base/PR overlay worktrees and emit the classification plan.")
    for flag in ("--repo", "--base", "--candidate", "--overlay-id"):
        parser.add_argument(flag, required=True)
    parser.add_argument("--overlay-root")
    parser.add_argument("--installed-package-dir", default=None, help="stage installed compiled extensions into both arms")
    parser.add_argument("--trial-cmd", default=None, help="ABBA trial command run once per arm in its own process")
    parser.add_argument("--trials", type=int, default=2, help="ABBA trial sequences")
    parser.add_argument("--out", "--output", dest="output", default=None)
    parser.add_argument("--remove", action="store_true", help="remove worktrees after emitting")
    args = parser.parse_args(argv)
    phase = "plan"
    try:
        plan = plan_overlay(args.repo, args.base, args.candidate, overlay_id=args.overlay_id, overlay_root=args.overlay_root)
        staging = None
        if args.installed_package_dir:
            staging = { arm: stage_compiled_extensions(plan["arms"][arm]["tree"], args.installed_package_dir)
                for arm in _ARMS}
        trials = None
        if args.trial_cmd:
            trials = run_paired_trials( plan, subprocess_trial_runner(args.trial_cmd), trials=args.trials)
        text = json.dumps({"schema": "mindie-bench-pr-ab/1", "plan": plan, "staging": staging, "trials": trials}, indent=2, sort_keys=True) + "\n"
        phase = "emit"
        if args.output:
            output = os.path.abspath(args.output)
            os.makedirs(os.path.dirname(output), exist_ok=True)
            temporary = output + ".tmp"
            with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            os.replace(temporary, output)
        else:
            sys.stdout.write(text)
        if args.remove:
            phase = "cleanup"
            remove_overlay(plan)
    except TimeoutError:
        raise
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"mindie-profiler bench pr-ab: {phase} failed: {_bounded(exc, MAX_STDERR_CHARS)}", file=sys.stderr)
        return 1
    return 0
