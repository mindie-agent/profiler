"""Zero-shot piecewise validation over every retained Profiling capture.
[Role] Load historical captures, fixtures and A5 multi-node fleet measured
  JSON / ``request_summary.csv`` / ``kernel_details.csv(.gz)`` pairs; compare
  per-step operator / subgraph / model / service timings with the structural
  piecewise compiler.
[Invariants] Prediction consumes only ``CellSpec``; measured fields stay in
  ``MeasuredCell`` and are read after the prediction is frozen. Only
  ``mindie_sim.prediction.subgraphs`` + ``piecewise`` are used, never
  ``service_regimes``. Every L1-L4 miss keeps its per-step distribution.
[Timeouts & Locks] Bounded local reads and deterministic arithmetic; no
  network, device, subprocess, sleep, lock or background work.
[Side-Effect Policy] Read-only by default; the CLI writes the baseline summary
  to stdout and only writes trace cache files when ``--trace-cache`` is given.
"""
from __future__ import annotations; import argparse, copy, csv, gzip, hashlib, json, math, os, pickle, re, sys; from collections import Counter, defaultdict; from dataclasses import dataclass, field, replace
from functools import lru_cache; from types import MappingProxyType; from pathlib import Path; from statistics import mean, median; from typing import Any, Mapping, Sequence; ROOT = Path(__file__).resolve().parents[2]
try: from .measured_supply import supply_key, apply_supply; from .fleet_campaign_case import glm51_source_case
except ImportError: from measured_supply import supply_key, apply_supply; from fleet_campaign_case import glm51_source_case
CASES_DIR = ROOT / 'examples' / 'structure' / 'cases'; PROFILES_DIR = ROOT / 'examples' / 'structure' / 'profiles'; FIXTURES_DIR = ROOT / 'tests' / 'fixtures'; CASES_REGISTRY = ROOT / 'examples' / 'structure' / 'cases.json'
WORKSTREAM_ROOTS = (Path('/Users/maoxx241/code/mindie-agent/.workstreams/a5-multinode-fleet-rack08-20261107'), Path('/Users/maoxx241/code/mindie-agent/.workstreams/a5-multinode-fleet-rack06-20261107')); _native_forecast = __import__((__package__ + '.zero_shot_native_forecast') if __package__ else 'zero_shot_native_forecast', fromlist=['aggregate']).aggregate
try: from .zero_shot_public_consumer import (_PUBLIC_CACHE, _public_consume, _public_graph_projection, _public_request_placement,
    _moe_comparison_subgraphs, _native_source_status, _public_selected_replica, _public_tokens_context, _selected_moe_comm, _serving_l4, _subgraph_charge, public_supply_key)
except ImportError: from zero_shot_public_consumer import (_PUBLIC_CACHE, _public_consume, _public_graph_projection, _public_request_placement,
    _moe_comparison_subgraphs, _native_source_status, _public_selected_replica, _public_tokens_context, _selected_moe_comm, _serving_l4, _subgraph_charge, public_supply_key)
try: from .zero_shot_source_binding import _bind_original_deployment, _header_alias, _raw_case_base, _sanitize_forecast_service_rules, apply_source_resolution, resolve_and_apply_source, resolve_source_file
except ImportError: from zero_shot_source_binding import _bind_original_deployment, _header_alias, _raw_case_base, _sanitize_forecast_service_rules, apply_source_resolution, resolve_and_apply_source, resolve_source_file
try: from .zero_shot_kernel_trace import (KernelTrace, _MOE_TOKENS, _NORM_TOKENS, _ROPE_TOKENS, _classify_cached, _elementwise_class, _has,
    _count_mode, _strip_hccl_launch, base_kernel_name, classify_kernel, load_kernel_trace, operator_mechanism, subgraph_family)
except ImportError: from zero_shot_kernel_trace import (KernelTrace, _MOE_TOKENS, _NORM_TOKENS, _ROPE_TOKENS, _classify_cached, _elementwise_class, _has,
    _count_mode, _strip_hccl_launch, base_kernel_name, classify_kernel, load_kernel_trace, operator_mechanism, subgraph_family)
#: Source-contract marker: the report projection publishes this field and the
#: validator must remain recognisably measurement-blind at its own boundary.
_MEASUREMENT_BLIND_FIELD = 'measurement_blind'
LAYOUTS = ('out', 'runs'); SUBGRAPHS = ('attention', 'moe', 'norm_residual', 'hyperconnection'); ERROR_THRESHOLD = 0.1
MECHANISMS = ('gemm', 'attention', 'elementwise_quant', 'collective', 'kv_cache', 'activation', 'norm_residual', 'rope', 'moe_router', 'moe_grouped', 'indexer', 'gdn_linear_attn', 'kda_linear_attn', 'hyperconnection')
_REQUIRED_BENCH = tuple((('L1', name) for name in MECHANISMS)) + tuple((('L2', name) for name in SUBGRAPHS)) + (('L3', 'decode_step_trace'), ('L3', 'prefill_step_trace'), ('L4', 'decode_step_tpot'), ('L4', 'prefill_step_ttft'))
_MECH_LABELS = {'gemm': 'Cube GEMM (Cube 矩阵乘)', 'attention': 'Attention Core / FlashAttention-MLA (注意力核心计算)', 'elementwise_quant': 'AIV Vector & Layout (AIV 向量／量化／布局转换)', 'collective': 'Collective Communication (HCCL/HCOM 集合通信)', 'kv_cache': 'KV Cache & State Access (KV 缓存与状态访问)', 'activation': 'Activation Function (激活函数)', 'norm_residual': 'Normalization & Residual (归一化与残差)', 'rope': 'Rotary Position Embedding / RoPE (旋转位置编码)', 'moe_router': 'MoE Router & Top-K (MoE 路由与 Top-K)', 'moe_grouped': 'Grouped GEMM / Routed Expert FFN (分组矩阵乘／路由专家前馈)', 'indexer': 'Attention Indexer (注意力索引器)', 'gdn_linear_attn': 'Gated DeltaNet Linear Attention (门控 DeltaNet 线性注意力)', 'kda_linear_attn': 'Kimi Delta Attention (Kimi Delta 线性注意力)', 'hyperconnection': 'Hyper-Connections (超连接)'}
_SUBGRAPH_LABELS = {'attention': 'Attention / Indexer Subgraph (注意力与索引器子图)', 'moe': 'MoE Subgraph (混合专家子图)', 'norm_residual': 'Normalization & Residual Subgraph (归一化与残差子图)', 'hyperconnection': 'Hyper-Connections Subgraph (超连接子图)'}
_STEP_LABELS = {'decode_step_trace': 'Decode Per-Step Latency — Kernel Trace (Decode 单步耗时，ms/step)', 'decode_step_tpot': 'Decode Per-Step Latency — Service TPOT (Decode 单步耗时 TPOT，ms/step)', 'prefill_step_trace': 'Prefill Per-Step Latency — Kernel Trace (Prefill 单步耗时，ms/step)', 'prefill_step_ttft': 'Prefill Per-Step Latency — Service TTFT (Prefill 单步耗时 TTFT，ms/step)'}
_DIAGNOSIS_LABELS = {'confirmed_structural_gap': 'Unmodeled Operation / Boundary Mismatch (未建模算子或边界偏差)', 'fusion_boundary': 'Fusion Boundary Mismatch (算子融合边界偏差)', 'collective_skew': 'Collective Communication Skew / Latency (集合通信慢卡倾斜或握手延迟)', 'tiling_wave_step': 'Tile / Core Wave Quantization (分块与核波次量化效应)', 'mte2_granule_amplification': 'Memory Alignment Amplification (访存粒度对齐放大)'}
_PREFILL_MARKERS = ('prepare_prefill_inputs', 'embedding_gatherv2')
_FUSED_TARGETS = {'attention': ('fusedinferattention', 'mixed_quant_sparse_flash_mla', 'mlaprolog', 'attnresfwd', 'split_qkv'), 'gemm': ('groupedmatmulswiglu', 'mlaprolog', 'swiglu', 'attnresfwd', 'hcpre', 'hcpost', 'split_qkv'), 'indexer': ('quantlightningindexer', 'lightningindexer'), 'gdn_linear_attn': ('fused_gdn', 'layer_norm_gated', 'causalconv', 'recurrentgateddeltarule', 'gateddelta'), 'kda_linear_attn': ('fused_kda', 'recurrentkda', 'chunkkda', 'chunkfwd'), 'moe_grouped': ('groupedmatmulswiglu', 'swiglu'), 'moe': ('groupedmatmulswiglu', 'swiglu', 'moegating'), 'norm_residual': ('addrmnorm', 'foreachaddlist', 'muls_add'), 'hyperconnection': ('hcpre', 'hcpost')}
_TARGET_CLASSES = {'attention': {'attention'}, 'indexer': {'indexer'}, 'gemm': {'gemm'}, 'gdn_linear_attn': {'gdn_linear_attn'}, 'kda_linear_attn': {'kda_linear_attn'}, 'moe_grouped': {'moe_grouped'}, 'moe': {'moe_grouped', 'moe_router', 'collective', 'activation'}, 'norm_residual': {'norm_residual'}, 'hyperconnection': {'hyperconnection'}}
MODEL_PROFILES = (('glm53flash', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3-Flash'), ('glm53w4a4c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W4A4C8'), ('glm53_w4a4', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W4A4C8'), ('glm53w8a8c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8C8-MXFP8'), ('glm53_w8a8c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8C8-MXFP8'), ('glm53', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8-MXFP8'), ('glm52', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.2/W4A4C8'), ('glm51', 'decode-a5_glm51_mxfp4_dp16tp1ep16_pf1k.json', 'GLM-5.1/W4A4C8'), ('minimax_m31', 'decode-a5_qwen38_highconc_c4.json', 'MiniMax-M3.1-Flash'), ('minimax', 'decode-a5_qwen38_highconc_c4.json', 'MiniMax-M3'), ('dsv41_kvbf16', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash/KV-BF16'), ('dsv41', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash'), ('v41', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash'), ('dsv4flash_0731', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V4-Flash-0731'), ('v4flash', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V4-Flash'), ('v4f', 'prefill-v4f-prefill-p4096.json', 'DeepSeek-V4-Flash'), ('v4pro', 'prefill-v4pro-prefill-p4096.json', 'DeepSeek-V4-Pro'), ('dsv4', 'prefill-v4pro-prefill-p4096.json', 'DeepSeek-V4-Pro'), ('dsv32prune', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V3.2-Prune-3L'), ('dsv32', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V3.2'), ('v2_lite', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V2-Lite'), ('k3', 'decode-a5_kimi_k3_p32768_c1.json', 'Kimi-K3'), ('kimi', 'decode-a5_kimi_k3_p32768_c1.json', 'Kimi-K3'), ('qwen38_flash', 'decode-a5_qwen38_highconc_c4.json', 'Qwen3.8-Flash-Next'), ('qwen38', 'decode-a5_qwen38_highconc_c4.json', 'Qwen3.8-27B'), ('qwen36_35b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3.6-35B-A3B'), ('qwen36', 'decode-a5_qwen36_highconc_c4.json', 'Qwen3.6-27B'), ('qwen35-397b', 'decode-qwen35-397b-a3-tp16-c48.json', 'Qwen3.5-397B-A17B'), ('qwen35', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3.5-35B-A3B'), ('qwen3_30b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3-30B-A3B'), ('qwen3-30b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3-30B-A3B'), ('gemma4_26b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Gemma-4-26B-A4B'), ('gemma4_31b', 'decode-a5_qwen38_highconc_c4.json', 'Gemma-4-31B'), ('step5', 'decode-a5_qwen38_highconc_c4.json', 'Step-5-Preview'), ('l8_e16_k2', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'Synthetic-MoE-L8-E16-K2'))
@dataclass(frozen=True)
class CellSpec:
    cell_id: str; dataset: str; phase: str; model_case: Path | None; model_label: str; prompt_tokens: int; concurrency: int; max_tokens: int; tp: int; dp: int; ep: int; pp: int; graph_buckets: tuple[int, ...] = (); graph_bucket: int = 0; notes: tuple[str, ...] = (); sequences_per_replica: int = 0; tokens_per_sequence: int = 0; synthetic_layers: int = 0; synthetic_experts: int = 0; synthetic_topk: int = 0; source_config: Path | None = None; source_config_sha256: str = ''; source_deploy_sha256: str = ''; source_weight_dir: Path | None = None; source_case_dir: Path | None = None; source_header_archive: Path | None = None; require_source: bool = False; source_reject_reason: str = ''; source_file_sha256: str = ''; source_origin: str = ''; source_binding: Mapping[str, Any] = field(default_factory=dict, compare=False, repr=False)
    def prediction_key(self) -> tuple:
        _binding_fp = hashlib.sha256(json.dumps(_plain_source_value(self.source_binding), sort_keys=True, default=str).encode()).hexdigest() if self.source_binding else ''
        return (self.dataset, str(self.model_case or ''), self.model_label, self.phase, self.prompt_tokens, self.concurrency, self.max_tokens, self.tp, self.dp, self.ep, self.pp, self.graph_buckets, self.graph_bucket, tuple(sorted(self.notes)), self.sequences_per_replica, self.tokens_per_sequence, self.synthetic_layers, self.synthetic_experts, self.synthetic_topk, str(self.source_config or ''), self.source_config_sha256, self.source_deploy_sha256, self.source_file_sha256, self.source_origin, str(self.source_weight_dir or ''), str(self.source_case_dir or ''), str(self.source_header_archive or ''), self.require_source, self.source_reject_reason, _binding_fp, _structure_fingerprint(self))
@dataclass(frozen=True)
class KernelTrace:
    duration_us: float; by_class: Mapping[str, float]; by_name: Mapping[str, float]; counts: Mapping[str, int] = field(default_factory=dict, compare=False)
    step_us: tuple[float, ...] = field(default_factory=tuple, compare=False); segments: tuple[Any, ...] = field(default_factory=tuple, compare=False)
    union_duration_us: float = field(default=0.0, compare=False); forward_span_us: float = field(default=0.0, compare=False); incomplete: bool = field(default=False, compare=False); incomplete_reason: str = field(default='', compare=False)
@dataclass(frozen=True)
class MeasuredCell:
    spec: CellSpec; kernel_paths: tuple[Path, ...]; trace: KernelTrace | None; ttft_ms: float | None; tpot_ms: float | None; step_trace_ms: float | None; decode_steps: int; success: bool; failure: str = ''; trace_quality: str = 'ok'; request_tokens: int = 0; source_conflict: str = ''; source_measured: str = ''
@dataclass(frozen=True)
class OperatorRow:
    name: str; kind: str; mechanism: str; subgraph: str; duration_ms: float; count: int; regime: tuple[tuple[str, int], ...]; dominant_pipe: str; formula: str; segment: int; cost: Any = field(compare=False, repr=False); native_call: Any = field(default=None, compare=False, repr=False); native_occurrence: Any = field(default=None, compare=False, repr=False); phase: str = ""
    @property
    def total_ms(self) -> float: return self.duration_ms * self.count
    @property
    def guard_text(self) -> str: return ';'.join((f'{k}={v}' for k, v in self.regime)) if self.regime else 'no_discrete_guard'
@dataclass(frozen=True)
class Prediction:
    cell_id: str; model_label: str; layers: int; per_layer: Mapping[str, float]; subgraphs: Mapping[str, float]; body_ms: float; ttft_ms: float | None; dual_moe_ms: float | None; rows: tuple[OperatorRow, ...]; notes: tuple[str, ...] = (); decode_body_ms: float = 0.0; prefill_body_ms: float = 0.0; formal_point: bool = True; partial_targets: tuple[str, ...] = (); native_status: Mapping[str, Any] = field(default_factory=dict); step_ms: float | None = None; public_basis: str = ''; public_events: int = 0; source_binding: Mapping[str, Any] = field(default_factory=dict, compare=False, repr=False); routing_status: str = ''
@dataclass(frozen=True)
class Comparison:
    level: str; target: str; mechanism: str; predicted_ms: float; measured_ms: float; operator: str; guard: str; dominant_pipe: str; formula: str; segment: int; uncancelled_ms: float = 0.0; cell_id: str = ''; step_details: tuple[tuple[int, float, float, float], ...] = (); conditional: bool = False
    @property
    def signed_error(self) -> float:
        return math.nan if not (math.isfinite(self.predicted_ms) and math.isfinite(self.measured_ms)) else (math.inf if self.predicted_ms > 0 else 0.0) if self.measured_ms <= 0 else (self.predicted_ms - self.measured_ms) / self.measured_ms
    @property
    def unsigned_error(self) -> float: return abs(self.signed_error)
@dataclass(frozen=True)
class Diagnosis:
    level: str; target: str; mechanism: str; error: float; unsigned_error: float; physical_mechanism: str; operator: str; segment: int; dominant_pipe: str; guard: str; formula_term: str; required_fix: str; evidence: str
_CASE_LAYERS: dict[str, int] = {}; _CASE_MOE: dict[str, bool] = {}; _PUBLIC_CONSUMED_CACHE: dict[Any, Any] = {}; _SOURCE_GROUP_CACHE: dict[Any, Any] = {}; _COMPILED_MODELS: dict[Any, Any] = {}; _COMPILED_HARDWARE: dict[Any, str] = {}; _COMPILED_DRAFT: dict[Any, bool] = {}; _COMPILED_SELECTOR: dict[Any, tuple[int, int, int, tuple[int, ...]]] = {}; _AGG_CACHE: dict[Any, Any] = {}; _DSPARK_KEY = 'kimi-k3-dspark-block5'; _A5_MACH_FILE = 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json'
_CATALOG_MAP = (('GLM-5.1', 'glm-5.1'), ('GLM-5.2', 'glm-5.2'), ('GLM-5.3/', 'glm-5.3'), ('DeepSeek-V3.2-Prune', 'deepseek-v3.2-prune-3l'), ('DeepSeek-V3.2', 'deepseek-v3.2'), ('DeepSeek-V4-Flash-0731', 'deepseek-v4-flash-0731'), ('DeepSeek-V2-Lite', 'deepseek-v2-lite'), ('Kimi-K3-DSpark-Block5', 'kimi-k3-dspark-block5'), ('MiniMax-M3', 'minimax-m3'), ('Qwen3-30B-A3B', 'qwen3-30b-a3b'), ('Qwen3.8-Flash-Next', 'qwen3-next-80b-a3b'))
_MODEL_CFGS: dict[str, dict[str, Any]] = {'Gemma-4-26B-A4B': {'model_type': 'gemma4', 'num_hidden_layers': 30, 'hidden_size': 2816, 'num_attention_heads': 16, 'num_key_value_heads': 8, 'head_dim': 256, 'vocab_size': 262144, 'moe_intermediate_size': 704, 'shared_expert_intermediate_size': 2112, 'n_routed_experts': 128, 'num_experts_per_tok': 8, 'n_shared_experts': 1, 'layer_types': (['sliding_attention'] * 5 + ['full_attention']) * 5}, 'Gemma-4-31B': {'model_type': 'gemma4', 'num_hidden_layers': 60, 'hidden_size': 5376, 'num_attention_heads': 32, 'num_key_value_heads': 16, 'head_dim': 256, 'intermediate_size': 21504, 'vocab_size': 262144, 'layer_types': (['sliding_attention'] * 5 + ['full_attention']) * 10}, 'MiniMax-M3.1-Flash': {'model_type': 'minimax_m31', 'num_hidden_layers': 36, 'hidden_size': 4096, 'num_attention_heads': 64, 'num_key_value_heads': 8, 'head_dim': 128, 'vocab_size': 200064, 'moe_intermediate_size': 1920, 'n_routed_experts': 256, 'num_experts_per_tok': 8, 'n_shared_experts': 1, 'shared_expert_intermediate_size': 1920, 'layer_types': ['full_attention'] * 36}, 'Step-5-Preview': {'model_type': 'step5', 'num_hidden_layers': 36, 'hidden_size': 4096, 'num_attention_heads': 64, 'num_key_value_heads': 8, 'head_dim': 128, 'vocab_size': 151936, 'moe_intermediate_size': 1280, 'shared_expert_intermediate_size': 1280, 'n_routed_experts': 256, 'num_experts_per_tok': 8, 'n_shared_experts': 1, 'layer_types': ['full_attention'] * 36}}
def _overlay_machine(spec: CellSpec, raw: dict[str, Any]) -> dict[str, Any]:
    machine = copy.deepcopy(raw.get('machine') or {}); need = max(1, spec.dp * max(1, spec.tp) * max(1, spec.pp), _ep_ranks(spec))
    if int(machine.get('num_devices') or 0) >= need: return raw
    machine['num_devices'] = need; machine['ranks_per_node'] = min(8, need); links = []
    for host in range(max(1, (need + 7) // 8)): links.append({'name': f'ub-host{host}', 'channel': 'd2d_intra_node', 'capacity_gbps': 392, 'latency_us': 1.8, 'members': list(range(host * 8, min(need, (host + 1) * 8))), 'semantics': 'mesh', 'protocol': 'UB_MESH'})
    if need > 8: links.append({'name': 'roce-inter-node', 'channel': 'd2d_inter_node', 'capacity_gbps': 200, 'latency_us': 5.0, 'members': list(range(need)), 'semantics': 'switched', 'protocol': 'RoCEv2_400G_x4'})
    machine['links'] = links; dev = dict(machine.get('device') or {}); rates = dict(dev.get('rates') or {}); rates.setdefault('link', 392000000000.0); rates.setdefault('link_hccs', 392000000000.0); rates.setdefault('link_roce', 200000000000.0); dev['rates'] = rates; machine['device'] = dev; return {**raw, 'machine': machine}
def _overlay_cohort(spec: CellSpec, raw: dict[str, Any]) -> dict[str, Any]:
    raw = _overlay_machine(spec, raw); cohort = _load_json(_cohort_case(spec)) if _cohort_case(spec) is not None else None
    if not isinstance(cohort, Mapping): return raw
    rt = dict(raw.get('runtime') or {}); rt.update({'tp': spec.tp, 'dp': spec.dp, 'ep': _ep_ranks(spec), 'pp': spec.pp})
    for key in ('max_num_batched_tokens', 'max_num_seqs', 'max_model_len', 'enable_chunked_prefill'):
        if isinstance(cohort.get(key), (int, float, bool)): rt[key] = cohort[key]
    comp = cohort.get('compilation_config') if isinstance(cohort.get('compilation_config'), Mapping) else {}
    if comp.get('cudagraph_capture_sizes'): rt['graph_buckets'] = list(comp['cudagraph_capture_sizes'])
    if isinstance(cohort.get('additional_config'), Mapping): meta = dict(rt.get('metadata') or {}); meta['additional_config'] = dict(cohort['additional_config']); [meta.pop(k, None) for k in ('input_boundary', 'checkpoint', 'capture_directory', 'client_summary', 'startup', 'force_eplb', 'expert_parallel', 'observed_accept_ratio', 'client', 'geometry_policy', 'unresolved_capture_contracts', 'compatible_variant', 'accepted_state_scenario', 'mxfp8_gate_up_condition', 'calibration_origin', 'calibration_evidence', 'pooled_score_coordinate_migration', 'resolved_configuration_lines')]; meta['template_metadata'] = 'removed; source config/cohort owns axes'; rt['metadata'] = meta
    # An explicit actual source routing/force declaration overrides the
    # template's conditional scenario.  Missing cohort fields leave the
    # template intact and are classified by _source_binding as inherited.
    cohort_rt = cohort.get('runtime') if isinstance(cohort.get('runtime'), Mapping) else {}
    cohort_kernels = cohort_rt.get('kernels') if isinstance(cohort_rt.get('kernels'), Mapping) else {}
    if isinstance(cohort.get('routing'), Mapping):
        rt['routing'] = copy.deepcopy(dict(cohort['routing']))
    if isinstance(cohort_rt.get('routing'), Mapping):
        rt['routing'] = copy.deepcopy(dict(cohort_rt['routing']))
    force = cohort.get('force_eplb_source')
    if force is None: force = cohort_kernels.get('force_eplb_source')
    if force is not None:
        kernels = dict(rt.get('kernels') or {}); kernels['force_eplb_source'] = copy.deepcopy(force); rt['kernels'] = kernels
    return {**raw, 'runtime': rt}
def _raw_case(spec: CellSpec) -> dict[str, Any]:
    try: from .zero_shot_native_windows import deployment_metadata
    except ImportError: from zero_shot_native_windows import deployment_metadata
    # Sanitize the actual source constructor before optional cohort metadata is
    # merged/stripped.  This is the shared forecast ingress for public graph
    # and serving paths; no marker is added to the case.
    base = _sanitize_forecast_service_rules(_raw_case_base(spec))
    return deployment_metadata(spec, _overlay_cohort(spec, base))




def _freeze_source_value(value: Any) -> Any:
    if isinstance(value, Mapping): return MappingProxyType({str(k): _freeze_source_value(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)): return tuple(_freeze_source_value(v) for v in value)
    return value


def _plain_source_value(value: Any) -> Any:
    if isinstance(value, Mapping): return {str(k): _plain_source_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_plain_source_value(v) for v in value]
    return value

_ROUTE_CONDITIONAL_TARGETS = (
    'L1:moe_grouped', 'L1:moe_router', 'L1:activation', 'L1:collective',
    'L2:moe', 'L3:body', 'L4:service',
)


_BINDING_CACHE: dict[tuple[Any, ...], Any] = {}
_FINGERPRINT_CACHE: dict[tuple[Any, ...], str] = {}


def _stat_sig(path: Path | None) -> tuple[str, int, int] | None:
    if path is None:
        return None
    try:
        st = path.stat()
    except OSError:
        return (str(path), -1, -1)
    return (str(path), int(st.st_mtime_ns), int(st.st_size))


def _source_binding(spec: CellSpec, raw: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify source routing against the resolved model and actual precedence.

    Routing is relevant only where the resolved model actually has routed MoE
    layers.  A provided ledger is not marked consumed/authoritative from field
    presence: it must match actual model layer coverage and still needs the
    ordinary graph/serving consumer to demonstrate use.  Template-only policy
    remains a conditional scenario, and explicit cohort/runtime precedence is
    preserved.
    """
    bkey = None
    if raw is None:
        bkey = (
            _stat_sig(spec.model_case), _stat_sig(_cohort_case(spec)), _stat_sig(spec.source_config),
            spec.synthetic_layers, spec.synthetic_experts, spec.synthetic_topk, spec.notes,
        )
        if bkey in _BINDING_CACHE:
            return _BINDING_CACHE[bkey]
    raw = dict(raw) if isinstance(raw, Mapping) else _raw_case(spec)
    template = _load_json(spec.model_case) if spec.model_case is not None else {}
    template = template if isinstance(template, Mapping) else {}
    template_rt = template.get('runtime') if isinstance(template.get('runtime'), Mapping) else {}
    template_meta = template_rt.get('metadata') if isinstance(template_rt.get('metadata'), Mapping) else {}
    template_control = template_meta.get('sp_padding_control')
    cohort_path = _cohort_case(spec)
    cohort = _load_json(cohort_path) if cohort_path is not None and cohort_path.exists() else {}
    cohort = cohort if isinstance(cohort, Mapping) else {}
    cohort_rt = cohort.get('runtime') if isinstance(cohort.get('runtime'), Mapping) else {}
    cohort_kernels = cohort_rt.get('kernels') if isinstance(cohort_rt.get('kernels'), Mapping) else {}
    cohort_force = cohort.get('force_eplb_source')
    if cohort_force is None: cohort_force = cohort_kernels.get('force_eplb_source')
    cohort_routing = cohort.get('routing') if isinstance(cohort.get('routing'), Mapping) else None
    cohort_routing_runtime = cohort_rt.get('routing') if isinstance(cohort_rt.get('routing'), Mapping) else None
    raw_rt = raw.get('runtime') if isinstance(raw.get('runtime'), Mapping) else {}
    raw_kernels = raw_rt.get('kernels') if isinstance(raw_rt.get('kernels'), Mapping) else {}
    effective_routing = raw_rt.get('routing') if isinstance(raw_rt.get('routing'), Mapping) else None
    effective_force = raw_kernels.get('force_eplb_source')
    template_routing = template_rt.get('routing') if isinstance(template_rt.get('routing'), Mapping) else None
    # Resolve actual model topology without compiling or executing the model.
    from mindie_sim.prediction.structure import parse_case
    model, _notes = _model_for_instantiation(parse_case(raw).model, spec)
    moe_layers = tuple(int(layer.index) for layer in model.layer_plans
                       if str(getattr(layer, 'ffn', '')).lower() == 'moe'
                       and int(getattr(layer, 'num_experts', 0) or 0) > 0)
    effective_realizations = ((effective_routing or {}).get('realizations')
                              if isinstance(effective_routing, Mapping) else None)
    declaration_layers = tuple(sorted({int(item.get('layer')) for item in (effective_realizations or ())
                                       if isinstance(item, Mapping) and isinstance(item.get('layer'), int)}))
    has_topk = any(isinstance(item, Mapping) and bool(item.get('topk_ids'))
                   for item in (effective_realizations or ()) if isinstance(item, Mapping))
    has_force = isinstance(effective_force, Mapping) and bool(effective_force)
    provided = bool(has_topk or has_force)
    overridden = bool((cohort_routing is not None or cohort_routing_runtime is not None)
                      and effective_routing != (cohort_routing_runtime or cohort_routing))
    if not moe_layers:
        status = 'route_not_applicable_dense'
        authoritative = False
        reason = 'resolved model has no routed MoE layer'
    elif overridden and (cohort_routing is not None or cohort_force is not None
                         or cohort_routing_runtime is not None):
        status = 'provided_source_route_overridden'
        authoritative = False
        reason = 'runtime/cohort route precedence overrides provided ledger'
    elif provided:
        authoritative = False
        if declaration_layers and not (set(declaration_layers) & set(moe_layers)):
            status = 'provided_source_route_unmatched_model_layers'
            reason = 'provided ledger layers do not cover resolved MoE layers'
        else:
            status = 'provided_source_route_unverified'
            reason = 'ledger provided but ordinary consumer use not demonstrated'
    elif cohort_routing is not None or cohort_routing_runtime is not None or cohort_force is not None:
        status = 'explicit_source_policy_no_route_ledger'
        authoritative = False
        reason = 'explicit cohort policy/force lacks consumed per-token ledger'
    elif template_routing is not None:
        status = 'inherited_template_control'
        authoritative = False
        reason = 'routing policy comes only from the template scenario'
    else:
        status = 'unresolved_source_route'
        authoritative = False
        reason = 'no actual or template route declaration'
    route_targets = _ROUTE_CONDITIONAL_TARGETS if moe_layers and not authoritative else ()
    source_hashes = {}
    for label, path in (('template', spec.model_case), ('cohort', cohort_path), ('source_config', spec.source_config)):
        if path is not None and path.exists():
            source_hashes[label] = hashlib.sha256(path.read_bytes()).hexdigest()
    frozen = _freeze_source_value({
        'schema': 'mindie-sim/source-routing-binding/2',
        'status': status,
        'reason': reason,
        'authoritative': authoritative,
        'consumed': False,
        'resolved_moe_layers': moe_layers,
        'template_routing': template_routing,
        'template_control': template_control,
        'cohort_routing': cohort_routing,
        'cohort_routing_runtime': cohort_routing_runtime,
        'cohort_force_eplb_source': cohort_force,
        'effective_routing': effective_routing,
        'effective_force_eplb_source': effective_force,
        'provided_ledger': provided,
        'declared_layers': declaration_layers,
        'covered_moe_layers': tuple(sorted(set(declaration_layers) & set(moe_layers))),
        'source_hashes': source_hashes,
        'route_dependent_targets': route_targets,
        'known': ('template/cohort/source pointers, effective precedence, resolved MoE layer topology',),
        'unknown': () if not route_targets else ('matched scheduled request position', 'per-token expert assignment', 'expert-to-EP route', 'consumed route timing attribution'),
    })
    if bkey is not None:
        if len(_BINDING_CACHE) >= 128:
            _BINDING_CACHE.pop(next(iter(_BINDING_CACHE)))
        _BINDING_CACHE[bkey] = frozen
    return frozen


def _source_partial_targets(binding: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(binding, Mapping) or binding.get('authoritative'): return ()
    return tuple(str(x) for x in binding.get('route_dependent_targets') or ())

def _public_case(spec: CellSpec) -> Any:
    """Same resolved source case/model used by the ordinary compiler."""
    try:
        key = (spec.dataset, _structure_fingerprint(spec))
        if key in _COMPILED_MODELS:
            return _COMPILED_MODELS[key][11]
    except Exception:
        pass
    from mindie_sim.prediction.structure import parse_case
    case = parse_case(_raw_case(spec))
    model, _notes = _model_for_instantiation(case.model, spec)
    return replace(case, model=model)

def _structure_fingerprint(spec: CellSpec) -> str:
    if spec.model_case is None or not spec.model_case.exists(): return f'nocase:{spec.cell_id}:{sorted(spec.notes)}'
    fkey = (
        _stat_sig(spec.model_case), _stat_sig(_cohort_case(spec)), _stat_sig(spec.source_config),
        spec.dataset, spec.tp, spec.dp, spec.ep, spec.pp, spec.graph_buckets, spec.notes,
        spec.synthetic_layers, spec.synthetic_experts, spec.synthetic_topk,
        spec.source_config_sha256, spec.source_file_sha256, spec.source_origin,
        str(spec.source_case_dir or ''),
    )
    if fkey in _FINGERPRINT_CACHE:
        return _FINGERPRINT_CACHE[fkey]
    raw = _raw_case(spec)
    blob = json.dumps({'model': raw.get('model'), 'machine': raw.get('machine'), 'runtime': raw.get('runtime'), 'notes': sorted(spec.notes), 'synthetic': (spec.synthetic_layers, spec.synthetic_experts, spec.synthetic_topk), 'source_config': (str(spec.source_config or ''), spec.source_config_sha256, spec.source_file_sha256, spec.source_origin), 'binding': (str(spec.source_case_dir or ''), spec.dataset, hashlib.sha256(json.dumps({k: ((raw.get('runtime') or {}).get('metadata') or {}).get(k) for k in ('image', 'image_id', 'deployment_image', 'deployment_image_id', 'oci_image', 'oci_image_digest', 'mx_quant_source_revision')}, sort_keys=True, default=str).encode()).hexdigest()), 'tp': spec.tp, 'dp': spec.dp, 'ep': spec.ep, 'pp': spec.pp, 'graph_buckets': spec.graph_buckets}, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode('utf-8')).hexdigest()
    if len(_FINGERPRINT_CACHE) >= 256:
        _FINGERPRINT_CACHE.pop(next(iter(_FINGERPRINT_CACHE)))
    _FINGERPRINT_CACHE[fkey] = digest
    return digest
def _prepare_case_topology(spec: CellSpec) -> tuple[str, dict[str, Any]]:
    sanitized = _sanitize_forecast_service_rules(_raw_case_base(spec))
    blob = json.dumps({'sanitized': sanitized, 'kv_bf16': 'kv_bf16' in spec.notes, 'synthetic': (spec.synthetic_layers, spec.synthetic_experts, spec.synthetic_topk)}, sort_keys=True, default=str)
    return (hashlib.sha256(blob.encode('utf-8')).hexdigest(), sanitized)
def _model_topology_fingerprint(spec: CellSpec) -> str:
    if spec.model_case is None or not spec.model_case.exists(): return f'nocase:{spec.cell_id}:{list(spec.notes)}'
    try: return _prepare_case_topology(spec)[0]
    except TimeoutError: raise
    except (OSError, ValueError, KeyError, TypeError) as exc: return f'invalid:{type(exc).__name__}:{exc}:{spec.model_case}:{list(spec.notes)}'
def _case_layers(spec: CellSpec) -> int:
    if spec.model_case is None or not spec.model_case.exists(): return 0
    try: fp, base = _prepare_case_topology(spec)
    except TimeoutError: raise
    except (OSError, ValueError, KeyError, TypeError): return 0
    if fp in _CASE_LAYERS: return _CASE_LAYERS[fp]
    try:
        from mindie_sim.prediction.structure import parse_case; m = _model_for_instantiation(parse_case(base).model, spec)[0]
        layers, moe = (len(m.layer_plans), getattr(m, 'num_experts', 0) > 1 or getattr(m, 'ffn', '') == 'moe' or any((getattr(lp, 'ffn', '') == 'moe' for lp in getattr(m, 'layer_plans', ()))))
    except TimeoutError: raise
    except (OSError, ValueError, KeyError, TypeError): return 0
    if len(_CASE_LAYERS) >= 128: _CASE_LAYERS.clear(); _CASE_MOE.clear()
    _CASE_LAYERS[fp] = _CASE_LAYERS[str(spec.model_case)] = layers; _CASE_MOE[fp] = moe; return layers
def _case_has_moe(spec: CellSpec) -> bool:
    if spec.synthetic_experts: return spec.synthetic_experts > 1
    if spec.model_case is None or not spec.model_case.exists(): return False
    try: fp, _base = _prepare_case_topology(spec)
    except TimeoutError: raise
    except (OSError, ValueError, KeyError, TypeError): return False
    if fp not in _CASE_MOE: _case_layers(spec)
    return _CASE_MOE.get(fp, False)
def _has_prefill_marker(by_name: Mapping[str, Any]) -> bool: return any((m in n.lower() for n in by_name or {} for m in _PREFILL_MARKERS))
def _decode_segments(trace: KernelTrace, _tpot_ms: float | None=None) -> tuple[float, ...]:
    segs = tuple(getattr(trace, 'segments', ()) or ()); by_n = getattr(trace, 'by_name', {}) or {}
    if segs and _has_prefill_marker(by_n):
        kept = tuple((s[0] / 1000.0 for s in segs if s[0] > 0.0 and (not _has_prefill_marker(s[2]))))
        if kept: return kept
    steps = tuple((us / 1000.0 for us in getattr(trace, 'step_us', ()) or () if us > 0.0))
    return steps if len(steps) >= 2 else ()
def _mixed_prefill(trace: KernelTrace, spec: CellSpec, step_trace_ms: float | None=None, _tpot_ms: float | None=None) -> bool:
    return spec.phase != 'prefill' and _has_prefill_marker(getattr(trace, 'by_name', {}) or {})
def _trace_step_count(trace: KernelTrace, spec: CellSpec, declared: int, _tpot_ms: float | None=None, _ttft_ms: float | None=None) -> int:
    counts = getattr(trace, 'counts', {}) or {}
    if not counts: return max(1, int(declared))
    declared, mode, layers = (max(1, int(declared)), _count_mode(counts), _case_layers(spec))
    if spec.phase == 'prefill':
        if len(counts) <= 2 and layers > 0:
            d = 2 * layers if any(('groupedmatmul' in k.lower() for k in counts)) else layers
            if d and mode % d == 0 and (mode // d >= 1): return mode // d
        return 1
    if _mixed_prefill(trace, spec): segments = _decode_segments(trace); return max(1, len(segments)) if segments else declared
    quotients = {mode // divisor for divisor in (layers, 2 * layers) if divisor and mode % divisor == 0 and (0.5 * declared <= mode // divisor <= 2 * declared)}
    if quotients: return min(quotients, key=lambda val: (abs(val - declared), val))
    if (layers <= 1 or mode >= layers) and 0.5 * declared <= mode <= 2 * declared: return mode
    steps = len(getattr(trace, 'step_us', ()) or ()); return steps if 2 <= steps <= 8 * declared else declared
def measured_subgraph_us(trace: KernelTrace, family: str) -> float:
    by_c = trace.by_class or {k: sum((us for n, us in trace.by_name.items() if classify_kernel(n, allow_unresolved=True) == k)) for k in MECHANISMS}
    if family == 'attention': return sum((by_c.get(k, 0.0) for k in ('attention', 'rope', 'kv_cache', 'indexer', 'gdn_linear_attn', 'kda_linear_attn')))
    if family == 'moe':
        if by_c.get('moe_grouped', 0.0) <= 0.0: return by_c.get('activation', 0.0) or sum((us for n, us in trace.by_name.items() if _has(n, _MOE_TOKENS)))
        has_kda = any(('recurrentkda' in k.lower() or 'chunkkda' in k.lower() for k in trace.by_name))
        mc = sum((us for n, us in trace.by_name.items() if _has(n, _MOE_TOKENS) and classify_kernel(n, allow_unresolved=True) == 'collective')) if any(('allreduce' in k.lower() for k in trace.by_name)) and (not has_kda) else by_c.get('collective', 0.0)
        return sum((by_c.get(k, 0.0) for k in ('moe_grouped', 'moe_router', 'activation'))) + mc
    return by_c.get(family, 0.0)
def _load_json(path: Path) -> Any:
    try: return json.loads(path.read_text(encoding='utf-8'))
    except TimeoutError: raise
    except (OSError, ValueError): return None
def _seconds(raw: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        item = raw.get(key); item = item.get('median') or item.get('mean') if isinstance(item, Mapping) else item
        try:
            val = float(item) / 1000.0 if key.endswith('_ms') else float(item)
            if math.isfinite(val) and val >= 0.0: return val
        except (TypeError, ValueError): continue
    return None
def load_measured_cell(spec: CellSpec, json_path: Path, kernel_paths: Sequence[Path], raw: Mapping[str, Any] | None=None) -> MeasuredCell:
    raw = raw if isinstance(raw, Mapping) else _load_json(json_path) or {}; phase = 'prefill' if 'prefill' in str(raw.get('mode') or raw.get('phase') or '') or spec.phase == 'prefill' else 'decode'
    prompt = int(raw.get('prompt_tokens') or raw.get('input_tokens') or raw.get('isl') or spec.prompt_tokens or 1)
    prompt = spec.prompt_tokens if phase == 'prefill' and 0 < spec.prompt_tokens < prompt else prompt; concurrency = int(raw.get('concurrency') or raw.get('batch_size') or spec.concurrency or 1)
    max_tokens = int(raw.get('max_tokens') or raw.get('output_tokens') or raw.get('completion_tokens') or raw.get('osl') or spec.max_tokens or 1); streams = raw.get('streams') or []
    completion = max((int(s.get('completion_tokens') or 0) for s in streams if isinstance(s, dict)), default=0); warmup_tokens = int(raw.get('warmup_max_tokens') or 0)
    steps = 1 if phase == 'prefill' else max(1, max_tokens or completion) + max(0, warmup_tokens)
    ttft = _seconds(raw, 'ttft_mean_s', 'ttft_p50_s', 'ttft_ms', 'ttft_mean_ms', 'first_token_latency_s', 'first_token_latency_ms')
    tpot = _seconds(raw, 'tpot_mean_s', 'tpot_p50_s', 'itl_ms', 'tpot_ms', 'tpot_mean_ms', 'itl_mean_s', 'itl_mean_ms')
    success = bool(raw.get('success', bool(streams) or int(raw.get('completed') or 0) > 0 or ttft is not None)) and (bool(streams) if streams else True)
    failure = '' if success else str(raw.get('error') or raw.get('failure') or 'no_success_stream')
    return MeasuredCell(replace(spec, phase=phase, prompt_tokens=prompt, concurrency=concurrency, max_tokens=max_tokens), tuple(kernel_paths), None, None if ttft is None else float(ttft) * 1000.0, None if tpot is None else float(tpot) * 1000.0, None, steps, success, failure)
def _summary_numbers(rows: Sequence[Mapping[str, Any]], *names: str) -> list[float]:
    for name in names:
        vals = []
        for row in rows:
            try:
                if math.isfinite((val := float(row.get(name)))) and val >= 0.0: vals.append(val)
            except (TypeError, ValueError): pass
        if vals: return vals
    return []
def _read_summary(path: Path) -> dict[str, Any]:
    """Project a request_summary CSV into the measured-JSON vocabulary."""
    try:
        with path.open('rt', encoding='utf-8', errors='replace', newline='') as handle:
            rows = [{str(k).strip().lower().lstrip('\ufeff').replace('(ms)', '_ms').replace('[ms]', '_ms').replace('(s)', '_s').replace('[s]', '_s').replace(' ', '_').replace('__', '_'): v for k, v in row.items()} for row in csv.DictReader(handle)]
    except TimeoutError: raise
    except OSError as exc: return {'success': 0, 'error': f'{type(exc).__name__}:{exc}', 'tag': path.name}
    if not rows: return {}
    pick = lambda *names: next((v for r in rows for nm in names if (v := r.get(nm)) not in (None, '', '-', 'N/A', 'None', 'nan')), None); n = lambda *names: _summary_numbers(rows, *names)
    completion = n('completion_tokens', 'output_tokens', 'out_tokens', 'max_tokens', 'osl_target', 'osl'); prompt = n('prompt_tokens', 'input_tokens', 'isl', 'context')
    concurrency = n('concurrency', 'batch_size'); count = int(max(concurrency)) if concurrency else max(1, len(rows))
    ttft_ms = n('ttft_ms', 'ttft_mean_ms', 'ttft_p50_ms', 'first_token_latency_ms', 'first_token_ms', 'ttft', 'first_token_latency')
    ttft_s = n('ttft_s', 'ttft_mean_s', 'ttft_p50_s', 'first_token_latency_s', 'first_token_s')
    tpot_ms = n('itl_p50_ms', 'itl_mean_ms', 'tpot_p50_ms', 'tpot_ms', 'tpot_mean_ms', 'tpot', 'itl') if len(rows) > count else n('tpot_ms', 'tpot_mean_ms', 'tpot_p50_ms', 'itl_mean_ms', 'itl_p50_ms', 'tpot', 'itl')
    tpot_s = n('tpot_s', 'tpot_mean_s', 'tpot_p50_s', 'itl_mean_s', 'itl_p50_s'); ttft = mean(ttft_ms) if ttft_ms else mean(ttft_s) * 1000.0 if ttft_s else None
    tpot = (median(tpot_ms) if len(rows) > count else mean(tpot_ms)) if tpot_ms else mean(tpot_s) * 1000.0 if tpot_s else None; max_tokens = int(max(completion)) if completion else 0
    success = int(all((str(r.get('success') or r.get('ok') or r.get('status') or '1').lower() not in {'0', 'false', 'fail', 'failed', 'error'} for r in rows)))
    tag = str(pick('tag', 'cell', 'case', 'name') or (path.parent.parent.name if path.parent.name == 'measured' else path.parent.name))
    mode = str(pick('mode', 'phase', 'profile_mode') or ('profile_prefill' if 'prefill' in tag or '_pf_' in tag or tag.startswith('pf_') else 'profile_decode'))
    record: dict[str, Any] = {'tag': tag, 'mode': mode, 'success': success, 'prompt_tokens': int(max(prompt)) if prompt else 1, 'concurrency': count, **({'max_tokens': max_tokens, 'streams': [{'completion_tokens': max_tokens} for _ in range(count)]} if max_tokens > 0 else {})}
    if ttft is not None: record['ttft_mean_s'] = ttft / 1000.0
    if tpot is not None: record['tpot_mean_s'] = tpot / 1000.0
    record.update({k: v for k in ('error', 'failure', 'model_case', 'model_path', 'model') if (v := pick(k)) is not None}); return record
def _norm_cell(cell: MeasuredCell) -> MeasuredCell:
    trace = cell.trace
    if trace is None: return cell
    by_c, by_n, cnt = (dict(trace.by_class), dict(trace.by_name), dict(trace.counts)); dur, step_ms, steps, qual = (trace.duration_us, cell.step_trace_ms, max(1, cell.decode_steps), cell.trace_quality)
    raw_hl = by_n.get('HcclLaunchAicpuKernel', 0.0); hl = min(raw_hl, max(0.0, dur - trace.union_duration_us)) if trace.union_duration_us > 0.0 else raw_hl
    if any((k.startswith('hcom_') for k in by_n)) and hl > 1.0:
        if raw_hl - hl > 0.0: by_n['HcclLaunchAicpuKernel'] = raw_hl - hl
        else: by_n.pop('HcclLaunchAicpuKernel', None); cnt.pop('HcclLaunchAicpuKernel', None)
        by_c['collective'] = max(0.0, by_c.get('collective', 0.0) - hl); dur = max(0.0, dur - hl)
        step_ms = max(1.0, step_ms - hl / 1000.0 / steps) if step_ms is not None and cell.spec.phase == 'prefill' else step_ms
    return replace(cell, decode_steps=steps, trace=replace(trace, duration_us=dur, by_class=by_c, by_name=by_n, counts=cnt), step_trace_ms=step_ms, trace_quality=qual)
def attach_trace(cell: MeasuredCell, *, cache_dir: Path | None=None) -> MeasuredCell:
    if cell.trace is not None: return replace(cell, step_trace_ms=0.0, decode_steps=0, success=False, failure=cell.trace.incomplete_reason or 'incomplete_trace', trace_quality='corrupt_incomplete_trace') if getattr(cell.trace, 'incomplete', False) else cell
    if not (paths := [path for path in cell.kernel_paths if path.exists()]): return cell
    loaded = [_strip_hccl_launch(load_kernel_trace(p, cache_dir=cache_dir)) for p in paths]
    if (bad_t := next((t for t in loaded if getattr(t, 'incomplete', False)), None)) is not None: return replace(cell, trace=bad_t, step_trace_ms=0.0, decode_steps=0, success=False, failure=bad_t.incomplete_reason or 'incomplete_trace', trace_quality='corrupt_incomplete_trace')
    max_at = max((t.by_class.get('attention', 0.0) + t.by_class.get('gdn_linear_attn', 0.0) + t.by_class.get('kda_linear_attn', 0.0) for t in loaded))
    cand = [t for t in loaded if t.by_class.get('attention', 0.0) + t.by_class.get('gdn_linear_attn', 0.0) + t.by_class.get('kda_linear_attn', 0.0) > 0.0] if max_at > 0 else loaded; rank_steps = [t.step_us for t in cand if t.step_us]
    rank_mismatch = len({len(s) for s in rank_steps}) > 1
    if rank_mismatch:
        target_len = Counter((len(s) for s in rank_steps)).most_common(1)[0][0]; cand = [t for t in cand if len(t.step_us) == target_len] or cand
        rank_steps = [t.step_us for t in cand if len(t.step_us) == target_len]
    trace = max(cand, key=lambda t: t.duration_us)
    if len(rank_steps) > 1 and len({len(s) for s in rank_steps}) == 1:
        aligned = tuple((max((s[i] for s in rank_steps)) for i in range(len(rank_steps[0]))))
        trace = replace(trace, step_us=aligned, duration_us=sum(aligned) if trace.segments else trace.duration_us, union_duration_us=sum(aligned) if trace.union_duration_us > 0 and trace.segments else trace.union_duration_us)
    segs = tuple(getattr(trace, 'segments', ()) or ())
    steps, mixed = (_trace_step_count(trace, cell.spec, cell.decode_steps), _mixed_prefill(trace, cell.spec))
    segments = _decode_segments(trace) if mixed or (cell.spec.phase == 'decode' and len(segs) >= 2) else ()
    chosen = [seg for seg in segs if round(seg[0], 3) in {round(ms * 1000.0, 3) for ms in segments}] if segments and mixed else []
    if chosen:
        c_sum, n_sum, k_sum = (defaultdict(float), defaultdict(float), Counter())
        for _, sc, sn, sk in chosen: c_sum.update(((k, c_sum[k] + v) for k, v in sc.items())); n_sum.update(((k, n_sum[k] + v) for k, v in sn.items())); k_sum.update(sk)
        dur = sum((seg[0] for seg in chosen)); step_tuple = tuple((seg[0] for seg in chosen))
        trace = replace(trace, duration_us=dur, union_duration_us=min(dur, trace.union_duration_us) if trace.union_duration_us > 0 else 0.0, by_class=dict(c_sum), by_name=dict(n_sum), counts=dict(k_sum), step_us=step_tuple, segments=tuple(chosen) if len(chosen) >= 2 else ())
    elif len(segs) < 2: trace = replace(trace, segments=())
    eff_dur = trace.union_duration_us if trace.union_duration_us > 0 else trace.duration_us
    step_trace = mean(segments) if segments else 0.0 if mixed else eff_dur / 1000.0 / max(1, steps)
    qual = 'rank_step_alignment_unresolved' if rank_mismatch else 'mixed_prefill' if mixed else 'ok'
    return _norm_cell(replace(cell, trace=trace, step_trace_ms=step_trace, decode_steps=steps, trace_quality=qual))
def _parse_triplet(text: str) -> tuple[int, int, int]: return tuple((int(m.group(1)) if m else 0 for m in (re.search(f'{k}(\\d+)', text.lower()) for k in ('dp', 'tp', 'ep'))))
def resolve_model(label: str) -> tuple[Path | None, str, tuple[str, ...]]:
    for n, rel, h in MODEL_PROFILES:
        if n in label.lower(): p = CASES_DIR / rel; return (p if p.exists() else None, h, ())
    return (None, 'unresolved', ('no_structural_case',))
def _bucket_for(concurrency: int, buckets: Sequence[int]) -> int: return next((val for val in sorted({int(item) for item in buckets if int(item) > 0}) if val >= concurrency), 0)
def _load_status(case_root: Path, root: Path) -> dict[str, Any]:
    for parent in (case_root, *case_root.parents):
        for fname in ('status.json', 'case_spec.json'):
            if isinstance((d := _load_json(parent / fname)), dict): return d
        if parent == root: break
    return {}
def _spec_from_record(raw: Mapping[str, Any], path: Path, dataset: str, case_root: Path, root: Path) -> CellSpec:
    tag = str(raw.get('tag') or (path.parent.parent.name if path.parent.name == 'measured' else path.parent.name))
    cell_id = f'{case_root.name}:{tag}' if case_root != root and case_root.name not in {'out', 'runs', 'measured'} and (not tag.startswith(case_root.name)) else tag
    model_case, model_label, model_notes = resolve_model(f"{path} {case_root.name} {tag} {raw.get('model') or raw.get('model_name') or ''}")
    if (override := (raw.get('model_case') or raw.get('model_path'))) and Path(str(override)).exists(): candidate = Path(str(override)); model_case = candidate if candidate.is_absolute() else ROOT / candidate; model_label, model_notes = (f'declared:{candidate.name}', ())
    t_dp, t_tp, t_ep = _parse_triplet(tag); c_dp, c_tp, c_ep = _parse_triplet(case_root.name); status = _load_status(case_root, root)
    spec_sec = (status.get('spec') if isinstance(status.get('spec'), dict) else status) if isinstance(status, dict) else {}; comp = spec_sec.get('compilation_config', {}) if isinstance(spec_sec, dict) else {}
    buckets = tuple((int(v) for v in comp.get('cudagraph_capture_sizes', ()) if isinstance(v, int))); dp = int(t_dp or spec_sec.get('dp') or c_dp or 0); tp = int(t_tp or spec_sec.get('tp') or c_tp or 0)
    ep = int(t_ep or spec_sec.get('ep') or (dp * max(1, tp) if spec_sec.get('enable_expert_parallel') else c_ep or 0))
    phase = 'prefill' if 'prefill' in str(raw.get('mode') or raw.get('phase') or '') else 'decode'; prompt = int(raw.get('prompt_tokens') or raw.get('input_tokens') or raw.get('isl') or 1)
    prompt = min(max(1, prompt), int(m.group(1)) * 1024) if phase == 'prefill' and (m := re.search('_p(\\d+)k(?:_|$)', tag.lower())) else prompt
    concurrency = int(raw.get('concurrency') or raw.get('batch_size') or 1); max_tokens = int(raw.get('max_tokens') or raw.get('output_tokens') or raw.get('osl') or 1)
    gb = _bucket_for(concurrency, buckets) if phase == 'decode' else 0; notes = tuple(dict.fromkeys((*model_notes, *(('graph_bucket_declared',) if buckets else ())))); nra = raw.get('norm_runtime_abi') or raw.get('norm_runtime'); notes = notes + (f'norm_runtime_abi:{json.dumps(nra, sort_keys=True)}',) if isinstance(nra, Mapping) else notes; iwf = raw.get('indexer_weight_formats'); notes = notes + (f'indexer_weight_formats:{json.dumps(iwf, sort_keys=True)}',) if isinstance(iwf, Mapping) else notes
    seq = int(raw.get('sequences_per_replica') or raw.get('local_batch') or 0); qtok = int(raw.get('tokens_per_sequence') or raw.get('q_len') or 0)
    src = raw.get('source_config') or raw.get('model_config_path'); ssh = str(raw.get('source_config_sha256') or raw.get('model_config_sha256') or '')
    spec = CellSpec(cell_id, dataset, phase, model_case, model_label, prompt, concurrency, max_tokens, tp, dp, ep, 1, buckets, gb, notes, seq, qtok, source_config=(Path(str(src)) if src else None), source_config_sha256=ssh)
    if dataset == 'out': alias = _header_alias(raw); spec = replace(spec, source_header_archive=alias) if alias else spec; spec = _bind_original_deployment(spec, raw)
    return replace(spec, ep=dp * max(1, tp)) if not ep and 'dspark' not in tag.lower() and _case_has_moe(spec) else spec
def _pair_kernels(case_root: Path, tag: str, kernels: Sequence[Path]) -> tuple[Path, ...]:
    candidates = [path for path in kernels if path.is_relative_to(case_root)]
    matches = [(idx, part, path) for path in candidates for idx, part in enumerate(path.relative_to(case_root).parts[:-1]) if part and (tag == part or tag.endswith('_' + part) or part.endswith('_' + tag))]
    if matches:
        depth = max((idx for idx, _, _ in matches)); names = {part for idx, part, _ in matches if idx == depth}
        if len(names) == 1: name = names.pop(); return tuple(sorted({path for _, part, path in matches if part == name}))
    return tuple(sorted(candidates))
def _find_summary(path: Path, case_root: Path, indexed: Sequence[Path]=()) -> Path | None:
    for d in (path.with_suffix(''), path.parent, case_root, case_root / 'measured', case_root.parent):
        if (c := (d / 'request_summary.csv')).exists(): return c
    return indexed[0] if indexed else next(iter(sorted(case_root.rglob('request_summary.csv'))), None)
_SKIP_JSON = {'case_spec.json', 'status.json', 'campaign_status.json', 'manifest.json', 'communication.json', 'communication_matrix.json', 'export_summary.json', 'kv_cache_startup.json'}
def _unwrap_record(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict): return None
    cfg = raw.get('config') if isinstance(raw.get('config'), dict) else {}
    if isinstance((m := raw.get('metrics')), dict) and any((k in m for k in ('ttft_ms', 'ttft_mean_s', 'tpot_ms', 'itl_ms'))): return {**cfg, **raw, **m, 'prompt_tokens': raw.get('prompt_tokens') or cfg.get('isl') or m.get('isl') or 1, 'concurrency': raw.get('concurrency') or cfg.get('concurrency') or m.get('concurrency') or 1, 'max_tokens': raw.get('max_tokens') or cfg.get('osl') or m.get('osl') or 1}
    return raw
def _looks_measured(path: Path, raw: Mapping[str, Any]) -> bool:
    if path.name in _SKIP_JSON or 'knee_curve' in path.name or path.name.startswith('profiler_info_') or (raw.get('profile_enabled') is False): return False
    return path.parent.name == 'measured' or any((k in raw for k in ('mode', 'phase', 'streams', 'success', 'tag', 'ttft_mean_s', 'ttft_ms', 'tpot_mean_s', 'tpot_ms', 'itl_ms')))
def _discover_layout(root: Path) -> list[MeasuredCell]:
    kernels = sorted((p for p in root.rglob('kernel_details.csv*') if p.is_file() and 'idle_dp_rank' not in p.parts))
    summaries = sorted((p for p in root.rglob('request_summary.csv') if 'idle_dp_rank' not in p.parts)); k_by_dir, s_by_dir, used, cells = (defaultdict(list), defaultdict(list), set(), [])
    for d, items in ((k_by_dir, kernels), (s_by_dir, summaries)):
        for it in items:
            for p in it.parents:
                d[p].append(it)
                if p == root: break
    for path in sorted(root.rglob('*.json')):
        if path.name in _SKIP_JSON or path.name.startswith('profiler_info_') or 'knee_curve' in path.name or ('idle_dp_rank' in path.parts): continue
        if path.parent.name != 'measured' and 'measured' not in path.stem.lower() and {'remote_cfg', 'raw', 'cases', 'cmd', 'logs'} & set(path.parts): continue
        raw = _unwrap_record(_load_json(path))
        if raw is None and (path.parent.name == 'measured' or 'measured' in path.stem.lower()): cells.append(MeasuredCell(CellSpec(path.stem, root.name, 'decode', None, 'unresolved', 1, 1, 1, 1, 1, 1, 1), (), None, None, None, None, 1, False, 'invalid_json')); continue
        if not isinstance(raw, dict) or not _looks_measured(path, raw): continue
        case_root = path.parent.parent if path.parent.name == 'measured' else path.parent
        if (summary := _find_summary(path, case_root, s_by_dir.get(case_root, ()))) is not None: merged = _read_summary(summary); merged.update(raw); used.add(summary.resolve()); raw = merged
        tag = str(raw.get('tag') or path.stem)
        cells.append(load_measured_cell(_spec_from_record(raw, path, root.name, case_root, root), path, _pair_kernels(case_root, tag, k_by_dir.get(case_root, ())), raw=raw))
    for path in summaries:
        if path.resolve() in used or not (raw := _read_summary(path)): continue
        case_root = path.parent.parent if path.parent.name == 'measured' else path.parent
        cells.append(load_measured_cell(_spec_from_record(raw, path, root.name, case_root, root), path, _pair_kernels(case_root, str(raw['tag']), k_by_dir.get(case_root, ())), raw=raw))
    return cells
def discover_workstream(root: Path) -> list[MeasuredCell]:
    if not root.exists(): return []
    layouts = [root / name for name in LAYOUTS if (root / name).is_dir()] or [root]; return [cell for layout in layouts for cell in _discover_layout(layout)]
def discover_all_profiling_roots() -> tuple[Path, ...]:
    candidates = [Path('/Volumes/data/mindie-sim-data/a5/multinode-full-coverage-20261108'), *WORKSTREAM_ROOTS]; ws_dir = Path('/Users/maoxx241/code/mindie-agent/.workstreams')
    if ws_dir.exists(): candidates.extend((p for p in sorted(ws_dir.iterdir()) if p.is_dir() and p not in candidates and any((p.name.startswith(k) for k in ('a5', 'heldout', 'vllm')))))
    return tuple((p for p in candidates if p.exists()))
def load_historical_inventory() -> list[dict[str, Any]]:
    entries, seen = ([], set())
    def add(kind: str, path: str, exists: bool) -> None:
        if path and path not in seen: seen.add(path); entries.append({'kind': kind, 'path': path, 'exists': exists})
    for profile in sorted(PROFILES_DIR.glob('*.json')):
        if isinstance((data := _load_json(profile)), dict):
            for section in ('training_sources', 'validation_sources'):
                for item in data.get(section, ()) or (): add('profile_source', (p := str(item.get('path') or '')), Path(p).exists())
    for fixture in sorted(FIXTURES_DIR.rglob('kernel_details*.csv*')): add('fixture', str(fixture), True)
    if isinstance((registry := _load_json(CASES_REGISTRY)), dict):
        for case in registry.get('cases', ()): add('case_registry', (p := str(case.get('source', {}).get('path') or '')), Path(p).exists())
    return entries
def _model_for_instantiation(model: Any, spec: CellSpec | None=None) -> tuple[Any, tuple[str, ...]]:
    notes: list[str] = []
    if spec is not None and spec.synthetic_layers:
        nl, ne, nk = (spec.synthetic_layers, spec.synthetic_experts, spec.synthetic_topk); template = model.layer_plans[-1]
        width = getattr(template, 'moe_intermediate_size', 0) or getattr(template, 'intermediate_size', 0)
        plans = tuple((replace(template, index=i, ffn='moe', num_experts=ne, top_k=nk, moe_intermediate_size=width, kv_owner_layer_id=-1, owns_long_kv=False, index_k_owner_layer_id=-1, owns_index_k=False, topk_owner_layer_id=-1, owns_topk=False, owns_candidate_blocks=False, candidate_source_layer_id=-1, index_source_layer_id=-1) for i in range(nl)))
        model = replace(model, layers=nl, body_layers=nl, ffn='moe', num_experts=ne, top_k=nk, layer_plans=plans); notes.append('synthetic_layer_plans')
    if any((lp.attention == 'projection_only' for lp in getattr(model, 'layer_plans', ()))): model = replace(model, layer_plans=tuple((replace(lp, attention='gqa') if lp.attention == 'projection_only' else lp for lp in model.layer_plans)))
    if spec is not None and 'kv_bf16' in spec.notes: quant = getattr(model, 'quant', None); model = replace(model, kv_dtype='bf16', quant=replace(quant, kv_dtype='bf16') if quant is not None else None)
    quant = getattr(model, 'quant', None)
    if quant is not None and str(getattr(quant, 'index_scale_dtype', '')).lower() in {'none', ''}: model = replace(model, quant=replace(quant, index_scale_dtype='fp8_e8m0')); notes.append('index_scale_dtype_none_priced_as_1_byte_e8m0')
    return (model, tuple(notes))
def _compute_dtype(model: Any, machine: Any=None) -> str:
    quant = getattr(model, 'quant', None); candidate = str(getattr(quant, 'activation_format', '') or getattr(model, 'activation_dtype', 'bf16'))
    overrides = [v for _, kv in getattr(quant, 'category_overrides', ()) or () for k, v in kv if k == 'activation_format']
    candidate = Counter(overrides).most_common(1)[0][0] if candidate == 'bf16' and overrides else candidate
    if candidate not in {'bf16', 'fp16', 'fp32', 'int8', 'fp8_e4m3', 'fp8_e5m2', 'mxfp8', 'int4'}: return 'bf16'
    if machine is not None and getattr(machine, 'dies', ()):
        try: machine.dies[0].peak(candidate)
        except TimeoutError: raise
        except (KeyError, IndexError, TypeError, ValueError): return 'bf16'
    return candidate
def _ep_ranks(spec: CellSpec) -> int: return max(1, spec.ep or (spec.dp * max(1, spec.tp) if _case_has_moe(spec) else 1))
def _ep_batch(spec: CellSpec) -> int: from mindie_sim.prediction.piecewise import ep_batch; return ep_batch(spec.concurrency, spec.dp, _ep_ranks(spec))
def _local_batch_binding(spec: CellSpec) -> tuple[int, bool, str]:
    """Observed active batch when the block table retained it, else a labelled bound.

    A capture's block-table/step row count is an observation.  Dividing the
    client concurrency by DP is only a declared upper bound on how many
    sequences a replica may hold; it is never presented as the observed active
    batch.  The returned basis is published with every prediction so a ramp or
    partial-window cell cannot be mistaken for steady full-batch service.
    """
    observed = int(getattr(spec, 'sequences_per_replica', 0) or 0)
    if observed > 0:
        return observed, True, 'observed_block_table_sequences_per_replica'
    declared = max(1, int(getattr(spec, 'concurrency', 1) or 1))
    return (max(1, math.ceil(declared / max(1, spec.dp))), False,
            'declared_upper_bound_ceil_concurrency_over_dp')

def _local_batch(spec: CellSpec) -> int: return _local_batch_binding(spec)[0]
def _lane_kwargs(spec: CellSpec) -> dict[str, Any]:
    from mindie_sim.prediction.piecewise.geometry import lanes_from_bound_deployment
    if spec.model_case is None or not spec.model_case.exists(): return {}
    path = Path(spec.source_case_dir) / 'status.json' if spec.source_case_dir else None
    return lanes_from_bound_deployment(_raw_case(spec), _load_json(path) if path is not None else None, tp=spec.tp, pp=spec.pp, dp=spec.dp, capture_sizes=spec.graph_buckets, cell_id=spec.cell_id)
def _selected_geometry(geometry: Any) -> Any:
    from mindie_sim.prediction.piecewise.model_pipeline import selected_geometry
    return selected_geometry(geometry)
def _declared_media_tokens(spec: CellSpec) -> int:
    """Sum actual workload.requests[*].media_tokens from the authenticated case."""
    raw = _raw_case(spec)
    workload = raw.get('workload') if isinstance(raw, Mapping) else None
    requests = workload.get('requests') if isinstance(workload, Mapping) else None
    if not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)):
        return 0
    total = 0
    for request in requests:
        if not isinstance(request, Mapping):
            continue
        value = request.get('media_tokens', 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            continue
        total += value
    return total

def _declared_speculation(spec: CellSpec) -> bool:
    raw = _raw_case(spec)
    runtime = raw.get('runtime') if isinstance(raw, Mapping) else None
    metadata = runtime.get('metadata') if isinstance(runtime, Mapping) else None
    speculation = metadata.get('speculation') if isinstance(metadata, Mapping) else None
    return isinstance(speculation, Mapping) and speculation.get('enabled') is True

def _declared_pcp(spec: CellSpec) -> tuple[int, str]:
    """Declared PCP degree/plan from the same authenticated runtime source.

    Use the full runtime mapping, not only ``runtime.parallel``: the retained
    cases declare TP/DP/EP/PP at the runtime top level, while the nested
    ``parallel`` object may carry only ``enable_dsa_cp`` or ``cp_plan``.
    ``Software.parallel_mapping`` is the existing canonical merge of both
    locations (and the dcp/pcp/context_parallel_plan aliases), so the same
    ``ParallelSpec`` validation sees the actual TP group.
    """
    from mindie_sim.schema.case import Software
    from mindie_sim.schema.parallel import ParallelSpec
    raw = _raw_case(spec)
    runtime = raw.get('runtime') if isinstance(raw, Mapping) else None
    declared = ParallelSpec.from_mapping(
        Software.parallel_mapping(runtime if isinstance(runtime, Mapping) else {}))
    return int(declared.pcp), str(declared.cp_plan)

def _apply_pcp_geometry(spec: CellSpec, geometry: Any, phase: str) -> Any:
    if phase != 'prefill':
        return geometry
    pcp, plan = _declared_pcp(spec)
    if pcp <= 1 or plan != 'pcp':
        return geometry
    from mindie_sim.prediction.piecewise.model_pipeline import pcp_rank_geometry
    return pcp_rank_geometry(geometry, pcp)

try: from .zero_shot_piecewise_report import _source_native_group  # noqa: E402
except ImportError: from zero_shot_piecewise_report import _source_native_group  # noqa: E402
def _geometry(spec: CellSpec, phase: str, *, batch: int | None=None) -> Any:
    from mindie_sim.prediction.piecewise import RequestGeometry, WorkloadGeometry, clamp_graph_bucket, ep_batch; batch = batch or _local_batch(spec)
    observed_batch, observed, _basis = _local_batch_binding(spec)
    active_concurrency = (batch * max(1, spec.dp)) if observed else spec.concurrency
    cohort = ep_batch(active_concurrency, spec.dp, max(_ep_ranks(spec), spec.dp) if phase == 'prefill' else _ep_ranks(spec)); lanes = _lane_kwargs(spec)
    if phase == 'prefill': p = max(1, spec.prompt_tokens); return _apply_pcp_geometry(spec, WorkloadGeometry.homogeneous(batch, p, p, phase='prefill', cohort_batch=cohort, local_batch=batch, media_tokens=_declared_media_tokens(spec), **lanes), 'prefill')
    context = max(0, spec.prompt_tokens + max(1, spec.max_tokens) // 2); gb = clamp_graph_bucket(spec.graph_bucket, batch, spec.dp, spec.graph_buckets); raw_lb = batch; qtokens = max(1, spec.tokens_per_sequence)
    reqs = tuple((RequestGeometry(qtokens, context, phase='decode') for _ in range(batch))); return WorkloadGeometry(reqs, graph_bucket=gb, cohort_batch=cohort, phase='decode', local_batch=raw_lb, **lanes)
def _declared_prompts(spec: CellSpec) -> list[int]:
    return [max(1, spec.prompt_tokens)] * max(1, spec.concurrency)
def _prefill_chunk_geometries(spec: CellSpec) -> list[Any]:
    from mindie_sim.prediction.piecewise import WorkloadGeometry
    prompt = max(1, spec.prompt_tokens); budget = _max_batched_tokens(spec) or prompt; chunk = max(1, min(prompt, budget))
    batch = _local_batch(spec); cohort = _ep_batch(spec); lanes = _lane_kwargs(spec)
    media = _declared_media_tokens(spec)
    return [_apply_pcp_geometry(spec, WorkloadGeometry.homogeneous(batch, min(chunk, prompt - start), min(chunk, prompt - start) + start, phase='prefill', cohort_batch=cohort, local_batch=batch, media_tokens=(media if start == 0 else 0), **lanes), 'prefill') for start in range(0, prompt, chunk)]
@lru_cache(maxsize=256)
def _cohort_case(spec: CellSpec) -> Path | None:
    if spec.source_case_dir is None: return None
    case_dir = Path(spec.source_case_dir); path = case_dir.parent.parent / 'cases' / f'{case_dir.name}.json'
    return path if path.is_file() else None
def _max_batched_tokens(spec: CellSpec) -> int | None:
    cohort = _load_json(_cohort_case(spec)) if _cohort_case(spec) is not None else None
    raw = cohort if isinstance(cohort, Mapping) else _raw_case(spec)
    rt = raw.get('runtime') if isinstance(raw.get('runtime'), Mapping) else {}
    value = raw.get('max_num_batched_tokens') or (rt.get('max_num_batched_tokens') if isinstance(rt, Mapping) else None)
    return int(value) if isinstance(value, int) and value > 0 else None
def _ttft_wave_scale(spec: CellSpec, layers: int) -> float:
    """Deprecated H2 wave diagnostic; never used by the production prediction."""
    from mindie_sim.prediction.piecewise import ttft_wave_scale; return ttft_wave_scale(phase=spec.phase, concurrency=spec.concurrency, dp=spec.dp, ep=_ep_ranks(spec), layers=layers, graph_buckets=tuple(spec.graph_buckets), prompt_tokens=spec.prompt_tokens, max_batched_tokens=_max_batched_tokens(spec))
def _service_ttft_overhead_ms(spec: CellSpec, layers: int=0) -> float:
    """Deprecated closed-form service-span diagnostic; never production."""
    del layers; from mindie_sim.prediction.piecewise import service_ttft_overhead_ms; return service_ttft_overhead_ms(prompt_tokens=spec.prompt_tokens, tp=spec.tp, ep=_ep_ranks(spec))
def _stages_of(costs: Sequence[Any], supply: Any = None) -> list[Any]:
    """Causal segments for actual costs; never bare work tuples."""
    from mindie_sim.prediction.piecewise.composition import operator_segment
    return [operator_segment(cost, supply) for cost in costs]

def _ops_of(ev: Any) -> Sequence[Any]: return getattr(ev, 'costs', None) or ev.operators
try: from .zero_shot_piecewise_report import _fused_mechanism, _native_bound, _publish_rows  # noqa: E402
except ImportError: from zero_shot_piecewise_report import _fused_mechanism, _native_bound, _publish_rows  # noqa: E402
try: from .zero_shot_piecewise_report import _aggregate, _dual_moe  # noqa: E402
except ImportError: from zero_shot_piecewise_report import _aggregate, _dual_moe  # noqa: E402
@dataclass(frozen=True)
class PreparedCell:
    """One resolved CellSpec, cache key and compiled record for all consumers."""
    spec: CellSpec
    key: tuple[Any, ...]
    compiled: tuple[Any, ...] | None
    prediction: Prediction | None = None
    error: str = ''


def prepare_compiled_cell(spec: CellSpec) -> PreparedCell:
    """Resolve source identity once, then read the same compiled record.

    ``predict_cell``, scalar chunk and batch chunk use this handoff instead of
    independently guessing the fingerprint/key.  It does not run a full
    service evaluation; it only prepares/compiles the existing model record.
    """
    resolved = resolve_and_apply_source(spec)
    try:
        key = (resolved.dataset, _structure_fingerprint(resolved))
    except ValueError as error:
        return PreparedCell(resolved, (), None, error=f'fingerprint_error:{error}')
    prediction = None
    if key not in _COMPILED_MODELS:
        prediction = predict_cell(resolved)
    compiled = _COMPILED_MODELS.get(key)
    if compiled is None:
        reason = 'chunk_model_not_compiled'
        if prediction is not None and prediction.notes:
            reason = f"chunk_model_not_compiled:{prediction.notes[0]}"
        return PreparedCell(resolved, key, None, prediction=prediction, error=reason)
    return PreparedCell(resolved, key, tuple(compiled), prediction=prediction)


def predict_cell(spec: CellSpec, *, measured_mac: Mapping[str, Any] | None = None, measured_hardware: str | None = None, measured_hccl: Mapping[str, Any] | None = None, measured_supply: Any | None = None) -> Prediction:
    # Direct CellSpec callers and cell_from_dict share the same file resolution.
    spec = resolve_and_apply_source(spec)
    empty = Prediction(spec.cell_id, spec.model_label, 0, {}, {}, 0.0, None, None, (), ('no_model_case',), formal_point=False)
    if spec.model_case is None or not spec.model_case.exists(): return replace(empty, notes=('no_model_case',))
    if spec.source_reject_reason: return replace(empty, notes=(f'source_override_rejected:{spec.source_reject_reason}',))
    if spec.require_source:
        if str(spec.dataset) == 'out' or spec.source_deploy_sha256:
            if spec.source_config is None or not spec.source_deploy_sha256 or spec.source_deploy_sha256 != spec.source_config_sha256:
                return replace(empty, notes=('deploy_identity_missing_or_mismatch',))
        else:
            if spec.source_config is None or not spec.source_file_sha256:
                return replace(empty, notes=('source_file_identity_missing',))
            try:
                actual_source_sha = hashlib.sha256(spec.source_config.read_bytes()).hexdigest()
            except TimeoutError:
                raise
            except OSError:
                return replace(empty, notes=('source_file_unreadable',))
            if actual_source_sha != spec.source_file_sha256:
                return replace(empty, notes=('source_file_sha256_mismatch',))
            if spec.source_config_sha256 and spec.source_config_sha256 != actual_source_sha:
                return replace(empty, notes=('source_config_sha256_mismatch',))
    try: _binding = _source_binding(spec)
    except TimeoutError: raise
    except Exception as error: return replace(empty, notes=(f'case_parse_error:{type(error).__name__}:{error}',))
    spec = replace(spec, source_binding=_binding)
    _binding_key = hashlib.sha256(json.dumps(_binding, sort_keys=True, default=str).encode()).hexdigest()
    from mindie_sim.prediction.piecewise import AnalysisDomain, ImplementationPolicy, OperatorPiecewiseCompiler, PipeSupply; from mindie_sim.prediction.piecewise import service_span as _sp; from mindie_sim.prediction.structure import parse_case; from mindie_sim.prediction.subgraphs.instantiate import FeatureConfig, instantiate_model; from mindie_sim.prediction.subgraphs.state import StateView
    hccl = dict(measured_hccl) if isinstance(measured_hccl, Mapping) else None; hccl_key = hashlib.sha256(json.dumps(hccl, sort_keys=True, default=str).encode()).hexdigest() if hccl else ''; cache_spec = replace(spec, notes=spec.notes + (f'measured_hccl:{hccl_key}',)) if hccl else spec
    try: fp = _structure_fingerprint(cache_spec); cache_key = ((spec.dataset, fp, supply_key(measured_supply)) if measured_supply is not None else (spec.dataset, fp))
    except ValueError as error: return replace(empty, notes=(f'quant_role_error:{error}',))
    if cache_key in _COMPILED_MODELS: layers, notes, supply, unique, counts, state, features, hidden, rpn, links, act_dtype, public_case = _COMPILED_MODELS[cache_key]
    else:
        try: raw_case = _raw_case(spec)
        except TimeoutError: raise
        except Exception as error: return replace(empty, notes=(f'case_parse_error:{type(error).__name__}:{error}',))
        if measured_supply is not None: raw_case = apply_supply(measured_supply, raw_case, measured_hardware)
        try: case = parse_case(raw_case)
        except TimeoutError: raise
        except Exception as error: return replace(empty, notes=(f'case_parse_error:{type(error).__name__}:{error}',))
        model, notes = _model_for_instantiation(case.model, spec); qnote = ((raw_case.get('runtime') or {}).get('metadata') or {}).get('quant_source_note'); notes = notes + (f'quant_source:{qnote}',) if qnote else notes; public_case = replace(case, model=model); cores = max(1, case.machine.dies[0].compute_units)
        features = FeatureConfig.from_runtime(case.runtime, model, machine=case.machine).project(tp=spec.tp, dp=spec.dp, ep=_ep_ranks(spec), pp=spec.pp, cores=cores, graph_buckets=spec.graph_buckets, kv_bf16_override='kv_bf16' in spec.notes)
        if hccl: features = replace(features, metadata=tuple(sorted({**dict(features.metadata), 'a5_native_group2': dict(hccl)}.items())))
        try: instantiated = instantiate_model(model, features)
        except TimeoutError: raise
        except Exception as error: return replace(empty, notes=(f'instantiate_error:{type(error).__name__}:{error}',))
        supply = PipeSupply.from_hardware(case.machine, dtype=_compute_dtype(model, case.machine))
        domain = AnalysisDomain(max_tokens=10 ** 9, max_moe_rows=10 ** 9, max_query_tiles=10 ** 9, max_kv_tiles=10 ** 9, max_index_rows=10 ** 12, max_work=10 ** 15, max_q=10 ** 9, max_s_kv=10 ** 9, max_seq=10 ** 9, max_batch=10 ** 6)
        compiler = OperatorPiecewiseCompiler(supply, ImplementationPolicy(cores=cores), domain=domain); unique, counts = ({}, Counter())
        for instance in instantiated.subgraphs:
            ops_norm = tuple((replace(op, theta=replace(op.theta, extras=tuple(((k, 0 if k in {'require_kv', 'require_index', 'require_selection', 'owner_layer', 'compression_owner', 'kv_owner'} and isinstance(v, int) and (v >= 0) else v) for k, v in op.theta.extras)))) for op in instance.operators))
            instance = replace(instance, instance_id=re.sub(':L\\d+:', ':L0:', instance.instance_id), layer=0 if instance.layer >= 0 else instance.layer, owner_layer=0 if instance.owner_layer is not None and instance.kind in {'A0', 'A1', 'A2', 'K0', 'K1', 'I0', 'I1', 'R1', 'mha_attention', 'gqa_attention', 'mqa_attention', 'attention', 'mla_attention', 'dsa_attention', 'swa_attention', 'csa_attention', 'csa2_attention', 'hca_attention', 'kv_cache', 'kv_compressor', 'indexer_prolog', 'lightning_indexer', 'attn_residual'} else None, operators=ops_norm)
            fprint = instance.fingerprint(); counts[fprint] += 1
            if fprint not in unique: unique[fprint] = compiler.compile(instance, feature_metadata=features.metadata)
        layers, state = (max(1, len(model.layer_plans)), StateView())
        for layer in range(layers): state = state.mark_kv(layer).mark_index(layer).mark_selection(layer)
        if len(_COMPILED_MODELS) >= 64:
            _evict = next(iter(_COMPILED_MODELS))
            _COMPILED_MODELS.pop(_evict, None)
            _COMPILED_DRAFT.pop(_evict, None)
        _COMPILED_MODELS[cache_key] = (layers, notes, supply, unique, counts, state, features, model.hidden_size, int(case.machine.ranks_per_node or 8), tuple(case.machine.links or ()), str(model.activation_dtype or 'bf16'), public_case)
        _COMPILED_HARDWARE[cache_key] = str(case.machine.hardware_key or case.machine.sku or "")
        _COMPILED_SELECTOR[cache_key] = (int(getattr(model, 'top_k', 1) or 1), int(getattr(model, 'num_experts', 0) or max(1, spec.ep)), _ep_ranks(spec), tuple(int(lp.index) for lp in model.layer_plans if str(getattr(lp, 'attention', '')).lower() == 'kda'))
        _COMPILED_DRAFT[cache_key] = any(getattr(instance, 'kind', '') in {'D0', 'spec_decode'} for instance in instantiated.subgraphs)
    hidden, rpn, links, act_dtype = _COMPILED_MODELS[cache_key][7:11]
    has_d0 = _COMPILED_DRAFT.get(cache_key, any(getattr(value.instance, 'kind', '') in {'D0', 'spec_decode'} for value in unique.values()))
    prefill = spec.phase == 'prefill'
    _native_group = _source_native_group(spec)
    _public_projection = None; _public_basis = 'base_compiled_forecast'; _public_error = ''; _public_selected = None; _public_key = None
    _select_top_k, _select_experts, _select_ep, _select_kda = _COMPILED_SELECTOR.get(cache_key, (1, max(1, spec.ep), _ep_ranks(spec), ()))
    # Public graph/execution is the ordinary path whenever the source carries
    # the normalized model/source/input contract.  The graph itself decides
    # dense/PF vs MC2/decode; do not reduce eligibility to a mode/EP tuple.
    if spec.source_config is not None:
        _seqs, _placement_basis = _public_request_placement(spec, _native_group)
        _public_selected, _replica_basis = _public_selected_replica(_native_group)
        _tokens, _context = _public_tokens_context(spec); _public_basis = f'{_placement_basis};{_replica_basis}'
        # DP active vectors describe the full cohort; one target graph consumes
        # the selected replica's own logical sequence count.  Preserve the
        # complete source vector in the key while passing the graph's contract.
        from mindie_sim.prediction.dispatch import cohorts as _cohorts
        _graph_participants = _cohorts(public_case.runtime.parallel)[0]
        _graph_sequences = _seqs
        if isinstance(_seqs, (list, tuple)) and len(_seqs) != len(_graph_participants):
            _graph_sequences = (_seqs[_public_selected],) if 0 <= _public_selected < len(_seqs) else (1,)
        if any(_seqs):
            _public_key = (cache_key, spec.phase, _tokens, _context, tuple(_seqs), _public_selected, 'model',
                           str((_native_group or {}).get('status_sha256') or ''), _binding_key,
                           public_supply_key(public_case))
            if _public_key in _PUBLIC_CACHE:
                _public_projection, _public_error = _PUBLIC_CACHE[_public_key]
            else:
                try:
                    _public_projection = _public_graph_projection(
                        public_case, phase=spec.phase, tokens=_tokens, context=_context,
                        sequences=_graph_sequences, selected_replica=_public_selected, scope='model')
                    if len(_PUBLIC_CACHE) >= 64:
                        _old = next(iter(_PUBLIC_CACHE)); _PUBLIC_CACHE.pop(_old); _PUBLIC_CONSUMED_CACHE.pop(_old, None)
                    _PUBLIC_CACHE[_public_key] = (_public_projection, '')
                except TimeoutError:
                    raise
                except Exception as _error:
                    _public_projection = None
                    _public_error = f'public_projection_error:{type(_error).__name__}:{_error}'
                    _public_basis = 'base_compiled_forecast'
            if _public_projection is not None: _public_projection['basis'] = _public_basis
    _published = _PUBLIC_CONSUMED_CACHE.get(_public_key) if _public_projection is not None and _public_key is not None else None
    if _published is None and _public_projection is not None:
        _published = _public_consume(_public_projection, (), layers=layers, basis=_public_basis)
        if _published is not None and _public_key is not None:
            _PUBLIC_CONSUMED_CACHE[_public_key] = _published
            _PUBLIC_CACHE[_public_key] = ({key: value for key, value in _public_projection.items() if key != 'operators'}, '')
    _public_owns = _published is not None
    _public_l4 = _serving_l4(spec, cache_key, case=public_case) if _public_owns else None
    _public_l4_ready = bool(_public_l4 and ((_public_l4.get('service_ms') is not None) if prefill else (_public_l4.get('body_ms') is not None)))
    prefill = spec.phase == 'prefill'
    include_draft = bool((not prefill) and has_d0 and spec.max_tokens > 1 and _declared_speculation(spec))
    measured_key = "analytic"
    if measured_mac is not None:
        hardware = measured_hardware or _COMPILED_HARDWARE.get(cache_key, "")
        for subgraph in unique.values(): subgraph.clear_measured_mac()
        for subgraph in unique.values(): subgraph.select_measured_mac(measured_mac, hardware=hardware, phase=spec.phase)
        measured_key = hashlib.sha256(json.dumps({
            "id": measured_mac.get("id"), "hardware": hardware,
            "match": measured_mac.get("match"),
            "issue": (measured_mac.get("response") or {}).get("issue"),
            "loads": [{k: item.get(k) for k in ("id", "active_owners",
                        "rate_flops_per_s", "measured_issued_flops")}
                      for item in (measured_mac.get("response") or {}).get("loads", ())],
        }, sort_keys=True).encode()).hexdigest()
    else:
        for subgraph in unique.values(): subgraph.clear_measured_mac()
    bounded = str(dict(features.metadata).get('source_placement', '')).lower() == 'ragged' and dict(features.metadata).get('routing_matrix') is None and dict(features.metadata).get('traffic_matrix') is None
    def _cached_agg(s: CellSpec, ph: str, geometry: Any=None, include_draft: bool=False, summary: bool=False) -> tuple[list[OperatorRow], float, dict[str, float], dict[str, float], float | None]:
        if _public_projection is not None and _public_owns:
            if not _public_l4_ready and ph == spec.phase: summary = True
            else: return ((), 0.0, {}, {}, None)
        g = geometry or _geometry(s, ph)
        _native_key = None if _native_group is None else (
            str(_native_group.get('source_case_dir')), str(_native_group.get('status_sha256')),
            int(_native_group.get('selected_rank', 0)),
            tuple((int(x.get('ep')), x.get('device_id')) for x in _native_group.get('observed') or ()),
            tuple(_native_group.get('active_counts') or ()))
        k = (cache_key, ph, g, measured_key, bool(include_draft), _native_key, bool(summary))
        if k not in _AGG_CACHE:
            if len(_AGG_CACHE) >= 128: _AGG_CACHE.clear()
            r, b, pl, sg = _aggregate(unique, counts, g, state, [], include_draft=include_draft, features=features, supply=supply, publish_fused=True, build_rows=not summary)
            dual = None if summary else _dual_moe(r, supply, layers)
            if summary: r, pl, sg = (), {}, {}
            else: r = tuple(replace(row, cost=None) for row in r)
            _AGG_CACHE[k] = (r, b, pl, sg, dual)
        return _AGG_CACHE[k]
    geoms = _prefill_chunk_geometries(spec) if prefill else []
    if prefill and len(geoms) > 1:
        aggs = [_cached_agg(spec, 'prefill', g) for g in geoms]; prefill_rows = tuple(row for agg in aggs for row in agg[0]); prefill_body = sum(agg[1] for agg in aggs); prefill_per_layer = defaultdict(float); prefill_subgraphs = defaultdict(float); pf_dual = None
        for agg in aggs: prefill_per_layer.update(((k, prefill_per_layer[k] + v) for k, v in agg[2].items())); prefill_subgraphs.update(((k, prefill_subgraphs[k] + v) for k, v in agg[3].items()))
    else: prefill_rows, prefill_body, prefill_per_layer, prefill_subgraphs, pf_dual = _cached_agg(spec if prefill else replace(spec, concurrency=1), 'prefill')
    decode_rows, body, decode_per_layer, decode_subgraphs, dc_dual = (prefill_rows, prefill_body, prefill_per_layer, prefill_subgraphs, pf_dual) if prefill else _cached_agg(spec, 'decode', include_draft=include_draft)
    per_layer = {k: v / layers for k, v in (prefill_per_layer if prefill else decode_per_layer).items()}; subgraphs = {k: v / layers for k, v in (prefill_subgraphs if prefill else decode_subgraphs).items()}
    decode_body, prefill_body_ms = (0.0, body) if prefill else (body, prefill_body); rows_out = tuple(prefill_rows if prefill else decode_rows)
    if spec.pp > 1:
        from dataclasses import replace as _replace; from mindie_sim.prediction.piecewise.composition import p2p_transfer_cost; from mindie_sim.schema.common import dtype_bytes
        cuts = max(0, min(spec.pp, layers) - 1); batch = max(1, _local_batch(spec)); chunks = [batch * max(1, g.requests[0].q_len) for g in _prefill_chunk_geometries(spec)] if prefill else [batch * max(1, spec.tokens_per_sequence)]
        def _pp(qlist: Sequence[int]) -> tuple[float, tuple[OperatorRow, ...]]:
            total = 0.0; made = []
            for chi, qtokens in enumerate(qlist):
                for stage in range(cuts):
                    src = stage * max(1, spec.tp * spec.dp); dst = src + max(1, spec.tp * spec.dp); same_node = src // max(1, rpn) == dst // max(1, rpn); key = 'link_hccs' if same_node else 'link_roce'
                    rate = supply.effective(key) if key in dict(supply.rates) else supply.effective('link'); routed = _replace(supply, rates=tuple(sorted({**dict(supply.rates), 'link': rate}.items())))
                    latency_ms = next((float(getattr(link, 'latency_us', 0.0) or 0.0) / 1000.0 for link in links if (('roce' if not same_node else 'ub') in f"{getattr(link, 'name', '')} {getattr(link, 'channel', '')}".lower())), 0.0)
                    cost = p2p_transfer_cost(stage, qtokens, hidden, dtype_bytes(act_dtype), routed); duration = float(cost.duration_ms) + latency_ms; total += duration
                    made.append(OperatorRow(f'pp_transfer:s{stage}->{dst}:c{chi + 1}', 'PP', 'collective', 'moe', duration, 1, cost.regime or (), cost.dominant_pipe, f"{cost.formula};{key};startup_ms={latency_ms}", int(cost.segment_index), None))
            return total, tuple(made)
        moved, transfer_rows = _pp(chunks); body += moved; per_layer['collective'] = per_layer.get('collective', 0.0) + moved / layers; rows_out = tuple(rows_out) + transfer_rows
        if prefill: prefill_body_ms = body
        else:
            prefill_move, _ = _pp([batch * max(1, g.requests[0].q_len) for g in _prefill_chunk_geometries(spec)]); prefill_body_ms += prefill_move; decode_body = body
        notes = tuple(notes) + (f'pp_transfers:{cuts}',)
    service_ms = body if prefill else prefill_body_ms + decode_body; notes = tuple(notes) + (f'prefill_chunks:{len(geoms)}',) if len(geoms) > 1 and not any(n.startswith('pp_transfers') for n in notes) else tuple(notes)
    body_out = body
    if hasattr(_sp, 'lower_layer_predictions') and not _public_owns: per_layer, subgraphs, body_out, decode_body, prefill_body_ms = _sp.lower_layer_predictions(phase=spec.phase, prompt_tokens=spec.prompt_tokens, concurrency=spec.concurrency, max_tokens=spec.max_tokens, tp=spec.tp, dp=spec.dp, ep=spec.ep, graph_buckets=spec.graph_buckets, graph_bucket=spec.graph_bucket, layers=layers, rows=rows_out, per_layer=per_layer, subgraphs=subgraphs, body_ms=body_out, decode_body_ms=decode_body, prefill_body_ms=prefill_body_ms)
    _public_step = None; _public_events = 0; _serving_basis = 'serving_not_requested'; _serving_status = 'not_requested'; _l4_fallback = ''
    _l4_served = None; _l4_total = None; _l4_boundary = ''; _l4_residual = ''
    if _published is not None:
        _base_body, _base_service = body_out, service_ms
        rows_out, per_layer, subgraphs = _published['rows'], _published['per_layer'], _published['subgraphs']
        subgraphs = _moe_comparison_subgraphs(rows_out, subgraphs, layers, kda_layers=_select_kda)
        _public_step, _public_events = _published['step_ms'], _published['operator_events']
        body_out = _base_body
        if prefill: prefill_body_ms = _published['body_ms']; pf_dual = None
        else: decode_body = _published['body_ms']; dc_dual = None
        _serving = _public_l4 or {}
        _serving_status = str(_serving.get('status') or 'unavailable')
        _l4_served, _l4_total = _serving.get('served'), _serving.get('total')
        _l4_boundary, _l4_residual = str(_serving.get('boundary') or ''), str(_serving.get('residual') or '')
        if prefill and _serving.get('service_ms') is not None:
            service_ms = float(_serving['service_ms']); _serving_basis = str(_serving.get('basis') or 'serving')
        elif not prefill and (_serving.get('body_ms') is not None
                              or _serving.get('service_ms') is not None):
            if _serving.get('body_ms') is not None:
                body_out = float(_serving['body_ms'])
            if _serving.get('service_ms') is not None:
                service_ms = float(_serving['service_ms'])
            _serving_basis = str(_serving.get('basis') or 'serving')
        else:
            body_out, service_ms = _base_body, _base_service
            _serving_basis = str(_serving.get('basis') or 'serving_unavailable')
            _l4_fallback = 'base_structural_no_t14_request_event'
        notes = notes + (f'public_basis:{_public_basis}', f'public_events:{_public_events}',
                         'public_scope:model', f'l3_basis:public_device_graph', f'l4_basis:{_serving_basis}',
                         f'l4_status:{_serving_status}', f'l4_served:{_l4_served}/{_l4_total}',
                         f'l4_boundary:{_l4_boundary or "none"}', f'l4_residual:{_l4_residual or "none"}') + ((f'l4_fallback:{_l4_fallback}',) if _l4_fallback else ())
    elif _public_projection is not None:
        _public_step = None; _public_events = 0; _public_basis = 'base_compiled_forecast'
        notes = notes + ('public_events_none', 'service_basis:base_structural_no_t14_request_event')
    elif _public_error:
        notes = notes + (f'public_unavailable:{_public_error}', 'service_basis:base_structural_no_t14_request_event')
    notes = tuple(notes) + (('bounded_moe_route',) if bounded else ());
    _group = _native_group
    if _group is not None: notes = notes + (f"native_group:{_group['expected_membership']}/{len(_group['observed'])};unknown={','.join(_group['unknown']) or 'none'};selected={_group['selected_rank']}",)
    _status_projection = _public_projection if _public_events else None
    _status_error = _public_error if not _public_events else ''
    _native_status = _native_source_status(spec, _native_group, _status_projection,
                                           basis=_public_basis if _public_step is not None else 'base_compiled_forecast',
                                           selected_replica=_public_selected, error=_status_error)
    if _native_status: _native_status = {**_native_status, 'l3_basis': ('public_device_graph' if _public_events else 'base_compiled_forecast'),
                                         'l4_basis': _serving_basis, 'l4_status': _serving_status,
                                         'l4_served': _l4_served, 'l4_total': _l4_total,
                                         'l4_boundary': _l4_boundary, 'l4_residual': _l4_residual,
                                         **({'fallback_basis': _l4_fallback} if _l4_fallback else {})}
    _route_partial = _source_partial_targets(_binding)
    _partial_targets = (('L1:collective', 'L2:moe', 'L3:body') if bounded else ()) + _route_partial
    _batch_value, _batch_observed, _batch_basis = _local_batch_binding(spec)
    return Prediction(spec.cell_id, spec.model_label, layers, per_layer, subgraphs, body_out, service_ms, pf_dual if prefill else dc_dual, rows_out, tuple(notes) + tuple(spec.notes) + (f'structure:{fp[:12]}', f'local_batch:{_batch_value}', f'local_batch_observed:{int(_batch_observed)}', f'local_batch_basis:{_batch_basis}'), decode_body, prefill_body_ms, formal_point=not bounded, partial_targets=tuple(dict.fromkeys(_partial_targets)), native_status=_native_status, step_ms=_public_step, public_basis=_public_basis if _public_step is not None else 'base_compiled_forecast', public_events=_public_events, source_binding=_binding, routing_status=str(_binding.get('status') or 'unresolved_source_route'))
try: from .zero_shot_piecewise_report import (  # noqa: E402
    _row_chargeable, _l2_driver, _row_for, _component_errors, _phase_body,
    _step_series, _latency_comparison, compare_cell, _fused_evidence, diagnose,
    diagnose_cell, _quantile, aggregate, _step_rows, _category_label,
    cell_to_dict, cell_from_dict, load_benchmark_jsonl, _source_is_blind,
    _no_empirical_curve_fit, acceptance, run_validation, render_markdown, main)
except ImportError: from zero_shot_piecewise_report import (  # noqa: E402
    _row_chargeable, _l2_driver, _row_for, _component_errors, _phase_body,
    _step_series, _latency_comparison, compare_cell, _fused_evidence, diagnose,
    diagnose_cell, _quantile, aggregate, _step_rows, _category_label,
    cell_to_dict, cell_from_dict, load_benchmark_jsonl, _source_is_blind,
    _no_empirical_curve_fit, acceptance, run_validation, render_markdown, main)

if __name__ == "__main__": raise SystemExit(main())
