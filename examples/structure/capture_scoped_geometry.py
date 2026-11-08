"""Declared local-expert row geometry for one scoped generated graph.

[Role] Derive the grouped-matrix rows of the representative contiguous local
  expert bank from declared query geometry, never from the generated operator.
[Invariants] A rank-global average assignment is not a local bank row count.
  Only the declared balanced integer ledger or the uniform probability-moment
  rank average is returned; observed timing and generated shapes never enter.
  Balanced here means the raw's declared routing policy. The four 20261031 E48
  commands contain no force-EPLB literal and inherit balanced from the archived
  template, but that capture-specific origin is not inferred for other raws and
  is not a native force-EPLB confirmation.
[Timeouts & Locks] O(1) integer arithmetic; no I/O, locks or device work.
[Side-Effect Policy] Pure function over declared integers.
"""
from math import ceil


def local_expert_rows(query_rows, top_k, experts, ep, routing=None):
    """Return generated grouped rows for one declared routing policy.

    Sim's balanced policy splits ``query_rows * top_k`` assignments into a
    forced integer ledger, then the local-expert caller selects one contiguous
    bank. Uniform probability moments instead keep the rank average
    ``ceil(query_rows * top_k / ep)``. Both quantities are exact declarations,
    not tolerance windows around a global division.
    """
    assignments = query_rows * top_k
    if routing == {"policy": "balanced"}:
        bank = experts // ep
        base, remainder = divmod(assignments, experts)
        return bank * base + min(remainder, bank)
    return ceil(assignments / ep)


def routing_basis(routing):
    """Name the declared policy without promoting it to native evidence."""
    if routing == {"policy": "balanced"}:
        return "declared_balanced_integer_ledger; not_native_force_eplb"
    return "declared_probability_moments_or_default; not_native_force_eplb"
