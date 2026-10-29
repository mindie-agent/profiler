"""Explicit body-workload alternatives for paged attention and recurrent GDN.

[Role] Reuse the independently declared model, block size and speculative width.
[Invariants] Query geometry never identifies a captured step, phase or layer.
  Context is a caller scenario, not cache capacity or an observed sequence value.
  Alternative declarations reuse events and must not be summed as new evidence.
[Timeouts & Locks] Finite metadata copies; no I/O, device calls or locks.
[Side-Effect Policy] Returns new case dictionaries without changing the baseline.
"""
from copy import deepcopy


def paged_variants(key, baseline):
    if key not in {"a3_qwen35", "a3_qwen36", "a5_qwen38"}:
        return []
    case = baseline["case"]
    runtime = case["runtime"]
    proposal_tokens = runtime["metadata"]["draft_proposal_tokens"]
    prompt_chunk = baseline["geometry"]["tokens"]
    scenarios = [("prefill", prompt_chunk, 0)]
    scenarios.extend(("decode", q, prompt_chunk) for q in (1, 1 + proposal_tokens))
    variants = []
    for phase, tokens, context in scenarios:
        value = deepcopy(baseline)
        suffix = f"{key}_paged_{phase}_q{tokens}"
        value.update(
            name=suffix + "-reference", declaration_key=suffix,
            variant="paged_body_geometry_conditional",
            geometry={"phase": phase, "tokens": tokens, "context": context, "sequences": 1},
        )
        selected_runtime = value["case"]["runtime"]
        selected_runtime.setdefault("attention_policy", {})["kv_storage"] = "paged"
        source = value["declaration_source"]
        source["runtime_overrides"] = {"attention_policy": {"kv_storage": "paged"}}
        source["workload_scenario"] = {
            "basis": "caller_declared_body_geometry",
            "query_width_source": (
                "baseline_prefill_chunk" if phase == "prefill" else
                "single_token_alternative" if tokens == 1 else
                "independent_recipe_draft_proposal_tokens_plus_one"
            ),
            "draft_proposal_tokens": proposal_tokens,
            "context_source": (
                "caller_declared_zero_context" if phase == "prefill" else
                "caller_selected_baseline_prefill_chunk_for_decode"
            ),
            "phase_observed": False, "context_observed": False,
            "draft_or_verify_identity_observed": False,
            "cache_capacity_used_as_active_work": False,
            "binary_dispatch_verified": False,
            "comparison_scope": "body_work_only; does_not_add_draft_model_cost",
        }
        source["source_evidence"] = {
            **(source.get("source_evidence") or {}),
            "paged_attention": {
                "frontend_commit": "b355d9f6",
                "interface": "attention_tensor_view.kind=paged_gqa",
                "packed_width_source": "independent_local_kv_heads_times_head_dim",
                "block_size_source": "runtime.kv_block_size",
                "source_path": "vllm_ascend/attention/attention_v1.py",
                "source_symbol": "_get_fia_params",
                "capture_binary_identity_verified": False,
            },
        }
        variants.append(value)
    return variants
