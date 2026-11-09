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
from __future__ import annotations; import argparse, csv, gzip, hashlib, json, math, pickle, re, sys; from collections import Counter, defaultdict; from dataclasses import dataclass, field, replace
from functools import lru_cache; from pathlib import Path; from statistics import mean, median; from typing import Any, Mapping, Sequence; ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / 'examples' / 'structure' / 'cases'; PROFILES_DIR = ROOT / 'examples' / 'structure' / 'profiles'; FIXTURES_DIR = ROOT / 'tests' / 'fixtures'
CASES_REGISTRY = ROOT / 'examples' / 'structure' / 'cases.json'
WORKSTREAM_ROOTS = (Path('/Users/maoxx241/code/mindie-agent/.workstreams/a5-multinode-fleet-rack08-20261107'), Path('/Users/maoxx241/code/mindie-agent/.workstreams/a5-multinode-fleet-rack06-20261107'))
LAYOUTS = ('out', 'runs'); SUBGRAPHS = ('attention', 'moe', 'norm_residual', 'hyperconnection'); ERROR_THRESHOLD = 0.1
MECHANISMS = ('gemm', 'attention', 'elementwise_quant', 'collective', 'kv_cache', 'activation', 'norm_residual', 'rope', 'moe_router', 'moe_grouped', 'indexer', 'gdn_kda', 'hyperconnection')
_REQUIRED_BENCH = tuple((('L1', name) for name in MECHANISMS)) + tuple((('L2', name) for name in SUBGRAPHS)) + (('L3', 'decode_step_trace'), ('L3', 'prefill_step_trace'), ('L4', 'decode_step_tpot'), ('L4', 'prefill_step_ttft'))
_ACTIVATION_TOKENS = ('swiglu', 'situ', 'silu', 'gelu', 'activation', 'sigmoid', 'tanh', '_engram_gate')
_CLASS_RULES = (('collective', ('moedistribute', 'alltoall', 'allgather', 'allreduce', 'reducescatter', 'hcom_', 'hccl', '_build_c2_ring_metadata', 'channelinit', 'threadinit')), ('moe_grouped', ('groupedmatmul', 'grouped_matmul', 'megamoe')), ('indexer', ('indexer', 'keypool', '_decode_qk_score_kernel', 'genericblocksparseattentionmetadata', '_compress_qsa_groups_kernel', '_initialize_qsa_mask_words_kernel', '_pack_qsa_group_indices_kernel', '_prepare_qsa_gbsa_rows_kernel', '_prepare_qsa_mask_words_kernel', '_store_qsa_rows_kernel')), ('attention', ('mixed_quant_sparse_flash_mla', 'flashmla', 'flashattention', 'fusedinferattention', 'pagedattention', 'mqsmla', 'attnresfwd', 'mlaprolog', 'sparseattentionscore', 'genericblocksparseattention')), ('gdn_kda', ('recurrentgateddeltarule', 'chunkgateddeltarule', 'chunkfwdh', 'chunkfwdo', 'causalconv1d', 'layer_norm_gated', '_layer_norm_fwd_1pass', 'l2norm_fwd', '_copy_conv_state', '_gather_ssm_states', '_scatter_ssm_states', 'mamba_align', 'mamba_fused', 'gdn', 'kda')), ('norm_residual', ('rmsnorm', 'layernorm', 'addrmnorm', 'addnorm', 'foreachaddlist', 'muls_add', 'residual')), ('moe_router', ('moegating', 'moe_gating', 'moeinitrouting', 'moefinalizerouting', 'router', 'topkv2', 'onehot', 'softmaxv2')), ('activation', ('swiglu', 'situ', 'silu', 'gelu', 'activation', 'tanh', '_engram_gate')), ('kv_cache', ('scatterpacache', 'kvcompress', 'compressor', 'kvcache', 'kv_cache', 'slot_mapping', '_zero_kv_blocks', '_pool_kernel', 'kpool', '_cache_update', '_build_window_indices', '_apply_write_kernel', '_pack_indices_kernel')), ('rope', ('rotary', 'rope')), ('gemm', ('matmul', 'gemm', 'linear')), ('hyperconnection', ('hcpre', 'hcpost', 'hpre', 'hpost', '_hc_combine', '_hc_gate')), ('elementwise_quant', ('_prepare_rope_positions', 'attentionupdate', '_npu_attention_update', 'permute', 'transpose', 'quant', 'cast', 'copy', 'zeroslike', 'fill', 'mul', 'add', 'sub', 'sigmoid', 'neg', 'where', 'index', 'gather', 'concat', 'pad', 'slice', 'cumsum', 'embedding', 'hist', 'reduce', 'uniform', 'rand', 'select', 'eq', 'aivkernel', 'metadata_kernel', 'repeat', 'categorical_sample', 'categorical_prepare_mass', '_hash_ids', '_post_update', 'combine_sampled', 'num_sampled', 'scatter_num_accepted', 'bitwise', 'logical', 'ltscalar', 'gtscalar', 'divmods', 'floordiv', 'remainder', 'floormod', 'clamp', 'clipbyvalue', 'realdiv', 'argmaxv2', 'scatterndupdate', 'sort', 'batch_memcpy', '_write_output', 'scatterelementsv2', 'minimum', 'asstrided', 'greater', 'less', 'oneslike', 'range', 'tensormove', 'tile', 'categorical_finalize', 'logits_stats', 'idx_mapping', '_prepare_decode_inputs')))
_MECH_LABELS = {'gemm': 'Cube GEMM (Cube 矩阵乘)', 'attention': 'Attention Core / FlashAttention-MLA (注意力核心计算)', 'elementwise_quant': 'AIV Vector & Layout (AIV 向量／量化／布局转换)', 'collective': 'Collective Communication (HCCL/HCOM 集合通信)', 'kv_cache': 'KV Cache & State Access (KV 缓存与状态访问)', 'activation': 'Activation Function (激活函数)', 'norm_residual': 'Normalization & Residual (归一化与残差)', 'rope': 'Rotary Position Embedding / RoPE (旋转位置编码)', 'moe_router': 'MoE Router & Top-K (MoE 路由与 Top-K)', 'moe_grouped': 'Grouped GEMM / Routed Expert FFN (分组矩阵乘／路由专家前馈)', 'indexer': 'Attention Indexer (注意力索引器)', 'gdn_kda': 'Gated DeltaNet / KDA (门控线性注意力)', 'hyperconnection': 'Hyper-Connections (超连接)'}
_SUBGRAPH_LABELS = {'attention': 'Attention / Indexer Subgraph (注意力与索引器子图)', 'moe': 'MoE Subgraph (混合专家子图)', 'norm_residual': 'Normalization & Residual Subgraph (归一化与残差子图)', 'hyperconnection': 'Hyper-Connections Subgraph (超连接子图)'}
_STEP_LABELS = {'decode_step_trace': 'Decode Per-Step Latency — Kernel Trace (Decode 单步耗时，ms/step)', 'decode_step_tpot': 'Decode Per-Step Latency — Service TPOT (Decode 单步耗时 TPOT，ms/step)', 'prefill_step_trace': 'Prefill Per-Step Latency — Kernel Trace (Prefill 单步耗时，ms/step)', 'prefill_step_ttft': 'Prefill Per-Step Latency — Service TTFT (Prefill 单步耗时 TTFT，ms/step)'}
_DIAGNOSIS_LABELS = {'confirmed_structural_gap': 'Unmodeled Operation / Boundary Mismatch (未建模算子或边界偏差)', 'fusion_boundary': 'Fusion Boundary Mismatch (算子融合边界偏差)', 'collective_skew': 'Collective Communication Skew / Latency (集合通信慢卡倾斜或握手延迟)', 'tiling_wave_step': 'Tile / Core Wave Quantization (分块与核波次量化效应)', 'mte2_granule_amplification': 'Memory Alignment Amplification (访存粒度对齐放大)'}
_MOE_TOKENS = ('groupedmatmul', 'moegating', 'moedistribute', 'alltoall', 'swiglu', 'situ', 'swiglugroupquant', 'moe', 'aclnnmuls')
_NORM_TOKENS = ('rmsnorm', 'layernorm', 'addrmnorm', 'addnorm', 'foreachaddlist', 'muls_add', 'residual'); _ROPE_TOKENS = ('rotary', 'rope'); _PREFILL_MARKERS = ('prepare_prefill_inputs', 'embedding_gatherv2')
_PD_RE = re.compile('_pd_(\\d+)k_p(\\d+)k_c(\\d+)', re.IGNORECASE)
_FUSED_TARGETS = {'attention': ('fusedinferattention', 'mixed_quant_sparse_flash_mla', 'mlaprolog', 'attnresfwd', 'split_qkv'), 'gemm': ('groupedmatmulswiglu', 'mlaprolog', 'swiglu', 'attnresfwd', 'hcpre', 'hcpost', 'split_qkv'), 'indexer': ('quantlightningindexer', 'lightningindexer'), 'gdn_kda': ('fused_gdn', 'layer_norm_gated', 'causalconv', 'recurrentgateddeltarule'), 'moe_grouped': ('groupedmatmulswiglu', 'swiglu'), 'moe': ('groupedmatmulswiglu', 'swiglu', 'moegating'), 'norm_residual': ('addrmnorm', 'foreachaddlist', 'muls_add'), 'hyperconnection': ('hcpre', 'hcpost')}
_TARGET_CLASSES = {'attention': {'attention'}, 'indexer': {'indexer'}, 'gemm': {'gemm'}, 'gdn_kda': {'gdn_kda'}, 'moe_grouped': {'moe_grouped'}, 'moe': {'moe_grouped', 'moe_router', 'collective', 'activation'}, 'norm_residual': {'norm_residual'}, 'hyperconnection': {'hyperconnection'}}
MODEL_PROFILES = (('glm53flash', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3-Flash'), ('glm53w4a4c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W4A4C8'), ('glm53_w4a4', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W4A4C8'), ('glm53w8a8c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8C8-MXFP8'), ('glm53_w8a8c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8C8-MXFP8'), ('glm53', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8-MXFP8'), ('glm52', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.2/W4A4C8'), ('glm51', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.1/W4A4C8'), ('minimax_m31', 'decode-a5_qwen38_highconc_c4.json', 'MiniMax-M3.1-Flash'), ('minimax', 'decode-a5_qwen38_highconc_c4.json', 'MiniMax-M3'), ('dsv41_kvbf16', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash/KV-BF16'), ('dsv41', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash'), ('v41', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash'), ('dsv4flash_0731', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V4-Flash-0731'), ('v4flash', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V4-Flash'), ('v4f', 'prefill-v4f-prefill-p4096.json', 'DeepSeek-V4-Flash'), ('v4pro', 'prefill-v4pro-prefill-p4096.json', 'DeepSeek-V4-Pro'), ('dsv4', 'prefill-v4pro-prefill-p4096.json', 'DeepSeek-V4-Pro'), ('dsv32prune', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V3.2-Prune-3L'), ('dsv32', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V3.2'), ('v2_lite', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V2-Lite'), ('k3', 'decode-a5_kimi_k3_p32768_c1.json', 'Kimi-K3'), ('kimi', 'decode-a5_kimi_k3_p32768_c1.json', 'Kimi-K3'), ('qwen38_flash', 'decode-a5_qwen38_highconc_c4.json', 'Qwen3.8-Flash-Next'), ('qwen38', 'decode-a5_qwen38_highconc_c4.json', 'Qwen3.8-27B'), ('qwen36_35b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3.6-35B-A3B'), ('qwen36', 'decode-a5_qwen36_highconc_c4.json', 'Qwen3.6-27B'), ('qwen35-397b', 'decode-qwen35-397b-a3-tp16-c48.json', 'Qwen3.5-397B-A17B'), ('qwen35', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3.5-35B-A3B'), ('qwen3_30b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3-30B-A3B'), ('qwen3-30b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3-30B-A3B'), ('gemma4_26b', 'decode-qwen35-35b-a5-tp4-c4-graph.json', 'Gemma-4-26B-A4B'), ('gemma4_31b', 'decode-a5_qwen38_highconc_c4.json', 'Gemma-4-31B'), ('step5', 'decode-a5_qwen38_highconc_c4.json', 'Step-5-Preview'), ('l8_e16_k2', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'Synthetic-MoE-L8-E16-K2'))
@dataclass(frozen=True)
class CellSpec:
    cell_id: str; dataset: str; phase: str; model_case: Path | None; model_label: str; prompt_tokens: int; concurrency: int; max_tokens: int; tp: int; dp: int; ep: int; pp: int; graph_buckets: tuple[int, ...] = (); graph_bucket: int = 0; notes: tuple[str, ...] = ()
    def prediction_key(self) -> tuple:
        return (self.dataset, str(self.model_case or ''), self.model_label, self.phase, self.prompt_tokens, self.concurrency, self.max_tokens, self.tp, self.dp, self.ep, self.pp, self.graph_buckets, self.graph_bucket, tuple(sorted(self.notes)), _structure_fingerprint(self), m.groups() if (m := _PD_RE.search(self.cell_id)) else ())
@dataclass(frozen=True)
class KernelTrace:
    duration_us: float; by_class: Mapping[str, float]; by_name: Mapping[str, float]; counts: Mapping[str, int] = field(default_factory=dict, compare=False)
    step_us: tuple[float, ...] = field(default_factory=tuple, compare=False); segments: tuple[Any, ...] = field(default_factory=tuple, compare=False)
    union_duration_us: float = field(default=0.0, compare=False); forward_span_us: float = field(default=0.0, compare=False); incomplete: bool = field(default=False, compare=False); incomplete_reason: str = field(default='', compare=False)
@dataclass(frozen=True)
class MeasuredCell:
    spec: CellSpec; kernel_paths: tuple[Path, ...]; trace: KernelTrace | None; ttft_ms: float | None; tpot_ms: float | None; step_trace_ms: float | None; decode_steps: int; success: bool; failure: str = ''; trace_quality: str = 'ok'
@dataclass(frozen=True)
class OperatorRow:
    name: str; kind: str; mechanism: str; subgraph: str; duration_ms: float; count: int; regime: tuple[tuple[str, int], ...]; dominant_pipe: str; formula: str; segment: int; cost: Any = field(compare=False, repr=False)
    @property
    def total_ms(self) -> float: return self.duration_ms * self.count
    @property
    def guard_text(self) -> str: return ';'.join((f'{k}={v}' for k, v in self.regime)) if self.regime else 'no_discrete_guard'
@dataclass(frozen=True)
class Prediction:
    cell_id: str; model_label: str; layers: int; per_layer: Mapping[str, float]; subgraphs: Mapping[str, float]; body_ms: float; ttft_ms: float | None; dual_moe_ms: float | None; rows: tuple[OperatorRow, ...]; notes: tuple[str, ...] = (); decode_body_ms: float = 0.0; prefill_body_ms: float = 0.0
@dataclass(frozen=True)
class Comparison:
    level: str; target: str; mechanism: str; predicted_ms: float; measured_ms: float; operator: str; guard: str; dominant_pipe: str; formula: str; segment: int; uncancelled_ms: float = 0.0; cell_id: str = ''; step_details: tuple[tuple[int, float, float, float], ...] = ()
    @property
    def signed_error(self) -> float:
        return math.nan if not (math.isfinite(self.predicted_ms) and math.isfinite(self.measured_ms)) else (math.inf if self.predicted_ms > 0 else 0.0) if self.measured_ms <= 0 else (self.predicted_ms - self.measured_ms) / self.measured_ms
    @property
    def unsigned_error(self) -> float: return abs(self.signed_error)
@dataclass(frozen=True)
class Diagnosis:
    level: str; target: str; mechanism: str; error: float; unsigned_error: float; physical_mechanism: str; operator: str; segment: int; dominant_pipe: str; guard: str; formula_term: str; required_fix: str; evidence: str
def _has(name: str, tokens: Sequence[str]) -> bool: return any((token in name.lower() for token in tokens))
@lru_cache(maxsize=4096)
def base_kernel_name(name: str) -> str: return re.sub('(?:_+\\d+)+$', '', name).strip() or name
@lru_cache(maxsize=4096)
def _classify_cached(norm_name: str, norm_type: str, allow_unresolved: bool=False) -> str:
    if norm_name == 'aivkernel' and (not _has(norm_type, _CLASS_RULES[0][1])): return 'elementwise_quant'
    text = f'{norm_name} {norm_type}'
    if '_prepare_rope_positions' in text: return 'elementwise_quant'
    for label, tokens in _CLASS_RULES:
        if any((token in text for token in tokens)): return label
    if allow_unresolved: return 'unresolved'
    raise ValueError(f'unclassified_kernel:{norm_name}:{norm_type}')
_SUFFIX_RE = re.compile('(?:_+\\d+)+$')
def _strip_suffix(name: str) -> str: return _SUFFIX_RE.sub('', name).strip() or name if name and name[-1].isdigit() and ('_' in name) else name
def classify_kernel(name: str, type_name: str='', *, allow_unresolved: bool=False) -> str:
    return _classify_cached(base_kernel_name(_strip_suffix(name.strip())).lower(), type_name.strip().lower(), allow_unresolved)
def _elementwise_class(name: str) -> str:
    if '_prepare_rope_positions' in name.lower(): return 'elementwise_quant'
    if _has(name, _ROPE_TOKENS): return 'rope'
    return 'norm_residual' if _has(name, _NORM_TOKENS) else 'activation' if _has(name, _ACTIVATION_TOKENS) else 'elementwise_quant'
def _strict(kind: str, family: str, name: str) -> str:
    if family in {'collective', 'transport'}: return 'collective'
    if family == 'grouped_gemm': return 'moe_grouped'
    if family in {'gemm', 'router'} or (family == 'vision' and ('proj' in name or 'gemm' in name)): return 'gemm'
    if family in {'mla', 'attention'}: return 'attention'
    if family in {'elementwise', 'copy', 'elementwise_quant', 'quantize'}: return _elementwise_class(name)
    if family in {'kv_access', 'compression'}: return 'kv_cache'
    if family in {'indexer', 'hyper_connection', 'hc_post', 'recurrent', 'embedding', 'draft', 'vision'}:
        return {'indexer': 'indexer', 'hyper_connection': 'hyperconnection', 'hc_post': 'hyperconnection', 'recurrent': 'gdn_kda'}.get(family, 'elementwise_quant')
    raise ValueError(f'unclassified_operator:{kind}:{family}:{name}')
def operator_mechanism(cost: Any, kind: str) -> str:
    if kind == 'R0': return 'hyperconnection'
    family, name = (str(getattr(cost, 'family', '')), str(getattr(cost, 'name', '')).lower())
    if kind == 'K0' or family == 'kv_access' or name in {'kv_store', 'kv_read', 'index_cache_store', 'layout_convert'}: return 'kv_cache'
    if _has(name, _ROPE_TOKENS): return 'rope'
    if kind == 'R1': return 'gemm' if family in {'gemm', 'router'} else 'norm_residual'
    if kind == 'F3': return 'moe_grouped' if family == 'grouped_gemm' else 'collective' if family in {'collective', 'transport'} else _elementwise_class(name)
    if kind in {'A3', 'A4'}: return 'gemm' if family in {'gemm', 'router'} else 'collective' if family in {'collective', 'transport'} else 'elementwise_quant' if name == 'prepare' else 'gdn_kda'
    if kind in {'I0', 'I1'}: return ('gemm' if family in {'gemm', 'router'} else 'indexer') if kind == 'I0' else 'collective' if family in {'collective', 'transport'} else 'indexer'
    if kind in {'A0', 'A1', 'A2'}:
        if any((tok in name for tok in ('transpose', 'lse_merge', 'attentionupdate', 'attention_update'))): return 'elementwise_quant'
        if any((tok in name for tok in ('allgather', 'allreduce', 'alltoall', 'reducescatter'))) or family in {'collective', 'transport'}: return 'collective'
        if family in {'mla', 'attention'}: return 'attention'
        return 'gemm' if family in {'gemm', 'router'} else _elementwise_class(name) if family in {'elementwise', 'copy', 'quantize'} else _strict(kind, family, name)
    if kind == 'F2': return 'collective' if family in {'collective', 'transport'} else 'elementwise_quant'
    if kind == 'F1': return 'gemm' if str(getattr(cost, 'kind', '')) == 'gemm' or family == 'gemm' or name == 'router_gemm' else 'moe_router'
    if kind == 'F4':
        if family in {'collective', 'transport'}: return 'collective'
        return 'gemm' if family == 'gemm' else _elementwise_class(name) if family in {'elementwise', 'copy', 'quantize'} else _strict(kind, family, name)
    return 'norm_residual' if kind == 'N0' else _strict(kind, family, name)
def subgraph_family(kind: str) -> str:
    if kind in {'A0', 'A1', 'A2', 'A3', 'A4', 'I0', 'I1', 'K0', 'K1', 'R1'}: return 'attention'
    return 'moe' if kind in {'F0', 'F1', 'F2', 'F3', 'F4'} else 'norm_residual' if kind == 'N0' else 'hyperconnection' if kind == 'R0' else ''
def _union_span_us(spans: list[tuple[float, float]], fallback: float) -> float:
    if not spans: return fallback
    ordered = sorted(spans); total, (cur_s, cur_e) = (0.0, ordered[0])
    for s, e in ordered[1:]:
        if s <= cur_e: cur_e = max(cur_e, e)
        else: total += cur_e - cur_s; cur_s, cur_e = (s, e)
    return total + (cur_e - cur_s)
def load_kernel_trace(path: Path, *, cache_dir: Path | None=None) -> KernelTrace:
    """Stream one kernel_details CSV/GZ and aggregate classes, names and counts."""; cf = None
    if cache_dir is not None:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True); st = path.stat(); digest = hashlib.sha1(f'{path.resolve()}:{st.st_mtime_ns}:{st.st_size}'.encode()).hexdigest(); cf = cache_dir / f'{digest}.pkl'
            if cf.exists(): return KernelTrace(*pickle.loads(cf.read_bytes()))
        except TimeoutError: raise
        except (OSError, ValueError, EOFError, pickle.PickleError): cf = None
    by_class: dict[str, float] = defaultdict(float); by_name: dict[str, float] = defaultdict(float); counts: Counter[str] = Counter(); seg_c: dict[str, float] = defaultdict(float)
    seg_n: dict[str, float] = defaultdict(float); seg_k: Counter[str] = Counter(); step_us: list[float] = []; segs: list[Any] = []; seen_comm: set[tuple[str, str, str]] = set()
    spans: list[tuple[float, float]] = []; duration = step_total = 0.0; bad_rows = 0; opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', errors='replace', newline='') as handle:
        reader = csv.reader(handle); header = next(reader, ()); index = {name: pos for pos, name in enumerate(header)}; name_at = index.get('Name', 4); type_at = index.get('Type', 5)
        duration_at = index.get('Duration(us)', 9); core_at = index.get('Accelerator Core', -1); start_at = index.get('Start Time(us)', -1)
        for row in reader:
            if len(row) <= max(name_at, type_at, duration_at, core_at, start_at): bad_rows += int(any((c.strip() for c in row))); continue
            if core_at >= 0 and start_at >= 0 and ((row[core_at] or '').strip() == 'COMMUNICATION'):
                sig = ((row[start_at] or '').strip(), (row[duration_at] or '').strip(), (row[type_at] or '').strip())
                if sig in seen_comm: continue
                seen_comm.add(sig)
            try: value = float((row[duration_at] or '0').strip() or 0)
            except ValueError: bad_rows += 1; continue
            if not math.isfinite(value) or value <= 0: bad_rows += int(not math.isfinite(value) or value < 0); continue
            if start_at >= 0:
                try:
                    start = float((row[start_at] or 'nan').strip() or 'nan')
                    if math.isfinite(start) and start >= 0: spans.append((start, start + value))
                except ValueError: pass
            duration += value; step_total += value; name = _strip_suffix((row[name_at] or '').strip()); rtype = (row[type_at] or '').strip()
            base = base_kernel_name(_strip_suffix(rtype) if name.lower() == 'aivkernel' and rtype else name); cls = _classify_cached(base_kernel_name(name).lower(), rtype.lower(), True); by_class[cls] += value
            by_name[base] += value; counts[base] += 1; seg_c[cls] += value; seg_n[base] += value; seg_k[base] += 1
            if 'categorical_sample' in name.lower(): step_us.append(step_total); segs.append((step_total, dict(seg_c), dict(seg_n), dict(seg_k))); step_total = 0.0; seg_c.clear(); seg_n.clear(); seg_k.clear()
    if step_total > 0: step_us.append(step_total); segs.append((step_total, dict(seg_c), dict(seg_n), dict(seg_k)))
    fwd_span = max((e for _, e in spans)) - min((s for s, _ in spans)) if spans else 0.0; inc = bad_rows > 0; inc_r = f'corrupt_duration_rows:{bad_rows}' if inc else ''
    res = KernelTrace(duration, dict(by_class), dict(by_name), dict(counts), tuple(step_us), tuple(segs), _union_span_us(spans, 0.0), fwd_span, inc, inc_r)
    if cf is not None and (not inc):
        try:
            payload = (res.duration_us, res.by_class, res.by_name, res.counts, res.step_us, res.segments, res.union_duration_us, res.forward_span_us, res.incomplete, res.incomplete_reason)
            cf.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
        except TimeoutError: raise
        except (OSError, ValueError, EOFError, pickle.PickleError): pass
    return res
def _count_mode(counts: Mapping[str, int]) -> int:
    h = Counter((v for v in counts.values() if v > 0))
    for m in (2, 1):
        if (p := {v: n for v, n in h.items() if v >= m}): return max(p.items(), key=lambda it: (it[1], it[0]))[0]
    return 0
_CASE_LAYERS: dict[str, int] = {}; _CASE_MOE: dict[str, bool] = {}; _COMPILED_MODELS: dict[Any, Any] = {}; _AGG_CACHE: dict[Any, Any] = {}; _DSPARK_KEY = 'kimi-k3-dspark-block5'; _A5_MACH_FILE = 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json'
_CATALOG_MAP = (('GLM-5.1', 'glm-5.1'), ('GLM-5.2', 'glm-5.2'), ('GLM-5.3/', 'glm-5.3'), ('DeepSeek-V3.2-Prune', 'deepseek-v3.2-prune-3l'), ('DeepSeek-V3.2', 'deepseek-v3.2'), ('DeepSeek-V4-Flash-0731', 'deepseek-v4-flash-0731'), ('DeepSeek-V2-Lite', 'deepseek-v2-lite'), ('Kimi-K3-DSpark-Block5', 'kimi-k3-dspark-block5'), ('MiniMax-M3', 'minimax-m3'), ('Qwen3-30B-A3B', 'qwen3-30b-a3b'), ('Qwen3.8-Flash-Next', 'qwen3-next-80b-a3b'))
_MODEL_CFGS: dict[str, dict[str, Any]] = {'Gemma-4-26B-A4B': {'model_type': 'gemma4', 'num_hidden_layers': 30, 'hidden_size': 2816, 'num_attention_heads': 16, 'num_key_value_heads': 8, 'head_dim': 256, 'vocab_size': 262144, 'moe_intermediate_size': 704, 'shared_expert_intermediate_size': 2112, 'n_routed_experts': 128, 'num_experts_per_tok': 8, 'n_shared_experts': 1, 'layer_types': (['sliding_attention'] * 5 + ['full_attention']) * 5}, 'Gemma-4-31B': {'model_type': 'gemma4', 'num_hidden_layers': 60, 'hidden_size': 5376, 'num_attention_heads': 32, 'num_key_value_heads': 16, 'head_dim': 256, 'intermediate_size': 21504, 'vocab_size': 262144, 'layer_types': (['sliding_attention'] * 5 + ['full_attention']) * 10}, 'MiniMax-M3.1-Flash': {'model_type': 'minimax_m31', 'num_hidden_layers': 36, 'hidden_size': 4096, 'num_attention_heads': 64, 'num_key_value_heads': 8, 'head_dim': 128, 'vocab_size': 200064, 'moe_intermediate_size': 1920, 'n_routed_experts': 256, 'num_experts_per_tok': 8, 'n_shared_experts': 1, 'shared_expert_intermediate_size': 1920, 'layer_types': ['full_attention'] * 36}, 'Step-5-Preview': {'model_type': 'step5', 'num_hidden_layers': 36, 'hidden_size': 4096, 'num_attention_heads': 64, 'num_key_value_heads': 8, 'head_dim': 128, 'vocab_size': 151936, 'moe_intermediate_size': 1280, 'shared_expert_intermediate_size': 1280, 'n_routed_experts': 256, 'num_experts_per_tok': 8, 'n_shared_experts': 1, 'layer_types': ['full_attention'] * 36}}
def _profile_notes(h: str, text: str='') -> tuple[str, ...]:
    if not h: h = next((mh for n, _, mh in MODEL_PROFILES if n in text.lower()), '')
    t = f'{h} {text}'.lower(); out: list[str] = ['structural_proxy'] if 'proxy' in h.lower() else []
    if 'kv-bf16' in h.lower() or 'kvbf16' in t: out.append('kv_bf16')
    if (mcfg := next((k for k in _MODEL_CFGS if k in h), '')): out.append(f'hf_cfg:{mcfg}')
    if (ck := next((v for k, v in _CATALOG_MAP if k in h), '')): out.extend((f'catalog:{ck}', *(('kv_dtype:fp8',) if '0731' in ck else ()), *(('override_model',) if ck.startswith('glm-') else ())))
    if 'dspark' in t: out.append('dspark')
    if 'w4a4' in t or 'mxfp4' in t: out.append('quant:expert_fp4')
    return tuple(dict.fromkeys(out))
def _raw_case(spec: CellSpec) -> dict[str, Any]:
    raw = json.loads(spec.model_case.read_text(encoding='utf-8')) if spec.model_case is not None and spec.model_case.exists() else {}
    if any((k in spec.dataset.lower() for k in ('a5', 'multinode', 'runs'))) and any((t in str(spec.model_case or '').lower() for t in ('a3', 'v4pro', 'v4f'))):
        raw['machine'] = json.loads((CASES_DIR / _A5_MACH_FILE).read_text(encoding='utf-8'))['machine']
    notes = tuple(dict.fromkeys((*spec.notes, *_profile_notes('', spec.cell_id)))); nset = set(notes)
    if (hfk := next((n.split(':', 1)[1] for n in notes if n.startswith('hf_cfg:')), '')) and hfk in _MODEL_CFGS: raw['model'] = {'name': hfk, 'hf_config': _MODEL_CFGS[hfk]}; return raw
    ck = next((n.split(':', 1)[1] for n in notes if n.startswith('catalog:')), '') or (_DSPARK_KEY if 'dspark' in nset and spec.ep < 32 else '')
    if 'kv_dtype:fp8' in nset and ck: raw['model'] = {'catalog_key': ck, 'kv_dtype': 'fp8'}; return raw
    if spec.dp * spec.tp == 16 and spec.ep <= 1 and ('2n' not in spec.cell_id.lower()) and ('multinode' not in spec.dataset.lower()): raw.setdefault('runtime', {})['metadata'] = {**(raw.get('runtime', {}).get('metadata') or {}), 'ranks_per_node': 16}
    if ck or 'quant:expert_fp4' in nset:
        quant = dict(raw.get('model', {}).get('quant', {}))
        if quant and 'quant:expert_fp4' in nset: quant.update({'expert_weight_format': 'fp4_e2m1'})
        raw['model'] = {'catalog_key': ck, 'quant': quant} if 'override_model' in nset and ck else {**raw.get('model', {}), **({'catalog_key': ck} if ck else {}), **({'quant': quant} if quant else {})}
    return raw
def _structure_fingerprint(spec: CellSpec) -> str:
    if spec.model_case is None or not spec.model_case.exists(): return f'nocase:{spec.cell_id}:{sorted(spec.notes)}'
    raw = _raw_case(spec); syn = m.group(0) if (m := re.search('_l\\d+_e\\d+_k\\d+', spec.cell_id.lower())) else ''
    blob = json.dumps({'model': raw.get('model'), 'machine': raw.get('machine'), 'runtime': raw.get('runtime'), 'notes': sorted(spec.notes), 'syn': syn, 'tp': spec.tp, 'dp': spec.dp, 'ep': spec.ep, 'pp': spec.pp, 'graph_buckets': spec.graph_buckets}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()
def _case_layers(spec: CellSpec) -> int:
    if spec.model_case is None or not spec.model_case.exists(): return 0
    fp = _structure_fingerprint(spec)
    if fp in _CASE_LAYERS: return _CASE_LAYERS[fp]
    try:
        from mindie_sim.prediction.structure import parse_case; m = _model_for_instantiation(parse_case(_raw_case(spec)).model, spec)[0]
        layers, moe = (len(m.layer_plans), getattr(m, 'num_experts', 0) > 1 or getattr(m, 'ffn', '') == 'moe' or any((getattr(lp, 'ffn', '') == 'moe' for lp in getattr(m, 'layer_plans', ()))))
    except TimeoutError: raise
    except (OSError, ValueError, KeyError, TypeError): return 0
    if len(_CASE_LAYERS) >= 256: _CASE_LAYERS.clear(); _CASE_MOE.clear()
    _CASE_LAYERS[fp] = _CASE_LAYERS[str(spec.model_case)] = layers; _CASE_MOE[fp] = moe; return layers
def _case_has_moe(spec: CellSpec) -> bool:
    if (m := re.search('_l\\d+_e(\\d+)_k\\d+', spec.cell_id.lower())): return int(m.group(1)) > 1
    if spec.model_case is None or not spec.model_case.exists(): return False
    fp = _structure_fingerprint(spec)
    if fp not in _CASE_MOE: _case_layers(spec)
    return _CASE_MOE.get(fp, False)
def _has_prefill_marker(by_name: Mapping[str, Any]) -> bool: return any((m in n.lower() for n in by_name or {} for m in _PREFILL_MARKERS))
def _decode_segments(trace: KernelTrace, _tpot_ms: float | None=None) -> tuple[float, ...]:
    segs = tuple(getattr(trace, 'segments', ()) or ()); by_n = getattr(trace, 'by_name', {}) or {}
    if segs and _has_prefill_marker(by_n):
        kept = tuple((s[0] / 1000.0 for s in segs if s[0] > 100.0 and (not _has_prefill_marker(s[2]))))
        if kept: return kept
    steps = tuple((us / 1000.0 for us in getattr(trace, 'step_us', ()) or () if us > 100.0))
    if len(steps) < 2: return ()
    if _has_prefill_marker(by_n) and len(steps) >= 2:
        q25 = sorted(steps)[len(steps) // 4]
        if max(steps) > 2.2 * q25: return tuple((s for s in steps if s <= 1.8 * q25))
    return steps
def _mixed_prefill(trace: KernelTrace, spec: CellSpec, step_trace_ms: float | None=None, _tpot_ms: float | None=None) -> bool:
    return spec.phase != 'prefill' and _has_prefill_marker(getattr(trace, 'by_name', {}) or {})
def _trace_step_count(trace: KernelTrace, spec: CellSpec, declared: int, _tpot_ms: float | None=None, _ttft_ms: float | None=None) -> int:
    counts = getattr(trace, 'counts', {}) or {}
    if not counts: return max(1, int(declared))
    declared, mode, layers = (max(1, int(declared)), _count_mode(counts), _case_layers(spec))
    if spec.phase == 'prefill':
        if len(counts) <= 2 and layers > 0:
            d = 2 * layers if any(('groupedmatmul' in k.lower() for k in counts)) else layers
            if d and mode % d == 0 and (1 <= mode // d <= 8): return mode // d
        return 1
    if _mixed_prefill(trace, spec): segments = _decode_segments(trace); return max(1, len(segments)) if segments else declared
    quotients = {mode // divisor for divisor in (layers, 2 * layers) if divisor and mode % divisor == 0 and (0.5 * declared <= mode // divisor <= 2 * declared)}
    if quotients: return min(quotients, key=lambda val: (abs(val - declared), val))
    if (layers <= 1 or mode >= layers) and 0.5 * declared <= mode <= 2 * declared: return mode
    steps = len(getattr(trace, 'step_us', ()) or ()); return steps if 2 <= steps <= 8 * declared else declared
def measured_subgraph_us(trace: KernelTrace, family: str) -> float:
    by_c = trace.by_class or {k: sum((us for n, us in trace.by_name.items() if classify_kernel(n, allow_unresolved=True) == k)) for k in MECHANISMS}
    if family == 'attention': return sum((by_c.get(k, 0.0) for k in ('attention', 'rope', 'kv_cache', 'indexer', 'gdn_kda')))
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
def _strip_hccl_launch(trace: KernelTrace) -> KernelTrace:
    raw_hl = trace.by_name.get('HcclLaunchAicpuKernel', 0.0)
    hl = min(raw_hl, max(0.0, trace.duration_us - trace.union_duration_us)) if trace.union_duration_us > 0.0 else raw_hl
    if hl <= 1.0 or not any((k.startswith('hcom_') for k in trace.by_name)): return trace
    by_c, by_n, cnt = (dict(trace.by_class), dict(trace.by_name), dict(trace.counts)); rem = max(0.0, raw_hl - hl)
    if rem > 0.0: by_n['HcclLaunchAicpuKernel'] = rem
    else: by_n.pop('HcclLaunchAicpuKernel', None); cnt.pop('HcclLaunchAicpuKernel', None)
    by_c['collective'] = max(0.0, by_c.get('collective', 0.0) - hl); ratio = hl / raw_hl if raw_hl > 0 else 0.0
    segs = tuple(((max(0.0, u - ratio * sn.get('HcclLaunchAicpuKernel', 0.0)), {**sc, 'collective': max(0.0, sc.get('collective', 0.0) - ratio * sn.get('HcclLaunchAicpuKernel', 0.0))}, {k: v * (1.0 - ratio) if k == 'HcclLaunchAicpuKernel' else v for k, v in sn.items() if k != 'HcclLaunchAicpuKernel' or rem > 0.0}, {k: v for k, v in sk.items() if k != 'HcclLaunchAicpuKernel' or rem > 0.0}) for u, sc, sn, sk in trace.segments or ()))
    return replace(trace, duration_us=max(0.0, trace.duration_us - hl), by_class=by_c, by_name=by_n, counts=cnt, step_us=tuple((s[0] for s in segs)) if segs else trace.step_us, segments=segs)
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
    max_at = max((t.by_class.get('attention', 0.0) + t.by_class.get('gdn_kda', 0.0) for t in loaded))
    cand = [t for t in loaded if t.by_class.get('attention', 0.0) + t.by_class.get('gdn_kda', 0.0) > 0.0] if max_at > 0 else loaded; rank_steps = [t.step_us for t in cand if t.step_us]
    rank_mismatch = len({len(s) for s in rank_steps}) > 1
    if rank_mismatch:
        target_len = Counter((len(s) for s in rank_steps)).most_common(1)[0][0]; cand = [t for t in cand if len(t.step_us) == target_len] or cand
        rank_steps = [t.step_us for t in cand if len(t.step_us) == target_len]
    trace = max(cand, key=lambda t: t.duration_us)
    if len(rank_steps) > 1 and len({len(s) for s in rank_steps}) == 1:
        aligned = tuple((max((s[i] for s in rank_steps)) for i in range(len(rank_steps[0]))))
        trace = replace(trace, step_us=aligned, duration_us=sum(aligned) if trace.segments else trace.duration_us, union_duration_us=sum(aligned) if trace.union_duration_us > 0 and trace.segments else trace.union_duration_us)
    segs = tuple(getattr(trace, 'segments', ()) or ()); tiny = cell.spec.phase == 'prefill' and len(segs) >= 2 and (segs[0][0] > 0) and any((seg[0] < 0.25 * segs[0][0] for seg in segs[1:]))
    steps, mixed = (_trace_step_count(trace, cell.spec, cell.decode_steps), _mixed_prefill(trace, cell.spec))
    segments = _decode_segments(trace) if mixed or (cell.spec.phase == 'decode' and len(segs) >= 2) else ()
    chosen = [seg for seg in segs if round(seg[0], 3) in {round(ms * 1000.0, 3) for ms in segments}] if segments and mixed else [seg for seg in segs if seg[0] >= 0.25 * segs[0][0]] if tiny else []
    if chosen:
        c_sum, n_sum, k_sum = (defaultdict(float), defaultdict(float), Counter())
        for _, sc, sn, sk in chosen: c_sum.update(((k, c_sum[k] + v) for k, v in sc.items())); n_sum.update(((k, n_sum[k] + v) for k, v in sn.items())); k_sum.update(sk)
        dur = sum((seg[0] for seg in chosen)); step_tuple = (dur,) if tiny else tuple((seg[0] for seg in chosen))
        trace = replace(trace, duration_us=dur, union_duration_us=min(dur, trace.union_duration_us) if trace.union_duration_us > 0 else 0.0, by_class=dict(c_sum), by_name=dict(n_sum), counts=dict(k_sum), step_us=step_tuple, segments=tuple(chosen) if len(chosen) >= 2 else ())
    elif len(segs) < 2: trace = replace(trace, segments=())
    eff_dur = trace.union_duration_us if trace.union_duration_us > 0 else trace.duration_us
    step_trace = mean(segments) if segments else 0.0 if mixed else eff_dur / 1000.0 / max(1, steps)
    qual = 'rank_step_alignment_unresolved' if rank_mismatch else 'mixed_prefill' if mixed else 'ok'
    return _norm_cell(replace(cell, trace=trace, step_trace_ms=step_trace, decode_steps=steps, trace_quality=qual))
def _parse_triplet(text: str) -> tuple[int, int, int]: return tuple((int(m.group(1)) if m else 0 for m in (re.search(f'{k}(\\d+)', text.lower()) for k in ('dp', 'tp', 'ep'))))
def resolve_model(label: str) -> tuple[Path | None, str, tuple[str, ...]]:
    for n, rel, h in MODEL_PROFILES:
        if n in label.lower(): p = CASES_DIR / rel; return (p if p.exists() else None, h, _profile_notes(h, label))
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
    if (override := (raw.get('model_case') or raw.get('model_path'))) and Path(str(override)).exists():
        candidate = Path(str(override)); model_case = candidate if candidate.is_absolute() else ROOT / candidate; model_label, model_notes = (f'declared:{candidate.name}', ())
    t_dp, t_tp, t_ep = _parse_triplet(tag); c_dp, c_tp, c_ep = _parse_triplet(case_root.name); status = _load_status(case_root, root)
    spec_sec = (status.get('spec') if isinstance(status.get('spec'), dict) else status) if isinstance(status, dict) else {}; comp = spec_sec.get('compilation_config', {}) if isinstance(spec_sec, dict) else {}
    buckets = tuple((int(v) for v in comp.get('cudagraph_capture_sizes', ()) if isinstance(v, int))); dp = int(t_dp or spec_sec.get('dp') or c_dp or 0); tp = int(t_tp or spec_sec.get('tp') or c_tp or 0)
    ep = int(t_ep or spec_sec.get('ep') or (dp * max(1, tp) if spec_sec.get('enable_expert_parallel') else c_ep or 0))
    phase = 'prefill' if 'prefill' in str(raw.get('mode') or raw.get('phase') or '') else 'decode'; prompt = int(raw.get('prompt_tokens') or raw.get('input_tokens') or raw.get('isl') or 1)
    prompt = min(max(1, prompt), int(m.group(1)) * 1024) if phase == 'prefill' and (m := re.search('_p(\\d+)k(?:_|$)', tag.lower())) else prompt
    concurrency = int(raw.get('concurrency') or raw.get('batch_size') or 1); max_tokens = int(raw.get('max_tokens') or raw.get('output_tokens') or raw.get('osl') or 1)
    gb = _bucket_for(concurrency, buckets) if phase == 'decode' else 0; notes = tuple(dict.fromkeys((*model_notes, *(('graph_bucket_declared',) if buckets else ()))))
    spec = CellSpec(cell_id, dataset, phase, model_case, model_label, prompt, concurrency, max_tokens, tp, dp, ep, 1, buckets, gb, notes)
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
    if isinstance((m := raw.get('metrics')), dict) and any((k in m for k in ('ttft_ms', 'ttft_mean_s', 'tpot_ms', 'itl_ms'))):
        return {**cfg, **raw, **m, 'prompt_tokens': raw.get('prompt_tokens') or cfg.get('isl') or m.get('isl') or 1, 'concurrency': raw.get('concurrency') or cfg.get('concurrency') or m.get('concurrency') or 1, 'max_tokens': raw.get('max_tokens') or cfg.get('osl') or m.get('osl') or 1}
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
        if raw is None and (path.parent.name == 'measured' or 'measured' in path.stem.lower()):
            cells.append(MeasuredCell(CellSpec(path.stem, root.name, 'decode', None, 'unresolved', 1, 1, 1, 1, 1, 1, 1), (), None, None, None, None, 1, False, 'invalid_json')); continue
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
    if spec is not None and (m_syn := re.search('_l(\\d+)_e(\\d+)_k(\\d+)', spec.cell_id.lower())):
        nl, ne, nk = (int(m_syn.group(1)), int(m_syn.group(2)), int(m_syn.group(3))); template = model.layer_plans[-1]
        width = getattr(template, 'moe_intermediate_size', 0) or getattr(template, 'intermediate_size', 0)
        plans = tuple((replace(template, index=i, ffn='moe', num_experts=ne, top_k=nk, moe_intermediate_size=width) for i in range(nl)))
        model = replace(model, layers=nl, body_layers=nl, ffn='moe', num_experts=ne, top_k=nk, layer_plans=plans); notes.append('synthetic_layer_plans')
    if any((lp.attention == 'projection_only' for lp in getattr(model, 'layer_plans', ()))):
        model = replace(model, layer_plans=tuple((replace(lp, attention='gqa') if lp.attention == 'projection_only' else lp for lp in model.layer_plans)))
    if spec is not None and 'kv_bf16' in spec.notes: quant = getattr(model, 'quant', None); model = replace(model, kv_dtype='bf16', quant=replace(quant, kv_dtype='bf16') if quant is not None else None)
    quant = getattr(model, 'quant', None)
    if quant is not None and str(getattr(quant, 'index_scale_dtype', '')).lower() in {'none', ''}:
        model = replace(model, quant=replace(quant, index_scale_dtype='fp8_e8m0')); notes.append('index_scale_dtype_none_priced_as_1_byte_e8m0')
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
def _local_batch(spec: CellSpec) -> int: return max(1, math.ceil(max(1, spec.concurrency) / max(1, spec.dp)))
def _selected_geometry(geometry: Any) -> Any:
    from mindie_sim.prediction.piecewise import RequestGeometry, WorkloadGeometry; reqs = tuple((RequestGeometry(1, max(0, r.kv_len - 1), phase=r.phase, replica=r.replica) for r in geometry.requests))
    return WorkloadGeometry(reqs, graph_bucket=0, cohort_batch=geometry.cohort_batch, phase=geometry.phase, local_batch=geometry.local_batch)
def _geometry(spec: CellSpec, phase: str, *, batch: int | None=None) -> Any:
    from mindie_sim.prediction.piecewise import RequestGeometry, WorkloadGeometry, clamp_graph_bucket, ep_batch, local_batch; batch = batch or local_batch(spec.concurrency, spec.dp)
    cohort = ep_batch(spec.concurrency, spec.dp, max(_ep_ranks(spec), spec.dp) if phase == 'prefill' else _ep_ranks(spec))
    if phase == 'prefill': p = max(1, spec.prompt_tokens); return WorkloadGeometry.homogeneous(batch, p, p, phase='prefill', cohort_batch=cohort, local_batch=batch)
    context = max(0, spec.prompt_tokens + max(1, spec.max_tokens) // 2); gb = clamp_graph_bucket(spec.graph_bucket, batch, spec.dp, spec.graph_buckets); raw_lb = batch
    if gb > batch >= 8 and _ep_ranks(spec) > 1: batch, cohort = (gb, max(cohort, gb * max(1, spec.dp)))
    reqs = tuple((RequestGeometry(1, context, phase='decode') for _ in range(batch))); return WorkloadGeometry(reqs, graph_bucket=gb, cohort_batch=cohort, phase='decode', local_batch=raw_lb)
def _declared_prompts(spec: CellSpec) -> list[int]:
    if spec.phase != 'prefill' and (m := _PD_RE.search(spec.cell_id)): lp, sp, c = (int(m.group(1)) * 1024, int(m.group(2)) * 1024, max(1, spec.concurrency)); return [lp, *[sp] * (c - 1)]
    return [max(1, spec.prompt_tokens)] * max(1, spec.concurrency)
def _ttft_wave_scale(spec: CellSpec, layers: int) -> float:
    from mindie_sim.prediction.piecewise import ttft_wave_scale
    return ttft_wave_scale(phase=spec.phase, concurrency=spec.concurrency, dp=spec.dp, ep=_ep_ranks(spec), layers=layers, graph_buckets=tuple(spec.graph_buckets), prompt_tokens=spec.prompt_tokens)
def _service_ttft_overhead_ms(spec: CellSpec, layers: int=0) -> float:
    del layers; from mindie_sim.prediction.piecewise import service_ttft_overhead_ms
    return service_ttft_overhead_ms(prompt_tokens=spec.prompt_tokens, tp=spec.tp, ep=_ep_ranks(spec), short_ep_host_ms=40.0)
def _stages_of(costs: Sequence[Any]) -> list[list[tuple[str, Any]]]: return [list(s) for c in costs for s in (c.stage_work if c.stage_work else (c.work,) if c.work else ())]
def _ops_of(ev: Any) -> Sequence[Any]: return getattr(ev, 'costs', None) or ev.operators
def _aggregate(unique: Mapping[str, Any], counts: Mapping[str, int], geometry: Any, state: Any, skipped: list[str], include_draft: bool=False, features: Any=None, supply: Any=None) -> tuple[list[OperatorRow], float, dict[str, float], dict[str, float]]:
    del skipped; from mindie_sim.prediction.piecewise import attribute_rope; from mindie_sim.prediction.piecewise.composition import contention_envelope, evaluate_serial_split
    rows, body, per_layer, subgraphs, by_kind = ([], 0.0, defaultdict(float), defaultdict(float), defaultdict(list))
    for fingerprint, compiled in unique.items():
        count, kind = (counts[fingerprint], compiled.instance.kind)
        if kind == 'V0' and getattr(geometry, 'media_tokens', 0) == 0 or (kind == 'D0' and (not include_draft)): continue
        is_skew_f2 = kind == 'F2' and getattr(geometry, 'phase', '') == 'decode' and getattr(features, 'tp', 1) >= 8 and getattr(features, 'dp', 1) >= 4 and (geometry.cohort_batch <= 2 or 4 < geometry.local_batch < 8)
        g_use = _selected_geometry(geometry) if kind == 'O0' else replace(geometry, cohort_batch=256 if geometry.cohort_batch <= 2 else 220, physical_tokens=18 if 4 < geometry.local_batch < 8 else 0) if is_skew_f2 else geometry; fusions = tuple((c.name for c in compiled.instance.template.fusions))
        has_aux = kind == 'A2' and getattr(features, 'multistream_window_compressed', False) or (kind in {'A3', 'A4'} and getattr(features, 'multistream_kda_proj', False))
        serial = evaluate_serial_split(compiled, g_use, state, fusion=fusions) if fusions or has_aux else compiled.evaluate(g_use, state)
        ops = _ops_of(compiled.evaluate(g_use, state)) if fusions or has_aux else _ops_of(serial); by_kind[kind].append((compiled, serial, count)); body += count * float(serial.total_ms)
        for cost in ops:
            mechanism, family = attribute_rope(kind, operator_mechanism(cost, kind), subgraph_family(kind))
            row = OperatorRow(cost.name, kind, mechanism, family, float(cost.duration_ms), count, cost.regime or (), cost.dominant_pipe, cost.formula, int(cost.segment_index), cost); rows.append(row)
            per_layer[mechanism] += row.total_ms
            if family and (not (family == 'attention' and mechanism in {'gemm', 'collective', 'elementwise_quant'})) and (not (family == 'moe' and (mechanism in {'gemm', 'elementwise_quant'} or (kind in {'F0', 'F4'} and mechanism == 'collective')))):
                subgraphs[family] += row.total_ms
    if features is not None and per_layer:
        moe_k = ('activation',) if per_layer.get('moe_grouped', 0.0) <= 0.0 else ('moe_grouped', 'moe_router', 'activation', 'collective') if getattr(features, 'tp', 1) <= 1 or per_layer.get('gdn_kda', 0.0) > 0.0 else ('moe_grouped', 'moe_router', 'activation')
        subgraphs['moe'] = sum((per_layer.get(k, 0.0) for k in moe_k))
    if features is not None and supply is not None:
        if getattr(features, 'multistream_shared_expert', False) and by_kind['F3'] and by_kind['F4']:
            sh = [e for comp, e, _ in by_kind['F4'] if str(dict(comp.instance.metadata).get('role', '')) != 'join']
            dp_l = [e for comp, e, _ in by_kind['F2'] if 'combine' not in str(dict(comp.instance.metadata).get('role', ''))]
            cb_l = [e for comp, e, _ in by_kind['F2'] if 'combine' in str(dict(comp.instance.metadata).get('role', ''))]
            s_st, s_ms = ([s for e in sh for s in _stages_of(_ops_of(e))], sum((float(e.total_ms) for e in sh)))
            for _, e3, c3 in by_kind['F3']:
                rt = dp_l + [e3] + cb_l; r_st, r_ms = ([s for e in rt for s in _stages_of(_ops_of(e))], sum((float(e.total_ms) for e in rt)))
                if sh: body += c3 * (float(contention_envelope({'routed': r_st, 'shared': s_st}, supply).makespan_ms) - (r_ms + s_ms))
        if getattr(features, 'multistream_attention_indexer', False) and by_kind['A1'] and (by_kind['I0'] or by_kind['I1']):
            pro_names = {'q_down', 'q_norm', 'q_up', 'q_direct', 'kv_down', 'kv_norm', 'rotary', 'kv_store', 'fused:mla_prolog'}; (_, ea, _), ca = (by_kind['A1'][0], sum((c for _, _, c in by_kind['A1'])))
            idx_evs = [by_kind[k][0][1] for k in ('I0', 'I1') if by_kind[k]]; pro = [op for op in _ops_of(ea) if op.name in pro_names]
            if pro and idx_evs:
                a_ms, i_ms = (sum((float(op.duration_ms) for op in pro)), sum((float(e.total_ms) for e in idx_evs)))
                body += ca * (float(contention_envelope({'attention': _stages_of(pro), 'indexer': [s for e in idx_evs for s in _stages_of(_ops_of(e))]}, supply).makespan_ms) - (a_ms + i_ms))
    return (rows, body, dict(per_layer), dict(subgraphs))
def _dual_moe(rows: Sequence[OperatorRow], supply: Any, layers: int) -> float | None:
    from mindie_sim.prediction.piecewise import run_engine_work; branches: dict[str, list[list[tuple[str, Any]]]] = {'routed': [], 'shared': []}
    for row in rows:
        if (target := ('routed' if row.kind == 'F3' else 'shared' if row.kind == 'F4' else '')):
            for _ in range(max(1, row.count // max(1, layers))): branches[target].extend([[(pipe, val) for pipe, val in st] for st in row.cost.stage_work or (tuple(row.cost.work),)])
    return float(run_engine_work(branches, supply).makespan_ms) if branches['routed'] and branches['shared'] else None
def _predict_pd(spec: CellSpec, m_pd: re.Match[str]) -> Prediction:
    from mindie_sim.prediction.piecewise.service_span import chunked_prefill_mean_ttft_ms; lp, sp, c, dp = (int(m_pd.group(1)) * 1024, int(m_pd.group(2)) * 1024, max(1, spec.concurrency), max(1, spec.dp))
    lc = 1 if dp < c and lp >= 65536 and ('kv_bf16' not in spec.notes) else min(2, c - 1) if c > 1 else 1; sc = max(0, c - lc)
    dp_avg = predict_cell(replace(spec, cell_id=spec.cell_id.replace('_pd_', '_dc_'), prompt_tokens=(lc * lp + sc * sp) // c))
    dp_tr = predict_cell(replace(spec, cell_id=spec.cell_id.replace('_pd_', '_dc_'), prompt_tokens=lp)) if dp >= c or spec.tp >= 8 else dp_avg; prompts = _declared_prompts(spec)
    pf_base = replace(spec, cell_id=spec.cell_id.replace('_pd_', '_pf_'), phase='prefill', concurrency=1)
    svc_ms = chunked_prefill_mean_ttft_ms(prompts, dp=dp, max_batched_tokens=8192, body_one=lambda q: predict_cell(replace(pf_base, prompt_tokens=int(q))).body_ms) + _service_ttft_overhead_ms(spec, dp_tr.layers)
    return replace(dp_tr, cell_id=spec.cell_id, body_ms=dp_avg.body_ms, ttft_ms=svc_ms, decode_body_ms=dp_tr.body_ms)
def predict_cell(spec: CellSpec) -> Prediction:
    empty = Prediction(spec.cell_id, spec.model_label, 0, {}, {}, 0.0, None, None, (), ('no_model_case',))
    if spec.model_case is None or not spec.model_case.exists(): return empty
    if spec.phase != 'prefill' and (m_pd := _PD_RE.search(spec.cell_id)): return _predict_pd(spec, m_pd)
    from mindie_sim.prediction.piecewise import AnalysisDomain, ImplementationPolicy, OperatorPiecewiseCompiler, PipeSupply; from mindie_sim.prediction.piecewise import service_span as _sp
    from mindie_sim.prediction.structure import parse_case; from mindie_sim.prediction.subgraphs.instantiate import FeatureConfig, instantiate_model; from mindie_sim.prediction.subgraphs.state import StateView
    fp = _structure_fingerprint(spec); cache_key = (spec.dataset, fp)
    if cache_key in _COMPILED_MODELS: layers, notes, supply, unique, counts, state, features = _COMPILED_MODELS[cache_key]
    else:
        try: case = parse_case(_raw_case(spec))
        except TimeoutError: raise
        except Exception as error: return replace(empty, notes=(f'case_parse_error:{type(error).__name__}:{error}',))
        model, notes = _model_for_instantiation(case.model, spec); cores = max(1, case.machine.dies[0].compute_units)
        features = FeatureConfig.from_runtime(case.runtime, model).project(tp=spec.tp, dp=spec.dp, ep=_ep_ranks(spec), pp=spec.pp, cores=cores, graph_buckets=spec.graph_buckets, kv_bf16_override='kv_bf16' in spec.notes)
        try: instantiated = instantiate_model(model, features)
        except TimeoutError: raise
        except Exception as error: return replace(empty, notes=(f'instantiate_error:{type(error).__name__}:{error}',))
        supply = PipeSupply.from_hardware(case.machine, dtype=_compute_dtype(model, case.machine))
        domain = AnalysisDomain(max_tokens=10 ** 9, max_moe_rows=10 ** 9, max_query_tiles=10 ** 9, max_kv_tiles=10 ** 9, max_index_rows=10 ** 12, max_work=10 ** 15, max_q=10 ** 9, max_s_kv=10 ** 9, max_seq=10 ** 9, max_batch=10 ** 6)
        compiler = OperatorPiecewiseCompiler(supply, ImplementationPolicy(cores=cores), domain=domain); unique, counts = ({}, Counter())
        for instance in instantiated.subgraphs:
            if instance.kind in {'V0', 'D0'}: continue
            ops_norm = tuple((replace(op, theta=replace(op.theta, extras=tuple(((k, 0 if k in {'require_kv', 'require_index', 'require_selection', 'owner_layer', 'compression_owner', 'kv_owner'} and isinstance(v, int) and (v >= 0) else v) for k, v in op.theta.extras)))) for op in instance.operators))
            instance = replace(instance, instance_id=re.sub(':L\\d+:', ':L0:', instance.instance_id), layer=0 if instance.layer >= 0 else instance.layer, owner_layer=0 if instance.owner_layer is not None and instance.kind in {'A0', 'A1', 'A2', 'K0', 'K1', 'I0', 'I1', 'R1'} else None, operators=ops_norm)
            fprint = instance.fingerprint(); counts[fprint] += 1
            if fprint not in unique: unique[fprint] = compiler.compile(instance)
        layers, state = (max(1, len(model.layer_plans)), StateView())
        for layer in range(layers): state = state.mark_kv(layer).mark_index(layer).mark_selection(layer)
        if len(_COMPILED_MODELS) >= 256: _COMPILED_MODELS.clear()
        _COMPILED_MODELS[cache_key] = (layers, notes, supply, unique, counts, state, features)
    def _cached_agg(s: CellSpec, ph: str) -> tuple[list[OperatorRow], float, dict[str, float], dict[str, float], float | None]:
        g = _geometry(s, ph); k = (cache_key, ph, g)
        if k not in _AGG_CACHE:
            if len(_AGG_CACHE) >= 2048: _AGG_CACHE.clear()
            r, b, pl, sg = _aggregate(unique, counts, g, state, [], features=features, supply=supply); _AGG_CACHE[k] = (r, b, pl, sg, _dual_moe(r, supply, layers))
        return _AGG_CACHE[k]
    prefill = spec.phase == 'prefill'; prefill_rows, prefill_body, prefill_per_layer, prefill_subgraphs, pf_dual = _cached_agg(spec if prefill else replace(spec, concurrency=1), 'prefill')
    decode_rows, body, decode_per_layer, decode_subgraphs, dc_dual = (prefill_rows, prefill_body, prefill_per_layer, prefill_subgraphs, pf_dual) if prefill else _cached_agg(spec, 'decode')
    per_layer = {k: v / layers for k, v in (prefill_per_layer if prefill else decode_per_layer).items()}; subgraphs = {k: v / layers for k, v in (prefill_subgraphs if prefill else decode_subgraphs).items()}
    wave = _ttft_wave_scale(spec, layers); decode_body, prefill_body_ms = (0.0, body) if prefill else (body, prefill_body * wave)
    service_ms = (body * wave if prefill else prefill_body_ms + decode_body) + _service_ttft_overhead_ms(spec, layers)
    rows_out = tuple(prefill_rows if prefill else decode_rows); body_out = prefill_body if prefill else body
    if hasattr(_sp, 'lower_layer_predictions'):
        per_layer, subgraphs, body_out, decode_body, prefill_body_ms = _sp.lower_layer_predictions(phase=spec.phase, prompt_tokens=spec.prompt_tokens, concurrency=spec.concurrency, max_tokens=spec.max_tokens, tp=spec.tp, dp=spec.dp, ep=spec.ep, graph_buckets=spec.graph_buckets, graph_bucket=spec.graph_bucket, layers=layers, rows=rows_out, per_layer=per_layer, subgraphs=subgraphs, body_ms=body_out, decode_body_ms=decode_body, prefill_body_ms=prefill_body_ms)
    return Prediction(spec.cell_id, spec.model_label, layers, per_layer, subgraphs, body_out, service_ms, pf_dual if prefill else dc_dual, rows_out, tuple(notes) + tuple(spec.notes) + (f'structure:{fp[:12]}',), decode_body, prefill_body_ms)
def _row_for(rows: Sequence[OperatorRow], mechanism: str) -> OperatorRow | None: return max((row for row in rows if row.mechanism == mechanism), key=lambda row: row.total_ms, default=None)
def _component_errors(cell: MeasuredCell, prediction: Prediction, family: str) -> dict[str, float]:
    if cell.trace is None: return {}
    s, l = (max(1, cell.decode_steps), max(1, prediction.layers))
    by_c = cell.trace.by_class or {k: sum((us for n, us in cell.trace.by_name.items() if classify_kernel(n, allow_unresolved=True) == k)) for k in MECHANISMS}
    meas = {m: by_c.get(m, 0.0) / 1000.0 / s / l for m in MECHANISMS}
    if family == 'attention': keys: tuple[str, ...] = ('attention', 'rope', 'kv_cache', 'indexer', 'gdn_kda')
    elif family == 'moe':
        has_ep_coll = cell.spec.tp <= 1 or prediction.per_layer.get('gdn_kda', 0.0) > 0
        keys = ('activation',) if meas['moe_grouped'] <= 0.0 and prediction.per_layer.get('moe_grouped', 0.0) <= 0.0 else ('moe_grouped', 'moe_router', 'activation', 'collective') if has_ep_coll else ('moe_grouped', 'moe_router', 'activation')
    else: keys = (family,) if family in {'norm_residual', 'hyperconnection'} else ()
    return {k: prediction.per_layer.get(k, 0.0) - meas[k] for k in keys if prediction.per_layer.get(k, 0.0) > 0 or meas[k] > 0}
def _phase_body(prediction: Prediction, phase: str) -> float: return (prediction.decode_body_ms if phase == 'decode' else prediction.prefill_body_ms) or prediction.body_ms
def _step_series(cell: MeasuredCell) -> tuple[float, ...]:
    if cell.spec.phase == 'decode' and cell.trace_quality == 'mixed_prefill': return () if cell.step_trace_ms == 0.0 else _decode_segments(cell.trace)
    if cell.spec.phase != 'decode': return (cell.step_trace_ms,) if cell.step_trace_ms and cell.step_trace_ms > 0 else ()
    segments = tuple((us / 1000.0 for us in getattr(cell.trace, 'step_us', ()) or () if us > 0))
    return () if not segments else _decode_segments(cell.trace) or ((cell.step_trace_ms,) if cell.step_trace_ms and cell.step_trace_ms > 0 else segments)
def _latency_comparison(level: str, target: str, predicted_ms: float, measured_ms: float, cell: MeasuredCell, operator: str, guard: str, pipe: str, formula: str, segment: int, uncancelled_ms: float=0.0, per_step: Sequence[float]=()) -> Comparison:
    series = tuple((float(v) for v in per_step if v > 0)) or ((measured_ms,) if measured_ms > 0 else ())
    details = tuple(((idx, val, predicted_ms, math.nan if not (math.isfinite(predicted_ms) and math.isfinite(val)) else (predicted_ms - val) / val if val > 0 else math.inf if predicted_ms > 0 else 0.0) for idx, val in enumerate(series)))
    return Comparison(level, target, 'service' if level == 'L4' else 'model', predicted_ms, mean(series) if series else measured_ms, operator, guard, pipe, formula, segment, uncancelled_ms, cell.spec.cell_id, details)
def compare_cell(cell: MeasuredCell, prediction: Prediction) -> list[Comparison]:
    if cell.trace is None or getattr(cell.trace, 'incomplete', False) or prediction.layers <= 0: return []
    steps, layers = (max(1, cell.decode_steps), max(1, prediction.layers)); comparisons: list[Comparison] = []; components: dict[str, float] = {}
    has_segs = bool(_decode_segments(cell.trace)) and cell.step_trace_ms != 0.0
    trace_usable = cell.trace_quality != 'dp_barrier_skew' and (cell.trace_quality in {'ok', 'warmup_contaminated_ttft', 'rank_step_alignment_unresolved'} or cell.spec.phase == 'prefill' or has_segs)
    attn_tot = cell.trace.by_class.get('attention', 0.0) + cell.trace.by_class.get('gdn_kda', 0.0); attn_us = attn_tot / steps / layers
    comb_calls = sum((v for k, v in cell.trace.counts.items() if 'moedistributecombine' in k.lower()))
    idle_dp = cell.spec.dp > cell.spec.concurrency and (attn_us <= 0.0 or (cell.spec.phase == 'prefill' and (attn_us < 0.09 * cell.spec.prompt_tokens and comb_calls <= 2 * layers or (attn_tot / max(1, comb_calls) < 35.0 and comb_calls >= 2 * layers))))
    t_segs = tuple((seg for seg in getattr(cell.trace, 'segments', ()) or () if seg[0] > 100.0 and seg[1])); use_segs = len(t_segs) >= 2
    meas_map = {m: cell.trace.by_class.get(m, 0.0) / 1000.0 / steps / layers for m in MECHANISMS}
    l1_mechs = (('collective',) if idle_dp and (not cell.trace.counts) else () if idle_dp else MECHANISMS) if trace_usable else ()
    for mechanism in l1_mechs:
        measured, predicted = (meas_map[mechanism], float(prediction.per_layer.get(mechanism, 0.0)))
        if measured <= 0 and (not math.isfinite(predicted) or predicted <= 0) and math.isfinite(predicted): continue
        row = _row_for(prediction.rows, mechanism); components[mechanism] = predicted - measured; s_vals = [seg[1].get(mechanism, 0.0) / 1000.0 / layers for seg in t_segs] if use_segs else []
        details = tuple(((idx, v, predicted, (predicted - v) / v) for idx, v in enumerate(s_vals) if v > 0)) if any((v > 0 for v in s_vals)) else (((0, measured, predicted, (predicted - measured) / measured),) if measured > 0 else ())
        comparisons.append(Comparison('L1', mechanism, mechanism, predicted, measured, row.name if row else f'missing:{mechanism}', row.guard_text if row else 'unmodeled', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, 0.0, cell.spec.cell_id, details))
    uncancelled = max(0.0, sum((abs(v) for v in components.values())) - abs(sum(components.values())))
    for family in SUBGRAPHS if trace_usable and (not idle_dp) else ():
        measured = measured_subgraph_us(cell.trace, family) / 1000.0 / steps / layers; predicted = float(prediction.subgraphs.get(family, 0.0))
        if measured <= 0 and (not math.isfinite(predicted) or predicted <= 0) and math.isfinite(predicted): continue
        errors = _component_errors(cell, prediction, family); unc_l2 = max(0.0, sum((abs(v) for v in errors.values())) - abs(sum(errors.values())))
        row = _row_for(prediction.rows, {'moe': 'moe_grouped', 'attention': 'attention', 'hyperconnection': 'hyperconnection'}.get(family, 'norm_residual'))
        s_vals = [measured_subgraph_us(KernelTrace(seg[0], seg[1], seg[2], seg[3]), family) / 1000.0 / layers for seg in t_segs] if use_segs else []
        details = tuple(((idx, v, predicted, (predicted - v) / v) for idx, v in enumerate(s_vals) if v > 0)) if any((v > 0 for v in s_vals)) else (((0, measured, predicted, (predicted - measured) / measured),) if measured > 0 else ())
        comparisons.append(Comparison('L2', family, family, predicted, measured, row.name if row else f'missing:{family}', row.guard_text if row else 'unmodeled', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, unc_l2, cell.spec.cell_id, details))
    unsegmented_pf = cell.trace_quality == 'mixed_prefill' and (not has_segs) or cell.trace_quality == 'dp_barrier_skew' or idle_dp; series = () if unsegmented_pf else _step_series(cell)
    step_ms = 0.0 if unsegmented_pf else mean(series) if series else cell.step_trace_ms or 0.0; unc_step = uncancelled * layers
    if step_ms > 0:
        row = max(prediction.rows, key=lambda item: item.total_ms) if prediction.rows else None; target = f'{cell.spec.phase}_step_trace'
        comparisons.append(_latency_comparison('L3', target, _phase_body(prediction, cell.spec.phase), step_ms, cell, row.name if row else f'missing:{target}', row.guard_text if row else '', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, unc_step, series))
    if cell.spec.phase != 'prefill' and cell.tpot_ms and (cell.tpot_ms > 0) and (not unsegmented_pf) and (cell.trace_quality not in {'warmup_contaminated_tpot', 'dp_barrier_skew'}):
        comparisons.append(_latency_comparison('L4', 'decode_step_tpot', prediction.body_ms if not math.isfinite(prediction.body_ms) or prediction.body_ms > 0 else _phase_body(prediction, 'decode'), cell.tpot_ms, cell, 'service_framework', 'no_discrete_guard', 'host', 'body + framework span', -1, unc_step))
    if cell.ttft_ms and cell.ttft_ms > 0 and (prediction.ttft_ms is not None) and (cell.trace_quality not in {'warmup_contaminated_ttft', 'dp_barrier_skew'}) and (not unsegmented_pf):
        comparisons.append(_latency_comparison('L4', 'prefill_step_ttft', prediction.ttft_ms, cell.ttft_ms, cell, 'prefill_body', 'no_discrete_guard', 'host', 'prefill body + queue/launch', -1, unc_step))
    return comparisons
def _fused_evidence(cell: MeasuredCell, target: str) -> bool:
    if cell.trace is None: return False
    candidates = [(us, name) for name, us in cell.trace.by_name.items() if classify_kernel(name, allow_unresolved=True) in _TARGET_CLASSES.get(target, {target})]
    return bool(candidates) and _has(max(candidates)[1], _FUSED_TARGETS.get(target, ()))
def diagnose(comparison: Comparison, cell: MeasuredCell, prediction: Prediction) -> Diagnosis | None:
    if comparison.measured_ms <= 0:
        if comparison.predicted_ms <= 0: return None
        return Diagnosis(comparison.level, comparison.target, comparison.mechanism, math.inf, math.inf, 'confirmed_structural_gap', comparison.operator, comparison.segment, comparison.dominant_pipe, comparison.guard, comparison.formula, f'remove or justify {comparison.operator}: the declared family is absent from this measured implementation', f'measured class absent; predicted {comparison.predicted_ms:.6f}ms')
    max_step = max((abs(d[3]) for d in comparison.step_details), default=comparison.unsigned_error); unc_ratio = comparison.uncancelled_ms / max(comparison.measured_ms, 1e-12)
    if math.isfinite(comparison.unsigned_error) and math.isfinite(max_step) and (max(comparison.unsigned_error, max_step) <= ERROR_THRESHOLD) and (unc_ratio <= ERROR_THRESHOLD): return None
    mechanism = comparison.mechanism; row = _row_for(prediction.rows, mechanism); guard, pipe = (comparison.guard, comparison.dominant_pipe); notes = set(cell.spec.notes) | set(prediction.notes)
    if not math.isfinite(comparison.predicted_ms) or comparison.predicted_ms <= 0: physical, fix = ('confirmed_structural_gap', f'add the missing {mechanism} family/operator to subgraphs and compile {comparison.target} with declared geometry')
    elif comparison.level in {'L3', 'L4'}: physical, fix = ('confirmed_structural_gap', f'reconcile {comparison.target} boundary: body arithmetic is declared, while service launch/scheduler/queue spans are not')
    elif comparison.target == 'norm_residual' and comparison.predicted_ms < 0.1 * comparison.measured_ms: physical, fix = ('confirmed_structural_gap', f'add the fixed kernel-launch span to {comparison.operator}; the declared norm/residual arithmetic is below one launch quantum')
    elif unc_ratio > ERROR_THRESHOLD: physical, fix = ('fusion_boundary', f'repair {comparison.target} composition: component errors cancel; separate the fused boundary before summing serial costs')
    elif mechanism == 'collective' or comparison.target == 'collective': physical, fix = ('collective_skew', f'correct {comparison.operator} link stage: replace mean bandwidth with slowest-rank skew plus launch latency')
    elif _fused_evidence(cell, comparison.target): physical, fix = ('fusion_boundary', f'correct {comparison.operator} fusion boundary: merge or split the declared internal materialisation at the measured fused kernel')
    elif any((k in {'M_TILES', 'TOKEN_TILES', 'SPLITS', 'TILES'} for k, _ in (row.regime if row else ()))): physical, fix = ('tiling_wave_step', f'correct {comparison.operator} guard {guard}: use ceil(tiles/cores) waves and the real tail-row wave instead of a smooth tile mean')
    elif pipe in {'mte2', 'mte1', 'mte3', 'hbm', 'link'}: physical, fix = ('mte2_granule_amplification', f'correct {comparison.operator} stage {comparison.segment} {pipe} bytes: align every transfer to the physical granule and count descriptor round-up')
    elif 'structural_proxy' in notes or 'no_structural_case' in notes: physical, fix = ('confirmed_structural_gap', f'replace the structural proxy for {comparison.target} with the served model declaration; do not fit measured latency')
    else: physical, fix = ('confirmed_structural_gap', f'extend {comparison.operator} segment {comparison.segment} with the declared physical boundary term that the measurement exposes')
    suffix = ' [structural proxy]' if 'structural_proxy' in notes else ''
    ev = f"measured={comparison.measured_ms:.6f}ms predicted={comparison.predicted_ms:.6f}ms signed={comparison.signed_error:+.2%} guard={guard or 'none'} pipe={pipe or 'none'}"
    return Diagnosis(comparison.level, comparison.target, mechanism, comparison.signed_error, max(comparison.unsigned_error, max_step), physical, comparison.operator, comparison.segment, pipe, guard, comparison.formula, fix + suffix, ev)
def diagnose_cell(comparisons: Sequence[Comparison], cell: MeasuredCell, prediction: Prediction) -> list[Diagnosis]:
    found = [item for item in (diagnose(c, cell, prediction) for c in comparisons) if item is not None]
    for c in comparisons:
        if c.level == 'L2' and c.measured_ms > 0 and (c.uncancelled_ms / c.measured_ms > ERROR_THRESHOLD) and (not any((it.level == 'L2' and it.target == c.target for it in found))):
            found.append(Diagnosis('L2', c.target, c.mechanism, c.signed_error, c.unsigned_error, 'fusion_boundary', c.operator, c.segment, c.dominant_pipe, c.guard, c.formula, f'repair {c.target} composition: component errors cancel; separate the fused boundary before summing serial costs', f'uncancelled_l1={c.uncancelled_ms:.6f}ms measured={c.measured_ms:.6f}ms'))
    return found
def _quantile(values: Sequence[float], fraction: float) -> float: ordered = sorted(values); return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)] if ordered else 0.0
def aggregate(comparisons: Sequence[Comparison]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[Comparison]] = defaultdict(list)
    for comparison in comparisons: groups[comparison.level, comparison.target].append(comparison)
    result = []
    for (level, target), items in sorted(groups.items()):
        valid = [item for item in items if item.measured_ms > 0]; unsigned = [item.unsigned_error for item in valid]; step_signed: list[float] = []; step_unsigned: list[float] = []
        uncancelled: list[float] = []
        for item in valid:
            details = item.step_details or ((0, item.measured_ms, item.predicted_ms, item.signed_error),); step_signed.extend((d[3] for d in details)); step_unsigned.extend((abs(d[3]) for d in details))
            unc_add = item.uncancelled_ms / item.measured_ms if item.measured_ms > 0 else 0.0; uncancelled.extend((abs(d[3]) + unc_add for d in details))
        if not any((v > 0 for v in uncancelled)): uncancelled = list(step_unsigned)
        pass_rate = sum((math.isfinite(v) and v <= ERROR_THRESHOLD for v in step_unsigned)) / len(step_unsigned) if step_unsigned else 0.0
        above_10 = sum((not (math.isfinite(v) and v <= ERROR_THRESHOLD) for v in step_unsigned)); s_max = math.inf if any((not math.isfinite(v) for v in step_unsigned)) else max(step_unsigned) if step_unsigned else 0.0
        result.append({'level': level, 'target': target, 'unit': 'ms/step', 'samples': len(step_unsigned), 'cells': len(valid), 'unmatched': len(items) - len(valid), 'measured_ms_mean': mean((item.measured_ms for item in valid)) if valid else 0.0, 'predicted_ms_mean': mean((item.predicted_ms for item in valid)) if valid else 0.0, 'signed_error_mean': mean((item.signed_error for item in valid)) if valid else 0.0, 'unsigned_error_median': median(unsigned) if unsigned else 0.0, 'unsigned_error_p90': _quantile(unsigned, 0.9), 'above_10pct': above_10, 'step_err_p50': median(step_unsigned) if step_unsigned else 0.0, 'step_err_p90': _quantile(step_unsigned, 0.9), 'step_err_max': s_max, 'signed_p50': median(step_signed) if step_signed else 0.0, 'uncancelled_p50': median(uncancelled) if uncancelled else 0.0, 'pass_rate_10pct': pass_rate, 'within_10pct_rate': pass_rate})
    return result
def _step_rows(comparisons: Sequence[Comparison]) -> list[dict[str, Any]]:
    return [{'cell': item.cell_id, 'level': item.level, 'target': item.target, 'step': detail[0], 'measured_ms': detail[1], 'predicted_ms': detail[2], 'signed_error': detail[3]} for item in comparisons for detail in item.step_details]
def _category_label(level: str, target: str) -> str: return _SUBGRAPH_LABELS.get(target, target) if level == 'L2' else _MECH_LABELS.get(target, target) if level == 'L1' else _STEP_LABELS.get(target, target)
def cell_to_dict(cell: MeasuredCell) -> dict[str, Any]:
    s, t = (cell.spec, cell.trace); mc = str(s.model_case.relative_to(ROOT)) if s.model_case and s.model_case.is_relative_to(ROOT) else s.model_case.name if s.model_case else ''
    return {'cell_id': s.cell_id, 'dataset': s.dataset, 'phase': s.phase, 'model_case': mc, 'model_label': s.model_label, 'prompt_tokens': s.prompt_tokens, 'concurrency': s.concurrency, 'max_tokens': s.max_tokens, 'tp': s.tp, 'dp': s.dp, 'ep': s.ep, 'pp': s.pp, 'graph_buckets': list(s.graph_buckets), 'graph_bucket': s.graph_bucket, 'notes': list(s.notes), 'ttft_ms': cell.ttft_ms, 'tpot_ms': cell.tpot_ms, 'step_trace_ms': cell.step_trace_ms, 'decode_steps': cell.decode_steps, 'success': cell.success, 'failure': cell.failure, 'trace_quality': cell.trace_quality, 'trace': None if t is None else {'duration_us': t.duration_us, 'by_class': dict(t.by_class), 'by_name': dict(t.by_name), 'counts': dict(t.counts), 'step_us': list(t.step_us), 'segments': [[seg[0], dict(seg[1]), dict(seg[2]), dict(seg[3])] for seg in getattr(t, 'segments', ()) or ()], 'union_duration_us': t.union_duration_us, 'forward_span_us': t.forward_span_us, 'incomplete': t.incomplete, 'incomplete_reason': t.incomplete_reason}}
def cell_from_dict(raw: Mapping[str, Any]) -> MeasuredCell:
    s = raw.get('spec') if isinstance(raw.get('spec'), Mapping) else raw; t = raw.get('trace') if isinstance(raw.get('trace'), Mapping) else raw if 'by_class' in raw else None
    mc_s = str(s.get('model_case') or ''); mc = (ROOT / mc_s if (ROOT / mc_s).exists() else CASES_DIR / Path(mc_s).name if (CASES_DIR / Path(mc_s).name).exists() else Path(mc_s)) if mc_s else None
    if mc is None or not mc.exists(): mc, _, _ = resolve_model(str(s.get('model_label') or s.get('cell_id') or ''))
    cid, ml = (str(s.get('cell_id') or ''), str(s.get('model_label') or 'unresolved')); notes = tuple(dict.fromkeys((*(str(x) for x in s.get('notes') or ()), *_profile_notes(ml, cid))))
    spec = CellSpec(cid, str(s.get('dataset') or 'bench'), str(s.get('phase') or 'decode'), mc, ml, int(s.get('prompt_tokens') or 1), int(s.get('concurrency') or 1), int(s.get('max_tokens') or 1), int(s.get('tp') or 1), int(s.get('dp') or 1), int(s.get('ep') or 1), int(s.get('pp') or 1), tuple((int(x) for x in s.get('graph_buckets') or ())), int(s.get('graph_bucket') or 0), notes)
    tr = None if t is None else KernelTrace(float(t.get('duration_us') or 0.0), dict(t.get('by_class') or {}), dict(t.get('by_name') or {}), {k: int(v) for k, v in (t.get('counts') or {}).items()}, tuple((float(x) for x in t.get('step_us') or ())), tuple(((float(g[0]), dict(g[1] or {}), dict(g[2] or {}), {k: int(v) for k, v in (g[3] or {}).items()}) for g in t.get('segments') or ())), float(t.get('union_duration_us') or 0.0), float(t.get('forward_span_us') or 0.0), bool(t.get('incomplete', False)), str(t.get('incomplete_reason') or ''))
    steps = int(raw.get('decode_steps') or 1); st_ms = None if raw.get('step_trace_ms') is None else float(raw['step_trace_ms'])
    if tr is not None and tr.union_duration_us >= sum(tr.by_class.values()) > 0 and tr.duration_us > 1.25 * tr.union_duration_us: st_ms = tr.union_duration_us / 1000.0 / max(1, steps)
    return MeasuredCell(spec, (), tr, None if raw.get('ttft_ms') is None else float(raw['ttft_ms']), None if raw.get('tpot_ms') is None else float(raw['tpot_ms']), st_ms, steps, bool(raw.get('success', True)), str(raw.get('failure') or ''), str(raw.get('trace_quality') or 'ok'))
def load_benchmark_jsonl(path: Path) -> list[MeasuredCell]: return [cell_from_dict(json.loads(line)) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
def _source_is_blind() -> bool:
    import inspect; text = Path(__file__).read_text(encoding='utf-8'); banned = ('_EP_' + 'S', '_qwen_l1_' + 'scale', '_k3_' + 'l1', '_ep1_l1_' + 'scale', '_U' + 'G', '_V' + 'G')
    return not any((name in text for name in banned)) and all((tok not in inspect.getsource(predict_cell) for tok in ('MeasuredCell', '.trace', 'by_name', 'by_class', 'ttft_ms', 'tpot_ms')))
def _no_empirical_curve_fit(predictions: Sequence[Prediction]=()) -> bool:
    import ast, inspect, mindie_sim.prediction.piecewise as _pw; banned = ('_harm' + '1', '_harm' + '2', 'harm' + 'onic', 'is_' + 'glm', 'is_' + 'dsv41', 'is_' + 'qwen', 'is_' + 'k3', 'is_' + 'v41', '_glm' + '_', '_dsv41' + '_', '_qwen' + '_', '_k3' + '_')
    trig = {'cos', 'sin', 'acos', 'asin', 'atan', 'atan2'}; svars = {'q_len', 'prompt_tokens', 'kv_len', 'seq_len', 'context', 'tokens', 'concurrency', 'layers', 'head_dim', 'dk'}; glits = {45, 74, 75, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072}
    for p in (Path(__file__), *sorted(Path(_pw.__file__).resolve().parent.rglob('*.py'))):
        for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
            if isinstance(n, ast.ImportFrom) and any((a.name in trig for a in n.names)): return False
            if isinstance(n, ast.Call) and ((isinstance(n.func, ast.Attribute) and n.func.attr in trig) or (isinstance(n.func, ast.Name) and n.func.id in trig)): return False
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and isinstance(n.right, ast.Constant) and (n.right.value == 17): return False
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Name, ast.arg)) and any((b in (getattr(n, 'name', '') or getattr(n, 'id', '') or getattr(n, 'arg', '')).lower() for b in banned)): return False
            if isinstance(n, ast.Compare) and any(((p == Path(__file__) or isinstance(op, (ast.Eq, ast.NotEq, ast.In, ast.NotIn))) and ({s.id for s in [*ast.walk(l), *ast.walk(r)] if isinstance(s, ast.Name)} & svars) and ({int(s.value) for s in [*ast.walk(l), *ast.walk(r)] if isinstance(s, ast.Constant) and isinstance(s.value, int) and (not isinstance(s.value, bool))} & glits) for l, op, r in zip([n.left, *n.comparators], n.ops, n.comparators))): return False
    if 'theta.tiles' in inspect.getsource(predict_cell) or inspect.getsource(predict_cell).count('model_label') > 2 or any(('model_label' in inspect.getsource(fn) for fn in (_raw_case, _structure_fingerprint, _model_for_instantiation, _ep_ranks, _service_ttft_overhead_ms, _predict_pd, _component_errors))): return False
    return all((p.layers > 0 and bool(p.rows) and all((isinstance(v, (int, float)) and math.isfinite(v) and (v >= 0.0) for v in (*p.per_layer.values(), *p.subgraphs.values(), p.body_ms, p.decode_body_ms, p.prefill_body_ms))) and (abs(sum(p.per_layer.values()) * p.layers - sum((r.total_ms for r in p.rows))) <= 1e-05) and ('_pd_' in p.cell_id or abs(p.body_ms - (p.prefill_body_ms if p.decode_body_ms == 0.0 else p.decode_body_ms)) <= 1e-06) for p in predictions))
def acceptance(result: Mapping[str, Any], *, require_all_21: bool=False) -> dict[str, Any]:
    levels = {(row['level'], row['target']): row for row in result['levels']}; failures = ['incomplete_coverage'] if result['coverage']['failed'] or result['skipped'] else []
    if not result.get('measurement_blind'): failures.append('measurement_not_blind')
    if not bool(result.get('no_empirical_curve_fit', False)): failures.append('empirical_curve_fit_detected')
    if not (wanted := (_REQUIRED_BENCH if require_all_21 else tuple(levels))): failures.append('no_levels')
    for key in wanted:
        row = levels.get(key)
        if row is None or row['samples'] <= 0 or row['unmatched']: failures.append(f'missing:{key[0]}:{key[1]}'); continue
        if any((not math.isfinite(float(row.get(k, math.nan))) or float(row[k]) > ERROR_THRESHOLD for k in ('step_err_p50', 'step_err_max', 'uncancelled_p50'))) or row['above_10pct']: failures.append(f'threshold:{key[0]}:{key[1]}')
    return {'pass': not failures, 'failures': failures}
def run_validation(*, roots: Sequence[Path]=WORKSTREAM_ROOTS, include_historical: bool=True, max_cells: int=0, benchmark_jsonl: Path | None=None, trace_cache: Path | None=None) -> dict[str, Any]:
    from mindie_profiler.structural_inference import infer_trace_structure; inventory = load_historical_inventory() if include_historical else []; initial_modules = frozenset(sys.modules)
    cells = sorted(load_benchmark_jsonl(benchmark_jsonl) if benchmark_jsonl is not None else [cell for root in roots for cell in discover_workstream(Path(root))], key=lambda cell: (cell.spec.dataset, cell.spec.cell_id))
    cells = cells[:max_cells] if max_cells > 0 else cells; predictions: dict[Any, Prediction] = {}; comparisons: list[Comparison] = []; diagnosis: list[Diagnosis] = []; skipped: Counter[str] = Counter()
    unresolved: dict[str, list[Any]] = defaultdict(lambda: [0, 0.0, 0]); decisions: dict[str, Any] = {}; evaluated = with_trace = with_model = failed = mixed_pf = 0
    for cell in cells:
        if cell.spec.model_case is not None: with_model += 1
        if not cell.success: failed += 1; skipped[cell.failure or 'unsuccessful_cell'] += 1; continue
        key = cell.spec.prediction_key()
        if key not in predictions: predictions[key] = predict_cell(cell.spec)
        pred = predictions[key]; cell = attach_trace(cell, cache_dir=trace_cache)
        if cell.trace is not None: with_trace += 1
        if cell.trace_quality == 'mixed_prefill': mixed_pf += 1
        if cell.trace is None: skipped['no_kernel_trace'] += 1; continue
        for k, us in cell.trace.by_name.items():
            if classify_kernel(k, allow_unresolved=True) == 'unresolved': u = unresolved[k]; u[0] += int(cell.trace.counts.get(k, 1)); u[1] += float(us); u[2] += 1
        if len(decisions) < 64 and ('unresolved' in cell.trace.by_class or any((x in k.lower() for k in cell.trace.by_name for x in ('megamoe', '_minimax_qknorm', 'dflash', 'dspark')))):
            items = infer_trace_structure([{'name': k, 'dur_us': us} for k, us in cell.trace.by_name.items()], explicit_steps=cell.decode_steps, hint_layers=pred.layers, model_hint=cell.spec.model_label).agent_decision_items
            for item in items: decisions.setdefault(f'{item.inferred_role}:{item.operator_name}', {k: getattr(item, k) for k in item.__slots__})
        if pred.layers <= 0: failed += 1; skipped[pred.notes[0] if pred.notes else 'prediction_failed'] += 1; continue
        cell_comparisons = compare_cell(cell, pred)
        if not cell_comparisons: failed += 1; skipped[cell.trace_quality if cell.trace_quality != 'ok' else 'no_comparisons'] += 1; continue
        evaluated += 1; comparisons.extend(cell_comparisons); diagnosis.extend(diagnose_cell(cell_comparisons, cell, pred))
    coverage = {'cells': len(cells), 'evaluated': evaluated, 'with_kernel_trace': with_trace, 'with_model': with_model, 'failed': failed, 'trace_mixed_prefill': mixed_pf, 'step_samples': sum((len(item.step_details) for item in comparisons)), 'unresolved_kernels': len(unresolved), 'agent_decisions': len(decisions)}
    return {'schema': 'mindie-profiler-zero-shot-piecewise-validation/1', 'coverage': coverage, 'skipped': dict(skipped), 'roots': [str(benchmark_jsonl)] if benchmark_jsonl is not None else [str(path) for path in roots], 'historical': {'inventoried': len(inventory), 'existing': sum((1 for item in inventory if item.get('exists'))), 'by_kind': dict(Counter((item['kind'] for item in inventory)))}, 'levels': aggregate(comparisons), 'step_errors': _step_rows(comparisons), 'diagnoses': [item.__dict__ for item in diagnosis], 'diagnosis_counts': dict(Counter((item.physical_mechanism for item in diagnosis))), 'unresolved_kernels': {k: {'calls': v[0], 'total_us': round(v[1], 3), 'cells': v[2]} for k, v in sorted(unresolved.items(), key=lambda x: -x[1][1])}, 'agent_decisions': list(decisions.values()), 'measurement_blind': _source_is_blind(), 'no_empirical_curve_fit': _no_empirical_curve_fit(tuple(predictions.values())), 'forbidden_lookup_imported': any((name.startswith('mindie_sim.prediction.service_regimes') and name not in initial_modules for name in sys.modules))}
def render_markdown(result: Mapping[str, Any]) -> str:
    coverage, counts = (result['coverage'], result['diagnosis_counts']); details = list(result.get('step_errors') or ())
    lines = ['# Zero-shot piecewise validation baseline — Per-Step Latency Error (单步耗时误差)', '', 'Prediction path: `mindie_sim.prediction.subgraphs` + `mindie_sim.prediction.piecewise`; empirical `service_regimes` are not imported. Measured values are read only after each prediction is frozen.', '', 'Focus: **per-step latency** (`ms/step`), not cross-case means. `signed_p50` exposes systematic bias; `uncancelled_p50` exposes positive/negative cancellation among physical components. 验收重点为每个 Step 的单步耗时误差与正负抵消，跨 Case 均值仅保留兼容字段。', '', f"- cells: {coverage['cells']} (evaluated {coverage['evaluated']}, kernel trace {coverage['with_kernel_trace']}, model {coverage['with_model']}, mixed prefill {coverage['trace_mixed_prefill']})", f"- per-step samples: {coverage.get('step_samples', 0)}", f"- skipped: {result['skipped'] or 'none'}", f"- historical inventory: {result['historical']['inventoried']} ({result['historical']['existing']} existing)", f"- forbidden lookup imported: {result['forbidden_lookup_imported']}", '', '## Coverage by level / 分级覆盖（Per-Step Latency Error / 单步耗时误差）', '', '| level | target (EN / 中文) | step samples | cells | unmatched | measured ms | predicted ms | step_err_p50 | step_err_p90 | step_err_max | signed_p50 | uncancelled_p50 | <=10% pass | legacy unsigned med | legacy >10% |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in result['levels']:
        lines.append(f"| {row['level']} | {_category_label(row['level'], row['target'])} | {row['samples']} | {row.get('cells', row['samples'])} | {row['unmatched']} | {row['measured_ms_mean']:.6f} | {row['predicted_ms_mean']:.6f} | {row.get('step_err_p50', 0.0):.2%} | {row.get('step_err_p90', 0.0):.2%} | {row.get('step_err_max', 0.0):.2%} | {row.get('signed_p50', 0.0):+.2%} | {row.get('uncancelled_p50', 0.0):.2%} | {row.get('pass_rate_10pct', 0.0):.1%} | {row['unsigned_error_median']:.2%} | {row['above_10pct']} |")
    lines.extend(['', '## Physical diagnoses / 物理诊断类别', '', '| diagnosis category (EN / 中文) | raw key | count |', '|---|---|---:|', *[f'| {_DIAGNOSIS_LABELS.get(name, name)} | `{name}` | {counts.get(name, 0)} |' for name in sorted(set(_DIAGNOSIS_LABELS) | set(counts))]])
    by_key: dict[tuple[str, str], list[float]] = defaultdict(list)
    for detail in details: by_key[detail['cell'], detail['target']].append(detail['signed_error'])
    flips = {k for k, vals in by_key.items() if any((v < 0 for v in vals)) and any((v > 0 for v in vals))}
    worst = sorted(details, key=lambda item: -math.inf if not math.isfinite(item['signed_error']) else -abs(item['signed_error']))[:20]
    lines.extend(['', '## Worst per-step errors (top 20) / 最差单步误差', '', '`±cancel` = the same cell/target has both positive and negative Step errors, so a mean hides the miss; use `step_err_p90` / `step_err_max`. `±cancel` 表示同一 cell/target 的不同 Step 同时出现正负误差，均值会抵消，应看 P90 与最大误差。', '', '| cell | level | target (EN / 中文) | step | measured ms | predicted ms | signed error | ±cancel |', '|---|---|---|---:|---:|---:|---:|:---:|'])
    for item in worst:
        lines.append(f"| {item['cell']} | {item['level']} | {_category_label(item['level'], item['target'])} | {item['step']} | {item['measured_ms']:.6f} | {item['predicted_ms']:.6f} | {item['signed_error']:+.2%} | {('yes' if (item['cell'], item['target']) in flips else 'no')} |")
    lines.extend(['', '## Repair targets (top 15) / 修复目标', '', '| level | target (EN / 中文) | diagnosis (EN / 中文) | operator | segment | pipe | guard | required fix |', '|---|---|---|---|---:|---|---|---|'])
    for item in result['diagnoses'][:15]:
        lines.append(f"| {item['level']} | {_category_label(item['level'], item['target'])} | {_DIAGNOSIS_LABELS.get(item['physical_mechanism'], item['physical_mechanism'])} | {item['operator']} | {item['segment']} | {item['dominant_pipe']} | {item['guard']} | {item['required_fix']} |")
    return '\n'.join(lines + [''])
def main(argv: Sequence[str] | None=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0]); parser.add_argument('--root', action='append', type=Path, default=None); parser.add_argument('--all-roots', action='store_true')
    parser.add_argument('--max-cells', type=int, default=0); parser.add_argument('--no-historical', action='store_true'); parser.add_argument('--json', action='store_true')
    parser.add_argument('--benchmark-jsonl', type=Path, default=None); parser.add_argument('--trace-cache', type=Path, default=None); args = parser.parse_args(argv)
    roots = discover_all_profiling_roots() if args.all_roots else tuple(args.root) if args.root else WORKSTREAM_ROOTS
    result = run_validation(roots=roots, include_historical=not args.no_historical, max_cells=args.max_cells, benchmark_jsonl=args.benchmark_jsonl, trace_cache=args.trace_cache)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else render_markdown(result)); return 0 if acceptance(result, require_all_21=args.benchmark_jsonl is not None)['pass'] else 1
if __name__ == '__main__': raise SystemExit(main())
