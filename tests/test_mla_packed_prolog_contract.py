"""Retained GLM78 A3 prolog rows cover both query-norm output branches."""
from dataclasses import replace
import json
from pathlib import Path

from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import observed_contract, observed_contract_diagnostic


FIXTURE = Path(__file__).parent / 'fixtures/native_body_contracts/glm78_packed_prolog.csv'


def test_packed_cache_matches_retained_bytes_without_losing_full_native_abi():
    provenance = json.loads(FIXTURE.with_suffix('.provenance.json').read_text())
    for row, origin in zip(kernel_rows(FIXTURE), provenance['rows'], strict=True):
        assert json.loads(json.dumps(native_tensor_contract(row))) == origin['native_abi']
        result = observed_contract(row)
        tokens = row.input_shapes[0][0]
        assert result == (
            'mla_prolog_active', 'MlaPrologV3', ((tokens, 6144), 'int8', 'ND'),
            (((6144, 2048), 'int8'), ((2048, 1024), 'int8'),
             ((4, 192, 512), 'bf16'), ((6144, 576), 'int8'),
             ((2048,), 'bf16'), ((512,), 'bf16')),
            (((1, 656), 'int8', 'ND'), ((), None, None)),
            (((tokens, 4, 512), 'bf16', 'ND'), ((tokens, 4, 64), 'bf16', 'ND'),
             ((tokens, 2048), 'int8', 'ND') if origin['layer_count'] == 21 else ((), None, None)))
        assert origin['complete_call_count'] == origin['layer_count'] * origin['forward_count']
        # Cache allocation and elapsed time cannot identify the layer occurrence.
        cache = (9000, 128, 1, 656)
        changed = replace(row, duration_ns=row.duration_ns * 10,
                          input_shapes=(*row.input_shapes[:9], cache, *row.input_shapes[10:]),
                          output_shapes=(*row.output_shapes[:2], cache, *row.output_shapes[3:]))
        assert observed_contract(changed) == result
        assert native_tensor_contract(changed) != native_tensor_contract(row)


def test_packed_layout_cannot_be_widened_or_treated_as_floating_cache():
    row = next(kernel_rows(FIXTURE))
    cache = (*row.input_shapes[9][:-1], 672)
    padded = replace(row, input_shapes=(*row.input_shapes[:9], cache, *row.input_shapes[10:]),
                     output_shapes=(*row.output_shapes[:2], cache, *row.output_shapes[3:]))
    assert observed_contract(padded) is None
    assert observed_contract_diagnostic(padded)['reason'] == 'unsupported_mla_packed_cache'
    typed = replace(row, input_dtypes=(*row.input_dtypes[:9], 'DT_BF16', *row.input_dtypes[10:]),
                    output_dtypes=(*row.output_dtypes[:2], 'DT_BF16', *row.output_dtypes[3:]))
    assert observed_contract(typed) is None
    assert observed_contract_diagnostic(typed)['missing_fields'] == ['input[10].shape', 'output[3].shape']
