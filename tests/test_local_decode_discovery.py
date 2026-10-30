"""Local intake uses real producer metadata instead of directory/token capacity."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from decode import capture_metadata, local_capture_directories, prepare_local_capture
from pipeline import discover_local, identity
from tests.sim_fixtures import case_path

FIXTURE = ROOT / 'tests/fixtures/pipeline/local_glm128k'


def registry(tmp_path):
    model = ROOT / 'examples/structure/cases/a3-glm53flash-heldout-tp16.json'
    row = {'id': 'decode:declared-glm', 'case_id': 'declared-glm', 'phase': 'decode',
           'sim_case_path': str(model), 'model_case': identity(model), 'source': {}}
    path = tmp_path / 'cases.json'
    value = {'schema_version': 'mindie-cases/1', 'cases': [row]}
    path.write_text(json.dumps(value))
    return path, value


def capture(tmp_path, *, device=True):
    path = tmp_path / 'capture_128k_decode_retained'
    path.mkdir()
    shutil.copyfile(FIXTURE / 'benchmark_summary.json', path / 'benchmark_summary.json')
    if device:
        shutil.copyfile(FIXTURE / 'kernel_details.csv', path / 'kernel_details.csv')
    return path


def test_real_client_prompt_is_not_directory_128k_or_kv_capacity(tmp_path):
    directory = capture(tmp_path)
    path, value = registry(tmp_path)
    before = deepcopy(value)
    prepared = prepare_local_capture(directory, value, path.parent, template_case_id='decode:declared-glm')
    entry = prepared['entry']
    assert prepared['status'] == 'prepared'
    assert entry['source'] == {**identity(directory / 'kernel_details.csv'), 'kind': 'csv'}
    assert entry['geometry_limit'] is None
    assert entry['context_evidence']['representative_tokens'] == 131201
    assert entry['context_evidence']['upper_bound_tokens'] == 131265
    assert entry['context_evidence']['per_step_context_observed'] is False
    assert entry['scenario_evidence']['client']['concurrency'] == 10
    assert entry['template_selection']['unobserved_parameters'] == ['model', 'hardware', 'tp', 'dp', 'ep', 'quant']
    assert entry['calibration']['evaluation_relation'] == 'not_declared'
    assert value == before


def test_discovery_preserves_device_missing_and_does_not_register_api_only(tmp_path):
    directory = capture(tmp_path, device=False)
    path, original = registry(tmp_path)
    found = list(local_capture_directories(tmp_path, '*_128k_decode_*'))
    assert found == [directory]
    result = discover_local(path, [tmp_path], patterns=['*_128k_decode_*'],
        output=tmp_path / 'discovery.json', archive_root=tmp_path / 'evidence',
        template_case_id='declared-glm', update=True)
    assert result['summary']['registered_ids'] == []
    assert result['cases'][0]['reasons'] == ['device_capture_missing']
    assert json.loads(path.read_text()) == original
    assert result['new_Sim_predictions'] == 0


def test_no_template_is_selected_from_case_name_or_past_accuracy(tmp_path):
    directory = capture(tmp_path)
    path, value = registry(tmp_path)
    value['cases'][0]['comparison'] = {'passed': True}
    prepared = prepare_local_capture(directory, value, path.parent)
    assert prepared['entry'] is None
    assert 'explicit_or_unique_exact_capture_template_required' in prepared['reasons']
    # Co-located metadata has no model/parallel declaration; an incomplete
    # registry match must not make missing fields look observed.
    value['capture_templates'] = [{'case_id': 'declared-glm', 'match': {'tp': 16}}]
    assert prepare_local_capture(directory, value, path.parent)['entry'] is None


def test_real_prefill_record_does_not_become_a_complete_decode_capture(tmp_path):
    capture(tmp_path)
    path, original = registry(tmp_path)
    result = discover_local(path, [tmp_path], patterns=['*_128k_decode_*'],
        output=tmp_path / 'discovery.json', archive_root=tmp_path / 'evidence',
        template_case_id='declared-glm', update=True)
    assert result['cases'][0]['status'] == 'unresolved'
    assert result['cases'][0]['reasons'] == ['complete_decode_topology_not_found']
    assert json.loads(path.read_text()) == original


def test_metadata_requires_explicit_prompt_not_native_cache_allocation(tmp_path):
    directory = capture(tmp_path)
    summary = json.loads((directory / 'benchmark_summary.json').read_text())
    summary.pop('input_tokens')
    summary['native'].pop('InputTokens')
    (directory / 'benchmark_summary.json').write_text(json.dumps(summary))
    metadata = capture_metadata(directory)
    assert metadata['context_evidence']['representative_tokens'] is None
    assert metadata['context_evidence']['upper_bound_tokens'] is None


def test_real_qwen36_tp2_uses_full_prompt_usage_and_retains_deployment_gaps(tmp_path):
    fixtures = ROOT / 'tests/fixtures/pipeline/local_a5_metadata'
    shutil.copyfile(fixtures / 'qwen36-benchmark.json', tmp_path / 'benchmark_summary.json')
    shutil.copyfile(fixtures / 'qwen36-client-cell.json', tmp_path / 'client_cell.json')
    metadata = capture_metadata(tmp_path)
    assert metadata['client'] == {'input_len': 4104, 'concurrency': 1, 'output_tokens': 640}
    assert metadata['context_evidence']['requested_prefix_tokens'] == 4096
    assert metadata['context_evidence']['upper_bound_tokens'] == 4744
    assert metadata['context_evidence']['per_step_context_observed'] is False
    assert metadata['capture_parameters'] == {'model': '/mnt/weight/Qwen3.6-27B-W8A8',
        'hardware': 'Ascend950DT_9582', 'tp': 2, 'quant': 'ascend (W8A8)'}
    assert metadata['parameter_sources']['tp']['field'] == 'tensor_parallel_size'
    assert metadata['parameter_sources']['hardware']['field'] == 'extra.host_deviation.identical_hardware'
    # A known TP2 deployment cannot silently bind an explicit TP4 template.
    wrong = case_path('qwen36-a3-tp4.json')
    registry = {'cases': [{'id': 'decode:wrong-tp', 'case_id': 'wrong-tp', 'phase': 'decode',
        'sim_case_path': str(wrong), 'model_case': identity(wrong)}]}
    candidate = prepare_local_capture(tmp_path, registry, tmp_path, template_case_id='decode:wrong-tp')
    assert 'capture_template_deployment_mismatch' in candidate['reasons']
    assert candidate['entry'] is None


def test_real_qwen35_usage_does_not_invent_parallelism(tmp_path):
    source = ROOT / 'tests/fixtures/pipeline/local_a5_metadata/qwen35-benchmark.json'
    shutil.copyfile(source, tmp_path / 'benchmark_summary.json')
    metadata = capture_metadata(tmp_path)
    assert metadata['client'] == {'input_len': 4096, 'concurrency': 4, 'output_tokens': 256}
    assert metadata['context_evidence']['basis'] == 'retained_request_prompt_usage'
    assert metadata['context_evidence']['upper_bound_tokens'] == 4352
    assert metadata['capture_parameters'] == {'model': 'qwen35'}


def test_requested_prompt_fallback_is_not_reported_as_observed_usage(tmp_path):
    source = ROOT / 'tests/fixtures/pipeline/local_a5_metadata/qwen36-client-cell.json'
    payload = json.loads(source.read_text())
    # Actual usage fields may be absent when a producer cannot recover tokens.
    payload.pop('observed_prompt_tokens')
    for row in payload['per_request']:
        row.pop('prompt_tokens')
    (tmp_path / 'benchmark_summary.json').write_text(json.dumps(payload))
    context = capture_metadata(tmp_path)['context_evidence']
    assert context['representative_tokens'] == 4104
    assert context['basis'] == 'requested_prefix_plus_suffix_condition'
