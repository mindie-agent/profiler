"""Public facade for original zero-shot client-request source and P6/P7 projection.

The source and projection live in cohesive modules:
  * ``zero_shot_client_source``: original JSON/argv readers, launch-ordinal TTFT
    identity, stream joins, producer/rack metadata.
  * ``zero_shot_client_projection``: per-request P7 declarations, P6 interface,
    summaries and CLI.

Import from this facade to keep the established API.
"""
from __future__ import annotations

from zero_shot_client_source import (
    DEFAULT_SOURCE_ROOTS,
    P6_SCHEMA,
    P7_SCHEMA,
    SCHEMA_VERSION,
    ClientCapture,
    ClientDeclaration,
    ClientRequest,
    ClientStream,
    iter_original_rows,
    iter_original_rows_with_sha,
)
from zero_shot_client_capture import (
    client_capture,
    iter_client_captures,
    iter_client_captures_from_jsonl,
    iter_client_requests,
)
from zero_shot_client_projection import (
    iter_p6_requests,
    iter_prediction_declarations,
    p6_interface,
    prediction_declaration,
    summarize_client_requests,
)

__all__ = [
    "DEFAULT_SOURCE_ROOTS", "P6_SCHEMA", "P7_SCHEMA", "SCHEMA_VERSION",
    "ClientCapture", "ClientDeclaration", "ClientRequest", "ClientStream", "client_capture",
    "iter_client_captures", "iter_client_captures_from_jsonl",
    "iter_client_requests", "iter_original_rows", "iter_original_rows_with_sha",
    "iter_p6_requests", "iter_prediction_declarations", "p6_interface",
    "prediction_declaration", "summarize_client_requests",
]


def _main() -> int:
    from zero_shot_client_projection import _main as projection_main
    return projection_main()


if __name__ == "__main__":
    raise SystemExit(_main())
