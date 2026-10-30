# GLM78 TP8 complete native service refinement

The three existing captures now predict within 3% of the complete observed Body mean. This is an in-sample service arm. The preceding source-correct `tp_join_reduce` arm remains recorded with its genuine accuracy failures.

| Capture | Observed Body ms | Predicted Body ms | Relative error |
|---|---:|---:|---:|
| dc16k b1 | 39.112085 | 38.334370 | -1.9884% |
| dc4k b1 | 38.954827 | 38.046014 | -2.3330% |
| dc4k b2 | 40.969878 | 39.766880 | -2.9363% |

Each case preserves the previous three AllReduce service rules byte for byte and adds 24 rules from complete local native populations. Parameters come from full integer duration histograms, with exact source, native ABI, contract, and rule-hit evidence in `low-native-service-populations.json`. No parameter uses the Body residual. Local joint services replace one declared local kernel schedule; communication stays an inclusive service floor.

The original TP8/EP1/DP1 source caller performs 156 AllReduce calls per Forward. Router precision is tied to the complete BF16 population. Sparse attention is declared once for the complete batch, including b2. Unknown dynamic expert group-list values and unsupported combined projection/scatter boundaries remain explicit; buffer capacities are not promoted to valid routed counts.

One bounded local pass per original CSV preserved all 218 accepted Forward windows: 479,874 positive events and 148 complete ABI partitions. No device or remote collection ran. Source scanning peaked at 71.32 MiB. The standard Body arithmetic review passed 964 checks; root independently checked 582 parameter, histogram, preserved-rule, and actual Engine-query assertions with no failures.

The full replay JSON is an archive-backed artifact (SHA `abcf7a00f9c6e0c48e0d20cbe77ff6cccbc2b3741e50cb2e811b33189dc4bb00`); repository publication retains the compact table, source cases, complete population proof, and archive index. Layer and Body spans retain real communication and internal gaps. Native activity differences are not additive Body-wall attributions.
