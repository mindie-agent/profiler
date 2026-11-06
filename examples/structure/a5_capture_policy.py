"""Import a retained capture's literal graph policy into its replay declaration.

[Role] Read compilation fields from the caller-selected capture cmd.sh.
[Invariants] Command text is never executed; model names and timings never
  select a capture policy. Missing fields remain explicitly unprovided.
[Timeouts & Locks] One small local command file; no subprocesses or locks.
[Side-Effect Policy] Return copied input and source provenance; no file writes.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shlex


def import_a5_capture_policy(raw: dict, *, capture_path: str | Path) -> tuple[dict, dict]:
    """Apply only literal compilation fields present in the selected source."""
    source = Path(capture_path)
    command = source if source.name == "cmd.sh" else (
        source / "cmd.sh" if source.is_dir() else source.parent / "cmd.sh")
    result = deepcopy(raw)
    provenance = {"schema_version": "mindie-profiler-capture-policy-import/1",
                  "status": "not_provided", "capture_path": str(source),
                  "command_path": str(command), "command_executed": False,
                  "timing_values_used": False, "provided_fields": [], "changed_fields": []}
    try:
        data = command.read_bytes()
    except FileNotFoundError:
        return result, {**provenance, "reason": "capture_command_not_present"}
    provenance["command_sha256"] = sha256(data).hexdigest()
    tokens = shlex.split(data.decode("utf-8"), comments=True, posix=True)
    values = []
    for index, token in enumerate(tokens):
        if token == "--compilation-config":
            if index + 1 >= len(tokens):
                raise ValueError("capture_compilation_config_missing_value")
            values.append(tokens[index + 1])
        elif token.startswith("--compilation-config="):
            values.append(token.split("=", 1)[1])
    if not values:
        return result, {**provenance, "reason": "compilation_config_not_declared"}
    if len(values) != 1:
        raise ValueError("capture_compilation_config_ambiguous_multiple_declarations")
    try:
        config = json.loads(values[0])
    except json.JSONDecodeError as error:
        raise ValueError("capture_compilation_config_requires_literal_json") from error
    if not isinstance(config, dict):
        raise ValueError("capture_compilation_config_requires_object")
    fields = {name: config[name] for name in ("cudagraph_mode", "cudagraph_capture_sizes") if name in config}
    if not fields:
        return result, {**provenance, "reason": "graph_policy_fields_not_declared"}
    provenance["provided_fields"] = sorted(fields)
    provenance["captured_fields"] = deepcopy(fields)
    provenance["missing_fields"] = sorted({"cudagraph_mode", "cudagraph_capture_sizes"} - fields.keys())
    mode = fields.get("cudagraph_mode")
    if mode is not None and mode not in {"NONE", "FULL_DECODE_ONLY"}:
        return result, {**provenance, "status": "unsupported", "reason": "capture_mode_not_represented"}
    sizes = fields.get("cudagraph_capture_sizes")
    if sizes is not None and (not isinstance(sizes, list) or
            any(type(size) is not int or size <= 0 for size in sizes) or len(set(sizes)) != len(sizes)):
        raise ValueError("capture_graph_sizes_require_unique_positive_integers")
    runtime = result.setdefault("runtime", {})
    before = deepcopy(runtime)
    if mode is not None:
        runtime["graph_mode"] = "none" if mode == "NONE" else "auto"
        runtime["graph_capture_mode"] = "none" if mode == "NONE" else "full"
        runtime.setdefault("metadata", {})["captured_execution_mode"] = mode
        if mode == "NONE":
            runtime["graph_capture_keys"] = []
            runtime["graph_buckets"] = []
        runtime["piecewise_capture_keys"] = []
    if sizes is not None:
        sizes = sorted(sizes)
        runtime.setdefault("metadata", {})["cudagraph_capture_sizes"] = sizes
        selected = runtime.get("graph_capture_mode", "full")
        if selected == "full":
            runtime["graph_capture_keys"] = sizes
            runtime["graph_buckets"] = sizes
        if selected == "piecewise":
            runtime["piecewise_capture_keys"] = sizes
    provenance["changed_fields"] = sorted(key for key in runtime if before.get(key) != runtime[key])
    provenance.update(status="applied" if not provenance["missing_fields"] else "partially_provided",
                      reason="literal_captured_compilation_fields_imported")
    return result, provenance
