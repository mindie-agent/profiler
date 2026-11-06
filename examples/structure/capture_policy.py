"""Import retained literal graph and caller conditions into replay declarations.

[Role] Read compilation and additional config from caller-selected cmd.sh.
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


def _literal_config(tokens, option):
    values = []
    error_prefix = "capture_" + option.removeprefix("--").replace("-", "_")
    for index, token in enumerate(tokens):
        if token == option:
            if index + 1 >= len(tokens):
                raise ValueError(error_prefix + "_missing_value")
            values.append(tokens[index + 1])
        elif token.startswith(option + "="):
            values.append(token.split("=", 1)[1])
    if not values:
        return None
    if len(values) != 1:
        raise ValueError(error_prefix + "_ambiguous_multiple_declarations")
    try:
        config = json.loads(values[0])
    except json.JSONDecodeError as error:
        raise ValueError(error_prefix + "_requires_literal_json") from error
    if not isinstance(config, dict):
        raise ValueError(error_prefix + "_requires_object")
    return config


def import_capture_policy(raw: dict, *, capture_path: str | Path) -> tuple[dict, dict]:
    """Apply literal graph fields and retain caller conditions without guessing."""
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
    config = _literal_config(tokens, "--compilation-config")
    additional = _literal_config(tokens, "--additional-config")
    if config is None and additional is None:
        return result, {**provenance, "reason": "compilation_config_not_declared"}
    fields = {name: config[name] for name in ("cudagraph_mode", "cudagraph_capture_sizes")
              if config is not None and name in config}
    if not fields and additional is None:
        return result, {**provenance, "reason": "graph_policy_fields_not_declared"}
    provenance["provided_fields"] = sorted([*fields, *(["additional_config"] if additional is not None else [])])
    provenance["captured_fields"] = deepcopy(fields)
    if additional is not None:
        provenance["captured_fields"]["additional_config"] = deepcopy(additional)
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
    if additional is not None:
        runtime.setdefault("metadata", {})["captured_additional_config"] = deepcopy(additional)
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
