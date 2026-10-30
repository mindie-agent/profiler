"""[Role] Move large tracked acceptance payloads out of the release tree.
[Invariants] Original paths stay usable locally; immutable SHA256 objects retain
  every byte, while an index and exact ignore entries replace Git tracking.
[Timeouts & Locks] Streaming copies/hashes; bounded Git calls, no shared locks.
[Side-Effect Policy] Explicit --apply archives files, updates index and Git index.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from scoreboard_archive import digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-root', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    index_path = root / 'examples/structure/acceptance-archive-index.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {
        'schema_version': 'mindie-acceptance-archive/1', 'objects': []}
    known = {r['repository_path']: r for r in index['objects']}
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root, timeout=15)
    selected = [Path(p.decode()) for p in tracked.split(b'\0') if p]
    selected = [p for p in selected if (root / p).is_file() and (root / p).stat().st_size > 10_000_000]
    if not args.apply:
        print(json.dumps({'large_files': [str(p) for p in selected]})); return
    args.archive_root.mkdir(parents=True, exist_ok=True)
    for relative in selected:
        source = root / relative; sha = digest(source)
        target = args.archive_root / (sha + source.suffix)
        if not target.exists():
            with source.open('rb') as inp, target.open('xb') as out:
                shutil.copyfileobj(inp, out, 1024 * 1024)
        if digest(target) != sha:
            raise ValueError('archive content mismatch: ' + str(target))
        known[str(relative)] = {'repository_path': str(relative), 'sha256': sha,
                               'size_bytes': source.stat().st_size, 'archive_path': str(target.resolve())}
    index['objects'] = sorted(known.values(), key=lambda r: r['repository_path'])
    index_path.write_text(json.dumps(index, indent=2) + '\n')
    ignore = root / '.gitignore'; lines = ignore.read_text().splitlines()
    additions = ['/' + str(p) for p in selected if '/' + str(p) not in lines]
    if additions:
        ignore.write_text('\n'.join(lines + ['# External content-addressed acceptance archives'] + additions) + '\n')
    if selected:
        subprocess.run(['git', 'rm', '--cached', '--', *map(str, selected)], cwd=root,
                       check=True, timeout=30, stdout=subprocess.DEVNULL)
    print(json.dumps({'archived_files': len(selected), 'index_objects': len(known),
                      'archived_bytes': sum((root / p).stat().st_size for p in selected)}))


if __name__ == '__main__':
    main()
