"""Content identity for the simulator used by offline evaluation caches.

[Role] Fingerprint installed simulator source and runtime data at evaluator startup.
[Invariants] Relative paths and file contents determine identity, independently of
  checkout location, traversal order, timestamps and Python bytecode caches.
[Timeouts & Locks] One package traversal; files stream in bounded 1 MiB chunks.
[Side-Effect Policy] Read-only package access; no device, network or capture reads.
"""
from hashlib import sha256
from pathlib import Path


def simulator_identity(module) -> str:
    """Hash every runtime Python/JSON file, including catalogs and device profiles.

    Evaluators retain this value for the process lifetime. Recompute only when
    starting a new evaluation; prediction workers must not hash on every case.
    """
    root = Path(module.__file__).resolve().parent
    version = getattr(module, "__version__", "unversioned")
    digest = sha256(b"mindie-sim-runtime-tree/1\0")
    digest.update(str(version).encode("utf-8") + b"\0")
    paths = sorted(
        (path for path in root.rglob("*")
         if path.is_file() and path.suffix in {".py", ".json"}
         and "__pycache__" not in path.relative_to(root).parts),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        content = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                content.update(chunk)
        digest.update(content.digest())
    return f"mindie_sim/{version}:{digest.hexdigest()}"
