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
from types import SimpleNamespace


def local_expert_rows(query_rows, top_k, experts, ep, routing=None):
    """Return generated grouped rows for one declared routing policy.

    Sim's balanced policy splits ``query_rows * top_k`` assignments into a
    forced integer ledger, then the local-expert caller selects one contiguous
    bank. Non-balanced probability-moment routing delegates to Sim's
    ``RoutingPolicy.local`` straggler-rank expectation (falling back to
    ``ceil(query_rows * top_k / ep)`` when ``ep <= 1`` or Sim is absent).
    """
    assignments = query_rows * top_k
    if routing == {"policy": "balanced"}:
        bank = experts // ep
        base, remainder = divmod(assignments, experts)
        return bank * base + min(remainder, bank)
    if ep > 1:
        try:
            from mindie_sim.prediction.operators.moe_transport.moe_callers import RoutingPolicy
            model = SimpleNamespace(expert_routing=None)
            layer = SimpleNamespace(
                num_experts=experts, top_k=top_k, expert_placement=None,
                redundant_experts=0, eplb_slots=None)
            parallel = SimpleNamespace(
                ep=ep, tp=ep, dp=1, eplb=False,
                eplb_redundant_experts=0, redundant_experts=0)
            rows, _ = RoutingPolicy().local(model, layer, parallel, query_rows)
            return int(ceil(rows))
        except ImportError:
            pass
    return ceil(assignments / ep)


def routing_basis(routing):
    """Name the declared policy without promoting it to native evidence."""
    if routing == {"policy": "balanced"}:
        return "declared_balanced_integer_ledger; not_native_force_eplb"
    return "declared_probability_moments_or_default; not_native_force_eplb"
