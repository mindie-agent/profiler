# Native Fusion Storage Evidence

This is a read-only source audit supporting resource declarations. It is not a
new NPU run, a measurement of physical HBM traffic, or proof of the binaries that
produced the retained captures. The companion JSON pins source state, revisions,
file hashes, and exact line ranges.

| Native boundary | Proven local edges | Traffic that remains |
|---|---|---|
| MlaPrologV3, inspected arch35 implementation | KV normalization to cache scatter; K rotary to cache scatter | Q down/norm/up, KV projection, absorbed projection intermediates remain GM workspaces. Query, Q-rope, cache, and scale outputs remain. |
| HcPre, A3 and arch35 K-split | Pre coefficients to residual reduction; affine coefficients through Sinkhorn | A3 FP32 cast workspace; partial RMS/projection workspaces; source X reread; final y/post/comb writes. |
| HcPre, arch35 M-split key 1001 only | Cast through UB to L1; projection through L0C to UB; coefficient processing | Source X reread and external y/post/comb writes. This stronger reduction requires the selected tiling branch. |
| HcPost | Weighted products and accumulated residual mixture remain in UB/registers | x/residual/post/comb reads and final y write. |
| AttnResFwd | Exact native implementation is not established | The independent Triton candidate cannot authorize folding the captured native kind. That candidate itself reads residuals twice. |

The MlaProlog implementation explicitly allocates `mmCqResGm`,
`rmsNormCqResGm`, `mmCkvKrResGm`, `mmQcQrResGm`, and dequantized Q workspace.
`queryNormFlag=0` moves Q normalization into an internal GM workspace; it does
not keep that result on chip. Workspace aliasing likewise does not eliminate
the producer write and consumer read.

HC Pre requires branch-specific accounting. A3 casts X into a GM workspace
that the cube reads and exchanges partial projection/RMS results through GM.
Its later pre coefficients and Sinkhorn iterations use local tensors. The
arch35 M-split branch instead passes cast X from UB to L1 and copies the cube
result directly to UB. Applying that branch's savings to the A3 or K-split
branch would undercount traffic.

For the independently inspected Kimi Triton attention-residual implementation,
RMS normalization, score projection, and softmax remain local, but the weighted
sum loads the original residuals a second time. The captured `AttnResFwd` has
not been tied to this implementation, so its resource behavior remains an
explicit source gap.

Resource folding must preserve arithmetic and required output/cache effects.
Only a payload edge proven to stay local in the selected implementation can
lose its standalone GM write/read. GM address-space operations are not a claim
that every byte reaches physical HBM; caching belongs to the resource model.

The GQA preprocessing declaration also respects its native boundary: it starts
from projected QKV, includes Q/K normalization, rotary, and materialized V/gate
outputs, and excludes the QKV GEMM. Retained captures exposing only one of the
four required outputs keep an unknown tensor contract. The DCP
`AttentionUpdate` correspondence belongs to the existing partial-result merge
node and excludes the preceding collective. No exact source for the retained
`_copy_pcp_kv_cache_kernel` has been established.
