"""Implementation and tiling issue laws for measured matrix-pipe supply.

[Role]
  Own the issue-law registry that certifies measured matrix work against a
  pinned kernel/op-host source identity and wrapper source identity, plus the
  deployment-source identity and tensor-rule helpers.  ``measured_supply``
  re-exports these names and keeps derivation and dual-load aggregation.

[Invariants]
  * A law is certified by implementation evidence that is stable across
    container images: exact kernel and wrapper source sha256/revision pairs,
    native type, tensor formats, dtypes, and the physical m tile alignment.
  * Deployment image digests are corroborating metadata only; a digest is
    never the sole or required certification predicate.
  * Absent, partial, ambiguous, or conflicting evidence never certifies.
  * Only exact 4-slot ``[M, K] x NZ -> [M, N]`` layouts are accepted.

[Timeouts & Locks]
  Pure in-memory finite arithmetic; no I/O or locks.

[Side-Effect Policy]
  Returns fresh dicts/tuples or immutable mappings; mutates no global state.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

R64_IMAGE_SHA = "8d422528ac20a8babcbbf93762cde3b47d4db6c5f7ab777f4f1f65b32b89ab3e"
R35_IMAGE_SHA = "5461a1a8253c6dc07868956166ad94751f84c82d00ff7791c59a9c1ac497de06"

# Physical tile and tensor-slot geometry referenced by every law below.
_M_ALIGNMENT = 16
_NZ_TILE_MX = 32
_NZ_TILE_MAX = 64
_MATRIX_INPUT_SLOTS = 4
_MAX_TENSOR_SLOTS = _MATRIX_INPUT_SLOTS + 2

_DTYPE_ALIASES = {
    "bfloat16": "bf16",
    "bf16": "bf16",
    "float16": "fp16",
    "half": "fp16",
    "fp16": "fp16",
    "float": "fp32",
    "float32": "fp32",
    "fp32": "fp32",
    "double": "fp64",
    "float64": "fp64",
    "fp64": "fp64",
    "int8": "int8",
    "int16": "int16",
    "int32": "int32",
    "int64": "int64",
    "float8_e4m3fn": "fp8_e4m3",
    "fp8_e4m3": "fp8_e4m3",
    "float8_e5m2": "fp8_e5m2",
    "fp8_e5m2": "fp8_e5m2",
    "float8_e8m0": "fp8_e8m0",
    "fp8_e8m0": "fp8_e8m0",
    "hifloat8": "hif8",
    "hif8": "hif8",
    "dt_hifloat8": "hif8",
    "float4_e2m1": "fp4_e2m1",
    "fp4_e2m1": "fp4_e2m1",
    "dt_float4_e2m1": "fp4_e2m1",
    "mxfp4": "fp4_e2m1",
    "mx_fp4": "fp4_e2m1",
    "dt_int4": "int4",
    "uint4": "uint4",
    "dt_uint4": "uint4",
    "float8_e4m3": "fp8_e4m3",
    "dt_float8_e4m3fn": "fp8_e4m3",
    "dt_float8_e5m2": "fp8_e5m2",
    "dt_float8_e8m0": "fp8_e8m0",
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "uint64": "uint64",
    "int4": "int4",
    "bool": "bool",
}

ISSUE_LAWS: tuple[dict[str, Any], ...] = (
    {
        "law_id": "qbmm_v3_mxfp8_m16_nz",
        "native_type": "QuantBatchMatmulV3",
        "dtype": "fp8_e4m3",
        "output_dtype": "bf16",
        "m_alignment": _M_ALIGNMENT,
        "alignment_basis": "physical_tile_m16_not_logical_m",
        "weight_layout": "FRACTAL_NZ",
        "required_input_dtypes": ("fp8_e4m3", "fp8_e4m3", "fp8_e8m0", "fp8_e8m0"),
        "required_input_formats": ("ND", "FRACTAL_NZ", "ND", "ND"),
        "required_output_format": "ND",
        "kernel_source": {
            "path": "cann/op_kernel/quant_batch_matmul_v3/arch35/quant_batch_matmul_v3.cpp",
            "sha256": "13daf996890d70e7b1dc9275ab3a464043860e67d6df730e28742393c023ec88",
            "revision": "cann-9.2.1-r64",
        },
        "wrapper_source": {
            "path": "vllm_ascend/quantization/methods/w8a8/w8a8_mxfp8.py",
            "sha256": "38de2275cf33ced653b8398e98a07f483489dc8e7353b2b3c238a5ff00782f79",
            "revision": "r64/8d422528",
            "symbol": "AscendW8A8MXFP8DynamicLinearMethod.apply",
        },
        "scope": "r64",
        "legacy_image_digests": (R64_IMAGE_SHA,),
    },
)

_LEGACY_DIGEST_SCOPES = {
    digest: law["scope"] for law in ISSUE_LAWS for digest in law["legacy_image_digests"]
}
_LEGACY_DIGEST_SCOPES[R35_IMAGE_SHA] = "r35"

_CONFLICT = object()


def image_digest(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text.split(":", 1)[1] if text.startswith("sha256:") else text


def _law_by_id(law_id: Any) -> Mapping[str, Any] | None:
    return next((law for law in ISSUE_LAWS if law["law_id"] == law_id), None)


def _law_for_digest(digest: Any) -> Mapping[str, Any] | None:
    if not digest:
        return None
    return next(
        (law for law in ISSUE_LAWS if digest in law["legacy_image_digests"]), None
    )


def _legacy_scope(digest: Any) -> str:
    if not digest:
        return "absent"
    return _LEGACY_DIGEST_SCOPES.get(digest, "unpinned")


def _conflicts_with_law(digest: str, law: Mapping[str, Any]) -> bool:
    """A known different image contradicts a law; an unknown image does not."""
    if not digest or digest not in _LEGACY_DIGEST_SCOPES:
        return False
    return digest not in law["legacy_image_digests"]


def _evidence_value(
    evidence: Mapping[str, Any],
    flat_keys: tuple[str, ...],
    nested: Any,
    nested_key: str,
) -> Any:
    values = [evidence[key] for key in flat_keys if evidence.get(key) is not None]
    if isinstance(nested, Mapping) and nested.get(nested_key) is not None:
        values.append(nested[nested_key])
    if not values:
        return None
    texts = {str(value).strip() for value in values}
    return next(iter(texts)) if len(texts) == 1 else _CONFLICT


def verified_implementation(
    evidence: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Normalize stable implementation evidence into a frozen classification.

    Accepts flat ``kernel_source_sha256``/``wrapper_source_sha256`` plus
    revision keys, and equivalent nested ``kernel_source``/``wrapper_source``
    mappings.  Missing, partial, ambiguous, or internally conflicting evidence
    returns ``None``; no evidence is ever invented.
    """
    if not isinstance(evidence, Mapping):
        return None
    kernel = evidence.get("kernel_source")
    wrapper = evidence.get("wrapper_source")
    kernel_sha = _evidence_value(
        evidence, ("kernel_source_sha256", "source_sha256"), kernel, "sha256"
    )
    kernel_revision = _evidence_value(
        evidence, ("kernel_revision", "source_revision"), kernel, "revision"
    )
    wrapper_sha = _evidence_value(
        evidence, ("wrapper_source_sha256",), wrapper, "sha256"
    )
    wrapper_revision = _evidence_value(
        evidence, ("wrapper_revision", "wrapper_source_revision"), wrapper, "revision"
    )
    native = evidence.get("native_type")
    native_type = str(native).strip() if native is not None else None
    for value in (kernel_sha, kernel_revision, wrapper_sha, wrapper_revision):
        if value is None or value is _CONFLICT:
            return None
    matches = [
        law
        for law in ISSUE_LAWS
        if (native_type is None or native_type == law["native_type"])
        and image_digest(kernel_sha) == image_digest(law["kernel_source"]["sha256"])
        and kernel_revision == law["kernel_source"]["revision"]
        and image_digest(wrapper_sha) == image_digest(law["wrapper_source"]["sha256"])
        and wrapper_revision == law["wrapper_source"]["revision"]
    ]
    if len(matches) != 1:
        return None
    law = matches[0]
    return MappingProxyType(
        {
            "implementation_verified": True,
            "law_id": law["law_id"],
            "native_type": law["native_type"],
            "source_scope": law["scope"],
            "kernel_source_sha256": image_digest(kernel_sha),
            "kernel_revision": kernel_revision,
            "wrapper_source_sha256": image_digest(wrapper_sha),
            "wrapper_revision": wrapper_revision,
        }
    )


def _conflicting_identity(digest: str, basis: str) -> dict[str, Any]:
    return {
        "source_scope": "conflicting",
        "image_digest": digest or None,
        "basis": basis,
        "implementation_verified": False,
        "law_id": None,
    }


def deployment_source_identity(
    image_id: Any = None,
    *,
    basis: str = "absent",
    implementation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify implementation evidence first and the image digest second.

    Implementation evidence that matches a law wins the scope classification
    even when the image digest is absent, unknown, or from a different
    container image.  The digest still gates certification: a known digest
    pinned to another scope, or unverifiable implementation evidence alongside
    a corroborating digest, is reported as conflicting work and never
    certifies.  Without implementation evidence the legacy digest-only
    classification is retained for old captures.
    """
    digest = image_digest(image_id)
    if implementation is not None:
        verified = verified_implementation(implementation)
        if verified is not None:
            law = _law_by_id(verified["law_id"])
            if law is not None:
                return {
                    "source_scope": law["scope"],
                    "image_digest": digest or None,
                    "basis": basis,
                    "implementation_verified": True,
                    "law_id": law["law_id"],
                    "kernel_source_sha256": verified["kernel_source_sha256"],
                    "kernel_revision": verified["kernel_revision"],
                    "wrapper_source_sha256": verified["wrapper_source_sha256"],
                    "wrapper_revision": verified["wrapper_revision"],
                    "native_type": verified["native_type"],
                }
            return _conflicting_identity(digest, basis)
        if _law_for_digest(digest) is not None:
            return _conflicting_identity(digest, basis)
    law = _law_for_digest(digest)
    return {
        "source_scope": _legacy_scope(digest),
        "image_digest": digest or None,
        "basis": basis,
        "implementation_verified": False,
        "law_id": law["law_id"] if law is not None else None,
    }


def _issue_law_payload(law: Mapping[str, Any]) -> dict[str, Any]:
    kernel = law["kernel_source"]
    wrapper = law["wrapper_source"]
    return {
        "law_id": law["law_id"],
        "native_type": law["native_type"],
        "dtype": law["dtype"],
        "output_dtype": law["output_dtype"],
        "m_alignment": law["m_alignment"],
        "alignment_basis": law["alignment_basis"],
        "weight_layout": law["weight_layout"],
        "required_input_dtypes": tuple(law["required_input_dtypes"]),
        "required_input_formats": tuple(law["required_input_formats"]),
        "required_output_format": law["required_output_format"],
        "kernel_source": dict(kernel),
        "wrapper_source": dict(wrapper),
        "source_path": kernel["path"],
        "source_sha256": kernel["sha256"],
        "source_revision": kernel["revision"],
        "wrapper_source_path": wrapper["path"],
        "wrapper_source_sha256": wrapper["sha256"],
        "wrapper_source_revision": wrapper["revision"],
        "wrapper_symbol": wrapper["symbol"],
        "scope": law["scope"],
        "legacy_image_digests": tuple(law["legacy_image_digests"]),
    }


_QBMM_ISSUE_RULE = _issue_law_payload(ISSUE_LAWS[0])


def _source_certifies_law(source: Mapping[str, Any], law: Mapping[str, Any]) -> bool:
    digest = image_digest(source.get("image_digest"))
    if source.get("implementation_verified") is True:
        verified = verified_implementation(source)
        if verified is None or verified.get("law_id") != law["law_id"]:
            return False
        return not _conflicts_with_law(digest, law)
    return (
        source.get("source_scope") == law["scope"]
        and digest in law["legacy_image_digests"]
    )


def _law_matches_tensor(
    law: Mapping[str, Any],
    native_type: Any,
    dtype: Any,
    output_dtype: Any,
    n: Any,
    k: Any,
    weight: tuple[int, ...],
    input_dtypes: tuple[str | None, ...],
    input_formats: list[str],
    output_formats: list[str],
) -> bool:
    alignment = law["m_alignment"]
    return (
        native_type == law["native_type"]
        and dtype == law["dtype"]
        and output_dtype == law["output_dtype"]
        and isinstance(n, int)
        and isinstance(k, int)
        and n > 0
        and k > 0
        and n % alignment == 0
        and k % alignment == 0
        and len(weight) == _MATRIX_INPUT_SLOTS
        and input_dtypes == law["required_input_dtypes"]
        and input_formats[:_MATRIX_INPUT_SLOTS] == list(law["required_input_formats"])
        and (not output_formats or output_formats[0] == law["required_output_format"])
    )


def certify_issue_law(
    native_type: Any,
    dtype: Any,
    output_dtype: Any,
    n: Any,
    k: Any,
    *,
    input_shapes_slots: tuple[tuple[int, ...] | None, ...] = (),
    input_dtypes_slots: tuple[str | None, ...] = (),
    input_formats: Any = None,
    output_formats: Any = None,
    source: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Certify issued work from implementation evidence or a legacy digest."""
    if not isinstance(source, Mapping) or not source:
        return None
    if len(input_shapes_slots) < _MATRIX_INPUT_SLOTS:
        return None
    if len(input_dtypes_slots) < _MATRIX_INPUT_SLOTS:
        return None
    weight, scale_shape, bias_shape = input_shapes_slots[1:_MATRIX_INPUT_SLOTS]
    if weight is None or len(weight) != _MATRIX_INPUT_SLOTS:
        return None
    if scale_shape is None or bias_shape is None:
        return None
    dtypes = input_dtypes_slots[:_MATRIX_INPUT_SLOTS]
    formats = [
        part.strip().upper() for part in str(input_formats or "").strip('"').split(";")
    ]
    outputs = [
        part.strip().upper() for part in str(output_formats or "").strip('"').split(";")
    ]
    for law in ISSUE_LAWS:
        if not _law_matches_tensor(
            law, native_type, dtype, output_dtype, n, k, weight, dtypes, formats, outputs
        ):
            continue
        if not _source_certifies_law(source, law):
            continue
        return {
            **_issue_law_payload(law),
            "deployment_image_id": source.get("image_digest"),
            "source_scope": source.get("source_scope"),
            "source_basis": source.get("basis"),
            "implementation_verified": bool(source.get("implementation_verified")),
            "law_id": law["law_id"],
        }
    return None


_issue_rule = certify_issue_law


def _issued_flops(
    logical_flops: int | None, m: int | None, issue: Mapping[str, Any] | None
) -> int | None:
    if logical_flops is None or m is None or issue is None:
        return None
    alignment = int(issue["m_alignment"])
    if alignment < 1 or m < 1:
        return None
    return int(logical_flops) // m * (((m + alignment - 1) // alignment) * alignment)


def _tensor_rows(
    value: Any, limit: int = _MAX_TENSOR_SLOTS
) -> tuple[tuple[int, ...] | None, ...]:
    text = str(value or "").strip().strip('"')
    if not text:
        return ()
    rows: list[tuple[int, ...] | None] = []
    for raw in text.split(";")[:limit]:
        cell = raw.strip().strip('"')
        if not cell or cell in {"N/A", "NULL", "None"}:
            rows.append(None)
            continue
        try:
            dims = tuple(int(part.strip()) for part in cell.split(","))
        except ValueError:
            return ()
        if not dims or any(dim < 0 for dim in dims):
            return ()
        rows.append(dims)
    return tuple(rows)


def _dtype_name(value: Any) -> str | None:
    first = str(value or "").strip().strip('"').split(";")[0].strip()
    if not first or first in {"N/A", "NULL", "None"}:
        return None
    key = first.removeprefix("DT_").lower()
    return _DTYPE_ALIASES.get(key)


def _dtype_slots(value: Any, limit: int = _MAX_TENSOR_SLOTS) -> tuple[str | None, ...]:
    text = str(value or "").strip().strip('"')
    if not text:
        return ()
    slots: list[str | None] = []
    for raw in text.split(";")[:limit]:
        slots.append(_dtype_name(raw))
    return tuple(slots)


def _nz_matches(w: tuple[int, ...], k: int, n: int) -> bool:
    """Exact Fractal-NZ ceiling tile of logical (K, N); outer/inner order coupled.

    ``n_tile`` is 16 for ordinary NZ and 32 for the MXFP8 32-element block view
    retained by the QBMM law fixture; outer axis order and inner tile order are
    always checked together, so equal-product swapped permutations stay invalid.
    """
    if len(w) != _MATRIX_INPUT_SLOTS or k <= 0 or n <= 0:
        return False
    return any(
        w in {
            ((k + kt - 1) // kt, (n + nt - 1) // nt, nt, kt),
            ((n + nt - 1) // nt, (k + kt - 1) // kt, kt, nt),
        }
        for kt in (_M_ALIGNMENT, _NZ_TILE_MX, _NZ_TILE_MAX)
        for nt in (_M_ALIGNMENT, _NZ_TILE_MX)
    )


def _parse_2d_matrix_shapes(
    input_shapes: Any, output_shapes: Any
) -> tuple[int | None, int | None, int | None, list[str], tuple[tuple[int, ...] | None, ...]]:
    inputs = _tensor_rows(input_shapes, limit=_MAX_TENSOR_SLOTS)
    outputs = _tensor_rows(output_shapes, limit=2)
    reasons: list[str] = []
    m = k = n = None
    if not inputs or inputs[0] is None:
        reasons.append("input_matrix_shape_not_parsed")
    elif len(inputs[0]) != 2:
        reasons.append("non_2d_matrix_shape_unsupported")
    else:
        m, k = int(inputs[0][0]), int(inputs[0][1])

    if len(inputs) < 2 or inputs[1] is None:
        reasons.append("weight_matrix_shape_not_parsed")

    if not outputs or outputs[0] is None:
        reasons.append("output_matrix_shape_not_parsed")
    elif len(outputs) > 1 or len(outputs[0]) != 2:
        if "non_2d_matrix_shape_unsupported" not in reasons:
            reasons.append("non_2d_matrix_shape_unsupported")
    else:
        out_m, n = int(outputs[0][0]), int(outputs[0][1])
        if m is not None and out_m != m:
            reasons.append("input_output_m_mismatch")

    if len(inputs) >= 2 and inputs[1] is not None:
        weight = inputs[1]
        if len(weight) not in {2, _MATRIX_INPUT_SLOTS}:
            if "non_2d_matrix_shape_unsupported" not in reasons:
                reasons.append("non_2d_matrix_shape_unsupported")
        elif m is not None and k is not None and n is not None:
            if len(weight) == 2 and weight not in {(k, n), (n, k)}:
                reasons.append("weight_matrix_shape_mismatch")
            elif len(weight) == _MATRIX_INPUT_SLOTS and not _nz_matches(weight, k, n):
                reasons.append("weight_matrix_shape_mismatch")

    return m, k, n, reasons, inputs


__all__ = [
    "ISSUE_LAWS",
    "R35_IMAGE_SHA",
    "R64_IMAGE_SHA",
    "_DTYPE_ALIASES",
    "_QBMM_ISSUE_RULE",
    "_dtype_name",
    "_dtype_slots",
    "_issue_rule",
    "_issued_flops",
    "_nz_matches",
    "_parse_2d_matrix_shapes",
    "_tensor_rows",
    "certify_issue_law",
    "deployment_source_identity",
    "image_digest",
    "verified_implementation",
]
