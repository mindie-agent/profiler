"""CANN 9.x public ABI discovery, version gate, and cached shim compilation.

[Role]
  Locate a CANN 9.x (>= 9.0) installation, verify required public C headers
  (``mspti.h``, ``acl/acl_rt.h``, ``acl/acl_prof.h``) and shared libraries,
  construct library-resolved runtime environments, and compile/cache the
  native ``libmindie_cann9_capture.so`` preload shim.

[Invariants]
  * CANN < 9.0 is explicitly rejected with ``ProfilerUsageError``; no legacy
    8.x fallback paths exist.
  * Explicit ``cann_root`` never silently falls back to another installation.
  * Compiled shims are keyed by ``(abi_version, cann_version, innerversion,
    arch, source_sha256)`` and published atomically via ``os.replace``.

[Timeouts & Locks]
  ``ensure_capture_shim_binary`` enforces a bounded ``timeout_s`` compiler
  budget under an advisory ``flock`` file lock when available.

[Side-Effect Policy]
  Discovery is read-only.  Shim compilation writes only inside the isolated
  ``cache_root`` (default ``$MINDIE_DATA_HOME/profiler/cann9_shim``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import platform
import re
import subprocess

from .events import ProfilerError, ProfilerUsageError

SHIM_ABI_VERSION = "cann9-native-capture-v3"
SHIM_SOURCE_FILENAME = "_cann9_capture_shim.c"
SHIM_HEADER_FILENAME = "_cann9_capture_mspti.h"
_VERSION_RE = re.compile(r"^\s*(\d+)\.(\d+)(?:\.([0-9A-Za-z._-]+))?\s*$")
_ARCH_CANDIDATES = ("aarch64-linux", "x86_64-linux")


@dataclass(frozen=True, slots=True)
class Cann9Installation:
    """Verified CANN 9.x installation descriptor."""

    cann_root: Path
    arch_dir: Path
    arch: str
    version: str
    major_version: int
    minor_version: int
    innerversion: str
    acl_include_dir: Path
    mspti_include_dir: Path
    libascendcl_so: Path
    libmsprofiler_so: Path
    libmspti_so: Path
    msprof_bin: Path

    def as_dict(self) -> dict[str, object]:
        return {
            "cann_root": str(self.cann_root),
            "arch_dir": str(self.arch_dir),
            "arch": self.arch,
            "version": self.version,
            "major_version": self.major_version,
            "minor_version": self.minor_version,
            "innerversion": self.innerversion,
            "libascendcl_so": str(self.libascendcl_so),
            "libmsprofiler_so": str(self.libmsprofiler_so),
            "libmspti_so": str(self.libmspti_so),
            "msprof_bin": str(self.msprof_bin),
        }


def parse_cann_install_info(text: str) -> dict[str, str]:
    """Parse ``ascend_toolkit_install.info`` ``key=value`` pairs."""

    info: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            info[key] = value
    return info


def parse_cann_version_tuple(version: str) -> tuple[int, int, str]:
    """Parse ``major.minor[.patch]`` and enforce ``major >= 9``."""

    match = _VERSION_RE.match(version or "")
    if match is None:
        raise ProfilerUsageError(
            f"unrecognized CANN version string {version!r}; expected >= 9.0"
        )
    major = int(match.group(1))
    minor = int(match.group(2))
    rest = match.group(3) or ""
    if major < 9:
        raise ProfilerUsageError(
            f"CANN >= 9.0 is required for native steady-state capture; "
            f"found unsupported CANN {version!r}"
        )
    return major, minor, rest


def _resolve_arch_dir(cann_root: Path, host_machine: str | None = None) -> Path:
    machine = (host_machine or platform.machine()).lower()
    preferred: list[str] = []
    if machine in {"aarch64", "arm64"}:
        preferred.append("aarch64-linux")
    elif machine in {"x86_64", "amd64"}:
        preferred.append("x86_64-linux")
    for candidate in _ARCH_CANDIDATES:
        if candidate not in preferred:
            preferred.append(candidate)
    for dirname in preferred:
        arch_dir = cann_root / dirname
        if (arch_dir / "ascend_toolkit_install.info").is_file():
            return arch_dir
    raise ProfilerUsageError(
        f"no <arch>-linux/ascend_toolkit_install.info under {cann_root}"
    )


def _validate_cann9_root(
    cann_root: Path,
    *,
    host_machine: str | None = None,
) -> Cann9Installation:
    if not cann_root.is_dir():
        raise ProfilerUsageError(f"CANN root does not exist: {cann_root}")
    resolved_root = cann_root.resolve()
    arch_dir = _resolve_arch_dir(resolved_root, host_machine=host_machine)
    info_path = arch_dir / "ascend_toolkit_install.info"
    try:
        info = parse_cann_install_info(info_path.read_text(encoding="utf-8"))
    except TimeoutError:
        raise
    except OSError as exc:
        raise ProfilerUsageError(f"cannot read {info_path}: {exc}") from exc

    version = info.get("version", "")
    major, minor, _ = parse_cann_version_tuple(version)
    arch = info.get("arch") or arch_dir.name.split("-", 1)[0]
    innerversion = info.get("innerversion") or "unknown"

    acl_include_dir = arch_dir / "include"
    mspti_include_dir = resolved_root / "tools" / "mspti" / "include"
    acl_rt_h = acl_include_dir / "acl" / "acl_rt.h"
    acl_prof_h = acl_include_dir / "acl" / "acl_prof.h"
    mspti_h = mspti_include_dir / "mspti.h"
    libascendcl_so = arch_dir / "lib64" / "libascendcl.so"
    libmsprofiler_so = arch_dir / "lib64" / "libmsprofiler.so"
    libmspti_so = resolved_root / "tools" / "mspti" / "lib64" / "libmspti.so"
    msprof_bin = resolved_root / "tools" / "profiler" / "bin" / "msprof"

    required_files = (
        ("acl/acl_rt.h", acl_rt_h),
        ("acl/acl_prof.h", acl_prof_h),
        ("mspti.h", mspti_h),
        ("libascendcl.so", libascendcl_so),
        ("libmsprofiler.so", libmsprofiler_so),
        ("libmspti.so", libmspti_so),
        ("msprof", msprof_bin),
    )
    missing = [label for label, path in required_files if not path.is_file()]
    if missing:
        raise ProfilerUsageError(
            f"CANN {version} at {resolved_root} is missing required files: "
            f"{', '.join(missing)}"
        )

    try:
        acl_rt_text = acl_rt_h.read_text(encoding="utf-8", errors="ignore")
        acl_prof_text = acl_prof_h.read_text(encoding="utf-8", errors="ignore")
    except TimeoutError:
        raise
    except OSError as exc:
        raise ProfilerUsageError(f"cannot inspect CANN 9.x headers: {exc}") from exc

    if "aclrtApiInjectionSetFunc" not in acl_rt_text:
        raise ProfilerUsageError(
            f"{acl_rt_h} lacks public aclrtApiInjectionSetFunc required by CANN 9.x capture"
        )
    if "ACL_PROF_AICORE_SHAPE" not in acl_prof_text:
        raise ProfilerUsageError(
            f"{acl_prof_h} lacks ACL_PROF_AICORE_SHAPE required by CANN 9.x Gear-2 capture"
        )

    return Cann9Installation(
        cann_root=resolved_root,
        arch_dir=arch_dir,
        arch=arch,
        version=version,
        major_version=major,
        minor_version=minor,
        innerversion=innerversion,
        acl_include_dir=acl_include_dir,
        mspti_include_dir=mspti_include_dir,
        libascendcl_so=libascendcl_so,
        libmsprofiler_so=libmsprofiler_so,
        libmspti_so=libmspti_so,
        msprof_bin=msprof_bin,
    )


def discover_cann9(
    cann_root: str | os.PathLike[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    ascend_base: str | os.PathLike[str] = "/usr/local/Ascend",
    host_machine: str | None = None,
) -> Cann9Installation:
    """Discover and validate a CANN >= 9.0 installation."""

    if cann_root is not None:
        return _validate_cann9_root(
            Path(cann_root).expanduser(), host_machine=host_machine
        )

    env_map = os.environ if env is None else env
    candidates: list[Path] = []
    for env_key in ("MINDIE_CANN_ROOT", "ASCEND_HOME_PATH", "ASCEND_TOOLKIT_HOME"):
        raw = (env_map.get(env_key) or "").strip()
        if raw:
            candidates.append(Path(raw).expanduser())

    base = Path(ascend_base)
    candidates.append(base / "cann")
    if base.is_dir():
        versioned = sorted(base.glob("cann-9*"), reverse=True)
        candidates.extend(versioned)
    candidates.append(base / "ascend-toolkit" / "latest")

    errors: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen or not candidate.exists():
            continue
        seen.add(key)
        try:
            return _validate_cann9_root(candidate, host_machine=host_machine)
        except ProfilerUsageError as exc:
            errors.append(f"{candidate}: {exc}")

    detail = "; ".join(errors) if errors else f"no CANN installation under {base}"
    raise ProfilerUsageError(
        f"unable to locate a valid CANN >= 9.0 installation ({detail})"
    )


def build_cann_runtime_env(
    install: Cann9Installation,
    base_env: Mapping[str, str] | None = None,
    *,
    driver_root: str | os.PathLike[str] = "/usr/local/Ascend/driver",
) -> dict[str, str]:
    """Return a clean environment matching CANN 9.x ``set_env.sh`` + MSPTI/profiler."""

    env = dict(os.environ if base_env is None else base_env)
    drv = Path(driver_root).expanduser().resolve()
    root = Path(install.cann_root).expanduser().resolve()
    arch_dir = Path(install.arch_dir).expanduser().resolve()
    tiling_dir = (
        root / "opp" / "built-in" / "op_impl" / "ai_core" / "tbe" / "op_tiling" / "lib" / "linux" / install.arch
    )
    lib_dirs = [
        root / "lib64",
        root / "lib64" / "plugin" / "opskernel",
        root / "lib64" / "plugin" / "nnengine",
        arch_dir / "lib64",
        arch_dir / "lib64" / "plugin" / "opskernel",
        arch_dir / "lib64" / "plugin" / "nnengine",
        tiling_dir,
        root / "tools" / "mspti" / "lib64",
        root / "tools" / "profiler" / "lib64",
        drv / "lib64",
        drv / "lib64" / "common",
        drv / "lib64" / "driver",
    ]
    has_real_driver = any(
        (p / "libascend_hal.so").is_file()
        for p in (drv / "lib64" / "driver", drv / "lib64" / "common", drv / "lib64")
    )
    ordered_libs: list[str] = []
    for p in lib_dirs:
        s = str(p)
        if p.is_dir() and s not in ordered_libs:
            ordered_libs.append(s)
    for item in env.get("LD_LIBRARY_PATH", "").split(os.pathsep):
        if item and item not in ordered_libs:
            ordered_libs.append(item)
    if not has_real_driver:
        for devlib in (root / "devlib", arch_dir / "devlib"):
            s = str(devlib)
            if devlib.is_dir() and s not in ordered_libs:
                ordered_libs.append(s)
    env["LD_LIBRARY_PATH"] = os.pathsep.join(ordered_libs)

    env["ASCEND_HOME_PATH"] = str(root)
    env["ASCEND_TOOLKIT_HOME"] = str(root)
    env["ASCEND_AICPU_PATH"] = str(root)
    if (root / "opp").is_dir():
        env["ASCEND_OPP_PATH"] = str(root / "opp")
    if (root / "toolkit").is_dir():
        env["TOOLCHAIN_HOME"] = str(root / "toolkit")

    py_dirs = [
        str(p)
        for p in (
            root / "python" / "site-packages",
            root / "opp" / "built-in" / "op_impl" / "ai_core" / "tbe",
        )
        if p.is_dir()
    ]
    if py_dirs:
        for item in env.get("PYTHONPATH", "").split(os.pathsep):
            if item and item not in py_dirs:
                py_dirs.append(item)
        env["PYTHONPATH"] = os.pathsep.join(py_dirs)

    bin_dirs = [
        str(p)
        for p in (
            root / "bin",
            root / "tools" / "ccec_compiler" / "bin",
            root / "tools" / "profiler" / "bin",
            arch_dir / "bin",
        )
        if p.is_dir()
    ]
    for item in env.get("PATH", "").split(os.pathsep):
        if item and item not in bin_dirs:
            bin_dirs.append(item)
    env["PATH"] = os.pathsep.join(bin_dirs)
    return env


def default_shim_cache_dir(env: Mapping[str, str] | None = None) -> Path:
    env_map = os.environ if env is None else env
    data_home = (env_map.get("MINDIE_DATA_HOME") or "").strip()
    if data_home:
        root = Path(data_home).expanduser()
    else:
        root = Path.home() / ".local" / "share" / "mindie"
    return (root / "profiler" / "cann9_shim").resolve()


def shim_source_path() -> Path:
    path = Path(__file__).resolve().with_name(SHIM_SOURCE_FILENAME)
    if not path.is_file():
        raise ProfilerError(f"missing native capture C source: {path}")
    return path


def compute_shim_cache_key(install: Cann9Installation, source_bytes: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(SHIM_ABI_VERSION.encode("utf-8"))
    digest.update(b"\0")
    digest.update(install.version.encode("utf-8"))
    digest.update(b"\0")
    digest.update(install.innerversion.encode("utf-8"))
    digest.update(b"\0")
    digest.update(install.arch.encode("utf-8"))
    digest.update(b"\0")
    digest.update(source_bytes)
    return digest.hexdigest()[:20]


def ensure_capture_shim_binary(
    install: Cann9Installation,
    *,
    gear: str = "fast",
    cache_root: str | os.PathLike[str] | None = None,
    compiler: str = "gcc",
    timeout_s: float = 45.0,
) -> Path:
    """Compile and atomically cache ``libmindie_cann9_capture.so`` for ``install``."""

    if timeout_s <= 0:
        raise ProfilerUsageError(f"compiler timeout_s must be > 0, got {timeout_s}")
    gear_tag = (
        "fast"
        if (gear or "fast").strip().lower() in {"fast", "gear1", "mspti"}
        else "deep"
    )
    src_path = shim_source_path()
    hdr_path = src_path.with_name(SHIM_HEADER_FILENAME)
    if not hdr_path.is_file():
        raise ProfilerError(f"missing native capture C header: {hdr_path}")
    source_bytes = (
        gear_tag.encode("utf-8")
        + b"\0"
        + src_path.read_bytes()
        + b"\0"
        + hdr_path.read_bytes()
    )
    cache_key = compute_shim_cache_key(install, source_bytes)
    target_dir = (
        Path(cache_root).expanduser().resolve()
        if cache_root is not None
        else default_shim_cache_dir()
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_ver = re.sub(r"[^0-9A-Za-z._-]+", "_", install.version)
    so_path = (
        target_dir
        / f"libmindie_cann9_capture_{gear_tag}_{safe_ver}_{install.arch}_{cache_key}.so"
    )
    if so_path.is_file() and so_path.stat().st_size > 0:
        return so_path

    lock_path = target_dir / f".{so_path.name}.lock"
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if os.name != "nt":
            import fcntl

            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        if so_path.is_file() and so_path.stat().st_size > 0:
            return so_path

        acl_lib_dir = install.libascendcl_so.parent
        mspti_lib_dir = install.libmspti_so.parent
        rpath = (
            f"{mspti_lib_dir}:{acl_lib_dir}"
            if gear_tag == "fast"
            else str(acl_lib_dir)
        )
        tmp_so = target_dir / f".{so_path.name}.tmp.{os.getpid()}"
        cmd = [
            compiler,
            "-shared",
            "-fPIC",
            "-O2",
            "-std=gnu11",
            "-pthread",
            "-Wall",
            "-Wextra",
            "-Wno-unused-parameter",
            f"-I{src_path.parent}",
            "-isystem",
            str(install.mspti_include_dir),
            "-isystem",
            str(install.acl_include_dir),
            str(src_path),
            "-o",
            str(tmp_so),
            f"-L{acl_lib_dir}",
        ]
        cmd.append("-Wl,--no-as-needed")
        if gear_tag == "fast":
            cmd.extend([f"-L{mspti_lib_dir}", "-lmspti"])
        cmd.extend(
            [
                "-lascendcl",
                "-Wl,--as-needed",
                f"-Wl,-rpath,{rpath}",
                "-ldl",
                "-lpthread",
                "-lm",
            ]
        )
        popen_kwargs: dict[str, object] = {}
        if os.name == "nt":
            popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
                **popen_kwargs,
            )
        except TimeoutError:
            if tmp_so.exists():
                tmp_so.unlink(missing_ok=True)
            raise
        except OSError as exc:
            if tmp_so.exists():
                tmp_so.unlink(missing_ok=True)
            raise ProfilerError(
                f"failed to invoke C compiler {compiler!r} for CANN 9.x shim: {exc}"
            ) from exc

        if proc.returncode != 0 or not tmp_so.is_file():
            tmp_so.unlink(missing_ok=True)
            stderr = (proc.stderr or proc.stdout or "").strip()
            raise ProfilerError(
                f"failed to compile CANN 9.x capture shim (rc={proc.returncode}): {stderr[:800]}"
            )
        os.replace(tmp_so, so_path)
        return so_path
    finally:
        if os.name != "nt":
            try:
                import fcntl

                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(lock_fd)
