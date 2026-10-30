"""Build explicit in-sample GLM service regimes from retained complete populations.

[Role] Bind observed native call service to physical recipe/shape coordinates.
[Invariants] No Body residual assigns parameters; inclusive native responses are
  applied once. Pooled copy directions and native ABI gaps remain explicit.
[Timeouts & Locks] Small saved JSON inputs and one source graph at a time; no locks.
[Side-Effect Policy] Writes only this acceptance directory; no capture/device I/O.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FIXED = Path('/tmp/mindie-sim-cohort-wave6-20261029').resolve()
ORDER = ['a5_glm53flash_tp8_c64_p4k', 'a5_glm53flash_tp8_c32_p4k',
         'a5_glm53flash_tp8_c32_p8k', 'a5_glm53flash_tp8_c16_p4k',
         'a5_glm53flash_tp8_c16_p8k', 'a5_glm53flash_tp8_c8_p4k',
         'a5_glm53flash_tp8_c4_p8k', 'glm53flash-a5-tp8-c3', 'glm53flash-a5-tp8-c1']
NATIVES = {'hcom_allReduce_AicpuKernel': 90, '_copy_conv_state_kernel': 68,
           'MoeInitRoutingV3': 42, 'GroupedMatmulSwigluQuantV2': 42,
           'CausalConv1d': 34, 'RecurrentKda': 34}


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def summarize(families):
    counts = Counter()
    for family in families:
        counts.update({int(k): n for k, n in family['duration_ns_counter']})
    size = sum(counts.values())
    def percentile(p):
        at = (size-1)*p
        lo, hi = int(at), min(int(at)+1, size-1)
        found = []
        for rank in (lo, hi):
            cumulative = 0
            for value, count in sorted(counts.items()):
                cumulative += count
                if cumulative > rank:
                    found.append(value)
                    break
        return (found[0] + (found[1]-found[0])*(at-lo))/1000
    return {'count': size, 'mean_us': sum(k*v for k,v in counts.items())/size/1000,
            'p50_us': percentile(.5), 'p90_us': percentile(.9),
            'duration_ns_counter': [[k,v] for k,v in sorted(counts.items())]}


def prepare():
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.operator_analysis import target_graphs
    manifest_path = ROOT/'examples/structure/acceptance-20261030-source-complete/decode-forward-glm-cases.json'
    operator_path = ROOT/'examples/structure/acceptance-20261030-glm-source-complete-operators/body-operator-family-scoreboard.json'
    generation_path = ROOT/'examples/structure/acceptance-20261030-controller-alias/extraction-generation-map.json'
    manifest = read(manifest_path)
    declared = {r['case_id']: r for r in manifest['cases']}
    operator = {r['source_case_id']: r for r in read(operator_path)['cases']}
    generations = {r['case_id']: r for r in read(generation_path)['cases']}
    out, evidence = [], []
    for cid in ORDER:
        row = deepcopy(declared[cid]); old_case = Path(row['sim_case_path'])
        # The case path is the same committed relative input in the selected runtime.
        relative = str(old_case).split('/examples/cases/',1)[1]
        old_case = FIXED/'examples/cases'/relative
        case = read(old_case); actual_pin = operator[cid]['actual_identity']; actual = read(actual_pin['path'])
        assert pin(actual_pin['path'])['sha256'] == actual_pin['sha256']
        generation = generations[cid]
        assert generation['body_operator_population_reusable']
        assert actual['source_identity']['sha256'] == row['source']['sha256'] == generation['source']['sha256']
        geometry = deepcopy(actual['geometry'])
        geometry.update(phase='decode', context_tokens=row['geometry']['context_tokens'])
        M, B, q = [geometry[k] for k in ('query_rows','sequences_per_replica','tokens_per_sequence')]
        kernels = case['runtime'].setdefault('kernels', {})
        lowerings = kernels.setdefault('lowerings', {})
        lowerings.update(conv_state_copy={'implementation':'triton_noncontiguous_conv_state_copy',
                                         'options':{'state_slots':6}},
                         moe_init_routing='ascend_moe_init_routing_v3_mxfp8')
        kernels['hccl'] = {'allreduce':{'expansion':'AICPU_TS','template':'mesh_oneshot','axes':['tp']}}
        kernels.pop('service_regimes', None)
        parsed = parse_case(case)
        ops = target_graphs(parsed, phase='decode', tokens=q, context=geometry['context_tokens'],
                            sequences=B, scope='body')[0]
        plans = {
            'hcom_allReduce_AicpuKernel': ('hccl_entry', {'kernel':'HCCL_AICPU_TS_allreduce_mesh_oneshot',
                 'metadata.hccl_selection.ranks':8,'metadata.hccl_selection.dtype_bytes':2},
                 {'payload_bytes':{'path':'metadata.hccl_selection.payload_bytes'}},
                 {'payload_bytes':{'min':M*4096*2,'max':M*4096*2}}),
            '_copy_conv_state_kernel': ('triton_noncontiguous_conv_state_copy',
                 {'recipe':'triton_noncontiguous_conv_state_copy','dtype':'bf16',
                  'local_shape.1':6,'local_shape.2':3072},
                 {'batch':{'path':'local_shape.0'}},{'batch':{'min':B,'max':B}}),
            'MoeInitRoutingV3': ('ascend_moe_init_routing_v3_mxfp8',
                 {'recipe':'ascend_moe_init_routing_v3_mxfp8','dtype':'bf16',
                  'metadata.moe_init_config.experts':288,'metadata.moe_init_config.topk':8,
                  'metadata.moe_init_config.width':4096},
                 {'tokens':{'path':'metadata.moe_init_config.tokens'}},{'tokens':{'min':M,'max':M}}),
            'GroupedMatmulSwigluQuantV2': ('ascend_mxfp8_grouped_swiglu_quant',
                 {'recipe':'ascend_mxfp8_grouped_swiglu_quant','metadata.mxfp8_swiglu_config.k':4096,
                  'metadata.mxfp8_swiglu_config.width':256},
                 {'routed_rows':{'path':'local_shape.0'}, 'groups':{'path':'metadata.mxfp8_swiglu_config.rows','reduce':'len'}},
                 {'routed_rows':{'min':M*8,'max':M*8},'groups':{'min':288,'max':288}}),
            'CausalConv1d': ('short_convolution', {'recipe':'short_convolution','dtype':'bf16'},
                 {'elements':{'path':'local_shape.0'}},{'elements':{'min':M*3072,'max':M*3072}}),
            'RecurrentKda': ('vllm_ascend_recurrent_kda_arch35',
                 {'recipe':'vllm_ascend_recurrent_kda_arch35','metadata.native_kind':'RecurrentKda',
                  'metadata.heads':8,'metadata.dk':128,'metadata.dv':128,'metadata.state_dtype':'fp32'},
                 {'tokens':{'path':'local_shape.0'}, 'batch':{'path':'metadata.sequence_tokens','reduce':'len'},
                  'query':{'path':'metadata.sequence_tokens','reduce':'max'}},
                 {'tokens':{'min':M,'max':M},'batch':{'min':B,'max':B},'query':{'min':q,'max':q}}),
        }
        rules, observed_groups = [], []
        for native, expected in NATIVES.items():
            families = [f for f in actual['families'] if f['native_operator_type']==native]
            if not families:
                observed_groups.append({'native_operator_type':native,'status':'missing_retained_population'})
                continue
            stats = summarize(families)
            assert stats['count'] == actual['forward_count']*expected, (cid,native,stats['count'])
            recipe, match, coordinates, domain = plans[native]
            targets = [o for o in ops if o.recipe==recipe]
            assert len(targets)==expected, (cid,native,len(targets))
            rid = native.lower().replace('_','-')+'-observed'
            population = {'native_operator_type':native,'actual_identity':actual_pin,
                          'source_identity':actual['source_identity'],'forward_count':actual['forward_count'],
                          'calls_per_forward':expected,'observed':stats,
                          'family_indices':[i for i,f in enumerate(actual['families']) if f in families],
                          'recipe':recipe,'declared_occurrences':len(targets),
                          'rule_id':rid,'native_abi_admission':'unchanged; service observation is not strict tensor proof'}
            if native == '_copy_conv_state_kernel':
                population['boundary_caution']='Pooled gather/scatter histogram; equal per-call mean is an explicit service assignment, not measured direction-specific latency.'
            if native.startswith('hcom'):
                population['boundary_caution']='COMMUNICATION envelope; full call may include peer waiting. Mesh OneShot and payload are source-declared conditions; no pure-link bandwidth inference.'
                ledger = ROOT/'examples/structure/acceptance-20261030-hccl-66'/f'{cid}-capture-hccl.json'
                population['typed_capture_ledger_identity'] = pin(ledger)
            rules.append({'id':rid,'match':{'hardware':parsed.machine.sku,**match},
                          'coordinates':coordinates,'domain':domain,
                          'response':{'fixed_us':stats['mean_us']},
                          'provenance':{'basis':'retained_complete_native_population_mean',
                                        'calibration_origin':'observed','evaluation_role':'in_sample',
                                        'actual_identity':actual_pin,'source_sha256':actual['source_identity']['sha256'],
                                        'native_operator_type':native,'count':stats['count'],
                                        'body_count':actual['forward_count'],'mean_us':stats['mean_us'],
                                        'p50_us':stats['p50_us'],'physical_domain':geometry,
                                        'body_residual_used':False,'response_boundary':'inclusive_native_call_once',
                                        'contract_and_source_uncertainties_retained':True,
                                        'boundary_caution':population.get('boundary_caution')}})
            observed_groups.append(population)
        kernels['service_regimes'] = rules
        calibration = {'evaluation_role':'in_sample','parameter_assignment':'native_call_means_only',
                       'source_identity':actual['source_identity'],'actual_identity':actual_pin,
                       'body_residual_used':False,'held_out_capture':False,
                       'contract_admission_changed':False,'regime_count':len(rules)}
        metadata = case['runtime'].setdefault('metadata',{})
        metadata.update(calibration_origin='observed',calibration_evidence=calibration)
        case_path = HERE/'cases'/f'{cid}-service-regimes.json'
        write(case_path,case)
        row.update(sim_case_path=str(case_path), extraction_path=generation['extraction_path'],
                   calibration_origin='observed',calibration_evidence=calibration,variant_id='observed-service-2f48346b')
        row['model_declaration']=pin(case_path)
        row['replay_input_pins']={'case':pin(case_path),'extraction':generation['extraction_identity'],
                                 'source_identity':row['source'],'primary_geometry':geometry}
        row['prior_source_case_identity']=pin(old_case)
        out.append(row)
        evidence.append({'case_id':cid,'case_identity':pin(case_path),'prior_case_identity':pin(old_case),
                         'source_identity':row['source'],'geometry':geometry,'forward_count':actual['forward_count'],
                         'extraction_identity':generation['extraction_identity'],'groups':observed_groups})
        print(cid, 'rules',len(rules),'F',actual['forward_count'],flush=True)
    write(HERE/'observed-populations.json', {'schema_version':'mindie-native-service-populations/1',
          'cases':evidence,'raw_capture_scans':0,'new_predictions':0,
          'input_identities':[pin(manifest_path),pin(operator_path),pin(generation_path)],'generator_identity':pin(__file__)})
    write(HERE/'decode-forward-service-cases.json',{'schema_version':manifest['schema_version'],
          'variant_id':'observed-service-2f48346b','cases':out,'not_new_live_collection':True,
          'calibration_origin':'observed','calibration_evidence':{'evaluation_role':'in_sample'},
          'basis':'Native per-call observation parameters; no Body residual fitting.'})


if __name__=='__main__':
    prepare()
