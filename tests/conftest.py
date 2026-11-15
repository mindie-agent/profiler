"""[Role] Shared pytest isolation for the standalone profiler test suite.
[Invariants] Tests never inherit developer contribution or GitHub credentials.
[Timeouts & Locks] No locks, timers, sleeps, or background services.
[Side-Effect Policy] Monkeypatches process environment only; writes no files.
"""
import os
import shutil
import sys
import tempfile

import pytest

from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
_REPO_ROOT = str(Path(__file__).resolve().parents[1])
for _entry in (_TESTS_DIR, _REPO_ROOT):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)


_SIM_SOURCE = os.environ.get("MINDIE_SIM_SOURCE")
if _SIM_SOURCE and _SIM_SOURCE not in sys.path:
    # Apply the supported source environment before any test imports mindie_sim,
    # so parent collectors and spawned evaluator workers resolve one identity.
    sys.path.insert(0, _SIM_SOURCE)


@pytest.fixture(scope="session")
def _session_sim_cache_home(tmp_path_factory):
    base = tmp_path_factory.getbasetemp()
    if "PYTEST_XDIST_WORKER" in os.environ:
        base = base.parent
    return str(base / "mindie-sim-cache")


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch, _session_sim_cache_home):
    # Tests must not use a developer's real contribution or GitHub settings.
    # Setting (rather than deleting) also restores env changes made directly by
    # runner-under-test code, even when the original variable did not exist.
    for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'MINDIE_COMMUNITY_POLICY'):
        monkeypatch.setenv(key, '')
    root = tmp_path.resolve()
    for key, name in (
        ('HOME', 'home'),
        ('USERPROFILE', 'home'),
        ('XDG_CONFIG_HOME', 'xdg-config'),
        ('XDG_CACHE_HOME', 'xdg-cache'),
        ('XDG_STATE_HOME', 'xdg-state'),
        ('LOCALAPPDATA', 'local-app-data'),
        ('MINDIE_CONFIG_HOME', 'mindie-config'),
        ('MINDIE_DATA_HOME', 'mindie-data'),
    ):
        monkeypatch.setenv(key, str(root / name))
    if not os.environ.get('MINDIE_CACHE_HOME'):
        monkeypatch.setenv('MINDIE_CACHE_HOME', _session_sim_cache_home)
    monkeypatch.setenv('MINDIE_DIAGNOSTICS_ROOT', str(root / 'isolated-diagnostics'))
    monkeypatch.setenv('MINDIE_DIAGNOSTICS_CONFIG', str(root / 'reporting.json'))
    Path('/tmp').mkdir(parents=True, exist_ok=True)
    short_root = tempfile.mkdtemp(prefix='mpr_', dir='/tmp')
    monkeypatch.setenv('MINDIE_REPRO_SHORT_ROOT', short_root)
    try:
        yield
    finally:
        shutil.rmtree(short_root, ignore_errors=True)
