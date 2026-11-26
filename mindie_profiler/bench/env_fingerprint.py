"""Version-agnostic Ascend environment fingerprinting for incremental campaigns.

[Role]
  Probe the live hardware/software execution stack into a portable
  ``mindie-bench-env/1`` receipt and deterministic ``env_fingerprint_id``
  bucket identifier covering CANN (<9.0, 9.x, >=9.4), CANN OPP subpackages,
  wheel-safe 5-tier ``va_commit``, driver, torch/torch_npu/triton, custom-op
  libraries, timing protocol, and cache partition.

[Invariants]
  * Pure CPU at import time (``DEV-ZERO-CTX``): never imports ``torch``,
    ``torch_npu``, or ``mindie_sim``.
  * ``env_fingerprint_id`` hashes ONLY static stack identity fields; it
    strictly excludes ``ordinal``, ``physical_id``, hostname/IP, ``$HOME``,
    ``/dev/davinci*``, ``@sha256:``, timestamps, and live clock jitter.
  * CANN ``ascend_toolkit_install.info`` parsing is version-agnostic and never
    hard-fails on CANN ``<9.0`` or ``>=9.4``.
  * Every emitted receipt passes ``abi_portable.portable_receipt()``.

[Timeouts & Locks]
  All subprocess probes (``git``, ``npu-smi``) enforce a bounded finite timeout
  and re-raise ``TimeoutError`` before ``OSError``; acquires no locks.

[Side-Effect Policy]
  Strictly read-only probes against local filesystem/metadata/device handles.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from importlib import metadata as importlib_metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
from typing import Any

from .. import __version__ as PROFILER_VERSION
from ..cann_abi import parse_cann_install_info
from .abi_portable import portable_receipt
from .profiles import profile_section

ENV_SCHEMA = "mindie-bench-env/1"
DEFAULT_TIMING_PROTOCOL_ID = "certified_5w_3t_20r_3xl2_2p5ms"
CPU_SMOKE_PROTOCOL_ID = "cpu_smoke"
CACHE_PARTITIONS = ("shared", "train", "heldout")
NON_LIVE_CLOCK_SOURCES = frozenset({"", "unavailable", "device_properties_nominal_mhz"})


def is_live_clock_source(clock_source: str | None) -> bool:
    """Return True iff ``clock_source`` represents a live measured clock (not nominal fallback)."""
    return str(clock_source or "").strip() not in NON_LIVE_CLOCK_SOURCES

_CAMPAIGN_CFG = profile_section("campaign")
_TIMING_CFG = profile_section("timing")
_UNITS_CFG = profile_section("units")

_DIGEST_CHARS = int(_CAMPAIGN_CFG["digest_chars"])
_DIRTY_CHARS = int(_CAMPAIGN_CFG["dirty_hash_chars"])
_SUBPROCESS_TIMEOUT_S = float(_CAMPAIGN_CFG["subprocess_timeout_s"])
_HASH_CHUNK_BYTES = int(_CAMPAIGN_CFG["hash_chunk_bytes"])
_CLOCK_DRIFT_PCT = float(_CAMPAIGN_CFG["clock_drift_pct"])
_CLOCK_MIN_RATIO = float(_CAMPAIGN_CFG["clock_throttle_min_ratio"])
_CLOCK_MAX_RATIO = float(_CAMPAIGN_CFG["clock_max_ratio"])
_HZ_PER_MHZ = int(_UNITS_CFG["hz_per_mhz"])
_MAX_CLOCK_HZ = float(_TIMING_CFG["max_clock_hz"])
_NPU_SMI_MAP_MIN_COLS = int(_CAMPAIGN_CFG["npu_smi_map_min_cols"])
_NPU_SMI_MAP_PHY_ID_COL = int(_CAMPAIGN_CFG["npu_smi_map_phy_id_col"])

STATIC_BUCKET_KEYS: tuple[str, ...] = (
    "sku",
    "soc_arch",
    "hw_geometry",
    "driver_version",
    "cann_version",
    "cann_innerversion",
    "cann_packages",
    "torch_version",
    "torch_npu_version",
    "va_commit",
    "triton_version",
    "custom_op_libs",
    "profiler_version",
    "timing_protocol_id",
    "cache_partition",
)
_ARCH_DIRS = ("aarch64-linux", "x86_64-linux")
_CANN_PACKAGE_KEYS = ("ops_transformer", "ops_nn", "hccl", "atb")
_CUSTOM_OP_LIBS = (
    "catlass",
    "fla",
    "fla_npu",
    "flash_attn_npu",
    "tilelang",
    "vllm_ascend_csrc",
    "xllm_ops",
)
_SLUG_RE = re.compile(r"[^a-z0-9_]+")
_VER_SLUG_RE = re.compile(r"[^a-z0-9._-]+")
_CUR_FREQ_RE = re.compile(
    r"aicore\s+cur(?:rent\s+)?_?freq\s*\(mhz\)\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", re.I
)
_CHIP_SECTION_HEADER_RE = re.compile(r"^\s*Chip\s+ID\s*:\s*\d+\b", re.I | re.M)
_DRIVER_RE = re.compile(r"^\s*(?:software|driver)?\s*version\s*[:=]\s*([^\s]+)", re.I | re.M)


def canonical_env_json(payload: Mapping[str, Any]) -> bytes:
    """Serialize a mapping deterministically for hashing."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def infer_soc_arch(sku: str | None) -> str:
    """Normalize an Ascend SKU string to ``A2``, ``A3``, ``A5``, or ``unknown``."""
    text = str(sku or "").strip().upper()
    if not text:
        return "unknown"
    if "950" in text or text.startswith("A5"):
        return "A5"
    if "93" in text and ("910" in text or "ASCEND" in text):
        return "A3"
    if text.startswith("A3"):
        return "A3"
    if "910B" in text or "DAV_2201" in text or text.startswith("A2"):
        return "A2"
    return "unknown"


def _bounded_run(cmd: Sequence[str], *, cwd: Path | None = None) -> str | None:
    try:
        proc = subprocess.run(
            list(cmd),
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_SUBPROCESS_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"probe command timed out after {_SUBPROCESS_TIMEOUT_S}s: {cmd[0]}") from exc
    except TimeoutError:
        raise
    except OSError:
        return None
    return proc.stdout if proc.returncode == 0 else None


def _candidate_cann_roots(
    cann_root: str | os.PathLike[str] | None,
    environ: Mapping[str, str],
    ascend_base: str | os.PathLike[str],
) -> list[Path]:
    candidates: list[Path] = []
    if cann_root is not None:
        candidates.append(Path(cann_root).expanduser())
    for key in ("MINDIE_CANN_ROOT", "ASCEND_HOME_PATH", "ASCEND_TOOLKIT_HOME"):
        raw = str(environ.get(key) or "").strip()
        if raw:
            candidates.append(Path(raw).expanduser())
    base = Path(ascend_base)
    candidates.append(base / "cann")
    if base.is_dir():
        try:
            candidates.extend(sorted(base.glob("cann-*"), reverse=True))
        except TimeoutError:
            raise
        except OSError:
            pass
    candidates.append(base / "ascend-toolkit" / "latest")
    return candidates


def _preferred_arch_dirs(host_machine: str | None = None) -> list[str]:
    machine = (host_machine or platform.machine()).lower()
    ordered: list[str] = []
    if machine in {"aarch64", "arm64"}:
        ordered.append("aarch64-linux")
    elif machine in {"x86_64", "amd64"}:
        ordered.append("x86_64-linux")
    for item in _ARCH_DIRS:
        if item not in ordered:
            ordered.append(item)
    return ordered


def _read_install_info(path: Path) -> dict[str, str]:
    try:
        return parse_cann_install_info(path.read_text(encoding="utf-8", errors="replace"))
    except TimeoutError:
        raise
    except OSError:
        return {}


def probe_cann_version(
    *,
    cann_root: str | os.PathLike[str] | None = None,
    environ: Mapping[str, str] | None = None,
    ascend_base: str | os.PathLike[str] = "/usr/local/Ascend",
    host_machine: str | None = None,
) -> dict[str, Any]:
    """Version-agnostic CANN ``ascend_toolkit_install.info`` and subpackage probe."""
    env = os.environ if environ is None else environ
    arch_dirs = _preferred_arch_dirs(host_machine)
    found_root: Path | None = None
    info: dict[str, str] = {}
    seen: set[str] = set()
    for candidate in _candidate_cann_roots(cann_root, env, ascend_base):
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        for arch_dir in arch_dirs:
            info_path = candidate / arch_dir / "ascend_toolkit_install.info"
            if info_path.is_file():
                info = _read_install_info(info_path)
                found_root = candidate
                break
        if info:
            break
        direct_info = candidate / "ascend_toolkit_install.info"
        if direct_info.is_file():
            info = _read_install_info(direct_info)
            found_root = candidate
            break
    version = str(info.get("version") or info.get("Version") or "").strip() or "unknown"
    inner = str(info.get("innerversion") or info.get("InnerVersion") or "").strip() or "unknown"
    packages = probe_cann_packages(cann_root=found_root, environ=env)
    return {
        "cann_version": version,
        "cann_innerversion": inner,
        "cann_packages": packages,
    }


def _extract_version_from_info(path: Path) -> str | None:
    parsed = _read_install_info(path)
    for key in ("Version", "version", "version_dir"):
        val = str(parsed.get(key) or "").strip()
        if val:
            return val
    return None


def probe_cann_packages(
    *,
    cann_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Discover granular CANN subpackage versions (``ops_transformer/ops_nn/hccl/atb``)."""
    env = os.environ if environ is None else environ
    packages = {name: "absent" for name in _CANN_PACKAGE_KEYS}
    roots: list[Path] = []
    opp_env = str(env.get("ASCEND_OPP_PATH") or "").strip()
    if opp_env:
        roots.append(Path(opp_env).expanduser())
    if cann_root is not None:
        roots.extend([cann_root / "opp", cann_root])
    rel_map = {
        "ops_transformer": ("built-in/op_impl/ai_core/tbe/ops_transformer/version.info", "vendors/ops_transformer/version.info", "ops_transformer/version.info"),
        "ops_nn": ("built-in/op_impl/ai_core/tbe/ops_nn/version.info", "vendors/ops_nn/version.info", "ops_nn/version.info"),
        "hccl": ("hccl/version.info", "../hccl/version.info"),
        "atb": ("atb/version.info", "../atb/version.info"),
    }
    for pkg, rels in rel_map.items():
        for root in roots:
            for rel in rels:
                candidate = root / rel
                if candidate.is_file():
                    ver = _extract_version_from_info(candidate)
                    if ver:
                        packages[pkg] = ver
                        break
            if packages[pkg] != "absent":
                break
    if packages["ops_transformer"] == "absent":
        for dist_name in ("cann_ops_transformer", "cann-ops-transformer"):
            ver = _safe_dist_version(dist_name)
            if ver:
                packages["ops_transformer"] = ver
                break
    return packages


def _safe_dist_version(dist_name: str) -> str | None:
    try:
        return importlib_metadata.version(dist_name)
    except TimeoutError:
        raise
    except Exception:
        return None


def _pep610_vcs_commit(dist_name: str) -> str | None:
    try:
        dist = importlib_metadata.distribution(dist_name)
        raw = dist.read_text("direct_url.json")
    except TimeoutError:
        raise
    except Exception:
        return None
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except ValueError:
        return None
    vcs = parsed.get("vcs_info") if isinstance(parsed, Mapping) else None
    if not isinstance(vcs, Mapping):
        return None
    commit = str(vcs.get("commit_id") or vcs.get("requested_revision") or "").strip()
    return commit or None


def _git_checkout_commit(pkg_root: Path | None) -> str | None:
    if pkg_root is None or not pkg_root.exists():
        return None
    head = _bounded_run(("git", "rev-parse", "HEAD"), cwd=pkg_root)
    if not head:
        return None
    commit = head.strip()
    if not commit:
        return None
    porcelain = _bounded_run(("git", "status", "--porcelain"), cwd=pkg_root)
    if porcelain and porcelain.strip():
        dirty_digest = hashlib.sha256(porcelain.encode("utf-8")).hexdigest()[:_DIRTY_CHARS]
        return f"{commit}+dirty-{dirty_digest}"
    return commit


def probe_va_commit(
    *,
    explicit_va_commit: str | None = None,
    va_module: Any = None,
    va_repo_root: str | os.PathLike[str] | None = None,
) -> str:
    """5-tier wheel-safe ``va_commit`` resolver (never assumes ``.git`` exists)."""
    if explicit_va_commit is not None and str(explicit_va_commit).strip():
        return str(explicit_va_commit).strip()
    for dist_name in ("vllm-ascend", "vllm_ascend"):
        commit = _pep610_vcs_commit(dist_name)
        if commit:
            return commit
    repo_root: Path | None = Path(va_repo_root).expanduser() if va_repo_root is not None else None
    if repo_root is None and va_module is not None:
        mod_file = getattr(va_module, "__file__", None)
        if mod_file:
            repo_root = Path(mod_file).resolve().parent
    git_rev = _git_checkout_commit(repo_root)
    if git_rev:
        return git_rev
    for dist_name in ("vllm-ascend", "vllm_ascend"):
        ver = _safe_dist_version(dist_name)
        if ver:
            return f"wheel:{ver}"
    mod_ver = getattr(va_module, "__version__", None) if va_module is not None else None
    if mod_ver:
        return f"wheel:{mod_ver}"
    return "absent"


def probe_driver_version(
    *,
    driver_info_path: str | os.PathLike[str] = "/usr/local/Ascend/driver/version.info",
    allow_npu_smi: bool = False,
) -> str:
    """Read Ascend driver version from ``version.info`` or bounded ``npu-smi``."""
    path = Path(driver_info_path)
    if path.is_file():
        ver = _extract_version_from_info(path)
        if ver:
            return ver
    if allow_npu_smi:
        out = _bounded_run(("npu-smi", "info", "-t", "board"))
        if out:
            match = _DRIVER_RE.search(out)
            if match:
                return match.group(1).strip()
    return "unknown"


def _file_sha256_prefix(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(_HASH_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
        return f"so:{digest.hexdigest()[:_DIGEST_CHARS]}"
    except TimeoutError:
        raise
    except OSError:
        return None


def probe_custom_op_libs(
    *,
    modules: Mapping[str, Any] | None = None,
    so_paths: Mapping[str, str | os.PathLike[str]] | None = None,
) -> dict[str, str]:
    """Collect sorted versions/digests for non-CANN custom operator libraries."""
    mod_map = modules or {}
    path_map = so_paths or {}
    result: dict[str, str] = {}
    for name in _CUSTOM_OP_LIBS:
        if name in path_map and path_map[name]:
            so_hash = _file_sha256_prefix(Path(path_map[name]))
            if so_hash:
                result[name] = so_hash
                continue
        mod = mod_map.get(name)
        mod_file = getattr(mod, "__file__", None) if mod is not None else None
        if isinstance(mod_file, str) and mod_file.endswith(".so") and Path(mod_file).is_file():
            so_hash = _file_sha256_prefix(Path(mod_file))
            if so_hash:
                result[name] = so_hash
                continue
        vcs = _pep610_vcs_commit(name) or _pep610_vcs_commit(name.replace("_", "-"))
        if vcs:
            result[name] = vcs
            continue
        ver = (
            getattr(mod, "__version__", None)
            or _safe_dist_version(name)
            or _safe_dist_version(name.replace("_", "-"))
        )
        result[name] = str(ver).strip() if ver else "absent"
    return result


def _resolve_npu_smi_card_chip(physical_id: int) -> tuple[int, int | None]:
    """Map ``Chip Phy-ID`` to ``(NPU ID, Chip ID)`` via ``npu-smi info -m`` for dual-die A3."""
    mapping_out = _bounded_run(("npu-smi", "info", "-m"))
    if not mapping_out:
        return int(physical_id), None
    for raw_line in mapping_out.splitlines():
        cols = raw_line.split()
        if len(cols) < _NPU_SMI_MAP_MIN_COLS:
            continue
        try:
            npu_id = int(cols[0])
            chip_id = int(cols[1])
            phy_id = int(cols[_NPU_SMI_MAP_PHY_ID_COL])
        except ValueError:
            continue
        if phy_id == int(physical_id):
            return npu_id, chip_id
    return int(physical_id), None


def _select_chip_section(common_out: str, chip_id: int | None) -> str:
    """Slice the matching ``Chip ID : <chip_id>`` block from dual-die ``npu-smi info -t common``."""
    if chip_id is None:
        return common_out
    if not _CHIP_SECTION_HEADER_RE.search(common_out):
        return common_out
    blocks = re.split(r"(?=^\s*Chip\s+ID\s*:\s*\d+\b)", common_out, flags=re.I | re.M)
    pattern = re.compile(rf"^\s*Chip\s+ID\s*:\s*{int(chip_id)}\b", re.I | re.M)
    for block in blocks:
        if pattern.search(block):
            return block
    return ""


def probe_observed_clock(
    *,
    torch_npu: Any = None,
    device_properties: Mapping[str, Any] | None = None,
    physical_id: int | None = None,
    allow_npu_smi: bool = False,
) -> tuple[float | None, str]:
    """Read live NPU AIC clock in MHz without contaminating the static bucket key."""
    if torch_npu is not None:
        for attr in ("npu_get_clock_rate", "get_clock_rate"):
            getter = getattr(torch_npu, attr, None)
            if not callable(getter):
                continue
            try:
                value = float(getter())
            except TimeoutError:
                raise
            except Exception:
                continue
            if math.isfinite(value) and value > 0:
                mhz = value / _HZ_PER_MHZ if value > _MAX_CLOCK_HZ else value
                return mhz, "torch_npu_clock_rate"
    if allow_npu_smi:
        chip_id: int | None = None
        cmd = ["npu-smi", "info", "-t", "common"]
        if physical_id is not None:
            card_id, chip_id = _resolve_npu_smi_card_chip(int(physical_id))
            cmd.extend(["-i", str(card_id)])
        out = _bounded_run(cmd)
        if not out and physical_id is not None and chip_id is not None and card_id != int(physical_id):
            out = _bounded_run(["npu-smi", "info", "-t", "common", "-i", str(int(physical_id))])
        if out:
            scoped = _select_chip_section(out, chip_id)
            match = _CUR_FREQ_RE.search(scoped)
            if match:
                val = float(match.group(1))
                if math.isfinite(val) and val > 0:
                    return val, "npu-smi_cur_freq_mhz"
    props = device_properties if isinstance(device_properties, Mapping) else {}
    nominal = props.get("clock_mhz")
    if isinstance(nominal, (int, float)) and not isinstance(nominal, bool) and math.isfinite(float(nominal)) and float(nominal) > 0:
        return float(nominal), "device_properties_nominal_mhz"
    return None, "unavailable"


def validate_clock_band(
    observed_clock_mhz: float | None,
    *,
    nominal_clock_mhz: float | None = None,
    baseline_clock_mhz: float | None = None,
) -> tuple[bool, str | None]:
    """Reject thermally throttled, out-of-band, or drifted clock readings from qualified hits."""
    if observed_clock_mhz is None:
        return True, None
    obs = float(observed_clock_mhz)
    if not math.isfinite(obs) or obs <= 0:
        return False, "observed_clock_invalid"
    if nominal_clock_mhz is not None and math.isfinite(float(nominal_clock_mhz)) and float(nominal_clock_mhz) > 0:
        ratio = obs / float(nominal_clock_mhz)
        if ratio < _CLOCK_MIN_RATIO:
            return False, f"clock_thermally_throttled:{obs:.1f}<{_CLOCK_MIN_RATIO * float(nominal_clock_mhz):.1f}"
        if ratio > _CLOCK_MAX_RATIO:
            return False, f"clock_out_of_band:{obs:.1f}>{_CLOCK_MAX_RATIO * float(nominal_clock_mhz):.1f}"
    if baseline_clock_mhz is not None and math.isfinite(float(baseline_clock_mhz)) and float(baseline_clock_mhz) > 0:
        drift_pct = abs(obs - float(baseline_clock_mhz)) / float(baseline_clock_mhz) * 100.0
        if drift_pct > _CLOCK_DRIFT_PCT:
            return False, f"clock_drift_exceeded:{drift_pct:.2f}pct>{_CLOCK_DRIFT_PCT:.1f}pct"
    return True, None


def static_bucket_key(fingerprint: Mapping[str, Any]) -> dict[str, Any]:
    """Project strictly static stack-identity fields (zero host/ordinal/clock jitter)."""
    hw = fingerprint.get("hw_geometry")
    hw_clean = {str(k): v for k, v in sorted(hw.items())} if isinstance(hw, Mapping) else {}
    cann_pkgs = fingerprint.get("cann_packages")
    pkgs_clean = (
        {str(k): str(v) for k, v in sorted(cann_pkgs.items())}
        if isinstance(cann_pkgs, Mapping)
        else {}
    )
    custom = fingerprint.get("custom_op_libs")
    custom_clean = (
        {str(k): str(v) for k, v in sorted(custom.items())}
        if isinstance(custom, Mapping)
        else {}
    )
    return {
        "sku": str(fingerprint.get("sku") or "unknown"),
        "soc_arch": str(fingerprint.get("soc_arch") or infer_soc_arch(str(fingerprint.get("sku") or ""))),
        "hw_geometry": hw_clean,
        "driver_version": str(fingerprint.get("driver_version") or "unknown"),
        "cann_version": str(fingerprint.get("cann_version") or "unknown"),
        "cann_innerversion": str(fingerprint.get("cann_innerversion") or "unknown"),
        "cann_packages": pkgs_clean,
        "torch_version": str(fingerprint.get("torch_version") or "absent"),
        "torch_npu_version": str(fingerprint.get("torch_npu_version") or "absent"),
        "va_commit": str(fingerprint.get("va_commit") or "absent"),
        "triton_version": str(fingerprint.get("triton_version") or "absent"),
        "custom_op_libs": custom_clean,
        "profiler_version": str(fingerprint.get("profiler_version") or PROFILER_VERSION),
        "timing_protocol_id": str(fingerprint.get("timing_protocol_id") or DEFAULT_TIMING_PROTOCOL_ID),
        "cache_partition": str(fingerprint.get("cache_partition") or "shared"),
    }


def compute_env_fingerprint_id(fingerprint: Mapping[str, Any]) -> str:
    """Compute ``env-<sku_slug>-cann<cann_short>-<sha256[:16]>`` from static fields only."""
    static = static_bucket_key(fingerprint)
    sku_slug = _SLUG_RE.sub("_", static["sku"].lower()).strip("_") or "unknown"
    cann_short = _VER_SLUG_RE.sub("_", static["cann_version"].lower()).strip("_") or "unknown"
    digest = hashlib.sha256(canonical_env_json(static)).hexdigest()[:_DIGEST_CHARS]
    return f"env-{sku_slug}-cann{cann_short}-{digest}"


def probe_env_fingerprint(
    *,
    sku: str | None = None,
    soc_arch: str | None = None,
    device_properties: Mapping[str, Any] | None = None,
    torch: Any = None,
    torch_npu: Any = None,
    modules: Mapping[str, Any] | None = None,
    so_paths: Mapping[str, str | os.PathLike[str]] | None = None,
    cann_root: str | os.PathLike[str] | None = None,
    driver_info_path: str | os.PathLike[str] = "/usr/local/Ascend/driver/version.info",
    explicit_va_commit: str | None = None,
    va_repo_root: str | os.PathLike[str] | None = None,
    timing_protocol_id: str = DEFAULT_TIMING_PROTOCOL_ID,
    cache_partition: str = "shared",
    observed_clock_mhz: float | None = None,
    clock_source: str | None = None,
    nominal_clock_mhz: float | None = None,
    physical_id: int | None = None,
    allow_npu_smi: bool = False,
    environ: Mapping[str, str] | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    """Assemble and portable-scrub a complete ``mindie-bench-env/1`` fingerprint receipt."""
    props = device_properties if isinstance(device_properties, Mapping) else {}
    resolved_sku = str(sku or props.get("name") or "unknown").strip() or "unknown"
    resolved_arch = str(soc_arch or infer_soc_arch(resolved_sku)).strip() or "unknown"
    hw_geometry = {
        "aic_count": props.get("aic_count"),
        "aiv_count": props.get("vector_count") if props.get("aiv_count") is None else props.get("aiv_count"),
        "l2_bytes": props.get("l2_bytes"),
        "hbm_bytes": props.get("hbm_bytes"),
    }
    cann_info = probe_cann_version(cann_root=cann_root, environ=environ)
    driver_ver = probe_driver_version(driver_info_path=driver_info_path, allow_npu_smi=allow_npu_smi)
    mod_map = dict(modules or {})
    va_commit = probe_va_commit(
        explicit_va_commit=explicit_va_commit,
        va_module=mod_map.get("vllm_ascend"),
        va_repo_root=va_repo_root,
    )
    torch_ver = str(getattr(torch, "__version__", None) or _safe_dist_version("torch") or "absent")
    torch_npu_ver = str(getattr(torch_npu, "__version__", None) or _safe_dist_version("torch_npu") or "absent")
    triton_mod = mod_map.get("triton")
    triton_ver = str(
        getattr(triton_mod, "__version__", None)
        or _safe_dist_version("triton")
        or _safe_dist_version("triton-ascend")
        or "absent"
    )
    custom_libs = probe_custom_op_libs(modules=mod_map, so_paths=so_paths)
    if observed_clock_mhz is None:
        obs_mhz, obs_source = probe_observed_clock(
            torch_npu=torch_npu,
            device_properties=props,
            physical_id=physical_id,
            allow_npu_smi=allow_npu_smi,
        )
    else:
        obs_mhz = float(observed_clock_mhz)
        obs_source = str(clock_source or "explicit")
    payload: dict[str, Any] = {
        "schema": ENV_SCHEMA,
        "sku": resolved_sku,
        "soc_arch": resolved_arch,
        "hw_geometry": hw_geometry,
        "driver_version": driver_ver,
        "cann_version": cann_info["cann_version"],
        "cann_innerversion": cann_info["cann_innerversion"],
        "cann_packages": cann_info["cann_packages"],
        "torch_version": torch_ver,
        "torch_npu_version": torch_npu_ver,
        "va_commit": va_commit,
        "triton_version": triton_ver,
        "custom_op_libs": custom_libs,
        "profiler_version": PROFILER_VERSION,
        "timing_protocol_id": str(timing_protocol_id or DEFAULT_TIMING_PROTOCOL_ID),
        "cache_partition": str(cache_partition or "shared"),
        "observed_clock_mhz": obs_mhz,
        "clock_source": obs_source,
    }
    resolved_home = os.environ.get("HOME") if home is None else home
    scrubbed = portable_receipt(payload, home=resolved_home)
    scrubbed["env_fingerprint_id"] = compute_env_fingerprint_id(scrubbed)
    return scrubbed


__all__ = [
    "CACHE_PARTITIONS",
    "CPU_SMOKE_PROTOCOL_ID",
    "DEFAULT_TIMING_PROTOCOL_ID",
    "ENV_SCHEMA",
    "NON_LIVE_CLOCK_SOURCES",
    "STATIC_BUCKET_KEYS",
    "canonical_env_json",
    "compute_env_fingerprint_id",
    "infer_soc_arch",
    "is_live_clock_source",
    "probe_cann_packages",
    "probe_cann_version",
    "probe_custom_op_libs",
    "probe_driver_version",
    "probe_env_fingerprint",
    "probe_observed_clock",
    "probe_va_commit",
    "static_bucket_key",
    "validate_clock_band",
]
