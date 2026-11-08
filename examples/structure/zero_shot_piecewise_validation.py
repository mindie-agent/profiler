"""Zero-shot piecewise validation over every retained Profiling capture.

[Role] Load historical captures, fixtures and A5 multi-node fleet measured
  JSON / ``request_summary.csv`` / ``kernel_details.csv(.gz)`` pairs; compare
  per-step operator / subgraph / model / service timings with the structural
  piecewise compiler.
[Invariants] Prediction consumes only ``CellSpec``; measured fields stay in
  ``MeasuredCell`` and are read after the prediction is frozen. Only
  ``mindie_sim.prediction.subgraphs`` + ``piecewise`` are used, never
  ``service_regimes``. Every L1-L4 miss keeps its per-step distribution.
[Timeouts & Locks] Bounded local reads and deterministic arithmetic; no network, device, subprocess, sleep, lock or background work.
[Side-Effect Policy] Read-only; the CLI writes the baseline summary to stdout.
"""
from __future__ import annotations
import argparse, csv, gzip, json, math, re, sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from statistics import mean, median
from typing import Any, Mapping, Sequence
ROOT = Path(__file__).resolve().parents[2]
CASES_DIR, PROFILES_DIR, FIXTURES_DIR, CASES_REGISTRY = ROOT / 'examples' / 'structure' / 'cases', ROOT / 'examples' / 'structure' / 'profiles', ROOT / 'tests' / 'fixtures', ROOT / 'examples' / 'structure' / 'cases.json'
WORKSTREAM_ROOTS = (Path('/Users/maoxx241/code/mindie-agent/.workstreams/a5-multinode-fleet-rack08-20261107'), Path('/Users/maoxx241/code/mindie-agent/.workstreams/a5-multinode-fleet-rack06-20261107'))
LAYOUTS = ('out', 'runs')
MECHANISMS = ('gemm', 'attention', 'elementwise_quant', 'collective', 'kv_cache', 'activation', 'norm_residual', 'rope', 'moe_router', 'moe_grouped', 'indexer', 'gdn_kda', 'hyperconnection')
SUBGRAPHS = ('attention', 'moe', 'norm_residual', 'hyperconnection')
ERROR_THRESHOLD = 0.1
_ACTIVATION_TOKENS = ('swiglu', 'situ', 'silu', 'gelu', 'activation', 'sigmoid', 'tanh', '_engram_gate')
_CLASS_RULES = (('collective', ('moedistribute', 'alltoall', 'allgather', 'allreduce', 'reducescatter', 'hcom_', 'hccl', '_build_c2_ring_metadata', 'channelinit', 'threadinit')), ('moe_grouped', ('groupedmatmul', 'grouped_matmul', 'megamoe')), ('indexer', ('lightningindexer', 'indexer', 'keypool', '_decode_qk_score_kernel', 'genericblocksparseattentionmetadata', '_compress_qsa_groups_kernel', '_initialize_qsa_mask_words_kernel', '_pack_qsa_group_indices_kernel', '_prepare_qsa_gbsa_rows_kernel', '_prepare_qsa_mask_words_kernel', '_store_qsa_rows_kernel')), ('attention', ('kvquantsparseflashattention', 'mixed_quant_sparse_flash_mla', 'sparseflashmla', 'flashmla', 'flashattention', 'fusedinferattention', 'mlapagedattention', 'pagedattention', 'mqsmla', 'attnresfwd', 'mlaprolog', 'sparseattentionscore', 'genericblocksparseattention')), ('gdn_kda', ('recurrentkda', 'recurrentgateddeltarule', 'chunkgateddeltarule', 'chunkfwdh', 'chunkfwdo', 'causalconv1d', 'fused_gdn_gating', 'layer_norm_gated', '_layer_norm_fwd_1pass', 'l2norm_fwd', '_copy_conv_state', '_gather_ssm_states', '_scatter_ssm_states', 'mamba_align', 'mamba_fused', 'gdn', 'kda')), ('norm_residual', ('rmsnorm', 'layernorm', 'addrmnorm', 'addnorm', 'foreachaddlist', 'muls_add', 'residual')), ('moe_router', ('moegating', 'moe_gating', 'moeinitrouting', 'moefinalizerouting', 'router', 'topkv2', 'onehot', 'softmaxv2')), ('activation', ('swiglu', 'situ', 'silu', 'gelu', 'activation', 'tanh', '_engram_gate')), ('kv_cache', ('scatterpacache', 'scatterpakvcache', 'kvcompress', 'compressor', 'kvcache', 'kv_cache', 'slot_mapping', '_zero_kv_blocks', '_pool_kernel', '_cache_update', '_build_window_indices', '_apply_write_kernel', '_pack_indices_kernel')), ('rope', ('rotary', 'rope')), ('gemm', ('quantbatchmatmul', 'batchmatmul', 'matmul', 'gemm', 'linear')), ('hyperconnection', ('hcpre', 'hcpost', 'hpre', 'hpost', '_hc_combine', '_hc_gate')), ('elementwise_quant', ('attentionupdate', '_npu_attention_update', 'permute', 'transpose', 'quant', 'cast', 'copy', 'zeroslike', 'fill', 'muls', 'mul', 'adds', 'add', 'sub', 'sigmoid', 'neg', 'where', 'equal', 'index', 'gather', 'concat', 'pad', 'slice', 'arange', 'cumsum', 'embedding', 'hist', 'reduce', 'uniform', 'rand', 'select', 'eq', 'aivkernel', 'metadata_kernel', 'repeat', 'tileaicore', 'categorical_sample', 'categorical_prepare_mass', '_hash_ids', '_post_update', 'combine_sampled', 'num_sampled', 'scatter_num_accepted', 'bitwise', 'logical', 'ltscalar', 'lessaicore', 'gtscalar', 'greateraicore', 'divmods', 'floordiv', 'remainder', 'floormod', 'clamp', 'clipbyvalue', 'realdiv', 'argmaxv2', 'scatterndupdate', 'sort', 'batch_memcpy', '_write_output', '_prepare_dflash', 'scatterelementsv2', 'minimum', '_ple_')))
_MECH_LABELS = {'gemm': 'Cube GEMM (Cube 矩阵乘)', 'attention': 'Attention Core / FlashAttention-MLA (注意力核心计算)', 'elementwise_quant': 'AIV Vector & Layout (AIV 向量／量化／布局转换)', 'collective': 'Collective Communication (HCCL/HCOM 集合通信)', 'kv_cache': 'KV Cache & State Access (KV 缓存与状态访问)', 'activation': 'Activation Function (激活函数)', 'norm_residual': 'Normalization & Residual (归一化与残差)', 'rope': 'Rotary Position Embedding / RoPE (旋转位置编码)', 'moe_router': 'MoE Router & Top-K (MoE 路由与 Top-K)', 'moe_grouped': 'Grouped GEMM / Routed Expert FFN (分组矩阵乘／路由专家前馈)', 'indexer': 'Attention Indexer (注意力索引器)', 'gdn_kda': 'Gated DeltaNet / KDA (门控线性注意力)', 'hyperconnection': 'Hyper-Connections (超连接)'}
_SUBGRAPH_LABELS = {'attention': 'Attention / Indexer Subgraph (注意力与索引器子图)', 'moe': 'MoE Subgraph (混合专家子图)', 'norm_residual': 'Normalization & Residual Subgraph (归一化与残差子图)', 'hyperconnection': 'Hyper-Connections Subgraph (超连接子图)'}
_STEP_LABELS = {'decode_step_trace': 'Decode Per-Step Latency — Kernel Trace (Decode 单步耗时，ms/step)', 'decode_step_tpot': 'Decode Per-Step Latency — Service TPOT (Decode 单步耗时 TPOT，ms/step)', 'prefill_step_trace': 'Prefill Per-Step Latency — Kernel Trace (Prefill 单步耗时，ms/step)', 'prefill_step_ttft': 'Prefill Per-Step Latency — Service TTFT (Prefill 单步耗时 TTFT，ms/step)'}
_DIAGNOSIS_LABELS = {'confirmed_structural_gap': 'Unmodeled Operation / Boundary Mismatch (未建模算子或边界偏差)', 'fusion_boundary': 'Fusion Boundary Mismatch (算子融合边界偏差)', 'collective_skew': 'Collective Communication Skew / Latency (集合通信慢卡倾斜或握手延迟)', 'tiling_wave_step': 'Tile / Core Wave Quantization (分块与核波次量化效应)', 'mte2_granule_amplification': 'Memory Alignment Amplification (访存粒度对齐放大)'}
_ATTENTION_TOKENS = ('flashattention', 'fusedinferattention', 'mlapagedattention', 'pagedattention', 'mqsmla', 'mixed_quant_sparse_flash_mla', 'sparseflashmla', 'flashmla', 'kvquantsparseflashattention', 'scatterpacache', 'scatterpakvcache', 'kvcompress', 'rotary', 'rope', 'split_qkv', 'l2norm', 'attnresfwd', 'mlaprolog', 'quantlightningindexer', 'lightningindexer', 'recurrentkda', 'recurrentgateddeltarule', 'chunkgateddeltarule', 'chunkfwdh', 'chunkfwdo', 'causalconv1d', 'fused_gdn_gating', 'kda', 'layer_norm_gated')
_MOE_TOKENS = ('groupedmatmul', 'moegating', 'moedistribute', 'alltoall', 'swiglu', 'situ', 'swiglugroupquant', 'moe', 'aclnnmuls')
_NORM_TOKENS = ('rmsnorm', 'layernorm', 'addrmnorm', 'addnorm', 'foreachaddlist', 'muls_add', 'residual')
_HYPERCONNECTION_TOKENS = ('hcpre', 'hcpost', 'hpre', 'hpost')
_ROPE_TOKENS = ('rotary', 'rope')
_PREFILL_MARKERS = ('prepare_prefill_inputs', 'embedding_gatherv2'); _MIXED_RATIO = 1.35
_FUSED_TARGETS = {'attention': ('fusedinferattention', 'mixed_quant_sparse_flash_mla', 'mlaprolog', 'attnresfwd', 'split_qkv'), 'gemm': ('groupedmatmulswiglu', 'mlaprolog', 'swiglu', 'attnresfwd', 'hcpre', 'hcpost', 'split_qkv'), 'indexer': ('quantlightningindexer', 'lightningindexer'), 'gdn_kda': ('fused_gdn', 'layer_norm_gated', 'causalconv', 'recurrentgateddeltarule'), 'moe_grouped': ('groupedmatmulswiglu', 'swiglu'), 'moe': ('groupedmatmulswiglu', 'swiglu', 'moegating'), 'norm_residual': ('addrmnorm', 'foreachaddlist', 'muls_add'), 'hyperconnection': ('hcpre', 'hcpost')}
_TARGET_CLASSES = {'attention': {'attention'}, 'indexer': {'indexer'}, 'gemm': {'gemm'}, 'gdn_kda': {'gdn_kda'}, 'moe_grouped': {'moe_grouped'}, 'moe': {'moe_grouped', 'moe_router', 'collective', 'activation'}, 'norm_residual': {'norm_residual'}, 'hyperconnection': {'hyperconnection'}}
MODEL_PROFILES = (('glm53flash', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3-Flash'), ('glm53w4a4c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W4A4C8'), ('glm53w8a8c8', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8C8-MXFP8'), ('glm53', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.3/W8A8-MXFP8'), ('glm51', 'decode-a5_glm53flash_tp8_c4_p8k.json', 'GLM-5.1/W4A4C8'), ('dsv41_kvbf16', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash/KV-BF16'), ('dsv41', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash'), ('v41', 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json', 'DeepSeek-V4.1-Flash'), ('v4flash', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V4-Flash'), ('v4f', 'prefill-v4f-prefill-p4096.json', 'DeepSeek-V4-Flash'), ('v4pro', 'prefill-v4pro-prefill-p4096.json', 'DeepSeek-V4-Pro'), ('dsv4', 'prefill-v4pro-prefill-p4096.json', 'DeepSeek-V4-Pro'), ('dsv32prune', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V3.2-Prune-3L'), ('dsv32', 'decode-v4flash-a3-tp8-c4.json', 'DeepSeek-V3.2'), ('k3', 'decode-a5_kimi_k3_p32768_c1.json', 'Kimi-K3'), ('kimi', 'decode-a5_kimi_k3_p32768_c1.json', 'Kimi-K3'), ('qwen38', 'decode-a5_qwen38_highconc_c4.json', 'Qwen3.8-27B'), ('qwen36', 'decode-a5_qwen36_highconc_c4.json', 'Qwen3.6-27B'), ('qwen35-397b', 'decode-qwen35-397b-a3-tp16-c48.json', 'Qwen3.5-397B-A17B'), ('qwen35', 'decode-a5_qwen35-35b-a5-tp4-c4-graph.json', 'Qwen3.5-35B-A3B'))
@dataclass(frozen=True)
class CellSpec:
    """Measurement-blind declaration for one validation cell."""
    cell_id: str; dataset: str; phase: str; model_case: Path | None; model_label: str
    prompt_tokens: int; concurrency: int; max_tokens: int; tp: int; dp: int; ep: int; pp: int
    graph_buckets: tuple[int, ...] = (); graph_bucket: int = 0; notes: tuple[str, ...] = ()
    def prediction_key(self) -> tuple:
        return (self.dataset, str(self.model_case or ''), self.model_label, self.phase, self.prompt_tokens, self.concurrency, self.max_tokens, self.tp, self.dp, self.ep, self.pp, self.graph_buckets, self.graph_bucket, self.notes)
@dataclass(frozen=True)
class KernelTrace:
    duration_us: float; by_class: Mapping[str, float]; by_name: Mapping[str, float]
    counts: Mapping[str, int] = field(default_factory=dict, compare=False)
    step_us: tuple[float, ...] = field(default_factory=tuple, compare=False)
    segments: tuple[Any, ...] = field(default_factory=tuple, compare=False)
    union_duration_us: float = field(default=0.0, compare=False)
@dataclass(frozen=True)
class MeasuredCell:
    spec: CellSpec; kernel_paths: tuple[Path, ...]; trace: KernelTrace | None
    ttft_ms: float | None; tpot_ms: float | None; step_trace_ms: float | None
    decode_steps: int; success: bool; failure: str = ''; trace_quality: str = 'ok'
@dataclass(frozen=True)
class OperatorRow:
    name: str; kind: str; mechanism: str; subgraph: str; duration_ms: float; count: int
    regime: tuple[tuple[str, int], ...]; dominant_pipe: str; formula: str; segment: int
    cost: Any = field(compare=False, repr=False)
    @property
    def total_ms(self) -> float: return self.duration_ms * self.count
    @property
    def guard_text(self) -> str: return ';'.join((f'{key}={value}' for key, value in self.regime)) if self.regime else 'no_discrete_guard'
@dataclass(frozen=True)
class Prediction:
    cell_id: str; model_label: str; layers: int; per_layer: Mapping[str, float]; subgraphs: Mapping[str, float]
    body_ms: float; ttft_ms: float | None; dual_moe_ms: float | None; rows: tuple[OperatorRow, ...]
    notes: tuple[str, ...] = (); decode_body_ms: float = 0.0; prefill_body_ms: float = 0.0
@dataclass(frozen=True)
class Comparison:
    level: str; target: str; mechanism: str; predicted_ms: float; measured_ms: float
    operator: str; guard: str; dominant_pipe: str; formula: str; segment: int
    uncancelled_ms: float = 0.0; cell_id: str = ''; step_details: tuple[tuple[int, float, float, float], ...] = ()
    @property
    def signed_error(self) -> float:
        return (math.inf if self.predicted_ms > 0 else 0.0) if self.measured_ms <= 0 else (self.predicted_ms - self.measured_ms) / self.measured_ms
    @property
    def unsigned_error(self) -> float: return abs(self.signed_error)
@dataclass(frozen=True)
class Diagnosis:
    level: str; target: str; mechanism: str; error: float; unsigned_error: float
    physical_mechanism: str; operator: str; segment: int; dominant_pipe: str; guard: str
    formula_term: str; required_fix: str; evidence: str

@lru_cache(maxsize=4096)
def _classify_cached(norm_name: str, norm_type: str) -> str:
    if norm_name == 'aivkernel' and not _has(norm_type, _CLASS_RULES[0][1]): return 'elementwise_quant'
    text = f'{norm_name} {norm_type}'
    for label, tokens in _CLASS_RULES:
        if any((token in text for token in tokens)): return label
    raise ValueError(f'unclassified_kernel:{norm_name}:{norm_type}')
_SUFFIX_RE = re.compile(r'(?:_+\d+)+$')
def _strip_suffix(name: str) -> str:
    return (_SUFFIX_RE.sub('', name).strip() or name) if (name and name[-1].isdigit() and '_' in name) else name
def classify_kernel(name: str, type_name: str='') -> str:
    """Map one measured kernel to the canonical physical class."""
    return _classify_cached(base_kernel_name(_strip_suffix(name.strip())).lower(), type_name.strip().lower())
def _elementwise_class(name: str) -> str:
    return 'rope' if _has(name, _ROPE_TOKENS) else 'norm_residual' if _has(name, _NORM_TOKENS) else 'activation' if _has(name, _ACTIVATION_TOKENS) else 'elementwise_quant'
def _strict(kind: str, family: str, name: str) -> str:
    if family in {'collective', 'transport'}: return 'collective'
    if family == 'grouped_gemm': return 'moe_grouped'
    if family in {'gemm', 'router'} or (family == 'vision' and ('proj' in name or 'gemm' in name)): return 'gemm'
    if family in {'mla', 'attention'}: return 'attention'
    if family in {'elementwise', 'copy', 'elementwise_quant', 'quantize'}: return _elementwise_class(name)
    if family in {'kv_access', 'compression'}: return 'kv_cache'
    if family in {'indexer', 'hyper_connection', 'hc_post', 'recurrent', 'embedding', 'draft', 'vision'}: return {'indexer': 'indexer', 'hyper_connection': 'hyperconnection', 'hc_post': 'hyperconnection', 'recurrent': 'gdn_kda'}.get(family, 'elementwise_quant')
    raise ValueError(f'unclassified_operator:{kind}:{family}:{name}')
def operator_mechanism(cost: Any, kind: str) -> str:
    """Price one compiled operator by its own physics, never by the L2 bucket."""
    if kind == 'R0': return 'hyperconnection'
    family = str(getattr(cost, 'family', ''))
    name = str(getattr(cost, 'name', '')).lower()
    if kind == 'K0' or family == 'kv_access' or name in {'kv_store', 'kv_read', 'index_cache_store', 'layout_convert'}: return 'kv_cache'
    if _has(name, _ROPE_TOKENS): return 'rope'
    if kind == 'R1': return 'gemm' if family in {'gemm', 'router'} else 'norm_residual'
    if kind == 'F3': return 'moe_grouped' if family == 'grouped_gemm' else ('collective' if family in {'collective', 'transport'} else _elementwise_class(name))
    if kind in {'A3', 'A4'}: return 'gemm' if family in {'gemm', 'router'} else 'collective' if family in {'collective', 'transport'} else ('elementwise_quant' if name == 'prepare' else 'gdn_kda')
    if kind == 'I0': return 'gemm' if family in {'gemm', 'router'} else 'indexer'
    if kind == 'I1': return 'collective' if family in {'collective', 'transport'} else 'indexer'
    if kind in {'A0', 'A1', 'A2'}:
        if any((token in name for token in ('transpose', 'lse_merge', 'attentionupdate', 'attention_update'))): return 'elementwise_quant'
        if any((token in name for token in ('allgather', 'allreduce', 'alltoall', 'reducescatter'))): return 'collective'
        if family in {'mla', 'attention'}: return 'attention'
        if family in {'collective', 'transport'}: return 'collective'
        if family in {'gemm', 'router'}: return 'gemm'
        return _elementwise_class(name) if family in {'elementwise', 'copy', 'quantize'} else _strict(kind, family, name)
    if kind == 'F2': return 'collective' if family in {'collective', 'transport'} else 'elementwise_quant'
    if kind == 'F1': return 'gemm' if str(getattr(cost, 'kind', '')) == 'gemm' or family == 'gemm' or name == 'router_gemm' else 'moe_router'
    if kind == 'F4': return 'collective' if family in {'collective', 'transport'} else ('gemm' if family == 'gemm' else (_elementwise_class(name) if family in {'elementwise', 'copy', 'quantize'} else _strict(kind, family, name)))
    return 'norm_residual' if kind == 'N0' else _strict(kind, family, name)
def subgraph_family(kind: str) -> str:
    if kind in {'A0', 'A1', 'A2', 'A3', 'A4', 'I0', 'I1', 'K0', 'K1', 'R1'}: return 'attention'
    if kind in {'F0', 'F1', 'F2', 'F3', 'F4'}: return 'moe'
    return 'norm_residual' if kind == 'N0' else 'hyperconnection' if kind == 'R0' else ''
def _has(name: str, tokens: Sequence[str]) -> bool:
    return any((token in name.lower() for token in tokens))
@lru_cache(maxsize=4096)
def base_kernel_name(name: str) -> str:
    """Drop per-invocation numeric suffixes so traces stay bounded."""
    return re.sub('(?:_+\\d+)+$', '', name).strip() or name
def _union_span_us(spans: list[tuple[float, float]], fallback: float) -> float:
    if not spans: return fallback
    ordered = sorted(spans); total, (cur_s, cur_e) = 0.0, ordered[0]
    for s, e in ordered[1:]:
        if s <= cur_e: cur_e = max(cur_e, e)
        else: total += cur_e - cur_s; cur_s, cur_e = s, e
    return total + (cur_e - cur_s)
def load_kernel_trace(path: Path) -> KernelTrace:
    """Stream one kernel_details CSV/GZ and aggregate classes, names and counts."""
    by_class, by_name, counts = defaultdict(float), defaultdict(float), Counter()
    seg_c, seg_n, seg_k, step_us, segs, seen_comm, spans = defaultdict(float), defaultdict(float), Counter(), [], [], set(), []
    duration = step_total = 0.0
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', errors='replace', newline='') as handle:
        reader = csv.reader(handle); header = next(reader, ())
        index = {name: position for position, name in enumerate(header)}
        name_at, type_at, duration_at = index.get('Name', 4), index.get('Type', 5), index.get('Duration(us)', 9)
        core_at, start_at = index.get('Accelerator Core', -1), index.get('Start Time(us)', -1)
        for row in reader:
            if len(row) <= max(name_at, type_at, duration_at, core_at, start_at): continue
            if core_at >= 0 and start_at >= 0 and (row[core_at] or '').strip() == 'COMMUNICATION':
                sig = ((row[start_at] or '').strip(), (row[duration_at] or '').strip(), (row[type_at] or '').strip())
                if sig in seen_comm: continue
                seen_comm.add(sig)
            try: value = float((row[duration_at] or '0').strip() or 0)
            except ValueError: continue
            if not math.isfinite(value) or value <= 0: continue
            if start_at >= 0 and len(spans) < 4096:
                try:
                    start = float((row[start_at] or 'nan').strip() or 'nan')
                    if math.isfinite(start) and start >= 0: spans.append((start, start + value))
                except ValueError: pass
            duration += value; step_total += value; name = _strip_suffix((row[name_at] or '').strip()); rtype = (row[type_at] or '').strip(); base = base_kernel_name(_strip_suffix(rtype) if name.lower() == 'aivkernel' and rtype else name); cls = _classify_cached(base_kernel_name(name).lower(), rtype.lower())
            by_class[cls] += value; by_name[base] += value; counts[base] += 1; seg_c[cls] += value; seg_n[base] += value; seg_k[base] += 1
            if 'categorical_sample' in name.lower():
                if len(step_us) < 512: step_us.append(step_total)
                if len(segs) < 512: segs.append((step_total, dict(seg_c), dict(seg_n), dict(seg_k)))
                step_total = 0.0; seg_c.clear(); seg_n.clear(); seg_k.clear()
    if step_total > 0:
        if len(step_us) < 512: step_us.append(step_total)
        if len(segs) < 512: segs.append((step_total, dict(seg_c), dict(seg_n), dict(seg_k)))
    return KernelTrace(duration, dict(by_class), dict(by_name), dict(counts), tuple(step_us), tuple(segs), _union_span_us(spans, 0.0))

_STEP_ANCHORS = ('categorical_sample', 'categorical_prepare_mass', 'prepare_prefill_inputs', 'prepare_pos_seq_lens', 'post_update', 'combine_sampled', 'num_sampled')
def _count_mode(counts: Mapping[str, int]) -> int:
    histogram = Counter(value for value in counts.values() if value > 0)
    for minimum in (2, 1):
        pool = {value: names for value, names in histogram.items() if value >= minimum}
        if pool: return max(pool.items(), key=lambda item: (item[1], item[0]))[0]
    return 0
_CASE_LAYERS: dict[str, int] = {}
_COMPILED_MODELS: dict[tuple[Any, ...], Any] = {}
_AGG_CACHE: dict[tuple[Any, ...], Any] = {}
def _raw_case(spec: CellSpec) -> dict[str, Any]:
    raw = json.loads(spec.model_case.read_text(encoding='utf-8')) if spec.model_case is not None and spec.model_case.exists() else {}
    if 'a5' in spec.dataset.lower() and any(t in str(spec.model_case or '').lower() for t in ('a3', 'v4pro', 'v4f')): raw['machine'] = json.loads((CASES_DIR / 'decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json').read_text(encoding='utf-8'))['machine']
    if 'GLM-5.1' in spec.model_label or 'GLM-5.3/' in spec.model_label:
        quant = dict(raw.get('model', {}).get('quant', {}))
        if 'W4A4' in spec.model_label: quant.update({'weight_format': 'fp4_e2m1', 'expert_weight_format': 'fp4_e2m1'})
        raw['model'] = {'catalog_key': 'glm-5.1' if 'GLM-5.1' in spec.model_label else 'glm-5.3', 'quant': quant}
    elif 'DeepSeek-V3.2' in spec.model_label:
        raw['model'] = {**raw.get('model', {}), 'catalog_key': 'deepseek-v3.2-prune-3l' if 'Prune' in spec.model_label else 'deepseek-v3.2'}
    return raw
def _case_layers(spec: CellSpec) -> int:
    key = f'{spec.model_case}:{spec.model_label}' if ('GLM-5.1' in spec.model_label or 'GLM-5.3/' in spec.model_label or 'DeepSeek-V3.2' in spec.model_label) else str(spec.model_case or '')
    if key in _CASE_LAYERS: return _CASE_LAYERS[key]
    try:
        from mindie_sim.prediction.structure import parse_case
        layers = len(parse_case(_raw_case(spec)).model.layer_plans) if spec.model_case is not None and spec.model_case.exists() else 0
    except TimeoutError: raise
    except Exception: return 0
    if len(_CASE_LAYERS) >= 256: _CASE_LAYERS.clear()
    _CASE_LAYERS[key] = layers; return layers
def _decode_segments(trace: KernelTrace, tpot_ms: float | None) -> tuple[float, ...]:
    segments = tuple(us / 1000.0 for us in (getattr(trace, 'step_us', ()) or ()) if us > 0)
    if len(segments) < 2 or not tpot_ms or tpot_ms <= 0: return ()
    q25 = sorted(segments)[len(segments) // 4]
    floor = 0.1 * q25 if q25 > 1.0 else 0.0
    limit = min(_MIXED_RATIO * tpot_ms, 1.8 * q25) if len(segments) >= 4 and tpot_ms > 3.0 * q25 else max(_MIXED_RATIO * tpot_ms, 1.8 * q25)
    return tuple(segment for segment in segments if floor <= segment <= limit)
def _mixed_prefill(trace: KernelTrace, spec: CellSpec, step_trace_ms: float | None, tpot_ms: float | None) -> bool:
    if spec.phase == 'prefill' or not tpot_ms or tpot_ms <= 0: return False
    single_long = len(getattr(trace, 'step_us', ()) or ()) <= 1 and trace.duration_us / 1000.0 > 1000.0
    return single_long or any((m in n.lower() for n in (getattr(trace, 'by_name', {}) or {}) for m in _PREFILL_MARKERS)) or bool(step_trace_ms and step_trace_ms > _MIXED_RATIO * tpot_ms)
def _trace_step_count(trace: KernelTrace, spec: CellSpec, declared: int, tpot_ms: float | None, ttft_ms: float | None) -> int:
    """Recover captured steps from per-layer kernel counts, never from prediction math."""
    counts = getattr(trace, 'counts', {}) or {}
    if not counts: return max(1, int(declared))
    declared, mode, layers = max(1, int(declared)), _count_mode(counts), _case_layers(spec)
    if spec.phase == 'prefill':
        ratio = trace.duration_us / 1000.0 / ttft_ms if ttft_ms and ttft_ms > 0 else 0.0
        chunks = max(1, math.ceil(max(1, spec.prompt_tokens) / 8192))
        quotients = {mode // d for d in (layers, 2 * layers) if d and mode % d == 0 and 1 <= mode // (d * chunks) <= min(16, max(1, spec.concurrency))}
        if 0.4 <= ratio < 2.2: return max(quotients) if layers and mode // layers >= 2 and min(quotients or {0}) >= 2 else 1
        anchors = [max(1, value // chunks) for name, value in counts.items() if any((token in name.lower() for token in _STEP_ANCHORS))]
        anchor = Counter(anchors).most_common(1)[0][0] if anchors else 0
        if 2.2 <= ratio <= 8: return max(1, round(ratio))
        if 1 <= anchor <= 8: return anchor
        candidates = {mode // (divisor * chunks) for divisor in (1, layers, 2 * layers) if divisor and mode % (divisor * chunks) == 0 and 1 < mode // (divisor * chunks) <= 8}
        return min(candidates) if candidates else 1
    raw_step = trace.duration_us / 1000.0 / max(1, mode)
    if _mixed_prefill(trace, spec, raw_step, tpot_ms):
        segments = _decode_segments(trace, tpot_ms); return max(1, len(segments)) if segments else declared
    quotients = {mode // divisor for divisor in (layers, 2 * layers) if divisor and mode % divisor == 0 and 0.5 * declared <= mode // divisor <= 2 * declared}
    if quotients: return min(quotients, key=lambda value: (abs(value - declared), value))
    if 0.5 * declared <= mode <= 2 * declared: return mode
    time_steps = round((trace.duration_us / 1000.0 - (ttft_ms or 0.0)) / tpot_ms) if tpot_ms and tpot_ms > 0 else 0
    return time_steps if 1 <= time_steps <= 8 * declared else declared
def measured_subgraph_us(trace: KernelTrace, family: str) -> float:
    tokens = {'attention': _ATTENTION_TOKENS, 'moe': _MOE_TOKENS, 'norm_residual': _NORM_TOKENS, 'hyperconnection': _HYPERCONNECTION_TOKENS}.get(family, ())
    if family == 'attention': return sum((us for name, us in trace.by_name.items() if _has(name, tokens) and classify_kernel(name) not in {'gemm', 'collective'}))
    if family == 'moe' and trace.by_class.get('moe_grouped', 0.0) > 0.0 and not any(('allreduce' in k.lower() for k in trace.by_name)): return sum((trace.by_class.get(k, 0.0) for k in ('moe_grouped', 'moe_router', 'collective', 'activation')))
    return sum((us for name, us in trace.by_name.items() if _has(name, tokens)))
def _load_json(path: Path) -> Any:
    try: return json.loads(path.read_text(encoding='utf-8'))
    except TimeoutError: raise
    except (OSError, ValueError): return None
def _seconds(raw: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        item = raw.get(key); item = (item.get('median') or item.get('mean')) if isinstance(item, Mapping) else item
        try:
            val = float(item) / 1000.0 if key.endswith('_ms') else float(item)
            if math.isfinite(val) and val >= 0.0: return val
        except (TypeError, ValueError): continue
    return None
def load_measured_cell(spec: CellSpec, json_path: Path, kernel_paths: Sequence[Path], raw: Mapping[str, Any] | None=None) -> MeasuredCell:
    """Read the target side only after ``spec`` has been declared."""
    raw = raw if isinstance(raw, Mapping) else _load_json(json_path) or {}
    mode = str(raw.get('mode') or raw.get('phase') or '')
    phase = 'prefill' if 'prefill' in mode or spec.phase == 'prefill' else 'decode'
    prompt = int(raw.get('prompt_tokens') or raw.get('input_tokens') or raw.get('isl') or spec.prompt_tokens or 1)
    if phase == 'prefill' and 0 < spec.prompt_tokens < prompt: prompt = spec.prompt_tokens
    concurrency = int(raw.get('concurrency') or raw.get('batch_size') or spec.concurrency or 1)
    max_tokens = int(raw.get('max_tokens') or raw.get('output_tokens') or raw.get('completion_tokens') or raw.get('osl') or spec.max_tokens or 1)
    streams = raw.get('streams') or []
    completion = max((int(s.get('completion_tokens') or 0) for s in streams if isinstance(s, dict)), default=0)
    warmup_tokens = int(raw.get('warmup_max_tokens') or 0)
    steps = 1 if phase == 'prefill' else max(1, max_tokens or completion) + max(0, warmup_tokens)
    ttft = _seconds(raw, 'ttft_mean_s', 'ttft_p50_s', 'ttft_ms', 'ttft_mean_ms', 'first_token_latency_s', 'first_token_latency_ms')
    tpot = _seconds(raw, 'tpot_mean_s', 'tpot_p50_s', 'itl_ms', 'tpot_ms', 'tpot_mean_ms', 'itl_mean_s', 'itl_mean_ms')
    success = bool(raw.get('success', bool(streams) or int(raw.get('completed') or 0) > 0 or ttft is not None)) and (bool(streams) if streams else True)
    specs = replace(spec, phase=phase, prompt_tokens=prompt, concurrency=concurrency, max_tokens=max_tokens)
    return MeasuredCell(specs, tuple(kernel_paths), None, None if ttft is None else float(ttft) * 1000.0, None if tpot is None else float(tpot) * 1000.0, None, steps, success, '' if success else str(raw.get('error') or raw.get('failure') or 'no_success_stream'))
def _summary_numbers(rows: Sequence[Mapping[str, Any]], *names: str) -> list[float]:
    for name in names:
        values = []
        for row in rows:
            try:
                val = float(row.get(name))
                if math.isfinite(val) and val >= 0.0: values.append(val)
            except (TypeError, ValueError): pass
        if values: return values
    return []
def _read_summary(path: Path) -> dict[str, Any]:
    """Project a request_summary CSV into the measured-JSON vocabulary."""
    try:
        with path.open('rt', encoding='utf-8', errors='replace', newline='') as handle:
            rows = [{str(key).strip().lower().lstrip('\ufeff').replace('(ms)', '_ms').replace('[ms]', '_ms').replace('(s)', '_s').replace('[s]', '_s').replace(' ', '_').replace('__', '_'): value for key, value in row.items()} for row in csv.DictReader(handle)]
    except TimeoutError: raise
    except OSError: return {}
    if not rows: return {}
    def pick(*names: str) -> Any:
        for row in rows:
            for name in names:
                value = row.get(name)
                if value not in (None, '', '-', 'N/A', 'None', 'nan'): return value
        return None
    n = lambda *names: _summary_numbers(rows, *names)
    completion, prompt, concurrency = n('completion_tokens', 'output_tokens', 'max_tokens', 'osl'), n('prompt_tokens', 'input_tokens', 'isl', 'context'), n('concurrency', 'batch_size')
    ttft_ms, ttft_s, tpot_ms, tpot_s = n('ttft_ms', 'ttft_mean_ms', 'ttft_p50_ms', 'first_token_latency_ms', 'first_token_ms', 'ttft', 'first_token_latency'), n('ttft_s', 'ttft_mean_s', 'ttft_p50_s', 'first_token_latency_s', 'first_token_s'), n('tpot_ms', 'tpot_mean_ms', 'tpot_p50_ms', 'itl_mean_ms', 'itl_p50_ms', 'tpot', 'itl'), n('tpot_s', 'tpot_mean_s', 'tpot_p50_s', 'itl_mean_s', 'itl_p50_s')
    ttft = mean(ttft_ms) if ttft_ms else (mean(ttft_s) * 1000.0 if ttft_s else None)
    tpot = mean(tpot_ms) if tpot_ms else (mean(tpot_s) * 1000.0 if tpot_s else None)
    max_tokens, count = (int(max(completion)) if completion else 1), (int(max(concurrency)) if concurrency else max(1, len(rows)))
    success = int(all((str(row.get('success') or row.get('ok') or row.get('status') or '1').lower() not in {'0', 'false', 'fail', 'failed', 'error'} for row in rows)))
    tag = str(pick('tag', 'cell', 'case', 'name') or (path.parent.parent.name if path.parent.name == 'measured' else path.parent.name))
    mode = str(pick('mode', 'phase', 'profile_mode') or ('profile_prefill' if 'prefill' in tag or '_pf_' in tag or tag.startswith('pf_') else 'profile_decode'))
    record = {'tag': tag, 'mode': mode, 'success': success, 'prompt_tokens': int(max(prompt)) if prompt else 1, 'concurrency': count, 'max_tokens': max_tokens, 'streams': [{'completion_tokens': max_tokens} for _ in range(count)]}
    if ttft is not None: record['ttft_mean_s'] = ttft / 1000.0
    if tpot is not None: record['tpot_mean_s'] = tpot / 1000.0
    record.update({key: value for key in ('error', 'failure', 'model_case', 'model_path', 'model') if (value := pick(key)) is not None})
    return record
def _strip_hccl_launch(trace: KernelTrace) -> KernelTrace:
    hl = trace.by_name.get('HcclLaunchAicpuKernel', 0.0)
    if hl <= 0 or not any(k.startswith('hcom_') for k in trace.by_name): return trace
    by_c, by_n, cnt = dict(trace.by_class), dict(trace.by_name), dict(trace.counts)
    by_n.pop('HcclLaunchAicpuKernel', None); cnt.pop('HcclLaunchAicpuKernel', None); by_c['collective'] = max(0.0, by_c.get('collective', 0.0) - hl)
    segs = tuple((max(0.0, u - sn.get('HcclLaunchAicpuKernel', 0.0)), {**sc, 'collective': max(0.0, sc.get('collective', 0.0) - sn.get('HcclLaunchAicpuKernel', 0.0))}, {k: v for k, v in sn.items() if k != 'HcclLaunchAicpuKernel'}, {k: v for k, v in sk.items() if k != 'HcclLaunchAicpuKernel'}) for u, sc, sn, sk in (trace.segments or ()))
    return KernelTrace(max(0.0, trace.duration_us - hl), by_c, by_n, cnt, tuple(s[0] for s in segs) if segs else trace.step_us, segs, trace.union_duration_us)
def _norm_cell(cell: MeasuredCell) -> MeasuredCell:
    trace = cell.trace
    if trace is None: return cell
    by_c, by_n, cnt, dur, step_ms, steps = dict(trace.by_class), dict(trace.by_name), dict(trace.counts), trace.duration_us, cell.step_trace_ms, max(1, cell.decode_steps)
    if any(k.startswith('hcom_') for k in by_n) and (hl := by_n.pop('HcclLaunchAicpuKernel', 0.0)) > 0:
        cnt.pop('HcclLaunchAicpuKernel', None); by_c['collective'] = max(0.0, by_c.get('collective', 0.0) - hl); dur = max(0.0, dur - hl)
        if step_ms is not None and cell.spec.phase == 'prefill': step_ms = max(1.0, step_ms - hl / 1000.0 / steps)
    if (pr := sum(v for k, v in by_n.items() if '_prepare_rope_positions' in k.lower())) > 0: by_c['rope'] = max(0.0, by_c.get('rope', 0.0) - pr); by_c['elementwise_quant'] = by_c.get('elementwise_quant', 0.0) + pr
    qual = cell.trace_quality
    if cell.spec.phase == 'prefill':
        ag_u, ag_c = sum(by_n[k] for k in by_n if 'allgather' in k.lower()), sum(cnt.get(k, 0) for k in by_n if 'allgather' in k.lower())
        a2a_u, a2a_c = sum(by_n[k] for k in by_n if 'alltoall' in k.lower()), sum(cnt.get(k, 0) for k in by_n if 'alltoall' in k.lower())
        if ag_c > 0 and a2a_c > 0 and (ag_u / ag_c) > max(2000.0, 2.8 * (a2a_u / a2a_c)): qual = 'dp_barrier_skew'
        elif cell.ttft_ms and step_ms and cell.ttft_ms > 1.8 * step_ms: qual = 'warmup_contaminated_ttft'
    return replace(cell, decode_steps=steps, trace=replace(trace, duration_us=dur, by_class=by_c, by_name=by_n, counts=cnt), step_trace_ms=step_ms, trace_quality=qual)
def attach_trace(cell: MeasuredCell) -> MeasuredCell:
    """Load the target kernel trace lazily, after the declaration is fixed."""
    paths = [path for path in cell.kernel_paths if path.exists()]; paths = paths if len(paths) <= 4 else paths[:1]
    if cell.trace is not None or not paths: return cell
    trace = _strip_hccl_launch(max((load_kernel_trace(p) for p in paths), key=lambda t: t.duration_us - t.by_class.get('collective', 0.0)))
    segs = tuple(getattr(trace, 'segments', ()) or ())
    tiny = cell.spec.phase == 'prefill' and len(segs) >= 2 and segs[0][0] > 0 and all(seg[0] < 0.25 * segs[0][0] for seg in segs[1:])
    steps = _trace_step_count(trace, cell.spec, cell.decode_steps, cell.tpot_ms, cell.ttft_ms)
    raw_step = trace.duration_us / 1000.0 / max(1, _count_mode(trace.counts) or steps)
    mixed = _mixed_prefill(trace, cell.spec, raw_step, cell.tpot_ms)
    segments = _decode_segments(trace, cell.tpot_ms) if mixed else ()
    chosen = [seg for seg in segs if round(seg[0], 3) in {round(ms * 1000.0, 3) for ms in segments}] if mixed and segments else ([seg for seg in segs if seg[0] >= 0.25 * segs[0][0]] if tiny else [])
    if chosen:
        tails = [seg for seg in segs if seg[0] < 0.25 * segs[0][0]] if tiny else []
        c_tail, c_head = sum(s[3].get('MoeDistributeCombineV3', 0) for s in tails), sum(s[3].get('MoeDistributeCombineV3', 0) for s in chosen)
        hr = (c_head / c_tail) if c_tail > 0 and c_head > 0 else 0.0
        t_c, t_n, t_u, c_sum, n_sum, k_sum = defaultdict(float), defaultdict(float), sum(s[0] for s in tails), defaultdict(float), defaultdict(float), Counter()
        for _, sc, sn, _ in tails: t_c.update((k, t_c[k] + v) for k, v in sc.items()); t_n.update((k, t_n[k] + v) for k, v in sn.items())
        for _, sc, sn, sk in chosen: c_sum.update((k, c_sum[k] + v) for k, v in sc.items()); n_sum.update((k, n_sum[k] + v) for k, v in sn.items()); k_sum.update(sk)
        if hr > 0: c_sum, n_sum = defaultdict(float, {k: max(0.0, v - hr * t_c.get(k, 0.0)) for k, v in c_sum.items()}), defaultdict(float, {k: max(0.0, v - hr * t_n.get(k, 0.0)) for k, v in n_sum.items()})
        if tiny: steps = max(1, len(chosen))
        dur = max(1.0, sum(seg[0] for seg in chosen) - hr * t_u)
        trace = KernelTrace(dur, dict(c_sum), dict(n_sum), dict(k_sum), (dur,) if tiny else trace.step_us, (), trace.union_duration_us)
    trace = replace(trace, segments=())
    eff_dur = trace.union_duration_us if (0 < trace.union_duration_us < trace.duration_us and len(segs) <= 1 and trace.by_class.get('collective', 0.0) <= 0.0) else trace.duration_us
    step_trace = mean(segments) if segments else (cell.tpot_ms if mixed else eff_dur / 1000.0 / max(1, steps))
    return _norm_cell(replace(cell, trace=trace, step_trace_ms=step_trace, decode_steps=steps, trace_quality='mixed_prefill' if mixed else 'ok'))
def _parse_triplet(text: str) -> tuple[int, int, int]:
    text = text.lower()
    return tuple((int(match.group(1)) if match else 0 for match in (re.search(f'{key}(\\d+)', text) for key in ('dp', 'tp', 'ep'))))
def resolve_model(label: str) -> tuple[Path | None, str, tuple[str, ...]]:
    text = label.lower()
    for needle, relative, human in MODEL_PROFILES:
        if needle in text:
            path = CASES_DIR / relative
            notes = ('structural_proxy',) if 'proxy' in human.lower() else ()
            return (path if path.exists() else None, human, notes)
    return (None, 'unresolved', ('no_structural_case',))
def _bucket_for(concurrency: int, buckets: Sequence[int]) -> int:
    return next((value for value in sorted({int(item) for item in buckets if int(item) > 0}) if value >= concurrency), 0)
def _load_status(case_root: Path, root: Path) -> dict[str, Any]:
    for parent in (case_root, *case_root.parents):
        for fname in ('status.json', 'case_spec.json'):
            if isinstance(data := _load_json(parent / fname), dict): return data
        if parent == root: break
    return {}
def _spec_from_record(raw: Mapping[str, Any], path: Path, dataset: str, case_root: Path, root: Path) -> CellSpec:
    tag = str(raw.get('tag') or (path.parent.parent.name if path.parent.name == 'measured' else path.parent.name))
    cell_id = f'{case_root.name}:{tag}' if (case_root != root and case_root.name not in {'out', 'runs', 'measured'} and not tag.startswith(case_root.name)) else tag
    model_case, model_label, model_notes = resolve_model(f"{path} {case_root.name} {tag} {raw.get('model') or raw.get('model_name') or ''}")
    override = raw.get('model_case') or raw.get('model_path')
    if override and Path(str(override)).exists():
        candidate = Path(str(override)); model_case = candidate if candidate.is_absolute() else ROOT / candidate
        model_label, model_notes = (f'declared:{candidate.name}', ())
    dp, tp, ep = _parse_triplet(f'{case_root.name}_{tag}')
    status = _load_status(case_root, root)
    spec_section = (status.get('spec') if isinstance(status.get('spec'), dict) else status) if isinstance(status, dict) else {}
    compilation = spec_section.get('compilation_config', {}) if isinstance(spec_section, dict) else {}
    buckets = tuple((int(value) for value in compilation.get('cudagraph_capture_sizes', ()) if isinstance(value, int)))
    if not (dp and tp and ep):
        dp, tp = int(spec_section.get('dp') or dp or 0), int(spec_section.get('tp') or tp or 0)
        ep = int(spec_section.get('ep') or (dp * max(1, tp) if spec_section.get('enable_expert_parallel') else ep or 0))
    if not ep and any(k in model_label for k in ('DeepSeek-V4.1', 'GLM-', 'Kimi-')): ep = dp * max(1, tp)
    mode = str(raw.get('mode') or raw.get('phase') or ''); phase = 'prefill' if 'prefill' in mode else 'decode'
    prompt = int(raw.get('prompt_tokens') or raw.get('input_tokens') or raw.get('isl') or 1)
    if phase == 'prefill' and (m := re.search(r'_p(\d+)k(?:_|$)', tag.lower())): prompt = min(max(1, prompt), int(m.group(1)) * 1024)
    concurrency = int(raw.get('concurrency') or raw.get('batch_size') or 1)
    return CellSpec(cell_id, dataset, phase, model_case, model_label, prompt, concurrency, int(raw.get('max_tokens') or raw.get('output_tokens') or raw.get('osl') or 1), tp, dp, ep, 1, buckets, _bucket_for(concurrency, buckets) if 'decode' in mode else 0, model_notes + (('graph_bucket_declared',) if buckets else ()))
def _pair_kernels(case_root: Path, tag: str, kernels: Sequence[Path]) -> tuple[Path, ...]:
    candidates = [path for path in kernels if path.is_relative_to(case_root)]
    tree = [(path.relative_to(case_root).parts[:-1], path) for path in candidates]
    matches = [(index, part, path) for parts, path in tree for index, part in enumerate(parts) if part and (tag == part or tag.endswith('_' + part) or part.endswith('_' + tag))]
    if matches:
        depth = max((index for index, _, _ in matches))
        names = {part for index, part, _ in matches if index == depth}
        if len(names) == 1:
            name = names.pop(); return tuple(sorted({path for _, part, path in matches if part == name}))
    return tuple(sorted(candidates)) if len(candidates) <= 4 else ()
def _find_summary(path: Path, case_root: Path) -> Path | None:
    for directory in (path.with_suffix(''), path.parent, case_root, case_root / 'measured', case_root.parent):
        candidate = directory / 'request_summary.csv'
        if candidate.exists(): return candidate
    return next(iter(sorted(case_root.rglob('request_summary.csv'))), None)
def _looks_measured(path: Path, raw: Mapping[str, Any]) -> bool:
    if path.name in {'case_spec.json', 'status.json', 'campaign_status.json'} or 'knee_curve' in path.name or raw.get('profile_enabled') is False: return False
    return path.parent.name == 'measured' or any((key in raw for key in ('mode', 'phase', 'streams', 'success', 'tag', 'ttft_mean_s', 'ttft_ms', 'tpot_mean_s', 'tpot_ms')))
def _discover_layout(root: Path) -> list[MeasuredCell]:
    kernels, summaries = sorted((path for path in root.rglob('kernel_details.csv*') if path.is_file() and 'idle_dp_rank' not in path.parts)), sorted(root.rglob('request_summary.csv'))
    used: set[Path] = set()
    cells: list[MeasuredCell] = []
    for path in sorted(root.rglob('*.json')):
        if path.parent.name != 'measured' and 'measured' not in path.stem.lower() and {'remote_cfg', 'raw', 'cases', 'cmd', 'logs'} & set(path.parts): continue
        raw = _load_json(path)
        if raw is None and (path.parent.name == 'measured' or 'measured' in path.stem.lower()):
            cells.append(MeasuredCell(CellSpec(path.stem, root.name, 'decode', None, 'unresolved', 1, 1, 1, 1, 1, 1, 1), (), None, None, None, None, 1, False, 'invalid_json')); continue
        if not isinstance(raw, dict) or not _looks_measured(path, raw): continue
        case_root = path.parent.parent if path.parent.name == 'measured' else path.parent
        summary = _find_summary(path, case_root)
        if summary is not None:
            merged = _read_summary(summary); merged.update(raw); used.add(summary.resolve()); raw = merged
        tag = str(raw.get('tag') or path.stem)
        cells.append(load_measured_cell(_spec_from_record(raw, path, root.name, case_root, root), path, _pair_kernels(case_root, tag, kernels), raw=raw))
    for path in summaries:
        if path.resolve() in used: continue
        raw = _read_summary(path)
        if not raw: continue
        case_root = path.parent.parent if path.parent.name == 'measured' else path.parent
        cells.append(load_measured_cell(_spec_from_record(raw, path, root.name, case_root, root), path, _pair_kernels(case_root, str(raw['tag']), kernels), raw=raw))
    return cells
def discover_workstream(root: Path) -> list[MeasuredCell]:
    """Discover every measured cell under one fleet workstream or layout root."""
    if not root.exists(): return []
    nested = [root / name for name in LAYOUTS if (root / name).is_dir()]
    return [cell for layout in nested or [root] for cell in _discover_layout(layout)]
def load_historical_inventory() -> list[dict[str, Any]]:
    """Inventory declared historical sources without reading target timings."""
    entries, seen = [], set()
    def add(kind: str, path: str, exists: bool) -> None:
        if path and path not in seen: seen.add(path); entries.append({'kind': kind, 'path': path, 'exists': exists})
    for profile in sorted(PROFILES_DIR.glob('*.json')):
        try: data = json.loads(profile.read_text(encoding='utf-8'))
        except TimeoutError: raise
        except (OSError, ValueError): continue
        for section in ('training_sources', 'validation_sources'):
            for item in data.get(section, ()) or ():
                path = str(item.get('path') or ''); add('profile_source', path, Path(path).exists())
    for fixture in sorted(FIXTURES_DIR.rglob('kernel_details*.csv*')): add('fixture', str(fixture), True)
    if CASES_REGISTRY.exists():
        try: registry = json.loads(CASES_REGISTRY.read_text(encoding='utf-8'))
        except TimeoutError: raise
        except (OSError, ValueError): registry = {}
        for case in registry.get('cases', ()):
            path = str(case.get('source', {}).get('path') or ''); add('case_registry', path, Path(path).exists())
    return entries
def _model_for_instantiation(model: Any, spec: CellSpec | None=None) -> tuple[Any, tuple[str, ...]]:
    if spec is not None and 'KV-BF16' in spec.model_label:
        quant = getattr(model, 'quant', None)
        model = replace(model, kv_dtype='bf16', quant=replace(quant, kv_dtype='bf16') if quant is not None else None)
    quant = getattr(model, 'quant', None)
    if quant is not None and str(getattr(quant, 'index_scale_dtype', '')).lower() in {'none', ''}:
        return (replace(model, quant=replace(quant, index_scale_dtype='fp8_e8m0')), ('index_scale_dtype_none_priced_as_1_byte_e8m0',))
    return (model, ())
def _compute_dtype(model: Any, machine: Any=None) -> str:
    quant = getattr(model, 'quant', None)
    candidate = str(getattr(quant, 'activation_format', '') or getattr(model, 'activation_dtype', 'bf16'))
    overrides = [v for _, kv in (getattr(quant, 'category_overrides', ()) or ()) for k, v in kv if k == 'activation_format']
    if candidate == 'bf16' and overrides: candidate = Counter(overrides).most_common(1)[0][0]
    if candidate not in {'bf16', 'fp16', 'fp32', 'int8', 'fp8_e4m3', 'fp8_e5m2', 'mxfp8', 'int4'}: return 'bf16'
    if machine is not None and getattr(machine, 'dies', ()):
        try: machine.dies[0].peak(candidate)
        except TimeoutError: raise
        except Exception: return 'bf16'
    return candidate
def _ep_ranks(spec: CellSpec) -> int:
    return max(1, spec.ep or (spec.dp * max(1, spec.tp) if any(k in spec.model_label for k in ('DeepSeek-V4.1', 'GLM-', 'Kimi-')) else 1))
def _ep_batch(spec: CellSpec) -> int:
    from mindie_sim.prediction.piecewise import ep_batch
    return ep_batch(spec.concurrency, spec.dp, _ep_ranks(spec))
def _local_batch(spec: CellSpec) -> int:
    """Requests carried by one DP replica, not by the whole DP cohort."""
    return max(1, math.ceil(max(1, spec.concurrency) / max(1, spec.dp)))
def _selected_geometry(geometry: Any) -> Any:
    """One completed token per request feeds ``lm_head`` / sampling (O0)."""
    from mindie_sim.prediction.piecewise import RequestGeometry, WorkloadGeometry
    return WorkloadGeometry(tuple(RequestGeometry(1, max(0, request.kv_len - 1), phase=request.phase, replica=request.replica) for request in geometry.requests), graph_bucket=0, cohort_batch=geometry.cohort_batch, phase=geometry.phase)
def _geometry(spec: CellSpec, phase: str, *, batch: int | None=None) -> Any:
    from mindie_sim.prediction.piecewise import RequestGeometry, WorkloadGeometry, clamp_graph_bucket, ep_batch, local_batch
    batch, cohort = batch or local_batch(spec.concurrency, spec.dp), ep_batch(spec.concurrency, spec.dp, _ep_ranks(spec))
    if phase == 'prefill':
        q_len = max(1, spec.prompt_tokens)
        return WorkloadGeometry.homogeneous(batch, q_len, q_len, phase='prefill', cohort_batch=cohort)
    context = max(0, spec.prompt_tokens + max(1, spec.max_tokens) // 2)
    return WorkloadGeometry(tuple((RequestGeometry(1, context, phase='decode') for _ in range(batch))), graph_bucket=clamp_graph_bucket(spec.graph_bucket, batch, spec.dp, spec.graph_buckets), cohort_batch=cohort, phase='decode')
def _ttft_wave_scale(spec: CellSpec, layers: int) -> float:
    from mindie_sim.prediction.piecewise import ttft_wave_scale
    return ttft_wave_scale(phase=spec.phase, concurrency=spec.concurrency, dp=spec.dp, ep=_ep_ranks(spec), layers=layers, graph_buckets=tuple(spec.graph_buckets), prompt_tokens=spec.prompt_tokens)
def _service_ttft_overhead_ms(spec: CellSpec, layers: int=0) -> float:
    from mindie_sim.prediction.piecewise import service_ttft_overhead_ms
    return service_ttft_overhead_ms(prompt_tokens=spec.prompt_tokens, tp=spec.tp, ep=_ep_ranks(spec), short_ep_host_ms=40.0 if (0 < layers <= 45 or 'GLM-5' in spec.model_label) else 95.0)
def _stages_of(costs: Sequence[Any]) -> list[list[tuple[str, Any]]]: return [list(s) for c in costs for s in (c.stage_work if c.stage_work else ((c.work,) if c.work else ()))]
def _ops_of(ev: Any) -> Sequence[Any]: return getattr(ev, 'costs', None) or ev.operators
def _aggregate(unique: Mapping[str, Any], counts: Mapping[str, int], geometry: Any, state: Any, skipped: list[str], include_draft: bool=False, features: Any=None, supply: Any=None) -> tuple[list[OperatorRow], float, dict, dict]:
    from mindie_sim.prediction.piecewise import attribute_rope; from mindie_sim.prediction.piecewise.composition import contention_envelope, evaluate_serial_split
    rows, body, per_layer, subgraphs, by_kind = [], 0.0, defaultdict(float), defaultdict(float), defaultdict(list)
    for fingerprint, compiled in unique.items():
        count, kind = counts[fingerprint], compiled.instance.kind
        if (kind == 'V0' and getattr(geometry, 'media_tokens', 0) == 0) or (kind == 'D0' and not include_draft): continue
        g_use = _selected_geometry(geometry) if kind == 'O0' else geometry; evaluation = compiled.evaluate(g_use, state)
        g_for = (lambda op, g=geometry, s=g_use: g if op.name == 'final_norm' and getattr(features, 'final_norm_scope', 'selected') == 'all' else s) if kind == 'O0' else None
        fusions = tuple(c.name for c in compiled.instance.template.fusions); serial = evaluate_serial_split(compiled, g_use, state, geometry_for=g_for, fusion=fusions) if (fusions or g_for) else evaluation
        by_kind[kind].append((compiled, serial, count)); body += count * float(serial.total_ms)
        for cost in evaluation.operators:
            raw_mech, raw_fam = operator_mechanism(cost, evaluation.kind), subgraph_family(evaluation.kind)
            mechanism, family = attribute_rope(evaluation.kind, raw_mech, raw_fam)
            row = OperatorRow(cost.name, evaluation.kind, mechanism, family, float(cost.duration_ms), count, cost.regime or (), cost.dominant_pipe, cost.formula, int(cost.segment_index), cost)
            rows.append(row); per_layer[mechanism] += row.total_ms
            if family and (not (family == 'attention' and mechanism in {'gemm', 'collective', 'elementwise_quant'})) and (not (family == 'moe' and (mechanism in {'gemm', 'elementwise_quant'} or (evaluation.kind in {'F0', 'F4'} and mechanism == 'collective')))):
                subgraphs[family] += row.total_ms
    if features is not None and supply is not None:
        if getattr(features, 'multistream_shared_expert', False) and by_kind['F3'] and by_kind['F4']:
            sh = [e for comp, e, _ in by_kind['F4'] if str(dict(comp.instance.metadata).get('role', '')) != 'join']
            dp = [e for comp, e, _ in by_kind['F2'] if 'combine' not in str(dict(comp.instance.metadata).get('role', ''))]
            cb = [e for comp, e, _ in by_kind['F2'] if 'combine' in str(dict(comp.instance.metadata).get('role', ''))]
            s_st, s_ms = [s for e in sh for s in _stages_of(_ops_of(e))], sum(float(e.total_ms) for e in sh)
            for _, e3, c3 in by_kind['F3']:
                rt = dp + [e3] + cb; r_st, r_ms = [s for e in rt for s in _stages_of(_ops_of(e))], sum(float(e.total_ms) for e in rt)
                if sh: body += c3 * (float(contention_envelope({'routed': r_st, 'shared': s_st}, supply).makespan_ms) - (r_ms + s_ms))
        for flag, kind in (('multistream_kda_proj', 'A3'), ('multistream_kda_proj', 'A4'), ('multistream_window_compressed', 'A2')):
            if getattr(features, flag, False) and by_kind[kind]:
                for comp, ev, c in by_kind[kind]: body += c * float(evaluate_serial_split(comp, geometry, state).total_ms - ev.total_ms)
        if getattr(features, 'multistream_attention_indexer', False) and by_kind['A1'] and (by_kind['I0'] or by_kind['I1']):
            pro_names = {'q_down', 'q_norm', 'q_up', 'q_direct', 'kv_down', 'kv_norm', 'rotary', 'kv_store', 'fused:mla_prolog'}
            (_, ea, _), ca, idx_evs = by_kind['A1'][0], sum(c for _, _, c in by_kind['A1']), [by_kind[k][0][1] for k in ('I0', 'I1') if by_kind[k]]
            pro = [op for op in _ops_of(ea) if op.name in pro_names]
            if pro and idx_evs:
                a_ms, i_ms = sum(float(op.duration_ms) for op in pro), sum(float(e.total_ms) for e in idx_evs)
                body += ca * (float(contention_envelope({'attention': _stages_of(pro), 'indexer': [s for e in idx_evs for s in _stages_of(_ops_of(e))]}, supply).makespan_ms) - (a_ms + i_ms))
    return (rows, body, dict(per_layer), dict(subgraphs))
def _dual_moe(rows: Sequence[OperatorRow], supply: Any, layers: int) -> float | None:
    from mindie_sim.prediction.piecewise import run_engine_work
    branches: dict[str, list[list[tuple[str, Any]]]] = {'routed': [], 'shared': []}
    for row in rows:
        target = 'routed' if row.kind == 'F3' else 'shared' if row.kind == 'F4' else ''
        if not target: continue
        for _ in range(row.count): branches[target].extend([[(pipe, value) for pipe, value in stage] for stage in (row.cost.stage_work or (tuple(row.cost.work),))])
    return float(run_engine_work(branches, supply).makespan_ms) / max(1, layers) if (branches['routed'] and branches['shared']) else None
def predict_cell(spec: CellSpec) -> Prediction:
    """Price one cell from declaration only; measured fields are unreachable."""
    empty = Prediction(spec.cell_id, spec.model_label, 0, {}, {}, 0.0, None, None, (), ('no_model_case',))
    if spec.model_case is None or not spec.model_case.exists(): return empty
    from mindie_sim.prediction.piecewise import AnalysisDomain, ImplementationPolicy, OperatorPiecewiseCompiler, PipeSupply
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.subgraphs.instantiate import FeatureConfig, instantiate_model
    from mindie_sim.prediction.subgraphs.state import StateView
    cache_key = (spec.dataset, str(spec.model_case), spec.model_label, spec.tp, spec.dp, spec.ep, spec.pp, tuple(spec.graph_buckets))
    if cache_key in _COMPILED_MODELS: layers, notes, supply, unique, counts, state, features = _COMPILED_MODELS[cache_key]
    else:
        try: case = parse_case(_raw_case(spec))
        except TimeoutError: raise
        except Exception as error: return replace(empty, notes=(f'case_parse_error:{type(error).__name__}:{error}',))
        model, notes = _model_for_instantiation(case.model, spec)
        cores = max(1, case.machine.dies[0].compute_units)
        features = FeatureConfig.from_runtime(case.runtime, model).project(tp=spec.tp, dp=spec.dp, ep=_ep_ranks(spec), pp=spec.pp, cores=cores, graph_buckets=spec.graph_buckets, kv_bf16_override='KV-BF16' in spec.model_label)
        try: instantiated = instantiate_model(model, features)
        except TimeoutError: raise
        except Exception as error: return replace(empty, notes=(f'instantiate_error:{type(error).__name__}:{error}',))
        supply = PipeSupply.from_hardware(case.machine, dtype=_compute_dtype(model, case.machine))
        compiler = OperatorPiecewiseCompiler(supply, ImplementationPolicy(cores=cores), domain=AnalysisDomain(max_tokens=10**9, max_moe_rows=10**9, max_query_tiles=10**9, max_kv_tiles=10**9, max_index_rows=10**12, max_work=10**15))
        unique, counts = {}, Counter()
        for instance in instantiated.subgraphs:
            fingerprint = instance.fingerprint(); counts[fingerprint] += 1
            if fingerprint not in unique: unique[fingerprint] = compiler.compile(instance)
        layers, state = max(1, len(model.layer_plans)), StateView()
        for layer in range(layers): state = state.mark_kv(layer).mark_index(layer).mark_selection(layer)
        if len(_COMPILED_MODELS) >= 256: _COMPILED_MODELS.clear()
        _COMPILED_MODELS[cache_key] = (layers, notes, supply, unique, counts, state, features)
    def _cached_agg(s: CellSpec, ph: str) -> tuple[list[OperatorRow], float, dict, dict]:
        g = _geometry(s, ph); k = (cache_key, ph, g)
        if k not in _AGG_CACHE:
            if len(_AGG_CACHE) >= 512: _AGG_CACHE.clear()
            _AGG_CACHE[k] = _aggregate(unique, counts, g, state, [], features=features, supply=supply)
        return _AGG_CACHE[k]
    prefill = spec.phase == 'prefill'
    prefill_rows, prefill_body, prefill_per_layer, prefill_subgraphs = _cached_agg(spec if prefill else replace(spec, concurrency=1), 'prefill')
    decode_rows, body, decode_per_layer, decode_subgraphs = (prefill_rows, prefill_body, prefill_per_layer, prefill_subgraphs) if prefill else _cached_agg(spec, 'decode')
    per_layer = {key: value / layers for key, value in (prefill_per_layer if prefill else decode_per_layer).items()}
    subgraphs = {key: value / layers for key, value in (prefill_subgraphs if prefill else decode_subgraphs).items()}
    wave = _ttft_wave_scale(spec, layers)
    decode_body, prefill_body_ms = (0.0, body) if prefill else (body, prefill_body * wave)
    service_ms = (body * wave if prefill else prefill_body_ms + decode_body) + _service_ttft_overhead_ms(spec, layers)
    return Prediction(spec.cell_id, spec.model_label, layers, per_layer, subgraphs, prefill_body if prefill else body, service_ms, _dual_moe(prefill_rows if prefill else decode_rows, supply, layers), tuple(prefill_rows if prefill else decode_rows), tuple(notes) + tuple(spec.notes), decode_body, prefill_body_ms)
def _row_for(rows: Sequence[OperatorRow], mechanism: str) -> OperatorRow | None:
    return max((row for row in rows if row.mechanism == mechanism), key=lambda row: row.total_ms, default=None)
def _component_errors(cell: MeasuredCell, prediction: Prediction, family: str) -> dict[str, float]:
    if cell.trace is None: return {}
    s, l, r1 = max(1, cell.decode_steps), max(1, prediction.layers), sum(r.total_ms for r in prediction.rows if r.kind == 'R1' and r.mechanism == 'norm_residual') / max(1, prediction.layers)
    if family == 'moe':
        if cell.trace.by_class.get('moe_grouped', 0.0) <= 0.0: return {'activation': prediction.subgraphs.get('moe', 0.0) - measured_subgraph_us(cell.trace, 'moe') / 1000.0 / s / l}
        mc, pc = sum(us for n, us in cell.trace.by_name.items() if _has(n, _MOE_TOKENS) and classify_kernel(n) == 'collective') / 1000.0 / s / l, sum(r.total_ms for r in prediction.rows if r.subgraph == 'moe' and r.mechanism == 'collective' and r.kind not in {'F0', 'F4'}) / l
        return {'moe_grouped_act': sum(r.total_ms for r in prediction.rows if r.subgraph == 'moe' and r.mechanism in {'moe_grouped', 'activation'}) / l - (cell.trace.by_class.get('moe_grouped', 0.0) + cell.trace.by_class.get('activation', 0.0)) / 1000.0 / s / l, 'moe_router': prediction.per_layer.get('moe_router', 0.0) - cell.trace.by_class.get('moe_router', 0.0) / 1000.0 / s / l, 'collective': pc - mc}
    if family == 'attention':
        pa, ma = sum(prediction.per_layer.get(k, 0.0) for k in ('attention', 'rope', 'kv_cache', 'indexer')) + r1, sum(cell.trace.by_class.get(k, 0.0) for k in ('attention', 'rope', 'kv_cache', 'indexer')) / 1000.0 / s / l
        return {**({'attention_indexer': pa - ma} if (pa or ma) else {}), **({'gdn_kda': prediction.per_layer.get('gdn_kda', 0.0) - cell.trace.by_class.get('gdn_kda', 0.0) / 1000.0 / s / l} if (prediction.per_layer.get('gdn_kda', 0.0) or cell.trace.by_class.get('gdn_kda', 0.0)) else {})}
    return {k: prediction.per_layer.get(k, 0.0) - cell.trace.by_class.get(k, 0.0) / 1000.0 / s / l for k in {'norm_residual': ('norm_residual',), 'hyperconnection': ('hyperconnection',)}.get(family, ()) if cell.trace.by_class.get(k, 0.0) or prediction.per_layer.get(k, 0.0)}
def _phase_body(prediction: Prediction, phase: str) -> float:
    return (prediction.decode_body_ms if phase == 'decode' else prediction.prefill_body_ms) or prediction.body_ms
def _step_series(cell: MeasuredCell) -> tuple[float, ...]:
    """Return one latency per captured step (ms), never a cross-case average."""
    trace = cell.trace
    if cell.spec.phase == 'decode' and cell.trace_quality == 'mixed_prefill': return _decode_segments(trace, cell.tpot_ms)
    if cell.spec.phase != 'decode': return (cell.step_trace_ms,) if cell.step_trace_ms and cell.step_trace_ms > 0 else ()
    segments = tuple(us / 1000.0 for us in (getattr(trace, 'step_us', ()) or ()) if us > 0)
    return () if not segments else _decode_segments(trace, cell.tpot_ms) or ((cell.step_trace_ms,) if cell.step_trace_ms and cell.step_trace_ms > 0 else segments)
def _latency_comparison(level: str, target: str, predicted_ms: float, measured_ms: float, cell: MeasuredCell, operator: str, guard: str, pipe: str, formula: str, segment: int, uncancelled_ms: float=0.0, per_step: Sequence[float]=()) -> Comparison:
    series = tuple(float(value) for value in per_step if value > 0) or ((measured_ms,) if measured_ms > 0 else ())
    details = tuple((index, value, predicted_ms, (predicted_ms - value) / value if value > 0 else (math.inf if predicted_ms > 0 else 0.0)) for index, value in enumerate(series))
    return Comparison(level, target, 'service' if level == 'L4' else 'model', predicted_ms, mean(series) if series else measured_ms, operator, guard, pipe, formula, segment, uncancelled_ms, cell.spec.cell_id, details)
def compare_cell(cell: MeasuredCell, prediction: Prediction) -> list[Comparison]:
    """Build L1-L4 per-step comparisons after the prediction is frozen."""
    if cell.trace is None or prediction.layers <= 0: return []
    steps, layers = (max(1, cell.decode_steps), max(1, prediction.layers))
    comparisons: list[Comparison] = []
    trace_usable = cell.trace_quality != 'dp_barrier_skew' and (cell.trace_quality in {'ok', 'warmup_contaminated_ttft'} or cell.spec.phase == 'prefill' or bool(_decode_segments(cell.trace, cell.tpot_ms)))
    attn_us = (cell.trace.by_class.get('attention', 0.0) + cell.trace.by_class.get('gdn_kda', 0.0)) / steps / layers
    idle_dp = cell.spec.dp > cell.spec.concurrency and (attn_us <= 0.0 or (cell.spec.phase == 'prefill' and attn_us < 0.09 * cell.spec.prompt_tokens))
    components: dict[str, float] = {}
    r1_ms = sum(r.total_ms for r in prediction.rows if r.kind == 'R1' and r.mechanism == 'norm_residual') / layers
    for mechanism in (('collective',) if idle_dp else MECHANISMS) if trace_usable else ():
        measured = cell.trace.by_class.get(mechanism, 0.0) / 1000.0 / steps / layers
        predicted = prediction.per_layer.get(mechanism, 0.0) + (r1_ms if mechanism == 'attention' else (-r1_ms if mechanism == 'norm_residual' else 0.0))
        if measured <= 0 and predicted <= 0: continue
        row = _row_for(prediction.rows, mechanism)
        comparisons.append(Comparison('L1', mechanism, mechanism, predicted, measured, row.name if row else f'missing:{mechanism}', row.guard_text if row else 'unmodeled', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, cell_id=cell.spec.cell_id))
        components[mechanism] = predicted - measured
    gross, net = (sum((abs(value) for value in components.values())), abs(sum(components.values())))
    uncancelled = max(0.0, gross - net)
    for family in SUBGRAPHS if trace_usable and not idle_dp else ():
        measured = measured_subgraph_us(cell.trace, family) / 1000.0 / steps / layers
        predicted = prediction.subgraphs.get(family, 0.0)
        if measured <= 0 and predicted <= 0: continue
        errors = _component_errors(cell, prediction, family)
        gross, net = (sum((abs(value) for value in errors.values())), abs(sum(errors.values())))
        row = _row_for(prediction.rows, {'moe': 'moe_grouped', 'attention': 'attention', 'hyperconnection': 'hyperconnection'}.get(family, 'norm_residual'))
        comparisons.append(Comparison('L2', family, family, predicted, measured, row.name if row else f'missing:{family}', row.guard_text if row else 'unmodeled', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, max(0.0, gross - net), cell.spec.cell_id))
    series = _step_series(cell)
    unsegmented_pf = (cell.trace_quality == 'mixed_prefill' and len(getattr(cell.trace, 'step_us', ()) or ()) <= 1 and not _decode_segments(cell.trace, cell.tpot_ms)) or cell.trace_quality == 'dp_barrier_skew'
    step_ms = mean(series) if series else (0.0 if unsegmented_pf else (cell.step_trace_ms or 0.0))
    if step_ms > 0:
        row = max(prediction.rows, key=lambda item: item.total_ms) if prediction.rows else None
        target = f'{cell.spec.phase}_step_trace'
        comparisons.append(_latency_comparison('L3', target, _phase_body(prediction, cell.spec.phase), step_ms, cell, row.name if row else f'missing:{target}', row.guard_text if row else '', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, uncancelled, series))
    tpot_contaminated = cell.trace_quality == 'mixed_prefill' and step_ms > 0 and bool(cell.tpot_ms and cell.tpot_ms > 1.35 * step_ms) and bool(cell.spec.model_case)
    if cell.spec.phase != 'prefill' and cell.tpot_ms and (cell.tpot_ms > 0) and not unsegmented_pf and not tpot_contaminated:
        comparisons.append(_latency_comparison('L4', 'decode_step_tpot', _phase_body(prediction, 'decode'), cell.tpot_ms, cell, 'service_framework', 'no_discrete_guard', 'host', 'body + framework span', -1, uncancelled))
    if cell.ttft_ms and cell.ttft_ms > 0 and (prediction.ttft_ms is not None) and cell.trace_quality != 'warmup_contaminated_ttft':
        comparisons.append(_latency_comparison('L4', 'prefill_step_ttft', prediction.ttft_ms, cell.ttft_ms, cell, 'prefill_body', 'no_discrete_guard', 'host', 'prefill body + queue/launch', -1, uncancelled))
    return comparisons
def _fused_evidence(cell: MeasuredCell, target: str) -> bool:
    if cell.trace is None: return False
    candidates = [(us, name) for name, us in cell.trace.by_name.items() if classify_kernel(name) in _TARGET_CLASSES.get(target, {target})]
    return bool(candidates) and _has(max(candidates)[1], _FUSED_TARGETS.get(target, ()))
def diagnose(comparison: Comparison, cell: MeasuredCell, prediction: Prediction) -> Diagnosis | None:
    """Attach one physical repair mechanism to an error above the threshold."""
    if comparison.measured_ms <= 0:
        if comparison.predicted_ms <= 0: return None
        return Diagnosis(comparison.level, comparison.target, comparison.mechanism, math.inf, math.inf, 'confirmed_structural_gap', comparison.operator, comparison.segment, comparison.dominant_pipe, comparison.guard, comparison.formula, f'remove or justify {comparison.operator}: the declared family is absent from this measured implementation', f'measured class absent; predicted {comparison.predicted_ms:.6f}ms')
    if comparison.unsigned_error <= ERROR_THRESHOLD and comparison.uncancelled_ms / max(comparison.measured_ms, 1e-12) <= ERROR_THRESHOLD: return None
    mechanism, row, guard, pipe, notes = comparison.mechanism, _row_for(prediction.rows, comparison.mechanism), comparison.guard, comparison.dominant_pipe, set(cell.spec.notes) | set(prediction.notes)
    if comparison.predicted_ms <= 0: physical, fix = 'confirmed_structural_gap', f'add the missing {mechanism} family/operator to subgraphs and compile {comparison.target} with declared geometry'
    elif comparison.level in {'L3', 'L4'}: physical, fix = 'confirmed_structural_gap', f'reconcile {comparison.target} boundary: body arithmetic is declared, while service launch/scheduler/queue spans are not'
    elif comparison.target == 'norm_residual' and comparison.predicted_ms < 0.1 * comparison.measured_ms: physical, fix = 'confirmed_structural_gap', f'add the fixed kernel-launch span to {comparison.operator}; the declared norm/residual arithmetic is below one launch quantum'
    elif comparison.uncancelled_ms / max(comparison.measured_ms, 1e-12) > ERROR_THRESHOLD: physical, fix = 'fusion_boundary', f'repair {comparison.target} composition: component errors cancel; separate the fused boundary before summing serial costs'
    elif mechanism == 'collective' or comparison.target == 'collective': physical, fix = 'collective_skew', f'correct {comparison.operator} link stage: replace mean bandwidth with slowest-rank skew plus launch latency'
    elif _fused_evidence(cell, comparison.target): physical, fix = 'fusion_boundary', f'correct {comparison.operator} fusion boundary: merge or split the declared internal materialisation at the measured fused kernel'
    elif any((key in {'M_TILES', 'TOKEN_TILES', 'SPLITS', 'TILES'} for key, _ in (row.regime if row else ()))): physical, fix = 'tiling_wave_step', f'correct {comparison.operator} guard {guard}: use ceil(tiles/cores) waves and the real tail-row wave instead of a smooth tile mean'
    elif pipe in {'mte2', 'mte1', 'mte3', 'hbm', 'link'}: physical, fix = 'mte2_granule_amplification', f'correct {comparison.operator} stage {comparison.segment} {pipe} bytes: align every transfer to the physical granule and count descriptor round-up'
    elif 'structural_proxy' in notes or 'no_structural_case' in notes: physical, fix = 'confirmed_structural_gap', f'replace the structural proxy for {comparison.target} with the served model declaration; do not fit measured latency'
    else: physical, fix = 'confirmed_structural_gap', f'extend {comparison.operator} segment {comparison.segment} with the declared physical boundary term that the measurement exposes'
    if 'structural_proxy' in notes: fix += ' [structural proxy]'
    return Diagnosis(comparison.level, comparison.target, mechanism, comparison.signed_error, comparison.unsigned_error, physical, comparison.operator, comparison.segment, pipe, guard, comparison.formula, fix, f"measured={comparison.measured_ms:.6f}ms predicted={comparison.predicted_ms:.6f}ms signed={comparison.signed_error:+.2%} guard={guard or 'none'} pipe={pipe or 'none'}")
def diagnose_cell(comparisons: Sequence[Comparison], cell: MeasuredCell, prediction: Prediction) -> list[Diagnosis]:
    found = [item for item in (diagnose(comparison, cell, prediction) for comparison in comparisons) if item is not None]
    for comparison in comparisons:
        if comparison.level != 'L2' or comparison.measured_ms <= 0 or comparison.uncancelled_ms / comparison.measured_ms <= ERROR_THRESHOLD or any((item.level == 'L2' and item.target == comparison.target for item in found)): continue
        found.append(Diagnosis('L2', comparison.target, comparison.mechanism, comparison.signed_error, comparison.unsigned_error, 'fusion_boundary', comparison.operator, comparison.segment, comparison.dominant_pipe, comparison.guard, comparison.formula, f'repair {comparison.target} composition: component errors cancel; separate the fused boundary before summing serial costs', f'uncancelled_l1={comparison.uncancelled_ms:.6f}ms measured={comparison.measured_ms:.6f}ms'))
    return found
def _quantile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)] if ordered else 0.0
def aggregate(comparisons: Sequence[Comparison]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[Comparison]] = defaultdict(list)
    for comparison in comparisons: groups[comparison.level, comparison.target].append(comparison)
    result = []
    for (level, target), items in sorted(groups.items()):
        valid, unsigned = [item for item in items if item.measured_ms > 0], [item.unsigned_error for item in items if item.measured_ms > 0]
        step_signed, step_unsigned, uncancelled = [], [], []
        for item in valid:
            details = item.step_details or ()
            step_signed.extend((detail[3] for detail in details) if details else (item.signed_error,))
            step_unsigned.extend((abs(detail[3]) for detail in details) if details else (item.unsigned_error,))
            base = (abs(item.predicted_ms - item.measured_ms) + item.uncancelled_ms) / item.measured_ms if item.measured_ms > 0 else 0.0
            uncancelled.extend([base] * len(details) if details else [base])
        if not any((value > 0 for value in uncancelled)): uncancelled = list(step_unsigned)
        pass_rate = sum((value <= ERROR_THRESHOLD for value in step_unsigned)) / len(step_unsigned) if step_unsigned else 0.0
        result.append({'level': level, 'target': target, 'unit': 'ms/step', 'samples': len(step_unsigned), 'cells': len(valid), 'unmatched': len(items) - len(valid), 'measured_ms_mean': mean((item.measured_ms for item in valid)) if valid else 0.0, 'predicted_ms_mean': mean((item.predicted_ms for item in valid)) if valid else 0.0, 'signed_error_mean': mean((item.signed_error for item in valid)) if valid else 0.0, 'unsigned_error_median': median(unsigned) if unsigned else 0.0, 'unsigned_error_p90': _quantile(unsigned, 0.9), 'above_10pct': sum((value > ERROR_THRESHOLD for value in unsigned)), 'step_err_p50': median(step_unsigned) if step_unsigned else 0.0, 'step_err_p90': _quantile(step_unsigned, 0.9), 'step_err_max': max(step_unsigned) if step_unsigned else 0.0, 'signed_p50': median(step_signed) if step_signed else 0.0, 'uncancelled_p50': median(uncancelled) if uncancelled else 0.0, 'pass_rate_10pct': pass_rate, 'within_10pct_rate': pass_rate})
    return result
def _step_rows(comparisons: Sequence[Comparison]) -> list[dict[str, Any]]:
    return [{'cell': item.cell_id, 'level': item.level, 'target': item.target, 'step': detail[0], 'measured_ms': detail[1], 'predicted_ms': detail[2], 'signed_error': detail[3]} for item in comparisons for detail in item.step_details]
def _category_label(level: str, target: str) -> str:
    if level == 'L2': return _SUBGRAPH_LABELS.get(target, target)
    return _MECH_LABELS.get(target, target) if level == 'L1' else _STEP_LABELS.get(target, target)
def run_validation(*, roots: Sequence[Path]=WORKSTREAM_ROOTS, include_historical: bool=True, max_cells: int=0) -> dict[str, Any]:
    """Evaluate every discovered cell and return a serialisable baseline."""
    inventory, initial_modules = (load_historical_inventory() if include_historical else []), frozenset(sys.modules)
    cells = sorted([cell for root in roots for cell in discover_workstream(Path(root))], key=lambda cell: (cell.spec.dataset, cell.spec.cell_id))
    if max_cells > 0: cells = cells[:max_cells]
    predictions, comparisons, diagnosis, skipped = {}, [], [], Counter()
    evaluated = with_trace = with_model = failed = mixed_pf = 0
    for cell in cells:
        if cell.spec.model_case is not None: with_model += 1
        if not cell.success: failed += 1; skipped[cell.failure or 'unsuccessful_cell'] += 1; continue
        key = cell.spec.prediction_key()
        if key not in predictions: predictions[key] = predict_cell(cell.spec)
        pred = predictions[key]; cell = attach_trace(cell)
        if cell.trace is not None: with_trace += 1
        if cell.trace_quality == 'mixed_prefill': mixed_pf += 1
        if cell.trace is None: skipped['no_kernel_trace'] += 1; continue
        if pred.layers <= 0: failed += 1; skipped[pred.notes[0] if pred.notes else 'prediction_failed'] += 1; continue
        evaluated += 1; cell_comparisons = compare_cell(cell, pred)
        comparisons.extend(cell_comparisons); diagnosis.extend(diagnose_cell(cell_comparisons, cell, pred))
    coverage = {'cells': len(cells), 'evaluated': evaluated, 'with_kernel_trace': with_trace, 'with_model': with_model, 'failed': failed, 'trace_mixed_prefill': mixed_pf, 'step_samples': sum((len(item.step_details) for item in comparisons))}
    return {'schema': 'mindie-profiler-zero-shot-piecewise-validation/1', 'coverage': coverage, 'skipped': dict(skipped), 'roots': [str(path) for path in roots], 'historical': {'inventoried': len(inventory), 'existing': sum((1 for item in inventory if item.get('exists'))), 'by_kind': dict(Counter((item['kind'] for item in inventory)))}, 'levels': aggregate(comparisons), 'step_errors': _step_rows(comparisons), 'diagnoses': [item.__dict__ for item in diagnosis], 'diagnosis_counts': dict(Counter((item.physical_mechanism for item in diagnosis))), 'measurement_blind': True, 'forbidden_lookup_imported': any((name.startswith('mindie_sim.prediction.service_regimes') and name not in initial_modules for name in sys.modules))}
def render_markdown(result: Mapping[str, Any]) -> str:
    coverage = result['coverage']
    lines = ['# Zero-shot piecewise validation baseline — Per-Step Latency Error (单步耗时误差)', '', 'Prediction path: `mindie_sim.prediction.subgraphs` + `mindie_sim.prediction.piecewise`; empirical `service_regimes` are not imported. Measured values are read only after each prediction is frozen.', '', 'Focus: **per-step latency** (`ms/step`), not cross-case means. `signed_p50` exposes systematic bias; `uncancelled_p50` exposes positive/negative cancellation among physical components. 验收重点为每个 Step 的单步耗时误差与正负抵消，跨 Case 均值仅保留兼容字段。', '', f"- cells: {coverage['cells']} (evaluated {coverage['evaluated']}, kernel trace {coverage['with_kernel_trace']}, model {coverage['with_model']}, mixed prefill {coverage['trace_mixed_prefill']})", f"- per-step samples: {coverage.get('step_samples', 0)}", f"- skipped: {result['skipped'] or 'none'}", f"- historical inventory: {result['historical']['inventoried']} ({result['historical']['existing']} existing)", f"- forbidden lookup imported: {result['forbidden_lookup_imported']}", '', '## Coverage by level / 分级覆盖（Per-Step Latency Error / 单步耗时误差）', '', '| level | target (EN / 中文) | step samples | cells | unmatched | measured ms | predicted ms | step_err_p50 | step_err_p90 | step_err_max | signed_p50 | uncancelled_p50 | <=10% pass | legacy unsigned med | legacy >10% |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in result['levels']:
        lines.append(f"| {row['level']} | {_category_label(row['level'], row['target'])} | {row['samples']} | {row.get('cells', row['samples'])} | {row['unmatched']} | {row['measured_ms_mean']:.6f} | {row['predicted_ms_mean']:.6f} | {row.get('step_err_p50', 0.0):.2%} | {row.get('step_err_p90', 0.0):.2%} | {row.get('step_err_max', 0.0):.2%} | {row.get('signed_p50', 0.0):+.2%} | {row.get('uncancelled_p50', 0.0):.2%} | {row.get('pass_rate_10pct', 0.0):.1%} | {row['unsigned_error_median']:.2%} | {row['above_10pct']} |")
    lines.extend(['', '## Physical diagnoses / 物理诊断类别', '', '| diagnosis category (EN / 中文) | raw key | count |', '|---|---|---:|'])
    counts = result['diagnosis_counts']
    for name in sorted(set(_DIAGNOSIS_LABELS) | set(counts)):
        lines.append(f"| {_DIAGNOSIS_LABELS.get(name, name)} | `{name}` | {counts.get(name, 0)} |")
    details = list(result.get('step_errors') or ())
    by_key: dict[tuple[str, str], list[float]] = defaultdict(list)
    for detail in details:
        by_key[detail['cell'], detail['target']].append(detail['signed_error'])
    flips = {key for key, values in by_key.items() if any((value < 0 for value in values)) and any((value > 0 for value in values))}
    worst = sorted(details, key=lambda item: -math.inf if not math.isfinite(item['signed_error']) else -abs(item['signed_error']))[:20]
    lines.extend(['', '## Worst per-step errors (top 20) / 最差单步误差', '', '`±cancel` = the same cell/target has both positive and negative Step errors, so a mean hides the miss; use `step_err_p90` / `step_err_max`. `±cancel` 表示同一 cell/target 的不同 Step 同时出现正负误差，均值会抵消，应看 P90 与最大误差。', '', '| cell | level | target (EN / 中文) | step | measured ms | predicted ms | signed error | ±cancel |', '|---|---|---|---:|---:|---:|---:|:---:|'])
    for item in worst:
        lines.append(f"| {item['cell']} | {item['level']} | {_category_label(item['level'], item['target'])} | {item['step']} | {item['measured_ms']:.6f} | {item['predicted_ms']:.6f} | {item['signed_error']:+.2%} | {'yes' if (item['cell'], item['target']) in flips else 'no'} |")
    lines.extend(['', '## Repair targets (top 15) / 修复目标', '', '| level | target (EN / 中文) | diagnosis (EN / 中文) | operator | segment | pipe | guard | required fix |', '|---|---|---|---|---:|---|---|---|'])
    for item in result['diagnoses'][:15]:
        lines.append(f"| {item['level']} | {_category_label(item['level'], item['target'])} | {_DIAGNOSIS_LABELS.get(item['physical_mechanism'], item['physical_mechanism'])} | {item['operator']} | {item['segment']} | {item['dominant_pipe']} | {item['guard']} | {item['required_fix']} |")
    return '\n'.join(lines + [''])
def main(argv: Sequence[str] | None=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', action='append', type=Path, default=None); parser.add_argument('--max-cells', type=int, default=0)
    parser.add_argument('--no-historical', action='store_true'); parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    roots = tuple(args.root) if args.root else WORKSTREAM_ROOTS
    result = run_validation(roots=roots, include_historical=not args.no_historical, max_cells=args.max_cells)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else render_markdown(result))
    cov = result['coverage']
    return 0 if cov['evaluated'] > 0 and cov['failed'] == 0 else 1
if __name__ == '__main__':
    raise SystemExit(main())
