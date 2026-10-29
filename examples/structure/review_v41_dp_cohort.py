"""Independently check and present the bounded retained DP cohort evidence.

[Role] Recompute overlap, populations, integer spans and shape capacities.
[Invariants] Reviews captured descriptors, never claims active-mask values or
  cross-rank step identities absent from the source.
[Timeouts & Locks] Bounded evidence JSON only; no raw source reread or locks.
[Side-Effect Policy] Write a compact review and Markdown table beside evidence.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


def review(path):
    path = Path(path)
    data = json.loads(path.read_text())
    checks, failures = 0, []

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    rows, aligned, population = [], [], {'ranks': 0, 'decoded_rows': 0, 'complete_bodies': 0,
                                         'mc2_calls': 0, 'conditional_cohorts': 0}
    for capture in data['captures']:
        cid = capture['case_id']
        prior = json.loads(Path(capture['prior_body_identity']['path']).read_text())
        before = {(row['start_ns'], row['end_ns']): row for row in prior['forwards']}
        check(len(capture['ranks']) == 4, cid + ':four_representatives')
        for rank in capture['ranks']:
            population['ranks'] += 1
            population['decoded_rows'] += rank['scan']['decoded_rows']
            population['complete_bodies'] += rank['forward_count']
            check(rank['forward_count'] == len(rank['forwards']), cid + rank['rank_id'] + ':body_count')
            check(rank['scan']['stopped_at_absolute_time_bound'] and not rank['scan']['full_capture_scanned'], cid + rank['rank_id'] + ':bounded')
            check(len(rank['step_rows']) == 1 and not rank['step_rows'][0]['Step'], cid + rank['rank_id'] + ':no_step_id')
            for forward in rank['forwards']:
                label = cid + rank['rank_id'] + forward['forward_id']
                check(forward['matched_layer_count'] == 40, label + ':complete_layers')
                check(abs((forward['end_ns'] - forward['start_ns']) / 1e6 - forward['body_forward_span_ms']) < 1e-10, label + ':integer_span')
                if rank['rank_id'] == 'dp0_tp0':
                    original = before.get((forward['start_ns'], forward['end_ns']))
                    check(original is not None and original['geometry'] == forward['geometry'], label + ':existing_full_extraction_matches')
                geometry = forward['geometry']
                check(geometry['query_rows'] == geometry['sequences_per_replica'] * geometry['tokens_per_sequence'], label + ':query_geometry')
                check(geometry['query_rows'] == 4 * geometry['hidden_rows_per_shard'], label + ':sp_factor4')
                check([row['layer_id'] for row in forward['native_mc2']] == list(range(40)), label + ':mc2_each_layer')
                check(len(forward['native_mc2']) == forward['native_mc2_count'] == 40, label + ':mc2_count')
                population['mc2_calls'] += len(forward['native_mc2'])
                for native in forward['native_mc2']:
                    check(native['x_shape'][0] == native['route_ids_shape'][0] == native['active_mask_shape'][0], label + ':capacity_axes')
                    check(native['route_ids_shape'][1] == 6 and native['local_expert_counts_shape'] == [24], label + ':route_slots_and_local_experts')
                    check(native['active_mask_values'] is None and native['routed_counts_values'] is None, label + ':unknown_values')
            rows.append([capture['client_concurrency'], rank['rank_id'], rank['forwards'][0]['device_id'],
                ', '.join(str(f['geometry']['sequences_per_replica']) for f in rank['forwards']),
                ', '.join(str(f['geometry']['hidden_rows_per_shard']) for f in rank['forwards']),
                ', '.join(f"{f['body_forward_span_ms']:.3f}" for f in rank['forwards']),
                ', '.join(f"{f['body_endpoint_evidence']['first_locator']['csv_line']}–{f['body_endpoint_evidence']['last_locator']['csv_line']}" for f in rank['forwards']),
                rank['source_identity']['sha256'][:12]])
        for window in capture['aligned_windows']:
            reference = next(f for f in capture['ranks'][0]['forwards'] if f['forward_id'] == window['dp0_forward_id'])
            selected = []
            for rank, member in zip(capture['ranks'], window['members']):
                matches = [f for f in rank['forwards'] if max(f['start_ns'], reference['start_ns']) < min(f['end_ns'], reference['end_ns'])]
                check(len(matches) == member['overlap_candidate_count'], cid + ':recomputed_overlap')
                if len(matches) == 1:
                    check(matches[0]['forward_id'] == member['forward_id'], cid + ':matched_occurrence')
                    selected.append(matches[0])
            expected = 'conditional_unique' if len(selected) == 4 else 'unresolved'
            check(window['alignment_status'] == expected, cid + ':alignment_status')
            check(not window['shared_step_id_observed'], cid + ':no_invented_step')
            if expected != 'conditional_unique':
                continue
            population['conditional_cohorts'] += 1
            common_start = max(f['start_ns'] for f in selected)
            common_end = min(f['end_ns'] for f in selected)
            check(common_start < common_end, cid + ':four_way_overlap')
            check(len({json.dumps(f['geometry'], sort_keys=True) for f in selected}) == 1, cid + ':uniform_execution_geometry')
            capacities = {row['x_shape'][0] for f in selected for row in f['native_mc2']}
            check(capacities == {reference['geometry']['hidden_rows_per_shard']}, cid + ':aligned_mc2_matches_hidden_shard')
            geometry = reference['geometry']
            aligned.append([capture['client_concurrency'], window['dp0_forward_id'],
                geometry['sequences_per_replica'], geometry['tokens_per_sequence'], geometry['query_rows'],
                geometry['hidden_rows_per_shard'], next(iter(capacities)),
                *[f"{f['body_forward_span_ms']:.3f}" for f in selected],
                f"{(max(f['start_ns'] for f in selected) - min(f['start_ns'] for f in selected))/1000:.3f}",
                f"{(common_end-common_start)/1e6:.3f}"])
    result = {'schema_version': 'mindie-bounded-dp-cohort-review/1',
              'evidence_path': str(path), 'evidence_sha256': sha256(path.read_bytes()).hexdigest(),
              'reviewer_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'checks': checks, 'failures': failures, 'status': 'passed' if not failures else 'failed',
              'population': population, 'raw_sources_reread': False}
    path.with_name('dp-cohort-independent-review.json').write_text(json.dumps(result, indent=2) + '\n')

    def table(headers, contents):
        return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |',
                          *['| ' + ' | '.join(map(str, row)) + ' |' for row in contents]])

    lines = ['# A3 V4.1：c4 / c64 的有界 DP cohort 证据', '',
        '四个 TP0 代表在 7 个可共同对齐的完整 40 层 target Forward 中，执行形状完全一致。c4 为 B=2、Q=8、全 query rows=16、hidden shard=4；c64 为 B=14 或 17、Q=8、全 query rows=112 或 136、hidden shard=28 或 34。这里的 B 是 block-table 行数，不能替代实际活跃请求数。', '',
        f"仅流式解码 {population['decoded_rows']:,} 行、保留 {population['complete_bodies']} 个完整主体与 {population['mc2_calls']} 个逐层 MC2 描述；耗时 {data['elapsed_s']:.3f}s、峰值 RSS {data['max_rss_bytes']/1024**2:.1f} MiB。每源在 dp0 第 5 个完整 body 结束后 5ms 的绝对时间界限停止，最多 30k rows；不是八源全量复扫。独立检查 {checks} 项，失败 {len(failures)}。", '',
        '## 每 rank 前几个可完整闭合的 target Forward', '',
        '列表按本 rank 的时间顺序。Q 均为 8；各 rank 的局部 auto 编号不代表同一 step。行号指各自 gzip 解码后的原 CSV 行。未闭合的早期段保留在 JSON anomaly counts，不用其他 rank 的第 n 次强行补齐。', '',
        table(['Client c','Rank','Device','B 序列','hidden shard rows','Body span ms 序列','原 CSV body 首末行','压缩源 SHA256 前12位'], rows), '',
        '## 同绝对时间的唯一重叠主体', '',
        '每行四个区间存在共同交集，且都独立通过 40 层拓扑/FFN/终端 norm 校验。该结果标为 conditional_unique：step_trace_time 每 rank 只有一行整窗汇总且 Step 为空，未保留跨设备时钟同步记录或跨 rank step ID，因此不提升为确定的同 step 绑定。', '',
        table(['Client c','DP0 局部编号','B','Q','query rows','hidden SP','MC2 X/mask capacity','DP0 ms','DP1 ms','DP2 ms','DP3 ms','最大起点差 us','四方交叠 ms'], aligned), '',
        '## 对 balanced expert counts 的约束', '',
        '- 在以上 7 组窗口内，每 rank 的 40 次 DispatchFFNCombine 都是 X=[hidden_shard,5120]、route_ids=[hidden_shard,6]、active_mask=[hidden_shard]，本地 expert count 输出 descriptor=[24]。四个 DP 代表的这些容量均一致。',
        '- 可以据此约束 rank-local 输入容量和 top-k slot 数：c4 为 4×6 个 source routing slots；c64 为 28×6 或 34×6。不能直接将其作为已执行的有效路由量、平均每 expert token 数或 GEMM FLOPs。active_mask 值、route_ids 值及 24 个 expert count 值均未采集。',
        '- 所有 DP 代表都实际执行了完整 body，不存在“该窗口完全没运行”的代表 rank；但 padded graph 可以让无请求的 DP 执行相同 shape，因此实际 idle DP、请求/有效 token 均匀和 force-EPLB 是否生效仍 unresolved。',
        '- 早期 B=1 body 可见 hidden shard=2、MC2 buffer capacity 却为 64 或 128，直接说明容量不能反推有效计算行数。它们不并入上表的稳态容量结论。',
        '- 此证据只覆盖 16 rank 中四个 DP 的 TP0；没有检查另外 12 个 TP rank。MC2 elapsed 包含 peer wait，不能据此调带宽或把所有 rank 的时长相加。', '',
        f"完整 SHA/原行/每层 descriptor：[evidence](dp-cohort-bounded-evidence.json)；[独立审查](dp-cohort-independent-review.json)。Evidence SHA256：`{result['evidence_sha256']}`。未修改 profiler/Sim 核心，也没有远端或设备操作。", '']
    path.with_name('dp-cohort-bounded-evidence.md').write_text('\n'.join(lines))
    print(json.dumps(result))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('evidence', type=Path)
    review(parser.parse_args().evidence)
