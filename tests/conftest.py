"""[Role] Shared pytest isolation for the standalone profiler test suite.
[Invariants] Tests never inherit developer contribution or GitHub credentials.
[Timeouts & Locks] No locks, timers, sleeps, or background services.
[Side-Effect Policy] Monkeypatches process environment only; writes no files.
"""
import os
import sys

import pytest


_SIM_SOURCE = os.environ.get("MINDIE_SIM_SOURCE")
if _SIM_SOURCE and _SIM_SOURCE not in sys.path:
    # Apply the supported source environment before any test imports mindie_sim,
    # so parent collectors and spawned evaluator workers resolve one identity.
    sys.path.insert(0, _SIM_SOURCE)


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
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
        ('XDG_STATE_HOME', 'xdg-state'),
        ('LOCALAPPDATA', 'local-app-data'),
        ('MINDIE_CONFIG_HOME', 'mindie-config'),
        ('MINDIE_DATA_HOME', 'mindie-data'),
    ):
        monkeypatch.setenv(key, str(root / name))
    monkeypatch.setenv('MINDIE_DIAGNOSTICS_ROOT', str(root / 'isolated-diagnostics'))
    monkeypatch.setenv('MINDIE_DIAGNOSTICS_CONFIG', str(root / 'reporting.json'))
