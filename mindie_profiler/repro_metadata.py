"""Deterministic metadata synthesis for the exact allocated reproducer shapes.

[Role]
  Build sequence offsets (cumulative with a leading zero or per-batch lengths),
  group lists in cumsum/counts/sparse-pair form, block tables bounded by the
  physical KV cache, routing indices and an explicit install list whose shapes
  and numels must match the allocated tensors exactly.

[Invariants]
  * ``effective_tokens == 0`` is honored; it is never replaced by the bucket.
  * Cumulative offsets always carry the leading zero where the contract requires
    it, and a TND tail must equal ``T`` for the arch22 rule.
  * Synthesized block-table page ids are in bounds of the **minimum** page
    capacity across every allocated KV cache, and rows are unique for active
    pages.  Captured values are installed verbatim and then checked.
  * Group counts come from the allocated expert weights, never a guessed
    default; sparse ``(expert_id, count)`` indices are unique, in range and
    increasing.  Every install item is shape/numel-checked.
  * The module is injected verbatim into the emitted script, so it imports only
    ``synthesize_group_list`` (also injected).

[Timeouts & Locks]
  Pure in-memory arithmetic proportional to the metadata size.

[Side-Effect Policy]
  No I/O, hardware access or torch import.
"""

from __future__ import annotations

from typing import Any
from .events import ProfilerUsageError

from .op_abi_padding import synthesize_group_list, validate_group_list
from .repro_values import bounded_count, bounded_sequence, bounded_shape, validate_count_attributes, bounded_summary, validate_container_depth, storage_mapping


def _ceil_div(value: int, divisor: int) -> int:
    return -(-int(value) // int(divisor)) if divisor else 0


def _flatten_values(value: Any, *, integer_only: bool = False) -> list[Any] | None:
    """Recursively flatten nested captured values, rejecting malformed leaves."""
    if integer_only and not isinstance(value, (list, tuple)):
        return ([value] if isinstance(value, int) and not isinstance(value, bool)
                and 0 <= value <= 268_435_456 else None)
    if isinstance(value, (int, float)):
        return [value]
    if isinstance(value, (list, tuple)):
        out: list[Any] = []
        for item in bounded_sequence(value, "metadata values"):
            nested = _flatten_values(item, integer_only=integer_only)
            if nested is None:
                return None
            bounded_count(len(out) + len(nested), "flattened metadata values")
            out.extend(nested)
        return out
    return None


def _spread(total: int, parts: int) -> list[int]:
    bounded_count(total, "spread total", 0, 268_435_456)
    bounded_count(parts, "spread parts", 1)
    total, parts = max(0, int(total)), max(1, int(parts))
    base, extra = divmod(total, parts)
    return [base + (1 if index < extra else 0) for index in range(parts)]


def _monotonic(values: list[int]) -> bool:
    return all(value >= 0 for value in values) and all(
        right >= left for left, right in zip(values, values[1:]))


def _diffs(values: list[int]) -> list[int]:
    previous, out = 0, []
    for value in values:
        out.append(max(0, int(value) - previous))
        previous = int(value)
    return out


def _cumulative(counts: list[int], *, leading_zero: bool = True) -> list[int]:
    out, running = ([0] if leading_zero else []), 0
    for count in counts:
        running += int(count)
        out.append(running)
    return out


def _metadata_fidelity(captured_any: bool, captured_all: bool,
              allocations: list[dict[str, Any]],
              *, metadata_roles: set[str]) -> str:
    def _numel(shape: list[int]) -> int:
        total = 1
        for dim in shape or [1]:
            total *= max(0, int(dim))
        return total

    def _exact_values(spec: dict[str, Any]) -> bool:
        values = spec.get("values")
        if values is None:
            return False
        flat = _flatten_values(values, integer_only=spec.get("role") in metadata_roles)
        return flat is not None and len(flat) == _numel(list(spec.get("shape") or []))

    inputs = [spec for spec in allocations
              if spec.get("direction") == "input" and spec.get("state") != "alias"]
    if inputs and all(_exact_values(spec) for spec in inputs):
        return "value_captured"
    if captured_any or any(_exact_values(spec) for spec in inputs):
        if any(_exact_values(spec) for spec in inputs
               if spec.get("role") not in metadata_roles):
            return "shape_and_values_captured"
        return "metadata_captured_activations_synthetic"
    return "descriptor_synthetic"


def validate_metadata_counts(occurrence):
    """Bound tensor geometry and every scalar feeding host metadata expansion.

    Tensor allocations total at most 2**28 elements; host metadata totals at
    most 10**6. Scalar extents are at most 2**28, batch counts at most 65536.
    """
    validate_container_depth(occurrence)
    elements = metadata = 0
    for spec in bounded_sequence(occurrence.get("allocations", ()), "allocations", 1024):
        count = bounded_shape(spec.get("shape", []))
        elements += count
        if spec.get("role") in {"seq_lens", "block_table", "group_list", "index"}:
            bounded_shape(spec.get("shape", []), 1_000_000)
            metadata += count
        storage = storage_mapping(spec.get("storage"))
        for key in ("storage_offset", "storage_bytes"):
            if storage.get(key) is not None:
                bounded_count(storage[key], key, 0, 1 << 40)
        strides = storage.get("strides", storage.get("stride"))
        if strides is not None:
            for stride in bounded_sequence(strides, "strides", 32):
                bounded_count(stride, "stride", 0, 1 << 40)
            shape = spec.get("shape") or []
            if len(shape) != len(strides):
                raise ProfilerUsageError("strides must match shape dimensions")
            span = bounded_count(1 + sum(max(0, dim - 1) * stride for dim, stride in zip(shape, strides)),
                                 "strided storage elements", 0, 268_435_456)
            elements += max(0, span - count)
    bounded_count(elements, "total tensor elements", 0, 268_435_456)
    bounded_count(metadata, "total metadata elements")
    padding = occurrence.get("padding") or {}
    for source in (occurrence.get("attrs") or {}, padding, padding.get("qualification") or {}):
        validate_count_attributes(source)


def synthesize_metadata(occurrence: dict[str, Any]) -> dict[str, Any]:
    """Synthesize values for the exact allocated metadata tensor shapes."""
    validate_metadata_counts(occurrence)
    attrs = dict(occurrence.get("attrs") or {})
    padding = dict(occurrence.get("padding") or {})
    qualification = dict(padding.get("qualification") or {})
    layout = str(qualification.get("layout") or attrs.get("input_layout") or "TND")
    cumsum = str(qualification.get("encoding") or "cumsum") != "lengths"
    bucket = max(0, int(padding.get("bucket_tokens") or attrs.get("bucket_tokens") or 0))
    token_capacity = max(0, int(qualification.get("physical_bucket_tokens") or bucket))
    effective_raw = padding.get("effective_tokens")
    if effective_raw is None:
        effective_raw = attrs.get("effective_tokens")
    effective = 0 if effective_raw is None else max(0, int(effective_raw))
    effective = min(effective, bucket) if bucket else effective
    allocations = list(occurrence.get("allocations") or ())
    by_name = {spec["name"]: spec for spec in allocations}
    inputs = [spec for spec in allocations if spec.get("direction") == "input"]
    primary = next((spec for spec in inputs if spec.get("role") == "activation"), None)
    primary = primary or (inputs[0] if inputs else None)
    primary_shape = list((primary or {}).get("shape") or [])

    seq_specs = sorted((spec for spec in inputs if spec.get("role") == "seq_lens"),
                       key=lambda spec: spec["name"])
    batch = None
    for spec in seq_specs:
        size = int((spec.get("shape") or [0])[0])
        if "context" in spec["name"] or "kv" in spec["name"]:
            continue
        batch = max(1, size - 1 if (cumsum and qualification.get("leading_zero"))
                    else size)
        break
    if batch is None:
        for spec in seq_specs:
            if "context" in spec["name"] or "kv" in spec["name"]:
                batch = max(1, int((spec.get("shape") or [0])[0]))
                break
    if batch is None and layout in {"BSH", "BSND", "BNSD"} and len(primary_shape) > 1:
        batch = max(1, int(primary_shape[0]))
    if batch is None:
        batch = max(1, int(attrs.get("batch_size") or attrs.get("num_seqs") or 1))

    kv_len = int(attrs.get("kv_len") or attrs.get("context_len") or attrs.get("seq_len")
                 or (effective or bucket) or 1)
    q_counts = _spread(effective, batch)
    kv_counts = _spread(kv_len, batch)
    leading_zero = bool(qualification.get("leading_zero"))
    pa_lengths = bool(qualification.get("pa")) or (
        (qualification.get("kv_mode") or {}).get("PA") == "lengths")
    q_values = _cumulative(q_counts, leading_zero=leading_zero) if cumsum else q_counts
    kv_values = (kv_counts if pa_lengths else
                 _cumulative(kv_counts, leading_zero=leading_zero) if cumsum else kv_counts)

    checks: dict[str, Any] = {}
    install: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    role_targets = {}
    for spec in allocations:
        if spec.get("role") not in {"seq_lens", "block_table", "group_list", "index"}:
            continue
        role_key = (spec.get("direction"), spec["role"])
        previous = role_targets.setdefault(role_key, spec)
        if previous is not spec and (spec.get("direction") != "input" or
                (spec["role"] != "seq_lens" and spec.get("shape") != previous.get("shape"))):
            violations.append({"code": "unsupported_metadata_allocation",
                               "tensor": spec["name"], "role": spec["role"]})
        if spec.get("values") is not None:
            flat = _flatten_values(spec["values"], integer_only=True)
            if flat is None or len(flat) != bounded_shape(spec.get("shape", [])):
                violations.append({"code": "captured_metadata_type_invalid" if flat is None
                                   else "captured_metadata_length_mismatch",
                                   "tensor": spec["name"], "values": bounded_summary(spec["values"])})
            if flat is not None and spec.get("direction") == "output":
                # Output indices have distinct declared meanings: expanded row
                # permutations versus expert IDs. Unknown targets fail closed.
                capacity = 0
                if spec["role"] == "index" and spec["name"] == "expanded_row_idx_out":
                    capacity = bounded_shape(spec.get("shape", []))
                elif spec["role"] == "index" and spec["name"] == "expert_idx":
                    capacity = primary_shape[-1] if primary_shape else 0
                valid = (bool(capacity) and len(flat) == bounded_shape(spec.get("shape", []))
                         and all(value < capacity for value in flat))
                install.append({"tensor": spec["name"], "shape": list(spec.get("shape", [])),
                                "values": flat, "encoding": "output_indices|captured",
                                "captured": True, "captured_valid": valid})
                if not valid:
                    violations.append({"code": "captured_metadata_invalid" if capacity
                                       else "unsupported_metadata_output", "tensor": spec["name"]})
    if any(sum(item["name"] == spec["name"] for item in allocations) > 1 for spec in allocations
           if spec.get("role") in {"seq_lens", "block_table", "group_list", "index"}):
        violations.append({"code": "duplicate_metadata_target", "detail": "allocation names must be unique"})

    def record_checks(spec, target_checks):
        # A later valid allocation cannot overwrite an earlier failed check.
        for name, value in target_checks.items():
            checks[name] = (checks.get(name, True) and value) if isinstance(value, bool) else value
            if value is False:
                violations.append({"code": "metadata_geometry_invalid",
                                   "tensor": spec["name"], "check": name})

    captured_any = [False]
    captured_all = [True]

    def _numel(shape: list[int]) -> int:
        total = 1
        for dim in shape or [1]:
            total *= max(0, int(dim))
        return total

    def _valid_captured(kind: str, values: list[int],
                        *, shape: list[int] | None = None,
                        num_blocks: int = 0, block_size: int = 1,
                        table_cols: int = 0, batch_rows: int = 0,
                        kv_capacity: int = 0, expert_count: int = 0,
                        group_count: int | None = None,
                        per_item_extent: int | None = None) -> bool:
        numbers = _flatten_values(values, integer_only=True)
        if numbers is None:
            return False
        if any(value < 0 for value in numbers):
            return False
        limit = kv_len if kind.startswith("kv") else token_capacity
        if kind == "paged_block_table":
            expected = 1
            for dim in shape or [1]:
                expected *= max(0, int(dim))
            if len(numbers) != expected:
                return False
            cols = int(shape[1]) if shape and len(shape) > 1 else table_cols
            rows = int(shape[0]) if shape else batch_rows
            if batch_rows and rows != batch_rows:
                return False
            if not num_blocks or any(value < 0 or value >= num_blocks
                                     for value in numbers):
                return False
            if cols and any(value >= num_blocks for value in numbers):
                return False
            return True
        if kind.startswith("cumsum") or kind.startswith("kv_cumsum"):
            return (all(right >= left for left, right in zip(numbers, numbers[1:]))
                    and (not leading_zero or not numbers or numbers[0] == 0)
                    and (not numbers or numbers[-1] <= limit))
        if kind.startswith("per_batch") or kind.startswith("kv_lengths"):
            if per_item_extent is not None:
                return all(value <= int(per_item_extent) for value in numbers)
            capacity = kv_capacity or limit
            return sum(numbers) <= capacity and (
                not numbers or max(numbers) <= capacity)
        if kind.startswith("expert"):
            return bool(expert_count) and all(
                0 <= value < int(expert_count) for value in numbers)
        if kind.startswith("group_list"):
            if group_type in {"1", "counts", "count"}:
                return sum(numbers) <= token_capacity
            if group_type in {"2", "sparse_pairs", "pairs"}:
                indices = numbers[0::2]
                return (len(numbers) % 2 == 0
                        and all(right > left for left, right in zip(indices, indices[1:]))
                        and (group_count is None or all(
                            0 <= index < int(group_count) for index in indices))
                        and sum(numbers[1::2]) <= token_capacity)
            return (all(right >= left for left, right in zip(numbers, numbers[1:]))
                    and (not numbers or numbers[-1] <= token_capacity))
        return False

    def add(name: str, values: list[int], encoding: str,
            *, num_blocks: int = 0, block_size: int = 1,
            table_cols: int = 0, batch_rows: int = 0,
            kv_capacity: int = 0, expert_count: int = 0,
            group_count: int | None = None,
            per_item_extent: int | None = None) -> None:
        spec = by_name.get(name)
        if spec is None:
            return
        shape = list(spec.get("shape") or [])
        flat = [item for row in values for item in row] if values and isinstance(
            values[0], list) else list(values)
        captured = spec.get("values")
        if captured is not None:
            captured_flat = _flatten_values(captured, integer_only=True)
            typed = captured_flat is not None
            if typed and len(captured_flat) == _numel(shape):
                captured_numbers = captured_flat
                valid = _valid_captured(
                    encoding, captured_numbers, shape=shape, num_blocks=num_blocks,
                    block_size=block_size, table_cols=table_cols,
                    batch_rows=batch_rows, kv_capacity=kv_capacity,
                    expert_count=expert_count, group_count=group_count,
                    per_item_extent=per_item_extent)
                install.append({"tensor": name, "shape": shape,
                                "values": captured_numbers,
                                "encoding": encoding + "|captured",
                                "captured": True, "captured_valid": bool(valid)})
                captured_any[0] = True
                if not valid:
                    violations.append({"code": "captured_metadata_invalid",
                                       "tensor": name, "encoding": encoding,
                                       "values": captured_numbers[:8]})
                return
            if not typed:
                violations.append({"code": "captured_metadata_type_invalid",
                                   "tensor": name, "shape": shape,
                                   "values": bounded_summary(captured)})
            else:
                violations.append({"code": "captured_metadata_length_mismatch",
                                   "tensor": name, "shape": shape,
                                   "values": len(captured_flat)})
        install.append({"tensor": name, "shape": shape,
                        "values": flat, "encoding": encoding,
                        "captured": False, **({"captured_valid": False,
                        "invalid_capture": bounded_summary(captured)} if captured is not None else {})})
        captured_all[0] = False

    per_batch_lengths = not cumsum
    seq_extent = (qualification.get("seq_extent")
                  if per_batch_lengths else None)
    for spec in seq_specs:
        name = spec["name"]
        lower = name.lower()
        if "context" in lower or "kv" in lower:
            add(name, kv_values,
                "kv_lengths" if pa_lengths else ("kv_cumsum" if cumsum else "kv_lengths"))
        else:
            add(name, q_values, "cumsum_leading_zero" if cumsum else "per_batch_lengths",
                per_item_extent=seq_extent)
        expected = len(kv_values if "context" in lower or "kv" in lower else q_values)
        associated = list(spec.get("shape") or []) == [expected]
        record_checks(spec, {"sequence_batch_matches": associated})
        if not associated and install[-1].get("captured"):
            install[-1]["captured_valid"] = False
    group_type = str(padding.get("group_list_type") or attrs.get("group_list_type") or "0")
    weight_allocs = [spec for spec in inputs if spec.get("name") in
                     {"weight", "w1", "w2"}]
    group_count = None
    if weight_allocs:
        if len(weight_allocs) > 1:
            group_count = len(weight_allocs)
        else:
            shape = list(weight_allocs[0].get("shape") or [])
            group_count = (int(shape[0]) if len(shape) >= 3
                           else 1) if shape else 1
        group_count = max(1, group_count)
    group_values: list[int] = []
    for group_spec in (spec for spec in inputs if spec.get("role") == "group_list"):
        target_checks = {}
        numel = 1
        for dim in group_spec.get("shape") or [1]:
            numel *= max(1, int(dim))
        bounded_count(numel, "group metadata elements")
        groups = numel // 2 if group_type in {"2", "sparse_pairs", "pairs"} else numel
        group_values = synthesize_group_list(effective, groups, group_type)
        add(group_spec["name"], group_values, "group_list_" + group_type,
            group_count=group_count)
        installed_group = next((item for item in install
                                if item["tensor"] == group_spec["name"]), None)
        final_group = (list(installed_group["values"])
                       if installed_group is not None else list(group_values))
        group_checked = validate_group_list(final_group, group_type, token_capacity,
                                            num_groups=group_count)
        target_checks["group_list_valid"] = bool(group_checked["valid"])
        target_checks["group_list_num_groups"] = group_count
        target_checks["group_list_violations"] = group_checked["violations"]
        routed = int(group_checked["routed_tokens"])
        target_checks["group_list_reaches_effective"] = routed == effective
        target_checks["group_list_bounded"] = routed <= token_capacity
        record_checks(group_spec, target_checks)

    block_table: list[list[int]] = []
    block_specs = sorted((spec for spec in inputs if spec.get("role") == "block_table"), key=lambda spec: spec["name"])
    caches = sorted((spec for spec in inputs if spec.get("role") == "kv_cache"), key=lambda spec: spec["name"])
    sequence_items = [item for item in install if by_name[item["tensor"]].get("role") == "seq_lens"]
    if sequence_items and caches and not block_specs:
        record_checks(seq_specs[0], {"sequence_geometry_associated": False})
    for block_spec in block_specs:
        target_checks = {}
        block_table = []
        table_shape = [int(dim) for dim in block_spec.get("shape") or []]
        target_checks["block_table_rank_valid"] = len(table_shape) == 2
        rows = table_shape[0] if table_shape else batch
        cols = table_shape[1] if len(table_shape) > 1 else 0
        cache_shapes = [[int(dim) for dim in spec.get("shape") or []]
                        for spec in caches]
        cache_shape = cache_shapes[0] if cache_shapes else []
        target_checks["kv_cache_geometry_unambiguous"] = bool(cache_shapes) and all(
            len(shape) >= 2 and shape[0] > 0 and shape[1] > 0
            and shape[1:] == cache_shape[1:] for shape in cache_shapes)
        capacities = [shape[0] for shape in cache_shapes if shape]
        allocated_pages = min(capacities) if capacities else 0
        attribute_block_size = int(attrs.get("block_size") or 0)
        physical_block_size = (int(cache_shape[1]) if len(cache_shape) > 1 else 0)
        block_size = physical_block_size or attribute_block_size or 1
        block_size = max(1, block_size)
        attribute_pages = int(attrs.get("num_blocks") or 0)
        # Physical capacity is authoritative: an attribute may never enlarge it.
        num_blocks = allocated_pages or attribute_pages
        pages = [_ceil_div(count, block_size) for count in kv_counts]
        target_checks["block_table_batch_matches"] = rows == batch
        target_checks["block_table_capacity"] = bool(num_blocks) and cols >= max(pages or [0])
        target_checks["allocated_pages"] = allocated_pages
        target_checks["kv_cache_page_capacities"] = capacities
        target_checks["kv_cache_count"] = len(caches)
        target_checks["attributes_num_blocks"] = attribute_pages
        target_checks["page_capacity_source"] = ("kv_cache.shape[0]" if allocated_pages
                                          else "attributes.num_blocks")
        target_checks["block_size_matches_cache"] = (
            not (physical_block_size and attribute_block_size)
            or physical_block_size == attribute_block_size)
        shared = max(0, min(int(attrs.get("shared_prefix_pages") or 0),
                            min(pages or [0]), cols))
        total_needed = shared + sum(max(0, page - shared) for page in pages)
        target_checks["block_table_physical_fit"] = bool(num_blocks) and total_needed + 1 <= num_blocks
        active_start = 1 if num_blocks > 1 else 0
        cursor, sentinel = active_start, 0
        for row in range(rows):
            row_pages = []
            for page in range(cols):
                if page < shared:
                    row_pages.append(active_start + page)
                elif row < len(pages) and page < pages[row]:
                    row_pages.append(cursor)
                    cursor += 1
                else:
                    row_pages.append(sentinel)
            block_table.append(row_pages)
        add(block_spec["name"], block_table, "paged_block_table",
            num_blocks=num_blocks, block_size=block_size, table_cols=cols,
            batch_rows=batch)
        installed = next((item for item in install
                          if item["tensor"] == block_spec["name"]), None)
        final_table: list[list[int]] = []
        if installed is not None and cols:
            flat = list(installed["values"])
            final_table = [flat[index * cols:(index + 1) * cols]
                           for index in range(rows)]
        target_checks["block_table_in_bounds"] = bool(num_blocks) and all(
            0 <= page < num_blocks for row in final_table for page in row)
        target_checks["block_table_row_unique"] = all(
            len(set(item for item in row if item != sentinel)) ==
            len([item for item in row if item != sentinel]) for row in final_table)
        target_checks["block_table_shared_prefix_allowed"] = (
            shared == 0 or "shared_prefix_pages" in attrs)
        valid_pages = [[page for page in row if 0 <= page < num_blocks]
                       for row in final_table]
        # Every installed sequence is checked against every table/cache. There
        # is no first-match shortcut, including for the forwarded argument.
        for item in sequence_items:
            values = item["values"]
            encoding = item["encoding"].split("|")[0]
            if "cumsum" in encoding:
                values = _diffs(values)[1:] if leading_zero else _diffs(values)
            associated = (len(item["shape"]) == 1 and len(values) == rows
                          and target_checks["kv_cache_geometry_unambiguous"])
            needed = [_ceil_div(value, block_size) for value in values]
            sequence_checks = {
                "sequence_geometry_associated": associated,
                "context_fits_block_table": associated and bool(final_table) and all(
                    required <= len(row) for required, row in zip(needed, valid_pages)),
                "context_width_bound": bool(cols) and all(value <= cols * block_size for value in values),
                "context_cache_capacity": bool(cache_shapes) and all(
                    sum(values) <= shape[0] * shape[1] and all(
                        value <= shape[0] * shape[1] for value in values)
                    for shape in cache_shapes if len(shape) >= 2),
            }
            if item.get("captured") and not all(sequence_checks.values()):
                item["captured_valid"] = False
            record_checks(by_name[item["tensor"]], sequence_checks)
            checks["context_pages_required"] = max(checks.get("context_pages_required", 0), max(needed or [0]))
        target_checks["block_table_width_pages"] = cols
        record_checks(block_spec, target_checks)

    for index_spec in (spec for spec in inputs if spec.get("role") == "index"):
        target_checks = {}
        shape = [int(dim) for dim in index_spec.get("shape") or []]
        numel = 1
        for dim in shape or [1]:
            numel *= max(1, dim)
        bounded_count(numel, "index metadata elements")
        experts = max(1, int(attrs.get("expert_num") or attrs.get("num_experts") or 1))
        routed = (effective if effective else bucket) or numel
        values = [index % experts for index in range(numel)]
        add(index_spec["name"], values, "expert_ids", expert_count=experts)
        installed_index = next((item for item in install
                                if item["tensor"] == index_spec["name"]), None)
        final_index = (list(installed_index["values"])
                       if installed_index is not None else list(values))
        target_checks["expert_ids_non_negative"] = all(value >= 0 for value in final_index)
        target_checks["expert_ids_in_bounds"] = all(
            0 <= value < experts for value in final_index)
        target_checks["expert_ids_cover_routed_rows"] = len(final_index) == numel and (
            numel >= min(routed, numel))
        record_checks(index_spec, target_checks)

    for item in install:
        spec = by_name.get(item["tensor"])
        if spec is None:
            violations.append({"code": "metadata_target_missing", "tensor": item["tensor"]})
            continue
        expected = 1
        for dim in item["shape"]:
            expected *= int(dim)
        if expected != len(item["values"]):
            violations.append({"code": "metadata_numel_mismatch",
                               "tensor": item["tensor"], "shape": item["shape"],
                               "values": len(item["values"])})
    checks["metadata_installable"] = not violations
    checks["effective_within_bucket"] = effective <= bucket if bucket else True
    checks["effective_within_allocation"] = (effective <= token_capacity
                                              if token_capacity else True)
    checks["effective_zero_faithful"] = (effective != 0 or (
        not q_values or max(q_values) == 0))
    checks["leading_zero_offsets"] = (not cumsum) or (not leading_zero) or (
        not q_values or q_values[0] == 0)
    checks["sequence_monotonic"] = (
        True if not cumsum else (_monotonic(q_values) and _monotonic(kv_values)))
    if per_batch_lengths:
        per_item_ok = True
        per_item_violations: list[dict[str, Any]] = []
        for spec in seq_specs:
            lower = spec["name"].lower()
            if "context" in lower or "kv" in lower:
                continue
            installed = next((item for item in install
                              if item["tensor"] == spec["name"]), None)
            values = (list(installed["values"]) if installed is not None else [])
            if seq_extent is not None and any(
                    value < 0 or value > int(seq_extent) for value in values):
                per_item_ok = False
                per_item_violations.append({
                    "code": "sequence_per_item_out_of_bounds",
                    "tensor": spec["name"], "values": values[:8],
                    "extent": int(seq_extent)})
        checks["sequence_per_item_bounds"] = per_item_ok
        if per_item_violations:
            violations.extend(per_item_violations)
        checks["metadata_installable"] = not violations
    tail_rule = qualification.get("tail_rule")
    checks["tnd_tail_equals_bucket"] = (layout != "TND" or tail_rule != "eq_bucket"
                                        or effective == bucket)
    checks["batch_rows_match"] = all(
        int((spec.get("shape") or [batch])[0]) in {batch, batch + 1}
        for spec in seq_specs) if seq_specs else True
    return {
        "effective_tokens": effective, "bucket_tokens": bucket, "batch_size": batch,
        "layout": layout, "kv_len": kv_len,
        "actual_seq_lens_q": q_values, "actual_seq_lens_kv": kv_values,
        "per_sequence_q": q_counts, "per_sequence_kv": kv_counts,
        "context_lens": kv_counts, "group_list": group_values,
        "group_list_type": group_type, "block_table": block_table,
        "install": install, "checks": checks, "violations": violations,
        "fidelity": _metadata_fidelity(captured_any[0], captured_all[0], allocations,
                              metadata_roles={"seq_lens", "block_table",
                                              "group_list", "index"}),
    }
