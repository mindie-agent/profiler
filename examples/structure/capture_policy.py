"""Import retained literal graph and caller conditions into replay declarations.

[Role] Read compilation and additional config from caller-selected cmd.sh.
[Invariants] Command text is never executed; model names and timings never
  select a capture policy. Missing graph fields remain explicitly unprovided.
  A selected MC2 caller aligns locally without changing the full-graph rows.
[Timeouts & Locks] One small local command file; no subprocesses or locks.
[Side-Effect Policy] Return copied input and source provenance; no file writes.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shlex


MC2_ALIGNMENT_SOURCE = {
    "repository": "vllm-ascend",
    "revision": "8c30e4f491f73cba737a1dacc522894e437cdf3d",
    "forward_context": {
        "repository_path": "vllm_ascend/ascend_forward_context.py", "lines": [216, 226],
        "sha256": "ab5110b44b2b951f0f55d09fcc90c316f6515bb8d085a5fdd0ac1b1b1dcd099e",
    },
    "prepare_finalize": {
        "repository_path": "vllm_ascend/ops/fused_moe/prepare_finalize.py", "lines": [291, 325],
        "sha256": "41dc995d6a8b2ec714733eb229803ad45e6ed0f09d40a531bd764ac794f2b902",
    },
    "formula": "ceil(max_tokens_across_dp / tp_world_size) * tp_world_size",
    "scope": "MC2 prepare padding and TP slicing; finalize trims to original rows",
    "capture_binary_identity": "unknown",
}


def _complete_mc2_alignment(runtime):
    caller = runtime.get("kernels", {}).get("moe_token_partition")
    if (not isinstance(caller, dict) or caller.get("kind") != "vllm_ascend_mc2_tp_slice"
            or "padding" in caller):
        return None
    # MC2 pads after the full-row router, then slices across TP. Captured graph
    # keys govern attention/shared rows and must not absorb this local padding.
    caller["padding"] = "right_to_tp"
    return {"field": "runtime.kernels.moe_token_partition.padding",
            "value": "right_to_tp", "basis": "already_selected_mc2_caller_source_semantics",
            "source": deepcopy(MC2_ALIGNMENT_SOURCE)}


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
    if fields:
        alignment = _complete_mc2_alignment(runtime)
        if alignment is not None:
            provenance["source_conditions"] = [alignment]
    provenance["changed_fields"] = sorted(key for key in runtime if before.get(key) != runtime[key])
    provenance.update(status="applied" if not provenance["missing_fields"] else "partially_provided",
                      reason="literal_captured_compilation_fields_imported")
    return result, provenance
