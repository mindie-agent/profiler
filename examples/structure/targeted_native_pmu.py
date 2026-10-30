"""Raw PMU summaries alongside the shared streaming CSV event decoder.

[Role] Preserve exporter counters and locator examples for selected native ABI groups.
[Invariants] Missing/NA and measured zero differ; task ID is not an occurrence ID.
  Pipeline times are exporter measurements, not inferred communication waits.
[Timeouts & Locks] One stream; 180 s and 5M rows by default; bounded histograms.
[Side-Effect Policy] Read-only CSV; no devices, remote calls or predictions.
"""
import csv
from collections import Counter
from decimal import Decimal
from math import ceil
import time

from mindie_profiler.events import ProfilerQueryError, QueryStats
from mindie_profiler.normalized import row_from_event
from mindie_profiler.sources_csv import _number, _open_csv_text, decode_csv_row


def scan_rows(path, schema, native_types, *, max_rows=5_000_000, timeout_s=180):
    deadline = time.perf_counter() + timeout_s
    stats = QueryStats(rank_id='rank_0', window_label='targeted_native_with_raw_pmu', budget=max_rows)
    with _open_csv_text(path) as handle:
        reader = csv.reader(handle)
        if tuple(next(reader)) != schema.header:
            raise ValueError('csv_header_changed_after_probe')
        for index, row in enumerate(reader):
            if index >= max_rows or (index % 1024 == 0 and time.perf_counter() > deadline):
                raise ProfilerQueryError('targeted_pmu_csv_budget_exceeded')
            event = decode_csv_row(row, index, schema, rank_id='rank_0', rank_index=0, stats=stats, strict=True)
            if event is None: continue
            raw = {name: row[i].strip() if i < len(row) else None for i, name in enumerate(schema.header)} if event.op_type in native_types else None
            yield row_from_event(event), raw


def numeric_stats(counter):
    pairs = sorted((Decimal(value), n) for value, n in counter.items())
    count = sum(n for _, n in pairs)
    if not count: return None
    def at(index):
        seen = 0
        for value, n in pairs:
            seen += n
            if seen > index: return value
        raise ValueError('pmu_histogram_index_outside_population')
    return {'count': count, 'mean': float(sum(v*n for v,n in pairs)/count),
        'p50': float((at((count-1)//2)+at(count//2))/2),
        'p90': float(at(ceil(count*.9)-1)), 'min': float(pairs[0][0]), 'max': float(pairs[-1][0])}


class NativePmu:
    def __init__(self, header):
        self.header = tuple(header)
        self.numeric = {name: Counter() for name in header if name.startswith(('aic_', 'aiv_'))
            or name in {'aicore_time(us)', 'cube_utilization(%)', 'Duration(us)', 'Wait Time(us)', 'Block Num', 'Mix Block Num'}}
        self.status = {name: Counter() for name in self.numeric}
        self.dimensions = {name: Counter() for name in ('Accelerator Core', 'OP State', 'Block Num', 'Mix Block Num', 'Device_id', 'Stream ID', 'Model ID', 'Context ID')}
        self.count = 0
        self.examples, self.longest = [], []

    def add(self, raw, event, *, forward_id, layer_id):
        self.count += 1
        for name, values in self.numeric.items():
            text = raw.get(name); status = self.status[name]
            if text is not None: status['present_count'] += 1
            if text is None or text.upper() in {'', 'N/A', 'NA', 'NONE', 'NULL', 'NAN'}:
                status['missing_or_na_count'] += 1
                continue
            status['non_na_count'] += 1
            value = _number(text)
            if value is None:
                status['invalid_numeric_count'] += 1
                continue
            status['numeric_count'] += 1
            if value == 0: status['zero_count'] += 1
            values[str(value)] += 1
        for name, values in self.dimensions.items():
            values[raw.get(name)] += 1
        example = {'locator': event.locator, 'event_id': event.event_id,
            'forward_id': forward_id, 'layer_id': layer_id,
            'start_ns': event.start_ns, 'end_ns': event.end_ns, 'duration_ns': event.duration_ns,
            'raw_fields': {name: raw.get(name) for name in ('Task ID', *self.dimensions, *self.numeric)}}
        if len(self.examples) < 2: self.examples.append(example)
        self.longest.append(example)
        self.longest.sort(key=lambda x: (-x['duration_ns'], x['start_ns']))
        del self.longest[5:]

    def result(self):
        return {'event_count': self.count, 'header_columns': list(self.header),
            'fields': {name: {'column_present': name in self.header,
                **{key: self.status[name].get(key, 0) for key in ('present_count', 'non_na_count', 'missing_or_na_count', 'numeric_count', 'invalid_numeric_count', 'zero_count')},
                'statistics': numeric_stats(values), 'numeric_value_counter': sorted(values.items(), key=lambda x: Decimal(x[0]))}
                for name, values in self.numeric.items()},
            'dimensions': {name: [[value, count] for value, count in sorted(values.items(), key=lambda x: str(x[0]))]
                           for name, values in self.dimensions.items()},
            'examples': self.examples, 'longest_calls': self.longest,
            'interpretation': ['Missing values remain absent, not measured zero.',
                'Task ID can repeat; full event/CSV locator identifies each retained example.',
                'PMU time/ratio fields remain in exporter units; pipelines may overlap.',
                'High scalar activity is not by itself evidence of network or peer waiting.']}
