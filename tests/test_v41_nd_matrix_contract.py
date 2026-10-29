"""Actual V4.1 ND MXFP8 weights and scale orientations, independent of time."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import observed_contract
from mindie_profiler.body_matrix_contracts import matrix_contract_diagnostic

FIXTURE = Path(__file__).parent / 'fixtures/decode_forward/v41_dp8_first_body.csv'


def selected():
    return {row.line: row for row in kernel_rows(FIXTURE) if row.line in {73, 79, 83, 97}}


def change(row, field, index, value):
    values = list(getattr(row, field)); values[index] = value
    return replace(row, **{field: tuple(values)})


@pytest.mark.parametrize('line,n,k,weight_axes', [
    (73, 1280, 5120, (1280, 5120)), (79, 512, 5120, (512, 5120)),
    (83, 32768, 1280, (32768, 1280)), (97, 5120, 8192, (8192, 5120)),
])
def test_original_nd_v3_both_orientations_keep_complete_scale_geometry(line, n, k, weight_axes):
    row = selected()[line]
    assert row.input_shapes[1] == weight_axes
    expected = ('matrix', (1, n, k), 'fp8_e4m3', 'fp8_e4m3', 'bf16',
                (1, k // 64, 2), 'fp8_e8m0')
    assert observed_contract(row) == expected
    assert observed_contract(replace(row, duration_ns=999999999)) == expected
    reversed_axes = change(row, 'input_shapes', 1, tuple(reversed(weight_axes)))
    assert observed_contract(reversed_axes) is None
    assert matrix_contract_diagnostic(reversed_axes)['reason'] == 'unsupported_nd_mx_matrix_axes_or_scales'
    for field, index, value in [('input_shapes', 3, (1, k // 64, 1)),
            ('input_dtypes', 2, 'FLOAT'), ('input_formats', 2, 'NCHW'),
            ('input_dtypes', 1, 'INT8'), ('input_shapes', 2, (n, k // 64)),
            ('output_shapes', 0, (1, n + 1))]:
        assert observed_contract(change(row, field, index, value)) is None


def test_nd_mx_does_not_promote_an_int32_accumulator_or_unknown_tensor_slot():
    row = selected()[73]
    assert observed_contract(replace(row, output_dtypes=('INT32',))) is None
    assert observed_contract(change(row, 'input_dtypes', 2, 'DT_UNDEFINED')) is None
    assert observed_contract(replace(row, kind='QuantBatchMatmulV4')) is None
