"""Kernel-name classification and streamed Ascend kernel trace loading.

[Role] Map raw kernel names/types to the ordinary L1 mechanism classes and load
  one CSV/GZ trace without retaining per-row history.
[Invariants] Unknown names stay unresolved only when the caller allows it; the
  stream keeps union/forward spans and step segments separately.
[Side-Effect Policy] Read-only files; optional pickle cache under the caller's
  trace-cache directory.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
import csv
import gzip
import hashlib
import math
import pickle
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence


_MOE_TOKENS = ('groupedmatmul', 'moegating', 'moedistribute', 'alltoall', 'swiglu', 'situ', 'swiglugroupquant', 'moe', 'aclnnmuls')
_NORM_TOKENS = ('rmsnorm', 'layernorm', 'addrmnorm', 'addnorm', 'foreachaddlist', 'muls_add', 'residual')
_ROPE_TOKENS = ('rotary', 'rope')


@dataclass(frozen=True)
class KernelTrace:
    duration_us: float; by_class: Mapping[str, float]; by_name: Mapping[str, float]; counts: Mapping[str, int] = field(default_factory=dict, compare=False)
    step_us: tuple[float, ...] = field(default_factory=tuple, compare=False); segments: tuple[Any, ...] = field(default_factory=tuple, compare=False)
    union_duration_us: float = field(default=0.0, compare=False); forward_span_us: float = field(default=0.0, compare=False); incomplete: bool = field(default=False, compare=False); incomplete_reason: str = field(default='', compare=False)

_ACTIVATION_TOKENS = ('swiglu', 'situ', 'silu', 'gelu', 'activation', 'sigmoid', 'tanh', '_engram_gate')
_CLASS_RULES = (('collective', ('moedistribute', 'alltoall', 'allgather', 'allreduce', 'reducescatter', 'hcom_', 'hccl', '_build_c2_ring_metadata', 'channelinit', 'threadinit')), ('moe_grouped', ('groupedmatmul', 'grouped_matmul', 'megamoe')), ('indexer', ('indexer', 'keypool', '_decode_qk_score_kernel', 'genericblocksparseattentionmetadata', '_compress_qsa_groups_kernel', '_initialize_qsa_mask_words_kernel', '_pack_qsa_group_indices_kernel', '_prepare_qsa_gbsa_rows_kernel', '_prepare_qsa_mask_words_kernel', '_store_qsa_rows_kernel')), ('attention', ('mixed_quant_sparse_flash_mla', 'flashmla', 'flashattention', 'fusedinferattention', 'pagedattention', 'mqsmla', 'attnresfwd', 'mlaprolog', 'sparseattentionscore', 'genericblocksparseattention')), ('gdn_kda', ('recurrentgateddeltarule', 'chunkgateddeltarule', 'chunkfwdh', 'chunkfwdo', 'causalconv1d', 'layer_norm_gated', '_layer_norm_fwd_1pass', 'l2norm_fwd', '_copy_conv_state', '_gather_ssm_states', '_scatter_ssm_states', 'mamba_align', 'mamba_fused', 'gdn', 'kda')), ('norm_residual', ('rmsnorm', 'layernorm', 'addrmnorm', 'addnorm', 'foreachaddlist', 'muls_add', 'residual')), ('moe_router', ('moegating', 'moe_gating', 'moeinitrouting', 'moefinalizerouting', 'router', 'topkv2', 'onehot', 'softmaxv2')), ('activation', ('swiglu', 'situ', 'silu', 'gelu', 'activation', 'tanh', '_engram_gate')), ('kv_cache', ('scatterpacache', 'kvcompress', 'compressor', 'kvcache', 'kv_cache', 'slot_mapping', '_zero_kv_blocks', '_pool_kernel', 'kpool', '_cache_update', '_build_window_indices', '_apply_write_kernel', '_pack_indices_kernel')), ('rope', ('rotary', 'rope')), ('gemm', ('matmul', 'gemm', 'linear')), ('hyperconnection', ('hcpre', 'hcpost', 'hpre', 'hpost', '_hc_combine', '_hc_gate')), ('elementwise_quant', ('_prepare_rope_positions', 'attentionupdate', '_npu_attention_update', 'permute', 'transpose', 'quant', 'cast', 'copy', 'zeroslike', 'fill', 'mul', 'add', 'sub', 'sigmoid', 'neg', 'where', 'index', 'gather', 'concat', 'pad', 'slice', 'cumsum', 'embedding', 'hist', 'reduce', 'uniform', 'rand', 'select', 'eq', 'aivkernel', 'metadata_kernel', 'repeat', 'categorical_sample', 'categorical_prepare_mass', '_hash_ids', '_post_update', 'combine_sampled', 'num_sampled', 'scatter_num_accepted', 'bitwise', 'logical', 'ltscalar', 'gtscalar', 'divmods', 'floordiv', 'remainder', 'floormod', 'clamp', 'clipbyvalue', 'realdiv', 'argmaxv2', 'scatterndupdate', 'sort', 'batch_memcpy', '_write_output', 'scatterelementsv2', 'minimum', 'asstrided', 'greater', 'less', 'oneslike', 'range', 'tensormove', 'tile', 'categorical_finalize', 'logits_stats', 'idx_mapping', '_prepare_decode_inputs')))

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
    if family in {'indexer', 'hyper_connection', 'hc_post', 'recurrent', 'embedding', 'draft', 'vision'}: return {'indexer': 'indexer', 'hyper_connection': 'hyperconnection', 'hc_post': 'hyperconnection', 'recurrent': 'gdn_kda'}.get(family, 'elementwise_quant')
    raise ValueError(f'unclassified_operator:{kind}:{family}:{name}')
def operator_mechanism(cost: Any, kind: str) -> str:
    if kind == 'R0': return 'hyperconnection'
    family, name = (str(getattr(cost, 'family', '')), str(getattr(cost, 'name', '')).lower())
    if kind == 'K0' or family == 'kv_access' or name in {'kv_store', 'kv_read', 'index_cache_store', 'layout_convert'}: return 'kv_cache'
    if _has(name, _ROPE_TOKENS): return 'rope'
    if kind == 'R1': return 'gemm' if family in {'gemm', 'router'} else 'norm_residual'
    if kind == 'F3':
        if family == 'router': return 'moe_router'
        return 'moe_grouped' if family == 'grouped_gemm' else 'collective' if family in {'collective', 'transport'} else _elementwise_class(name)
    if kind in {'A3', 'A4'}: return 'gemm' if family in {'gemm', 'router'} else 'collective' if family in {'collective', 'transport'} else 'elementwise_quant' if name == 'prepare' or family == 'copy' else 'gdn_kda'
    if kind in {'I0', 'I1'}: return ('gemm' if family in {'gemm', 'router'} else 'indexer') if kind == 'I0' else 'collective' if family in {'collective', 'transport'} else 'indexer'
    if kind in {'A0', 'A1', 'A2'}:
        if any((tok in name for tok in ('transpose', 'lse_merge', 'attentionupdate', 'attention_update'))): return 'elementwise_quant'
        if any((tok in name for tok in ('allgather', 'allreduce', 'alltoall', 'reducescatter'))) or family in {'collective', 'transport'}: return 'collective'
        if family in {'mla', 'attention'}: return 'attention'
        return 'gemm' if family in {'gemm', 'router'} else _elementwise_class(name) if family in {'elementwise', 'copy', 'quantize'} else _strict(kind, family, name)
    if kind == 'F2':
        if family == 'router' and name.startswith('router_'):
            return 'moe_router'
        return 'collective' if family in {'collective', 'transport', 'mc2_transport'} else 'elementwise_quant'
    if kind == 'F1': return 'gemm' if str(getattr(cost, 'kind', '')) == 'gemm' or family == 'gemm' or name == 'router_gemm' else 'moe_router'
    if kind == 'F4':
        if family in {'collective', 'transport'}: return 'collective'
        if family == 'router' and name.startswith('router_'):
            return 'moe_router'
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


def _count_mode(counts: Mapping[str, int]) -> int:
    h = Counter((v for v in counts.values() if v > 0))
    for m in (2, 1):
        if (p := {v: n for v, n in h.items() if v >= m}): return max(p.items(), key=lambda it: (it[1], it[0]))[0]
    return 0
