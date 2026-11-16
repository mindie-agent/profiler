#!/usr/bin/env python3
"""Stdlib-only, fail-closed numeric-literal gate. Never imports inspected code.

Strict: python3 check_no_magic_numbers.py --root sim=/repo/mindie_sim
Debt ratchet: add --baseline gate_baseline.json. Hash-identical, previously
parsed files reuse their census; changed files are parsed and compared as
multisets of (symbol, enclosing statement AST, value). No uppercase exemption.
Exit 0: clean under selected policy; 1: new/non-exempt literals; 2: input error.
All output is stdout/stderr. This gate creates no files, caches or bytecode.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
import argparse
import ast
import collections
import hashlib
import json
import os
import stat
import time
import tokenize
import io
import datetime

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['GIT_OPTIONAL_LOCKS'] = '0'
VERSION = 'magic-number-gate/1'
TRIVIAL = frozenset((0, 1, -1, 2, 0.5))
UNIT_VALUES = frozenset((100, 1000, 1000000, 1000000000))
# Lexical check MUST precede ANY filesystem operation; no resolve/realpath.
FORBIDDEN = (
    '/Volumes/data/Codex/2026-11-12/kan-x/work/a5-implementation/jobs/A5-HOLDOUT',
    '/Volumes/data/Codex/2026-11-12/kan-x/outputs/a5-implementation/holdout',
)
UNIT_NAMES = ('_ms', '_us', '_ns', '_hz', '_gbps', '_tflops', 'per_second',
              'per_ms', 'per_s', 'seconds', 'milliseconds', 'microseconds',
              'percent', 'pct', '_gb', '_mb', 'duration_ms', 'duration_us')


def checked_path(path):
    value = os.path.abspath(os.fspath(path))
    if any(value == p or value.startswith(p + os.sep) for p in FORBIDDEN):
        raise ValueError('forbidden path rejected lexically')
    # User-specified repo roots can have symlink ancestors (this workspace does).
    # Resolve one hop at a time, lexically rejecting forbidden destinations
    # BEFORE lstat/open on the destination. Descendant links are still rejected.
    pending = value.split(os.sep)[1:]
    current, hops = os.sep, 0
    while pending:
        current = os.path.join(current, pending.pop(0))
        if stat.S_ISLNK(os.lstat(current).st_mode):
            hops += 1
            if hops > 40:
                raise ValueError('symlink loop')
            target = os.readlink(current)
            target = os.path.abspath(os.path.join(os.path.dirname(current), target))
            combined = os.path.join(target, *pending)
            if any(target == p or target.startswith(p + os.sep) or combined == p or combined.startswith(p + os.sep) for p in FORBIDDEN):
                raise ValueError('forbidden symlink destination rejected lexically')
            pending, current = combined.split(os.sep)[1:], os.sep
    return value


def files_in(root):
    root = checked_path(root)
    if os.path.isfile(root):
        if not root.endswith('.py'):
            raise ValueError('expected Python file: ' + root)
        yield root, os.path.basename(root)
        return
    def walk_error(exc):
        raise exc
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        kept = []
        for name in sorted(dirs):
            candidate = os.path.join(directory, name)
            if any(candidate == p or candidate.startswith(p + os.sep) for p in FORBIDDEN):
                raise ValueError('forbidden descendant rejected lexically')
            if os.path.islink(candidate):
                raise ValueError('symlink directory rejected: ' + candidate)
            if name != '__pycache__':
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            if name.endswith('.py'):
                path = os.path.join(directory, name)
                if os.path.islink(path):
                    raise ValueError('symlink file rejected: ' + path)
                yield path, os.path.relpath(path, root).replace(os.sep, '/')


def read_source(path):
    # O_NOFOLLOW also closes the final-component symlink race. No imports.
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as stream:
        data = stream.read()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data, data.decode(encoding)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stable_dump(node):
    """Version-stable AST dump: 3.12+ adds ``type_params`` and hides empty fields."""
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            fields = getattr(child, '_fields', ())
            if 'type_params' in fields:
                child._fields = tuple(field for field in fields if field != 'type_params')
    try:
        return ast.dump(node, include_attributes=False, show_empty=True)
    except TypeError:  # Python < 3.13 always includes empty optional fields.
        return ast.dump(node, include_attributes=False)


def numeric_census(source, filename='<source>'):
    """Return all nontrivial literals, including contextual unit exemptions.

    Unary +/- is one signed occurrence; bool/complex/strings aren't numbers
    for this rule. Folded expressions remain distinct literal occurrences.
    Annotation/default/decorator/dict/set/match/f-string expressions are walked.
    """
    tree = ast.parse(source, filename=filename)
    lines = source.splitlines()
    rows = []
    hashes = {}
    excluded = collections.Counter()

    def visit(node, scope, binding, anchor, ancestors):
        cls = type(node)
        if cls in (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef):
            scope = scope + (node.name,)
        if isinstance(node, ast.stmt) and cls not in (
                ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef):
            anchor = node
        if cls in (ast.Assign, ast.AnnAssign, ast.AugAssign):
            target = node.targets[0] if cls is ast.Assign else node.target
            binding = ast.unparse(target)
        if cls is ast.keyword:
            binding = node.arg or binding
        value_node = node
        signed = cls is ast.UnaryOp and type(node.op) in (ast.USub, ast.UAdd) and (
            type(node.operand) is ast.Constant and type(node.operand.value) in (int, float))
        if signed:
            value = (-1 if type(node.op) is ast.USub else 1) * node.operand.value
        elif cls is ast.Constant and type(node.value) in (int, float):
            value = node.value
        else:
            value = None
        if value is not None:
            if value in TRIVIAL:
                excluded['trivial'] += 1
                return
            parent = ancestors[-1] if ancestors else node
            owner = anchor or parent
            if owner not in hashes:
                hashes[owner] = digest(stable_dump(owner).encode())
            symbol = '.'.join(scope) or '<module>'
            # Context only exempts unit factors used in multiplication/division.
            near = ' '.join((binding, ast.unparse(parent))).lower()
            conversion = (value in UNIT_VALUES and isinstance(parent, ast.BinOp)
                          and isinstance(parent.op, (ast.Mult, ast.Div, ast.FloorDiv))
                          and any(word in near for word in UNIT_NAMES))
            if node.lineno == node.end_lineno:
                text = lines[node.lineno-1].encode('utf-8')[node.col_offset:node.end_col_offset].decode('utf-8')
            else:
                pieces = [lines[node.lineno-1].encode('utf-8')[node.col_offset:].decode('utf-8')]
                pieces.extend(lines[node.lineno:node.end_lineno-1])
                pieces.append(lines[node.end_lineno-1].encode('utf-8')[:node.end_col_offset].decode('utf-8'))
                text = '\n'.join(pieces)
            signature = digest(json.dumps([symbol, binding, hashes[owner], type(value).__name__, repr(value)],
                                         ensure_ascii=True, separators=(',', ':')).encode())
            rows.append(dict(line=node.lineno, column=node.col_offset, end_line=node.end_lineno,
                             end_column=node.end_col_offset, symbol=symbol, binding=binding,
                             literal=text, value=value, numeric_type=type(value).__name__,
                             parent_type=type(parent).__name__, statement_sha256=hashes[owner],
                             signature=signature, unit_conversion_exempt=conversion,
                             source_line=lines[node.lineno-1].strip()[:800],
                             expression=ast.unparse(parent)[:500]))
            return
        # Give nested dictionaries their exact semantic key, rather than only
        # the outer table's name. Keys themselves still receive an AST visit.
        if cls is ast.Dict:
            for key, item in zip(node.keys, node.values):
                if key is not None:
                    visit(key, scope, binding, anchor, ancestors + (node,))
                key_name = str(key.value) if isinstance(key, ast.Constant) else ''
                visit(item, scope, '.'.join(x for x in (binding, key_name) if x), anchor, ancestors + (node,))
            return
        if cls is ast.arguments:
            args = node.posonlyargs + node.args
            for arg in args + node.kwonlyargs:
                if arg.annotation:
                    visit(arg.annotation, scope, arg.arg, arg.annotation, ancestors + (node,))
            for arg, default in zip(args[-len(node.defaults):], node.defaults):
                visit(default, scope, arg.arg, default, ancestors + (node,))
            for arg, default in zip(node.kwonlyargs, node.kw_defaults):
                if default is not None:
                    visit(default, scope, arg.arg, default, ancestors + (node,))
            for arg in (node.vararg, node.kwarg):
                if arg and arg.annotation:
                    visit(arg.annotation, scope, arg.arg, arg.annotation, ancestors + (node,))
            return
        for child in ast.iter_child_nodes(node):
            visit(child, scope, binding, anchor, ancestors + (node,))

    visit(tree, (), '', None, ())
    rows.sort(key=lambda r: (r['line'], r['column']))
    return rows, dict(excluded)


def counts(rows):
    return collections.Counter(r['signature'] for r in rows if not r['unit_conversion_exempt'])


def main(argv=None):
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='append', required=True, metavar='LABEL=PATH',
                        help='explicit production package root; repeat for multiple roots')
    parser.add_argument('--baseline', help='trusted, reviewed debt manifest; omit for strict mode')
    parser.add_argument('--exceptions', help='exact, provenance-tagged literal exceptions (JSON); no globs')
    parser.add_argument('--max-diagnostics', type=int, default=20)
    args = parser.parse_args(argv)
    try:
        baseline = {'files': {}, 'contents': {}}
        if args.baseline:
            raw, _ = read_source(checked_path(args.baseline))
            baseline = json.loads(raw)
            if baseline.get('schema') != VERSION:
                raise ValueError('incompatible baseline schema')
        exemptions = collections.defaultdict(collections.Counter)
        if args.exceptions:
            raw, _ = read_source(checked_path(args.exceptions))
            declaration = json.loads(raw)
            if declaration.get('schema') != 'magic-number-exceptions/1':
                raise ValueError('incompatible exception schema')
            for item in declaration['entries']:
                required = {'file', 'signature', 'count', 'category', 'reason', 'source', 'owner', 'expires'}
                if set(item) != required or not all(item[k] for k in required):
                    raise ValueError('exceptions require exact keys and nonempty provenance')
                if item['category'] not in {'H-CAP','H-TOPO','H-TIME','M-GEOM','P-HEUR'}:
                    raise ValueError('invalid exception category')
                if type(item['count']) is not int or item['count'] < 1:
                    raise ValueError('exception count must be positive integer')
                if len(item['signature']) != 64 or any(c not in '0123456789abcdef' for c in item['signature']):
                    raise ValueError('invalid exception signature')
                if datetime.date.fromisoformat(item['expires']) < datetime.date.today():
                    raise ValueError('expired literal exception')
                if any(c in item['file'] for c in '*?['):
                    raise ValueError('exception paths cannot be patterns')
                exemptions[item['file']][item['signature']] += item['count']
        labels = set()
        seen = set()
        file_count = cached = new_count = debt = 0
        parsed = {}
        diagnostics = []
        for spec in args.root:
            if '=' not in spec:
                raise ValueError('--root must be LABEL=PATH')
            label, root = spec.split('=', 1)
            if not label or label in labels:
                raise ValueError('duplicate/empty root label')
            labels.add(label)
            root_count = 0
            for path, relative in files_in(root):
                root_count += 1
                key = label + ':' + relative
                seen.add(key)
                data, source = read_source(path)
                sha = digest(data)
                old = baseline['files'].get(key)
                file_count += 1
                if old == sha:
                    if sha not in baseline['contents']:
                        raise ValueError('baseline missing parsed content record')
                    cached += 1
                    debt += sum(baseline['contents'][sha].values())
                    continue
                if sha not in parsed:
                    parsed[sha] = numeric_census(source, path)[0]
                rows = parsed[sha]
                current = counts(rows)
                previous = collections.Counter(baseline['contents'].get(old, {})) if old else collections.Counter()
                new = current - previous - exemptions[key]
                new_count += sum(new.values())
                debt += sum((current & previous).values())
                for row in rows:
                    signature = row['signature']
                    if new[signature] and len(diagnostics) < max(0, args.max_diagnostics):
                        diagnostics.append(f"{path}:{row['line']}:{row['column']+1}: {row['symbol']} "
                                           f"{row['binding']}: numeric literal {row['literal']}")
                        new[signature] -= 1
            if not root_count:
                raise ValueError('empty root: ' + root)
        # Prevent passing a subset under a reviewed root label to hide debt.
        missing = sorted(k for k in baseline['files'] if k.split(':', 1)[0] in labels and k not in seen)
        if missing:
            raise ValueError('baseline files absent from selected root; review manifest removal: ' + missing[0])
        for diagnostic in diagnostics:
            print(diagnostic)
        print(json.dumps(dict(mode='no-new-debt' if args.baseline else 'strict',
                              files=file_count, parsed_unique_contents=len(parsed), hash_reused_files=cached,
                              existing_debt_literals=debt, new_literals=new_count,
                              elapsed_seconds=round(time.perf_counter()-started, 6)), sort_keys=True))
        return 1 if new_count else 0
    except (OSError, ValueError, SyntaxError, RecursionError, KeyError, TypeError) as exc:
        print('magic-number gate input error: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
