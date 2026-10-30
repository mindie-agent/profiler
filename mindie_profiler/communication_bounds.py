"""Structural evidence for a padded hidden reduce-scatter consumer.

[Role] Verify the captured projection/padding/AttnRes tensor chain.
[Invariants] Declared TP and every native tensor boundary must agree; launch
  names alone do not bind a communication summary to a physical task.
[Timeouts & Locks] Bounded in-memory traversal of one closed forward; no locks.
[Side-Effect Policy] Read-only event inspection; no timestamp rewriting or I/O.
"""
from .normalized import row_from_event


def padded_hidden_consumer(rows, producer_index, consumer_index, hidden, tp, matrix_types):
    """Return shape evidence for TP-sharded AttnRes, or no proven chain."""
    pad, consumer = rows[producer_index], rows[consumer_index]
    if (tp <= 1 or pad.kind != "PadV3" or not pad.inputs or not pad.outputs
            or len(pad.inputs) != 3 or len(pad.outputs) != 1
            or len(pad.inputs[0]) != 2 or len(pad.outputs[0]) != 2
            or pad.inputs[0][1] != hidden or pad.outputs[0][1] != hidden
            or pad.inputs[1:] != ((4,), ()) or consumer.kind != "AttnResFwd"):
        return None
    original_rows, padded_rows = pad.inputs[0][0], pad.outputs[0][0]
    if (original_rows <= 0 or padded_rows <= original_rows
            or padded_rows != ((original_rows + tp - 1) // tp) * tp):
        return None
    local_rows = padded_rows // tp
    local, parameter = (local_rows * hidden,), (hidden,)
    if (consumer.inputs != (local, local, parameter, parameter, local, parameter)
            or consumer.outputs != (local, local, local)):
        return None
    # MemSet initializes the pad destination; it is not the hidden producer.
    prior = producer_index - 1
    while prior >= 0 and rows[prior].kind == "MemSet":
        prior -= 1
    if prior < 0:
        return None
    projection = rows[prior]
    if (projection.kind not in matrix_types or projection.outputs != (pad.inputs[0],)
            or projection.event.end_ns > pad.event.start_ns):
        return None
    cores = {"AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "MIX_AIV"}
    following = next((row for row in rows[consumer_index + 1:]
                      if row.event.core in cores), None)
    if (following is None or following.kind not in matrix_types
            or not following.inputs or following.inputs[0] != (local_rows, hidden)
            or consumer.event.end_ns > following.event.start_ns):
        return None
    chain = (projection, pad, consumer, following)
    if any((row.event.device_id, row.event.rank_id, row.event.stream_id) !=
           (pad.event.device_id, pad.event.rank_id, pad.event.stream_id) for row in chain):
        return None
    if any(row.event.task_id in {"", "N/A", "NA", "None"} or row.event.core not in cores
           for row in chain):
        return None
    projected, padded, consumed, follow = (row_from_event(row.event) for row in chain)
    dtype = projected.output_dtypes
    if (dtype != ("DT_BF16",) or padded.input_dtypes != ("DT_BF16", "INT32", "DT_BF16")
            or padded.output_dtypes != dtype or consumed.input_dtypes != dtype * 6
            or consumed.output_dtypes != dtype * 3 or follow.input_dtypes[0:1] != dtype
            or projected.output_formats != ("ND",) or padded.input_formats != ("ND",) * 3
            or padded.output_formats != ("ND",) or consumed.input_formats !=
            ("ND", "NCL", "ND", "ND", "ND", "ND") or consumed.output_formats != ("ND",) * 3):
        return None
    return {
        "basis": "captured_projection_pad_attnres_tp_shard_chain",
        "declared_tp": tp, "projection_output_shape": list(pad.inputs[0]),
        "padded_hidden_shape": list(pad.outputs[0]),
        "consumer_flat_hidden_shape": list(local), "local_hidden_rows": local_rows,
        "projection_locator": projection.event.locator, "padding_locator": pad.event.locator,
        "following_hidden_matrix_locator": following.event.locator,
        "tensor_identity_observed": False,
    }
