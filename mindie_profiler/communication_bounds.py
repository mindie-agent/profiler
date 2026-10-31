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


def dual_stream_moe_hidden_consumer(rows, summary_index, consumer_index, hidden, tp, matrix_types):
    """Verify dual-stream shared-expert + routed-expert merge into ForeachAddList -> HcPost -> HcPre -> RmsNorm."""
    summary, consumer = rows[summary_index].event, rows[consumer_index]
    if (tp <= 1 or not consumer.inputs or len(consumer.inputs[0]) != 2
            or consumer.inputs[0][1] != hidden):
        return None
    m_rows = consumer.inputs[0][0]
    if m_rows <= 0 or m_rows % tp != 0:
        return None
    missing = {"", "N/A", "NA", "None"}
    cores = {"AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "MIX_AIV"}
    c_ev = consumer.event
    if c_ev.core not in cores or c_ev.task_id in missing or c_ev.stream_id in missing:
        return None
    window_before = [r for r in rows[max(0, summary_index - 10):summary_index]
                     if r.event.core in cores and r.event.task_id not in missing
                     and r.event.stream_id not in missing
                     and (r.event.device_id, r.event.rank_id) == (c_ev.device_id, c_ev.rank_id)
                     and r.event.end_ns <= summary.start_ns]
    combine = next((r for r in reversed(window_before)
                    if r.event.stream_id == c_ev.stream_id
                    and any(tok in r.kind for tok in ("DistributeCombine", "Unpermute", "FinalizeRouting"))
                    and r.outputs and r.outputs[0] in {(m_rows // tp, hidden), (m_rows, hidden)}), None)
    shared = next((r for r in reversed(window_before)
                   if r.kind in matrix_types and r.outputs and r.outputs[0] == (m_rows, hidden)), None)
    if combine is None or shared is None:
        return None
    window_after = [r for r in rows[summary_index + 1:consumer_index]
                    if r.event.core in cores and r.event.stream_id == c_ev.stream_id
                    and (r.event.device_id, r.event.rank_id) == (c_ev.device_id, c_ev.rank_id)
                    and summary.start_ns < r.event.start_ns <= c_ev.start_ns]
    if any(r.event.task_id in missing for r in window_after
           if "ForeachAdd" in r.kind or r.kind in {"HcPost", "HcPre"}):
        return None
    add_op = next((r for r in window_after
                   if "ForeachAdd" in r.kind and r.inputs and r.inputs[:2] == ((m_rows, hidden), (m_rows, hidden))
                   and r.outputs == ((m_rows, hidden),)), None)
    hc_post = next((r for r in window_after
                    if r.kind == "HcPost" and r.inputs and r.outputs and len(r.inputs) >= 2
                    and r.inputs[0] in {(m_rows, hidden), (1, m_rows, hidden)}
                    and len(r.inputs[1]) >= 3 and r.inputs[1][-3] == m_rows
                    and r.inputs[1][-2] >= 2 and r.inputs[1][-1] == hidden
                    and r.outputs == (r.inputs[1],)), None)
    hc_pre = next((r for r in window_after
                   if r.kind == "HcPre" and r.inputs and r.outputs and hc_post is not None
                   and r.inputs[0] == hc_post.outputs[0][-3:]
                   and r.outputs[0] == (m_rows, hidden)), None)
    if (add_op is None or hc_post is None or hc_pre is None
            or not (add_op.event.end_ns <= hc_post.event.start_ns
                    and hc_post.event.end_ns <= hc_pre.event.start_ns
                    and hc_pre.event.end_ns <= c_ev.start_ns)):
        return None
    added, posted, prepped = (row_from_event(r.event) for r in (add_op, hc_post, hc_pre))
    if (added.input_dtypes[:2] != ("DT_BF16", "DT_BF16") or added.output_dtypes != ("DT_BF16",)
            or posted.input_dtypes[:2] != ("DT_BF16", "DT_BF16") or posted.output_dtypes != ("DT_BF16",)
            or prepped.input_dtypes[:1] != ("DT_BF16",) or prepped.output_dtypes[:1] != ("DT_BF16",)):
        return None
    producer = shared if shared.event.end_ns >= combine.event.end_ns else combine
    return {
        "producer": producer,
        "evidence": {
            "basis": "captured_dual_stream_moe_foreach_add_mhc_norm_chain",
            "declared_tp": tp,
            "merged_hidden_shape": [m_rows, hidden],
            "mhc_stream_shape": list(hc_post.outputs[0][-3:]),
            "routed_combine_shape": list(combine.outputs[0]),
            "routed_combine_locator": combine.event.locator,
            "shared_projection_locator": shared.event.locator,
            "foreach_add_locator": add_op.event.locator,
            "hc_post_locator": hc_post.event.locator,
            "hc_pre_locator": hc_pre.event.locator,
            "tensor_identity_observed": False,
        },
    }
