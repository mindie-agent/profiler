"""Pinned test declarations work with an installed Sim wheel, without its checkout."""
from hashlib import sha256
import json
from pathlib import Path

DIRECTORY = Path(__file__).parent / 'fixtures/sim_declarations'


def case_path(name):
    """Resolve one unchanged source declaration and verify its retained identity."""
    path = DIRECTORY / name
    provenance = json.loads((DIRECTORY / 'provenance.json').read_text())
    record = next(row for row in provenance['files'] if row['fixture'] == name)
    assert sha256(path.read_bytes()).hexdigest() == record['sha256']
    return path
