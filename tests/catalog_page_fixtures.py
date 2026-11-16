"""Reassembly helpers for bounded catalog page fixtures.

[Role]
  Apply flat path/value units and split-path segments back into one mapping.
[Invariants]
  Integer path components address arrays; string components address mappings.
  Segments are never merged with a differently typed unit.
[Timeouts & Locks]
  Pure in-memory arithmetic.
[Side-Effect Policy]
  No I/O; callers own the paged payload.
"""

from __future__ import annotations


def _assign(root, path, value):
    if not path:
        if isinstance(value, dict):
            root.update(value)
        return
    node = root
    for position, token in enumerate(path[:-1]):
        following = path[position + 1]
        if isinstance(token, int):
            while len(node) <= token:
                node.append(None)
            if node[token] is None:
                node[token] = [] if isinstance(following, int) else {}
            node = node[token]
        else:
            child = node.get(token)
            if not isinstance(child, (dict, list)):
                child = [] if isinstance(following, int) else {}
                node[token] = child
            node = child
    last = path[-1]
    if isinstance(last, int):
        while len(node) <= last:
            node.append(None)
        node[last] = value
    else:
        node[last] = value


def _reassemble(pages):
    root = {}
    segments = {}
    for page in pages:
        for unit in page["items"]:
            path, value = unit[0], unit[1]
            if len(unit) == 3:
                segments.setdefault(tuple(path), {})[unit[2]] = value
            else:
                _assign(root, path, value)
    for path, parts in segments.items():
        _assign(root, list(path),
                "".join(parts[offset] for offset in sorted(parts)))
    return root
