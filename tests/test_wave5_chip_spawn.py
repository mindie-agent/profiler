"""Spawn the actual archived evaluator with maintained inputs and output paths.

[Role] Check process-boundary propagation of the current simulator identity.
[Invariants] Prediction and extraction caches are written outside the archive;
  workers receive the same explicitly imported catalog as the parent.
[Timeouts & Locks] One local spawned worker; 10-second future deadlines.
[Side-Effect Policy] Reads the optional local archive and retained CSV fixture;
  all generated files and environment homes are isolated by tmp_path.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import wave5_generalization_eval as wave5


@pytest.mark.skipif(not (wave5.DEFAULT_ARCHIVE_ROOT / "a3" / "eval_a3_wave5.py").is_file(),
                    reason="local Wave 5 archived evaluator is not installed")
def test_archived_workers_use_imported_catalog_current_identity_and_separate_cache(tmp_path):
    archive_files = {
        str(path): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in wave5.DEFAULT_ARCHIVE_ROOT.rglob("*") if path.is_file()
    }
    cache = tmp_path / "chip-cache"
    module, provenance = wave5._configure_chip("a3", wave5.DEFAULT_ARCHIVE_ROOT, cache, wave5.SIM_IDENTITY)
    assert provenance["changed_rule_count"] == 36
    traits = {"cohort": "a3/priority_b_400k_1m/kimik3_4l_tp8_ep8_decode",
              "context_tokens": 196608, "concurrency": 1}
    _, template, _, _ = module.resolve_template(traits)
    key = (sha256(json.dumps(template, sort_keys=True).encode()).hexdigest()[:16], "decode", 1, 512, 1)
    capture = ROOT / "tests" / "fixtures" / "profiler_core" / "real_a3_wait_pmu" / "kernel_details.csv"
    pool = module.ProcessPoolExecutor(max_workers=1)
    procs = []
    try:
        returned_key, predicted = pool.submit(module._predict_worker, (key, template)).result(timeout=10)
        _, extracted = pool.submit(module._extract_worker, (
            str(capture), {"phase": "prefill", "tp": 8}, template, {},
        )).result(timeout=10)
        procs = list((getattr(pool, "_processes", None) or {}).values())
    finally:
        if not procs:
            procs = list((getattr(pool, "_processes", None) or {}).values())
        pool.shutdown(wait=False, cancel_futures=True)
        for proc in procs:
            if proc.is_alive():
                proc.terminate()
            proc.join(timeout=2)
    assert returned_key == key
    assert predicted["status"] == "modeled"
    material = f"v2:{wave5.SIM_IDENTITY}:{key[0]}:decode:1:512:1"
    prediction_path = module.CACHE_ROOT / f"pred_{sha256(material.encode()).hexdigest()[:24]}.json"
    assert json.loads(prediction_path.read_text()) == json.loads(json.dumps(predicted))
    assert (module.CACHE_ROOT / f"{extracted['cache_key']}.json").is_file()
    assert predicted["native_observation_provenance"]["arm"] == "observed_native"
    catalog_path = wave5.DEFAULT_ARCHIVE_ROOT / "a3" / "templates" / "_regime_catalog.json"
    assert sha256(catalog_path.read_bytes()).hexdigest() == provenance["catalog"]["sha256"]
    assert archive_files == {
        str(path): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in wave5.DEFAULT_ARCHIVE_ROOT.rglob("*") if path.is_file()
    }
