"""Generate one runnable single-op reproducer from a complete slot binding.

[Role]
  Gate on a complete binding, build exact allocations and a call plan (including
  optional ``None`` positions, tensor-list packing, output buffers and mutable
  aliases), synthesize metadata for the *allocated* tensor shapes, emit
  ``repro.py`` plus a provenance ``manifest.json`` and expose the CLI/MCP
  receipt.

[Invariants]
  * ``ready`` is emitted only for ``status="bound"`` bindings with a complete
    identity and exact slot conservation.  Missing required scalars/tensors or
    unverified signatures block emission.
  * Every metadata value is installed into a tensor with the exact allocated
    shape and numel; a mismatch is a hard error in the script, never a silent
    no-op.
  * Optional positional arguments keep their semantic positions as ``None``.
  * Stateful inputs are cloned from a pristine template outside the timed
    region each iteration; mutable in-place outputs alias their inputs.
  * Fidelity is labelled ``value_captured`` only when every input tensor has a
    captured value; partial/metadata-only captures use explicit narrower
    labels.  The manifest carries source/catalog/native digests.

[Timeouts & Locks]
  Pure in-memory generation.  The emitted script bounds each ``npu-smi`` call
  to 2 s and owns its warmup/iteration budget.

[Side-Effect Policy]
  Writes only the requested ``repro.py``/``manifest.json`` (or ``--output``);
  no hardware access at generation time.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .events import ProfilerUsageError
from .repro_values import _INT_RANGES, bounded_container_len, bounded_mapping, _bounded_members, _container_nodes, _copy_container
from .repro_values import bounded_count, bounded_sequence, bounded_shape, repro_count_options, validate_binding_counts, validate_count_attributes, validate_json_integers, bounded_summary, load_cli_json, validate_container_depth, binding_issues
from .repro_metadata import validate_metadata_counts
from .op_abi_binding import BINDING_SCHEMA, operator_name
from .op_abi_attributes import attr_issue as _attr_issue, validate_binding_attributes

REPRO_SCHEMA = "mindie-single-op-repro/2"
MANIFEST_SCHEMA = "mindie-single-op-repro-manifest/1"
_DTYPE_MAP = {
    "bf16": "bfloat16", "fp16": "float16", "fp32": "float32", "fp64": "float64",
    "int8": "int8", "int32": "int32", "int64": "int64", "uint8": "uint8",
    "bool": "bool", "fp8_e4m3": "float8_e4m3fn", "fp8_e5m2": "float8_e5m2",
    "fp8_e8m0": "uint8",
}
_DTYPE_ALIASES = {
    "bfloat16": "bf16", "float16": "fp16", "float32": "fp32",
    "float64": "fp64", "float8_e4m3fn": "fp8_e4m3",
    "float8_e5m2": "fp8_e5m2",
}

def _torch_dtype(dtype: Any) -> str | None:
    """Concrete ``torch.<dtype>`` attribute, or None when unallocatable."""
    name = str(dtype or "").lower().strip()
    if name.startswith("dt_"):
        name = name[3:]
    name = _DTYPE_ALIASES.get(name, name)
    return _DTYPE_MAP.get(name)

def _binding_dtype_slots(binding: dict[str, Any]) -> list[dict[str, Any]]:
    """Every present tensor item with the dtype it would allocate."""
    slots = []
    for field in ("inputs", "outputs"):
        for record in binding.get(field) or ():
            items = (record.get("items") if record.get("cat") == "tensor_list"
                     else [record])
            for item in items or ():
                if item.get("present") and item.get("dtype") is not None:
                    slots.append({"name": record.get("name"),
                                  "dtype": item.get("dtype")})
    return slots

_BLOCKING = {"descriptor_incomplete", "descriptor_invalid", "dtype_unknown",
             "dtype_not_declared", "layout_not_declared", "abi_signature_unpinned",
             "capture_abi_id_mismatch", "required_attrs_absent", "padding_invalid",
             "unexpected_input_slots", "unexpected_output_slots", "span_deficit",
             "surplus_slots", "tensor_list_item_invalid", "tensor_list_lengths_invalid",
             "required_slot_null", "required_slot_omitted",
             "undefined_policy_unspecified", "undefined_not_nullable",
             "invalid_attribute_type", "invalid_attribute_range",
             "invalid_attribute_value", "invalid_array_length",
             "invalid_array_range", "invalid_array_order",
             "descriptor_not_a_mapping",
             "descriptor_column_mismatch", "missing_descriptor_field"}

from .repro_preconditions import precondition_problems

from .repro_values import (
    fidelity as _fidelity, jsonable as _jsonable,
    slot_allocations as _slot_allocations, storage_record as _storage_record, storage_mapping, literal_value,
)

from .repro_metadata import (
    _ceil_div, _cumulative, _diffs, _flatten_values, _metadata_fidelity,
    _monotonic, _spread, synthesize_metadata,
)
from .repro_storage import resolve_repro_artifact, stage_artifacts

def _required_attrs(binding: dict[str, Any], recipe: dict[str, Any]) -> list[str]:
    present = {record["name"] for record in binding.get("attr_slots") or ()
               if record.get("present")}
    known = {spec["attr"] for spec in (recipe.get("keyword") or {}).values()
             if isinstance(spec, dict) and spec.get("attr")}
    required_attrs = {spec["attr"] for spec in (recipe.get("keyword") or {}).values()
                      if isinstance(spec, dict) and spec.get("attr")
                      and not spec.get("optional")}
    required = [attr for attr in required_attrs if attr not in present]
    for record in binding.get("attr_slots") or ():
        if (record.get("required") and not record.get("present")
                and (not known or record["name"] in required_attrs)):
            required.append(record["name"])
    return sorted(set(required))

_TENSOR_PLAN_KINDS = {"tensor", "output", "meta"}
_SCALAR_ARGUMENT_KINDS = {"int", "float", "str", "bool", "boolean",
                          "int_array", "float_array", "array"}

def _argument_issue(name: str, declared_kind: str | None,
                    spec: dict[str, Any], value: Any) -> dict[str, Any] | None:
    """Validate one generated call argument against the callable schema kind."""
    if not declared_kind:
        return None
    if declared_kind == "tensor":
        if spec.get("kind") not in _TENSOR_PLAN_KINDS:
            return {"code": "argument_kind_mismatch", "name": name,
                    "declared": declared_kind, "generated": spec.get("kind")}
        return None
    if declared_kind == "tensor_list":
        if spec.get("kind") != "tensor_list":
            return {"code": "argument_kind_mismatch", "name": name,
                    "declared": declared_kind, "generated": spec.get("kind")}
        return None
    if declared_kind not in _SCALAR_ARGUMENT_KINDS:
        return {"code": "unknown_argument_kind", "name": name,
                "declared": declared_kind}
    if spec.get("kind") not in {"attr", "array", "const"}:
        return {"code": "argument_kind_mismatch", "name": name,
                "declared": declared_kind, "generated": spec.get("kind")}
    issue, _normalized = _attr_issue(name, declared_kind, value)
    return issue

def _call_plan(binding: dict[str, Any], recipe: dict[str, Any]
               ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_name = binding.get("by_name") or {}
    attrs = binding.get("attrs") or {}
    signature = recipe.get("signature") or {}
    params = signature.get("params") or {}
    problems: list[dict[str, Any]] = []
    if not signature.get("verified"):
        problems.append({"code": "callable_signature_unverified",
                         "call": recipe.get("call")})
    positional = []
    positional_names: list[str] = []
    for name in recipe.get("positional") or ():
        record = by_name.get(name)
        declared_kind = (params.get(name) or {}).get("kind")
        if record is not None and (record.get("present") or record.get("optional")):
            if record.get("cat") == "tensor_list":
                if declared_kind == "tensor_list":
                    spec = {"kind": "tensor_list", "name": name}
                    positional.append(spec)
                elif len(record.get("items") or ()) == 1:
                    spec = {"kind": "tensor", "name": name,
                            "list_index": 0}
                    positional.append(spec)
                else:
                    problems.append({"code": "tensor_argument_is_list", "name": name,
                                     "items": len(record.get("items") or ())})
                    spec = {}
            else:
                spec = {"kind": "output"
                        if record.get("direction") == "output"
                        else "tensor", "name": name}
                positional.append(spec)
            issue = _argument_issue(name, declared_kind, spec, None)
            if issue is not None:
                problems.append(issue)
        elif name in attrs:
            spec = {"kind": "attr", "name": name}
            positional.append(spec)
            issue = _argument_issue(name, declared_kind, spec, attrs.get(name))
            if issue is not None:
                problems.append(issue)
        else:
            problems.append({"code": "required_positional_absent", "name": name})
        positional_names.append(name)
    keyword = {}
    for name, spec in (recipe.get("keyword") or {}).items():
        if name not in params:
            problems.append({"code": "unknown_callable_keyword", "name": name,
                             "declared": sorted(params)})
            continue
        if not isinstance(spec, dict):
            spec = {"const": spec}
        if "const" in spec:
            keyword[name] = {"kind": "const", "value": spec["const"]}
        elif "attr" in spec or "array" in spec:
            attr_name = spec.get("attr") or spec.get("array")
            value = attrs.get(attr_name)
            optional = bool(spec.get("optional"))
            if value is None and not optional:
                problems.append({"code": "required_attr_absent", "name": attr_name})
            enum_map = spec.get("enum_map")
            if enum_map is not None and value is not None:
                key = str(value).strip()
                if key in enum_map:
                    value = enum_map[key]
                elif str(value) in enum_map.values():
                    value = str(value)
                else:
                    problems.append({"code": "unknown_enum_value", "name": name,
                                     "value": value, "declared": sorted(enum_map)})
            keyword[name] = {"kind": "array" if "array" in spec else "attr",
                             "name": attr_name, "value": value,
                             "optional": optional}
            if enum_map is not None:
                keyword[name]["capture_kind"] = next((item.get("kind") for item in
                    binding.get("attr_slots") or () if item.get("name") == attr_name), None)
        elif "list" in spec:
            record = by_name.get(spec["list"])
            if record is None or record.get("cat") != "tensor_list":
                problems.append({"code": "required_tensor_list_absent",
                                 "name": spec["list"]})
            keyword[name] = {"kind": "tensor_list", "name": spec["list"],
                             "optional": bool(spec.get("optional"))}
        elif "output" in spec:
            if by_name.get(spec["output"]) is None:
                problems.append({"code": "required_output_absent",
                                 "name": spec["output"]})
            keyword[name] = {"kind": "output", "name": spec["output"]}
        elif "meta" in spec:
            keyword[name] = {"kind": "meta", "name": spec["meta"]}
        elif "input" in spec:
            record = by_name.get(spec["input"])
            optional = bool(spec.get("optional"))
            if record is None and not optional:
                problems.append({"code": "required_input_absent",
                                 "name": spec["input"]})
            if record is not None and record.get("cat") == "tensor_list":
                if len(record.get("items") or ()) == 1:
                    keyword[name] = {"kind": "tensor", "name": spec["input"],
                                     "list_index": 0, "optional": optional}
                else:
                    problems.append({"code": "tensor_argument_is_list",
                                     "name": spec["input"],
                                     "items": len(record.get("items") or ())})
            else:
                keyword[name] = {"kind": "tensor", "name": spec["input"],
                                 "optional": optional}
        else:
            problems.append({"code": "unknown_recipe_reference", "name": name})
        generated = keyword.get(name)
        if generated is not None:
            declared_kind = (params.get(name) or {}).get("kind")
            if "value" in generated:
                value = generated.get("value")
            else:
                value = attrs.get(generated.get("name")) if generated.get(
                    "kind") in {"attr", "array"} else None
            if not (value is None and generated.get("optional")
                    and declared_kind not in {"tensor", "tensor_list"}):
                issue = _argument_issue(name, declared_kind, generated, value)
                if issue is not None:
                    problems.append(issue)
    supplied = set(positional_names) | set(keyword)
    for name, spec in params.items():
        if spec.get("required") and name not in supplied:
            problems.append({"code": "required_signature_argument_absent",
                             "name": name})
    plan = {"call": recipe.get("call"), "positional": positional,
            "positional_names": positional_names, "keyword": keyword,
            "tensor_lists": dict(recipe.get("tensor_lists") or {}),
            "outputs": list(recipe.get("output_buffers") or ()),
            "mutable_aliases": list(recipe.get("mutable_aliases") or ()),
            "returns": recipe.get("returns"),
            "return_indices": recipe.get("return_indices"),
            "signature_verified": bool(signature.get("verified"))}
    return plan, problems

def _compact_occurrence(binding: dict[str, Any]) -> dict[str, Any]:
    binding = bounded_mapping(binding, "binding")
    if not isinstance(binding, dict) or binding.get("schema") != BINDING_SCHEMA:
        raise ProfilerUsageError("repro-op requires a mindie-op-occurrence-binding/2")
    issues = binding_issues(binding)
    validate_binding_counts(binding)
    validate_binding_attributes(binding)
    if binding.get("status") != "bound" or binding.get("slot_status", "bound") != "bound":
        raise ProfilerUsageError(
            f"repro-op blocks status {bounded_summary(binding.get('status'))}: "
            f"{bounded_summary([i.get('code') if isinstance(i, dict) else i for i in issues[:8]])}")
    identity = binding.get("identity") or {}
    if (not identity.get("catalog_abi_id") or not identity.get("native_abi_sha256")
            or not identity.get("call_abi_sha256")):
        raise ProfilerUsageError("repro-op requires a complete ABI identity")
    blocking = [issue for issue in issues
                if not isinstance(issue, dict) or not isinstance(issue.get("code"), str) or issue.get("code") in _BLOCKING]
    if blocking:
        raise ProfilerUsageError(f"repro-op blocks incomplete binding: {bounded_summary(blocking)}")
    if not (binding.get("conservation") or {}).get("exact"):
        raise ProfilerUsageError("repro-op blocks non-conserved slot binding")
    dtype_slots = _binding_dtype_slots(binding)
    dtype_problems = [
        {"code": "allocatable_torch_dtype", "tensor": slot.get("name"),
         "dtype": slot.get("dtype"),
         "detail": "no concrete allocatable torch dtype / packed lowering"}
        for slot in dtype_slots if _torch_dtype(slot.get("dtype")) is None]
    unallocatable = {item["tensor"] for item in dtype_problems}
    allocations, problems = _slot_allocations(binding)
    if problems:
        deferred = all(problem.get("name") in unallocatable
                       and str(problem.get("code", "")).startswith(
                           "captured_value_")
                       for problem in problems)
        if not deferred:
            raise ProfilerUsageError(f"repro-op allocation problems: {bounded_summary(problems)}")
    if not allocations:
        raise ProfilerUsageError("repro-op found no active tensor slots")
    recipe = dict(binding.get("repro") or {})
    if (not recipe.get("supported") or binding.get("repro_status") != "ready"
            or not binding.get("repro_supported")):
        reason = (recipe.get("unsupported_reason")
                  or binding.get("repro_block_reason"))
        raise ProfilerUsageError(f"repro-op blocked recipe: {bounded_summary(reason)}")
    plan, plan_problems = _call_plan(binding, recipe)
    if plan_problems:
        raise ProfilerUsageError(f"repro-op call plan incomplete: {bounded_summary(plan_problems)}")
    padding = dict(binding.get("padding") or {})
    attrs = {name: value for name, value in (binding.get("attrs") or {}).items()
             if _jsonable(value) is not None}
    attrs.setdefault("effective_tokens", padding.get("effective_tokens"))
    attrs.setdefault("bucket_tokens", padding.get("bucket_tokens"))
    validate_metadata_counts({"allocations": allocations, "attrs": attrs, "padding": padding})
    validate_json_integers(binding)
    binding = literal_value(binding)
    occurrence = {
        "schema": "mindie-single-op-repro-occurrence/1",
        "api": binding.get("canonical") or binding.get("operator"),
        "operator": binding.get("operator"), "pipe": binding.get("pipe"),
        "cann_version": binding.get("cann_version"), "padding": padding,
        "attrs": attrs, "allocations": allocations, "call_plan": plan,
        "signature": recipe.get("signature"),
        "preconditions": recipe.get("preconditions"),
        "required_attrs": _required_attrs(binding, recipe),
        "fidelity": _fidelity(allocations),
        "provenance": {
            "catalog_abi_id": identity.get("catalog_abi_id"),
            "native_abi_sha256": identity.get("native_abi_sha256"),
            "capture_shape_abi_sha256": identity.get("capture_shape_abi_sha256"),
            "call_abi_sha256": identity.get("call_abi_sha256"),
            "source_sha256": identity.get("source_sha256"),
            "binding_sha256": "sha256:" + hashlib.sha256(json.dumps(
                binding, sort_keys=True, separators=(",", ":"),
                allow_nan=False).encode("utf-8")).hexdigest(),
        },
    }
    problems = precondition_problems(occurrence)
    occurrence["precondition_problems"] = problems + dtype_problems
    if any(problem.get("rule") != "metadata" for problem in problems):
        raise ProfilerUsageError(
            "repro-op precondition failed: "
            + bounded_summary(problems))
    occurrence["fractal_nz_count"] = sum(
        1 for spec in allocations if spec["layout"] == "FRACTAL_NZ")
    occurrence["metadata"] = synthesize_metadata(occurrence)
    occurrence["checks"] = occurrence["metadata"]["checks"]
    occurrence["checks"]["preconditions_passed"] = not problems
    occurrence["checks"]["allocatable_torch_dtype"] = not dtype_problems
    failed = sorted(name for name, value in occurrence["checks"].items()
                    if value is False)
    occurrence["status"] = "ready" if not failed else "blocked"
    occurrence["block_reason"] = None if not failed else {
        "code": "prelaunch_checks_failed", "failed_checks": failed}
    occurrence["fidelity"] = (occurrence["metadata"]["fidelity"]
                              if not dtype_problems else "unsupported_dtype")
    return occurrence

from .repro_script_template import SCRIPT_TEMPLATE as _SCRIPT_TEMPLATE  # noqa: E402

from .op_abi_padding import (  # noqa: E402 - injected into the script
    _num, synthesize_group_list, validate_group_list,
)

_HELPERS = (_ceil_div, _spread, _monotonic, _diffs, _cumulative, _flatten_values,
            bounded_container_len, bounded_mapping, _bounded_members, _container_nodes, _copy_container,
            _metadata_fidelity, _num, synthesize_group_list, validate_group_list,
            bounded_count, bounded_sequence, bounded_shape, repro_count_options, validate_count_attributes,
            bounded_summary, validate_container_depth, validate_json_integers, literal_value, storage_mapping,
            validate_metadata_counts, synthesize_metadata)

def _render(occurrence: dict[str, Any], *, warmup: int, iters: int, flush_mb: int,
            max_cv_pct: float, l2_bytes: int | None, seed: int = 0) -> str:
    seed_i = bounded_count(seed, "seed", 0, _INT_RANGES["int64"][1])
    source = "\n\n".join(inspect.getsource(function) for function in _HELPERS)
    import pprint
    replacements = {
        "__OCCURRENCE__": pprint.pformat(literal_value(occurrence), sort_dicts=True, width=100),
        "__SYNTH_SOURCE__": source, "__DTYPE_MAP__": repr(_DTYPE_MAP),
        "__WARMUP__": str(int(warmup)), "__ITERS__": str(int(iters)),
        "__FLUSH_MB__": str(int(flush_mb)), "__MAX_CV_PCT__": repr(float(max_cv_pct)),
        "__L2_BYTES__": "None" if l2_bytes is None else str(int(l2_bytes)),
    }
    replacements["__SEED__"] = str(int(seed_i))
    return re.sub("|".join(replacements), lambda match: replacements[match[0]], _SCRIPT_TEMPLATE)

def generate_single_op_reproducer(
    bound_occurrence: dict[str, Any], *, output_path: str | Path | None = None,
    output_dir: str | Path | None = None, warmup: int = 10, iters: int = 50,
    flush_mb: int = 256, max_cv_pct: float = 5.0, l2_bytes: int | None = None,
    seed: int = 0, cann_version: str | None = None, stage: bool = False,
) -> dict[str, Any]:
    """Emit a syntax-checked, metadata-verified reproducer for one binding."""
    repro_count_options(warmup, iters, flush_mb, l2_bytes)
    seed_i = bounded_count(seed, "seed", 0, _INT_RANGES["int64"][1])
    if cann_version is not None:
        if not isinstance(cann_version, str) or not cann_version.strip():
            raise ProfilerUsageError("repro-op requires non-empty cann_version string")
        cann_version = cann_version.strip()
    try:
        max_cv_pct = float(max_cv_pct)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ProfilerUsageError("repro-op requires finite max_cv_pct") from exc
    if not 0 < max_cv_pct <= 100:
        raise ProfilerUsageError("repro-op requires 0 < max_cv_pct <= 100")
    if (isinstance(bound_occurrence, Mapping) and bound_occurrence.get("schema") != BINDING_SCHEMA
            and any(k in bound_occurrence for k in ("op_type", "operator", "name", "kind", "input_shapes", "output_shapes"))):
        from .op_api_registry import bind_captured_occurrence
        eff_ver = cann_version or str(bound_occurrence.get("cann_version") or bound_occurrence.get("cann_release") or "").strip() or None
        bound_occurrence = bind_captured_occurrence(bound_occurrence, cann_version=eff_ver)
    occurrence = _compact_occurrence(bound_occurrence)
    if cann_version and occurrence.get("cann_version") and occurrence["cann_version"] != cann_version:
        raise ProfilerUsageError(f"cann_version mismatch: {occurrence['cann_version']} != {cann_version}")
    failed = {name: value for name, value in occurrence["checks"].items() if value is False}
    if failed:
        raise ProfilerUsageError(f"repro-op prelaunch checks failed: {failed}")
    script = _render(occurrence, warmup=warmup, iters=iters, flush_mb=flush_mb,
                     max_cv_pct=max_cv_pct, l2_bytes=l2_bytes, seed=seed_i)
    try:
        compile(script, "<repro>", "exec")
    except SyntaxError as exc:
        raise ProfilerUsageError(f"generated reproducer failed syntax validation: {exc}") from exc
    digest = hashlib.sha256(script.encode("utf-8")).hexdigest()
    limitations = []
    if any(spec["layout"] == "FRACTAL_NZ" for spec in occurrence["allocations"]):
        limitations.append("FRACTAL_NZ is requested with npu_format_cast(29); the physical NZ storage layout is not byte-verified against the capture.")
    if any(spec["dtype"] == "fp8_e8m0" for spec in occurrence["allocations"]):
        limitations.append("FP8 E8M0 is stored in a uint8 container; the packing contract is declared, not verified.")
    if any((spec.get("storage") or {}).get("storage_offset") for spec in occurrence["allocations"]):
        limitations.append("A captured storage_offset cannot be reproduced on a fresh allocation; the tensor is contiguous at offset zero.")
    if not any((spec.get("storage") or {}).get("strides") or (spec.get("storage") or {}).get("stride") for spec in occurrence["allocations"]):
        limitations.append("No captured strides were supplied; allocations are contiguous.")
    manifest = {
        "schema": MANIFEST_SCHEMA, "api": occurrence["api"],
        "operator": occurrence["operator"], "cann_version": occurrence["cann_version"],
        "catalog_abi_id": occurrence["provenance"]["catalog_abi_id"],
        "native_abi_sha256": occurrence["provenance"]["native_abi_sha256"],
        "source_sha256": occurrence["provenance"]["source_sha256"],
        "binding_sha256": occurrence["provenance"]["binding_sha256"],
        "repro_sha256": f"sha256:{digest}",
        "script_sha256": f"sha256:{digest}",
        "line_count": len(script.splitlines()),
        "allocation_count": len(occurrence["allocations"]),
        "fractal_nz_count": occurrence["fractal_nz_count"],
        "fidelity": occurrence["fidelity"],
        "checks": occurrence["checks"], "metadata": occurrence["metadata"],
        "limitations": limitations,
        "initialization": {"policy": "deterministic_legal", "seed": seed_i,
                           "weights_and_gamma": "ones",
                           "activations_and_outputs": "zeros",
                           "stateful_inputs": "zeros_with_pristine_reset"},
        "gate": {"warmup": warmup, "iters": iters, "flush_mb": flush_mb,
                 "max_cv_pct": max_cv_pct, "l2_bytes": l2_bytes, "seed": seed_i},
    }
    storage = None
    if stage or output_dir is not None or output_path is not None:
        storage = stage_artifacts(script, manifest, output_dir=output_dir,
                                  output_path=output_path)
    storage_status = storage.get("status") if storage else None
    delivery_failed = storage_status in {"delivery_blocked", "delivery_failed"}
    return {
        "schema": REPRO_SCHEMA, "api": occurrence["api"],
        "status": storage_status if delivery_failed else "ready",
        "error": storage.get("error") if delivery_failed else None,
        "syntax_ok": True, "sha256": f"sha256:{digest}",
        "line_count": len(script.splitlines()), "metadata": occurrence["metadata"],
        "checks": occurrence["checks"], "fidelity": occurrence["fidelity"],
        "allocation_count": len(occurrence["allocations"]),
        "fractal_nz_count": occurrence["fractal_nz_count"],
        "output_path": storage["artifact_path"] if storage else None,
        "manifest_path": storage["manifest_path"] if storage else None,
        "artifact_id": storage["artifact_id"] if storage else None,
        "index_persisted": storage.get("index_persisted") if storage else None,
        "index_warning": storage.get("index_warning") if storage else None,
        "storage": storage,
        "manifest": manifest, "script": script,
    }

def extract_raw_rows(payload: Any) -> list[dict[str, Any]]:
    """Return raw rows in document order, retaining descriptor-less positions."""
    if isinstance(payload, (Mapping, list, tuple)):
        payload = bounded_mapping(payload) if isinstance(payload, Mapping) else bounded_sequence(payload, "capture")
    return _raw_rows_from_snapshot(payload)

def _raw_rows_from_snapshot(payload: Any) -> list[dict[str, Any]]:
    """Read a bounded capture snapshot without traversing caller mappings again."""
    if isinstance(payload, dict):
        for field in ("ops", "kernels", "occurrences", "operator_rows",
                      "operators", "rows"):
            value = payload.get(field)
            if isinstance(value, list):
                # Keep one slot per raw document position.  Non-dict rows become
                # empty placeholders so a raw index selected by diff-trace is
                # the exact same index here.
                return [dict(row) if isinstance(row, dict) else {}
                        for row in value]
    rows: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if any(key in node for key in ("input_shapes", "output_shapes")) and any(
                    key in node for key in ("op_type", "kind", "operator", "name")):
                rows.append(node)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(payload)
    return rows

def extract_capture_rows(payload: Any) -> list[dict[str, Any]]:
    """Descriptor-bearing rows in document order (backwards-compatible view)."""
    return [row for row in extract_raw_rows(payload)
            if "input_shapes" in row or "output_shapes" in row]

_SELECTOR = re.compile(r"[^a-z0-9]")

def _name_of(row: dict[str, Any]) -> str:
    return operator_name(row)

def _safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return 0

def _row_uid(run_id: str, row: dict[str, Any], raw_index: int) -> str:
    payload = [str(run_id), _safe_int(row.get("rank", row.get("device_id", 0))),
               _safe_int(row.get("step", row.get("step_id", 0))),
               _safe_int(row.get("stream", row.get("stream_id", 0))),
               int(raw_index),
               str(row.get("abi_sha256") or row.get("abi_digest")
                   or row.get("abi_id") or "")]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _row_from_args(args: argparse.Namespace) -> tuple[dict[str, Any], int | None, str | None]:
    from .op_api_registry import bind_captured_occurrence

    version = getattr(args, "version", None)
    if args.row:
        payload = bounded_mapping(load_cli_json(args.row), "row")
        validate_container_depth(payload)
        if isinstance(payload, dict) and payload.get("schema") == BINDING_SCHEMA:
            validate_binding_counts(payload)
            return payload, None, str(Path(args.row))
        if version is None and isinstance(payload, dict):
            version = str(payload.get("cann_version") or payload.get("cann_release") or "").strip() or None
        return (bind_captured_occurrence(payload, cann_version=version),
                None, str(Path(args.row)))
    payload = load_cli_json(args.capture)
    if isinstance(payload, Mapping):
        payload = bounded_mapping(payload, "capture")
    rows = _raw_rows_from_snapshot(payload) if isinstance(payload, dict) else extract_raw_rows(payload)
    if not rows:
        raise ProfilerUsageError("capture contains no occurrence rows")
    if version is None and isinstance(payload, dict):
        version = str(payload.get("cann_version") or payload.get("cann_release") or "").strip() or None
    run_id = str(payload.get("run_id") or payload.get("capture_id") or "run") \
        if isinstance(payload, dict) else "run"
    op_uid = getattr(args, "op_uid", None)
    index = args.occurrence_index if args.occurrence_index is not None else args.index
    if op_uid:
        matches = []
        for position, row in enumerate(rows):
            if row and op_uid in {row.get("op_uid"), _row_uid(run_id, row, position)}:
                matches.append(position)
        if index is not None:
            if not 0 <= index < len(rows):
                raise ProfilerUsageError(
                    f"--occurrence-index {index} out of range ({len(rows)})")
            if not rows[index]:
                raise ProfilerUsageError(
                    f"--occurrence-index {index} selects a non-object raw row")
            if index not in matches:
                raise ProfilerUsageError(
                    "selector_mismatch: --op-uid and --occurrence-index select "
                    f"different raw rows ({matches} != {index})")
            selected = rows[index]
        else:
            if not matches:
                raise ProfilerUsageError(f"--op-uid {op_uid} does not select any raw row")
            if len(matches) > 1:
                raise ProfilerUsageError(
                    f"ambiguous_op_uid: {len(matches)} raw rows match {op_uid!r}; "
                    "use --occurrence-index")
            index, selected = matches[0], rows[matches[0]]
        if args.op_name and _SELECTOR.sub("", args.op_name.lower()) != _SELECTOR.sub(
                "", _name_of(selected).lower()):
            raise ProfilerUsageError(
                f"occurrence {index} is {_name_of(selected)!r}, not {args.op_name!r}; "
                "occurrence indices are applied before name filtering")
    elif index is not None:
        if not 0 <= index < len(rows):
            raise ProfilerUsageError(f"--occurrence-index {index} out of range ({len(rows)})")
        selected = rows[index]
        if not selected:
            raise ProfilerUsageError(
                f"--occurrence-index {index} selects a non-object raw row")
        if args.op_name and _SELECTOR.sub("", args.op_name.lower()) != _SELECTOR.sub(
                "", _name_of(selected).lower()):
            raise ProfilerUsageError(
                f"occurrence {index} is {_name_of(selected)!r}, not {args.op_name!r}; "
                "occurrence indices are applied before name filtering")
    elif args.op_name:
        wanted = _SELECTOR.sub("", args.op_name.lower())
        matches = [(position, row) for position, row in enumerate(rows)
                   if row and _SELECTOR.sub("", _name_of(row).lower()) == wanted]
        if not matches:
            raise ProfilerUsageError(f"capture has no exact occurrence {args.op_name!r}")
        if len(matches) > 1:
            raise ProfilerUsageError(
                f"capture has {len(matches)} occurrences of {args.op_name!r}; " "use --occurrence-index")
        index, selected = matches[0]
    elif len(rows) == 1 and rows[0]:
        index, selected = 0, rows[0]
    else:
        raise ProfilerUsageError("capture has multiple rows; use --occurrence-index")
    return (bind_captured_occurrence(selected, cann_version=version), index, str(Path(args.capture)))

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mindie-profiler repro-op", description="Generate a standalone NPU single-operator reproducer script from a captured row.", allow_abbrev=False)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--row", help="bound occurrence JSON or one raw capture row")
    source.add_argument("--capture", help="capture.json / op_summary export")
    parser.add_argument("--op-name", default=None, help="exact operator API or kernel name filter")
    parser.add_argument("--occurrence-index", type=int, default=None, help="zero-based row index inside --capture")
    parser.add_argument("--op-uid", default=None, help="immutable (run,rank,step,stream,raw_index,abi) selector")
    parser.add_argument("--index", type=int, default=None, help="deprecated alias of --occurrence-index")
    parser.add_argument("--version", default=None, help="CANN release version override when absent from capture")
    parser.add_argument("--output", "-o", default=None, help="explicit destination path for generated repro.py")
    parser.add_argument("--output-dir", default=None, help="directory to stage content-addressed repro.py and manifest")
    parser.add_argument("--warmup", type=int, default=10, help="untimed warmup launches before measurement (default: 10)")
    parser.add_argument("--iters", type=int, default=50, help="timed launches per measurement pass (default: 50)")
    parser.add_argument("--flush-mb", type=int, default=256, help="L2 cache flush buffer size in MiB (0 disables; default: 256)")
    parser.add_argument("--max-cv-pct", type=float, default=5.0, help="steady-state window CV threshold in percent (default: 5.0)")
    parser.add_argument("--l2-bytes", type=int, default=None, help="override target NPU L2 size in bytes for cold-flush validation")
    parser.add_argument("--seed", type=int, default=0, help="deterministic RNG seed for tensor setup (default: 0)")
    parser.add_argument("--dry-run", action="store_true", help="print metadata/checks without writing a script")
    args = parser.parse_args(list(argv or ()))
    binding, index, source_path = _row_from_args(args)
    try:
        if args.dry_run:
            occurrence = _compact_occurrence(binding)
            failed = [name for name, value in occurrence["checks"].items() if value is False]
            print(json.dumps({
                "schema": "mindie-single-op-repro-dry-run/2", "api": occurrence["api"], "occurrence_index": index,
                "source": source_path, "metadata": occurrence["metadata"],
                "checks": occurrence["checks"], "failed_checks": failed,
                "install": occurrence["metadata"]["install"], "fidelity": occurrence["fidelity"],
                "repro_status": binding.get("repro_status")}, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if not failed else 2
        result = generate_single_op_reproducer(binding, output_path=args.output, output_dir=args.output_dir,
            warmup=args.warmup, iters=args.iters, flush_mb=args.flush_mb,
            max_cv_pct=args.max_cv_pct, l2_bytes=args.l2_bytes, seed=args.seed, cann_version=args.version)
    except ProfilerUsageError as exc:
        print(json.dumps({"schema": REPRO_SCHEMA, "status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 4
    summary = {key: value for key, value in result.items() if key != "script"}
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "ready" else 4

from .repro_mcp import MCP_TOOL_SPECS, call_mcp_tool  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
